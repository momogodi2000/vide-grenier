
# vide/settings/production.py
from .base import *
import dj_database_url

# Sécurité en production
DEBUG = False
SECURE_SSL_REDIRECT = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Hosts autorisés
ALLOWED_HOSTS = [
    'vide-grenier-kamer.onrender.com',
    'www.videgrenier-kamer.com',
    'videgrenier-kamer.com'
]

# Base de données PostgreSQL
DATABASES = {
    'default': dj_database_url.parse(config('DATABASE_URL'))
}

# Redis pour le cache et les sessions
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Sessions Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Storage pour les fichiers statiques et media
STORAGES = {
    'default': {
        'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Cloudinary pour les images
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': config('CLOUDINARY_API_KEY'),
    'API_SECRET': config('CLOUDINARY_API_SECRET'),
}

# Email en production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Logging en production
LOGGING['handlers']['file']['filename'] = '/var/log/django.log'
