from typing import Any, List, Optional, cast

from catalogsources.admin.actions import (
    hide_fetched_items,
    import_fetched_games_fixing_duplicates_appending_platform,
    import_fetched_games_fixing_duplicates_appending_publish_date,
    import_fetched_games_link_automatically_if_name_and_year_matches,
    import_fetched_games_link_only_if_exact_name_match,
    import_fetched_games_link_only_if_exact_name_and_date_match,
    import_fetched_items,
    sync_fetched_games_base_fields,
)
from catalogsources.admin.decorators import hyperlink_fg_game, hyperlink_fg_platform, hyperlink_source_url
from catalogsources.admin.filters import (
    CustomPlatformsFilter,
    HiddenByDefaultFilter,
    NotImportedFetchedGames,
    NotImportedFetchedPlatforms,
    SyncedFetchedGames,
)
from catalogsources.admin.views import FetchedGameAdminViewsMixin, FetchedPlatformAdminViewsMixin
from catalogsources.models import FetchedGame, FetchedPlatform
from core.models import Game
from django.db.models.fields import Field
from django.db.models.functions import Lower
from django.forms import ModelForm
from django.forms.fields import Field as Form_Field
from django.http import HttpRequest
from django.urls import path
from web.admin import FGModelAdmin


class FetchedGameAdmin(FetchedGameAdminViewsMixin, FGModelAdmin):
    list_display = [
        "name",
        hyperlink_fg_game,
        "publish_date",
        "platforms_list",
        "dlc_or_expansion",
        hyperlink_source_url,
        "is_sync",
        "last_modified_date",
        "source_id",
        "hidden",
    ]
    list_filter = [
        HiddenByDefaultFilter,
        NotImportedFetchedGames,
        SyncedFetchedGames,
        "last_modified_date",
        "source_id",
        CustomPlatformsFilter,
        "dlc_or_expansion",
    ]
    search_fields = ["name"]
    readonly_fields = [
        "last_modified_date",
        "change_hash",
    ]
    ordering = [
        "-last_modified_date",
        "source_id",
        "name",
    ]
    actions = [
        hide_fetched_items,
        import_fetched_items,
        import_fetched_games_fixing_duplicates_appending_platform,
        import_fetched_games_fixing_duplicates_appending_publish_date,
        import_fetched_games_link_automatically_if_name_and_year_matches,
        import_fetched_games_link_only_if_exact_name_match,
        import_fetched_games_link_only_if_exact_name_and_date_match,
        sync_fetched_games_base_fields,
    ]
    raw_id_fields = [
        "fg_game",
        "parent_game",
    ]

    fields = (
        "name",
        "platforms",
        "publish_date",
        "dlc_or_expansion",
        "parent_game",
        "hidden",
        "fg_game",
        "source_game_id",
        ("source_id", "source_url"),
        ("last_modified_date", "change_hash"),
    )

    def get_form(self, request: HttpRequest, obj: Optional[FetchedGame] = None, **kwargs: Any) -> ModelForm:
        # just save obj reference for future processing in Inline
        request._current_object = obj
        return super().get_form(request, obj, **kwargs)

    # When rendering the platforms list of the fetched game, do some custom filtering
    def formfield_for_manytomany(self, db_field: Field, request: HttpRequest, **kwargs: Any) -> Form_Field:
        if db_field.name == "platforms":
            # Hidden platforms out (un-hide first if want to use)
            kwargs["queryset"] = FetchedPlatform.objects.filter(hidden=False)
            # Only from same source
            if request._current_object:
                kwargs["queryset"] = kwargs["queryset"].filter(source_id=request._current_object.source_id)
            kwargs["queryset"] = kwargs["queryset"].order_by(Lower("name"))
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field: Field, request: HttpRequest, **kwargs: Any) -> Form_Field:
        if db_field.name == "parent_game":
            # Hidden games out
            kwargs["queryset"] = FetchedGame.objects.filter(hidden=False)
            # Only from same source
            if request._current_object:
                kwargs["queryset"] = kwargs["queryset"].filter(source_id=request._current_object.source_id)
            kwargs["queryset"] = kwargs["queryset"].order_by(Lower("name"))
        elif db_field.name == "fg_game":
            kwargs["queryset"] = Game.objects.order_by(Lower("name"))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_urls(self) -> List[str]:
        urls = super().get_urls()
        my_urls = [
            path("import_setup/", self.admin_site.admin_view(self.import_setup_view), name="game_import_setup"),
            path("import/batch", self.admin_site.admin_view(self.import_batch_view), name="game_import_batch"),
            path("import/", self.admin_site.admin_view(self.import_view), name="game_import"),
        ]
        return cast(List[str], my_urls + urls)


class FetchedPlatformAdmin(FetchedPlatformAdminViewsMixin, FGModelAdmin):
    list_display = ["name", hyperlink_fg_platform, hyperlink_source_url, "last_modified_date", "source_id", "hidden"]
    list_filter = ["last_modified_date", HiddenByDefaultFilter, NotImportedFetchedPlatforms, "source_id"]
    search_fields = ["name"]
    readonly_fields = ["last_modified_date", "change_hash"]
    ordering = ["-last_modified_date", "source_id", "name"]
    actions = [hide_fetched_items, import_fetched_items]

    fields = (
        "name",
        "shortname",
        "publish_date",
        "hidden",
        "fg_platform",
        "source_platform_id",
        ("source_id", "source_url"),
        ("last_modified_date", "change_hash"),
    )

    def get_urls(self) -> List[str]:
        urls = super().get_urls()
        my_urls = [
            path("import_setup/", self.admin_site.admin_view(self.import_setup_view), name="platform_import_setup"),
            path("import/batch", self.admin_site.admin_view(self.import_batch_view), name="platform_import_batch"),
            path("import/", self.admin_site.admin_view(self.import_view), name="platform_import"),
        ]
        return cast(List[str], my_urls + urls)
