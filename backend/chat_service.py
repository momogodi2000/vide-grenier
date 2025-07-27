# backend/chat_service.py - WebSocket Chat Integration Service

import json
import asyncio
from typing import Dict, List, Optional, Set
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Chat, Message, User
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat functionality
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None
        self.user = None
        self.chat = None
    
    async def connect(self):
        """
        Handle WebSocket connection
        """
        try:
            # Get user from scope
            self.user = self.scope["user"]
            
            if not self.user.is_authenticated:
                await self.close()
                return
            
            # Get chat room from URL parameters
            self.room_name = self.scope['url_route']['kwargs']['chat_id']
            self.room_group_name = f'chat_{self.room_name}'
            
            # Verify user has access to this chat
            if not await self.can_access_chat():
                await self.close()
                return
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Send connection confirmation
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to chat',
                'user_id': self.user.id,
                'chat_id': self.room_name
            }))
            
            # Mark user as online
            await self.mark_user_online(True)
            
            # Notify other users in chat
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': self.user.id,
                    'status': 'online',
                    'username': self.user.get_full_name()
                }
            )
            
        except Exception as e:
            logger.error(f"Error in WebSocket connect: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection
        """
        try:
            # Mark user as offline
            await self.mark_user_online(False)
            
            # Notify other users in chat
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': self.user.id,
                    'status': 'offline',
                    'username': self.user.get_full_name()
                }
            )
            
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
        except Exception as e:
            logger.error(f"Error in WebSocket disconnect: {e}")
    
    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')
            
            if message_type == 'message':
                await self.handle_chat_message(data)
            elif message_type == 'typing':
                await self.handle_typing_indicator(data)
            elif message_type == 'read_receipt':
                await self.handle_read_receipt(data)
            elif message_type == 'file_upload':
                await self.handle_file_upload(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
    
    async def handle_chat_message(self, data):
        """
        Handle chat message
        """
        try:
            content = data.get('content', '').strip()
            message_type = data.get('message_type', 'text')
            reply_to = data.get('reply_to')
            
            if not content:
                return
            
            # Save message to database
            message = await self.save_message(content, message_type, reply_to)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message_id': message.id,
                    'content': content,
                    'message_type': message_type,
                    'user_id': self.user.id,
                    'username': self.user.get_full_name(),
                    'timestamp': message.created_at.isoformat(),
                    'reply_to': reply_to
                }
            )
            
            # Send delivery confirmation
            await self.send(text_data=json.dumps({
                'type': 'message_sent',
                'message_id': message.id,
                'timestamp': message.created_at.isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
    
    async def handle_typing_indicator(self, data):
        """
        Handle typing indicator
        """
        try:
            is_typing = data.get('is_typing', False)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': self.user.id,
                    'username': self.user.get_full_name(),
                    'is_typing': is_typing
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling typing indicator: {e}")
    
    async def handle_read_receipt(self, data):
        """
        Handle read receipt
        """
        try:
            message_id = data.get('message_id')
            
            if message_id:
                await self.mark_message_read(message_id)
                
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'read_receipt',
                        'message_id': message_id,
                        'user_id': self.user.id,
                        'username': self.user.get_full_name(),
                        'timestamp': timezone.now().isoformat()
                    }
                )
                
        except Exception as e:
            logger.error(f"Error handling read receipt: {e}")
    
    async def handle_file_upload(self, data):
        """
        Handle file upload
        """
        try:
            file_data = data.get('file_data')
            file_name = data.get('file_name')
            file_type = data.get('file_type')
            
            # Process file upload (implement file handling logic)
            file_url = await self.process_file_upload(file_data, file_name, file_type)
            
            if file_url:
                # Save file message
                message = await self.save_message(
                    f"File: {file_name}",
                    'file',
                    file_url=file_url
                )
                
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message_id': message.id,
                        'content': f"File: {file_name}",
                        'message_type': 'file',
                        'file_url': file_url,
                        'file_name': file_name,
                        'file_type': file_type,
                        'user_id': self.user.id,
                        'username': self.user.get_full_name(),
                        'timestamp': message.created_at.isoformat()
                    }
                )
                
        except Exception as e:
            logger.error(f"Error handling file upload: {e}")
    
    # WebSocket message handlers
    async def chat_message(self, event):
        """
        Send chat message to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message_id': event['message_id'],
            'content': event['content'],
            'message_type': event['message_type'],
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp'],
            'reply_to': event.get('reply_to'),
            'file_url': event.get('file_url'),
            'file_name': event.get('file_name'),
            'file_type': event.get('file_type')
        }))
    
    async def typing_indicator(self, event):
        """
        Send typing indicator to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'typing_indicator',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))
    
    async def read_receipt(self, event):
        """
        Send read receipt to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))
    
    async def user_status(self, event):
        """
        Send user status update to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user_id': event['user_id'],
            'username': event['username'],
            'status': event['status']
        }))
    
    # Database operations
    @database_sync_to_async
    def can_access_chat(self):
        """
        Check if user can access this chat
        """
        try:
            self.chat = Chat.objects.get(id=self.room_name)
            return (self.user in self.chat.participants.all() or 
                   self.user.is_staff or 
                   self.user.is_superuser)
        except Chat.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content, message_type='text', reply_to=None, file_url=None):
        """
        Save message to database
        """
        try:
            message = Message.objects.create(
                chat=self.chat,
                sender=self.user,
                content=content,
                message_type=message_type,
                reply_to_id=reply_to,
                file_url=file_url
            )
            
            # Update chat last activity
            self.chat.last_activity = timezone.now()
            self.chat.save()
            
            return message
            
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None
    
    @database_sync_to_async
    def mark_message_read(self, message_id):
        """
        Mark message as read
        """
        try:
            message = Message.objects.get(id=message_id, chat=self.chat)
            if self.user not in message.read_by.all():
                message.read_by.add(self.user)
                message.save()
        except Message.DoesNotExist:
            pass
    
    @database_sync_to_async
    def mark_user_online(self, is_online):
        """
        Mark user as online/offline
        """
        try:
            self.user.is_online = is_online
            self.user.last_seen = timezone.now()
            self.user.save()
        except Exception as e:
            logger.error(f"Error marking user online: {e}")
    
    @database_sync_to_async
    def process_file_upload(self, file_data, file_name, file_type):
        """
        Process file upload (implement file handling)
        """
        # This would typically handle file upload to storage
        # For now, return a placeholder URL
        return f"/media/uploads/{file_name}"


class ChatManager:
    """
    Chat management service for admin operations
    """
    
    @staticmethod
    def create_chat(participants: List[User], chat_type: str = 'private', title: str = None):
        """
        Create a new chat
        """
        try:
            chat = Chat.objects.create(
                chat_type=chat_type,
                title=title or f"Chat between {', '.join([p.get_full_name() for p in participants])}"
            )
            chat.participants.add(*participants)
            return chat
        except Exception as e:
            logger.error(f"Error creating chat: {e}")
            return None
    
    @staticmethod
    def get_user_chats(user: User):
        """
        Get all chats for a user
        """
        try:
            return Chat.objects.filter(participants=user).order_by('-last_activity')
        except Exception as e:
            logger.error(f"Error getting user chats: {e}")
            return []
    
    @staticmethod
    def get_chat_messages(chat_id: int, limit: int = 50, offset: int = 0):
        """
        Get chat messages with pagination
        """
        try:
            return Message.objects.filter(chat_id=chat_id).order_by('-created_at')[offset:offset + limit]
        except Exception as e:
            logger.error(f"Error getting chat messages: {e}")
            return []
    
    @staticmethod
    def mark_chat_as_read(chat_id: int, user: User):
        """
        Mark all messages in chat as read for user
        """
        try:
            messages = Message.objects.filter(chat_id=chat_id, sender__in=chat.participants.exclude(id=user.id))
            for message in messages:
                if user not in message.read_by.all():
                    message.read_by.add(user)
        except Exception as e:
            logger.error(f"Error marking chat as read: {e}")
    
    @staticmethod
    def get_unread_count(user: User):
        """
        Get unread message count for user
        """
        try:
            user_chats = Chat.objects.filter(participants=user)
            total_unread = 0
            
            for chat in user_chats:
                unread_messages = Message.objects.filter(
                    chat=chat,
                    sender__in=chat.participants.exclude(id=user.id)
                ).exclude(read_by=user)
                total_unread += unread_messages.count()
            
            return total_unread
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0
    
    @staticmethod
    def delete_chat(chat_id: int, user: User):
        """
        Delete chat (admin only)
        """
        try:
            if user.is_staff or user.is_superuser:
                chat = Chat.objects.get(id=chat_id)
                chat.delete()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting chat: {e}")
            return False


class NotificationService:
    """
    Real-time notification service
    """
    
    @staticmethod
    async def send_notification(user_id: int, notification_type: str, data: Dict):
        """
        Send real-time notification to user
        """
        try:
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            
            await channel_layer.group_send(
                f"user_{user_id}",
                {
                    'type': 'notification',
                    'notification_type': notification_type,
                    'data': data
                }
            )
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    @staticmethod
    async def broadcast_to_admins(notification_type: str, data: Dict):
        """
        Broadcast notification to all online admins
        """
        try:
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            
            await channel_layer.group_send(
                "admin_notifications",
                {
                    'type': 'admin_notification',
                    'notification_type': notification_type,
                    'data': data
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting to admins: {e}")


# Global instances
chat_manager = ChatManager()
notification_service = NotificationService() 