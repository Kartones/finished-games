from django.conf import settings
from django.http import (HttpResponse, HttpRequest)
from django.shortcuts import render

from core.models import (Game, Platform)


def index(request: HttpRequest) -> HttpResponse:
    latest_added_games = Game.objects \
                             .only("id", "name", "platforms") \
                             .prefetch_related("platforms") \
                             .order_by("-id")[:settings.LATEST_VIDEOGAMES_DISPLAY_COUNT]

    latest_added_platforms = Platform.objects \
                                     .only("id", "name") \
                                     .order_by("-id")[:settings.LATEST_PLATFORMS_DISPLAY_COUNT]

    context = {
        "latest_added_games": latest_added_games,
        "latest_added_platforms": latest_added_platforms,
    }
    return render(request, "index.html", context)


def help(request: HttpRequest) -> HttpResponse:
    return render(request, "help.html", {})
