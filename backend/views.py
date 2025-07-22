# backend/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, 
    UpdateView, DeleteView, FormView
)
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.conf import settings

import json
import random
import string
from datetime import datetime, timedelta

from .models import (
    User, Product, Category, Order, Payment, Review, 
    Chat, Message, Favorite, SearchHistory, Notification, 
    AdminStock, PickupPoint, Analytics
)
from .forms import (
    CustomSignupForm, CustomLoginForm, ProductForm, 
    OrderForm, ReviewForm, ChatMessageForm, ProfileForm
)
from .utils import (
    send_sms_notification, send_email_notification, 
    process_payment, track_analytics, generate_pickup_code
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
            f"Bienvenue sur Vidé-Grenier Kamer! Votre compte a été créé avec succès. Code de vérification à venir."
        )
        
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    """Vue de déconnexion personnalisée"""
    next_page = reverse_lazy('backend:home')
    
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "Vous avez été déconnecté avec succès.")
        return super().dispatch(request, *args, **kwargs)


class DashboardView(LoginRequiredMixin, TemplateView):
    """Tableau de bord utilisateur personnalisé selon le type"""
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
        
        if user.user_type == 'CLIENT':
            # Dashboard client
            context.update({
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
                    'active_products': Product.objects.filter(
                        seller=user, status='ACTIVE'
                    ).count()
                }
            })
            
        elif user.user_type == 'ADMIN':
            # Dashboard admin
            today = timezone.now().date()
            context.update({
                'daily_stats': {
                    'new_users': User.objects.filter(date_joined__date=today).count(),
                    'new_products': Product.objects.filter(created_at__date=today).count(),
                    'new_orders': Order.objects.filter(created_at__date=today).count(),
                    'daily_revenue': Order.objects.filter(
                        created_at__date=today, status__in=['DELIVERED', 'PAID']
                    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
                },
                'pending_orders': Order.objects.filter(status='PAID').count(),
                'low_stock_items': AdminStock.objects.filter(quantity__lte=5).count(),
                'recent_reviews': Review.objects.order_by('-created_at')[:5],
                'top_categories': Category.objects.annotate(
                    product_count=Count('products')
                ).order_by('-product_count')[:5]
            })
        
        return context


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
    """Détail d'un produit avec suggestions"""
    model = Product
    template_name = 'backend/products/detail.html'
    context_object_name = 'product'
    
    def get_object(self):
        product = get_object_or_404(Product, slug=self.kwargs['slug'], status='ACTIVE')
        
        # Incrémenter le compteur de vues
        Product.objects.filter(id=product.id).update(views_count=models.F('views_count') + 1)
        
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
        
        # Calculs pour l'affichage
        context.update({
            'delivery_cost': self.get_delivery_cost(product.city),
            'commission_amount': product.commission_amount,
            'total_with_delivery': product.price + self.get_delivery_cost(product.city)
        })
        
        return context
    
    def get_delivery_cost(self, city):
        if city in ['DOUALA', 'YAOUNDE']:
            return settings.VGK_SETTINGS['DELIVERY_COST_DOUALA_YAOUNDE']
        return settings.VGK_SETTINGS['DELIVERY_COST_OTHER_CITIES']


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
        
        # Envoyer notification admin pour validation
        admins = User.objects.filter(user_type='ADMIN')
        for admin in admins:
            Notification.objects.create(
                user=admin,
                type='SYSTEM',
                title='Nouveau produit à valider',
                message=f'Le produit "{self.object.title}" nécessite une validation.',
                data={'product_id': str(self.object.id)}
            )
        
        return response
    
    def get_success_url(self):
        return reverse('backend:product_detail', kwargs={'slug': self.object.slug})


class OrderCreateView(LoginRequiredMixin, CreateView):
    """Création d'une commande"""
    model = Order
    form_class = OrderForm
    template_name = 'backend/orders/create.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, id=kwargs['product_id'], status='ACTIVE')
        
        # Vérifier que l'utilisateur n'achète pas son propre produit
        if request.user == self.product.seller:
            messages.error(request, "Vous ne pouvez pas acheter votre propre produit.")
            return redirect('backend:product_detail', slug=self.product.slug)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['product'] = self.product
        return kwargs
    
    def form_valid(self, form):
        form.instance.buyer = self.request.user
        form.instance.product = self.product
        form.instance.total_amount = self.calculate_total_amount(form)
        form.instance.commission_amount = self.product.commission_amount
        
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
    
    def calculate_total_amount(self, form):
        total = self.product.price
        
        # Ajouter les frais de livraison
        if form.instance.delivery_method == 'DELIVERY':
            if self.product.city in ['DOUALA', 'YAOUNDE']:
                total += settings.VGK_SETTINGS['DELIVERY_COST_DOUALA_YAOUNDE']
            else:
                total += settings.VGK_SETTINGS['DELIVERY_COST_OTHER_CITIES']
        
        return total
    
    def get_success_url(self):
        return reverse('backend:payment', kwargs={'order_id': self.object.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        return context


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
            # Initier le paiement
            payment_result = process_payment(self.order, payment_method)
            
            if payment_result['success']:
                # Créer l'enregistrement de paiement
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
        
        # Vérifier que l'utilisateur fait partie de la conversation
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
            
            # Envoyer notification à l'autre utilisateur
            recipient = self.object.seller if request.user == self.object.buyer else self.object.buyer
            Notification.objects.create(
                user=recipient,
                type='MESSAGE',
                title='Nouveau message',
                message=f'Vous avez reçu un message concernant "{self.object.product.title}"',
                data={'chat_id': str(self.object.id)}
            )
            
            # Envoyer SMS si message important
            if message.message_type == 'OFFER':
                send_sms_notification(
                    recipient.phone,
                    f"Nouvelle offre de {form.cleaned_data['offer_amount']} FCFA pour votre produit {self.object.product.title}"
                )
            
            messages.success(request, "Message envoyé avec succès!")
            return redirect('backend:chat_detail', pk=self.object.id)
        
        return self.render_to_response(self.get_context_data(form=form))


class AdminPanelView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Panel d'administration principal"""
    template_name = 'backend/admin/panel.html'
    
    def test_func(self):
        return self.request.user.user_type == 'ADMIN'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques générales
        now = timezone.now()
        today = now.date()
        this_month = now.replace(day=1).date()
        
        context.update({
            'stats': {
                'total_users': User.objects.filter(user_type='CLIENT').count(),
                'active_products': Product.objects.filter(status='ACTIVE').count(),
                'pending_orders': Order.objects.filter(status__in=['PENDING', 'PAID']).count(),
                'total_revenue': Order.objects.filter(
                    status='DELIVERED',
                    created_at__date__gte=this_month
                ).aggregate(Sum('commission_amount'))['commission_amount__sum'] or 0,
                'new_users_today': User.objects.filter(date_joined__date=today).count(),
                'orders_today': Order.objects.filter(created_at__date=today).count(),
            },
            'recent_orders': Order.objects.select_related(
                'buyer', 'product', 'product__seller'
            ).order_by('-created_at')[:10],
            'pending_products': Product.objects.filter(
                status='DRAFT'
            ).select_related('seller')[:10],
            'low_stock_alerts': AdminStock.objects.filter(
                quantity__lte=5,
                status='AVAILABLE'
            ).select_related('product')[:5],
        })
        
        return context


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


# Vues AJAX pour les interactions dynamiques
class ProductViewAjax(View):
    """Incrémenter les vues produit via AJAX"""
    
    def post(self, request, pk):
        try:
            product = get_object_or_404(Product, id=pk)
            Product.objects.filter(id=pk).update(views_count=models.F('views_count') + 1)
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


# Vues pour les webhooks de paiement
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


class PhoneVerificationView(LoginRequiredMixin, TemplateView):
    """Vérification du numéro de téléphone"""
    template_name = 'backend/auth/verify_phone.html'
    
    def post(self, request):
        code = request.POST.get('verification_code')
        # Logique de vérification du code SMS
        # À implémenter avec l'API SMS choisie
        
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