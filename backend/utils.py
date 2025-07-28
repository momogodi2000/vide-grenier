# backend/utils.py
import requests
import json
import random
import string
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Notification
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


def send_sms_notification(phone_number, message):
    """Envoyer une notification SMS via différents fournisseurs"""
    providers = [
        ('orange', send_sms_orange),
        ('mtn', send_sms_mtn),
        ('twilio', send_sms_twilio)
    ]
    
    for provider_name, provider_func in providers:
        try:
            result = provider_func(phone_number, message)
            if result['success']:
                logger.info(f"SMS envoyé avec succès via {provider_name} à {phone_number}")
                return result
        except Exception as e:
            logger.error(f"Erreur SMS {provider_name}: {str(e)}")
            continue
    
    logger.error(f"Échec envoi SMS à {phone_number} - Tous les fournisseurs ont échoué")
    return {'success': False, 'error': 'Tous les fournisseurs SMS ont échoué'}


def send_sms_orange(phone_number, message):
    """Envoyer SMS via Orange Money API"""
    url = "https://api.orange.com/smsmessaging/v1/outbound/sms/send"
    headers = {
        'Authorization': f'Bearer {settings.ORANGE_MONEY_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'outboundSMSMessageRequest': {
            'address': [phone_number],
            'senderAddress': 'VGKamer',
            'outboundSMSTextMessage': {
                'message': message
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=10)
    
    if response.status_code == 200:
        return {'success': True, 'response': response.json()}
    else:
        return {'success': False, 'error': response.text}


def send_sms_mtn(phone_number, message):
    """Envoyer SMS via MTN API"""
    # Configuration factice - à adapter selon l'API MTN réelle
    url = "https://api.mtn.cm/sms/send"
    headers = {
        'Authorization': f'Bearer {settings.MTN_MONEY_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'to': phone_number,
        'from': 'VGKamer',
        'text': message
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            return {'success': True, 'response': response.json()}
        else:
            return {'success': False, 'error': response.text}
    except requests.RequestException as e:
        return {'success': False, 'error': str(e)}


def send_sms_twilio(phone_number, message):
    """Envoyer SMS via Twilio (fallback)"""
    # Configuration Twilio pour l'Afrique
    try:
        # Simuler l'envoi Twilio
        return {
            'success': True, 
            'response': {'sid': f'SM{random.randint(1000000, 9999999)}'}
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def send_email_notification(to_email, subject, template_name, context=None):
    """Envoyer une notification par email avec template"""
    import yagmail
    try:
        if context is None:
            context = {}
        context.update({
            'site_name': 'Vidé-Grenier Kamer',
            'site_url': 'https://vide-grenier-kamer.onrender.com',
            'support_email': 'support@videgrenier-kamer.com',
            'support_phone': '+237 694 63 84 12'
        })
        html_message = render_to_string(f'emails/{template_name}.html', context)
        text_message = render_to_string(f'emails/{template_name}.txt', context)
        try:
            yag = yagmail.SMTP(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            yag.send(
                to=to_email,
                subject=subject,
                contents=[text_message, html_message]
            )
            logger.info(f"Email envoyé avec succès à {to_email}")
            return {'success': True}
        except Exception as e:
            logger.error(f"Erreur yagmail envoi email à {to_email}: {str(e)}")
            # Optionally, fallback to Django send_mail
            try:
                send_mail(
                    subject=subject,
                    message=text_message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[to_email],
                    html_message=html_message,
                    fail_silently=False
                )
                logger.info(f"Email envoyé avec succès à {to_email} via fallback")
                return {'success': True, 'fallback': True}
            except Exception as e2:
                logger.error(f"Erreur fallback envoi email à {to_email}: {str(e2)}")
                return {'success': False, 'error': str(e2)}
    except Exception as e:
        logger.error(f"Erreur globale envoi email à {to_email}: {str(e)}")
        return {'success': False, 'error': str(e)}


def process_payment(order, payment_method):
    """Traiter un paiement selon la méthode choisie"""
    payment_processors = {
        'CAMPAY': process_campay_payment,
        'ORANGE_MONEY': process_orange_money_payment,
        'MTN_MONEY': process_mtn_money_payment,
        'NOUPIA': process_noupia_payment,
        'CARD': process_card_payment
    }
    
    processor = payment_processors.get(payment_method)
    if not processor:
        return {'success': False, 'error': 'Mode de paiement non supporté'}
    
    try:
        result = processor(order)
        
        # Logger la transaction
        logger.info(f"Paiement initié: Order {order.order_number}, Method {payment_method}, Amount {order.total_amount}")
        
        return result
    except Exception as e:
        logger.error(f"Erreur traitement paiement: {str(e)}")
        return {'success': False, 'error': str(e)}


def process_campay_payment(order):
    """Traiter paiement Campay"""
    url = f"{settings.CAMPAY_BASE_URL}/collect"
    
    headers = {
        'Authorization': f'Token {settings.CAMPAY_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Générer référence unique
    reference = f"VGK-{order.order_number}-{int(timezone.now().timestamp())}"
    
    data = {
        'amount': str(order.total_amount),
        'currency': 'XAF',
        'phone_number': order.buyer.phone,
        'description': f'Achat {order.product.title}',
        'external_reference': reference,
        'webhook_url': f'{settings.SITE_URL}/webhooks/campay/'
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'reference': reference,
                'data': result,
                'payment_url': result.get('payment_url'),
                'ussd_code': result.get('ussd_code')
            }
        else:
            return {
                'success': False,
                'error': f'Erreur Campay: {response.text}'
            }
            
    except requests.RequestException as e:
        return {'success': False, 'error': f'Erreur réseau Campay: {str(e)}'}


def process_orange_money_payment(order):
    """Traiter paiement Orange Money"""
    # Configuration similaire à Campay mais pour Orange Money
    reference = f"VGK-OM-{order.order_number}-{int(timezone.now().timestamp())}"
    
    # Simuler pour l'exemple
    return {
        'success': True,
        'reference': reference,
        'data': {'transaction_id': f'OM{random.randint(100000, 999999)}'},
        'ussd_code': f'#150*{random.randint(1000, 9999)}#'
    }


def process_mtn_money_payment(order):
    """Traiter paiement MTN Mobile Money"""
    reference = f"VGK-MTN-{order.order_number}-{int(timezone.now().timestamp())}"
    
    # Simuler pour l'exemple
    return {
        'success': True,
        'reference': reference,
        'data': {'transaction_id': f'MTN{random.randint(100000, 999999)}'},
        'ussd_code': f'#126*{random.randint(1000, 9999)}#'
    }


def process_noupia_payment(order):
    """Traiter paiement Noupia"""
    reference = f"VGK-NP-{order.order_number}-{int(timezone.now().timestamp())}"
    
    # Simuler pour l'exemple
    return {
        'success': True,
        'reference': reference,
        'data': {'transaction_id': f'NP{random.randint(100000, 999999)}'},
        'payment_url': f'https://pay.noupia.com/payment/{reference}'
    }


def process_card_payment(order):
    """Traiter paiement par carte"""
    reference = f"VGK-CARD-{order.order_number}-{int(timezone.now().timestamp())}"
    
    # Simuler intégration carte (Stripe, PayPal, etc.)
    return {
        'success': True,
        'reference': reference,
        'data': {'transaction_id': f'CARD{random.randint(100000, 999999)}'},
        'payment_url': f'https://pay.stripe.com/payment/{reference}'
    }


def track_analytics(user=None, metric_type='PAGE_VIEW', request=None, data=None):
    """Enregistrer une métrique d'analytics (using performance monitoring)"""
    try:
        if data is None:
            data = {}
        
        # Extract request information
        page_url = request.build_absolute_uri() if request else ''
        referrer = request.META.get('HTTP_REFERER', '') if request else ''
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
        ip_address = get_client_ip(request) if request else '127.0.0.1'
        session_id = request.session.session_key if request and request.session.session_key else ''
        
        # Log analytics data for performance monitoring
        analytics_data = {
            'metric_type': metric_type,
            'user_id': user.id if user else None,
            'session_id': session_id,
            'page_url': page_url,
            'referrer': referrer,
            'user_agent': user_agent,
            'ip_address': ip_address,
            'data': data,
            'timestamp': timezone.now().isoformat()
        }
        
        # Store in cache for performance monitoring
        from django.core.cache import cache
        cache_key = f"analytics_{metric_type}_{ip_address}_{int(timezone.now().timestamp() / 3600)}"
        cache.set(cache_key, analytics_data, 3600)  # Cache for 1 hour
        
        logger.info(f"Analytics tracked: {metric_type} for {page_url}")
        
    except Exception as e:
        logger.error(f"Error tracking analytics: {str(e)}")


def get_client_ip(request):
    """Obtenir l'adresse IP réelle du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def generate_pickup_code():
    """Générer un code de retrait à 6 chiffres"""
    return ''.join(random.choices(string.digits, k=6))


def generate_sku():
    """Générer un SKU unique pour les produits admin"""
    prefix = 'VGK'
    timestamp = str(int(timezone.now().timestamp()))[-6:]
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}{timestamp}{random_suffix}"


def calculate_commission(price, source='CLIENT'):
    """Calculer la commission VGK"""
    if source == 'CLIENT':
        return price * settings.VGK_SETTINGS['COMMISSION_RATE']
    return 0  # Pas de commission sur les produits admin


def calculate_delivery_cost(city, delivery_method='DELIVERY'):
    """Calculer les frais de livraison"""
    if delivery_method == 'PICKUP':
        return 0
    
    if city in ['DOUALA', 'YAOUNDE']:
        return settings.VGK_SETTINGS['DELIVERY_COST_DOUALA_YAOUNDE']
    else:
        return settings.VGK_SETTINGS['DELIVERY_COST_OTHER_CITIES']


def validate_phone_number(phone):
    """Valider un numéro de téléphone camerounais"""
    import re
    pattern = r'^\+237[6-9][0-9]{8}$'
    return re.match(pattern, phone) is not None


def format_price(amount):
    """Formater un prix en FCFA"""
    return f"{amount:,.0f} FCFA".replace(',', ' ')


def get_user_location_from_ip(ip_address):
    """Obtenir la localisation approximative depuis l'IP (optionnel)"""
    # Utiliser un service comme ipinfo.io ou geoip2
    # Pour l'instant, retourner Douala par défaut
    return {
        'city': 'DOUALA',
        'country': 'CM',
        'region': 'Littoral'
    }


def notify_admins(title, message, data=None):
    """Envoyer une notification à tous les administrateurs"""
    admins = User.objects.filter(user_type='ADMIN', is_active=True)
    
    for admin in admins:
        Notification.objects.create(
            user=admin,
            type='SYSTEM',
            title=title,
            message=message,
            data=data or {}
        )


def create_system_notification(user, title, message, notification_type='SYSTEM', data=None):
    """Créer une notification système pour un utilisateur"""
    return Notification.objects.create(
        user=user,
        type=notification_type,
        title=title,
        message=message,
        data=data or {}
    )


def bulk_upload_products_csv(csv_file, admin_user):
    """Importer des produits en masse depuis un fichier CSV"""
    import csv
    import io
    from .models import Product, Category
    
    results = {
        'success': 0,
        'errors': [],
        'total': 0
    }
    
    try:
        # Lire le fichier CSV
        file_content = csv_file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(file_content))
        
        for row_num, row in enumerate(csv_reader, start=2):
            results['total'] += 1
            
            try:
                # Valider et créer le produit
                category = Category.objects.get(name=row['category'])
                
                product = Product.objects.create(
                    title=row['title'],
                    description=row['description'],
                    category=category,
                    seller=admin_user,
                    price=float(row['price']),
                    condition=row['condition'],
                    source='ADMIN',
                    city=row['city'],
                    slug=f"{row['title'].lower().replace(' ', '-')}-{random.randint(1000, 9999)}"
                )
                
                results['success'] += 1
                
            except Exception as e:
                results['errors'].append(f"Ligne {row_num}: {str(e)}")
    
    except Exception as e:
        results['errors'].append(f"Erreur lecture fichier: {str(e)}")
    
    return results


def generate_sales_report(start_date, end_date, user=None):
    """Générer un rapport de ventes"""
    from django.db.models import Sum, Count, Avg
    from .models import Order
    
    # Filtrer les commandes
    orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
        status='DELIVERED'
    )
    
    if user and user.user_type == 'CLIENT':
        orders = orders.filter(product__seller=user)
    
    # Calculer les statistiques
    stats = orders.aggregate(
        total_orders=Count('id'),
        total_revenue=Sum('total_amount'),
        total_commission=Sum('commission_amount'),
        avg_order_value=Avg('total_amount')
    )
    
    # Répartition par ville
    by_city = orders.values('product__city').annotate(
        count=Count('id'),
        revenue=Sum('total_amount')
    ).order_by('-revenue')
    
    # Répartition par catégorie
    by_category = orders.values('product__category__name').annotate(
        count=Count('id'),
        revenue=Sum('total_amount')
    ).order_by('-revenue')
    
    return {
        'period': {'start': start_date, 'end': end_date},
        'stats': stats,
        'by_city': list(by_city),
        'by_category': list(by_category),
        'orders': orders.select_related('buyer', 'product')[:50]  # Dernières 50 commandes
    }


def backup_user_data(user):
    """Créer une sauvegarde des données utilisateur (GDPR)"""
    from .models import Product, Order, Review, Message, Favorite
    
    data = {
        'user_info': {
            'email': user.email,
            'phone': user.phone,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'city': user.city,
            'address': user.address,
            'created_at': user.date_joined.isoformat(),
            'trust_score': user.trust_score,
            'loyalty_points': user.loyalty_points
        },
        'products': list(Product.objects.filter(seller=user).values()),
        'orders_as_buyer': list(Order.objects.filter(buyer=user).values()),
        'orders_as_seller': list(Order.objects.filter(product__seller=user).values()),
        'reviews_given': list(Review.objects.filter(reviewer=user).values()),
        'reviews_received': list(Review.objects.filter(order__product__seller=user).values()),
        'messages': list(Message.objects.filter(sender=user).values()),
        'favorites': list(Favorite.objects.filter(user=user).values())
    }
    
    return data


def delete_user_data(user):
    """Supprimer toutes les données d'un utilisateur (GDPR)"""
    from .models import Product, Order, Review, Message, Favorite, Chat, Notification
    
    # Marquer les produits comme supprimés au lieu de les supprimer
    Product.objects.filter(seller=user).update(
        status='SUSPENDED',
        title='[Produit supprimé]',
        description='Ce produit a été supprimé par l\'utilisateur.'
    )
    
    # Anonymiser les commandes
    Order.objects.filter(buyer=user).update(
        buyer=None,
        delivery_address='[Adresse supprimée]'
    )
    
    # Anonymiser les avis
    Review.objects.filter(reviewer=user).update(
        reviewer=None,
        comment='[Avis supprimé par l\'utilisateur]'
    )
    
    # Supprimer les données personnelles
    user.email = f'deleted_{user.id}@deleted.com'
    user.phone = '+237000000000'
    user.first_name = 'Utilisateur'
    user.last_name = 'Supprimé'
    user.address = ''
    user.is_active = False
    user.save()
    
    # Supprimer complètement certaines données
    Message.objects.filter(sender=user).delete()
    Favorite.objects.filter(user=user).delete()
    Notification.objects.filter(user=user).delete()


class VGKMiddleware:
    """Middleware personnalisé pour VGK"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Code avant la vue
        
        # Ajouter l'IP et la géolocalisation au request
        request.client_ip = get_client_ip(request)
        request.user_location = get_user_location_from_ip(request.client_ip)
        
        response = self.get_response(request)
        
        # Code après la vue
        
        # Tracker les vues de pages
        if hasattr(request, 'user') and request.method == 'GET':
            track_analytics(
                user=request.user if request.user.is_authenticated else None,
                metric_type='PAGE_VIEW',
                request=request
            )
        
        return response


# Context processor pour les variables globales
def global_context(request):
    """Context processor pour ajouter des variables globales aux templates"""
    context = {
        'VGK_SETTINGS': settings.VGK_SETTINGS,
        'SITE_NAME': 'Vidé-Grenier Kamer',
        'SITE_TAGLINE': 'Vendez, Achetez, Économisez',
        'CURRENT_YEAR': timezone.now().year,
    }
    
    if request.user.is_authenticated:
        # Notifications non lues
        context['unread_notifications_count'] = request.user.notifications.filter(
            is_read=False
        ).count()
        
        # Messages non lus
        from .models import Message, Chat
        unread_messages = Message.objects.filter(
            chat__in=Chat.objects.filter(
                models.Q(buyer=request.user) | models.Q(seller=request.user)
            ),
            is_read=False
        ).exclude(sender=request.user).count()
        
        context['unread_messages_count'] = unread_messages
        
        # Produits favoris
        context['favorites_count'] = request.user.favorites.count()
    
    return context