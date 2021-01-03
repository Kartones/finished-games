import re
from typing import Any, Optional

from core.models import Game, Platform, UserGame, WishlistedUserGame
from dal import autocomplete
from django.db.models.functions import Length, Lower
from django.db.models.query import QuerySet
from web import constants


# see core.models.Game.save() for details
def simplify_query(query: str) -> str:
    return re.sub(r"[^\w\-. ]", "", query.strip()).lower()


class GameAutocompleteView(autocomplete.Select2QuerySetView):
    def get_queryset(self) -> Optional[QuerySet]:
        if not self.q:
            return None

        queryset = Game.objects.all()
        queryset = queryset.filter(name_for_search__contains=simplify_query(self.q))
        queryset = queryset.order_by(Length("name"), Lower("name"))

        return queryset


class PlatformAutocompleteView(autocomplete.Select2QuerySetView):
    def get_result_label(self, item: Platform) -> Any:
        return item.shortname

    def get_selected_result_label(self, item: Platform) -> Any:
        return item.shortname

    def get_queryset(self) -> Optional[QuerySet]:
        # if in the future used from other places, remove the username present requirement
        username = self.forwarded.get("username")
        if not self.q or not username:
            return None

        queryset = Platform.objects.all().filter(shortname__contains=simplify_query(self.q))

        # comes from PlatformFilterform
        filter_type = self.forwarded.get("filter_type", "")

        if filter_type == constants.PLATFORM_FILTER_WISHLISTED:
            queryset = queryset.filter(
                id__in=WishlistedUserGame.objects.filter(user__username=username)
                .values_list("platform__id", flat=True)
                .distinct()
            )
        elif filter_type == constants.PLATFORM_FILTER_FINISHED:
            queryset = queryset.filter(
                id__in=UserGame.objects.filter(user__username=username, year_finished__isnull=False)
                .values_list("platform__id", flat=True)
                .distinct()
            )
        elif filter_type == constants.PLATFORM_FILTER_PENDING:
            queryset = queryset.filter(
                id__in=UserGame.objects.filter(user__username=username)
                .exclude(year_finished__isnull=False)
                .exclude(abandoned=True)
                .values_list("platform__id", flat=True)
                .distinct()
            )
        elif filter_type == constants.PLATFORM_FILTER_ABANDONED:
            queryset = queryset.filter(
                id__in=UserGame.objects.filter(user__username=username, abandoned=True)
                .values_list("platform__id", flat=True)
                .distinct()
            )
        elif filter_type == constants.PLATFORM_FILTER_CURRENTLY_PLAYING:
            queryset = queryset.filter(
                id__in=UserGame.objects.filter(user__username=username, currently_playing=True)
                .values_list("platform__id", flat=True)
                .distinct()
            )

        queryset = queryset.only("id", "shortname").order_by(Length("shortname"), Lower("shortname"))

        return queryset
