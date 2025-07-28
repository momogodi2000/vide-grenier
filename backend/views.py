"""
backend/views.py - VERSION COMPLÈTE AVEC TOUTES LES VUES
Includes all main views, AJAX, and webhook logic. Updated for anonymous orders and payment methods.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, 
    UpdateView, DeleteView, FormView
)
from django.views import View
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Avg, Sum, F
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import cache_page
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.core.cache import cache
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import json
import logging

import random
import string
import urllib.parse
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    User, Product, Category, Order, Payment, Review, 
    Chat, Message, Favorite, SearchHistory, Notification, 
    AdminStock, PickupPoint, ProductImage,
    GroupChat, GroupChatMessage, SearchAlert, SavedSearch,
    ProductAlert
)
from .models_advanced import (
    VisitorCart, VisitorCartItem, ProductReport, VisitorFavorite, 
    VisitorCompare, ProductComment, ProductLike
)
from .forms import (
    CustomSignupForm, CustomLoginForm, ProductForm, 
    OrderForm, ReviewForm, ChatMessageForm, ProfileForm,
    SearchForm, AdminStockForm, ContactForm,
    GroupChatForm, GroupChatMessageForm
)
from .utils import (
    send_sms_notification, send_email_notification, 
    process_payment, track_analytics, generate_pickup_code,
    get_client_ip
)

logger = logging.getLogger(__name__)

# Cache decorators for performance
CACHE_TIMEOUT = 60 * 15  # 15 minutes
PRODUCT_CACHE_TIMEOUT = 60 * 30  # 30 minutes for product pages

def get_cache_key(prefix, *args):
    """Generate cache key with prefix and arguments"""
    return f"vgk_{prefix}_{'_'.join(str(arg) for arg in args)}"


class HomeView(TemplateView):
    template_name = 'backend/visitor/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get or create visitor session for cart functionality
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        
        # Get visitor cart for product integration
        visitor_cart, created = VisitorCart.objects.get_or_create(
            session_key=session_key,
            defaults={'session_key': session_key}
        )
        
        # Produits en vedette
        featured_products = Product.objects.filter(
            is_featured=True, 
            status='ACTIVE'
        ).select_related('category', 'seller').prefetch_related('images')[:8]
        
        # Produits récents
        recent_products = Product.objects.filter(
            status='ACTIVE'
        ).select_related('category', 'seller').prefetch_related('images').order_by('-created_at')[:12]
        
        # Add visitor interaction data to products
        if session_key:
            # Get visitor favorites
            favorite_product_ids = set(
                VisitorFavorite.objects.filter(session_key=session_key)
                .values_list('product_id', flat=True)
            )
            
            # Get visitor cart items
            cart_product_ids = set(
                visitor_cart.items.values_list('product_id', flat=True)
            )
            
            # Get visitor compares
            compare_product_ids = set(
                VisitorCompare.objects.filter(session_key=session_key)
                .values_list('product_id', flat=True)
            )
            
            # Add flags to products
            for product in featured_products:
                product.is_favorited = product.id in favorite_product_ids
                product.is_in_cart = product.id in cart_product_ids
                product.is_comparing = product.id in compare_product_ids
                # Get like counts
                product.likes_count = ProductLike.objects.filter(product=product, like_type='LIKE').count()
                product.comments_count = ProductComment.objects.filter(product=product, is_approved=True).count()
            
            for product in recent_products:
                product.is_favorited = product.id in favorite_product_ids
                product.is_in_cart = product.id in cart_product_ids
                product.is_comparing = product.id in compare_product_ids
                # Get like counts
                product.likes_count = ProductLike.objects.filter(product=product, like_type='LIKE').count()
                product.comments_count = ProductComment.objects.filter(product=product, is_approved=True).count()
        
        # Catégories principales
        context['main_categories'] = Category.objects.filter(
            parent=None, 
            is_active=True
        ).order_by('order')[:8]
        
        # Statistiques
        context['stats'] = {
            'total_products': Product.objects.filter(status='ACTIVE').count(),
            'total_users': User.objects.filter(user_type='CLIENT').count(),
            'total_orders': Order.objects.filter(status='DELIVERED').count(),
            'cities_count': len(getattr(settings, 'VGK_SETTINGS', {}).get('SUPPORTED_CITIES', ['DOUALA', 'YAOUNDE']))
        }
        
        # Témoignages (derniers avis 5 étoiles)
        context['testimonials'] = Review.objects.filter(
            overall_rating=5
        ).select_related('reviewer', 'order__product').order_by('-created_at')[:6]
        
        # Add visitor data to context
        context.update({
            'featured_products': featured_products,
            'recent_products': recent_products,
            'visitor_cart': visitor_cart,
            'total_favorites': VisitorFavorite.objects.filter(session_key=session_key).count() if session_key else 0,
            'total_compares': VisitorCompare.objects.filter(session_key=session_key).count() if session_key else 0,
        })
        
        return context


class CustomLoginView(LoginView):
    """Vue de connexion personnalisée"""
    form_class = CustomLoginForm
    template_name = 'backend/visitor/auth/login.html'
    
    def get_success_url(self):
        """Redirect users to their appropriate dashboard based on user type"""
        try:
            user = self.request.user
            
            # Redirect to user-type-specific dashboard using direct paths
            if user.user_type == 'CLIENT':
                return '/client/'
            elif user.user_type == 'STAFF':
                return '/staff/'
            elif user.user_type == 'ADMIN':
                return '/admin-panel/'
            else:
                return reverse_lazy('backend:dashboard')
        except Exception as e:
            # If URL resolution fails, fallback to main dashboard
            print(f"URL resolution error in CustomLoginView: {e}")
            return reverse_lazy('backend:dashboard')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Bienvenue {self.request.user.get_full_name() or self.request.user.email}!")
        
        # Track login analytics
        track_analytics(
            user=self.request.user,
            metric_type='LOGIN',
            request=self.request
        )
        
        return response


class CustomSignupView(CreateView):
    """Vue d'inscription personnalisée"""
    form_class = CustomSignupForm
    template_name = 'backend/visitor/auth/register.html'
    
    def get_success_url(self):
        """Redirect users to their appropriate dashboard based on user type"""
        try:
            user = self.request.user
            
            # Redirect to user-type-specific dashboard using direct paths
            if user.user_type == 'CLIENT':
                return '/client/'
            elif user.user_type == 'STAFF':
                return '/staff/'
            elif user.user_type == 'ADMIN':
                return '/admin-panel/'
            else:
                return reverse_lazy('backend:dashboard')
        except Exception as e:
            # If URL resolution fails, fallback to main dashboard
            print(f"URL resolution error in CustomSignupView: {e}")
            return reverse_lazy('backend:dashboard')
    
    def form_valid(self, form):
        user = form.save()
        # Specify the backend explicitly to avoid multiple backends error
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(
            self.request, 
            "Compte créé avec succès! Vérifiez votre email pour activer votre compte."
        )
        
        # Envoyer SMS de bienvenue
        try:
            send_sms_notification(
                user.phone,
                f"Bienvenue sur Vidé-Grenier Kamer! Votre compte a été créé avec succès."
            )
        except Exception as e:
            # Log the error but don't fail the registration
            print(f"SMS sending failed: {e}")
        
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    """Vue de déconnexion personnalisée"""
    next_page = reverse_lazy('backend:home')
    
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "Vous avez été déconnecté avec succès.")
        return super().dispatch(request, *args, **kwargs)


# Enhanced DashboardView for admin dashboard with comprehensive real data
# Add this to your backend/views.py or create a new file backend/admin_views.py

from django.db.models import Q, Count, Avg, Sum, F, Case, When, IntegerField
from django.utils import timezone
from datetime import datetime, timedelta
import json
from decimal import Decimal

