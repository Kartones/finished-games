
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import (HttpRequest, HttpResponseRedirect)


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
