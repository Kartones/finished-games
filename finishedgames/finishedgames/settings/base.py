"""
For more information on this file, see https://docs.djangoproject.com/en/2.1/topics/settings/
For the full list of settings and their values, see https://docs.djangoproject.com/en/2.1/ref/settings/
"""

from typing import Dict  # NOQA: F401
import os


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "[8x6?[zLKSKjp?HVU=WVlOjj$B.6n6JljFtG*nS #Ugu=Wh[?1@vmkMcL8nt#t61*G#0X]ju4-by;s.i;:#M){k*o"

# SECURITY WARNING: don"t run with debug turned on in production!
DEBUG = True

# Enable at dev settings
DJANGO_DEBUG_TOOLBAR_ENABLED = False

ALLOWED_HOSTS = [
    "0.0.0.0",
]

# Application definition

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core.apps.CoreConfig",
    "web.apps.WebConfig",
    "catalogsources.apps.CatalogSourcesConfig",
    "dal",
    "dal_select2",
    # After custom apps to allow for example overriding templates
    "django.contrib.admin",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "finishedgames.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "finishedgames.wsgi.application"


# Database https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "fg-dev.db.sqlite3"),
    }
}


# Password validation https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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

# Internationalization https://docs.djangoproject.com/en/2.1/topics/i18n/
LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images) https://docs.djangoproject.com/en/2.1/howto/static-files/
STATIC_URL = "/static/"
# Static files location for development
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Directory from which you’d serve statics in production
# STATIC_ROOT = "/code/finishedgames/statics/"

# Disable default maximum of GET/POST fields allowed, else massive imports will fail
DATA_UPLOAD_MAX_NUMBER_FIELDS = None

# Custom Finished Games settings

LATEST_VIDEOGAMES_DISPLAY_COUNT = 10
LATEST_PLATFORMS_DISPLAY_COUNT = 5

# Setup adapters at prod settings
CATALOG_SOURCES_ADAPTERS = {}  # type: Dict

# Remember to setup a user agent at prod settings
CATALOG_SOURCES_ADAPTER_USER_AGENT = None

# Until paged load of list items is ready, this controls the maximum games to render with a single query
MAXIMUM_GAMES_PER_PLATFORM_NON_PAGED = 3000
