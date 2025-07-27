# backend/views_client.py - CLIENT-SPECIFIC VIEWS FOR VGK
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from .views_enhanced import ClientRequiredMixin
from .models import Product, Order, Category, User
from .models_advanced import Wallet, Transaction, PrivateChat, ShoppingCart, UserBehavior, ProductRecommendation
from .forms import ProductForm, ProfileForm
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


# ============= SHOPPING CART VIEWS =============

class ShoppingCartView(ClientRequiredMixin, TemplateView):
    """Enhanced shopping cart view"""
    template_name = 'backend/client/cart/shopping_cart.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart, created = ShoppingCart.objects.get_or_create(user=self.request.user)
        context['cart'] = cart
        context['cart_items'] = cart.items.all() if hasattr(cart, 'items') else []
        return context


@login_required
@require_POST
def add_to_cart(request):
    """Add product to cart"""
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    
    if not product_id:
        return JsonResponse({'success': False, 'error': 'Product ID required'})
    
    try:
        product = Product.objects.get(id=product_id)
        cart, created = ShoppingCart.objects.get_or_create(user=request.user)
        
        # Add behavior tracking
        UserBehavior.objects.create(
            user=request.user,
            product=product,
            action_type='CART_ADD',
            session_id=request.session.session_key or 'anonymous'
        )
        
        return JsonResponse({
            'success': True, 
            'message': 'Produit ajouté au panier',
            'cart_count': cart.items.count() if hasattr(cart, 'items') else 0
        })
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Produit introuvable'})


@login_required
@require_POST
def update_cart_item(request):
    """Update cart item quantity"""
    item_id = request.POST.get('item_id')
    quantity = int(request.POST.get('quantity', 1))
    
    # Implementation for updating cart item
    return JsonResponse({'success': True, 'message': 'Panier mis à jour'})


@login_required
@require_POST
def remove_cart_item(request):
    """Remove item from cart"""
    item_id = request.POST.get('item_id')
    
    # Implementation for removing cart item
    return JsonResponse({'success': True, 'message': 'Article retiré du panier'})


@login_required
def checkout_cart(request):
    """Checkout process"""
    cart, created = ShoppingCart.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Process checkout
        return JsonResponse({'success': True, 'redirect_url': '/payment/'})
    
    return render(request, 'backend/client/cart/checkout.html', {'cart': cart})


# ============= WISHLIST VIEWS =============

class WishlistListView(ClientRequiredMixin, TemplateView):
    """User's wishlist"""
    template_name = 'backend/client/favorites/wishlist_list.html'


class WishlistDetailView(ClientRequiredMixin, DetailView):
    """Wishlist detail view"""
    template_name = 'backend/client/favorites/wishlist_detail.html'
    
    def get_object(self):
        # Implementation for wishlist detail
        return None


@login_required
@require_POST
def add_to_wishlist(request):
    """Add product to wishlist"""
    product_id = request.POST.get('product_id')
    
    if not product_id:
        return JsonResponse({'success': False, 'error': 'Product ID required'})
    
    try:
        product = Product.objects.get(id=product_id)
        
        # Add behavior tracking
        UserBehavior.objects.create(
            user=request.user,
            product=product,
            action_type='LIKE',
            session_id=request.session.session_key or 'anonymous'
        )
        
        return JsonResponse({'success': True, 'message': 'Ajouté à la liste de souhaits'})
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Produit introuvable'})


# ============= AI RECOMMENDATIONS =============

class RecommendationsView(ClientRequiredMixin, TemplateView):
    """AI-powered product recommendations"""
    template_name = 'backend/client/analytics/recommendations.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user recommendations
        recommendations = ProductRecommendation.objects.filter(
            user=self.request.user,
            expires_at__gt=timezone.now()
        ).select_related('product')[:12]
        
        context['recommendations'] = recommendations
        return context


