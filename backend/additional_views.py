from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.views import View
import yagmail
from .forms_password_reset import PasswordResetRequestForm, PasswordResetConfirmForm
from django.conf import settings

User = get_user_model()

class PasswordResetRequestView(View):
    template_name = 'backend/auth/password_reset_request.html'

    def get(self, request):
        form = PasswordResetRequestForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "Aucun utilisateur trouvé avec cette adresse email.")
                return render(request, self.template_name, {'form': form})
            # Generate token
            token = get_random_string(64)
            user.reset_token = token
            user.save()
            # Send email
            yag = yagmail.SMTP(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            reset_url = request.build_absolute_uri(reverse_lazy('backend:password_reset_confirm', args=[token]))
            yag.send(
                to=email,
                subject="Réinitialisation de votre mot de passe",
                contents=f"Bonjour,\n\nPour réinitialiser votre mot de passe, cliquez sur le lien suivant : {reset_url}\n\nSi vous n'avez pas demandé cette opération, ignorez ce message."
            )
            messages.success(request, "Un email de réinitialisation a été envoyé si l'adresse existe.")
            return redirect('backend:login')
        return render(request, self.template_name, {'form': form})

class PasswordResetConfirmView(View):
    template_name = 'backend/auth/password_reset_confirm.html'

    def get(self, request, token):
        try:
            user = User.objects.get(reset_token=token)
        except User.DoesNotExist:
            messages.error(request, "Lien invalide ou expiré.")
            return redirect('backend:password_reset_request')
        form = PasswordResetConfirmForm()
        return render(request, self.template_name, {'form': form, 'token': token})

    def post(self, request, token):
        try:
            user = User.objects.get(reset_token=token)
        except User.DoesNotExist:
            messages.error(request, "Lien invalide ou expiré.")
            return redirect('backend:password_reset_request')
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            user.password = make_password(new_password)
            user.reset_token = ''
            user.save()
            messages.success(request, "Votre mot de passe a été réinitialisé avec succès.")
            return redirect('backend:login')
        return render(request, self.template_name, {'form': form, 'token': token})
"""
backend/additional_views.py - VUES SUPPLÉMENTAIRES POUR VGK
Nettoyage: Suppression des vues dupliquées, organisation, commentaires.
"""
## Duplicate views removed. All main views are in views.py. Only keep unique/supplementary views here.
## If you need to add new supplementary views, do so below.
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import transaction
from decimal import Decimal
import json

from .models import (
    User, Product, Category, Order, Payment, Review, 
    Chat, Message, Favorite, SearchHistory, Notification, 
    AdminStock, PickupPoint, Analytics
)
from .utils import send_sms_notification, send_email_notification


class FavoriteListView(LoginRequiredMixin, ListView):
    """Liste des produits favoris de l'utilisateur"""
    model = Favorite
    template_name = 'backend/favorites/list.html'
    context_object_name = 'favorites'
    paginate_by = 24
    
    def get_queryset(self):
        return Favorite.objects.filter(
            user=self.request.user
        ).select_related('product', 'product__seller').order_by('-created_at')


class StatsView(LoginRequiredMixin, TemplateView):
    """Statistiques personnelles pour vendeurs"""
    template_name = 'backend/stats/personal.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Statistiques de vente
        sales_stats = {
            'total_products': Product.objects.filter(seller=user).count(),
            'active_products': Product.objects.filter(seller=user, status='ACTIVE').count(),
            'sold_products': Order.objects.filter(product__seller=user, status='DELIVERED').count(),
            'total_revenue': Order.objects.filter(
                product__seller=user, status='DELIVERED'
            ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            'average_rating': Review.objects.filter(
                order__product__seller=user
            ).aggregate(Avg('overall_rating'))['overall_rating__avg'] or 0
        }
        
        # Évolution mensuelle
        from datetime import datetime, timedelta
        now = timezone.now()
        monthly_sales = []
        
        for i in range(12):
            month_start = (now - timedelta(days=30*i)).replace(day=1)
            month_end = (month_start.replace(month=month_start.month % 12 + 1) - timedelta(days=1))
            
            monthly_revenue = Order.objects.filter(
                product__seller=user,
                status='DELIVERED',
                created_at__range=[month_start, month_end]
            ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            
            monthly_sales.append({
                'month': month_start.strftime('%B %Y'),
                'revenue': float(monthly_revenue)
            })
        
        # Top catégories
        top_categories = Category.objects.filter(
            products__seller=user
        ).annotate(
            sales_count=Count('products__order')
        ).order_by('-sales_count')[:5]
        
        context.update({
            'sales_stats': sales_stats,
            'monthly_sales': monthly_sales,
            'top_categories': top_categories
        })
        
        return context


class ProductPromoteView(LoginRequiredMixin, TemplateView):
    """Promouvoir un produit (mise en avant payante)"""
    template_name = 'backend/products/promote.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(
            Product, 
            slug=kwargs['slug'], 
            seller=request.user
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'product': self.product,
            'promotion_prices': {
                'featured': 1500,  # Mise en vedette
                'premium': 2500,   # Premium listing
                'boost': 1000      # Boost visibility
            }
        })
        return context
    
    def post(self, request, *args, **kwargs):
        promotion_type = request.POST.get('promotion_type')
        
        if promotion_type == 'featured':
            self.product.is_featured = True
            cost = 1500
            message = "Votre produit est maintenant mis en vedette!"
        elif promotion_type == 'premium':
            self.product.is_premium = True
            cost = 2500
            message = "Votre produit est maintenant en listing premium!"
        elif promotion_type == 'boost':
            # Augmenter la visibilité temporairement
            self.product.views_count += 100
            cost = 1000
            message = "Votre produit a reçu un boost de visibilité!"
        else:
            messages.error(request, "Type de promotion invalide.")
            return redirect('backend:product_promote', slug=self.product.slug)
        
        self.product.save()
        
        # Déduire des points de fidélité ou traiter le paiement
        if request.user.loyalty_points >= cost:
            request.user.loyalty_points -= cost
            request.user.save()
            messages.success(request, f"{message} ({cost} points déduits)")
        else:
            # Rediriger vers paiement
            messages.info(request, f"Coût: {cost} FCFA. Redirection vers paiement...")
            # Logique de paiement ici
        
        return redirect('backend:product_detail', slug=self.product.slug)


class WishlistView(LoginRequiredMixin, TemplateView):
    """Wishlist avec alertes de prix"""
    template_name = 'backend/wishlist/list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Produits favoris avec alertes prix
        favorites = Favorite.objects.filter(
            user=self.request.user
        ).select_related('product')
        
        # Alertes de prix (produits similaires moins chers)
        price_alerts = []
        for fav in favorites:
            similar_products = Product.objects.filter(
                category=fav.product.category,
                price__lt=fav.product.price,
                status='ACTIVE'
            ).exclude(id=fav.product.id)[:3]
            
            if similar_products:
                price_alerts.append({
                    'favorite': fav,
                    'cheaper_alternatives': similar_products
                })
        
        context.update({
            'favorites': favorites,
            'price_alerts': price_alerts
        })
        
        return context


class SellerProfileView(DetailView):
    """Profil public d'un vendeur"""
    model = User
    template_name = 'backend/sellers/profile.html'
    context_object_name = 'seller'
    
    def get_queryset(self):
        return User.objects.filter(user_type='CLIENT')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seller = self.object
        
        # Produits du vendeur
        seller_products = Product.objects.filter(
            seller=seller,
            status='ACTIVE'
        ).order_by('-created_at')[:12]
        
        # Statistiques vendeur
        seller_stats = {
            'total_sales': Order.objects.filter(
                product__seller=seller, status='DELIVERED'
            ).count(),
            'average_rating': Review.objects.filter(
                order__product__seller=seller
            ).aggregate(Avg('overall_rating'))['overall_rating__avg'] or 0,
            'response_rate': 95,  # À calculer basé sur les messages
            'member_since': seller.date_joined
        }
        
        # Avis récents
        recent_reviews = Review.objects.filter(
            order__product__seller=seller
        ).select_related('reviewer', 'order__product').order_by('-created_at')[:5]
        
        context.update({
            'seller_products': seller_products,
            'seller_stats': seller_stats,
            'recent_reviews': recent_reviews
        })
        
        return context


class CompareProductsView(TemplateView):
    """Comparaison de produits"""
    template_name = 'backend/products/compare.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les IDs des produits à comparer (max 4)
        product_ids = self.request.GET.get('products', '').split(',')[:4]
        
        if product_ids and product_ids[0]:
            products = Product.objects.filter(
                id__in=product_ids,
                status='ACTIVE'
            ).select_related('seller', 'category')
            
            # Calculer le meilleur prix
            if products:
                min_price = min(p.price for p in products)
                max_price = max(p.price for p in products)
                
                for product in products:
                    product.is_best_price = product.price == min_price
                    product.is_highest_price = product.price == max_price
            
            context['products'] = products
        
        return context


class ProductReportView(LoginRequiredMixin, TemplateView):
    """Signaler un produit"""
    template_name = 'backend/products/report.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, slug=kwargs['slug'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        context['report_reasons'] = [
            'Produit contrefait',
            'Photos non conformes',
            'Prix aberrant',
            'Description mensongère',
            'Produit interdit',
            'Comportement inapproprié du vendeur',
            'Autre'
        ]
        return context
    
    def post(self, request, *args, **kwargs):
        reason = request.POST.get('reason')
        details = request.POST.get('details', '')
        
        # Créer une notification pour les admins
        admins = User.objects.filter(user_type='ADMIN')
        for admin in admins:
            Notification.objects.create(
                user=admin,
                type='SYSTEM',
                title='Produit signalé',
                message=f'Le produit "{self.product.title}" a été signalé pour: {reason}',
                data={
                    'product_id': str(self.product.id),
                    'reporter_id': str(request.user.id),
                    'reason': reason,
                    'details': details
                }
            )
        
        messages.success(request, "Signalement envoyé. Nos équipes vont examiner ce produit.")
        return redirect('backend:product_detail', slug=self.product.slug)


