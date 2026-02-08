from django.conf import settings
from django.http import HttpRequest


def app_settings(request: HttpRequest) -> dict:
    """
    Context processor to expose selected settings to all templates.
    """
    return {
        "HIDE_GAMES_BUTTON": settings.HIDE_GAMES_BUTTON,
        "HIDE_PLATFORMS_BUTTON": settings.HIDE_PLATFORMS_BUTTON,
        "HIDE_USERS_BUTTON": settings.HIDE_USERS_BUTTON,
    }
