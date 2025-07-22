
# backend/apps.py
from django.apps import AppConfig


class BackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend'
    verbose_name = 'Vidé-Grenier Kamer Backend'
    
    def ready(self):
        # Importer les signaux
        import backend.signals
