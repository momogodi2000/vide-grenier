# backend/tasks.py
"""
Celery tasks for background processing including scheduled newsletters
"""

from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail, send_mass_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
import yagmail
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Setup logging
logger = logging.getLogger(__name__)

# Import your models (adjust based on your actual models)
# from .models import NewsletterSubscriber, Newsletter, ScheduledNewsletter, NotificationLog

User = get_user_model()

class EmailService:
    """Enhanced email service for bulk operations"""
    
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
            logger.info("Yagmail setup successful")
        except Exception as e:
            logger.error(f"Error setting up yagmail: {e}")
            self.yag = None
    
    def send_email_batch(self, email_batch: List[Dict[str, Any]]) -> Dict[str, int]:
        """Send a batch of emails"""
        successful = 0
        failed = 0
        
        for email_data in email_batch:
            try:
                if self.send_single_email(**email_data):
                    successful += 1
                else:
                    failed += 1
                
                # Small delay to avoid overwhelming SMTP server
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error sending email to {email_data.get('to_email')}: {e}")
                failed += 1
        
        return {
            'successful': successful,
            'failed': failed,
            'total': successful + failed
        }
    
    def send_single_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """Send single email"""
        try:
            if not self.yag:
                self.setup_yagmail()
            
            if not self.yag:
                logger.error("Yagmail not initialized, falling back to Django send_mail")
                return self._fallback_send_email(to_email, subject, html_content, text_content)
            
            contents = [html_content]
            if text_content:
                contents.insert(0, text_content)
            
            self.yag.send(
                to=to_email,
                subject=subject,
                contents=contents
            )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return self._fallback_send_email(to_email, subject, html_content, text_content)
    
    def _fallback_send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """Fallback to Django's send_mail"""
        try:
            send_mail(
                subject=subject,
                message=text_content or html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                html_message=html_content,
                fail_silently=False
            )
            logger.info(f"Fallback email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Fallback email failed for {to_email}: {e}")
            return False

# Initialize email service
email_service = EmailService()

@shared_task(bind=True, max_retries=3)
def send_scheduled_newsletters(self):
    """Celery task to send scheduled newsletters"""
    try:
        now = timezone.now()
        logger.info(f"Checking for scheduled newsletters at {now}")
        
        # Get scheduled newsletters that are due (uncomment when models are ready)
        # scheduled_newsletters = ScheduledNewsletter.objects.filter(
        #     scheduled_time__lte=now,
        #     is_sent=False,
        #     is_cancelled=False
        # )
        
        # For demo purposes
        scheduled_newsletters = []
        
        sent_count = 0
        for newsletter in scheduled_newsletters:
            try:
                result = send_newsletter_task.delay(newsletter.id)
                if result.successful():
                    sent_count += 1
                    logger.info(f"Newsletter {newsletter.id} sent successfully")
                
            except Exception as e:
                logger.error(f"Error sending scheduled newsletter {newsletter.id}: {e}")
        
        logger.info(f"Processed {len(scheduled_newsletters)} scheduled newsletters, {sent_count} sent successfully")
        return f"Processed {len(scheduled_newsletters)} newsletters"
        
    except Exception as e:
        logger.error(f"Error in send_scheduled_newsletters: {e}")
        raise self.retry(countdown=60)

@shared_task(bind=True, max_retries=3)
def send_newsletter_task(self, newsletter_id: int):
    """Send a specific newsletter to all subscribers"""
    try:
        # newsletter = ScheduledNewsletter.objects.get(id=newsletter_id)
        # subscribers = NewsletterSubscriber.objects.filter(is_active=True)
        
        # For demo purposes
        newsletter_data = {
            'subject': 'Demo Newsletter',
            'html_content': '<h1>Hello World</h1>',
            'text_content': 'Hello World'
        }
        subscribers = []  # Replace with actual subscriber query
        
        if not subscribers:
            logger.warning(f"No active subscribers found for newsletter {newsletter_id}")
            return "No subscribers"
        
        # Prepare email batches
        batch_size = settings.NEWSLETTER_SETTINGS.get('BATCH_SIZE', 50)
        batches = [subscribers[i:i + batch_size] for i in range(0, len(subscribers), batch_size)]
        
        total_sent = 0
        total_failed = 0
        
        for batch_index, batch in enumerate(batches):
            logger.info(f"Processing batch {batch_index + 1}/{len(batches)} for newsletter {newsletter_id}")
            
            # Prepare email data for batch
            email_batch = []
            for subscriber in batch:
                personalized_content = newsletter_data['html_content'].format(
                    name=getattr(subscriber, 'name', 'Subscriber'),
                    email=getattr(subscriber, 'email', '')
                )
                personalized_subject = newsletter_data['subject'].format(
                    name=getattr(subscriber, 'name', 'Subscriber')
                )
                
                email_batch.append({
                    'to_email': getattr(subscriber, 'email'),
                    'subject': personalized_subject,
                    'html_content': personalized_content,
                    'text_content': newsletter_data['text_content']
                })
            
            # Send batch
            result = email_service.send_email_batch(email_batch)
            total_sent += result['successful']
            total_failed += result['failed']
            
            # Delay between batches
            batch_delay = settings.NEWSLETTER_SETTINGS.get('BATCH_DELAY', 5)
            if batch_index < len(batches) - 1:  # Don't delay after last batch
                time.sleep(batch_delay)
        
        # Update newsletter status (uncomment when model is ready)
        # newsletter.is_sent = True
        # newsletter.sent_at = timezone.now()
        # newsletter.recipients_count = total_sent
        # newsletter.failed_count = total_failed
        # newsletter.save()
        
        logger.info(f"Newsletter {newsletter_id} completed: {total_sent} sent, {total_failed} failed")
        return f"Sent to {total_sent} recipients, {total_failed} failed"
        
    except Exception as e:
        logger.error(f"Error sending newsletter {newsletter_id}: {e}")
        raise self.retry(countdown=300)  # Retry after 5 minutes

