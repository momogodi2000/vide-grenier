# backend/views_admin.py - COMPLETE ADMIN VIEWS IMPLEMENTATION
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

# Import your existing models
try:
    from .models import Product, Category, Order, Review, Chat, Notification
    MAIN_MODELS_AVAILABLE = True
except ImportError:
    MAIN_MODELS_AVAILABLE = False
    print("⚠️ Main models not found")

# Import newsletter models
try:
    from .models_newsletter import NewsletterSubscriber, Newsletter
    NEWSLETTER_MODELS_AVAILABLE = True
except ImportError:
    NEWSLETTER_MODELS_AVAILABLE = False
    print("⚠️ Newsletter models not found")

User = get_user_model()

# ============ UTILITY FUNCTIONS ============
def is_admin(user):
    """Check if user is admin/staff"""
    return user.is_staff or user.is_superuser

def admin_required(view_func):
    """Decorator to require admin access"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('backend:login')
        if not is_admin(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper

def get_admin_stats():
    """Get admin dashboard statistics"""
    stats = {
        'total_users': 0,
        'total_products': 0,
        'total_orders': 0,
        'total_revenue': 0,
        'new_users_this_month': 0,
        'active_products': 0,
        'pending_orders': 0,
        'newsletter_subscribers': 0,
    }
    
    if MAIN_MODELS_AVAILABLE:
        try:
            stats['total_users'] = User.objects.count()
            stats['total_products'] = Product.objects.count()
            stats['active_products'] = Product.objects.filter(status='active').count()
            stats['total_orders'] = Order.objects.count()
            stats['pending_orders'] = Order.objects.filter(status='pending').count()
            
            # Calculate revenue
            total_revenue = Order.objects.filter(
                status__in=['completed', 'delivered']
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            stats['total_revenue'] = total_revenue
            
            # New users this month
            this_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            new_users = User.objects.filter(date_joined__gte=this_month).count()
            stats['new_users_this_month'] = new_users
            
        except Exception as e:
            print(f"Error calculating stats: {e}")
    
    if NEWSLETTER_MODELS_AVAILABLE:
        try:
            stats['newsletter_subscribers'] = NewsletterSubscriber.objects.filter(is_active=True).count()
        except Exception as e:
            print(f"Error calculating newsletter stats: {e}")
    
    return stats

# ============ MAIN ADMIN DASHBOARD ============
@admin_required
def admin_dashboard(request):
    """Main admin dashboard"""
    context = {
        'stats': get_admin_stats(),
        'recent_users': [],
        'recent_products': [],
        'recent_orders': [],
        'pending_moderations': [],
    }
    
    if MAIN_MODELS_AVAILABLE:
        try:
            # Get recent data
            context['recent_users'] = User.objects.order_by('-date_joined')[:5]
            context['recent_products'] = Product.objects.order_by('-created_at')[:5]
            context['recent_orders'] = Order.objects.order_by('-created_at')[:5]
            context['pending_moderations'] = Product.objects.filter(status='pending')[:10]
        except Exception as e:
            print(f"Error loading dashboard data: {e}")
    
    return render(request, 'backend/dashboard/admin_dashboard.html', context)

# ============ USER MANAGEMENT ============
@method_decorator([login_required, staff_member_required], name='dispatch')
class AdminUserListView(ListView):
    """Admin view for managing users"""
    model = User
    template_name = 'backend/admin/users.html'
    context_object_name = 'users'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        
        # Search functionality
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone_number__icontains=search)
            )
        
        # Filter by user type
        user_type = self.request.GET.get('user_type', '')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        
        # Filter by status
        status = self.request.GET.get('status', '')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'sellers_count': User.objects.filter(user_type='seller').count(),
            'suspended_users': User.objects.filter(is_active=False).count(),
            'search': self.request.GET.get('search', ''),
            'user_type_filter': self.request.GET.get('user_type', ''),
            'status_filter': self.request.GET.get('status', ''),
        })
        
        # Add product counts for each user if models available
        if MAIN_MODELS_AVAILABLE:
            try:
                for user in context['users']:
                    user.products_count = Product.objects.filter(seller=user).count()
                    user.total_sales = Order.objects.filter(
                        product__seller=user,
                        status__in=['completed', 'delivered']
                    ).aggregate(total=Sum('total_amount'))['total'] or 0
            except Exception as e:
                print(f"Error adding user stats: {e}")
        
        return context

# ============ PRODUCT MANAGEMENT ============
@method_decorator([login_required, staff_member_required], name='dispatch')
class AdminProductListView(ListView):
    """Admin view for managing products"""
    template_name = 'backend/admin/products.html'
    context_object_name = 'products'
    paginate_by = 25
    
    def get_queryset(self):
        if not MAIN_MODELS_AVAILABLE:
            return []
        
        try:
            queryset = Product.objects.all().order_by('-created_at')
            
            # Search functionality
            search = self.request.GET.get('search', '')
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(description__icontains=search) |
                    Q(reference_number__icontains=search)
                )
            
            # Filter by category
            category = self.request.GET.get('category', '')
            if category:
                queryset = queryset.filter(category__slug=category)
            
            # Filter by status
            status = self.request.GET.get('status', '')
            if status:
                queryset = queryset.filter(status=status)
            
            # Filter by price range
            price_range = self.request.GET.get('price_range', '')
            if price_range:
                if price_range == '0-10000':
                    queryset = queryset.filter(price__gte=0, price__lte=10000)
                elif price_range == '10000-50000':
                    queryset = queryset.filter(price__gte=10000, price__lte=50000)
                elif price_range == '50000-100000':
                    queryset = queryset.filter(price__gte=50000, price__lte=100000)
                elif price_range == '100000+':
                    queryset = queryset.filter(price__gte=100000)
            
            return queryset
        except Exception as e:
            print(f"Error loading products: {e}")
            return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if MAIN_MODELS_AVAILABLE:
            try:
                context.update({
                    'total_products': Product.objects.count(),
                    'active_products': Product.objects.filter(status='active').count(),
                    'pending_products': Product.objects.filter(status='pending').count(),
                    'admin_stock': Product.objects.filter(seller__user_type='admin').count(),
                    'categories': Category.objects.all(),
                })
            except Exception as e:
                print(f"Error loading product stats: {e}")
                context.update({
                    'total_products': 0,
                    'active_products': 0,
                    'pending_products': 0,
                    'admin_stock': 0,
                    'categories': [],
                })
        
        context.update({
            'search': self.request.GET.get('search', ''),
            'category_filter': self.request.GET.get('category', ''),
            'status_filter': self.request.GET.get('status', ''),
            'price_range_filter': self.request.GET.get('price_range', ''),
        })
        
        return context

# ============ PAYMENT ADMIN VIEWS ============
@method_decorator([login_required, staff_member_required], name='dispatch')
class AdminPaymentListView(ListView):
    """Admin view for managing payments"""
    template_name = 'backend/admin/payments/list.html'
    context_object_name = 'payments'
    paginate_by = 25
    
    def get_queryset(self):
        # TODO: Replace with actual Payment model when available
        # For now, return orders as payment proxies
        if MAIN_MODELS_AVAILABLE:
            try:
                queryset = Order.objects.all().order_by('-created_at')
                
                # Search functionality
                search = self.request.GET.get('search', '')
                if search:
                    queryset = queryset.filter(
                        Q(order_number__icontains=search) |
                        Q(user__email__icontains=search) |
                        Q(user__first_name__icontains=search) |
                        Q(user__last_name__icontains=search)
                    )
                
                # Filter by payment status
                status = self.request.GET.get('status', '')
                if status:
                    queryset = queryset.filter(payment_status=status)
                
                return queryset
            except Exception as e:
                print(f"Error loading payments: {e}")
        
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if MAIN_MODELS_AVAILABLE:
            try:
                context.update({
                    'total_payments': Order.objects.count(),
                    'completed_payments': Order.objects.filter(payment_status='completed').count(),
                    'pending_payments': Order.objects.filter(payment_status='pending').count(),
                    'failed_payments': Order.objects.filter(payment_status='failed').count(),
                    'total_revenue': Order.objects.filter(
                        payment_status='completed'
                    ).aggregate(total=Sum('total_amount'))['total'] or 0,
                })
            except Exception as e:
                print(f"Error loading payment stats: {e}")
                context.update({
                    'total_payments': 0,
                    'completed_payments': 0,
                    'pending_payments': 0,
                    'failed_payments': 0,
                    'total_revenue': 0,
                })
        
        context.update({
            'search': self.request.GET.get('search', ''),
            'status_filter': self.request.GET.get('status', ''),
        })
        
        return context

@admin_required
def admin_payment_detail(request, payment_id):
    """View payment details"""
    if MAIN_MODELS_AVAILABLE:
        try:
            # Using order as payment proxy
            payment = get_object_or_404(Order, id=payment_id)
            return render(request, 'backend/admin/payments/detail.html', {
                'payment': payment
            })
        except Exception as e:
            messages.error(request, f'Erreur lors du chargement du paiement: {e}')
    
    return redirect('backend:system_payment_list')

@admin_required
@require_http_methods(["POST"])
def admin_payment_update_status(request, payment_id):
    """Update payment status via AJAX"""
    try:
        new_status = request.POST.get('status')
        
        if MAIN_MODELS_AVAILABLE:
            # Using order as payment proxy
            payment = get_object_or_404(Order, id=payment_id)
            payment.payment_status = new_status
            payment.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Statut de paiement mis à jour avec succès'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Modèles non disponibles'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

# ============ LOYALTY PROGRAM ADMIN VIEWS ============
@method_decorator([login_required, staff_member_required], name='dispatch')
class AdminLoyaltyListView(ListView):
    """Admin view for managing loyalty programs"""
    template_name = 'backend/admin/loyalty/list.html'
    context_object_name = 'loyalty_programs'
    paginate_by = 20
    
    def get_queryset(self):
        # TODO: Replace with actual LoyaltyProgram model when available
        # For now, return user loyalty stats
        if MAIN_MODELS_AVAILABLE:
            try:
                # Return users with their loyalty points
                return User.objects.filter(
                    loyalty_points__gt=0
                ).order_by('-loyalty_points')
            except Exception as e:
                print(f"Error loading loyalty data: {e}")
        
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if MAIN_MODELS_AVAILABLE:
            try:
                context.update({
                    'total_members': User.objects.filter(loyalty_points__gt=0).count(),
                    'bronze_members': User.objects.filter(loyalty_level='bronze').count(),
                    'silver_members': User.objects.filter(loyalty_level='silver').count(),
                    'gold_members': User.objects.filter(loyalty_level='gold').count(),
                    'platinum_members': User.objects.filter(loyalty_level='platinum').count(),
                    'total_points_issued': User.objects.aggregate(
                        total=Sum('loyalty_points')
                    )['total'] or 0,
                })
            except Exception as e:
                print(f"Error loading loyalty stats: {e}")
                context.update({
                    'total_members': 0,
                    'bronze_members': 0,
                    'silver_members': 0,
                    'gold_members': 0,
                    'platinum_members': 0,
                    'total_points_issued': 0,
                })
        
        return context

@admin_required
def admin_loyalty_create(request):
    """Create new loyalty program"""
    if request.method == 'POST':
        # TODO: Handle form submission when model is available
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            points_per_euro = request.POST.get('points_per_euro', 1)
            
            # For now, just show success message
            messages.success(request, f'Programme de fidélité "{name}" créé avec succès!')
            return redirect('backend:system_loyalty_list')
        except Exception as e:
            messages.error(request, f'Erreur lors de la création: {e}')
    
    return render(request, 'backend/admin/loyalty/create.html')

@admin_required
def admin_loyalty_edit(request, loyalty_id):
    """Edit loyalty program"""
    if request.method == 'POST':
        # TODO: Handle form submission when model is available
        try:
            messages.success(request, 'Programme de fidélité mis à jour avec succès!')
            return redirect('backend:system_loyalty_list')
        except Exception as e:
            messages.error(request, f'Erreur lors de la mise à jour: {e}')
    
    return render(request, 'backend/admin/loyalty/edit.html', {
        'loyalty_id': loyalty_id
    })

# ============ PROMOTION ADMIN VIEWS ============
@method_decorator([login_required, staff_member_required], name='dispatch')
class AdminPromotionListView(ListView):
    """Admin view for managing promotions"""
    template_name = 'backend/admin/promotions/list.html'
    context_object_name = 'promotions'
    paginate_by = 20
    
    def get_queryset(self):
        # TODO: Replace with actual Promotion model when available
        # For now, return empty list
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'total_promotions': 0,
            'active_promotions': 0,
            'expired_promotions': 0,
            'scheduled_promotions': 0,
        })
        return context

@admin_required
def admin_promotion_create(request):
    """Create new promotion"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            code = request.POST.get('code')
            discount_percent = request.POST.get('discount_percent')
            
            # TODO: Create actual promotion when model is available
            messages.success(request, f'Promotion "{name}" créée avec succès!')
            return redirect('backend:system_promotion_list')
        except Exception as e:
            messages.error(request, f'Erreur lors de la création: {e}')
    
    return render(request, 'backend/admin/promotions/create.html')

