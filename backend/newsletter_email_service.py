"""
Enhanced Newsletter Email Service using Yagmail
Optimized for handling millions of subscribers with advanced features
"""

import yagmail
import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import datetime, timedelta
import threading
import queue
import time
from typing import List, Dict, Any, Optional
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .models_newsletter import (
    NewsletterSubscriber, NewsletterCampaign, NewsletterLog, 
    NewsletterTemplate, ScheduledNewsletter
)

logger = logging.getLogger(__name__)


class NewsletterEmailService:
    """
    High-performance newsletter email service optimized for millions of subscribers
    """
    
    def __init__(self):
        self.yag = None
        self.email_queue = queue.Queue()
        self.max_workers = 10
        self.batch_size = 100
        self.rate_limit_per_minute = 1000
        self.last_send_time = 0
        self._setup_yagmail()
        self._start_worker_threads()
    
    def _setup_yagmail(self):
        """Setup yagmail with environment credentials"""
        try:
            email_user = getattr(settings, 'EMAIL_HOST_USER', None)
            email_password = getattr(settings, 'EMAIL_HOST_PASSWORD', None)
            
            if not email_user or not email_password:
                logger.error("Email credentials not configured in environment")
                return
            
            self.yag = yagmail.SMTP(
                user=email_user,
                password=email_password,
                host=getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com'),
                port=getattr(settings, 'EMAIL_PORT', 587),
                smtp_starttls=True,
                smtp_ssl=False
            )
            logger.info("Yagmail configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup yagmail: {str(e)}")
            self.yag = None
    
    def _start_worker_threads(self):
        """Start background worker threads for email processing"""
        self.workers = []
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._email_worker, daemon=True)
            worker.start()
            self.workers.append(worker)
        logger.info(f"Started {self.max_workers} email worker threads")
    
    def _email_worker(self):
        """Background worker for processing email queue"""
        while True:
            try:
                email_task = self.email_queue.get(timeout=1)
                if email_task is None:
                    break
                
                self._send_single_email(email_task)
                self.email_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Email worker error: {str(e)}")
    
    def _send_single_email(self, email_task: Dict[str, Any]):
        """Send a single email with error handling"""
        try:
            subscriber = email_task['subscriber']
            campaign = email_task['campaign']
            subject = email_task['subject']
            html_content = email_task['html_content']
            text_content = email_task['text_content']
            
            # Create log entry
            log = NewsletterLog.objects.create(
                campaign=campaign,
                subscriber=subscriber,
                status='PENDING'
            )
            
            # Rate limiting
            self._rate_limit()
            
            # Send email using yagmail
            if self.yag:
                self.yag.send(
                    to=subscriber.email,
                    subject=subject,
                    contents=[html_content],
                    headers={'List-Unsubscribe': f'<mailto:{settings.DEFAULT_FROM_EMAIL}?subject=unsubscribe>'})
            else:
                # Fallback to Django email backend
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
            
            logger.info(f"Email sent successfully to {subscriber.email}")
            
        except Exception as e:
            logger.error(f"Failed to send email to {subscriber.email}: {str(e)}")
            if 'log' in locals():
                log.status = 'FAILED'
                log.error_message = str(e)
                log.save()
    
    def _rate_limit(self):
        """Implement rate limiting to avoid being blocked"""
        current_time = time.time()
        time_since_last = current_time - self.last_send_time
        min_interval = 60.0 / self.rate_limit_per_minute
        
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        self.last_send_time = time.time()
    
    def send_campaign(self, campaign: NewsletterCampaign, subscribers: List[NewsletterSubscriber] = None):
        """
        Send a newsletter campaign to subscribers
        Optimized for large subscriber lists
        """
        try:
            if not subscribers:
                subscribers = self._get_target_subscribers(campaign)
            
            if not subscribers:
                logger.warning(f"No subscribers found for campaign {campaign.name}")
                return
            
            logger.info(f"Starting campaign {campaign.name} to {len(subscribers)} subscribers")
            
            # Update campaign status
            campaign.status = 'SENDING'
            campaign.total_recipients = len(subscribers)
            campaign.save()
            
            # Prepare email content
            subject = campaign.subject
            html_content = campaign.html_content or campaign.content
            text_content = campaign.content
            
            # Queue emails for background processing
            sent_count = 0
            for subscriber in subscribers:
                email_task = {
                    'subscriber': subscriber,
                    'campaign': campaign,
                    'subject': subject,
                    'html_content': html_content,
                    'text_content': text_content
                }
                self.email_queue.put(email_task)
                sent_count += 1
            
            # Wait for all emails to be processed
            self.email_queue.join()
            
            # Update campaign
            campaign.status = 'SENT'
            campaign.sent_at = timezone.now()
            campaign.sent_count = sent_count
            campaign.save()
            
            logger.info(f"Campaign {campaign.name} completed. Sent {sent_count} emails.")
            
        except Exception as e:
            logger.error(f"Campaign {campaign.name} failed: {str(e)}")
            campaign.status = 'FAILED'
            campaign.save()
    
    def _get_target_subscribers(self, campaign: NewsletterCampaign) -> List[NewsletterSubscriber]:
        """Get targeted subscribers based on campaign criteria"""
        queryset = NewsletterSubscriber.objects.filter(is_active=True)
        
        # Apply targeting filters
        if campaign.target_cities:
            queryset = queryset.filter(city__in=campaign.target_cities)
        
        if campaign.target_active_users:
            # Filter for active users (custom logic based on your user model)
            pass
        
        if campaign.target_new_subscribers:
            # Filter for new subscribers (e.g., subscribed in last 30 days)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            queryset = queryset.filter(subscribed_at__gte=thirty_days_ago)
        
        return list(queryset)
    
    def send_template_email(self, template: NewsletterTemplate, subscribers: List[NewsletterSubscriber], 
                          variables: Dict[str, Any] = None):
        """Send email using a template with variable substitution"""
        try:
            if not variables:
                variables = {}
            
            # Render template with variables
            subject = template.subject_template.format(**variables)
            content = template.content_template.format(**variables)
            html_content = template.html_template.format(**variables) if template.html_template else content
            
            # Create temporary campaign for tracking
            campaign = NewsletterCampaign.objects.create(
                name=f"Template: {template.name}",
                subject=subject,
                content=content,
                html_content=html_content,
                campaign_type='CUSTOM',
                status='DRAFT'
            )
            
            # Send campaign
            self.send_campaign(campaign, subscribers)
            
        except Exception as e:
            logger.error(f"Template email failed: {str(e)}")
    
    def send_scheduled_newsletters(self):
        """Process and send scheduled newsletters"""
        try:
            now = timezone.now()
            scheduled_newsletters = ScheduledNewsletter.objects.filter(
                is_active=True,
                next_send_date__lte=now
            )
            
            for scheduled in scheduled_newsletters:
                try:
                    # Get subscribers
                    subscribers = NewsletterSubscriber.objects.filter(is_active=True)
                    
                    # Send template email
                    self.send_template_email(scheduled.template, list(subscribers))
                    
                    # Update next send date
                    scheduled.last_sent_date = now
                    scheduled.next_send_date = self._calculate_next_send_date(scheduled)
                    scheduled.save()
                    
                    logger.info(f"Scheduled newsletter {scheduled.name} sent successfully")
                    
                except Exception as e:
                    logger.error(f"Scheduled newsletter {scheduled.name} failed: {str(e)}")
        
        except Exception as e:
            logger.error(f"Scheduled newsletters processing failed: {str(e)}")
    
    def _calculate_next_send_date(self, scheduled: ScheduledNewsletter) -> datetime:
        """Calculate next send date based on frequency"""
        now = timezone.now()
        
        if scheduled.frequency == 'DAILY':
            return now + timedelta(days=1)
        elif scheduled.frequency == 'WEEKLY':
            return now + timedelta(weeks=1)
        elif scheduled.frequency == 'MONTHLY':
            return now + timedelta(days=30)
        else:
            return now + timedelta(weeks=1)
    
    def get_campaign_stats(self, campaign: NewsletterCampaign) -> Dict[str, Any]:
        """Get comprehensive campaign statistics"""
        logs = NewsletterLog.objects.filter(campaign=campaign)
        
        stats = {
            'total_recipients': campaign.total_recipients,
            'sent_count': logs.filter(status='SENT').count(),
            'failed_count': logs.filter(status='FAILED').count(),
            'opened_count': logs.filter(status='OPENED').count(),
            'clicked_count': logs.filter(status='CLICKED').count(),
            'unsubscribed_count': logs.filter(status='UNSUBSCRIBED').count(),
            'open_rate': 0,
            'click_rate': 0,
            'failure_rate': 0
        }
        
        if stats['sent_count'] > 0:
            stats['open_rate'] = (stats['opened_count'] / stats['sent_count']) * 100
            stats['click_rate'] = (stats['clicked_count'] / stats['sent_count']) * 100
            stats['failure_rate'] = (stats['failed_count'] / stats['sent_count']) * 100
        
        return stats
    
    def export_subscribers_to_excel(self, subscribers: List[NewsletterSubscriber], filename: str = None):
        """Export subscribers to Excel file"""
        try:
            import pandas as pd
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill
            
            if not filename:
                filename = f"newsletter_subscribers_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            # Prepare data
            data = []
            for subscriber in subscribers:
                data.append({
                    'Email': subscriber.email,
                    'Name': subscriber.name or '',
                    'Phone': subscriber.phone or '',
                    'City': subscriber.city or '',
                    'Active': 'Yes' if subscriber.is_active else 'No',
                    'Subscribed Date': subscriber.subscribed_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'Last Email Sent': subscriber.last_email_sent.strftime('%Y-%m-%d %H:%M:%S') if subscriber.last_email_sent else '',
                    'Email Count': subscriber.email_count,
                    'Preferences': json.dumps(subscriber.preferences) if subscriber.preferences else ''
                })
            
            # Create DataFrame and export
            df = pd.DataFrame(data)
            df.to_excel(filename, index=False, engine='openpyxl')
            
            logger.info(f"Subscribers exported to {filename}")
            return filename
            
        except ImportError:
            logger.error("pandas or openpyxl not installed for Excel export")
            return None
        except Exception as e:
            logger.error(f"Excel export failed: {str(e)}")
            return None
    
    def cleanup_old_logs(self, days: int = 90):
        """Clean up old newsletter logs to maintain performance"""
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            deleted_count = NewsletterLog.objects.filter(sent_at__lt=cutoff_date).delete()[0]
            logger.info(f"Cleaned up {deleted_count} old newsletter logs")
        except Exception as e:
            logger.error(f"Log cleanup failed: {str(e)}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall newsletter system statistics"""
        try:
            total_subscribers = NewsletterSubscriber.objects.count()
            active_subscribers = NewsletterSubscriber.objects.filter(is_active=True).count()
            total_campaigns = NewsletterCampaign.objects.count()
            sent_campaigns = NewsletterCampaign.objects.filter(status='SENT').count()
            
            # Recent activity
            last_24h = timezone.now() - timedelta(hours=24)
            recent_subscribers = NewsletterSubscriber.objects.filter(subscribed_at__gte=last_24h).count()
            recent_emails = NewsletterLog.objects.filter(sent_at__gte=last_24h).count()
            
            return {
                'total_subscribers': total_subscribers,
                'active_subscribers': active_subscribers,
                'total_campaigns': total_campaigns,
                'sent_campaigns': sent_campaigns,
                'recent_subscribers_24h': recent_subscribers,
                'recent_emails_24h': recent_emails,
                'system_status': 'healthy' if self.yag else 'email_service_disabled'
            }
        except Exception as e:
            logger.error(f"Failed to get system stats: {str(e)}")
            return {}


# Global instance
newsletter_email_service = NewsletterEmailService() 