from typing import (Any, cast, List)

from django.contrib import admin
from django.db.models.functions import Lower
from django.forms import ModelForm
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import (format_html, format_html_join)
from django.utils.safestring import mark_safe

from core.forms import (GameForm, PlatformForm)
from core.models import (Game, Platform, UserGame, WishlistedUserGame)


class FGModelAdmin(admin.ModelAdmin):
    class Media:
        css = {
             'all': ('css/admin.css',)
        }


class UserGameAdmin(FGModelAdmin):
    list_display = ["game", "user", "platform", "currently_playing", "year_finished", "no_longer_owned"]
    list_filter = ["user__username", "platform", "currently_playing", "year_finished", "no_longer_owned"]
    search_fields = ["game__name"]
    autocomplete_fields = ["user", "game"]

    def get_ordering(self, request: HttpRequest) -> List[str]:
        return [Lower("user__username"), "-id"]

    def get_form(self, request: HttpRequest, obj: Any = None, **kwargs: Any) -> ModelForm:
        form = super(UserGameAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['user'].initial = request.user
        return form


class PlatformAdmin(FGModelAdmin):
    form = PlatformForm
    list_display = ["name", "shortname", "publish_date", "platform_url"]
    readonly_fields = ["platform_url"]

    def get_ordering(self, request: HttpRequest) -> List[str]:
        return [Lower("name")]

    def platform_url(self, instance: FGModelAdmin) -> str:
        url = reverse("platform_details", args=[instance.id])
        return cast(str, format_html("<a href='{}' target='_blank'>{}</a>", url, url))
    platform_url.short_description = "Platform Url"  # type:ignore # NOQA: E305


class GameAdmin(FGModelAdmin):
    form = GameForm
    fieldsets = [
        ("Basic Info", {"fields": ["name", "platforms", "publish_date", "game_url"]}),
        ("DLCs & Expansions", {"fields": ["dlc_or_expansion", "parent_game"]}),
        ("Advanced", {"fields": ["urls_list", "urls"]}),
    ]
    list_display = ["name", "platforms_list", "dlc_or_expansion", "parent_game"]
    list_filter = ["dlc_or_expansion", "platforms"]
    search_fields = ["name"]
    autocomplete_fields = ["parent_game"]

    readonly_fields = ["urls_list", "game_url"]

    def game_url(self, instance: FGModelAdmin) -> str:
        url = reverse("game_details", args=[instance.id])
        return cast(str, format_html("<a href='{}' target='_blank'>{}</a>", url, url))
    game_url.short_description = "Game Url"  # type:ignore # NOQA: E305

    def urls_list(self, instance: FGModelAdmin) -> str:
        return cast(str, format_html_join(
            mark_safe("<br>"),
            "{}: <a href='{}' target='_blank'>{}</a>",
            ((name, url, url) for name, url in instance.urls_dict.items()),
        ))
    urls_list.short_description = "URLs list"  # type:ignore # NOQA: E305

    def get_ordering(self, request: HttpRequest) -> List[str]:
        return ["-id"]


class WishlistedUserGameAdmin(FGModelAdmin):
    list_display = ("game", "user", "platform")
    list_filter = ["user__username", "platform"]
    search_fields = ["game__name"]
    autocomplete_fields = ["user", "game"]

    def get_ordering(self, request: HttpRequest) -> List[str]:
        return [Lower("user__username"), "-id"]

    def get_form(self, request: HttpRequest, obj: Any = None, **kwargs: Any) -> ModelForm:
        form = super(WishlistedUserGameAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['user'].initial = request.user
        return form


admin.site.register(Game, GameAdmin)
admin.site.register(Platform, PlatformAdmin)
admin.site.register(UserGame, UserGameAdmin)
admin.site.register(WishlistedUserGame, WishlistedUserGameAdmin)