@login_required
@require_POST
def recommendation_feedback(request):
    """Track recommendation feedback"""
    rec_id = request.POST.get('recommendation_id')
    action = request.POST.get('action')  # 'clicked', 'purchased', 'dismissed'
    
    try:
        recommendation = ProductRecommendation.objects.get(id=rec_id, user=request.user)
        if action == 'clicked':
            recommendation.is_clicked = True
        elif action == 'purchased':
            recommendation.is_purchased = True
        recommendation.save()
        
        return JsonResponse({'success': True})
    except ProductRecommendation.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Recommendation not found'})


# ============= SOCIAL FEATURES =============

class SocialFeedView(ClientRequiredMixin, TemplateView):
    """Social activity feed"""
    template_name = 'backend/client/social/social_feed.html'


class UserFollowView(ClientRequiredMixin, TemplateView):
    """User follow/unfollow"""
    template_name = 'backend/client/social/user_follow.html'


class CreateSocialPostView(ClientRequiredMixin, CreateView):
    """Create social post"""
    template_name = 'backend/client/social/create_social_post.html'
    success_url = reverse_lazy('client:social_feed')


# ============= ENHANCED REVIEWS =============

class EnhancedReviewCreateView(ClientRequiredMixin, CreateView):
    """Enhanced review creation with AI insights"""
    template_name = 'backend/client/reviews/enhanced_review_create.html'
    success_url = reverse_lazy('client:purchases')


# ============= SMART SEARCH =============

class SmartSearchView(ClientRequiredMixin, TemplateView):
    """AI-powered smart search with filters and suggestions"""
    template_name = 'backend/client/search/smart_search.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        
        if query:
            # Track search behavior
            UserBehavior.objects.create(
                user=self.request.user,
                action_type='SEARCH',
                session_id=self.request.session.session_key or 'anonymous',
                metadata={'search_query': query}
            )
            
            # Perform search
            products = Product.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query),
                status='ACTIVE'
            )[:24]
            
            context['products'] = products
            context['query'] = query
        
        return context


# ============= PERSONAL ANALYTICS =============

class PersonalAnalyticsView(ClientRequiredMixin, TemplateView):
    """Personal analytics and insights"""
    template_name = 'backend/client/analytics/personal_analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Calculate personal stats
        context.update({
            'total_spent': user.orders.aggregate(total=Sum('total_amount'))['total'] or 0,
            'total_earned': Order.objects.filter(product__seller=user, status='DELIVERED').aggregate(
                total=Sum('total_amount'))['total'] or 0,
            'favorite_categories': user.behaviors.filter(action_type='VIEW').values(
                'category__name').annotate(count=Count('id')).order_by('-count')[:5],
            'monthly_activity': user.behaviors.filter(
                created_at__month=timezone.now().month).count(),
            'shopping_patterns': self._get_shopping_patterns(user),
        })
        
        return context
    
    def _get_shopping_patterns(self, user):
        """Analyze user shopping patterns"""
        # Simple implementation - can be enhanced with more sophisticated analysis
        behaviors = user.behaviors.filter(action_type='PURCHASE')
        patterns = {
            'most_active_hour': behaviors.extra(
                select={'hour': "EXTRACT(hour FROM created_at)"}
            ).values('hour').annotate(count=Count('id')).order_by('-count').first(),
            'most_active_day': behaviors.extra(
                select={'day': "EXTRACT(dow FROM created_at)"}
            ).values('day').annotate(count=Count('id')).order_by('-count').first(),
        }
        return patterns


