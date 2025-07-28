
# vide/settings/development.py - OPTIMIZED FOR DEVELOPMENT
from .base import *

# Development settings
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Override database to use SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Override cache to use local memory
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Override session engine
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Override channel layers for development
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Email backend console for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable performance monitoring middleware for development
MIDDLEWARE = [mw for mw in MIDDLEWARE if 'PerformanceMiddleware' not in mw]

# Disable PostgreSQL specific features
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'django.contrib.postgres']

# Simplified Celery configuration for development
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'rpc://'

# Logging configuration for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

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

# Disable security settings for development
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
X_FRAME_OPTIONS = 'SAMEORIGIN'
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
