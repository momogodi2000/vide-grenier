# backend/views_advanced_features.py - ADVANCED BUSINESS FEATURES
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count, Avg, F, Max, Min, ExpressionWrapper, DecimalField
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
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import pandas as pd
import numpy as np
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_agg import FigureCanvasAgg

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
    StaffTaskForm, PickupPointForm, StaffPerformanceForm,
    EscrowPaymentForm, InstallmentPlanForm
)

User = get_user_model()
logger = logging.getLogger(__name__)

# ============= ESCROW PAYMENT SYSTEM =============

@login_required
def escrow_dashboard(request):
    """Escrow payment system dashboard"""
    
    user = request.user
    
    # Get escrow payments
    escrow_payments = EscrowPayment.objects.filter(
        Q(buyer=user) | Q(seller=user)
    ).order_by('-created_at')
    
    # Escrow statistics
    escrow_stats = {
        'total_escrow': escrow_payments.count(),
        'pending_escrow': escrow_payments.filter(status='PENDING').count(),
        'funded_escrow': escrow_payments.filter(status='FUNDED').count(),
        'released_escrow': escrow_payments.filter(status='RELEASED_TO_SELLER').count(),
        'disputed_escrow': escrow_payments.filter(status='DISPUTED').count(),
    }
    
    # Amount statistics
    amount_stats = escrow_payments.aggregate(
        total_amount=Sum('amount'),
        total_fees=Sum('fee_amount'),
        avg_amount=Avg('amount')
    )
    
    # Recent escrow payments
    recent_escrow = escrow_payments[:10]
    
    context = {
        'escrow_payments': recent_escrow,
        'escrow_stats': escrow_stats,
        'amount_stats': amount_stats,
    }
    
    return render(request, 'backend/advanced/escrow/escrow_dashboard.html', context)

@login_required
@require_POST
def create_escrow_payment(request, order_id):
    """Create escrow payment for order"""
    
    try:
        order = get_object_or_404(Order, id=order_id)
        
        # Check if user is the buyer
        if order.buyer != request.user:
            return JsonResponse({
                'success': False,
                'message': 'Accès non autorisé'
            })
        
        # Check if escrow already exists
        if hasattr(order, 'escrow_payment'):
            return JsonResponse({
                'success': False,
                'message': 'Paiement escrow déjà créé'
            })
        
        # Calculate escrow fee (2% of order amount)
        escrow_fee = order.total_amount * Decimal('0.02')
        
        # Create escrow payment
        escrow = EscrowPayment.objects.create(
            order=order,
            buyer=order.buyer,
            seller=order.product.seller,
            amount=order.total_amount,
            fee_amount=escrow_fee,
            release_date=timezone.now() + timedelta(days=7)  # 7 days auto-release
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Paiement escrow créé avec succès',
            'escrow_id': str(escrow.id)
        })
        
    except Exception as e:
        logger.error(f"Error creating escrow payment: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors de la création du paiement escrow'
        })

@login_required
@require_POST
def fund_escrow_payment(request, escrow_id):
    """Fund escrow payment"""
    
    try:
        escrow = get_object_or_404(EscrowPayment, id=escrow_id)
        
        # Check if user is the buyer
        if escrow.buyer != request.user:
            return JsonResponse({
                'success': False,
                'message': 'Accès non autorisé'
            })
        
        # Check if escrow is pending
        if escrow.status != 'PENDING':
            return JsonResponse({
                'success': False,
                'message': 'Paiement escrow non disponible'
            })
        
        # Check buyer wallet balance
        buyer_wallet = escrow.buyer.wallet
        total_amount = escrow.amount + escrow.fee_amount
        
        if buyer_wallet.available_balance < total_amount:
            return JsonResponse({
                'success': False,
                'message': 'Solde insuffisant'
            })
        
        with transaction.atomic():
            # Deduct funds from buyer
            buyer_wallet.deduct_funds(
                escrow.amount,
                f"Paiement escrow - Commande {escrow.order.id}"
            )
            buyer_wallet.deduct_funds(
                escrow.fee_amount,
                f"Frais escrow - Commande {escrow.order.id}"
            )
            
            # Update escrow status
            escrow.status = 'FUNDED'
            escrow.funded_at = timezone.now()
            escrow.save()
            
            # Update order status
            escrow.order.status = 'PAID'
            escrow.order.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Paiement escrow financé avec succès'
        })
        
    except Exception as e:
        logger.error(f"Error funding escrow payment: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors du financement'
        })

