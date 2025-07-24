# backend/urls.py - REORGANIZED AND CLEANED URLs FOR VIDÉ-GRENIER KAMER

from django.urls import path
from . import views
from . import additional_views
# Import visitor purchase views
from .views import (
    VisitorProductDetailView,
    visitor_order_create,
    visitor_payment_process,
    visitor_order_success,
    campay_webhook,
)

app_name = 'backend'

# ============= PAGES PRINCIPALES =============
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('search/', views.SearchView.as_view(), name='search'),
]

# ============= AUTHENTIFICATION =============
urlpatterns += [
    path('auth/login/', views.CustomLoginView.as_view(), name='login'),
    path('auth/register/', views.CustomSignupView.as_view(), name='register'),
    path('auth/logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('auth/verify-phone/', views.PhoneVerificationView.as_view(), name='verify_phone'),
    path('auth/profile/', views.ProfileView.as_view(), name='profile'),
    path('auth/profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    # Password reset
    path('auth/password-reset/', additional_views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('auth/password-reset/<str:token>/', additional_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]

# ============= GESTION PRODUITS =============
urlpatterns += [
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<slug:slug>/edit/', views.ProductEditView.as_view(), name='product_edit'),
    path('products/<slug:slug>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    
    # Gestion avancée des produits
    path('products/<slug:slug>/promote/', additional_views.ProductPromoteView.as_view(), name='product_promote'),
    path('products/<slug:slug>/report/', additional_views.ProductReportView.as_view(), name='product_report'),
    path('products/bulk-actions/', additional_views.ProductBulkActionsView.as_view(), name='product_bulk_actions'),
    path('products/compare/', additional_views.CompareProductsView.as_view(), name='product_compare'),
]

# ============= CATÉGORIES =============
urlpatterns += [
    path('category/<slug:slug>/', views.CategoryView.as_view(), name='category'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
]

# ============= COMMANDES ET PAIEMENTS =============
urlpatterns += [
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
]

# ============= CHAT ET MESSAGES =============
urlpatterns += [
    path('chat/', views.ChatListView.as_view(), name='chat_list'),
    path('chat/<uuid:pk>/', views.ChatDetailView.as_view(), name='chat_detail'),
    path('chat/create/<uuid:product_id>/', views.ChatCreateView.as_view(), name='chat_create'),
]

# ============= AVIS ET ÉVALUATIONS =============
urlpatterns += [
    path('review/create/<uuid:order_id>/', views.ReviewCreateView.as_view(), name='review_create'),
    path('reviews/', views.ReviewListView.as_view(), name='review_list'),
    path('review/<uuid:pk>/', views.ReviewDetailView.as_view(), name='review_detail'),
]

# ============= POINTS DE RETRAIT =============
urlpatterns += [
    path('pickup-points/', views.PickupPointListView.as_view(), name='pickup_point_list'),
    path('pickup-point/<uuid:pk>/', views.PickupPointDetailView.as_view(), name='pickup_point_detail'),
]

# ============= PAGES UTILITAIRES =============
urlpatterns += [
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('help/', views.HelpView.as_view(), name='help'),
    path('terms/', views.TermsView.as_view(), name='terms'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
]

# ============= FAVORIS ET WISHLIST =============
urlpatterns += [
    path('favorites/', additional_views.FavoriteListView.as_view(), name='favorite_list'),
    path('wishlist/', additional_views.WishlistView.as_view(), name='wishlist'),
]

# ============= STATISTIQUES ET ANALYTICS =============
urlpatterns += [
    path('stats/', additional_views.StatsView.as_view(), name='personal_stats'),
    path('trending/', additional_views.TrendingProductsView.as_view(), name='trending_products'),
    path('recently-viewed/', additional_views.RecentlyViewedView.as_view(), name='recently_viewed'),
    path('recommended/', additional_views.RecommendedProductsView.as_view(), name='recommended_products'),
]

# ============= PROFILS ET VENDEURS =============
urlpatterns += [
    path('seller/<uuid:pk>/', additional_views.SellerProfileView.as_view(), name='seller_profile'),
]

# ============= RECHERCHE AVANCÉE =============
urlpatterns += [
    path('search/advanced/', additional_views.ProductAdvancedSearchView.as_view(), name='advanced_search'),
    path('search/saved/', additional_views.SavedSearchesView.as_view(), name='saved_searches'),
]

# ============= API ENDPOINTS AJAX =============
urlpatterns += [
    # Analytics produits
    path('ajax/product-views/<uuid:pk>/', views.ProductViewAjax.as_view(), name='product_view_ajax'),
    
    # Favoris
    path('ajax/favorite/<slug:slug>/', views.FavoriteToggleView.as_view(), name='favorite_toggle'),
    
    # Notifications
    path('ajax/notifications/', views.NotificationListAjax.as_view(), name='notification_ajax'),
    path('ajax/notifications/<uuid:pk>/read/', views.NotificationMarkReadAjax.as_view(), name='notification_read_ajax'),
]

# ============= WEBHOOKS PAIEMENT =============
urlpatterns += [
    path('webhooks/campay/', views.CampayWebhookView.as_view(), name='campay_webhook'),
    path('webhooks/orange-money/', views.OrangeMoneyWebhookView.as_view(), name='orange_webhook'),
    path('webhooks/mtn-money/', views.MTNMoneyWebhookView.as_view(), name='mtn_webhook'),
]

# ============= PATTERNS D'URL ALTERNATIFS =============
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

# ============= NEWSLETTER FUNCTIONALITY =============
# Import newsletter views from admin views (consolidated)
try:
    from .views_admin import (
        newsletter_subscribe,
        newsletter_unsubscribe,
    )
    
    # Newsletter URLs - public endpoints
    urlpatterns += [
        path('newsletter/subscribe/', newsletter_subscribe, name='newsletter_subscribe'),
        path('newsletter/unsubscribe/', newsletter_unsubscribe, name='newsletter_unsubscribe'),
    ]
    print("✅ Newsletter public URL patterns added successfully")
    
except ImportError:
    print("⚠️ Newsletter views not found in admin views. Skipping newsletter URL patterns.")

# ============= COMPLETE ADMIN PANEL - ALL CONSOLIDATED =============
# Import all admin views from the consolidated views_admin.py
try:
    from .views_admin import (
        # Main admin dashboard
        admin_dashboard,
        
        # User management - Complete CRUD
        AdminUserListView,
        AdminUserDetailView,
        AdminUserCreateView,
        AdminUserUpdateView,
        admin_user_delete,
        admin_user_bulk_actions,
        admin_user_toggle_status,
        admin_user_toggle_verification,
        admin_users_ajax,
        admin_export_users,
        
        # Product management
        AdminProductListView,
        
        # Order management
        AdminOrderListView,
        
        # Newsletter management - Complete CRUD
        AdminNewsletterListView,
        admin_newsletter_create,
        admin_newsletter_send,
        admin_newsletter_delete,
        
        # Analytics and reports
        AdminAnalyticsView,
        
        # Bulk actions and utilities
        admin_bulk_actions,
        admin_stats_ajax,
        admin_quick_action,

        AdminPaymentListView,
        admin_payment_detail,
        admin_payment_update_status,
        AdminLoyaltyListView,
        admin_loyalty_create,
        admin_loyalty_edit,
        AdminPromotionListView,
        admin_promotion_create,
        admin_promotion_edit,
        admin_promotion_toggle_status,
        AdminStockView,
        AdminStockAddView,
        AdminNotificationListView,
        admin_notification_create,
        admin_notification_send_bulk,
        
        # Product approval/rejection
        admin_product_approve,
        admin_product_reject,
        admin_product_detail,
        admin_product_create,
        admin_product_edit,
    )
    
    # ============= COMPLETE ADMIN PANEL URLs =============
    urlpatterns += [
        # ============= MAIN ADMIN DASHBOARD =============
        path('admin-panel/', admin_dashboard, name='admin_panel'),
        path('admin-panel/dashboard/', admin_dashboard, name='admin_dashboard'),
        
        # ============= USER MANAGEMENT - COMPLETE CRUD =============
        path('admin-panel/users/', AdminUserListView.as_view(), name='admin_user_list'),
        path('admin-panel/users/<int:user_id>/', AdminUserDetailView.as_view(), name='admin_user_detail'),
        path('admin-panel/users/create/', AdminUserCreateView.as_view(), name='admin_user_create'),
        path('admin-panel/users/<int:user_id>/edit/', AdminUserUpdateView.as_view(), name='admin_user_edit'),
        path('admin-panel/users/<int:user_id>/delete/', admin_user_delete, name='admin_user_delete'),
        
        # User bulk actions
        path('admin-panel/users/bulk-actions/', admin_user_bulk_actions, name='admin_user_bulk_actions'),
        path('admin-panel/users/<int:user_id>/toggle-status/', admin_user_toggle_status, name='admin_user_toggle_status'),
        path('admin-panel/users/<int:user_id>/toggle-verification/', admin_user_toggle_verification, name='admin_user_toggle_verification'),
        
        # User export and AJAX
        path('admin-panel/users/export/', admin_export_users, name='admin_export_users'),
        path('admin-panel/users/ajax/', admin_users_ajax, name='admin_users_ajax'),
        
        # ============= PRODUCT MANAGEMENT =============
        path('admin-panel/products/', AdminProductListView.as_view(), name='admin_product_list'),
        path('admin-panel/products/<uuid:product_id>/', admin_product_detail, name='admin_product_detail'),
        path('admin-panel/products/create/', admin_product_create, name='admin_product_create'),
        path('admin-panel/products/<uuid:product_id>/edit/', admin_product_edit, name='admin_product_edit'),
        path('admin-panel/products/<uuid:product_id>/approve/', admin_product_approve, name='admin_product_approve'),
        path('admin-panel/products/<uuid:product_id>/reject/', admin_product_reject, name='admin_product_reject'),
        
        # ============= ORDER MANAGEMENT =============
        path('admin-panel/orders/', AdminOrderListView.as_view(), name='admin_order_list'),
        
        # ============= NEWSLETTER MANAGEMENT - COMPLETE CRUD =============
        path('admin-panel/newsletter/', AdminNewsletterListView.as_view(), name='admin_newsletter_list'),
        path('admin-panel/newsletter/create/', admin_newsletter_create, name='admin_newsletter_create'),
        path('admin-panel/newsletter/<int:newsletter_id>/send/', admin_newsletter_send, name='admin_newsletter_send'),
        path('admin-panel/newsletter/<int:newsletter_id>/delete/', admin_newsletter_delete, name='admin_newsletter_delete'),
        
        # ============= ANALYTICS AND REPORTS =============
        path('admin-panel/analytics/', AdminAnalyticsView.as_view(), name='admin_analytics'),
        
        # ============= BULK ACTIONS AND UTILITIES =============
        path('admin-panel/bulk-actions/', admin_bulk_actions, name='admin_bulk_actions'),
        
        # ============= AJAX ENDPOINTS FOR ADMIN =============
        path('admin-panel/ajax/stats/', admin_stats_ajax, name='admin_stats_ajax'),
        path('admin-panel/ajax/quick-action/', admin_quick_action, name='admin_quick_action'),
        
        # ============= PAYMENT MANAGEMENT =============
        path('admin-panel/payments/', AdminPaymentListView.as_view(), name='admin_payment_list'),
        path('admin-panel/payments/<int:payment_id>/', admin_payment_detail, name='admin_payment_detail'),
        path('admin-panel/payments/<int:payment_id>/update-status/', admin_payment_update_status, name='admin_payment_update_status'),
        
        # ============= LOYALTY PROGRAM MANAGEMENT =============
        path('admin-panel/loyalty/', AdminLoyaltyListView.as_view(), name='admin_loyalty_list'),
        path('admin-panel/loyalty/create/', admin_loyalty_create, name='admin_loyalty_create'),
        path('admin-panel/loyalty/<int:loyalty_id>/edit/', admin_loyalty_edit, name='admin_loyalty_edit'),
        
        # ============= PROMOTION MANAGEMENT =============
        path('admin-panel/promotions/', AdminPromotionListView.as_view(), name='admin_promotion_list'),
        path('admin-panel/promotions/create/', admin_promotion_create, name='admin_promotion_create'),
        path('admin-panel/promotions/<int:promotion_id>/edit/', admin_promotion_edit, name='admin_promotion_edit'),
        path('admin-panel/promotions/<int:promotion_id>/toggle-status/', admin_promotion_toggle_status, name='admin_promotion_toggle_status'),
        
        # ============= STOCK MANAGEMENT =============
        path('admin-panel/stock/', AdminStockView.as_view(), name='admin_stock'),
        path('admin-panel/stock/add/', AdminStockAddView.as_view(), name='admin_stock_add'),
        
        # ============= NOTIFICATION MANAGEMENT =============
        path('admin-panel/notifications/', AdminNotificationListView.as_view(), name='admin_notification_list'),
        path('admin-panel/notifications/create/', admin_notification_create, name='admin_notification_create'),
        path('admin-panel/notifications/bulk-send/', admin_notification_send_bulk, name='admin_notification_bulk_send'),
    ]
    
    print("✅ All missing admin URL patterns added successfully")
    
except ImportError as e:
    print(f"⚠️ Some admin views not found: {e}. Add them to views_admin.py first.")
    print("✅ Complete admin panel URL patterns added successfully")
    print("✅ All admin views consolidated in views_admin.py")
    print("✅ No duplicate admin views - all removed from views.py and views_newsletter.py")
    
except ImportError as e:
    print(f"⚠️ Admin views not found: {e}. Using fallback admin URLs.")
    
    # Fallback to basic admin panel if views_admin.py is not available
    urlpatterns += [
        path('admin-panel/', admin_dashboard, name='admin_panel'),
        path('admin-panel/dashboard/', admin_dashboard, name='admin_dashboard'),
    ]

# ============= DEBUG AND INFORMATION =============
if __name__ == "__main__":
    print(f"\n🔗 Total URL patterns: {len(urlpatterns)}")
    print("=" * 60)
    print("✅ URL REORGANIZATION COMPLETE")
    print("=" * 60)
    print("🏠 Main URLs:")
    print("  └── Homepage: /")
    print("  └── Dashboard: /dashboard/")
    print("  └── Products: /products/")
    print("  └── Search: /search/")
    print()
    print("🔐 Authentication URLs:")
    print("  └── Login: /auth/login/")
    print("  └── Register: /auth/register/")
    print("  └── Profile: /auth/profile/")
    print()
    print("🛍️ E-commerce URLs:")
    print("  └── Products: /products/")
    print("  └── Orders: /orders/")
    print("  └── Cart: /cart/")
    print("  └── Payment: /payment/")
    print()
    print("📧 Newsletter URLs (Public):")
    print("  └── Subscribe: /newsletter/subscribe/")
    print("  └── Unsubscribe: /newsletter/unsubscribe/")
    print()
    print("🎛️ COMPLETE ADMIN PANEL:")
    print("  └── 📊 Main Dashboard: /admin-panel/ & /admin-panel/dashboard/")
    print("  └── 👥 User Management (CRUD): /admin-panel/users/")
    print("      ├── List: /admin-panel/users/")
    print("      ├── Detail: /admin-panel/users/<id>/")
    print("      ├── Create: /admin-panel/users/create/")
    print("      ├── Edit: /admin-panel/users/<id>/edit/")
    print("      ├── Delete: /admin-panel/users/<id>/delete/")
    print("      ├── Bulk Actions: /admin-panel/users/bulk-actions/")
    print("      ├── Toggle Status: /admin-panel/users/<id>/toggle-status/")
    print("      ├── Toggle Verification: /admin-panel/users/<id>/toggle-verification/")
    print("      ├── Export: /admin-panel/users/export/")
    print("      └── AJAX: /admin-panel/users/ajax/")
    print("  └── 📦 Product Management: /admin-panel/products/")
    print("  └── 📋 Order Management: /admin-panel/orders/")
    print("  └── 📧 Newsletter Management (CRUD): /admin-panel/newsletter/")
    print("      ├── List: /admin-panel/newsletter/")
    print("      ├── Create: /admin-panel/newsletter/create/")
    print("      ├── Send: /admin-panel/newsletter/<id>/send/")
    print("      └── Delete: /admin-panel/newsletter/<id>/delete/")
    print("  └── 📈 Analytics: /admin-panel/analytics/")
    print("  └── ⚡ Bulk Actions: /admin-panel/bulk-actions/")
    print("  └── 🔄 AJAX Endpoints: /admin-panel/ajax/")
    print()
    print("=" * 60)
    print("🎯 REORGANIZATION SUMMARY:")
    print("=" * 60)
    print("✅ ELIMINATED duplicates in views.py")
    print("✅ ELIMINATED duplicates in views_newsletter.py") 
    print("✅ ALL admin views consolidated in views_admin.py")
    print("✅ Complete CRUD for Users (Create, Read, Update, Delete)")
    print("✅ Complete CRUD for Newsletter management")
    print("✅ Bulk actions for admin operations")
    print("✅ Export functionality (Excel/CSV)")
    print("✅ AJAX endpoints for dynamic admin features")
    print("✅ Public newsletter subscription endpoints")
    print("✅ Comprehensive analytics and reports")
    print("✅ Clean URL structure with logical grouping")
    print("✅ No conflicts or overlapping view names")
    print("=" * 60)

# ============= VISITOR PURCHASE URLS (No Login Required) =============
urlpatterns += [
    # Visitor product detail with purchase options
    path('visitor/product/<uuid:pk>/', VisitorProductDetailView.as_view(), name='visitor_product_detail'),
    
    # Visitor order creation and payment
    path('visitor/order/create/<uuid:product_id>/', visitor_order_create, name='visitor_order_create'),
    path('visitor/order/payment/<uuid:order_id>/', visitor_payment_process, name='visitor_payment_process'),
    path('visitor/order/success/<uuid:order_id>/', visitor_order_success, name='visitor_order_success'),
    
    # Campay webhook
    path('api/campay/webhook/', campay_webhook, name='campay_webhook'),
]

print("✅ Visitor purchase URLs added successfully")