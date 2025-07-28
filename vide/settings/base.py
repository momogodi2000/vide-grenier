# vide/settings/base.py - OPTIMIZED VERSION
import os
from pathlib import Path

from decouple import config
# Social providers config
try:
    from .social_providers import SOCIALACCOUNT_PROVIDERS
except ImportError:
    SOCIALACCOUNT_PROVIDERS = {}

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.onrender.com', 'vide-grenier-kamer.onrender.com']

# VGK Specific Settings
VGK_SETTINGS = {
    'SUPPORTED_CITIES': ['DOUALA', 'YAOUNDE'],
    'DEFAULT_CURRENCY': 'FCFA',
    'DELIVERY_FEE': 2000,
    'ADMIN_WHATSAPP': '237694638412',
    'COMPANY_NAME': 'Vidé-Grenier Kamer',
    'COMPANY_EMAIL': 'support@videgrenier-kamer.com',
    'COMPANY_PHONE': '+237 694 63 84 12',
    'COMMISSION_RATE': 0.08,  # 8% commission
    'CDN_URL': config('CDN_URL', default=''),  # CDN URL for static files
    'MIN_PRODUCT_PRICE': 100,  # Minimum product price in FCFA
    'MAX_PRODUCT_PRICE': 10000000,  # Maximum product price in FCFA
    'DELIVERY_COST_DOUALA_YAOUNDE': 2000,  # Delivery cost for Douala and Yaounde
    'DELIVERY_COST_OTHER_CITIES': 5000,  # Delivery cost for other cities
    'PICKUP_POINTS': {
        'DOUALA': [
            {'name': 'Point de retrait Douala Centre', 'address': 'Centre-ville, Douala'},
            {'name': 'Point de retrait Douala Akwa', 'address': 'Akwa, Douala'},
        ],
        'YAOUNDE': [
            {'name': 'Point de retrait Yaounde Centre', 'address': 'Centre-ville, Yaounde'},
            {'name': 'Point de retrait Yaounde Bastos', 'address': 'Bastos, Yaounde'},
        ]
    }
}

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django.contrib.postgres',  # PostgreSQL specific features
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    # 'channels',  # Commented out to avoid dependency
    # 'crispy_tailwind',  # Commented out to avoid dependency
]

LOCAL_APPS = [
    'backend',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Performance monitoring middleware
    'backend.views.PerformanceMiddleware',
]

ROOT_URLCONF = 'vide.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'backend.context_processors.global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'vide.wsgi.application'
ASGI_APPLICATION = 'vide.asgi.application'

# Channels configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# WebSocket settings
WEBSOCKET_URL = '/ws/'
WEBSOCKET_ORIGIN_WHITELIST = [
    'localhost:8000',
    '127.0.0.1:8000',
]

# Database - OPTIMIZED CONFIGURATION
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='vide_grenier_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='root'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        # Database optimization settings
        'OPTIONS': {
            'MAX_CONNS': 20,  # Maximum connections
            'CONN_MAX_AGE': 600,  # Connection lifetime (10 minutes)
            'OPTIONS': {
                'sslmode': 'require' if not DEBUG else 'disable',
            },
        },
        # Connection pooling
        'CONN_HEALTH_CHECKS': True,
        'ATOMIC_REQUESTS': False,  # Disable for better performance
    }
}

# Redis Configuration - OPTIMIZED
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

# Enhanced Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        },
        'TIMEOUT': 300,  # 5 minutes default
        'KEY_PREFIX': 'vgk',
        'VERSION': 1,
    },
    'session': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL + '/1',  # Separate database for sessions
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'TIMEOUT': 1500,  # 25 minutes for sessions
        'KEY_PREFIX': 'vgk_session',
    },
    'long_term': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL + '/2',  # Separate database for long-term cache
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'TIMEOUT': 3600,  # 1 hour for long-term cache
        'KEY_PREFIX': 'vgk_long',
    }
}

