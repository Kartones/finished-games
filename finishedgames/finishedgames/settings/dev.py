# type: ignore

import os

from .base import *  # NOQA: F401, F403

DEBUG = True

SECRET_KEY = "zc Si,$# SG6ht53iYWWmZ9 nLgZ]n4!ge,qbV=HVo;opAjNSztrGJ@thpe:}#QFtYN{2l.p@#"  # nosec

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


# To mess around with configuration without ever commiting it to the repository (but neither using prod settings)
# NOTE: Should go at the end of the file, to override any dev settings
try:
    from .local import *  # NOQA: F401, F403
except Exception:  # nosec
    pass
