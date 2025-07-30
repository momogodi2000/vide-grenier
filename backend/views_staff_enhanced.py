# backend/views_staff_enhanced.py - ENHANCED STAFF DASHBOARD
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count, Avg, F, Max, Min
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
    StaffTask, InventoryMovement, StaffPerformance,
    ShoppingCart, CartItem, Wishlist, WishlistItem,
    ProductReview, Commission, Wallet, Transaction,
    WithdrawalRequest, PrivateChat, PrivateMessage
)
from .forms import (
    ProductForm, OrderForm, ReviewForm, ProfileForm,
    StaffTaskForm, PickupPointForm, StaffPerformanceForm
)

User = get_user_model()
logger = logging.getLogger(__name__)

# ============= ENHANCED STAFF DASHBOARD =============

@login_required
def staff_dashboard(request):
    """Enhanced staff dashboard with comprehensive analytics"""
    
    # Check if user is staff
    if not request.user.is_staff:
        messages.error(request, 'Accès non autorisé')
        return redirect('backend:home')
    
    user = request.user
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    # Task Analytics
    assigned_tasks = StaffTask.objects.filter(
        assigned_to=user,
        created_at__gte=last_30_days
    )
    
    completed_tasks = assigned_tasks.filter(status='COMPLETED').count()
    pending_tasks = assigned_tasks.filter(status='PENDING').count()
    in_progress_tasks = assigned_tasks.filter(status='IN_PROGRESS').count()
    
    # Performance Metrics
    performance_records = StaffPerformance.objects.filter(
        staff_member=user,
        date__gte=last_30_days
    )
    
    avg_efficiency = performance_records.aggregate(
        avg_efficiency=Avg('efficiency_score')
    )['avg_efficiency'] or 0.0
    
    avg_customer_rating = performance_records.aggregate(
        avg_rating=Avg('customer_rating')
    )['avg_rating'] or 0.0
    
    # Order Processing
    processed_orders = Order.objects.filter(
        status='COMPLETED',
        updated_at__gte=last_30_days
    ).count()
    
    pending_orders = Order.objects.filter(
        status='PENDING'
    ).count()
    
    # Inventory Management
    inventory_movements = InventoryMovement.objects.filter(
        staff_member=user,
        created_at__gte=last_30_days
    ).count()
    
    # Pickup Point Performance
    pickup_points = PickupPoint.objects.all()
    pickup_point_stats = []
    
    for point in pickup_points:
        point_orders = Order.objects.filter(
            pickup_point=point,
            created_at__gte=last_30_days
        )
        point_stats = {
            'name': point.name,
            'total_orders': point_orders.count(),
            'completed_orders': point_orders.filter(status='COMPLETED').count(),
            'pending_orders': point_orders.filter(status='PENDING').count(),
        }
        pickup_point_stats.append(point_stats)
    
    # Recent Activities
    recent_tasks = assigned_tasks.order_by('-created_at')[:5]
    recent_movements = InventoryMovement.objects.filter(
        staff_member=user
    ).order_by('-created_at')[:5]
    
    # System Overview
    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(
        status='COMPLETED'
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    context = {
        'user': user,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'avg_efficiency': avg_efficiency,
        'avg_customer_rating': avg_customer_rating,
        'processed_orders': processed_orders,
        'pending_orders': pending_orders,
        'inventory_movements': inventory_movements,
        'pickup_point_stats': pickup_point_stats,
        'recent_tasks': recent_tasks,
        'recent_movements': recent_movements,
        'total_users': total_users,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
    }
    
    return render(request, 'backend/staff/dashboard/enhanced_staff_dashboard.html', context)

@login_required
def staff_analytics(request):
    """Detailed analytics for staff"""
    
    if not request.user.is_staff:
        messages.error(request, 'Accès non autorisé')
        return redirect('backend:home')
    
    user = request.user
    period = request.GET.get('period', '30')  # days
    days = int(period)
    start_date = timezone.now().date() - timedelta(days=days)
    
    # Task Performance Analytics
    task_data = StaffTask.objects.filter(
        assigned_to=user,
        created_at__gte=start_date
    ).values('created_at__date').annotate(
        tasks_created=Count('id'),
        tasks_completed=Count('id', filter=Q(status='COMPLETED')),
        avg_duration=Avg('actual_duration')
    ).order_by('created_at__date')
    
    # Order Processing Analytics
    order_data = Order.objects.filter(
        status='COMPLETED',
        updated_at__gte=start_date
    ).values('updated_at__date').annotate(
        orders_processed=Count('id'),
        total_revenue=Sum('total_amount')
    ).order_by('updated_at__date')
    
    # Inventory Movement Analytics
    movement_data = InventoryMovement.objects.filter(
        staff_member=user,
        created_at__gte=start_date
    ).values('created_at__date').annotate(
        movements=Count('id'),
        total_quantity=Sum('quantity_change')
    ).order_by('created_at__date')
    
    # Performance Trends
    performance_data = StaffPerformance.objects.filter(
        staff_member=user,
        date__gte=start_date
    ).values('date').annotate(
        efficiency=Avg('efficiency_score'),
        customer_rating=Avg('customer_rating'),
        tasks_completed=Sum('tasks_completed')
    ).order_by('date')
    
    # Pickup Point Performance
    pickup_performance = PickupPoint.objects.annotate(
        total_orders=Count('orders'),
        completed_orders=Count('orders', filter=Q(orders__status='COMPLETED')),
        pending_orders=Count('orders', filter=Q(orders__status='PENDING')),
        avg_processing_time=Avg('orders__updated_at' - 'orders__created_at')
    ).values('name', 'total_orders', 'completed_orders', 'pending_orders')
    
    context = {
        'task_data': list(task_data),
        'order_data': list(order_data),
        'movement_data': list(movement_data),
        'performance_data': list(performance_data),
        'pickup_performance': list(pickup_performance),
        'period': period,
    }
    
    return render(request, 'backend/staff/analytics/staff_analytics.html', context)

# ============= TASK MANAGEMENT =============

@login_required
def staff_task_dashboard(request):
    """Task management dashboard"""
    
    if not request.user.is_staff:
        messages.error(request, 'Accès non autorisé')
        return redirect('backend:home')
    
    user = request.user
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    task_type_filter = request.GET.get('task_type', '')
    
    # Get tasks
    tasks = StaffTask.objects.filter(assigned_to=user)
    
    # Apply filters
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    if task_type_filter:
        tasks = tasks.filter(task_type=task_type_filter)
    
    # Pagination
    paginator = Paginator(tasks, 20)
    page_number = request.GET.get('page')
    tasks_page = paginator.get_page(page_number)
    
    # Task statistics
    task_stats = {
        'total_tasks': StaffTask.objects.filter(assigned_to=user).count(),
        'pending_tasks': StaffTask.objects.filter(assigned_to=user, status='PENDING').count(),
        'in_progress_tasks': StaffTask.objects.filter(assigned_to=user, status='IN_PROGRESS').count(),
        'completed_tasks': StaffTask.objects.filter(assigned_to=user, status='COMPLETED').count(),
        'urgent_tasks': StaffTask.objects.filter(assigned_to=user, priority='URGENT').count(),
    }
    
    # Performance metrics
    completed_tasks = StaffTask.objects.filter(
        assigned_to=user,
        status='COMPLETED',
        completed_at__gte=timezone.now() - timedelta(days=30)
    )
    
    avg_completion_time = completed_tasks.aggregate(
        avg_time=Avg('actual_duration')
    )['avg_time'] or 0
    
    context = {
        'tasks': tasks_page,
        'task_stats': task_stats,
        'avg_completion_time': avg_completion_time,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'task_type_filter': task_type_filter,
    }
    
    return render(request, 'backend/staff/tasks/enhanced_task_dashboard.html', context)

class StaffTaskCreateView(LoginRequiredMixin, CreateView):
    """Create new task"""
    model = StaffTask
    form_class = StaffTaskForm
    template_name = 'backend/staff/tasks/task_form.html'
    success_url = reverse_lazy('backend:staff_task_dashboard')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Tâche créée avec succès!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['staff_members'] = User.objects.filter(is_staff=True)
        context['pickup_points'] = PickupPoint.objects.all()
        return context

class StaffTaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update task"""
    model = StaffTask
    form_class = StaffTaskForm
    template_name = 'backend/staff/tasks/task_form.html'
    success_url = reverse_lazy('backend:staff_task_dashboard')
    
    def test_func(self):
        task = self.get_object()
        return task.assigned_to == self.request.user or task.created_by == self.request.user
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Tâche mise à jour avec succès!')
        return response

@login_required
@require_POST
def staff_start_task(request, task_id):
    """Start a task"""
    
    try:
        task = get_object_or_404(StaffTask, id=task_id, assigned_to=request.user)
        
        if task.status == 'PENDING':
            task.status = 'IN_PROGRESS'
            task.started_at = timezone.now()
            task.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Tâche démarrée avec succès'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Tâche déjà en cours ou terminée'
            })
            
    except Exception as e:
        logger.error(f"Error starting task: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors du démarrage de la tâche'
        })

@login_required
@require_POST
def staff_complete_task(request, task_id):
    """Complete a task"""
    
    try:
        task = get_object_or_404(StaffTask, id=task_id, assigned_to=request.user)
        
        if task.status == 'IN_PROGRESS':
            task.status = 'COMPLETED'
            task.completed_at = timezone.now()
            task.actual_duration = request.POST.get('actual_duration', 0)
            task.completion_notes = request.POST.get('completion_notes', '')
            task.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Tâche terminée avec succès'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Tâche non démarrée ou déjà terminée'
            })
            
    except Exception as e:
        logger.error(f"Error completing task: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors de la finalisation de la tâche'
        })

# ============= INVENTORY MANAGEMENT =============

@login_required
def staff_inventory_dashboard(request):
    """Inventory management dashboard"""
    
    if not request.user.is_staff:
        messages.error(request, 'Accès non autorisé')
        return redirect('backend:home')
    
    user = request.user
    movement_type_filter = request.GET.get('movement_type', '')
    pickup_point_filter = request.GET.get('pickup_point', '')
    
    # Get inventory movements
    movements = InventoryMovement.objects.filter(staff_member=user)
    
    # Apply filters
    if movement_type_filter:
        movements = movements.filter(movement_type=movement_type_filter)
    if pickup_point_filter:
        movements = movements.filter(pickup_point_id=pickup_point_filter)
    
    # Pagination
    paginator = Paginator(movements, 20)
    page_number = request.GET.get('page')
    movements_page = paginator.get_page(page_number)
    
    # Inventory statistics
    inventory_stats = {
        'total_movements': InventoryMovement.objects.filter(staff_member=user).count(),
        'stock_received': InventoryMovement.objects.filter(
            staff_member=user, movement_type='RECEIVE'
        ).count(),
        'orders_picked': InventoryMovement.objects.filter(
            staff_member=user, movement_type='PICK'
        ).count(),
        'returns_processed': InventoryMovement.objects.filter(
            staff_member=user, movement_type='RETURN'
        ).count(),
    }
    
    # Pickup point inventory
    pickup_points = PickupPoint.objects.all()
    pickup_inventory = []
    
    for point in pickup_points:
        point_movements = InventoryMovement.objects.filter(pickup_point=point)
        point_stats = {
            'name': point.name,
            'total_movements': point_movements.count(),
            'stock_received': point_movements.filter(movement_type='RECEIVE').count(),
            'orders_picked': point_movements.filter(movement_type='PICK').count(),
        }
        pickup_inventory.append(point_stats)
    
    context = {
        'movements': movements_page,
        'inventory_stats': inventory_stats,
        'pickup_inventory': pickup_inventory,
        'pickup_points': pickup_points,
        'movement_type_filter': movement_type_filter,
        'pickup_point_filter': pickup_point_filter,
    }
    
    return render(request, 'backend/staff/inventory/enhanced_inventory_dashboard.html', context)

@login_required
@require_POST
def staff_record_inventory_movement(request):
    """Record inventory movement"""
    
    try:
        data = json.loads(request.body)
        
        movement = InventoryMovement.objects.create(
            product_id=data.get('product_id'),
            pickup_point_id=data.get('pickup_point_id'),
            staff_member=request.user,
            movement_type=data.get('movement_type'),
            quantity_change=data.get('quantity_change'),
            reference_order_id=data.get('reference_order_id'),
            notes=data.get('notes', ''),
            batch_id=data.get('batch_id', ''),
            location_from=data.get('location_from', ''),
            location_to=data.get('location_to', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Mouvement d\'inventaire enregistré avec succès',
            'movement_id': str(movement.id)
        })
        
    except Exception as e:
        logger.error(f"Error recording inventory movement: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors de l\'enregistrement du mouvement'
        })

# ============= PICKUP POINT MANAGEMENT =============

@login_required
def staff_pickup_point_dashboard(request):
    """Pickup point management dashboard"""
    
    if not request.user.is_staff:
        messages.error(request, 'Accès non autorisé')
        return redirect('backend:home')
    
    # Get pickup points
    pickup_points = PickupPoint.objects.all()
    
    # Pickup point statistics
    for point in pickup_points:
        point_orders = Order.objects.filter(pickup_point=point)
        point.total_orders = point_orders.count()
        point.completed_orders = point_orders.filter(status='COMPLETED').count()
        point.pending_orders = point_orders.filter(status='PENDING').count()
        point.total_revenue = point_orders.filter(
            status='COMPLETED'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    # Staff assignments
    staff_members = User.objects.filter(is_staff=True)
    staff_assignments = []
    
    for staff in staff_members:
        staff_tasks = StaffTask.objects.filter(assigned_to=staff)
        staff_stats = {
            'user': staff,
            'total_tasks': staff_tasks.count(),
            'completed_tasks': staff_tasks.filter(status='COMPLETED').count(),
            'pending_tasks': staff_tasks.filter(status='PENDING').count(),
        }
        staff_assignments.append(staff_stats)
    
    context = {
        'pickup_points': pickup_points,
        'staff_assignments': staff_assignments,
    }
    
    return render(request, 'backend/staff/pickup/enhanced_pickup_dashboard.html', context)

class PickupPointCreateView(LoginRequiredMixin, CreateView):
    """Create pickup point"""
    model = PickupPoint
    form_class = PickupPointForm
    template_name = 'backend/staff/pickup/pickup_point_form.html'
    success_url = reverse_lazy('backend:staff_pickup_point_dashboard')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Point de retrait créé avec succès!')
        return response

class PickupPointUpdateView(LoginRequiredMixin, UpdateView):
    """Update pickup point"""
    model = PickupPoint
    form_class = PickupPointForm
    template_name = 'backend/staff/pickup/pickup_point_form.html'
    success_url = reverse_lazy('backend:staff_pickup_point_dashboard')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Point de retrait mis à jour avec succès!')
        return response

# ============= PERFORMANCE MONITORING =============

@login_required
def staff_performance_dashboard(request):
    """Staff performance monitoring dashboard"""
    
    if not request.user.is_staff:
        messages.error(request, 'Accès non autorisé')
        return redirect('backend:home')
    
    user = request.user
    period = request.GET.get('period', '30')  # days
    days = int(period)
    start_date = timezone.now().date() - timedelta(days=days)
    
    # Performance records
    performance_records = StaffPerformance.objects.filter(
        staff_member=user,
        date__gte=start_date
    ).order_by('-date')
    
    # Performance trends
    performance_trends = performance_records.values('date').annotate(
        avg_efficiency=Avg('efficiency_score'),
        avg_customer_rating=Avg('customer_rating'),
        total_tasks=Sum('tasks_completed'),
        total_orders=Sum('orders_processed')
    ).order_by('date')
    
    # Performance statistics
    performance_stats = performance_records.aggregate(
        avg_efficiency=Avg('efficiency_score'),
        avg_customer_rating=Avg('customer_rating'),
        total_tasks=Sum('tasks_completed'),
        total_orders=Sum('orders_processed'),
        avg_punctuality=Avg('punctuality_score'),
        avg_inventory_accuracy=Avg('inventory_accuracy')
    )
    
    # Comparison with other staff
    all_staff_performance = StaffPerformance.objects.filter(
        date__gte=start_date
    ).values('staff_member__username').annotate(
        avg_efficiency=Avg('efficiency_score'),
        avg_customer_rating=Avg('customer_rating'),
        total_tasks=Sum('tasks_completed')
    ).order_by('-avg_efficiency')
    
    context = {
        'performance_records': performance_records,
        'performance_trends': list(performance_trends),
        'performance_stats': performance_stats,
        'all_staff_performance': list(all_staff_performance),
        'period': period,
    }
    
    return render(request, 'backend/staff/performance/enhanced_performance_dashboard.html', context)

@login_required
@require_POST
def staff_record_performance(request):
    """Record performance metrics"""
    
    try:
        data = json.loads(request.body)
        
        performance = StaffPerformance.objects.create(
            staff_member=request.user,
            pickup_point_id=data.get('pickup_point_id'),
            date=data.get('date'),
            tasks_completed=data.get('tasks_completed', 0),
            orders_processed=data.get('orders_processed', 0),
            customer_rating=data.get('customer_rating', 0.0),
            efficiency_score=data.get('efficiency_score', 0.0),
            punctuality_score=data.get('punctuality_score', 0.0),
            inventory_accuracy=data.get('inventory_accuracy', 0.0),
            notes=data.get('notes', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Performance enregistrée avec succès',
            'performance_id': str(performance.id)
        })
        
    except Exception as e:
        logger.error(f"Error recording performance: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors de l\'enregistrement de la performance'
        })

# ============= ORDER PROCESSING =============

@login_required
def staff_order_processing(request):
    """Order processing dashboard"""
    
    if not request.user.is_staff:
        messages.error(request, 'Accès non autorisé')
        return redirect('backend:home')
    
    status_filter = request.GET.get('status', '')
    pickup_point_filter = request.GET.get('pickup_point', '')
    
    # Get orders
    orders = Order.objects.all()
    
    # Apply filters
    if status_filter:
        orders = orders.filter(status=status_filter)
    if pickup_point_filter:
        orders = orders.filter(pickup_point_id=pickup_point_filter)
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)
    
    # Order statistics
    order_stats = {
        'total_orders': Order.objects.count(),
        'pending_orders': Order.objects.filter(status='PENDING').count(),
        'processing_orders': Order.objects.filter(status='PROCESSING').count(),
        'completed_orders': Order.objects.filter(status='COMPLETED').count(),
        'cancelled_orders': Order.objects.filter(status='CANCELLED').count(),
    }
    
    # Pickup point orders
    pickup_points = PickupPoint.objects.all()
    pickup_orders = []
    
    for point in pickup_points:
        point_orders = Order.objects.filter(pickup_point=point)
        point_stats = {
            'name': point.name,
            'total_orders': point_orders.count(),
            'pending_orders': point_orders.filter(status='PENDING').count(),
            'processing_orders': point_orders.filter(status='PROCESSING').count(),
            'completed_orders': point_orders.filter(status='COMPLETED').count(),
        }
        pickup_orders.append(point_stats)
    
    context = {
        'orders': orders_page,
        'order_stats': order_stats,
        'pickup_orders': pickup_orders,
        'pickup_points': pickup_points,
        'status_filter': status_filter,
        'pickup_point_filter': pickup_point_filter,
    }
    
    return render(request, 'backend/staff/orders/enhanced_order_processing.html', context)

@login_required
@require_POST
def staff_update_order_status(request, order_id):
    """Update order status"""
    
    try:
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        if new_status in ['PENDING', 'PROCESSING', 'COMPLETED', 'CANCELLED']:
            order.status = new_status
            order.save()
            
            # Record inventory movement if order is completed
            if new_status == 'COMPLETED':
                InventoryMovement.objects.create(
                    product=order.product,
                    pickup_point=order.pickup_point,
                    staff_member=request.user,
                    movement_type='PICK',
                    quantity_change=-order.quantity,
                    reference_order=order,
                    notes=f'Order {order.id} completed'
                )
            
            return JsonResponse({
                'success': True,
                'message': f'Statut de commande mis à jour: {new_status}'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Statut invalide'
            })
            
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors de la mise à jour du statut'
        })

# ============= API ENDPOINTS =============

@login_required
@require_POST
def staff_analytics_data(request):
    """API endpoint for staff analytics data"""
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    user = request.user
    period = request.POST.get('period', '30')
    days = int(period)
    start_date = timezone.now().date() - timedelta(days=days)
    
    # Task data
    task_data = StaffTask.objects.filter(
        assigned_to=user,
        created_at__gte=start_date
    ).values('created_at__date').annotate(
        tasks=Count('id'),
        completed=Count('id', filter=Q(status='COMPLETED'))
    ).order_by('created_at__date')
    
    # Performance data
    performance_data = StaffPerformance.objects.filter(
        staff_member=user,
        date__gte=start_date
    ).values('date').annotate(
        efficiency=Avg('efficiency_score'),
        customer_rating=Avg('customer_rating')
    ).order_by('date')
    
    return JsonResponse({
        'task_data': list(task_data),
        'performance_data': list(performance_data),
    })

@login_required
@require_POST
def staff_create_task(request):
    """Create task via API"""
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        task = StaffTask.objects.create(
            assigned_to_id=data.get('assigned_to'),
            created_by=request.user,
            pickup_point_id=data.get('pickup_point'),
            task_type=data.get('task_type'),
            title=data.get('title'),
            description=data.get('description'),
            priority=data.get('priority', 'MEDIUM'),
            due_date=data.get('due_date'),
            estimated_duration=data.get('estimated_duration', 60)
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Tâche créée avec succès',
            'task_id': str(task.id)
        })
        
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors de la création de la tâche'
        })

@login_required
@require_POST
def staff_record_movement(request):
    """Record inventory movement via API"""
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        movement = InventoryMovement.objects.create(
            product_id=data.get('product_id'),
            pickup_point_id=data.get('pickup_point_id'),
            staff_member=request.user,
            movement_type=data.get('movement_type'),
            quantity_change=data.get('quantity_change'),
            reference_order_id=data.get('reference_order_id'),
            notes=data.get('notes', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Mouvement enregistré avec succès',
            'movement_id': str(movement.id)
        })
        
    except Exception as e:
        logger.error(f"Error recording movement: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors de l\'enregistrement du mouvement'
        }) 