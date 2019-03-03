from typing import (Any, cast, Generator, List, Optional, Tuple)

from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.db.models.fields import Field
from django.db.models.query import QuerySet
from django.http import (HttpRequest, HttpResponseRedirect)
from django.forms import ModelForm
from django.forms.fields import Field as Form_Field
from django.template.response import TemplateResponse
from django.urls import (path, reverse)
from django.utils.translation import ugettext_lazy as _

from catalogsources.apps import CatalogSourcesConfig
from catalogsources.models import (FetchedGame, FetchedPlatform)
from core.admin import FGModelAdmin
from core.models import Platform


# Custom admin action
def hide_fetched_items(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet) -> None:
    queryset.update(hidden=True)
hide_fetched_items.short_description = "Mark selected items as hidden"  # type:ignore # NOQA: E305


# Custom admin action
def import_fetched_items(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
) -> HttpResponseRedirect:
    selected_ids = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("import_setup/?ids={}".format(",".join(selected_ids)))
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
        "name", "dlc_or_expansion", "parent_game", "publish_date", "source_id", "last_modified_date", "hidden"
    ]
    list_filter = [HiddenByDefaultFilter, "source_id", "dlc_or_expansion", "platforms"]
    search_fields = ["name"]
    readonly_fields = ["last_modified_date", "change_hash"]
    ordering = ["-last_modified_date", "source_id", "name"]
    actions = [hide_fetched_items, import_fetched_items]

    def get_form(self, request: HttpRequest, obj: Optional[FetchedGame] = None, **kwargs: Any) -> ModelForm:
        # just save obj reference for future processing in Inline
        request._obj_ = obj
        return super().get_form(request, obj, **kwargs)

    # When rendering the platforms list of the fetched game, do some custom filtering
    def formfield_for_manytomany(self, db_field: Field, request: HttpRequest, **kwargs: Any) -> Form_Field:
        if db_field.name == "platforms":
            # Hidden platforms out (un-hide first if want to use)
            kwargs["queryset"] = FetchedPlatform.objects.filter(hidden=False)
            # Only from same source
            if request._obj_:
                kwargs["queryset"] = kwargs["queryset"].filter(source_id=request._obj_.source_id)
            kwargs["queryset"] = kwargs["queryset"].order_by("name")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_urls(self) -> List[str]:
        urls = super().get_urls()
        my_urls = [
            path("import_setup/", self.admin_site.admin_view(self.import_setup_view)),
        ]
        return cast(List[str], my_urls + urls)

    def import_setup_view(self, request: HttpRequest) -> TemplateResponse:
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
    list_display = ["name", "fg_platform", "publish_date", "last_modified_date", "source_id", "hidden"]
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
        if request.POST["id"]:
            platform = Platform.objects \
                               .filter(id=request.POST["id"]) \
                               .get()
        else:
            platform = Platform()

        platform.name = request.POST["name"]
        platform.shortname = request.POST["shortname"]
        platform.publish_date = request.POST["publish_date"]
        try:
            platform.save()
        except Exception as error:
            self.message_user(request, "Error importing Fetched Platform: {}".format(error), level="error")
            return HttpResponseRedirect(reverse("admin:catalogsources_fetchedplatform_changelist"))

        # Update always linked platform
        fetched_platform = FetchedPlatform.objects \
                                          .filter(id=request.POST["fetched_platform_id"]) \
                                          .get()
        fetched_platform.fg_platform_id = platform.id
        fetched_platform.save(update_fields=["fg_platform_id"])

        self.message_user(request, "Fetched Platform imported successfully")
        return HttpResponseRedirect(reverse("admin:catalogsources_fetchedplatform_changelist"))


admin.site.register(FetchedGame, FetchedGameAdmin)
admin.site.register(FetchedPlatform, FetchedPlatformAdmin)
