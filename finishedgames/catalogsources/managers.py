from typing import (List, Optional)

from catalogsources.models import (FetchedGame, FetchedPlatform)
from core.models import (Game, Platform)


class GameImportSaveError(Exception):
    pass


class PlatformImportSaveError(Exception):
    pass


class ImportManager():

    @staticmethod
    def import_fetched_game(
        name: str, publish_date_string: str, dlc_or_expansion: bool, platforms: List[int], fetched_game_id: int,
        game_id: int = None, parent_game_id: int = None, source_display_name: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> None:
        if game_id:
            game = Game.objects \
                        .filter(id=game_id) \
                        .get()
        else:
            game = Game()

        game.name = name
        game.publish_date = publish_date_string
        game.dlc_or_expansion = dlc_or_expansion
        if parent_game_id:
            game.parent_game_id = parent_game_id
        if source_display_name and source_url:
            game.upsert_url(display_name=source_display_name, url=source_url)

        try:
            game.save()
        except Exception as error:
            raise GameImportSaveError(str(error))

        # many to many need an id to be set, so platforms added after initial save
        try:
            platforms = Platform.objects.filter(id__in=platforms)
            game.platforms.set(platforms)
            game.save()
        except Exception as error:
            raise GameImportSaveError(str(error))

        # Update always linked game
        fetched_game = FetchedGame.objects \
                                  .filter(id=fetched_game_id) \
                                  .get()
        fetched_game.fg_game_id = game.id
        fetched_game.save(update_fields=["fg_game_id"])

    @staticmethod
    def import_fetched_platform(
        name: str, shortname: str, publish_date_string: str, fetched_platform_id: int, platform_id: int = None
    ) -> None:
        if platform_id:
            platform = Platform.objects \
                               .filter(id=platform_id) \
                               .get()
        else:
            platform = Platform()

        platform.name = name
        platform.shortname = shortname
        platform.publish_date = publish_date_string
        try:
            platform.save()
        except Exception as error:
            raise PlatformImportSaveError(str(error))

        # Update always linked platform
        fetched_platform = FetchedPlatform.objects \
                                          .filter(id=fetched_platform_id) \
                                          .get()
        fetched_platform.fg_platform_id = platform.id
        fetched_platform.save(update_fields=["fg_platform_id"])
