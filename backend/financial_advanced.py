# backend/financial_advanced.py - ADVANCED FINANCIAL FEATURES FOR VGK
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, TemplateView, View
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum, Avg, F
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import json
import hashlib
import hmac
from datetime import datetime, timedelta
import requests
import logging

from .models import User, Product, Order, Payment
from .models_advanced import (
    EscrowPayment, InstallmentPlan, InstallmentPayment
)
from .smart_notifications import smart_notifications

logger = logging.getLogger(__name__)

# ============= ESCROW PAYMENT SYSTEM =============

class EscrowPaymentView(LoginRequiredMixin, TemplateView):
    """Escrow payment management"""
    template_name = 'backend/payments/escrow.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Escrow payments as buyer
        buyer_escrows = EscrowPayment.objects.filter(
            buyer=user
        ).select_related('order', 'seller').order_by('-created_at')
        
        # Escrow payments as seller
        seller_escrows = EscrowPayment.objects.filter(
            seller=user
        ).select_related('order', 'buyer').order_by('-created_at')
        
        context.update({
            'buyer_escrows': buyer_escrows,
            'seller_escrows': seller_escrows,
            'total_in_escrow': buyer_escrows.filter(status='FUNDED').aggregate(
                total=Sum('amount')
            )['total'] or 0
        })
        
        return context

