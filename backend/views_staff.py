# backend/views_staff.py - STAFF-SPECIFIC VIEWS FOR VIDÉ-GRENIER KAMER
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from decimal import Decimal
import json
from datetime import datetime, timedelta

from .models import User, Product, Order, Chat, Message, Category
from .models_advanced import Wallet, Transaction, ShoppingCart


class StaffRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure only staff can access views"""
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type != 'STAFF':
            messages.error(request, "Accès non autorisé pour ce type d'utilisateur.")
            return redirect('backend:home')
        return super().dispatch(request, *args, **kwargs)


class StaffDashboardView(StaffRequiredMixin, TemplateView):
    """Enhanced Staff Dashboard with comprehensive metrics"""
    template_name = 'backend/staff/dashboard/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get today's date range
        today = timezone.now().date()
        start_of_day = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        end_of_day = timezone.make_aware(datetime.combine(today, datetime.max.time()))
        
        # Order processing stats
        todays_orders = Order.objects.filter(created_at__range=[start_of_day, end_of_day])
        pending_orders = Order.objects.filter(status__in=['PENDING', 'PAID'])
        
        # Financial metrics
        todays_revenue = todays_orders.filter(status='DELIVERED').aggregate(
            total=Sum('total_amount'))['total'] or Decimal('0')
        monthly_revenue = Order.objects.filter(
            created_at__month=today.month,
            status='DELIVERED'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        # Inventory alerts
        low_stock_products = Product.objects.filter(stock_quantity__lt=5)
        
        # Customer service metrics
        active_chats = Chat.objects.filter(is_active=True).count()
        unresolved_issues = Order.objects.filter(status='ISSUE').count()
        
        context.update({
            # Order Processing
            'todays_orders_count': todays_orders.count(),
            'pending_orders_count': pending_orders.count(),
            'completed_orders_today': todays_orders.filter(status='DELIVERED').count(),
            'cancelled_orders_today': todays_orders.filter(status='CANCELLED').count(),
            
            # Financial
            'todays_revenue': todays_revenue,
            'monthly_revenue': monthly_revenue,
            'avg_order_value': todays_orders.aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0'),
            
            # Inventory
            'low_stock_count': low_stock_products.count(),
            'total_products': Product.objects.count(),
            'active_products': Product.objects.filter(status='ACTIVE').count(),
            
            # Customer Service
            'active_chats': active_chats,
            'unresolved_issues': unresolved_issues,
            'satisfaction_rate': 95,  # To be calculated from feedback
            
            # Performance
            'orders_processed_today': todays_orders.filter(status__in=['DELIVERED', 'SHIPPED']).count(),
            'efficiency_score': self._calculate_efficiency_score(user),
            'monthly_performance': self._get_monthly_performance(user),
        })
        
        return context
    
    def _calculate_efficiency_score(self, user):
        """Calculate staff efficiency score"""
        # Placeholder calculation - can be enhanced with real metrics
        today = timezone.now().date()
        orders_processed = Order.objects.filter(
            updated_at__date=today,
            status__in=['DELIVERED', 'SHIPPED']
        ).count()
        target_orders = 20  # Daily target
        
        if target_orders > 0:
            efficiency = min((orders_processed / target_orders) * 100, 100)
        else:
            efficiency = 0
        
        return round(efficiency, 1)
    
    def _get_monthly_performance(self, user):
        """Get monthly performance metrics"""
        current_month = timezone.now().month
        monthly_orders = Order.objects.filter(
            created_at__month=current_month,
            status__in=['DELIVERED', 'SHIPPED']
        ).count()
        
        return {
            'orders_processed': monthly_orders,
            'revenue_generated': Order.objects.filter(
                created_at__month=current_month,
                status='DELIVERED'
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0'),
            'customer_interactions': Chat.objects.filter(
                created_at__month=current_month
            ).count(),
        }


# ============= ORDER PROCESSING VIEWS =============

class OrderProcessingView(StaffRequiredMixin, ListView):
    """Comprehensive order processing interface"""
    model = Order
    template_name = 'backend/staff/orders/processing.html'
    context_object_name = 'orders'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = Order.objects.select_related('buyer', 'product', 'product__seller')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        # Search by order ID or customer
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(id__icontains=search) |
                Q(buyer__first_name__icontains=search) |
                Q(buyer__last_name__icontains=search) |
                Q(buyer__email__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'order_statuses': Order.STATUS_CHOICES,
            'current_status': self.request.GET.get('status', ''),
            'search_query': self.request.GET.get('search', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
        })
        return context


class OrderDetailView(StaffRequiredMixin, DetailView):
    """Detailed order view for staff processing"""
    model = Order
    template_name = 'backend/staff/orders/detail.html'
    context_object_name = 'order'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        
        # Order timeline
        context['order_timeline'] = self._get_order_timeline(order)
        
        # Payment information
        if hasattr(order, 'payment'):
            context['payment_info'] = order.payment
        
        # Customer information
        context['customer_orders_count'] = Order.objects.filter(buyer=order.buyer).count()
        context['customer_total_spent'] = Order.objects.filter(
            buyer=order.buyer, status='DELIVERED'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        return context
    
    def _get_order_timeline(self, order):
        """Get order processing timeline"""
        timeline = [
            {
                'status': 'PENDING',
                'label': 'Commande créée',
                'timestamp': order.created_at,
                'completed': True
            }
        ]
        
        # Add more timeline events based on order status
        if order.status in ['PAID', 'SHIPPED', 'DELIVERED']:
            timeline.append({
                'status': 'PAID',
                'label': 'Paiement confirmé',
                'timestamp': order.updated_at,  # Should be actual payment timestamp
                'completed': True
            })
        
        if order.status in ['SHIPPED', 'DELIVERED']:
            timeline.append({
                'status': 'SHIPPED',
                'label': 'Expédié',
                'timestamp': order.updated_at,
                'completed': True
            })
        
        if order.status == 'DELIVERED':
            timeline.append({
                'status': 'DELIVERED',
                'label': 'Livré',
                'timestamp': order.updated_at,
                'completed': True
            })
        
        return timeline


class POSSystemView(StaffRequiredMixin, TemplateView):
    """Point of Sale system for in-person transactions"""
    template_name = 'backend/staff/pos/system.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Recent products for quick access
        context['featured_products'] = Product.objects.filter(
            status='ACTIVE'
        ).order_by('-created_at')[:20]
        
        # Categories for navigation
        context['categories'] = Category.objects.all()
        
        # Today's POS sales
        today = timezone.now().date()
        context['todays_pos_sales'] = Order.objects.filter(
            created_at__date=today,
            payment_method='CASH'  # Assuming CASH indicates POS sale
        ).count()
        
        return context


# ============= INVENTORY MANAGEMENT VIEWS =============

class InventoryDashboardView(StaffRequiredMixin, TemplateView):
    """Comprehensive inventory management dashboard"""
    template_name = 'backend/staff/inventory/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Inventory statistics
        total_products = Product.objects.count()
        active_products = Product.objects.filter(status='ACTIVE').count()
        low_stock_products = Product.objects.filter(stock_quantity__lt=5)
        out_of_stock_products = Product.objects.filter(stock_quantity=0)
        
        # Value calculations
        total_inventory_value = Product.objects.aggregate(
            total=Sum('price'))['total'] or Decimal('0')
        
        # Recent activity
        recent_stock_changes = Product.objects.filter(
            updated_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-updated_at')[:10]
        
        context.update({
            'total_products': total_products,
            'active_products': active_products,
            'low_stock_count': low_stock_products.count(),
            'out_of_stock_count': out_of_stock_products.count(),
            'total_inventory_value': total_inventory_value,
            'low_stock_products': low_stock_products[:10],
            'recent_stock_changes': recent_stock_changes,
            'stock_alerts': self._get_stock_alerts(),
        })
        
        return context
    
    def _get_stock_alerts(self):
        """Get inventory alerts"""
        alerts = []
        
        # Low stock alerts
        low_stock = Product.objects.filter(stock_quantity__lt=5, stock_quantity__gt=0)
        for product in low_stock:
            alerts.append({
                'type': 'warning',
                'message': f'Stock faible pour {product.title} ({product.stock_quantity} restant)',
                'product': product
            })
        
        # Out of stock alerts
        out_of_stock = Product.objects.filter(stock_quantity=0)
        for product in out_of_stock:
            alerts.append({
                'type': 'danger',
                'message': f'Rupture de stock pour {product.title}',
                'product': product
            })
        
        return alerts[:10]  # Limit to 10 alerts


class InventoryListView(StaffRequiredMixin, ListView):
    """Enhanced inventory list with search and filters"""
    model = Product
    template_name = 'backend/staff/inventory/list.html'
    context_object_name = 'products'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Product.objects.select_related('seller', 'category')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(seller__first_name__icontains=search) |
                Q(seller__last_name__icontains=search)
            )
        
        # Category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Stock level filter
        stock_filter = self.request.GET.get('stock')
        if stock_filter == 'low':
            queryset = queryset.filter(stock_quantity__lt=5, stock_quantity__gt=0)
        elif stock_filter == 'out':
            queryset = queryset.filter(stock_quantity=0)
        elif stock_filter == 'available':
            queryset = queryset.filter(stock_quantity__gt=0)
        
        # Sorting
        sort_by = self.request.GET.get('sort', '-created_at')
        queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'categories': Category.objects.all(),
            'search_query': self.request.GET.get('search', ''),
            'selected_category': self.request.GET.get('category', ''),
            'selected_status': self.request.GET.get('status', ''),
            'selected_stock': self.request.GET.get('stock', ''),
            'sort_by': self.request.GET.get('sort', '-created_at'),
        })
        return context


class QRScannerView(StaffRequiredMixin, TemplateView):
    """QR Code scanner for staff"""
    template_name = 'backend/staff/tools/qr_scanner.html'


class PickupManagementView(StaffRequiredMixin, ListView):
    """Pickup management for staff"""
    model = Order
    template_name = 'backend/staff/pickup/management.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        # Filter orders for pickup
        return Order.objects.filter(
            delivery_method='PICKUP',
            status__in=['PAID', 'SHIPPED']
        ).select_related('product', 'buyer').order_by('-created_at')


class CustomerServiceView(StaffRequiredMixin, TemplateView):
    """Customer service interface for staff"""
    template_name = 'backend/staff/customer/service.html'


class PerformanceAnalyticsView(StaffRequiredMixin, TemplateView):
    """Performance analytics for staff"""
    template_name = 'backend/staff/analytics/performance.html'


class StockReceivingView(StaffRequiredMixin, TemplateView):
    """Stock receiving interface"""
    template_name = 'backend/staff/inventory/receiving.html'
    
    def post(self, request, *args, **kwargs):
        """Process stock receiving"""
        product_id = request.POST.get('product_id')
        quantity_received = int(request.POST.get('quantity', 0))
        
        try:
            product = Product.objects.get(id=product_id)
            product.stock_quantity += quantity_received
            product.save()
            
            # Log the stock movement (implement stock movement model if needed)
            
            messages.success(request, f'Stock mis à jour: +{quantity_received} pour {product.title}')
            return JsonResponse({'success': True, 'new_stock': product.stock_quantity})
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Produit introuvable'})


class StaffTaskListView(StaffRequiredMixin, ListView):
    """Staff task management"""
    template_name = 'backend/staff/tasks/list.html'
    context_object_name = 'tasks'
    
    def get_queryset(self):
        # Placeholder - return empty queryset for now
        return []


class InventoryMovementListView(StaffRequiredMixin, TemplateView):
    """Inventory movement tracking"""
    template_name = 'backend/staff/inventory/movements.html'


class StaffPerformanceView(StaffRequiredMixin, TemplateView):
    """Staff performance analytics"""
    template_name = 'backend/staff/analytics/dashboard.html'


class StaffProfileView(StaffRequiredMixin, TemplateView):
    """Staff profile view"""
    template_name = 'backend/staff/profile/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get staff-specific data
        context.update({
            'performance': {
                'average_rating': 4.5,  # This would come from actual data
                'tasks_completed': 150,
                'orders_processed': 89,
            },
            'daily_stats': {
                'orders_today': 12,
                'tasks_today': 8,
                'clients_served': 15,
                'average_time': 5,
            },
            'work_schedule': {
                'today': '08:00 - 17:00',
                'hours_this_week': 40,
            },
            'pending_tasks': 3,
        })
        return context

class StaffProfileEditView(StaffRequiredMixin, UpdateView):
    """Staff profile edit view"""
    model = User
    template_name = 'backend/staff/profile/edit.html'
    fields = ['first_name', 'last_name', 'email', 'phone', 'city']
    success_url = reverse_lazy('staff:profile')
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# ============= AJAX FUNCTIONS =============

@login_required
def process_pickup(request):
    """Process a pickup request"""
    if request.user.user_type != 'STAFF':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    if request.method == 'POST':
        data = json.loads(request.body)
        order_id = data.get('order_id')
        action = data.get('action', 'process')
        
        try:
            order = Order.objects.get(id=order_id)
            
            if action == 'process':
                order.status = 'SHIPPED'
            elif action == 'deliver':
                order.status = 'DELIVERED'
            elif action == 'confirm':
                order.status = 'PAID'
                
            order.save()
            return JsonResponse({'success': True, 'message': 'Commande traitée avec succès'})
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Commande introuvable'})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@login_required
def scan_qr_code(request):
    """Process QR code scan"""
    if request.user.user_type != 'STAFF':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    # Placeholder for QR processing
    return JsonResponse({'success': True, 'message': 'Code QR scanné'})


@login_required
def update_inventory(request):
    """Update inventory levels"""
    if request.user.user_type != 'STAFF':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    # Placeholder for inventory update
    return JsonResponse({'success': True, 'message': 'Inventaire mis à jour'})


@login_required
def customer_assistance(request):
    """Provide customer assistance"""
    if request.user.user_type != 'STAFF':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    # Placeholder for customer assistance
    return JsonResponse({'success': True, 'message': 'Assistance fournie'})


@login_required
def generate_report(request):
    """Generate performance report"""
    if request.user.user_type != 'STAFF':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    # Placeholder for report generation
    return JsonResponse({'success': True, 'message': 'Rapport généré'})


@login_required
def update_task_status(request):
    """Update task status"""
    if request.user.user_type != 'STAFF':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    # Placeholder for task status update
    return JsonResponse({'success': True, 'message': 'Statut de tâche mis à jour'})


@login_required
def process_qr_scan(request):
    """Process QR code scan result"""
    if request.user.user_type != 'STAFF':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    # Placeholder for QR scan processing
    return JsonResponse({'success': True, 'message': 'QR Code traité'})


@login_required
def generate_qr_code(request):
    """Generate QR code for items"""
    if request.user.user_type != 'STAFF':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    # Placeholder for QR code generation
    return JsonResponse({'success': True, 'qr_code': 'data:image/png;base64,...'})


@login_required
def receive_stock(request):
    """Receive stock into inventory"""
    if request.user.user_type != 'STAFF':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    # Placeholder for stock receiving
    return JsonResponse({'success': True, 'message': 'Stock reçu'})


@login_required
def contact_customer(request):
    """Contact customer for support"""
    if request.user.user_type != 'STAFF':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    # Placeholder for customer contact
    return JsonResponse({'success': True, 'message': 'Client contacté'}) 