# backend/views_visitor.py - ENHANCED VISITOR VIEWS FOR VGK
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, DetailView, View
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Avg, Sum, F
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages
from django.core.cache import cache
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

from .models import (
    User, Product, Category, Order, Payment, Review, 
    Chat, Message, Favorite, SearchHistory, Notification, 
    AdminStock, PickupPoint, ProductImage,
    GroupChat, GroupChatMessage, SearchAlert, SavedSearch,
    ProductAlert
)
from .models_visitor import (
    VisitorCart, VisitorCartItem, VisitorBehavior, VisitorPreference,
    VisitorFavorite, VisitorCompare, 
    ProductComment, ProductLike, ProductReport, WhatsAppRequest, QRReceipt,
    VisitorSession
)
from .models_advanced import ProductRecommendation
from .forms import (
    CustomSignupForm, CustomLoginForm, ProductForm, 
    OrderForm, ReviewForm, ChatMessageForm, ProfileForm,
    SearchForm, AdminStockForm, ContactForm,
    GroupChatForm, GroupChatMessageForm
)
from .utils import (
    send_sms_notification, send_email_notification, 
    process_payment, track_analytics, generate_pickup_code,
    get_client_ip
)

logger = logging.getLogger(__name__)

# ============= VISITOR PRODUCT LISTING =============

class VisitorProductListView(ListView):
    """Enhanced product list view for visitors with AI recommendations"""
    model = Product
    template_name = 'backend/visitor/products/list.html'
    context_object_name = 'products'
    paginate_by = 24
    
    def get_queryset(self):
        """Get filtered and sorted products"""
        queryset = Product.objects.filter(status='ACTIVE').select_related(
            'category', 'seller'
        ).prefetch_related('images')
        
        # Apply filters
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        city = self.request.GET.get('city')
        if city:
            queryset = queryset.filter(city=city)
        
        condition = self.request.GET.get('condition')
        if condition:
            queryset = queryset.filter(condition=condition)
        
        min_price = self.request.GET.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        
        max_price = self.request.GET.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Apply sorting
        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by in ['price', '-price', 'created_at', '-created_at', 'views_count', '-views_count']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get or create session
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        
        # Track behavior
        self._track_product_list_view(session_key)
        
        # Get AI recommendations
        recommendations = self._get_ai_recommendations(session_key)
        
        # Get categories for filter
        categories = Category.objects.filter(is_active=True).annotate(
            product_count=Count('products', filter=Q(products__status='ACTIVE'))
        )
        
        context.update({
            'categories': categories,
            'recommendations': recommendations,
            'current_filters': self.request.GET.dict(),
            'total_products': self.get_queryset().count(),
        })
        
        return context
    
    def _track_product_list_view(self, session_key):
        """Track visitor behavior for AI"""
        try:
            VisitorBehavior.objects.create(
                session_key=session_key,
                visitor_ip=get_client_ip(self.request),
                action_type='VIEW',
                metadata={
                    'page': 'product_list',
                    'filters': self.request.GET.dict(),
                    'user_agent': self.request.META.get('HTTP_USER_AGENT', '')
                }
            )
        except Exception as e:
            logger.error(f"Error tracking behavior: {e}")
    
    def _get_ai_recommendations(self, session_key, limit=6):
        """Get AI-powered product recommendations"""
        try:
            # Get recent recommendations
            recommendations = ProductRecommendation.objects.filter(
                session_key=session_key,
                expires_at__gt=timezone.now(),
                is_shown=False
            ).select_related('product', 'product__category').order_by('-confidence_score')[:limit]
            
            # Mark as shown
            for rec in recommendations:
                rec.is_shown = True
                rec.shown_at = timezone.now()
                rec.save()
            
            return recommendations
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []


