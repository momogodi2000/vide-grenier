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
# Make celery optional to avoid dependency issues during development
try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    # Fallback decorator when celery is not available
    CELERY_AVAILABLE = False
    def shared_task(func):
        return func
import requests

from .models import User, Product, Order
from .models_advanced import (
    SmartNotification, NotificationTemplate, UserBehavior,
    UserPreference, WishlistItem
)
from .utils import send_sms_notification

logger = logging.getLogger(__name__)

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
        self.delivery_channels = {
            'IN_APP': self._deliver_in_app,
            'EMAIL': self._deliver_email,
            'SMS': self._deliver_sms,
            'PUSH': self._deliver_push,
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
                'PRICE_DROP': ['PUSH', 'EMAIL'],
                'BACK_IN_STOCK': ['PUSH', 'SMS'],
                'NEW_SIMILAR': ['IN_APP', 'EMAIL'],
                'PROMOTION': ['EMAIL', 'IN_APP'],
                'REMINDER': ['PUSH', 'IN_APP'],
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
            elif channel == 'PUSH':
                # Check if user has push subscription (would need to implement)
                return True  # Assume available for now
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
                schedule_notification_delivery.apply_async(
                    args=[notification.id],
                    eta=send_time
                )
            
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
            
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.user.email],
                fail_silently=False
            )
            
            return True
            
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
            
            return send_sms_notification(notification.user.phone, message)
            
        except Exception as e:
            logger.error(f"Error delivering SMS notification: {e}")
            return False
    
    def _deliver_push(self, notification: SmartNotification) -> bool:
        """Deliver push notification"""
        try:
            # Implement push notification delivery
            # This would integrate with services like Firebase, OneSignal, etc.
            
            # Placeholder implementation
            push_data = {
                'title': notification.title,
                'body': notification.message,
                'data': notification.data,
                'user_id': str(notification.user.id)
            }
            
            # Would send to push service here
            logger.info(f"Push notification sent: {push_data}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error delivering push notification: {e}")
            return False
    
    def _deliver_whatsapp(self, notification: SmartNotification) -> bool:
        """Deliver WhatsApp notification"""
        try:
            # Implement WhatsApp Business API integration
            # This would use services like Twilio, WhatsApp Business API, etc.
            
            message = f"*{notification.title}*\n\n{notification.message}"
            
            # Placeholder implementation
            logger.info(f"WhatsApp message sent to {notification.user.phone}: {message}")
            
            return True
            
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

# Singleton instance
smart_notifications = SmartNotificationEngine() 