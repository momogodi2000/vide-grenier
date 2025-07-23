# backend/views_newsletter.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail, send_mass_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from celery import shared_task
import yagmail
import json
from datetime import datetime, timedelta
import threading
import time
from django.core.management.base import BaseCommand

# Newsletter Models (adjust based on your actual models)
# from .models import NewsletterSubscriber, Newsletter, ScheduledNewsletter

class EmailService:
    """Enhanced email service using yagmail"""
    
    def __init__(self):
        self.yag = None
        self.setup_yagmail()
    
    def setup_yagmail(self):
        """Setup yagmail with configuration"""
        try:
            self.yag = yagmail.SMTP(
                user=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                smtp_starttls=settings.EMAIL_USE_TLS,
                smtp_ssl=settings.EMAIL_USE_SSL
            )
        except Exception as e:
            print(f"Error setting up yagmail: {e}")
    
    def send_single_email(self, to_email, subject, html_content, text_content=None):
        """Send single email"""
        try:
            if not self.yag:
                self.setup_yagmail()
            
            contents = [html_content]
            if text_content:
                contents.insert(0, text_content)
            
            self.yag.send(
                to=to_email,
                subject=subject,
                contents=contents
            )
            return True
        except Exception as e:
            print(f"Error sending email to {to_email}: {e}")
            return False
    
    def send_bulk_emails(self, email_list, subject, html_content, text_content=None):
        """Send bulk emails with better performance"""
        successful = 0
        failed = 0
        
        for email_data in email_list:
            if isinstance(email_data, dict):
                to_email = email_data.get('email')
                personalized_content = html_content.format(**email_data)
                personalized_subject = subject.format(**email_data)
            else:
                to_email = email_data
                personalized_content = html_content
                personalized_subject = subject
            
            if self.send_single_email(to_email, personalized_subject, personalized_content, text_content):
                successful += 1
            else:
                failed += 1
            
            # Small delay to avoid overwhelming the SMTP server
            time.sleep(0.1)
        
        return {
            'successful': successful,
            'failed': failed,
            'total': successful + failed
        }

# Initialize email service
email_service = EmailService()

@csrf_exempt
@require_http_methods(["POST"])
def newsletter_subscribe(request):
    """Subscribe to newsletter"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        name = data.get('name', '')
        
        if not email:
            return JsonResponse({
                'success': False,
                'message': 'Email is required'
            })
        
        # Check if already subscribed
        # subscriber, created = NewsletterSubscriber.objects.get_or_create(
        #     email=email,
        #     defaults={'name': name, 'is_active': True}
        # )
        
        # if not created and not subscriber.is_active:
        #     subscriber.is_active = True
        #     subscriber.save()
        
        # Send welcome email
        welcome_subject = "Welcome to our Newsletter!"
        welcome_content = render_to_string('emails/newsletter_welcome.html', {
            'name': name or 'Subscriber',
            'unsubscribe_url': request.build_absolute_uri('/newsletter/unsubscribe/')
        })
        
        email_service.send_single_email(email, welcome_subject, welcome_content)
        
        return JsonResponse({
            'success': True,
            'message': 'Successfully subscribed to newsletter!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@csrf_exempt
@require_http_methods(["POST", "GET"])
def newsletter_unsubscribe(request):
    """Unsubscribe from newsletter"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            
            # subscriber = NewsletterSubscriber.objects.filter(email=email).first()
            # if subscriber:
            #     subscriber.is_active = False
            #     subscriber.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Successfully unsubscribed from newsletter'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return render(request, 'newsletter/unsubscribe.html')

@login_required
@require_http_methods(["POST"])
def newsletter_send_mass(request):
    """Send mass newsletter immediately"""
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Permission denied'
        })
    
    try:
        data = json.loads(request.body)
        subject = data.get('subject')
        html_content = data.get('html_content')
        text_content = data.get('text_content', '')
        
        if not subject or not html_content:
            return JsonResponse({
                'success': False,
                'message': 'Subject and content are required'
            })
        
        # Get active subscribers
        # subscribers = NewsletterSubscriber.objects.filter(is_active=True)
        # email_list = [{'email': s.email, 'name': s.name} for s in subscribers]
        
        # For demo purposes, using empty list
        email_list = []
        
        # Send emails in background thread
        def send_emails():
            result = email_service.send_bulk_emails(email_list, subject, html_content, text_content)
            # Log result or save to database
            print(f"Newsletter sent: {result}")
        
        threading.Thread(target=send_emails).start()
        
        return JsonResponse({
            'success': True,
            'message': f'Newsletter is being sent to {len(email_list)} subscribers'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
@require_http_methods(["POST"])
def newsletter_schedule(request):
    """Schedule newsletter for future sending"""
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Permission denied'
        })
    
    try:
        data = json.loads(request.body)
        subject = data.get('subject')
        html_content = data.get('html_content')
        text_content = data.get('text_content', '')
        scheduled_time = data.get('scheduled_time')  # ISO format datetime
        
        if not all([subject, html_content, scheduled_time]):
            return JsonResponse({
                'success': False,
                'message': 'Subject, content, and scheduled time are required'
            })
        
        # Parse scheduled time
        scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
        
        if scheduled_datetime <= timezone.now():
            return JsonResponse({
                'success': False,
                'message': 'Scheduled time must be in the future'
            })
        
        # Save scheduled newsletter
        # scheduled_newsletter = ScheduledNewsletter.objects.create(
        #     subject=subject,
        #     html_content=html_content,
        #     text_content=text_content,
        #     scheduled_time=scheduled_datetime,
        #     created_by=request.user,
        #     is_sent=False
        # )
        
        return JsonResponse({
            'success': True,
            'message': f'Newsletter scheduled for {scheduled_datetime.strftime("%Y-%m-%d %H:%M")}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

# Celery task for scheduled newsletters (if you use Celery)
@shared_task
def send_scheduled_newsletters():
    """Celery task to send scheduled newsletters"""
    now = timezone.now()
    # scheduled_newsletters = ScheduledNewsletter.objects.filter(
    #     scheduled_time__lte=now,
    #     is_sent=False
    # )
    
    # for newsletter in scheduled_newsletters:
    #     try:
    #         subscribers = NewsletterSubscriber.objects.filter(is_active=True)
    #         email_list = [{'email': s.email, 'name': s.name} for s in subscribers]
    #         
    #         result = email_service.send_bulk_emails(
    #             email_list, 
    #             newsletter.subject, 
    #             newsletter.html_content, 
    #             newsletter.text_content
    #         )
    #         
    #         newsletter.is_sent = True
    #         newsletter.sent_at = now
    #         newsletter.recipients_count = result['successful']
    #         newsletter.save()
    #         
    #     except Exception as e:
    #         print(f"Error sending scheduled newsletter {newsletter.id}: {e}")
    
    return "Scheduled newsletters processed"

# Management command alternative (if not using Celery)
class NewsletterScheduler:
    """Alternative scheduler using threading"""
    
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the scheduler"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_scheduler)
            self.thread.daemon = True
            self.thread.start()
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            try:
                self._process_scheduled_newsletters()
                time.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(60)
    
    def _process_scheduled_newsletters(self):
        """Process scheduled newsletters"""
        now = timezone.now()
        # Process scheduled newsletters similar to Celery task
        pass

# Initialize scheduler (start this in your Django app startup)
newsletter_scheduler = NewsletterScheduler()

def start_newsletter_scheduler():
    """Start the newsletter scheduler"""
    newsletter_scheduler.start()

def stop_newsletter_scheduler():
    """Stop the newsletter scheduler"""
    newsletter_scheduler.stop()