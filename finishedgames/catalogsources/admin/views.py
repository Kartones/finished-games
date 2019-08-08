from typing import List

from django.forms import Form
from django.conf import settings
from django.db.models.functions import Lower
from django.http import (
    Http404,
    HttpRequest,
    HttpResponseRedirect
)
from django.template.response import TemplateResponse
from django.urls import reverse

from catalogsources.admin.forms import (
    GamesImportForm,
    PlatformsImportForm,
    SingleFetchedGameImportForm,
    SingleFetchedPlatformImportForm,
    SingleGameImportForm,
    SinglePlatformImportForm
)
from catalogsources.apps import CatalogSourcesConfig
from catalogsources.managers import (
    GameImportSaveError,
    ImportManager,
    PlatformImportSaveError
)
from catalogsources.models import (
    FetchedGame,
    FetchedPlatform
)
from core.admin import FGModelAdmin
from finishedgames import constants


class BaseFetchedModelAdmin(FGModelAdmin):

    def redirect_to_import_errors(
        self, form: Form, request: HttpRequest, capitalized_model_name: str, model_value: str, redirect_location: str
    ) -> HttpResponseRedirect:
        non_field_errors = ", ".join([error for error in form.non_field_errors()])
        field_errors = ", ".join([
            "Field '{field}': {errors}".format(
                field=field.label,
                errors=",".join(field.errors)
            ) for field in form if field.errors
        ])
        if non_field_errors:
            non_field_errors = "{}, ".format(non_field_errors)

        self.message_user(
            request, "Errors importing {model_name} '{model_value}': {errors} {field_errors}".format(
                model_name=capitalized_model_name,
                model_value=model_value,
                errors=non_field_errors,
                field_errors=field_errors
            ),
            level="error"
        )
        return HttpResponseRedirect(reverse(redirect_location))


