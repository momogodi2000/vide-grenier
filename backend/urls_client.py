# backend/urls_client.py - CLIENT-SPECIFIC URL PATTERNS
from django.urls import path, include
from . import views_client

app_name = 'client'

urlpatterns = [
    # ============= DASHBOARD =============
    path('', views_client.ClientDashboardView.as_view(), name='dashboard'),
    
    # ============= WALLET MANAGEMENT =============
    path('wallet/', views_client.WalletView.as_view(), name='wallet'),
    path('wallet/transactions/', views_client.WalletTransactionsView.as_view(), name='wallet_transactions'),
    path('wallet/add-funds/', views_client.AddFundsView.as_view(), name='add_funds'),
    path('wallet/withdraw/', views_client.WithdrawRequestView.as_view(), name='withdraw_request'),
    
    # ============= PRODUCT MANAGEMENT =============
    path('products/', views_client.ClientProductsView.as_view(), name='products'),
    path('products/create/', views_client.ProductCreateView.as_view(), name='product_create'),
    path('products/<uuid:pk>/', views_client.ClientProductDetailView.as_view(), name='product_detail'),
    path('products/<uuid:pk>/edit/', views_client.ProductEditView.as_view(), name='product_edit'),
    path('products/<uuid:pk>/delete/', views_client.ProductDeleteView.as_view(), name='product_delete'),
    
    # ============= SHOPPING & PURCHASING =============
    path('browse/', views_client.BrowseProductsView.as_view(), name='browse_products'),
    path('category/<slug:slug>/', views_client.CategoryProductsView.as_view(), name='category_products'),
    path('purchases/', views_client.ClientPurchasesView.as_view(), name='purchases'),
    path('purchases/<uuid:pk>/', views_client.PurchaseDetailView.as_view(), name='purchase_detail'),
    path('sales/', views_client.ClientSalesView.as_view(), name='sales'),
    path('sales/<uuid:pk>/', views_client.SaleDetailView.as_view(), name='sale_detail'),
    
    # ============= SHOPPING CART =============
    path('cart/', views_client.ShoppingCartView.as_view(), name='shopping_cart'),
    path('cart/add/', views_client.add_to_cart, name='add_to_cart'),
    path('cart/update/', views_client.update_cart_item, name='update_cart_item'),
    path('cart/remove/', views_client.remove_cart_item, name='remove_cart_item'),
    path('cart/checkout/', views_client.checkout_cart, name='checkout_cart'),
    
    # ============= WISHLIST & FAVORITES =============
    path('wishlist/', views_client.WishlistListView.as_view(), name='wishlist_list'),
    path('wishlist/<uuid:pk>/', views_client.WishlistDetailView.as_view(), name='wishlist_detail'),
    path('wishlist/add/', views_client.add_to_wishlist, name='add_to_wishlist'),
    path('favorites/', views_client.ClientFavoritesView.as_view(), name='favorites'),
    path('compare/', views_client.CompareProductsView.as_view(), name='compare'),
    
    # ============= AI & RECOMMENDATIONS =============
    path('recommendations/', views_client.RecommendationsView.as_view(), name='recommendations'),
    path('recommendations/feedback/', views_client.recommendation_feedback, name='recommendation_feedback'),
    path('search/smart/', views_client.SmartSearchView.as_view(), name='smart_search'),
    path('analytics/personal/', views_client.PersonalAnalyticsView.as_view(), name='personal_analytics'),
    
    # ============= SOCIAL FEATURES =============
    path('social/feed/', views_client.SocialFeedView.as_view(), name='social_feed'),
    path('social/follow/', views_client.UserFollowView.as_view(), name='user_follow'),
    path('social/post/create/', views_client.CreateSocialPostView.as_view(), name='create_social_post'),
    
    # ============= COMMUNICATION =============
    path('chats/', views_client.ClientChatsView.as_view(), name='chats'),
    path('chats/<uuid:pk>/', views_client.ClientChatDetailView.as_view(), name='chat_detail'),
    path('admin-chat/', views_client.ClientAdminChatView.as_view(), name='admin_chat'),
    
    # ============= PROFILE & SETTINGS =============
    path('profile/', views_client.ClientProfileView.as_view(), name='profile'),
    path('profile/edit/', views_client.ClientProfileEditView.as_view(), name='profile_edit'),
    path('notifications/', views_client.ClientNotificationsView.as_view(), name='notifications'),
    path('notifications/mark-read/', views_client.MarkNotificationReadView.as_view(), name='mark_notification_read'),
    
    # ============= ENHANCED FEATURES =============
    path('review/create/enhanced/<uuid:order_id>/', views_client.EnhancedReviewCreateView.as_view(), name='create_enhanced_review'),
] 