@shared_task(bind=True, max_retries=3)
def send_bulk_notification_task(self, notification_data: Dict[str, Any], recipient_ids: List[int]):
    """Send bulk notifications to specific users"""
    try:
        recipients = User.objects.filter(id__in=recipient_ids, is_active=True)
        
        if not recipients:
            logger.warning("No active recipients found for bulk notification")
            return "No recipients"
        
        successful = 0
        failed = 0
        
        for recipient in recipients:
            try:
                # Personalize content
                personalized_content = notification_data['content'].format(
                    name=recipient.get_full_name() or recipient.username,
                    username=recipient.username
                )
                personalized_subject = notification_data['subject'].format(
                    name=recipient.get_full_name() or recipient.username
                )
                
                # Send email
                if email_service.send_single_email(
                    to_email=recipient.email,
                    subject=personalized_subject,
                    html_content=personalized_content,
                    text_content=notification_data.get('text_content', '')
                ):
                    successful += 1
                else:
                    failed += 1
                
                # Small delay
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error sending notification to {recipient.email}: {e}")
                failed += 1
        
        logger.info(f"Bulk notification completed: {successful} sent, {failed} failed")
        return f"Sent to {successful} recipients, {failed} failed"
        
    except Exception as e:
        logger.error(f"Error in bulk notification task: {e}")
        raise self.retry(countdown=180)

@shared_task
def send_welcome_email_task(user_id: int):
    """Send welcome email to new user"""
    try:
        user = User.objects.get(id=user_id)
        
        subject = "Welcome to Vide Grenier!"
        html_content = render_to_string('emails/welcome.html', {
            'user': user,
            'site_name': 'Vide Grenier'
        })
        text_content = render_to_string('emails/welcome.txt', {
            'user': user,
            'site_name': 'Vide Grenier'
        })
        
        success = email_service.send_single_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        
        if success:
            logger.info(f"Welcome email sent to {user.email}")
        else:
            logger.error(f"Failed to send welcome email to {user.email}")
            
        return success
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for welcome email")
        return False
    except Exception as e:
        logger.error(f"Error sending welcome email to user {user_id}: {e}")
        return False

@shared_task
def cleanup_old_newsletters():
    """Clean up old newsletter data"""
    try:
        # Delete old sent newsletters (older than 6 months)
        cutoff_date = timezone.now() - timedelta(days=180)
        
        # deleted_count = ScheduledNewsletter.objects.filter(
        #     sent_at__lt=cutoff_date,
        #     is_sent=True
        # ).delete()[0]
        
        deleted_count = 0  # For demo
        
        logger.info(f"Cleaned up {deleted_count} old newsletters")
        return f"Cleaned up {deleted_count} newsletters"
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        return "Cleanup failed"

@shared_task
def send_password_reset_email_task(user_id: int, reset_token: str):
    """Send password reset email"""
    try:
        user = User.objects.get(id=user_id)
        
        subject = "Password Reset Request"
        html_content = render_to_string('emails/password_reset.html', {
            'user': user,
            'reset_token': reset_token,
            'site_name': 'Vide Grenier'
        })
        text_content = render_to_string('emails/password_reset.txt', {
            'user': user,
            'reset_token': reset_token,
            'site_name': 'Vide Grenier'
        })
        
        success = email_service.send_single_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        
        logger.info(f"Password reset email sent to {user.email}: {success}")
        return success
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for password reset email")
        return False
    except Exception as e:
        logger.error(f"Error sending password reset email: {e}")
        return False

@shared_task(bind=True, max_retries=3)
def test_email_configuration(self):
    """Test email configuration"""
    try:
        test_subject = "Email Configuration Test"
        test_content = """
        <h2>Email Configuration Test</h2>
        <p>This is a test email to verify that your email configuration is working correctly.</p>
        <p>If you receive this email, your SMTP settings are properly configured.</p>
        <p>Time sent: {}</p>
        """.format(timezone.now())
        
        # Send to admin email
        admin_email = settings.EMAIL_HOST_USER
        success = email_service.send_single_email(
            to_email=admin_email,
            subject=test_subject,
            html_content=test_content
        )
        
        if success:
            logger.info("Email configuration test successful")
            return "Email test successful"
        else:
            logger.error("Email configuration test failed")
            return "Email test failed"
            
    except Exception as e:
        logger.error(f"Error in email configuration test: {e}")
        raise self.retry(countdown=60)