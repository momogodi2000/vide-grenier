# backend/smart_notifications.py - INTELLIGENT NOTIFICATION SYSTEM
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Optional, Tuple
import os
import requests
import random
import string

# Make celery optional to avoid dependency issues during development
try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    # Fallback decorator when celery is not available
    CELERY_AVAILABLE = False
    def shared_task(func):
        return func

from .models import User, Product, Order
from .models_advanced import (
    SmartNotification, NotificationTemplate, UserBehavior,
    UserPreference, WishlistItem
)

logger = logging.getLogger(__name__)

class SMSService:
    """SMS service using multiple providers with fallback"""
    
    def __init__(self):
        self.twilio_enabled = os.environ.get('TWILIO_ENABLED', 'False').lower() == 'true'
        self.infobip_enabled = os.environ.get('INFOBIP_ENABLED', 'False').lower() == 'true'
        self.africastalking_enabled = os.environ.get('AFRICASTALKING_ENABLED', 'False').lower() == 'true'
        
        # Twilio configuration
        self.twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
        
        # Infobip configuration
        self.infobip_api_key = os.environ.get('INFOBIP_API_KEY')
        self.infobip_base_url = os.environ.get('INFOBIP_BASE_URL', 'https://api.infobip.com')
        self.infobip_sender_id = os.environ.get('INFOBIP_SENDER_ID', 'VIDEGRENIER')
        
        # Africa's Talking configuration
        self.africastalking_api_key = os.environ.get('AFRICASTALKING_API_KEY')
        self.africastalking_username = os.environ.get('AFRICASTALKING_USERNAME')
        self.africastalking_sender_id = os.environ.get('AFRICASTALKING_SENDER_ID', 'VIDEGRENIER')
    
    def send_sms(self, phone_number: str, message: str) -> Dict:
        """Send SMS using available providers with fallback"""
        providers = []
        
        if self.twilio_enabled and self.twilio_account_sid:
            providers.append(('twilio', self._send_twilio_sms))
        
        if self.infobip_enabled and self.infobip_api_key:
            providers.append(('infobip', self._send_infobip_sms))
        
        if self.africastalking_enabled and self.africastalking_api_key:
            providers.append(('africastalking', self._send_africastalking_sms))
        
        # Try each provider until one succeeds
        for provider_name, provider_func in providers:
            try:
                result = provider_func(phone_number, message)
                if result.get('success'):
                    logger.info(f"SMS sent successfully via {provider_name} to {phone_number}")
                    return result
                else:
                    logger.warning(f"SMS failed via {provider_name}: {result.get('error')}")
            except Exception as e:
                logger.error(f"Error sending SMS via {provider_name}: {str(e)}")
                continue
        
        logger.error(f"All SMS providers failed for {phone_number}")
        return {'success': False, 'error': 'All SMS providers failed'}
    
    def _send_twilio_sms(self, phone_number: str, message: str) -> Dict:
        """Send SMS via Twilio"""
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
            
            data = {
                'To': phone_number,
                'From': self.twilio_phone_number,
                'Body': message
            }
            
            response = requests.post(
                url,
                data=data,
                auth=(self.twilio_account_sid, self.twilio_auth_token),
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                return {
                    'success': True,
                    'provider': 'twilio',
                    'message_id': result.get('sid'),
                    'status': result.get('status')
                }
            else:
                return {
                    'success': False,
                    'provider': 'twilio',
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'provider': 'twilio',
                'error': str(e)
            }
    
    def _send_infobip_sms(self, phone_number: str, message: str) -> Dict:
        """Send SMS via Infobip"""
        try:
            url = f"{self.infobip_base_url}/sms/2/text/advanced"
            
            headers = {
                'Authorization': f'App {self.infobip_api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            data = {
                'messages': [
                    {
                        'destinations': [{'to': phone_number}],
                        'from': self.infobip_sender_id,
                        'text': message
                    }
                ]
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'provider': 'infobip',
                    'message_id': result.get('messages', [{}])[0].get('messageId'),
                    'status': 'SENT'
                }
            else:
                return {
                    'success': False,
                    'provider': 'infobip',
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'provider': 'infobip',
                'error': str(e)
            }
    
    def _send_africastalking_sms(self, phone_number: str, message: str) -> Dict:
        """Send SMS via Africa's Talking"""
        try:
            url = "https://api.africastalking.com/version1/messaging"
            
            headers = {
                'apiKey': self.africastalking_api_key,
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            data = {
                'username': self.africastalking_username,
                'to': phone_number,
                'message': message,
                'from': self.africastalking_sender_id
            }
            
            response = requests.post(url, headers=headers, data=data, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                return {
                    'success': True,
                    'provider': 'africastalking',
                    'message_id': result.get('SMSMessageData', {}).get('Recipients', [{}])[0].get('messageId'),
                    'status': 'SENT'
                }
            else:
                return {
                    'success': False,
                    'provider': 'africastalking',
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'provider': 'africastalking',
                'error': str(e)
            }

class WhatsAppService:
    """WhatsApp service using Twilio"""
    
    def __init__(self):
        self.twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.whatsapp_phone_number_id = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
        self.enabled = bool(self.twilio_account_sid and self.whatsapp_phone_number_id)
    
    def send_whatsapp(self, phone_number: str, message: str) -> Dict:
        """Send WhatsApp message via Twilio"""
        if not self.enabled:
            return {'success': False, 'error': 'WhatsApp service not configured'}
        
        try:
            url = f"https://graph.facebook.com/v17.0/{self.whatsapp_phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.twilio_auth_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'messaging_product': 'whatsapp',
                'to': phone_number,
                'type': 'text',
                'text': {'body': message}
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'provider': 'whatsapp',
                    'message_id': result.get('messages', [{}])[0].get('id'),
                    'status': 'SENT'
                }
            else:
                return {
                    'success': False,
                    'provider': 'whatsapp',
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'provider': 'whatsapp',
                'error': str(e)
            }

class EmailService:
    """Enhanced email service with multiple backends"""
    
    def __init__(self):
        self.default_from_email = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@videgrenierkamer.com')
        self.admin_email = os.environ.get('ADMIN_EMAIL', 'admin@videgrenierkamer.com')
    
    def send_email(self, to_email: str, subject: str, message: str, html_message: str = None) -> Dict:
        """Send email using Django's email backend"""
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=self.default_from_email,
                recipient_list=[to_email],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Email sent successfully to {to_email}")
            return {
                'success': True,
                'provider': 'django_email',
                'to': to_email,
                'subject': subject
            }
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return {
                'success': False,
                'provider': 'django_email',
                'error': str(e)
            }
    
    def send_template_email(self, to_email: str, template_name: str, context: Dict) -> Dict:
        """Send email using template"""
        try:
            # Render email templates
            subject = render_to_string(f'emails/{template_name}_subject.txt', context).strip()
            text_message = render_to_string(f'emails/{template_name}.txt', context)
            html_message = render_to_string(f'emails/{template_name}.html', context)
            
            return self.send_email(to_email, subject, text_message, html_message)
            
        except Exception as e:
            logger.error(f"Error sending template email to {to_email}: {str(e)}")
            return {
                'success': False,
                'provider': 'django_email',
                'error': str(e)
            }

class SmartNotificationEngine:
    """
    AI-powered notification system with:
    - Behavior-triggered notifications
    - Smart timing optimization
    - Multi-channel delivery
    - Personalization
    - A/B testing
    """
    
    def __init__(self):
        self.sms_service = SMSService()
        self.whatsapp_service = WhatsAppService()
        self.email_service = EmailService()
        
        self.delivery_channels = {
            'IN_APP': self._deliver_in_app,
            'EMAIL': self._deliver_email,
            'SMS': self._deliver_sms,
            'WHATSAPP': self._deliver_whatsapp
        }
        
        # User activity patterns for optimal timing
        self.optimal_send_hours = {
            'morning': (8, 10),
            'lunch': (12, 13),
            'evening': (18, 20),
            'night': (20, 22)
        }
    
    def trigger_notification(self, template_name: str, user: User, context: Dict,
                           preferred_channels: List[str] = None, priority: str = 'NORMAL'):
        """
        Trigger a smart notification with optimal timing and channel selection
        """
        try:
            template = NotificationTemplate.objects.get(
                name=template_name,
                is_active=True
            )
            
            # Check if user should receive this notification
            if not self._should_send_notification(user, template, context):
                return False
            
            # Determine optimal delivery channels
            channels = preferred_channels or self._select_optimal_channels(user, template)
            
            # Calculate optimal send time
            send_time = self._calculate_optimal_send_time(user, template, priority)
            
            # Create notifications for each channel
            for channel in channels:
                self._create_notification(user, template, context, channel, send_time)
            
            return True
            
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Notification template '{template_name}' not found")
            return False
        except Exception as e:
            logger.error(f"Error triggering notification: {e}")
            return False
    
    def _should_send_notification(self, user: User, template: NotificationTemplate, 
                                context: Dict) -> bool:
        """
        Determine if notification should be sent based on conditions and user preferences
        """
        try:
            # Check user notification preferences
            if hasattr(user, 'notification_preferences'):
                prefs = user.notification_preferences
                if not prefs.get(template.notification_type.lower(), True):
                    return False
            
            # Check frequency limits
            recent_count = SmartNotification.objects.filter(
                user=user,
                template=template,
                sent_at__gte=timezone.now() - timedelta(days=1)
            ).count()
            
            max_daily = template.trigger_conditions.get('max_daily', 3)
            if recent_count >= max_daily:
                return False
            
            # Check target audience criteria
            if not self._matches_target_audience(user, template.target_audience):
                return False
            
            # Check specific trigger conditions
            return self._check_trigger_conditions(user, template.trigger_conditions, context)
            
        except Exception as e:
            logger.error(f"Error checking notification conditions: {e}")
            return False
    
    def _matches_target_audience(self, user: User, target_criteria: Dict) -> bool:
        """
        Check if user matches target audience criteria
        """
        try:
            # User type filter
            if 'user_types' in target_criteria:
                if user.user_type not in target_criteria['user_types']:
                    return False
            
            # Loyalty level filter
            if 'loyalty_levels' in target_criteria:
                if user.loyalty_level not in target_criteria['loyalty_levels']:
                    return False
            
            # City filter
            if 'cities' in target_criteria:
                if user.city not in target_criteria['cities']:
                    return False
            
            # Activity level filter
            if 'activity_level' in target_criteria:
                recent_activity = UserBehavior.objects.filter(
                    user=user,
                    created_at__gte=timezone.now() - timedelta(days=7)
                ).count()
                
                min_activity = target_criteria['activity_level'].get('min', 0)
                max_activity = target_criteria['activity_level'].get('max', 1000)
                
                if not (min_activity <= recent_activity <= max_activity):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error matching target audience: {e}")
            return False
    
    def _check_trigger_conditions(self, user: User, conditions: Dict, context: Dict) -> bool:
        """
        Check specific trigger conditions for the notification
        """
        try:
            condition_type = conditions.get('type')
            
            if condition_type == 'price_drop':
                return self._check_price_drop_condition(user, conditions, context)
            elif condition_type == 'back_in_stock':
                return self._check_stock_condition(user, conditions, context)
            elif condition_type == 'abandoned_cart':
                return self._check_abandoned_cart_condition(user, conditions, context)
            elif condition_type == 'recommendation':
                return self._check_recommendation_condition(user, conditions, context)
            elif condition_type == 'milestone':
                return self._check_milestone_condition(user, conditions, context)
            
            return True  # Default to true if no specific conditions
            
        except Exception as e:
            logger.error(f"Error checking trigger conditions: {e}")
            return False
    
    def _check_price_drop_condition(self, user: User, conditions: Dict, context: Dict) -> bool:
        """Check price drop notification conditions"""
        try:
            product = context.get('product')
            if not product:
                return False
            
            # Check if user has this product in wishlist
            wishlist_item = WishlistItem.objects.filter(
                wishlist__user=user,
                product=product
            ).first()
            
            if not wishlist_item:
                return False
            
            # Check if price dropped below threshold
            if wishlist_item.price_alert_threshold:
                return product.price <= wishlist_item.price_alert_threshold
            
            # Default: any price drop
            min_drop_percentage = conditions.get('min_drop_percentage', 10)
            old_price = context.get('old_price', product.price)
            drop_percentage = ((old_price - product.price) / old_price) * 100
            
            return drop_percentage >= min_drop_percentage
            
        except Exception as e:
            logger.error(f"Error checking price drop condition: {e}")
            return False
    
    def _check_abandoned_cart_condition(self, user: User, conditions: Dict, context: Dict) -> bool:
        """Check abandoned cart notification conditions"""
        try:
            from .models_advanced import ShoppingCart
            
            # Check if user has items in cart
            cart = ShoppingCart.objects.filter(user=user).first()
            if not cart or not cart.items.exists():
                return False
            
            # Check how long cart has been abandoned
            last_activity = cart.updated_at
            hours_abandoned = conditions.get('hours_abandoned', 24)
            
            return (timezone.now() - last_activity).total_seconds() >= hours_abandoned * 3600
            
        except Exception as e:
            logger.error(f"Error checking abandoned cart condition: {e}")
            return False
    
    def _select_optimal_channels(self, user: User, template: NotificationTemplate) -> List[str]:
        """
        Select optimal delivery channels based on user preferences and template type
        """
        try:
            channels = []
            
            # Priority channels based on notification type
            priority_channels = {
                'PRICE_DROP': ['SMS', 'EMAIL'],
                'BACK_IN_STOCK': ['SMS', 'EMAIL'],
                'NEW_SIMILAR': ['IN_APP', 'EMAIL'],
                'PROMOTION': ['EMAIL', 'IN_APP'],
                'REMINDER': ['SMS', 'IN_APP'],
                'MILESTONE': ['IN_APP', 'EMAIL']
            }
            
            default_channels = priority_channels.get(
                template.notification_type,
                ['IN_APP', 'EMAIL']
            )
            
            # Check user's channel preferences and availability
            for channel in default_channels:
                if self._is_channel_available_for_user(user, channel):
                    channels.append(channel)
            
            # Always include in-app as fallback
            if 'IN_APP' not in channels:
                channels.append('IN_APP')
            
            return channels[:2]  # Limit to 2 channels to avoid spam
            
        except Exception as e:
            logger.error(f"Error selecting optimal channels: {e}")
            return ['IN_APP']
    
    def _is_channel_available_for_user(self, user: User, channel: str) -> bool:
        """Check if delivery channel is available for user"""
        try:
            if channel == 'EMAIL':
                return bool(user.email)
            elif channel == 'SMS':
                return bool(user.phone and user.phone_verified)
            elif channel == 'WHATSAPP':
                return bool(user.phone)
            elif channel == 'IN_APP':
                return True  # Always available
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking channel availability: {e}")
            return False
    
    def _calculate_optimal_send_time(self, user: User, template: NotificationTemplate,
                                   priority: str) -> datetime:
        """
        Calculate optimal send time based on user behavior patterns
        """
        try:
            now = timezone.now()
            
            # Immediate delivery for urgent notifications
            if priority == 'URGENT':
                return now
            
            # Get user's activity patterns
            user_activity = self._analyze_user_activity_patterns(user)
            optimal_hour = user_activity.get('peak_hour', 19)  # Default to 7 PM
            
            # Calculate next optimal send time
            optimal_time = now.replace(
                hour=optimal_hour,
                minute=0,
                second=0,
                microsecond=0
            )
            
            # If optimal time has passed today, schedule for tomorrow
            if optimal_time <= now:
                optimal_time += timedelta(days=1)
            
            # Don't send too late or too early
            if optimal_time.hour < 8:
                optimal_time = optimal_time.replace(hour=9)
            elif optimal_time.hour > 21:
                optimal_time = optimal_time.replace(hour=19)
            
            return optimal_time
            
        except Exception as e:
            logger.error(f"Error calculating optimal send time: {e}")
            return timezone.now()
    
    def _analyze_user_activity_patterns(self, user: User) -> Dict:
        """
        Analyze user activity patterns to determine optimal notification timing
        """
        try:
            # Get user behavior in different hours
            behaviors = UserBehavior.objects.filter(
                user=user,
                created_at__gte=timezone.now() - timedelta(days=30)
            ).extra(
                select={'hour': 'EXTRACT(hour FROM created_at)'}
            ).values('hour').annotate(
                count=Count('id')
            ).order_by('-count')
            
            if behaviors:
                peak_hour = int(behaviors[0]['hour'])
                return {
                    'peak_hour': peak_hour,
                    'activity_distribution': list(behaviors)
                }
            
            # Default pattern if no data
            return {
                'peak_hour': 19,  # 7 PM default
                'activity_distribution': []
            }
            
        except Exception as e:
            logger.error(f"Error analyzing user activity patterns: {e}")
            return {'peak_hour': 19}
    
    def _create_notification(self, user: User, template: NotificationTemplate,
                           context: Dict, channel: str, send_time: datetime):
        """
        Create notification record in database
        """
        try:
            # Render notification content
            title = self._render_template(template.title_template, context)
            message = self._render_template(template.message_template, context)
            
            notification = SmartNotification.objects.create(
                user=user,
                template=template,
                delivery_method=channel,
                title=title,
                message=message,
                data=context,
                scheduled_for=send_time
            )
            
            # Schedule delivery
            if send_time <= timezone.now() + timedelta(minutes=1):
                # Send immediately
                self._deliver_notification(notification)
            else:
                # Schedule for later (would use Celery in production)
                if CELERY_AVAILABLE:
                    schedule_notification_delivery.apply_async(
                        args=[notification.id],
                        eta=send_time
                    )
                else:
                    # Fallback for development
                    logger.info(f"Notification scheduled for {send_time}: {notification.id}")
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
    
    def _render_template(self, template: str, context: Dict) -> str:
        """
        Render notification template with context
        """
        try:
            # Simple template rendering (can be enhanced with Django templates)
            rendered = template
            for key, value in context.items():
                placeholder = f"{{{{{key}}}}}"
                rendered = rendered.replace(placeholder, str(value))
            
            return rendered
            
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            return template
    
    def _deliver_notification(self, notification: SmartNotification):
        """
        Deliver notification through specified channel
        """
        try:
            channel = notification.delivery_method
            delivery_func = self.delivery_channels.get(channel)
            
            if delivery_func:
                success = delivery_func(notification)
                
                if success:
                    notification.status = 'SENT'
                    notification.sent_at = timezone.now()
                else:
                    notification.status = 'FAILED'
                
                notification.save()
            else:
                logger.error(f"Unknown delivery channel: {channel}")
                
        except Exception as e:
            logger.error(f"Error delivering notification: {e}")
    
    def _deliver_in_app(self, notification: SmartNotification) -> bool:
        """Deliver in-app notification"""
        try:
            # Create in-app notification record
            from .models import Notification
            
            Notification.objects.create(
                user=notification.user,
                title=notification.title,
                message=notification.message,
                notification_type='SYSTEM',
                data=notification.data
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error delivering in-app notification: {e}")
            return False
    
    def _deliver_email(self, notification: SmartNotification) -> bool:
        """Deliver email notification"""
        try:
            template = notification.template
            
            subject = template.email_subject_template or notification.title
            
            # Render email body
            if template.email_body_template:
                body = self._render_template(template.email_body_template, notification.data)
            else:
                body = notification.message
            
            result = self.email_service.send_email(
                notification.user.email,
                subject,
                body
            )
            
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"Error delivering email notification: {e}")
            return False
    
    def _deliver_sms(self, notification: SmartNotification) -> bool:
        """Deliver SMS notification"""
        try:
            template = notification.template
            
            # Use SMS template if available, otherwise truncate message
            if template.sms_template:
                message = self._render_template(template.sms_template, notification.data)
            else:
                message = notification.message[:160]  # SMS character limit
            
            result = self.sms_service.send_sms(notification.user.phone, message)
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"Error delivering SMS notification: {e}")
            return False
    
    def _deliver_whatsapp(self, notification: SmartNotification) -> bool:
        """Deliver WhatsApp notification"""
        try:
            template = notification.template
            
            # Use WhatsApp template if available, otherwise use message
            if template.whatsapp_template:
                message = self._render_template(template.whatsapp_template, notification.data)
            else:
                message = f"*{notification.title}*\n\n{notification.message}"
            
            result = self.whatsapp_service.send_whatsapp(notification.user.phone, message)
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"Error delivering WhatsApp notification: {e}")
            return False
    
    def create_notification_templates(self):
        """
        Create default notification templates
        """
        templates = [
            {
                'name': 'price_drop_alert',
                'notification_type': 'PRICE_DROP',
                'title_template': '💰 Prix Réduit: {{product_name}}',
                'message_template': 'Le prix de {{product_name}} a baissé de {{old_price}} à {{new_price}} FCFA! Achetez maintenant avant que ça ne parte.',
                'email_subject_template': 'Alerte Prix: {{product_name}} - Économisez {{savings}} FCFA',
                'email_body_template': '''
                Bonjour {{user_name}},
                
                Bonne nouvelle! Le produit que vous suivez a baissé de prix:
                
                📦 {{product_name}}
                💰 Ancien prix: {{old_price}} FCFA
                🎉 Nouveau prix: {{new_price}} FCFA
                💵 Vous économisez: {{savings}} FCFA
                
                Achetez maintenant: {{product_url}}
                ''',
                'sms_template': 'Prix réduit! {{product_name}}: {{new_price}} FCFA (était {{old_price}}). Voir: {{short_url}}',
                'whatsapp_template': '💰 *Prix Réduit!*\n\n{{product_name}}\n\n💵 Nouveau prix: {{new_price}} FCFA\n💸 Ancien prix: {{old_price}} FCFA\n💎 Économies: {{savings}} FCFA\n\nAchetez maintenant: {{product_url}}',
                'trigger_conditions': {
                    'type': 'price_drop',
                    'min_drop_percentage': 10,
                    'max_daily': 2
                }
            },
            {
                'name': 'back_in_stock',
                'notification_type': 'BACK_IN_STOCK',
                'title_template': '🔥 De retour en stock: {{product_name}}',
                'message_template': '{{product_name}} est de nouveau disponible! Dépêchez-vous, quantité limitée.',
                'sms_template': '🔥 {{product_name}} est de retour en stock! Quantité limitée. Voir: {{short_url}}',
                'whatsapp_template': '🔥 *De retour en stock!*\n\n{{product_name}}\n\n⚠️ Quantité limitée\n\nAchetez maintenant: {{product_url}}',
                'trigger_conditions': {
                    'type': 'back_in_stock',
                    'max_daily': 1
                }
            },
            {
                'name': 'abandoned_cart',
                'notification_type': 'REMINDER',
                'title_template': '🛒 Vous avez oublié quelque chose!',
                'message_template': 'Votre panier contient {{item_count}} article(s) pour {{total_amount}} FCFA. Terminez votre achat maintenant!',
                'sms_template': '🛒 Votre panier vous attend! {{item_count}} article(s) pour {{total_amount}} FCFA. Terminez votre achat: {{short_url}}',
                'whatsapp_template': '🛒 *Votre panier vous attend!*\n\n📦 {{item_count}} article(s)\n💵 Total: {{total_amount}} FCFA\n\nTerminez votre achat: {{product_url}}',
                'trigger_conditions': {
                    'type': 'abandoned_cart',
                    'hours_abandoned': 24,
                    'max_daily': 1
                }
            },
            {
                'name': 'ai_recommendation',
                'notification_type': 'RECOMMENDATION',
                'title_template': '✨ Recommandé pour vous',
                'message_template': 'Découvrez {{product_name}} à {{price}} FCFA. {{reason}}',
                'sms_template': '✨ {{product_name}} à {{price}} FCFA - Recommandé pour vous! Voir: {{short_url}}',
                'whatsapp_template': '✨ *Recommandé pour vous*\n\n{{product_name}}\n💵 {{price}} FCFA\n\n{{reason}}\n\nVoir: {{product_url}}',
                'trigger_conditions': {
                    'type': 'recommendation',
                    'min_confidence': 0.7,
                    'max_daily': 3
                }
            },
            {
                'name': 'loyalty_milestone',
                'notification_type': 'MILESTONE',
                'title_template': '🎉 Félicitations! Nouveau niveau atteint',
                'message_template': 'Vous venez d\'atteindre le niveau {{new_level}}! Débloquez de nouveaux avantages.',
                'sms_template': '🎉 Félicitations! Vous avez atteint le niveau {{new_level}}! Nouveaux avantages débloqués.',
                'whatsapp_template': '🎉 *Félicitations!*\n\nVous avez atteint le niveau *{{new_level}}*!\n\n✨ Nouveaux avantages débloqués',
                'trigger_conditions': {
                    'type': 'milestone',
                    'max_daily': 1
                }
            }
        ]
        
        for template_data in templates:
            template, created = NotificationTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            if created:
                logger.info(f"Created notification template: {template.name}")

