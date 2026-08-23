import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-lathriya-spices-secret-key-default')

DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')

allowed_hosts_env = os.getenv('ALLOWED_HOSTS', '')
if allowed_hosts_env:
    ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_env.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['*']

SITE_DOMAIN = os.getenv('SITE_DOMAIN', 'lathriyaspices.com').strip()

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third party apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    
    # Custom app
    'spices',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
]

try:
    import whitenoise
    MIDDLEWARE.append('whitenoise.middleware.WhiteNoiseMiddleware')
except ImportError:
    pass

MIDDLEWARE.extend([
    'spices.middleware.security.SecurityAndRateLimitMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
])

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'SAMEORIGIN'
CSRF_COOKIE_HTTPONLY = False  # Must be False so frontend JS (AJAX cart, Razorpay verify) can read CSRF token
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'

ROOT_URLCONF = 'spices_project.urls'

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
                'spices.context_processors.cart_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'spices_project.wsgi.application'

# Database Configuration with Persistent Connection Pooling
DATABASE_URL = os.getenv('DATABASE_URL', '').strip()
DB_HOST = os.getenv('DB_HOST', '').strip()
DB_USER = os.getenv('DB_USER', '').strip()
DB_PASSWORD = os.getenv('DB_PASSWORD', '').strip()
DB_NAME = os.getenv('DB_NAME', 'postgres').strip()
DB_PORT = os.getenv('DB_PORT', '6543').strip()

if DATABASE_URL and 'your_supabase_db_password' not in DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,         # Reuse DB connection for 600s (10 mins)
            conn_health_checks=True,   # Validate idle pooled connections
        )
    }
    DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True  # Critical for Supabase transaction pooler (port 6543)
elif DB_HOST and DB_USER and DB_PASSWORD and 'your_supabase_db_password' not in DB_PASSWORD:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
            'CONN_MAX_AGE': 600,        # Connection pooling: 10 mins
            'CONN_HEALTH_CHECKS': True,  # Connection health check
            'DISABLE_SERVER_SIDE_CURSORS': True,  # Critical for Supabase transaction pooler (port 6543)
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID', ''),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET', ''),
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}

# AllAuth Configuration
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_STORE_TOKENS = False
SILENCED_SYSTEM_CHECKS = ['account.W001']
LOGIN_REDIRECT_URL = '/shop/'

LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/accounts/google/login/'
SOCIALACCOUNT_LOGIN_ON_GET = True

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Razorpay Keys
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')

# Media Files & Supabase Storage Configuration (S3 Private Bucket Compatible)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

SUPABASE_STORAGE_S3_KEY_ID = os.getenv('SUPABASE_STORAGE_S3_KEY_ID', '').strip()
SUPABASE_STORAGE_S3_SECRET_KEY = os.getenv('SUPABASE_STORAGE_S3_SECRET_KEY', '').strip()

if SUPABASE_STORAGE_S3_KEY_ID and SUPABASE_STORAGE_S3_SECRET_KEY and 'your_supabase_s3_access_key' not in SUPABASE_STORAGE_S3_KEY_ID:
    if 'storages' not in INSTALLED_APPS:
        INSTALLED_APPS.append('storages')
    
    AWS_ACCESS_KEY_ID = SUPABASE_STORAGE_S3_KEY_ID
    AWS_SECRET_ACCESS_KEY = SUPABASE_STORAGE_S3_SECRET_KEY
    AWS_STORAGE_BUCKET_NAME = os.getenv('SUPABASE_STORAGE_BUCKET', 'spices-posters').strip()
    AWS_S3_ENDPOINT_URL = os.getenv('SUPABASE_STORAGE_S3_ENDPOINT', '').strip()
    AWS_S3_REGION_NAME = os.getenv('SUPABASE_STORAGE_REGION', 'ap-southeast-1').strip()
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_QUERYSTRING_AUTH = True  # Generates signed URLs for secure access to private buckets
    AWS_QUERYSTRING_EXPIRES = 604800  # Presigned URLs remain valid and cacheable for 7 days
    AWS_S3_FILE_OVERWRITE = True
    AWS_DEFAULT_ACL = None


    # Aggressive dynamic caching headers for fast image loading
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'public, max-age=31536000, must-revalidate',
    }

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"


