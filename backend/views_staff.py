# backend/views_staff.py - COMPLETE STAFF SYSTEM FOR VGK
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
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
import qrcode
import io
import base64
from datetime import datetime, timedelta, date
from PIL import Image, ImageDraw, ImageFont

from .models import User, Product, Category, Order, PickupPoint
from .models_advanced import (
    StaffTask, InventoryMovement, StaffPerformance, SmartNotification
)
from .utils import send_sms_notification

class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user is staff"""
    def test_func(self):
        return self.request.user.user_type == 'STAFF'

def staff_required(view_func):
    """Decorator to ensure user is staff"""
    def wrapper(request, *args, **kwargs):
        if request.user.user_type != 'STAFF':
            messages.error(request, 'Accès réservé au personnel.')
            return redirect('backend:home')
        return view_func(request, *args, **kwargs)
    return wrapper

# ============= STAFF DASHBOARD =============

class StaffDashboardView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """Comprehensive staff dashboard"""
    template_name = 'backend/staff/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get staff's pickup point
        pickup_point = self._get_staff_pickup_point(user)
        
        # Today's tasks and statistics
        today_data = self._get_today_statistics(user, pickup_point)
        
        # Pending tasks
        pending_tasks = self._get_pending_tasks(user, pickup_point)
        
        # Performance metrics
        performance_data = self._get_performance_metrics(user)
        
        # Inventory alerts
        inventory_alerts = self._get_inventory_alerts(pickup_point)
        
        context.update({
            'pickup_point': pickup_point,
            'today_data': today_data,
            'pending_tasks': pending_tasks,
            'performance_data': performance_data,
            'inventory_alerts': inventory_alerts,
            'quick_actions': self._get_quick_actions()
        })
        
        return context
    
    def _get_staff_pickup_point(self, user):
        """Get the pickup point managed by this staff member"""
        return PickupPoint.objects.filter(manager=user).first()
    
    def _get_today_statistics(self, user, pickup_point):
        """Get today's key statistics"""
        today = timezone.now().date()
        
        # Orders to process today
        orders_today = Order.objects.filter(
            delivery_method='PICKUP',
            created_at__date=today
        )
        
        if pickup_point:
            # Filter by pickup point if available (would need relationship)
            pass
        
        # Tasks completed today
        tasks_completed = StaffTask.objects.filter(
            assigned_to=user,
            completed_at__date=today,
            status='COMPLETED'
        ).count()
        
        # Inventory movements today
        movements_today = InventoryMovement.objects.filter(
            staff_member=user,
            created_at__date=today
        ).count()
        
        return {
            'orders_to_process': orders_today.filter(status='PAID').count(),
            'orders_completed': orders_today.filter(status='DELIVERED').count(),
            'tasks_completed': tasks_completed,
            'inventory_movements': movements_today,
            'efficiency_score': self._calculate_daily_efficiency(user, today)
        }
    
    def _get_pending_tasks(self, user, pickup_point):
        """Get pending tasks for staff member"""
        return StaffTask.objects.filter(
            assigned_to=user,
            status__in=['PENDING', 'IN_PROGRESS']
        ).order_by('due_date', '-priority')[:10]
    
    def _get_performance_metrics(self, user):
        """Get staff performance metrics"""
        last_7_days = timezone.now() - timedelta(days=7)
        
        recent_performance = StaffPerformance.objects.filter(
            staff_member=user,
            date__gte=last_7_days.date()
        ).aggregate(
            avg_efficiency=Avg('efficiency_score'),
            avg_customer_rating=Avg('customer_rating'),
            avg_punctuality=Avg('punctuality_score'),
            total_tasks=Sum('tasks_completed')
        )
        
        return {
            'efficiency_score': recent_performance['avg_efficiency'] or 0,
            'customer_rating': recent_performance['avg_customer_rating'] or 0,
            'punctuality_score': recent_performance['avg_punctuality'] or 0,
            'total_tasks_week': recent_performance['total_tasks'] or 0
        }
    
    def _get_inventory_alerts(self, pickup_point):
        """Get inventory alerts and issues"""
        alerts = []
        
        if pickup_point:
            # Low stock alerts (would need proper inventory tracking)
            # Damage reports
            # Expired items
            pass
        
        return alerts
    
    def _get_quick_actions(self):
        """Get quick action items"""
        return [
            {'icon': 'qr-code', 'title': 'Scanner QR Code', 'action': 'scan_qr'},
            {'icon': 'package', 'title': 'Réception Stock', 'action': 'receive_stock'},
            {'icon': 'clipboard-check', 'title': 'Inventaire', 'action': 'inventory_count'},
            {'icon': 'truck', 'title': 'Traiter Livraison', 'action': 'process_delivery'},
            {'icon': 'user-check', 'title': 'Service Client', 'action': 'customer_service'},
            {'icon': 'alert-triangle', 'title': 'Signaler Problème', 'action': 'report_issue'}
        ]
    
    def _calculate_daily_efficiency(self, user, date):
        """Calculate daily efficiency score"""
        try:
            performance = StaffPerformance.objects.get(
                staff_member=user,
                date=date
            )
            return performance.efficiency_score
        except StaffPerformance.DoesNotExist:
            return 0.0

