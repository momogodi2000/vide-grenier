# backend/models.py - VERSION CORRIGÉE (SQLite Compatible)
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# PostgreSQL-specific imports (optional)
try:
    from django.contrib.postgres.indexes import GinIndex
    from django.contrib.postgres.search import SearchVectorField, SearchVector
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    # Fallback for SQLite
    class GinIndex:
        def __init__(self, fields):
            self.fields = fields
    
    class SearchVectorField(models.TextField):
        pass
    
    class SearchVector:
        def __init__(self, field, weight=None):
            self.field = field
            self.weight = weight
        
        def __add__(self, other):
            return self

from decimal import Decimal
from PIL import Image
import uuid
import os

class User(AbstractUser):
    """Modèle utilisateur personnalisé pour VGK"""
    
    USER_TYPES = [
        ('CLIENT', 'Client'),
        ('ADMIN', 'Administrateur'),
        ('STAFF', 'Staff Point de Retrait'),
    ]
    
    CITIES = [
        ('DOUALA', 'Douala'),
        ('YAOUNDE', 'Yaoundé'),
        ('BAFOUSSAM', 'Bafoussam'),
        ('GAROUA', 'Garoua'),
        ('BAMENDA', 'Bamenda'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Override username to make it optional since we use email as USERNAME_FIELD
    username = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='CLIENT')
    reset_token = models.CharField(max_length=128, blank=True, null=True, help_text="Token de réinitialisation du mot de passe")
    city = models.CharField(max_length=20, choices=CITIES, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='users/profiles/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    trust_score = models.IntegerField(default=100)
    loyalty_points = models.IntegerField(default=0)
    loyalty_level = models.CharField(
        max_length=20,
        choices=[
            ('bronze', 'Bronze'),
            ('silver', 'Argent'),
            ('gold', 'Or'),
            ('platinum', 'Platine')
        ],
        default='bronze'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['user_type', 'is_active']),
            models.Index(fields=['city', 'is_active']),
            models.Index(fields=['created_at']),
            models.Index(fields=['last_activity']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
    
    @property
    def display_name(self):
        return self.get_full_name() or self.email
    
    def get_city_display(self):
        return dict(self.CITIES).get(self.city, self.city)


class Category(models.Model):
    """Catégories de produits"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name = 'Catégorie'
        verbose_name_plural = 'Catégories'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent', 'is_active']),
            models.Index(fields=['order', 'is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('backend:category_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    """Modèle pour les produits"""
    
    CONDITIONS = [
        ('NEUF', 'Neuf'),
        ('EXCELLENT', 'Excellent état'),
        ('BON', 'Bon état'),
        ('CORRECT', 'État correct'),
        ('USAGE', 'Très usagé'),
    ]
    
    SOURCES = [
        ('CLIENT', 'Article Client'),
        ('ADMIN', 'Stock Admin'),
    ]
    
    STATUSES = [
        ('DRAFT', 'Brouillon'),
        ('PENDING', 'En attente d\'approbation'),
        ('ACTIVE', 'Actif'),
        ('REJECTED', 'Rejeté'),
        ('SOLD', 'Vendu'),
        ('RESERVED', 'Réservé'),
        ('EXPIRED', 'Expiré'),
        ('SUSPENDED', 'Suspendu'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products_sold')
    price = models.DecimalField(max_digits=10, decimal_places=2, 
                               validators=[MinValueValidator(1000), MaxValueValidator(50000000)])
    condition = models.CharField(max_length=20, choices=CONDITIONS)
    source = models.CharField(max_length=10, choices=SOURCES, default='CLIENT')
    status = models.CharField(max_length=20, choices=STATUSES, default='ACTIVE')
    is_negotiable = models.BooleanField(default=True)
    city = models.CharField(max_length=20, choices=User.CITIES)
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Full-text search field for PostgreSQL (optional)
    # Removed for SQLite compatibility
    
    class Meta:
        db_table = 'products'
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['city', 'status']),
            models.Index(fields=['price']),
            models.Index(fields=['condition', 'status']),
            models.Index(fields=['is_featured', 'status']),
            models.Index(fields=['views_count']),
            models.Index(fields=['likes_count']),
        ]
        
        # Add PostgreSQL-specific indexes only if available
        # Removed for SQLite compatibility
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.title)
            self.slug = base_slug
            
            # Ensure uniqueness
            counter = 1
            while Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        
        # Update search vector for full-text search (PostgreSQL only)
        # Removed for SQLite compatibility
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('backend:product_detail', kwargs={'slug': self.slug})
    
    @property
    def main_image(self):
        return self.images.filter(is_primary=True).first()
    
    @property
    def commission_amount(self):
        if self.source == 'CLIENT':
            from django.conf import settings
            commission_rate = Decimal(str(settings.VGK_SETTINGS.get('COMMISSION_RATE', 0.08)))
            return self.price * commission_rate
        return Decimal('0')
    
    @property
    def seller_amount(self):
        return self.price - self.commission_amount


class ProductImage(models.Model):
    """Images des produits"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/images/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'product_images'
        ordering = ['order']
        indexes = [
            models.Index(fields=['product', 'is_primary']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        return f"Image {self.order} - {self.product.title}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Resize image
        if self.image:
            try:
                img = Image.open(self.image.path)
                if img.height > 1200 or img.width > 1200:
                    img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                    img.save(self.image.path, optimize=True, quality=90)
            except Exception:
                pass  # Ignorer les erreurs de traitement d'image


class Order(models.Model):
    """Commandes"""
    
    STATUSES = [
        ('PENDING', 'En attente'),
        ('PAID', 'Payé'),
        ('PROCESSING', 'En traitement'),
        ('SHIPPED', 'Expédié'),
        ('DELIVERED', 'Livré'),
        ('CANCELLED', 'Annulé'),
        ('REFUNDED', 'Remboursé'),
    ]
    
    PAYMENT_METHODS = [
        ('CAMPAY', 'Campay'),
        ('ORANGE_MONEY', 'Orange Money'),
        ('MTN_MONEY', 'MTN Mobile Money'),
        ('CASH', 'Espèces'),
    ]
    
    DELIVERY_METHODS = [
        ('PICKUP', 'Point de retrait'),
        ('DELIVERY', 'Livraison à domicile'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders_bought')
    pickup_point = models.ForeignKey('PickupPoint', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUSES, default='PENDING')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHODS)
    delivery_address = models.TextField(blank=True)
    pickup_code = models.CharField(max_length=6, blank=True)
    notes = models.TextField(blank=True)
    
    # Fields for visitor/anonymous orders
    visitor_name = models.CharField(max_length=100, blank=True, help_text="Nom du visiteur (pour commandes sans compte)")
    visitor_email = models.EmailField(blank=True, help_text="Email du visiteur (pour commandes sans compte)")
    visitor_phone = models.CharField(max_length=20, blank=True, help_text="Téléphone du visiteur (pour commandes sans compte)")
    whatsapp_preferred = models.BooleanField(default=False, help_text="Le visiteur préfère WhatsApp pour contact")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'orders'
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['product', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['payment_method', 'status']),
            models.Index(fields=['pickup_point', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['delivered_at']),
        ]
    
    def __str__(self):
        return f"Commande {self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        import random
        import string
        return f"VGK{''.join(random.choices(string.digits, k=8))}"


class Payment(models.Model):
    """Paiements"""
    
    STATUSES = [
        ('PENDING', 'En attente'),
        ('PROCESSING', 'En traitement'),
        ('COMPLETED', 'Complété'),
        ('FAILED', 'Échoué'),
        ('CANCELLED', 'Annulé'),
        ('REFUNDED', 'Remboursé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    payment_reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUSES, default='PENDING')
    provider_response = models.JSONField(default=dict)
    transaction_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_reference']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['completed_at']),
        ]
    
    def __str__(self):
        return f"Paiement {self.payment_reference}"


class Review(models.Model):
    """Avis clients"""
    
    RATING_CHOICES = [(i, i) for i in range(1, 6)]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    product_quality = models.IntegerField(choices=RATING_CHOICES)
    seller_communication = models.IntegerField(choices=RATING_CHOICES)
    delivery_speed = models.IntegerField(choices=RATING_CHOICES)
    packaging = models.IntegerField(choices=RATING_CHOICES)
    overall_rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    images = models.JSONField(default=list, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reviewer', 'created_at']),
            models.Index(fields=['overall_rating']),
            models.Index(fields=['is_verified', 'created_at']),
        ]
    
    def __str__(self):
        return f"Avis de {self.reviewer.email} - {self.overall_rating}/5"


class Chat(models.Model):
    """Conversations privées entre acheteur et vendeur"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='chats')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats_as_buyer')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats_as_seller')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chats'
        unique_together = ['product', 'buyer', 'seller']
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['buyer', 'is_active']),
            models.Index(fields=['seller', 'is_active']),
            models.Index(fields=['product', 'is_active']),
            models.Index(fields=['updated_at']),
        ]
    
    def __str__(self):
        return f"Chat {self.buyer.email} - {self.seller.email}"


class GroupChat(models.Model):
    """Conversations de groupe entre utilisateurs"""
    
    TYPES = [
        ('ADMIN_CLIENT', 'Admin-Client'),
        ('ADMIN_STAFF', 'Admin-Staff'),
        ('CLIENT_STAFF', 'Client-Staff'),
        ('GENERAL', 'Général'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPES)
    participants = models.ManyToManyField(User, related_name='group_chats')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'group_chats'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['type', 'is_active']),
            models.Index(fields=['updated_at']),
        ]
    
    def __str__(self):
        return f"Groupe {self.name}"
    
    @property
    def last_message(self):
        return self.group_messages.order_by('-created_at').first()


class Message(models.Model):
    """Messages dans les chats"""
    
    MESSAGE_TYPES = [
        ('TEXT', 'Texte'),
        ('IMAGE', 'Image'),
        ('OFFER', 'Offre de prix'),
        ('SYSTEM', 'Message système'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='TEXT')
    content = models.TextField()
    image = models.ImageField(upload_to='chat/images/', blank=True, null=True)
    offer_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['chat', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['is_read', 'created_at']),
            models.Index(fields=['message_type']),
        ]
    
    def __str__(self):
        return f"Message de {self.sender.email} - {self.created_at}"


class GroupChatMessage(models.Model):
    """Messages dans les conversations de groupe"""
    
    MESSAGE_TYPES = [
        ('TEXT', 'Texte'),
        ('IMAGE', 'Image'),
        ('FILE', 'Fichier'),
        ('SYSTEM', 'Message système'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group_chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='group_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_group_messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='TEXT')
    content = models.TextField()
    image = models.ImageField(upload_to='chat/group_images/', blank=True, null=True)
    file = models.FileField(upload_to='chat/group_files/', blank=True, null=True)
    read_by = models.ManyToManyField(User, related_name='read_group_messages', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'group_chat_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['group_chat', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['message_type']),
        ]
    
    def __str__(self):
        return f"Message groupe de {self.sender.email} - {self.created_at}"
    
    @property
    def is_read_by_all(self):
        return self.read_by.count() == self.group_chat.participants.count()


class Favorite(models.Model):
    """Produits favoris des utilisateurs"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'favorites'
        unique_together = ['user', 'product']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['product', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.product.title}"


class SearchHistory(models.Model):
    """Historique des recherches"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history', null=True, blank=True)
    search_term = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    results_count = models.PositiveIntegerField(default=0)
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'search_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['search_term']),
            models.Index(fields=['ip_address', 'created_at']),
        ]
    
    def __str__(self):
        return f"Recherche: {self.search_term}"


class Notification(models.Model):
    """Notifications utilisateurs"""
    
    TYPES = [
        ('ORDER', 'Commande'),
        ('PAYMENT', 'Paiement'),
        ('MESSAGE', 'Message'),
        ('REVIEW', 'Avis'),
        ('SYSTEM', 'Système'),
        ('PROMOTION', 'Promotion'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['type', 'created_at']),
            models.Index(fields=['is_read', 'created_at']),
        ]
    
    def __str__(self):
        return f"Notification pour {self.user.email}: {self.title}"


class PickupPoint(models.Model):
    """Points de retrait"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=20, choices=User.CITIES)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    opening_hours = models.JSONField(default=dict, blank=True)
    special_hours = models.JSONField(default=dict, blank=True)
    capacity = models.PositiveIntegerField(default=100)
    processing_time = models.PositiveIntegerField(default=24, help_text="Temps de traitement en heures")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pickup_points'
        ordering = ['name']
        indexes = [
            models.Index(fields=['city', 'is_active']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.city}"


# NewsletterSubscriber model moved to models_newsletter.py to avoid conflicts


class SearchAlert(models.Model):
    """Alertes de recherche pour les utilisateurs"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_alerts')
    search_term = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    city = models.CharField(max_length=20, choices=User.CITIES, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'search_alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['search_term']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f"Alerte: {self.search_term} - {self.user.email}"


class SavedSearch(models.Model):
    """Recherches sauvegardées par les utilisateurs"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=100)
    search_params = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'saved_searches'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.user.email}"


class AdminStock(models.Model):
    """Stock administrateur"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='admin_stock')
    quantity = models.PositiveIntegerField(default=0)
    location = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'admin_stock'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['product', 'quantity']),
            models.Index(fields=['quantity']),
        ]
    
    def __str__(self):
        return f"{self.product.title} - {self.quantity} unités"


class ProductAlert(models.Model):
    """Alertes de produits (stock faible, etc.)"""
    
    TYPES = [
        ('LOW_STOCK', 'Stock faible'),
        ('PRICE_CHANGE', 'Changement de prix'),
        ('STATUS_CHANGE', 'Changement de statut'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='alerts')
    type = models.CharField(max_length=20, choices=TYPES)
    message = models.TextField(blank=True, default="")
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'product_alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'type']),
            models.Index(fields=['is_resolved', 'created_at']),
        ]
    
    def __str__(self):
        return f"Alerte {self.type} - {self.product.title}"