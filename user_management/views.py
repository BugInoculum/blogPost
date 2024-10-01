from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from .forms import UserRegistrationForm
from .models import BlogPost, CustomUser, Comment
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, DetailView


class UserRegistrationView(FormView):
    template_name = 'registration/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.user_type = form.cleaned_data['user_type']
        user.save()
        login(self.request, user)
        return super().form_valid(form)


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    success_url = reverse_lazy('post_list')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)


@method_decorator(never_cache, name='dispatch')
class PostCreateView(LoginRequiredMixin, CreateView):
    model = BlogPost
    fields = ['title', 'content']
    template_name = 'blog/create_post.html'
    success_url = reverse_lazy('post_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        post = form.save()

        # Prepare the post data to send to WebSocket clients
        post_data = {
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'author': post.author.username,
            'created_at': post.created_at.strftime('%Y-%m-%d %H:%M')
        }

        # Send the new post to WebSocket clients
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'posts',  # Group name for posts
            {
                'type': 'send_post_update',
                'action': 'create',
                'post': post_data
            }
        )

        return JsonResponse(post_data, status=201)

    def dispatch(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return HttpResponseForbidden("You need to log in to create posts")

        if self.request.user.user_type != 'admin':
            return redirect(reverse_lazy('post_list'))

        return super().dispatch(request, *args, **kwargs)


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = BlogPost
    fields = ['title', 'content']
    template_name = 'blog/edit_post.html'

    def form_valid(self, form):
        post = form.save()

        # Send WebSocket message to notify about the updated post
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "posts",  # WebSocket group name
            {
                'type': 'send_post_update',  # This calls send_post_update method in PostConsumer
                'action': 'update',
                'post': {
                    'id': post.id,
                    'title': post.title,
                    'content': post.content
                }
            }
        )

        if self.request.method == 'POST':
            return JsonResponse({
                'id': post.id,
                'title': post.title,
                'content': post.content
            })

        return super().form_valid(form)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = BlogPost
    success_url = reverse_lazy('post_list')

    def post(self, request, *args, **kwargs):
        print("in delete")
        post = self.get_object()
        post_id = post.id
        post.delete()

        # Send WebSocket message
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "posts",
            {
                'type': 'send_post_update',
                'action': 'delete',
                'post': {
                    'id': post_id
                }
            }
        )

        if request.method == 'POST':
            return JsonResponse({'status': 'success'})

        return super().delete(request, *args, **kwargs)


@method_decorator(never_cache, name='dispatch')
class PostListView(ListView):
    model = BlogPost
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    ordering = ['-created_at']

    def get_queryset(self):
        return BlogPost.objects.all().order_by('-created_at')


@method_decorator(never_cache, name='dispatch')
class UserProfileView(LoginRequiredMixin, ListView):
    model = BlogPost
    template_name = 'user_management/profile.html'
    context_object_name = 'posts'

    def get_queryset(self):
        return BlogPost.objects.filter(author=self.request.user)


class BlogPostDetailView(DetailView):
    model = BlogPost
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    pk_url_kwarg = 'post_id'


def fetch_posts(request):
    posts = BlogPost.objects.all().order_by('-created_at')
    posts_data = []
    for post in posts:
        preview_content = ''

        posts_data.append({
            'id': post.id,
            'title': post.title,
            'content': post.content[:20],  # For the preview
            'full_content': post.content,  # Full content for edit modal
            'author': post.author.username,
            'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    return JsonResponse({'posts': posts_data})


@login_required()
def add_comment(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(BlogPost, pk=post_id)
        author = request.user
        content = request.POST.get('content')

        if content:
            comment = Comment.objects.create(post=post, author=author, content=content)
            comment_data = {
                'id': comment.id,
                'author': comment.author.username,
                'content': comment.content,
                'post_id': post_id,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            }

            # Notify via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'comments_{post_id}',
                {
                    'type': 'send_comment',
                    'comment': comment_data
                }
            )

            return JsonResponse(comment_data, status=201)
        return JsonResponse({'error': 'Content is required'}, status=400)


def fetch_comments(request, post_id):
    post = get_object_or_404(BlogPost, pk=post_id)
    comments = post.comments.all().values('author__username', 'content', 'created_at')
    return JsonResponse(list(comments), safe=False)


@login_required
def like_post(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        post.dislikes.remove(request.user)  # Optional: Prevent both like and dislike
        liked = True

    return JsonResponse({
        'like_count': post.like_count,
        'dislike_count': post.dislike_count,
        'liked': liked
    })


@login_required
def dislike_post(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    if request.user in post.dislikes.all():
        post.dislikes.remove(request.user)
        disliked = False
    else:
        post.dislikes.add(request.user)
        post.likes.remove(request.user)  # Optional: Prevent both like and dislike
        disliked = True

    return JsonResponse({
        'like_count': post.like_count,
        'dislike_count': post.dislike_count,
        'disliked': disliked
    })
