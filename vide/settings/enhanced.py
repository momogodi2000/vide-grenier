# vide/settings/enhanced.py - ENHANCED SETTINGS FOR VGK ADVANCED FEATURES
from .base import *
import os

# ============= AI & MACHINE LEARNING =============
# AI Recommendation Engine Settings
AI_RECOMMENDATIONS = {
    'ENABLED': True,
    'MIN_INTERACTIONS': 5,
    'SIMILARITY_THRESHOLD': 0.1,
    'CACHE_HOURS': 6,
    'ALGORITHMS': {
        'COLLABORATIVE_FILTERING': True,
        'CONTENT_BASED_FILTERING': True,
        'HYBRID_RECOMMENDATIONS': True
    }
}

# Machine Learning Dependencies
SKLEARN_CACHE_DIR = os.path.join(BASE_DIR, 'ml_cache')
os.makedirs(SKLEARN_CACHE_DIR, exist_ok=True)

# ============= SMART NOTIFICATIONS =============
# Notification System Configuration
SMART_NOTIFICATIONS = {
    'ENABLED': True,
    'CHANNELS': {
        'IN_APP': True,
        'EMAIL': True,
        'SMS': True,
        'PUSH': True,
        'WHATSAPP': False  # Requires WhatsApp Business API
    },
    'RATE_LIMITING': {
        'MAX_DAILY_NOTIFICATIONS': 10,
        'MAX_HOURLY_NOTIFICATIONS': 3
    },
    'DELIVERY_WINDOWS': {
        'MORNING': (8, 10),
        'LUNCH': (12, 13),
        'EVENING': (18, 20),
        'NIGHT': (20, 22)
    }
}

# SMS Configuration
SMS_PROVIDERS = {
    'DEFAULT': 'CAMPAY',
    'CAMPAY': {
        'API_KEY': os.environ.get('CAMPAY_API_KEY', ''),
        'API_SECRET': os.environ.get('CAMPAY_API_SECRET', ''),
        'SENDER_ID': 'VGK'
    },
    'TWILIO': {
        'ACCOUNT_SID': os.environ.get('TWILIO_ACCOUNT_SID', ''),
        'AUTH_TOKEN': os.environ.get('TWILIO_AUTH_TOKEN', ''),
        'FROM_NUMBER': os.environ.get('TWILIO_FROM_NUMBER', '')
    }
}

# Push Notification Configuration
PUSH_NOTIFICATIONS = {
    'FIREBASE': {
        'SERVER_KEY': os.environ.get('FIREBASE_SERVER_KEY', ''),
        'SENDER_ID': os.environ.get('FIREBASE_SENDER_ID', ''),
        'API_KEY': os.environ.get('FIREBASE_API_KEY', '')
    },
    'ONE_SIGNAL': {
        'APP_ID': os.environ.get('ONE_SIGNAL_APP_ID', ''),
        'API_KEY': os.environ.get('ONE_SIGNAL_API_KEY', '')
    }
}

# ============= ADVANCED PAYMENTS =============
# Payment Gateway Configuration
PAYMENT_GATEWAYS = {
    'CAMPAY': {
        'ENABLED': True,
        'API_KEY': os.environ.get('CAMPAY_API_KEY', ''),
        'API_SECRET': os.environ.get('CAMPAY_API_SECRET', ''),
        'API_URL': 'https://api.campay.net/api/v1/',
        'WEBHOOK_SECRET': os.environ.get('CAMPAY_WEBHOOK_SECRET', '')
    },
    'ORANGE_MONEY': {
        'ENABLED': True,
        'MERCHANT_KEY': os.environ.get('ORANGE_MERCHANT_KEY', ''),
        'API_URL': 'https://api.orange.com/orange-money-webpay/v1/',
        'WEBHOOK_SECRET': os.environ.get('ORANGE_WEBHOOK_SECRET', '')
    },
    'MTN_MONEY': {
        'ENABLED': True,
        'API_KEY': os.environ.get('MTN_API_KEY', ''),
        'API_SECRET': os.environ.get('MTN_API_SECRET', ''),
        'API_URL': 'https://momodeveloper.mtn.com/',
        'WEBHOOK_SECRET': os.environ.get('MTN_WEBHOOK_SECRET', '')
    }
}