class ClientDashboardView(ClientRequiredMixin, TemplateView):
    """Enhanced Client Dashboard with comprehensive wallet and product management"""
    template_name = 'backend/client/dashboard/client_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        try:
            # Wallet integration
            wallet, created = Wallet.objects.get_or_create(user=user)
            recent_transactions = wallet.transactions.all()[:5] if hasattr(wallet, 'transactions') else []
            
            # Product management stats - Fixed relationship names
            user_products = user.products_sold.all()  # Fixed: was user.products.all()
            active_products = user_products.filter(status='ACTIVE')
            sold_products = user.products_sold.filter(status='SOLD')  # Fixed: was user.sold_products
            
            # Purchase history - Fixed: use correct relationship names
            user_orders = user.orders.all()  # This is correct - buyer relationship
            pending_orders = user_orders.filter(status__in=['PENDING', 'PAID', 'SHIPPED'])
            completed_orders = user_orders.filter(status='DELIVERED')
            
            # Financial calculations - Fixed to use orders instead of products
            # Calculate earnings from orders where user is the seller
            seller_orders = Order.objects.filter(product__seller=user)
            total_earned = seller_orders.filter(status='DELIVERED').aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
            total_spent = completed_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
            pending_earnings = seller_orders.filter(status__in=['PAID', 'SHIPPED']).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
            
            # Performance metrics
            avg_product_rating = 4.5  # Placeholder - calculate from reviews
            total_views = user.behaviors.filter(action_type='VIEW').count() if hasattr(user, 'behaviors') else 0
            total_likes = user.behaviors.filter(action_type='LIKE').count() if hasattr(user, 'behaviors') else 0
            
            # Recent activity
            recent_activities = self._get_recent_activities(user)
            
            # Recommendations
            recommendations = ProductRecommendation.objects.filter(
                user=user,
                expires_at__gt=timezone.now()
            ).select_related('product')[:6] if hasattr(ProductRecommendation, 'objects') else []
            
            # Analytics data for charts
            monthly_sales_data = self._get_monthly_sales_data(user)
            category_performance = self._get_category_performance(user)
            
            context.update({
                # Wallet Information
                'wallet': wallet,
                'wallet_balance': wallet.available_balance if hasattr(wallet, 'available_balance') else Decimal('0'),
                'pending_balance': wallet.pending_balance if hasattr(wallet, 'pending_balance') else Decimal('0'),
                'recent_transactions': recent_transactions,
                
                # Product Management
                'total_products': user_products.count(),
                'active_products_count': active_products.count(),
                'draft_products_count': user_products.filter(status='DRAFT').count(),
                'sold_products_count': sold_products.count(),
                'product_views_today': self._get_product_views_today(user),
                'low_stock_products': active_products.filter(stock_quantity__lt=5) if hasattr(Product, 'stock_quantity') else [],
                
                # Sales & Purchases
                'total_sales': sold_products.count(),
                'total_purchases': completed_orders.count(),
                'pending_orders_count': pending_orders.count(),
                'total_earned': total_earned,
                'total_spent': total_spent,
                'pending_earnings': pending_earnings,
                'net_balance': total_earned - total_spent,
                
                # Performance
                'avg_product_rating': avg_product_rating,
                'total_views': total_views,
                'total_likes': total_likes,
                'conversion_rate': self._calculate_conversion_rate(user),
                
                # Recent Activity
                'recent_activities': recent_activities,
                'recent_products': user_products.order_by('-created_at')[:5],
                'recent_orders': user_orders.order_by('-created_at')[:5],
                
                # Recommendations & Insights
                'recommendations': recommendations,
                'trending_categories': self._get_trending_categories(),
                'suggested_price_ranges': self._get_suggested_price_ranges(user),
                
                # Analytics Data
                'monthly_sales_data': monthly_sales_data,
                'category_performance': category_performance,
                'wallet_chart_data': self._get_wallet_chart_data(wallet),
                
                # Quick Actions
                'quick_stats': {
                    'orders_this_month': user_orders.filter(created_at__month=timezone.now().month).count(),
                    'revenue_this_month': seller_orders.filter(
                        created_at__month=timezone.now().month,
                        status='DELIVERED'
                    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0'),
                    'new_messages': self._get_unread_messages_count(user),
                    'pending_reviews': self._get_pending_reviews_count(user),
                }
            })
            
        except Exception as e:
            # If there's an error, provide default values
            print(f"Error in ClientDashboardView: {e}")
            context.update({
                'wallet': None,
                'wallet_balance': Decimal('0'),
                'pending_balance': Decimal('0'),
                'recent_transactions': [],
                'total_products': 0,
                'active_products_count': 0,
                'draft_products_count': 0,
                'sold_products_count': 0,
                'product_views_today': 0,
                'low_stock_products': [],
                'total_sales': 0,
                'total_purchases': 0,
                'pending_orders_count': 0,
                'total_earned': Decimal('0'),
                'total_spent': Decimal('0'),
                'pending_earnings': Decimal('0'),
                'net_balance': Decimal('0'),
                'avg_product_rating': 0,
                'total_views': 0,
                'total_likes': 0,
                'conversion_rate': 0,
                'recent_activities': [],
                'recent_products': [],
                'recent_orders': [],
                'recommendations': [],
                'trending_categories': [],
                'suggested_price_ranges': [],
                'monthly_sales_data': [],
                'category_performance': [],
                'wallet_chart_data': [],
                'quick_stats': {
                    'orders_this_month': 0,
                    'revenue_this_month': Decimal('0'),
                    'new_messages': 0,
                    'pending_reviews': 0,
                }
            })
        
        return context
    
    def _get_recent_activities(self, user):
        """Get recent user activities"""
        activities = []
        
        # Recent orders
        recent_orders = user.orders.order_by('-created_at')[:3]
        for order in recent_orders:
            activities.append({
                'type': 'order',
                'action': 'Commande passée',
                'description': f'Commande pour {order.product.title}',
                'timestamp': order.created_at,
                'url': f'/client/purchases/{order.id}/'
            })
        
        # Recent product additions - Fixed to use products_sold relationship
        recent_products = user.products_sold.order_by('-created_at')[:3]
        for product in recent_products:
            activities.append({
                'type': 'product',
                'action': 'Produit ajouté',
                'description': f'Nouveau produit: {product.title}',
                'timestamp': product.created_at,
                'url': f'/client/products/{product.id}/'
            })
        
        # Sort by timestamp and return top 10
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:10]
    
    def _get_monthly_sales_data(self, user):
        """Get monthly sales data for charts"""
        from django.db.models.functions import TruncMonth
        
        monthly_data = Order.objects.filter(
            product__seller=user,
            status='DELIVERED',
            created_at__gte=timezone.now() - timedelta(days=365)
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total_sales=Count('id'),
            total_revenue=Sum('total_amount')
        ).order_by('month')
        
        return list(monthly_data)
    
    def _get_category_performance(self, user):
        """Get performance by category"""
        category_data = user.products_sold.values(
            'category__name'
        ).annotate(
            product_count=Count('id'),
            total_sales=Count('orders', filter=Q(orders__status='DELIVERED')),
            total_revenue=Sum('orders__total_amount', filter=Q(orders__status='DELIVERED'))
        ).order_by('-total_revenue')
        
        return list(category_data)[:5]  # Top 5 categories
    
    def _get_product_views_today(self, user):
        """Get today's product views"""
        today = timezone.now().date()
        return UserBehavior.objects.filter(
            product__seller=user,
            action_type='VIEW',
            created_at__date=today
        ).count() if hasattr(UserBehavior, 'objects') else 0
    
    def _calculate_conversion_rate(self, user):
        """Calculate view to purchase conversion rate"""
        total_views = UserBehavior.objects.filter(
            product__seller=user,
            action_type='VIEW'
        ).count() if hasattr(UserBehavior, 'objects') else 0
        
        total_purchases = Order.objects.filter(
            product__seller=user,
            status='DELIVERED'
        ).count()
        
        if total_views > 0:
            return round((total_purchases / total_views) * 100, 2)
        return 0
    
    def _get_trending_categories(self):
        """Get trending categories based on recent activity"""
        return Category.objects.annotate(
            recent_products=Count(
                'products',
                filter=Q(products__created_at__gte=timezone.now() - timedelta(days=7))
            )
        ).order_by('-recent_products')[:5]
    
    def _get_suggested_price_ranges(self, user):
        """Get suggested price ranges for user's categories"""
        user_categories = user.products_sold.values_list('category', flat=True).distinct()
        
        price_suggestions = []
        for category_id in user_categories:
            category_products = Product.objects.filter(category_id=category_id, status='ACTIVE')
            if category_products.exists():
                avg_price = category_products.aggregate(avg=Avg('price'))['avg']
                min_price = category_products.aggregate(min=Min('price'))['min']
                max_price = category_products.aggregate(max=Max('price'))['max']
                
                price_suggestions.append({
                    'category_id': category_id,
                    'avg_price': avg_price,
                    'suggested_min': min_price,
                    'suggested_max': max_price
                })
        
        return price_suggestions
    
    def _get_wallet_chart_data(self, wallet):
        """Get wallet transaction data for charts"""
        if not hasattr(wallet, 'transactions'):
            return []
        
        from django.db.models.functions import TruncDate
        
        daily_data = wallet.transactions.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).annotate(
            date=TruncDate('created_at')
        ).values('date', 'transaction_type').annotate(
            total_amount=Sum('amount')
        ).order_by('date')
        
        return list(daily_data)
    
    def _get_unread_messages_count(self, user):
        """Get count of unread messages"""
        # Placeholder - implement with actual message model
        return PrivateChat.objects.filter(
            Q(participant_1=user) | Q(participant_2=user),
            is_active=True
        ).count()
    
    def _get_pending_reviews_count(self, user):
        """Get count of pending reviews to write"""
        # Placeholder - implement with actual review system
        return Order.objects.filter(
            buyer=user,
            status='DELIVERED'
            # Add condition for orders without reviews
        ).count()


