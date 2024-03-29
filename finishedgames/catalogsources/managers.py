import re
from typing import List, Optional, Tuple, cast

from catalogsources.helpers import clean_string_field
from catalogsources.models import FetchedGame, FetchedPlatform
from core.models import UNKNOWN_PUBLISH_DATE, Game, Platform
from django.conf import settings

from finishedgames import constants


class GameImportSaveError(Exception):
    pass


class PlatformImportSaveError(Exception):
    pass


class ImportManager:

    # Cap certain heavy operations to a reasonable number of items
    MAX_IMPORT_ITEMS = 100

    @staticmethod
    def import_fetched_game(
        platforms: List[int],
        fetched_game_id: int,
        name: Optional[str] = None,
        publish_date_string: Optional[str] = None,
        dlc_or_expansion: Optional[bool] = None,
        game_id: Optional[int] = None,
        parent_game_id: Optional[int] = None,
        source_display_name: Optional[str] = None,
        source_url: Optional[str] = None,
        update_fields_filter: Optional[List[str]] = None,
    ) -> None:
        if game_id:
            game = Game.objects.filter(id=game_id).get()
        else:
            game = Game()

        include_all_fields = not game_id or update_fields_filter is None

        # cast is like a NOP outside type checking
        if include_all_fields or "name" in cast(List[str], update_fields_filter):
            if not name:
                raise GameImportSaveError("Name field missing")
            game.name = clean_string_field(name)
        if include_all_fields or "publish_date" in cast(List[str], update_fields_filter):
            if not publish_date_string:
                raise GameImportSaveError("Publish Date field missing")
            game.publish_date = publish_date_string
        if include_all_fields or "dlc_or_expansion" in cast(List[str], update_fields_filter):
            if dlc_or_expansion is None:
                raise GameImportSaveError("DLC field missing")
            game.dlc_or_expansion = dlc_or_expansion
        if include_all_fields or "parent_game" in cast(List[str], update_fields_filter):
            if parent_game_id:
                game.parent_game_id = parent_game_id
            else:
                game.parent_game = None

        # update always the url for this source
        if source_display_name and source_url:
            game.upsert_url(display_name=source_display_name, url=source_url)

        try:
            game.save()
        except Exception as error:
            raise GameImportSaveError(str(error))

        # many to many need an id to be set, so platforms added after initial save
        if include_all_fields or "platforms" in cast(List[str], update_fields_filter):
            try:
                platforms = Platform.objects.filter(id__in=platforms)
                # Add new platforms if proceed, not removing existing ones (and if already added, nothing happens).
                # Also, because one catalog source might only include a subset of the platforms for a game.
                game.platforms.add(*platforms)
                game.save()
            except Exception as error:
                raise GameImportSaveError(str(error))

        # Update always linked game
        fetched_game = FetchedGame.objects.filter(id=fetched_game_id).get()
        fetched_game.fg_game_id = game.id
        fetched_game.mark_as_synchronized()
        fetched_game.save(update_fields=["fg_game_id", "last_sync_date"])

    @staticmethod
    def import_fetched_platform(
        name: str,
        shortname: str,
        publish_date_string: str,
        fetched_platform_id: int,
        platform_id: Optional[int] = None,
        update_fields_filter: Optional[List[str]] = None,
    ) -> None:
        if platform_id:
            platform = Platform.objects.filter(id=platform_id).get()
        else:
            platform = Platform()

        include_all_fields = not platform_id or update_fields_filter is None

        # cast is like a NOP outside type checking
        if include_all_fields or "name" in cast(List[str], update_fields_filter):
            platform.name = clean_string_field(name)
        if include_all_fields or "shortname" in cast(List[str], update_fields_filter):
            platform.shortname = clean_string_field(shortname)
        if include_all_fields or "publish_date" in cast(List[str], update_fields_filter):
            platform.publish_date = publish_date_string

        try:
            platform.save()
        except Exception as error:
            raise PlatformImportSaveError(str(error))

        # Update always linked platform
        fetched_platform = FetchedPlatform.objects.filter(id=fetched_platform_id).get()
        fetched_platform.fg_platform_id = platform.id
        fetched_platform.save(update_fields=["fg_platform_id"])

    @classmethod
    def import_fetched_games_fixing_duplicates_appending_publish_date(cls, fetched_game_ids: List[int]) -> List[str]:
        source_display_names = {
            key: settings.CATALOG_SOURCES_ADAPTERS[key][constants.ADAPTER_DISPLAY_NAME]
            for key in settings.CATALOG_SOURCES_ADAPTERS.keys()
        }
        errors = []  # type: List[str]

        for fetched_game_id in fetched_game_ids:
            fetched_game = FetchedGame.objects.filter(id=fetched_game_id).get()

            available_platform_ids = []  # List[int]
            for platform in fetched_game.platforms.all():
                if platform.fg_platform:
                    available_platform_ids.append(platform.fg_platform.id)

            should_retry_import, error_message = cls._attempt_import(
                fetched_game, available_platform_ids, fetched_game_id, source_display_names[fetched_game.source_id]
            )
            if error_message:
                errors.append(error_message)

            if should_retry_import:
                fixed_name = "{} ({})".format(fetched_game.name, fetched_game.publish_date)
                try:
                    cls.import_fetched_game(
                        name=fixed_name,
                        publish_date_string=str(fetched_game.publish_date),
                        dlc_or_expansion=fetched_game.dlc_or_expansion,
                        platforms=available_platform_ids,
                        fetched_game_id=fetched_game_id,
                        # TODO: include parent_game
                        source_display_name=source_display_names[fetched_game.source_id],
                        source_url=fetched_game.source_url,
                    )
                except GameImportSaveError as error:
                    errors.append("'{}': {}".format(fetched_game.name, error))

        return errors

    @classmethod
    def import_fetched_games_fixing_duplicates_appending_platform(cls, fetched_game_ids: List[int]) -> List[str]:
        source_display_names = {
            key: settings.CATALOG_SOURCES_ADAPTERS[key][constants.ADAPTER_DISPLAY_NAME]
            for key in settings.CATALOG_SOURCES_ADAPTERS.keys()
        }

        errors = []  # type: List[str]

        for fetched_game_id in fetched_game_ids:
            fetched_game = FetchedGame.objects.filter(id=fetched_game_id).get()

            available_platform_ids = []  # List[int]
            first_available_platform_shortname = None
            for platform in fetched_game.platforms.all():
                if platform.fg_platform:
                    available_platform_ids.append(platform.fg_platform.id)
                    if first_available_platform_shortname is None:
                        first_available_platform_shortname = platform.fg_platform.shortname

            should_retry_import, error_message = cls._attempt_import(
                fetched_game, available_platform_ids, fetched_game_id, source_display_names[fetched_game.source_id]
            )
            if error_message:
                errors.append(error_message)

            if should_retry_import:
                fixed_name = "{} ({})".format(fetched_game.name, first_available_platform_shortname)
                try:
                    cls.import_fetched_game(
                        name=fixed_name,
                        publish_date_string=str(fetched_game.publish_date),
                        dlc_or_expansion=fetched_game.dlc_or_expansion,
                        platforms=available_platform_ids,
                        fetched_game_id=fetched_game_id,
                        # TODO: include parent_game
                        source_display_name=source_display_names[fetched_game.source_id],
                        source_url=fetched_game.source_url,
                    )
                except GameImportSaveError as error:
                    errors.append("'{}': {}".format(fetched_game.name, error))

        return errors

    @classmethod
    def import_fetched_games_linking_if_name_and_year_matches(cls, fetched_game_ids: List[int]) -> List[str]:
        source_display_names = {
            key: settings.CATALOG_SOURCES_ADAPTERS[key][constants.ADAPTER_DISPLAY_NAME]
            for key in settings.CATALOG_SOURCES_ADAPTERS.keys()
        }
        errors = []  # type: List[str]

        for fetched_game_id in fetched_game_ids:
            fetched_game = FetchedGame.objects.filter(id=fetched_game_id).get()

            game_id = None  # Optional[int]
            available_platform_ids = []  # List[int]
            for platform in fetched_game.platforms.all():
                if platform.fg_platform:
                    available_platform_ids.append(platform.fg_platform.id)

            source_display_name = source_display_names[fetched_game.source_id]

            should_retry_import, error_message = cls._attempt_import(
                fetched_game, available_platform_ids, fetched_game_id, source_display_name
            )
            if error_message:
                errors.append(error_message)

            # If we don't know the date, don't touch it
            if should_retry_import and fetched_game.publish_date != UNKNOWN_PUBLISH_DATE:
                existing_game = Game.objects.only("id").filter(name=fetched_game.name).get()
                game_id = existing_game.id

                if fetched_game.publish_date == existing_game.publish_date:
                    cls.import_fetched_game(
                        name=fetched_game.name,
                        publish_date_string=str(fetched_game.publish_date),
                        dlc_or_expansion=fetched_game.dlc_or_expansion,
                        platforms=available_platform_ids,
                        game_id=game_id,
                        fetched_game_id=fetched_game_id,
                        # TODO: include parent_game
                        source_display_name=source_display_name,
                        source_url=fetched_game.source_url,
                        update_fields_filter=["publish_date", "dlc_or_expansion", "platforms"],
                    )

        return errors

    @classmethod
    def sync_fetched_games(cls, fetched_game_ids: List[int], force_sync: bool = False) -> Tuple[int, int]:
        source_display_names = {
            key: settings.CATALOG_SOURCES_ADAPTERS[key][constants.ADAPTER_DISPLAY_NAME]
            for key in settings.CATALOG_SOURCES_ADAPTERS.keys()
        }
        count_synced = 0
        count_skipped = 0

        for fetched_game_id in fetched_game_ids:
            fetched_game = FetchedGame.objects.filter(id=fetched_game_id).get()

            if not fetched_game.can_sync or (fetched_game.is_sync and not force_sync):
                count_skipped += 1
                continue

            available_platforms = [platform.id for platform in fetched_game.fg_game.platforms.all()]  # type: List[int]

            for platform in fetched_game.platforms.all():
                if platform.fg_platform and (platform.fg_platform.id not in available_platforms):
                    available_platforms.append(platform.fg_platform.id)

            if fetched_game.publish_date > fetched_game.fg_game.publish_date:
                publish_date = fetched_game.publish_date
            else:
                publish_date = fetched_game.fg_game.publish_date

            source_display_name = source_display_names[fetched_game.source_id]

            cls.import_fetched_game(
                publish_date_string=publish_date,
                platforms=available_platforms,
                game_id=fetched_game.fg_game.id,
                fetched_game_id=fetched_game_id,
                source_display_name=source_display_name,
                source_url=fetched_game.source_url,
                update_fields_filter=["publish_date", "platforms"],
            )
            count_synced += 1

        return count_synced, count_skipped

    @classmethod
    def _attempt_import(
        cls,
        fetched_game: FetchedGame,
        available_platform_ids: List[int],
        fetched_game_id: int,
        source_display_name: str,
    ) -> Tuple[bool, str]:
        error_message = ""
        import_failed_name_exists = False

        try:
            cls.import_fetched_game(
                name=fetched_game.name,
                publish_date_string=str(fetched_game.publish_date),
                dlc_or_expansion=fetched_game.dlc_or_expansion,
                platforms=available_platform_ids,
                fetched_game_id=fetched_game_id,
                # TODO: include parent_game
                source_display_name=source_display_name,
                source_url=fetched_game.source_url,
            )
        except GameImportSaveError as error:
            if re.match(r"UNIQUE constraint failed(.*)\.name", str(error)):
                import_failed_name_exists = True
            else:
                error_message = "'{}': {}".format(fetched_game.name, error)

        return import_failed_name_exists, error_message