@login_required
@require_POST
def release_escrow_payment(request, escrow_id):
    """Release escrow payment to seller"""
    
    try:
        escrow = get_object_or_404(EscrowPayment, id=escrow_id)
        
        # Check if user is the buyer
        if escrow.buyer != request.user:
            return JsonResponse({
                'success': False,
                'message': 'Accès non autorisé'
            })
        
        # Check if escrow is funded
        if escrow.status != 'FUNDED':
            return JsonResponse({
                'success': False,
                'message': 'Paiement escrow non financé'
            })
        
        with transaction.atomic():
            # Credit seller wallet
            seller_wallet = escrow.seller.wallet
            seller_wallet.add_funds(
                escrow.amount,
                f"Paiement escrow libéré - Commande {escrow.order.id}"
            )
            
            # Update escrow status
            escrow.status = 'RELEASED_TO_SELLER'
            escrow.released_at = timezone.now()
            escrow.save()
            
            # Update order status
            escrow.order.status = 'COMPLETED'
            escrow.order.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Paiement escrow libéré avec succès'
        })
        
    except Exception as e:
        logger.error(f"Error releasing escrow payment: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors de la libération'
        })

@login_required
@require_POST
def dispute_escrow_payment(request, escrow_id):
    """Dispute escrow payment"""
    
    try:
        escrow = get_object_or_404(EscrowPayment, id=escrow_id)
        
        # Check if user is buyer or seller
        if escrow.buyer != request.user and escrow.seller != request.user:
            return JsonResponse({
                'success': False,
                'message': 'Accès non autorisé'
            })
        
        dispute_reason = request.POST.get('dispute_reason', '')
        
        if not dispute_reason:
            return JsonResponse({
                'success': False,
                'message': 'Raison de litige requise'
            })
        
        # Update escrow status
        escrow.status = 'DISPUTED'
        escrow.dispute_reason = dispute_reason
        escrow.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Litige enregistré avec succès'
        })
        
    except Exception as e:
        logger.error(f"Error disputing escrow payment: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors de l\'enregistrement du litige'
        })

# ============= INSTALLMENT PLANS =============

@login_required
def installment_dashboard(request):
    """Installment plans dashboard"""
    
    user = request.user
    
    # Get installment plans
    installment_plans = InstallmentPlan.objects.filter(
        order__buyer=user
    ).order_by('-created_at')
    
    # Installment statistics
    installment_stats = {
        'total_plans': installment_plans.count(),
        'active_plans': installment_plans.filter(is_active=True).count(),
        'completed_plans': installment_plans.filter(is_active=False).count(),
    }
    
    # Payment statistics
    payment_stats = InstallmentPayment.objects.filter(
        plan__order__buyer=user
    ).aggregate(
        total_paid=Sum('amount', filter=Q(status='PAID')),
        total_pending=Sum('amount', filter=Q(status='PENDING')),
        total_overdue=Sum('amount', filter=Q(status='OVERDUE'))
    )
    
    # Recent payments
    recent_payments = InstallmentPayment.objects.filter(
        plan__order__buyer=user
    ).order_by('-created_at')[:10]
    
    context = {
        'installment_plans': installment_plans,
        'installment_stats': installment_stats,
        'payment_stats': payment_stats,
        'recent_payments': recent_payments,
    }
    
    return render(request, 'backend/advanced/installments/installment_dashboard.html', context)

