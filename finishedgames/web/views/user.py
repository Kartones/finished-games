from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple  # NOQA: F401

from core.managers import CatalogManager
from core.models import Platform, UserGame, WishlistedUserGame
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models.functions import Lower
from django.db.models.query import QuerySet
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views import View
from web import constants
from web.decorators import authenticated_user_games, viewed_user


def progress_bar_class(progress: int) -> str:
    # Leaving "bad" colors for low thresholds, as in general users will have high % of catalog unfinished
    if progress <= 15:
        return "is-error"
    elif 15 < progress < 35:
        return "is-warning"
    elif 35 < progress < 65:
        return "is-primary"
    else:
        return "is-success"


def filter_and_exclude_games(user_games: QuerySet, request: HttpRequest) -> Tuple[QuerySet, str, str]:
    sort_by = request.GET.get("sort_by", constants.SORT_BY_GAME_NAME)
    try:
        order_by = constants.SORT_FIELDS_MAPPING[sort_by]
    except KeyError:
        order_by = constants.SORT_FIELDS_MAPPING[constants.SORT_BY_GAME_NAME]

    exclude = request.GET.get("exclude", None)
    exclude_kwargs = None  # type: Any
    try:
        exclude_kwargs = constants.EXCLUDE_FIELDS_MAPPING[exclude]
    except KeyError:
        exclude = None

    if exclude:
        return user_games.exclude(**exclude_kwargs).order_by(*order_by), sort_by, exclude
    else:
        return user_games.order_by(*order_by), sort_by, ""


def users(request: HttpRequest) -> HttpResponse:
    # For security reasons, no superadmins should have normal site profiles
    users = get_user_model().objects.all()  # .filter(is_active=True, is_superuser=False)

    paginator = Paginator(users, settings.PAGINATION_ITEMS_PER_PAGE)
    page_number = request.GET.get("page", 1)
    users = paginator.get_page(page_number)

    context = {
        "users": users,
    }

    return render(request, "user/users.html", context)


def catalog(request: HttpRequest, username: str) -> HttpResponse:
    viewed_user = get_object_or_404(get_user_model(), username=username)

    all_user_games = UserGame.objects.filter(user=viewed_user)

    user_games = all_user_games.order_by("-id").select_related("game", "platform")
    user_games_count = len(user_games)
    # trying to use ORM's distinct() causes an extra query and always leaves usergame.id
    user_platform_ids = [user_game.platform_id for user_game in user_games]
    user_platform_ids = sorted(set(user_platform_ids))  # remove duplicates
    user_platforms_count = Platform.objects.filter(id__in=user_platform_ids).count()

    currently_playing_games_count = all_user_games.filter(currently_playing=True).count()
    finished_games_count = all_user_games.exclude(year_finished__isnull=True).count()
    abandoned_games_count = all_user_games.filter(abandoned=True).count()
    completed_games_count = finished_games_count + abandoned_games_count
    pending_games_count = user_games_count - completed_games_count
    if user_games_count > 0:
        completed_games_progress = int(completed_games_count * 100 / user_games_count)
    else:
        completed_games_progress = 0
    wishlisted_games_count = WishlistedUserGame.objects.filter(user=viewed_user).count()

    context = {
        "viewed_user": viewed_user,
        "user_games_count": user_games_count,
        "user_platforms_count": user_platforms_count,
        "currently_playing_games_count": currently_playing_games_count,
        "finished_games_count": finished_games_count,
        "completed_games_count": completed_games_count,
        "completed_games_progress": completed_games_progress,
        "pending_games_count": pending_games_count,
        "abandoned_games_count": abandoned_games_count,
        "progress_class": progress_bar_class(completed_games_progress),
        "wishlisted_games_count": wishlisted_games_count,
    }

    return render(request, "user/catalog.html", context)


