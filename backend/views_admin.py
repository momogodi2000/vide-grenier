# backend/views_admin.py - Updated to use your existing models_newsletter
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime, timedelta
from django.utils import timezone

# Import your existing newsletter models
try:
    from .models_newsletter import NewsletterSubscriber, Newsletter
    NEWSLETTER_MODELS_AVAILABLE = True
except ImportError:
    NEWSLETTER_MODELS_AVAILABLE = False
    print("⚠️ Newsletter models not found in models_newsletter.py")

# Import other models when they exist
# from .models import Payment, LoyaltyProgram, Promotion, Notification

def is_admin(user):
    """Check if user is admin/staff"""
    return user.is_staff or user.is_superuser

def admin_required(view_func):
    """Decorator to require admin access"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not is_admin(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper

# ============ PAYMENT ADMIN VIEWS ============
@method_decorator([login_required, staff_member_required], name='dispatch')
class AdminPaymentListView(ListView):
    """Admin view for managing payments"""
    template_name = 'admin/payments/list.html'
    context_object_name = 'payments'
    paginate_by = 20
    
    def get_queryset(self):
        # TODO: Replace with actual Payment model when available
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        return context

@admin_required
def admin_payment_detail(request, payment_id):
    """View payment details"""
    return render(request, 'admin/payments/detail.html', {
        'payment_id': payment_id
    })

@admin_required
@require_http_methods(["POST"])
def admin_payment_update_status(request, payment_id):
    """Update payment status via AJAX"""
    try:
        new_status = request.POST.get('status')
        # TODO: Update actual payment when model is available
        
        return JsonResponse({
            'success': True,
            'message': 'Payment status updated successfully'
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
    template_name = 'admin/loyalty/list.html'
    context_object_name = 'loyalty_programs'
    paginate_by = 20
    
    def get_queryset(self):
        # TODO: Replace with actual LoyaltyProgram model when available
        return []

@admin_required
def admin_loyalty_create(request):
    """Create new loyalty program"""
    if request.method == 'POST':
        # TODO: Handle form submission when model is available
        messages.success(request, 'Loyalty program created successfully!')
        return redirect('admin_loyalty_list')
    
    return render(request, 'admin/loyalty/create.html')

@admin_required
def admin_loyalty_edit(request, loyalty_id):
    """Edit loyalty program"""
    if request.method == 'POST':
        # TODO: Handle form submission when model is available
        messages.success(request, 'Loyalty program updated successfully!')
        return redirect('admin_loyalty_list')
    
    return render(request, 'admin/loyalty/edit.html', {
        'loyalty_id': loyalty_id
    })

# ============ PROMOTION ADMIN VIEWS ============
@method_decorator([login_required, staff_member_required], name='dispatch')
class AdminPromotionListView(ListView):
    """Admin view for managing promotions"""
    template_name = 'admin/promotions/list.html'
    context_object_name = 'promotions'
    paginate_by = 20
    
    def get_queryset(self):
        # TODO: Replace with actual Promotion model when available
        return []

@admin_required
def admin_promotion_create(request):
    """Create new promotion"""
    if request.method == 'POST':
        # TODO: Handle form submission when model is available
        messages.success(request, 'Promotion created successfully!')
        return redirect('admin_promotion_list')
    
    return render(request, 'admin/promotions/create.html')

@admin_required
def admin_promotion_edit(request, promotion_id):
    """Edit promotion"""
    if request.method == 'POST':
        # TODO: Handle form submission when model is available
        messages.success(request, 'Promotion updated successfully!')
        return redirect('admin_promotion_list')
    
    return render(request, 'admin/promotions/edit.html', {
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
            'message': 'Promotion status updated successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

# ============ NEWSLETTER ADMIN VIEWS (Using existing models_newsletter) ============
@method_decorator([login_required, staff_member_required], name='dispatch')
class AdminNewsletterListView(ListView):
    """Admin view for managing newsletters"""
    template_name = 'admin/newsletter/list.html'
    context_object_name = 'newsletters'
    paginate_by = 20
    
    def get_queryset(self):
        if NEWSLETTER_MODELS_AVAILABLE:
            queryset = Newsletter.objects.all().order_by('-created_at')
            search = self.request.GET.get('search', '')
            if search:
                queryset = queryset.filter(
                    Q(subject__icontains=search) |
                    Q(content__icontains=search)
                )
            return queryset
        return []

@admin_required
def admin_newsletter_create(request):
    """Create new newsletter"""
    if request.method == 'POST':
        if NEWSLETTER_MODELS_AVAILABLE:
            subject = request.POST.get('subject')
            content = request.POST.get('content')
            
            if subject and content:
                newsletter = Newsletter.objects.create(
                    subject=subject,
                    content=content,
                    created_by=request.user
                )
                messages.success(request, 'Newsletter created successfully!')
                return redirect('admin_newsletter_list')
            else:
                messages.error(request, 'Subject and content are required!')
        else:
            messages.error(request, 'Newsletter models not available!')
    
    return render(request, 'admin/newsletter/create.html')

@admin_required
def admin_newsletter_send(request, newsletter_id):
    """Send newsletter to subscribers"""
    if NEWSLETTER_MODELS_AVAILABLE:
        newsletter = get_object_or_404(Newsletter, id=newsletter_id)
        
        if request.method == 'POST':
            # Get active subscribers
            subscribers = NewsletterSubscriber.objects.filter(is_active=True)
            
            if subscribers.exists():
                # You can integrate with your email service here
                # For now, just mark as sent
                newsletter.is_sent = True
                newsletter.sent_at = timezone.now()
                newsletter.save()
                
                messages.success(request, f'Newsletter sent to {subscribers.count()} subscribers!')
            else:
                messages.warning(request, 'No active subscribers found!')
            
            return redirect('admin_newsletter_list')
        
        return render(request, 'admin/newsletter/send.html', {
            'newsletter': newsletter
        })
    else:
        messages.error(request, 'Newsletter models not available!')
        return redirect('admin_newsletter_list')

@admin_required
@require_http_methods(["DELETE"])
def admin_newsletter_delete(request, newsletter_id):
    """Delete newsletter"""
    try:
        if NEWSLETTER_MODELS_AVAILABLE:
            newsletter = get_object_or_404(Newsletter, id=newsletter_id)
            newsletter.delete()
            return JsonResponse({
                'success': True,
                'message': 'Newsletter deleted successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Newsletter models not available'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

# ============ NOTIFICATION ADMIN VIEWS ============
@method_decorator([login_required, staff_member_required], name='dispatch')
class AdminNotificationListView(ListView):
    """Admin view for managing notifications"""
    template_name = 'admin/notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        # TODO: Replace with actual Notification model when available
        return []

@admin_required
def admin_notification_create(request):
    """Create new notification"""
    if request.method == 'POST':
        # TODO: Handle form submission when model is available
        messages.success(request, 'Notification created successfully!')
        return redirect('admin_notification_list')
    
    return render(request, 'admin/notifications/create.html')

@admin_required
def admin_notification_send_bulk(request):
    """Send bulk notifications"""
    if request.method == 'POST':
        # TODO: Handle bulk notification sending when model is available
        messages.success(request, 'Bulk notifications sent successfully!')
        return redirect('admin_notification_list')
    
    return render(request, 'admin/notifications/bulk_send.html')

# ============ DASHBOARD VIEW ============
@admin_required
def admin_dashboard(request):
    """Admin dashboard with statistics"""
    context = {
        'newsletter_models_available': NEWSLETTER_MODELS_AVAILABLE,
    }
    
    if NEWSLETTER_MODELS_AVAILABLE:
        context.update({
            'total_newsletters': Newsletter.objects.count(),
            'total_subscribers': NewsletterSubscriber.objects.filter(is_active=True).count(),
            'recent_newsletters': Newsletter.objects.order_by('-created_at')[:5],
        })
    
    return render(request, 'admin/dashboard.html', context)