class VisitorProductDetailView(DetailView):
    """Enhanced product detail view for visitors"""
    model = Product
    template_name = 'backend/visitor/products/visitor_detail.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        return Product.objects.filter(status='ACTIVE').select_related(
            'category', 'seller'
        ).prefetch_related('images')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        # Get or create session
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        
        # Track behavior
        self._track_product_view(session_key, product)
        
        # Get visitor cart
        visitor_cart = self._get_visitor_cart(session_key)
        
        # Get similar products
        similar_products = self._get_similar_products(product)
        
        # Get AI recommendations
        recommendations = self._get_ai_recommendations(session_key, product)
        
        # Get visitor interactions
        visitor_interactions = self._get_visitor_interactions(session_key, product)
        
        # Get comments
        comments = ProductComment.objects.filter(
            product=product, 
            is_approved=True
        ).order_by('-created_at')[:10]
        
        # Generate WhatsApp messages
        whatsapp_messages = self._generate_whatsapp_messages(product, visitor_cart)
        
        context.update({
            'visitor_cart': visitor_cart,
            'similar_products': similar_products,
            'recommendations': recommendations,
            'visitor_interactions': visitor_interactions,
            'comments': comments,
            'whatsapp_messages': whatsapp_messages,
            'delivery_cost': Decimal('2000'),
        })
        
        return context
    
    def _track_product_view(self, session_key, product):
        """Track product view behavior"""
        try:
            VisitorBehavior.objects.create(
                session_key=session_key,
                visitor_ip=get_client_ip(self.request),
                action_type='VIEW',
                product=product,
                category=product.category,
                metadata={
                    'page': 'product_detail',
                    'duration': 0,  # Will be updated by JavaScript
                    'user_agent': self.request.META.get('HTTP_USER_AGENT', '')
                }
            )
            
            # Increment product view count
            product.views_count = F('views_count') + 1
            product.save()
        except Exception as e:
            logger.error(f"Error tracking product view: {e}")
    
    def _get_visitor_cart(self, session_key):
        """Get or create visitor cart"""
        try:
            cart, created = VisitorCart.objects.get_or_create(
                session_key=session_key,
                defaults={
                    'visitor_ip': get_client_ip(self.request)
                }
            )
            return cart
        except Exception as e:
            logger.error(f"Error getting visitor cart: {e}")
            return None
    
    def _get_similar_products(self, product, limit=6):
        """Get similar products based on category and price range"""
        try:
            similar = Product.objects.filter(
                status='ACTIVE',
                category=product.category
            ).exclude(id=product.id)
            
            # Add price range filter
            price_range = product.price * Decimal('0.3')  # 30% range
            similar = similar.filter(
                price__range=(product.price - price_range, product.price + price_range)
            )
            
            return similar.select_related('category', 'seller').prefetch_related('images')[:limit]
        except Exception as e:
            logger.error(f"Error getting similar products: {e}")
            return []
    
    def _get_ai_recommendations(self, session_key, product, limit=4):
        """Get AI recommendations excluding current product"""
        try:
            recommendations = ProductRecommendation.objects.filter(
                session_key=session_key,
                product__status='ACTIVE'
            ).exclude(product=product).select_related(
                'product', 'product__category'
            ).order_by('-confidence_score')[:limit]
            
            return recommendations
        except Exception as e:
            logger.error(f"Error getting AI recommendations: {e}")
            return []
    
    def _get_visitor_interactions(self, session_key, product):
        """Get visitor's interactions with this product"""
        try:
            interactions = {
                'is_favorited': VisitorFavorite.objects.filter(
                    session_key=session_key, product=product
                ).exists(),
                'is_in_cart': VisitorCartItem.objects.filter(
                    cart__session_key=session_key, product=product
                ).exists(),
                'is_compared': VisitorCompare.objects.filter(
                    session_key=session_key, product=product
                ).exists(),
                'like_status': None,
            }
            
            # Get like status
            like_obj = ProductLike.objects.filter(
                session_key=session_key, product=product
            ).first()
            if like_obj:
                interactions['like_status'] = like_obj.like_type
            
            return interactions
        except Exception as e:
            logger.error(f"Error getting visitor interactions: {e}")
            return {}
    
    def _generate_whatsapp_messages(self, product, visitor_cart):
        """Generate WhatsApp messages for different scenarios"""
        admin_phone = '+237694638412'
        
        messages = {
            'single_product': self._generate_single_whatsapp_message(product),
            'cart_pickup': self._generate_cart_whatsapp_message(visitor_cart, 'PICKUP') if visitor_cart else None,
            'cart_negotiation': self._generate_cart_whatsapp_message(visitor_cart, 'NEGOTIATION') if visitor_cart else None,
        }
        
        return messages
    
    def _generate_single_whatsapp_message(self, product):
        """Generate WhatsApp message for single product"""
        message = f"""Bonjour, je suis intéressé par ce produit :

🛍️ {product.title}
💰 Prix : {product.price:,} FCFA
📍 Ville : {product.get_city_display()}
📝 État : {product.get_condition_display()}

Pouvez-vous me donner plus d'informations ?"""
        
        return {
            'text': message,
            'url': f"https://wa.me/{admin_phone}?text={urllib.parse.quote(message)}"
        }
    
    def _generate_cart_whatsapp_message(self, cart, request_type):
        """Generate WhatsApp message for cart"""
        if not cart or cart.is_empty:
            return None
        
        items_text = ""
        for item in cart.items.all():
            items_text += f"• {item.product.title} (Qté: {item.quantity}) - {item.total_price:,} FCFA\n"
        
        if request_type == 'PICKUP':
            message = f"""Bonjour, je souhaite récupérer les articles suivants :

🛒 Panier :
{items_text}
💰 Montant total : {cart.total_amount:,} FCFA

👤 Nom : {cart.visitor_name or 'À préciser'}
📱 Téléphone : {cart.visitor_phone or 'À préciser'}

Merci de me confirmer l'adresse de retrait."""
        else:  # NEGOTIATION
            message = f"""Bonjour, je suis intéressé par ces articles et je souhaite discuter du prix :

🛒 Articles :
{items_text}
💰 Montant total : {cart.total_amount:,} FCFA

👤 Nom : {cart.visitor_name or 'À préciser'}
📱 Téléphone : {cart.visitor_phone or 'À préciser'}

Je souhaite effectuer un retrait sur place et négocier le prix."""
        
        return {
            'text': message,
            'url': f"https://wa.me/{admin_phone}?text={urllib.parse.quote(message)}"
        }


