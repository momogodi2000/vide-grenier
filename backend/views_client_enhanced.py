# backend/views_client_enhanced.py - ENHANCED CLIENT DASHBOARD
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count, Avg, F, Max
from django.utils import timezone
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.utils.html import strip_tags
from django.templatetags.static import static
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from .models import (
    Product, Order, Category, PickupPoint, User, 
    ProductImage
)
from .models_advanced import (
    UserBehavior, UserPreference, ProductRecommendation,
    SocialPost, UserFollow, NotificationTemplate, SmartNotification,
    EscrowPayment, InstallmentPlan, InstallmentPayment,
    ShoppingCart, CartItem, Wishlist, WishlistItem,
    ProductReview, Commission, Wallet, Transaction,
    WithdrawalRequest, PrivateChat, PrivateMessage
)
from .forms import (
    ProductForm, OrderForm, ReviewForm, ProfileForm
)

User = get_user_model()
logger = logging.getLogger(__name__)

# ============= ENHANCED CLIENT DASHBOARD =============

@login_required
def client_dashboard(request):
    """Enhanced client dashboard with comprehensive analytics"""
    
    # Get user data
    user = request.user
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    # Sales Analytics
    recent_orders = Order.objects.filter(
        product__seller=user,
        created_at__gte=last_30_days
    ).order_by('-created_at')[:10]
    
    total_sales = Order.objects.filter(
        product__seller=user,
        status='COMPLETED'
    ).aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )
    
    monthly_sales = Order.objects.filter(
        product__seller=user,
        status='COMPLETED',
        created_at__gte=last_30_days
    ).aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )
    
    # Product Analytics
    active_products = Product.objects.filter(
        seller=user,
        status='ACTIVE'
    ).count()
    
    total_products = Product.objects.filter(seller=user).count()
    
    # Views and Engagement
    product_views = UserBehavior.objects.filter(
        product__seller=user,
        action_type='VIEW',
        created_at__gte=last_30_days
    ).count()
    
    # Revenue Analytics
    revenue_data = Order.objects.filter(
        product__seller=user,
        status='COMPLETED',
        created_at__gte=last_30_days
    ).values('created_at__date').annotate(
        daily_revenue=Sum('total_amount'),
        order_count=Count('id')
    ).order_by('created_at__date')
    
    # Commission Analytics
    commission_data = Commission.objects.filter(
        seller=user,
        created_at__gte=last_30_days
    ).aggregate(
        total_commission=Sum('commission_amount'),
        total_earned=Sum('seller_amount')
    )
    
    # Wallet Information
    try:
        wallet = user.wallet
        wallet_balance = wallet.balance
        pending_balance = wallet.pending_balance
    except Wallet.DoesNotExist:
        wallet_balance = Decimal('0.00')
        pending_balance = Decimal('0.00')
    
    # Recent Transactions
    recent_transactions = Transaction.objects.filter(
        wallet__user=user
    ).order_by('-created_at')[:5]
    
    # Social Analytics
    followers_count = user.followers.count()
    following_count = user.following.count()
    social_posts = SocialPost.objects.filter(author=user).count()
    
    # AI Recommendations
    ai_recommendations = ProductRecommendation.objects.filter(
        user=user,
        expires_at__gte=timezone.now()
    ).order_by('-confidence_score')[:5]
    
    # Notifications
    unread_notifications = SmartNotification.objects.filter(
        user=user,
        status='PENDING'
    ).count()
    
    # Performance Metrics
    avg_order_value = total_sales['total'] / total_sales['count'] if total_sales['count'] > 0 else 0
    conversion_rate = (monthly_sales['count'] / product_views * 100) if product_views > 0 else 0
    
    context = {
        'user': user,
        'recent_orders': recent_orders,
        'total_sales': total_sales,
        'monthly_sales': monthly_sales,
        'active_products': active_products,
        'total_products': total_products,
        'product_views': product_views,
        'revenue_data': list(revenue_data),
        'commission_data': commission_data,
        'wallet_balance': wallet_balance,
        'pending_balance': pending_balance,
        'recent_transactions': recent_transactions,
        'followers_count': followers_count,
        'following_count': following_count,
        'social_posts': social_posts,
        'ai_recommendations': ai_recommendations,
        'unread_notifications': unread_notifications,
        'avg_order_value': avg_order_value,
        'conversion_rate': conversion_rate,
    }
    
    return render(request, 'backend/client/dashboard/enhanced_dashboard.html', context)

