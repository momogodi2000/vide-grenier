"""
Enhanced Newsletter Admin Views
Provides comprehensive newsletter management functionality including:
- Campaign management
- Mass email functionality
- Scheduled messages
- Subscriber management
- Analytics and reporting
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
import uuid
from datetime import datetime, timedelta

from .models_newsletter import (
    NewsletterSubscriber, NewsletterCampaign, NewsletterTemplate,
    NewsletterLog, ScheduledNewsletter
)
from .models import User


def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and user.user_type == 'ADMIN'


@login_required
@user_passes_test(is_admin)
def newsletter_dashboard(request):
    """Newsletter dashboard with statistics and overview"""
    context = {
        'total_subscribers': NewsletterSubscriber.objects.filter(is_active=True).count(),
        'total_campaigns': NewsletterCampaign.objects.count(),
        'sent_campaigns': NewsletterCampaign.objects.filter(status='SENT').count(),
        'scheduled_campaigns': NewsletterCampaign.objects.filter(status='SCHEDULED').count(),
        'total_templates': NewsletterTemplate.objects.filter(is_active=True).count(),
        'scheduled_newsletters': ScheduledNewsletter.objects.filter(is_active=True).count(),
        
        # Recent activity
        'recent_campaigns': NewsletterCampaign.objects.order_by('-created_at')[:5],
        'recent_subscribers': NewsletterSubscriber.objects.order_by('-subscribed_at')[:10],
        'recent_logs': NewsletterLog.objects.order_by('-sent_at')[:20],
        
        # Statistics
        'subscribers_by_city': NewsletterSubscriber.objects.filter(is_active=True).values('city').annotate(count=Count('id')).order_by('-count')[:5],
        'campaigns_by_type': NewsletterCampaign.objects.values('campaign_type').annotate(count=Count('id')).order_by('-count'),
        
        # Performance metrics
        'avg_open_rate': NewsletterCampaign.objects.filter(status='SENT').aggregate(avg=Avg('opened_count'))['avg'] or 0,
        'avg_click_rate': NewsletterCampaign.objects.filter(status='SENT').aggregate(avg=Avg('clicked_count'))['avg'] or 0,
    }
    
    return render(request, 'backend/admin/newsletter/dashboard.html', context)


class NewsletterCampaignListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all newsletter campaigns"""
    model = NewsletterCampaign
    template_name = 'backend/admin/newsletter/campaigns/list.html'
    context_object_name = 'campaigns'
    paginate_by = 20
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_queryset(self):
        queryset = NewsletterCampaign.objects.all().order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by type
        campaign_type = self.request.GET.get('type')
        if campaign_type:
            queryset = queryset.filter(campaign_type=campaign_type)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(subject__icontains=search) |
                Q(content__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'status_choices': NewsletterCampaign.STATUS_CHOICES,
            'campaign_types': NewsletterCampaign.CAMPAIGN_TYPES,
            'total_campaigns': NewsletterCampaign.objects.count(),
            'draft_campaigns': NewsletterCampaign.objects.filter(status='DRAFT').count(),
            'scheduled_campaigns': NewsletterCampaign.objects.filter(status='SCHEDULED').count(),
            'sent_campaigns': NewsletterCampaign.objects.filter(status='SENT').count(),
        })
        return context


class NewsletterCampaignCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new newsletter campaign"""
    model = NewsletterCampaign
    template_name = 'backend/admin/newsletter/campaigns/create.html'
    fields = [
        'name', 'subject', 'content', 'html_content', 'campaign_type',
        'target_cities', 'target_user_types', 'target_loyalty_levels',
        'target_active_users', 'target_new_subscribers', 'scheduled_at'
    ]
    success_url = reverse_lazy('backend:newsletter_campaigns')
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Campagne créée avec succès!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'campaign_types': NewsletterCampaign.CAMPAIGN_TYPES,
            'cities': User.CITIES,
            'user_types': User.USER_TYPES,
            'loyalty_levels': User._meta.get_field('loyalty_level').choices,
            'templates': NewsletterTemplate.objects.filter(is_active=True),
        })
        return context


class NewsletterCampaignUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update a newsletter campaign"""
    model = NewsletterCampaign
    template_name = 'backend/admin/newsletter/campaigns/edit.html'
    fields = [
        'name', 'subject', 'content', 'html_content', 'campaign_type',
        'target_cities', 'target_user_types', 'target_loyalty_levels',
        'target_active_users', 'target_new_subscribers', 'scheduled_at'
    ]
    success_url = reverse_lazy('backend:newsletter_campaigns')
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Campagne mise à jour avec succès!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'campaign_types': NewsletterCampaign.CAMPAIGN_TYPES,
            'cities': User.CITIES,
            'user_types': User.USER_TYPES,
            'loyalty_levels': User._meta.get_field('loyalty_level').choices,
            'templates': NewsletterTemplate.objects.filter(is_active=True),
        })
        return context


class NewsletterCampaignDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View campaign details and statistics"""
    model = NewsletterCampaign
    template_name = 'backend/admin/newsletter/campaigns/detail.html'
    context_object_name = 'campaign'
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign = self.get_object()
        
        context.update({
            'logs': NewsletterLog.objects.filter(campaign=campaign).order_by('-sent_at')[:50],
            'logs_count': NewsletterLog.objects.filter(campaign=campaign).count(),
            'sent_logs': NewsletterLog.objects.filter(campaign=campaign, status='SENT').count(),
            'failed_logs': NewsletterLog.objects.filter(campaign=campaign, status='FAILED').count(),
            'opened_logs': NewsletterLog.objects.filter(campaign=campaign, opened_at__isnull=False).count(),
            'clicked_logs': NewsletterLog.objects.filter(campaign=campaign, clicked_at__isnull=False).count(),
        })
        return context


@login_required
@user_passes_test(is_admin)
def send_campaign(request, campaign_id):
    """Send a newsletter campaign"""
    campaign = get_object_or_404(NewsletterCampaign, id=campaign_id)
    
    if request.method == 'POST':
        try:
            # Get target subscribers based on campaign criteria
            subscribers = NewsletterSubscriber.objects.filter(is_active=True)
            
            # Apply targeting filters
            if campaign.target_cities:
                subscribers = subscribers.filter(city__in=campaign.target_cities)
            
            if campaign.target_active_users:
                # Get active users and match with subscribers
                active_users = User.objects.filter(is_active=True)
                if campaign.target_user_types:
                    active_users = active_users.filter(user_type__in=campaign.target_user_types)
                if campaign.target_loyalty_levels:
                    active_users = active_users.filter(loyalty_level__in=campaign.target_loyalty_levels)
                
                subscriber_emails = active_users.values_list('email', flat=True)
                subscribers = subscribers.filter(email__in=subscriber_emails)
            
            if campaign.target_new_subscribers:
                # Subscribers who joined in the last 30 days
                thirty_days_ago = timezone.now() - timedelta(days=30)
                subscribers = subscribers.filter(subscribed_at__gte=thirty_days_ago)
            
            # Update campaign status
            campaign.status = 'SENDING'
            campaign.total_recipients = subscribers.count()
            campaign.save()
            
            # Send emails
            sent_count = 0
            for subscriber in subscribers:
                try:
                    # Create log entry
                    log = NewsletterLog.objects.create(
                        campaign=campaign,
                        subscriber=subscriber,
                        status='PENDING'
                    )
                    
                    # Send email
                    subject = campaign.subject
                    text_content = campaign.content
                    html_content = campaign.html_content or campaign.content
                    
                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body=text_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[subscriber.email]
                    )
                    msg.attach_alternative(html_content, "text/html")
                    msg.send()
                    
                    # Update log
                    log.status = 'SENT'
                    log.sent_at = timezone.now()
                    log.save()
                    
                    # Update subscriber stats
                    subscriber.email_count += 1
                    subscriber.last_email_sent = timezone.now()
                    subscriber.save()
                    
                    sent_count += 1
                    
                except Exception as e:
                    # Log error
                    log.status = 'FAILED'
                    log.error_message = str(e)
                    log.save()
            
            # Update campaign
            campaign.status = 'SENT'
            campaign.sent_at = timezone.now()
            campaign.sent_count = sent_count
            campaign.save()
            
            messages.success(request, f'Campagne envoyée avec succès à {sent_count} abonnés!')
            
        except Exception as e:
            campaign.status = 'FAILED'
            campaign.save()
            messages.error(request, f'Erreur lors de l\'envoi: {str(e)}')
    
    return redirect('backend:newsletter_campaign_detail', campaign_id=campaign.id)


@login_required
@user_passes_test(is_admin)
def schedule_campaign(request, campaign_id):
    """Schedule a campaign for later sending"""
    campaign = get_object_or_404(NewsletterCampaign, id=campaign_id)
    
    if request.method == 'POST':
        scheduled_at = request.POST.get('scheduled_at')
        if scheduled_at:
            try:
                scheduled_datetime = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
                campaign.scheduled_at = scheduled_datetime
                campaign.status = 'SCHEDULED'
                campaign.save()
                messages.success(request, f'Campagne programmée pour le {scheduled_datetime.strftime("%d/%m/%Y à %H:%M")}')
            except ValueError:
                messages.error(request, 'Format de date invalide')
        else:
            messages.error(request, 'Date de programmation requise')
    
    return redirect('backend:newsletter_campaign_detail', campaign_id=campaign.id)


class NewsletterSubscriberListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all newsletter subscribers"""
    model = NewsletterSubscriber
    template_name = 'backend/admin/newsletter/subscribers/list.html'
    context_object_name = 'subscribers'
    paginate_by = 50
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_queryset(self):
        queryset = NewsletterSubscriber.objects.all().order_by('-subscribed_at')
        
        # Filter by status
        is_active = self.request.GET.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')
        
        # Filter by city
        city = self.request.GET.get('city')
        if city:
            queryset = queryset.filter(city=city)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) | 
                Q(name__icontains=search) |
                Q(phone__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'cities': User.CITIES,
            'total_subscribers': NewsletterSubscriber.objects.count(),
            'active_subscribers': NewsletterSubscriber.objects.filter(is_active=True).count(),
            'inactive_subscribers': NewsletterSubscriber.objects.filter(is_active=False).count(),
            'subscribers_by_city': NewsletterSubscriber.objects.values('city').annotate(count=Count('id')).order_by('-count'),
        })
        return context


