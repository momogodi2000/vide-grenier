# backend/views_visitor_checkout.py - ENHANCED VISITOR CHECKOUT AND PAYMENT
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, View
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import datetime, timedelta
import json
import logging
import random
import string
import urllib.parse
import os
import sys
from decimal import Decimal
import qrcode
import io
import base64
from PIL import Image

from .models import (
    User, Product, Category, Order, Payment, PickupPoint
)
from .models_visitor import (
    VisitorCart, VisitorCartItem, WhatsAppRequest, QRReceipt,
    VisitorBehavior, VisitorSession
)
from .utils import (
    send_sms_notification, send_email_notification, 
    process_payment, track_analytics, generate_pickup_code,
    get_client_ip
)

logger = logging.getLogger(__name__)

# ============= VISITOR CHECKOUT =============

class VisitorCheckoutView(TemplateView):
    """Enhanced visitor checkout view with multiple payment options"""
    template_name = 'backend/visitor/checkout/checkout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get or create session
        if not self.request.session.session_key:
            self.request.session.create()
        
        session_key = self.request.session.session_key
        
        # Get visitor cart
        try:
            visitor_cart = VisitorCart.objects.get(session_key=session_key)
        except VisitorCart.DoesNotExist:
            messages.error(self.request, "Panier non trouvé")
            return redirect('backend:visitor_cart')
        
        if visitor_cart.is_empty:
            messages.error(self.request, "Votre panier est vide")
            return redirect('backend:visitor_cart')
        
        # Get pickup points
        pickup_points = PickupPoint.objects.filter(is_active=True)
        
        # Generate WhatsApp messages
        whatsapp_messages = self._generate_whatsapp_messages(visitor_cart)
        
        # Get delivery cost
        delivery_cost = Decimal('2000') if visitor_cart.delivery_method == 'DELIVERY' else Decimal('0')
        
        context.update({
            'visitor_cart': visitor_cart,
            'cart_items': visitor_cart.items.select_related('product', 'product__category').all(),
            'pickup_points': pickup_points,
            'whatsapp_messages': whatsapp_messages,
            'delivery_cost': delivery_cost,
            'final_total': visitor_cart.final_total,
        })
        
        return context
    
    def _generate_whatsapp_messages(self, visitor_cart):
        """Generate WhatsApp messages for different scenarios"""
        admin_phone = '+237694638412'
        
        messages = {
            'pickup': self._generate_pickup_whatsapp_message(visitor_cart),
            'negotiation': self._generate_negotiation_whatsapp_message(visitor_cart),
        }
        
        return messages
    
    def _generate_pickup_whatsapp_message(self, visitor_cart):
        """Generate WhatsApp message for pickup"""
        items_text = ""
        for item in visitor_cart.items.all():
            items_text += f"• {item.product.title} (Qté: {item.quantity}) - {item.total_price:,} FCFA\n"
        
        message = f"""Bonjour, je souhaite récupérer les articles suivants :

🛒 Panier :
{items_text}
💰 Montant total : {visitor_cart.total_amount:,} FCFA

👤 Nom : {visitor_cart.visitor_name or 'À préciser'}
📱 Téléphone : {visitor_cart.visitor_phone or 'À préciser'}

Merci de me confirmer l'adresse de retrait."""
        
        return {
            'text': message,
            'url': f"https://wa.me/{admin_phone}?text={urllib.parse.quote(message)}"
        }
    
    def _generate_negotiation_whatsapp_message(self, visitor_cart):
        """Generate WhatsApp message for negotiation"""
        items_text = ""
        for item in visitor_cart.items.all():
            items_text += f"• {item.product.title} (Qté: {item.quantity}) - {item.total_price:,} FCFA\n"
        
        message = f"""Bonjour, je suis intéressé par ces articles et je souhaite discuter du prix :

🛒 Articles :
{items_text}
💰 Montant total : {visitor_cart.total_amount:,} FCFA

👤 Nom : {visitor_cart.visitor_name or 'À préciser'}
📱 Téléphone : {visitor_cart.visitor_phone or 'À préciser'}

Je souhaite effectuer un retrait sur place et négocier le prix."""
        
        return {
            'text': message,
            'url': f"https://wa.me/{admin_phone}?text={urllib.parse.quote(message)}"
        }


