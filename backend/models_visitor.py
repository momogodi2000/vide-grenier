# backend/models_visitor.py - ENHANCED VISITOR SYSTEM FOR VGK
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid
import json
import qrcode
import io
import base64
from PIL import Image
from .models import Product, Order, Category, PickupPoint
# ProductRecommendation will be imported when needed to avoid circular imports

User = get_user_model()

# ============= ENHANCED VISITOR CART SYSTEM =============

class VisitorCart(models.Model):
    """Enhanced shopping cart for anonymous visitors with AI features"""
    
    DELIVERY_METHODS = [
        ('PICKUP', 'Retrait en point'),
        ('DELIVERY', 'Livraison à domicile'),
    ]
    
    PAYMENT_OPTIONS = [
        ('CAMPAY_DELIVERY', 'Campay + Livraison (2000 FCFA)'),
        ('WHATSAPP_PICKUP', 'WhatsApp + Retrait sur place'),
        ('WHATSAPP_NEGOTIATION', 'WhatsApp + Négociation'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=100, unique=True)
    
    # Visitor information
    visitor_name = models.CharField(max_length=100, blank=True)
    visitor_email = models.EmailField(blank=True)
    visitor_phone = models.CharField(max_length=20, blank=True)
    visitor_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Delivery and payment preferences
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHODS, default='PICKUP')
    payment_option = models.CharField(max_length=30, choices=PAYMENT_OPTIONS, default='WHATSAPP_PICKUP')
    delivery_address = models.TextField(blank=True)
    pickup_point = models.ForeignKey(PickupPoint, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Communication preferences
    whatsapp_preferred = models.BooleanField(default=False)
    email_preferred = models.BooleanField(default=False)
    sms_preferred = models.BooleanField(default=False)
    
    # Additional information
    notes = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    
    # AI and analytics
    ai_recommendations_shown = models.JSONField(default=list)  # Track shown recommendations
    behavior_data = models.JSONField(default=dict)  # Store visitor behavior
    
    # Status and tracking
    is_active = models.BooleanField(default=True)
    is_abandoned = models.BooleanField(default=False)
    abandoned_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'visitor_carts_enhanced'
        indexes = [
            models.Index(fields=['session_key']),
            models.Index(fields=['visitor_phone']),
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['is_abandoned', 'abandoned_at']),
        ]
    
    def __str__(self):
        return f"Cart {self.session_key[:8]} - {self.visitor_name or 'Anonymous'}"
    
    @property
    def total_amount(self):
        """Calculate total amount of all items"""
        return sum(item.total_price for item in self.items.all())
    
    @property
    def total_items(self):
        """Calculate total number of items"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def delivery_cost(self):
        """Calculate delivery cost based on method"""
        if self.delivery_method == 'DELIVERY':
            return Decimal('2000')  # 2000 FCFA for delivery
        return Decimal('0')
    
    @property
    def final_total(self):
        """Calculate final total including delivery"""
        return self.total_amount + self.delivery_cost
    
    @property
    def is_empty(self):
        """Check if cart is empty"""
        return not self.items.exists()
    
    def add_item(self, product, quantity=1):
        """Add item to cart"""
        cart_item, created = VisitorCartItem.objects.get_or_create(
            cart=self,
            product=product,
            defaults={
                'quantity': quantity,
                'unit_price': product.price
            }
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return cart_item
    
    def remove_item(self, product):
        """Remove item from cart"""
        self.items.filter(product=product).delete()
    
    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()
    
    def mark_abandoned(self):
        """Mark cart as abandoned"""
        self.is_abandoned = True
        self.abandoned_at = timezone.now()
        self.save()
    
    def generate_qr_code(self):
        """Generate QR code for receipt"""
        qr_data = {
            'cart_id': str(self.id),
            'session_key': self.session_key,
            'total_amount': float(self.total_amount),
            'items_count': self.total_items,
            'timestamp': self.created_at.isoformat()
        }
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return img_str


class VisitorCartItem(models.Model):
    """Enhanced items in visitor cart"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(VisitorCart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    # Item details
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Additional options
    notes = models.TextField(blank=True)
    special_requests = models.TextField(blank=True)
    
    # Timestamps
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'visitor_cart_items_enhanced'
        unique_together = ['cart', 'product']
        indexes = [
            models.Index(fields=['cart', 'product']),
            models.Index(fields=['added_at']),
        ]
    
    def __str__(self):
        return f"{self.product.title} x{self.quantity} - {self.cart.session_key[:8]}"
    
    @property
    def total_price(self):
        """Calculate total price for this item"""
        return self.quantity * self.unit_price
    
    @property
    def is_available(self):
        """Check if product is still available"""
        return self.product.status == 'ACTIVE'


