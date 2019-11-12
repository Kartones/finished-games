from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from core.models import Game, Platform


def index(request: HttpRequest) -> HttpResponse:
    games_count = Game.objects.count()
    platforms_count = Platform.objects.count()

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
        "games_count": games_count,
        "platforms_count": platforms_count,
    }
    return render(request, "index.html", context)


def help(request: HttpRequest) -> HttpResponse:
    return render(request, "help.html", {})
