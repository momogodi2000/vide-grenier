# backend/views_client.py - ENHANCED CLIENT FEATURES FOR VGK
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View, TemplateView
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum, Avg, F, Case, When
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import transaction
from decimal import Decimal
import json
from datetime import datetime, timedelta

from .models import User, Product, Category, Order, Favorite
from .models_advanced import (
    ShoppingCart, CartItem, Wishlist, WishlistItem, UserFollow,
    ProductRecommendation, UserBehavior, SocialPost, ProductReview, 
    ReviewMedia, SmartNotification
)
from .forms import ProductForm, ReviewForm
from .ai_engine import ai_engine
from .smart_notifications import smart_notifications

# ============= ENHANCED SHOPPING CART =============

class ShoppingCartView(LoginRequiredMixin, TemplateView):
    """Enhanced shopping cart with multiple products"""
    template_name = 'backend/cart/cart.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        cart, created = ShoppingCart.objects.get_or_create(user=self.request.user)
        
        context.update({
            'cart': cart,
            'cart_items': cart.items.select_related('product', 'product__category').all(),
            'total_amount': cart.total_amount,
            'total_items': cart.total_items,
            'delivery_cost': Decimal('2000'),  # Fixed delivery cost
            'final_total': cart.total_amount + Decimal('2000'),
            'recommended_products': self._get_cart_recommendations()
        })
        
        return context
    
    def _get_cart_recommendations(self):
        """Get product recommendations based on cart contents"""
        try:
            cart = ShoppingCart.objects.get(user=self.request.user)
            cart_categories = set(
                cart.items.values_list('product__category_id', flat=True)
            )
            
            if cart_categories:
                # Get complementary products from same categories
                recommendations = Product.objects.filter(
                    category_id__in=cart_categories,
                    status='ACTIVE'
                ).exclude(
                    id__in=cart.items.values_list('product_id', flat=True)
                ).exclude(
                    seller=self.request.user
                ).order_by('-views_count')[:6]
                
                return recommendations
            
        except ShoppingCart.DoesNotExist:
            pass
        
        return []

