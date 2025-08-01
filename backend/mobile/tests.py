from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from backend.models import Product, Category, VisitorCart, VisitorCartItem, PickupPoint
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class MobileAPITestCase(APITestCase):
    """Test cases for mobile API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            user_type='CLIENT'
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            user_type='ADMIN'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            description='Electronic devices'
        )
        
        # Create test product
        self.product = Product.objects.create(
            title='Test Product',
            description='A test product',
            price=10000,
            condition='GOOD',
            category=self.category,
            seller=self.user,
            city='DOUALA'
        )
        
        # Create test pickup point
        self.pickup_point = PickupPoint.objects.create(
            name='Test Pickup Point',
            address='123 Test Street',
            city='DOUALA',
            phone='+237123456789',
            is_active=True
        )
    
    def test_health_check(self):
        """Test health check endpoint"""
        url = reverse('mobile-health')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')
    
    def test_products_list(self):
        """Test products list endpoint"""
        url = reverse('mobile-products-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_categories_list(self):
        """Test categories list endpoint"""
        url = reverse('mobile-categories-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_search_products(self):
        """Test search endpoint"""
        url = reverse('mobile-search')
        response = self.client.get(url, {'q': 'test'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_authentication_required(self):
        """Test that authentication is required for protected endpoints"""
        url = reverse('mobile-user-profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_profile_authenticated(self):
        """Test user profile endpoint with authentication"""
        self.client.force_authenticate(user=self.user)
        url = reverse('mobile-user-profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['email'], self.user.email)
    
    def test_login_without_2fa(self):
        """Test login without 2FA"""
        url = reverse('mobile-auth-login')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['requires_2fa'])
        self.assertIn('tokens', response.data)
    
    def test_login_with_2fa(self):
        """Test login with 2FA enabled"""
        # Enable 2FA for user
        self.user.two_factor_enabled = True
        self.user.save()
        
        url = reverse('mobile-auth-login')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['requires_2fa'])
        self.assertIn('message', response.data)
    
    def test_verify_2fa(self):
        """Test 2FA verification"""
        # Set up 2FA code for user
        self.user.verification_code = '123456'
        self.user.verification_code_expires = timezone.now() + timedelta(minutes=10)
        self.user.save()
        
        url = reverse('mobile-auth-verify_2fa')
        data = {
            'email': 'test@example.com',
            'code': '123456'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
    
    def test_register_with_phone_verification(self):
        """Test registration with phone verification"""
        url = reverse('mobile-auth-register')
        data = {
            'email': 'newuser@example.com',
            'phone': '+237123456789',
            'password': 'newpass123',
            'confirm_password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'user_type': 'CLIENT',
            'city': 'DOUALA'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['requires_phone_verification'])
        self.assertIn('user_id', response.data)
    
    def test_visitor_add_to_cart(self):
        """Test visitor add to cart"""
        url = reverse('mobile-visitor-add_to_cart')
        data = {
            'product_id': str(self.product.id),
            'quantity': 2,
            'session_key': 'test_session_123'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cart', response.data)
    
    def test_visitor_get_cart(self):
        """Test visitor get cart"""
        # Create a cart first
        cart = VisitorCart.objects.create(session_key='test_session_123')
        VisitorCartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1
        )
        
        url = reverse('mobile-visitor-cart')
        response = self.client.get(url, {'session_key': 'test_session_123'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cart', response.data)
    
    def test_visitor_create_order(self):
        """Test visitor create order"""
        # Create a cart first
        cart = VisitorCart.objects.create(session_key='test_session_123')
        VisitorCartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1
        )
        
        url = reverse('mobile-visitor-create_order')
        data = {
            'session_key': 'test_session_123',
            'customer_name': 'John Doe',
            'customer_phone': '+237123456789',
            'customer_email': 'john@example.com',
            'pickup_point_id': str(self.pickup_point.id)
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('orders', response.data)
    
    def test_admin_dashboard_stats(self):
        """Test admin dashboard statistics"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('mobile-admin-dashboard_stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('stats', response.data)
    
    def test_admin_users_list(self):
        """Test admin users list"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('mobile-admin-users')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_admin_pending_products(self):
        """Test admin pending products"""
        # Create a pending product
        pending_product = Product.objects.create(
            title='Pending Product',
            description='A pending product',
            price=5000,
            condition='GOOD',
            category=self.category,
            seller=self.user,
            city='DOUALA',
            status='PENDING'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('mobile-admin-pending_products')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_admin_approve_product(self):
        """Test admin approve product"""
        # Create a pending product
        pending_product = Product.objects.create(
            title='Pending Product',
            description='A pending product',
            price=5000,
            condition='GOOD',
            category=self.category,
            seller=self.user,
            city='DOUALA',
            status='PENDING'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('mobile-admin-approve_product', kwargs={'pk': pending_product.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that product status was updated
        pending_product.refresh_from_db()
        self.assertEqual(pending_product.status, 'ACTIVE')
    
    def test_payment_process(self):
        """Test payment processing"""
        url = reverse('mobile-payment')
        data = {
            'amount': 25000,
            'payment_method': 'MOBILE_MONEY',
            'phone_number': '+237123456789'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('reference', response.data)
    
    def test_payment_verification(self):
        """Test payment verification"""
        url = reverse('mobile-payment')
        data = {
            'reference': 'PAY_ABC12345',
            'transaction_id': 'transaction_123'
        }
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_user_setup_2fa(self):
        """Test user 2FA setup"""
        self.client.force_authenticate(user=self.user)
        url = reverse('mobile-user-setup_2fa')
        data = {
            'enable_2fa': True
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that 2FA was enabled
        self.user.refresh_from_db()
        self.assertTrue(self.user.two_factor_enabled)
    
    def test_google_oauth_not_implemented(self):
        """Test Google OAuth endpoint (not implemented)"""
        url = reverse('mobile-auth-google_oauth')
        data = {
            'access_token': 'fake_google_token'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_501_NOT_IMPLEMENTED)
    
    def test_non_admin_access_denied(self):
        """Test that non-admin users cannot access admin endpoints"""
        self.client.force_authenticate(user=self.user)  # Regular user, not admin
        url = reverse('mobile-admin-dashboard_stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_visitor_cart_empty(self):
        """Test visitor cart when empty"""
        url = reverse('mobile-visitor-cart')
        response = self.client.get(url, {'session_key': 'non_existent_session'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cart']['total_items'], 0)
        self.assertEqual(response.data['cart']['total_amount'], 0) 