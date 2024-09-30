from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):

    ADMIN = 'admin'
    REGULAR = 'regular'

    USER_TYPE_CHOICES = [
        (ADMIN, 'Admin'),
        (REGULAR, 'Regular')
    ]

    user_type = models.CharField(choices=USER_TYPE_CHOICES, default=REGULAR, max_length=10)

    def __str__(self):
        return self.username + f" ({self.user_type})"


class BlogPost(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    likes = models.ManyToManyField(CustomUser, related_name="post_likes", blank=True)
    dislikes = models.ManyToManyField(CustomUser, related_name="post_dislikes", blank=True)

    def __str__(self):
        return self.title

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def dislike_count(self):
        return self.dislikes.count()


class Comment(models.Model):
    post = models.ForeignKey(BlogPost, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"