# backend/models_advanced.py - ADVANCED FEATURES FOR VGK
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid
import json
from .models import Product, Order, Category

User = get_user_model()

# ============= AI & RECOMMENDATION SYSTEM =============

class UserBehavior(models.Model):
    """Track user behavior for AI recommendations"""
    ACTION_TYPES = [
        ('VIEW', 'Product View'),
        ('LIKE', 'Product Like'),
        ('SEARCH', 'Search'),
        ('PURCHASE', 'Purchase'),
        ('CART_ADD', 'Add to Cart'),
        ('SHARE', 'Share Product'),
        ('CONTACT_SELLER', 'Contact Seller'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='behaviors')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    session_id = models.CharField(max_length=100)
    duration = models.PositiveIntegerField(default=0)  # seconds
    metadata = models.JSONField(default=dict)  # search terms, filters, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_behaviors'
        indexes = [
            models.Index(fields=['user', 'action_type', 'created_at']),
            models.Index(fields=['product', 'action_type']),
        ]


class UserPreference(models.Model):
    """AI-learned user preferences"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ai_preferences')
    preferred_categories = models.JSONField(default=list)  # [{"category_id": "id", "score": 0.8}]
    price_range_min = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_range_max = models.DecimalField(max_digits=10, decimal_places=2, default=100000)
    preferred_conditions = models.JSONField(default=list)  # ["NEUF", "EXCELLENT"]
    preferred_cities = models.JSONField(default=list)
    shopping_patterns = models.JSONField(default=dict)  # time patterns, frequency, etc.
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_preferences'


class ProductRecommendation(models.Model):
    """Generated product recommendations"""
    RECOMMENDATION_TYPES = [
        ('COLLABORATIVE', 'Collaborative Filtering'),
        ('CONTENT_BASED', 'Content-Based'),
        ('TRENDING', 'Trending Products'),
        ('SIMILAR_USERS', 'Similar Users'),
        ('CROSS_SELL', 'Cross-Sell'),
        ('UPSELL', 'Upsell'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    confidence_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    reason = models.TextField(blank=True)  # explanation for the recommendation
    is_clicked = models.BooleanField(default=False)
    is_purchased = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'product_recommendations'
        unique_together = ['user', 'product', 'recommendation_type']


# ============= ENHANCED SHOPPING EXPERIENCE =============

class ShoppingCart(models.Model):
    """Multi-product shopping cart"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shopping_carts')
    session_id = models.CharField(max_length=100, blank=True)  # for anonymous users
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shopping_carts'
    
    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    """Items in shopping cart"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cart_items'
        unique_together = ['cart', 'product']
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price


class Wishlist(models.Model):
    """Enhanced wishlist with sharing capabilities"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    name = models.CharField(max_length=100, default="Ma liste de souhaits")
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    is_default = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'wishlists'


class WishlistItem(models.Model):
    """Items in wishlist"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    priority = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    price_alert_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wishlist_items'
        unique_together = ['wishlist', 'product']


# ============= VISITOR CART FOR ANONYMOUS USERS =============

class VisitorCart(models.Model):
    """Shopping cart for anonymous visitors"""
    DELIVERY_METHODS = [
        ('PICKUP', 'Retrait en point'),
        ('DELIVERY', 'Livraison à domicile'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=100, unique=True)
    visitor_name = models.CharField(max_length=100, blank=True)
    visitor_email = models.EmailField(blank=True)
    visitor_phone = models.CharField(max_length=20, blank=True)
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHODS, default='PICKUP')
    delivery_address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    whatsapp_preferred = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'visitor_carts'
    
    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def delivery_cost(self):
        return Decimal('2000') if self.delivery_method == 'DELIVERY' else Decimal('0')
    
    @property
    def final_total(self):
        return self.total_amount + self.delivery_cost


class VisitorCartItem(models.Model):
    """Items in visitor cart"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(VisitorCart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'visitor_cart_items'
        unique_together = ['cart', 'product']
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price


# ============= SOCIAL COMMERCE =============

class UserFollow(models.Model):
    """User following system"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_follows'
        unique_together = ['follower', 'following']


class ProductReview(models.Model):
    """Enhanced reviews with media"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='enhanced_review')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enhanced_reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='enhanced_reviews')
    overall_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    quality_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    seller_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    delivery_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    content = models.TextField()
    pros = models.JSONField(default=list)  # ["Good quality", "Fast delivery"]
    cons = models.JSONField(default=list)  # ["Expensive", "Poor packaging"]
    is_verified_purchase = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'product_reviews_enhanced'


class ReviewMedia(models.Model):
    """Media attachments for reviews"""
    MEDIA_TYPES = [
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='media')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = models.FileField(upload_to='reviews/media/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'review_media'
        ordering = ['order']


class SocialPost(models.Model):
    """User-generated content posts"""
    POST_TYPES = [
        ('PRODUCT_SHOWCASE', 'Product Showcase'),
        ('UNBOXING', 'Unboxing'),
        ('REVIEW', 'Review'),
        ('COLLECTION', 'Collection'),
        ('TIP', 'Tip/Advice'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_posts')
    post_type = models.CharField(max_length=20, choices=POST_TYPES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    products = models.ManyToManyField(Product, blank=True, related_name='social_posts')
    tags = models.JSONField(default=list)  # ["fashion", "vintage", "deals"]
    is_featured = models.BooleanField(default=False)
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'social_posts'
        ordering = ['-created_at']


# ============= ADVANCED STAFF FEATURES =============

class StaffTask(models.Model):
    """Task management for staff"""
    TASK_TYPES = [
        ('STOCK_RECEIVE', 'Stock Reception'),
        ('INVENTORY_COUNT', 'Inventory Count'),
        ('ORDER_PICKUP', 'Order Pickup'),
        ('CUSTOMER_SERVICE', 'Customer Service'),
        ('CLEANING', 'Cleaning/Maintenance'),
        ('REPORTING', 'Reporting'),
    ]
    
    PRIORITIES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    STATUSES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    pickup_point = models.ForeignKey('PickupPoint', on_delete=models.CASCADE, related_name='tasks')
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITIES, default='MEDIUM')
    status = models.CharField(max_length=15, choices=STATUSES, default='PENDING')
    due_date = models.DateTimeField()
    estimated_duration = models.PositiveIntegerField(help_text="Estimated duration in minutes")
    actual_duration = models.PositiveIntegerField(null=True, blank=True)
    completion_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'staff_tasks'
        ordering = ['due_date', '-priority']


class InventoryMovement(models.Model):
    """Track all inventory movements"""
    MOVEMENT_TYPES = [
        ('RECEIVE', 'Stock Received'),
        ('PICK', 'Order Picked'),
        ('RETURN', 'Return'),
        ('DAMAGE', 'Damage Report'),
        ('ADJUSTMENT', 'Inventory Adjustment'),
        ('TRANSFER', 'Transfer Between Points'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_movements')
    pickup_point = models.ForeignKey('PickupPoint', on_delete=models.CASCADE, related_name='inventory_movements')
    staff_member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory_movements')
    movement_type = models.CharField(max_length=15, choices=MOVEMENT_TYPES)
    quantity_change = models.IntegerField()  # can be negative
    reference_order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    notes = models.TextField(blank=True)
    batch_id = models.CharField(max_length=50, blank=True)
    location_from = models.CharField(max_length=100, blank=True)
    location_to = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inventory_movements'
        ordering = ['-created_at']


class StaffPerformance(models.Model):
    """Track staff performance metrics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff_member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performance_records')
    pickup_point = models.ForeignKey('PickupPoint', on_delete=models.CASCADE, related_name='performance_records')
    date = models.DateField()
    tasks_completed = models.PositiveIntegerField(default=0)
    orders_processed = models.PositiveIntegerField(default=0)
    customer_rating = models.FloatField(default=0.0)
    efficiency_score = models.FloatField(default=0.0)  # tasks completed vs time worked
    punctuality_score = models.FloatField(default=0.0)
    inventory_accuracy = models.FloatField(default=0.0)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'staff_performance'
        unique_together = ['staff_member', 'date']


# ============= SMART NOTIFICATIONS =============

class NotificationTemplate(models.Model):
    """Templates for smart notifications"""
    NOTIFICATION_TYPES = [
        ('PRICE_DROP', 'Price Drop Alert'),
        ('BACK_IN_STOCK', 'Back in Stock'),
        ('NEW_SIMILAR', 'New Similar Product'),
        ('SELLER_UPDATE', 'Seller Update'),
        ('RECOMMENDATION', 'AI Recommendation'),
        ('PROMOTION', 'Promotion'),
        ('REMINDER', 'Reminder'),
        ('MILESTONE', 'Achievement/Milestone'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title_template = models.CharField(max_length=200)
    message_template = models.TextField()
    email_subject_template = models.CharField(max_length=200, blank=True)
    email_body_template = models.TextField(blank=True)
    sms_template = models.CharField(max_length=160, blank=True)
    trigger_conditions = models.JSONField(default=dict)  # conditions for triggering
    target_audience = models.JSONField(default=dict)  # user segmentation criteria
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notification_templates'


class SmartNotification(models.Model):
    """AI-powered smart notifications"""
    DELIVERY_METHODS = [
        ('IN_APP', 'In-App'),
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push Notification'),
        ('WHATSAPP', 'WhatsApp'),
    ]
    
    STATUSES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('READ', 'Read'),
        ('CLICKED', 'Clicked'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='smart_notifications')
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE, related_name='notifications')
    delivery_method = models.CharField(max_length=10, choices=DELIVERY_METHODS)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict)  # additional data for the notification
    status = models.CharField(max_length=10, choices=STATUSES, default='PENDING')
    scheduled_for = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'smart_notifications'
        ordering = ['-scheduled_for']


# ============= ADVANCED PAYMENTS =============

class EscrowPayment(models.Model):
    """Escrow payment system for secure transactions"""
    STATUSES = [
        ('PENDING', 'Pending'),
        ('FUNDED', 'Funded'),
        ('RELEASED_TO_SELLER', 'Released to Seller'),
        ('REFUNDED_TO_BUYER', 'Refunded to Buyer'),
        ('DISPUTED', 'Disputed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='escrow_payment')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='escrow_payments_as_buyer')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='escrow_payments_as_seller')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUSES, default='PENDING')
    funded_at = models.DateTimeField(null=True, blank=True)
    release_date = models.DateTimeField()  # automatic release date
    released_at = models.DateTimeField(null=True, blank=True)
    dispute_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'escrow_payments'


class InstallmentPlan(models.Model):
    """Installment payment plans"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='installment_plan')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    down_payment = models.DecimalField(max_digits=10, decimal_places=2)
    number_of_installments = models.PositiveIntegerField()
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # percentage
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'installment_plans'


class InstallmentPayment(models.Model):
    """Individual installment payments"""
    STATUSES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(InstallmentPlan, on_delete=models.CASCADE, related_name='payments')
    installment_number = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUSES, default='PENDING')
    paid_at = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'installment_payments'
        unique_together = ['plan', 'installment_number']
        ordering = ['installment_number'] 


# ============= PRODUCT REPORTS =============

class ProductReport(models.Model):
    """Product reports for inappropriate content"""
    REPORT_TYPES = [
        ('FAKE', 'Produit contrefait'),
        ('INAPPROPRIATE', 'Contenu inapproprié'),
        ('MISLEADING', 'Description trompeuse'),
        ('OVERPRICED', 'Prix excessif'),
        ('SPAM', 'Spam/Publicité'),
        ('DUPLICATE', 'Annonce dupliquée'),
        ('BROKEN', 'Produit défectueux'),
        ('OTHER', 'Autre')
    ]
    
    STATUSES = [
        ('PENDING', 'En attente'),
        ('REVIEWING', 'En cours d\'examen'),
        ('RESOLVED', 'Résolu'),
        ('DISMISSED', 'Rejeté')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reports')
    reporter_ip = models.GenericIPAddressField()
    reporter_email = models.EmailField(blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUSES, default='PENDING')
    admin_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'product_reports'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Report #{self.id} - {self.get_report_type_display()}" 


# ============= VISITOR FAVORITES & INTERACTIONS =============

class VisitorFavorite(models.Model):
    """Favorites for visitors (session-based)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=100)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='visitor_favorites')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['session_key', 'product']
        db_table = 'visitor_favorites'
    
    def __str__(self):
        return f"Visitor Favorite: {self.product.title}"


class VisitorCompare(models.Model):
    """Product comparison for visitors"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=100)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='visitor_compares')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['session_key', 'product']
        db_table = 'visitor_compares'
    
    def __str__(self):
        return f"Visitor Compare: {self.product.title}"


class ProductComment(models.Model):
    """Comments on products (for both users and visitors)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    
    # For registered users
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    
    # For visitors
    visitor_name = models.CharField(max_length=100, blank=True)
    visitor_email = models.EmailField(blank=True)
    visitor_ip = models.GenericIPAddressField(null=True, blank=True)
    
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'product_comments'
    
    def __str__(self):
        commenter = self.user.get_full_name() if self.user else self.visitor_name
        return f"Comment by {commenter} on {self.product.title}"
    
    @property
    def commenter_name(self):
        return self.user.get_full_name() if self.user else self.visitor_name
    
    @property
    def is_reply(self):
        return self.parent is not None


class ProductLike(models.Model):
    """Likes/Dislikes for products"""
    LIKE_CHOICES = [
        ('LIKE', 'Like'),
        ('DISLIKE', 'Dislike'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='likes')
    
    # For registered users
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='product_likes')
    
    # For visitors  
    visitor_ip = models.GenericIPAddressField(null=True, blank=True)
    session_key = models.CharField(max_length=100, blank=True)
    
    like_type = models.CharField(max_length=10, choices=LIKE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'product_likes'
        # Prevent duplicate likes from same user/visitor
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'user'], 
                condition=models.Q(user__isnull=False),
                name='unique_user_product_like'
            ),
            models.UniqueConstraint(
                fields=['product', 'visitor_ip', 'session_key'], 
                condition=models.Q(user__isnull=True),
                name='unique_visitor_product_like'
            ),
        ]
    
    def __str__(self):
        identifier = self.user.get_full_name() if self.user else f"Visitor {self.visitor_ip}"
        return f"{identifier} {self.like_type.lower()}d {self.product.title}"


# ProductAlert model moved to main models.py to avoid conflicts


# ============= WALLET & FINANCIAL SYSTEM =============

class Wallet(models.Model):
    """User wallet for managing funds"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    pending_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    is_frozen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'wallets'
        verbose_name = 'Portefeuille'
        verbose_name_plural = 'Portefeuilles'
    
    def __str__(self):
        return f"Wallet {self.user.email} - {self.balance} XAF"
    
    @property
    def available_balance(self):
        return self.balance - self.pending_balance
    
    def can_withdraw(self, amount):
        return self.available_balance >= amount and not self.is_frozen
    
    def add_funds(self, amount, description="Ajout de fonds"):
        """Add funds to wallet"""
        if amount > 0:
            self.balance += amount
            self.total_earned += amount
            self.save()
            
            Transaction.objects.create(
                wallet=self,
                transaction_type='CREDIT',
                amount=amount,
                description=description,
                status='COMPLETED'
            )
    
    def deduct_funds(self, amount, description="Déduction de fonds"):
        """Deduct funds from wallet"""
        if amount > 0 and self.can_withdraw(amount):
            self.balance -= amount
            self.total_spent += amount
            self.save()
            
            Transaction.objects.create(
                wallet=self,
                transaction_type='DEBIT',
                amount=amount,
                description=description,
                status='COMPLETED'
            )
            return True
        return False


class Transaction(models.Model):
    """Wallet transactions"""
    TRANSACTION_TYPES = [
        ('CREDIT', 'Crédit'),
        ('DEBIT', 'Débit'),
        ('COMMISSION', 'Commission'),
        ('REFUND', 'Remboursement'),
        ('WITHDRAWAL', 'Retrait'),
        ('DEPOSIT', 'Dépôt'),
    ]
    
    STATUSES = [
        ('PENDING', 'En attente'),
        ('PROCESSING', 'En traitement'),
        ('COMPLETED', 'Complété'),
        ('FAILED', 'Échoué'),
        ('CANCELLED', 'Annulé'),
    ]
    
    SOURCES = [
        ('SALE', 'Vente'),
        ('PURCHASE', 'Achat'),
        ('COMMISSION', 'Commission'),
        ('ADMIN_CREDIT', 'Crédit Admin'),
        ('ADMIN_DEBIT', 'Débit Admin'),
        ('REFUND', 'Remboursement'),
        ('WITHDRAWAL', 'Retrait'),
        ('DEPOSIT', 'Dépôt'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    source = models.CharField(max_length=20, choices=SOURCES, default='ADMIN_CREDIT')
    reference_id = models.CharField(max_length=100, blank=True)  # Order ID, Payment ID, etc.
    status = models.CharField(max_length=20, choices=STATUSES, default='PENDING')
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', 'status']),
            models.Index(fields=['transaction_type', 'created_at']),
            models.Index(fields=['reference_id']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} XAF - {self.wallet.user.email}"


class Commission(models.Model):
    """Track admin commissions from sales"""
    COMMISSION_TYPES = [
        ('SALE', 'Commission sur vente'),
        ('SERVICE', 'Frais de service'),
        ('PENALTY', 'Pénalité'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='commission_record')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='commissions_paid')
    commission_type = models.CharField(max_length=20, choices=COMMISSION_TYPES, default='SALE')
    base_amount = models.DecimalField(max_digits=12, decimal_places=2)  # Original sale amount
    commission_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.1000'))  # 10%
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2)
    seller_amount = models.DecimalField(max_digits=12, decimal_places=2)  # Amount credited to seller
    is_paid = models.BooleanField(default=False)
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'commissions'
        verbose_name = 'Commission'
        verbose_name_plural = 'Commissions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Commission {self.commission_amount} XAF - Commande {self.order.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.commission_amount:
            self.commission_amount = self.base_amount * self.commission_rate
        if not self.seller_amount:
            self.seller_amount = self.base_amount - self.commission_amount
        super().save(*args, **kwargs)


class WithdrawalRequest(models.Model):
    """User withdrawal requests"""
    STATUSES = [
        ('PENDING', 'En attente'),
        ('APPROVED', 'Approuvé'),
        ('PROCESSING', 'En traitement'),
        ('COMPLETED', 'Complété'),
        ('REJECTED', 'Rejeté'),
        ('CANCELLED', 'Annulé'),
    ]
    
    WITHDRAWAL_METHODS = [
        ('MOBILE_MONEY', 'Mobile Money'),
        ('BANK_TRANSFER', 'Virement bancaire'),
        ('CASH_PICKUP', 'Retrait en espèces'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawal_requests')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    withdrawal_method = models.CharField(max_length=20, choices=WITHDRAWAL_METHODS)
    account_details = models.JSONField(default=dict)  # Phone number, bank details, etc.
    status = models.CharField(max_length=20, choices=STATUSES, default='PENDING')
    admin_notes = models.TextField(blank=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_withdrawals')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'withdrawal_requests'
        verbose_name = 'Demande de retrait'
        verbose_name_plural = 'Demandes de retrait'
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Retrait {self.amount} XAF - {self.user.email} - {self.status}"


# ============= ENHANCED MESSAGING SYSTEM =============

class PrivateChat(models.Model):
    """Private conversations between users - separate from product-based chats"""
    
    CHAT_TYPES = [
        ('CLIENT_ADMIN', 'Client-Admin'),
        ('STAFF_ADMIN', 'Staff-Admin'),
        ('CLIENT_CLIENT', 'Client-Client'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_type = models.CharField(max_length=20, choices=CHAT_TYPES)
    participant_1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_chats_as_p1')
    participant_2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_chats_as_p2')
    initiated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_private_chats')
    subject = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'private_chats'
        unique_together = ['participant_1', 'participant_2', 'chat_type']
        ordering = ['-last_message_at', '-updated_at']
    
    def __str__(self):
        return f"{self.get_chat_type_display()}: {self.participant_1.email} - {self.participant_2.email}"
    
    def get_other_participant(self, user):
        """Get the other participant in the chat"""
        return self.participant_2 if self.participant_1 == user else self.participant_1
    
    @property
    def last_message(self):
        return self.private_messages.order_by('-created_at').first()


class PrivateMessage(models.Model):
    """Messages in private chats"""
    
    MESSAGE_TYPES = [
        ('TEXT', 'Texte'),
        ('IMAGE', 'Image'),
        ('FILE', 'Fichier'),
        ('SYSTEM', 'Message système'),
        ('VOICE', 'Message vocal'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    private_chat = models.ForeignKey(PrivateChat, on_delete=models.CASCADE, related_name='private_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_private_messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='TEXT')
    content = models.TextField()
    image = models.ImageField(upload_to='chat/private_images/', blank=True, null=True)
    file = models.FileField(upload_to='chat/private_files/', blank=True, null=True)
    voice_note = models.FileField(upload_to='chat/voice_notes/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'private_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['private_chat', 'created_at']),
            models.Index(fields=['sender', 'is_read']),
        ]
    
    def __str__(self):
        return f"Message privé de {self.sender.email} - {self.created_at}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update last_message_at on the chat
        self.private_chat.last_message_at = self.created_at
        self.private_chat.save(update_fields=['last_message_at'])


# Enhanced GroupChat with better admin controls
def enhance_group_chat():
    """
    Add these fields to the existing GroupChat model:
    - max_participants: IntegerField for limiting group size
    - admin_only_creation: BooleanField to restrict who can create groups
    - auto_delete_inactive: BooleanField for automatic cleanup
    - tags: JSONField for categorizing groups
    """
    pass


class GroupChatParticipant(models.Model):
    """Track participant status in group chats"""
    
    ROLES = [
        ('ADMIN', 'Administrateur'),
        ('MODERATOR', 'Modérateur'),
        ('MEMBER', 'Membre'),
    ]
    
    STATUSES = [
        ('ACTIVE', 'Actif'),
        ('MUTED', 'Silencieux'),
        ('BANNED', 'Banni'),
        ('LEFT', 'Parti'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group_chat = models.ForeignKey('backend.GroupChat', on_delete=models.CASCADE, related_name='participant_details')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_participations')
    role = models.CharField(max_length=20, choices=ROLES, default='MEMBER')
    status = models.CharField(max_length=20, choices=STATUSES, default='ACTIVE')
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(null=True, blank=True)
    muted_until = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'group_chat_participants'
        unique_together = ['group_chat', 'user']
        indexes = [
            models.Index(fields=['group_chat', 'status']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.group_chat.name} ({self.role})"
    
    @property
    def unread_count(self):
        """Count unread messages for this participant"""
        if not self.last_read_at:
            return self.group_chat.group_messages.count()
        return self.group_chat.group_messages.filter(created_at__gt=self.last_read_at).count()


class ChatSettings(models.Model):
    """Global chat settings and preferences"""
    
    NOTIFICATION_TYPES = [
        ('ALL', 'Toutes les notifications'),
        ('MENTIONS_ONLY', 'Mentions uniquement'),
        ('NONE', 'Aucune notification'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='chat_settings')
    notification_preference = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='ALL')
    email_notifications = models.BooleanField(default=True)
    show_online_status = models.BooleanField(default=True)
    auto_delete_messages_days = models.IntegerField(default=0)  # 0 means never delete
    blocked_users = models.ManyToManyField(User, related_name='blocked_by', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_settings'
        verbose_name = 'Paramètres de chat'
        verbose_name_plural = 'Paramètres de chat'
    
    def __str__(self):
        return f"Paramètres chat - {self.user.email}"


class MessageReaction(models.Model):
    """Reactions to messages"""
    
    REACTION_TYPES = [
        ('LIKE', '👍'),
        ('LOVE', '❤️'),
        ('LAUGH', '😂'),
        ('WOW', '😮'),
        ('ANGRY', '😠'),
        ('SAD', '😢'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_reactions')
    # Can be either a private message or group message
    private_message = models.ForeignKey(PrivateMessage, on_delete=models.CASCADE, null=True, blank=True, related_name='reactions')
    group_message = models.ForeignKey('backend.GroupChatMessage', on_delete=models.CASCADE, null=True, blank=True, related_name='reactions')
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'message_reactions'
        unique_together = [
            ['user', 'private_message'],
            ['user', 'group_message']
        ]
        indexes = [
            models.Index(fields=['private_message', 'reaction_type']),
            models.Index(fields=['group_message', 'reaction_type']),
        ]
    
    def __str__(self):
        message_ref = self.private_message or self.group_message
        return f"{self.user.email} - {self.get_reaction_type_display()} - {message_ref}"


class OnlineStatus(models.Model):
    """Track user online status for real-time features"""
    
    STATUSES = [
        ('ONLINE', 'En ligne'),
        ('AWAY', 'Absent'),
        ('BUSY', 'Occupé'),
        ('OFFLINE', 'Hors ligne'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='online_status')
    status = models.CharField(max_length=10, choices=STATUSES, default='OFFLINE')
    last_activity = models.DateTimeField(auto_now=True)
    current_chat = models.ForeignKey(PrivateChat, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_users')
    current_group_chat = models.ForeignKey('backend.GroupChat', on_delete=models.SET_NULL, null=True, blank=True, related_name='current_users')
    is_typing = models.BooleanField(default=False)
    typing_in_chat = models.ForeignKey(PrivateChat, on_delete=models.SET_NULL, null=True, blank=True, related_name='typing_users')
    typing_in_group = models.ForeignKey('backend.GroupChat', on_delete=models.SET_NULL, null=True, blank=True, related_name='typing_users')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'online_statuses'
        verbose_name = 'Statut en ligne'
        verbose_name_plural = 'Statuts en ligne'
    
    def __str__(self):
        return f"{self.user.email} - {self.get_status_display()}"
    
    @property
    def is_online(self):
        from django.utils import timezone
        # Consider user online if last activity was within 5 minutes
        return self.status == 'ONLINE' and (timezone.now() - self.last_activity).seconds < 300