# Cryptocurrency Payment Configuration
CRYPTO_PAYMENTS = {
    'ENABLED': True,
    'SUPPORTED_CURRENCIES': ['BTC', 'ETH', 'USDT', 'USDC'],
    'WALLET_PROVIDER': 'BLOCKCHAIN_INFO',  # Or 'COINBASE', 'BINANCE'
    'API_KEYS': {
        'BLOCKCHAIN_INFO': os.environ.get('BLOCKCHAIN_API_KEY', ''),
        'COINBASE': os.environ.get('COINBASE_API_KEY', ''),
        'BINANCE': os.environ.get('BINANCE_API_KEY', '')
    },
    'CONFIRMATIONS_REQUIRED': {
        'BTC': 2,
        'ETH': 12,
        'USDT': 12,
        'USDC': 12
    }
}

# Escrow Configuration
ESCROW_SETTINGS = {
    'ENABLED': True,
    'FEE_PERCENTAGE': 2.0,  # 2% escrow fee
    'AUTO_RELEASE_DAYS': 7,  # Auto-release after 7 days
    'DISPUTE_PERIOD_DAYS': 14,  # Dispute period
    'MINIMUM_AMOUNT': 10000,  # Minimum 10,000 FCFA for escrow
}

# Installment Payment Configuration
INSTALLMENT_SETTINGS = {
    'ENABLED': True,
    'AVAILABLE_PLANS': [2, 3, 6, 12],  # 2, 3, 6, or 12 installments
    'INTEREST_RATES': {
        2: 5.0,   # 5% for 2 installments
        3: 8.0,   # 8% for 3 installments
        6: 12.0,  # 12% for 6 installments
        12: 18.0  # 18% for 12 installments
    },
    'MINIMUM_AMOUNT': 50000,  # Minimum 50,000 FCFA for installments
    'DOWN_PAYMENT_PERCENTAGE': 30  # 30% down payment required
}

# ============= SOCIAL COMMERCE =============
# Social Features Configuration
SOCIAL_FEATURES = {
    'ENABLED': True,
    'USER_FOLLOWING': True,
    'SOCIAL_POSTS': True,
    'CONTENT_MODERATION': {
        'AUTO_MODERATE': True,
        'PROFANITY_FILTER': True,
        'MANUAL_REVIEW_THRESHOLD': 10  # Posts with >10 reports need manual review
    },
    'VIRAL_FEATURES': {
        'SHARE_REWARDS': True,
        'REFERRAL_BONUS': 1000,  # 1000 FCFA for successful referral
        'LOYALTY_POINTS_PER_POST': 10
    }
}

# Content Sharing Configuration
CONTENT_SHARING = {
    'PLATFORMS': ['FACEBOOK', 'TWITTER', 'WHATSAPP', 'TELEGRAM'],
    'TRACKING': True,
    'REWARDS': {
        'POINTS_PER_SHARE': 5,
        'POINTS_PER_CLICK': 1
    }
}

# ============= STAFF MANAGEMENT =============
# Staff System Configuration
STAFF_MANAGEMENT = {
    'QR_CODE_SYSTEM': {
        'ENABLED': True,
        'ERROR_CORRECTION': 'L',  # L, M, Q, H
        'BOX_SIZE': 10,
        'BORDER': 4
    },
    'TASK_MANAGEMENT': {
        'AUTO_ASSIGN': True,
        'PRIORITY_LEVELS': ['LOW', 'MEDIUM', 'HIGH', 'URGENT'],
        'SLA_HOURS': {
            'LOW': 48,
            'MEDIUM': 24,
            'HIGH': 8,
            'URGENT': 2
        }
    },
    'PERFORMANCE_TRACKING': {
        'ENABLED': True,
        'METRICS': ['EFFICIENCY', 'CUSTOMER_RATING', 'PUNCTUALITY', 'ACCURACY'],
        'REPORTING_FREQUENCY': 'DAILY'
    },
    'INVENTORY_MANAGEMENT': {
        'REAL_TIME_TRACKING': True,
        'LOW_STOCK_ALERT': 10,  # Alert when stock < 10 items
        'BARCODE_SCANNING': True
    }
}

# ============= ANALYTICS & BUSINESS INTELLIGENCE =============
# Analytics Configuration
ANALYTICS_SETTINGS = {
    'ENABLED': True,
    'GOOGLE_ANALYTICS': {
        'TRACKING_ID': os.environ.get('GA_TRACKING_ID', ''),
        'ENHANCED_ECOMMERCE': True
    },
    'FACEBOOK_PIXEL': {
        'PIXEL_ID': os.environ.get('FB_PIXEL_ID', ''),
        'ENABLED': True
    },
    'CUSTOM_EVENTS': {
        'TRACK_SCROLL_DEPTH': True,
        'TRACK_TIME_ON_PAGE': True,
        'TRACK_CLICK_HEATMAP': True
    }
}

