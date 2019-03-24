from typing import (Any, List)

from django.contrib import admin
# TODO: Use when adding data fields for the user, like an avatar (or fully remove)
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from django.contrib.auth.models import User
from django.db.models.functions import Lower
from django.forms import ModelForm
from django.http import HttpRequest

from core.forms import (GameForm, PlatformForm)
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
    list_display = ["user"]
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
    list_display = ["game", "user", "platform", "currently_playing", "year_finished", "no_longer_owned"]
    list_filter = ["user__username", "platform", "currently_playing", "year_finished", "no_longer_owned"]
    search_fields = ["game__name"]

    def get_ordering(self, request: HttpRequest) -> List[str]:
        return [Lower("user__username"), "-id"]

    def get_form(self, request: HttpRequest, obj: Any = None, **kwargs: Any) -> ModelForm:
        form = super(UserGameAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['user'].initial = request.user
        return form


class PlatformAdmin(FGModelAdmin):
    form = PlatformForm
    list_display = ["name", "shortname", "publish_date"]

    def get_ordering(self, request: HttpRequest) -> List[str]:
        return [Lower("name")]


class GameAdmin(FGModelAdmin):
    form = GameForm
    fieldsets = [
        ("Basic Info", {"fields": ["name", "platforms", "publish_date"]}),
        ("DLCs & Expansions", {"fields": ["dlc_or_expansion", "parent_game"]}),
        ("Advanced (don't touch if you don't know what you're doing)", {"fields": ["urls"]}),
    ]
    list_display = ["name", "platforms_list", "dlc_or_expansion", "parent_game"]
    list_filter = ["dlc_or_expansion", "platforms"]
    search_fields = ["name"]

    def get_ordering(self, request: HttpRequest) -> List[str]:
        return ["-id"]


class WishlistedUserGameAdmin(FGModelAdmin):
    list_display = ("game", "user", "platform")
    list_filter = ["user__username", "platform"]
    search_fields = ["game__name"]

    def get_ordering(self, request: HttpRequest) -> List[str]:
        return [Lower("user__username"), "-id"]

    def get_form(self, request: HttpRequest, obj: Any = None, **kwargs: Any) -> ModelForm:
        form = super(WishlistedUserGameAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['user'].initial = request.user
        return form


# TODO: Use when adding data fields for the user, like an avatar (or fully remove)
"""
class UserAdmin(BaseUserAdmin):
    inlines = [UserDataInline]
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
