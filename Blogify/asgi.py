"""
ASGI config for Blogify project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path
from .consumers import CommentConsumer, PostConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Blogify.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter([
            path('ws/comments/', CommentConsumer.as_asgi()),
            path('ws/posts/', PostConsumer.as_asgi()),

        ])
    ),
})