# ============= VISITOR CART OPERATIONS =============

@require_POST
@csrf_exempt
def visitor_add_to_cart(request, product_id):
    """Add product to visitor cart with enhanced features"""
    try:
        product = get_object_or_404(Product, id=product_id, status='ACTIVE')
        
        # Get or create session
        if not request.session.session_key:
            request.session.create()
        
        session_key = request.session.session_key
        
        # Get or create visitor cart
        visitor_cart, created = VisitorCart.objects.get_or_create(
            session_key=session_key,
            defaults={
                'visitor_ip': get_client_ip(request)
            }
        )
        
        # Get quantity from request
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            quantity = 1
        
        # Add or update cart item
        cart_item, item_created = VisitorCartItem.objects.get_or_create(
            cart=visitor_cart,
            product=product,
            defaults={
                'quantity': quantity,
                'unit_price': product.price
            }
        )
        
        if not item_created:
            cart_item.quantity += quantity
            cart_item.save()
        
        # Track behavior
        try:
            VisitorBehavior.objects.create(
                session_key=session_key,
                visitor_ip=get_client_ip(request),
                action_type='CART_ADD',
                product=product,
                metadata={
                    'quantity': quantity,
                    'unit_price': float(product.price),
                    'total_price': float(cart_item.total_price)
                }
            )
        except Exception as e:
            logger.error(f"Error tracking cart add behavior: {e}")
        
        return JsonResponse({
            'success': True,
            'message': f'{product.title} ajouté au panier',
            'cart_items': visitor_cart.total_items,
            'cart_total': float(visitor_cart.total_amount),
            'item_total': float(cart_item.total_price)
        })
        
    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


