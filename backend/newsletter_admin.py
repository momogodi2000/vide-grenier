"""
Enhanced Newsletter Admin Views
Comprehensive admin interface for managing newsletter campaigns, subscribers, and analytics
Optimized for handling millions of subscribers
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.core.serializers import serialize
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
import io

from .models_newsletter import (
    NewsletterSubscriber, NewsletterCampaign, NewsletterTemplate,
    NewsletterLog, ScheduledNewsletter
)
from .newsletter_email_service import newsletter_email_service

logger = logging.getLogger(__name__)


def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(is_admin)
def newsletter_dashboard(request):
    """Main newsletter dashboard with comprehensive statistics"""
    try:
        # Get system statistics
        stats = newsletter_email_service.get_system_stats()
        
        # Get recent campaigns
        recent_campaigns = NewsletterCampaign.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).order_by('-created_at')[:5]
        
        # Get recent subscribers
        recent_subscribers = NewsletterSubscriber.objects.filter(
            subscribed_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-subscribed_at')[:10]
        
        # Get top performing campaigns
        top_campaigns = NewsletterCampaign.objects.filter(
            status='SENT'
        ).annotate(
            open_rate=Count('logs', filter=Q(logs__status='OPENED')) * 100.0 / Count('logs')
        ).order_by('-open_rate')[:5]
        
        # Get subscriber growth data
        growth_data = []
        for i in range(30):
            date = timezone.now() - timedelta(days=i)
            count = NewsletterSubscriber.objects.filter(
                subscribed_at__date=date.date()
            ).count()
            growth_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'subscribers': count
            })
        growth_data.reverse()
        
        context = {
            'stats': stats,
            'recent_campaigns': recent_campaigns,
            'recent_subscribers': recent_subscribers,
            'top_campaigns': top_campaigns,
            'growth_data': json.dumps(growth_data),
            'page_title': 'Newsletter Dashboard'
        }
        
        return render(request, 'backend/admin/newsletter/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Newsletter dashboard error: {str(e)}")
        messages.error(request, 'Erreur lors du chargement du tableau de bord')
        return redirect('admin_panel:newsletter_campaigns')


class NewsletterCampaignListView:
    """List view for newsletter campaigns with advanced filtering"""
    
    @staticmethod
    @login_required
    @user_passes_test(is_admin)
    def as_view(request):
        try:
            # Get filter parameters
            status_filter = request.GET.get('status', '')
            campaign_type = request.GET.get('type', '')
            search = request.GET.get('search', '')
            
            # Build queryset
            campaigns = NewsletterCampaign.objects.all()
            
            if status_filter:
                campaigns = campaigns.filter(status=status_filter)
            
            if campaign_type:
                campaigns = campaigns.filter(campaign_type=campaign_type)
            
            if search:
                campaigns = campaigns.filter(
                    Q(name__icontains=search) |
                    Q(subject__icontains=search) |
                    Q(content__icontains=search)
                )
            
            # Order by creation date
            campaigns = campaigns.order_by('-created_at')
            
            # Pagination
            paginator = Paginator(campaigns, 20)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            
            context = {
                'campaigns': page_obj,
                'status_choices': NewsletterCampaign.STATUS_CHOICES,
                'campaign_types': NewsletterCampaign.CAMPAIGN_TYPES,
                'page_title': 'Campagnes Newsletter'
            }
            
            return render(request, 'backend/admin/newsletter/campaigns/list.html', context)
            
        except Exception as e:
            logger.error(f"Campaign list error: {str(e)}")
            messages.error(request, 'Erreur lors du chargement des campagnes')
            return redirect('admin_panel:newsletter_dashboard')


class NewsletterCampaignCreateView:
    """Create new newsletter campaign"""
    
    @staticmethod
    @login_required
    @user_passes_test(is_admin)
    def as_view(request):
        if request.method == 'POST':
            try:
                # Get form data
                name = request.POST.get('name', '').strip()
                subject = request.POST.get('subject', '').strip()
                content = request.POST.get('content', '').strip()
                html_content = request.POST.get('html_content', '').strip()
                campaign_type = request.POST.get('campaign_type', 'NEWSLETTER')
                
                # Targeting options
                target_cities = request.POST.getlist('target_cities')
                target_user_types = request.POST.getlist('target_user_types')
                target_loyalty_levels = request.POST.getlist('target_loyalty_levels')
                target_active_users = request.POST.get('target_active_users') == 'on'
                target_new_subscribers = request.POST.get('target_new_subscribers') == 'on'
                
                # Validation
                if not name or not subject or not content:
                    messages.error(request, 'Tous les champs obligatoires doivent être remplis')
                    return render(request, 'backend/admin/newsletter/campaigns/create.html')
                
                # Create campaign
                campaign = NewsletterCampaign.objects.create(
                    name=name,
                    subject=subject,
                    content=content,
                    html_content=html_content,
                    campaign_type=campaign_type,
                    target_cities=target_cities,
                    target_user_types=target_user_types,
                    target_loyalty_levels=target_loyalty_levels,
                    target_active_users=target_active_users,
                    target_new_subscribers=target_new_subscribers,
                    created_by=request.user
                )
                
                messages.success(request, f'Campagne "{name}" créée avec succès')
                return redirect('admin_panel:newsletter_campaign_detail', pk=campaign.id)
                
            except Exception as e:
                logger.error(f"Campaign creation error: {str(e)}")
                messages.error(request, 'Erreur lors de la création de la campagne')
        
        # GET request - show form
        context = {
            'campaign_types': NewsletterCampaign.CAMPAIGN_TYPES,
            'cities': NewsletterSubscriber.objects.values_list('city', flat=True).distinct(),
            'page_title': 'Créer une Campagne'
        }
        
        return render(request, 'backend/admin/newsletter/campaigns/create.html', context)


class NewsletterCampaignDetailView:
    """Detail view for newsletter campaign with statistics"""
    
    @staticmethod
    @login_required
    @user_passes_test(is_admin)
    def as_view(request, pk):
        try:
            campaign = get_object_or_404(NewsletterCampaign, pk=pk)
            
            # Get campaign statistics
            stats = newsletter_email_service.get_campaign_stats(campaign)
            
            # Get recent logs
            recent_logs = NewsletterLog.objects.filter(
                campaign=campaign
            ).select_related('subscriber').order_by('-sent_at')[:20]
            
            context = {
                'campaign': campaign,
                'stats': stats,
                'recent_logs': recent_logs,
                'page_title': f'Campagne: {campaign.name}'
            }
            
            return render(request, 'backend/admin/newsletter/campaigns/detail.html', context)
            
        except Exception as e:
            logger.error(f"Campaign detail error: {str(e)}")
            messages.error(request, 'Erreur lors du chargement de la campagne')
            return redirect('admin_panel:newsletter_campaigns')


class NewsletterCampaignUpdateView:
    """Update newsletter campaign"""
    
    @staticmethod
    @login_required
    @user_passes_test(is_admin)
    def as_view(request, pk):
        try:
            campaign = get_object_or_404(NewsletterCampaign, pk=pk)
            
            if request.method == 'POST':
                # Update campaign data
                campaign.name = request.POST.get('name', '').strip()
                campaign.subject = request.POST.get('subject', '').strip()
                campaign.content = request.POST.get('content', '').strip()
                campaign.html_content = request.POST.get('html_content', '').strip()
                campaign.campaign_type = request.POST.get('campaign_type', 'NEWSLETTER')
                
                # Update targeting
                campaign.target_cities = request.POST.getlist('target_cities')
                campaign.target_user_types = request.POST.getlist('target_user_types')
                campaign.target_loyalty_levels = request.POST.getlist('target_loyalty_levels')
                campaign.target_active_users = request.POST.get('target_active_users') == 'on'
                campaign.target_new_subscribers = request.POST.get('target_new_subscribers') == 'on'
                
                campaign.save()
                
                messages.success(request, f'Campagne "{campaign.name}" mise à jour avec succès')
                return redirect('admin_panel:newsletter_campaign_detail', pk=campaign.id)
            
            # GET request - show form
            context = {
                'campaign': campaign,
                'campaign_types': NewsletterCampaign.CAMPAIGN_TYPES,
                'cities': NewsletterSubscriber.objects.values_list('city', flat=True).distinct(),
                'page_title': f'Modifier: {campaign.name}'
            }
            
            return render(request, 'backend/admin/newsletter/campaigns/edit.html', context)
            
        except Exception as e:
            logger.error(f"Campaign update error: {str(e)}")
            messages.error(request, 'Erreur lors de la mise à jour de la campagne')
            return redirect('admin_panel:newsletter_campaigns')


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def send_campaign(request, campaign_id):
    """Send a newsletter campaign"""
    try:
        campaign = get_object_or_404(NewsletterCampaign, pk=campaign_id)
        
        if campaign.status != 'DRAFT':
            messages.error(request, 'Seules les campagnes en brouillon peuvent être envoyées')
            return redirect('admin_panel:newsletter_campaign_detail', pk=campaign.id)
        
        # Get target subscribers
        subscribers = newsletter_email_service._get_target_subscribers(campaign)
        
        if not subscribers:
            messages.warning(request, 'Aucun abonné trouvé pour cette campagne')
            return redirect('admin_panel:newsletter_campaign_detail', pk=campaign.id)
        
        # Send campaign in background
        import threading
        thread = threading.Thread(
            target=newsletter_email_service.send_campaign,
            args=(campaign, subscribers)
        )
        thread.start()
        
        messages.success(request, f'Campagne "{campaign.name}" en cours d\'envoi à {len(subscribers)} abonnés')
        return redirect('admin_panel:newsletter_campaign_detail', pk=campaign.id)
        
    except Exception as e:
        logger.error(f"Campaign send error: {str(e)}")
        messages.error(request, 'Erreur lors de l\'envoi de la campagne')
        return redirect('admin_panel:newsletter_campaigns')


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def schedule_campaign(request, campaign_id):
    """Schedule a newsletter campaign"""
    try:
        campaign = get_object_or_404(NewsletterCampaign, pk=campaign_id)
        
        scheduled_at = request.POST.get('scheduled_at')
        if not scheduled_at:
            messages.error(request, 'Date de programmation requise')
            return redirect('admin_panel:newsletter_campaign_detail', pk=campaign.id)
        
        # Parse scheduled date
        scheduled_datetime = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
        
        campaign.scheduled_at = scheduled_datetime
        campaign.status = 'SCHEDULED'
        campaign.save()
        
        messages.success(request, f'Campagne "{campaign.name}" programmée pour le {scheduled_datetime.strftime("%d/%m/%Y à %H:%M")}')
        return redirect('admin_panel:newsletter_campaign_detail', pk=campaign.id)
        
    except Exception as e:
        logger.error(f"Campaign schedule error: {str(e)}")
        messages.error(request, 'Erreur lors de la programmation de la campagne')
        return redirect('admin_panel:newsletter_campaigns')


class NewsletterSubscriberListView:
    """List view for newsletter subscribers with advanced filtering and export"""
    
    @staticmethod
    @login_required
    @user_passes_test(is_admin)
    def as_view(request):
        try:
            # Get filter parameters
            city_filter = request.GET.get('city', '')
            status_filter = request.GET.get('status', '')
            search = request.GET.get('search', '')
            export = request.GET.get('export', '')
            
            # Build queryset
            subscribers = NewsletterSubscriber.objects.all()
            
            if city_filter:
                subscribers = subscribers.filter(city=city_filter)
            
            if status_filter == 'active':
                subscribers = subscribers.filter(is_active=True)
            elif status_filter == 'inactive':
                subscribers = subscribers.filter(is_active=False)
            
            if search:
                subscribers = subscribers.filter(
                    Q(email__icontains=search) |
                    Q(name__icontains=search) |
                    Q(phone__icontains=search)
                )
            
            # Order by subscription date
            subscribers = subscribers.order_by('-subscribed_at')
            
            # Export functionality
            if export == 'excel':
                return export_subscribers_to_excel(subscribers)
            
            # Pagination
            paginator = Paginator(subscribers, 50)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            
            # Get statistics
            total_subscribers = NewsletterSubscriber.objects.count()
            active_subscribers = NewsletterSubscriber.objects.filter(is_active=True).count()
            cities = NewsletterSubscriber.objects.values_list('city', flat=True).distinct()
            
            context = {
                'subscribers': page_obj,
                'total_subscribers': total_subscribers,
                'active_subscribers': active_subscribers,
                'cities': cities,
                'page_title': 'Abonnés Newsletter'
            }
            
            return render(request, 'backend/admin/newsletter/subscribers/list.html', context)
            
        except Exception as e:
            logger.error(f"Subscriber list error: {str(e)}")
            messages.error(request, 'Erreur lors du chargement des abonnés')
            return redirect('admin_panel:newsletter_dashboard')


@login_required
@user_passes_test(is_admin)
def export_subscribers_to_excel(request):
    """Export subscribers to Excel file"""
    try:
        # Get filter parameters
        city_filter = request.GET.get('city', '')
        status_filter = request.GET.get('status', '')
        search = request.GET.get('search', '')
        
        # Build queryset
        subscribers = NewsletterSubscriber.objects.all()
        
        if city_filter:
            subscribers = subscribers.filter(city=city_filter)
        
        if status_filter == 'active':
            subscribers = subscribers.filter(is_active=True)
        elif status_filter == 'inactive':
            subscribers = subscribers.filter(is_active=False)
        
        if search:
            subscribers = subscribers.filter(
                Q(email__icontains=search) |
                Q(name__icontains=search) |
                Q(phone__icontains=search)
            )
        
        # Export to Excel
        filename = newsletter_email_service.export_subscribers_to_excel(
            list(subscribers),
            f"newsletter_subscribers_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        
        if filename:
            # Read file and return as response
            with open(filename, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
        else:
            messages.error(request, 'Erreur lors de l\'export Excel')
            return redirect('admin_panel:newsletter_subscribers')
            
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        messages.error(request, 'Erreur lors de l\'export')
        return redirect('admin_panel:newsletter_subscribers')


@login_required
@user_passes_test(is_admin)
def import_subscribers(request):
    """Import subscribers from Excel file"""
    if request.method == 'POST':
        try:
            if 'file' not in request.FILES:
                messages.error(request, 'Aucun fichier sélectionné')
                return redirect('admin_panel:newsletter_subscribers_enhanced')
            
            file = request.FILES['file']
            
            # Check file extension
            if not file.name.endswith(('.xlsx', '.xls')):
                messages.error(request, 'Veuillez sélectionner un fichier Excel (.xlsx ou .xls)')
                return redirect('admin_panel:newsletter_subscribers_enhanced')
            
            # Read Excel file
            df = pd.read_excel(file)
            
            # Validate required columns
            required_columns = ['email']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                messages.error(request, f'Colonnes manquantes: {", ".join(missing_columns)}')
                return redirect('admin_panel:newsletter_subscribers_enhanced')
            
            # Process subscribers
            imported_count = 0
            updated_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    email = str(row['email']).strip().lower()
                    if not email or '@' not in email:
                        continue
                    
                    # Check if subscriber exists
                    subscriber, created = NewsletterSubscriber.objects.get_or_create(
                        email=email,
                        defaults={
                            'name': str(row.get('name', '')).strip(),
                            'phone': str(row.get('phone', '')).strip(),
                            'city': str(row.get('city', '')).strip(),
                            'is_active': True,
                            'preferences': {}
                        }
                    )
                    
                    if created:
                        imported_count += 1
                    else:
                        # Update existing subscriber
                        if row.get('name'):
                            subscriber.name = str(row['name']).strip()
                        if row.get('phone'):
                            subscriber.phone = str(row['phone']).strip()
                        if row.get('city'):
                            subscriber.city = str(row['city']).strip()
                        subscriber.is_active = True
                        subscriber.save()
                        updated_count += 1
                        
                except Exception as e:
                    errors.append(f"Ligne {index + 2}: {str(e)}")
            
            # Show results
            if imported_count > 0 or updated_count > 0:
                messages.success(request, f'Import terminé: {imported_count} nouveaux abonnés, {updated_count} mis à jour')
            
            if errors:
                messages.warning(request, f'{len(errors)} erreurs lors de l\'import')
                logger.warning(f"Import errors: {errors}")
            
            return redirect('admin_panel:newsletter_subscribers_enhanced')
            
        except Exception as e:
            logger.error(f"Import error: {str(e)}")
            messages.error(request, f'Erreur lors de l\'import: {str(e)}')
            return redirect('admin_panel:newsletter_subscribers_enhanced')
    
    # GET request - show import form
    context = {
        'page_title': 'Importer des Abonnés'
    }
    return render(request, 'backend/admin/newsletter/subscribers/import.html', context)


class NewsletterTemplateListView:
    """List view for newsletter templates"""
    
    @staticmethod
    @login_required
    @user_passes_test(is_admin)
    def as_view(request):
        try:
            templates = NewsletterTemplate.objects.all().order_by('name')
            
            context = {
                'templates': templates,
                'page_title': 'Templates Newsletter'
            }
            
            return render(request, 'backend/admin/newsletter/templates/list.html', context)
            
        except Exception as e:
            logger.error(f"Template list error: {str(e)}")
            messages.error(request, 'Erreur lors du chargement des templates')
            return redirect('admin_panel:newsletter_dashboard')


class NewsletterTemplateCreateView:
    """Create new newsletter template"""
    
    @staticmethod
    @login_required
    @user_passes_test(is_admin)
    def as_view(request):
        if request.method == 'POST':
            try:
                # Get form data
                name = request.POST.get('name', '').strip()
                template_type = request.POST.get('template_type', 'CUSTOM')
                subject_template = request.POST.get('subject_template', '').strip()
                content_template = request.POST.get('content_template', '').strip()
                html_template = request.POST.get('html_template', '').strip()
                variables = request.POST.get('variables', '{}')
                
                # Validation
                if not name or not subject_template or not content_template:
                    messages.error(request, 'Tous les champs obligatoires doivent être remplis')
                    return render(request, 'backend/admin/newsletter/templates/create.html')
                
                # Create template
                template = NewsletterTemplate.objects.create(
                    name=name,
                    template_type=template_type,
                    subject_template=subject_template,
                    content_template=content_template,
                    html_template=html_template,
                    variables=json.loads(variables),
                    created_by=request.user
                )
                
                messages.success(request, f'Template "{name}" créé avec succès')
                return redirect('admin_panel:newsletter_templates')
                
            except Exception as e:
                logger.error(f"Template creation error: {str(e)}")
                messages.error(request, 'Erreur lors de la création du template')
        
        # GET request - show form
        context = {
            'template_types': NewsletterTemplate.TEMPLATE_TYPES,
            'page_title': 'Créer un Template'
        }
        
        return render(request, 'backend/admin/newsletter/templates/create.html', context)


class ScheduledNewsletterListView:
    """List view for scheduled newsletters"""
    
    @staticmethod
    @login_required
    @user_passes_test(is_admin)
    def as_view(request):
        try:
            scheduled_newsletters = ScheduledNewsletter.objects.all().order_by('next_send_date')
            
            context = {
                'scheduled_newsletters': scheduled_newsletters,
                'page_title': 'Newsletters Programmées'
            }
            
            return render(request, 'backend/admin/newsletter/scheduled/list.html', context)
            
        except Exception as e:
            logger.error(f"Scheduled newsletter list error: {str(e)}")
            messages.error(request, 'Erreur lors du chargement des newsletters programmées')
            return redirect('admin_panel:newsletter_dashboard')


@login_required
@user_passes_test(is_admin)
def newsletter_analytics(request):
    """Comprehensive newsletter analytics"""
    try:
        # Get date range
        days = int(request.GET.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Subscriber growth
        subscriber_growth = []
        for i in range(days):
            date = end_date - timedelta(days=i)
            count = NewsletterSubscriber.objects.filter(
                subscribed_at__date=date.date()
            ).count()
            subscriber_growth.append({
                'date': date.strftime('%Y-%m-%d'),
                'subscribers': count
            })
        subscriber_growth.reverse()
        
        # Campaign performance
        campaigns = NewsletterCampaign.objects.filter(
            created_at__gte=start_date,
            status='SENT'
        ).annotate(
            open_rate=Count('logs', filter=Q(logs__status='OPENED')) * 100.0 / Count('logs'),
            click_rate=Count('logs', filter=Q(logs__status='CLICKED')) * 100.0 / Count('logs')
        ).order_by('-sent_at')
        
        # Top performing campaigns
        top_campaigns = campaigns.order_by('-open_rate')[:10]
        
        # City distribution
        city_distribution = NewsletterSubscriber.objects.filter(
            is_active=True
        ).values('city').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Recent activity
        recent_logs = NewsletterLog.objects.filter(
            sent_at__gte=start_date
        ).select_related('campaign', 'subscriber').order_by('-sent_at')[:20]
        
        context = {
            'subscriber_growth': json.dumps(subscriber_growth),
            'campaigns': campaigns,
            'top_campaigns': top_campaigns,
            'city_distribution': city_distribution,
            'recent_logs': recent_logs,
            'days': days,
            'page_title': 'Analytics Newsletter'
        }
        
        return render(request, 'backend/admin/newsletter/analytics.html', context)
        
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        messages.error(request, 'Erreur lors du chargement des analytics')
        return redirect('admin_panel:newsletter_dashboard')


@csrf_exempt
@require_http_methods(["POST"])
def newsletter_webhook(request):
    """Webhook for email tracking (opens, clicks, etc.)"""
    try:
        data = json.loads(request.body)
        
        # Extract tracking data
        campaign_id = data.get('campaign_id')
        subscriber_email = data.get('subscriber_email')
        event_type = data.get('event_type')  # 'open', 'click', 'unsubscribe'
        
        if not all([campaign_id, subscriber_email, event_type]):
            return JsonResponse({'status': 'error', 'message': 'Missing required fields'})
        
        # Find campaign and subscriber
        try:
            campaign = NewsletterCampaign.objects.get(id=campaign_id)
            subscriber = NewsletterSubscriber.objects.get(email=subscriber_email)
            log = NewsletterLog.objects.get(campaign=campaign, subscriber=subscriber)
        except (NewsletterCampaign.DoesNotExist, NewsletterSubscriber.DoesNotExist, NewsletterLog.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Campaign or subscriber not found'})
        
        # Update log based on event type
        if event_type == 'open':
            log.status = 'OPENED'
            log.opened_at = timezone.now()
            campaign.opened_count += 1
        elif event_type == 'click':
            log.status = 'CLICKED'
            log.clicked_at = timezone.now()
            campaign.clicked_count += 1
        elif event_type == 'unsubscribe':
            log.status = 'UNSUBSCRIBED'
            subscriber.is_active = False
            subscriber.unsubscribed_at = timezone.now()
            subscriber.save()
            campaign.unsubscribed_count += 1
        
        log.save()
        campaign.save()
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
@user_passes_test(is_admin)
def cleanup_old_logs(request):
    """Clean up old newsletter logs for performance"""
    try:
        days = int(request.GET.get('days', 90))
        deleted_count = newsletter_email_service.cleanup_old_logs(days)
        
        messages.success(request, f'{deleted_count} anciens logs supprimés avec succès')
        return redirect('admin_panel:newsletter_dashboard')
        
    except Exception as e:
        logger.error(f"Log cleanup error: {str(e)}")
        messages.error(request, 'Erreur lors du nettoyage des logs')
        return redirect('admin_panel:newsletter_dashboard') 