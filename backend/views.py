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
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail

import json
import random
import string
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    User, Product, Category, Order, Payment, Review, 
    Chat, Message, Favorite, SearchHistory, Notification, 
    AdminStock, PickupPoint, Analytics, ProductImage
)
from .forms import (
    CustomSignupForm, CustomLoginForm, ProductForm, 
    OrderForm, ReviewForm, ChatMessageForm, ProfileForm,
    SearchForm, AdminStockForm, ContactForm
)
from .utils import (
    send_sms_notification, send_email_notification, 
    process_payment, track_analytics, generate_pickup_code,
    get_client_ip
)


class HomeView(TemplateView):
    """Page d'accueil avec produits featured et catégories"""
    template_name = 'backend/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Produits en vedette
        context['featured_products'] = Product.objects.filter(
            is_featured=True, 
            status='ACTIVE'
        ).select_related('category', 'seller').prefetch_related('images')[:8]
        
        # Produits récents
        context['recent_products'] = Product.objects.filter(
            status='ACTIVE'
        ).select_related('category', 'seller').prefetch_related('images').order_by('-created_at')[:12]
        
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
            'cities_count': len(settings.VGK_SETTINGS['SUPPORTED_CITIES'])
        }
        
        # Témoignages (derniers avis 5 étoiles)
        context['testimonials'] = Review.objects.filter(
            overall_rating=5
        ).select_related('reviewer', 'order__product').order_by('-created_at')[:6]
        
        return context


class CustomLoginView(LoginView):
    """Vue de connexion personnalisée"""
    form_class = CustomLoginForm
    template_name = 'backend/auth/login.html'
    
    def get_success_url(self):
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
    template_name = 'backend/auth/register.html'
    success_url = reverse_lazy('backend:dashboard')
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(
            self.request, 
            "Compte créé avec succès! Vérifiez votre email pour activer votre compte."
        )
        
        # Envoyer SMS de bienvenue
        send_sms_notification(
            user.phone,
            f"Bienvenue sur Vidé-Grenier Kamer! Votre compte a été créé avec succès."
        )
        
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
    template_name = 'backend/dashboard/dashboard.html'
    
    def get_template_names(self):
        user_type = self.request.user.user_type
        if user_type == 'ADMIN':
            return ['backend/dashboard/admin_dashboard.html']
        elif user_type == 'STAFF':
            return ['backend/dashboard/staff_dashboard.html']
        return ['backend/dashboard/client_dashboard.html']
    
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
    template_name = 'backend/products/list.html'
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
        context.update({
            'categories': Category.objects.filter(is_active=True, parent=None),
            'cities': User.CITIES,
            'conditions': Product.CONDITIONS,
            'selected_conditions': self.request.GET.getlist('condition'),  # Add this line
            'current_filters': {
                'q': self.request.GET.get('q', ''),
                'category': self.request.GET.get('category', ''),
                'city': self.request.GET.get('city', ''),
                'min_price': self.request.GET.get('min_price', ''),
                'max_price': self.request.GET.get('max_price', ''),
                'condition': self.request.GET.get('condition', ''),
                'sort': self.request.GET.get('sort', '-created_at'),
            }
        })
        return context


class ProductDetailView(DetailView):
    """Détail d'un produit avec suggestions et achat public"""
    model = Product
    template_name = 'backend/products/detail.html'
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
    template_name = 'backend/orders/public_order.html'
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
    template_name = 'backend/orders/public_success.html'
    
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
    template_name = 'backend/products/create.html'
    
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
    template_name = 'backend/products/edit.html'
    
    def get_queryset(self):
        # Seul le propriétaire peut modifier
        return Product.objects.filter(seller=self.request.user)
    
    def get_success_url(self):
        return reverse('backend:product_detail', kwargs={'slug': self.object.slug})


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    """Suppression d'un produit"""
    model = Product
    template_name = 'backend/products/delete.html'
    success_url = reverse_lazy('backend:dashboard')
    
    def get_queryset(self):
        # Seul le propriétaire peut supprimer
        return Product.objects.filter(seller=self.request.user)