class SavedSearchesView(LoginRequiredMixin, ListView):
    """Recherches sauvegardées avec alertes"""
    model = SearchHistory
    template_name = 'backend/searches/saved.html'
    context_object_name = 'saved_searches'
    
    def get_queryset(self):
        # Pour l'instant, récupérer l'historique de recherche
        return SearchHistory.objects.filter(
            user=self.request.user
        ).order_by('-created_at')[:20]


class ProductAdvancedSearchView(FormView):
    """Recherche avancée avec filtres détaillés"""
    template_name = 'backend/search/advanced.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filtres avancés
        context.update({
            'categories': Category.objects.filter(is_active=True),
            'cities': User.CITIES,
            'conditions': Product.CONDITIONS,
            'price_ranges': [
                (0, 10000, '0 - 10 000 FCFA'),
                (10000, 50000, '10 000 - 50 000 FCFA'),
                (50000, 100000, '50 000 - 100 000 FCFA'),
                (100000, 500000, '100 000 - 500 000 FCFA'),
                (500000, None, '500 000+ FCFA'),
            ]
        })
        
        return context
    
    def get(self, request, *args, **kwargs):
        # Traiter les filtres et afficher les résultats
        filters = {}
        
        if request.GET.get('category'):
            filters['category_id'] = request.GET.get('category')
        
        if request.GET.get('city'):
            filters['city'] = request.GET.get('city')
        
        if request.GET.get('condition'):
            filters['condition'] = request.GET.get('condition')
        
        if request.GET.get('min_price'):
            filters['price__gte'] = request.GET.get('min_price')
        
        if request.GET.get('max_price'):
            filters['price__lte'] = request.GET.get('max_price')
        
        if request.GET.get('has_images'):
            filters['images__isnull'] = False
        
        if request.GET.get('negotiable_only'):
            filters['is_negotiable'] = True
        
        # Recherche textuelle
        query = request.GET.get('q', '')
        products = Product.objects.filter(status='ACTIVE', **filters)
        
        if query:
            products = products.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )
        
        # Tri
        sort_by = request.GET.get('sort', '-created_at')
        products = products.order_by(sort_by)
        
        # Pagination
        paginator = Paginator(products, 24)
        page = paginator.get_page(request.GET.get('page'))
        
        context = self.get_context_data()
        context.update({
            'products': page,
            'query': query,
            'total_results': products.count(),
            'current_filters': request.GET
        })
        
        return render(request, self.template_name, context)


