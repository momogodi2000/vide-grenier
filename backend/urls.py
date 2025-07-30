# backend/urls.py - REORGANIZED URLs FOR VIDÉ-GRENIER KAMER

from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from . import views, additional_views
from .views_enhanced import DashboardRedirectView

app_name = 'backend'

# ============= MAIN PAGES =============
urlpatterns = [
    # Home page
    path('', views.HomeView.as_view(), name='home'),
    
    # Dashboard redirector (redirects to user-type-specific interfaces)
    path('dashboard/', DashboardRedirectView.as_view(), name='dashboard'),
    
    # Newsletter subscription
    path('api/newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    
    # APK Download
    path('download-apk/', views.APKDownloadView.as_view(), name='download_apk'),
    path('generate-apk/', views.APKGenerationView.as_view(), name='generate_apk'),
    
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
    
    # Visitor product listings (no login required)
    path('visitor/products/', views.VisitorProductListView.as_view(), name='visitor_product_list'),
    path('visitor/product/<slug:slug>/', views.VisitorProductDetailView.as_view(), name='visitor_product_detail'),
    path('visitor/product/id/<uuid:pk>/', views.VisitorProductDetailView.as_view(), name='visitor_product_detail_pk'),
    
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
    
    # Visitor cart operations
    path('visitor/cart/', views.visitor_cart_view, name='visitor_cart'),
    path('visitor/cart/add/<uuid:product_id>/', views.visitor_add_to_cart, name='visitor_add_to_cart'),
    path('visitor/cart/update/<uuid:item_id>/', views.visitor_update_cart_item, name='visitor_update_cart_item'),
    path('visitor/cart/remove/<uuid:item_id>/', views.visitor_remove_cart_item, name='visitor_remove_cart_item'),
    path('visitor/cart/items/', views.visitor_cart_items, name='visitor_cart_items'),
    path('visitor/cart/status/', views.visitor_cart_status, name='visitor_cart_status'),
    path('visitor/cart/preview/', views.visitor_cart_preview, name='visitor_cart_preview'),
    path('visitor/cart/update-info/', views.visitor_update_cart_info, name='visitor_update_cart_info'),
    path('visitor/cart/checkout/', views.visitor_cart_checkout, name='visitor_cart_checkout'),
    path('visitor/cart/payment/', views.visitor_cart_payment, name='visitor_cart_payment'),
    path('visitor/cart/verify-payment/', views.visitor_verify_payment, name='visitor_verify_payment'),
    path('visitor/cart/success/<str:cart_session>/', views.visitor_cart_success, name='visitor_cart_success'),
    path('visitor/cart/download-receipt/<str:cart_session>/', views.visitor_download_receipt, name='visitor_download_receipt'),

    # Visitor Interaction URLs
    path('visitor/report/<uuid:product_id>/', views.visitor_report_product, name='visitor_report_product'),
    path('visitor/favorite/toggle/<uuid:product_id>/', views.visitor_toggle_favorite, name='visitor_toggle_favorite'),
    path('visitor/favorites/', views.visitor_favorites_list, name='visitor_favorites_list'),
    path('visitor/compare/toggle/<uuid:product_id>/', views.visitor_toggle_compare, name='visitor_toggle_compare'),
    path('visitor/compare/', views.visitor_compare_list, name='visitor_compare_list'),
    path('visitor/comment/add/<uuid:product_id>/', views.visitor_add_comment, name='visitor_add_comment'),
    path('visitor/like/toggle/<uuid:product_id>/', views.visitor_toggle_like, name='visitor_toggle_like'),
    path('visitor/alert/create/<uuid:product_id>/', views.visitor_create_alert, name='visitor_create_alert'),

    # AI Recommendations
    path('visitor/products/ai-recommendations/', views.ai_recommendations_view, name='ai_recommendations'),
    
    # ============= ENHANCED CLIENT DASHBOARD =============
    
    # Client Dashboard
    path('client/dashboard/', views.client_dashboard, name='client_dashboard'),
    path('client/analytics/', views.client_analytics, name='client_analytics'),
    path('client/loyalty/', views.client_loyalty_dashboard, name='client_loyalty_dashboard'),
    path('client/wallet/', views.client_wallet_dashboard, name='client_wallet_dashboard'),
    path('client/social/', views.client_social_dashboard, name='client_social_dashboard'),
    
    # Client Products
    path('client/products/', views.ClientProductListView.as_view(), name='client_product_list'),
    path('client/products/create/', views.ClientProductCreateView.as_view(), name='client_product_create'),
    path('client/products/<uuid:pk>/edit/', views.ClientProductUpdateView.as_view(), name='client_product_edit'),
    
    # Client Orders
    path('client/orders/', views.client_orders_dashboard, name='client_orders_dashboard'),
    
    # Client Chat
    path('client/chat/', views.client_chat_dashboard, name='client_chat_dashboard'),
    
    # Client API Endpoints
    path('client/api/analytics/', views.client_analytics_data, name='client_analytics_data'),
    path('client/api/withdrawal-request/', views.client_create_withdrawal_request, name='client_create_withdrawal_request'),
    # path('client/api/social-post/', views.client_create_social_post, name='client_create_social_post'),
    path('client/api/follow/<uuid:user_id>/', views.client_follow_user, name='client_follow_user'),
    path('client/notifications/', views.client_notifications, name='client_notifications'),
    path('client/api/mark-notification-read/', views.client_mark_notification_read, name='client_mark_notification_read'),
    
    # ============= ENHANCED STAFF DASHBOARD =============
    
    # Staff Dashboard
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/analytics/', views.staff_analytics, name='staff_analytics'),
    
    # Staff Tasks
    path('staff/tasks/', views.staff_task_dashboard, name='staff_task_dashboard'),
    path('staff/tasks/create/', views.StaffTaskCreateView.as_view(), name='staff_task_create'),
    path('staff/tasks/<uuid:pk>/edit/', views.StaffTaskUpdateView.as_view(), name='staff_task_edit'),
    path('staff/tasks/<uuid:task_id>/start/', views.staff_start_task, name='staff_start_task'),
    path('staff/tasks/<uuid:task_id>/complete/', views.staff_complete_task, name='staff_complete_task'),
    
    # Staff Inventory
    path('staff/inventory/', views.staff_inventory_dashboard, name='staff_inventory_dashboard'),
    path('staff/inventory/movement/', views.staff_record_inventory_movement, name='staff_record_inventory_movement'),
    
    # Staff Pickup Points
    path('staff/pickup-points/', views.staff_pickup_point_dashboard, name='staff_pickup_point_dashboard'),
    path('staff/pickup-points/create/', views.PickupPointCreateView.as_view(), name='staff_pickup_point_create'),
    path('staff/pickup-points/<uuid:pk>/edit/', views.PickupPointUpdateView.as_view(), name='staff_pickup_point_edit'),
    
    # Staff Performance
    path('staff/performance/', views.staff_performance_dashboard, name='staff_performance_dashboard'),
    path('staff/performance/record/', views.staff_record_performance, name='staff_record_performance'),
    
    # Staff Orders
    path('staff/orders/', views.staff_order_processing, name='staff_order_processing'),
    path('staff/orders/<uuid:order_id>/update-status/', views.staff_update_order_status, name='staff_update_order_status'),
    
    # Staff API Endpoints
    path('staff/api/analytics/', views.staff_analytics_data, name='staff_analytics_data'),
    path('staff/api/tasks/', views.staff_create_task, name='staff_create_task'),
    path('staff/api/movements/', views.staff_record_movement, name='staff_record_movement'),
    
    # ============= ADVANCED BUSINESS FEATURES =============
    
    # Escrow Payment System
    path('escrow/dashboard/', views.escrow_dashboard, name='escrow_dashboard'),
    path('escrow/create/<uuid:order_id>/', views.create_escrow_payment, name='create_escrow_payment'),
    path('escrow/<uuid:escrow_id>/fund/', views.fund_escrow_payment, name='fund_escrow_payment'),
    path('escrow/<uuid:escrow_id>/release/', views.release_escrow_payment, name='release_escrow_payment'),
    path('escrow/<uuid:escrow_id>/dispute/', views.dispute_escrow_payment, name='dispute_escrow_payment'),
    
    # Installment Plans
    path('installments/dashboard/', views.installment_dashboard, name='installment_dashboard'),
    path('installments/create/<uuid:order_id>/', views.create_installment_plan, name='create_installment_plan'),
    path('installments/pay/<uuid:payment_id>/', views.pay_installment, name='pay_installment'),
    
    # Commission System
    path('commissions/dashboard/', views.commission_dashboard, name='commission_dashboard'),
    path('commissions/payout-request/', views.request_commission_payout, name='request_commission_payout'),
    
    # Business Intelligence
    path('business-intelligence/', views.business_intelligence_dashboard, name='business_intelligence_dashboard'),
    path('analytics/report/', views.generate_analytics_report, name='generate_analytics_report'),
    
    # Security Features
    path('security/2fa/enable/', views.enable_2fa, name='enable_2fa'),
    path('security/2fa/verify/', views.verify_2fa, name='verify_2fa'),
    path('security/fraud-detection/', views.fraud_detection_dashboard, name='fraud_detection_dashboard'),
    
    # Advanced API Endpoints
    path('api/advanced-analytics/', views.advanced_analytics_data, name='advanced_analytics_data'),
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
    path('review/create/', views.ReviewListView.as_view(), name='review_create'),
    path('review/create/<uuid:order_id>/', views.ReviewCreateView.as_view(), name='review_create'),
    path('review/<uuid:pk>/', views.ReviewDetailView.as_view(), name='review_detail'),
]

# ============= CHAT =============
urlpatterns += [
    # Private chats (product-based)
    path('chat/', views.ChatListView.as_view(), name='chat_list'),
    path('chat/<uuid:pk>/', views.ChatDetailView.as_view(), name='chat_detail'),
    path('chat/create/<uuid:product_id>/', views.ChatCreateView.as_view(), name='chat_create'),
    
    # Group chats (new)
    path('group-chat/', views.GroupChatListView.as_view(), name='group_chat_list'),
    path('group-chat/<uuid:pk>/', views.GroupChatDetailView.as_view(), name='group_chat_detail'),
    path('group-chat/create/', views.GroupChatCreateView.as_view(), name='group_chat_create'),
    path('group-chat/<uuid:pk>/add-user/', views.GroupChatAddUserView.as_view(), name='group_chat_add_user'),
    path('group-chat/<uuid:pk>/leave/', views.GroupChatLeaveView.as_view(), name='group_chat_leave'),
]

# ============= PICKUP POINTS =============
urlpatterns += [
    path('pickup-points/', views.PickupPointListView.as_view(), name='pickup_point_list'),
    path('pickup-point/<uuid:pk>/', views.PickupPointDetailView.as_view(), name='pickup_point_detail'),
]

# ============= SELLER PROFILES =============
urlpatterns += [
    path('seller/<uuid:pk>/', additional_views.SellerProfileView.as_view(), name='seller_profile'),
]

# ============= ADMIN PANEL =============
# Admin URLs are now handled by backend/urls_admin.py
# This section has been moved to avoid duplication

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
    
    # Reviews
    path('ajax/reviewable-orders/', views.ajax_get_reviewable_orders
         if hasattr(views, 'ajax_get_reviewable_orders') else views.HomeView.as_view(),
         name='ajax_get_reviewable_orders'),
    
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
         
    # Group chat AJAX endpoints
    path('ajax/group-chat/messages/<uuid:chat_id>/', views.ajax_get_group_chat_messages, 
         name='ajax_get_group_chat_messages'),
    path('ajax/group-chat/send-message/', views.ajax_send_group_chat_message, 
         name='ajax_send_group_chat_message'),
    path('ajax/group-chat/mark-read/<uuid:message_id>/', views.ajax_mark_group_message_read, 
         name='ajax_mark_group_message_read'),
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
# ============= USER-TYPE-SPECIFIC ROUTES =============
urlpatterns += [
    # ============= CLIENT URLS =============
    path('client/', include('backend.urls_client', namespace='client')),
    
    # ============= STAFF URLS =============
    path('staff/', include('backend.urls_staff', namespace='staff')),
    
    # Admin interface (user_type = ADMIN)
    path('admin-panel/', include('backend.urls_admin', namespace='admin_panel')),
]

# ============= ERROR HANDLERS =============
handler404 = 'backend.views.handler404'
handler500 = 'backend.views.handler500'
handler403 = 'backend.views.handler403'