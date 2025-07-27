# backend/consumers.py - WEBSOCKET CONSUMERS FOR REAL-TIME CHAT
import json
import uuid
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from .models import Chat, Message, GroupChat, GroupChatMessage
from .models_advanced import PrivateChat, PrivateMessage, OnlineStatus

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for product-based chats"""
    
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_name = f'chat_{self.chat_id}'
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
            
        # Join chat group
        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Update user's online status
        await self.update_online_status('ONLINE')
        
        # Notify other users that user joined
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'user_status',
                'user_id': str(self.user.id),
                'status': 'joined',
                'username': self.user.get_full_name() or self.user.email
            }
        )

    async def disconnect(self, close_code):
        # Update user's online status
        await self.update_online_status('OFFLINE')
        
        # Notify other users that user left
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'user_status',
                'user_id': str(self.user.id),
                'status': 'left',
                'username': self.user.get_full_name() or self.user.email
            }
        )
        
        # Leave chat group
        await self.channel_layer.group_discard(
            self.chat_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        
        if message_type == 'message':
            await self.handle_message(data)
        elif message_type == 'typing':
            await self.handle_typing(data)
        elif message_type == 'read':
            await self.handle_read_receipt(data)

    async def handle_message(self, data):
        message_content = data['message']
        message_type = data.get('message_type', 'TEXT')
        
        # Save message to database
        message = await self.save_message(message_content, message_type)
        
        if message:
            # Send message to chat group
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'chat_message',
                    'message_id': str(message.id),
                    'message': message_content,
                    'message_type': message_type,
                    'user_id': str(self.user.id),
                    'username': self.user.get_full_name() or self.user.email,
                    'timestamp': message.created_at.isoformat()
                }
            )

    async def handle_typing(self, data):
        is_typing = data.get('is_typing', False)
        
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'typing_indicator',
                'user_id': str(self.user.id),
                'username': self.user.get_full_name() or self.user.email,
                'is_typing': is_typing
            }
        )

    async def handle_read_receipt(self, data):
        message_id = data.get('message_id')
        if message_id:
            await self.mark_message_read(message_id)

    async def chat_message(self, event):
        """Send message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message_id': event['message_id'],
            'message': event['message'],
            'message_type': event['message_type'],
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        if event['user_id'] != str(self.user.id):  # Don't send to self
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))

    async def user_status(self, event):
        """Send user status to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user_id': event['user_id'],
            'username': event['username'],
            'status': event['status']
        }))

    @database_sync_to_async
    def save_message(self, message_content, message_type):
        try:
            chat = Chat.objects.get(id=self.chat_id)
            # Check if user is participant in this chat
            if self.user not in [chat.buyer, chat.seller]:
                return None
                
            message = Message.objects.create(
                chat=chat,
                sender=self.user,
                content=message_content,
                message_type=message_type
            )
            return message
        except ObjectDoesNotExist:
            return None

    @database_sync_to_async
    def mark_message_read(self, message_id):
        try:
            message = Message.objects.get(id=message_id)
            if message.chat.id == uuid.UUID(self.chat_id) and message.sender != self.user:
                message.is_read = True
                message.read_at = datetime.now()
                message.save()
        except ObjectDoesNotExist:
            pass

    @database_sync_to_async
    def update_online_status(self, status):
        try:
            online_status, created = OnlineStatus.objects.get_or_create(user=self.user)
            online_status.status = status
            online_status.save()
        except Exception:
            pass


class GroupChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for group chats"""
    
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.group_name = f'group_chat_{self.group_id}'
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
            
        # Check if user is member of this group
        is_member = await self.check_group_membership()
        if not is_member:
            await self.close()
            return
            
        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notify group that user joined
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'user_joined',
                'user_id': str(self.user.id),
                'username': self.user.get_full_name() or self.user.email
            }
        )

    async def disconnect(self, close_code):
        # Notify group that user left
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'user_left',
                'user_id': str(self.user.id),
                'username': self.user.get_full_name() or self.user.email
            }
        )
        
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        
        if message_type == 'message':
            await self.handle_group_message(data)
        elif message_type == 'typing':
            await self.handle_group_typing(data)

    async def handle_group_message(self, data):
        message_content = data['message']
        msg_type = data.get('message_type', 'TEXT')
        
        # Save message to database
        message = await self.save_group_message(message_content, msg_type)
        
        if message:
            # Send message to group
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'group_message',
                    'message_id': str(message.id),
                    'message': message_content,
                    'message_type': msg_type,
                    'user_id': str(self.user.id),
                    'username': self.user.get_full_name() or self.user.email,
                    'timestamp': message.created_at.isoformat()
                }
            )

    async def handle_group_typing(self, data):
        is_typing = data.get('is_typing', False)
        
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'group_typing',
                'user_id': str(self.user.id),
                'username': self.user.get_full_name() or self.user.email,
                'is_typing': is_typing
            }
        )

    async def group_message(self, event):
        """Send group message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message_id': event['message_id'],
            'message': event['message'],
            'message_type': event['message_type'],
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    async def group_typing(self, event):
        """Send typing indicator to WebSocket"""
        if event['user_id'] != str(self.user.id):  # Don't send to self
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))

    async def user_joined(self, event):
        """Send user joined notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username']
        }))

    async def user_left(self, event):
        """Send user left notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'username': event['username']
        }))

    @database_sync_to_async
    def check_group_membership(self):
        try:
            group_chat = GroupChat.objects.get(id=self.group_id)
            return group_chat.participants.filter(id=self.user.id).exists()
        except ObjectDoesNotExist:
            return False

    @database_sync_to_async
    def save_group_message(self, message_content, message_type):
        try:
            group_chat = GroupChat.objects.get(id=self.group_id)
            message = GroupChatMessage.objects.create(
                group_chat=group_chat,
                sender=self.user,
                content=message_content,
                message_type=message_type
            )
            return message
        except ObjectDoesNotExist:
            return None


class PrivateChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for private chats (client-admin, staff-admin)"""
    
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_name = f'private_chat_{self.chat_id}'
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
            
        # Check if user is participant in this private chat
        is_participant = await self.check_chat_participation()
        if not is_participant:
            await self.close()
            return
            
        # Join chat group
        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave chat group
        await self.channel_layer.group_discard(
            self.chat_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        
        if message_type == 'message':
            await self.handle_private_message(data)
        elif message_type == 'typing':
            await self.handle_private_typing(data)

    async def handle_private_message(self, data):
        message_content = data['message']
        msg_type = data.get('message_type', 'TEXT')
        
        # Save message to database
        message = await self.save_private_message(message_content, msg_type)
        
        if message:
            # Send message to chat group
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'private_message',
                    'message_id': str(message.id),
                    'message': message_content,
                    'message_type': msg_type,
                    'user_id': str(self.user.id),
                    'username': self.user.get_full_name() or self.user.email,
                    'timestamp': message.created_at.isoformat()
                }
            )

    async def handle_private_typing(self, data):
        is_typing = data.get('is_typing', False)
        
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'private_typing',
                'user_id': str(self.user.id),
                'username': self.user.get_full_name() or self.user.email,
                'is_typing': is_typing
            }
        )

    async def private_message(self, event):
        """Send private message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message_id': event['message_id'],
            'message': event['message'],
            'message_type': event['message_type'],
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    async def private_typing(self, event):
        """Send typing indicator to WebSocket"""
        if event['user_id'] != str(self.user.id):  # Don't send to self
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))

    @database_sync_to_async
    def check_chat_participation(self):
        try:
            private_chat = PrivateChat.objects.get(id=self.chat_id)
            return self.user in [private_chat.participant_1, private_chat.participant_2]
        except ObjectDoesNotExist:
            return False

    @database_sync_to_async
    def save_private_message(self, message_content, message_type):
        try:
            private_chat = PrivateChat.objects.get(id=self.chat_id)
            message = PrivateMessage.objects.create(
                private_chat=private_chat,
                sender=self.user,
                content=message_content,
                message_type=message_type
            )
            return message
        except ObjectDoesNotExist:
            return None


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications"""
    
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.notification_group_name = f'notifications_{self.user_id}'
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated or str(self.user.id) != self.user_id:
            await self.close()
            return
            
        # Join notification group
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave notification group
        await self.channel_layer.group_discard(
            self.notification_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Handle notification acknowledgments
        data = json.loads(text_data)
        if data.get('type') == 'mark_read' and data.get('notification_id'):
            await self.mark_notification_read(data['notification_id'])

    async def send_notification(self, event):
        """Send notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification_id': event['notification_id'],
            'title': event['title'],
            'message': event['message'],
            'notification_type': event['notification_type'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        try:
            from .models import Notification
            notification = Notification.objects.get(id=notification_id, user=self.user)
            notification.is_read = True
            notification.read_at = datetime.now()
            notification.save()
        except ObjectDoesNotExist:
            pass 