def platforms(request: HttpRequest, username: str) -> HttpResponse:
    viewed_user = get_object_or_404(get_user_model(), username=username)

    user_games = UserGame.objects.filter(user=viewed_user)
    # trying to use ORM's distinct() causes an extra query and always leaves usergame.id
    user_platform_ids = [user_game.platform_id for user_game in user_games]
    user_platform_ids = sorted(set(user_platform_ids))  # remove duplicates
    user_platforms = Platform.objects.filter(id__in=user_platform_ids).order_by(Lower("name"))

    context = {
        "viewed_user": viewed_user,
        "user_platforms": user_platforms,
        "user_platforms_count": len(user_platforms),
    }

    return render(request, "user/platforms.html", context)


class NoLongerOwnedGamesView(View):
    def post(self, request: HttpRequest, username: str, *args: Any, **kwargs: Any) -> HttpResponse:
        if username != request.user.get_username() or request.method != "POST":
            raise Http404("Invalid URL")

        if request.POST.get("_method") == constants.FORM_METHOD_DELETE:
            CatalogManager.unmark_game_from_no_longer_owned(
                user=request.user, game_id=int(request.POST["game"]), platform_id=int(request.POST["platform"])
            )
        else:
            CatalogManager.mark_game_as_no_longer_owned(
                user=request.user, game_id=int(request.POST["game"]), platform_id=int(request.POST["platform"])
            )

        return HttpResponse(status=204)


class GamesView(View):
    @method_decorator(viewed_user)
    @method_decorator(authenticated_user_games)
    def get(self, request: HttpRequest, username: str, *args: Any, **kwargs: Any) -> HttpResponse:
        viewed_user = kwargs["viewed_user"]
        if not viewed_user:
            raise Http404("Invalid URL")

        user_games, sort_by, exclude = filter_and_exclude_games(UserGame.objects.filter(user=viewed_user), request)
        user_games = user_games.select_related("game", "platform")

        paginator = Paginator(user_games, settings.PAGINATION_ITEMS_PER_PAGE)
        games_count = paginator.count

        currently_playing_games_count = user_games.filter(currently_playing=True).count()
        finished_games_count = user_games.exclude(year_finished__isnull=True).count()
        abandoned_games_count = user_games.filter(abandoned=True).count()
        completed_games_count = finished_games_count + abandoned_games_count
        pending_games_count = games_count - completed_games_count
        if games_count > 0:
            completed_games_progress = int(completed_games_count * 100 / games_count)
        else:
            completed_games_progress = 0

        page_number = request.GET.get("page", 1)
        user_games = paginator.get_page(page_number)

        context = {
            "viewed_user": viewed_user,
            "user_games": user_games,
            "user_games_count": games_count,
            "currently_playing_games_count": currently_playing_games_count,
            "finished_games_count": finished_games_count,
            "abandoned_games_count": abandoned_games_count,
            "completed_games_count": completed_games_count,
            "pending_games_count": pending_games_count,
            "completed_games_progress": completed_games_progress,
            "progress_class": progress_bar_class(completed_games_progress),
            "constants": constants,
            "sort_by": sort_by,
            "exclude": exclude if exclude else "",
            "enabled_statuses": [
                constants.KEY_GAMES_CURRENTLY_PLAYING,
                constants.KEY_GAMES_FINISHED,
                constants.KEY_GAMES_ABANDONED,
                constants.KEY_GAMES_NO_LONGER_OWNED,
            ],
            "enabled_fields": [constants.KEY_FIELD_PLATFORM],
            "authenticated_user_catalog": kwargs["authenticated_user_catalog"],
        }

        return render(request, "user/games.html", context)

    def post(self, request: HttpRequest, username: str, *args: Any, **kwargs: Any) -> HttpResponse:
        if username != request.user.get_username() or request.method != "POST":
            raise Http404("Invalid URL")

        if request.POST.get("_method") == constants.FORM_METHOD_DELETE:
            CatalogManager.remove_game_from_catalog(
                user=request.user, game_id=int(request.POST["game"]), platform_id=int(request.POST["platform"])
            )
        else:
            CatalogManager.add_game_to_catalog(
                user=request.user,
                form_user_id=int(request.POST["user"]),
                game_id=int(request.POST["game"]),
                platform_id=int(request.POST["platform"]),
            )

        return HttpResponse(status=204)