class ProductBulkActionsView(LoginRequiredMixin, TemplateView):
    """Actions en lot sur les produits"""
    template_name = 'backend/products/bulk_actions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_products'] = Product.objects.filter(
            seller=self.request.user
        ).order_by('-created_at')
        return context
    
    def post(self, request):
        action = request.POST.get('action')
        product_ids = request.POST.getlist('product_ids')
        
        if not product_ids:
            messages.error(request, "Aucun produit sélectionné.")
            return redirect('backend:product_bulk_actions')
        
        products = Product.objects.filter(
            id__in=product_ids,
            seller=request.user
        )
        
        if action == 'delete':
            count = products.count()
            products.delete()
            messages.success(request, f"{count} produits supprimés.")
        
        elif action == 'deactivate':
            count = products.update(status='SUSPENDED')
            messages.success(request, f"{count} produits désactivés.")
        
        elif action == 'activate':
            count = products.update(status='ACTIVE')
            messages.success(request, f"{count} produits réactivés.")
        
        elif action == 'feature':
            # Vérifier les points de fidélité
            cost_per_product = 1500
            total_cost = len(product_ids) * cost_per_product
            
            if request.user.loyalty_points >= total_cost:
                products.update(is_featured=True)
                request.user.loyalty_points -= total_cost
                request.user.save()
                messages.success(
                    request, 
                    f"{len(product_ids)} produits mis en vedette ({total_cost} points déduits)."
                )
            else:
                messages.error(
                    request, 
                    f"Points insuffisants. Nécessaire: {total_cost}, Disponible: {request.user.loyalty_points}"
                )
        
        return redirect('backend:product_bulk_actions')