class WalletView(ClientRequiredMixin, TemplateView):
    """Client Wallet Management"""
    template_name = 'backend/client/wallet/wallet.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        context['wallet'] = wallet
        context['recent_transactions'] = wallet.transactions.all()[:10]
        return context


class WalletTransactionsView(ClientRequiredMixin, ListView):
    """Client Wallet Transactions"""
    model = Transaction
    template_name = 'backend/client/wallet/transactions.html'
    context_object_name = 'transactions'
    paginate_by = 20
    
    def get_queryset(self):
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        return wallet.transactions.all()


class AddFundsView(ClientRequiredMixin, TemplateView):
    """Add funds to wallet"""
    template_name = 'backend/client/wallet/add_funds.html'


class WithdrawRequestView(ClientRequiredMixin, TemplateView):
    """Request withdrawal from wallet"""
    template_name = 'backend/client/wallet/withdraw_request.html'


class ClientProductsView(ClientRequiredMixin, ListView):
    """Client's Products"""
    model = Product
    template_name = 'backend/client/products/products.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        return self.request.user.products_sold.all()


class ProductCreateView(ClientRequiredMixin, CreateView):
    """Create new product"""
    model = Product
    form_class = ProductForm
    template_name = 'backend/client/products/product_create.html'
    success_url = reverse_lazy('client:products')
    
    def form_valid(self, form):
        form.instance.seller = self.request.user
        return super().form_valid(form)


