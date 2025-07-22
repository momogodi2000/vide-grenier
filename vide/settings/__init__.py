# vide/settings/__init__.py
from .base import *

# Importer les settings selon l'environnement
import os
environment = os.environ.get('DJANGO_ENVIRONMENT', 'development')

if environment == 'production':
    from .production import *
elif environment == 'staging':
    from .staging import *
else:
    from .development import *
