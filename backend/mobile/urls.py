from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MobileAuthViewSet, MobileProductViewSet, MobileCategoryViewSet,
    MobileOrderViewSet, MobileUserViewSet, MobileSearchView,
    MobileHealthCheckView, MobilePickupPointViewSet, MobileWalletViewSet,
    MobileVisitorViewSet, MobileAdminViewSet, MobilePaymentView
)

# Create router for mobile API
router = DefaultRouter()
router.register(r'auth', MobileAuthViewSet, basename='mobile-auth')
router.register(r'products', MobileProductViewSet, basename='mobile-products')
router.register(r'categories', MobileCategoryViewSet, basename='mobile-categories')
router.register(r'orders', MobileOrderViewSet, basename='mobile-orders')
router.register(r'user', MobileUserViewSet, basename='mobile-user')
router.register(r'pickup-points', MobilePickupPointViewSet, basename='mobile-pickup-points')
router.register(r'wallet', MobileWalletViewSet, basename='mobile-wallet')
router.register(r'visitor', MobileVisitorViewSet, basename='mobile-visitor')
router.register(r'admin', MobileAdminViewSet, basename='mobile-admin')

# Mobile API URL patterns
urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Search endpoint
    path('search/', MobileSearchView.as_view(), name='mobile-search'),
    
    # Health check endpoint
    path('health/', MobileHealthCheckView.as_view(), name='mobile-health'),
    
    # Payment endpoint
    path('payment/', MobilePaymentView.as_view(), name='mobile-payment'),
] 