@require_POST
@csrf_exempt
def visitor_update_cart_item(request, item_id):
    """Update visitor cart item quantity"""
    try:
        if not request.session.session_key:
            return JsonResponse({'success': False, 'message': 'Session non trouvée'})
        
        cart_item = get_object_or_404(
            VisitorCartItem,
            id=item_id,
            cart__session_key=request.session.session_key
        )
        
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity <= 0:
            cart_item.delete()
            message = 'Produit retiré du panier'
        else:
            cart_item.quantity = quantity
            cart_item.save()
            message = 'Quantité mise à jour'
        
        cart = cart_item.cart
        
        return JsonResponse({
            'success': True,
            'message': message,
            'cart_items': cart.total_items,
            'cart_total': float(cart.total_amount),
            'item_total': float(cart_item.total_price) if quantity > 0 else 0
        })
        
    except Exception as e:
        logger.error(f"Error updating cart item: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


@require_POST
@csrf_exempt
def visitor_remove_cart_item(request, item_id):
    """Remove item from visitor cart"""
    try:
        if not request.session.session_key:
            return JsonResponse({'success': False, 'message': 'Session non trouvée'})
        
        cart_item = get_object_or_404(
            VisitorCartItem,
            id=item_id,
            cart__session_key=request.session.session_key
        )
        
        product_title = cart_item.product.title
        cart = cart_item.cart
        
        cart_item.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'{product_title} retiré du panier',
            'cart_items': cart.total_items,
            'cart_total': float(cart.total_amount)
        })
        
    except Exception as e:
        logger.error(f"Error removing cart item: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


def visitor_cart_view(request):
    """Enhanced visitor cart view"""
    try:
        # Get or create session
        if not request.session.session_key:
            request.session.create()
        
        session_key = request.session.session_key
        
        # Get or create visitor cart
        try:
            visitor_cart = VisitorCart.objects.get(session_key=session_key)
        except VisitorCart.DoesNotExist:
            visitor_cart = VisitorCart.objects.create(
                session_key=session_key,
                visitor_ip=get_client_ip(request)
            )
        
        # Get pickup points
        pickup_points = PickupPoint.objects.filter(is_active=True)
        
        # Get AI recommendations for empty cart
        recommendations = []
        if visitor_cart.is_empty:
            recommendations = ProductRecommendation.objects.filter(
                session_key=session_key,
                expires_at__gt=timezone.now(),
                is_shown=False
            ).select_related('product', 'product__category').order_by('-confidence_score')[:6]
        
        context = {
            'visitor_cart': visitor_cart,
            'cart_items': visitor_cart.items.select_related('product', 'product__category').all(),
            'pickup_points': pickup_points,
            'recommendations': recommendations,
            'delivery_cost': Decimal('2000'),
        }
        
        return render(request, 'backend/visitor/cart/cart.html', context)
        
    except Exception as e:
        logger.error(f"Error in visitor cart view: {e}")
        messages.error(request, "Erreur lors du chargement du panier")
        return redirect('backend:visitor_product_list')


@require_http_methods(["GET"])
def visitor_cart_items(request):
    """Get visitor cart items as JSON"""
    try:
        if not request.session.session_key:
            return JsonResponse({'items': [], 'total': 0, 'count': 0})
        
        visitor_cart = get_object_or_404(VisitorCart, session_key=request.session.session_key)
        
        items = []
        for item in visitor_cart.items.select_related('product').all():
            items.append({
                'id': str(item.id),
                'product_id': str(item.product.id),
                'product_title': item.product.title,
                'product_slug': item.product.slug,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'total_price': float(item.total_price),
                'product_image': item.product.main_image.image.url if item.product.main_image else None,
            })
        
        return JsonResponse({
            'items': items,
            'total': float(visitor_cart.total_amount),
            'count': visitor_cart.total_items,
            'delivery_cost': float(visitor_cart.delivery_cost),
            'final_total': float(visitor_cart.final_total)
        })
        
    except Exception as e:
        logger.error(f"Error getting cart items: {e}")
        return JsonResponse({'items': [], 'total': 0, 'count': 0})


@require_http_methods(["GET"])
def visitor_cart_status(request):
    """Get visitor cart status for AJAX updates"""
    try:
        if not request.session.session_key:
            return JsonResponse({
                'has_cart': False,
                'item_count': 0,
                'total_amount': 0
            })
        
        visitor_cart = get_object_or_404(VisitorCart, session_key=request.session.session_key)
        
        return JsonResponse({
            'has_cart': True,
            'item_count': visitor_cart.total_items,
            'total_amount': float(visitor_cart.total_amount),
            'delivery_cost': float(visitor_cart.delivery_cost),
            'final_total': float(visitor_cart.final_total)
        })
        
    except Exception as e:
        logger.error(f"Error getting cart status: {e}")
        return JsonResponse({
            'has_cart': False,
            'item_count': 0,
            'total_amount': 0
        })


@require_POST
def visitor_cart_preview(request):
    """Get cart preview for widget"""
    try:
        if not request.session.session_key:
            return JsonResponse({
                'success': True,
                'cart_items': 0,
                'cart_total': 0,
                'items': []
            })
        
        visitor_cart = VisitorCart.objects.get(session_key=request.session.session_key)
        cart_items = visitor_cart.items.select_related('product').all()
        
        items_data = []
        for item in cart_items:
            items_data.append({
                'id': str(item.id),
                'product_id': str(item.product.id),
                'title': item.product.title,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'total_price': float(item.total_price),
                'image_url': item.product.main_image.image.url if item.product.main_image else None
            })
        
        return JsonResponse({
            'success': True,
            'cart_items': visitor_cart.total_items,
            'cart_total': float(visitor_cart.total_amount),
            'items': items_data
        })
        
    except VisitorCart.DoesNotExist:
        return JsonResponse({
            'success': True,
            'cart_items': 0,
            'cart_total': 0,
            'items': []
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })

@require_POST
def visitor_update_cart_info(request):
    """Update visitor cart information"""
    try:
        if not request.session.session_key:
            return JsonResponse({
                'success': False,
                'message': 'Session invalide'
            })
        
        visitor_cart = VisitorCart.objects.get(session_key=request.session.session_key)
        
        # Update cart information
        visitor_cart.visitor_name = request.POST.get('visitor_name', '')
        visitor_cart.visitor_email = request.POST.get('visitor_email', '')
        visitor_cart.visitor_phone = request.POST.get('visitor_phone', '')
        visitor_cart.delivery_method = request.POST.get('delivery_method', 'PICKUP')
        visitor_cart.delivery_address = request.POST.get('delivery_address', '')
        visitor_cart.whatsapp_preferred = request.POST.get('whatsapp_preferred') == 'on'
        visitor_cart.notes = request.POST.get('notes', '')
        visitor_cart.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Informations mises à jour'
        })
        
    except VisitorCart.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Panier non trouvé'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