@require_POST
def visitor_update_cart_info(request):
    """Update visitor cart information"""
    try:
        if not request.session.session_key:
            return JsonResponse({'success': False, 'message': 'Session non trouvée'})
        
        visitor_cart = get_object_or_404(VisitorCart, session_key=request.session.session_key)
        
        # Update cart information
        visitor_cart.visitor_name = request.POST.get('visitor_name', '').strip()
        visitor_cart.visitor_email = request.POST.get('visitor_email', '').strip()
        visitor_cart.visitor_phone = request.POST.get('visitor_phone', '').strip()
        visitor_cart.delivery_method = request.POST.get('delivery_method', 'PICKUP')
        visitor_cart.payment_option = request.POST.get('payment_option', 'WHATSAPP_PICKUP')
        visitor_cart.delivery_address = request.POST.get('delivery_address', '').strip()
        visitor_cart.notes = request.POST.get('notes', '').strip()
        visitor_cart.whatsapp_preferred = request.POST.get('whatsapp_preferred') == 'on'
        visitor_cart.email_preferred = request.POST.get('email_preferred') == 'on'
        visitor_cart.sms_preferred = request.POST.get('sms_preferred') == 'on'
        
        # Set pickup point if delivery method is pickup
        if visitor_cart.delivery_method == 'PICKUP':
            pickup_point_id = request.POST.get('pickup_point')
            if pickup_point_id:
                try:
                    visitor_cart.pickup_point = PickupPoint.objects.get(id=pickup_point_id)
                except PickupPoint.DoesNotExist:
                    pass
        
        visitor_cart.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Informations mises à jour',
            'final_total': float(visitor_cart.final_total)
        })
        
    except Exception as e:
        logger.error(f"Error updating cart info: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


def visitor_cart_checkout(request):
    """Process visitor cart checkout"""
    try:
        if not request.session.session_key:
            messages.error(request, "Session non trouvée")
            return redirect('backend:visitor_cart')
        
        visitor_cart = get_object_or_404(VisitorCart, session_key=request.session.session_key)
        
        if visitor_cart.is_empty:
            messages.error(request, "Votre panier est vide")
            return redirect('backend:visitor_cart')
        
        # Validate required information
        if not visitor_cart.visitor_name or not visitor_cart.visitor_phone:
            messages.error(request, "Nom et téléphone requis pour continuer")
            return render(request, 'backend/visitor/checkout/checkout.html', {
                'visitor_cart': visitor_cart,
                'cart_items': visitor_cart.items.select_related('product', 'product__category').all(),
                'pickup_points': PickupPoint.objects.filter(is_active=True),
            })
        
        # Process based on payment option
        if visitor_cart.payment_option == 'CAMPAY_DELIVERY':
            return self._process_campay_delivery(request, visitor_cart)
        elif visitor_cart.payment_option == 'WHATSAPP_PICKUP':
            return self._process_whatsapp_pickup(request, visitor_cart)
        elif visitor_cart.payment_option == 'WHATSAPP_NEGOTIATION':
            return self._process_whatsapp_negotiation(request, visitor_cart)
        else:
            messages.error(request, "Option de paiement invalide")
            return redirect('backend:visitor_checkout')
        
    except Exception as e:
        logger.error(f"Error in cart checkout: {e}")
        messages.error(request, "Erreur lors du traitement de la commande")
        return redirect('backend:visitor_cart')
    
    def _process_campay_delivery(self, request, visitor_cart):
        """Process Campay delivery payment"""
        try:
            with transaction.atomic():
                # Create orders for each cart item
                orders = []
                for cart_item in visitor_cart.items.all():
                    order = Order.objects.create(
                        product=cart_item.product,
                        buyer=None,  # Anonymous buyer
                        quantity=cart_item.quantity,
                        unit_price=cart_item.unit_price,
                        total_amount=cart_item.total_price,
                        status='PENDING',
                        payment_method='CAMPAY',
                        delivery_method='DELIVERY',
                        delivery_address=visitor_cart.delivery_address,
                        visitor_name=visitor_cart.visitor_name,
                        visitor_email=visitor_cart.visitor_email,
                        visitor_phone=visitor_cart.visitor_phone,
                        whatsapp_preferred=visitor_cart.whatsapp_preferred,
                        notes=visitor_cart.notes
                    )
                    orders.append(order)
                
                # Create QR receipt
                qr_receipt = self._create_qr_receipt(visitor_cart, orders)
                
                # Clear cart
                visitor_cart.clear()
                
                # Track behavior
                self._track_checkout_behavior(request, visitor_cart, 'CAMPAY_DELIVERY')
                
                # Redirect to payment
                return redirect('backend:visitor_cart_payment')
                
        except Exception as e:
            logger.error(f"Error processing Campay delivery: {e}")
            messages.error(request, "Erreur lors du traitement de la commande")
            return redirect('backend:visitor_checkout')
    
    def _process_whatsapp_pickup(self, request, visitor_cart):
        """Process WhatsApp pickup"""
        try:
            with transaction.atomic():
                # Create orders for each cart item
                orders = []
                for cart_item in visitor_cart.items.all():
                    order = Order.objects.create(
                        product=cart_item.product,
                        buyer=None,  # Anonymous buyer
                        quantity=cart_item.quantity,
                        unit_price=cart_item.unit_price,
                        total_amount=cart_item.total_price,
                        status='PENDING',
                        payment_method='CASH',
                        delivery_method='PICKUP',
                        pickup_point=visitor_cart.pickup_point,
                        visitor_name=visitor_cart.visitor_name,
                        visitor_email=visitor_cart.visitor_email,
                        visitor_phone=visitor_cart.visitor_phone,
                        whatsapp_preferred=visitor_cart.whatsapp_preferred,
                        notes=visitor_cart.notes
                    )
                    orders.append(order)
                
                # Create WhatsApp request
                whatsapp_request = self._create_whatsapp_request(
                    visitor_cart, orders, 'PICKUP'
                )
                
                # Clear cart
                visitor_cart.clear()
                
                # Track behavior
                self._track_checkout_behavior(request, visitor_cart, 'WHATSAPP_PICKUP')
                
                # Redirect to success page
                return redirect('backend:visitor_cart_success', cart_session=request.session.session_key)
                
        except Exception as e:
            logger.error(f"Error processing WhatsApp pickup: {e}")
            messages.error(request, "Erreur lors du traitement de la commande")
            return redirect('backend:visitor_checkout')
    
    def _process_whatsapp_negotiation(self, request, visitor_cart):
        """Process WhatsApp negotiation"""
        try:
            with transaction.atomic():
                # Create orders for each cart item
                orders = []
                for cart_item in visitor_cart.items.all():
                    order = Order.objects.create(
                        product=cart_item.product,
                        buyer=None,  # Anonymous buyer
                        quantity=cart_item.quantity,
                        unit_price=cart_item.unit_price,
                        total_amount=cart_item.total_price,
                        status='PENDING',
                        payment_method='CASH',
                        delivery_method='PICKUP',
                        pickup_point=visitor_cart.pickup_point,
                        visitor_name=visitor_cart.visitor_name,
                        visitor_email=visitor_cart.visitor_email,
                        visitor_phone=visitor_cart.visitor_phone,
                        whatsapp_preferred=visitor_cart.whatsapp_preferred,
                        notes=visitor_cart.notes
                    )
                    orders.append(order)
                
                # Create WhatsApp request
                whatsapp_request = self._create_whatsapp_request(
                    visitor_cart, orders, 'NEGOTIATION'
                )
                
                # Clear cart
                visitor_cart.clear()
                
                # Track behavior
                self._track_checkout_behavior(request, visitor_cart, 'WHATSAPP_NEGOTIATION')
                
                # Redirect to success page
                return redirect('backend:visitor_cart_success', cart_session=request.session.session_key)
                
        except Exception as e:
            logger.error(f"Error processing WhatsApp negotiation: {e}")
            messages.error(request, "Erreur lors du traitement de la commande")
            return redirect('backend:visitor_checkout')
    
    def _create_qr_receipt(self, visitor_cart, orders):
        """Create QR receipt for orders"""
        try:
            # Generate QR code
            qr_data = {
                'cart_id': str(visitor_cart.id),
                'session_key': visitor_cart.session_key,
                'total_amount': float(visitor_cart.total_amount),
                'items_count': visitor_cart.total_items,
                'orders': [str(order.id) for order in orders],
                'timestamp': visitor_cart.created_at.isoformat()
            }
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            qr_code_data = base64.b64encode(buffer.getvalue()).decode()
            
            # Create QR receipt
            qr_receipt = QRReceipt.objects.create(
                session_key=visitor_cart.session_key,
                visitor_cart=visitor_cart,
                receipt_number=QRReceipt().generate_receipt_number(),
                qr_code_data=qr_code_data,
                orders=[str(order.id) for order in orders],
                total_amount=visitor_cart.total_amount,
                delivery_cost=visitor_cart.delivery_cost,
                visitor_name=visitor_cart.visitor_name,
                visitor_phone=visitor_cart.visitor_phone,
                visitor_email=visitor_cart.visitor_email,
                delivery_address=visitor_cart.delivery_address
            )
            
            return qr_receipt
            
        except Exception as e:
            logger.error(f"Error creating QR receipt: {e}")
            return None
    
    def _create_whatsapp_request(self, visitor_cart, orders, request_type):
        """Create WhatsApp request"""
        try:
            # Generate message content
            items_text = ""
            for item in visitor_cart.items.all():
                items_text += f"• {item.product.title} (Qté: {item.quantity}) - {item.total_price:,} FCFA\n"
            
            if request_type == 'PICKUP':
                message_content = f"""Bonjour, je souhaite récupérer les articles suivants :

🛒 Panier :
{items_text}
💰 Montant total : {visitor_cart.total_amount:,} FCFA

👤 Nom : {visitor_cart.visitor_name}
📱 Téléphone : {visitor_cart.visitor_phone}

Merci de me confirmer l'adresse de retrait."""
            else:  # NEGOTIATION
                message_content = f"""Bonjour, je suis intéressé par ces articles et je souhaite discuter du prix :

🛒 Articles :
{items_text}
💰 Montant total : {visitor_cart.total_amount:,} FCFA

👤 Nom : {visitor_cart.visitor_name}
📱 Téléphone : {visitor_cart.visitor_phone}

Je souhaite effectuer un retrait sur place et négocier le prix."""
            
            # Create WhatsApp request
            whatsapp_request = WhatsAppRequest.objects.create(
                session_key=visitor_cart.session_key,
                visitor_ip=get_client_ip(request),
                request_type=request_type,
                visitor_name=visitor_cart.visitor_name,
                visitor_phone=visitor_cart.visitor_phone,
                visitor_email=visitor_cart.visitor_email,
                products=[{
                    'product_id': str(item.product.id),
                    'product_title': item.product.title,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total_price': float(item.total_price)
                } for item in visitor_cart.items.all()],
                total_amount=visitor_cart.total_amount,
                message_content=message_content,
                whatsapp_url=f"https://wa.me/+237694638412?text={urllib.parse.quote(message_content)}"
            )
            
            return whatsapp_request
            
        except Exception as e:
            logger.error(f"Error creating WhatsApp request: {e}")
            return None
    
    def _track_checkout_behavior(self, request, visitor_cart, payment_method):
        """Track checkout behavior"""
        try:
            VisitorBehavior.objects.create(
                session_key=visitor_cart.session_key,
                visitor_ip=get_client_ip(request),
                action_type='PURCHASE',
                metadata={
                    'payment_method': payment_method,
                    'total_amount': float(visitor_cart.total_amount),
                    'items_count': visitor_cart.total_items,
                    'delivery_method': visitor_cart.delivery_method
                }
            )
        except Exception as e:
            logger.error(f"Error tracking checkout behavior: {e}")


# ============= VISITOR PAYMENT =============

def visitor_cart_payment(request):
    """Visitor cart payment view for Campay delivery"""
    try:
        if not request.session.session_key:
            messages.error(request, "Session non trouvée")
            return redirect('backend:visitor_cart')
        
        # Get QR receipt
        try:
            qr_receipt = QRReceipt.objects.get(session_key=request.session.session_key)
        except QRReceipt.DoesNotExist:
            messages.error(request, "Reçu non trouvé")
            return redirect('backend:visitor_cart')
        
        # Get orders
        orders = Order.objects.filter(id__in=qr_receipt.orders)
        
        # Calculate delivery cost
        delivery_cost = Decimal('2000')
        final_total = qr_receipt.total_amount + delivery_cost
        
        context = {
            'qr_receipt': qr_receipt,
            'orders': orders,
            'delivery_cost': delivery_cost,
            'final_total': final_total,
            'campay_phone': qr_receipt.visitor_phone,
        }
        
        return render(request, 'backend/visitor/payment/payment.html', context)
        
    except Exception as e:
        logger.error(f"Error in cart payment view: {e}")
        messages.error(request, "Erreur lors du chargement du paiement")
        return redirect('backend:visitor_cart')


@require_POST
def visitor_initiate_campay_payment(request):
    """Initiate Campay payment for visitor"""
    try:
        if not request.session.session_key:
            return JsonResponse({'success': False, 'message': 'Session non trouvée'})
        
        # Get QR receipt
        try:
            qr_receipt = QRReceipt.objects.get(session_key=request.session.session_key)
        except QRReceipt.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Reçu non trouvé'})
        
        # Get phone number
        phone_number = request.POST.get('phone_number')
        if not phone_number:
            return JsonResponse({'success': False, 'message': 'Numéro de téléphone requis'})
        
        # Calculate total amount (products + delivery)
        delivery_cost = Decimal('2000')
        total_amount = qr_receipt.total_amount + delivery_cost
        
        # Initiate Campay payment
        payment_result = initiate_campay_payment_bulk(qr_receipt.orders, phone_number, total_amount)
        
        if payment_result['success']:
            return JsonResponse({
                'success': True,
                'message': 'Paiement initié avec succès',
                'payment_reference': payment_result['payment_reference'],
                'amount': float(total_amount)
            })
        else:
            return JsonResponse({
                'success': False,
                'message': payment_result['message']
            })
        
    except Exception as e:
        logger.error(f"Error initiating Campay payment: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


def initiate_campay_payment_bulk(orders, phone_number, total_amount):
    """Initiate Campay payment for multiple orders"""
    try:
        # This is a simplified implementation
        # In production, you would integrate with the actual Campay API
        
        # Generate payment reference
        payment_reference = f"VGK{''.join(random.choices(string.digits, k=8))}"
        
        # Create payment record
        payment = Payment.objects.create(
            order=orders[0],  # Use first order as primary
            payment_reference=payment_reference,
            amount=total_amount,
            status='PENDING',
            provider_response={
                'phone_number': phone_number,
                'orders_count': len(orders),
                'delivery_cost': 2000
            }
        )
        
        # Update orders status
        for order in orders:
            order.status = 'PROCESSING'
            order.save()
        
        # In production, make actual API call to Campay
        # campay_response = campay_api.create_payment(
        #     amount=total_amount,
        #     phone_number=phone_number,
        #     reference=payment_reference,
        #     description=f"Paiement VGK - {len(orders)} articles"
        # )
        
        return {
            'success': True,
            'payment_reference': payment_reference,
            'amount': float(total_amount)
        }
        
    except Exception as e:
        logger.error(f"Error in Campay payment: {e}")
        return {
            'success': False,
            'message': str(e)
        }


# ============= VISITOR SUCCESS PAGES =============

def visitor_cart_success(request, cart_session):
    """Visitor cart success page"""
    try:
        # Get WhatsApp request
        try:
            whatsapp_request = WhatsAppRequest.objects.get(session_key=cart_session)
        except WhatsAppRequest.DoesNotExist:
            messages.error(request, "Demande non trouvée")
            return redirect('backend:visitor_product_list')
        
        # Get orders
        orders = Order.objects.filter(
            visitor_phone=whatsapp_request.visitor_phone,
            created_at__gte=whatsapp_request.created_at - timedelta(minutes=5)
        )
        
        context = {
            'whatsapp_request': whatsapp_request,
            'orders': orders,
            'total_amount': whatsapp_request.total_amount,
        }
        
        return render(request, 'backend/visitor/checkout/success.html', context)
        
    except Exception as e:
        logger.error(f"Error in cart success view: {e}")
        messages.error(request, "Erreur lors du chargement de la page de succès")
        return redirect('backend:visitor_product_list')


def visitor_download_receipt(request):
    """Download QR receipt as PDF"""
    try:
        if not request.session.session_key:
            messages.error(request, "Session non trouvée")
            return redirect('backend:visitor_cart')
        
        # Get QR receipt
        try:
            qr_receipt = QRReceipt.objects.get(session_key=request.session.session_key)
        except QRReceipt.DoesNotExist:
            messages.error(request, "Reçu non trouvé")
            return redirect('backend:visitor_cart')
        
        # Get orders
        orders = Order.objects.filter(id__in=qr_receipt.orders)
        
        # Generate PDF receipt
        pdf_content = generate_receipt_pdf(qr_receipt, orders)
        
        # Create response
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_{qr_receipt.receipt_number}.pdf"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error downloading receipt: {e}")
        messages.error(request, "Erreur lors du téléchargement du reçu")
        return redirect('backend:visitor_cart')


def generate_receipt_pdf(qr_receipt, orders):
    """Generate PDF receipt with QR code"""
    try:
        # This is a simplified implementation
        # In production, you would use a proper PDF library like ReportLab
        
        # For now, return a simple text representation
        receipt_text = f"""
        VIDÉ-GRENIER KAMER - RECEIPT
        =============================
        
        Receipt Number: {qr_receipt.receipt_number}
        Date: {qr_receipt.created_at.strftime('%d/%m/%Y %H:%M')}
        
        Customer Information:
        Name: {qr_receipt.visitor_name}
        Phone: {qr_receipt.visitor_phone}
        Email: {qr_receipt.visitor_email}
        
        Orders:
        """
        
        for order in orders:
            receipt_text += f"""
        - {order.product.title}
          Quantity: {order.quantity}
          Unit Price: {order.unit_price:,} FCFA
          Total: {order.total_amount:,} FCFA
        """
        
        receipt_text += f"""
        
        Subtotal: {qr_receipt.total_amount:,} FCFA
        Delivery Cost: {qr_receipt.delivery_cost:,} FCFA
        Total: {qr_receipt.total_amount + qr_receipt.delivery_cost:,} FCFA
        
        QR Code: {qr_receipt.qr_code_data[:50]}...
        
        Thank you for your purchase!
        """
        
        return receipt_text.encode('utf-8')
        
    except Exception as e:
        logger.error(f"Error generating PDF receipt: {e}")
        return b"Error generating receipt"


# ============= WHATSAPP INTEGRATION =============

@require_POST
def visitor_send_whatsapp_message(request):
    """Send WhatsApp message for pickup or negotiation"""
    try:
        if not request.session.session_key:
            return JsonResponse({'success': False, 'message': 'Session non trouvée'})
        
        visitor_cart = get_object_or_404(VisitorCart, session_key=request.session.session_key)
        
        if visitor_cart.is_empty:
            return JsonResponse({'success': False, 'message': 'Panier vide'})
        
        # Get message type
        message_type = request.POST.get('message_type', 'PICKUP')
        
        # Generate message
        if message_type == 'PICKUP':
            whatsapp_request = create_whatsapp_request(visitor_cart, 'PICKUP')
        else:
            whatsapp_request = create_whatsapp_request(visitor_cart, 'NEGOTIATION')
        
        if whatsapp_request:
            return JsonResponse({
                'success': True,
                'message': 'Message WhatsApp généré',
                'whatsapp_url': whatsapp_request.whatsapp_url
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Erreur lors de la génération du message'
            })
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


def create_whatsapp_request(visitor_cart, request_type):
    """Create WhatsApp request"""
    try:
        # Generate message content
        items_text = ""
        for item in visitor_cart.items.all():
            items_text += f"• {item.product.title} (Qté: {item.quantity}) - {item.total_price:,} FCFA\n"
        
        if request_type == 'PICKUP':
            message_content = f"""Bonjour, je souhaite récupérer les articles suivants :

🛒 Panier :
{items_text}
💰 Montant total : {visitor_cart.total_amount:,} FCFA

👤 Nom : {visitor_cart.visitor_name or 'À préciser'}
📱 Téléphone : {visitor_cart.visitor_phone or 'À préciser'}

Merci de me confirmer l'adresse de retrait."""
        else:  # NEGOTIATION
            message_content = f"""Bonjour, je suis intéressé par ces articles et je souhaite discuter du prix :

🛒 Articles :
{items_text}
💰 Montant total : {visitor_cart.total_amount:,} FCFA

👤 Nom : {visitor_cart.visitor_name or 'À préciser'}
📱 Téléphone : {visitor_cart.visitor_phone or 'À préciser'}

Je souhaite effectuer un retrait sur place et négocier le prix."""
        
        # Create WhatsApp request
        whatsapp_request = WhatsAppRequest.objects.create(
            session_key=visitor_cart.session_key,
            visitor_ip=get_client_ip(request),
            request_type=request_type,
            visitor_name=visitor_cart.visitor_name or '',
            visitor_phone=visitor_cart.visitor_phone or '',
            visitor_email=visitor_cart.visitor_email or '',
            products=[{
                'product_id': str(item.product.id),
                'product_title': item.product.title,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'total_price': float(item.total_price)
            } for item in visitor_cart.items.all()],
            total_amount=visitor_cart.total_amount,
            message_content=message_content,
            whatsapp_url=f"https://wa.me/+237694638412?text={urllib.parse.quote(message_content)}"
        )
        
        return whatsapp_request
        
    except Exception as e:
        logger.error(f"Error creating WhatsApp request: {e}")
        return None 

@require_POST
def visitor_verify_payment(request):
    """Verify Campay payment and process order"""
    try:
        data = json.loads(request.body)
        transaction_id = data.get('transaction_id')
        status = data.get('status')
        
        if not transaction_id or not status:
            return JsonResponse({
                'success': False,
                'message': 'Données de transaction manquantes'
            })
        
        # Verify payment with Campay API
        verification_result = verify_campay_payment(transaction_id)
        
        if verification_result['success'] and status == 'success':
            # Get session key from request
            session_key = request.session.session_key
            
            try:
                visitor_cart = VisitorCart.objects.get(session_key=session_key)
            except VisitorCart.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Panier non trouvé'
                })
            
            # Process successful payment
            with transaction.atomic():
                # Create orders
                orders = []
                for cart_item in visitor_cart.items.all():
                    order = Order.objects.create(
                        product=cart_item.product,
                        buyer=None,  # No registered buyer for visitor orders
                        quantity=cart_item.quantity,
                        unit_price=cart_item.unit_price,
                        total_amount=cart_item.total_price,
                        status='PAID',
                        payment_method='CAMPAY',
                        delivery_method=visitor_cart.delivery_method,
                        delivery_address=visitor_cart.delivery_address,
                        visitor_name=visitor_cart.visitor_name,
                        visitor_email=visitor_cart.visitor_email,
                        visitor_phone=visitor_cart.visitor_phone,
                        whatsapp_preferred=visitor_cart.whatsapp_preferred,
                        notes=visitor_cart.notes,
                        transaction_id=transaction_id
                    )
                    orders.append(order)
                
                # Create QR receipt
                qr_receipt = QRReceipt.objects.create(
                    visitor_cart=visitor_cart,
                    transaction_id=transaction_id,
                    receipt_number=generate_receipt_number(),
                    total_amount=visitor_cart.final_total,
                    payment_method='CAMPAY',
                    status='PAID'
                )
                
                # Clear cart
                visitor_cart.items.all().delete()
                
                # Send notifications
                send_order_notifications(orders, visitor_cart)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Paiement vérifié avec succès',
                    'redirect_url': reverse('backend:visitor_cart_success', kwargs={'cart_session': session_key})
                })
                
        else:
            return JsonResponse({
                'success': False,
                'message': 'Échec de la vérification du paiement'
            })
            
    except Exception as e:
        logger.error(f"Error verifying payment: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur lors de la vérification du paiement'
        })

