"""
Django settings for CSH project.

Generated by 'django-admin startproject' using Django 4.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
from pathlib import Path
import os
from datetime import timedelta

ALLOWED_HOSTS = ['13.127.171.88','172.16.20.48','rtsengser.cidcoindia.com']
# ALLOWED_HOSTS = ['127.0.0.1']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
# DEBUG = True   

# Adding the Router
DATABASE_ROUTERS = ['Account.routers.ServiceRouter']

DATABASES = {
    'default': {
        # 'ENGINE': 'django.db.backends.mysql',
        'ENGINE': 'mysql.connector.django',
        'NAME': 'common_db',      # Replace with your database name
        'USER': 'root',      # Replace with your database user
        'PASSWORD': 'Mysql_7319',  # Replace with your database password
        # 'HOST': '13.127.171.88',       # IP FOR TEST
        'HOST': '127.0.0.1',       # IP FOR LOCAL VM
        'PORT': '3306',            
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    },
     '1': {
        'ENGINE': 'mysql.connector.django',
        'NAME': 'drainage_connection_db',  
        'USER': 'root',    
        'PASSWORD': 'Mysql_7319',  
        # 'HOST': '13.127.171.88',   
        'HOST': '127.0.0.1',    
        'PORT': '3306',
    },
     '2': {
        'ENGINE': 'mysql.connector.django',
        'NAME': 'tree_cutting_db',  
        'USER': 'root',    
        'PASSWORD': 'Mysql_7319',  
        # 'HOST': '13.127.171.88',  
        'HOST': '127.0.0.1',      
        'PORT': '3306',
    },
     '3': {
        'ENGINE': 'mysql.connector.django',
        'NAME': 'tree_trimming_db',  
        'USER': 'root',    
        'PASSWORD': 'Mysql_7319',  
        # 'HOST': '13.127.171.88',  
        'HOST': '127.0.0.1',      
        'PORT': '3306',
    },
     '4': {
        'ENGINE': 'mysql.connector.django',
        'NAME': 'contract_registration_db',  
        'USER': 'root',    
        'PASSWORD': 'Mysql_7319',  
        # 'HOST': '13.127.171.88',  
        'HOST': '127.0.0.1',      
        'PORT': '3306',
    },
      '5': {
        'ENGINE': 'mysql.connector.django',
        'NAME': 'product_approval_db',  
        'USER': 'root',    
        'PASSWORD': 'Mysql_7319',  
        # 'HOST': '13.127.171.88',  
        'HOST': '127.0.0.1',      
        'PORT': '3306',
    },
}

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# MEDIA_ROOT = os.path.join(BASE_DIR, 'D:/Python Project/Documents/')
# MEDIA_ROOT = os.path.join(BASE_DIR, '/home/ubuntu/Documents/')
MEDIA_ROOT = os.path.join(BASE_DIR, '/home/services/Documents/')
MEDIA_URL = '/media/'

SECURE_CROSS_ORIGIN_OPENER_POLICY = None

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-$vute#e^tqlu5ehd!)vv5m3x!z5^7p%jb9hm9272-!6%0ouz*r'
SECRET_KEY1 = '5pQsZXhU8vKyv7GxThldGn_JLK9UXVYyZD3GwQxsztY='
LOGOUT_REDIRECT_URL ='Account'
LOGIN_REDIRECT_URL ='Account'
LOGIN_URL="Account"
# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


SESSION_EXPIRE_AFTER_LAST_ACTIVITY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 3600  # 1-hour session timeout
# Clickjacking Protection
X_FRAME_OPTIONS = 'DENY'

# Security Headers
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True


ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', 'oRVCHTumzesh-E71A-bAnjjEDuIlkceL6dvAYiCShp0=')

AUTH_USER_MODEL = 'Account.CustomUser'

# Account Lockout 
AXES_FAILURE_LIMIT = 5  # Lock out after 5 failed login attempts
AXES_COOLOFF_TIME = 1
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'axes',
    'Account',
    'MenuManager',
    'Masters',
    'corsheaders',
    'Reports',
    'Dashboard',
    'DrainageConnection',
    'TreeCutting',
    'TreeTrimming',
    'ContractRegistration',
    'ProductApproval',
]

# SESSION_ENGINE ="django.contrib.sessions.backends.signed_cookies"
# SESSION_ENGINE ="django.contrib.sessions.backends.file"
# SESSION_FILE_PATH=r"D:\PYTHON PROJECTS\CSH"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_auto_logout.middleware.auto_logout',
    'corsheaders.middleware.CorsMiddleware',
    'axes.middleware.AxesMiddleware',
    'Account.middleware.ServiceDatabaseMiddleware',
]
CORS_ALLOWED_ORIGINS = [
    'http://13.202.157.7',
    'https://push3.aclgateway.com'
]
CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_WHITELIST = [
    'http://13.202.157.7',
    'https://push3.aclgateway.com'
]
AUTO_LOGOUT = {
    'IDLE_TIME': 3600,
    'REDIRECT_TO_LOGIN_IMMEDIATELY': True,
    'MESSAGE': 'The session has expired. Please login again to continue.',
}
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
   
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            # 'filename': os.path.join(BASE_DIR, 'D:/Python Project/CSH Logs', 'django.log'),  
            # 'filename': os.path.join(BASE_DIR, '/home/ubuntu/CSH Logs', 'django.log'),  
            'filename': os.path.join(BASE_DIR, '/home/services/CSH Logs', 'django.log'),  
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    # Add any additional authentication backends if needed
    'axes.backends.AxesStandaloneBackend',  # Add this line
]

ROOT_URLCONF = 'CSH.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        "DIRS": ['Template'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django_auto_logout.context_processors.auto_logout_client',
                'Account.context_processors.logged_in_user',
            ],
        },
    },
]

WSGI_APPLICATION = 'CSH.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': { 'min_length': 8,},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

TIME_ZONE = 'Asia/Kolkata' 
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/




# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587  # Use the appropriate port for your SMTP server
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'noreply.Complianceoperation@gmail.com'
EMAIL_HOST_PASSWORD = 'mgypdsldfzsvyvle'

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=2),  # Change the access token expiry time to 2 days
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),  # Keep the refresh token expiry time as 30 days
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': False,
}

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'notify_users_2pm': {
        'task': 'your_app.tasks.check_and_notify_all_users',
        'schedule': crontab(hour=14, minute=0),  # Run every day at 2 PM
    },
    'notify_users_7pm': {
        'task': 'your_app.tasks.check_and_notify_all_users',
        'schedule': crontab(hour=19, minute=0),  # Run every day at 7 PM
    },
}