# Business Intelligence
BUSINESS_INTELLIGENCE = {
    'ENABLED': True,
    'DASHBOARDS': {
        'ADMIN': True,
        'SELLER': True,
        'STAFF': True
    },
    'PREDICTIVE_ANALYTICS': {
        'SALES_FORECASTING': True,
        'CUSTOMER_LIFETIME_VALUE': True,
        'CHURN_PREDICTION': True,
        'DEMAND_FORECASTING': True
    },
    'CUSTOMER_SEGMENTATION': {
        'RFM_ANALYSIS': True,  # Recency, Frequency, Monetary
        'BEHAVIORAL_SEGMENTATION': True,
        'DEMOGRAPHIC_SEGMENTATION': True
    }
}

# ============= SEARCH & DISCOVERY =============
# Enhanced Search Configuration
SEARCH_SETTINGS = {
    'ELASTICSEARCH': {
        'ENABLED': False,  # Set to True if using Elasticsearch
        'HOSTS': [os.environ.get('ELASTICSEARCH_URL', 'localhost:9200')],
        'INDEX_NAME': 'vgk_products'
    },
    'AI_SEARCH': {
        'ENABLED': True,
        'FUZZY_MATCHING': True,
        'SEMANTIC_SEARCH': True,
        'AUTO_COMPLETE': True,
        'SPELL_CORRECTION': True
    },
    'FILTERS': {
        'FACETED_SEARCH': True,
        'DYNAMIC_FILTERS': True,
        'LOCATION_BASED': True,
        'PRICE_RANGE_OPTIMIZATION': True
    }
}

# ============= MOBILE & PWA =============
# Progressive Web App Configuration
PWA_SETTINGS = {
    'ENABLED': True,
    'OFFLINE_SUPPORT': True,
    'PUSH_NOTIFICATIONS': True,
    'CAMERA_INTEGRATION': True,
    'GEOLOCATION': True,
    'BACKGROUND_SYNC': True,
    'INSTALLATION_PROMPT': True
}

# Mobile App Configuration
MOBILE_APP = {
    'API_VERSION': 'v2',
    'DEEP_LINKING': True,
    'UNIVERSAL_LINKS': True,
    'QR_SCANNER': True,
    'BIOMETRIC_AUTH': True,
    'OFFLINE_MODE': True
}

# ============= SECURITY & COMPLIANCE =============
# Enhanced Security Settings
SECURITY_SETTINGS = {
    'TWO_FACTOR_AUTH': {
        'ENABLED': True,
        'METHODS': ['SMS', 'EMAIL', 'APP'],
        'REQUIRED_FOR_STAFF': True
    },
    'RATE_LIMITING': {
        'ENABLED': True,
        'LOGIN_ATTEMPTS': 5,
        'API_CALLS_PER_MINUTE': 100,
        'PASSWORD_RESET_ATTEMPTS': 3
    },
    'DATA_ENCRYPTION': {
        'ENCRYPT_PII': True,
        'ENCRYPT_PAYMENTS': True,
        'ENCRYPTION_ALGORITHM': 'AES-256-GCM'
    },
    'COMPLIANCE': {
        'GDPR': True,
        'CCPA': False,
        'DATA_RETENTION_DAYS': 2555,  # 7 years
        'AUDIT_LOGGING': True
    }
}

# ============= THIRD-PARTY INTEGRATIONS =============
# External Service Integrations
INTEGRATIONS = {
    'GOOGLE_MAPS': {
        'API_KEY': os.environ.get('GOOGLE_MAPS_API_KEY', ''),
        'GEOCODING': True,
        'PLACES_API': True
    },
    'CLOUDINARY': {
        'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
        'API_KEY': os.environ.get('CLOUDINARY_API_KEY', ''),
        'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', ''),
        'AUTO_OPTIMIZE': True,
        'AUTO_FORMAT': True
    },
    'REDIS': {
        'ENABLED': True,
        'URL': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        'CACHE_TIMEOUT': 3600
    },
    'CELERY': {
        'BROKER_URL': os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
        'RESULT_BACKEND': os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2'),
        'TASK_SERIALIZER': 'json',
        'ACCEPT_CONTENT': ['json'],
        'RESULT_SERIALIZER': 'json',
        'TIMEZONE': 'UTC'
    }
}