@login_required
def client_analytics(request):
    """Detailed analytics for client"""
    
    user = request.user
    period = request.GET.get('period', '30')  # days
    days = int(period)
    start_date = timezone.now().date() - timedelta(days=days)
    
    # Sales Analytics
    sales_data = Order.objects.filter(
        product__seller=user,
        created_at__gte=start_date
    ).values('created_at__date').annotate(
        daily_sales=Sum('total_amount'),
        order_count=Count('id'),
        avg_order=Avg('total_amount')
    ).order_by('created_at__date')
    
    # Product Performance
    product_performance = Product.objects.filter(
        seller=user
    ).annotate(
        total_sales=Sum('orders__total_amount'),
        order_count=Count('orders'),
        view_count=Count('behaviors', filter=Q(behaviors__action_type='VIEW')),
        like_count=Count('likes', filter=Q(likes__like_type='LIKE'))
    ).order_by('-total_sales')[:10]
    
    # Category Performance
    category_performance = Category.objects.filter(
        products__seller=user,
        products__orders__created_at__gte=start_date
    ).annotate(
        total_sales=Sum('products__orders__total_amount'),
        product_count=Count('products'),
        order_count=Count('products__orders')
    ).order_by('-total_sales')
    
    # Customer Analytics
    customer_data = Order.objects.filter(
        product__seller=user,
        created_at__gte=start_date
    ).values('buyer').annotate(
        total_spent=Sum('total_amount'),
        order_count=Count('id'),
        last_order=Max('created_at')
    ).order_by('-total_spent')[:10]
    
    # Revenue Trends
    revenue_trends = Order.objects.filter(
        product__seller=user,
        status='COMPLETED',
        created_at__gte=start_date
    ).extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        revenue=Sum('total_amount'),
        orders=Count('id')
    ).order_by('day')
    
    context = {
        'sales_data': list(sales_data),
        'product_performance': product_performance,
        'category_performance': category_performance,
        'customer_data': customer_data,
        'revenue_trends': list(revenue_trends),
        'period': period,
    }
    
    return render(request, 'backend/client/analytics/detailed_analytics.html', context)

@login_required
def client_loyalty_dashboard(request):
    """Loyalty system dashboard"""
    
    user = request.user
    
    # Calculate loyalty points
    total_orders = Order.objects.filter(buyer=user, status='COMPLETED').count()
    total_spent = Order.objects.filter(buyer=user, status='COMPLETED').aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')
    
    # Loyalty tiers (example calculation)
    if total_spent >= Decimal('100000'):  # 100,000 FCFA
        tier = 'GOLD'
        points_multiplier = 3
    elif total_spent >= Decimal('50000'):  # 50,000 FCFA
        tier = 'SILVER'
        points_multiplier = 2
    else:
        tier = 'BRONZE'
        points_multiplier = 1
    
    # Calculate points (1 point per 100 FCFA spent)
    points_earned = int(total_spent / 100) * points_multiplier
    points_used = 0  # This would come from a points usage model
    points_available = points_earned - points_used
    
    # Rewards available
    rewards = [
        {'name': '5% Discount', 'points_required': 100, 'description': '5% discount on next purchase'},
        {'name': 'Free Delivery', 'points_required': 50, 'description': 'Free delivery on next order'},
        {'name': 'Premium Support', 'points_required': 200, 'description': 'Priority customer support'},
        {'name': 'Exclusive Access', 'points_required': 500, 'description': 'Early access to new products'},
    ]
    
    # Recent point transactions
    point_transactions = []  # This would come from a points transaction model
    
    context = {
        'tier': tier,
        'points_earned': points_earned,
        'points_used': points_used,
        'points_available': points_available,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'rewards': rewards,
        'point_transactions': point_transactions,
    }
    
    return render(request, 'backend/client/loyalty/loyalty_dashboard.html', context)

