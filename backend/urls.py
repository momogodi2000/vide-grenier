# backend/urls.py - URLs COMPLÈTES POUR VIDÉ-GRENIER KAMER - FIXED VERSION

from django.urls import path
from . import views
from . import additional_views

app_name = 'backend'

# ============= ALL YOUR EXISTING URLS - PRESERVED =============
urlpatterns = [
    # ============= PAGES PRINCIPALES =============
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('search/', views.SearchView.as_view(), name='search'),
    
    # ============= AUTHENTIFICATION =============
    path('auth/login/', views.CustomLoginView.as_view(), name='login'),
    path('auth/register/', views.CustomSignupView.as_view(), name='register'),
    path('auth/logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('auth/verify-phone/', views.PhoneVerificationView.as_view(), name='verify_phone'),
    path('auth/profile/', views.ProfileView.as_view(), name='profile'),
    path('auth/profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    # Password reset
    path('auth/password-reset/', additional_views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('auth/password-reset/<str:token>/', additional_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # ============= GESTION PRODUITS =============
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<slug:slug>/edit/', views.ProductEditView.as_view(), name='product_edit'),
    path('products/<slug:slug>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    
    # ============= CATÉGORIES =============
    path('category/<slug:slug>/', views.CategoryView.as_view(), name='category'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    
    # ============= COMMANDES ET PAIEMENTS =============
    # Commandes pour utilisateurs connectés
    path('order/create/<uuid:product_id>/', views.OrderCreateView.as_view(), name='order_create'),
    path('order/<uuid:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    
    # Commandes publiques (paiement à la livraison)
    path('order/public/<slug:slug>/', views.PublicOrderCreateView.as_view(), name='public_order_create'),
    path('order/public/success/<str:order_number>/', views.PublicOrderSuccessView.as_view(), name='public_order_success'),
    
    # Paiements
    path('payment/<uuid:order_id>/', views.PaymentView.as_view(), name='payment'),
    path('payment/<uuid:pk>/success/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('payment/<uuid:pk>/cancel/', views.PaymentCancelView.as_view(), name='payment_cancel'),
    
    # ============= CHAT ET MESSAGES =============
    path('chat/', views.ChatListView.as_view(), name='chat_list'),
    path('chat/<uuid:pk>/', views.ChatDetailView.as_view(), name='chat_detail'),
    path('chat/create/<uuid:product_id>/', views.ChatCreateView.as_view(), name='chat_create'),
    
    # ============= AVIS ET ÉVALUATIONS =============
    path('review/create/<uuid:order_id>/', views.ReviewCreateView.as_view(), name='review_create'),
    path('reviews/', views.ReviewListView.as_view(), name='review_list'),
    path('review/<uuid:pk>/', views.ReviewDetailView.as_view(), name='review_detail'),
    
    # ============= ADMINISTRATION EXISTANTE =============
    path('admin-panel/', views.AdminPanelView.as_view(), name='admin_panel'),
    path('admin-panel/products/', views.AdminProductListView.as_view(), name='admin_product_list'),
    path('admin-panel/orders/', views.AdminOrderListView.as_view(), name='admin_order_list'),
    path('admin-panel/users/', views.AdminUserListView.as_view(), name='admin_user_list'),
    path('admin-panel/analytics/', views.AdminAnalyticsView.as_view(), name='admin_analytics'),
    
    # Gestion Stock Admin
    path('admin-panel/stock/', views.AdminStockView.as_view(), name='admin_stock'),
    path('admin-panel/stock/add/', views.AdminStockAddView.as_view(), name='admin_stock_add'),
    
    # ============= POINTS DE RETRAIT =============
    path('pickup-points/', views.PickupPointListView.as_view(), name='pickup_point_list'),
    path('pickup-point/<uuid:pk>/', views.PickupPointDetailView.as_view(), name='pickup_point_detail'),
    
    # ============= PAGES UTILITAIRES =============
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('help/', views.HelpView.as_view(), name='help'),
    path('terms/', views.TermsView.as_view(), name='terms'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
    
    # ============= API ENDPOINTS AJAX =============
    # Analytics produits
    path('ajax/product-views/<uuid:pk>/', views.ProductViewAjax.as_view(), name='product_view_ajax'),
    
    # Favoris
    path('ajax/favorite/<slug:slug>/', views.FavoriteToggleView.as_view(), name='favorite_toggle'),
    
    # Notifications
    path('ajax/notifications/', views.NotificationListAjax.as_view(), name='notification_ajax'),
    path('ajax/notifications/<uuid:pk>/read/', views.NotificationMarkReadAjax.as_view(), name='notification_read_ajax'),
    
    # ============= WEBHOOKS PAIEMENT =============
    path('webhooks/campay/', views.CampayWebhookView.as_view(), name='campay_webhook'),
    path('webhooks/orange-money/', views.OrangeMoneyWebhookView.as_view(), name='orange_webhook'),
    path('webhooks/mtn-money/', views.MTNMoneyWebhookView.as_view(), name='mtn_webhook'),
]

# ============= PATTERNS D'URL ALTERNATIFS =============
# Patterns pour compatibilité et SEO

# URLs courtes pour partage
urlpatterns += [
    # Produit court: /p/slug/
    path('p/<slug:slug>/', views.ProductDetailView.as_view(), name='product_short'),
    
    # Catégorie courte: /c/slug/
    path('c/<slug:slug>/', views.CategoryView.as_view(), name='category_short'),
    
    # Commande rapide: /buy/slug/
    path('buy/<slug:slug>/', views.PublicOrderCreateView.as_view(), name='quick_buy'),
]

# URLs pour mobile/PWA
urlpatterns += [
    # Version mobile du dashboard
    path('m/dashboard/', views.DashboardView.as_view(), {'mobile': True}, name='mobile_dashboard'),
    
    # Recherche mobile optimisée
    path('m/search/', views.SearchView.as_view(), {'mobile': True}, name='mobile_search'),
]

# URLs pour API future
urlpatterns += [
    # Endpoints pour app mobile future
    path('api/v1/products/', views.ProductListView.as_view(), {'format': 'json'}, name='api_products'),
    path('api/v1/categories/', views.CategoryListView.as_view(), {'format': 'json'}, name='api_categories'),
]

# ============= URLS SUPPLÉMENTAIRES AVANCÉES =============
# Favoris et Wishlist
urlpatterns += [
    path('favorites/', additional_views.FavoriteListView.as_view(), name='favorite_list'),
    path('wishlist/', additional_views.WishlistView.as_view(), name='wishlist'),
]

# Statistiques et Analytics
urlpatterns += [
    path('stats/', additional_views.StatsView.as_view(), name='personal_stats'),
    path('trending/', additional_views.TrendingProductsView.as_view(), name='trending_products'),
    path('recently-viewed/', additional_views.RecentlyViewedView.as_view(), name='recently_viewed'),
    path('recommended/', additional_views.RecommendedProductsView.as_view(), name='recommended_products'),
]

# Gestion avancée des produits
urlpatterns += [
    path('products/<slug:slug>/promote/', additional_views.ProductPromoteView.as_view(), name='product_promote'),
    path('products/<slug:slug>/report/', additional_views.ProductReportView.as_view(), name='product_report'),
    path('products/bulk-actions/', additional_views.ProductBulkActionsView.as_view(), name='product_bulk_actions'),
    path('products/compare/', additional_views.CompareProductsView.as_view(), name='product_compare'),
]

# Profils et vendeurs
urlpatterns += [
    path('seller/<uuid:pk>/', additional_views.SellerProfileView.as_view(), name='seller_profile'),
]

# Recherche avancée
urlpatterns += [
    path('search/advanced/', additional_views.ProductAdvancedSearchView.as_view(), name='advanced_search'),
    path('search/saved/', additional_views.SavedSearchesView.as_view(), name='saved_searches'),
]

# ============= NEWSLETTER FUNCTIONALITY =============
# Only import newsletter views if they exist
try:
    from .views_newsletter import (
        newsletter_subscribe,
        newsletter_unsubscribe,
        newsletter_send_mass,
        newsletter_schedule,
    )
    
    # Newsletter URLs - using different namespace to avoid conflicts
    urlpatterns += [
        path('newsletter/subscribe/', newsletter_subscribe, name='newsletter_subscribe'),
        path('newsletter/unsubscribe/', newsletter_unsubscribe, name='newsletter_unsubscribe'),
        path('newsletter/send-mass/', newsletter_send_mass, name='newsletter_send_mass'),
        path('newsletter/schedule/', newsletter_schedule, name='newsletter_schedule'),
    ]
    print("✅ Newsletter URL patterns added successfully")
    
except ImportError:
    print("⚠️ Newsletter views not found. Skipping newsletter URL patterns.")

# ============= ADVANCED ADMIN FUNCTIONALITY =============
# Only import admin views if they exist
try:
    from .views_admin import (
        AdminPaymentListView,
        AdminLoyaltyListView, 
        AdminPromotionListView,
        AdminNewsletterListView,
        AdminNotificationListView,
        admin_payment_detail,
        admin_payment_update_status,
        admin_loyalty_create,
        admin_loyalty_edit,
        admin_promotion_create,
        admin_promotion_edit,
        admin_promotion_toggle_status,
        admin_newsletter_create,
        admin_newsletter_send,
        admin_newsletter_delete,
        admin_notification_create,
        admin_notification_send_bulk,
        admin_dashboard,
    )
    
    # Advanced Admin URLs - using 'system' prefix to avoid conflicts with existing admin-panel
    urlpatterns += [
        # System Admin Dashboard (different from your existing admin-panel)
        path('system/dashboard/', admin_dashboard, name='system_admin_dashboard'),
        
        # Payment Management (separate from your existing payment views)
        path('system/payments/', AdminPaymentListView.as_view(), name='system_payment_list'),
        path('system/payments/<int:payment_id>/', admin_payment_detail, name='system_payment_detail'),
        path('system/payments/<int:payment_id>/update-status/', admin_payment_update_status, name='system_payment_update_status'),
        
        # Loyalty Program Management
        path('system/loyalty/', AdminLoyaltyListView.as_view(), name='system_loyalty_list'),
        path('system/loyalty/create/', admin_loyalty_create, name='system_loyalty_create'),
        path('system/loyalty/<int:loyalty_id>/edit/', admin_loyalty_edit, name='system_loyalty_edit'),
        
        # Promotion Management
        path('system/promotions/', AdminPromotionListView.as_view(), name='system_promotion_list'),
        path('system/promotions/create/', admin_promotion_create, name='system_promotion_create'),
        path('system/promotions/<int:promotion_id>/edit/', admin_promotion_edit, name='system_promotion_edit'),
        path('system/promotions/<int:promotion_id>/toggle-status/', admin_promotion_toggle_status, name='system_promotion_toggle_status'),
        
        # Newsletter Management
        path('system/newsletter/', AdminNewsletterListView.as_view(), name='system_newsletter_list'),
        path('system/newsletter/create/', admin_newsletter_create, name='system_newsletter_create'),
        path('system/newsletter/<int:newsletter_id>/send/', admin_newsletter_send, name='system_newsletter_send'),
        path('system/newsletter/<int:newsletter_id>/delete/', admin_newsletter_delete, name='system_newsletter_delete'),
        
        # Notification Management
        path('system/notifications/', AdminNotificationListView.as_view(), name='system_notification_list'),
        path('system/notifications/create/', admin_notification_create, name='system_notification_create'),
        path('system/notifications/bulk-send/', admin_notification_send_bulk, name='system_notification_bulk_send'),
    ]
    print("✅ Advanced admin URL patterns added successfully")
    
except ImportError:
    print("⚠️ Advanced admin views not found. Skipping advanced admin URL patterns.")

# Debug information
if __name__ == "__main__":
    print(f"\n🔗 Total URL patterns: {len(urlpatterns)}")
    print("✅ All existing URLs preserved")
    print("🏠 Homepage: /")
    print("📊 Dashboard: /dashboard/")
    print("🛍️ Products: /products/")
    print("📧 Newsletter: /newsletter/")
    print("🔧 System Admin: /system/")
    print("🎛️ Admin Panel: /admin-panel/ (your existing)")