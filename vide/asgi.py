
# vide/asgi.py - WEBSOCKET SUPPORT FOR VGK CHAT SYSTEM
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from backend import consumers

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vide.settings')

django_asgi_app = get_asgi_application()

websocket_urlpatterns = [
    path('ws/chat/<uuid:chat_id>/', consumers.ChatConsumer.as_asgi()),
    path('ws/group-chat/<uuid:group_id>/', consumers.GroupChatConsumer.as_asgi()),
    path('ws/private-chat/<uuid:chat_id>/', consumers.PrivateChatConsumer.as_asgi()),
    path('ws/notifications/<str:user_id>/', consumers.NotificationConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
