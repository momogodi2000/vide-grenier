from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models_newsletter import NewsletterSubscriber
import json

@csrf_exempt
def newsletter_subscribe(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip()
            if not email:
                return JsonResponse({'success': False, 'error': 'Email requis.'})
            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({'success': False, 'error': 'Email invalide.'})
            obj, created = NewsletterSubscriber.objects.get_or_create(email=email)
            if not created:
                return JsonResponse({'success': False, 'error': 'Déjà abonné.'})
            return JsonResponse({'success': True})
        except Exception:
            return JsonResponse({'success': False, 'error': 'Erreur serveur.'})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'})
