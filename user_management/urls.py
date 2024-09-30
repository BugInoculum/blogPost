from django.contrib.auth.views import LogoutView
from django.urls import path
from .views import PostCreateView, PostUpdateView, PostDeleteView, PostListView, UserRegistrationView, CustomLoginView, \
    fetch_posts, post_comment, like_post, dislike_post, UserProfileView, BlogPostDetailView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('create-post/', PostCreateView.as_view(), name='create_post'),
    path('fetch-posts/', fetch_posts, name='fetch_posts'),

    path('edit-post/<int:pk>/', PostUpdateView.as_view(), name='edit_post'),
    path('delete-post/<int:pk>/', PostDeleteView.as_view(), name='delete_post'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', PostListView.as_view(), name='post_list'),
    path('post/<int:post_id>/comment/', post_comment, name='post_comment'),
    path('post/<int:post_id>/like/', like_post, name='like_post'),
    path('post/<int:post_id>/dislike/', dislike_post, name='dislike_post'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('post/<int:post_id>/', BlogPostDetailView.as_view(), name='blog_post_detail'),

]