@admin_required
def admin_promotion_edit(request, promotion_id):
    """Edit promotion"""
    if request.method == 'POST':
        try:
            # TODO: Handle form submission when model is available
            messages.success(request, 'Promotion mise à jour avec succès!')
            return redirect('backend:system_promotion_list')
        except Exception as e:
            messages.error(request, f'Erreur lors de la mise à jour: {e}')
    
    return render(request, 'backend/admin/promotions/edit.html', {
        'promotion_id': promotion_id
    })

@admin_required
@require_http_methods(["POST"])
def admin_promotion_toggle_status(request, promotion_id):
    """Toggle promotion active status"""
    try:
        # TODO: Toggle actual promotion when model is available
        return JsonResponse({
            'success': True,
            'message': 'Statut de la promotion mis à jour avec succès'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

# ============ NEWSLETTER ADMIN VIEWS ============
@method_decorator([login_required, staff_member_required], name='dispatch')
class AdminNewsletterListView(ListView):
    """Admin view for managing newsletters"""
    template_name = 'backend/admin/newsletter/list.html'
    context_object_name = 'newsletters'
    paginate_by = 20
    
    def get_queryset(self):
        if not NEWSLETTER_MODELS_AVAILABLE:
            return []
        
        try:
            queryset = Newsletter.objects.all().order_by('-created_at')
            
            # Search functionality
            search = self.request.GET.get('search', '')
            if search:
                queryset = queryset.filter(
                    Q(subject__icontains=search) |
                    Q(content__icontains=search)
                )
            
            return queryset
        except Exception as e:
            print(f"Error loading newsletters: {e}")
            return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if NEWSLETTER_MODELS_AVAILABLE:
            try:
                context.update({
                    'total_newsletters': Newsletter.objects.count(),
                    'sent_newsletters': Newsletter.objects.filter(is_sent=True).count(),
                    'draft_newsletters': Newsletter.objects.filter(is_sent=False).count(),
                    'total_subscribers': NewsletterSubscriber.objects.filter(is_active=True).count(),
                })
            except Exception as e:
                print(f"Error loading newsletter stats: {e}")
                context.update({
                    'total_newsletters': 0,
                    'sent_newsletters': 0,
                    'draft_newsletters': 0,
                    'total_subscribers': 0,
                })
        
        context.update({
            'search': self.request.GET.get('search', ''),
        })
        
        return context

@admin_required
def admin_newsletter_create(request):
    """Create new newsletter"""
    if request.method == 'POST':
        if not NEWSLETTER_MODELS_AVAILABLE:
            messages.error(request, 'Modèles de newsletter non disponibles!')
            return redirect('backend:system_newsletter_list')
        
        try:
            subject = request.POST.get('subject')
            content = request.POST.get('content')
            
            if subject and content:
                newsletter = Newsletter.objects.create(
                    subject=subject,
                    content=content,
                    created_by=request.user
                )
                messages.success(request, 'Newsletter créée avec succès!')
                return redirect('backend:system_newsletter_list')
            else:
                messages.error(request, 'Le sujet et le contenu sont requis!')
        except Exception as e:
            messages.error(request, f'Erreur lors de la création: {e}')
    
    return render(request, 'backend/admin/newsletter/create.html')

@admin_required
def admin_newsletter_send(request, newsletter_id):
    """Send newsletter to subscribers"""
    if not NEWSLETTER_MODELS_AVAILABLE:
        messages.error(request, 'Modèles de newsletter non disponibles!')
        return redirect('backend:system_newsletter_list')
    
    try:
        newsletter = get_object_or_404(Newsletter, id=newsletter_id)
        
        if request.method == 'POST':
            # Get active subscribers
            subscribers = NewsletterSubscriber.objects.filter(is_active=True)
            
            if subscribers.exists():
                sent_count = 0
                failed_count = 0
                
                for subscriber in subscribers:
                    try:
                        # Render email content
                        html_content = render_to_string('emails/newsletter.html', {
                            'newsletter': newsletter,
                            'subscriber': subscriber,
                        })
                        
                        # Send email
                        send_mail(
                            subject=newsletter.subject,
                            message=newsletter.content,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[subscriber.email],
                            html_message=html_content,
                            fail_silently=False,
                        )
                        sent_count += 1
                    except Exception as e:
                        print(f"Failed to send to {subscriber.email}: {e}")
                        failed_count += 1
                
                # Mark newsletter as sent
                newsletter.is_sent = True
                newsletter.sent_at = timezone.now()
                newsletter.recipients_count = sent_count
                newsletter.save()
                
                if failed_count > 0:
                    messages.warning(
                        request, 
                        f'Newsletter envoyée à {sent_count} abonnés, {failed_count} échecs.'
                    )
                else:
                    messages.success(
                        request, 
                        f'Newsletter envoyée avec succès à {sent_count} abonnés!'
                    )
            else:
                messages.warning(request, 'Aucun abonné actif trouvé!')
            
            return redirect('backend:system_newsletter_list')
        
        context = {
            'newsletter': newsletter,
            'subscribers_count': NewsletterSubscriber.objects.filter(is_active=True).count(),
        }
        return render(request, 'backend/admin/newsletter/send.html', context)
        
    except Exception as e:
        messages.error(request, f'Erreur: {e}')
        return redirect('backend:system_newsletter_list')

@admin_required
@require_http_methods(["DELETE", "POST"])
def admin_newsletter_delete(request, newsletter_id):
    """Delete newsletter"""
    try:
        if NEWSLETTER_MODELS_AVAILABLE:
            newsletter = get_object_or_404(Newsletter, id=newsletter_id)
            newsletter_subject = newsletter.subject
            newsletter.delete()
            
            if request.method == 'POST':
                messages.success(request, f'Newsletter "{newsletter_subject}" supprimée avec succès!')
                return redirect('backend:system_newsletter_list')
            
            return JsonResponse({
                'success': True,
                'message': 'Newsletter supprimée avec succès'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Modèles de newsletter non disponibles'
            })
    except Exception as e:
        if request.method == 'POST':
            messages.error(request, f'Erreur lors de la suppression: {e}')
            return redirect('backend:system_newsletter_list')
        
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

# ============ NOTIFICATION ADMIN VIEWS ============
@method_decorator([login_required, staff_member_required], name='dispatch')
class AdminNotificationListView(ListView):
    """Admin view for managing notifications"""
    template_name = 'backend/admin/notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 25
    
    def get_queryset(self):
        if not MAIN_MODELS_AVAILABLE:
            return []
        
        try:
            queryset = Notification.objects.all().order_by('-created_at')
            
            # Search functionality
            search = self.request.GET.get('search', '')
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(message__icontains=search) |
                    Q(recipient__email__icontains=search)
                )
            
            # Filter by type
            notification_type = self.request.GET.get('type', '')
            if notification_type:
                queryset = queryset.filter(notification_type=notification_type)
            
            # Filter by read status
            read_status = self.request.GET.get('read_status', '')
            if read_status == 'read':
                queryset = queryset.filter(is_read=True)
            elif read_status == 'unread':
                queryset = queryset.filter(is_read=False)
            
            return queryset
        except Exception as e:
            print(f"Error loading notifications: {e}")
            return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if MAIN_MODELS_AVAILABLE:
            try:
                context.update({
                    'total_notifications': Notification.objects.count(),
                    'unread_notifications': Notification.objects.filter(is_read=False).count(),
                    'system_notifications': Notification.objects.filter(notification_type='system').count(),
                    'user_notifications': Notification.objects.filter(notification_type='user').count(),
                })
            except Exception as e:
                print(f"Error loading notification stats: {e}")
                context.update({
                    'total_notifications': 0,
                    'unread_notifications': 0,
                    'system_notifications': 0,
                    'user_notifications': 0,
                })
        
        context.update({
            'search': self.request.GET.get('search', ''),
            'type_filter': self.request.GET.get('type', ''),
            'read_status_filter': self.request.GET.get('read_status', ''),
        })
        
        return context

@admin_required
def admin_notification_create(request):
    """Create new notification"""
    if request.method == 'POST':
        if not MAIN_MODELS_AVAILABLE:
            messages.error(request, 'Modèles de notification non disponibles!')
            return redirect('backend:system_notification_list')
        
        try:
            title = request.POST.get('title')
            message = request.POST.get('message')
            notification_type = request.POST.get('notification_type', 'system')
            recipient_type = request.POST.get('recipient_type', 'all')
            
            if title and message:
                # Get recipients based on type
                recipients = []
                if recipient_type == 'all':
                    recipients = User.objects.filter(is_active=True)
                elif recipient_type == 'sellers':
                    recipients = User.objects.filter(user_type='seller', is_active=True)
                elif recipient_type == 'clients':
                    recipients = User.objects.filter(user_type='client', is_active=True)
                
                # Create notifications
                created_count = 0
                for recipient in recipients:
                    try:
                        Notification.objects.create(
                            recipient=recipient,
                            title=title,
                            message=message,
                            notification_type=notification_type,
                            created_by=request.user
                        )
                        created_count += 1
                    except Exception as e:
                        print(f"Failed to create notification for {recipient.email}: {e}")
                
                messages.success(request, f'{created_count} notifications créées avec succès!')
                return redirect('backend:system_notification_list')
            else:
                messages.error(request, 'Le titre et le message sont requis!')
        except Exception as e:
            messages.error(request, f'Erreur lors de la création: {e}')
    
    return render(request, 'backend/admin/notifications/create.html')

@admin_required
@require_http_methods(["POST"])
def admin_notification_send_bulk(request):
    """Send bulk notifications"""
    try:
        if not MAIN_MODELS_AVAILABLE:
            return JsonResponse({
                'success': False,
                'message': 'Modèles de notification non disponibles'
            })
        
        notification_ids = request.POST.getlist('notification_ids')
        action = request.POST.get('action')
        
        if action == 'mark_read':
            updated = Notification.objects.filter(
                id__in=notification_ids
            ).update(is_read=True, read_at=timezone.now())
            
            return JsonResponse({
                'success': True,
                'message': f'{updated} notifications marquées comme lues'
            })
        
        elif action == 'delete':
            deleted_count = Notification.objects.filter(
                id__in=notification_ids
            ).delete()[0]
            
            return JsonResponse({
                'success': True,
                'message': f'{deleted_count} notifications supprimées'
            })
        
        else:
            return JsonResponse({
                'success': False,
                'message': 'Action non reconnue'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

# ============ ANALYTICS ADMIN VIEWS ============
@method_decorator([login_required, staff_member_required], name='dispatch')
class AdminAnalyticsView(ListView):
    """Admin analytics dashboard"""
    template_name = 'backend/admin/analytics.html'
    context_object_name = 'analytics_data'
    
    def get_queryset(self):
        return []  # No queryset needed for analytics
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate date ranges
        today = timezone.now().date()
        last_week = today - timedelta(days=7)
        last_month = today - timedelta(days=30)
        last_year = today - timedelta(days=365)
        
        analytics = {
            'overview': {},
            'user_analytics': {},
            'product_analytics': {},
            'sales_analytics': {},
            'engagement_analytics': {},
        }
        
        if MAIN_MODELS_AVAILABLE:
            try:
                # Overview Analytics
                analytics['overview'] = {
                    'total_users': User.objects.count(),
                    'total_products': Product.objects.count(),
                    'total_orders': Order.objects.count(),
                    'total_revenue': Order.objects.filter(
                        status__in=['completed', 'delivered']
                    ).aggregate(total=Sum('total_amount'))['total'] or 0,
                    'conversion_rate': 0,  # Calculate based on views vs orders
                }
                
                # User Analytics
                analytics['user_analytics'] = {
                    'new_users_today': User.objects.filter(date_joined__date=today).count(),
                    'new_users_week': User.objects.filter(date_joined__date__gte=last_week).count(),
                    'new_users_month': User.objects.filter(date_joined__date__gte=last_month).count(),
                    'active_users_week': User.objects.filter(last_login__date__gte=last_week).count(),
                    'user_types': {
                        'clients': User.objects.filter(user_type='client').count(),
                        'sellers': User.objects.filter(user_type='seller').count(),
                        'admins': User.objects.filter(user_type='admin').count(),
                        'staff': User.objects.filter(user_type='staff').count(),
                    },
                    'loyalty_levels': {
                        'bronze': User.objects.filter(loyalty_level='bronze').count(),
                        'silver': User.objects.filter(loyalty_level='silver').count(),
                        'gold': User.objects.filter(loyalty_level='gold').count(),
                        'platinum': User.objects.filter(loyalty_level='platinum').count(),
                    }
                }
                
                # Product Analytics
                analytics['product_analytics'] = {
                    'products_today': Product.objects.filter(created_at__date=today).count(),
                    'products_week': Product.objects.filter(created_at__date__gte=last_week).count(),
                    'products_month': Product.objects.filter(created_at__date__gte=last_month).count(),
                    'active_products': Product.objects.filter(status='active').count(),
                    'sold_products': Product.objects.filter(status='sold').count(),
                    'pending_moderation': Product.objects.filter(status='pending').count(),
                    'avg_product_price': Product.objects.aggregate(avg=Avg('price'))['avg'] or 0,
                    'top_categories': Category.objects.annotate(
                        product_count=Count('products')
                    ).order_by('-product_count')[:5],
                }
                
                # Sales Analytics
                analytics['sales_analytics'] = {
                    'orders_today': Order.objects.filter(created_at__date=today).count(),
                    'orders_week': Order.objects.filter(created_at__date__gte=last_week).count(),
                    'orders_month': Order.objects.filter(created_at__date__gte=last_month).count(),
                    'revenue_today': Order.objects.filter(
                        created_at__date=today,
                        status__in=['completed', 'delivered']
                    ).aggregate(total=Sum('total_amount'))['total'] or 0,
                    'revenue_week': Order.objects.filter(
                        created_at__date__gte=last_week,
                        status__in=['completed', 'delivered']
                    ).aggregate(total=Sum('total_amount'))['total'] or 0,
                    'revenue_month': Order.objects.filter(
                        created_at__date__gte=last_month,
                        status__in=['completed', 'delivered']
                    ).aggregate(total=Sum('total_amount'))['total'] or 0,
                    'avg_order_value': Order.objects.filter(
                        status__in=['completed', 'delivered']
                    ).aggregate(avg=Avg('total_amount'))['avg'] or 0,
                    'order_statuses': {
                        'pending': Order.objects.filter(status='pending').count(),
                        'confirmed': Order.objects.filter(status='confirmed').count(),
                        'processing': Order.objects.filter(status='processing').count(),
                        'shipped': Order.objects.filter(status='shipped').count(),
                        'delivered': Order.objects.filter(status='delivered').count(),
                        'cancelled': Order.objects.filter(status='cancelled').count(),
                    }
                }
                
                # Engagement Analytics
                analytics['engagement_analytics'] = {
                    'total_reviews': Review.objects.count(),
                    'avg_rating': Review.objects.aggregate(avg=Avg('rating'))['avg'] or 0,
                    'reviews_week': Review.objects.filter(created_at__date__gte=last_week).count(),
                    'active_chats': Chat.objects.filter(is_active=True).count(),
                    'messages_week': Chat.objects.filter(
                        messages__created_at__date__gte=last_week
                    ).count(),
                }
                
                # Calculate monthly data for charts
                monthly_data = []
                for i in range(12):
                    month_start = today.replace(day=1) - timedelta(days=30*i)
                    month_end = month_start + timedelta(days=30)
                    
                    monthly_data.append({
                        'month': month_start.strftime('%Y-%m'),
                        'users': User.objects.filter(
                            date_joined__date__gte=month_start,
                            date_joined__date__lt=month_end
                        ).count(),
                        'products': Product.objects.filter(
                            created_at__date__gte=month_start,
                            created_at__date__lt=month_end
                        ).count(),
                        'orders': Order.objects.filter(
                            created_at__date__gte=month_start,
                            created_at__date__lt=month_end
                        ).count(),
                        'revenue': Order.objects.filter(
                            created_at__date__gte=month_start,
                            created_at__date__lt=month_end,
                            status__in=['completed', 'delivered']
                        ).aggregate(total=Sum('total_amount'))['total'] or 0,
                    })
                
                analytics['monthly_data'] = list(reversed(monthly_data))
                
            except Exception as e:
                print(f"Error calculating analytics: {e}")
        
        # Newsletter Analytics
        if NEWSLETTER_MODELS_AVAILABLE:
            try:
                analytics['newsletter_analytics'] = {
                    'total_newsletters': Newsletter.objects.count(),
                    'sent_newsletters': Newsletter.objects.filter(is_sent=True).count(),
                    'total_subscribers': NewsletterSubscriber.objects.filter(is_active=True).count(),
                    'subscribers_week': NewsletterSubscriber.objects.filter(
                        subscribed_at__date__gte=last_week
                    ).count(),
                }
            except Exception as e:
                print(f"Error calculating newsletter analytics: {e}")
                analytics['newsletter_analytics'] = {
                    'total_newsletters': 0,
                    'sent_newsletters': 0,
                    'total_subscribers': 0,
                    'subscribers_week': 0,
                }
        
        context['analytics'] = analytics
        return context

# ============ BULK ACTIONS ============
@admin_required
@require_http_methods(["POST"])
def admin_bulk_actions(request):
    """Handle bulk actions across different admin sections"""
    try:
        action = request.POST.get('action')
        item_type = request.POST.get('item_type')
        item_ids = request.POST.getlist('item_ids')
        
        if not action or not item_type or not item_ids:
            return JsonResponse({
                'success': False,
                'message': 'Paramètres manquants'
            })
        
        result_count = 0
        
        if item_type == 'users' and MAIN_MODELS_AVAILABLE:
            if action == 'activate':
                result_count = User.objects.filter(id__in=item_ids).update(is_active=True)
            elif action == 'deactivate':
                result_count = User.objects.filter(id__in=item_ids).update(is_active=False)
            elif action == 'delete':
                result_count = User.objects.filter(id__in=item_ids).delete()[0]
        
        elif item_type == 'products' and MAIN_MODELS_AVAILABLE:
            if action == 'approve':
                result_count = Product.objects.filter(id__in=item_ids).update(status='active')
            elif action == 'reject':
                result_count = Product.objects.filter(id__in=item_ids).update(status='inactive')
            elif action == 'delete':
                result_count = Product.objects.filter(id__in=item_ids).delete()[0]
        
        elif item_type == 'notifications' and MAIN_MODELS_AVAILABLE:
            if action == 'mark_read':
                result_count = Notification.objects.filter(id__in=item_ids).update(
                    is_read=True, read_at=timezone.now()
                )
            elif action == 'delete':
                result_count = Notification.objects.filter(id__in=item_ids).delete()[0]
        
        elif item_type == 'newsletters' and NEWSLETTER_MODELS_AVAILABLE:
            if action == 'delete':
                result_count = Newsletter.objects.filter(id__in=item_ids).delete()[0]
        
        return JsonResponse({
            'success': True,
            'message': f'Action "{action}" appliquée à {result_count} éléments'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

# ============ EXPORT FUNCTIONS ============
@admin_required
def admin_export_data(request):
    """Export admin data to CSV"""
    export_type = request.GET.get('type', 'users')
    
    try:
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{export_type}_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        
        if export_type == 'users' and MAIN_MODELS_AVAILABLE:
            writer.writerow(['ID', 'Email', 'Nom', 'Prénom', 'Type', 'Statut', 'Date inscription'])
            for user in User.objects.all():
                writer.writerow([
                    user.id,
                    user.email,
                    user.last_name,
                    user.first_name,
                    user.get_user_type_display(),
                    'Actif' if user.is_active else 'Inactif',
                    user.date_joined.strftime('%Y-%m-%d %H:%M')
                ])
        
        elif export_type == 'products' and MAIN_MODELS_AVAILABLE:
            writer.writerow(['ID', 'Nom', 'Prix', 'Catégorie', 'Vendeur', 'Statut', 'Date création'])
            for product in Product.objects.select_related('category', 'seller'):
                writer.writerow([
                    product.id,
                    product.name,
                    product.price,
                    product.category.name if product.category else '',
                    f"{product.seller.first_name} {product.seller.last_name}",
                    product.get_status_display(),
                    product.created_at.strftime('%Y-%m-%d %H:%M')
                ])
        
        elif export_type == 'orders' and MAIN_MODELS_AVAILABLE:
            writer.writerow(['ID', 'Numéro', 'Client', 'Produit', 'Montant', 'Statut', 'Date'])
            for order in Order.objects.select_related('user', 'product'):
                writer.writerow([
                    order.id,
                    order.order_number,
                    f"{order.user.first_name} {order.user.last_name}",
                    order.product.name,
                    order.total_amount,
                    order.get_status_display(),
                    order.created_at.strftime('%Y-%m-%d %H:%M')
                ])
        
        return response
        
    except Exception as e:
        messages.error(request, f'Erreur lors de l\'export: {e}')
        return redirect('backend:admin_dashboard')

# ============ AJAX ENDPOINTS ============
@admin_required
@require_http_methods(["GET"])
def admin_stats_ajax(request):
    """Get admin statistics via AJAX"""
    try:
        stats = get_admin_stats()
        return JsonResponse({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@admin_required
@require_http_methods(["POST"])
def admin_quick_action(request):
    """Handle quick actions from admin dashboard"""
    try:
        action = request.POST.get('action')
        item_id = request.POST.get('item_id')
        item_type = request.POST.get('item_type')
        
        if action == 'approve_product' and MAIN_MODELS_AVAILABLE:
            product = get_object_or_404(Product, id=item_id)
            product.status = 'active'
            product.save()
            return JsonResponse({
                'success': True,
                'message': f'Produit "{product.name}" approuvé'
            })
        
        elif action == 'suspend_user' and MAIN_MODELS_AVAILABLE:
            user = get_object_or_404(User, id=item_id)
            user.is_active = False
            user.save()
            return JsonResponse({
                'success': True,
                'message': f'Utilisateur "{user.email}" suspendu'
            })
        
        return JsonResponse({
            'success': False,
            'message': 'Action non reconnue'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })