# backend/urls_enhanced.py - ENHANCED URLs FOR VGK ADVANCED FEATURES
from django.urls import path, include
from . import views_client, views_staff

app_name = 'backend_enhanced'

# ============= CLIENT ENHANCED URLS =============
client_urls = [
    # Enhanced Shopping Cart
    path('cart/', views_client.ShoppingCartView.as_view(), name='shopping_cart'),
    path('cart/add/', views_client.add_to_cart, name='add_to_cart'),
    path('cart/update/', views_client.update_cart_item, name='update_cart_item'),
    path('cart/remove/', views_client.remove_cart_item, name='remove_cart_item'),
    path('cart/checkout/', views_client.checkout_cart, name='checkout_cart'),
    
    # Enhanced Wishlist
    path('wishlist/', views_client.WishlistListView.as_view(), name='wishlist_list'),
    path('wishlist/<uuid:pk>/', views_client.WishlistDetailView.as_view(), name='wishlist_detail'),
    path('wishlist/add/', views_client.add_to_wishlist, name='add_to_wishlist'),
    
    # AI Recommendations
    path('recommendations/', views_client.RecommendationsView.as_view(), name='recommendations'),
    path('recommendations/feedback/', views_client.recommendation_feedback, name='recommendation_feedback'),
    
    # Social Features
    path('social/feed/', views_client.SocialFeedView.as_view(), name='social_feed'),
    path('social/follow/', views_client.UserFollowView.as_view(), name='user_follow'),
    path('social/post/create/', views_client.CreateSocialPostView.as_view(), name='create_social_post'),
    
    # Enhanced Reviews
    path('review/create/enhanced/<uuid:order_id>/', views_client.EnhancedReviewCreateView.as_view(), name='create_enhanced_review'),
    
    # Smart Search
    path('search/smart/', views_client.SmartSearchView.as_view(), name='smart_search'),
    
    # Personal Analytics
    path('analytics/personal/', views_client.PersonalAnalyticsView.as_view(), name='personal_analytics'),
]

# ============= STAFF ENHANCED URLS =============
staff_urls = [
    # Staff Dashboard
    path('dashboard/', views_staff.StaffDashboardView.as_view(), name='staff_dashboard'),
    
    # Task Management
    path('tasks/', views_staff.StaffTaskListView.as_view(), name='staff_tasks'),
    path('tasks/update-status/', views_staff.update_task_status, name='update_task_status'),
    
    # QR Code System
    path('qr-scanner/', views_staff.QRScannerView.as_view(), name='qr_scanner'),
    path('qr/scan/', views_staff.process_qr_scan, name='process_qr_scan'),
    path('qr/generate/', views_staff.generate_qr_code, name='generate_qr_code'),
    
    # Inventory Management
    path('inventory/', views_staff.InventoryListView.as_view(), name='staff_inventory'),
    path('inventory/receive/', views_staff.receive_stock, name='receive_stock'),
    path('inventory/movements/', views_staff.InventoryMovementListView.as_view(), name='inventory_movements'),
    
    # Customer Service
    path('customer-service/', views_staff.CustomerServiceView.as_view(), name='customer_service'),
    path('customer-service/contact/', views_staff.contact_customer, name='contact_customer'),
    
    # Performance Tracking
    path('performance/', views_staff.StaffPerformanceView.as_view(), name='staff_performance'),
]

# ============= MAIN URL PATTERNS =============
urlpatterns = [
    # Client URLs
    path('client/', include(client_urls)),
    
    # Staff URLs  
    path('staff/', include(staff_urls)),
] 