# ============= TASK MANAGEMENT =============

class StaffTaskListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """Task management for staff"""
    model = StaffTask
    template_name = 'backend/staff/tasks/list.html'
    context_object_name = 'tasks'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = StaffTask.objects.filter(
            assigned_to=self.request.user
        ).select_related('created_by', 'pickup_point')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by priority
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by task type
        task_type = self.request.GET.get('task_type')
        if task_type:
            queryset = queryset.filter(task_type=task_type)
        
        return queryset.order_by('due_date', '-priority')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Task statistics
        all_tasks = StaffTask.objects.filter(assigned_to=self.request.user)
        
        context.update({
            'stats': {
                'total': all_tasks.count(),
                'pending': all_tasks.filter(status='PENDING').count(),
                'in_progress': all_tasks.filter(status='IN_PROGRESS').count(),
                'completed': all_tasks.filter(status='COMPLETED').count(),
                'overdue': all_tasks.filter(
                    due_date__lt=timezone.now(),
                    status__in=['PENDING', 'IN_PROGRESS']
                ).count()
            },
            'task_types': StaffTask.TASK_TYPES,
            'priorities': StaffTask.PRIORITIES,
            'statuses': StaffTask.STATUSES
        })
        
        return context

@login_required
@staff_required
def update_task_status(request):
    """Update task status via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            task_id = data.get('task_id')
            new_status = data.get('status')
            completion_notes = data.get('notes', '')
            
            task = get_object_or_404(
                StaffTask,
                id=task_id,
                assigned_to=request.user
            )
            
            old_status = task.status
            task.status = new_status
            
            if new_status == 'IN_PROGRESS' and old_status == 'PENDING':
                task.started_at = timezone.now()
            elif new_status == 'COMPLETED':
                task.completed_at = timezone.now()
                task.completion_notes = completion_notes
                
                # Calculate actual duration
                if task.started_at:
                    duration = (task.completed_at - task.started_at).total_seconds() / 60
                    task.actual_duration = int(duration)
            
            task.save()
            
            # Update daily performance if task completed
            if new_status == 'COMPLETED':
                self._update_daily_performance(request.user)
            
            return JsonResponse({
                'success': True,
                'message': f'Tâche mise à jour: {task.get_status_display()}'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def _update_daily_performance(user):
    """Update daily performance metrics"""
    today = timezone.now().date()
    
    # Get or create performance record
    performance, created = StaffPerformance.objects.get_or_create(
        staff_member=user,
        date=today,
        defaults={
            'pickup_point': PickupPoint.objects.filter(manager=user).first()
        }
    )
    
    # Calculate metrics
    today_tasks = StaffTask.objects.filter(
        assigned_to=user,
        completed_at__date=today,
        status='COMPLETED'
    )
    
    performance.tasks_completed = today_tasks.count()
    
    # Calculate efficiency (tasks completed vs estimated time)
    if today_tasks.exists():
        total_estimated = sum(task.estimated_duration for task in today_tasks)
        total_actual = sum(task.actual_duration or task.estimated_duration for task in today_tasks)
        
        if total_actual > 0:
            performance.efficiency_score = min(100, (total_estimated / total_actual) * 100)
    
    performance.save()

# ============= QR CODE SYSTEM =============

class QRScannerView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """QR Code scanner interface"""
    template_name = 'backend/staff/qr_scanner.html'

@login_required
@staff_required
def process_qr_scan(request):
    """Process QR code scan results"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            qr_data = data.get('qr_data')
            scan_type = data.get('scan_type', 'order')  # order, product, inventory
            
            if scan_type == 'order':
                return self._process_order_qr(request, qr_data)
            elif scan_type == 'product':
                return self._process_product_qr(request, qr_data)
            elif scan_type == 'inventory':
                return self._process_inventory_qr(request, qr_data)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def _process_order_qr(request, qr_data):
    """Process order pickup QR code"""
    try:
        # QR data format: "ORDER:{order_id}:{pickup_code}"
        parts = qr_data.split(':')
        if len(parts) != 3 or parts[0] != 'ORDER':
            return JsonResponse({
                'success': False,
                'error': 'QR Code invalide'
            })
        
        order_id = parts[1]
        pickup_code = parts[2]
        
        order = get_object_or_404(
            Order,
            id=order_id,
            pickup_code=pickup_code,
            delivery_method='PICKUP',
            status='PAID'
        )
        
        # Mark order as delivered
        order.status = 'DELIVERED'
        order.delivered_at = timezone.now()
        order.save()
        
        # Record inventory movement
        InventoryMovement.objects.create(
            product=order.product,
            pickup_point=PickupPoint.objects.filter(manager=request.user).first(),
            staff_member=request.user,
            movement_type='PICK',
            quantity_change=-order.quantity,
            reference_order=order,
            notes=f'Retrait client - QR scan'
        )
        
        # Send notification to customer
        if order.buyer:
            from .smart_notifications import smart_notifications
            smart_notifications.trigger_notification(
                template_name='order_picked_up',
                user=order.buyer,
                context={
                    'order_number': order.order_number,
                    'product_name': order.product.title,
                    'pickup_time': timezone.now().strftime('%H:%M')
                }
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Commande {order.order_number} retirée avec succès',
            'order_info': {
                'order_number': order.order_number,
                'product_name': order.product.title,
                'customer_name': order.buyer.get_full_name() if order.buyer else order.visitor_name,
                'amount': float(order.total_amount)
            }
        })
        
    except Order.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Commande non trouvée ou code invalide'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def _process_product_qr(request, qr_data):
    """Process product QR code for inventory"""
    try:
        # QR data format: "PRODUCT:{product_id}"
        parts = qr_data.split(':')
        if len(parts) != 2 or parts[0] != 'PRODUCT':
            return JsonResponse({
                'success': False,
                'error': 'QR Code produit invalide'
            })
        
        product_id = parts[1]
        product = get_object_or_404(Product, id=product_id)
        
        return JsonResponse({
            'success': True,
            'product_info': {
                'id': str(product.id),
                'title': product.title,
                'price': float(product.price),
                'condition': product.get_condition_display(),
                'category': product.category.name,
                'status': product.get_status_display()
            }
        })
        
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Produit non trouvé'
        })

