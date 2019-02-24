from typing import (cast, Generator, List, Tuple)

from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.db.models.query import QuerySet
from django.http import (HttpRequest, HttpResponseRedirect)
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.translation import ugettext_lazy as _

from catalogsources.apps import CatalogSourcesConfig
from catalogsources.models import (FetchedGame, FetchedPlatform)
from core.admin import FGModelAdmin


# Custom admin action
def hide_fetched_items(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet) -> None:
    queryset.update(hidden=True)
hide_fetched_items.short_description = "Mark selected items as hidden"  # type:ignore # NOQA: E305


# Custom admin action
def import_fetched_items(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
) -> HttpResponseRedirect:
    selected_ids = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("import/?ids={}".format(",".join(selected_ids)))
import_fetched_items.short_description = "Import selected items into catalog"  # type:ignore # NOQA: E305


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
    actions = [hide_fetched_items, import_fetched_items]

    def get_urls(self) -> List[str]:
        urls = super().get_urls()
        my_urls = [
            path("import/", self.admin_site.admin_view(self.import_view)),
        ]
        return cast(List[str], my_urls + urls)

    def import_view(self, request: HttpRequest) -> TemplateResponse:
        context = self.admin_site.each_context(request)
        context.update({
            "title": "Import Game into main catalog",
            "opts": {
                # TODO: improve breadcrumbs
                "app_label": CatalogSourcesConfig.name,
                "app_config": {
                    "verbose_name": CatalogSourcesConfig.name.capitalize
                },
            },
        })
        return TemplateResponse(request, "game_import.html", context)


class FetchedPlatformAdmin(FGModelAdmin):
    list_display = ["name", "shortname", "publish_date", "source_id", "last_modified_date", "last_fetch_date", "hidden"]
    list_filter = ["last_modified_date", HiddenByDefaultFilter, "source_id", "name"]
    search_fields = ["name"]
    readonly_fields = ["last_modified_date", "last_fetch_date", "change_hash"]
    ordering = ["-last_modified_date", "source_id", "name"]
    actions = [hide_fetched_items, import_fetched_items]

    def get_urls(self) -> List[str]:
        urls = super().get_urls()
        my_urls = [
            path("import/", self.admin_site.admin_view(self.import_view)),
        ]
        return cast(List[str], my_urls + urls)

    def import_view(self, request: HttpRequest) -> TemplateResponse:
        context = self.admin_site.each_context(request)
        context.update({
            "title": "Import Platform into main catalog",
            "opts": {
                # TODO: improve breadcrumbs
                "app_label": CatalogSourcesConfig.name,
                "app_config": {
                    "verbose_name": CatalogSourcesConfig.name.capitalize
                },
            },
        })

        selected_ids = list(map(int, request.GET["ids"].split(",")))
        if len(selected_ids) != 1:
            self.message_user(request, "This action currently only supports acting upon a single entity", level="error")
            return TemplateResponse(request, "platform_import.html", context)

        fetched_platform = FetchedPlatform.objects.get(id=selected_ids[0])
        context.update({
            "fetched_platform": fetched_platform
        })

        return TemplateResponse(request, "platform_import.html", context)


admin.site.register(FetchedGame, FetchedGameAdmin)
admin.site.register(FetchedPlatform, FetchedPlatformAdmin)