class TrendingProductsView(ListView):
    """Produits tendance basés sur l'activité"""
    model = Product
    template_name = 'backend/products/trending.html'
    context_object_name = 'trending_products'
    paginate_by = 24
    
    def get_queryset(self):
        # Calculer les produits tendance basés sur vues, likes, messages
        from django.db.models import F, Count
        
        return Product.objects.filter(
            status='ACTIVE',
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).annotate(
            trend_score=F('views_count') + F('likes_count') * 5 + Count('chats') * 10
        ).order_by('-trend_score')


class RecentlyViewedView(LoginRequiredMixin, TemplateView):
    """Produits récemment consultés"""
    template_name = 'backend/products/recently_viewed.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer de l'historique analytics
        recent_views = Analytics.objects.filter(
            user=self.request.user,
            metric_type='PRODUCT_VIEW'
        ).order_by('-created_at')[:20]
        
        # Extraire les IDs des produits
        product_ids = [
            view.data.get('product_id') for view in recent_views
            if view.data.get('product_id')
        ]
        
        # Récupérer les produits (en préservant l'ordre)
        products = []
        for product_id in product_ids:
            try:
                product = Product.objects.get(id=product_id, status='ACTIVE')
                if product not in products:  # Éviter les doublons
                    products.append(product)
            except Product.DoesNotExist:
                continue
        
        context['recent_products'] = products[:12]
        return context


class RecommendedProductsView(LoginRequiredMixin, TemplateView):
    """Produits recommandés basés sur l'historique"""
    template_name = 'backend/products/recommended.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Catégories préférées basées sur les achats/vues
        preferred_categories = Category.objects.filter(
            Q(products__order__buyer=user) |
            Q(products__favorited_by=user)
        ).annotate(
            preference_score=Count('products__order') + Count('products__favorited_by')
        ).order_by('-preference_score')[:5]
        
        # Produits recommandés dans ces catégories
        recommended_products = Product.objects.filter(
            category__in=preferred_categories,
            status='ACTIVE'
        ).exclude(
            seller=user  # Exclure ses propres produits
        ).order_by('-views_count')[:12]
        
        # Si pas assez de recommandations, ajouter des produits populaires
        if len(recommended_products) < 12:
            popular_products = Product.objects.filter(
                status='ACTIVE'
            ).exclude(
                seller=user
            ).exclude(
                id__in=[p.id for p in recommended_products]
            ).order_by('-views_count')[:12-len(recommended_products)]
            
            recommended_products = list(recommended_products) + list(popular_products)
        
        context['recommended_products'] = recommended_products
        return context
