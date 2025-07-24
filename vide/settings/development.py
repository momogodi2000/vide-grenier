
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
# Update LOGGING configuration for development
LOGGING['root']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'

# Debug tools for development
if DEBUG:
    # Add browser reload for development
    if 'django_browser_reload' not in INSTALLED_APPS:
        INSTALLED_APPS += ['django_browser_reload']
    
    # Configure middleware
    if 'django_browser_reload.middleware.BrowserReloadMiddleware' not in MIDDLEWARE:
        MIDDLEWARE = ['django_browser_reload.middleware.BrowserReloadMiddleware'] + MIDDLEWARE
    
    INTERNAL_IPS = ['127.0.0.1']

# Development server configuration
RUNSERVER_PLUS_PRINT_SQL = True
SHELL_PLUS_PRINT_SQL = True

# Enable auto-reload optimizations
RUNSERVER_PLUS_AUTO_RELOAD = True
STATICFILES_DIRS = list(STATICFILES_DIRS)  # Convert tuple to list if necessary
WHITENOISE_AUTOREFRESH = True
