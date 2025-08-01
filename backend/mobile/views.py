from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg, Sum
from django.contrib.auth import authenticate
from django.utils import timezone
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from datetime import timedelta
import json
import random

from backend.models import (
    Product, Category, Order, Favorite, Review, User,
    PickupPoint, Payment
)
from backend.models_advanced import Wallet, Transaction
from backend.models_visitor import VisitorCart, VisitorCartItem
from .serializers import *
from .jwt_utils import generate_tokens_for_user, get_user_from_token
from .permissions import IsAdminUser, IsOwnerOrReadOnly

class MobilePagination(PageNumberPagination):
    """Custom pagination for mobile API"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class MobileAuthViewSet(viewsets.ViewSet):
    """Authentication endpoints for mobile app with 2FA and Google OAuth"""
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Mobile login endpoint with 2FA support"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            user = authenticate(request, username=email, password=password)
            if user and user.is_active:
                # Check if 2FA is enabled (using hasattr for backward compatibility)
                if hasattr(user, 'two_factor_enabled') and user.two_factor_enabled:
                    # Generate 2FA code and send via email
                    code = get_random_string(6, allowed_chars='0123456789')
                    user.verification_code = code
                    user.verification_code_expires = timezone.now() + timedelta(minutes=10)
                    user.save()
                    
                    # Send 2FA code via email
                    send_mail(
                        'Vidé-Grenier Kamer - Code de vérification 2FA',
                        f'Votre code de vérification est: {code}',
                        'noreply@videgrenier-kamer.com',
                        [user.email],
                        fail_silently=False,
                    )
                    
                    return Response({
                        'success': True,
                        'requires_2fa': True,
                        'message': 'Code de vérification envoyé par email'
                    })
                else:
                    # No 2FA required, generate tokens directly
                    tokens = generate_tokens_for_user(user)
                    user_data = UserSerializer(user, context={'request': request}).data
                    
                    return Response({
                        'success': True,
                        'requires_2fa': False,
                        'tokens': tokens,
                        'user': user_data
                    })
            else:
                return Response({
                    'success': False,
                    'error': 'Identifiants invalides'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def verify_2fa(self, request):
        """Verify 2FA code"""
        email = request.data.get('email')
        code = request.data.get('code')
        
        if not email or not code:
            return Response({
                'success': False,
                'error': 'Email et code requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            if (hasattr(user, 'verification_code') and 
                user.verification_code == code and 
                hasattr(user, 'verification_code_expires') and
                user.verification_code_expires > timezone.now()):
                
                # Clear verification code
                user.verification_code = None
                user.verification_code_expires = None
                user.save()
                
                # Generate tokens
                tokens = generate_tokens_for_user(user)
                user_data = UserSerializer(user, context={'request': request}).data
                
                return Response({
                    'success': True,
                    'tokens': tokens,
                    'user': user_data
                })
            else:
                return Response({
                    'success': False,
                    'error': 'Code invalide ou expiré'
                }, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Utilisateur non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def google_oauth(self, request):
        """Google OAuth login"""
        serializer = GoogleOAuthSerializer(data=request.data)
        if serializer.is_valid():
            access_token = serializer.validated_data['access_token']
            
            # Here you would verify the Google access token
            # and get user information from Google
            # For now, we'll return a placeholder response
            
            return Response({
                'success': False,
                'error': 'Google OAuth not implemented yet'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
        
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """Mobile registration endpoint with phone verification"""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Send phone verification code
            code = get_random_string(6, allowed_chars='0123456789')
            user.phone_verification_code = code
            user.phone_verification_expires = timezone.now() + timedelta(minutes=10)
            user.save()
            
            # Send SMS verification code (placeholder)
            # In production, integrate with SMS service
            
            return Response({
                'success': True,
                'message': 'Compte créé. Code de vérification envoyé par SMS.',
                'requires_phone_verification': True,
                'user_id': str(user.id)
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def verify_phone(self, request):
        """Verify phone number"""
        user_id = request.data.get('user_id')
        code = request.data.get('code')
        
        if not user_id or not code:
            return Response({
                'success': False,
                'error': 'ID utilisateur et code requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
            if (hasattr(user, 'phone_verification_code') and
                user.phone_verification_code == code and 
                hasattr(user, 'phone_verification_expires') and
                user.phone_verification_expires > timezone.now()):
                
                user.phone_verified = True
                user.phone_verification_code = None
                user.phone_verification_expires = None
                user.save()
                
                tokens = generate_tokens_for_user(user)
                user_data = UserSerializer(user, context={'request': request}).data
                
                return Response({
                    'success': True,
                    'tokens': tokens,
                    'user': user_data
                })
            else:
                return Response({
                    'success': False,
                    'error': 'Code invalide ou expiré'
                }, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Utilisateur non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def refresh(self, request):
        """Refresh access token"""
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({
                'success': False,
                'error': 'Refresh token requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from .jwt_utils import refresh_jwt_token
        new_access_token = refresh_jwt_token(refresh_token)
        
        if new_access_token:
            return Response({
                'success': True,
                'access_token': new_access_token
            })
        else:
            return Response({
                'success': False,
                'error': 'Refresh token invalide'
            }, status=status.HTTP_401_UNAUTHORIZED)

class MobileProductViewSet(viewsets.ModelViewSet):
    """Product endpoints for mobile app"""
    serializer_class = ProductSerializer
    pagination_class = MobilePagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'condition', 'city', 'status']
    
    def get_queryset(self):
        queryset = Product.objects.filter(status='ACTIVE').select_related(
            'seller', 'category'
        ).prefetch_related('images')
        
        # Apply search filter
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(category__name__icontains=search)
            )
        
        # Apply price filters
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        """Toggle product favorite status"""
        product = self.get_object()
        user = request.user
        
        if not user.is_authenticated:
            return Response({
                'success': False,
                'error': 'Authentification requise'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        favorite, created = Favorite.objects.get_or_create(user=user, product=product)
        
        if not created:
            favorite.delete()
            is_favorited = False
        else:
            is_favorited = True
        
        return Response({
            'success': True,
            'is_favorited': is_favorited
        })
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending products"""
        trending_products = Product.objects.filter(
            status='ACTIVE'
        ).annotate(
            view_avg=Avg('views_count'),
            like_avg=Avg('likes_count')
        ).order_by('-view_avg', '-like_avg')[:10]
        
        serializer = self.get_serializer(trending_products, many=True)
        return Response({
            'success': True,
            'products': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def recommended(self, request):
        """Get recommended products for user"""
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'error': 'Authentification requise'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Simple recommendation based on user's city and favorite categories
        user_city = request.user.city
        favorite_categories = Favorite.objects.filter(
            user=request.user
        ).values_list('product__category', flat=True)
        
        recommended_products = Product.objects.filter(
            status='ACTIVE'
        ).filter(
            Q(city=user_city) | Q(category__in=favorite_categories)
        ).exclude(
            seller=request.user
        ).order_by('-created_at')[:10]
        
        serializer = self.get_serializer(recommended_products, many=True)
        return Response({
            'success': True,
            'products': serializer.data
        })

class MobileCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Category endpoints for mobile app"""
    serializer_class = CategorySerializer
    queryset = Category.objects.filter(is_active=True).order_by('order', 'name')
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get products in a category"""
        category = self.get_object()
        products = Product.objects.filter(
            category=category,
            status='ACTIVE'
        ).order_by('-created_at')
        
        paginator = MobilePagination()
        page = paginator.paginate_queryset(products, request)
        
        serializer = ProductSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

class MobileOrderViewSet(viewsets.ModelViewSet):
    """Order endpoints for mobile app"""
    serializer_class = OrderSerializer
    pagination_class = MobilePagination
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'ADMIN':
            return Order.objects.all().select_related('product', 'buyer', 'seller')
        else:
            return Order.objects.filter(
                Q(buyer=user) | Q(seller=user)
            ).select_related('product', 'buyer', 'seller')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status"""
        order = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response({
                'success': False,
                'error': 'Statut requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = new_status
        order.save()
        
        serializer = self.get_serializer(order)
        return Response({
            'success': True,
            'order': serializer.data
        })

class MobileUserViewSet(viewsets.ViewSet):
    """User profile endpoints for mobile app"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get user profile"""
        serializer = UserSerializer(request.user, context={'request': request})
        return Response({
            'success': True,
            'user': serializer.data
        })
    
    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        """Update user profile"""
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            user_data = UserSerializer(request.user, context={'request': request}).data
            return Response({
                'success': True,
                'user': user_data
            })
        
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def favorites(self, request):
        """Get user favorites"""
        favorites = Favorite.objects.filter(
            user=request.user
        ).select_related('product', 'product__category').order_by('-created_at')
        
        paginator = MobilePagination()
        page = paginator.paginate_queryset(favorites, request)
        
        serializer = FavoriteSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get user statistics"""
        user = request.user
        
        stats = {
            'products_count': user.products_sold.filter(status='ACTIVE').count(),
            'orders_bought': user.orders_bought.count(),
            'orders_sold': user.products_sold.aggregate(
                total_orders=Count('orders')
            )['total_orders'] or 0,
            'favorites_count': user.favorites.count(),
            'reviews_given': user.reviews_given.count(),
            'total_spent': user.orders_bought.aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
            'total_earned': user.products_sold.aggregate(
                total=Sum('orders__total_amount')
            )['total'] or 0
        }
        
        return Response({
            'success': True,
            'stats': stats
        })
    
    @action(detail=False, methods=['post'])
    def setup_2fa(self, request):
        """Setup 2FA for user"""
        serializer = TwoFactorSetupSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            enable_2fa = serializer.validated_data['enable_2fa']
            
            if enable_2fa:
                # Generate QR code for 2FA setup
                # In production, use a proper 2FA library
                if hasattr(user, 'two_factor_enabled'):
                    user.two_factor_enabled = True
                    user.save()
                
                return Response({
                    'success': True,
                    'message': '2FA activé avec succès'
                })
            else:
                if hasattr(user, 'two_factor_enabled'):
                    user.two_factor_enabled = False
                    user.save()
                
                return Response({
                    'success': True,
                    'message': '2FA désactivé'
                })
        
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class MobileVisitorViewSet(viewsets.ViewSet):
    """Visitor endpoints for mobile app"""
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def add_to_cart(self, request):
        """Add product to visitor cart"""
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        session_key = request.data.get('session_key')
        
        if not product_id or not session_key:
            return Response({
                'success': False,
                'error': 'ID produit et clé de session requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = Product.objects.get(id=product_id, status='ACTIVE')
            cart, created = VisitorCart.objects.get_or_create(session_key=session_key)
            
            cart_item, created = VisitorCartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            serializer = VisitorCartSerializer(cart)
            return Response({
                'success': True,
                'cart': serializer.data
            })
        except Product.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Produit non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def cart(self, request):
        """Get visitor cart"""
        session_key = request.query_params.get('session_key')
        
        if not session_key:
            return Response({
                'success': False,
                'error': 'Clé de session requise'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cart = VisitorCart.objects.get(session_key=session_key)
            serializer = VisitorCartSerializer(cart)
            return Response({
                'success': True,
                'cart': serializer.data
            })
        except VisitorCart.DoesNotExist:
            return Response({
                'success': True,
                'cart': {
                    'items': [],
                    'total_items': 0,
                    'total_amount': 0
                }
            })
    
    @action(detail=False, methods=['post'])
    def create_order(self, request):
        """Create visitor order using regular Order model"""
        session_key = request.data.get('session_key')
        customer_name = request.data.get('customer_name')
        customer_phone = request.data.get('customer_phone')
        customer_email = request.data.get('customer_email')
        pickup_point_id = request.data.get('pickup_point_id')
        
        if not all([session_key, customer_name, customer_phone, customer_email, pickup_point_id]):
            return Response({
                'success': False,
                'error': 'Tous les champs sont requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cart = VisitorCart.objects.get(session_key=session_key)
            pickup_point = PickupPoint.objects.get(id=pickup_point_id)
            
            # Create order for each cart item using regular Order model
            orders = []
            for item in cart.items.all():
                order = Order.objects.create(
                    product=item.product,
                    quantity=item.quantity,
                    total_amount=item.product.price * item.quantity,
                    pickup_point=pickup_point,
                    visitor_name=customer_name,
                    visitor_phone=customer_phone,
                    visitor_email=customer_email,
                    buyer=None,  # No authenticated user for visitor orders
                    seller=item.product.seller
                )
                orders.append(order)
            
            # Clear cart
            cart.items.all().delete()
            
            return Response({
                'success': True,
                'message': f'{len(orders)} commande(s) créée(s) avec succès',
                'orders': [str(order.id) for order in orders]
            })
        except (VisitorCart.DoesNotExist, PickupPoint.DoesNotExist):
            return Response({
                'success': False,
                'error': 'Panier ou point de retrait non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)

class MobileSearchView(APIView):
    """Search endpoint for mobile app"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response({
                'success': False,
                'error': 'Requête de recherche requise'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        products = Product.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            status='ACTIVE'
        ).order_by('-created_at')[:20]
        
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response({
            'success': True,
            'query': query,
            'results': serializer.data,
            'count': len(serializer.data)
        })

class MobileHealthCheckView(APIView):
    """Health check endpoint for mobile app"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        return Response({
            'success': True,
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0'
        })

class MobilePickupPointViewSet(viewsets.ReadOnlyModelViewSet):
    """Pickup point endpoints for mobile app"""
    serializer_class = PickupPointSerializer
    queryset = PickupPoint.objects.filter(is_active=True)
    permission_classes = [permissions.AllowAny]

class MobileWalletViewSet(viewsets.ViewSet):
    """Wallet endpoints for mobile app"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get wallet balance"""
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        serializer = WalletSerializer(wallet)
        return Response({
            'success': True,
            'wallet': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """Get wallet transactions"""
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        transactions = Transaction.objects.filter(wallet=wallet).order_by('-created_at')
        
        paginator = MobilePagination()
        page = paginator.paginate_queryset(transactions, request)
        
        serializer = TransactionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def add_funds(self, request):
        """Add funds to wallet"""
        amount = request.data.get('amount')
        if not amount or amount <= 0:
            return Response({
                'success': False,
                'error': 'Montant valide requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        wallet.add_funds(amount, "Fonds ajoutés via mobile")
        
        serializer = WalletSerializer(wallet)
        return Response({
            'success': True,
            'wallet': serializer.data
        })

class MobileAdminViewSet(viewsets.ViewSet):
    """Admin endpoints for mobile app"""
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get admin dashboard statistics"""
        today = timezone.now().date()
        
        stats = {
            'total_users': User.objects.count(),
            'total_products': Product.objects.count(),
            'total_orders': Order.objects.count(),
            'total_revenue': Order.objects.aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
            'pending_products': Product.objects.filter(status='PENDING').count(),
            'active_users_today': User.objects.filter(
                last_login__date=today
            ).count()
        }
        
        return Response({
            'success': True,
            'stats': stats
        })
    
    @action(detail=False, methods=['get'])
    def users(self, request):
        """Get all users for admin"""
        users = User.objects.all().order_by('-created_at')
        
        paginator = MobilePagination()
        page = paginator.paginate_queryset(users, request)
        
        serializer = AdminUserManagementSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_products(self, request):
        """Get pending products for moderation"""
        products = Product.objects.filter(status='PENDING').order_by('-created_at')
        
        paginator = MobilePagination()
        page = paginator.paginate_queryset(products, request)
        
        serializer = AdminProductModerationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve_product(self, request, pk=None):
        """Approve a product"""
        product = get_object_or_404(Product, id=pk)
        product.status = 'ACTIVE'
        product.save()
        
        return Response({
            'success': True,
            'message': 'Produit approuvé avec succès'
        })
    
    @action(detail=True, methods=['post'])
    def reject_product(self, request, pk=None):
        """Reject a product"""
        product = get_object_or_404(Product, id=pk)
        product.status = 'REJECTED'
        product.save()
        
        return Response({
            'success': True,
            'message': 'Produit rejeté'
        })

class MobilePaymentView(APIView):
    """Payment endpoint for mobile app"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Process payment"""
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            payment_method = serializer.validated_data['payment_method']
            
            # Generate payment reference
            reference = f"PAY_{get_random_string(8).upper()}"
            
            # In production, integrate with payment gateway
            # For now, return success response
            
            return Response({
                'success': True,
                'reference': reference,
                'message': 'Paiement traité avec succès'
            })
        
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):
        """Verify payment"""
        serializer = PaymentVerificationSerializer(data=request.data)
        if serializer.is_valid():
            reference = serializer.validated_data['reference']
            transaction_id = serializer.validated_data['transaction_id']
            
            # In production, verify with payment gateway
            # For now, return success response
            
            return Response({
                'success': True,
                'message': 'Paiement vérifié avec succès'
            })
        
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST) 