# ============= LOGGING & MONITORING =============
# Enhanced Logging
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
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'vgk.log'),
            'formatter': 'verbose',
        },
        'ai_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'ai.log'),
            'formatter': 'verbose',
        },
        'payment_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'payments.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'backend.ai_engine': {
            'handlers': ['ai_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'backend.financial_advanced': {
            'handlers': ['payment_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'backend.smart_notifications': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ============= CACHE CONFIGURATION =============
# Redis Cache Configuration
if INTEGRATIONS['REDIS']['ENABLED']:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': INTEGRATIONS['REDIS']['URL'],
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        },
        'recommendations': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': INTEGRATIONS['REDIS']['URL'],
            'KEY_PREFIX': 'rec',
            'TIMEOUT': AI_RECOMMENDATIONS['CACHE_HOURS'] * 3600,
        },
        'sessions': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': INTEGRATIONS['REDIS']['URL'],
            'KEY_PREFIX': 'sess',
        }
    }
    
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'sessions'

# ============= EMAIL CONFIGURATION =============
# Enhanced Email Settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@vgk.cm')

# Email Templates
EMAIL_TEMPLATES = {
    'WELCOME': 'emails/welcome.html',
    'ORDER_CONFIRMATION': 'emails/order_confirmation.html',
    'PAYMENT_SUCCESS': 'emails/payment_success.html',
    'REVIEW_REQUEST': 'emails/review_request.html',
    'PRICE_DROP_ALERT': 'emails/price_drop_alert.html',
    'NEWSLETTER': 'emails/newsletter.html'
}

# ============= FILE UPLOAD CONFIGURATION =============
# Enhanced File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Media Storage
if INTEGRATIONS['CLOUDINARY']['CLOUD_NAME']:
    # Use Cloudinary for media storage
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': INTEGRATIONS['CLOUDINARY']['CLOUD_NAME'],
        'API_KEY': INTEGRATIONS['CLOUDINARY']['API_KEY'],
        'API_SECRET': INTEGRATIONS['CLOUDINARY']['API_SECRET'],
        'SECURE': True,
        'RESOURCE_TYPE': 'auto'
    }

# ============= INSTALLED APPS ADDITIONS =============
INSTALLED_APPS += [
    # Third-party apps for enhanced features
    'django_redis',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'django_celery_beat',
    'django_celery_results',
    
    # Optional: Add if using Cloudinary
    # 'cloudinary_storage',
    # 'cloudinary',
]

# ============= MIDDLEWARE ADDITIONS =============
MIDDLEWARE += [
    'corsheaders.middleware.CorsMiddleware',
    'backend.middleware.UserBehaviorTrackingMiddleware',
    'backend.middleware.SmartNotificationMiddleware',
]

# ============= REST FRAMEWORK CONFIGURATION =============
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ]
}

# ============= CORS CONFIGURATION =============
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://vgk.cm",
    "https://www.vgk.cm",
]

CORS_ALLOW_CREDENTIALS = True

# ============= CELERY CONFIGURATION =============
if INTEGRATIONS['CELERY']['BROKER_URL']:
    CELERY_BROKER_URL = INTEGRATIONS['CELERY']['BROKER_URL']
    CELERY_RESULT_BACKEND = INTEGRATIONS['CELERY']['RESULT_BACKEND']
    CELERY_TASK_SERIALIZER = INTEGRATIONS['CELERY']['TASK_SERIALIZER']
    CELERY_ACCEPT_CONTENT = INTEGRATIONS['CELERY']['ACCEPT_CONTENT']
    CELERY_RESULT_SERIALIZER = INTEGRATIONS['CELERY']['RESULT_SERIALIZER']
    CELERY_TIMEZONE = INTEGRATIONS['CELERY']['TIMEZONE']
    
    # Celery Beat Schedule
    CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ============= ENVIRONMENT-SPECIFIC OVERRIDES =============
# Load environment-specific settings
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'staging':
    from .staging import *
else:
    from .development import *

# Ensure log directories exist
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Create necessary directories
for directory in ['ml_cache', 'qr_codes', 'temp_uploads']:
    os.makedirs(os.path.join(BASE_DIR, directory), exist_ok=True) 