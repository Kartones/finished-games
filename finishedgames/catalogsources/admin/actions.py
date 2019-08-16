"""

Custom admin actions

"""

from django.contrib import (
    admin,
    messages
)
from django.db.models.query import QuerySet
from django.http import (HttpRequest, HttpResponseRedirect)

from catalogsources.managers import ImportManager
from finishedgames import constants


def hide_fetched_items(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet) -> None:
    queryset.update(hidden=True)
hide_fetched_items.short_description = "Hide selected items"  # type:ignore # NOQA: E305


def import_fetched_items(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
) -> HttpResponseRedirect:
    if request.POST.get("select_across", "0") == "1":
        ids = constants.ALL_IDS
    else:
        ids = ",".join(request.POST.getlist(admin.ACTION_CHECKBOX_NAME))
    return HttpResponseRedirect("import_setup/?ids={}&hidden={}".format(ids, request.GET.get("hidden", "False")))
import_fetched_items.short_description = "Import selected items into catalog"  # type:ignore # NOQA: E305


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
import_fetched_games_fixing_duplicates_appending_platform.short_description = "Import selected games - on duplicate append 1st platform"  # type:ignore # NOQA: E305, E501


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
import_fetched_games_fixing_duplicates_appending_publish_date.short_description = "Import selected games - on duplicate append publish date"  # type:ignore # NOQA: E305, E501
