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
    
    # Visitor cart operations
    path('visitor/cart/add/<uuid:product_id>/', views.visitor_add_to_cart, name='visitor_add_to_cart'),
    path('visitor/cart/update/<uuid:item_id>/', views.visitor_update_cart_item, name='visitor_update_cart_item'),
    path('visitor/cart/remove/<uuid:item_id>/', views.visitor_remove_cart_item, name='visitor_remove_cart_item'),
    path('visitor/cart/', views.visitor_cart_view, name='visitor_cart'),
    path('visitor/cart/update-info/', views.visitor_update_cart_info, name='visitor_update_cart_info'),
    path('visitor/cart/checkout/', views.visitor_cart_checkout, name='visitor_cart_checkout'),
    path('visitor/cart/payment/', views.visitor_cart_payment, name='visitor_cart_payment'),
    path('visitor/cart/success/<str:cart_session>/', views.visitor_cart_success, name='visitor_cart_success'),
    
    # Product reporting
    path('visitor/report/<uuid:product_id>/', views.visitor_report_product, name='visitor_report_product'),
    
    # Receipt download
    path('visitor/receipt/download/', views.visitor_download_receipt, name='visitor_download_receipt'),
    
    # AJAX endpoints for cart widget
    path('visitor/cart/status/', views.visitor_cart_status, name='visitor_cart_status'),
    path('visitor/cart/preview/', views.visitor_cart_preview, name='visitor_cart_preview'),
    
    # Visitor favorites, compare, likes, comments, alerts
    path('visitor/favorite/toggle/<uuid:product_id>/', views.visitor_toggle_favorite, name='visitor_toggle_favorite'),
    path('visitor/favorites/', views.visitor_favorites_list, name='visitor_favorites_list'),
    path('visitor/compare/toggle/<uuid:product_id>/', views.visitor_toggle_compare, name='visitor_toggle_compare'),
    path('visitor/compare/', views.visitor_compare_list, name='visitor_compare_list'),
    path('visitor/comment/add/<uuid:product_id>/', views.visitor_add_comment, name='visitor_add_comment'),
    path('visitor/like/toggle/<uuid:product_id>/', views.visitor_toggle_like, name='visitor_toggle_like'),
    path('visitor/alert/create/<uuid:product_id>/', views.visitor_create_alert, name='visitor_create_alert'),
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