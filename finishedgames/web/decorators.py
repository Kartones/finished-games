from typing import (Any, Callable)  # NOQA: F401

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from core.models import WishlistedUserGame


def viewed_user(wrapped_function: Callable) -> Any:
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        kwargs["viewed_user"] = get_object_or_404(get_user_model(), username=kwargs["username"])
        return wrapped_function(request, *args, **kwargs)
    return wrapper


def authenticated_user_wishlisted_games(wrapped_function: Callable) -> Any:
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        # if viewing own profile do not fetch anything
        if request.user.is_authenticated and kwargs["viewed_user"] != request.user:
            authenticated_user_wishlisted_games = [
                item.generic_id for item in WishlistedUserGame.objects
                                                              .filter(user=request.user)
                                                              .select_related("game", "platform")
            ]
        else:
            authenticated_user_wishlisted_games = list()

        kwargs["authenticated_user_wishlisted_games"] = authenticated_user_wishlisted_games
        return wrapped_function(request, *args, **kwargs)
    return wrapper
