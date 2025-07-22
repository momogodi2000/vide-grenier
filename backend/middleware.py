

# backend/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from .utils import get_client_ip, track_analytics


class VGKAnalyticsMiddleware(MiddlewareMixin):
    """Middleware pour tracker les analytics automatiquement"""
    
    def process_request(self, request):
        # Ajouter des informations utiles au request
        request.client_ip = get_client_ip(request)
        request.start_time = timezone.now()
        
        return None
    
    def process_response(self, request, response):
        # Tracker les vues de pages pour les requêtes GET réussies
        if (request.method == 'GET' and 
            response.status_code == 200 and 
            not request.path.startswith('/admin/') and
            not request.path.startswith('/static/') and
            not request.path.startswith('/media/')):
            
            track_analytics(
                user=request.user if hasattr(request, 'user') and request.user.is_authenticated else None,
                metric_type='PAGE_VIEW',
                request=request,
                data={
                    'response_time': (timezone.now() - request.start_time).total_seconds() if hasattr(request, 'start_time') else None,
                    'status_code': response.status_code
                }
            )
        
        return response


class UserActivityMiddleware(MiddlewareMixin):
    """Middleware pour mettre à jour la dernière activité utilisateur"""
    
    def process_request(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Mettre à jour last_activity toutes les 5 minutes pour éviter trop de writes
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            last_activity = request.user.last_activity
            now = timezone.now()
            
            if not last_activity or (now - last_activity).seconds > 300:  # 5 minutes
                User.objects.filter(id=request.user.id).update(last_activity=now)
        
        return None


