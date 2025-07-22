# backend/urls.py - URLs COMPLÈTES POUR VIDÉ-GRENIER KAMER

from django.urls import path
from . import views
from . import additional_views

app_name = 'backend'

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
    
    # ============= ADMINISTRATION =============
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
# Importer les vues supplémentaires
from . import additional_views

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