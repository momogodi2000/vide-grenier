"""
Management command to send scheduled newsletters
Run with: python manage.py send_scheduled_newsletters
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from datetime import datetime, timedelta
import logging

from backend.models_newsletter import ScheduledNewsletter, NewsletterCampaign, NewsletterSubscriber, NewsletterLog

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send scheduled newsletters'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force send even if not due',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS('Starting scheduled newsletter processing...')
        )
        
        # Get scheduled newsletters that are due
        now = timezone.now()
        if force:
            scheduled_newsletters = ScheduledNewsletter.objects.filter(is_active=True)
        else:
            scheduled_newsletters = ScheduledNewsletter.objects.filter(
                is_active=True,
                next_send_date__lte=now
            )
        
        if not scheduled_newsletters.exists():
            self.stdout.write(
                self.style.WARNING('No scheduled newsletters due for sending.')
            )
            return
        
        self.stdout.write(f'Found {scheduled_newsletters.count()} scheduled newsletters to process.')
        
        for scheduled in scheduled_newsletters:
            self.process_scheduled_newsletter(scheduled, dry_run)
        
        self.stdout.write(
            self.style.SUCCESS('Scheduled newsletter processing completed.')
        )

    def process_scheduled_newsletter(self, scheduled, dry_run=False):
        """Process a single scheduled newsletter"""
        self.stdout.write(f'Processing: {scheduled.name}')
        
        try:
            # Create campaign from template
            campaign = NewsletterCampaign.objects.create(
                name=f"Scheduled: {scheduled.name}",
                subject=scheduled.template.subject_template,
                content=scheduled.template.content_template,
                html_content=scheduled.template.html_template,
                campaign_type='NEWSLETTER',
                status='DRAFT',
                created_by=scheduled.created_by
            )
            
            # Get subscribers
            subscribers = NewsletterSubscriber.objects.filter(is_active=True)
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'[DRY RUN] Would send to {subscribers.count()} subscribers'
                    )
                )
                return
            
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
                    subject = scheduled.template.subject_template
                    text_content = scheduled.template.content_template
                    html_content = scheduled.template.html_template or scheduled.template.content_template
                    
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
                    logger.error(f'Failed to send email to {subscriber.email}: {str(e)}')
                    log.status = 'FAILED'
                    log.error_message = str(e)
                    log.save()
            
            # Update campaign
            campaign.status = 'SENT'
            campaign.sent_at = timezone.now()
            campaign.sent_count = sent_count
            campaign.total_recipients = subscribers.count()
            campaign.save()
            
            # Update scheduled newsletter
            scheduled.last_sent_date = timezone.now()
            scheduled.next_send_date = self.calculate_next_send_date(scheduled)
            scheduled.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully sent {sent_count} emails for "{scheduled.name}"'
                )
            )
            
        except Exception as e:
            logger.error(f'Failed to process scheduled newsletter {scheduled.name}: {str(e)}')
            self.stdout.write(
                self.style.ERROR(f'Failed to process {scheduled.name}: {str(e)}')
            )

    def calculate_next_send_date(self, scheduled):
        """Calculate the next send date based on frequency"""
        now = timezone.now()
        
        if scheduled.frequency == 'DAILY':
            return now + timedelta(days=1)
        elif scheduled.frequency == 'WEEKLY':
            return now + timedelta(weeks=1)
        elif scheduled.frequency == 'MONTHLY':
            # Simple monthly calculation (30 days)
            return now + timedelta(days=30)
        else:
            # CUSTOM frequency - use a default of weekly
            return now + timedelta(weeks=1) 