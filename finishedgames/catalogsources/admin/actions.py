
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import (HttpRequest, HttpResponseRedirect)

from finishedgames import constants


# Custom admin action
def hide_fetched_items(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet) -> None:
    queryset.update(hidden=True)
hide_fetched_items.short_description = "Hide selected items"  # type:ignore # NOQA: E305


# Custom admin action
def import_fetched_items(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
) -> HttpResponseRedirect:
    if request.POST.get("select_across", "0") == "1":
        ids = constants.ALL_IDS
    else:
        ids = ",".join(request.POST.getlist(admin.ACTION_CHECKBOX_NAME))
    return HttpResponseRedirect("import_setup/?ids={}&hidden={}".format(ids, request.GET.get("hidden", "False")))
import_fetched_items.short_description = "Import selected items into catalog"  # type:ignore # NOQA: E305