@login_required
def client_wallet_dashboard(request):
    """Enhanced wallet management"""
    
    user = request.user
    
    try:
        wallet = user.wallet
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=user)
    
    # Transaction history
    transactions = Transaction.objects.filter(
        wallet=wallet
    ).order_by('-created_at')
    
    # Transaction statistics
    transaction_stats = transactions.aggregate(
        total_credit=Sum('amount', filter=Q(transaction_type='CREDIT')),
        total_debit=Sum('amount', filter=Q(transaction_type='DEBIT')),
        total_commission=Sum('amount', filter=Q(transaction_type='COMMISSION')),
    )
    
    # Pending withdrawal requests
    pending_withdrawals = WithdrawalRequest.objects.filter(
        user=user,
        status__in=['PENDING', 'APPROVED', 'PROCESSING']
    ).order_by('-requested_at')
    
    # Monthly transaction summary
    current_month = timezone.now().month
    monthly_transactions = transactions.filter(
        created_at__month=current_month
    ).aggregate(
        total_credit=Sum('amount', filter=Q(transaction_type='CREDIT')),
        total_debit=Sum('amount', filter=Q(transaction_type='DEBIT')),
        transaction_count=Count('id')
    )
    
    context = {
        'wallet': wallet,
        'transactions': transactions[:20],  # Last 20 transactions
        'transaction_stats': transaction_stats,
        'pending_withdrawals': pending_withdrawals,
        'monthly_transactions': monthly_transactions,
    }
    
    return render(request, 'backend/client/wallet/enhanced_wallet.html', context)

@login_required
def client_social_dashboard(request):
    """Social features dashboard"""
    
    user = request.user
    
    # User's social posts
    social_posts = SocialPost.objects.filter(
        author=user
    ).order_by('-created_at')
    
    # Followers and following
    followers = user.followers.all()
    following = user.following.all()
    
    # Feed (posts from followed users)
    followed_users = [follow.following for follow in user.following.all()]
    feed_posts = SocialPost.objects.filter(
        author__in=followed_users
    ).order_by('-created_at')[:20]
    
    # Social statistics
    total_likes = sum(post.likes_count for post in social_posts)
    total_comments = sum(post.comments_count for post in social_posts)
    total_shares = sum(post.shares_count for post in social_posts)
    
    # Trending posts
    trending_posts = SocialPost.objects.filter(
        is_featured=True
    ).order_by('-likes_count')[:5]
    
    context = {
        'social_posts': social_posts,
        'followers': followers,
        'following': following,
        'feed_posts': feed_posts,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_shares': total_shares,
        'trending_posts': trending_posts,
    }
    
    return render(request, 'backend/client/social/social_dashboard.html', context)

# ============= ENHANCED PRODUCT MANAGEMENT =============

