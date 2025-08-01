from rest_framework import serializers
from django.contrib.auth import get_user_model
from backend.models import (
    Product, Category, Order, Favorite, Review, 
    PickupPoint, Payment, ProductImage
)
from backend.models_advanced import Wallet, Transaction
from backend.models_visitor import VisitorCart, VisitorCartItem

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """User serializer for mobile API"""
    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'first_name', 'last_name',
            'user_type', 'city', 'address', 'is_verified', 
            'phone_verified', 'trust_score', 'loyalty_points',
            'loyalty_level', 'profile_picture', 'created_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'trust_score', 'loyalty_points',
            'loyalty_level', 'is_verified', 'phone_verified'
        ]

class CategorySerializer(serializers.ModelSerializer):
    """Category serializer for mobile API"""
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 'product_count']
    
    def get_product_count(self, obj):
        return obj.products.filter(status='ACTIVE').count()

class ProductImageSerializer(serializers.ModelSerializer):
    """Product image serializer"""
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary', 'alt_text', 'order']
    
    def to_representation(self, instance):
        return {
            'id': instance.id,
            'image_url': instance.image.url if instance.image else None,
            'is_primary': instance.is_primary,
            'alt_text': instance.alt_text,
            'order': instance.order
        }

class ProductSerializer(serializers.ModelSerializer):
    """Product serializer for mobile API"""
    seller = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    main_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'description', 'price', 'condition',
            'city', 'is_negotiable', 'views_count', 'likes_count',
            'created_at', 'status', 'seller', 'category', 'images',
            'is_favorited', 'main_image'
        ]
        read_only_fields = [
            'id', 'slug', 'views_count', 'likes_count', 'created_at',
            'seller', 'is_favorited'
        ]
    
    def get_is_favorited(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        if user and user.is_authenticated:
            return Favorite.objects.filter(user=user, product=obj).exists()
        return False
    
    def get_main_image(self, obj):
        main_image = obj.images.filter(is_primary=True).first()
        if main_image:
            return main_image.image.url
        return None

class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating products"""
    class Meta:
        model = Product
        fields = [
            'title', 'description', 'price', 'condition', 'category',
            'city', 'is_negotiable'
        ]
    
    def create(self, validated_data):
        validated_data['seller'] = self.context['request'].user
        return super().create(validated_data)

class ReviewSerializer(serializers.ModelSerializer):
    """Review serializer"""
    reviewer = UserSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'overall_rating', 'comment', 'created_at', 'reviewer'
        ]
        read_only_fields = ['id', 'created_at', 'reviewer']

class OrderSerializer(serializers.ModelSerializer):
    """Order serializer for mobile API"""
    product = ProductSerializer(read_only=True)
    buyer = UserSerializer(read_only=True)
    seller = UserSerializer(read_only=True)
    pickup_point = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'product', 'buyer', 'seller', 'quantity', 'total_amount',
            'status', 'pickup_point', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_pickup_point(self, obj):
        if obj.pickup_point:
            return {
                'id': obj.pickup_point.id,
                'name': obj.pickup_point.name,
                'address': obj.pickup_point.address,
                'city': obj.pickup_point.city
            }
        return None

class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders"""
    class Meta:
        model = Order
        fields = ['product', 'quantity', 'pickup_point']
    
    def create(self, validated_data):
        validated_data['buyer'] = self.context['request'].user
        validated_data['seller'] = validated_data['product'].seller
        validated_data['total_amount'] = validated_data['product'].price * validated_data['quantity']
        return super().create(validated_data)

class FavoriteSerializer(serializers.ModelSerializer):
    """Favorite serializer"""
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = Favorite
        fields = ['id', 'product', 'created_at']
        read_only_fields = ['id', 'created_at']

class PickupPointSerializer(serializers.ModelSerializer):
    """Pickup point serializer"""
    class Meta:
        model = PickupPoint
        fields = ['id', 'name', 'address', 'city', 'phone', 'is_active']

class WalletSerializer(serializers.ModelSerializer):
    """Wallet serializer"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Wallet
        fields = ['id', 'user', 'balance', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class TransactionSerializer(serializers.ModelSerializer):
    """Transaction serializer"""
    class Meta:
        model = Transaction
        fields = [
            'id', 'wallet', 'amount', 'transaction_type', 'description',
            'status', 'reference', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class SearchResultSerializer(serializers.Serializer):
    """Search result serializer"""
    id = serializers.CharField()
    title = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    condition = serializers.CharField()
    city = serializers.CharField()
    main_image = serializers.CharField(allow_null=True)
    category = serializers.DictField()

class UserStatsSerializer(serializers.Serializer):
    """User statistics serializer"""
    products_count = serializers.IntegerField()
    orders_bought = serializers.IntegerField()
    orders_sold = serializers.IntegerField()
    favorites_count = serializers.IntegerField()
    reviews_given = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_earned = serializers.DecimalField(max_digits=10, decimal_places=2)

# Authentication Serializers
class LoginSerializer(serializers.Serializer):
    """Login serializer"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class RegisterSerializer(serializers.ModelSerializer):
    """Registration serializer"""
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'phone', 'password', 'confirm_password',
            'first_name', 'last_name', 'user_type', 'city', 'address'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        return User.objects.create_user(**validated_data)

class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Profile update serializer"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'city', 'address']

# 2FA Serializers
class TwoFactorSetupSerializer(serializers.Serializer):
    """2FA setup serializer"""
    enable_2fa = serializers.BooleanField()

class TwoFactorVerifySerializer(serializers.Serializer):
    """2FA verification serializer"""
    code = serializers.CharField(max_length=6)

class PhoneVerificationSerializer(serializers.Serializer):
    """Phone verification serializer"""
    phone = serializers.CharField()
    code = serializers.CharField(max_length=6)

class SendVerificationCodeSerializer(serializers.Serializer):
    """Send verification code serializer"""
    phone = serializers.CharField()

# Google OAuth Serializers
class GoogleOAuthSerializer(serializers.Serializer):
    """Google OAuth serializer"""
    access_token = serializers.CharField()

# Visitor Cart Serializers
class VisitorCartItemSerializer(serializers.ModelSerializer):
    """Visitor cart item serializer"""
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = VisitorCartItem
        fields = ['id', 'product', 'quantity', 'created_at']
        read_only_fields = ['id', 'created_at']

class VisitorCartSerializer(serializers.ModelSerializer):
    """Visitor cart serializer"""
    items = VisitorCartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = VisitorCart
        fields = ['id', 'session_key', 'items', 'total_items', 'total_amount', 'created_at']
        read_only_fields = ['id', 'session_key', 'created_at']
    
    def get_total_items(self, obj):
        return obj.items.count()
    
    def get_total_amount(self, obj):
        return sum(item.product.price * item.quantity for item in obj.items.all())

# Payment Serializers
class PaymentSerializer(serializers.Serializer):
    """Payment serializer"""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=['MOBILE_MONEY', 'CARD', 'CASH'])
    phone_number = serializers.CharField(required=False)
    reference = serializers.CharField(required=False)

class PaymentVerificationSerializer(serializers.Serializer):
    """Payment verification serializer"""
    reference = serializers.CharField()
    transaction_id = serializers.CharField()

# Admin Serializers
class AdminUserManagementSerializer(serializers.ModelSerializer):
    """Admin user management serializer"""
    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'first_name', 'last_name',
            'user_type', 'is_verified', 'phone_verified', 'is_active',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class AdminProductModerationSerializer(serializers.ModelSerializer):
    """Admin product moderation serializer"""
    class Meta:
        model = Product
        fields = ['id', 'title', 'status', 'seller', 'created_at']
        read_only_fields = ['id', 'created_at']

class AdminStatsSerializer(serializers.Serializer):
    """Admin statistics serializer"""
    total_users = serializers.IntegerField()
    total_products = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_products = serializers.IntegerField()
    active_users_today = serializers.IntegerField() 