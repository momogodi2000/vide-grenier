from django.core.management.base import BaseCommand
from backend.models import NewsletterSubscriber
import yagmail

class Command(BaseCommand):
    help = 'Send scheduled newsletter to all subscribers'

    def handle(self, *args, **kwargs):
        subject = "Votre newsletter périodique"
        message = "Ceci est votre newsletter automatique."
        emails = NewsletterSubscriber.objects.values_list('email', flat=True)
        yag = yagmail.SMTP('your_gmail_address', 'your_app_password')
        try:
            yag.send(to=emails, subject=subject, contents=message)
            self.stdout.write(self.style.SUCCESS('Newsletter envoyée à tous les abonnés.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Erreur: {e}'))