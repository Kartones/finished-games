from typing import (Any, cast, List, Optional)

from django.conf import settings
from django.db.models.fields import Field
from django.db.models.functions import Lower
from django.http import (HttpRequest, HttpResponseRedirect)
from django.forms import ModelForm
from django.forms.fields import Field as Form_Field
from django.template.response import TemplateResponse
from django.urls import (path, reverse)

from catalogsources.admin.actions import (hide_fetched_items, import_fetched_items)
from catalogsources.admin.decorators import (hyperlink_fg_game, hyperlink_fg_platform, hyperlink_source_url)
from catalogsources.admin.filters import (CustomPlatformsFilter, HiddenByDefaultFilter)
from catalogsources.apps import CatalogSourcesConfig
from catalogsources.managers import (GameImportSaveError, ImportManager, PlatformImportSaveError)
from catalogsources.models import (FetchedGame, FetchedPlatform)
from core.admin import FGModelAdmin
from core.models import (Game, Platform)
from finishedgames import constants


class FetchedGameAdmin(FGModelAdmin):
    list_display = [
        "name", "dlc_or_expansion", "fg_game", hyperlink_fg_game, hyperlink_source_url, "last_modified_date",
        "source_id", "hidden"
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
            kwargs["queryset"] = kwargs["queryset"].order_by(Lower("name"))
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
            path("import/batch", self.admin_site.admin_view(self.import_batch_view), name="game_import_batch"),
            path("import/", self.admin_site.admin_view(self.import_view), name="game_import")
        ]
        return cast(List[str], my_urls + urls)

    def import_setup_view(self, request: HttpRequest) -> TemplateResponse:
        context = self.admin_site.each_context(request)

        source_display_names = {
            key: settings.CATALOG_SOURCES_ADAPTERS[key][constants.ADAPTER_DISPLAY_NAME]
            for key in settings.CATALOG_SOURCES_ADAPTERS.keys()
        }

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

        if request.GET["ids"] == constants.ALL_IDS:
            import_all_games = True
        else:
            import_all_games = False
            selected_ids = list(map(int, request.GET["ids"].split(",")))

        if not import_all_games and len(selected_ids) == 1:
            fetched_game = FetchedGame.objects.get(id=selected_ids[0])

            games = Game.objects.only("id", "name").order_by(Lower("name"))
            platforms = Platform.objects.only("id", "name").all()

            context.update({
                "fetched_game": fetched_game,
                "fg_plaform_ids": ",".join([
                    str(platform.fg_platform.id)
                    for platform in fetched_game.platforms
                                                .prefetch_related("fg_platform")
                                                .all()
                    if platform.fg_platform
                ]),
                "games_for_selectbox": games,
                "platforms_for_selectbox": platforms,
                "existing_parent_game_id": "",
                "existing_platform_ids": "",
                "existing_platform_ids_list": [],
                "source_display_name": source_display_names[fetched_game.source_id],
            })

            if fetched_game.fg_game:
                platforms_list = [platform.id for platform in fetched_game.fg_game.platforms.only("id").all()]
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
        else:
            if import_all_games:
                hidden_filter = request.GET.get("hidden", "False")
                fetched_games = FetchedGame.objects
                # if == "all" don't filter
                if hidden_filter == "True" or hidden_filter == "False":
                    fetched_games = fetched_games.filter(hidden=(hidden_filter == "True"))
                fetched_games = fetched_games.prefetch_related("platforms", "fg_game", "parent_game")
            else:
                fetched_games = FetchedGame.objects  \
                                           .filter(id__in=selected_ids)  \
                                           .prefetch_related("platforms", "fg_game", "parent_game")
            fg_platform_ids = {
                str(fetched_game.id): ",".join([
                    str(platform.fg_platform.id)
                    for platform in fetched_game.platforms
                                                .prefetch_related("fg_platform")
                                                .all()
                    if platform.fg_platform
                ])
                for fetched_game in fetched_games
            }
            # django templates don't allow array item access, so build a list of tuples which can be easily iterated
            fetched_games_data = [
                (fetched_game, fg_platform_ids[str(fetched_game.id)], source_display_names[fetched_game.source_id])
                for fetched_game in fetched_games
            ]

            context.update({
                "fetched_games_with_platforms": fetched_games_data,
                "count_items_to_import": len(fetched_games_data),
                "constants": constants,
            })
            return TemplateResponse(request, "game_import_batch.html", context)

    def import_view(self, request: HttpRequest) -> HttpResponseRedirect:
        name = request.POST["name"]
        try:
            ImportManager.import_fetched_game(
                name=name,
                publish_date_string=request.POST["publish_date"],
                dlc_or_expansion=(request.POST.get("dlc_or_expansion") is not None),
                platforms=request.POST.getlist("platforms"),
                fetched_game_id=request.POST["fetched_game_id"],
                game_id=request.POST["id"],
                parent_game_id=request.POST["parent_game"],
                source_display_name=request.POST["source_display_name"],
                source_url=request.POST["source_url"]
            )
        except GameImportSaveError as error:
            self.message_user(request, "Error importing Fetched Game '{}': {}".format(name, error), level="error")
            return HttpResponseRedirect(reverse("admin:catalogsources_fetchedgame_changelist"))

        self.message_user(request, "Fetched Game {} imported successfully".format(name))
        return HttpResponseRedirect(reverse("admin:catalogsources_fetchedgame_changelist"))

    def import_batch_view(self, request: HttpRequest) -> HttpResponseRedirect:
        fetched_game_ids = request.POST.getlist("fetched_game_id")
        fg_game_ids = request.POST.getlist("fg_game_id")
        names = request.POST.getlist("name")
        publish_date_strings = request.POST.getlist("publish_date")
        dlcs_or_expansions = [(True if dlc == "true" else False) for dlc in request.POST.getlist("dlc_or_expansion")]
        platforms_lists = [platforms.split(",") for platforms in request.POST.getlist("platforms")]
        parent_game_ids = request.POST.getlist("parent_game_id")
        source_display_names = request.POST.getlist("source_display_name")
        source_urls = request.POST.getlist("source_url")

        update_fields_filter = request.POST.getlist("fields")

        imports_ok = []  # type: List[str]
        imports_ko = []  # type: List[str]

        for index in range(len(names)):
            try:
                name = names[index]
                if int(fg_game_ids[index]) != constants.NO_GAME:
                    game_id = fg_game_ids[index]
                else:
                    game_id = None
                if int(parent_game_ids[index]) != constants.NO_GAME:
                    parent_game_id = parent_game_ids[index]
                else:
                    parent_game_id = None

                ImportManager.import_fetched_game(
                    name=name,
                    publish_date_string=publish_date_strings[index],
                    dlc_or_expansion=dlcs_or_expansions[index],
                    platforms=platforms_lists[index],
                    fetched_game_id=fetched_game_ids[index],
                    game_id=game_id,
                    parent_game_id=parent_game_id,
                    source_display_name=source_display_names[index],
                    source_url=source_urls[index],
                    update_fields_filter=update_fields_filter
                )
                imports_ok.append(name)
            except GameImportSaveError as error:
                imports_ko.append("{} ({}) [{}]".format(name, fetched_game_ids[index], error))

        if len(imports_ko) > 0:
            if len(imports_ok) > 0:
                self.message_user(
                    request,
                    "Some Fetched Game imports failed... Imports OK: {} ... Imports KO: {}".format(
                        ",".join(imports_ok), ",".join(imports_ko)
                    ),
                    level="warning"
                )
            else:
                self.message_user(
                    request,
                    "All imports from the following Fetched Games failed: {}".format(",".join(imports_ko)),
                    level="error"
                )
        else:
            self.message_user(request, "Fetched Games imported successfully: {}".format(",".join(imports_ok)))
        return HttpResponseRedirect(reverse("admin:catalogsources_fetchedgame_changelist"))


