from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class AdminChat(models.Model):
    """Admin chat model for support tickets"""
    
    STATUS_CHOICES = [
        ('OPEN', 'Ouvert'),
        ('WAITING', 'En attente'),
        ('RESPONDED', 'Répondu'),
        ('CLOSED', 'Fermé'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Faible'),
        ('MEDIUM', 'Moyenne'),
        ('HIGH', 'Élevée'),
        ('URGENT', 'Urgente'),
    ]
    
    CATEGORY_CHOICES = [
        ('TECHNICAL', 'Problème technique'),
        ('BILLING', 'Facturation'),
        ('ACCOUNT', 'Compte utilisateur'),
        ('PRODUCT', 'Produit/Service'),
        ('GENERAL', 'Question générale'),
        ('COMPLAINT', 'Plainte'),
        ('SUGGESTION', 'Suggestion'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_chats')
    subject = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='GENERAL')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='OPEN')
    
    # Admin assignment
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_chats',
        limit_choices_to={'is_staff': True}
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    is_urgent = models.BooleanField(default=False)
    tags = models.JSONField(default=list, blank=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Chat Admin'
        verbose_name_plural = 'Chats Admin'
    
    def __str__(self):
        return f"Chat #{self.id} - {self.subject} ({self.user.username})"
    
    @property
    def message_count(self):
        return self.messages.count()
    
    @property
    def last_message(self):
        return self.messages.last()
    
    @property
    def is_active(self):
        return self.status in ['OPEN', 'WAITING', 'RESPONDED']
    
    def close(self):
        self.status = 'CLOSED'
        self.closed_at = timezone.now()
        self.save()
    
    def assign_to(self, staff_user):
        if staff_user.is_staff:
            self.assigned_to = staff_user
            self.save()


class AdminMessage(models.Model):
    """Messages in admin chats"""
    
    MESSAGE_TYPE_CHOICES = [
        ('USER', 'Utilisateur'),
        ('ADMIN', 'Administrateur'),
        ('SYSTEM', 'Système'),
    ]
    
    chat = models.ForeignKey(AdminChat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default='USER')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Message properties
    is_read = models.BooleanField(default=False)
    is_internal = models.BooleanField(default=False)  # Internal notes for admins
    attachments = models.JSONField(default=list, blank=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Message Admin'
        verbose_name_plural = 'Messages Admin'
    
    def __str__(self):
        return f"Message #{self.id} - {self.sender.username} ({self.created_at})"
    
    @property
    def is_from_admin(self):
        return self.message_type == 'ADMIN'
    
    @property
    def is_from_user(self):
        return self.message_type == 'USER'
    
    def mark_as_read(self):
        self.is_read = True
        self.save()


class AdminChatTemplate(models.Model):
    """Templates for admin responses"""
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=AdminChat.CATEGORY_CHOICES)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Template de Chat Admin'
        verbose_name_plural = 'Templates de Chat Admin'
    
    def __str__(self):
        return self.name


class AdminChatNote(models.Model):
    """Internal notes for admin chats"""
    
    chat = models.ForeignKey(AdminChat, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_staff': True})
    content = models.TextField()
    is_private = models.BooleanField(default=True)  # Only visible to staff
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Note Admin'
        verbose_name_plural = 'Notes Admin'
    
    def __str__(self):
        return f"Note #{self.id} - {self.author.username} ({self.created_at})" 