class FetchedGameAdminViewsMixin(BaseFetchedModelAdmin):

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
            fg_game_platforms = fetched_game.platforms.order_by(Lower("name"))
            fg_platform_ids = ",".join((
                str(platform.fg_platform.id)
                for platform in fg_game_platforms.prefetch_related("fg_platform")
                if platform.fg_platform
            ))

            is_fetched_game_linked = fetched_game.fg_game is not None
            has_parent_game = fetched_game.parent_game is not None
            is_parent_fetched_game_imported = bool(has_parent_game and fetched_game.parent_game.fg_game)

            context.update({
                "is_fetched_game_linked": is_fetched_game_linked,
                "has_parent_game": has_parent_game,
                "is_parent_fetched_game_imported": is_parent_fetched_game_imported,
                "existing_platform_ids": "",
            })

            initial_fetched_form_data = {
                "fetched_name": fetched_game.name,
                "fetched_publish_date": fetched_game.publish_date,
                "fg_platform_ids": fg_platform_ids,
                "fg_platforms": "",
                "fetched_dlc_or_expansion": fetched_game.dlc_or_expansion,
                "source_id": fetched_game.source_id,
                "source_game_id": fetched_game.source_game_id,
                "source_url": fetched_game.source_url,
                "hidden": fetched_game.hidden,
                "last_modified_date": fetched_game.last_modified_date,
            }

            initial_form_data = {
                "fetched_game_id": fetched_game.id,
                "source_display_name": source_display_names[fetched_game.source_id],
                "source_url": fetched_game.source_url,
            }

            if is_fetched_game_linked:
                platforms_list = [platform.id for platform in fetched_game.fg_game.platforms.only("id")]

                if fetched_game.fg_game.parent_game is not None:
                    initial_form_data.update({
                        "parent_game": fetched_game.fg_game.parent_game.id,
                    })

                initial_fetched_form_data.update({
                    "fg_game_id": fetched_game.fg_game.id,
                    "fg_game_name": fetched_game.fg_game.name,
                })

                context.update({
                    "existing_platform_ids": ",".join((str(platform_id) for platform_id in platforms_list)),
                })

                initial_form_data.update({
                    "game_id": fetched_game.fg_game.id,
                    "name": fetched_game.fg_game.name,
                    "publish_date": fetched_game.fg_game.publish_date,
                    "platforms": platforms_list,
                    "dlc_or_expansion": fetched_game.fg_game.dlc_or_expansion,
                })

            if has_parent_game:
                initial_fetched_form_data.update({
                    "fetched_parent_game_name": fetched_game.parent_game.name
                })

            if is_parent_fetched_game_imported:
                initial_fetched_form_data.update({
                    "parent_game_fg_game_id": fetched_game.parent_game.fg_game.id
                })

            for platform in fg_game_platforms:
                if platform.fg_platform:
                    initial_fetched_form_data["fg_platforms"] = initial_fetched_form_data["fg_platforms"] + \
                        "<strong>{}</strong><br />".format(platform.name)
                else:
                    initial_fetched_form_data["fg_platforms"] = initial_fetched_form_data["fg_platforms"] + \
                        "<span class=\"unavailable\">{}</span><br />".format(platform.name)

            fetched_game_form = SingleFetchedGameImportForm(initial=initial_fetched_form_data)
            game_form = SingleGameImportForm(initial=initial_form_data)

            context.update({
                "fetched_game_form": fetched_game_form,
                "game_form": game_form,
            })

            return TemplateResponse(request, "single_game_import_form.html", context)
        else:
            games_form = GamesImportForm()

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
            fg_platform_ids_dict = {
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
                (fetched_game, fg_platform_ids_dict[str(fetched_game.id)], source_display_names[fetched_game.source_id])
                for fetched_game in fetched_games
            ]

            context.update({
                "fetched_games_with_platforms": fetched_games_data,
                "games_form": games_form,
                "count_items_to_import": len(fetched_games_data),
                "constants": constants,
            })
            return TemplateResponse(request, "game_import_batch.html", context)

    def import_view(self, request: HttpRequest) -> HttpResponseRedirect:
        if request.method != "POST":
            raise Http404("Invalid URL")

        game_form = SingleGameImportForm(request.POST)

        if not game_form.is_valid():
            return self.redirect_to_import_errors(
                form=game_form,
                request=request,
                capitalized_model_name="Fetched Game",
                model_value=request.POST["name"],
                redirect_location="admin:catalogsources_fetchedgame_changelist"
            )

        name = game_form.cleaned_data["name"]
        has_parent_game = game_form.cleaned_data["parent_game"] is not None
        try:
            ImportManager.import_fetched_game(
                name=name,
                publish_date_string=game_form.cleaned_data["publish_date"],
                dlc_or_expansion=game_form.cleaned_data["dlc_or_expansion"],
                platforms=game_form.cleaned_data["platforms"],
                fetched_game_id=game_form.cleaned_data["fetched_game_id"],
                game_id=game_form.cleaned_data["game_id"],
                parent_game_id=game_form.cleaned_data["parent_game"].id if has_parent_game else None,
                source_display_name=game_form.cleaned_data["source_display_name"],
                source_url=game_form.cleaned_data["source_url"]
            )
        except GameImportSaveError as error:
            self.message_user(
                request,
                "Error importing Fetched Game '{}':{}".format(name, error),
                level="error"
            )
            return HttpResponseRedirect(reverse("admin:catalogsources_fetchedgame_changelist"))

        self.message_user(request, "Fetched Game '{}' imported successfully".format(name))
        return HttpResponseRedirect(reverse("admin:catalogsources_fetchedgame_changelist"))

    def import_batch_view(self, request: HttpRequest) -> HttpResponseRedirect:
        imports_ok = []  # type: List[str]
        imports_ko = []  # type: List[str]

        if request.method != "POST":
            raise Http404("Invalid URL")

        form_data = {
            "fields": request.POST.getlist("fields"),
            "fetched_game_ids": request.POST.getlist("fetched_game_ids"),
            "fg_game_ids": request.POST.getlist("fg_game_ids"),
            "names": request.POST.getlist("names"),
            "publish_date_strings": request.POST.getlist("publish_date_strings"),
            "dlcs_or_expansions": [
                (True if dlc == "true" else False) for dlc in request.POST.getlist("dlcs_or_expansions")
            ],
            "platforms_lists": request.POST.getlist("platforms_lists"),
            "parent_game_ids": request.POST.getlist("parent_game_ids"),
            "source_display_names": request.POST.getlist("source_display_names"),
            "source_urls": request.POST.getlist("source_urls"),
        }
        print(form_data)
        games_form = GamesImportForm(form_data)

        if not games_form.is_valid():
            return self.redirect_to_import_errors(
                form=games_form,
                request=request,
                capitalized_model_name="Fetched Games",
                model_value=", ".join(request.POST.getlist("name")),
                redirect_location="admin:catalogsources_fetchedgame_changelist"
            )

        for index, name in enumerate(games_form.cleaned_data["names"]):
            try:
                if int(games_form.cleaned_data["fg_game_ids"][index]) != constants.NO_GAME:
                    game_id = games_form.cleaned_data["fg_game_ids"][index]
                else:
                    game_id = None
                if int(games_form.cleaned_data["parent_game_ids"][index]) != constants.NO_GAME:
                    parent_game_id = games_form.cleaned_data["parent_game_ids"][index]
                else:
                    parent_game_id = None
                platforms = [int(platform) for platform in games_form.cleaned_data["platforms_lists"][index].split(",")]

                ImportManager.import_fetched_game(
                    name=name,
                    publish_date_string=games_form.cleaned_data["publish_date_strings"][index],
                    dlc_or_expansion=games_form.cleaned_data["dlcs_or_expansions"][index],
                    platforms=platforms,
                    fetched_game_id=games_form.cleaned_data["fetched_game_ids"][index],
                    game_id=game_id,
                    parent_game_id=parent_game_id,
                    source_display_name=games_form.cleaned_data["source_display_names"][index],
                    source_url=games_form.cleaned_data["source_urls"][index],
                    update_fields_filter=games_form.cleaned_data["fields"]
                )
                imports_ok.append(name)
            except GameImportSaveError as error:
                imports_ko.append("{} ({}) [{}]".format(
                    name, games_form.cleaned_data["fetched_game_ids"][index], error)
                )

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