@login_required
@staff_required
def generate_qr_code(request):
    """Generate QR codes for orders/products"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            qr_type = data.get('type')  # order, product
            item_id = data.get('item_id')
            
            if qr_type == 'order':
                order = get_object_or_404(Order, id=item_id)
                qr_data = f"ORDER:{order.id}:{order.pickup_code}"
                filename = f"order_{order.order_number}.png"
            elif qr_type == 'product':
                product = get_object_or_404(Product, id=item_id)
                qr_data = f"PRODUCT:{product.id}"
                filename = f"product_{product.id}.png"
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Type QR invalide'
                })
            
            # Generate QR code
            qr_image = self._create_qr_code(qr_data)
            
            return JsonResponse({
                'success': True,
                'qr_image': qr_image,
                'filename': filename
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def _create_qr_code(data):
    """Create QR code image and return as base64"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

# ============= INVENTORY MANAGEMENT =============

class InventoryListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """Inventory management view"""
    model = Product
    template_name = 'backend/staff/inventory/list.html'
    context_object_name = 'products'
    paginate_by = 25
    
    def get_queryset(self):
        # Get products at staff's pickup point
        pickup_point = PickupPoint.objects.filter(manager=self.request.user).first()
        
        queryset = Product.objects.filter(
            source='ADMIN',  # Admin products in inventory
            status__in=['ACTIVE', 'RESERVED']
        ).select_related('category', 'seller')
        
        # Add search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('title')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        pickup_point = PickupPoint.objects.filter(manager=self.request.user).first()
        
        # Inventory statistics
        total_products = self.get_queryset().count()
        active_products = self.get_queryset().filter(status='ACTIVE').count()
        reserved_products = self.get_queryset().filter(status='RESERVED').count()
        
        context.update({
            'pickup_point': pickup_point,
            'stats': {
                'total_products': total_products,
                'active_products': active_products,
                'reserved_products': reserved_products,
                'capacity_used': (total_products / pickup_point.capacity * 100) if pickup_point else 0
            }
        })
        
        return context