@login_required
def add_to_cart(request):
    """Add product to shopping cart via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 1))
            
            product = get_object_or_404(Product, id=product_id, status='ACTIVE')
            
            # Check if user is trying to add own product
            if product.seller == request.user:
                return JsonResponse({
                    'success': False,
                    'error': 'Vous ne pouvez pas acheter votre propre produit'
                })
            
            cart, created = ShoppingCart.objects.get_or_create(user=request.user)
            
            cart_item, item_created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={
                    'quantity': quantity,
                    'unit_price': product.price
                }
            )
            
            if not item_created:
                cart_item.quantity += quantity
                cart_item.save()
            
            # Track behavior
            ai_engine.track_user_behavior(
                user=request.user,
                action_type='CART_ADD',
                product=product,
                session_id=request.session.session_key
            )
            
            return JsonResponse({
                'success': True,
                'cart_total': cart.total_items,
                'cart_amount': float(cart.total_amount),
                'message': f'{product.title} ajouté au panier'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def update_cart_item(request):
    """Update cart item quantity"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            quantity = int(data.get('quantity', 1))
            
            if quantity <= 0:
                return remove_cart_item(request)
            
            cart_item = get_object_or_404(
                CartItem,
                id=item_id,
                cart__user=request.user
            )
            
            cart_item.quantity = quantity
            cart_item.save()
            
            cart = cart_item.cart
            
            return JsonResponse({
                'success': True,
                'item_total': float(cart_item.total_price),
                'cart_total': float(cart.total_amount),
                'cart_items': cart.total_items
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def remove_cart_item(request):
    """Remove item from cart"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            
            cart_item = get_object_or_404(
                CartItem,
                id=item_id,
                cart__user=request.user
            )
            
            cart = cart_item.cart
            cart_item.delete()
            
            return JsonResponse({
                'success': True,
                'cart_total': float(cart.total_amount),
                'cart_items': cart.total_items,
                'message': 'Produit retiré du panier'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def checkout_cart(request):
    """Checkout entire cart"""
    if request.method == 'POST':
        try:
            cart = get_object_or_404(ShoppingCart, user=request.user)
            
            if not cart.items.exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Votre panier est vide'
                })
            
            # Create individual orders for each item (VGK model)
            orders_created = []
            total_amount = Decimal('0')
            
            with transaction.atomic():
                for item in cart.items.all():
                    order = Order.objects.create(
                        buyer=request.user,
                        product=item.product,
                        quantity=item.quantity,
                        total_amount=item.total_price + Decimal('2000'),  # Include delivery
                        commission_amount=item.product.commission_amount * item.quantity,
                        delivery_cost=Decimal('2000'),
                        status='PENDING',
                        payment_method='PENDING',
                        delivery_method='DELIVERY'
                    )
                    
                    # Reserve product
                    item.product.status = 'RESERVED'
                    item.product.save()
                    
                    orders_created.append(order)
                    total_amount += order.total_amount
                
                # Clear cart
                cart.items.all().delete()
            
            return JsonResponse({
                'success': True,
                'orders_count': len(orders_created),
                'total_amount': float(total_amount),
                'redirect_url': '/orders/'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# ============= ENHANCED WISHLIST SYSTEM =============

class WishlistListView(LoginRequiredMixin, ListView):
    """Enhanced wishlist with multiple lists and sharing"""
    model = Wishlist
    template_name = 'backend/wishlist/list.html'
    context_object_name = 'wishlists'
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).prefetch_related('items')

class WishlistDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a specific wishlist"""
    model = Wishlist
    template_name = 'backend/wishlist/detail.html'
    context_object_name = 'wishlist'
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        wishlist = self.object
        items = wishlist.items.select_related('product', 'product__category').all()
        
        # Check for price drops
        price_drops = []
        for item in items:
            if item.price_alert_threshold and item.product.price <= item.price_alert_threshold:
                price_drops.append(item)
        
        context.update({
            'items': items,
            'price_drops': price_drops,
            'total_value': sum(item.product.price for item in items),
            'avg_priority': items.aggregate(Avg('priority'))['priority__avg'] or 0
        })
        
        return context

@login_required
def add_to_wishlist(request):
    """Add product to wishlist via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            wishlist_id = data.get('wishlist_id')
            price_alert = data.get('price_alert')
            notes = data.get('notes', '')
            priority = int(data.get('priority', 3))
            
            product = get_object_or_404(Product, id=product_id, status='ACTIVE')
            
            # Get or create default wishlist
            if wishlist_id:
                wishlist = get_object_or_404(Wishlist, id=wishlist_id, user=request.user)
            else:
                wishlist, created = Wishlist.objects.get_or_create(
                    user=request.user,
                    is_default=True,
                    defaults={'name': 'Ma liste de souhaits'}
                )
            
            # Add item to wishlist
            item, created = WishlistItem.objects.get_or_create(
                wishlist=wishlist,
                product=product,
                defaults={
                    'notes': notes,
                    'priority': priority,
                    'price_alert_threshold': Decimal(price_alert) if price_alert else None
                }
            )
            
            if not created:
                return JsonResponse({
                    'success': False,
                    'error': 'Produit déjà dans la liste de souhaits'
                })
            
            # Track behavior
            ai_engine.track_user_behavior(
                user=request.user,
                action_type='LIKE',
                product=product,
                session_id=request.session.session_key
            )
            
            return JsonResponse({
                'success': True,
                'message': f'{product.title} ajouté à votre liste de souhaits'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# ============= AI RECOMMENDATIONS =============

class RecommendationsView(LoginRequiredMixin, TemplateView):
    """AI-powered product recommendations"""
    template_name = 'backend/recommendations/list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get AI recommendations
        recommendations = ai_engine.generate_recommendations_for_user(
            user=self.request.user,
            num_recommendations=24
        )
        
        # Group recommendations by type
        rec_by_type = {}
        for rec in recommendations:
            rec_type = rec['type']
            if rec_type not in rec_by_type:
                rec_by_type[rec_type] = []
            rec_by_type[rec_type].append(rec)
        
        context.update({
            'recommendations': recommendations,
            'recommendations_by_type': rec_by_type,
            'total_count': len(recommendations)
        })
        
        return context

@login_required
def recommendation_feedback(request):
    """Handle recommendation feedback (clicked, purchased, etc.)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            feedback_type = data.get('feedback_type')  # 'clicked', 'purchased', 'not_interested'
            
            # Update recommendation record
            recommendation = ProductRecommendation.objects.filter(
                user=request.user,
                product_id=product_id
            ).first()
            
            if recommendation:
                if feedback_type == 'clicked':
                    recommendation.is_clicked = True
                elif feedback_type == 'purchased':
                    recommendation.is_purchased = True
                
                recommendation.save()
            
            # Track behavior for AI learning
            if feedback_type == 'clicked':
                ai_engine.track_user_behavior(
                    user=request.user,
                    action_type='VIEW',
                    product_id=product_id,
                    session_id=request.session.session_key,
                    metadata={'source': 'recommendation'}
                )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# ============= SOCIAL FEATURES =============

class SocialFeedView(LoginRequiredMixin, ListView):
    """Social feed with user-generated content"""
    model = SocialPost
    template_name = 'backend/social/feed.html'
    context_object_name = 'posts'
    paginate_by = 20
    
    def get_queryset(self):
        # Get posts from followed users + own posts + featured posts
        following_users = UserFollow.objects.filter(
            follower=self.request.user
        ).values_list('following_id', flat=True)
        
        return SocialPost.objects.filter(
            Q(author__in=following_users) |
            Q(author=self.request.user) |
            Q(is_featured=True)
        ).select_related('author').prefetch_related('products').order_by('-created_at')

class UserFollowView(LoginRequiredMixin, View):
    """Follow/unfollow users"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            action = data.get('action')  # 'follow' or 'unfollow'
            
            target_user = get_object_or_404(User, id=user_id)
            
            if target_user == request.user:
                return JsonResponse({
                    'success': False,
                    'error': 'Vous ne pouvez pas vous suivre vous-même'
                })
            
            if action == 'follow':
                follow, created = UserFollow.objects.get_or_create(
                    follower=request.user,
                    following=target_user
                )
                
                if created:
                    # Send notification to followed user
                    smart_notifications.trigger_notification(
                        template_name='new_follower',
                        user=target_user,
                        context={
                            'follower_name': request.user.get_full_name() or request.user.username,
                            'follower_url': f'/seller/{request.user.id}/'
                        }
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Vous suivez maintenant {target_user.get_full_name()}',
                        'following': True
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Vous suivez déjà cet utilisateur'
                    })
            
            elif action == 'unfollow':
                deleted, _ = UserFollow.objects.filter(
                    follower=request.user,
                    following=target_user
                ).delete()
                
                if deleted:
                    return JsonResponse({
                        'success': True,
                        'message': f'Vous ne suivez plus {target_user.get_full_name()}',
                        'following': False
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Vous ne suiviez pas cet utilisateur'
                    })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
        
        return JsonResponse({'success': False, 'error': 'Invalid action'})

class CreateSocialPostView(LoginRequiredMixin, CreateView):
    """Create social media post"""
    model = SocialPost
    template_name = 'backend/social/create_post.html'
    fields = ['post_type', 'title', 'content', 'products', 'tags']
    success_url = reverse_lazy('backend:social_feed')
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

# ============= ENHANCED REVIEWS =============

class EnhancedReviewCreateView(LoginRequiredMixin, CreateView):
    """Create enhanced review with media"""
    model = ProductReview
    template_name = 'backend/reviews/create_enhanced.html'
    fields = [
        'overall_rating', 'quality_rating', 'seller_rating', 'delivery_rating',
        'title', 'content', 'pros', 'cons'
    ]
    
    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(
            Order,
            id=kwargs['order_id'],
            buyer=request.user,
            status='DELIVERED'
        )
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.order = self.order
        form.instance.reviewer = self.request.user
        form.instance.product = self.order.product
        
        with transaction.atomic():
            response = super().form_valid(form)
            
            # Handle media uploads
            media_files = self.request.FILES.getlist('media_files')
            for i, media_file in enumerate(media_files):
                media_type = 'IMAGE' if media_file.content_type.startswith('image/') else 'VIDEO'
                
                ReviewMedia.objects.create(
                    review=self.object,
                    media_type=media_type,
                    file=media_file,
                    order=i
                )
            
            # Award loyalty points for detailed review
            if len(form.instance.content) > 100:  # Detailed review
                self.request.user.loyalty_points += 50
                self.request.user.save()
                
                # Send notification about points earned
                smart_notifications.trigger_notification(
                    template_name='loyalty_points_earned',
                    user=self.request.user,
                    context={
                        'points_earned': 50,
                        'reason': 'Avis détaillé',
                        'new_total': self.request.user.loyalty_points
                    }
                )
        
        messages.success(
            self.request,
            'Merci pour votre avis! Vous avez gagné 50 points de fidélité.'
        )
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = self.order
        context['product'] = self.order.product
        return context

# ============= SMART SEARCH =============

class SmartSearchView(ListView):
    """Enhanced search with AI and filters"""
    model = Product
    template_name = 'backend/search/smart_results.html'
    context_object_name = 'products'
    paginate_by = 24
    
    def get_queryset(self):
        query = self.request.GET.get('q', '')
        
        if not query:
            return Product.objects.none()
        
        # Basic text search
        products = Product.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            status='ACTIVE'
        ).select_related('category', 'seller').prefetch_related('images')
        
        # Apply filters
        products = self._apply_filters(products)
        
        # AI-enhanced ranking
        if self.request.user.is_authenticated:
            products = self._ai_rank_results(products, query)
        
        # Track search behavior
        if self.request.user.is_authenticated:
            ai_engine.track_user_behavior(
                user=self.request.user,
                action_type='SEARCH',
                session_id=self.request.session.session_key,
                metadata={
                    'search_query': query,
                    'results_count': products.count()
                }
            )
        
        return products
    
    def _apply_filters(self, queryset):
        """Apply search filters"""
        # Category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Price range
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Condition
        condition = self.request.GET.get('condition')
        if condition:
            queryset = queryset.filter(condition=condition)
        
        # City
        city = self.request.GET.get('city')
        if city:
            queryset = queryset.filter(city=city)
        
        # Sort
        sort = self.request.GET.get('sort', 'relevance')
        if sort == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort == 'popular':
            queryset = queryset.order_by('-views_count')
        
        return queryset
    
    def _ai_rank_results(self, queryset, query):
        """Use AI to rank search results based on user preferences"""
        try:
            user_prefs = ai_engine._get_or_create_user_preferences(self.request.user)
            
            # Get user's preferred categories
            preferred_cat_ids = [
                cat['category_id'] for cat in user_prefs.preferred_categories
            ]
            
            # Boost products from preferred categories
            if preferred_cat_ids:
                queryset = queryset.annotate(
                    preference_boost=Case(
                        When(category_id__in=preferred_cat_ids, then=1),
                        default=0
                    )
                ).order_by('-preference_boost', '-views_count')
            
        except Exception as e:
            pass  # Fall back to default ordering
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        query = self.request.GET.get('q', '')
        context.update({
            'search_query': query,
            'categories': Category.objects.filter(is_active=True),
            'cities': User.CITIES,
            'conditions': Product.CONDITIONS,
            'current_filters': {
                'category': self.request.GET.get('category', ''),
                'min_price': self.request.GET.get('min_price', ''),
                'max_price': self.request.GET.get('max_price', ''),
                'condition': self.request.GET.get('condition', ''),
                'city': self.request.GET.get('city', ''),
                'sort': self.request.GET.get('sort', 'relevance')
            }
        })
        
        # Add search suggestions for empty results
        if not context['products'] and query:
            context['suggestions'] = self._get_search_suggestions(query)
        
        return context
    
    def _get_search_suggestions(self, query):
        """Get search suggestions for failed searches"""
        suggestions = []
        
        # Find similar product titles
        similar_products = Product.objects.filter(
            title__icontains=query[:3],  # Partial match
            status='ACTIVE'
        ).values_list('title', flat=True)[:5]
        
        suggestions.extend(similar_products)
        
        # Add category suggestions
        similar_categories = Category.objects.filter(
            name__icontains=query,
            is_active=True
        ).values_list('name', flat=True)[:3]
        
        suggestions.extend(similar_categories)
        
        return suggestions[:8]

# ============= PERSONAL ANALYTICS =============

class PersonalAnalyticsView(LoginRequiredMixin, TemplateView):
    """Personal analytics dashboard for clients"""
    template_name = 'backend/analytics/personal.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Sales analytics (if user is a seller)
        sales_data = self._get_sales_analytics(user)
        
        # Buying analytics
        buying_data = self._get_buying_analytics(user)
        
        # Engagement analytics
        engagement_data = self._get_engagement_analytics(user)
        
        context.update({
            'sales_data': sales_data,
            'buying_data': buying_data,
            'engagement_data': engagement_data,
            'loyalty_progress': self._get_loyalty_progress(user)
        })
        
        return context
    
    def _get_sales_analytics(self, user):
        """Get seller analytics"""
        products = Product.objects.filter(seller=user)
        orders = Order.objects.filter(product__seller=user)
        
        return {
            'total_products': products.count(),
            'active_products': products.filter(status='ACTIVE').count(),
            'sold_products': products.filter(status='SOLD').count(),
            'total_revenue': orders.filter(status='DELIVERED').aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
            'avg_product_price': products.aggregate(
                avg=Avg('price')
            )['avg'] or 0,
            'most_viewed_product': products.order_by('-views_count').first()
        }
    
    def _get_buying_analytics(self, user):
        """Get buyer analytics"""
        orders = Order.objects.filter(buyer=user)
        
        return {
            'total_orders': orders.count(),
            'total_spent': orders.filter(status='DELIVERED').aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
            'avg_order_value': orders.aggregate(
                avg=Avg('total_amount')
            )['avg'] or 0,
            'favorite_categories': self._get_favorite_categories(user),
            'recent_orders': orders.order_by('-created_at')[:5]
        }
    
    def _get_engagement_analytics(self, user):
        """Get user engagement analytics"""
        behaviors = UserBehavior.objects.filter(user=user)
        
        return {
            'total_views': behaviors.filter(action_type='VIEW').count(),
            'total_likes': behaviors.filter(action_type='LIKE').count(),
            'total_searches': behaviors.filter(action_type='SEARCH').count(),
            'avg_session_duration': behaviors.aggregate(
                avg=Avg('duration')
            )['avg'] or 0,
            'most_active_hour': self._get_most_active_hour(user)
        }
    
    def _get_favorite_categories(self, user):
        """Get user's favorite categories based on purchases"""
        return Category.objects.filter(
            products__order__buyer=user
        ).annotate(
            purchase_count=Count('products__order')
        ).order_by('-purchase_count')[:5]
    
    def _get_most_active_hour(self, user):
        """Get user's most active hour"""
        behaviors = UserBehavior.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(days=30)
        ).extra(
            select={'hour': 'EXTRACT(hour FROM created_at)'}
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return behaviors[0]['hour'] if behaviors else 19  # Default to 7 PM
    
    def _get_loyalty_progress(self, user):
        """Get loyalty program progress"""
        current_points = user.loyalty_points
        
        thresholds = {
            'BRONZE': 0,
            'SILVER': 1000,
            'GOLD': 5000,
            'PLATINUM': 20000
        }
        
        current_level = user.loyalty_level
        next_level = None
        points_to_next = 0
        
        for level, threshold in thresholds.items():
            if current_points < threshold:
                next_level = level
                points_to_next = threshold - current_points
                break
        
        return {
            'current_level': current_level,
            'current_points': current_points,
            'next_level': next_level,
            'points_to_next': points_to_next,
            'progress_percentage': min((current_points / thresholds.get(next_level, 20000)) * 100, 100) if next_level else 100
        } 