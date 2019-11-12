from datetime import datetime
from typing import Any, Callable, Dict  # NOQA: F401

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Lower
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views import View

from core.managers import CatalogManager
from core.models import Platform, UserGame, WishlistedUserGame
from web import constants
from web.decorators import authenticated_user_games, viewed_user


def _progress_bar_class(progress: int) -> str:
    # Leaving "bad" colors for low thresholds, as in general users will have high % of catalog unfinished
    if progress <= 15:
        return "is-error"
    elif 15 < progress < 35:
        return "is-warning"
    elif 35 < progress < 65:
        return "is-primary"
    else:
        return "is-success"


def users(request: HttpRequest) -> HttpResponse:
    # For security reasons, no superadmins should have normal site profiles
    users = get_user_model().objects.filter(is_active=True, is_superuser=False)
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
        "progress_class": _progress_bar_class(completed_games_progress),
        "wishlisted_games_count": wishlisted_games_count
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


@login_required
def profile(request: HttpRequest, username: str) -> HttpResponse:
    if username != request.user.get_username():
        raise Http404("Invalid URL")

    context = {}  # type: Dict

    return render(request, "user/profile.html", context)


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

        sort_by = request.GET.get("sort_by", constants.SORT_BY_GAME_NAME)
        try:
            order_by = constants.SORT_FIELDS_MAPPING[sort_by]
        except KeyError:
            order_by = constants.SORT_FIELDS_MAPPING[constants.SORT_BY_GAME_NAME]

        user_games = UserGame.objects \
                             .filter(user=viewed_user) \
                             .order_by(*order_by) \
                             .select_related("game", "platform")

        context = {
            "viewed_user": viewed_user,
            "user_games": user_games,
            "user_games_count": len(user_games),
            "constants": constants,
            "sort_by": sort_by,
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
                user=request.user, form_user_id=int(request.POST["user"]), game_id=int(request.POST["game"]),
                platform_id=int(request.POST["platform"])
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
        user_games = UserGame.objects \
                             .filter(user=viewed_user, platform=platform) \
                             .order_by("game__name") \
                             .select_related("game")
        games_count = len(user_games)

        currently_playing_games_count = user_games.filter(currently_playing=True).count()
        finished_games_count = user_games.exclude(year_finished__isnull=True).count()
        abandoned_games_count = user_games.filter(abandoned=True).count()
        completed_games_count = finished_games_count + abandoned_games_count
        if games_count > 0:
            completed_games_progress = int(completed_games_count * 100 / games_count)
        else:
            completed_games_progress = 0

        context = {
            "viewed_user": viewed_user,
            "platform": platform,
            "user_games": user_games,
            "games_count": games_count,
            "currently_playing_games_count": currently_playing_games_count,
            "finished_games_count": finished_games_count,
            "abandoned_games_count": abandoned_games_count,
            "completed_games_count": completed_games_count,
            "completed_games_progress": completed_games_progress,
            "progress_class": _progress_bar_class(completed_games_progress),
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

        sort_by = request.GET.get("sort_by", constants.SORT_BY_GAME_NAME)
        try:
            order_by = constants.SORT_FIELDS_MAPPING[sort_by]
        except KeyError:
            order_by = constants.SORT_FIELDS_MAPPING[constants.SORT_BY_GAME_NAME]

        pending_games = UserGame.objects.filter(user=viewed_user) \
                                        .exclude(year_finished__isnull=False) \
                                        .exclude(abandoned=True) \
                                        .order_by(*order_by) \
                                        .select_related("game", "platform")

        context = {
            "viewed_user": viewed_user,
            "pending_games": pending_games,
            "pending_games_count": len(pending_games),
            "constants": constants,
            "sort_by": sort_by,
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

        sort_by = request.GET.get("sort_by", constants.SORT_BY_GAME_NAME)
        try:
            order_by = constants.SORT_FIELDS_MAPPING[sort_by]
        except KeyError:
            order_by = constants.SORT_FIELDS_MAPPING[constants.SORT_BY_GAME_NAME]

        finished_games = UserGame.objects.filter(user=viewed_user) \
                                         .exclude(year_finished__isnull=True) \
                                         .order_by(*order_by) \
                                         .select_related("game", "platform")

        context = {
            "viewed_user": viewed_user,
            "finished_games": finished_games,
            "finished_games_count": len(finished_games),
            "constants": constants,
            "sort_by": sort_by,
            "authenticated_user_catalog": kwargs["authenticated_user_catalog"],
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
                user=request.user, game_id=int(request.POST["game"]), platform_id=int(request.POST["platform"]),
                year_finished=datetime.now().year
            )

        return HttpResponse(status=204)


class GamesAbandonedView(View):

    @method_decorator(viewed_user)
    @method_decorator(authenticated_user_games)
    def get(self, request: HttpRequest, username: str, *args: Any, **kwargs: Any) -> HttpResponse:
        viewed_user = kwargs["viewed_user"]
        if not viewed_user:
            raise Http404("Invalid URL")

        sort_by = request.GET.get("sort_by", constants.SORT_BY_GAME_NAME)
        try:
            order_by = constants.SORT_FIELDS_MAPPING[sort_by]
        except KeyError:
            order_by = constants.SORT_FIELDS_MAPPING[constants.SORT_BY_GAME_NAME]

        abandoned_Games = UserGame.objects.filter(user=viewed_user) \
                                          .filter(abandoned=True) \
                                          .order_by(*order_by) \
                                          .select_related("game", "platform")

        context = {
            "viewed_user": viewed_user,
            "abandoned_games": abandoned_Games,
            "abandoned_games_count": len(abandoned_Games),
            "constants": constants,
            "sort_by": sort_by,
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

        sort_by = request.GET.get("sort_by", constants.SORT_BY_GAME_NAME)
        try:
            order_by = constants.SORT_FIELDS_MAPPING[sort_by]
        except KeyError:
            order_by = constants.SORT_FIELDS_MAPPING[constants.SORT_BY_GAME_NAME]

        currently_playing_games = UserGame.objects \
                                          .filter(user=viewed_user, currently_playing=True) \
                                          .order_by(*order_by) \
                                          .select_related("game", "platform")

        context = {
            "viewed_user": viewed_user,
            "currently_playing_games": currently_playing_games,
            "currently_playing_games_count": len(currently_playing_games),
            "constants": constants,
            "sort_by": sort_by,
            "authenticated_user_catalog": kwargs["authenticated_user_catalog"],
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

        sort_by = request.GET.get("sort_by", constants.SORT_BY_GAME_NAME)
        try:
            order_by = constants.SORT_FIELDS_MAPPING[sort_by]
        except KeyError:
            order_by = constants.SORT_FIELDS_MAPPING[constants.SORT_BY_GAME_NAME]

        wishlisted_games = WishlistedUserGame.objects \
                                             .filter(user=viewed_user) \
                                             .order_by(*order_by) \
                                             .select_related("game", "platform")

        context = {
            "viewed_user": viewed_user,
            "wishlisted_games": wishlisted_games,
            "wishlisted_games_count": len(wishlisted_games),
            "constants": constants,
            "sort_by": sort_by,
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
                user=request.user, form_user_id=int(request.POST["user"]), game_id=int(request.POST["game"]),
                platform_id=int(request.POST["platform"])
            )

        return HttpResponse(status=204)