class FetchedPlatformAdmin(FGModelAdmin):
    list_display = [
        "name", "fg_platform", hyperlink_fg_platform, hyperlink_source_url, "last_modified_date", "source_id", "hidden"
    ]
    list_filter = ["last_modified_date", HiddenByDefaultFilter, "source_id"]
    search_fields = ["name"]
    readonly_fields = ["last_modified_date", "change_hash"]
    ordering = ["-last_modified_date", "source_id", "name"]
    actions = [hide_fetched_items, import_fetched_items]

    def get_urls(self) -> List[str]:
        urls = super().get_urls()
        my_urls = [
            path("import_setup/", self.admin_site.admin_view(self.import_setup_view), name="platform_import_setup"),
            path("import/batch", self.admin_site.admin_view(self.import_batch_view), name="platform_import_batch"),
            path("import/", self.admin_site.admin_view(self.import_view), name="platform_import"),
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

        if request.GET["ids"] == constants.ALL_IDS:
            import_all_platforms = True
        else:
            import_all_platforms = False
            selected_ids = list(map(int, request.GET["ids"].split(",")))

        if not import_all_platforms and len(selected_ids) == 1:
            context.update({
                "fetched_platform": FetchedPlatform.objects.get(id=selected_ids[0]),
            })
            return TemplateResponse(request, "platform_import.html", context)
        else:
            if import_all_platforms:
                hidden_filter = request.GET.get("hidden", "False")
                fetched_platforms = FetchedPlatform.objects
                # if == "all" don't filter
                if hidden_filter == "True" or hidden_filter == "False":
                    fetched_platforms = fetched_platforms.filter(hidden=(hidden_filter == "True"))
                fetched_platforms = fetched_platforms.prefetch_related("fg_platform")
            else:
                fetched_platforms = FetchedPlatform.objects  \
                                                   .filter(id__in=selected_ids)  \
                                                   .prefetch_related("fg_platform")

            context.update({
                "fetched_platforms": fetched_platforms,
                "count_items_to_import": len(fetched_platforms),
                "constants": constants,
            })
            return TemplateResponse(request, "platform_import_batch.html", context)

    def import_view(self, request: HttpRequest) -> HttpResponseRedirect:
        name = request.POST["name"]
        try:
            ImportManager.import_fetched_platform(
                name=name,
                shortname=request.POST["shortname"],
                publish_date_string=request.POST["publish_date"],
                fetched_platform_id=request.POST["fetched_platform_id"],
                platform_id=request.POST["id"]
            )
        except PlatformImportSaveError as error:
            self.message_user(request, "Error importing Fetched Platform '{}': {}".format(name, error), level="error")
            return HttpResponseRedirect(reverse("admin:catalogsources_fetchedplatform_changelist"))

        self.message_user(request, "Fetched Platform '{}' imported successfully".format(name))
        return HttpResponseRedirect(reverse("admin:catalogsources_fetchedplatform_changelist"))

    def import_batch_view(self, request: HttpRequest) -> HttpResponseRedirect:
        fetched_platform_ids = request.POST.getlist("fetched_platform_id")
        fg_platform_ids = request.POST.getlist("fg_platform_id")
        names = request.POST.getlist("name")
        shortnames = request.POST.getlist("shortname")
        publish_date_strings = request.POST.getlist("publish_date")

        update_fields_filter = request.POST.getlist("fields")

        imports_ok = []  # type: List[str]
        imports_ko = []  # type: List[str]

        for index in range(len(names)):
            try:
                name = names[index]
                if int(fg_platform_ids[index]) != constants.NO_PLATFORM:
                    platform_id = fg_platform_ids[index]
                else:
                    platform_id = None
                ImportManager.import_fetched_platform(
                    name=name,
                    shortname=shortnames[index],
                    publish_date_string=publish_date_strings[index],
                    fetched_platform_id=fetched_platform_ids[index],
                    platform_id=platform_id,
                    update_fields_filter=update_fields_filter
                )
                imports_ok.append(name)
            except PlatformImportSaveError as error:
                imports_ko.append("{} ({}) [{}]".format(name, fetched_platform_ids[index], error))

        if len(imports_ko) > 0:
            if len(imports_ok) > 0:
                self.message_user(
                    request,
                    "Some Fetched Platform imports failed... Imports OK: {} ... Imports KO: {}".format(
                        ",".join(imports_ok), ",".join(imports_ko)
                    ),
                    level="warning"
                )
            else:
                self.message_user(
                    request,
                    "All imports from the following Fetched Platforms failed: {}".format(",".join(imports_ko)),
                    level="error"
                )
        else:
            self.message_user(request, "Fetched Platforms imported successfully: {}".format(",".join(imports_ok)))
        return HttpResponseRedirect(reverse("admin:catalogsources_fetchedplatform_changelist"))
