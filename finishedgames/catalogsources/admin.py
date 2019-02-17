from typing import (Generator, Tuple)

from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.utils.translation import ugettext_lazy as _

from catalogsources.models import (FetchedGame, FetchedPlatform)
from core.admin import FGModelAdmin


# Custom admin action
def hide_fetched_items(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet) -> None:
    queryset.update(hidden=True)
hide_fetched_items.short_description = "Mark selected items as hidden"  # type:ignore # NOQA: E305


# By default, hidden items won't show
class HiddenByDefaultFilter(admin.SimpleListFilter):
    title = "Hidden"
    parameter_name = "hidden"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> Tuple:
        return (
            ("all", _("All")),
            (None, _("False")),
            ("True", _("True")),
        )

    # Replace default filter choices by ours
    def choices(self, changelist: ChangeList) -> Generator:
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == lookup,
                "query_string": changelist.get_query_string({self.parameter_name: lookup}, []),
                "display": title,
            }

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        if self.value() in (None, "False"):
            return queryset.filter(hidden=False)
        elif self.value() == "True":
            return queryset.filter(hidden=True)


class FetchedGameAdmin(FGModelAdmin):
    list_display = [
        "name", "dlc_or_expansion", "parent_game", "publish_date", "source_id", "last_modified_date", "last_fetch_date",
        "hidden"
    ]
    list_filter = [HiddenByDefaultFilter, "source_id", "dlc_or_expansion", "platforms"]
    search_fields = ["name"]
    readonly_fields = ["last_modified_date", "last_fetch_date", "change_hash"]
    ordering = ["-last_modified_date", "source_id", "name"]
    actions = [hide_fetched_items]


class FetchedPlatformAdmin(FGModelAdmin):
    list_display = ["name", "shortname", "publish_date", "source_id", "last_modified_date", "last_fetch_date", "hidden"]
    list_filter = [HiddenByDefaultFilter, "source_id", "name"]
    search_fields = ["name"]
    readonly_fields = ["last_modified_date", "last_fetch_date", "change_hash"]
    ordering = ["-last_modified_date", "source_id", "name"]
    actions = [hide_fetched_items]


admin.site.register(FetchedGame, FetchedGameAdmin)
admin.site.register(FetchedPlatform, FetchedPlatformAdmin)
