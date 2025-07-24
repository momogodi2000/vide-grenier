# backend/urls.py - REORGANIZED URLs FOR VIDÉ-GRENIER KAMER

from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from . import views, views_admin, additional_views, views_client, views_staff

app_name = 'backend'

# ============= MAIN PAGES =============
urlpatterns = [
    # Home page
    path('', views.HomeView.as_view(), name='home'),
    
    # Dashboard redirector
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/client/', views.DashboardView.as_view(), {'user_type': 'CLIENT'}, name='client_dashboard'),
    path('dashboard/admin/', views.DashboardView.as_view(), {'user_type': 'ADMIN'}, name='admin_dashboard'),
    path('dashboard/staff/', views.DashboardView.as_view(), {'user_type': 'STAFF'}, name='staff_dashboard'),
    
    # Static pages
    path('about/', additional_views.AboutView.as_view(), name='about'),
    path('contact/', additional_views.ContactView.as_view(), name='contact'),
    path('help/', additional_views.HelpView.as_view(), name='help'),
    path('privacy/', additional_views.PrivacyView.as_view(), name='privacy'),
    path('terms/', additional_views.TermsView.as_view(), name='terms'),
]

# ============= AUTHENTICATION =============
urlpatterns += [
    path('auth/register/', views.CustomSignupView.as_view(), name='register'),
    path('auth/login/', views.CustomLoginView.as_view(), name='login'),
    path('auth/logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('auth/profile/', views.ProfileView.as_view(), name='profile'),
    path('auth/profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('auth/password-reset-request/', additional_views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('auth/password-reset-confirm/<str:token>/', additional_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('auth/verify-phone/', views.PhoneVerificationView.as_view(), name='verify_phone'),
]

# ============= PRODUCTS =============
urlpatterns += [
    # Product listings
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/trending/', additional_views.TrendingProductsView.as_view(), name='trending_products'),
    path('products/recommended/', additional_views.RecommendedProductsView.as_view(), name='recommended_products'),
    path('products/recently-viewed/', additional_views.RecentlyViewedView.as_view(), name='recently_viewed_products'),
    path('products/compare/', additional_views.CompareProductsView.as_view(), name='product_compare'),
    
    # Product CRUD
    path('products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('product/<slug:slug>/edit/', views.ProductEditView.as_view(), name='product_edit'),
    path('product/<slug:slug>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('product/<slug:slug>/promote/', additional_views.ProductPromoteView.as_view(), name='product_promote'),
    path('product/<slug:slug>/report/', additional_views.ProductReportView.as_view(), name='product_report'),
    path('products/bulk-actions/', additional_views.ProductBulkActionsView.as_view(), name='product_bulk_actions'),
    
    # Short URLs for sharing
    path('p/<slug:slug>/', views.ProductDetailView.as_view(), name='product_short'),
    path('buy/<slug:slug>/', views.PublicOrderCreateView.as_view(), name='quick_buy'),
    
    # Visitor-specific product routes
    path('visitor/product/<slug:slug>/', views.VisitorProductDetailView.as_view(), name='visitor_product_detail'),
]

# ============= CATEGORIES =============
urlpatterns += [
    path('categories/', additional_views.CategoryListView.as_view(), name='category_list'),
    path('category/<slug:slug>/', views.CategoryView.as_view(), name='category_detail'),
    # Short URL for categories
    path('c/<slug:slug>/', views.CategoryView.as_view(), name='category_short'),
]

# ============= ORDERS & PAYMENTS =============
urlpatterns += [
    # Regular orders
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/create/', views.OrderCreateView.as_view(), name='order_create'),
    path('orders/<uuid:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    
    # Public orders
    path('orders/public/', views.PublicOrderCreateView.as_view(), name='public_order_create'),
    path('orders/public/<uuid:order_id>/', views.PublicOrderSuccessView.as_view(), name='public_order_detail'),
    path('orders/public/success/<uuid:order_id>/', views.PublicOrderSuccessView.as_view(), name='public_order_success'),
    
    # Visitor orders
    path('visitor/order/<uuid:product_id>/', views.visitor_order_create, name='visitor_order_create'),
    path('visitor/payment/<uuid:order_id>/', views.visitor_payment_process, name='visitor_payment'),
    path('visitor/success/<uuid:order_id>/', views.visitor_order_success, name='visitor_order_success'),
    
    # Payments
    path('payment/<uuid:order_id>/', views.PaymentView.as_view(), name='payment_create'),
    path('payment/success/<uuid:payment_id>/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('payment/cancel/<uuid:payment_id>/', views.PaymentCancelView.as_view(), name='payment_cancel'),
]

# ============= SEARCH =============
urlpatterns += [
    path('search/', views.SearchView.as_view(), name='search_results'),
    path('search/advanced/', additional_views.ProductAdvancedSearchView.as_view(), name='advanced_search'),
    path('search/saved/', additional_views.SavedSearchesView.as_view(), name='saved_searches'),
]

# ============= FAVORITES & WISHLIST =============
urlpatterns += [
    path('favorites/', additional_views.FavoriteListView.as_view(), name='favorites_list'),
    path('wishlist/', additional_views.WishlistView.as_view(), name='wishlist'),
]

# ============= REVIEWS =============
urlpatterns += [
    path('reviews/', views.ReviewListView.as_view(), name='review_list'),
    path('review/create/<uuid:order_id>/', views.ReviewCreateView.as_view(), name='review_create'),
    path('review/<uuid:pk>/', views.ReviewDetailView.as_view(), name='review_detail'),
]

# ============= CHAT =============
urlpatterns += [
    path('chat/', views.ChatListView.as_view(), name='chat_list'),
    path('chat/<uuid:pk>/', views.ChatDetailView.as_view(), name='chat_detail'),
    path('chat/create/<uuid:product_id>/', views.ChatCreateView.as_view(), name='chat_create'),
]

# ============= PICKUP POINTS =============
urlpatterns += [
    path('pickup-points/', views.PickupPointListView.as_view(), name='pickup_list'),
    path('pickup-point/<uuid:pk>/', views.PickupPointDetailView.as_view(), name='pickup_detail'),
]

# ============= SELLER PROFILES =============
urlpatterns += [
    path('seller/<uuid:pk>/', additional_views.SellerProfileView.as_view(), name='seller_profile'),
]

# ============= ADMIN PANEL =============
urlpatterns += [
    # Main admin panel
    path('admin-panel/', views_admin.admin_dashboard, name='admin_panel'),
    
    # User Management
    path('admin-panel/users/', views_admin.AdminUserListView.as_view() 
         if hasattr(views_admin, 'AdminUserListView') else views_admin.admin_user_list, 
         name='admin_user_list'),
    path('admin-panel/users/create/', views_admin.AdminUserCreateView.as_view() 
         if hasattr(views_admin, 'AdminUserCreateView') else views_admin.admin_user_create, 
         name='admin_user_create'),
    path('admin-panel/users/<uuid:user_id>/', views_admin.AdminUserDetailView.as_view() 
         if hasattr(views_admin, 'AdminUserDetailView') else views_admin.admin_user_detail, 
         name='admin_user_detail'),
    path('admin-panel/users/<uuid:user_id>/edit/', views_admin.AdminUserUpdateView.as_view() 
         if hasattr(views_admin, 'AdminUserUpdateView') else views_admin.admin_user_edit, 
         name='admin_user_edit'),
    
    # Product Management
    path('admin-panel/products/', views_admin.AdminProductListView.as_view() 
         if hasattr(views_admin, 'AdminProductListView') else views_admin.admin_product_list, 
         name='admin_product_list'),
    path('admin-panel/products/create/', views_admin.admin_product_create, name='admin_product_create'),
    path('admin-panel/products/<uuid:product_id>/', views_admin.admin_product_detail, name='admin_product_detail'),
    path('admin-panel/products/<uuid:product_id>/edit/', views_admin.admin_product_edit, name='admin_product_edit'),
    
    # Order Management
    path('admin-panel/orders/', views_admin.AdminOrderListView.as_view() 
         if hasattr(views_admin, 'AdminOrderListView') else views_admin.admin_order_list, 
         name='admin_order_list'),
    
    # Payment Management
    path('admin-panel/payments/', views_admin.AdminPaymentListView.as_view() 
         if hasattr(views_admin, 'AdminPaymentListView') else views_admin.admin_payment_list, 
         name='admin_payment_list'),
    path('admin-panel/payments/<uuid:payment_id>/', views_admin.admin_payment_detail, name='admin_payment_detail'),
    
    # Stock Management
    path('admin-panel/stock/', views_admin.AdminStockView.as_view() 
         if hasattr(views_admin, 'AdminStockView') else views_admin.admin_stock_list, 
         name='admin_stock_list'),
    path('admin-panel/stock/add/', views_admin.AdminStockAddView.as_view() 
         if hasattr(views_admin, 'AdminStockAddView') else views_admin.admin_stock_add, 
         name='admin_stock_add'),
    
    # Promotion Management
    path('admin-panel/promotions/', views_admin.AdminPromotionListView.as_view() 
         if hasattr(views_admin, 'AdminPromotionListView') else views_admin.admin_promotion_list, 
         name='admin_promotion_list'),
    path('admin-panel/promotions/create/', views_admin.admin_promotion_create, name='admin_promotion_create'),
    path('admin-panel/promotions/<uuid:promotion_id>/edit/', views_admin.admin_promotion_edit, name='admin_promotion_edit'),
    
    # Loyalty Management
    path('admin-panel/loyalty/', views_admin.AdminLoyaltyListView.as_view() 
         if hasattr(views_admin, 'AdminLoyaltyListView') else views_admin.admin_loyalty_list, 
         name='admin_loyalty_list'),
    path('admin-panel/loyalty/create/', views_admin.admin_loyalty_create, name='admin_loyalty_create'),
    path('admin-panel/loyalty/<uuid:loyalty_id>/edit/', views_admin.admin_loyalty_edit, name='admin_loyalty_edit'),
    
    # Newsletter Management
    path('admin-panel/newsletter/', views_admin.AdminNewsletterListView.as_view() 
         if hasattr(views_admin, 'AdminNewsletterListView') else views_admin.admin_dashboard, 
         name='admin_newsletter_list'),
    path('admin-panel/newsletter/create/', views_admin.admin_newsletter_create, name='admin_newsletter_create'),
    path('admin-panel/newsletter/sent/', views_admin.admin_newsletter_send 
         if hasattr(views_admin, 'admin_newsletter_send') else views_admin.admin_newsletter_list, 
         name='admin_newsletter_sent'),
    
    # Notification Management
    path('admin-panel/notifications/', views_admin.AdminNotificationListView.as_view() 
         if hasattr(views_admin, 'AdminNotificationListView') else views_admin.admin_notification_list, 
         name='admin_notification_list'),
    path('admin-panel/notifications/create/', views_admin.admin_notification_create, name='admin_notification_create'),
    
    # Analytics
    path('admin-panel/analytics/', views_admin.AdminAnalyticsView.as_view() 
         if hasattr(views_admin, 'AdminAnalyticsView') else views_admin.admin_analytics, 
         name='admin_analytics'),
]

# ============= AJAX ENDPOINTS =============
urlpatterns += [
    # Product interactions
    path('ajax/product-views/<uuid:pk>/', views.ProductViewAjax.as_view(), name='product_view_ajax'),
    path('ajax/favorite/<slug:slug>/', views.FavoriteToggleView.as_view(), name='favorite_toggle'),
    
    # Recommendations and tracking
    path('ajax/recommendations/', views.ajax_get_recommendations 
         if hasattr(views, 'ajax_get_recommendations') else views.HomeView.as_view(), 
         name='ajax_get_recommendations'),
    path('ajax/behavior-track/', views.ajax_track_behavior 
         if hasattr(views, 'ajax_track_behavior') else views.HomeView.as_view(), 
         name='ajax_track_behavior'),
    
    # Notifications
    path('ajax/notifications/', views.NotificationListAjax.as_view(), name='notification_ajax'),
    path('ajax/notifications/<uuid:pk>/read/', views.NotificationMarkReadAjax.as_view(), name='notification_read_ajax'),
    path('ajax/notifications/mark-read/', views.ajax_mark_notifications_read 
         if hasattr(views, 'ajax_mark_notifications_read') else views.NotificationMarkReadAjax.as_view(), 
         name='ajax_mark_notifications_read'),
    
    # Shopping
    path('ajax/cart/count/', views.ajax_get_cart_count 
         if hasattr(views, 'ajax_get_cart_count') else views.HomeView.as_view(), 
         name='ajax_get_cart_count'),
    path('ajax/wishlist/toggle/', views.ajax_toggle_wishlist 
         if hasattr(views, 'ajax_toggle_wishlist') else views.FavoriteToggleView.as_view(), 
         name='ajax_toggle_wishlist'),
    path('ajax/follow/toggle/', views.ajax_toggle_follow 
         if hasattr(views, 'ajax_toggle_follow') else views.HomeView.as_view(), 
         name='ajax_toggle_follow'),
]

# ============= PAYMENT WEBHOOKS =============
urlpatterns += [
    path('webhooks/campay/', csrf_exempt(views.CampayWebhookView.as_view()), name='campay_webhook'),
    path('webhooks/orange-money/', csrf_exempt(views.OrangeMoneyWebhookView.as_view()), name='orange_money_webhook'),
    path('webhooks/mtn-money/', csrf_exempt(views.MTNMoneyWebhookView.as_view()), name='mtn_money_webhook'),
    path('api/campay/webhook/', csrf_exempt(views.campay_webhook), name='campay_webhook_alt'),
]

# ============= ENHANCED FEATURES =============
# Include enhanced features URLs (client and staff)
urlpatterns += [
    # Enhanced client features
    path('client/', include('backend.urls_enhanced', namespace='client')),
    
    # Enhanced staff features
    path('staff/', include('backend.urls_enhanced', namespace='staff')),
]

# ============= ERROR HANDLERS =============
handler404 = 'backend.views.handler404'
handler500 = 'backend.views.handler500'
handler403 = 'backend.views.handler403'