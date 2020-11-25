from typing import Any, Optional

from core.models import Game, Platform, WishlistedUserGame
from dal import autocomplete
from django.db.models.functions import Length, Lower
from django.db.models.query import QuerySet


class GameAutocompleteView(autocomplete.Select2QuerySetView):
    def get_queryset(self) -> Optional[QuerySet]:
        if not self.q:
            return None

        queryset = Game.objects.all()
        queryset = queryset.filter(name_for_search__contains=self.q.strip().lower())
        queryset = queryset.order_by(Length("name"), Lower("name"))

        return queryset


class PlatformAutocompleteView(autocomplete.Select2QuerySetView):
    def get_result_label(self, item: Platform) -> Any:
        return item.shortname

    def get_selected_result_label(self, item: Platform) -> Any:
        return item.shortname

    def get_queryset(self) -> Optional[QuerySet]:
        if not self.q:
            return None

        queryset = Platform.objects.all().filter(shortname__contains=self.q.strip().lower())

        # see WishlistedPlatformFilterForm
        if self.forwarded.get("filter_type", "") == "wishlisted":
            username = self.forwarded.get("username", None)
            if username:
                queryset = queryset.filter(
                    id__in=WishlistedUserGame.objects.filter(user__username=username)
                    .values_list("platform__id", flat=True)
                    .distinct()
                )

        queryset = queryset.only("id", "shortname").order_by(Length("shortname"), Lower("shortname"))

        return queryset
