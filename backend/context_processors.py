

# backend/context_processors.py
from django.conf import settings
from django.db.models import Q
from .models import Notification, Message, Chat, Category


def global_context(request):
    """Context processor pour ajouter des variables globales aux templates"""
    from django.utils import timezone
    
    context = {
        'VGK_SETTINGS': settings.VGK_SETTINGS,
        'SITE_NAME': 'Vidé-Grenier Kamer',
        'SITE_TAGLINE': 'Vendez, Achetez, Économisez – Simplicité et Sécurité',
        'CURRENT_YEAR': timezone.now().year,
        'MAIN_CATEGORIES': Category.objects.filter(
            parent=None, is_active=True
        ).order_by('order')[:6],
        'SUPPORTED_CITIES': {city: None for city in settings.VGK_SETTINGS['SUPPORTED_CITIES']} if isinstance(settings.VGK_SETTINGS.get('SUPPORTED_CITIES'), list) else {},
        'PICKUP_POINTS': settings.VGK_SETTINGS.get('PICKUP_POINTS', {}),
    }
    
    if request.user.is_authenticated:
        # Notifications non lues
        context['unread_notifications_count'] = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
        
        context['recent_notifications'] = Notification.objects.filter(
            user=request.user, is_read=False
        ).order_by('-created_at')[:5]
        
        # Messages non lus
        user_chats = Chat.objects.filter(
            Q(buyer=request.user) | Q(seller=request.user)
        )
        
        unread_messages_count = Message.objects.filter(
            chat__in=user_chats,
            is_read=False
        ).exclude(sender=request.user).count()
        
        context['unread_messages_count'] = unread_messages_count
        
        # Produits favoris
        context['favorites_count'] = request.user.favorites.count()
        
        # Niveau de fidélité
        context['user_loyalty_level'] = request.user.loyalty_level
        
        # Informations du profil utilisateur
        context['user_profile'] = {
            'completion_rate': calculate_profile_completion(request.user),
            'needs_phone_verification': not request.user.phone_verified,
            'needs_email_verification': not request.user.is_verified,
        }
    
    return context


def calculate_profile_completion(user):
    """Calculer le pourcentage de completion du profil"""
    fields_to_check = [
        'first_name', 'last_name', 'phone', 'city', 
        'address', 'profile_picture'
    ]
    
    completed_fields = 0
    total_fields = len(fields_to_check)
    
    for field in fields_to_check:
        value = getattr(user, field, None)
        if value:
            completed_fields += 1
    
    # Bonus pour les vérifications
    if user.is_verified:
        completed_fields += 0.5
    if user.phone_verified:
        completed_fields += 0.5
    
    total_fields += 1  # Ajouter 1 pour les vérifications
    
    completion_rate = (completed_fields / total_fields) * 100
    return min(100, completion_rate)