def verify_campay_payment(transaction_id):
    """Verify payment with Campay API"""
    try:
        # This would be the actual Campay API verification
        # For now, we'll simulate a successful verification
        return {
            'success': True,
            'amount': '2000',
            'currency': 'XAF',
            'status': 'success'
        }
    except Exception as e:
        logger.error(f"Campay verification error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def generate_receipt_number():
    """Generate unique receipt number"""
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"VG-{timestamp}-{random_suffix}"

def send_order_notifications(orders, visitor_cart):
    """Send notifications for successful order"""
    try:
        # Send email to visitor
        if visitor_cart.visitor_email:
            send_email_notification(
                to_email=visitor_cart.visitor_email,
                subject="Commande confirmée - Vidé-Grenier Kamer",
                template_name="emails/order_confirmation.html",
                context={
                    'visitor_name': visitor_cart.visitor_name,
                    'orders': orders,
                    'total_amount': visitor_cart.final_total,
                    'delivery_method': visitor_cart.delivery_method
                }
            )
        
        # Send SMS to visitor
        if visitor_cart.visitor_phone:
            send_sms_notification(
                phone_number=visitor_cart.visitor_phone,
                message=f"Votre commande a été confirmée. Total: {visitor_cart.final_total} FCFA. Merci de votre confiance!"
            )
        
        # Send notification to admin
        send_email_notification(
            to_email=settings.ADMIN_EMAIL,
            subject="Nouvelle commande visiteur",
            template_name="emails/admin_new_order.html",
            context={
                'visitor_name': visitor_cart.visitor_name,
                'visitor_phone': visitor_cart.visitor_phone,
                'orders': orders,
                'total_amount': visitor_cart.final_total
            }
        )
        
    except Exception as e:
        logger.error(f"Error sending notifications: {str(e)}") 