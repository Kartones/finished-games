from django.db.models.functions import Lower
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from core.models import Game, Platform


def platform_details(request: HttpRequest, platform_id: int) -> HttpResponse:
    platform = get_object_or_404(Platform, pk=platform_id)
    platform_games_count = Game.objects.filter(platforms__id=platform_id).count()

    context = {
        "platform": platform,
        "platform_games_count": platform_games_count
    }
    return render(request, "platform_details.html", context)


def platforms(request: HttpRequest) -> HttpResponse:
    platforms = Platform.objects \
                        .only("id", "name") \
                        .order_by(Lower("name")) \
                        .all()
    platforms_count = len(platforms)

    context = {
        "platforms": platforms,
        "platforms_count": platforms_count
    }
    return render(request, "platforms.html", context)
