"""
WebSocket Chat System for Vidé-Grenier Kamer
Real-time messaging between clients, admin, and staff users
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import User, Chat, Message, GroupChat, GroupChatMessage
from .smart_notifications import send_notification

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for private chat messages"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Get chat ID from URL parameters
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        
        # Verify user has access to this chat
        if not await self.can_access_chat():
            await self.close()
            return
        
        # Join chat room
        await self.channel_layer.group_add(
            f"chat_{self.chat_id}",
            self.channel_name
        )
        
        await self.accept()
        
        # Send chat history
        await self.send_chat_history()
        
        logger.info(f"User {self.user.id} connected to chat {self.chat_id}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'chat_id'):
            await self.channel_layer.group_discard(
                f"chat_{self.chat_id}",
                self.channel_name
            )
        
        logger.info(f"User {self.user.id} disconnected from chat {getattr(self, 'chat_id', 'unknown')}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')
            
            if message_type == 'message':
                await self.handle_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'read':
                await self.handle_read_receipt(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    async def handle_message(self, data):
        """Handle chat message"""
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'TEXT')
        
        if not content:
            return
        
        # Save message to database
        message = await self.save_message(content, message_type)
        
        if message:
            # Send message to chat group
            await self.channel_layer.group_send(
                f"chat_{self.chat_id}",
                {
                    'type': 'chat_message',
                    'message': {
                        'id': str(message.id),
                        'content': message.content,
                        'message_type': message.message_type,
                        'sender_id': str(message.sender.id),
                        'sender_name': message.sender.get_full_name() or message.sender.email,
                        'timestamp': message.created_at.isoformat(),
                        'is_read': message.is_read
                    }
                }
            )
            
            # Send notification to other user
            await self.send_notification_to_other_user(message)
    
    async def handle_typing(self, data):
        """Handle typing indicator"""
        is_typing = data.get('typing', False)
        
        await self.channel_layer.group_send(
            f"chat_{self.chat_id}",
            {
                'type': 'user_typing',
                'user_id': str(self.user.id),
                'user_name': self.user.get_full_name() or self.user.email,
                'typing': is_typing
            }
        )
    
    async def handle_read_receipt(self, data):
        """Handle read receipt"""
        message_id = data.get('message_id')
        
        if message_id:
            await self.mark_message_as_read(message_id)
            
            await self.channel_layer.group_send(
                f"chat_{self.chat_id}",
                {
                    'type': 'message_read',
                    'message_id': message_id,
                    'read_by': str(self.user.id),
                    'timestamp': timezone.now().isoformat()
                }
            )
    
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))
    
    async def user_typing(self, event):
        """Send typing indicator to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'typing': event['typing']
        }))
    
    async def message_read(self, event):
        """Send read receipt to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'read_by': event['read_by'],
            'timestamp': event['timestamp']
        }))
    
    @database_sync_to_async
    def can_access_chat(self):
        """Check if user can access this chat"""
        try:
            chat = Chat.objects.get(id=self.chat_id)
            return (self.user == chat.buyer or 
                   self.user == chat.seller or 
                   self.user.user_type in ['ADMIN', 'STAFF'])
        except Chat.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content, message_type):
        """Save message to database"""
        try:
            chat = Chat.objects.get(id=self.chat_id)
            message = Message.objects.create(
                chat=chat,
                sender=self.user,
                content=content,
                message_type=message_type
            )
            return message
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None
    
    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        """Mark message as read"""
        try:
            message = Message.objects.get(id=message_id)
            if message.sender != self.user:
                message.is_read = True
                message.save()
        except Message.DoesNotExist:
            pass
    
    @database_sync_to_async
    def send_chat_history(self):
        """Send chat history to user"""
        try:
            chat = Chat.objects.get(id=self.chat_id)
            messages = Message.objects.filter(chat=chat).order_by('created_at')[:50]
            
            history = []
            for msg in messages:
                history.append({
                    'id': str(msg.id),
                    'content': msg.content,
                    'message_type': msg.message_type,
                    'sender_id': str(msg.sender.id),
                    'sender_name': msg.sender.get_full_name() or msg.sender.email,
                    'timestamp': msg.created_at.isoformat(),
                    'is_read': msg.is_read
                })
            
            return history
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
    async def send_chat_history(self):
        """Send chat history to WebSocket"""
        history = await self.get_chat_history()
        
        await self.send(text_data=json.dumps({
            'type': 'chat_history',
            'messages': history
        }))
    
    @database_sync_to_async
    def send_notification_to_other_user(self, message):
        """Send notification to other user in chat"""
        try:
            chat = message.chat
            other_user = chat.buyer if message.sender == chat.seller else chat.seller
            
            # Send in-app notification
            from .models import Notification
            Notification.objects.create(
                user=other_user,
                type='MESSAGE',
                title=f'Nouveau message de {message.sender.get_full_name() or message.sender.email}',
                message=message.content[:100] + '...' if len(message.content) > 100 else message.content,
                data={
                    'chat_id': str(chat.id),
                    'message_id': str(message.id),
                    'sender_id': str(message.sender.id)
                }
            )
            
            # Send email notification if user is offline
            if not self.is_user_online(other_user):
                send_notification(
                    'new_message',
                    other_user,
                    {
                        'sender_name': message.sender.get_full_name() or message.sender.email,
                        'message_preview': message.content[:100],
                        'chat_id': str(chat.id)
                    }
                )
                
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    @database_sync_to_async
    def is_user_online(self, user):
        """Check if user is currently online"""
        # This is a simplified check - in production you'd track user sessions
        return False

class GroupChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for group chat messages"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Get group chat ID from URL parameters
        self.group_chat_id = self.scope['url_route']['kwargs']['group_chat_id']
        
        # Verify user has access to this group chat
        if not await self.can_access_group_chat():
            await self.close()
            return
        
        # Join group chat room
        await self.channel_layer.group_add(
            f"group_chat_{self.group_chat_id}",
            self.channel_name
        )
        
        await self.accept()
        
        # Send group chat history
        await self.send_group_chat_history()
        
        logger.info(f"User {self.user.id} connected to group chat {self.group_chat_id}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'group_chat_id'):
            await self.channel_layer.group_discard(
                f"group_chat_{self.group_chat_id}",
                self.channel_name
            )
        
        logger.info(f"User {self.user.id} disconnected from group chat {getattr(self, 'group_chat_id', 'unknown')}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')
            
            if message_type == 'message':
                await self.handle_group_message(data)
            elif message_type == 'typing':
                await self.handle_group_typing(data)
            elif message_type == 'read':
                await self.handle_group_read_receipt(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    async def handle_group_message(self, data):
        """Handle group chat message"""
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'TEXT')
        
        if not content:
            return
        
        # Save message to database
        message = await self.save_group_message(content, message_type)
        
        if message:
            # Send message to group chat
            await self.channel_layer.group_send(
                f"group_chat_{self.group_chat_id}",
                {
                    'type': 'group_chat_message',
                    'message': {
                        'id': str(message.id),
                        'content': message.content,
                        'message_type': message.message_type,
                        'sender_id': str(message.sender.id),
                        'sender_name': message.sender.get_full_name() or message.sender.email,
                        'timestamp': message.created_at.isoformat(),
                        'read_by': list(message.read_by.values_list('id', flat=True))
                    }
                }
            )
            
            # Send notifications to other participants
            await self.send_notifications_to_participants(message)
    
    async def handle_group_typing(self, data):
        """Handle group typing indicator"""
        is_typing = data.get('typing', False)
        
        await self.channel_layer.group_send(
            f"group_chat_{self.group_chat_id}",
            {
                'type': 'group_user_typing',
                'user_id': str(self.user.id),
                'user_name': self.user.get_full_name() or self.user.email,
                'typing': is_typing
            }
        )
    
    async def handle_group_read_receipt(self, data):
        """Handle group read receipt"""
        message_id = data.get('message_id')
        
        if message_id:
            await self.mark_group_message_as_read(message_id)
            
            await self.channel_layer.group_send(
                f"group_chat_{self.group_chat_id}",
                {
                    'type': 'group_message_read',
                    'message_id': message_id,
                    'read_by': str(self.user.id),
                    'timestamp': timezone.now().isoformat()
                }
            )
    
    async def group_chat_message(self, event):
        """Send group chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))
    
    async def group_user_typing(self, event):
        """Send group typing indicator to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'typing': event['typing']
        }))
    
    async def group_message_read(self, event):
        """Send group read receipt to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'read_by': event['read_by'],
            'timestamp': event['timestamp']
        }))
    
    @database_sync_to_async
    def can_access_group_chat(self):
        """Check if user can access this group chat"""
        try:
            group_chat = GroupChat.objects.get(id=self.group_chat_id)
            return self.user in group_chat.participants.all()
        except GroupChat.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_group_message(self, content, message_type):
        """Save group message to database"""
        try:
            group_chat = GroupChat.objects.get(id=self.group_chat_id)
            message = GroupChatMessage.objects.create(
                group_chat=group_chat,
                sender=self.user,
                content=content,
                message_type=message_type
            )
            return message
        except Exception as e:
            logger.error(f"Error saving group message: {e}")
            return None
    
    @database_sync_to_async
    def mark_group_message_as_read(self, message_id):
        """Mark group message as read"""
        try:
            message = GroupChatMessage.objects.get(id=message_id)
            if message.sender != self.user:
                message.read_by.add(self.user)
        except GroupChatMessage.DoesNotExist:
            pass
    
    @database_sync_to_async
    def get_group_chat_history(self):
        """Get group chat history"""
        try:
            group_chat = GroupChat.objects.get(id=self.group_chat_id)
            messages = GroupChatMessage.objects.filter(group_chat=group_chat).order_by('created_at')[:50]
            
            history = []
            for msg in messages:
                history.append({
                    'id': str(msg.id),
                    'content': msg.content,
                    'message_type': msg.message_type,
                    'sender_id': str(msg.sender.id),
                    'sender_name': msg.sender.get_full_name() or msg.sender.email,
                    'timestamp': msg.created_at.isoformat(),
                    'read_by': list(msg.read_by.values_list('id', flat=True))
                })
            
            return history
        except Exception as e:
            logger.error(f"Error getting group chat history: {e}")
            return []
    
    async def send_group_chat_history(self):
        """Send group chat history to WebSocket"""
        history = await self.get_group_chat_history()
        
        await self.send(text_data=json.dumps({
            'type': 'chat_history',
            'messages': history
        }))
    
    @database_sync_to_async
    def send_notifications_to_participants(self, message):
        """Send notifications to other participants"""
        try:
            group_chat = message.group_chat
            participants = group_chat.participants.exclude(id=self.user.id)
            
            for participant in participants:
                # Send in-app notification
                from .models import Notification
                Notification.objects.create(
                    user=participant,
                    type='MESSAGE',
                    title=f'Nouveau message dans {group_chat.name}',
                    message=f'{message.sender.get_full_name() or message.sender.email}: {message.content[:100]}',
                    data={
                        'group_chat_id': str(group_chat.id),
                        'message_id': str(message.id),
                        'sender_id': str(message.sender.id)
                    }
                )
                
        except Exception as e:
            logger.error(f"Error sending group notifications: {e}")

class ChatNotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for chat notifications"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Join user's notification room
        await self.channel_layer.group_add(
            f"user_notifications_{self.user.id}",
            self.channel_name
        )
        
        await self.accept()
        
        logger.info(f"User {self.user.id} connected to notifications")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            f"user_notifications_{self.user.id}",
            self.channel_name
        )
        
        logger.info(f"User {self.user.id} disconnected from notifications")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        # This consumer is mainly for receiving notifications
        pass
    
    async def notification_message(self, event):
        """Send notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))

# Utility functions for sending notifications
async def send_chat_notification(user_id, notification_data):
    """Send chat notification to specific user"""
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()
    
    await channel_layer.group_send(
        f"user_notifications_{user_id}",
        {
            'type': 'notification_message',
            'notification': notification_data
        }
    )

def create_chat_between_users(user1, user2, product=None):
    """Create a new chat between two users"""
    try:
        # Check if chat already exists
        existing_chat = Chat.objects.filter(
            buyer=user1,
            seller=user2,
            product=product
        ).first()
        
        if existing_chat:
            return existing_chat
        
        # Create new chat
        chat = Chat.objects.create(
            buyer=user1,
            seller=user2,
            product=product
        )
        
        logger.info(f"Created new chat {chat.id} between {user1.id} and {user2.id}")
        return chat
        
    except Exception as e:
        logger.error(f"Error creating chat: {e}")
        return None

def create_group_chat(name, chat_type, participants, created_by):
    """Create a new group chat"""
    try:
        # Only admins can create group chats
        if created_by.user_type != 'ADMIN':
            return None
        
        group_chat = GroupChat.objects.create(
            name=name,
            type=chat_type,
            created_by=created_by
        )
        
        # Add participants
        group_chat.participants.add(*participants)
        
        logger.info(f"Created new group chat {group_chat.id}: {name}")
        return group_chat
        
    except Exception as e:
        logger.error(f"Error creating group chat: {e}")
        return None

def get_user_chats(user):
    """Get all chats for a user"""
    try:
        # Get chats where user is buyer or seller
        buyer_chats = Chat.objects.filter(buyer=user, is_active=True)
        seller_chats = Chat.objects.filter(seller=user, is_active=True)
        
        # Get group chats where user is participant
        group_chats = GroupChat.objects.filter(participants=user, is_active=True)
        
        return {
            'private_chats': list(buyer_chats) + list(seller_chats),
            'group_chats': list(group_chats)
        }
        
    except Exception as e:
        logger.error(f"Error getting user chats: {e}")
        return {'private_chats': [], 'group_chats': []}

def get_unread_message_count(user):
    """Get unread message count for user"""
    try:
        # Private chat messages
        private_chats = Chat.objects.filter(
            models.Q(buyer=user) | models.Q(seller=user),
            is_active=True
        )
        
        unread_private = Message.objects.filter(
            chat__in=private_chats,
            is_read=False
        ).exclude(sender=user).count()
        
        # Group chat messages
        group_chats = GroupChat.objects.filter(participants=user, is_active=True)
        
        unread_group = GroupChatMessage.objects.filter(
            group_chat__in=group_chats
        ).exclude(sender=user).exclude(read_by=user).count()
        
        return unread_private + unread_group
        
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        return 0 