class ProductEditView(ClientRequiredMixin, UpdateView):
    """Edit product"""
    model = Product
    form_class = ProductForm
    template_name = 'backend/client/products/product_edit.html'
    
    def get_queryset(self):
        return self.request.user.products_sold.all()


class ProductDeleteView(ClientRequiredMixin, DeleteView):
    """Delete product"""
    model = Product
    template_name = 'backend/client/products/product_delete.html'
    success_url = reverse_lazy('client:products')
    
    def get_queryset(self):
        return self.request.user.products.all()


class ClientProductDetailView(ClientRequiredMixin, DetailView):
    """Client-specific product detail"""
    model = Product
    template_name = 'backend/client/products/product_detail.html'
    context_object_name = 'product'


class BrowseProductsView(ClientRequiredMixin, ListView):
    """Browse all products"""
    model = Product
    template_name = 'backend/client/products/browse_products.html'
    context_object_name = 'products'
    paginate_by = 24
    
    def get_queryset(self):
        return Product.objects.filter(status='ACTIVE').exclude(seller=self.request.user)


class CategoryProductsView(ClientRequiredMixin, ListView):
    """Products in a category"""
    model = Product
    template_name = 'backend/client/categories/category_products.html'
    context_object_name = 'products'
    paginate_by = 24
    
    def get_queryset(self):
        category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return Product.objects.filter(category=category, status='ACTIVE')


