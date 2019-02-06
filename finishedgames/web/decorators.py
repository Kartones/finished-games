from typing import (Any, Callable)

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from core.models import (UserGame, WishlistedUserGame)

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
            authenticated_user_wishlisted_games = [
                item.generic_id for item in WishlistedUserGame.objects
                                                              .filter(user=request.user)
                                                              .select_related("game", "platform")
            ]
        else:
            user_games = list()
            authenticated_user_wishlisted_games = list()

        authenticated_user_games = [item.generic_id for item in user_games]
        authenticated_user_currently_playing_games = [item.generic_id for item in user_games if item.currently_playing]
        authenticated_user_finished_games = [item.generic_id for item in user_games if item.finished()]
        authenticated_user_no_longer_owned_games = [item.generic_id for item in user_games if item.no_longer_owned]

        print(authenticated_user_finished_games)

        kwargs["authenticated_user_catalog"] = {
            constants.KEY_GAMES: authenticated_user_games,
            constants.KEY_GAMES_WISHLISTED: authenticated_user_wishlisted_games,
            constants.KEY_GAMES_CURRENTLY_PLAYING: authenticated_user_currently_playing_games,
            constants.KEY_GAMES_FINISHED: authenticated_user_finished_games,
            constants.KEY_GAMES_NO_LONGER_OWNED: authenticated_user_no_longer_owned_games,
        }
        return wrapped_function(request, *args, **kwargs)
    return wrapper