# Celery task for scheduled notifications
@shared_task
def schedule_notification_delivery(notification_id):
    """
    Celery task to deliver scheduled notifications
    """
    try:
        notification = SmartNotification.objects.get(id=notification_id)
        engine = SmartNotificationEngine()
        engine._deliver_notification(notification)
        
    except SmartNotification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
    except Exception as e:
        logger.error(f"Error in scheduled notification delivery: {e}")

# Singleton instances
smart_notifications = SmartNotificationEngine()
sms_service = SMSService()
whatsapp_service = WhatsAppService()
email_service = EmailService()

# Utility functions
def send_sms_notification(phone_number: str, message: str) -> Dict:
    """Send SMS notification using available providers"""
    return sms_service.send_sms(phone_number, message)

def send_whatsapp_notification(phone_number: str, message: str) -> Dict:
    """Send WhatsApp notification"""
    return whatsapp_service.send_whatsapp(phone_number, message)

def send_email_notification(to_email: str, subject: str, message: str, html_message: str = None) -> Dict:
    """Send email notification"""
    return email_service.send_email(to_email, subject, message, html_message)

def send_template_email_notification(to_email: str, template_name: str, context: Dict) -> Dict:
    """Send email notification using template"""
    return email_service.send_template_email(to_email, template_name, context) 