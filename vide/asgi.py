
# vide/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from backend.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vide.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})

# backend/routing.py (pour les WebSockets)
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<chat_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
]

# backend/consumers.py (WebSocket consumers)
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    """Consumer pour le chat temps réel"""
    
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_name = f'chat_{self.chat_id}'
        
        # Joindre le groupe
        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.chat_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender_id = text_data_json['sender_id']
        
        # Envoyer le message au groupe
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': sender_id
            }
        )
    
    async def chat_message(self, event):
        message = event['message']
        sender_id = event['sender_id']
        
        # Envoyer le message au WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender_id': sender_id
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    """Consumer pour les notifications temps réel"""
    
    async def connect(self):
        self.user = self.scope["user"]
        
        if self.user.is_authenticated:
            self.notification_group_name = f'notifications_{self.user.id}'
            
            await self.channel_layer.group_add(
                self.notification_group_name,
                self.channel_name
            )
            
            await self.accept()
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'notification_group_name'):
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )
    
    async def notification_message(self, event):
        # Envoyer la notification au WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'title': event['title'],
            'message': event['message'],
            'data': event.get('data', {})
        }))

# Procfile (pour Render)
web: gunicorn --worker-class gevent --workers 3 --timeout 120 --bind 0.0.0.0:$PORT vide.wsgi:application
worker: celery -A vide worker --loglevel=info