class GamesByPlatformView(View):
    @method_decorator(viewed_user)
    @method_decorator(authenticated_user_games)
    def get(self, request: HttpRequest, username: str, platform_id: int, *args: Any, **kwargs: Any) -> HttpResponse:
        viewed_user = kwargs["viewed_user"]
        if not viewed_user:
            raise Http404("Invalid URL")

        platform = get_object_or_404(Platform, pk=platform_id)
        user_games, sort_by, exclude = filter_and_exclude_games(
            UserGame.objects.filter(user=viewed_user, platform=platform), request
        )
        user_games = user_games.select_related("game")

        paginator = Paginator(user_games, settings.PAGINATION_ITEMS_PER_PAGE)
        games_count = paginator.count

        currently_playing_games_count = user_games.filter(currently_playing=True).count()
        finished_games_count = user_games.exclude(year_finished__isnull=True).count()
        abandoned_games_count = user_games.filter(abandoned=True).count()
        completed_games_count = finished_games_count + abandoned_games_count
        pending_games_count = games_count - completed_games_count
        if games_count > 0:
            completed_games_progress = int(completed_games_count * 100 / games_count)
        else:
            completed_games_progress = 0

        page_number = request.GET.get("page", 1)
        user_games = paginator.get_page(page_number)

        context = {
            "viewed_user": viewed_user,
            "platform": platform,
            "user_games": user_games,
            "games_count": games_count,
            "currently_playing_games_count": currently_playing_games_count,
            "finished_games_count": finished_games_count,
            "abandoned_games_count": abandoned_games_count,
            "completed_games_count": completed_games_count,
            "pending_games_count": pending_games_count,
            "completed_games_progress": completed_games_progress,
            "progress_class": progress_bar_class(completed_games_progress),
            "constants": constants,
            "sort_by": sort_by,
            "exclude": exclude,
            "enabled_statuses": [
                constants.KEY_GAMES_CURRENTLY_PLAYING,
                constants.KEY_GAMES_FINISHED,
                constants.KEY_GAMES_ABANDONED,
                constants.KEY_GAMES_NO_LONGER_OWNED,
            ],
            "enabled_fields": [],
            "authenticated_user_catalog": kwargs["authenticated_user_catalog"],
        }

        return render(request, "user/games_by_platform.html", context)


class GamesPendingView(View):
    @method_decorator(viewed_user)
    @method_decorator(authenticated_user_games)
    def get(self, request: HttpRequest, username: str, *args: Any, **kwargs: Any) -> HttpResponse:
        viewed_user = kwargs["viewed_user"]
        if not viewed_user:
            raise Http404("Invalid URL")

        pending_games, sort_by, exclude = filter_and_exclude_games(
            UserGame.objects.filter(user=viewed_user).exclude(year_finished__isnull=False).exclude(abandoned=True),
            request,
        )
        pending_games = pending_games.select_related("game", "platform")

        paginator = Paginator(pending_games, settings.PAGINATION_ITEMS_PER_PAGE)
        page_number = request.GET.get("page", 1)
        pending_games = paginator.get_page(page_number)

        context = {
            "viewed_user": viewed_user,
            "pending_games": pending_games,
            "pending_games_count": paginator.count,
            "constants": constants,
            "sort_by": sort_by,
            "enabled_statuses": [constants.KEY_GAMES_CURRENTLY_PLAYING, constants.KEY_GAMES_NO_LONGER_OWNED],
            "enabled_fields": [constants.KEY_FIELD_PLATFORM],
            "authenticated_user_catalog": kwargs["authenticated_user_catalog"],
        }

        return render(request, "user/pending_games.html", context)