# ============= AI RECOMMENDATION SYSTEM =============

class VisitorBehavior(models.Model):
    """Track visitor behavior for AI recommendations"""
    
    ACTION_TYPES = [
        ('VIEW', 'Product View'),
        ('LIKE', 'Product Like'),
        ('DISLIKE', 'Product Dislike'),
        ('SEARCH', 'Search'),
        ('CART_ADD', 'Add to Cart'),
        ('CART_REMOVE', 'Remove from Cart'),
        ('COMPARE', 'Compare Products'),
        ('FAVORITE', 'Add to Favorites'),
        ('SHARE', 'Share Product'),
        ('REPORT', 'Report Product'),
        ('COMMENT', 'Add Comment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=100)
    visitor_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Action details
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    
    # Additional data
    search_query = models.CharField(max_length=200, blank=True)
    duration = models.PositiveIntegerField(default=0)  # seconds spent
    metadata = models.JSONField(default=dict)  # additional context
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'visitor_behaviors'
        indexes = [
            models.Index(fields=['session_key', 'action_type']),
            models.Index(fields=['visitor_ip', 'created_at']),
            models.Index(fields=['product', 'action_type']),
            models.Index(fields=['category', 'action_type']),
        ]


class VisitorPreference(models.Model):
    """AI-learned visitor preferences"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=100, unique=True)
    visitor_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Preference data
    preferred_categories = models.JSONField(default=list)  # [{"category_id": "id", "score": 0.8}]
    price_range_min = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_range_max = models.DecimalField(max_digits=10, decimal_places=2, default=100000)
    preferred_conditions = models.JSONField(default=list)  # ["NEUF", "EXCELLENT"]
    preferred_cities = models.JSONField(default=list)
    
    # Behavior patterns
    shopping_patterns = models.JSONField(default=dict)  # time patterns, frequency, etc.
    interaction_history = models.JSONField(default=list)  # recent interactions
    
    # AI confidence scores
    confidence_score = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(1)])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'visitor_preferences'


# ProductRecommendation model is defined in models_advanced.py to avoid conflicts


# ============= ENHANCED INTERACTION SYSTEM =============

class VisitorFavorite(models.Model):
    """Enhanced favorites for visitors"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=100)
    visitor_ip = models.GenericIPAddressField(null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='visitor_favorites_enhanced')
    
    # Additional data
    notes = models.TextField(blank=True)
    priority = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    price_alert_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'visitor_favorites_enhanced'
        unique_together = ['session_key', 'product']
        indexes = [
            models.Index(fields=['session_key', 'created_at']),
            models.Index(fields=['product', 'created_at']),
        ]


class VisitorCompare(models.Model):
    """Enhanced product comparison for visitors"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=100)
    visitor_ip = models.GenericIPAddressField(null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='visitor_compares_enhanced')
    
    # Comparison data
    comparison_notes = models.TextField(blank=True)
    preference_score = models.IntegerField(default=0, validators=[MinValueValidator(-10), MaxValueValidator(10)])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'visitor_compares_enhanced'
        unique_together = ['session_key', 'product']
        indexes = [
            models.Index(fields=['session_key', 'created_at']),
            models.Index(fields=['product', 'created_at']),
        ]


class ProductComment(models.Model):
    """Enhanced comments on products for visitors"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='visitor_comments_enhanced')
    
    # Commenter information
    visitor_name = models.CharField(max_length=100)
    visitor_email = models.EmailField(blank=True)
    visitor_ip = models.GenericIPAddressField(null=True, blank=True)
    session_key = models.CharField(max_length=100, blank=True)
    
    # Comment content
    content = models.TextField()
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    
    # Moderation
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    is_approved = models.BooleanField(default=True)
    is_spam = models.BooleanField(default=False)
    moderation_notes = models.TextField(blank=True)
    
    # Interaction tracking
    likes_count = models.PositiveIntegerField(default=0)
    dislikes_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'product_comments_enhanced'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'is_approved']),
            models.Index(fields=['visitor_ip', 'created_at']),
            models.Index(fields=['session_key', 'created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.visitor_name} on {self.product.title}"
    
    @property
    def is_reply(self):
        return self.parent is not None


class ProductLike(models.Model):
    """Enhanced likes/dislikes for products"""
    
    LIKE_CHOICES = [
        ('LIKE', 'Like'),
        ('DISLIKE', 'Dislike'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='visitor_likes_enhanced')
    
    # Visitor information
    visitor_ip = models.GenericIPAddressField(null=True, blank=True)
    session_key = models.CharField(max_length=100, blank=True)
    
    # Like data
    like_type = models.CharField(max_length=10, choices=LIKE_CHOICES)
    reason = models.TextField(blank=True)  # Optional reason for like/dislike
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'product_likes_enhanced'
        # Prevent duplicate likes from same visitor
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'visitor_ip', 'session_key'], 
                name='unique_visitor_product_like'
            ),
        ]
        indexes = [
            models.Index(fields=['product', 'like_type']),
            models.Index(fields=['visitor_ip', 'created_at']),
        ]