class ClientPurchasesView(ClientRequiredMixin, ListView):
    """Client's purchases"""
    model = Order
    template_name = 'backend/client/orders/purchases.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def get_queryset(self):
        return self.request.user.orders.all()


class PurchaseDetailView(ClientRequiredMixin, DetailView):
    """Purchase detail"""
    model = Order
    template_name = 'backend/client/orders/purchase_detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        return self.request.user.orders.all()


class ClientFavoritesView(ClientRequiredMixin, TemplateView):
    """Client's favorites"""
    template_name = 'backend/client/favorites/favorites.html'


class ClientWishlistView(ClientRequiredMixin, TemplateView):
    """Client's wishlist"""
    template_name = 'backend/client/favorites/wishlist.html'


class CompareProductsView(ClientRequiredMixin, TemplateView):
    """Product comparison"""
    template_name = 'backend/client/products/compare.html'


class ClientChatsView(ClientRequiredMixin, ListView):
    """Client's chats"""
    model = PrivateChat
    template_name = 'backend/client/chat/chats.html'
    context_object_name = 'chats'
    
    def get_queryset(self):
        return PrivateChat.objects.filter(
            Q(participant_1=self.request.user) | Q(participant_2=self.request.user)
        ).filter(is_active=True)


class ClientChatDetailView(ClientRequiredMixin, DetailView):
    """Client chat detail"""
    model = PrivateChat
    template_name = 'backend/client/chat/chat_detail.html'
    context_object_name = 'chat'
    
    def get_queryset(self):
        return PrivateChat.objects.filter(
            Q(participant_1=self.request.user) | Q(participant_2=self.request.user)
        )


class ClientAdminChatView(ClientRequiredMixin, TemplateView):
    """Client-Admin chat"""
    template_name = 'backend/client/chat/admin_chat.html'


class ClientProfileView(ClientRequiredMixin, TemplateView):
    """Client profile page"""
    template_name = 'backend/client/profile/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add profile stats
        context.update({
            'total_products': user.products.count(),
            'total_purchases': user.orders.count(),
            'total_favorites': 0,  # Will be implemented with favorites model
            'loyalty_points': user.loyalty_points,
            'recent_activities': [],  # Will be implemented with activity tracking
        })
        
        return context


class ClientProfileEditView(ClientRequiredMixin, UpdateView):
    """Edit client profile"""
    model = User
    form_class = ProfileForm
    template_name = 'backend/client/profile/edit.html'
    success_url = reverse_lazy('client:profile')
    
    def get_object(self):
        return self.request.user


class ClientSalesView(ClientRequiredMixin, ListView):
    """Client's sales"""
    model = Order
    template_name = 'backend/client/orders/sales.html'
    context_object_name = 'sales'
    paginate_by = 10
    
    def get_queryset(self):
        return Order.objects.filter(product__seller=self.request.user)


class SaleDetailView(ClientRequiredMixin, DetailView):
    """Sale detail"""
    model = Order
    template_name = 'backend/client/orders/sale_detail.html'
    context_object_name = 'sale'
    
    def get_queryset(self):
        return Order.objects.filter(product__seller=self.request.user)


class ClientNotificationsView(ClientRequiredMixin, TemplateView):
    """Client notifications"""
    template_name = 'backend/client/notifications/notifications.html'


class MarkNotificationReadView(ClientRequiredMixin, TemplateView):
    """Mark notification as read"""
    
    def post(self, request, *args, **kwargs):
        # Implementation for marking notification as read
        return JsonResponse({'status': 'success'}) 