@login_required
@staff_required
def receive_stock(request):
    """Receive new stock at pickup point"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 1))
            location = data.get('location', '')
            notes = data.get('notes', '')
            
            product = get_object_or_404(Product, id=product_id)
            pickup_point = PickupPoint.objects.filter(manager=request.user).first()
            
            # Record inventory movement
            movement = InventoryMovement.objects.create(
                product=product,
                pickup_point=pickup_point,
                staff_member=request.user,
                movement_type='RECEIVE',
                quantity_change=quantity,
                location_to=location,
                notes=notes
            )
            
            # Update pickup point current stock
            if pickup_point:
                pickup_point.current_stock += quantity
                pickup_point.save()
            
            # Create staff task for stock organization
            StaffTask.objects.create(
                assigned_to=request.user,
                created_by=request.user,
                pickup_point=pickup_point,
                task_type='STOCK_RECEIVE',
                title=f'Ranger stock: {product.title}',
                description=f'Ranger {quantity} unité(s) de {product.title}',
                priority='MEDIUM',
                due_date=timezone.now() + timedelta(hours=2),
                estimated_duration=30
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Stock reçu: {quantity} unité(s) de {product.title}',
                'movement_id': str(movement.id)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

class InventoryMovementListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """View inventory movements history"""
    model = InventoryMovement
    template_name = 'backend/staff/inventory/movements.html'
    context_object_name = 'movements'
    paginate_by = 50
    
    def get_queryset(self):
        return InventoryMovement.objects.filter(
            staff_member=self.request.user
        ).select_related('product', 'pickup_point').order_by('-created_at')

# ============= CUSTOMER SERVICE =============

class CustomerServiceView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """Customer service interface for staff"""
    template_name = 'backend/staff/customer_service.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Recent customer interactions
        pickup_point = PickupPoint.objects.filter(manager=self.request.user).first()
        
        # Orders requiring attention
        problem_orders = Order.objects.filter(
            delivery_method='PICKUP',
            status__in=['PAID', 'PROCESSING'],
            created_at__lt=timezone.now() - timedelta(days=2)
        ).select_related('product', 'buyer')[:10]
        
        context.update({
            'pickup_point': pickup_point,
            'problem_orders': problem_orders,
            'service_stats': self._get_service_stats()
        })
        
        return context
    
    def _get_service_stats(self):
        """Get customer service statistics"""
        last_30_days = timezone.now() - timedelta(days=30)
        
        return {
            'orders_processed': Order.objects.filter(
                delivery_method='PICKUP',
                delivered_at__gte=last_30_days,
                # Add staff relationship when available
            ).count(),
            'avg_pickup_time': 15,  # Placeholder
            'customer_satisfaction': 4.5  # Placeholder
        }

@login_required
@staff_required
def contact_customer(request):
    """Contact customer about their order"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            message = data.get('message')
            contact_method = data.get('contact_method', 'SMS')
            
            order = get_object_or_404(Order, id=order_id)
            
            if contact_method == 'SMS' and order.buyer and order.buyer.phone:
                success = send_sms_notification(
                    order.buyer.phone,
                    f"VGK - {message} Commande: {order.order_number}"
                )
                
                if success:
                    return JsonResponse({
                        'success': True,
                        'message': 'SMS envoyé au client'
                    })
            
            # Fallback to in-app notification
            from .models import Notification
            Notification.objects.create(
                user=order.buyer,
                title='Message du point de retrait',
                message=message,
                notification_type='SYSTEM'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Notification envoyée au client'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# ============= PERFORMANCE TRACKING =============

class StaffPerformanceView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """Staff performance dashboard"""
    template_name = 'backend/staff/performance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Performance over time
        last_30_days = timezone.now().date() - timedelta(days=30)
        performance_data = StaffPerformance.objects.filter(
            staff_member=user,
            date__gte=last_30_days
        ).order_by('date')
        
        # Current month statistics
        current_month_stats = self._get_current_month_stats(user)
        
        # Performance comparison with other staff
        comparison_data = self._get_performance_comparison(user)
        
        context.update({
            'performance_data': performance_data,
            'current_month_stats': current_month_stats,
            'comparison_data': comparison_data,
            'achievements': self._get_achievements(user)
        })
        
        return context
    
    def _get_current_month_stats(self, user):
        """Get current month performance statistics"""
        current_month = timezone.now().replace(day=1).date()
        
        month_performance = StaffPerformance.objects.filter(
            staff_member=user,
            date__gte=current_month
        ).aggregate(
            avg_efficiency=Avg('efficiency_score'),
            avg_customer_rating=Avg('customer_rating'),
            total_tasks=Sum('tasks_completed'),
            total_orders=Sum('orders_processed')
        )
        
        return {
            'efficiency_score': month_performance['avg_efficiency'] or 0,
            'customer_rating': month_performance['avg_customer_rating'] or 0,
            'total_tasks': month_performance['total_tasks'] or 0,
            'total_orders': month_performance['total_orders'] or 0
        }
    
    def _get_performance_comparison(self, user):
        """Compare performance with other staff members"""
        # Get average performance of all staff
        avg_performance = StaffPerformance.objects.filter(
            date__gte=timezone.now().date() - timedelta(days=30)
        ).aggregate(
            avg_efficiency=Avg('efficiency_score'),
            avg_customer_rating=Avg('customer_rating')
        )
        
        user_performance = StaffPerformance.objects.filter(
            staff_member=user,
            date__gte=timezone.now().date() - timedelta(days=30)
        ).aggregate(
            avg_efficiency=Avg('efficiency_score'),
            avg_customer_rating=Avg('customer_rating')
        )
        
        return {
            'efficiency_vs_avg': (user_performance['avg_efficiency'] or 0) - (avg_performance['avg_efficiency'] or 0),
            'rating_vs_avg': (user_performance['avg_customer_rating'] or 0) - (avg_performance['avg_customer_rating'] or 0)
        }
    
    def _get_achievements(self, user):
        """Get staff achievements and badges"""
        achievements = []
        
        # Task completion achievement
        total_tasks = StaffTask.objects.filter(
            assigned_to=user,
            status='COMPLETED'
        ).count()
        
        if total_tasks >= 100:
            achievements.append({
                'title': 'Maître des Tâches',
                'description': f'{total_tasks} tâches accomplies',
                'icon': 'award',
                'color': 'gold'
            })
        
        # Efficiency achievement
        avg_efficiency = StaffPerformance.objects.filter(
            staff_member=user
        ).aggregate(avg=Avg('efficiency_score'))['avg']
        
        if avg_efficiency and avg_efficiency >= 90:
            achievements.append({
                'title': 'Efficacité Maximale',
                'description': f'{avg_efficiency:.1f}% d\'efficacité moyenne',
                'icon': 'zap',
                'color': 'blue'
            })
        
        return achievements 