# ============= PRODUCT REPORTING SYSTEM =============

class ProductReport(models.Model):
    """Enhanced product reports for inappropriate content"""
    
    REPORT_TYPES = [
        ('FAKE', 'Produit contrefait'),
        ('INAPPROPRIATE', 'Contenu inapproprié'),
        ('MISLEADING', 'Description trompeuse'),
        ('OVERPRICED', 'Prix excessif'),
        ('SPAM', 'Spam/Publicité'),
        ('DUPLICATE', 'Annonce dupliquée'),
        ('BROKEN', 'Produit défectueux'),
        ('DANGEROUS', 'Produit dangereux'),
        ('ILLEGAL', 'Produit illégal'),
        ('OTHER', 'Autre')
    ]
    
    STATUSES = [
        ('PENDING', 'En attente'),
        ('REVIEWING', 'En cours d\'examen'),
        ('RESOLVED', 'Résolu'),
        ('DISMISSED', 'Rejeté'),
        ('ESCALATED', 'Escaladé')
    ]
    
    PRIORITIES = [
        ('LOW', 'Faible'),
        ('MEDIUM', 'Moyenne'),
        ('HIGH', 'Élevée'),
        ('URGENT', 'Urgente'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='visitor_reports_enhanced')
    
    # Reporter information
    reporter_ip = models.GenericIPAddressField()
    reporter_email = models.EmailField(blank=True)
    reporter_name = models.CharField(max_length=100, blank=True)
    session_key = models.CharField(max_length=100, blank=True)
    
    # Report details
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField()
    evidence = models.JSONField(default=list)  # URLs, screenshots, etc.
    priority = models.CharField(max_length=10, choices=PRIORITIES, default='MEDIUM')
    
    # Status and moderation
    status = models.CharField(max_length=20, choices=STATUSES, default='PENDING')
    admin_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_visitor_reports')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'product_reports_enhanced'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['product', 'status']),
            models.Index(fields=['report_type', 'status']),
            models.Index(fields=['reporter_ip', 'created_at']),
            models.Index(fields=['priority', 'created_at']),
        ]
    
    def __str__(self):
        return f"Report #{self.id} - {self.get_report_type_display()}"


