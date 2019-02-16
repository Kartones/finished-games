from typing import List

from django.contrib import admin
from django.db.models.functions import Lower
from django.http import HttpRequest

from catalogsources.models import FetchedPlatform
from core.admin import FGModelAdmin


class FetchedPlatformAdmin(FGModelAdmin):
    list_display = ("name", "shortname", "publish_date", "source_id", "last_modified_date", "last_fetch_date")
    list_filter = ["name", "source_id"]
    search_fields = ["name"]

    def get_ordering(self, request: HttpRequest) -> List[str]:
        return [Lower("name")]


admin.site.register(FetchedPlatform, FetchedPlatformAdmin)
