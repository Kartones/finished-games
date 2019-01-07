from django.http import (HttpResponse, HttpRequest)
from django.shortcuts import (get_object_or_404, render)

from core.models import (Game, Platform)


def game_details(request: HttpRequest, game_id: int) -> HttpResponse:
    game = get_object_or_404(Game.objects.select_related("parent_game"), pk=game_id)

    context = {
        "game": game,
    }
    return render(request, "game_details.html", context)


def games_by_platform(request: HttpRequest, platform_id: int) -> HttpResponse:
    platform = get_object_or_404(Platform, pk=platform_id)
    games = Game.objects \
                .only("id", "name") \
                .filter(platforms__id=platform_id) \
                .order_by("name") \
                .all()
    games_count = len(games)

    context = {
        "platform": platform,
        "games": games,
        "games_count": games_count
    }
    return render(request, "games_by_platform.html", context)


def games(request: HttpRequest) -> HttpResponse:
    games = Game.objects \
                .only("id", "name") \
                .order_by("name") \
                .all()
    games_count = len(games)

    context = {
        "games": games,
        "games_count": games_count
    }
    return render(request, "games.html", context)
