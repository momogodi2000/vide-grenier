# backend/urls_mobile.py - MOBILE API URLS FOR REACT NATIVE/FLUTTER
from django.urls import path
from . import mobile_api

app_name = 'mobile_api'

urlpatterns = [
    # ============= AUTHENTICATION =============
    path('auth/login/', mobile_api.mobile_login, name='login'),
    path('auth/register/', mobile_api.mobile_register, name='register'),
    path('auth/logout/', mobile_api.mobile_logout, name='logout'),
    
    # ============= PRODUCTS =============
    path('products/', mobile_api.mobile_products_list, name='products_list'),
    path('products/<uuid:product_id>/', mobile_api.mobile_product_detail, name='product_detail'),
    path('products/<uuid:product_id>/favorite/', mobile_api.mobile_toggle_favorite, name='toggle_favorite'),
    
    # ============= CATEGORIES =============
    path('categories/', mobile_api.mobile_categories_list, name='categories_list'),
    
    # ============= USER PROFILE =============
    path('user/profile/', mobile_api.mobile_user_profile, name='user_profile'),
    path('user/profile/update/', mobile_api.mobile_update_profile, name='update_profile'),
    path('user/favorites/', mobile_api.mobile_favorites_list, name='favorites_list'),
    
    # ============= SEARCH =============
    path('search/', mobile_api.mobile_search, name='search'),
    
    # ============= HEALTH CHECK =============
    path('health/', mobile_api.mobile_health_check, name='health_check'),
] 