class ClientProductListView(LoginRequiredMixin, ListView):
    """Enhanced product list for clients"""
    model = Product
    template_name = 'backend/client/products/enhanced_product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Product statistics
        context['total_products'] = Product.objects.filter(seller=user).count()
        context['active_products'] = Product.objects.filter(seller=user, status='ACTIVE').count()
        context['pending_products'] = Product.objects.filter(seller=user, status='PENDING').count()
        context['sold_products'] = Product.objects.filter(seller=user, status='SOLD').count()
        
        # Performance metrics
        context['total_views'] = UserBehavior.objects.filter(
            product__seller=user,
            action_type='VIEW'
        ).count()
        
        context['total_sales'] = Order.objects.filter(
            product__seller=user,
            status='COMPLETED'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        return context

class ClientProductCreateView(LoginRequiredMixin, CreateView):
    """Enhanced product creation"""
    model = Product
    form_class = ProductForm
    template_name = 'backend/client/products/enhanced_product_form.html'
    success_url = reverse_lazy('backend:client_product_list')
    
    def form_valid(self, form):
        form.instance.seller = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Produit créé avec succès!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['pickup_points'] = PickupPoint.objects.all()
        return context

class ClientProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Enhanced product update"""
    model = Product
    form_class = ProductForm
    template_name = 'backend/client/products/enhanced_product_form.html'
    success_url = reverse_lazy('backend:client_product_list')
    
    def test_func(self):
        product = self.get_object()
        return product.seller == self.request.user
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Produit mis à jour avec succès!')
        return response

# ============= ENHANCED ORDER MANAGEMENT =============

@login_required
def client_orders_dashboard(request):
    """Enhanced orders dashboard"""
    
    user = request.user
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    
    # Get orders (both as buyer and seller)
    orders_as_buyer = Order.objects.filter(buyer=user)
    orders_as_seller = Order.objects.filter(product__seller=user)
    
    # Apply filters
    if status_filter:
        orders_as_buyer = orders_as_buyer.filter(status=status_filter)
        orders_as_seller = orders_as_seller.filter(status=status_filter)
    
    if date_filter:
        if date_filter == 'today':
            today = timezone.now().date()
            orders_as_buyer = orders_as_buyer.filter(created_at__date=today)
            orders_as_seller = orders_as_seller.filter(created_at__date=today)
        elif date_filter == 'week':
            week_ago = timezone.now().date() - timedelta(days=7)
            orders_as_buyer = orders_as_buyer.filter(created_at__date__gte=week_ago)
            orders_as_seller = orders_as_seller.filter(created_at__date__gte=week_ago)
        elif date_filter == 'month':
            month_ago = timezone.now().date() - timedelta(days=30)
            orders_as_buyer = orders_as_buyer.filter(created_at__date__gte=month_ago)
            orders_as_seller = orders_as_seller.filter(created_at__date__gte=month_ago)
    
    # Pagination
    paginator = Paginator(orders_as_seller, 20)
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)
    
    # Order statistics
    order_stats = {
        'total_orders': orders_as_seller.count(),
        'pending_orders': orders_as_seller.filter(status='PENDING').count(),
        'processing_orders': orders_as_seller.filter(status='PROCESSING').count(),
        'completed_orders': orders_as_seller.filter(status='COMPLETED').count(),
        'cancelled_orders': orders_as_seller.filter(status='CANCELLED').count(),
    }
    
    # Revenue statistics
    revenue_stats = orders_as_seller.filter(status='COMPLETED').aggregate(
        total_revenue=Sum('total_amount'),
        avg_order_value=Avg('total_amount'),
        order_count=Count('id')
    )
    
    context = {
        'orders': orders_page,
        'orders_as_buyer': orders_as_buyer[:10],  # Recent purchases
        'order_stats': order_stats,
        'revenue_stats': revenue_stats,
        'status_filter': status_filter,
        'date_filter': date_filter,
    }
    
    return render(request, 'backend/client/orders/enhanced_orders_dashboard.html', context)

# ============= ENHANCED COMMUNICATION =============

@login_required
def client_chat_dashboard(request):
    """Enhanced chat dashboard"""
    
    user = request.user
    
    # Get user's chats
    chats = PrivateChat.objects.filter(
        Q(participant_1=user) | Q(participant_2=user)
    ).order_by('-last_message_at')
    
    # Unread message counts
    for chat in chats:
        chat.unread_count = PrivateMessage.objects.filter(
            private_chat=chat,
            sender__in=[chat.participant_1, chat.participant_2],
            sender__ne=user,
            is_read=False
        ).count()
    
    # Recent messages
    recent_messages = PrivateMessage.objects.filter(
        private_chat__in=chats
    ).order_by('-created_at')[:10]
    
    context = {
        'chats': chats,
        'recent_messages': recent_messages,
    }
    
    return render(request, 'backend/client/chat/enhanced_chat_dashboard.html', context)

# ============= API ENDPOINTS =============

@login_required
@require_POST
def client_analytics_data(request):
    """API endpoint for analytics data"""
    
    user = request.user
    period = request.POST.get('period', '30')
    days = int(period)
    start_date = timezone.now().date() - timedelta(days=days)
    
    # Sales data
    sales_data = Order.objects.filter(
        product__seller=user,
        created_at__gte=start_date
    ).values('created_at__date').annotate(
        sales=Sum('total_amount'),
        orders=Count('id')
    ).order_by('created_at__date')
    
    # Product performance
    product_data = Product.objects.filter(
        seller=user
    ).annotate(
        sales=Sum('orders__total_amount'),
        views=Count('behaviors', filter=Q(behaviors__action_type='VIEW'))
    ).values('title', 'sales', 'views')[:10]
    
    return JsonResponse({
        'sales_data': list(sales_data),
        'product_data': list(product_data),
    })

@login_required
@require_POST
def client_create_withdrawal_request(request):
    """Create withdrawal request"""
    
    try:
        data = json.loads(request.body)
        amount = Decimal(data.get('amount'))
        withdrawal_method = data.get('withdrawal_method')
        account_details = data.get('account_details', {})
        
        # Validate amount
        if amount <= 0:
            return JsonResponse({
                'success': False,
                'message': 'Montant invalide'
            })
        
        # Check wallet balance
        wallet = request.user.wallet
        if wallet.available_balance < amount:
            return JsonResponse({
                'success': False,
                'message': 'Solde insuffisant'
            })
        
        # Create withdrawal request
        withdrawal = WithdrawalRequest.objects.create(
            user=request.user,
            amount=amount,
            withdrawal_method=withdrawal_method,
            account_details=account_details
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Demande de retrait créée avec succès',
            'withdrawal_id': str(withdrawal.id)
        })
        
    except Exception as e:
        logger.error(f"Error creating withdrawal request: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors de la création de la demande'
        })

# @login_required
# @require_POST
# def client_create_social_post(request):
#     """Create social post"""
#     
#     try:
#         form = SocialPostForm(request.POST, request.FILES)
#         if form.is_valid():
#             post = form.save(commit=False)
#             post.author = request.user
#             post.save()
#             form.save_m2m()  # Save many-to-many relationships
#             
#             return JsonResponse({
#                 'success': True,
#                 'message': 'Post créé avec succès',
#                 'post_id': str(post.id)
#             })
#         else:
#             return JsonResponse({
#                 'success': False,
#                 'message': 'Données invalides',
#                 'errors': form.errors
#             })
#             
#     except Exception as e:
#         logger.error(f"Error creating social post: {str(e)}")
#         return JsonResponse({
#             'success': False,
#             'message': 'Erreur lors de la création du post'
#         })

@login_required
@require_POST
def client_follow_user(request, user_id):
    """Follow/unfollow user"""
    
    try:
        target_user = get_object_or_404(User, id=user_id)
        
        if target_user == request.user:
            return JsonResponse({
                'success': False,
                'message': 'Vous ne pouvez pas vous suivre vous-même'
            })
        
        # Check if already following
        existing_follow = UserFollow.objects.filter(
            follower=request.user,
            following=target_user
        ).first()
        
        if existing_follow:
            existing_follow.delete()
            action = 'unfollowed'
        else:
            UserFollow.objects.create(
                follower=request.user,
                following=target_user
            )
            action = 'followed'
        
        return JsonResponse({
            'success': True,
            'message': f'Utilisateur {action} avec succès',
            'action': action,
            'followers_count': target_user.followers.count()
        })
        
    except Exception as e:
        logger.error(f"Error following user: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors de l\'opération'
        })

# ============= NOTIFICATION SYSTEM =============

@login_required
def client_notifications(request):
    """Client notifications dashboard"""
    
    user = request.user
    
    # Get notifications
    notifications = SmartNotification.objects.filter(
        user=user
    ).order_by('-scheduled_for')
    
    # Mark as read
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        if notification_id:
            try:
                notification = SmartNotification.objects.get(
                    id=notification_id,
                    user=user
                )
                notification.status = 'READ'
                notification.read_at = timezone.now()
                notification.save()
            except SmartNotification.DoesNotExist:
                pass
    
    context = {
        'notifications': notifications,
    }
    
    return render(request, 'backend/client/notifications/notifications_dashboard.html', context)

@login_required
@require_POST
def client_mark_notification_read(request):
    """Mark notification as read"""
    
    try:
        notification_id = request.POST.get('notification_id')
        notification = SmartNotification.objects.get(
            id=notification_id,
            user=request.user
        )
        notification.status = 'READ'
        notification.read_at = timezone.now()
        notification.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Notification marquée comme lue'
        })
        
    except SmartNotification.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Notification non trouvée'
        })
    except Exception as e:
        logger.error(f"Error marking notification read: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors de l\'opération'
        }) 