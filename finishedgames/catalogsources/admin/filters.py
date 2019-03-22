from typing import (Generator, Tuple)

from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.utils.translation import ugettext_lazy as _

from catalogsources.models import FetchedPlatform


# Don't show platforms which are hidden, and filter by source_id if one chosen
class CustomPlatformsFilter(admin.SimpleListFilter):
    title = "fetched platforms"
    parameter_name = "platforms"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> Tuple:
        source_id = request.GET.get("source_id")
        queryset = FetchedPlatform.objects.filter(hidden=False)
        if source_id:
            queryset = queryset.filter(source_id=source_id)
            return (
                tuple((platform.id, platform.name) for platform in queryset)
            )
        else:
            return (
                tuple((platform.id, "{} [{}]".format(platform.name, platform.source_id)) for platform in queryset)
            )

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
