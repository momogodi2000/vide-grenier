

# backend/middleware.py - ENHANCED MIDDLEWARE FOR VGK
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
import logging
import time
import json
from django.db import models
import settings

logger = logging.getLogger(__name__)

class UserBehaviorTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track user behavior for AI recommendations
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        # Record request start time
        request.start_time = time.time()
        
        # Get or create session ID
        if not request.session.session_key:
            request.session.create()
        
        request.behavior_data = {
            'session_id': request.session.session_key,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': self.get_client_ip(request),
            'referrer': request.META.get('HTTP_REFERER', ''),
            'start_time': request.start_time
        }
    
    def process_response(self, request, response):
        # Skip tracking for non-authenticated users on certain paths
        if isinstance(request.user, AnonymousUser):
            skip_paths = ['/admin/', '/api/', '/static/', '/media/']
            if any(request.path.startswith(path) for path in skip_paths):
                return response
        
        # Calculate page duration
        duration = int((time.time() - getattr(request, 'start_time', time.time())) * 1000)
        
        # Track page view if it's a product page
        if request.path.startswith('/product/') and response.status_code == 200:
            self.track_product_view(request, duration)
        
        # Track search behavior
        if 'search' in request.path and request.GET.get('q'):
            self.track_search_behavior(request, duration)
        
        return response
    
    def track_product_view(self, request, duration):
        """Track product page views"""
        try:
            from .ai_engine import ai_engine
            from .models import Product
            
            # Extract product ID from URL
            path_parts = request.path.strip('/').split('/')
            if len(path_parts) >= 2:
                product_slug = path_parts[-1]
                
                try:
                    product = Product.objects.get(slug=product_slug)
                    
                    # Track behavior if user is authenticated
                    if not isinstance(request.user, AnonymousUser):
                        ai_engine.track_user_behavior(
                            user=request.user,
                            action_type='VIEW',
                            product=product,
                            category=product.category,
                            session_id=request.behavior_data['session_id'],
                            duration=duration,
                            metadata={
                                'user_agent': request.behavior_data['user_agent'],
                                'referrer': request.behavior_data['referrer'],
                                'ip_address': request.behavior_data['ip_address']
                            }
                        )
                    
                    # Update product view count
                    Product.objects.filter(id=product.id).update(
                        views_count=models.F('views_count') + 1
                    )
                    
                except Product.DoesNotExist:
                    pass
                
        except Exception as e:
            logger.error(f"Error tracking product view: {e}")
    
    def track_search_behavior(self, request, duration):
        """Track search behavior"""
        try:
            from .ai_engine import ai_engine
            
            search_query = request.GET.get('q', '')
            filters = {
                'category': request.GET.get('category', ''),
                'min_price': request.GET.get('min_price', ''),
                'max_price': request.GET.get('max_price', ''),
                'city': request.GET.get('city', ''),
                'condition': request.GET.get('condition', '')
            }
            
            if not isinstance(request.user, AnonymousUser) and search_query:
                ai_engine.track_user_behavior(
                    user=request.user,
                    action_type='SEARCH',
                    session_id=request.behavior_data['session_id'],
                    duration=duration,
                    metadata={
                        'search_query': search_query,
                        'filters': filters,
                        'user_agent': request.behavior_data['user_agent']
                    }
                )
                
        except Exception as e:
            logger.error(f"Error tracking search behavior: {e}")
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SmartNotificationMiddleware(MiddlewareMixin):
    """
    Middleware to handle smart notification triggers and delivery
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_response(self, request, response):
        # Skip for AJAX requests and non-authenticated users
        if request.is_ajax() or isinstance(request.user, AnonymousUser):
            return response
        
        # Check for notification triggers based on user actions
        if response.status_code == 200:
            self.check_notification_triggers(request, response)
        
        return response
    
    def check_notification_triggers(self, request, response):
        """Check for various notification triggers"""
        try:
            # Abandoned cart check
            if request.path == '/cart/' and 'checkout' not in request.path:
                self.check_abandoned_cart(request.user)
            
            # Product view frequency check
            if request.path.startswith('/product/'):
                self.check_recommendation_trigger(request.user)
            
            # Price drop alerts check
            self.check_price_drop_alerts(request.user)
            
        except Exception as e:
            logger.error(f"Error checking notification triggers: {e}")
    
    def check_abandoned_cart(self, user):
        """Check for abandoned cart and trigger notification"""
        try:
            from .models_advanced import ShoppingCart
            from .smart_notifications import smart_notifications
            
            cart = ShoppingCart.objects.filter(user=user).first()
            if cart and cart.items.exists():
                # Check if cart was last updated more than 24 hours ago
                hours_since_update = (timezone.now() - cart.updated_at).total_seconds() / 3600
                
                if hours_since_update >= 24:
                    smart_notifications.trigger_notification(
                        template_name='abandoned_cart',
                        user=user,
                        context={
                            'item_count': cart.total_items,
                            'total_amount': cart.total_amount,
                            'cart_url': '/cart/'
                        },
                        preferred_channels=['PUSH', 'EMAIL']
                    )
                    
        except Exception as e:
            logger.error(f"Error checking abandoned cart: {e}")
    
    def check_recommendation_trigger(self, user):
        """Check if user should receive AI recommendations"""
        try:
            from .models_advanced import UserBehavior, ProductRecommendation
            from .smart_notifications import smart_notifications
            
            # Check if user has viewed 5+ products without recommendations today
            today_views = UserBehavior.objects.filter(
                user=user,
                action_type='VIEW',
                created_at__date=timezone.now().date()
            ).count()
            
            today_recommendations = ProductRecommendation.objects.filter(
                user=user,
                created_at__date=timezone.now().date()
            ).count()
            
            if today_views >= 5 and today_recommendations == 0:
                # Generate and send recommendations
                from .ai_engine import ai_engine
                recommendations = ai_engine.generate_recommendations_for_user(user, 3)
                
                if recommendations:
                    smart_notifications.trigger_notification(
                        template_name='ai_recommendation',
                        user=user,
                        context={
                            'product_name': recommendations[0]['product'].title,
                            'price': recommendations[0]['product'].price,
                            'reason': recommendations[0]['reason'],
                            'recommendations_url': '/recommendations/'
                        },
                        preferred_channels=['IN_APP', 'PUSH']
                    )
                    
        except Exception as e:
            logger.error(f"Error checking recommendation trigger: {e}")
    
    def check_price_drop_alerts(self, user):
        """Check for price drop alerts"""
        try:
            from .models_advanced import WishlistItem
            from .smart_notifications import smart_notifications
            
            # Check wishlist items with price alerts
            alert_items = WishlistItem.objects.filter(
                wishlist__user=user,
                price_alert_threshold__isnull=False,
                product__price__lte=models.F('price_alert_threshold')
            ).select_related('product')
            
            for item in alert_items:
                smart_notifications.trigger_notification(
                    template_name='price_drop_alert',
                    user=user,
                    context={
                        'product_name': item.product.title,
                        'old_price': item.price_alert_threshold,
                        'new_price': item.product.price,
                        'savings': item.price_alert_threshold - item.product.price,
                        'product_url': f'/product/{item.product.slug}/'
                    },
                    preferred_channels=['PUSH', 'EMAIL', 'SMS']
                )
                
                # Clear the alert to avoid duplicate notifications
                item.price_alert_threshold = None
                item.save()
                
        except Exception as e:
            logger.error(f"Error checking price drop alerts: {e}")


class SecurityMiddleware(MiddlewareMixin):
    """
    Enhanced security middleware
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.failed_attempts = {}
        super().__init__(get_response)
    
    def process_request(self, request):
        # Rate limiting for login attempts
        if request.path == '/auth/login/' and request.method == 'POST':
            client_ip = self.get_client_ip(request)
            
            if self.is_rate_limited(client_ip):
                return JsonResponse({
                    'error': 'Trop de tentatives de connexion. Veuillez réessayer plus tard.'
                }, status=429)
    
    def process_response(self, request, response):
        # Track failed login attempts
        if (request.path == '/auth/login/' and 
            request.method == 'POST' and 
            response.status_code == 400):
            
            client_ip = self.get_client_ip(request)
            self.record_failed_attempt(client_ip)
        
        # Clear failed attempts on successful login
        elif (request.path == '/auth/login/' and 
              request.method == 'POST' and 
              response.status_code == 200):
            
            client_ip = self.get_client_ip(request)
            self.clear_failed_attempts(client_ip)
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_rate_limited(self, ip):
        """Check if IP is rate limited"""
        if ip not in self.failed_attempts:
            return False
        
        attempts, last_attempt = self.failed_attempts[ip]
        
        # Reset if last attempt was more than 1 hour ago
        if (timezone.now() - last_attempt).total_seconds() > 3600:
            del self.failed_attempts[ip]
            return False
        
        # Rate limit after 5 failed attempts
        return attempts >= 5
    
    def record_failed_attempt(self, ip):
        """Record a failed login attempt"""
        if ip not in self.failed_attempts:
            self.failed_attempts[ip] = [0, timezone.now()]
        
        self.failed_attempts[ip][0] += 1
        self.failed_attempts[ip][1] = timezone.now()
    
    def clear_failed_attempts(self, ip):
        """Clear failed attempts for IP"""
        if ip in self.failed_attempts:
            del self.failed_attempts[ip]