class GamesFinishedView(View):
    @method_decorator(viewed_user)
    @method_decorator(authenticated_user_games)
    def get(self, request: HttpRequest, username: str, *args: Any, **kwargs: Any) -> HttpResponse:
        viewed_user = kwargs["viewed_user"]
        if not viewed_user:
            raise Http404("Invalid URL")

        finished_games, sort_by, exclude = filter_and_exclude_games(
            UserGame.objects.filter(user=viewed_user).exclude(year_finished__isnull=True), request
        )
        finished_games = finished_games.select_related("game", "platform")

        paginator = Paginator(finished_games, settings.PAGINATION_ITEMS_PER_PAGE)
        page_number = request.GET.get("page", 1)
        finished_games = paginator.get_page(page_number)

        context = {
            "viewed_user": viewed_user,
            "finished_games": finished_games,
            "finished_games_count": paginator.count,
            "constants": constants,
            "sort_by": sort_by,
            "enabled_statuses": [constants.KEY_GAMES_CURRENTLY_PLAYING, constants.KEY_GAMES_NO_LONGER_OWNED],
            "authenticated_user_catalog": kwargs["authenticated_user_catalog"],
            "enabled_fields": [constants.KEY_FIELD_PLATFORM, constants.KEY_FIELD_YEAR],
        }

        return render(request, "user/finished_games.html", context)

    def post(self, request: HttpRequest, username: str, *args: Any, **kwargs: Any) -> HttpResponse:
        if username != request.user.get_username() or request.method != "POST":
            raise Http404("Invalid URL")

        if request.POST.get("_method") == constants.FORM_METHOD_DELETE:
            CatalogManager.unmark_game_from_finished(
                user=request.user, game_id=int(request.POST["game"]), platform_id=int(request.POST["platform"])
            )
        else:
            CatalogManager.mark_game_as_finished(
                user=request.user,
                game_id=int(request.POST["game"]),
                platform_id=int(request.POST["platform"]),
                year_finished=datetime.now().year,
            )

        return HttpResponse(status=204)


class GamesAbandonedView(View):
    @method_decorator(viewed_user)
    @method_decorator(authenticated_user_games)
    def get(self, request: HttpRequest, username: str, *args: Any, **kwargs: Any) -> HttpResponse:
        viewed_user = kwargs["viewed_user"]
        if not viewed_user:
            raise Http404("Invalid URL")

        abandoned_Games, sort_by, exclude = filter_and_exclude_games(
            UserGame.objects.filter(user=viewed_user).filter(abandoned=True), request
        )
        abandoned_Games = abandoned_Games.select_related("game", "platform")

        paginator = Paginator(abandoned_Games, settings.PAGINATION_ITEMS_PER_PAGE)
        page_number = request.GET.get("page", 1)
        abandoned_Games = paginator.get_page(page_number)

        context = {
            "viewed_user": viewed_user,
            "abandoned_games": abandoned_Games,
            "abandoned_games_count": paginator.count,
            "constants": constants,
            "sort_by": sort_by,
            "enabled_fields": [constants.KEY_FIELD_PLATFORM],
            "authenticated_user_catalog": kwargs["authenticated_user_catalog"],
        }

        return render(request, "user/abandoned_games.html", context)

    def post(self, request: HttpRequest, username: str, *args: Any, **kwargs: Any) -> HttpResponse:
        if username != request.user.get_username() or request.method != "POST":
            raise Http404("Invalid URL")

        if request.POST.get("_method") == constants.FORM_METHOD_DELETE:
            CatalogManager.unmark_game_from_abandoned(
                user=request.user, game_id=int(request.POST["game"]), platform_id=int(request.POST["platform"])
            )
        else:
            CatalogManager.mark_game_as_abandoned(
                user=request.user, game_id=int(request.POST["game"]), platform_id=int(request.POST["platform"])
            )

        return HttpResponse(status=204)


