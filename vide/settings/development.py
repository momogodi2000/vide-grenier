
# vide/settings/development.py
from .base import *

# Réglages pour le développement
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Base de données SQLite pour le développement
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Cache simple pour le développement
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Email backend console pour le développement
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging plus verbeux en développement
LOGGING['root']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'

# Debug toolbar pour le développement
if DEBUG:
    # INSTALLED_APPS += ['debug_toolbar']
    # MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware', 'allauth.account.middleware.AccountMiddleware'] + MIDDLEWARE
    INTERNAL_IPS = ['127.0.0.1']
