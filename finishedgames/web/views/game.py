import string
from typing import Any

from core.models import Game, Platform
from django.conf import settings
from django.db.models.functions import Lower
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from web import constants
from web.decorators import authenticated_user_games
from web.forms import GameSearchForm


class GameDetailsView(View):
    @method_decorator(authenticated_user_games)
    def get(self, request: HttpRequest, game_id: int, *args: Any, **kwargs: Any) -> HttpResponse:
        game = get_object_or_404(Game.objects.select_related("parent_game"), pk=game_id)

        context = {
            "game": game,
            "authenticated_user_catalog": kwargs["authenticated_user_catalog"],
        }
        return render(request, "game_details.html", context)


class GamesByPlatformView(View):
    @method_decorator(authenticated_user_games)
    def get(self, request: HttpRequest, platform_id: int, *args: Any, **kwargs: Any) -> HttpResponse:
        platform = get_object_or_404(Platform, pk=platform_id)

        games_count = Game.objects.filter(platforms__id=platform_id).count()

        if games_count > settings.MAXIMUM_GAMES_PER_PLATFORM_NON_PAGED:
            context = {
                "platform": platform,
                "games_count": games_count,
                "cant_display_so_many_games": True,
            }
        else:
            games = Game.objects.only("id", "name").filter(platforms__id=platform_id).order_by(Lower("name")).all()

            context = {
                "platform": platform,
                "games": games,
                "games_count": games_count,
                "authenticated_user_catalog": kwargs["authenticated_user_catalog"],
            }

        return render(request, "games_by_platform.html", context)


def games(request: HttpRequest) -> HttpResponse:
    game_search_form = GameSearchForm()

    context = {
        "letters": list(string.ascii_lowercase),
        "digits": list(string.digits),
        "non_alphanumeric_constant": constants.CHARACTER_FILTER_NON_ALPHANUMERIC,
        "game_search_form": game_search_form,
    }
    return render(request, "games.html", context)


class GameSearch(View):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        game_search_form = GameSearchForm(request.GET)
        if game_search_form.is_valid():
            return HttpResponseRedirect(reverse("game_details", args=[game_search_form.cleaned_data["game"].id]))
        else:
            return HttpResponseRedirect(reverse("games"))


class GamesStartingWithCharacterView(View):
    def get(self, request: HttpRequest, character: str, *args: Any, **kwargs: Any) -> HttpResponse:
        character = character.lower()
        if not any(
            [
                character in string.ascii_lowercase,
                character in string.digits,
                character == constants.CHARACTER_FILTER_NON_ALPHANUMERIC,
            ]
        ):
            return HttpResponseRedirect(reverse("games"))

        if character != constants.CHARACTER_FILTER_NON_ALPHANUMERIC:
            games = Game.objects.only("id", "name").filter(name__istartswith=character).order_by(Lower("name"))
        else:
            all_games = Game.objects.only("id", "name").order_by(Lower("name")).all()
            # Non-optimal but ORM doesn't easily supports substring operations to build a complex filter
            # This will have more values as games starting with other non-alphanumeric appear in the main catalog
            games = [game for game in all_games if game.name.startswith(".")]

        games_count = len(games)

        context = {
            "character": character,
            "games": games,
            "games_count": games_count,
            "non_alphanumeric_constant": constants.CHARACTER_FILTER_NON_ALPHANUMERIC,
        }
        return render(request, "games_filtered_by_starting_character.html", context)