# Session Configuration - OPTIMIZED
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'session'
SESSION_COOKIE_AGE = 1500  # 25 minutes
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'fr-cm'
TIME_ZONE = 'Africa/Douala'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images) - OPTIMIZED
STATIC_URL = VGK_SETTINGS.get('CDN_URL', '') + '/static/' if VGK_SETTINGS.get('CDN_URL') else '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files - OPTIMIZED
MEDIA_URL = VGK_SETTINGS.get('CDN_URL', '') + '/media/' if VGK_SETTINGS.get('CDN_URL') else '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Static files configuration optimisée
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Configuration WhiteNoise améliorée
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Headers pour les fichiers statiques
WHITENOISE_MAX_AGE = 31536000  # 1 an pour les fichiers avec hash
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br']

# Compression des fichiers CSS/JS
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = config('DEBUG', default=False, cast=bool)

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'backend.User'

# Django Allauth
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# Allauth settings
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_SESSION_REMEMBER = True
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Custom Allauth adapters for user type redirects
ACCOUNT_ADAPTER = 'backend.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'backend.adapters.CustomSocialAccountAdapter'

# Social providers (Google, Facebook)
SOCIALACCOUNT_PROVIDERS = SOCIALACCOUNT_PROVIDERS

# REST Framework - OPTIMIZED
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    ],
}

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "https://vide-grenier-kamer.onrender.com"
]

# Security Settings - ENHANCED
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Email Configuration - OPTIMIZED
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = VGK_SETTINGS['COMPANY_EMAIL']

# Crispy Forms
# CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
# CRISPY_TEMPLATE_PACK = "tailwind"

# Payment APIs
CAMPAY_API_KEY = config('CAMPAY_API_KEY', default='')
CAMPAY_BASE_URL = 'https://api.campay.net'
ORANGE_MONEY_API_KEY = config('ORANGE_MONEY_API_KEY', default='')
MTN_MONEY_API_KEY = config('MTN_MONEY_API_KEY', default='')

# File Upload Settings - OPTIMIZED
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_TEMP_DIR = BASE_DIR / 'temp'

# Celery Configuration - OPTIMIZED
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_WORKER_CONCURRENCY = 8
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ROUTES = {
    'backend.tasks.*': {'queue': 'default'},
    'backend.tasks.send_newsletter_task': {'queue': 'newsletter'},
    'backend.tasks.send_bulk_notification_task': {'queue': 'notifications'},
}
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_DEFAULT_EXCHANGE = 'default'
CELERY_TASK_DEFAULT_ROUTING_KEY = 'default'

# Newsletter Settings
NEWSLETTER_SETTINGS = {
    'BATCH_SIZE': 50,
    'BATCH_DELAY': 5,  # seconds between batches
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 300,  # 5 minutes
}

# Performance Settings
PERFORMANCE_SETTINGS = {
    'CACHE_TIMEOUT': 900,  # 15 minutes
    'PRODUCT_CACHE_TIMEOUT': 1800,  # 30 minutes
    'DASHBOARD_CACHE_TIMEOUT': 600,  # 10 minutes
    'SEARCH_CACHE_TIMEOUT': 300,  # 5 minutes
    'MAX_QUERIES_PER_REQUEST': 20,
    'SLOW_QUERY_THRESHOLD': 1.0,  # seconds
}

# Logging - ENHANCED
LOGS_DIR = BASE_DIR / 'logs'
os.makedirs(LOGS_DIR, exist_ok=True)

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
        'performance': {
            'format': '{asctime} {levelname} {message} - {duration:.2f}s - {query_count} queries',
            'style': '{',
        },
    },
    'handlers': {
        'error_console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'request_console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'performance_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'performance.log',
            'formatter': 'performance',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'errors.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['error_console', 'request_console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['error_console', 'request_console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['request_console', 'error_console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.server': {
            'handlers': ['request_console', 'error_console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['error_console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'backend.views': {
            'handlers': ['performance_file', 'error_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['performance_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Database Query Logging (only in development)
if DEBUG:
    LOGGING['loggers']['django.db.backends']['level'] = 'DEBUG'
    LOGGING['loggers']['django.db.backends']['handlers'] = ['request_console']