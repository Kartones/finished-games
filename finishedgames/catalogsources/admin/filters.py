from typing import Generator, Tuple

from catalogsources.models import FetchedPlatform
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.db.models import F
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.utils.translation import ugettext_lazy as _


# Don't show platforms which are hidden, and filter by source_id if one chosen
class CustomPlatformsFilter(admin.SimpleListFilter):
    title = "fetched platforms"
    parameter_name = "platforms"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> Tuple:
        source_id = request.GET.get("source_id")
        queryset = FetchedPlatform.objects.filter(hidden=False)
        if source_id:
            queryset = queryset.filter(source_id=source_id)
            return tuple((platform.id, platform.name) for platform in queryset)
        else:
            return tuple((platform.id, "{} [{}]".format(platform.name, platform.source_id)) for platform in queryset)

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        if self.value():
            queryset = queryset.filter(platforms__id=self.value())
        return queryset


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
        if self.value() == "all":
            return queryset.filter(hidden__in=[True, False])
        if self.value() in (None, "False"):
            return queryset.filter(hidden=False)
        elif self.value() == "True":
            return queryset.filter(hidden=True)


class SyncedFetchedGames(admin.SimpleListFilter):
    title = "Synced"
    parameter_name = "is_sync"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> Tuple:
        return (
            (None, _("All")),
            ("True", _("True")),
            ("False", _("False")),
        )

    def choices(self, changelist: ChangeList) -> Generator:
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == lookup,
                "query_string": changelist.get_query_string({self.parameter_name: lookup}, []),
                "display": title,
            }

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        if self.value() == "True":
            return queryset.exclude(fg_game__isnull=True).filter(last_sync_date=F("last_modified_date"))
        elif self.value() == "False":
            return queryset.exclude(last_sync_date=F("last_modified_date"))


class NotImportedFetchedGames(admin.SimpleListFilter):
    title = "Not imported"
    parameter_name = "fg_game"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> Tuple:
        return (
            (None, _("All")),
            ("True", _("True")),
            ("False", _("False")),
        )

    def choices(self, changelist: ChangeList) -> Generator:
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == lookup,
                "query_string": changelist.get_query_string({self.parameter_name: lookup}, []),
                "display": title,
            }

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        if self.value() == "True":
            return queryset.filter(fg_game__isnull=True)
        elif self.value() == "False":
            return queryset.filter(fg_game__isnull=False)


class NotImportedFetchedPlatforms(admin.SimpleListFilter):
    title = "Not imported"
    parameter_name = "fg_platform"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> Tuple:
        return (
            (None, _("All")),
            ("True", _("True")),
            ("False", _("False")),
        )

    def choices(self, changelist: ChangeList) -> Generator:
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == lookup,
                "query_string": changelist.get_query_string({self.parameter_name: lookup}, []),
                "display": title,
            }

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        if self.value() == "True":
            return queryset.filter(fg_platform__isnull=True)
        elif self.value() == "False":
            return queryset.filter(fg_platform__isnull=False)
