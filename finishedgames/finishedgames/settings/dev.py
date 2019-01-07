from .base import *  # NOQA: F401, F403

DEBUG = True

# To disable it even in development
DJANGO_DEBUG_TOOLBAR_ENABLED = DEBUG and True

SECRET_KEY = "zc Si,$# SG6ht53iYWWmZ9 nLgZ]n4!ge,qbV=HVo;opAjNSztrGJ@thpe:}#QFtYN{2l.p@#"

if DJANGO_DEBUG_TOOLBAR_ENABLED:
    INSTALLED_APPS += ("debug_toolbar",)  # NOQA: F405

if DJANGO_DEBUG_TOOLBAR_ENABLED:
    MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)  # NOQA: F405

if DJANGO_DEBUG_TOOLBAR_ENABLED:
    INTERNAL_IPS = ['127.0.0.1', '0.0.0.0', '172.18.0.1']  # request.META['REMOTE_ADDR']
    DEBUG_TOOLBAR_PANELS = [
        # 'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        # 'debug_toolbar.panels.cache.CachePanel',
    ]