class ProfileView(LoginRequiredMixin, DetailView):
    """Profil utilisateur"""
    model = User
    template_name = 'backend/auth/profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        return self.request.user


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Modification du profil utilisateur"""
    model = User
    form_class = ProfileForm
    template_name = 'backend/auth/profile_edit.html'
    success_url = reverse_lazy('backend:profile')
    
    def get_object(self):
        return self.request.user


class CategoryView(ListView):
    """Produits d'une catégorie"""
    model = Product
    template_name = 'backend/categories/category.html'
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
    template_name = 'backend/categories/list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True, parent=None).prefetch_related('children')


class OrderCreateView(LoginRequiredMixin, CreateView):
    """Création d'une commande pour utilisateurs connectés"""
    model = Order
    form_class = OrderForm
    template_name = 'backend/orders/create.html'
    
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
    template_name = 'backend/orders/detail.html'
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
    template_name = 'backend/orders/list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        return Order.objects.filter(
            Q(buyer=self.request.user) | Q(product__seller=self.request.user)
        ).select_related('product', 'buyer').order_by('-created_at')


class PaymentView(LoginRequiredMixin, TemplateView):
    """Processus de paiement"""
    template_name = 'backend/payments/payment.html'
    
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
    template_name = 'backend/payments/success.html'
    context_object_name = 'payment'


class PaymentCancelView(LoginRequiredMixin, DetailView):
    """Page d'annulation du paiement"""
    model = Payment
    template_name = 'backend/payments/cancel.html'
    context_object_name = 'payment'


class ChatListView(LoginRequiredMixin, ListView):
    """Liste des conversations"""
    model = Chat
    template_name = 'backend/chat/list.html'
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
    template_name = 'backend/chat/detail.html'
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


class ReviewCreateView(LoginRequiredMixin, CreateView):
    """Créer un avis après livraison"""
    model = Review
    form_class = ReviewForm
    template_name = 'backend/reviews/create.html'
    
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
    template_name = 'backend/reviews/list.html'
    context_object_name = 'reviews'
    paginate_by = 20
    
    def get_queryset(self):
        return Review.objects.filter(
            is_verified=True
        ).select_related('reviewer', 'order__product').order_by('-created_at')


class ReviewDetailView(DetailView):
    """Détail d'un avis public"""
    model = Review
    template_name = 'backend/reviews/detail.html'
    context_object_name = 'review'
    
    def get_queryset(self):
        return Review.objects.filter(is_verified=True).select_related('reviewer', 'order__product')


class PickupPointListView(ListView):
    """Liste des points de retrait"""
    model = PickupPoint
    template_name = 'backend/pickup/list.html'
    context_object_name = 'pickup_points'
    
    def get_queryset(self):
        return PickupPoint.objects.filter(is_active=True).order_by('city', 'name')


class PickupPointDetailView(DetailView):
    """Détail d'un point de retrait"""
    model = PickupPoint
    template_name = 'backend/pickup/detail.html'
    context_object_name = 'pickup_point'
    
    def get_queryset(self):
        return PickupPoint.objects.filter(is_active=True)


class SearchView(TemplateView):
    """Recherche avancée avec suggestions"""
    template_name = 'backend/search/results.html'
    
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
    template_name = 'backend/pages/about.html'


class ContactView(FormView):
    """Page de contact"""
    template_name = 'backend/pages/contact.html'
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
    template_name = 'backend/pages/help.html'


class TermsView(TemplateView):
    """Conditions d'utilisation"""
    template_name = 'backend/pages/terms.html'


class PrivacyView(TemplateView):
    """Politique de confidentialité"""
    template_name = 'backend/pages/privacy.html'


class PhoneVerificationView(LoginRequiredMixin, TemplateView):
    """Vérification du numéro de téléphone"""
    template_name = 'backend/auth/verify_phone.html'
    
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



