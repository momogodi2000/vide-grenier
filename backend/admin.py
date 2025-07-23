# backend/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum
from .models import (
    User, Product, Category, Order, Payment, Review, 
    Chat, Message, Favorite, SearchHistory, Notification,
    AdminStock, PickupPoint, Analytics, ProductImage
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Administration des utilisateurs personnalisée"""
    
    list_display = (
        'email', 'get_full_name', 'user_type', 'city', 
        'trust_score', 'loyalty_points', 'is_verified', 
        'phone_verified', 'date_joined'
    )
    list_filter = ('user_type', 'city', 'is_verified', 'phone_verified', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'phone', 'city', 'address', 'profile_picture')
        }),
        ('Permissions', {
            'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Vérifications', {
            'fields': ('is_verified', 'phone_verified', 'trust_score', 'loyalty_points')
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'date_joined', 'last_activity')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'password1', 'password2', 'user_type', 'city')
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name() or 'Nom non renseigné'
    get_full_name.short_description = 'Nom complet'


class ProductImageInline(admin.TabularInline):
    """Inline pour les images de produits"""
    model = ProductImage
    extra = 1
    max_num = 5
    fields = ('image', 'alt_text', 'is_primary', 'order')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Administration des produits"""
    
    list_display = (
        'title', 'seller', 'category', 'price', 'condition', 
        'city', 'source', 'status', 'views_count', 'created_at'
    )
    list_filter = ('status', 'condition', 'source', 'city', 'category', 'created_at')
    search_fields = ('title', 'description', 'seller__email')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('-created_at',)
    inlines = [ProductImageInline]
    
    fieldsets = (
        ('Informations produit', {
            'fields': ('title', 'slug', 'description', 'category')
        }),
        ('Prix et condition', {
            'fields': ('price', 'condition', 'is_negotiable')
        }),
        ('Localisation et vendeur', {
            'fields': ('seller', 'city', 'source')
        }),
        ('Statut et visibilité', {
            'fields': ('status', 'is_featured', 'is_premium', 'expires_at')
        }),
        ('Statistiques', {
            'fields': ('views_count', 'likes_count'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['make_featured', 'make_active', 'make_suspended']
    
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f'{queryset.count()} produits mis en vedette.')
    make_featured.short_description = 'Mettre en vedette'
    
    def make_active(self, request, queryset):
        queryset.update(status='ACTIVE')
        self.message_user(request, f'{queryset.count()} produits activés.')
    make_active.short_description = 'Activer'
    
    def make_suspended(self, request, queryset):
        queryset.update(status='SUSPENDED')
        self.message_user(request, f'{queryset.count()} produits suspendus.')
    make_suspended.short_description = 'Suspendre'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Administration des catégories"""
    
    list_display = ('name', 'parent', 'icon', 'is_active', 'order', 'products_count')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')
    
    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = 'Nombre de produits'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Administration des commandes"""
    
    list_display = (
        'order_number', 'buyer', 'product', 'total_amount', 
        'status', 'payment_method', 'delivery_method', 'created_at'
    )
    list_filter = ('status', 'payment_method', 'delivery_method', 'created_at')
    search_fields = ('order_number', 'buyer__email', 'product__title')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Commande', {
            'fields': ('order_number', 'buyer', 'product', 'quantity')
        }),
        ('Montants', {
            'fields': ('total_amount', 'commission_amount', 'delivery_cost')
        }),
        ('Paiement et livraison', {
            'fields': ('payment_method', 'delivery_method', 'delivery_address', 'pickup_code')
        }),
        ('Statut et dates', {
            'fields': ('status', 'created_at', 'delivered_at')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Administration des paiements"""
    
    list_display = (
        'payment_reference', 'order', 'amount', 'status', 
        'transaction_id', 'created_at', 'completed_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('payment_reference', 'transaction_id', 'order__order_number')
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at', 'completed_at', 'provider_response')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Administration des avis"""
    
    list_display = (
        'reviewer', 'order', 'overall_rating', 'product_quality',
        'is_verified', 'helpful_count', 'created_at'
    )
    list_filter = ('overall_rating', 'is_verified', 'created_at')
    search_fields = ('reviewer__email', 'comment', 'order__product__title')
    ordering = ('-created_at',)


@admin.register(AdminStock)
class AdminStockAdmin(admin.ModelAdmin):
    """Administration du stock admin"""
    
    list_display = (
        'sku', 'product', 'quantity', 'location', 'status',
        'purchase_price', 'selling_price', 'profit_margin', 'received_date'
    )
    list_filter = ('status', 'location', 'received_date')
    search_fields = ('sku', 'product__title', 'shelf_location')
    ordering = ('-received_date',)
    
    def selling_price(self, obj):
        return obj.product.price if obj.product else 0
    selling_price.short_description = 'Prix vente'
    
    def profit_margin(self, obj):
        if obj.product and obj.purchase_price:
            margin = ((obj.product.price - obj.purchase_price) / obj.purchase_price) * 100
            return f"{margin:.1f}%"
        return "N/A"
    profit_margin.short_description = 'Marge'


@admin.register(PickupPoint)
class PickupPointAdmin(admin.ModelAdmin):
    """Administration des points de retrait"""
    
    list_display = (
        'name', 'city', 'manager', 'capacity', 'current_stock',
        'occupancy_rate', 'is_active'
    )
    list_filter = ('city', 'is_active')
    search_fields = ('name', 'address', 'phone')
    
    def occupancy_rate(self, obj):
        if obj.capacity > 0:
            rate = (obj.current_stock / obj.capacity) * 100
            return f"{rate:.1f}%"
        return "0%"
    occupancy_rate.short_description = 'Taux occupation'


@admin.register(Analytics)
class AnalyticsAdmin(admin.ModelAdmin):
    """Administration des analytics"""
    
    list_display = ('metric_type', 'user', 'page_url', 'ip_address', 'created_at')
    list_filter = ('metric_type', 'created_at')
    search_fields = ('user__email', 'page_url', 'ip_address')
    ordering = ('-created_at',)
    
    # Lecture seule pour préserver l'intégrité des données
    readonly_fields = ('metric_type', 'user', 'session_id', 'page_url', 'referrer', 
                      'user_agent', 'ip_address', 'data', 'created_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Administration des notifications"""
    
    list_display = ('title', 'user', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__email')
    ordering = ('-created_at',)


# Personnalisation de l'interface admin
admin.site.site_header = "Administration Vidé-Grenier Kamer"
admin.site.site_title = "VGK Admin"
admin.site.index_title = "Panneau d'administration"




# backend/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

User = get_user_model()

# Remove the import errors by commenting out or creating placeholder classes
# Only include actual model imports when the models exist

# Newsletter Models (uncomment when models are ready)
# from .models import (
#     NewsletterSubscriber, 
#     Newsletter, 
#     ScheduledNewsletter,
#     Payment,
#     LoyaltyProgram,
#     Promotion,
#     Notification
# )

# Placeholder admin classes to prevent import errors
class AdminPaymentListView:
    """Placeholder - will be replaced when models are ready"""
    pass

class AdminLoyaltyListView:
    """Placeholder - will be replaced when models are ready"""
    pass

class AdminPromotionListView:
    """Placeholder - will be replaced when models are ready"""
    pass

class AdminNewsletterListView:
    """Placeholder - will be replaced when models are ready"""
    pass

class AdminNotificationListView:
    """Placeholder - will be replaced when models are ready"""
    pass

# Newsletter Subscriber Admin (uncomment when model is ready)
# @admin.register(NewsletterSubscriber)
# class NewsletterSubscriberAdmin(admin.ModelAdmin):
#     list_display = ['email', 'name', 'is_active', 'subscribed_at']
#     list_filter = ['is_active', 'subscribed_at']
#     search_fields = ['email', 'name']
#     actions = ['activate_subscribers', 'deactivate_subscribers']
#     
#     def activate_subscribers(self, request, queryset):
#         queryset.update(is_active=True)
#         self.message_user(request, f'{queryset.count()} subscribers activated.')
#     activate_subscribers.short_description = "Activate selected subscribers"
#     
#     def deactivate_subscribers(self, request, queryset):
#         queryset.update(is_active=False)
#         self.message_user(request, f'{queryset.count()} subscribers deactivated.')
#     deactivate_subscribers.short_description = "Deactivate selected subscribers"

# Newsletter Admin (uncomment when model is ready)
# @admin.register(Newsletter)
# class NewsletterAdmin(admin.ModelAdmin):
#     list_display = ['subject', 'created_at', 'is_sent', 'recipients_count']
#     list_filter = ['is_sent', 'created_at']
#     search_fields = ['subject', 'content']
#     readonly_fields = ['created_at', 'sent_at']
#     
#     fieldsets = (
#         ('Content', {
#             'fields': ('subject', 'html_content', 'text_content')
#         }),
#         ('Status', {
#             'fields': ('is_sent', 'sent_at', 'recipients_count', 'failed_count')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at',),
#             'classes': ('collapse',)
#         }),
#     )

# Scheduled Newsletter Admin (uncomment when model is ready)
# @admin.register(ScheduledNewsletter)
# class ScheduledNewsletterAdmin(admin.ModelAdmin):
#     list_display = ['subject', 'scheduled_time', 'is_sent', 'is_cancelled', 'created_by']
#     list_filter = ['is_sent', 'is_cancelled', 'scheduled_time']
#     search_fields = ['subject', 'html_content']
#     readonly_fields = ['created_at', 'sent_at']
#     
#     fieldsets = (
#         ('Content', {
#             'fields': ('subject', 'html_content', 'text_content')
#         }),
#         ('Scheduling', {
#             'fields': ('scheduled_time', 'is_cancelled')
#         }),
#         ('Status', {
#             'fields': ('is_sent', 'sent_at', 'recipients_count', 'failed_count')
#         }),
#         ('Meta', {
#             'fields': ('created_by', 'created_at'),
#             'classes': ('collapse',)
#         }),
#     )
#     
#     def save_model(self, request, obj, form, change):
#         if not change:  # If creating new object
#             obj.created_by = request.user
#         super().save_model(request, obj, form, change)

# Payment Admin (uncomment when model is ready)
# @admin.register(Payment)
# class PaymentAdmin(admin.ModelAdmin):
#     list_display = ['transaction_id', 'user', 'amount', 'status', 'created_at']
#     list_filter = ['status', 'payment_method', 'created_at']
#     search_fields = ['transaction_id', 'user__username', 'user__email']
#     readonly_fields = ['transaction_id', 'created_at', 'updated_at']
#     
#     fieldsets = (
#         ('Transaction Info', {
#             'fields': ('transaction_id', 'user', 'amount', 'currency')
#         }),
#         ('Payment Details', {
#             'fields': ('payment_method', 'status', 'stripe_payment_id')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
#     
#     def has_delete_permission(self, request, obj=None):
#         return False  # Don't allow deletion of payment records

# Loyalty Program Admin (uncomment when model is ready)
# @admin.register(LoyaltyProgram)
# class LoyaltyProgramAdmin(admin.ModelAdmin):
#     list_display = ['name', 'points_per_euro', 'is_active', 'created_at']
#     list_filter = ['is_active', 'created_at']
#     search_fields = ['name', 'description']
#     
#     fieldsets = (
#         ('Program Details', {
#             'fields': ('name', 'description', 'points_per_euro')
#         }),
#         ('Settings', {
#             'fields': ('is_active', 'minimum_points_to_redeem')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )

# Promotion Admin (uncomment when model is ready)
# @admin.register(Promotion)
# class PromotionAdmin(admin.ModelAdmin):
#     list_display = ['name', 'code', 'discount_percentage', 'is_active', 'valid_until']
#     list_filter = ['is_active', 'promotion_type', 'created_at']
#     search_fields = ['name', 'code', 'description']
#     
#     fieldsets = (
#         ('Promotion Details', {
#             'fields': ('name', 'description', 'code')
#         }),
#         ('Discount Settings', {
#             'fields': ('promotion_type', 'discount_percentage', 'discount_amount')
#         }),
#         ('Validity', {
#             'fields': ('is_active', 'valid_from', 'valid_until', 'usage_limit')
#         }),
#         ('Usage', {
#             'fields': ('times_used',),
#             'classes': ('collapse',)
#         }),
#     )
#     
#     def save_model(self, request, obj, form, change):
#         if not obj.code:
#             # Generate unique code if not provided
#             import uuid
#             obj.code = str(uuid.uuid4())[:8].upper()
#         super().save_model(request, obj, form, change)

# Notification Admin (uncomment when model is ready)
# @admin.register(Notification)
# class NotificationAdmin(admin.ModelAdmin):
#     list_display = ['title', 'notification_type', 'is_sent', 'created_at']
#     list_filter = ['notification_type', 'is_sent', 'created_at']
#     search_fields = ['title', 'message']
#     
#     fieldsets = (
#         ('Notification Content', {
#             'fields': ('title', 'message', 'notification_type')
#         }),
#         ('Recipients', {
#             'fields': ('recipients', 'send_to_all')
#         }),
#         ('Status', {
#             'fields': ('is_sent', 'sent_at', 'sent_count')
#         }),
#     )

# Customize admin site
admin.site.site_header = "Vide Grenier Administration"
admin.site.site_title = "Vide Grenier Admin"
admin.site.index_title = "Welcome to Vide Grenier Administration"

# Add custom CSS and JS
admin.site.enable_nav_sidebar = True