@login_required
@require_POST
def create_installment_plan(request, order_id):
    """Create installment plan for order"""
    
    try:
        order = get_object_or_404(Order, id=order_id)
        
        # Check if user is the buyer
        if order.buyer != request.user:
            return JsonResponse({
                'success': False,
                'message': 'Accès non autorisé'
            })
        
        # Check if installment plan already exists
        if hasattr(order, 'installment_plan'):
            return JsonResponse({
                'success': False,
                'message': 'Plan de paiement déjà créé'
            })
        
        data = json.loads(request.body)
        number_of_installments = int(data.get('number_of_installments', 3))
        down_payment = Decimal(data.get('down_payment', '0'))
        
        # Validate installment plan
        if number_of_installments < 2 or number_of_installments > 12:
            return JsonResponse({
                'success': False,
                'message': 'Nombre d\'échéances invalide (2-12)'
            })
        
        if down_payment >= order.total_amount:
            return JsonResponse({
                'success': False,
                'message': 'Acompte trop élevé'
            })
        
        # Calculate installment amount
        remaining_amount = order.total_amount - down_payment
        installment_amount = remaining_amount / number_of_installments
        
        with transaction.atomic():
            # Create installment plan
            plan = InstallmentPlan.objects.create(
                order=order,
                total_amount=order.total_amount,
                down_payment=down_payment,
                number_of_installments=number_of_installments,
                installment_amount=installment_amount,
                interest_rate=Decimal('0.05')  # 5% interest
            )
            
            # Create installment payments
            for i in range(number_of_installments):
                due_date = timezone.now().date() + timedelta(days=30 * (i + 1))
                InstallmentPayment.objects.create(
                    plan=plan,
                    installment_number=i + 1,
                    amount=installment_amount,
                    due_date=due_date
                )
            
            # Process down payment if any
            if down_payment > 0:
                buyer_wallet = order.buyer.wallet
                if buyer_wallet.available_balance >= down_payment:
                    buyer_wallet.deduct_funds(
                        down_payment,
                        f"Acompte - Plan de paiement {plan.id}"
                    )
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'Solde insuffisant pour l\'acompte'
                    })
        
        return JsonResponse({
            'success': True,
            'message': 'Plan de paiement créé avec succès',
            'plan_id': str(plan.id)
        })
        
    except Exception as e:
        logger.error(f"Error creating installment plan: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors de la création du plan de paiement'
        })

@login_required
@require_POST
def pay_installment(request, payment_id):
    """Pay installment"""
    
    try:
        payment = get_object_or_404(InstallmentPayment, id=payment_id)
        
        # Check if user is the buyer
        if payment.plan.order.buyer != request.user:
            return JsonResponse({
                'success': False,
                'message': 'Accès non autorisé'
            })
        
        # Check if payment is pending
        if payment.status != 'PENDING':
            return JsonResponse({
                'success': False,
                'message': 'Paiement non disponible'
            })
        
        # Check buyer wallet balance
        buyer_wallet = payment.plan.order.buyer.wallet
        if buyer_wallet.available_balance < payment.amount:
            return JsonResponse({
                'success': False,
                'message': 'Solde insuffisant'
            })
        
        with transaction.atomic():
            # Deduct funds from buyer
            buyer_wallet.deduct_funds(
                payment.amount,
                f"Échéance {payment.installment_number} - Plan {payment.plan.id}"
            )
            
            # Update payment status
            payment.status = 'PAID'
            payment.paid_at = timezone.now()
            payment.payment_reference = f"PAY-{payment.id}"
            payment.save()
            
            # Check if all payments are completed
            remaining_payments = InstallmentPayment.objects.filter(
                plan=payment.plan,
                status='PENDING'
            ).count()
            
            if remaining_payments == 0:
                # Complete the plan
                payment.plan.is_active = False
                payment.plan.save()
                
                # Update order status
                payment.plan.order.status = 'COMPLETED'
                payment.plan.order.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Échéance payée avec succès'
        })
        
    except Exception as e:
        logger.error(f"Error paying installment: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors du paiement'
        })

# ============= ADVANCED COMMISSION SYSTEM =============

@login_required
def commission_dashboard(request):
    """Advanced commission dashboard"""
    
    user = request.user
    
    # Get commissions
    commissions = Commission.objects.filter(seller=user).order_by('-created_at')
    
    # Commission statistics
    commission_stats = commissions.aggregate(
        total_commission=Sum('commission_amount'),
        total_earned=Sum('seller_amount'),
        avg_commission_rate=Avg('commission_rate'),
        paid_commission=Sum('commission_amount', filter=Q(is_paid=True)),
        unpaid_commission=Sum('commission_amount', filter=Q(is_paid=False))
    )
    
    # Commission by type
    commission_by_type = commissions.values('commission_type').annotate(
        total_amount=Sum('commission_amount'),
        count=Count('id')
    )
    
    # Monthly commission trends
    monthly_commissions = commissions.values('created_at__year', 'created_at__month').annotate(
        total_commission=Sum('commission_amount'),
        total_earned=Sum('seller_amount')
    ).order_by('created_at__year', 'created_at__month')
    
    # Recent commissions
    recent_commissions = commissions[:10]
    
    context = {
        'commissions': recent_commissions,
        'commission_stats': commission_stats,
        'commission_by_type': commission_by_type,
        'monthly_commissions': list(monthly_commissions),
    }
    
    return render(request, 'backend/advanced/commissions/commission_dashboard.html', context)

