"""
Newsletter URL Patterns
Enhanced newsletter system with campaign management, mass emails, and scheduled messages
"""

from django.urls import path
from . import newsletter_admin

app_name = 'newsletter'

urlpatterns = [
    # Newsletter Dashboard
    path('dashboard/', newsletter_admin.newsletter_dashboard, name='dashboard'),
    
    # Campaign Management
    path('campaigns/', newsletter_admin.NewsletterCampaignListView.as_view(), name='campaigns'),
    path('campaigns/create/', newsletter_admin.NewsletterCampaignCreateView.as_view(), name='campaign_create'),
    path('campaigns/<uuid:pk>/', newsletter_admin.NewsletterCampaignDetailView.as_view(), name='campaign_detail'),
    path('campaigns/<uuid:pk>/edit/', newsletter_admin.NewsletterCampaignUpdateView.as_view(), name='campaign_edit'),
    path('campaigns/<uuid:campaign_id>/send/', newsletter_admin.send_campaign, name='campaign_send'),
    path('campaigns/<uuid:campaign_id>/schedule/', newsletter_admin.schedule_campaign, name='campaign_schedule'),
    
    # Subscriber Management
    path('subscribers/', newsletter_admin.NewsletterSubscriberListView.as_view(), name='subscribers'),
    path('subscribers/export/', newsletter_admin.export_subscribers, name='subscribers_export'),
    
    # Template Management
    path('templates/', newsletter_admin.NewsletterTemplateListView.as_view(), name='templates'),
    path('templates/create/', newsletter_admin.NewsletterTemplateCreateView.as_view(), name='template_create'),
    
    # Scheduled Newsletters
    path('scheduled/', newsletter_admin.ScheduledNewsletterListView.as_view(), name='scheduled'),
    
    # Analytics
    path('analytics/', newsletter_admin.newsletter_analytics, name='analytics'),
    
    # Webhooks
    path('webhook/', newsletter_admin.newsletter_webhook, name='webhook'),
] 