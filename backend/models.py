# backend/models.py - VERSION CORRIGÉE
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
    
    def __str__(self):
        return f"{self.email} ({self.get_user_type_display()})"
    
    def get_absolute_url(self):
        return reverse('backend:profile', kwargs={'pk': self.pk})
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def loyalty_level(self):
        if self.loyalty_points >= 20000:
            return 'PLATINE'
        elif self.loyalty_points >= 5000:
            return 'OR'
        elif self.loyalty_points >= 1000:
            return 'ARGENT'
        return 'BRONZE'


class Category(models.Model):
    """Catégories de produits hiérarchiques"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    icon = models.CharField(max_length=50, blank=True)  # For emoji or icon class
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name = 'Catégorie'
        verbose_name_plural = 'Catégories'
        ordering = ['order', 'name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def get_absolute_url(self):
        return reverse('backend:category', kwargs={'slug': self.slug})


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
        ('ACTIVE', 'Actif'),
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
    is_premium = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products'
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('backend:product_detail', kwargs={'slug': self.slug})
    
    @property
    def main_image(self):
        return self.images.filter(is_primary=True).first()
    
    @property
    def commission_amount(self):
        if self.source == 'CLIENT':
            from django.conf import settings
            from decimal import Decimal
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
        ('NOUPIA', 'Noupia'),
        ('CARD', 'Carte bancaire'),
        ('CASH_ON_DELIVERY', 'Paiement à la livraison'),
    ]
    
    DELIVERY_METHODS = [
        ('PICKUP', 'Retrait en point'),
        ('DELIVERY', 'Livraison à domicile'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True)
    # For public/anonymous orders, buyer can be null
    buyer = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='orders', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUSES, default='PENDING')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHODS)
    delivery_address = models.TextField(blank=True)
    pickup_code = models.CharField(max_length=6, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'orders'
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
        ordering = ['-created_at']
    
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
    is_verified = models.BooleanField(default=True)
    helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Avis de {self.reviewer.email} - {self.overall_rating}★"
    
    @property
    def average_rating(self):
        return (self.product_quality + self.seller_communication + 
                self.delivery_speed + self.packaging + self.overall_rating) / 5


class Chat(models.Model):
    """Conversations entre acheteurs et vendeurs"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='chats')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_chats')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_chats')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chats'
        unique_together = ['product', 'buyer', 'seller']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Chat {self.buyer.email} - {self.seller.email}"


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
    
    def __str__(self):
        return f"Message de {self.sender.email} - {self.created_at}"


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
    
    def __str__(self):
        return f"Notification pour {self.user.email}: {self.title}"


class AdminStock(models.Model):
    """Stock administrateur avec gestion physique"""
    
    STATUSES = [
        ('AVAILABLE', 'Disponible'),
        ('RESERVED', 'Réservé'),
        ('SOLD', 'Vendu'),
        ('DAMAGED', 'Endommagé'),
        ('MAINTENANCE', 'En maintenance'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='admin_stock')
    sku = models.CharField(max_length=50, unique=True)
    quantity = models.PositiveIntegerField(default=1)
    location = models.CharField(max_length=20, choices=User.CITIES)
    shelf_location = models.CharField(max_length=100, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    condition_notes = models.TextField(blank=True)
    warranty_info = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default='AVAILABLE')
    received_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'admin_stock'
        ordering = ['location', 'shelf_location']
    
    def __str__(self):
        return f"Stock {self.sku} - {self.product.title}"
    
    @property
    def profit_margin(self):
        if self.purchase_price > 0:
            return ((self.product.price - self.purchase_price) / self.purchase_price) * 100
        return 0


class PickupPoint(models.Model):
    """Points de retrait physiques"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=20, choices=User.CITIES)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    opening_hours = models.JSONField(default=dict)
    capacity = models.PositiveIntegerField(default=100)
    current_stock = models.PositiveIntegerField(default=0)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'pickup_points'
        ordering = ['city', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.city}"
    
    @property
    def is_full(self):
        return self.current_stock >= self.capacity


class Analytics(models.Model):
    """Analytics et métriques business"""
    
    METRIC_TYPES = [
        ('PAGE_VIEW', 'Vue de page'),
        ('PRODUCT_VIEW', 'Vue produit'),
        ('SEARCH', 'Recherche'),
        ('CLICK', 'Clic'),
        ('CONVERSION', 'Conversion'),
        ('REVENUE', 'Revenus'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    page_url = models.URLField(blank=True)
    referrer = models.URLField(blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField()
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['metric_type', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.metric_type} - {self.created_at}"
    




# Models to add for search functionality
class SavedSearch(models.Model):
    """Recherches sauvegardées par les utilisateurs"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=100)
    query_params = models.TextField()  # JSON string of search parameters
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'saved_searches'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"
    
    @property
    def query_description(self):
        """Description lisible de la recherche"""
        try:
            params = json.loads(self.query_params)
            parts = []
            
            if params.get('q'):
                parts.append(f"Mots-clés: {params['q']}")
            if params.get('category'):
                parts.append(f"Catégorie: {params['category']}")
            if params.get('price_min') or params.get('price_max'):
                price_range = f"Prix: {params.get('price_min', '0')} - {params.get('price_max', '∞')} FCFA"
                parts.append(price_range)
                
            return ' | '.join(parts) if parts else 'Recherche personnalisée'
        except:
            return 'Recherche personnalisée'


class SearchAlert(models.Model):
    """Alertes de recherche pour notifications"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_alerts')
    name = models.CharField(max_length=100)
    query_params = models.TextField()
    is_active = models.BooleanField(default=True)
    last_notification = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'search_alerts'
        ordering = ['-created_at']