@login_required
@require_POST
def request_commission_payout(request):
    """Request commission payout"""
    
    try:
        user = request.user
        
        # Get unpaid commissions
        unpaid_commissions = Commission.objects.filter(
            seller=user,
            is_paid=False
        )
        
        total_amount = unpaid_commissions.aggregate(
            total=Sum('commission_amount')
        )['total'] or Decimal('0.00')
        
        if total_amount < Decimal('5000'):  # Minimum 5000 FCFA
            return JsonResponse({
                'success': False,
                'message': 'Montant minimum requis: 5000 FCFA'
            })
        
        with transaction.atomic():
            # Create withdrawal request
            withdrawal = WithdrawalRequest.objects.create(
                user=user,
                amount=total_amount,
                withdrawal_method='MOBILE_MONEY',
                account_details={'reason': 'Commission payout'}
            )
            
            # Mark commissions as paid
            unpaid_commissions.update(
                is_paid=True,
                paid_at=timezone.now(),
                transaction=withdrawal
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Demande de paiement de commission créée',
            'withdrawal_id': str(withdrawal.id)
        })
        
    except Exception as e:
        logger.error(f"Error requesting commission payout: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors de la demande de paiement'
        })

# ============= BUSINESS INTELLIGENCE & ANALYTICS =============

@login_required
def business_intelligence_dashboard(request):
    """Business intelligence dashboard"""
    
    if not request.user.is_staff:
        messages.error(request, 'Accès non autorisé')
        return redirect('backend:home')
    
    # Date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Sales Analytics
    sales_data = Order.objects.filter(
        created_at__date__gte=start_date,
        status='COMPLETED'
    ).values('created_at__date').annotate(
        daily_sales=Sum('total_amount'),
        order_count=Count('id'),
        avg_order_value=Avg('total_amount')
    ).order_by('created_at__date')
    
    # Revenue Analytics
    revenue_stats = Order.objects.filter(
        status='COMPLETED'
    ).aggregate(
        total_revenue=Sum('total_amount'),
        total_orders=Count('id'),
        avg_order_value=Avg('total_amount'),
        monthly_revenue=Sum('total_amount', filter=Q(created_at__date__gte=start_date))
    )
    
    # Product Performance
    product_performance = Product.objects.annotate(
        total_sales=Sum('orders__total_amount', filter=Q(orders__status='COMPLETED')),
        order_count=Count('orders', filter=Q(orders__status='COMPLETED')),
        view_count=Count('behaviors', filter=Q(behaviors__action_type='VIEW'))
    ).filter(total_sales__gt=0).order_by('-total_sales')[:10]
    
    # Category Performance
    category_performance = Category.objects.annotate(
        total_sales=Sum('products__orders__total_amount', filter=Q(products__orders__status='COMPLETED')),
        product_count=Count('products'),
        order_count=Count('products__orders', filter=Q(products__orders__status='COMPLETED'))
    ).filter(total_sales__gt=0).order_by('-total_sales')
    
    # User Analytics
    user_stats = User.objects.aggregate(
        total_users=Count('id'),
        active_users=Count('id', filter=Q(last_login__date__gte=start_date)),
        new_users=Count('id', filter=Q(date_joined__date__gte=start_date))
    )
    
    # Top Sellers
    top_sellers = User.objects.annotate(
        total_sales=Sum('products__orders__total_amount', filter=Q(products__orders__status='COMPLETED')),
        order_count=Count('products__orders', filter=Q(products__orders__status='COMPLETED'))
    ).filter(total_sales__gt=0).order_by('-total_sales')[:10]
    
    # Top Buyers
    top_buyers = User.objects.annotate(
        total_spent=Sum('orders__total_amount', filter=Q(orders__status='COMPLETED')),
        order_count=Count('orders', filter=Q(orders__status='COMPLETED'))
    ).filter(total_spent__gt=0).order_by('-total_spent')[:10]
    
    # Commission Analytics
    commission_stats = Commission.objects.aggregate(
        total_commission=Sum('commission_amount'),
        total_paid=Sum('commission_amount', filter=Q(is_paid=True)),
        total_unpaid=Sum('commission_amount', filter=Q(is_paid=False))
    )
    
    context = {
        'sales_data': list(sales_data),
        'revenue_stats': revenue_stats,
        'product_performance': product_performance,
        'category_performance': category_performance,
        'user_stats': user_stats,
        'top_sellers': top_sellers,
        'top_buyers': top_buyers,
        'commission_stats': commission_stats,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'backend/advanced/analytics/business_intelligence.html', context)