class APIThrottleMiddleware(MiddlewareMixin):
    """
    API request throttling middleware
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.api_requests = {}
        super().__init__(get_response)
    
    def process_request(self, request):
        # Only apply to API endpoints
        if not request.path.startswith('/api/'):
            return None
        
        client_ip = self.get_client_ip(request)
        current_minute = int(time.time() / 60)
        
        # Initialize or update request count
        if client_ip not in self.api_requests:
            self.api_requests[client_ip] = {}
        
        if current_minute not in self.api_requests[client_ip]:
            self.api_requests[client_ip][current_minute] = 0
        
        self.api_requests[client_ip][current_minute] += 1
        
        # Clean old entries (older than 1 minute)
        old_minutes = [minute for minute in self.api_requests[client_ip] 
                      if minute < current_minute - 1]
        for old_minute in old_minutes:
            del self.api_requests[client_ip][old_minute]
        
        # Check rate limit (100 requests per minute)
        if self.api_requests[client_ip][current_minute] > 100:
            return JsonResponse({
                'error': 'Rate limit exceeded. Try again later.'
            }, status=429)
        
        return None
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Performance monitoring middleware
    """
    
    def process_request(self, request):
        request.start_time = time.time()
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log slow requests (>2 seconds)
            if duration > 2.0:
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.2f}s"
                )
            
            # Add performance header for development
            if settings.DEBUG:
                response['X-Response-Time'] = f"{duration:.3f}s"
        
        return response


