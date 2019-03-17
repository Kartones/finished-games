from typing import (Any, cast, Generator, List, Optional, Tuple)

from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.db.models.fields import Field
from django.db.models.functions import Lower
from django.db.models.query import QuerySet
from django.http import (HttpRequest, HttpResponseRedirect)
from django.forms import ModelForm
from django.forms.fields import Field as Form_Field
from django.template.response import TemplateResponse
from django.urls import (path, reverse)
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from catalogsources.apps import CatalogSourcesConfig
from catalogsources.managers import (GameImportSaveError, ImportManager, PlatformImportSaveError)
from catalogsources.models import (FetchedGame, FetchedPlatform)
from core.admin import FGModelAdmin
from core.models import (Game, Platform)


# Custom admin action
def hide_fetched_items(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet) -> None:
    queryset.update(hidden=True)
hide_fetched_items.short_description = "Hide selected items"  # type:ignore # NOQA: E305


# Custom admin action
def import_fetched_items(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
) -> HttpResponseRedirect:
    selected_ids = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("import_setup/?ids={}".format(",".join(selected_ids)))
import_fetched_items.short_description = "Import selected items into catalog"  # type:ignore # NOQA: E305


# Decorator to render source urls as hyperlinks on the listing pages
def hyperlink_source_url(model_instance: FGModelAdmin) -> str:
    return cast(str, format_html("<a href='{url}' target='_blank'>{url}</a>", url=model_instance.source_url))
hyperlink_source_url.short_description = "Source URL"  # type:ignore # NOQA: E305


# Don't show platforms which are hidden, and filter by source id if chosen
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
        return queryset.filter(hidden=False)


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
        "name", "dlc_or_expansion", "fg_game", hyperlink_source_url, "last_modified_date", "source_id", "hidden"
    ]
    list_filter = ["last_modified_date", HiddenByDefaultFilter, "source_id", CustomPlatformsFilter, "dlc_or_expansion"]
    search_fields = ["name"]
    readonly_fields = ["last_modified_date", "change_hash"]
    ordering = ["-last_modified_date", "source_id", "name"]
    actions = [hide_fetched_items, import_fetched_items]

    def get_form(self, request: HttpRequest, obj: Optional[FetchedGame] = None, **kwargs: Any) -> ModelForm:
        # just save obj reference for future processing in Inline
        request._current_object = obj
        return super().get_form(request, obj, **kwargs)

    # When rendering the platforms list of the fetched game, do some custom filtering
    def formfield_for_manytomany(self, db_field: Field, request: HttpRequest, **kwargs: Any) -> Form_Field:
        if db_field.name == "platforms":
            # Hidden platforms out (un-hide first if want to use)
            kwargs["queryset"] = FetchedPlatform.objects.filter(hidden=False)
            # Only from same source
            if request._current_object:
                kwargs["queryset"] = kwargs["queryset"].filter(source_id=request._current_object.source_id)
            kwargs["queryset"] = kwargs["queryset"].order_by("name")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field: Field, request: HttpRequest, **kwargs: Any) -> Form_Field:
        if db_field.name == "parent_game":
            # Hidden games out
            kwargs["queryset"] = FetchedGame.objects.filter(hidden=False)
            # Only from same source
            if request._current_object:
                kwargs["queryset"] = kwargs["queryset"].filter(source_id=request._current_object.source_id)
            kwargs["queryset"] = kwargs["queryset"].order_by(Lower("name"))
        elif db_field.name == "fg_game":
            kwargs["queryset"] = Game.objects.order_by(Lower("name"))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_urls(self) -> List[str]:
        urls = super().get_urls()
        my_urls = [
            path("import_setup/", self.admin_site.admin_view(self.import_setup_view), name="game_import_setup"),
            path("import/", self.admin_site.admin_view(self.import_view), name="game_import")
        ]
        return cast(List[str], my_urls + urls)

    def import_setup_view(self, request: HttpRequest) -> TemplateResponse:
        context = self.admin_site.each_context(request)
        context.update({
            "title": "Import fetched game into main catalog",
            "opts": {
                # TODO: improve breadcrumbs
                "app_label": CatalogSourcesConfig.name,
                "app_config": {
                    "verbose_name": CatalogSourcesConfig.name.capitalize
                },
            },
            "model_class_name": FetchedGame.__name__,
        })

        selected_ids = list(map(int, request.GET["ids"].split(",")))
        if len(selected_ids) != 1:
            self.message_user(request, "This action currently only supports acting upon a single entity", level="error")
            return TemplateResponse(request, "game_import.html", context)

        fetched_game = FetchedGame.objects.get(id=selected_ids[0])

        games = Game.objects.only("id", "name").order_by(Lower("name"))
        platforms = Platform.objects.only("id", "name").all()

        context.update({
            "fetched_game": fetched_game,
            "fg_plaform_ids": ",".join([
                str(platform.fg_platform.id) for platform in fetched_game.platforms.all() if platform.fg_platform
            ]),
            "games_for_selectbox": games,
            "platforms_for_selectbox": platforms,
            "existing_parent_game_id": "",
            "existing_platform_ids": "",
            "existing_platform_ids_list": [],
        })

        if fetched_game.fg_game:
            platforms_list = [platform.id for platform in fetched_game.fg_game.platforms.all()]
            context.update({
                "existing_parent_game_id": "",
                "existing_platform_ids": ",".join([str(platform_id) for platform_id in platforms_list]),
                "existing_platform_ids_list": platforms_list,
            })
            if fetched_game.fg_game.parent_game:
                context.update({
                    "existing_parent_game_id": fetched_game.fg_game.parent_game.id,
                })

        return TemplateResponse(request, "game_import.html", context)

    def import_view(self, request: HttpRequest) -> HttpResponseRedirect:
        name = request.POST["name"]
        try:
            ImportManager.import_fetched_game(
                name=name,
                publish_date_string=request.POST["publish_date"],
                dlc_or_expansion=(request.POST.get("dlc_or_expansion") is not None),
                platforms=request.POST.getlist("platforms"),
                fg_game_id=request.POST["fetched_game_id"],
                game_id=request.POST["id"],
                parent_game_id=request.POST["parent_game"]
            )
        except GameImportSaveError as error:
            self.message_user(request, "Error importing Fetched Game '{}': {}".format(name, error), level="error")
            return HttpResponseRedirect(reverse("admin:catalogsources_fetchedgame_changelist"))

        self.message_user(request, "Fetched Game {} imported successfully".format(name))
        return HttpResponseRedirect(reverse("admin:catalogsources_fetchedgame_changelist"))