# ============= WHATSAPP INTEGRATION =============

class WhatsAppRequest(models.Model):
    """Track WhatsApp requests for pickup and negotiation"""
    
    REQUEST_TYPES = [
        ('PICKUP', 'Retrait sur place'),
        ('NEGOTIATION', 'Négociation de prix'),
        ('INQUIRY', 'Demande d\'information'),
        ('BULK_ORDER', 'Commande en gros'),
    ]
    
    STATUSES = [
        ('PENDING', 'En attente'),
        ('SENT', 'Message envoyé'),
        ('RESPONDED', 'Réponse reçue'),
        ('COMPLETED', 'Terminé'),
        ('FAILED', 'Échoué'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=100)
    visitor_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Request details
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    visitor_name = models.CharField(max_length=100)
    visitor_phone = models.CharField(max_length=20)
    visitor_email = models.EmailField(blank=True)
    
    # Product information
    products = models.JSONField(default=list)  # List of product IDs and quantities
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Message content
    message_content = models.TextField()
    admin_phone = models.CharField(max_length=20, default='+237694638412')
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUSES, default='PENDING')
    whatsapp_url = models.URLField(blank=True)
    response_received = models.BooleanField(default=False)
    response_content = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'whatsapp_requests'
        indexes = [
            models.Index(fields=['session_key', 'status']),
            models.Index(fields=['visitor_phone', 'created_at']),
            models.Index(fields=['request_type', 'status']),
        ]
    
    def __str__(self):
        return f"WhatsApp {self.request_type} - {self.visitor_name}"


# ============= QR RECEIPT SYSTEM =============

class QRReceipt(models.Model):
    """QR code receipts for visitor orders"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=100)
    visitor_cart = models.ForeignKey(VisitorCart, on_delete=models.CASCADE, related_name='qr_receipts')
    
    # Receipt data
    receipt_number = models.CharField(max_length=20, unique=True)
    qr_code_data = models.TextField()  # Base64 encoded QR code
    receipt_pdf = models.FileField(upload_to='receipts/pdfs/', blank=True, null=True)
    
    # Order information
    orders = models.JSONField(default=list)  # List of order IDs
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Visitor information
    visitor_name = models.CharField(max_length=100)
    visitor_phone = models.CharField(max_length=20)
    visitor_email = models.EmailField(blank=True)
    delivery_address = models.TextField(blank=True)
    
    # Status
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'qr_receipts'
        indexes = [
            models.Index(fields=['receipt_number']),
            models.Index(fields=['session_key', 'created_at']),
            models.Index(fields=['visitor_phone', 'created_at']),
        ]
    
    def __str__(self):
        return f"Receipt {self.receipt_number} - {self.visitor_name}"
    
    def generate_receipt_number(self):
        """Generate unique receipt number"""
        import random
        import string
        return f"VGK{''.join(random.choices(string.digits, k=8))}"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = self.generate_receipt_number()
        super().save(*args, **kwargs)


# ============= SESSION MANAGEMENT =============

class VisitorSession(models.Model):
    """Enhanced session management for visitors"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=100, unique=True)
    visitor_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Session data
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    entry_page = models.URLField(blank=True)
    
    # Activity tracking
    page_views = models.PositiveIntegerField(default=0)
    products_viewed = models.JSONField(default=list)
    searches_performed = models.JSONField(default=list)
    
    # Conversion tracking
    cart_created = models.BooleanField(default=False)
    order_placed = models.BooleanField(default=False)
    account_created = models.BooleanField(default=False)
    
    # AI data
    ai_recommendations_count = models.PositiveIntegerField(default=0)
    ai_recommendations_clicked = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'visitor_sessions'
        indexes = [
            models.Index(fields=['session_key']),
            models.Index(fields=['visitor_ip', 'created_at']),
            models.Index(fields=['last_activity']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Session {self.session_key[:8]} - {self.visitor_ip}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def duration_minutes(self):
        return int((self.last_activity - self.created_at).total_seconds() / 60) 