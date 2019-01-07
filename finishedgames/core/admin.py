from typing import List

from django.contrib import admin
# TODO: Use when adding data fields for the user, like an avatar (or fully remove)
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from django.contrib.auth.models import User
from django.db.models.functions import Lower
from django.http import HttpRequest

from core.forms import (GameForm, PlatformForm, UserGameForm, WishlistedUserGameForm)
from core.models import (Game, Platform, UserGame, WishlistedUserGame)


class FGModelAdmin(admin.ModelAdmin):
    class Media:
        css = {
             'all': ('css/admin.css',)
        }


# TODO: Use when adding data fields for the user, like an avatar (or fully remove)
"""
class UserDataAdmin(FGModelAdmin):
    form = UserDataForm
    list_display = ("user",)
    list_filter = ["user"]
    search_fields = ["user__username", "user__email"]

    def get_ordering(self, request: HttpRequest) -> List[str]:
        return ["-id"]


class UserDataInline(admin.StackedInline):
    model = UserData
    can_delete = False
    verbose_name_plural = 'user data'
"""


class UserGameAdmin(FGModelAdmin):
    form = UserGameForm
    list_display = ("game", "user", "platform", "currently_playing", "year_finished")
    list_filter = ["user__username", "platform", "currently_playing", "year_finished"]
    search_fields = ["game__name"]

    def get_ordering(self, request: HttpRequest) -> List[str]:
        return [Lower("user__username"), "-id"]


class PlatformAdmin(FGModelAdmin):
    form = PlatformForm
    list_display = ("name", "publish_date")

    def get_ordering(self, request: HttpRequest) -> List[str]:
        return [Lower("name")]


class GameAdmin(FGModelAdmin):
    form = GameForm
    fieldsets = [
        ("Basic Info", {"fields": ["name", "platforms", "publish_date"]}),
        ("DLCs & Expansions", {"fields": ["dlc_or_expansion", "parent_game"]}),
    ]
    list_display = ("name", "dlc_or_expansion", "parent_game")
    list_filter = ["dlc_or_expansion"]
    search_fields = ["name"]

    def get_ordering(self, request: HttpRequest) -> List[str]:
        return ["-id"]


class WishlistedUserGameAdmin(FGModelAdmin):
    form = WishlistedUserGameForm
    list_display = ("game", "user", "platform")
    list_filter = ["user__username", "platform"]
    search_fields = ["game__name"]

    def get_ordering(self, request: HttpRequest) -> List[str]:
        return [Lower("user__username"), "-id"]


# TODO: Use when adding data fields for the user, like an avatar (or fully remove)
"""
class UserAdmin(BaseUserAdmin):
    inlines = (UserDataInline,)
"""


# TODO: Use when adding data fields for the user, like an avatar (or fully remove)
# admin.site.unregister(User)
# admin.site.register(User, UserAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(Platform, PlatformAdmin)
# TODO: Use when adding data fields for the user, like an avatar (or fully remove)
# admin.site.register(UserData, UserDataAdmin)
admin.site.register(UserGame, UserGameAdmin)
admin.site.register(WishlistedUserGame, WishlistedUserGameAdmin)
