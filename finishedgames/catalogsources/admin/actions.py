"""
Custom admin actions
"""
from typing import List

from catalogsources.managers import ImportManager
from django.contrib import admin, messages
from django.db.models import F
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponseRedirect
from finishedgames import constants


def hide_fetched_items(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet) -> None:
    queryset.update(hidden=True)


hide_fetched_items.short_description = "Hide item(s)"  # type:ignore # NOQA: E305


def import_fetched_items(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
) -> HttpResponseRedirect:
    if request.POST.get("select_across", "0") == "1":
        ids = constants.ALL_IDS
    else:
        ids = ",".join(request.POST.getlist(admin.ACTION_CHECKBOX_NAME))
    return HttpResponseRedirect("import_setup/?ids={}&hidden={}".format(ids, request.GET.get("hidden", "False")))


import_fetched_items.short_description = "Import item(s) into catalog"  # type:ignore # NOQA: E305


def import_fetched_games_fixing_duplicates_appending_platform(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
) -> None:
    errors = ImportManager.import_fetched_games_fixing_duplicates_appending_platform(
        [int(id) for id in request.POST.getlist(admin.ACTION_CHECKBOX_NAME)]
    )

    if errors:
        messages.error(request, "Errors importing Fetched Games: {errors}".format(errors=", ".join(errors)))
    else:
        messages.success(request, "Fetched Games imported successfully")


import_fetched_games_fixing_duplicates_appending_platform.short_description = (  # type:ignore # NOQA: E305, E501
    "Import game(s) - on duplicate append 1st platform"
)


def import_fetched_games_fixing_duplicates_appending_publish_date(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
) -> None:
    errors = ImportManager.import_fetched_games_fixing_duplicates_appending_publish_date(
        [int(id) for id in request.POST.getlist(admin.ACTION_CHECKBOX_NAME)]
    )

    if errors:
        messages.error(request, "Errors importing Fetched Games: {errors}".format(errors=", ".join(errors)))
    else:
        messages.success(request, "Fetched Games imported successfully")


import_fetched_games_fixing_duplicates_appending_publish_date.short_description = (  # type:ignore # NOQA: E305, E501
    "Import game(s) - on duplicate append publish date"
)


def import_fetched_games_link_automatically_if_name_and_year_matches(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
) -> None:
    errors = ImportManager.import_fetched_games_linking_if_name_and_year_matches(
        [int(id) for id in request.POST.getlist(admin.ACTION_CHECKBOX_NAME)]
    )

    if errors:
        messages.error(request, "Errors importing Fetched Games: {errors}".format(errors=", ".join(errors)))
    else:
        messages.success(request, "Fetched Games imported successfully")


import_fetched_games_link_automatically_if_name_and_year_matches.short_description = (  # type:ignore # NOQA: E305, E501
    "Import game(s) - link if name & date match"
)


def sync_fetched_games_publish_date_and_platforms(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
) -> None:
    try:
        game_ids = selected_fetched_game_ids(request, modeladmin)
    except ValueError as e:
        messages.error(request, e)
        return

    count_synced, count_skipped = ImportManager.sync_fetched_games_publish_date_and_platforms(game_ids)

    if count_skipped:
        messages.warning(
            request,
            "Imported: {} Skipped: {} Total: {}".format(count_synced, count_skipped, count_synced + count_skipped),
        )
    else:
        messages.success(request, "Synced: {} games".format(count_synced))


sync_fetched_games_publish_date_and_platforms.short_description = (  # type:ignore # NOQA: E305, E501
    "Sync imported game(s)"
)


def selected_fetched_game_ids(request: HttpRequest, modeladmin: admin.ModelAdmin) -> List[int]:
    if request.POST["select_across"] == "1":
        queryset = modeladmin.model.objects

        filters = {key: value for key, value in request.GET.items()}

        # special case, by default always acting upon non-hidden items
        if "hidden" not in filters:
            queryset = queryset.filter(hidden=False)
        else:
            if filters["hidden"] != "all":
                queryset = queryset.filter(hidden=True)

        for param, value in filters.items():
            if param == "source_id":
                queryset = queryset.filter(source_id=value)
            elif param == "fg_game":
                # "fg_game" meaning not imported in filter context
                queryset = queryset.filter(fg_game__isnull=(value == "True"))
            elif param == "is_sync":
                if value == "True":
                    queryset = queryset.exclude(fg_game__isnull=True).filter(last_sync_date=F("last_modified_date"))
                else:
                    queryset = queryset.exclude(last_sync_date=F("last_modified_date"))
            elif param == "platforms":
                queryset = queryset.filter(platforms=int(value))
            else:
                raise ValueError("Unsupported filter applied: '{}' (value: '{}')".format(param, value))

        return [game_id for game_id in queryset.values_list("id", flat=True)]
    else:
        return [int(game_id) for game_id in request.POST.getlist(admin.ACTION_CHECKBOX_NAME)]
