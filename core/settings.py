"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 4.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import os
import random
import string
import socket

from pathlib import Path
import dj_database_url
from dotenv import load_dotenv
from django.core.management.commands.runserver import Command as runserver

load_dotenv()  # take environment variables from .env.


def get_ip():
    """Get local ip address

    Returns:
        ip: string ip address
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0)
    try:
        # doesn't even have to be reachable
        sock.connect(('10.254.254.254', 1))
        ip = sock.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        sock.close()
    return str(ip)


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    SECRET_KEY = ''.join(random.choice(string.ascii_lowercase)
                         for i in range(32))

# SSL

if 'LOCAL' not in os.environ:
    global SECURE_PROXY_SSL_HEADER, SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE, RUNSERVERPLUS_SERVER_ADDRESS_PORT
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    runserver.default_port = 443
    runserver.default_addr = get_ip()
    RUNSERVERPLUS_SERVER_ADDRESS_PORT = f"{runserver.default_addr}:{runserver.default_port}"

# Render Deployment Code
# DEBUG = 'RENDER' not in os.environ
DEBUG = True
CURRENT_TOKEN = os.getenv("CURRENT_TOKEN", None)

# HOSTs List
ALLOWED_HOSTS = ["ghdash.zapto.org", 'cs587-dashboard.onrender.com', 'localhost', '127.0.0.1', '192.168.1.100']

# Add here your deployment HOSTS
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://localhost:5085',
                        'http://127.0.0.1:8000', 'http://127.0.0.1:5085']

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Application definition

INSTALLED_APPS = [
    'admin_soft.apps.AdminSoftDashboardConfig',
    "django_extensions",
    # "bootstrap_datepicker_plus",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "home",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

HOME_TEMPLATES = os.path.join(BASE_DIR, 'templates')

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [HOME_TEMPLATES],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DB_ENGINE = os.getenv('DB_ENGINE', None)
DB_USERNAME = os.getenv('DB_USERNAME', None)
DB_PASS = os.getenv('DB_PASS', None)
DB_HOST = os.getenv('DB_HOST', None)
DB_PORT = os.getenv('DB_PORT', None)
DB_NAME = os.getenv('DB_NAME', None)

DB_URL = os.getenv('DB_URL', None)

if DB_URL:
    DATABASES = {
        'default': dj_database_url.config(default=DB_URL, conn_max_age=600),
    }
elif DB_ENGINE and DB_NAME and DB_USERNAME:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.' + DB_ENGINE,
            'NAME': DB_NAME,
            'USER': DB_USERNAME,
            'PASSWORD': DB_PASS,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
        },
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite3',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Time in seconds to invalidate cached repos
CACHE_INVALIDATE = int(os.getenv('CACHE_INVALIDATE', str(60*60)))


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

# if not DEBUG:
# STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_REDIRECT_URL = '/'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# OAuth Settings
GITHUB_OAUTH_CLIENT_ID = os.getenv("GITHUB_OAUTH_CLIENT_ID")
GITHUB_OAUTH_SECRET = os.getenv("GITHUB_OAUTH_SECRET")
GITHUB_OAUTH_CALLBACK_URL = "callback"  # https://{ALLOWED_HOSTS[0]}/
GITHUB_OAUTH_URL = "https://github.com/login/oauth/authorize"
# https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps
GITHUB_OAUTH_SCOPES = ['repo']
