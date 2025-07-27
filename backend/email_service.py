# backend/email_service.py - Comprehensive Email Notification System

import yagmail
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail, send_mass_mail
from django.utils import timezone
from datetime import datetime, timedelta
import logging
import threading
from typing import List, Dict, Optional, Union
import json
import os

logger = logging.getLogger(__name__)

class EmailNotificationService:
    """
    Comprehensive email notification service with yagmail integration
    """
    
    def __init__(self):
        self.smtp_host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'EMAIL_PORT', 587)
        self.smtp_username = getattr(settings, 'EMAIL_HOST_USER', '')
        self.smtp_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        self.smtp_use_tls = getattr(settings, 'EMAIL_USE_TLS', True)
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@vide-grenier-kamer.com')
        self.from_name = getattr(settings, 'EMAIL_FROM_NAME', 'Vidé-Grenier Kamer')
        
        # Initialize yagmail
        self.yag = None
        self.setup_yagmail()
    
    def setup_yagmail(self):
        """Setup yagmail connection"""
        try:
            if self.smtp_username and self.smtp_password:
                self.yag = yagmail.SMTP(
                    user=self.smtp_username,
                    password=self.smtp_password,
                    host=self.smtp_host,
                    port=self.smtp_port
                )
                logger.info("Yagmail connection established successfully")
            else:
                logger.warning("SMTP credentials not configured, using Django's email backend")
        except Exception as e:
            logger.error(f"Failed to setup yagmail: {e}")
            self.yag = None
    
    def send_email(self, to_email: str, subject: str, html_content: str, 
                   text_content: str = None, attachments: List[str] = None,
                   reply_to: str = None) -> bool:
        """
        Send email using yagmail or Django's email backend
        """
        try:
            if self.yag:
                # Use yagmail
                self.yag.send(
                    to=to_email,
                    subject=subject,
                    contents=[html_content],
                    attachments=attachments or [],
                    headers={'Reply-To': reply_to} if reply_to else {}
                )
            else:
                # Use Django's email backend
                send_mail(
                    subject=subject,
                    message=text_content or self.html_to_text(html_content),
                    from_email=self.from_email,
                    recipient_list=[to_email],
                    html_message=html_content,
                    fail_silently=False
                )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_bulk_emails(self, emails: List[Dict]) -> Dict[str, int]:
        """
        Send bulk emails with success/failure tracking
        """
        success_count = 0
        failure_count = 0
        
        for email_data in emails:
            try:
                success = self.send_email(
                    to_email=email_data['to_email'],
                    subject=email_data['subject'],
                    html_content=email_data['html_content'],
                    text_content=email_data.get('text_content'),
                    attachments=email_data.get('attachments'),
                    reply_to=email_data.get('reply_to')
                )
                
                if success:
                    success_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to send bulk email: {e}")
                failure_count += 1
        
        return {
            'success_count': success_count,
            'failure_count': failure_count,
            'total_count': len(emails)
        }
    
    def send_product_approval_email(self, product, approved: bool = True, reason: str = None) -> bool:
        """
        Send product approval/rejection email to seller
        """
        try:
            seller = product.seller
            subject = f"Votre produit a été {'approuvé' if approved else 'rejeté'}"
            
            context = {
                'product': product,
                'seller': seller,
                'approved': approved,
                'reason': reason,
                'approval_date': timezone.now(),
                'product_url': f"{settings.SITE_URL}/products/{product.slug}",
                'admin_contact': settings.ADMIN_EMAIL
            }
            
            html_content = render_to_string('emails/product_approval.html', context)
            text_content = render_to_string('emails/product_approval.txt', context)
            
            return self.send_email(
                to_email=seller.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                reply_to=settings.ADMIN_EMAIL
            )
            
        except Exception as e:
            logger.error(f"Failed to send product approval email: {e}")
            return False
    
    def send_order_confirmation_email(self, order) -> bool:
        """
        Send order confirmation email to customer
        """
        try:
            customer = order.customer
            subject = f"Confirmation de commande #{order.order_number}"
            
            context = {
                'order': order,
                'customer': customer,
                'order_items': order.items.all(),
                'order_url': f"{settings.SITE_URL}/orders/{order.id}",
                'support_email': settings.SUPPORT_EMAIL
            }
            
            html_content = render_to_string('emails/order_confirmation.html', context)
            text_content = render_to_string('emails/order_confirmation.txt', context)
            
            return self.send_email(
                to_email=customer.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                reply_to=settings.SUPPORT_EMAIL
            )
            
        except Exception as e:
            logger.error(f"Failed to send order confirmation email: {e}")
            return False
    
    def send_payment_confirmation_email(self, payment) -> bool:
        """
        Send payment confirmation email
        """
        try:
            customer = payment.order.customer
            subject = f"Confirmation de paiement - Commande #{payment.order.order_number}"
            
            context = {
                'payment': payment,
                'order': payment.order,
                'customer': customer,
                'payment_date': payment.created_at,
                'support_email': settings.SUPPORT_EMAIL
            }
            
            html_content = render_to_string('emails/payment_confirmation.html', context)
            text_content = render_to_string('emails/payment_confirmation.txt', context)
            
            return self.send_email(
                to_email=customer.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                reply_to=settings.SUPPORT_EMAIL
            )
            
        except Exception as e:
            logger.error(f"Failed to send payment confirmation email: {e}")
            return False
    
    def send_delivery_status_email(self, order, status: str, tracking_number: str = None) -> bool:
        """
        Send delivery status update email
        """
        try:
            customer = order.customer
            subject = f"Mise à jour de livraison - Commande #{order.order_number}"
            
            context = {
                'order': order,
                'customer': customer,
                'status': status,
                'tracking_number': tracking_number,
                'delivery_date': timezone.now(),
                'support_email': settings.SUPPORT_EMAIL
            }
            
            html_content = render_to_string('emails/delivery_status.html', context)
            text_content = render_to_string('emails/delivery_status.txt', context)
            
            return self.send_email(
                to_email=customer.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                reply_to=settings.SUPPORT_EMAIL
            )
            
        except Exception as e:
            logger.error(f"Failed to send delivery status email: {e}")
            return False
    
    def send_newsletter_email(self, newsletter, subscribers: List) -> Dict[str, int]:
        """
        Send newsletter to subscribers
        """
        try:
            emails = []
            for subscriber in subscribers:
                context = {
                    'newsletter': newsletter,
                    'subscriber': subscriber,
                    'unsubscribe_url': f"{settings.SITE_URL}/newsletter/unsubscribe/{subscriber.unsubscribe_token}",
                    'site_url': settings.SITE_URL
                }
                
                html_content = render_to_string('emails/newsletter.html', context)
                text_content = render_to_string('emails/newsletter.txt', context)
                
                emails.append({
                    'to_email': subscriber.email,
                    'subject': newsletter.subject,
                    'html_content': html_content,
                    'text_content': text_content,
                    'reply_to': settings.NEWSLETTER_EMAIL
                })
            
            return self.send_bulk_emails(emails)
            
        except Exception as e:
            logger.error(f"Failed to send newsletter: {e}")
            return {'success_count': 0, 'failure_count': len(subscribers), 'total_count': len(subscribers)}
    
    def send_admin_notification_email(self, notification_type: str, data: Dict) -> bool:
        """
        Send admin notification emails
        """
        try:
            admin_emails = getattr(settings, 'ADMIN_EMAILS', [settings.ADMIN_EMAIL])
            subject = f"Notification Admin - {notification_type}"
            
            context = {
                'notification_type': notification_type,
                'data': data,
                'timestamp': timezone.now(),
                'site_url': settings.SITE_URL
            }
            
            html_content = render_to_string('emails/admin_notification.html', context)
            text_content = render_to_string('emails/admin_notification.txt', context)
            
            success_count = 0
            for admin_email in admin_emails:
                if self.send_email(
                    to_email=admin_email,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content
                ):
                    success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to send admin notification email: {e}")
            return False
    
    def send_welcome_email(self, user) -> bool:
        """
        Send welcome email to new users
        """
        try:
            subject = "Bienvenue sur Vidé-Grenier Kamer"
            
            context = {
                'user': user,
                'site_url': settings.SITE_URL,
                'support_email': settings.SUPPORT_EMAIL
            }
            
            html_content = render_to_string('emails/welcome.html', context)
            text_content = render_to_string('emails/welcome.txt', context)
            
            return self.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                reply_to=settings.SUPPORT_EMAIL
            )
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")
            return False
    
    def send_password_reset_email(self, user, reset_url: str) -> bool:
        """
        Send password reset email
        """
        try:
            subject = "Réinitialisation de votre mot de passe"
            
            context = {
                'user': user,
                'reset_url': reset_url,
                'expiry_hours': 24,
                'support_email': settings.SUPPORT_EMAIL
            }
            
            html_content = render_to_string('emails/password_reset.html', context)
            text_content = render_to_string('emails/password_reset.txt', context)
            
            return self.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                reply_to=settings.SUPPORT_EMAIL
            )
            
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
            return False
    
    def send_stock_alert_email(self, product, current_stock: int, threshold: int) -> bool:
        """
        Send stock alert email to admin
        """
        try:
            subject = f"Alerte Stock - {product.title}"
            
            context = {
                'product': product,
                'current_stock': current_stock,
                'threshold': threshold,
                'product_url': f"{settings.SITE_URL}/admin/products/{product.id}",
                'admin_url': f"{settings.SITE_URL}/admin-panel/stock"
            }
            
            html_content = render_to_string('emails/stock_alert.html', context)
            text_content = render_to_string('emails/stock_alert.txt', context)
            
            admin_emails = getattr(settings, 'ADMIN_EMAILS', [settings.ADMIN_EMAIL])
            success_count = 0
            
            for admin_email in admin_emails:
                if self.send_email(
                    to_email=admin_email,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content
                ):
                    success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to send stock alert email: {e}")
            return False
    
    def send_commission_notification_email(self, user, commission_amount: float, period: str) -> bool:
        """
        Send commission notification email
        """
        try:
            subject = f"Commission - Période {period}"
            
            context = {
                'user': user,
                'commission_amount': commission_amount,
                'period': period,
                'wallet_url': f"{settings.SITE_URL}/wallet",
                'support_email': settings.SUPPORT_EMAIL
            }
            
            html_content = render_to_string('emails/commission_notification.html', context)
            text_content = render_to_string('emails/commission_notification.txt', context)
            
            return self.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                reply_to=settings.SUPPORT_EMAIL
            )
            
        except Exception as e:
            logger.error(f"Failed to send commission notification email: {e}")
            return False
    
    def html_to_text(self, html_content: str) -> str:
        """
        Convert HTML content to plain text
        """
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text()
        except ImportError:
            # Fallback if BeautifulSoup is not available
            import re
            return re.sub(r'<[^>]+>', '', html_content)
    
    def send_async_email(self, to_email: str, subject: str, html_content: str, 
                        text_content: str = None, attachments: List[str] = None,
                        reply_to: str = None):
        """
        Send email asynchronously
        """
        def send_email_async():
            self.send_email(to_email, subject, html_content, text_content, attachments, reply_to)
        
        thread = threading.Thread(target=send_email_async)
        thread.daemon = True
        thread.start()
    
    def test_connection(self) -> bool:
        """
        Test email connection
        """
        try:
            if self.yag:
                # Test yagmail connection
                self.yag.send(to=self.smtp_username, subject="Test", contents="Test email")
            else:
                # Test Django email backend
                send_mail(
                    subject="Test",
                    message="Test email",
                    from_email=self.from_email,
                    recipient_list=[self.smtp_username],
                    fail_silently=False
                )
            return True
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False
    
    def get_email_stats(self) -> Dict:
        """
        Get email sending statistics
        """
        # This would typically query a database table tracking email sends
        return {
            'total_sent': 0,
            'successful': 0,
            'failed': 0,
            'last_sent': None
        }

# Global email service instance
email_service = EmailNotificationService() 