class GamesCurrentlyPlayingView(View):
    @method_decorator(viewed_user)
    @method_decorator(authenticated_user_games)
    def get(self, request: HttpRequest, username: str, *args: Any, **kwargs: Any) -> HttpResponse:
        viewed_user = kwargs["viewed_user"]
        if not viewed_user:
            raise Http404("Invalid URL")

        currently_playing_games, sort_by, exclude = filter_and_exclude_games(
            UserGame.objects.filter(user=viewed_user, currently_playing=True), request
        )
        currently_playing_games = currently_playing_games.select_related("game", "platform")

        paginator = Paginator(currently_playing_games, settings.PAGINATION_ITEMS_PER_PAGE)
        page_number = request.GET.get("page", 1)
        currently_playing_games = paginator.get_page(page_number)

        context = {
            "viewed_user": viewed_user,
            "currently_playing_games": currently_playing_games,
            "currently_playing_games_count": paginator.count,
            "constants": constants,
            "sort_by": sort_by,
            "authenticated_user_catalog": kwargs["authenticated_user_catalog"],
            "enabled_statuses": [constants.KEY_GAMES_FINISHED],
            "enabled_fields": [constants.KEY_FIELD_PLATFORM],
        }

        return render(request, "user/currently_playing_games.html", context)

    def post(self, request: HttpRequest, username: str, *args: Any, **kwargs: Any) -> HttpResponse:
        if username != request.user.get_username() or request.method != "POST":
            raise Http404("Invalid URL")

        if request.POST.get("_method") == constants.FORM_METHOD_DELETE:
            CatalogManager.unmark_game_from_currently_playing(
                user=request.user, game_id=int(request.POST["game"]), platform_id=int(request.POST["platform"])
            )
        else:
            CatalogManager.mark_game_as_currently_playing(
                user=request.user, game_id=int(request.POST["game"]), platform_id=int(request.POST["platform"])
            )

        return HttpResponse(status=204)


class GamesWishlistedView(View):
    @method_decorator(viewed_user)
    @method_decorator(authenticated_user_games)
    def get(self, request: HttpRequest, username: str, *args: Any, **kwargs: Any) -> HttpResponse:
        viewed_user = kwargs["viewed_user"]
        if not viewed_user:
            raise Http404("Invalid URL")

        wishlisted_games, sort_by, exclude = filter_and_exclude_games(
            WishlistedUserGame.objects.filter(user=viewed_user), request
        )
        wishlisted_games = wishlisted_games.select_related("game", "platform")

        paginator = Paginator(wishlisted_games, settings.PAGINATION_ITEMS_PER_PAGE)
        page_number = request.GET.get("page", 1)
        wishlisted_games = paginator.get_page(page_number)

        context = {
            "viewed_user": viewed_user,
            "wishlisted_games": wishlisted_games,
            "wishlisted_games_count": paginator.count,
            "constants": constants,
            "sort_by": sort_by,
            "enabled_fields": [constants.KEY_FIELD_PLATFORM],
            "authenticated_user_catalog": kwargs["authenticated_user_catalog"],
        }

        return render(request, "user/wishlisted_games.html", context)

    def post(self, request: HttpRequest, username: str, *args: Any, **kwargs: Any) -> HttpResponse:
        if username != request.user.get_username() or request.method != "POST":
            raise Http404("Invalid URL")

        if request.POST.get("_method") == constants.FORM_METHOD_DELETE:
            CatalogManager.remove_game_from_wishlisted(
                user=request.user, game_id=int(request.POST["game"]), platform_id=int(request.POST["platform"])
            )
        else:
            CatalogManager.mark_game_as_wishlisted(
                user=request.user,
                form_user_id=int(request.POST["user"]),
                game_id=int(request.POST["game"]),
                platform_id=int(request.POST["platform"]),
            )

        return HttpResponse(status=204)
