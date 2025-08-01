# backend/mobile_api.py - MOBILE API ENDPOINTS FOR REACT NATIVE/FLUTTER
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
import json
import jwt
from functools import wraps
from .models import *
from .mobile.serializers import *
from .mobile.jwt_utils import generate_jwt_token, verify_jwt_token

# ============= AUTHENTICATION DECORATORS =============

def mobile_auth_required(view_func):
    """Custom decorator for mobile API authentication using JWT"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        token = auth_header.split(' ')[1]
        try:
            payload = verify_jwt_token(token)
            request.user = User.objects.get(id=payload['user_id'])
            return view_func(request, *args, **kwargs)
        except (jwt.InvalidTokenError, User.DoesNotExist):
            return JsonResponse({'error': 'Invalid token'}, status=401)
    
    return wrapper

def mobile_optional_auth(view_func):
    """Decorator for endpoints that work with or without authentication"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                payload = verify_jwt_token(token)
                request.user = User.objects.get(id=payload['user_id'])
            except (jwt.InvalidTokenError, User.DoesNotExist):
                request.user = None
        else:
            request.user = None
        return view_func(request, *args, **kwargs)
    
    return wrapper

# ============= AUTHENTICATION ENDPOINTS =============

@csrf_exempt
@require_http_methods(["POST"])
def mobile_login(request):
    """Mobile login endpoint"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return JsonResponse({'error': 'Email and password required'}, status=400)
        
        user = authenticate(request, username=email, password=password)
        if user is None:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
        
        if not user.is_active:
            return JsonResponse({'error': 'Account is disabled'}, status=401)
        
        # Generate JWT token
        token = generate_jwt_token(user)
        
        # Return user data and token
        user_data = {
            'id': str(user.id),
            'email': user.email,
            'phone': user.phone,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user.user_type,
            'city': user.city,
            'is_verified': user.is_verified,
            'phone_verified': user.phone_verified,
            'trust_score': user.trust_score,
            'loyalty_points': user.loyalty_points,
            'loyalty_level': user.loyalty_level,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
        }
        
        return JsonResponse({
            'success': True,
            'token': token,
            'user': user_data
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def mobile_register(request):
    """Mobile registration endpoint"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['email', 'phone', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'error': f'{field} is required'}, status=400)
        
        # Check if user already exists
        if User.objects.filter(email=data['email']).exists():
            return JsonResponse({'error': 'Email already registered'}, status=400)
        
        if User.objects.filter(phone=data['phone']).exists():
            return JsonResponse({'error': 'Phone number already registered'}, status=400)
        
        # Create user
        user = User.objects.create_user(
            email=data['email'],
            phone=data['phone'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            user_type=data.get('user_type', 'CLIENT'),
            city=data.get('city', ''),
            address=data.get('address', '')
        )
        
        # Generate JWT token
        token = generate_jwt_token(user)
        
        user_data = {
            'id': str(user.id),
            'email': user.email,
            'phone': user.phone,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user.user_type,
            'city': user.city,
            'is_verified': user.is_verified,
            'phone_verified': user.phone_verified,
            'trust_score': user.trust_score,
            'loyalty_points': user.loyalty_points,
            'loyalty_level': user.loyalty_level,
        }
        
        return JsonResponse({
            'success': True,
            'token': token,
            'user': user_data
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@mobile_auth_required
def mobile_logout(request):
    """Mobile logout endpoint"""
    # In a real implementation, you might want to blacklist the token
    return JsonResponse({'success': True, 'message': 'Logged out successfully'})

# ============= PRODUCT ENDPOINTS =============

@mobile_optional_auth
def mobile_products_list(request):
    """Get products list with pagination and filters"""
    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        category = request.GET.get('category')
        city = request.GET.get('city')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        condition = request.GET.get('condition')
        search = request.GET.get('search')
        
        # Build query
        products = Product.objects.filter(status='ACTIVE')
        
        if category:
            products = products.filter(category__slug=category)
        
        if city:
            products = products.filter(city=city)
        
        if min_price:
            products = products.filter(price__gte=min_price)
        
        if max_price:
            products = products.filter(price__lte=max_price)
        
        if condition:
            products = products.filter(condition=condition)
        
        if search:
            products = products.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(category__name__icontains=search)
            )
        
        # Order by creation date
        products = products.order_by('-created_at')
        
        # Pagination
        paginator = Paginator(products, page_size)
        products_page = paginator.get_page(page)
        
        # Serialize products
        products_data = []
        for product in products_page:
            product_data = {
                'id': str(product.id),
                'title': product.title,
                'slug': product.slug,
                'description': product.description,
                'price': float(product.price),
                'condition': product.condition,
                'city': product.city,
                'is_negotiable': product.is_negotiable,
                'views_count': product.views_count,
                'likes_count': product.likes_count,
                'created_at': product.created_at.isoformat(),
                'category': {
                    'id': str(product.category.id),
                    'name': product.category.name,
                    'slug': product.category.slug
                },
                'seller': {
                    'id': str(product.seller.id),
                    'first_name': product.seller.first_name,
                    'last_name': product.seller.last_name,
                    'trust_score': product.seller.trust_score,
                    'city': product.seller.city
                },
                'images': [
                    {
                        'id': str(img.id),
                        'image_url': img.image.url,
                        'is_primary': img.is_primary
                    } for img in product.images.all()[:5]  # Limit to 5 images
                ]
            }
            products_data.append(product_data)
        
        return JsonResponse({
            'success': True,
            'products': products_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': products_page.has_next(),
                'has_previous': products_page.has_previous()
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@mobile_optional_auth
def mobile_product_detail(request, product_id):
    """Get detailed product information"""
    try:
        product = get_object_or_404(Product, id=product_id, status='ACTIVE')
        
        # Increment view count
        product.views_count += 1
        product.save()
        
        # Check if user has favorited this product
        is_favorited = False
        if request.user and request.user.is_authenticated:
            is_favorited = Favorite.objects.filter(user=request.user, product=product).exists()
        
        product_data = {
            'id': str(product.id),
            'title': product.title,
            'slug': product.slug,
            'description': product.description,
            'price': float(product.price),
            'condition': product.condition,
            'city': product.city,
            'is_negotiable': product.is_negotiable,
            'views_count': product.views_count,
            'likes_count': product.likes_count,
            'created_at': product.created_at.isoformat(),
            'is_favorited': is_favorited,
            'category': {
                'id': str(product.category.id),
                'name': product.category.name,
                'slug': product.category.slug
            },
            'seller': {
                'id': str(product.seller.id),
                'first_name': product.seller.first_name,
                'last_name': product.seller.last_name,
                'trust_score': product.seller.trust_score,
                'city': product.seller.city,
                'phone': product.seller.phone,
                'loyalty_level': product.seller.loyalty_level
            },
            'images': [
                {
                    'id': str(img.id),
                    'image_url': img.image.url,
                    'is_primary': img.is_primary,
                    'alt_text': img.alt_text
                } for img in product.images.all()
            ],
            'reviews': [
                {
                    'id': str(review.id),
                    'overall_rating': review.overall_rating,
                    'comment': review.comment,
                    'created_at': review.created_at.isoformat(),
                    'reviewer': {
                        'first_name': review.reviewer.first_name,
                        'last_name': review.reviewer.last_name
                    }
                } for review in product.orders.filter(review__isnull=False).values_list('review', flat=True)[:5]
            ]
        }
        
        return JsonResponse({
            'success': True,
            'product': product_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ============= CATEGORY ENDPOINTS =============

@mobile_optional_auth
def mobile_categories_list(request):
    """Get all categories"""
    try:
        categories = Category.objects.filter(is_active=True).order_by('order', 'name')
        
        categories_data = []
        for category in categories:
            category_data = {
                'id': str(category.id),
                'name': category.name,
                'slug': category.slug,
                'description': category.description,
                'icon': category.icon,
                'product_count': category.products.filter(status='ACTIVE').count(),
                'children': [
                    {
                        'id': str(child.id),
                        'name': child.name,
                        'slug': child.slug,
                        'product_count': child.products.filter(status='ACTIVE').count()
                    } for child in category.children.filter(is_active=True)
                ]
            }
            categories_data.append(category_data)
        
        return JsonResponse({
            'success': True,
            'categories': categories_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ============= USER PROFILE ENDPOINTS =============

@mobile_auth_required
def mobile_user_profile(request):
    """Get current user profile"""
    try:
        user = request.user
        
        user_data = {
            'id': str(user.id),
            'email': user.email,
            'phone': user.phone,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user.user_type,
            'city': user.city,
            'address': user.address,
            'is_verified': user.is_verified,
            'phone_verified': user.phone_verified,
            'trust_score': user.trust_score,
            'loyalty_points': user.loyalty_points,
            'loyalty_level': user.loyalty_level,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
            'created_at': user.created_at.isoformat(),
            'stats': {
                'products_count': user.products_sold.filter(status='ACTIVE').count(),
                'orders_bought': user.orders_bought.count(),
                'orders_sold': user.products_sold.aggregate(total_orders=Count('orders'))['total_orders'] or 0,
                'favorites_count': user.favorites.count(),
                'reviews_given': user.reviews_given.count()
            }
        }
        
        return JsonResponse({
            'success': True,
            'user': user_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@mobile_auth_required
@require_http_methods(["PUT"])
def mobile_update_profile(request):
    """Update user profile"""
    try:
        data = json.loads(request.body)
        user = request.user
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'city' in data:
            user.city = data['city']
        if 'address' in data:
            user.address = data['address']
        
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ============= FAVORITES ENDPOINTS =============

@mobile_auth_required
def mobile_favorites_list(request):
    """Get user favorites"""
    try:
        favorites = Favorite.objects.filter(user=request.user).order_by('-created_at')
        
        favorites_data = []
        for favorite in favorites:
            product = favorite.product
            product_data = {
                'id': str(product.id),
                'title': product.title,
                'price': float(product.price),
                'condition': product.condition,
                'city': product.city,
                'created_at': product.created_at.isoformat(),
                'main_image': product.main_image.url if product.main_image else None,
                'category': {
                    'name': product.category.name,
                    'slug': product.category.slug
                }
            }
            favorites_data.append(product_data)
        
        return JsonResponse({
            'success': True,
            'favorites': favorites_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@mobile_auth_required
@require_http_methods(["POST"])
def mobile_toggle_favorite(request, product_id):
    """Toggle product favorite status"""
    try:
        product = get_object_or_404(Product, id=product_id)
        favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
        
        if not created:
            favorite.delete()
            is_favorited = False
        else:
            is_favorited = True
        
        return JsonResponse({
            'success': True,
            'is_favorited': is_favorited
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ============= SEARCH ENDPOINTS =============

@mobile_optional_auth
def mobile_search(request):
    """Search products"""
    try:
        query = request.GET.get('q', '')
        if not query:
            return JsonResponse({'error': 'Search query required'}, status=400)
        
        products = Product.objects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            status='ACTIVE'
        ).order_by('-created_at')[:20]
        
        products_data = []
        for product in products:
            product_data = {
                'id': str(product.id),
                'title': product.title,
                'price': float(product.price),
                'condition': product.condition,
                'city': product.city,
                'main_image': product.main_image.url if product.main_image else None,
                'category': {
                    'name': product.category.name
                }
            }
            products_data.append(product_data)
        
        return JsonResponse({
            'success': True,
            'query': query,
            'results': products_data,
            'count': len(products_data)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ============= HEALTH CHECK ENDPOINT =============

def mobile_health_check(request):
    """Health check endpoint for mobile app"""
    return JsonResponse({
        'success': True,
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    }) 