class FetchedPlatformAdminViewsMixin(BaseFetchedModelAdmin):

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
        else:
            platforms_form = PlatformsImportForm()

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
                "platforms_form": platforms_form,
                "count_items_to_import": len(fetched_platforms),
                "constants": constants,
            })
            return TemplateResponse(request, "platform_import_batch.html", context)

    def import_view(self, request: HttpRequest) -> HttpResponseRedirect:
        if request.method != "POST":
            raise Http404("Invalid URL")

        platform_form = SinglePlatformImportForm(request.POST)

        if not platform_form.is_valid():
            return self.redirect_to_import_errors(
                form=platform_form,
                request=request,
                capitalized_model_name="Fetched Platform",
                model_value=request.POST["name"],
                redirect_location="admin:catalogsources_fetchedplatform_changelist"
            )

        name = platform_form.cleaned_data["name"]
        try:
            ImportManager.import_fetched_platform(
                name=name,
                shortname=platform_form.cleaned_data["shortname"],
                publish_date_string=platform_form.cleaned_data["publish_date"],
                fetched_platform_id=platform_form.cleaned_data["fetched_platform_id"],
                platform_id=platform_form.cleaned_data["platform_id"]
            )
        except PlatformImportSaveError as error:
            self.message_user(
                request, "Error importing Fetched Platform '{}': {}".format(name, error), level="error"
            )
            return HttpResponseRedirect(reverse("admin:catalogsources_fetchedplatform_changelist"))

        self.message_user(request, "Fetched Platform '{}' imported successfully".format(name))
        return HttpResponseRedirect(reverse("admin:catalogsources_fetchedplatform_changelist"))

    def import_batch_view(self, request: HttpRequest) -> HttpResponseRedirect:
        imports_ok = []  # type: List[str]
        imports_ko = []  # type: List[str]

        if request.method != "POST":
            raise Http404("Invalid URL")

        form_data = {
            "fields": request.POST.getlist("fields"),
            "fetched_platform_ids": request.POST.getlist("fetched_platform_ids"),
            "fg_platform_ids": request.POST.getlist("fg_platform_ids"),
            "names": request.POST.getlist("names"),
            "shortnames": request.POST.getlist("shortnames"),
            "publish_date_strings": request.POST.getlist("publish_date_strings"),
        }
        platforms_form = PlatformsImportForm(form_data)

        if not platforms_form.is_valid():
            return self.redirect_to_import_errors(
                form=platforms_form,
                request=request,
                capitalized_model_name="Fetched Platforms",
                model_value=", ".join(request.POST.getlist("names")),
                redirect_location="admin:catalogsources_fetchedplatform_changelist"
            )

        for index, name in enumerate(platforms_form.cleaned_data["names"]):
            try:
                if int(platforms_form.cleaned_data["fg_platform_ids"][index]) != constants.NO_PLATFORM:
                    platform_id = platforms_form.cleaned_data["fg_platform_ids"][index]
                else:
                    platform_id = None
                ImportManager.import_fetched_platform(
                    name=name,
                    shortname=platforms_form.cleaned_data["shortnames"][index],
                    publish_date_string=platforms_form.cleaned_data["publish_date_strings"][index],
                    fetched_platform_id=platforms_form.cleaned_data["fetched_platform_ids"][index],
                    platform_id=platform_id,
                    update_fields_filter=platforms_form.cleaned_data["fields"]
                )
                imports_ok.append(name)
            except PlatformImportSaveError as error:
                imports_ko.append("{} ({}) [{}]".format(
                    name, platforms_form.cleaned_data["fetched_platform_ids"][index], error)
                )

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
