# type: ignore

import os

from .base import *  # NOQA: F401, F403

# To mess around with configuration without ever commiting it to the repository (but neither using prod settings)
try:
    from .local import *  # NOQA: F401, F403
except Exception:  # nosec
    pass

DEBUG = True

# To disable it even in development
DJANGO_DEBUG_TOOLBAR_ENABLED = DEBUG and True

SECRET_KEY = "zc Si,$# SG6ht53iYWWmZ9 nLgZ]n4!ge,qbV=HVo;opAjNSztrGJ@thpe:}#QFtYN{2l.p@#"  # nosec

if DJANGO_DEBUG_TOOLBAR_ENABLED:
    INSTALLED_APPS += ("debug_toolbar",)  # NOQA: F405

if DJANGO_DEBUG_TOOLBAR_ENABLED:
    MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)  # NOQA: F405

if DJANGO_DEBUG_TOOLBAR_ENABLED:
    # request.META['REMOTE_ADDR']
    INTERNAL_IPS = ["127.0.0.1", "0.0.0.0", "172.18.0.1"]  # nosec
    DEBUG_TOOLBAR_PANELS = [
        # 'debug_toolbar.panels.timer.TimerPanel',
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        # 'debug_toolbar.panels.cache.CachePanel',
    ]

# Static files location for development
STATICFILES_DIRS = [
    #  serve first from 'static' (CSS, JS, etc.)
    os.path.join(BASE_DIR, "static"),  # NOQA: F405
    # but for example cover images from 'statics'
    os.path.join(BASE_DIR, "statics"),  # NOQA: F405
]

EXTRA_GAME_INFO_BUTTONS += [  # NOQA: F405
    ("PCGamingWiki", "https://www.pcgamingwiki.com/w/index.php?search={}&title=Special%3ASearch", 10),
]