@login_required
@user_passes_test(is_admin)
def export_subscribers(request):
    """Export subscribers to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="subscribers.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Email', 'Nom', 'Téléphone', 'Ville', 'Actif', 'Date d\'inscription', 'Dernier email', 'Nombre d\'emails'])
    
    subscribers = NewsletterSubscriber.objects.all().order_by('-subscribed_at')
    for subscriber in subscribers:
        writer.writerow([
            subscriber.email,
            subscriber.name,
            subscriber.phone,
            subscriber.city,
            'Oui' if subscriber.is_active else 'Non',
            subscriber.subscribed_at.strftime('%d/%m/%Y %H:%M'),
            subscriber.last_email_sent.strftime('%d/%m/%Y %H:%M') if subscriber.last_email_sent else '',
            subscriber.email_count
        ])
    
    return response


class NewsletterTemplateListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all newsletter templates"""
    model = NewsletterTemplate
    template_name = 'backend/admin/newsletter/templates/list.html'
    context_object_name = 'templates'
    paginate_by = 20
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_queryset(self):
        queryset = NewsletterTemplate.objects.all().order_by('name')
        
        # Filter by type
        template_type = self.request.GET.get('type')
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        
        # Filter by status
        is_active = self.request.GET.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'template_types': NewsletterTemplate.TEMPLATE_TYPES,
            'total_templates': NewsletterTemplate.objects.count(),
            'active_templates': NewsletterTemplate.objects.filter(is_active=True).count(),
        })
        return context


class NewsletterTemplateCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new newsletter template"""
    model = NewsletterTemplate
    template_name = 'backend/admin/newsletter/templates/create.html'
    fields = ['name', 'template_type', 'subject_template', 'content_template', 'html_template', 'variables', 'is_active']
    success_url = reverse_lazy('backend:newsletter_templates')
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Template créé avec succès!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'template_types': NewsletterTemplate.TEMPLATE_TYPES,
        })
        return context


class ScheduledNewsletterListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all scheduled newsletters"""
    model = ScheduledNewsletter
    template_name = 'backend/admin/newsletter/scheduled/list.html'
    context_object_name = 'scheduled_newsletters'
    paginate_by = 20
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_queryset(self):
        queryset = ScheduledNewsletter.objects.all().order_by('next_send_date')
        
        # Filter by status
        is_active = self.request.GET.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')
        
        # Filter by frequency
        frequency = self.request.GET.get('frequency')
        if frequency:
            queryset = queryset.filter(frequency=frequency)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'frequencies': ScheduledNewsletter.FREQUENCY_CHOICES,
            'total_scheduled': ScheduledNewsletter.objects.count(),
            'active_scheduled': ScheduledNewsletter.objects.filter(is_active=True).count(),
        })
        return context


@login_required
@user_passes_test(is_admin)
def newsletter_analytics(request):
    """Newsletter analytics and reporting"""
    # Date range
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Campaign statistics
    campaigns = NewsletterCampaign.objects.filter(created_at__gte=start_date)
    
    # Subscriber statistics
    new_subscribers = NewsletterSubscriber.objects.filter(subscribed_at__gte=start_date)
    unsubscribed = NewsletterSubscriber.objects.filter(unsubscribed_at__gte=start_date)
    
    # Email statistics
    logs = NewsletterLog.objects.filter(sent_at__gte=start_date)
    
    context = {
        'days': days,
        'start_date': start_date,
        
        # Campaign stats
        'total_campaigns': campaigns.count(),
        'sent_campaigns': campaigns.filter(status='SENT').count(),
        'scheduled_campaigns': campaigns.filter(status='SCHEDULED').count(),
        'draft_campaigns': campaigns.filter(status='DRAFT').count(),
        
        # Subscriber stats
        'new_subscribers': new_subscribers.count(),
        'unsubscribed': unsubscribed.count(),
        'total_subscribers': NewsletterSubscriber.objects.filter(is_active=True).count(),
        
        # Email stats
        'total_emails_sent': logs.filter(status='SENT').count(),
        'failed_emails': logs.filter(status='FAILED').count(),
        'opened_emails': logs.filter(opened_at__isnull=False).count(),
        'clicked_emails': logs.filter(clicked_at__isnull=False).count(),
        
        # Charts data
        'campaigns_by_type': campaigns.values('campaign_type').annotate(count=Count('id')),
        'subscribers_by_city': NewsletterSubscriber.objects.values('city').annotate(count=Count('id')).order_by('-count')[:10],
        'daily_subscribers': new_subscribers.extra(select={'day': 'date(subscribed_at)'}).values('day').annotate(count=Count('id')).order_by('day'),
    }
    
    return render(request, 'backend/admin/newsletter/analytics.html', context)


@csrf_exempt
@login_required
@user_passes_test(is_admin)
def newsletter_webhook(request):
    """Webhook for email tracking (opened, clicked)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            log_id = data.get('log_id')
            event_type = data.get('event_type')  # 'opened' or 'clicked'
            
            log = NewsletterLog.objects.get(id=log_id)
            
            if event_type == 'opened':
                log.opened_at = timezone.now()
                log.campaign.opened_count += 1
                log.campaign.save()
            elif event_type == 'clicked':
                log.clicked_at = timezone.now()
                log.campaign.clicked_count += 1
                log.campaign.save()
            
            log.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}) 