"""
For more information on this file, see https://docs.djangoproject.com/en/2.2/topics/settings/
For the full list of settings and their values, see https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
from typing import Dict  # NOQA: F401

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "[8x6?[zLKSKjp?HVU=WVlOjj$B.6n6JljFtG*nS #Ugu=Wh[?1@vmkMcL8nt#t61*G#0X]ju4-by;s.i;:#M){k*o"  # nosec

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Enable at dev settings
DJANGO_DEBUG_TOOLBAR_ENABLED = False

ALLOWED_HOSTS = [
    "0.0.0.0",  # nosec
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


# Database https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.path.join(BASE_DIR, "fg-dev.db.sqlite3")}}


# Password validation https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization https://docs.djangoproject.com/en/2.2/topics/i18n/
LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images) https://docs.djangoproject.com/en/2.2/howto/static-files/
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

PAGINATION_ITEMS_PER_PAGE = 100

# Generic external sources of game info to render as buttons at game details page.
# Format: (display_name, full_url_containing_placeholder_for_game_name, optional_platform_id_filter)
# List order == button order
EXTRA_GAME_INFO_BUTTONS = [
    ("HowLongToBeat", "https://howlongtobeat.com/?q={}#search", None),
    ("GameFAQs", "https://gamefaqs.gamespot.com/search?game={}", None),
]
