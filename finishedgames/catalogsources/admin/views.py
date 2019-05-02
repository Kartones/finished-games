from typing import (Dict, List)

from django.conf import settings
from django.db.models.functions import Lower
from django.http import (HttpRequest, HttpResponseRedirect)
from django.template.response import TemplateResponse
from django.urls import reverse

from catalogsources.admin.forms import (SingleFetchedPlatformImportForm, SinglePlatformImportForm)
from catalogsources.apps import CatalogSourcesConfig
from catalogsources.managers import (GameImportSaveError, ImportManager, PlatformImportSaveError)
from catalogsources.models import (FetchedGame, FetchedPlatform)
from core.admin import FGModelAdmin
from core.models import (Game, Platform)
from finishedgames import constants


class FetchedGameAdminViewsMixin(FGModelAdmin):

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
                "fg_plaform_ids": ",".join((
                    str(platform.fg_platform.id)
                    for platform in fetched_game.platforms
                                                .prefetch_related("fg_platform")
                                                .all()
                    if platform.fg_platform
                )),
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
                    "existing_platform_ids": ",".join((str(platform_id) for platform_id in platforms_list)),
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
                str(fetched_game.id): ",".join((
                    str(platform.fg_platform.id)
                    for platform in fetched_game.platforms
                                                .prefetch_related("fg_platform")
                                                .all()
                    if platform.fg_platform
                ))
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

        for index, name in enumerate(names):
            try:
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


class FetchedPlatformAdminViewsMixin(FGModelAdmin):
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

        # TODO: new code
        if not import_all_platforms and len(selected_ids) == 1:
            fetched_platform = FetchedPlatform.objects.get(id=selected_ids[0])
            is_fetched_platform_linked = fetched_platform.fg_platform is not None

            initial_fetched_form_data = {
                "fetched_name": fetched_platform.name,
                "fetched_shortname": fetched_platform.shortname,
                "fetched_publish_date": fetched_platform.publish_date,
                "source_id": fetched_platform.source_id,
                "source_platform_id": fetched_platform.source_platform_id,
                "source_url": fetched_platform.source_url,
                "hidden": fetched_platform.hidden,
                "last_modified_date": fetched_platform.last_modified_date,
            }

            initial_form_data = {
                "fetched_platform_id": fetched_platform.id,
            }

            if is_fetched_platform_linked:
                initial_fetched_form_data.update({
                    "fg_platform_id": fetched_platform.fg_platform.id,
                    "fg_platform_name": fetched_platform.fg_platform.name,
                })

                initial_form_data.update({
                    "platform_id": fetched_platform.fg_platform.id,
                    "name": fetched_platform.fg_platform.name,
                    "shortname": fetched_platform.fg_platform.shortname,
                    "publish_date": fetched_platform.fg_platform.publish_date,
                })

            fetched_platform_form = SingleFetchedPlatformImportForm(initial=initial_fetched_form_data)
            platform_form = SinglePlatformImportForm(initial=initial_form_data)

            context.update({
                "fetched_platform_form": fetched_platform_form,
                "platform_form": platform_form,
                "is_fetched_platform_linked": is_fetched_platform_linked,
            })
            return TemplateResponse(request, "single_platform_import_form.html", context)

        # -----

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

        for index, name in enumerate(names):
            try:
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
