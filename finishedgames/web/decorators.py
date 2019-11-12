from typing import Any, Callable

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from core.models import UserGame, WishlistedUserGame
from web import constants


def viewed_user(wrapped_function: Callable) -> Any:
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        if "username" in kwargs:
            kwargs["viewed_user"] = get_object_or_404(get_user_model(), username=kwargs["username"])
        else:
            kwargs["viewed_user"] = None
        return wrapped_function(request, *args, **kwargs)
    return wrapper


def authenticated_user_games(wrapped_function: Callable) -> Any:
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        if request.user.is_authenticated:
            user_games = UserGame.objects \
                                 .filter(user=request.user) \
                                 .select_related("game", "platform")
            wishlisted_games = [
                item.generic_id for item in WishlistedUserGame.objects
                                                              .filter(user=request.user)
                                                              .select_related("game", "platform")
            ]
        else:
            user_games = list()
            wishlisted_games = list()

        games = list()
        currently_playing_games = list()
        finished_games = list()
        no_longer_owned_games = list()
        abandoned_games = list()

        for item in user_games:
            games.append(item.generic_id)
            if item.currently_playing:
                currently_playing_games.append(item.generic_id)
            if item.finished():
                finished_games.append(item.generic_id)
            if item.no_longer_owned:
                no_longer_owned_games.append(item.generic_id)
            if item.abandoned:
                abandoned_games.append(item.generic_id)

        kwargs["authenticated_user_catalog"] = {
            constants.KEY_GAMES: games,
            constants.KEY_GAMES_WISHLISTED: wishlisted_games,
            constants.KEY_GAMES_CURRENTLY_PLAYING: currently_playing_games,
            constants.KEY_GAMES_FINISHED: finished_games,
            constants.KEY_GAMES_NO_LONGER_OWNED: no_longer_owned_games,
            constants.KEY_GAMES_ABANDONED: abandoned_games,
        }
        return wrapped_function(request, *args, **kwargs)
    return wrapper
