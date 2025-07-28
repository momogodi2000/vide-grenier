from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()

class NewsletterSubscriber(models.Model):
    """Abonnés à la newsletter"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    city = models.CharField(max_length=20, blank=True, choices=User.CITIES)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    last_email_sent = models.DateTimeField(null=True, blank=True)
    email_count = models.PositiveIntegerField(default=0)
    preferences = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'newsletter_subscribers'
        ordering = ['-subscribed_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['city']),
            models.Index(fields=['subscribed_at']),
        ]

    def __str__(self):
        return self.email


class NewsletterCampaign(models.Model):
    """Campagnes de newsletter"""
    CAMPAIGN_TYPES = [
        ('NEWSLETTER', 'Newsletter générale'),
        ('PROMOTION', 'Promotion/Offre'),
        ('ANNOUNCEMENT', 'Annonce importante'),
        ('PRODUCT_ALERT', 'Alerte produit'),
        ('EVENT', 'Événement'),
        ('CUSTOM', 'Campagne personnalisée'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Brouillon'),
        ('SCHEDULED', 'Programmée'),
        ('SENDING', 'En cours d\'envoi'),
        ('SENT', 'Envoyée'),
        ('CANCELLED', 'Annulée'),
        ('FAILED', 'Échouée'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    html_content = models.TextField(blank=True)
    campaign_type = models.CharField(max_length=20, choices=CAMPAIGN_TYPES, default='NEWSLETTER')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Targeting options
    target_cities = models.JSONField(default=list, blank=True)
    target_user_types = models.JSONField(default=list, blank=True)
    target_loyalty_levels = models.JSONField(default=list, blank=True)
    target_active_users = models.BooleanField(default=True)
    target_new_subscribers = models.BooleanField(default=False)
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    total_recipients = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    opened_count = models.PositiveIntegerField(default=0)
    clicked_count = models.PositiveIntegerField(default=0)
    unsubscribed_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='campaigns_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'newsletter_campaigns'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['campaign_type']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    @property
    def open_rate(self):
        if self.sent_count > 0:
            return (self.opened_count / self.sent_count) * 100
        return 0
    
    @property
    def click_rate(self):
        if self.sent_count > 0:
            return (self.clicked_count / self.sent_count) * 100
        return 0


class NewsletterTemplate(models.Model):
    """Templates de newsletter réutilisables"""
    TEMPLATE_TYPES = [
        ('WELCOME', 'Bienvenue'),
        ('PROMOTION', 'Promotion'),
        ('NEWSLETTER', 'Newsletter générale'),
        ('EVENT', 'Événement'),
        ('CUSTOM', 'Personnalisé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    subject_template = models.CharField(max_length=200)
    content_template = models.TextField()
    html_template = models.TextField(blank=True)
    variables = models.JSONField(default=dict, blank=True, help_text="Variables disponibles dans le template")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='templates_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'newsletter_templates'
        ordering = ['name']
        indexes = [
            models.Index(fields=['template_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name


class NewsletterLog(models.Model):
    """Logs des envois de newsletter"""
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('SENT', 'Envoyé'),
        ('FAILED', 'Échoué'),
        ('BOUNCED', 'Rebondi'),
        ('UNSUBSCRIBED', 'Désabonné'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(NewsletterCampaign, on_delete=models.CASCADE, related_name='logs')
    subscriber = models.ForeignKey(NewsletterSubscriber, on_delete=models.CASCADE, related_name='email_logs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'newsletter_logs'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['campaign', 'subscriber']),
        ]
    
    def __str__(self):
        return f"{self.campaign.name} -> {self.subscriber.email} ({self.status})"


class ScheduledNewsletter(models.Model):
    """Newsletters programmées"""
    FREQUENCY_CHOICES = [
        ('DAILY', 'Quotidien'),
        ('WEEKLY', 'Hebdomadaire'),
        ('MONTHLY', 'Mensuel'),
        ('CUSTOM', 'Personnalisé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    template = models.ForeignKey(NewsletterTemplate, on_delete=models.CASCADE, related_name='scheduled_newsletters')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='WEEKLY')
    is_active = models.BooleanField(default=True)
    next_send_date = models.DateTimeField()
    last_sent_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='scheduled_newsletters_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'scheduled_newsletters'
        ordering = ['next_send_date']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['next_send_date']),
            models.Index(fields=['frequency']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"


# Legacy model for backward compatibility
class Newsletter(models.Model):
    """Legacy Newsletter model for backward compatibility"""
    subject = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='newsletters_created')
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    recipients_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'newsletters'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.subject