@login_required
def create_escrow_payment(request):
    """Create escrow payment for order"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            
            order = get_object_or_404(
                Order,
                id=order_id,
                buyer=request.user,
                status='PENDING'
            )
            
            # Check if escrow already exists
            if hasattr(order, 'escrow_payment'):
                return JsonResponse({
                    'success': False,
                    'error': 'Escrow déjà créé pour cette commande'
                })
            
            # Calculate fees (2% of order amount)
            fee_rate = Decimal('0.02')
            fee_amount = order.total_amount * fee_rate
            
            # Create escrow payment
            escrow = EscrowPayment.objects.create(
                order=order,
                buyer=request.user,
                seller=order.product.seller,
                amount=order.total_amount,
                fee_amount=fee_amount,
                status='PENDING',
                release_date=timezone.now() + timedelta(days=7)  # Auto-release in 7 days
            )
            
            # Update order status
            order.payment_method = 'ESCROW'
            order.save()
            
            return JsonResponse({
                'success': True,
                'escrow_id': str(escrow.id),
                'total_amount': float(order.total_amount + fee_amount),
                'fee_amount': float(fee_amount),
                'message': 'Paiement sécurisé créé. Procédez au financement.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def fund_escrow(request):
    """Fund escrow payment"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            escrow_id = data.get('escrow_id')
            payment_method = data.get('payment_method')  # CAMPAY, ORANGE_MONEY, etc.
            
            escrow = get_object_or_404(
                EscrowPayment,
                id=escrow_id,
                buyer=request.user,
                status='PENDING'
            )
            
            # Process payment through chosen method
            payment_result = self._process_escrow_payment(
                escrow, payment_method, request.user
            )
            
            if payment_result['success']:
                # Update escrow status
                escrow.status = 'FUNDED'
                escrow.funded_at = timezone.now()
                escrow.save()
                
                # Update order status
                escrow.order.status = 'PAID'
                escrow.order.save()
                
                # Notify seller
                smart_notifications.trigger_notification(
                    template_name='escrow_funded',
                    user=escrow.seller,
                    context={
                        'order_number': escrow.order.order_number,
                        'amount': escrow.amount,
                        'product_name': escrow.order.product.title
                    }
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Paiement sécurisé financé avec succès'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': payment_result['error']
                })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def release_escrow(request):
    """Release escrow payment to seller"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            escrow_id = data.get('escrow_id')
            
            escrow = get_object_or_404(
                EscrowPayment,
                id=escrow_id,
                buyer=request.user,
                status='FUNDED'
            )
            
            # Release payment to seller
            escrow.status = 'RELEASED_TO_SELLER'
            escrow.released_at = timezone.now()
            escrow.save()
            
            # Update order status
            escrow.order.status = 'COMPLETED'
            escrow.order.save()
            
            # Process actual payment to seller
            self._transfer_to_seller(escrow)
            
            # Notify seller
            smart_notifications.trigger_notification(
                template_name='escrow_released',
                user=escrow.seller,
                context={
                    'amount': escrow.amount,
                    'order_number': escrow.order.order_number
                }
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Paiement libéré au vendeur'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def _process_escrow_payment(escrow, payment_method, user):
    """Process escrow payment through various methods"""
    try:
        total_amount = escrow.amount + escrow.fee_amount
        
        if payment_method == 'CAMPAY':
            return self._process_campay_payment(escrow, total_amount, user)
        elif payment_method == 'ORANGE_MONEY':
            return self._process_orange_money_payment(escrow, total_amount, user)
        elif payment_method == 'MTN_MONEY':
            return self._process_mtn_payment(escrow, total_amount, user)
        elif payment_method == 'CRYPTO':
            return self._process_crypto_payment(escrow, total_amount, user)
        else:
            return {'success': False, 'error': 'Méthode de paiement non supportée'}
    
    except Exception as e:
        logger.error(f"Error processing escrow payment: {e}")
        return {'success': False, 'error': str(e)}

def _transfer_to_seller(escrow):
    """Transfer escrow funds to seller"""
    try:
        # In a real implementation, this would trigger actual money transfer
        # For now, we'll just log it and update records
        
        logger.info(f"Transferring {escrow.amount} FCFA to seller {escrow.seller.id}")
        
        # Create payment record for seller
        Payment.objects.create(
            order=escrow.order,
            amount=escrow.amount,
            payment_method='ESCROW_RELEASE',
            status='COMPLETED',
            transaction_id=f"ESCROW_{escrow.id}",
            metadata={'escrow_id': str(escrow.id)}
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error transferring to seller: {e}")
        return False

# ============= INSTALLMENT PAYMENT SYSTEM =============

class InstallmentPlansView(LoginRequiredMixin, ListView):
    """Installment plans management"""
    model = InstallmentPlan
    template_name = 'backend/payments/installments.html'
    context_object_name = 'plans'
    
    def get_queryset(self):
        return InstallmentPlan.objects.filter(
            order__buyer=self.request.user
        ).select_related('order', 'order__product')

@login_required
def create_installment_plan(request):
    """Create installment payment plan"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            number_of_installments = int(data.get('installments', 3))
            down_payment_percentage = float(data.get('down_payment_percentage', 30))
            
            order = get_object_or_404(
                Order,
                id=order_id,
                buyer=request.user,
                status='PENDING'
            )
            
            # Check if installment plan already exists
            if hasattr(order, 'installment_plan'):
                return JsonResponse({
                    'success': False,
                    'error': 'Plan de paiement déjà créé pour cette commande'
                })
            
            # Calculate installment details
            total_amount = order.total_amount
            down_payment = total_amount * Decimal(down_payment_percentage / 100)
            remaining_amount = total_amount - down_payment
            
            # Interest rate based on number of installments
            interest_rates = {
                2: Decimal('5.0'),   # 5% for 2 installments
                3: Decimal('8.0'),   # 8% for 3 installments
                6: Decimal('12.0'),  # 12% for 6 installments
                12: Decimal('18.0')  # 18% for 12 installments
            }
            
            interest_rate = interest_rates.get(number_of_installments, Decimal('10.0'))
            interest_amount = remaining_amount * (interest_rate / 100)
            total_with_interest = remaining_amount + interest_amount
            installment_amount = total_with_interest / number_of_installments
            
            # Create installment plan
            plan = InstallmentPlan.objects.create(
                order=order,
                total_amount=total_amount,
                down_payment=down_payment,
                number_of_installments=number_of_installments,
                installment_amount=installment_amount,
                interest_rate=interest_rate
            )
            
            # Create individual installment payments
            start_date = timezone.now().date()
            for i in range(number_of_installments):
                due_date = start_date + timedelta(days=30 * (i + 1))
                
                InstallmentPayment.objects.create(
                    plan=plan,
                    installment_number=i + 1,
                    amount=installment_amount,
                    due_date=due_date
                )
            
            # Update order
            order.payment_method = 'INSTALLMENT'
            order.save()
            
            return JsonResponse({
                'success': True,
                'plan_id': str(plan.id),
                'down_payment': float(down_payment),
                'installment_amount': float(installment_amount),
                'total_interest': float(interest_amount),
                'message': 'Plan de paiement créé avec succès'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def pay_installment(request):
    """Pay a specific installment"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            installment_id = data.get('installment_id')
            payment_method = data.get('payment_method')
            
            installment = get_object_or_404(
                InstallmentPayment,
                id=installment_id,
                plan__order__buyer=request.user,
                status='PENDING'
            )
            
            # Process payment
            payment_result = self._process_installment_payment(
                installment, payment_method, request.user
            )
            
            if payment_result['success']:
                # Update installment status
                installment.status = 'PAID'
                installment.paid_at = timezone.now()
                installment.payment_reference = payment_result['transaction_id']
                installment.save()
                
                # Check if all installments are paid
                plan = installment.plan
                remaining_installments = plan.payments.filter(status='PENDING').count()
                
                if remaining_installments == 0:
                    # All installments paid, complete the order
                    plan.order.status = 'PAID'
                    plan.order.save()
                    
                    # Notify seller
                    smart_notifications.trigger_notification(
                        template_name='installment_plan_completed',
                        user=plan.order.product.seller,
                        context={
                            'order_number': plan.order.order_number,
                            'total_amount': plan.total_amount
                        }
                    )
                
                # Send payment confirmation
                smart_notifications.trigger_notification(
                    template_name='installment_paid',
                    user=request.user,
                    context={
                        'installment_number': installment.installment_number,
                        'amount': installment.amount,
                        'remaining_installments': remaining_installments
                    }
                )
                
                return JsonResponse({
                    'success': True,
                    'remaining_installments': remaining_installments,
                    'message': f'Versement {installment.installment_number} payé avec succès'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': payment_result['error']
                })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def _process_installment_payment(installment, payment_method, user):
    """Process installment payment"""
    try:
        # Similar to escrow payment processing
        if payment_method == 'CAMPAY':
            return self._process_campay_payment(installment, installment.amount, user)
        elif payment_method == 'ORANGE_MONEY':
            return self._process_orange_money_payment(installment, installment.amount, user)
        elif payment_method == 'MTN_MONEY':
            return self._process_mtn_payment(installment, installment.amount, user)
        else:
            return {'success': False, 'error': 'Méthode de paiement non supportée'}
    
    except Exception as e:
        logger.error(f"Error processing installment payment: {e}")
        return {'success': False, 'error': str(e)}

# ============= CRYPTOCURRENCY PAYMENTS =============

class CryptoPaymentView(LoginRequiredMixin, TemplateView):
    """Cryptocurrency payment interface"""
    template_name = 'backend/payments/crypto.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Supported cryptocurrencies
        context['supported_cryptos'] = [
            {
                'symbol': 'BTC',
                'name': 'Bitcoin',
                'network': 'Bitcoin',
                'icon': 'bitcoin'
            },
            {
                'symbol': 'ETH',
                'name': 'Ethereum',
                'network': 'Ethereum',
                'icon': 'ethereum'
            },
            {
                'symbol': 'USDT',
                'name': 'Tether',
                'network': 'Ethereum',
                'icon': 'tether'
            },
            {
                'symbol': 'USDC',
                'name': 'USD Coin',
                'network': 'Ethereum',
                'icon': 'usd-coin'
            }
        ]
        
        return context

@login_required
def create_crypto_payment(request):
    """Create cryptocurrency payment"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            crypto_currency = data.get('crypto_currency')  # BTC, ETH, USDT, etc.
            
            order = get_object_or_404(
                Order,
                id=order_id,
                buyer=request.user,
                status='PENDING'
            )
            
            # Get current crypto exchange rate
            crypto_rate = self._get_crypto_exchange_rate(crypto_currency, 'XAF')
            
            if not crypto_rate:
                return JsonResponse({
                    'success': False,
                    'error': 'Impossible d\'obtenir le taux de change crypto'
                })
            
            # Calculate crypto amount
            fcfa_amount = float(order.total_amount)
            crypto_amount = fcfa_amount / crypto_rate
            
            # Generate payment address (would be from crypto wallet service)
            payment_address = self._generate_crypto_address(crypto_currency)
            
            # Create payment record
            Payment.objects.create(
                order=order,
                amount=order.total_amount,
                payment_method=f'CRYPTO_{crypto_currency}',
                status='PENDING',
                metadata={
                    'crypto_currency': crypto_currency,
                    'crypto_amount': str(crypto_amount),
                    'crypto_rate': str(crypto_rate),
                    'payment_address': payment_address,
                    'expires_at': (timezone.now() + timedelta(minutes=30)).isoformat()
                }
            )
            
            # Update order
            order.payment_method = f'CRYPTO_{crypto_currency}'
            order.save()
            
            return JsonResponse({
                'success': True,
                'crypto_amount': crypto_amount,
                'payment_address': payment_address,
                'qr_code': self._generate_crypto_qr(payment_address, crypto_amount),
                'expires_in': 1800,  # 30 minutes
                'message': f'Envoyez {crypto_amount:.8f} {crypto_currency} à l\'adresse fournie'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def _get_crypto_exchange_rate(crypto_currency, fiat_currency):
    """Get crypto to fiat exchange rate"""
    try:
        # Example using CoinGecko API
        url = f'https://api.coingecko.com/api/v3/simple/price'
        params = {
            'ids': {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'USDT': 'tether',
                'USDC': 'usd-coin'
            }.get(crypto_currency, 'bitcoin'),
            'vs_currencies': 'xaf'  # West African CFA franc
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        coin_id = params['ids']
        return data.get(coin_id, {}).get('xaf')
        
    except Exception as e:
        logger.error(f"Error getting crypto exchange rate: {e}")
        return None

def _generate_crypto_address(crypto_currency):
    """Generate or retrieve crypto payment address"""
    # In a real implementation, this would interface with a crypto wallet service
    # For demo purposes, return a placeholder address
    
    placeholder_addresses = {
        'BTC': '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
        'ETH': '0x742d35Cc619C062cb4c1d96c5bcFB4bC', 
        'USDT': '0x742d35Cc619C062cb4c1d96c5bcFB4bC',
        'USDC': '0x742d35Cc619C062cb4c1d96c5bcFB4bC'
    }
    
    return placeholder_addresses.get(crypto_currency, '')

def _generate_crypto_qr(address, amount):
    """Generate QR code for crypto payment"""
    try:
        import qrcode
        import io
        import base64
        
        # Create payment URI
        payment_uri = f"{address}?amount={amount}"
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(payment_uri)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
        
    except Exception as e:
        logger.error(f"Error generating crypto QR: {e}")
        return None

# ============= SELLER FINANCIAL ANALYTICS =============

class SellerAnalyticsView(LoginRequiredMixin, TemplateView):
    """Advanced financial analytics for sellers"""
    template_name = 'backend/sellers/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Revenue analytics
        revenue_data = self._get_revenue_analytics(user)
        
        # Payment method analytics
        payment_analytics = self._get_payment_method_analytics(user)
        
        # Product performance
        product_performance = self._get_product_performance(user)
        
        # Financial projections
        projections = self._get_financial_projections(user)
        
        context.update({
            'revenue_data': revenue_data,
            'payment_analytics': payment_analytics,
            'product_performance': product_performance,
            'projections': projections
        })
        
        return context
    
    def _get_revenue_analytics(self, user):
        """Get comprehensive revenue analytics"""
        orders = Order.objects.filter(
            product__seller=user,
            status='DELIVERED'
        )
        
        # Monthly revenue
        monthly_revenue = orders.filter(
            delivered_at__gte=timezone.now() - timedelta(days=30)
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Annual revenue
        annual_revenue = orders.filter(
            delivered_at__gte=timezone.now() - timedelta(days=365)
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Average order value
        avg_order_value = orders.aggregate(avg=Avg('total_amount'))['avg'] or 0
        
        # Commission paid
        total_commission = orders.aggregate(
            total=Sum('commission_amount')
        )['total'] or 0
        
        return {
            'monthly_revenue': monthly_revenue,
            'annual_revenue': annual_revenue,
            'avg_order_value': avg_order_value,
            'total_commission': total_commission,
            'net_revenue': annual_revenue - total_commission
        }
    
    def _get_payment_method_analytics(self, user):
        """Get payment method analytics"""
        orders = Order.objects.filter(
            product__seller=user,
            status='DELIVERED'
        )
        
        payment_breakdown = orders.values('payment_method').annotate(
            count=Count('id'),
            total_amount=Sum('total_amount')
        ).order_by('-total_amount')
        
        return payment_breakdown
    
    def _get_product_performance(self, user):
        """Get product performance analytics"""
        products = Product.objects.filter(seller=user).annotate(
            total_revenue=Sum('order__total_amount'),
            total_orders=Count('order'),
            avg_rating=Avg('enhanced_reviews__overall_rating')
        ).order_by('-total_revenue')[:10]
        
        return products
    
    def _get_financial_projections(self, user):
        """Get financial projections based on trends"""
        # Last 6 months data
        months_data = []
        for i in range(6):
            month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            monthly_orders = Order.objects.filter(
                product__seller=user,
                status='DELIVERED',
                delivered_at__gte=month_start,
                delivered_at__lt=month_end
            )
            
            revenue = monthly_orders.aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            
            months_data.append({
                'month': month_start.strftime('%Y-%m'),
                'revenue': float(revenue),
                'orders': monthly_orders.count()
            })
        
        # Calculate trend
        if len(months_data) >= 3:
            recent_avg = sum(m['revenue'] for m in months_data[:3]) / 3
            older_avg = sum(m['revenue'] for m in months_data[3:]) / 3
            trend = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
        else:
            trend = 0
        
        return {
            'monthly_data': months_data,
            'trend_percentage': trend,
            'projected_monthly': recent_avg if len(months_data) >= 3 else 0
        }

# ============= PAYMENT METHOD IMPLEMENTATIONS =============

def _process_campay_payment(payment_obj, amount, user):
    """Process Campay payment"""
    try:
        # Implement Campay API integration
        # This is a placeholder implementation
        
        campay_api_url = "https://api.campay.net/api/v1/transactions"
        
        payload = {
            'amount': str(amount),
            'currency': 'XAF',
            'phone_number': user.phone,
            'description': f'VGK Payment - {payment_obj.id}',
            'external_reference': str(payment_obj.id)
        }
        
        headers = {
            'Authorization': f'Bearer {settings.CAMPAY_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(campay_api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'transaction_id': data.get('transaction_id'),
                'reference': data.get('reference')
            }
        else:
            return {
                'success': False,
                'error': 'Erreur de paiement Campay'
            }
    
    except Exception as e:
        logger.error(f"Campay payment error: {e}")
        return {'success': False, 'error': str(e)}

def _process_orange_money_payment(payment_obj, amount, user):
    """Process Orange Money payment"""
    try:
        # Implement Orange Money API integration
        # Placeholder implementation
        
        return {
            'success': True,
            'transaction_id': f'OM_{payment_obj.id}_{int(timezone.now().timestamp())}',
            'reference': f'OM_REF_{payment_obj.id}'
        }
    
    except Exception as e:
        logger.error(f"Orange Money payment error: {e}")
        return {'success': False, 'error': str(e)}

def _process_mtn_payment(payment_obj, amount, user):
    """Process MTN Mobile Money payment"""
    try:
        # Implement MTN Mobile Money API integration
        # Placeholder implementation
        
        return {
            'success': True,
            'transaction_id': f'MTN_{payment_obj.id}_{int(timezone.now().timestamp())}',
            'reference': f'MTN_REF_{payment_obj.id}'
        }
    
    except Exception as e:
        logger.error(f"MTN payment error: {e}")
        return {'success': False, 'error': str(e)}

def _process_crypto_payment(payment_obj, amount, user):
    """Process cryptocurrency payment"""
    try:
        # This would integrate with blockchain monitoring services
        # to detect incoming crypto payments
        
        return {
            'success': True,
            'transaction_id': f'CRYPTO_{payment_obj.id}',
            'reference': f'CRYPTO_REF_{payment_obj.id}'
        }
    
    except Exception as e:
        logger.error(f"Crypto payment error: {e}")
        return {'success': False, 'error': str(e)} 