# ============= VISITOR INTERACTIONS =============

@require_POST
@csrf_exempt
def visitor_toggle_favorite(request, product_id):
    """Toggle product favorite for visitor"""
    try:
        product = get_object_or_404(Product, id=product_id, status='ACTIVE')
        
        if not request.session.session_key:
            request.session.create()
        
        session_key = request.session.session_key
        
        # Check if already favorited
        favorite, created = VisitorFavorite.objects.get_or_create(
            session_key=session_key,
            product=product,
            defaults={
                'visitor_ip': get_client_ip(request)
            }
        )
        
        if not created:
            favorite.delete()
            is_favorited = False
            message = f'{product.title} retiré des favoris'
        else:
            is_favorited = True
            message = f'{product.title} ajouté aux favoris'
        
        # Track behavior
        try:
            VisitorBehavior.objects.create(
                session_key=session_key,
                visitor_ip=get_client_ip(request),
                action_type='FAVORITE' if is_favorited else 'UNFAVORITE',
                product=product,
                metadata={'is_favorited': is_favorited}
            )
        except Exception as e:
            logger.error(f"Error tracking favorite behavior: {e}")
        
        return JsonResponse({
            'success': True,
            'message': message,
            'is_favorited': is_favorited
        })
        
    except Exception as e:
        logger.error(f"Error toggling favorite: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


@require_POST
@csrf_exempt
def visitor_toggle_compare(request, product_id):
    """Toggle product comparison for visitor"""
    try:
        product = get_object_or_404(Product, id=product_id, status='ACTIVE')
        
        if not request.session.session_key:
            request.session.create()
        
        session_key = request.session.session_key
        
        # Check if already in compare list
        compare_item, created = VisitorCompare.objects.get_or_create(
            session_key=session_key,
            product=product,
            defaults={
                'visitor_ip': get_client_ip(request)
            }
        )
        
        if not created:
            compare_item.delete()
            is_compared = False
            message = f'{product.title} retiré de la comparaison'
        else:
            is_compared = True
            message = f'{product.title} ajouté à la comparaison'
        
        # Track behavior
        try:
            VisitorBehavior.objects.create(
                session_key=session_key,
                visitor_ip=get_client_ip(request),
                action_type='COMPARE' if is_compared else 'UNCOMPARE',
                product=product,
                metadata={'is_compared': is_compared}
            )
        except Exception as e:
            logger.error(f"Error tracking compare behavior: {e}")
        
        return JsonResponse({
            'success': True,
            'message': message,
            'is_compared': is_compared
        })
        
    except Exception as e:
        logger.error(f"Error toggling compare: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


@require_POST
@csrf_exempt
def visitor_toggle_like(request, product_id):
    """Toggle product like/dislike for visitor"""
    try:
        product = get_object_or_404(Product, id=product_id, status='ACTIVE')
        
        if not request.session.session_key:
            request.session.create()
        
        session_key = request.session.session_key
        
        like_type = request.POST.get('like_type', 'LIKE')
        if like_type not in ['LIKE', 'DISLIKE']:
            like_type = 'LIKE'
        
        # Check if already liked/disliked
        existing_like = ProductLike.objects.filter(
            session_key=session_key,
            product=product
        ).first()
        
        if existing_like:
            if existing_like.like_type == like_type:
                # Remove like/dislike
                existing_like.delete()
                is_liked = False
                message = f'Vote retiré pour {product.title}'
            else:
                # Change like type
                existing_like.like_type = like_type
                existing_like.save()
                is_liked = True
                message = f'{product.title} {like_type.lower()}é'
        else:
            # Create new like/dislike
            ProductLike.objects.create(
                session_key=session_key,
                visitor_ip=get_client_ip(request),
                product=product,
                like_type=like_type
            )
            is_liked = True
            message = f'{product.title} {like_type.lower()}é'
        
        # Track behavior
        try:
            VisitorBehavior.objects.create(
                session_key=session_key,
                visitor_ip=get_client_ip(request),
                action_type=like_type,
                product=product,
                metadata={'like_type': like_type, 'is_liked': is_liked}
            )
        except Exception as e:
            logger.error(f"Error tracking like behavior: {e}")
        
        return JsonResponse({
            'success': True,
            'message': message,
            'is_liked': is_liked,
            'like_type': like_type if is_liked else None
        })
        
    except Exception as e:
        logger.error(f"Error toggling like: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


@require_POST
@csrf_exempt
def visitor_add_comment(request, product_id):
    """Add comment to product for visitor"""
    try:
        product = get_object_or_404(Product, id=product_id, status='ACTIVE')
        
        if not request.session.session_key:
            request.session.create()
        
        session_key = request.session.session_key
        
        # Get comment data
        visitor_name = request.POST.get('visitor_name', '').strip()
        visitor_email = request.POST.get('visitor_email', '').strip()
        content = request.POST.get('content', '').strip()
        rating = request.POST.get('rating')
        
        # Validate required fields
        if not visitor_name or not content:
            return JsonResponse({
                'success': False,
                'message': 'Nom et commentaire requis'
            })
        
        if len(content) < 10:
            return JsonResponse({
                'success': False,
                'message': 'Le commentaire doit contenir au moins 10 caractères'
            })
        
        # Create comment
        comment = ProductComment.objects.create(
            product=product,
            visitor_name=visitor_name,
            visitor_email=visitor_email,
            visitor_ip=get_client_ip(request),
            session_key=session_key,
            content=content,
            rating=int(rating) if rating and rating.isdigit() else None
        )
        
        # Track behavior
        try:
            VisitorBehavior.objects.create(
                session_key=session_key,
                visitor_ip=get_client_ip(request),
                action_type='COMMENT',
                product=product,
                metadata={
                    'comment_id': str(comment.id),
                    'rating': comment.rating
                }
            )
        except Exception as e:
            logger.error(f"Error tracking comment behavior: {e}")
        
        return JsonResponse({
            'success': True,
            'message': 'Commentaire ajouté avec succès',
            'comment': {
                'id': str(comment.id),
                'visitor_name': comment.visitor_name,
                'content': comment.content,
                'rating': comment.rating,
                'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


@require_POST
@csrf_exempt
def visitor_report_product(request, product_id):
    """Report product for inappropriate content"""
    try:
        product = get_object_or_404(Product, id=product_id, status='ACTIVE')
        
        if not request.session.session_key:
            request.session.create()
        
        session_key = request.session.session_key
        
        # Get report data
        report_type = request.POST.get('report_type')
        description = request.POST.get('description', '').strip()
        reporter_name = request.POST.get('reporter_name', '').strip()
        reporter_email = request.POST.get('reporter_email', '').strip()
        
        # Validate required fields
        if not report_type or not description:
            return JsonResponse({
                'success': False,
                'message': 'Type de signalement et description requis'
            })
        
        if len(description) < 10:
            return JsonResponse({
                'success': False,
                'message': 'La description doit contenir au moins 10 caractères'
            })
        
        # Create report
        report = ProductReport.objects.create(
            product=product,
            reporter_ip=get_client_ip(request),
            reporter_email=reporter_email,
            reporter_name=reporter_name,
            session_key=session_key,
            report_type=report_type,
            description=description
        )
        
        # Track behavior
        try:
            VisitorBehavior.objects.create(
                session_key=session_key,
                visitor_ip=get_client_ip(request),
                action_type='REPORT',
                product=product,
                metadata={
                    'report_id': str(report.id),
                    'report_type': report_type
                }
            )
        except Exception as e:
            logger.error(f"Error tracking report behavior: {e}")
        
        return JsonResponse({
            'success': True,
            'message': 'Signalement envoyé avec succès'
        })
        
    except Exception as e:
        logger.error(f"Error reporting product: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


# ============= AI RECOMMENDATIONS =============

def ai_recommendations_view(request):
    """AI-powered product recommendations view"""
    try:
        if not request.session.session_key:
            request.session.create()
        
        session_key = request.session.session_key
        
        # Get AI recommendations
        recommendations = ProductRecommendation.objects.filter(
            session_key=session_key,
            expires_at__gt=timezone.now()
        ).select_related('product', 'product__category').order_by('-confidence_score')
        
        # Get visitor preferences
        try:
            preferences = VisitorPreference.objects.get(session_key=session_key)
        except VisitorPreference.DoesNotExist:
            preferences = None
        
        # Get trending products
        trending_products = Product.objects.filter(
            status='ACTIVE'
        ).order_by('-views_count', '-likes_count')[:12]
        
        context = {
            'recommendations': recommendations,
            'preferences': preferences,
            'trending_products': trending_products,
        }
        
        return render(request, 'backend/visitor/products/ai_recommendations.html', context)
        
    except Exception as e:
        logger.error(f"Error in AI recommendations view: {e}")
        messages.error(request, "Erreur lors du chargement des recommandations")
        return redirect('backend:visitor_product_list')


# ============= VISITOR FAVORITES AND COMPARE =============

def visitor_favorites_list(request):
    """Visitor favorites list view"""
    try:
        if not request.session.session_key:
            request.session.create()
        
        session_key = request.session.session_key
        
        favorites = VisitorFavorite.objects.filter(
            session_key=session_key
        ).select_related('product', 'product__category').order_by('-created_at')
        
        context = {
            'favorites': favorites,
        }
        
        return render(request, 'backend/visitor/favorites/favorites.html', context)
        
    except Exception as e:
        logger.error(f"Error in favorites list view: {e}")
        messages.error(request, "Erreur lors du chargement des favoris")
        return redirect('backend:visitor_product_list')


def visitor_compare_list(request):
    """Visitor compare list view"""
    try:
        if not request.session.session_key:
            request.session.create()
        
        session_key = request.session.session_key
        
        compare_items = VisitorCompare.objects.filter(
            session_key=session_key
        ).select_related('product', 'product__category').order_by('-created_at')
        
        context = {
            'compare_items': compare_items,
        }
        
        return render(request, 'backend/visitor/compare/compare.html', context)
        
    except Exception as e:
        logger.error(f"Error in compare list view: {e}")
        messages.error(request, "Erreur lors du chargement de la comparaison")
        return redirect('backend:visitor_product_list') 

@require_POST
def visitor_create_alert(request, product_id):
    """Create product alert for visitor"""
    try:
        product = get_object_or_404(Product, id=product_id, status='ACTIVE')
        
        # Get visitor information from form
        visitor_name = request.POST.get('visitor_name', '').strip()
        visitor_email = request.POST.get('visitor_email', '').strip()
        visitor_phone = request.POST.get('visitor_phone', '').strip()
        alert_type = request.POST.get('alert_type', 'PRICE_DROP')
        max_price = request.POST.get('max_price', '')
        
        if not visitor_name or not visitor_email:
            return JsonResponse({
                'success': False,
                'message': 'Nom et email requis'
            })
        
        # Create alert
        alert = ProductAlert.objects.create(
            product=product,
            visitor_name=visitor_name,
            visitor_email=visitor_email,
            visitor_phone=visitor_phone,
            alert_type=alert_type,
            max_price=Decimal(max_price) if max_price else None,
            visitor_ip=get_client_ip(request)
        )
        
        # Send confirmation email
        try:
            send_email_notification(
                to_email=visitor_email,
                subject="Alerte produit créée - Vidé-Grenier Kamer",
                template_name="emails/product_alert_created.html",
                context={
                    'visitor_name': visitor_name,
                    'product': product,
                    'alert': alert
                }
            )
        except Exception as e:
            logger.error(f"Error sending alert email: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': 'Alerte créée avec succès. Vous recevrez une notification par email.'
        })
        
    except Exception as e:
        logger.error(f"Error creating alert: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }) 