@login_required
def generate_analytics_report(request):
    """Generate comprehensive analytics report"""
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        # Get report parameters
        report_type = request.GET.get('type', 'sales')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = timezone.now().date() - timedelta(days=30)
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()
        
        # Generate report based on type
        if report_type == 'sales':
            report_data = self.generate_sales_report(start_date, end_date)
        elif report_type == 'products':
            report_data = self.generate_product_report(start_date, end_date)
        elif report_type == 'users':
            report_data = self.generate_user_report(start_date, end_date)
        elif report_type == 'commissions':
            report_data = self.generate_commission_report(start_date, end_date)
        else:
            return JsonResponse({
                'success': False,
                'message': 'Type de rapport invalide'
            })
        
        return JsonResponse({
            'success': True,
            'report_data': report_data
        })
        
    except Exception as e:
        logger.error(f"Error generating analytics report: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors de la génération du rapport'
        })

def generate_sales_report(self, start_date, end_date):
    """Generate sales report"""
    
    # Daily sales
    daily_sales = Order.objects.filter(
        created_at__date__range=[start_date, end_date],
        status='COMPLETED'
    ).values('created_at__date').annotate(
        sales=Sum('total_amount'),
        orders=Count('id'),
        avg_order=Avg('total_amount')
    ).order_by('created_at__date')
    
    # Sales by category
    category_sales = Category.objects.filter(
        products__orders__created_at__date__range=[start_date, end_date],
        products__orders__status='COMPLETED'
    ).annotate(
        sales=Sum('products__orders__total_amount'),
        orders=Count('products__orders')
    ).values('name', 'sales', 'orders')
    
    # Sales by pickup point
    pickup_sales = PickupPoint.objects.filter(
        orders__created_at__date__range=[start_date, end_date],
        orders__status='COMPLETED'
    ).annotate(
        sales=Sum('orders__total_amount'),
        orders=Count('orders')
    ).values('name', 'sales', 'orders')
    
    return {
        'daily_sales': list(daily_sales),
        'category_sales': list(category_sales),
        'pickup_sales': list(pickup_sales),
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
    }

def generate_product_report(self, start_date, end_date):
    """Generate product performance report"""
    
    # Top performing products
    top_products = Product.objects.filter(
        orders__created_at__date__range=[start_date, end_date],
        orders__status='COMPLETED'
    ).annotate(
        sales=Sum('orders__total_amount'),
        orders=Count('orders'),
        views=Count('behaviors', filter=Q(behaviors__action_type='VIEW'))
    ).order_by('-sales')[:20]
    
    # Product categories performance
    category_performance = Category.objects.filter(
        products__orders__created_at__date__range=[start_date, end_date],
        products__orders__status='COMPLETED'
    ).annotate(
        sales=Sum('products__orders__total_amount'),
        products=Count('products'),
        orders=Count('products__orders')
    ).order_by('-sales')
    
    return {
        'top_products': list(top_products.values('title', 'sales', 'orders', 'views')),
        'category_performance': list(category_performance.values('name', 'sales', 'products', 'orders')),
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
    }

def generate_user_report(self, start_date, end_date):
    """Generate user analytics report"""
    
    # User registration trends
    registration_trends = User.objects.filter(
        date_joined__date__range=[start_date, end_date]
    ).values('date_joined__date').annotate(
        new_users=Count('id')
    ).order_by('date_joined__date')
    
    # Active users
    active_users = User.objects.filter(
        last_login__date__range=[start_date, end_date]
    ).count()
    
    # Top buyers
    top_buyers = User.objects.filter(
        orders__created_at__date__range=[start_date, end_date],
        orders__status='COMPLETED'
    ).annotate(
        spent=Sum('orders__total_amount'),
        orders=Count('orders')
    ).order_by('-spent')[:10]
    
    # Top sellers
    top_sellers = User.objects.filter(
        products__orders__created_at__date__range=[start_date, end_date],
        products__orders__status='COMPLETED'
    ).annotate(
        sales=Sum('products__orders__total_amount'),
        orders=Count('products__orders')
    ).order_by('-sales')[:10]
    
    return {
        'registration_trends': list(registration_trends),
        'active_users': active_users,
        'top_buyers': list(top_buyers.values('username', 'spent', 'orders')),
        'top_sellers': list(top_sellers.values('username', 'sales', 'orders')),
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
    }

