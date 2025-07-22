
# backend/urls.py (URLs principales de l'app)
from django.urls import path
from . import views

app_name = 'backend'

urlpatterns = [
    # Pages principales
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('search/', views.SearchView.as_view(), name='search'),
    
    # Authentification personnalisée
    path('auth/login/', views.CustomLoginView.as_view(), name='login'),
    path('auth/register/', views.CustomSignupView.as_view(), name='register'),
    path('auth/logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('auth/verify-phone/', views.PhoneVerificationView.as_view(), name='verify_phone'),
    path('auth/profile/', views.ProfileView.as_view(), name='profile'),
    path('auth/profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    
    # Produits
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<slug:slug>/edit/', views.ProductEditView.as_view(), name='product_edit'),
    path('products/<slug:slug>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('products/<slug:slug>/favorite/', views.FavoriteToggleView.as_view(), name='favorite_toggle'),
    
    # Catégories
    path('category/<slug:slug>/', views.CategoryView.as_view(), name='category'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    
    # Commandes et paiements
    path('order/create/<uuid:product_id>/', views.OrderCreateView.as_view(), name='order_create'),
    path('order/<uuid:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('payment/<uuid:order_id>/', views.PaymentView.as_view(), name='payment'),
    path('payment/<uuid:pk>/success/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('payment/<uuid:pk>/cancel/', views.PaymentCancelView.as_view(), name='payment_cancel'),
    
    # Chat et messages
    path('chat/', views.ChatListView.as_view(), name='chat_list'),
    path('chat/<uuid:pk>/', views.ChatDetailView.as_view(), name='chat_detail'),
    path('chat/create/<uuid:product_id>/', views.ChatCreateView.as_view(), name='chat_create'),
    
    # Avis et évaluations
    path('review/create/<uuid:order_id>/', views.ReviewCreateView.as_view(), name='review_create'),
    path('reviews/', views.ReviewListView.as_view(), name='review_list'),
    
    # Administration (pour les admins)
    path('admin-panel/', views.AdminPanelView.as_view(), name='admin_panel'),
    path('admin-panel/products/', views.AdminProductListView.as_view(), name='admin_product_list'),
    path('admin-panel/orders/', views.AdminOrderListView.as_view(), name='admin_order_list'),
    path('admin-panel/users/', views.AdminUserListView.as_view(), name='admin_user_list'),
    path('admin-panel/analytics/', views.AdminAnalyticsView.as_view(), name='admin_analytics'),
    path('admin-panel/stock/', views.AdminStockView.as_view(), name='admin_stock'),
    path('admin-panel/stock/add/', views.AdminStockAddView.as_view(), name='admin_stock_add'),
    
    # Points de retrait
    path('pickup-points/', views.PickupPointListView.as_view(), name='pickup_point_list'),
    path('pickup-point/<uuid:pk>/', views.PickupPointDetailView.as_view(), name='pickup_point_detail'),
    
    # Pages utilitaires
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('help/', views.HelpView.as_view(), name='help'),
    path('terms/', views.TermsView.as_view(), name='terms'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
    
    # API endpoints AJAX
    path('ajax/product-views/<uuid:pk>/', views.ProductViewAjax.as_view(), name='product_view_ajax'),
    path('ajax/notifications/', views.NotificationListAjax.as_view(), name='notification_ajax'),
    path('ajax/mark-notification-read/<uuid:pk>/', views.NotificationMarkReadAjax.as_view(), name='notification_read_ajax'),
    
    # Webhooks paiement
    path('webhooks/campay/', views.CampayWebhookView.as_view(), name='campay_webhook'),
    path('webhooks/orange-money/', views.OrangeMoneyWebhookView.as_view(), name='orange_webhook'),
    path('webhooks/mtn-money/', views.MTNMoneyWebhookView.as_view(), name='mtn_webhook'),
]