# vide/settings/base.py
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

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'channels',
    'crispy_forms',
    'crispy_tailwind',
]

LOCAL_APPS = [
    'backend',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
INSTALLED_APPS += [
    'django_browser_reload',
]
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
]

MIDDLEWARE += [
    'django_browser_reload.middleware.BrowserReloadMiddleware',
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

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='vide_grenier_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='root'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Redis Configuration
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

# Channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

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

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
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
# Allauth settings
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_SESSION_REMEMBER = True
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Social providers (Google, Facebook)
SOCIALACCOUNT_PROVIDERS = SOCIALACCOUNT_PROVIDERS

# REST Framework
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
}

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "https://vide-grenier-kamer.onrender.com",
]

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# Payment APIs
CAMPAY_API_KEY = config('CAMPAY_API_KEY', default='')
CAMPAY_BASE_URL = 'https://api.campay.net'
ORANGE_MONEY_API_KEY = config('ORANGE_MONEY_API_KEY', default='')
MTN_MONEY_API_KEY = config('MTN_MONEY_API_KEY', default='')

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Session Configuration
SESSION_COOKIE_AGE = 1500  # 25 minutes
SESSION_SAVE_EVERY_REQUEST = False  # Only true inactivity counts
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Expire session when browser closes

# Logging

# Créer le dossier logs s'il n'existe pas
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
    },
    'handlers': {
        # 'console': {
        #     'level': 'DEBUG',
        #     'class': 'logging.StreamHandler',
        #     'formatter': 'verbose',
        # },
        # 'file': {
        #     'level': 'INFO',
        #     'class': 'logging.FileHandler',
        #     'filename': LOGS_DIR / 'django.log',
        #     'formatter': 'verbose',
        # },
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
        # 'backend': {
        #     'handlers': ['console', 'file', 'error_console', 'request_console'],
        #     'level': 'DEBUG',
        #     'propagate': False,
        # },
    },
}

# Custom Settings for VGK
VGK_SETTINGS = {
    'COMMISSION_RATE': 0.08,  # 8% commission
    'DELIVERY_COST_DOUALA_YAOUNDE': 1500,  # FCFA
    'DELIVERY_COST_OTHER_CITIES': 2500,  # FCFA
    'FREE_STORAGE_DAYS': 7,
    'STORAGE_COST_PER_DAY': 500,  # FCFA
    'MIN_PRODUCT_PRICE': 1000,  # FCFA
    'MAX_PRODUCT_PRICE': 50000000,  # FCFA
    'MAX_IMAGES_PER_PRODUCT': 5,
    'SUPPORTED_CITIES': ['Douala', 'Yaoundé'],
    'PICKUP_POINTS': {
        'Douala': {
            'address': '123 Avenue Ahidjo, Akwa',
            'phone': '+237 694 63 84 12',
            'hours': 'Lun-Ven 7h30-18h30, Sam 8h-16h, Dim 10h-14h'
        },
        'Yaoundé': {
            'address': '456 Avenue Kennedy, Centre-ville',
            'phone': '+237 694 63 84 13',
            'hours': 'Lun-Ven 7h30-18h30, Sam 8h-16h, Dim fermé'
        }
    }
}