def generate_commission_report(self, start_date, end_date):
    """Generate commission report"""
    
    # Commission trends
    commission_trends = Commission.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).values('created_at__date').annotate(
        commission=Sum('commission_amount'),
        paid=Sum('commission_amount', filter=Q(is_paid=True)),
        unpaid=Sum('commission_amount', filter=Q(is_paid=False))
    ).order_by('created_at__date')
    
    # Commission by type
    commission_by_type = Commission.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).values('commission_type').annotate(
        total=Sum('commission_amount'),
        count=Count('id')
    )
    
    # Top commission earners
    top_earners = Commission.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).values('seller__username').annotate(
        commission=Sum('commission_amount'),
        paid=Sum('commission_amount', filter=Q(is_paid=True))
    ).order_by('-commission')[:10]
    
    return {
        'commission_trends': list(commission_trends),
        'commission_by_type': list(commission_by_type),
        'top_earners': list(top_earners),
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
    }

# ============= ADVANCED SECURITY FEATURES =============

@login_required
@require_POST
def enable_2fa(request):
    """Enable two-factor authentication"""
    
    try:
        user = request.user
        
        # Generate 2FA secret
        import pyotp
        secret = pyotp.random_base32()
        
        # Save secret to user profile
        user.profile.two_fa_secret = secret
        user.profile.two_fa_enabled = True
        user.profile.save()
        
        # Generate QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="Vidé-Grenier Kamer"
        )
        
        return JsonResponse({
            'success': True,
            'message': '2FA activé avec succès',
            'secret': secret,
            'qr_code': provisioning_uri
        })
        
    except Exception as e:
        logger.error(f"Error enabling 2FA: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors de l\'activation de la 2FA'
        })

@login_required
@require_POST
def verify_2fa(request):
    """Verify 2FA token"""
    
    try:
        user = request.user
        token = request.POST.get('token')
        
        if not token:
            return JsonResponse({
                'success': False,
                'message': 'Token requis'
            })
        
        # Verify token
        import pyotp
        totp = pyotp.TOTP(user.profile.two_fa_secret)
        
        if totp.verify(token):
            return JsonResponse({
                'success': True,
                'message': 'Token vérifié avec succès'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Token invalide'
            })
        
    except Exception as e:
        logger.error(f"Error verifying 2FA: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors de la vérification'
        })

@login_required
def fraud_detection_dashboard(request):
    """Fraud detection dashboard"""
    
    if not request.user.is_staff:
        messages.error(request, 'Accès non autorisé')
        return redirect('backend:home')
    
    # Suspicious activities
    suspicious_orders = Order.objects.filter(
        total_amount__gt=100000  # Orders over 100,000 FCFA
    ).order_by('-created_at')[:20]
    
    # Multiple accounts from same IP
    from django.db.models import Count
    suspicious_ips = UserBehavior.objects.values('user__ip').annotate(
        user_count=Count('user', distinct=True)
    ).filter(user_count__gt=3)[:10]
    
    # Rapid transactions
    rapid_transactions = Order.objects.filter(
        created_at__gte=timezone.now() - timedelta(hours=1)
    ).values('buyer').annotate(
        transaction_count=Count('id')
    ).filter(transaction_count__gt=5)[:10]
    
    context = {
        'suspicious_orders': suspicious_orders,
        'suspicious_ips': suspicious_ips,
        'rapid_transactions': rapid_transactions,
    }
    
    return render(request, 'backend/advanced/security/fraud_detection.html', context)

# ============= API ENDPOINTS =============

@login_required
@require_POST
def advanced_analytics_data(request):
    """API endpoint for advanced analytics"""
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        data = json.loads(request.body)
        report_type = data.get('type')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = timezone.now().date() - timedelta(days=30)
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()
        
        # Generate report
        if report_type == 'sales':
            report_data = self.generate_sales_report(start_date, end_date)
        elif report_type == 'products':
            report_data = self.generate_product_report(start_date, end_date)
        elif report_type == 'users':
            report_data = self.generate_user_report(start_date, end_date)
        elif report_type == 'commissions':
            report_data = self.generate_commission_report(start_date, end_date)
        else:
            return JsonResponse({
                'success': False,
                'message': 'Type de rapport invalide'
            })
        
        return JsonResponse({
            'success': True,
            'data': report_data
        })
        
    except Exception as e:
        logger.error(f"Error generating analytics data: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors de la génération des données'
        }) 