class DashboardView(LoginRequiredMixin, TemplateView):
    """Tableau de bord utilisateur personnalisé selon le type avec données réelles"""
    template_name = 'backend/visitor/dashboard.html'
    
    def get_template_names(self):
        user_type = self.request.user.user_type
        if user_type == 'ADMIN':
            return ['backend/dashboard/admin_dashboard.html']
        elif user_type == 'STAFF':
            return ['backend/staff/dashboard.html']
        return ['backend/client/dashboard.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.user_type == 'ADMIN':
            # Dashboard admin avec données complètes
            context.update(self.get_admin_context())
        elif user.user_type == 'CLIENT':
            # Dashboard client
            context.update(self.get_client_context(user))
        elif user.user_type == 'STAFF':
            # Dashboard staff
            context.update(self.get_staff_context(user))
            
        return context

    def get_admin_context(self):
                """Contexte complet pour le dashboard administrateur avec noms de champs corrects"""
                now = timezone.now()
                today = now.date()
                this_month = now.replace(day=1).date()
                last_month = (now.replace(day=1) - timedelta(days=1)).replace(day=1).date()
                
                # =========================
                # STATISTIQUES PRINCIPALES
                # =========================
                
                # Utilisateurs
                total_users = User.objects.filter(user_type='CLIENT').count()
                new_users_this_month = User.objects.filter(
                    user_type='CLIENT',
                    date_joined__date__gte=this_month
                ).count()
                
                new_users_last_month = User.objects.filter(
                    user_type='CLIENT',
                    date_joined__date__gte=last_month,
                    date_joined__date__lt=this_month
                ).count()
                
                # Calcul pourcentage croissance utilisateurs
                if new_users_last_month > 0:
                    new_users_percentage = round(((new_users_this_month - new_users_last_month) / new_users_last_month) * 100, 1)
                else:
                    new_users_percentage = 100 if new_users_this_month > 0 else 0
                
                # Produits
                active_products = Product.objects.filter(status='ACTIVE').count()
                admin_stock_products = AdminStock.objects.filter(quantity__gt=0).count()
                low_stock_count = AdminStock.objects.filter(quantity__lte=5).count()
                
                # Commandes
                today_orders = Order.objects.filter(created_at__date=today).count()
                pending_orders = Order.objects.filter(status__in=['PENDING', 'PAID']).count()
                
                # Revenus et commissions
                monthly_revenue = Order.objects.filter(
                    status='DELIVERED',
                    created_at__date__gte=this_month
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
                
                monthly_commission = Order.objects.filter(
                    status='DELIVERED',
                    created_at__date__gte=this_month
                ).aggregate(total=Sum('commission_amount'))['total'] or Decimal('0')
                
                # Paiements mobiles
                mobile_payments = Payment.objects.filter(
                    order__payment_method__in=['MTN_MONEY', 'ORANGE_MONEY'],
                    status='COMPLETED',
                    created_at__date__gte=this_month
                ).count()
                
                # Points de retrait
                pickup_points_count = PickupPoint.objects.filter(is_active=True).count()
                
                # Avis et satisfaction
                reviews_data = Review.objects.filter(is_verified=True).aggregate(
                    avg_rating=Avg('overall_rating'),
                    total_count=Count('id')
                )
                average_rating = reviews_data['avg_rating'] or 0
                total_reviews = reviews_data['total_count'] or 0
                
                # Paiements en attente
                pending_payments = Payment.objects.filter(status='PENDING').count()
                
                # =========================
                # DONNÉES POUR GRAPHIQUES
                # =========================
                
                # Données des ventes sur 7 jours
                daily_sales_labels = []
                daily_sales_data = []
                
                for i in range(7):
                    date = today - timedelta(days=6-i)
                    daily_sales_labels.append(date.strftime('%a'))
                    
                    daily_revenue = Order.objects.filter(
                        created_at__date=date,
                        status='DELIVERED'
                    ).aggregate(total=Sum('total_amount'))['total'] or 0
                    
                    daily_sales_data.append(float(daily_revenue))
                
                # Données des méthodes de paiement
                payment_methods = Order.objects.filter(
                    status='DELIVERED',
                    created_at__date__gte=this_month
                ).values('payment_method').annotate(
                    count=Count('id')
                ).order_by('-count')
                
                payment_methods_labels = []
                payment_methods_data = []
                
                for pm in payment_methods:
                    method_name = dict(Order.PAYMENT_METHODS).get(pm['payment_method'], pm['payment_method'])
                    payment_methods_labels.append(method_name)
                    payment_methods_data.append(pm['count'])
                
                # =========================
                # TOP CATÉGORIES
                # =========================
                
                top_categories = Category.objects.annotate(
                    product_count=Count('products', filter=Q(products__status='ACTIVE'))
                ).filter(product_count__gt=0).order_by('-product_count')[:5]
                
                # =========================
                # FIDÉLITÉ CLIENTS (Corrigé)
                # =========================
                
                # Calculer les niveaux de fidélité basés sur le nombre de commandes
                loyalty_levels = []
                
                # Bronze: 1-3 commandes
                bronze_count = User.objects.filter(
                    user_type='CLIENT'
                ).annotate(
                    order_count=Count('orders', filter=Q(orders__status='DELIVERED'))
                ).filter(order_count__gte=1, order_count__lte=3).count()
                
                # Argent: 4-10 commandes
                silver_count = User.objects.filter(
                    user_type='CLIENT'
                ).annotate(
                    order_count=Count('orders', filter=Q(orders__status='DELIVERED'))
                ).filter(order_count__gte=4, order_count__lte=10).count()
                
                # Or: 11-25 commandes
                gold_count = User.objects.filter(
                    user_type='CLIENT'
                ).annotate(
                    order_count=Count('orders', filter=Q(orders__status='DELIVERED'))
                ).filter(order_count__gte=11, order_count__lte=25).count()
                
                # Platine: 25+ commandes
                platinum_count = User.objects.filter(
                    user_type='CLIENT'
                ).annotate(
                    order_count=Count('orders', filter=Q(orders__status='DELIVERED'))
                ).filter(order_count__gt=25).count()
                
                loyalty_levels = [
                    {'name': 'Bronze', 'count': bronze_count, 'color': 'bg-gray-400'},
                    {'name': 'Argent', 'count': silver_count, 'color': 'bg-gray-300'},
                    {'name': 'Or', 'count': gold_count, 'color': 'bg-yellow-400'},
                    {'name': 'Platine', 'count': platinum_count, 'color': 'bg-purple-500'},
                ]
                
                # Calcul taux de rétention (clients qui ont commandé plus d'une fois)
                total_customers_with_orders = User.objects.filter(
                    user_type='CLIENT',
                    orders__status='DELIVERED'
                ).distinct().count()
                
                repeat_customers = User.objects.filter(
                    user_type='CLIENT'
                ).annotate(
                    order_count=Count('orders', filter=Q(orders__status='DELIVERED'))
                ).filter(order_count__gt=1).count()
                
                retention_rate = round((repeat_customers / total_customers_with_orders * 100), 1) if total_customers_with_orders > 0 else 0
                
                # =========================
                # PERFORMANCE PAR VILLE
                # =========================
                
                # Obtenir les statistiques par ville
                city_stats = []
                total_users_all_cities = User.objects.filter(user_type='CLIENT').count()
                
                for city_code, city_name in User.CITIES:
                    city_users = User.objects.filter(city=city_code, user_type='CLIENT').count()
                    city_percentage = round((city_users / total_users_all_cities * 100), 1) if total_users_all_cities > 0 else 0
                    
                    city_stats.append({
                        'name': city_name,
                        'users': city_users,
                        'percentage': city_percentage
                    })
                
                # Revenus par ville principale
                douala_revenue = Order.objects.filter(
                    product__city='DOUALA',
                    status='DELIVERED',
                    created_at__date__gte=this_month
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
                
                yaounde_revenue = Order.objects.filter(
                    product__city='YAOUNDE',
                    status='DELIVERED',
                    created_at__date__gte=this_month
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
                
                # =========================
                # COMMANDES URGENTES
                # =========================
                
                urgent_orders = Order.objects.filter(
                    status__in=['PENDING', 'PAID']
                ).select_related('product').order_by('created_at')[:5]
                
                # =========================
                # POINTS DE RETRAIT
                # =========================
                
                pickup_points = PickupPoint.objects.all()
                for point in pickup_points:
                    # Calculer les commandes en attente pour chaque point
                    point.pending_orders_count = Order.objects.filter(
                        delivery_method='PICKUP',
                        status__in=['PAID', 'PROCESSING']
                    ).count()  # Générique pour tous les points pour l'instant
                    
                    # Calculer le staff actif
                    point.staff_count = User.objects.filter(
                        user_type='STAFF',
                        is_active=True
                    ).count()  # Générique pour tous les points
                    
                    # Capacité simulée basée sur les commandes en attente
                    max_capacity = 50  # Capacité maximale par point
                    point.capacity = min(100, round((point.pending_orders_count / max_capacity) * 100))
                
                # =========================
                # TOP VENDEURS DU MOIS (Corrigé)
                # =========================
                
                top_sellers = User.objects.filter(
                    user_type='CLIENT',
                    products_sold__order__status='DELIVERED',
                    products_sold__order__created_at__date__gte=this_month
                ).annotate(
                    total_sales=Count('products_sold__order', filter=Q(products_sold__order__status='DELIVERED')),
                    total_revenue=Sum('products_sold__order__total_amount', filter=Q(products_sold__order__status='DELIVERED'))
                ).filter(total_sales__gt=0).order_by('-total_revenue')[:5]
                
                # Ajouter city_display pour chaque vendeur
                for seller in top_sellers:
                    seller.city_display = dict(User.CITIES).get(seller.city, 'Non spécifié')
                
                # =========================
                # ACTIVITÉS RÉCENTES
                # =========================
                
                recent_activities = []
                
                # Nouveaux utilisateurs (dernières 24h)
                new_users_today = User.objects.filter(
                    user_type='CLIENT',
                    date_joined__date=today
                ).order_by('-date_joined')[:3]
                
                for user in new_users_today:
                    recent_activities.append({
                        'icon': 'user-plus',
                        'color': 'green',
                        'message': f'Nouvel utilisateur inscrit: <strong>{user.get_full_name() or user.email}</strong> - {dict(User.CITIES).get(user.city, "Lieu non spécifié")}',
                        'created_at': user.date_joined
                    })
                
                # Nouvelles commandes (dernières 24h)
                new_orders_today = Order.objects.filter(
                    created_at__date=today
                ).select_related('product', 'buyer').order_by('-created_at')[:3]
                
                for order in new_orders_today:
                    recent_activities.append({
                        'icon': 'shopping-cart',
                        'color': 'blue',
                        'message': f'Nouvelle commande: <strong>{order.product.title}</strong> - {order.total_amount} FCFA',
                        'created_at': order.created_at
                    })
                
                # Nouveaux avis (dernières 24h)
                new_reviews_today = Review.objects.filter(
                    created_at__date=today,
                    is_verified=True
                ).select_related('reviewer', 'order__product').order_by('-created_at')[:2]
                
                for review in new_reviews_today:
                    recent_activities.append({
                        'icon': 'star',
                        'color': 'orange',
                        'message': f'Nouvel avis {review.overall_rating} étoiles de <strong>{review.reviewer.get_full_name() or review.reviewer.email}</strong> sur {review.order.product.title}',
                        'created_at': review.created_at
                    })
                
                # Nouveaux produits admin stock
                try:
                    new_admin_products = AdminStock.objects.filter(
                        created_at__date=today
                    ).select_related('product').order_by('-created_at')[:2]
                    
                    for stock in new_admin_products:
                        recent_activities.append({
                            'icon': 'package',
                            'color': 'purple',
                            'message': f'Stock admin ajouté: <strong>{stock.product.title}</strong> - {stock.quantity} unités',
                            'created_at': stock.created_at
                        })
                except:
                    # Si AdminStock n'a pas de created_at, ignorer cette section
                    pass
                
                # Trier les activités par date
                recent_activities.sort(key=lambda x: x['created_at'], reverse=True)
                recent_activities = recent_activities[:10]  # Garder seulement les 10 plus récentes
                
                # =========================
                # MÉTRIQUES PERFORMANCE
                # =========================
                
                # Taux de conversion (commandes payées / visiteurs uniques)
                total_orders_this_month = Order.objects.filter(
                    created_at__date__gte=this_month
                ).count()
                
                conversion_rate = round((total_orders_this_month / total_users * 100), 1) if total_users > 0 else 0
                
                # Panier moyen
                average_order_value = Order.objects.filter(
                    status='DELIVERED',
                    created_at__date__gte=this_month
                ).aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0')
                
                # Taux de retour (simulation)
                return_rate = 2.1  # Simulé
                
                # =========================
                # MESSAGES ET NOTIFICATIONS
                # =========================
                
                # Messages non lus pour l'admin (corrigé)
                unread_messages_count = Message.objects.filter(
                    is_read=False
                ).exclude(sender__user_type='ADMIN').count()
                
                # Notifications non lues pour l'admin
                unread_notifications_count = Notification.objects.filter(
                    user=self.request.user,
                    is_read=False
                ).count()
                
                # =========================
                # ASSEMBLAGE DU CONTEXTE
                # =========================
                
                return {
                    'stats': {
                        'total_users': total_users,
                        'new_users_this_month': new_users_percentage,
                        'active_products': active_products,
                        'admin_stock_products': admin_stock_products,
                        'admin_stock_total': AdminStock.objects.aggregate(total=Sum('quantity'))['total'] or 0,
                        'low_stock_count': low_stock_count,
                        'today_orders': today_orders,
                        'pending_orders': pending_orders,
                        'monthly_revenue': monthly_revenue,
                        'monthly_commission': monthly_commission,
                        'mobile_payments': mobile_payments,
                        'pickup_points_count': pickup_points_count,
                        'average_rating': average_rating,
                        'total_reviews': total_reviews,
                        'pending_payments': pending_payments,
                        'retention_rate': retention_rate,
                        'new_users_percentage': new_users_percentage,
                        'conversion_rate': conversion_rate,
                        'conversion_change': 2.1,  # Simulé
                        'average_order_value': average_order_value,
                        'basket_change': 5,  # Simulé
                        'return_rate': return_rate,
                        'return_change': -0.3,  # Simulé
                    },
                    'top_categories': top_categories,
                    'loyalty_levels': loyalty_levels,
                    'city_stats': city_stats,
                    'city_stats': {
                        'douala_revenue': douala_revenue,
                        'yaounde_revenue': yaounde_revenue,
                    },
                    'urgent_orders': urgent_orders,
                    'pickup_points': pickup_points,
                    'top_sellers': top_sellers,
                    'recent_activities': recent_activities,
                    'unread_messages_count': unread_messages_count,
                    'unread_notifications_count': unread_notifications_count,
                    
                    # Données pour les graphiques (format JSON pour JavaScript)
                    'daily_sales_labels': json.dumps(daily_sales_labels),
                    'daily_sales_data': json.dumps(daily_sales_data),
                    'payment_methods_labels': json.dumps(payment_methods_labels),
                    'payment_methods_data': json.dumps(payment_methods_data),
                }
    
    def get_client_context(self, user):
        """Contexte pour le dashboard client (existant)"""
        return {
            'my_products': Product.objects.filter(seller=user).order_by('-created_at')[:5],
            'my_orders': Order.objects.filter(buyer=user).order_by('-created_at')[:5],
            'my_favorites': Favorite.objects.filter(user=user).select_related('product')[:5],
            'unread_messages': Message.objects.filter(
                chat__buyer=user, is_read=False
            ).exclude(sender=user).count(),
            'notifications': Notification.objects.filter(
                user=user, is_read=False
            ).order_by('-created_at')[:5],
            'sales_stats': {
                'total_sales': Order.objects.filter(
                    product__seller=user, status='DELIVERED'
                ).count(),
                'total_revenue': Order.objects.filter(
                    product__seller=user, status='DELIVERED'
                ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            }
        }
    
    def get_staff_context(self, user):
        """Contexte pour le dashboard staff"""
        # Assumant que le staff est associé à un point de retrait
        try:
            pickup_point = user.pickup_point  # Relation à définir dans le modèle
            
            return {
                'pickup_point': pickup_point,
                'pending_pickups': Order.objects.filter(
                    delivery_method='PICKUP',
                    status='PAID',
                    # pickup_point=pickup_point
                ).count(),
                'today_pickups': Order.objects.filter(
                    delivery_method='PICKUP',
                    status='DELIVERED',
                    delivered_at__date=timezone.now().date(),
                    # pickup_point=pickup_point
                ).count(),
            }
        except AttributeError:
            return {
                'pickup_point': None,
                'pending_pickups': 0,
                'today_pickups': 0,
            }



class ProductListView(ListView):
    """Liste des produits avec filtres et recherche"""
    model = Product
    template_name = 'backend/client/products/list.html'
    context_object_name = 'products'
    paginate_by = 24
    
    def get_queryset(self):
        queryset = Product.objects.filter(status='ACTIVE').select_related(
            'category', 'seller'
        ).prefetch_related('images')
        
        # Filtres de recherche
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(category__name__icontains=search)
            )
            
            # Enregistrer la recherche
            SearchHistory.objects.create(
                user=self.request.user if self.request.user.is_authenticated else None,
                search_term=search,
                results_count=queryset.count(),
                ip_address=self.request.META.get('REMOTE_ADDR', '127.0.0.1')
            )
        
        # Filtres par catégorie
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Filtres par ville
        city = self.request.GET.get('city')
        if city:
            queryset = queryset.filter(city=city)
        
        # Filtres par prix
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Filtres par condition
        condition = self.request.GET.get('condition')
        if condition:
            queryset = queryset.filter(condition=condition)
        
        # Tri
        sort = self.request.GET.get('sort', '-created_at')
        if sort == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort == 'popular':
            queryset = queryset.order_by('-views_count')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get or create visitor cart for cart-related annotations
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        
        visitor_cart, created = VisitorCart.objects.get_or_create(session_key=session_key)
        
        # Annotate products with visitor interaction data
        products = context['products']
        if products:
            # Get current visitor's favorites, comparisons, and cart items
            visitor_favorites = set(VisitorFavorite.objects.filter(
                session_key=session_key
            ).values_list('product_id', flat=True))
            
            visitor_compares = set(VisitorCompare.objects.filter(
                session_key=session_key
            ).values_list('product_id', flat=True))
            
            cart_items = set(VisitorCartItem.objects.filter(
                cart=visitor_cart
            ).values_list('product_id', flat=True))
            
            # Annotate each product
            for product in products:
                product.is_favorited = product.id in visitor_favorites
                product.is_comparing = product.id in visitor_compares
                product.is_in_cart = product.id in cart_items
                
                # Get like counts
                likes_count = ProductLike.objects.filter(
                    product=product, like_type='LIKE'
                ).count()
                dislikes_count = ProductLike.objects.filter(
                    product=product, like_type='DISLIKE'
                ).count()
                product.likes_count = likes_count
                product.dislikes_count = dislikes_count
                
                # Get comments count
                product.comments_count = ProductComment.objects.filter(
                    product=product, is_approved=True, parent=None
                ).count()
        
        # Get visitor favorites and comparisons count for display
        total_favorites = VisitorFavorite.objects.filter(session_key=session_key).count()
        total_compares = VisitorCompare.objects.filter(session_key=session_key).count()
        
        context.update({
            'categories': Category.objects.filter(is_active=True, parent=None),
            'cities': User.CITIES,
            'conditions': Product.CONDITIONS,
            'selected_conditions': self.request.GET.getlist('condition'),
            'current_filters': {
                'q': self.request.GET.get('q', ''),
                'category': self.request.GET.get('category', ''),
                'city': self.request.GET.get('city', ''),
                'min_price': self.request.GET.get('min_price', ''),
                'max_price': self.request.GET.get('max_price', ''),
                'condition': self.request.GET.get('condition', ''),
                'sort': self.request.GET.get('sort', '-created_at'),
            },
            'visitor_cart': visitor_cart,
            'total_favorites': total_favorites,
            'total_compares': total_compares,
        })
        return context


class ProductDetailView(DetailView):
    """Détail d'un produit avec suggestions et achat public"""
    model = Product
    template_name = 'backend/client/products/detail.html'
    context_object_name = 'product'
    
    def get_object(self):
        product = get_object_or_404(Product, slug=self.kwargs['slug'], status='ACTIVE')
        
        # Incrémenter le compteur de vues
        Product.objects.filter(id=product.id).update(views_count=F('views_count') + 1)
        
        # Track analytics
        track_analytics(
            user=self.request.user if self.request.user.is_authenticated else None,
            metric_type='PRODUCT_VIEW',
            request=self.request,
            data={'product_id': str(product.id), 'product_title': product.title}
        )
        
        return product
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        
        # Produits similaires
        context['similar_products'] = Product.objects.filter(
            category=product.category,
            status='ACTIVE'
        ).exclude(id=product.id)[:8]
        
        # Autres produits du vendeur
        context['seller_products'] = Product.objects.filter(
            seller=product.seller,
            status='ACTIVE'
        ).exclude(id=product.id)[:4]
        
        # Vérifier si l'utilisateur a mis ce produit en favori
        if self.request.user.is_authenticated:
            context['is_favorite'] = Favorite.objects.filter(
                user=self.request.user, 
                product=product
            ).exists()
            
            # Vérifier si l'utilisateur peut contacter le vendeur
            context['can_contact_seller'] = (
                self.request.user != product.seller and 
                product.status == 'ACTIVE'
            )
        
        # Avis sur ce produit (si vendu)
        context['reviews'] = Review.objects.filter(
            order__product=product
        ).select_related('reviewer').order_by('-created_at')
        
        # Calculs pour l'affichage avec frais de livraison fixes 2000 FCFA
        delivery_cost = Decimal('2000')  # Frais fixes 2000 FCFA
        context.update({
            'delivery_cost': delivery_cost,
            'commission_amount': product.commission_amount,
            'total_with_delivery': product.price + delivery_cost,
            'whatsapp_message': self.generate_whatsapp_message(product, delivery_cost),
            'whatsapp_url': self.generate_whatsapp_url(product, delivery_cost)
        })
        
        return context
    
    def generate_whatsapp_message(self, product, delivery_cost):
        """Générer le message WhatsApp pré-rempli"""
        total = product.price + delivery_cost
        message = f"""Bonjour! Je suis intéressé par ce produit:

🛍️ *{product.title}*
💰 Prix: {product.price:,.0f} FCFA
🚚 Livraison: {delivery_cost:,.0f} FCFA
💳 Total: {total:,.0f} FCFA

📍 Ville: {product.get_city_display()}
🔗 Lien: {self.request.build_absolute_uri()}

Je souhaite commander avec *paiement à la livraison*.

Merci!"""
        return message
    
    def generate_whatsapp_url(self, product, delivery_cost):
        """Générer l'URL WhatsApp Business"""
        import urllib.parse
        
        # Numéro WhatsApp Business VGK
        phone = "237694638412"  # Remplacez par votre numéro
        message = self.generate_whatsapp_message(product, delivery_cost)
        encoded_message = urllib.parse.quote(message)
        
        return f"https://wa.me/{phone}?text={encoded_message}"


class PublicOrderCreateView(CreateView):
    """Commande publique avec paiement à la livraison"""
    model = Order
    template_name = 'backend/visitor/orders/public_order.html'
    fields = ['delivery_address', 'notes']
    
    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, slug=kwargs['slug'], status='ACTIVE')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        delivery_cost = Decimal('2000')
        context.update({
            'product': self.product,
            'delivery_cost': delivery_cost,
            'total_amount': self.product.price + delivery_cost
        })
        return context
    
    def form_valid(self, form):
        delivery_cost = Decimal('2000')
        
        with transaction.atomic():
            # Créer la commande avec paiement à la livraison
            form.instance.product = self.product
            form.instance.total_amount = self.product.price + delivery_cost
            form.instance.commission_amount = self.product.commission_amount
            form.instance.delivery_cost = delivery_cost
            form.instance.status = 'PENDING'
            form.instance.payment_method = 'CASH_ON_DELIVERY'
            form.instance.delivery_method = 'DELIVERY'
            
            # Si l'utilisateur est connecté, l'assigner comme acheteur
            if self.request.user.is_authenticated:
                form.instance.buyer = self.request.user
            else:
                # Créer un utilisateur anonyme ou utiliser email/téléphone
                form.instance.buyer = None
            
            response = super().form_valid(form)
            
            # Réserver le produit
            self.product.status = 'RESERVED'
            self.product.save()
            
            # Notifier le vendeur
            send_sms_notification(
                self.product.seller.phone,
                f"Nouvelle commande VGK: {self.product.title} - Paiement à la livraison. Commande #{self.object.order_number}"
            )
            
            # Notifier les admins
            send_email_notification(
                'admin@vgk.com',
                'Nouvelle commande publique',
                'order_notification',
                {'order': self.object, 'product': self.product}
            )
        
        messages.success(
            self.request, 
            f"Commande créée avec succès! Numéro: {self.object.order_number}. "
            f"Vous serez contacté pour la livraison."
        )
        
        return response
    
    def get_success_url(self):
        return reverse('backend:public_order_success', kwargs={'order_number': self.object.order_number})


class PublicOrderSuccessView(TemplateView):
    """Page de confirmation de commande publique"""
    template_name = 'backend/visitor/orders/public_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = get_object_or_404(
            Order, 
            order_number=kwargs['order_number']
        )
        return context


class ProductCreateView(LoginRequiredMixin, CreateView):
    """Création d'un nouveau produit"""
    model = Product
    form_class = ProductForm
    template_name = 'backend/client/products/create.html'
    
    def form_valid(self, form):
        form.instance.seller = self.request.user
        form.instance.source = 'CLIENT'
        
        # Générer le slug automatiquement
        from django.utils.text import slugify
        import uuid
        base_slug = slugify(form.instance.title)
        form.instance.slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"
        
        response = super().form_valid(form)
        
        messages.success(
            self.request, 
            "Votre produit a été créé avec succès! Il sera visible après validation."
        )
        
        return response
    
    def get_success_url(self):
        return reverse('backend:product_detail', kwargs={'slug': self.object.slug})


class ProductEditView(LoginRequiredMixin, UpdateView):
    """Modification d'un produit"""
    model = Product
    form_class = ProductForm
    template_name = 'backend/client/products/edit.html'
    
    def get_queryset(self):
        # Seul le propriétaire peut modifier
        return Product.objects.filter(seller=self.request.user)
    
    def get_success_url(self):
        return reverse('backend:product_detail', kwargs={'slug': self.object.slug})


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    """Suppression d'un produit"""
    model = Product
    template_name = 'backend/client/products/delete.html'
    success_url = reverse_lazy('backend:dashboard')
    
    def get_queryset(self):
        # Seul le propriétaire peut supprimer
        return Product.objects.filter(seller=self.request.user)


class ProfileView(LoginRequiredMixin, DetailView):
    """Profil utilisateur"""
    model = User
    template_name = 'backend/client/profile/profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        return self.request.user


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Modification du profil utilisateur"""
    model = User
    form_class = ProfileForm
    template_name = 'backend/client/profile/edit.html'
    success_url = reverse_lazy('backend:profile')
    
    def get_object(self):
        return self.request.user


class CategoryView(ListView):
    """Produits d'une catégorie"""
    model = Product
    template_name = 'backend/client/categories/detail.html'
    context_object_name = 'products'
    paginate_by = 24
    
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return Product.objects.filter(
            category=self.category,
            status='ACTIVE'
        ).select_related('seller').prefetch_related('images')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class CategoryListView(ListView):
    """Liste de toutes les catégories"""
    model = Category
    template_name = 'backend/client/categories/list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True, parent=None).prefetch_related('children')


class OrderCreateView(LoginRequiredMixin, CreateView):
    """Création d'une commande pour utilisateurs connectés"""
    model = Order
    form_class = OrderForm
    template_name = 'backend/client/orders/create.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, id=kwargs['product_id'], status='ACTIVE')
        
        if request.user == self.product.seller:
            messages.error(request, "Vous ne pouvez pas acheter votre propre produit.")
            return redirect('backend:product_detail', slug=self.product.slug)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.buyer = self.request.user
        form.instance.product = self.product
        
        # Frais de livraison fixes 2000 FCFA
        delivery_cost = Decimal('2000')
        form.instance.total_amount = self.product.price + delivery_cost
        form.instance.commission_amount = self.product.commission_amount
        form.instance.delivery_cost = delivery_cost
        
        with transaction.atomic():
            response = super().form_valid(form)
            
            # Réserver le produit
            self.product.status = 'RESERVED'
            self.product.save()
            
            # Créer le code de retrait si nécessaire
            if form.instance.delivery_method == 'PICKUP':
                form.instance.pickup_code = generate_pickup_code()
                form.instance.save()
        
        messages.success(self.request, "Commande créée! Procédez au paiement.")
        return response
    
    def get_success_url(self):
        return reverse('backend:payment', kwargs={'order_id': self.object.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        context['delivery_cost'] = Decimal('2000')
        return context


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Détail d'une commande"""
    model = Order
    template_name = 'backend/client/orders/detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        # Seuls l'acheteur, le vendeur ou un admin peuvent voir
        return Order.objects.filter(
            Q(buyer=self.request.user) | 
            Q(product__seller=self.request.user) |
            Q(buyer__isnull=True)  # Commandes publiques
        ).select_related('product', 'buyer', 'product__seller')


class OrderListView(LoginRequiredMixin, ListView):
    """Liste des commandes de l'utilisateur"""
    model = Order
    template_name = 'backend/client/orders/list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        return Order.objects.filter(
            Q(buyer=self.request.user) | Q(product__seller=self.request.user)
        ).select_related('product', 'buyer').order_by('-created_at')


class PaymentView(LoginRequiredMixin, TemplateView):
    """Processus de paiement"""
    template_name = 'backend/client/payments/payment.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(
            Order, 
            id=kwargs['order_id'], 
            buyer=request.user, 
            status='PENDING'
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = self.order
        context['payment_methods'] = Order.PAYMENT_METHODS
        return context
    
    def post(self, request, *args, **kwargs):
        payment_method = request.POST.get('payment_method')
        
        if not payment_method:
            messages.error(request, "Veuillez sélectionner un mode de paiement.")
            return self.get(request, *args, **kwargs)
        
        try:
            payment_result = process_payment(self.order, payment_method)
            
            if payment_result['success']:
                payment = Payment.objects.create(
                    order=self.order,
                    payment_reference=payment_result['reference'],
                    amount=self.order.total_amount,
                    status='PROCESSING',
                    provider_response=payment_result.get('data', {})
                )
                
                messages.success(request, "Paiement initié avec succès!")
                return redirect('backend:payment_success', pk=payment.id)
            else:
                messages.error(request, f"Erreur de paiement: {payment_result.get('error', 'Erreur inconnue')}")
                
        except Exception as e:
            messages.error(request, f"Erreur lors du traitement: {str(e)}")
        
        return self.get(request, *args, **kwargs)


class PaymentSuccessView(LoginRequiredMixin, DetailView):
    """Page de succès du paiement"""
    model = Payment
    template_name = 'backend/client/payments/success.html'
    context_object_name = 'payment'


class PaymentCancelView(LoginRequiredMixin, DetailView):
    """Page d'annulation du paiement"""
    model = Payment
    template_name = 'backend/client/payments/cancel.html'
    context_object_name = 'payment'


class ChatListView(LoginRequiredMixin, ListView):
    """Liste des conversations"""
    model = Chat
    template_name = 'backend/client/chat/list.html'
    context_object_name = 'chats'
    paginate_by = 20
    
    def get_queryset(self):
        return Chat.objects.filter(
            Q(buyer=self.request.user) | Q(seller=self.request.user),
            is_active=True
        ).select_related('product', 'buyer', 'seller').order_by('-updated_at')


class ChatDetailView(LoginRequiredMixin, DetailView):
    """Détail d'une conversation avec messages"""
    model = Chat
    template_name = 'backend/client/chat/detail.html'
    context_object_name = 'chat'
    
    def get_object(self):
        chat = get_object_or_404(Chat, id=self.kwargs['pk'])
        
        if self.request.user not in [chat.buyer, chat.seller]:
            raise PermissionDenied("Vous n'avez pas accès à cette conversation.")
        
        # Marquer les messages comme lus
        Message.objects.filter(
            chat=chat,
            is_read=False
        ).exclude(sender=self.request.user).update(is_read=True)
        
        return chat
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages'] = self.object.messages.select_related('sender').order_by('created_at')
        context['form'] = ChatMessageForm()
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ChatMessageForm(request.POST, request.FILES)
        
        if form.is_valid():
            message = form.save(commit=False)
            message.chat = self.object
            message.sender = request.user
            message.save()
            
            # Notifier l'autre utilisateur
            recipient = self.object.seller if request.user == self.object.buyer else self.object.buyer
            Notification.objects.create(
                user=recipient,
                type='MESSAGE',
                title='Nouveau message',
                message=f'Vous avez reçu un message concernant "{self.object.product.title}"',
                data={'chat_id': str(self.object.id)}
            )
            
            messages.success(request, "Message envoyé avec succès!")
            return redirect('backend:chat_detail', pk=self.object.id)
        
        return self.render_to_response(self.get_context_data(form=form))


class ChatCreateView(LoginRequiredMixin, CreateView):
    """Créer une nouvelle conversation"""
    model = Chat
    fields = []
    
    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, id=kwargs['product_id'], status='ACTIVE')
        
        if request.user == self.product.seller:
            messages.error(request, "Vous ne pouvez pas discuter avec vous-même.")
            return redirect('backend:product_detail', slug=self.product.slug)
        
        # Vérifier si une conversation existe déjà
        existing_chat = Chat.objects.filter(
            product=self.product,
            buyer=request.user,
            seller=self.product.seller
        ).first()
        
        if existing_chat:
            return redirect('backend:chat_detail', pk=existing_chat.id)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.product = self.product
        form.instance.buyer = self.request.user
        form.instance.seller = self.product.seller
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('backend:chat_detail', kwargs={'pk': self.object.id})


# Group Chat Views
class GroupChatListView(LoginRequiredMixin, ListView):
    """Liste des conversations de groupe"""
    model = GroupChat
    template_name = 'backend/visitor/chat/group_list.html'
    context_object_name = 'group_chats'
    paginate_by = 20
    
    def get_queryset(self):
        return GroupChat.objects.filter(
            participants=self.request.user,
            is_active=True
        ).prefetch_related('participants').order_by('-updated_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Count unread messages for each group chat
        for chat in context['group_chats']:
            chat.unread_count = GroupChatMessage.objects.filter(
                group_chat=chat
            ).exclude(
                read_by=self.request.user
            ).exclude(
                sender=self.request.user
            ).count()
        
        # Add statistics
        context['total_group_chats'] = self.get_queryset().count()
        context['unread_messages'] = sum(chat.unread_count for chat in context['group_chats'])
        
        # Add user types for filtering
        context['admin_users'] = User.objects.filter(user_type='ADMIN')
        context['staff_users'] = User.objects.filter(user_type='STAFF')
        context['client_users'] = User.objects.filter(user_type='CLIENT')
        
        return context


class GroupChatDetailView(LoginRequiredMixin, DetailView):
    """Détail d'une conversation de groupe avec messages"""
    model = GroupChat
    template_name = 'backend/visitor/chat/group_detail.html'
    context_object_name = 'group_chat'
    
    def get_object(self):
        group_chat = get_object_or_404(GroupChat, id=self.kwargs['pk'])
        
        # Vérifier si l'utilisateur est participant
        if not group_chat.participants.filter(id=self.request.user.id).exists():
            raise PermissionDenied("Vous n'avez pas accès à cette conversation de groupe.")
        
        # Marquer les messages comme lus
        unread_messages = GroupChatMessage.objects.filter(
            group_chat=group_chat
        ).exclude(
            read_by=self.request.user
        ).exclude(
            sender=self.request.user
        )
        
        for message in unread_messages:
            message.read_by.add(self.request.user)
        
        return group_chat
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages'] = self.object.group_messages.select_related('sender').order_by('created_at')
        context['form'] = GroupChatMessageForm()
        context['participants'] = self.object.participants.all()
        
        # Check if user is creator/admin of the group
        context['is_admin'] = (self.request.user == self.object.creator or 
                               self.request.user.user_type == 'ADMIN')
        
        # Get potential users to add to the group
        if context['is_admin']:
            existing_participants = self.object.participants.all()
            context['potential_users'] = User.objects.exclude(
                id__in=[user.id for user in existing_participants]
            )
        
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = GroupChatMessageForm(request.POST, request.FILES)
        
        if form.is_valid():
            message = form.save(commit=False)
            message.group_chat = self.object
            message.sender = request.user
            message.save()
            
            # Add sender to read_by
            message.read_by.add(request.user)
            
            # Update group chat timestamp
            self.object.updated_at = timezone.now()
            self.object.save(update_fields=['updated_at'])
            
            # Notify other participants
            for participant in self.object.participants.exclude(id=request.user.id):
                Notification.objects.create(
                    user=participant,
                    type='MESSAGE',
                    title=f'Nouveau message dans {self.object.name}',
                    message=f'{request.user.get_full_name()} a envoyé un message dans le groupe',
                    data={'group_chat_id': str(self.object.id)}
                )
            
            messages.success(request, "Message envoyé avec succès!")
            return redirect('backend:group_chat_detail', pk=self.object.id)
        
        return self.render_to_response(self.get_context_data(form=form))


class GroupChatCreateView(LoginRequiredMixin, CreateView):
    """Créer une nouvelle conversation de groupe"""
    model = GroupChat
    form_class = GroupChatForm
    template_name = 'backend/visitor/chat/group_create.html'
    
    def form_valid(self, form):
        form.instance.creator = self.request.user
        response = super().form_valid(form)
        
        # Add creator as participant
        self.object.participants.add(self.request.user)
        
        # Add selected participants
        participants = form.cleaned_data.get('selected_participants', [])
        if participants:
            self.object.participants.add(*participants)
        
        # Create welcome message
        GroupChatMessage.objects.create(
            group_chat=self.object,
            sender=self.request.user,
            message_type='SYSTEM',
            content=f"Groupe '{self.object.name}' créé par {self.request.user.get_full_name()}"
        )
        
        # Notify participants
        for participant in self.object.participants.exclude(id=self.request.user.id):
            Notification.objects.create(
                user=participant,
                type='MESSAGE',
                title=f'Nouveau groupe: {self.object.name}',
                message=f'{self.request.user.get_full_name()} vous a ajouté au groupe {self.object.name}',
                data={'group_chat_id': str(self.object.id)}
            )
        
        messages.success(self.request, f"Groupe '{self.object.name}' créé avec succès!")
        return response
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        return reverse('backend:group_chat_detail', kwargs={'pk': self.object.id})


class GroupChatAddUserView(LoginRequiredMixin, View):
    """Ajouter un utilisateur à un groupe"""
    
    def post(self, request, pk):
        group_chat = get_object_or_404(GroupChat, id=pk)
        
        # Vérifier si l'utilisateur est admin du groupe
        if request.user != group_chat.creator and request.user.user_type != 'ADMIN':
            messages.error(request, "Vous n'avez pas les droits pour ajouter des utilisateurs.")
            return redirect('backend:group_chat_detail', pk=group_chat.id)
        
        user_id = request.POST.get('user_id')
        if not user_id:
            messages.error(request, "Utilisateur non spécifié.")
            return redirect('backend:group_chat_detail', pk=group_chat.id)
        
        try:
            user = User.objects.get(id=user_id)
            
            # Vérifier si l'utilisateur est déjà dans le groupe
            if group_chat.participants.filter(id=user.id).exists():
                messages.warning(request, f"{user.get_full_name()} est déjà dans le groupe.")
                return redirect('backend:group_chat_detail', pk=group_chat.id)
            
            # Ajouter l'utilisateur
            group_chat.participants.add(user)
            
            # Créer message système
            GroupChatMessage.objects.create(
                group_chat=group_chat,
                sender=request.user,
                message_type='SYSTEM',
                content=f"{user.get_full_name()} a été ajouté au groupe par {request.user.get_full_name()}"
            )
            
            # Notifier l'utilisateur ajouté
            Notification.objects.create(
                user=user,
                type='MESSAGE',
                title=f'Ajouté au groupe: {group_chat.name}',
                message=f'{request.user.get_full_name()} vous a ajouté au groupe {group_chat.name}',
                data={'group_chat_id': str(group_chat.id)}
            )
            
            messages.success(request, f"{user.get_full_name()} a été ajouté au groupe.")
            
        except User.DoesNotExist:
            messages.error(request, "Utilisateur non trouvé.")
        
        return redirect('backend:group_chat_detail', pk=group_chat.id)


class GroupChatLeaveView(LoginRequiredMixin, View):
    """Quitter un groupe de discussion"""
    
    def post(self, request, pk):
        group_chat = get_object_or_404(GroupChat, id=pk)
        
        # Vérifier si l'utilisateur est dans le groupe
        if not group_chat.participants.filter(id=request.user.id).exists():
            messages.error(request, "Vous n'êtes pas membre de ce groupe.")
            return redirect('backend:group_chat_list')
        
        # Si c'est le créateur et qu'il y a d'autres participants
        if request.user == group_chat.creator and group_chat.participants.count() > 1:
            # Trouver un nouveau créateur
            new_creator = group_chat.participants.exclude(id=request.user.id).first()
            group_chat.creator = new_creator
            group_chat.save()
            
            # Message système pour le changement de créateur
            GroupChatMessage.objects.create(
                group_chat=group_chat,
                sender=request.user,
                message_type='SYSTEM',
                content=f"{new_creator.get_full_name()} est maintenant administrateur du groupe"
            )
        
        # Retirer l'utilisateur du groupe
        group_chat.participants.remove(request.user)
        
        # Message système pour le départ
        GroupChatMessage.objects.create(
            group_chat=group_chat,
            sender=request.user,
            message_type='SYSTEM',
            content=f"{request.user.get_full_name()} a quitté le groupe"
        )
        
        # Si plus de participants, désactiver le groupe
        if group_chat.participants.count() == 0:
            group_chat.is_active = False
            group_chat.save()
        
        messages.success(request, f"Vous avez quitté le groupe '{group_chat.name}'.")
        return redirect('backend:group_chat_list')


class ReviewCreateView(LoginRequiredMixin, CreateView):
    """Créer un avis après livraison"""
    model = Review
    form_class = ReviewForm
    template_name = 'backend/client/reviews/create.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(
            Order, 
            id=kwargs['order_id'], 
            buyer=request.user, 
            status='DELIVERED'
        )
        
        # Vérifier qu'un avis n'existe pas déjà
        if hasattr(self.order, 'review'):
            messages.info(request, "Vous avez déjà laissé un avis pour cette commande.")
            return redirect('backend:review_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.order = self.order
        form.instance.reviewer = self.request.user
        response = super().form_valid(form)
        
        # Notifier le vendeur
        seller = self.order.product.seller
        Notification.objects.create(
            user=seller,
            type='REVIEW',
            title='Nouvel avis reçu',
            message=f'Vous avez reçu un avis {form.instance.overall_rating}★ pour "{self.order.product.title}"',
            data={'review_id': str(self.object.id)}
        )
        
        messages.success(self.request, "Merci pour votre avis!")
        return response
    
    def get_success_url(self):
        return reverse('backend:order_detail', kwargs={'pk': self.order.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = self.order
        return context


class ReviewListView(ListView):
    """Liste des avis publics"""
    model = Review
    template_name = 'backend/client/reviews/list.html'
    context_object_name = 'reviews'
    paginate_by = 20
    
    def get_queryset(self):
        return Review.objects.filter(
            is_verified=True
        ).select_related('reviewer', 'order__product').order_by('-created_at')


class ReviewDetailView(DetailView):
    """Détail d'un avis public"""
    model = Review
    template_name = 'backend/client/reviews/detail.html'
    context_object_name = 'review'
    
    def get_queryset(self):
        return Review.objects.filter(is_verified=True).select_related('reviewer', 'order__product')


class PickupPointListView(ListView):
    """Liste des points de retrait"""
    model = PickupPoint
    template_name = 'backend/client/pickup/list.html'
    context_object_name = 'pickup_points'
    
    def get_queryset(self):
        return PickupPoint.objects.filter(is_active=True).order_by('city', 'name')


class PickupPointDetailView(DetailView):
    """Détail d'un point de retrait"""
    model = PickupPoint
    template_name = 'backend/client/pickup/detail.html'
    context_object_name = 'pickup_point'
    
    def get_queryset(self):
        return PickupPoint.objects.filter(is_active=True)


class SearchView(TemplateView):
    """Recherche avancée avec suggestions"""
    template_name = 'backend/client/search/results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        
        if query:
            # Recherche dans les produits
            products = Product.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query),
                status='ACTIVE'
            ).select_related('category', 'seller').prefetch_related('images')
            
            # Pagination
            paginator = Paginator(products, 24)
            page_number = self.request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            
            context.update({
                'query': query,
                'products': page_obj,
                'total_results': products.count(),
                'suggestions': self.get_search_suggestions(query)
            })
            
            # Enregistrer la recherche
            SearchHistory.objects.create(
                user=self.request.user if self.request.user.is_authenticated else None,
                search_term=query,
                results_count=products.count(),
                ip_address=self.request.META.get('REMOTE_ADDR', '127.0.0.1')
            )
        
        return context
    
    def get_search_suggestions(self, query):
        """Générer des suggestions de recherche"""
        # Recherche dans les catégories
        categories = Category.objects.filter(
            name__icontains=query,
            is_active=True
        )[:5]
        
        # Termes de recherche populaires
        popular_searches = SearchHistory.objects.filter(
            search_term__icontains=query
        ).values('search_term').annotate(
            count=Count('search_term')
        ).order_by('-count')[:5]
        
        return {
            'categories': categories,
            'popular_searches': [item['search_term'] for item in popular_searches]
        }


class AboutView(TemplateView):
    """Page À propos"""
    template_name = 'backend/visitor/pages/about.html'


class ContactView(FormView):
    """Page de contact"""
    template_name = 'backend/visitor/pages/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('backend:contact')
    
    def form_valid(self, form):
        # Envoyer l'email de contact
        send_mail(
            subject=f"Contact VGK: {form.cleaned_data['subject']}",
            message=f"""
Nouveau message de contact:

Nom: {form.cleaned_data['name']}
Email: {form.cleaned_data['email']}
Sujet: {form.cleaned_data['subject']}

Message:
{form.cleaned_data['message']}
            """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['support@videgrenier-kamer.com'],
            fail_silently=False,
        )
        
        messages.success(self.request, "Votre message a été envoyé avec succès!")
        return super().form_valid(form)


class HelpView(TemplateView):
    """Page d'aide"""
    template_name = 'backend/visitor/pages/help.html'


class TermsView(TemplateView):
    """Conditions d'utilisation"""
    template_name = 'backend/visitor/pages/terms.html'


class PrivacyView(TemplateView):
    """Politique de confidentialité"""
    template_name = 'backend/visitor/pages/privacy.html'


class PhoneVerificationView(LoginRequiredMixin, TemplateView):
    """Vérification du numéro de téléphone"""
    template_name = 'backend/visitor/auth/verify_phone.html'
    
    def post(self, request):
        code = request.POST.get('verification_code')
        
        if self.verify_sms_code(request.user.phone, code):
            request.user.phone_verified = True
            request.user.save()
            messages.success(request, "Numéro de téléphone vérifié avec succès!")
            return redirect('backend:dashboard')
        else:
            messages.error(request, "Code de vérification incorrect.")
            return self.get(request)
    
    def verify_sms_code(self, phone, code):
        # Implémentation factice - à remplacer par la vraie vérification
        return code == '123456'  # Code de test


# ============= VUES AJAX =============

class ProductViewAjax(View):
    """Incrémenter les vues produit via AJAX"""
    
    def post(self, request, pk):
        try:
            product = get_object_or_404(Product, id=pk)
            Product.objects.filter(id=pk).update(views_count=F('views_count') + 1)
            return JsonResponse({'success': True, 'views': product.views_count + 1})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class FavoriteToggleView(LoginRequiredMixin, View):
    """Ajouter/retirer des favoris via AJAX"""
    
    def post(self, request, slug):
        try:
            product = get_object_or_404(Product, slug=slug)
            favorite, created = Favorite.objects.get_or_create(
                user=request.user,
                product=product
            )
            
            if not created:
                favorite.delete()
                is_favorite = False
            else:
                is_favorite = True
            
            return JsonResponse({
                'success': True, 
                'is_favorite': is_favorite,
                'favorites_count': product.favorited_by.count()
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class NotificationListAjax(LoginRequiredMixin, View):
    """Liste des notifications via AJAX"""
    
    def get(self, request):
        notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')[:10]
        
        data = [{
            'id': str(notif.id),
            'title': notif.title,
            'message': notif.message,
            'type': notif.type,
            'created_at': notif.created_at.isoformat(),
            'data': notif.data
        } for notif in notifications]
        
        return JsonResponse({'notifications': data})


class NotificationMarkReadAjax(LoginRequiredMixin, View):
    """Marquer une notification comme lue"""
    
    def post(self, request, pk):
        try:
            notification = get_object_or_404(
                Notification, 
                id=pk, 
                user=request.user
            )
            notification.is_read = True
            notification.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


# ============= WEBHOOKS PAIEMENT =============

@method_decorator(csrf_exempt, name='dispatch')
class CampayWebhookView(View):
    """Webhook pour les notifications Campay"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            reference = data.get('reference')
            status = data.get('status')
            
            # Trouver le paiement correspondant
            payment = Payment.objects.get(payment_reference=reference)
            
            if status == 'SUCCESSFUL':
                payment.status = 'COMPLETED'
                payment.completed_at = timezone.now()
                payment.order.status = 'PAID'
                payment.order.save()
                
                # Notifier le vendeur
                seller = payment.order.product.seller
                Notification.objects.create(
                    user=seller,
                    type='ORDER',
                    title='Nouveau paiement reçu',
                    message=f'Vous avez reçu un paiement de {payment.amount} FCFA pour "{payment.order.product.title}"',
                    data={'order_id': str(payment.order.id)}
                )
                
            elif status == 'FAILED':
                payment.status = 'FAILED'
                payment.order.status = 'CANCELLED'
                payment.order.save()
                
                # Libérer le produit
                payment.order.product.status = 'ACTIVE'
                payment.order.product.save()
            
            payment.save()
            return HttpResponse('OK')
            
        except Exception as e:
            return HttpResponse(f'Error: {str(e)}', status=400)


@method_decorator(csrf_exempt, name='dispatch')
class OrangeMoneyWebhookView(View):
    """Webhook pour Orange Money"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            # Logique similaire à Campay
            return HttpResponse('OK')
        except Exception as e:
            return HttpResponse(f'Error: {str(e)}', status=400)


@method_decorator(csrf_exempt, name='dispatch')
class MTNMoneyWebhookView(View):
    """Webhook pour MTN Mobile Money"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            # Logique similaire à Campay
            return HttpResponse('OK')
        except Exception as e:
            return HttpResponse(f'Error: {str(e)}', status=400)


# ==============================================================================
# VISITOR PURCHASE VIEWS (No Login Required)
# ==============================================================================

from django.conf import settings
import requests
import os

class VisitorProductDetailView(DetailView):
    """Vue détaillée d'un produit pour les visiteurs avec options d'achat et panier"""
    model = Product
    template_name = 'backend/visitor/products/visitor_detail.html'
    context_object_name = 'product'
    
    def get_object(self):
        # Try to get by slug first, then by pk
        if 'slug' in self.kwargs:
            return get_object_or_404(
                Product.objects.filter(status='ACTIVE').select_related('category', 'seller').prefetch_related('images'),
                slug=self.kwargs['slug']
            )
        elif 'pk' in self.kwargs:
            return get_object_or_404(
                Product.objects.filter(status='ACTIVE').select_related('category', 'seller').prefetch_related('images'),
                pk=self.kwargs['pk']
            )
        else:
            raise Http404("Product not found")
    
    def get_queryset(self):
        return Product.objects.filter(status='ACTIVE').select_related(
            'category', 'seller'
        ).prefetch_related('images')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get or create visitor cart
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        
        visitor_cart, created = VisitorCart.objects.get_or_create(
            session_key=session_key,
            defaults={'session_key': session_key}
        )
        
        # Get admin WhatsApp number from settings or environment
        admin_whatsapp = getattr(settings, 'ADMIN_WHATSAPP', os.getenv('ADMIN_WHATSAPP', '237694638412'))
        
        # Create WhatsApp message for single product
        product = self.object
        single_whatsapp_message = f"Bonjour! Je suis intéressé(e) par ce produit:\n\n" \
                                 f"*{product.title}*\n" \
                                 f"Prix: {product.price:,.0f} FCFA\n" \
                                 f"Lien: {self.request.build_absolute_uri()}\n\n" \
                                 f"Pouvez-vous me donner plus d'informations?"
        
        # Create WhatsApp message for cart
        cart_whatsapp_message = self._generate_cart_whatsapp_message(visitor_cart, admin_whatsapp)
        
        # Check if product is in cart
        is_in_cart = visitor_cart.items.filter(product=product).exists()
        cart_item = None
        if is_in_cart:
            cart_item = visitor_cart.items.get(product=product)
        
        # Get visitor interaction data
        is_favorited = VisitorFavorite.objects.filter(
            session_key=session_key, product=product
        ).exists()
        
        is_comparing = VisitorCompare.objects.filter(
            session_key=session_key, product=product
        ).exists()
        
        # Get visitor likes data
        user_like = None
        if self.request.user.is_authenticated:
            user_like_obj = ProductLike.objects.filter(
                product=product, user=self.request.user
            ).first()
            user_like = user_like_obj.like_type if user_like_obj else None
        else:
            visitor_like_obj = ProductLike.objects.filter(
                product=product, 
                visitor_ip=get_client_ip(self.request),
                session_key=session_key
            ).first()
            user_like = visitor_like_obj.like_type if visitor_like_obj else None
        
        # Get like counts
        likes_count = ProductLike.objects.filter(product=product, like_type='LIKE').count()
        dislikes_count = ProductLike.objects.filter(product=product, like_type='DISLIKE').count()
        
        # Get comments for this product
        comments = ProductComment.objects.filter(
            product=product, 
            parent=None,  # Only top-level comments
            is_approved=True
        ).prefetch_related('replies').order_by('-created_at')[:10]
        
        # Get total counts for visitor
        total_favorites = VisitorFavorite.objects.filter(session_key=session_key).count()
        total_compares = VisitorCompare.objects.filter(session_key=session_key).count()
        
        context.update({
            'admin_whatsapp': admin_whatsapp,
            'single_whatsapp_message': single_whatsapp_message,
            'single_whatsapp_url': f"https://wa.me/{admin_whatsapp}?text={urllib.parse.quote(single_whatsapp_message)}",
            'cart_whatsapp_message': cart_whatsapp_message,
            'cart_whatsapp_url': f"https://wa.me/{admin_whatsapp}?text={urllib.parse.quote(cart_whatsapp_message)}",
            'campay_enabled': bool(os.getenv('CAMPAY_API_KEY')),
            'visitor_cart': visitor_cart,
            'is_in_cart': is_in_cart,
            'cart_item': cart_item,
            'delivery_cost': Decimal('2000'),
            'similar_products': Product.objects.filter(
                category=product.category,
                status='ACTIVE'
            ).exclude(id=product.id)[:6],
            # Visitor interaction data
            'is_favorited': is_favorited,
            'is_comparing': is_comparing,
            'user_like': user_like,
            'likes_count': likes_count,
            'dislikes_count': dislikes_count,
            'comments': comments,
            'total_favorites': total_favorites,
            'total_compares': total_compares,
            'comments_count': ProductComment.objects.filter(product=product, is_approved=True).count(),
        })
        return context
    
    def _generate_cart_whatsapp_message(self, cart, admin_whatsapp):
        """Generate WhatsApp message with cart contents"""
        if not cart.items.exists():
            return "Bonjour! Je souhaite obtenir des informations sur vos produits."
        
        message = "Bonjour! Je suis intéressé(e) par ces produits:\n\n"
        
        for item in cart.items.all():
            message += f"🛍️ *{item.product.title}*\n"
            message += f"   Quantité: {item.quantity}\n"
            message += f"   Prix unitaire: {item.unit_price:,.0f} FCFA\n"
            message += f"   Sous-total: {item.total_price:,.0f} FCFA\n\n"
        
        message += f"💰 Total produits: {cart.total_amount:,.0f} FCFA\n"
        if cart.delivery_method == 'DELIVERY':
            message += f"🚚 Frais de livraison: {cart.delivery_cost:,.0f} FCFA\n"
            message += f"💳 Total final: {cart.final_total:,.0f} FCFA\n"
        else:
            message += f"📍 Mode: Retrait en point de collecte\n"
        
        message += f"\nPouvez-vous confirmer ma commande?\n"
        message += f"Merci!"
        
        return message


def visitor_order_create(request, product_id):
    """Créer une commande visiteur sans connexion"""
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id, status='ACTIVE')
            
            # Récupérer les données du formulaire
            visitor_name = request.POST.get('visitor_name', '').strip()
            visitor_email = request.POST.get('visitor_email', '').strip()
            visitor_phone = request.POST.get('visitor_phone', '').strip()
            payment_method = request.POST.get('payment_method')
            delivery_method = request.POST.get('delivery_method', 'PICKUP')
            delivery_address = request.POST.get('delivery_address', '').strip()
            whatsapp_preferred = request.POST.get('whatsapp_preferred') == 'on'
            notes = request.POST.get('notes', '').strip()
            quantity = int(request.POST.get('quantity', 1))
            
            # Validation basique
            if not all([visitor_name, visitor_phone, payment_method]):
                messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
                return redirect('backend:visitor_product_detail', pk=product_id)
            
            if quantity < 1:
                messages.error(request, 'La quantité doit être au moins 1.')
                return redirect('backend:visitor_product_detail', pk=product_id)
            
            # Calculer les coûts
            product_total = product.price * quantity
            delivery_cost = 0
            if delivery_method == 'DELIVERY':
                delivery_cost = Decimal('2000')  # Frais de livraison standard
            
            commission_rate = Decimal(os.getenv('VGK_COMMISSION_RATE', '0.08'))
            commission_amount = product_total * commission_rate
            total_amount = product_total + delivery_cost
            
            # Créer la commande
            order = Order.objects.create(
                product=product,
                quantity=quantity,
                total_amount=total_amount,
                commission_amount=commission_amount,
                delivery_cost=delivery_cost,
                payment_method=payment_method,
                delivery_method=delivery_method,
                delivery_address=delivery_address,
                visitor_name=visitor_name,
                visitor_email=visitor_email,
                visitor_phone=visitor_phone,
                whatsapp_preferred=whatsapp_preferred,
                notes=notes,
                status='PENDING'
            )
            
            # Rediriger selon le mode de paiement
            if payment_method == 'CASH_ON_DELIVERY':
                # Paiement à la livraison - confirmer la commande
                order.status = 'PAID' if delivery_method == 'PICKUP' else 'PROCESSING'
                order.save()
                
                # Envoyer notification à l'admin (si email configuré)
                try:
                    from .views_admin import EnhancedEmailNotificationService
                    email_service = EnhancedEmailNotificationService()
                    email_service.send_visitor_order_notification(order)
                except Exception as e:
                    print(f"Erreur envoi email: {e}")
                
                messages.success(request, 'Votre commande a été créée avec succès!')
                return redirect('backend:visitor_order_success', order_id=order.id)
                
            elif payment_method in ['CAMPAY', 'ORANGE_MONEY', 'MTN_MONEY']:
                # Paiement mobile - rediriger vers le processus de paiement
                return redirect('backend:visitor_payment_process', order_id=order.id)
            
            else:
                messages.error(request, 'Méthode de paiement non supportée.')
                return redirect('backend:visitor_product_detail', pk=product_id)
                
        except Exception as e:
            messages.error(request, f'Erreur lors de la création de la commande: {str(e)}')
            return redirect('backend:visitor_product_detail', pk=product_id)
    
    return redirect('backend:visitor_product_detail', pk=product_id)


def visitor_payment_process(request, order_id):
    """Traiter le paiement mobile pour les visiteurs"""
    order = get_object_or_404(Order, id=order_id, buyer__isnull=True)
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        
        if not phone_number:
            messages.error(request, 'Veuillez entrer votre numéro de téléphone.')
            return render(request, 'backend/visitor/orders/visitor_payment.html', {'order': order})


# ============= VISITOR CART OPERATIONS =============

@require_POST
def visitor_add_to_cart(request, product_id):
    """Add product to visitor cart"""
    try:
        product = get_object_or_404(Product, id=product_id, status='ACTIVE')
        
        # Get or create session
        if not request.session.session_key:
            request.session.create()
        
        # Get or create visitor cart
        visitor_cart, created = VisitorCart.objects.get_or_create(
            session_key=request.session.session_key
        )
        
        # Get quantity from request
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            quantity = 1
        
        # Add or update cart item
        cart_item, item_created = VisitorCartItem.objects.get_or_create(
            cart=visitor_cart,
            product=product,
            defaults={
                'quantity': quantity,
                'unit_price': product.price
            }
        )
        
        if not item_created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{product.title} ajouté au panier',
            'cart_items': visitor_cart.total_items,
            'cart_total': float(visitor_cart.total_amount)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


@require_POST
def visitor_update_cart_item(request, item_id):
    """Update visitor cart item quantity"""
    try:
        if not request.session.session_key:
            return JsonResponse({'success': False, 'message': 'Session non trouvée'})
        
        cart_item = get_object_or_404(
            VisitorCartItem,
            id=item_id,
            cart__session_key=request.session.session_key
        )
        
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity <= 0:
            cart_item.delete()
            message = 'Produit retiré du panier'
        else:
            cart_item.quantity = quantity
            cart_item.save()
            message = 'Quantité mise à jour'
        
        cart = cart_item.cart
        
        return JsonResponse({
            'success': True,
            'message': message,
            'cart_items': cart.total_items,
            'cart_total': float(cart.total_amount),
            'item_total': float(cart_item.total_price) if quantity > 0 else 0
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


@require_POST
def visitor_remove_cart_item(request, item_id):
    """Remove item from visitor cart"""
    try:
        if not request.session.session_key:
            return JsonResponse({'success': False, 'message': 'Session non trouvée'})
        
        cart_item = get_object_or_404(
            VisitorCartItem,
            id=item_id,
            cart__session_key=request.session.session_key
        )
        
        cart = cart_item.cart
        cart_item.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Produit retiré du panier',
            'cart_items': cart.total_items,
            'cart_total': float(cart.total_amount)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


def visitor_cart_view(request):
    """Display visitor cart"""
    if not request.session.session_key:
        request.session.create()
    
    try:
        visitor_cart = VisitorCart.objects.get(session_key=request.session.session_key)
    except VisitorCart.DoesNotExist:
        visitor_cart = VisitorCart.objects.create(session_key=request.session.session_key)
    
    context = {
        'visitor_cart': visitor_cart,
        'cart_items': visitor_cart.items.select_related('product').all(),
        'delivery_cost': Decimal('2000'),
    }
    
    return render(request, 'backend/visitor/cart.html', context)


@require_POST 
def visitor_update_cart_info(request):
    """Update visitor cart information (delivery, contact info)"""
    try:
        if not request.session.session_key:
            return JsonResponse({'success': False, 'message': 'Session non trouvée'})
        
        visitor_cart = get_object_or_404(VisitorCart, session_key=request.session.session_key)
        
        # Update cart information
        visitor_cart.visitor_name = request.POST.get('visitor_name', '')
        visitor_cart.visitor_email = request.POST.get('visitor_email', '')
        visitor_cart.visitor_phone = request.POST.get('visitor_phone', '')
        visitor_cart.delivery_method = request.POST.get('delivery_method', 'PICKUP')
        visitor_cart.delivery_address = request.POST.get('delivery_address', '')
        visitor_cart.whatsapp_preferred = request.POST.get('whatsapp_preferred') == 'on'
        visitor_cart.notes = request.POST.get('notes', '')
        visitor_cart.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Informations mises à jour',
            'final_total': float(visitor_cart.final_total)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


# ============= VISITOR CART CHECKOUT =============

def visitor_cart_checkout(request):
    """Checkout visitor cart"""
    if not request.session.session_key:
        messages.error(request, 'Panier introuvable')
        return redirect('backend:home')
    
    try:
        visitor_cart = VisitorCart.objects.get(session_key=request.session.session_key)
        
        if not visitor_cart.items.exists():
            messages.error(request, 'Votre panier est vide')
            return redirect('backend:visitor_cart')
        
        if request.method == 'POST':
            # Create orders for each cart item
            orders = []
            
            # Update cart info from form
            visitor_cart.visitor_name = request.POST.get('visitor_name', '')
            visitor_cart.visitor_email = request.POST.get('visitor_email', '')
            visitor_cart.visitor_phone = request.POST.get('visitor_phone', '')
            visitor_cart.delivery_method = request.POST.get('delivery_method', 'PICKUP')
            visitor_cart.delivery_address = request.POST.get('delivery_address', '')
            visitor_cart.whatsapp_preferred = request.POST.get('whatsapp_preferred') == 'on'
            visitor_cart.notes = request.POST.get('notes', '')
            payment_method = request.POST.get('payment_method', 'CASH_ON_DELIVERY')
            visitor_cart.save()
            
            # Validate required fields
            if not all([visitor_cart.visitor_name, visitor_cart.visitor_phone]):
                messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
                return render(request, 'backend/visitor/checkout.html', {'visitor_cart': visitor_cart})
            
            # Calculate delivery cost per order (split equally)
            total_delivery_cost = visitor_cart.delivery_cost
            items_count = visitor_cart.items.count()
            delivery_per_order = total_delivery_cost / items_count if items_count > 0 else Decimal('0')
            
            with transaction.atomic():
                for cart_item in visitor_cart.items.all():
                    # Calculate totals
                    product_total = cart_item.total_price
                    commission_rate = Decimal('0.08')
                    commission_amount = product_total * commission_rate
                    total_amount = product_total + delivery_per_order
                    
                    # Create order
                    order = Order.objects.create(
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        total_amount=total_amount,
                        commission_amount=commission_amount,
                        delivery_cost=delivery_per_order,
                        payment_method=payment_method,
                        delivery_method=visitor_cart.delivery_method,
                        delivery_address=visitor_cart.delivery_address,
                        visitor_name=visitor_cart.visitor_name,
                        visitor_email=visitor_cart.visitor_email,
                        visitor_phone=visitor_cart.visitor_phone,
                        whatsapp_preferred=visitor_cart.whatsapp_preferred,
                        notes=visitor_cart.notes,
                        status='PENDING'
                    )
                    orders.append(order)
                
                # Handle payment method
                if payment_method == 'CASH_ON_DELIVERY':
                    # Update all orders to paid/processing
                    for order in orders:
                        order.status = 'PAID' if visitor_cart.delivery_method == 'PICKUP' else 'PROCESSING'
                        order.save()
                    
                    # Clear cart
                    visitor_cart.items.all().delete()
                    
                    # Send notifications to admin
                    try:
                        self._send_cart_order_notifications(orders, visitor_cart)
                    except Exception as e:
                        print(f"Erreur envoi notification: {e}")
                    
                    messages.success(request, f'Vos {len(orders)} commandes ont été créées avec succès!')
                    return redirect('backend:visitor_cart_success', cart_session=request.session.session_key)
                
                elif payment_method in ['CAMPAY']:
                    # Store orders in session for payment processing
                    request.session['pending_orders'] = [str(order.id) for order in orders]
                    return redirect('backend:visitor_cart_payment')
                
        context = {
            'visitor_cart': visitor_cart,
            'cart_items': visitor_cart.items.select_related('product').all(),
        }
        
        return render(request, 'backend/visitor/checkout.html', context)
        
    except VisitorCart.DoesNotExist:
        messages.error(request, 'Panier introuvable')
        return redirect('backend:home')


def _send_cart_order_notifications(orders, cart):
    """Send notifications to admin for cart orders"""
    admin_users = User.objects.filter(user_type='ADMIN')
    
    for admin in admin_users:
        Notification.objects.create(
            user=admin,
            type='ORDER',
            title=f'Nouvelles commandes visiteur ({len(orders)})',
            message=f'{cart.visitor_name} a passé {len(orders)} commandes pour un total de {cart.final_total:,.0f} FCFA',
            data={
                'order_ids': [str(order.id) for order in orders],
                'visitor_name': cart.visitor_name,
                'visitor_phone': cart.visitor_phone,
                'total_amount': float(cart.final_total)
            }
        )


# ============= PRODUCT REPORTING =============

@require_POST
def visitor_report_product(request, product_id):
    """Report a product"""
    try:
        product = get_object_or_404(Product, id=product_id)
        
        report_type = request.POST.get('report_type')
        description = request.POST.get('description', '').strip()
        reporter_email = request.POST.get('reporter_email', '').strip()
        
        if not all([report_type, description]):
            return JsonResponse({
                'success': False,
                'message': 'Veuillez remplir tous les champs obligatoires'
            })
        
        # Create product report
        report = ProductReport.objects.create(
            product=product,
            reporter_ip=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            reporter_email=reporter_email,
            report_type=report_type,
            description=description
        )
        
        # Send notification to admins
        admin_users = User.objects.filter(user_type='ADMIN')
        for admin in admin_users:
            Notification.objects.create(
                user=admin,
                type='SYSTEM',
                title='Produit signalé',
                message=f'Le produit "{product.title}" a été signalé pour: {report.get_report_type_display()}',
                data={
                    'product_id': str(product.id),
                    'report_id': str(report.id),
                    'report_type': report_type,
                    'reporter_ip': report.reporter_ip
                }
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Signalement envoyé. Nos équipes vont examiner ce produit.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


# ============= VISITOR PAYMENT & RECEIPTS =============

def visitor_cart_payment(request):
    """Process payment for visitor cart"""
    if not request.session.get('pending_orders'):
        messages.error(request, 'Aucune commande en attente de paiement')
        return redirect('backend:visitor_cart')
    
    order_ids = request.session['pending_orders']
    orders = Order.objects.filter(id__in=order_ids)
    total_amount = sum(order.total_amount for order in orders)
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        
        if not phone_number:
            messages.error(request, 'Veuillez entrer votre numéro de téléphone.')
            return render(request, 'backend/visitor/payment.html', {
                'orders': orders,
                'total_amount': total_amount
            })
        
        try:
            # Process Campay payment for total amount
            payment_response = initiate_campay_payment_bulk(orders, phone_number)
            
            if payment_response.get('status') == 'success':
                # Create payment record
                for order in orders:
                    Payment.objects.create(
                        order=order,
                        payment_reference=payment_response.get('reference'),
                        amount=order.total_amount,
                        status='PROCESSING',
                        provider_response=payment_response
                    )
                
                # Clear pending orders
                del request.session['pending_orders']
                
                messages.success(request, 'Paiement initié. Suivez les instructions sur votre téléphone.')
                return redirect('backend:visitor_cart_success', cart_session=request.session.session_key)
            else:
                messages.error(request, f'Erreur de paiement: {payment_response.get("message", "Erreur inconnue")}')
        
        except Exception as e:
            messages.error(request, f'Erreur lors du paiement: {str(e)}')
    
    context = {
        'orders': orders,
        'total_amount': total_amount,
    }
    
    return render(request, 'backend/visitor/payment.html', context)


def visitor_cart_success(request, cart_session):
    """Success page for visitor cart orders"""
    # Get orders for this session
    orders = Order.objects.filter(
        visitor_phone__isnull=False,
        created_at__gte=timezone.now() - timedelta(hours=1)
    ).order_by('-created_at')
    
    # Filter by session if available
    if cart_session and hasattr(request, 'session') and request.session.session_key == cart_session:
        # Additional filtering if needed
        pass
    
    context = {
        'orders': orders[:10],  # Show recent orders
        'can_download_receipt': True,
    }
    
    return render(request, 'backend/visitor/success.html', context)


def visitor_download_receipt(request):
    """Generate and download receipt for visitor orders"""
    order_ids = request.GET.getlist('order_ids')
    
    if not order_ids:
        messages.error(request, 'Aucune commande sélectionnée')
        return redirect('backend:home')
    
    orders = Order.objects.filter(id__in=order_ids, visitor_phone__isnull=False)
    
    if not orders.exists():
        messages.error(request, 'Commandes introuvables')
        return redirect('backend:home')
    
    # Generate receipt
    from django.template.loader import render_to_string
    from django.http import HttpResponse
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from io import BytesIO
    import qrcode
    import base64
    
    try:
        # Create PDF
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Generate QR code for receipt verification
        receipt_id = f"VGK-{timezone.now().strftime('%Y%m%d%H%M')}-{orders.first().id}"
        qr_data = f"VGK Receipt: {receipt_id}\nTotal: {sum(order.total_amount for order in orders):,.0f} FCFA\nDate: {timezone.now().strftime('%d/%m/%Y %H:%M')}\nCustomer: {orders.first().visitor_name}"
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Generate QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Enhanced receipt layout
        y = 750
        
        # Header
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, y, "VIDÉ-GRENIER KAMER")
        p.setFont("Helvetica", 10)
        y -= 15
        p.drawString(50, y, "Marketplace camerounaise de seconde main")
        y -= 10
        p.drawString(50, y, "📞 +237 694 63 84 12 | 📧 support@videgrenier-kamer.com")
        
        # Receipt info
        y -= 30
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "REÇU DE COMMANDE")
        
        p.setFont("Helvetica", 10)
        y -= 20
        p.drawString(50, y, f"Date: {timezone.now().strftime('%d/%m/%Y %H:%M')}")
        y -= 15
        p.drawString(50, y, f"Numéro de reçu: {receipt_id}")
        
        # Customer info
        y -= 25
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Informations client")
        p.setFont("Helvetica", 10)
        y -= 15
        p.drawString(50, y, f"Nom: {orders.first().visitor_name}")
        y -= 15
        p.drawString(50, y, f"Téléphone: {orders.first().visitor_phone}")
        if orders.first().visitor_email:
            y -= 15
            p.drawString(50, y, f"Email: {orders.first().visitor_email}")
        
        # Orders details
        y -= 25
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Détail des commandes")
        p.setFont("Helvetica", 10)
        y -= 15
        
        # Table header
        p.drawString(50, y, "Produit")
        p.drawString(250, y, "Qté")
        p.drawString(300, y, "Prix unitaire")
        p.drawString(400, y, "Total")
        p.drawString(480, y, "N° Commande")
        y -= 5
        p.line(50, y, 550, y)  # Line under header
        y -= 10
        
        total = Decimal('0')
        for order in orders:
            # Truncate long product titles
            title = order.product.title[:25] + "..." if len(order.product.title) > 25 else order.product.title
            p.drawString(50, y, title)
            p.drawString(250, y, str(order.quantity))
            p.drawString(300, y, f"{order.product.price:,.0f} FCFA")
            p.drawString(400, y, f"{order.total_amount:,.0f} FCFA")
            p.drawString(480, y, order.order_number)
            total += order.total_amount
            y -= 15
        
        # Total
        y -= 10
        p.line(50, y, 550, y)  # Line above total
        y -= 15
        p.setFont("Helvetica-Bold", 12)
        p.drawString(400, y, f"TOTAL GÉNÉRAL: {total:,.0f} FCFA")
        
        # QR Code
        y -= 40
        p.setFont("Helvetica", 10)
        p.drawString(50, y, "Code QR pour vérification:")
        
        # Draw QR code (simplified - in real implementation you'd need to handle image drawing)
        from reportlab.lib.utils import ImageReader
        qr_image = ImageReader(qr_buffer)
        p.drawImage(qr_image, 50, y-100, width=80, height=80)
        
        # Footer
        y -= 120
        p.setFont("Helvetica", 8)
        p.drawString(50, y, "Merci pour votre confiance !")
        y -= 10
        p.drawString(50, y, "Ce reçu confirme vos commandes. Vous serez contacté pour les modalités de livraison.")
        y -= 10
        p.drawString(50, y, "Pour toute question: +237 694 63 84 12 ou support@videgrenier-kamer.com")
        y -= 15
        p.line(50, y, 550, y)
        y -= 10
        p.drawString(50, y, "Vidé-Grenier Kamer - Fièrement camerounais 🇨🇲")
        
        p.save()
        buffer.seek(0)
        
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="recu_vgk_{timezone.now().strftime("%Y%m%d_%H%M")}.pdf"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du reçu: {str(e)}')
        return redirect('backend:home')


# Helper function for bulk Campay payment
def initiate_campay_payment_bulk(orders, phone_number):
    """Initiate Campay payment for multiple orders"""
    try:
        total_amount = sum(order.total_amount for order in orders)
        
        # Use existing Campay integration
        from .utils import initiate_campay_payment
        
        # Create a temporary order with total amount for payment processing
        main_order = orders.first()
        payment_data = {
            'amount': float(total_amount),
            'phone': phone_number,
            'description': f'Commande VGK - {len(orders)} articles'
        }
        
        return initiate_campay_payment(main_order, phone_number)
        
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


# ============= VISITOR CART AJAX ENDPOINTS =============

def visitor_cart_status(request):
    """Get visitor cart status for widget"""
    try:
        if not request.session.session_key:
            return JsonResponse({'items': 0, 'total': 0})
        
        visitor_cart = VisitorCart.objects.filter(session_key=request.session.session_key).first()
        
        if visitor_cart:
            return JsonResponse({
                'items': visitor_cart.total_items,
                'total': float(visitor_cart.final_total)
            })
        else:
            return JsonResponse({'items': 0, 'total': 0})
            
    except Exception as e:
        return JsonResponse({'items': 0, 'total': 0})


def visitor_cart_preview(request):
    """Get visitor cart preview for modal"""
    try:
        if not request.session.session_key:
            return JsonResponse({'items': [], 'total': '0'})
        
        visitor_cart = VisitorCart.objects.filter(session_key=request.session.session_key).first()
        
        if visitor_cart and visitor_cart.items.exists():
            items = []
            for item in visitor_cart.items.select_related('product'):
                items.append({
                    'title': item.product.title[:30] + '...' if len(item.product.title) > 30 else item.product.title,
                    'quantity': item.quantity,
                    'total': f"{item.total_price:,.0f}"
                })
            
            return JsonResponse({
                'items': items,
                'total': f"{visitor_cart.final_total:,.0f}"
            })
        else:
            return JsonResponse({'items': [], 'total': '0'})
            
    except Exception as e:
        return JsonResponse({'items': [], 'total': '0'})


# ============= VISITOR FAVORITES & INTERACTIONS =============

@require_POST  
def visitor_toggle_favorite(request, product_id):
    """Toggle favorite for visitor"""
    try:
        if not request.session.session_key:
            request.session.create()
        
        product = get_object_or_404(Product, id=product_id, status='ACTIVE')
        session_key = request.session.session_key
        
        favorite, created = VisitorFavorite.objects.get_or_create(
            session_key=session_key,
            product=product
        )
        
        if not created:
            favorite.delete()
            is_favorited = False
            message = f"{product.title} retiré des favoris"
        else:
            is_favorited = True
            message = f"{product.title} ajouté aux favoris"
        
        # Get total favorites count for this visitor
        total_favorites = VisitorFavorite.objects.filter(session_key=session_key).count()
        
        return JsonResponse({
            'success': True,
            'is_favorited': is_favorited,
            'total_favorites': total_favorites,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def visitor_favorites_list(request):
    """List visitor's favorites"""
    if not request.session.session_key:
        favorites = []
    else:
        favorites = VisitorFavorite.objects.filter(
            session_key=request.session.session_key
        ).select_related('product__category', 'product__seller').prefetch_related('product__images')
    
    context = {
        'favorites': favorites,
        'total_favorites': len(favorites)
    }
    return render(request, 'backend/visitor/favorites.html', context)


@require_POST
def visitor_toggle_compare(request, product_id):
    """Toggle compare for visitor"""
    try:
        if not request.session.session_key:
            request.session.create()
        
        product = get_object_or_404(Product, id=product_id, status='ACTIVE')
        session_key = request.session.session_key
        
        # Check if already comparing (limit to 4 products)
        current_compares = VisitorCompare.objects.filter(session_key=session_key).count()
        
        compare, created = VisitorCompare.objects.get_or_create(
            session_key=session_key,
            product=product
        )
        
        if not created:
            compare.delete()
            is_comparing = False
            message = f"{product.title} retiré de la comparaison"
        else:
            if current_compares >= 4:
                return JsonResponse({
                    'success': False, 
                    'message': 'Vous ne pouvez comparer que 4 produits maximum'
                })
            
            is_comparing = True
            message = f"{product.title} ajouté à la comparaison"
        
        # Get total compares count for this visitor
        total_compares = VisitorCompare.objects.filter(session_key=session_key).count()
        
        return JsonResponse({
            'success': True,
            'is_comparing': is_comparing,
            'total_compares': total_compares,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def visitor_compare_list(request):
    """List visitor's compared products"""
    if not request.session.session_key:
        compares = []
    else:
        compares = VisitorCompare.objects.filter(
            session_key=request.session.session_key
        ).select_related('product__category', 'product__seller').prefetch_related('product__images')
    
    context = {
        'compares': compares,
        'total_compares': len(compares)
    }
    return render(request, 'backend/visitor/compare.html', context)


@require_POST
def visitor_add_comment(request, product_id):
    """Add comment to product"""
    try:
        product = get_object_or_404(Product, id=product_id, status='ACTIVE')
        
        visitor_name = request.POST.get('visitor_name', '').strip()
        visitor_email = request.POST.get('visitor_email', '').strip()
        content = request.POST.get('content', '').strip()
        parent_id = request.POST.get('parent_id')
        
        if not visitor_name or not content:
            return JsonResponse({
                'success': False,
                'message': 'Nom et commentaire requis'
            })
        
        if len(content) < 10:
            return JsonResponse({
                'success': False,
                'message': 'Le commentaire doit contenir au moins 10 caractères'
            })
        
        # Get parent comment if replying
        parent = None
        if parent_id:
            try:
                parent = ProductComment.objects.get(id=parent_id, product=product)
            except ProductComment.DoesNotExist:
                pass
        
        # Create comment
        comment = ProductComment.objects.create(
            product=product,
            user=request.user if request.user.is_authenticated else None,
            visitor_name=visitor_name if not request.user.is_authenticated else '',
            visitor_email=visitor_email if not request.user.is_authenticated else '',
            visitor_ip=get_client_ip(request),
            content=content,
            parent=parent
        )
        
        # Send notification to admin
        try:
            send_email_notification(
                subject=f"Nouveau commentaire sur {product.title}",
                message=f"Un nouveau commentaire a été ajouté par {visitor_name}: {content[:100]}...",
                recipient_list=['admin@videgrenier-kamer.com']
            )
        except Exception as e:
            print(f"Failed to send email notification: {e}")
        
        return JsonResponse({
            'success': True,
            'message': 'Commentaire ajouté avec succès',
            'comment': {
                'id': str(comment.id),
                'commenter_name': comment.commenter_name,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%d/%m/%Y à %H:%M'),
                'is_reply': comment.is_reply
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_POST
def visitor_toggle_like(request, product_id):
    """Toggle like/dislike for product"""
    try:
        if not request.session.session_key:
            request.session.create()
        
        product = get_object_or_404(Product, id=product_id, status='ACTIVE')
        like_type = request.POST.get('like_type', 'LIKE')  # LIKE or DISLIKE
        
        if like_type not in ['LIKE', 'DISLIKE']:
            return JsonResponse({'success': False, 'message': 'Type de vote invalide'})
        
        # Remove existing like/dislike for this visitor
        existing_likes = ProductLike.objects.filter(
            product=product,
            user=request.user if request.user.is_authenticated else None,
            visitor_ip=get_client_ip(request) if not request.user.is_authenticated else None,
            session_key=request.session.session_key if not request.user.is_authenticated else ''
        )
        
        # Check if same type already exists
        same_like = existing_likes.filter(like_type=like_type).first()
        
        if same_like:
            # Remove the like/dislike
            same_like.delete()
            user_vote = None
            message = "Vote retiré"
        else:
            # Remove any existing vote and add new one
            existing_likes.delete()
            
            ProductLike.objects.create(
                product=product,
                user=request.user if request.user.is_authenticated else None,
                visitor_ip=get_client_ip(request) if not request.user.is_authenticated else None,
                session_key=request.session.session_key if not request.user.is_authenticated else '',
                like_type=like_type
            )
            user_vote = like_type
            message = f"Produit {'aimé' if like_type == 'LIKE' else 'non aimé'}"
        
        # Get updated counts
        likes_count = ProductLike.objects.filter(product=product, like_type='LIKE').count()
        dislikes_count = ProductLike.objects.filter(product=product, like_type='DISLIKE').count()
        
        return JsonResponse({
            'success': True,
            'user_vote': user_vote,
            'likes_count': likes_count,
            'dislikes_count': dislikes_count,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_POST
def visitor_create_alert(request, product_id):
    """Create price alert for product"""
    try:
        product = get_object_or_404(Product, id=product_id, status='ACTIVE')
        
        visitor_email = request.POST.get('visitor_email', '').strip()
        visitor_phone = request.POST.get('visitor_phone', '').strip()
        alert_type = request.POST.get('alert_type', 'PRICE_DROP')
        target_price = request.POST.get('target_price')
        
        if not visitor_email and not visitor_phone:
            return JsonResponse({
                'success': False,
                'message': 'Email ou téléphone requis pour les alertes'
            })
        
        if alert_type == 'PRICE_DROP' and target_price:
            try:
                target_price = Decimal(target_price)
                if target_price >= product.price:
                    return JsonResponse({
                        'success': False,
                        'message': 'Le prix cible doit être inférieur au prix actuel'
                    })
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'message': 'Prix cible invalide'
                })
        else:
            target_price = None
        
        # Check if alert already exists
        existing_alert = ProductAlert.objects.filter(
            product=product,
            user=request.user if request.user.is_authenticated else None,
            visitor_email=visitor_email if not request.user.is_authenticated else '',
            alert_type=alert_type,
            is_active=True
        ).first()
        
        if existing_alert:
            return JsonResponse({
                'success': False,
                'message': 'Vous avez déjà une alerte active pour ce produit'
            })
        
        # Create alert
        ProductAlert.objects.create(
            product=product,
            user=request.user if request.user.is_authenticated else None,
            visitor_email=visitor_email if not request.user.is_authenticated else '',
            visitor_phone=visitor_phone if not request.user.is_authenticated else '',
            alert_type=alert_type,
            target_price=target_price
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Alerte créée avec succès. Vous serez notifié par email.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def visitor_order_create(request, product_id):
    """Créer une commande visiteur sans connexion"""
    if request.method == 'POST':
        try:
            # Intégration Campay
            if order.payment_method == 'CAMPAY':
                payment_response = initiate_campay_payment(order, phone_number)
                if payment_response.get('status') == 'success':
                    # Créer le paiement
                    Payment.objects.create(
                        order=order,
                        payment_reference=payment_response.get('reference'),
                        amount=order.total_amount,
                        status='PROCESSING',
                        provider_response=payment_response,
                        transaction_id=payment_response.get('transaction_id', '')
                    )
                    messages.success(request, 'Paiement initié. Suivez les instructions sur votre téléphone.')
                    return redirect('backend:visitor_order_success', order_id=order.id)
                else:
                    messages.error(request, f'Erreur de paiement: {payment_response.get("message", "Erreur inconnue")}')
            
            else:
                messages.error(request, 'Méthode de paiement non encore supportée.')
                
        except Exception as e:
            messages.error(request, f'Erreur lors du paiement: {str(e)}')
    
    context = {
        'order': order,
        'product': order.product,
    }
    return render(request, 'backend/visitor/orders/visitor_payment.html', context)


def visitor_order_success(request, order_id):
    """Page de succès pour les commandes visiteurs"""
    order = get_object_or_404(Order, id=order_id, buyer__isnull=True)
    
    # Get admin WhatsApp for contact
    admin_whatsapp = getattr(settings, 'ADMIN_WHATSAPP', os.getenv('ADMIN_WHATSAPP', '237'))
    whatsapp_message = f"Bonjour! J'ai passé une commande (#{order.order_number}). " \
                      f"Pouvez-vous me donner des nouvelles?"
    
    context = {
        'order': order,
        'product': order.product,
        'admin_whatsapp': admin_whatsapp,
        'whatsapp_url': f"https://wa.me/{admin_whatsapp}?text={whatsapp_message}",
    }
    return render(request, 'backend/visitor/orders/visitor_success.html', context)


def initiate_campay_payment(order, phone_number):
    """Initier un paiement via Campay"""
    try:
        api_key = os.getenv('CAMPAY_API_KEY')
        api_secret = os.getenv('CAMPAY_API_SECRET')
        base_url = os.getenv('CAMPAY_BASE_URL', 'https://api.campay.net/v1')
        
        if not all([api_key, api_secret]):
            return {'status': 'error', 'message': 'Configuration Campay manquante'}
        
        # Préparer les données de paiement
        payment_data = {
            'amount': str(order.total_amount),
            'currency': 'XAF',  # Franc CFA
            'from': phone_number,
            'description': f'Achat {order.product.title} - Commande #{order.order_number}',
            'external_reference': str(order.id),
            'redirect_url': f'https://yourdomain.com/orders/visitor/success/{order.id}/',
            'webhook_url': f'https://yourdomain.com/api/campay/webhook/',
        }
        
        # Headers pour l'authentification
        headers = {
            'Authorization': f'Token {api_key}',
            'Content-Type': 'application/json',
        }
        
        # Faire la requête à Campay
        response = requests.post(
            f'{base_url}/collect',
            json=payment_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'success',
                'reference': data.get('reference'),
                'transaction_id': data.get('transaction_id'),
                'message': 'Paiement initié avec succès'
            }
        else:
            return {
                'status': 'error',
                'message': f'Erreur API Campay: {response.status_code}'
            }
            
    except requests.RequestException as e:
        return {'status': 'error', 'message': f'Erreur de connexion: {str(e)}'}
    except Exception as e:
        return {'status': 'error', 'message': f'Erreur: {str(e)}'}


def campay_webhook(request):
    """Webhook pour recevoir les notifications de paiement Campay"""
    if request.method == 'POST':
        try:
            import json
            import hmac
            import hashlib
            
            # Vérifier la signature du webhook
            webhook_secret = os.getenv('CAMPAY_WEBHOOK_SECRET')
            if webhook_secret:
                signature = request.headers.get('X-Campay-Signature')
                payload = request.body
                expected_signature = hmac.new(
                    webhook_secret.encode(),
                    payload,
                    hashlib.sha256
                ).hexdigest()
                
                if signature != expected_signature:
                    return JsonResponse({'error': 'Invalid signature'}, status=400)
            
            # Traiter les données du webhook
            data = json.loads(request.body)
            reference = data.get('reference')
            status = data.get('status')
            transaction_id = data.get('transaction_id')
            
            # Trouver le paiement correspondant
            try:
                payment = Payment.objects.get(payment_reference=reference)
                order = payment.order
                
                if status == 'SUCCESSFUL':
                    payment.status = 'COMPLETED'
                    payment.transaction_id = transaction_id
                    payment.completed_at = timezone.now()
                    payment.save()
                    
                    order.status = 'PAID'
                    order.save()
                    
                    # Envoyer notification de confirmation
                    try:
                        from .views_admin import EnhancedEmailNotificationService
                        email_service = EnhancedEmailNotificationService()
                        email_service.send_visitor_payment_confirmation(order)
                    except Exception:
                        pass
                        
                elif status == 'FAILED':
                    payment.status = 'FAILED'
                    payment.save()
                    
                    order.status = 'CANCELLED'
                    order.save()
                
                return JsonResponse({'status': 'success'})
                
            except Payment.DoesNotExist:
                return JsonResponse({'error': 'Payment not found'}, status=404)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# AJAX functions for group chat
@login_required
@require_http_methods(["GET"])
def ajax_get_group_chat_messages(request, chat_id):
    """Get messages for a group chat via AJAX"""
    try:
        group_chat = get_object_or_404(GroupChat, id=chat_id)
        
        # Check if user is participant
        if not group_chat.participants.filter(id=request.user.id).exists():
            return JsonResponse({'error': 'Accès non autorisé'}, status=403)
        
        # Get last_message_id for pagination
        last_message_id = request.GET.get('last_message_id')
        limit = int(request.GET.get('limit', 20))
        
        # Get messages
        messages_query = group_chat.group_messages.select_related('sender')
        
        if last_message_id:
            try:
                last_message = GroupChatMessage.objects.get(id=last_message_id)
                messages_query = messages_query.filter(created_at__lt=last_message.created_at)
            except GroupChatMessage.DoesNotExist:
                pass
        
        messages_list = messages_query.order_by('-created_at')[:limit]
        
        # Mark messages as read
        for message in messages_list:
            if request.user != message.sender and not message.read_by.filter(id=request.user.id).exists():
                message.read_by.add(request.user)
        
        # Format messages for JSON
        messages_data = []
        for message in reversed(list(messages_list)):
            messages_data.append({
                'id': str(message.id),
                'sender_id': str(message.sender.id),
                'sender_name': message.sender.get_full_name(),
                'sender_initials': message.sender.get_full_name()[0:2].upper(),
                'content': message.content,
                'message_type': message.message_type,
                'created_at': message.created_at.isoformat(),
                'formatted_time': message.created_at.strftime('%H:%M'),
                'is_read_by_all': message.is_read_by_all,
                'read_by_count': message.read_by.count(),
                'is_own_message': message.sender.id == request.user.id,
                'has_image': bool(message.image),
                'image_url': message.image.url if message.image else None,
                'has_file': bool(message.file),
                'file_url': message.file.url if message.file else None,
            })
        
        return JsonResponse({
            'success': True,
            'messages': messages_data,
            'has_more': messages_list.count() == limit,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def ajax_send_group_chat_message(request):
    """Send a message to a group chat via AJAX"""
    try:
        data = json.loads(request.body)
        group_chat_id = data.get('group_chat_id')
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'TEXT')
        
        if not group_chat_id or not content:
            return JsonResponse({'error': 'Paramètres manquants'}, status=400)
        
        group_chat = get_object_or_404(GroupChat, id=group_chat_id)
        
        # Check if user is participant
        if not group_chat.participants.filter(id=request.user.id).exists():
            return JsonResponse({'error': 'Accès non autorisé'}, status=403)
        
        # Create message
        message = GroupChatMessage.objects.create(
            group_chat=group_chat,
            sender=request.user,
            message_type=message_type,
            content=content
        )
        
        # Mark as read by sender
        message.read_by.add(request.user)
        
        # Update group chat timestamp
        group_chat.updated_at = timezone.now()
        group_chat.save(update_fields=['updated_at'])
        
        # Notify other participants
        for participant in group_chat.participants.exclude(id=request.user.id):
            Notification.objects.create(
                user=participant,
                type='MESSAGE',
                title=f'Nouveau message dans {group_chat.name}',
                message=f'{request.user.get_full_name()} a envoyé un message dans le groupe',
                data={'group_chat_id': str(group_chat.id)}
            )
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': str(message.id),
                'sender_id': str(message.sender.id),
                'sender_name': message.sender.get_full_name(),
                'sender_initials': message.sender.get_full_name()[0:2].upper(),
                'content': message.content,
                'message_type': message.message_type,
                'created_at': message.created_at.isoformat(),
                'formatted_time': message.created_at.strftime('%H:%M'),
                'is_read_by_all': False,
                'read_by_count': 1,  # Just the sender
                'is_own_message': True,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def ajax_mark_group_message_read(request, message_id):
    """Mark a group chat message as read via AJAX"""
    try:
        message = get_object_or_404(GroupChatMessage, id=message_id)
        group_chat = message.group_chat
        
        # Check if user is participant
        if not group_chat.participants.filter(id=request.user.id).exists():
            return JsonResponse({'error': 'Accès non autorisé'}, status=403)
        
        # Mark as read if not already
        if not message.read_by.filter(id=request.user.id).exists():
            message.read_by.add(request.user)
        
        return JsonResponse({
            'success': True,
            'read_by_count': message.read_by.count(),
            'is_read_by_all': message.is_read_by_all,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============= ERROR HANDLERS =============

def handler404(request, exception=None):
    """Vue pour les erreurs 404 - Page non trouvée"""
    return render(request, 'backend/errors/404.html', status=404)


def handler500(request, *args, **argv):
    """Vue pour les erreurs 500 - Erreur serveur"""
    return render(request, 'backend/errors/500.html', status=500)


def handler403(request, exception=None):
    """Vue pour les erreurs 403 - Accès interdit"""
    return render(request, 'backend/errors/403.html', status=403)


@csrf_exempt
def newsletter_subscribe(request):
    """Handle newsletter subscription via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip()
            
            if not email:
                return JsonResponse({
                    'success': False,
                    'error': 'Adresse email requise'
                })
            
            # Import here to avoid circular imports
            from .models_newsletter import NewsletterSubscriber
            
            # Check if email already exists
            if NewsletterSubscriber.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Cette adresse email est déjà abonnée'
                })
            
            # Create new subscriber
            subscriber = NewsletterSubscriber.objects.create(
                email=email,
                is_active=True
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Merci pour votre abonnement!'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Données invalides'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur serveur: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Méthode non autorisée'
    })


# ============= OPTIMIZED PRODUCT VIEWS =============

@method_decorator(cache_page(PRODUCT_CACHE_TIMEOUT), name='dispatch')
class ProductListView(ListView):
    """Optimized product list view with caching and query optimization"""
    model = Product
    template_name = 'backend/client/products/products.html'
    context_object_name = 'products'
    paginate_by = 24
    
    def get_queryset(self):
        """Optimized queryset with select_related and prefetch_related"""
        queryset = Product.objects.select_related(
            'seller', 'category'
        ).prefetch_related(
            'images'
        ).filter(
            status='ACTIVE'
        ).only(
            'id', 'title', 'slug', 'price', 'condition', 'city', 
            'is_negotiable', 'views_count', 'likes_count', 'created_at',
            'seller__email', 'seller__first_name', 'seller__last_name',
            'category__name', 'category__slug'
        )
        
        # Apply filters
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        city = self.request.GET.get('city')
        if city:
            queryset = queryset.filter(city=city)
        
        condition = self.request.GET.get('condition')
        if condition:
            queryset = queryset.filter(condition=condition)
        
        min_price = self.request.GET.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        
        max_price = self.request.GET.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Sort options
        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by == 'price_low':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort_by == 'popular':
            queryset = queryset.order_by('-views_count')
        elif sort_by == 'recent':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Cache categories
        cache_key = get_cache_key('categories_active')
        categories = cache.get(cache_key)
        if categories is None:
            categories = Category.objects.filter(
                is_active=True, parent=None
            ).prefetch_related('children').only(
                'id', 'name', 'slug', 'icon'
            )
            cache.set(cache_key, categories, CACHE_TIMEOUT)
        
        context['categories'] = categories
        context['current_filters'] = self.request.GET
        return context


@method_decorator(cache_page(PRODUCT_CACHE_TIMEOUT), name='dispatch')
class ProductDetailView(DetailView):
    """Optimized product detail view with caching"""
    model = Product
    template_name = 'backend/client/products/product_detail.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        """Optimized queryset with related data"""
        return Product.objects.select_related(
            'seller', 'category'
        ).prefetch_related(
            'images', 'reviews__reviewer'
        ).filter(
            status='ACTIVE'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Increment view count (async)
        self.increment_view_count()
        
        # Get related products
        related_products = Product.objects.select_related(
            'seller', 'category'
        ).prefetch_related(
            'images'
        ).filter(
            category=self.object.category,
            status='ACTIVE'
        ).exclude(
            id=self.object.id
        ).only(
            'id', 'title', 'slug', 'price', 'condition', 'city',
            'seller__email', 'category__name'
        )[:6]
        
        context['related_products'] = related_products
        return context
    
    def increment_view_count(self):
        """Increment view count asynchronously"""
        try:
            # Use cache to batch updates
            cache_key = f"product_views_{self.object.id}"
            current_views = cache.get(cache_key, 0)
            cache.set(cache_key, current_views + 1, 60 * 5)  # 5 minutes
            
            # Update database periodically
            if current_views % 10 == 0:  # Update every 10 views
                Product.objects.filter(id=self.object.id).update(
                    views_count=F('views_count') + current_views + 1
                )
                cache.delete(cache_key)
        except Exception as e:
            logger.error(f"Error incrementing view count: {e}")


# ============= OPTIMIZED SEARCH VIEWS =============

class OptimizedSearchView(ListView):
    """Optimized search view with full-text search"""
    model = Product
    template_name = 'backend/client/search/results.html'
    context_object_name = 'products'
    paginate_by = 24
    
    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        if not query:
            return Product.objects.none()
        
        # Use PostgreSQL full-text search
        search_vector = SearchVector('title', weight='A') + SearchVector('description', weight='B')
        search_query = SearchQuery(query, config='french')
        
        queryset = Product.objects.select_related(
            'seller', 'category'
        ).prefetch_related(
            'images'
        ).annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(
            search=search_query,
            status='ACTIVE'
        ).order_by('-rank', '-created_at').only(
            'id', 'title', 'slug', 'price', 'condition', 'city',
            'seller__email', 'category__name'
        )
        
        # Log search for analytics
        self.log_search(query, queryset.count())
        
        return queryset
    
    def log_search(self, query, results_count):
        """Log search for analytics"""
        try:
            SearchHistory.objects.create(
                user=self.request.user if self.request.user.is_authenticated else None,
                search_term=query,
                results_count=results_count,
                ip_address=self.get_client_ip()
            )
        except Exception as e:
            logger.error(f"Error logging search: {e}")
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


# ============= OPTIMIZED DASHBOARD VIEWS =============

@method_decorator(cache_page(CACHE_TIMEOUT), name='dispatch')
class OptimizedDashboardView(TemplateView):
    """Optimized dashboard with caching and efficient queries"""
    template_name = 'backend/client/dashboard/client_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Cache user-specific data
        cache_key = get_cache_key('dashboard', user.id)
        cached_data = cache.get(cache_key)
        
        if cached_data is None:
            # Optimized queries with select_related
            my_products = Product.objects.filter(
                seller=user
            ).select_related('category').only(
                'id', 'title', 'price', 'status', 'created_at',
                'category__name'
            ).order_by('-created_at')[:5]
            
            my_orders = Order.objects.filter(
                buyer=user
            ).select_related('product', 'product__category').only(
                'id', 'order_number', 'total_amount', 'status', 'created_at',
                'product__title', 'product__category__name'
            ).order_by('-created_at')[:5]
            
            my_favorites = Favorite.objects.filter(
                user=user
            ).select_related('product', 'product__category').only(
                'id', 'created_at', 'product__title', 'product__price',
                'product__category__name'
            ).order_by('-created_at')[:5]
            
            # Count queries
            unread_messages = Message.objects.filter(
                chat__buyer=user, is_read=False
            ).exclude(sender=user).count()
            
            unread_notifications = Notification.objects.filter(
                user=user, is_read=False
            ).count()
            
            # Sales stats
            sales_stats = Order.objects.filter(
                product__seller=user, status='DELIVERED'
            ).aggregate(
                total_sales=Count('id'),
                total_revenue=Sum('total_amount')
            )
            
            cached_data = {
                'my_products': my_products,
                'my_orders': my_orders,
                'my_favorites': my_favorites,
                'unread_messages': unread_messages,
                'unread_notifications': unread_notifications,
                'sales_stats': sales_stats,
            }
            
            cache.set(cache_key, cached_data, CACHE_TIMEOUT)
        
        context.update(cached_data)
        return context


# ============= OPTIMIZED ORDER VIEWS =============

class OptimizedOrderListView(LoginRequiredMixin, ListView):
    """Optimized order list with efficient queries"""
    model = Order
    template_name = 'backend/client/orders/orders.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        return Order.objects.filter(
            buyer=self.request.user
        ).select_related(
            'product', 'product__category', 'product__seller'
        ).prefetch_related(
            'product__images'
        ).only(
            'id', 'order_number', 'total_amount', 'status', 'created_at',
            'product__title', 'product__category__name', 'product__seller__email'
        ).order_by('-created_at')


# ============= OPTIMIZED CHAT VIEWS =============

class OptimizedChatListView(LoginRequiredMixin, ListView):
    """Optimized chat list with efficient queries"""
    model = Chat
    template_name = 'backend/client/chat/chats.html'
    context_object_name = 'chats'
    
    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(
            Q(buyer=user) | Q(seller=user),
            is_active=True
        ).select_related(
            'product', 'product__category', 'buyer', 'seller'
        ).prefetch_related(
            'messages'
        ).only(
            'id', 'product__title', 'product__category__name',
            'buyer__email', 'seller__email', 'updated_at'
        ).order_by('-updated_at')


# ============= CACHE MANAGEMENT =============

def clear_product_cache(product_id=None):
    """Clear product-related cache"""
    if product_id:
        cache.delete(get_cache_key('product_detail', product_id))
    cache.delete_pattern('vgk_product_*')
    cache.delete_pattern('vgk_dashboard_*')


def clear_user_cache(user_id):
    """Clear user-specific cache"""
    cache.delete(get_cache_key('dashboard', user_id))
    cache.delete_pattern(f'vgk_user_{user_id}_*')


# ============= PERFORMANCE MONITORING =============

class PerformanceMiddleware:
    """Middleware to monitor query performance"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        from django.db import connection
        from django.utils import timezone
        
        start_time = timezone.now()
        
        response = self.get_response(request)
        
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        
        # Log slow requests
        if duration > 1.0:  # Log requests taking more than 1 second
            logger.warning(f"Slow request: {request.path} took {duration:.2f}s")
        
        # Log query count
        query_count = len(connection.queries)
        if query_count > 20:  # Log requests with more than 20 queries
            logger.warning(f"High query count: {request.path} made {query_count} queries")
        
        return response


# ============= BULK OPERATIONS =============

def bulk_update_product_status(product_ids, status):
    """Bulk update product status efficiently"""
    try:
        updated_count = Product.objects.filter(
            id__in=product_ids
        ).update(
            status=status,
            updated_at=timezone.now()
        )
        
        # Clear cache for updated products
        for product_id in product_ids:
            clear_product_cache(product_id)
        
        return updated_count
    except Exception as e:
        logger.error(f"Error in bulk update: {e}")
        return 0


def bulk_create_notifications(users, notification_data):
    """Bulk create notifications efficiently"""
    try:
        notifications = [
            Notification(
                user=user,
                **notification_data
            )
            for user in users
        ]
        
        Notification.objects.bulk_create(notifications, batch_size=1000)
        
        # Clear user cache
        for user in users:
            clear_user_cache(user.id)
        
        return len(notifications)
    except Exception as e:
        logger.error(f"Error in bulk notification creation: {e}")
        return 0


# ============= ANALYTICS OPTIMIZATION =============

def get_user_analytics(user_id, days=30):
    """Get user analytics with caching"""
    cache_key = get_cache_key('analytics', user_id, days)
    analytics = cache.get(cache_key)
    
    if analytics is None:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        analytics = {
            'orders': Order.objects.filter(
                buyer_id=user_id,
                created_at__range=(start_date, end_date)
            ).count(),
            'products': Product.objects.filter(
                seller_id=user_id,
                created_at__range=(start_date, end_date)
            ).count(),
            'revenue': Order.objects.filter(
                product__seller_id=user_id,
                status='DELIVERED',
                created_at__range=(start_date, end_date)
            ).aggregate(total=Sum('total_amount'))['total'] or 0,
        }
        
        cache.set(cache_key, analytics, CACHE_TIMEOUT)
    
    return analytics


# ============= SEARCH OPTIMIZATION =============

def get_search_suggestions(query, limit=10):
    """Get search suggestions with caching"""
    cache_key = get_cache_key('search_suggestions', query, limit)
    suggestions = cache.get(cache_key)
    
    if suggestions is None:
        # Use full-text search for suggestions
        search_vector = SearchVector('title', weight='A')
        search_query = SearchQuery(query, config='french')
        
        suggestions = Product.objects.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(
            search=search_query,
            status='ACTIVE'
        ).order_by('-rank').values_list(
            'title', flat=True
        ).distinct()[:limit]
        
        cache.set(cache_key, list(suggestions), CACHE_TIMEOUT)
    
    return suggestions


# ============= NOTIFICATION OPTIMIZATION =============

def get_user_notifications(user_id, limit=20):
    """Get user notifications with caching"""
    cache_key = get_cache_key('notifications', user_id, limit)
    notifications = cache.get(cache_key)
    
    if notifications is None:
        notifications = Notification.objects.filter(
            user_id=user_id
        ).order_by('-created_at').only(
            'id', 'type', 'title', 'message', 'is_read', 'created_at'
        )[:limit]
        
        cache.set(cache_key, list(notifications), CACHE_TIMEOUT)
    
    return notifications


# ============= FAVORITE OPTIMIZATION =============

def get_user_favorites(user_id, limit=20):
    """Get user favorites with caching"""
    cache_key = get_cache_key('favorites', user_id, limit)
    favorites = cache.get(cache_key)
    
    if favorites is None:
        favorites = Favorite.objects.filter(
            user_id=user_id
        ).select_related(
            'product', 'product__category'
        ).prefetch_related(
            'product__images'
        ).only(
            'id', 'created_at', 'product__title', 'product__price',
            'product__category__name'
        ).order_by('-created_at')[:limit]
        
        cache.set(cache_key, list(favorites), CACHE_TIMEOUT)
    
    return favorites