class FetchedPlatformAdmin(FGModelAdmin):
    list_display = ["name", "fg_platform", hyperlink_source_url, "last_modified_date", "source_id", "hidden"]
    list_filter = ["last_modified_date", HiddenByDefaultFilter, "source_id"]
    search_fields = ["name"]
    readonly_fields = ["last_modified_date", "change_hash"]
    ordering = ["-last_modified_date", "source_id", "name"]
    actions = [hide_fetched_items, import_fetched_items]

    def get_urls(self) -> List[str]:
        urls = super().get_urls()
        my_urls = [
            path("import_setup/", self.admin_site.admin_view(self.import_setup_view), name="platform_import_setup"),
            path("import/", self.admin_site.admin_view(self.import_view), name="platform_import")
        ]
        return cast(List[str], my_urls + urls)

    def import_setup_view(self, request: HttpRequest) -> TemplateResponse:
        context = self.admin_site.each_context(request)
        context.update({
            "title": "Import fetched platform into main catalog",
            # TODO: improve breadcrumbs
            "opts": {
                "app_label": CatalogSourcesConfig.name,
                "app_config": {
                    "verbose_name": CatalogSourcesConfig.name.capitalize
                },
            },
            "model_class_name": FetchedPlatform.__name__,
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

    def import_view(self, request: HttpRequest) -> HttpResponseRedirect:
        name = request.POST["name"]
        try:
            ImportManager.import_fetched_platform(
                name=name,
                shortname=request.POST["shortname"],
                publish_date_string=request.POST["publish_date"],
                fg_platform_id=request.POST["fetched_platform_id"],
                platform_id=request.POST["id"]
            )
        except PlatformImportSaveError as error:
            self.message_user(request, "Error importing Fetched Platform '{}': {}".format(name, error), level="error")
            return HttpResponseRedirect(reverse("admin:catalogsources_fetchedplatform_changelist"))

        self.message_user(request, "Fetched Platform '{}' imported successfully".format(name))
        return HttpResponseRedirect(reverse("admin:catalogsources_fetchedplatform_changelist"))


admin.site.register(FetchedGame, FetchedGameAdmin)
admin.site.register(FetchedPlatform, FetchedPlatformAdmin)
