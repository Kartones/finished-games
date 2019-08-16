from typing import (Any, cast, Dict)

from django.conf import settings
from django.core.management.base import (BaseCommand, CommandParser)

from catalogsources.managers import (GameImportSaveError, ImportManager)
from catalogsources.models import FetchedGame
from finishedgames import constants


class Command(BaseCommand):
    help = "Imports all Fetched Games that have no corresponding FG Game (new imports on the main plataform"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("max_items", type=int)

    def handle(self, *args: Any, **options: Dict) -> None:
        self.import_games(max_items=cast(int, options["max_items"]))

    def import_games(self, max_items: int) -> None:
        if max_items < 1:
            max_items = 1

        fetched_games = FetchedGame.objects  \
                                   .filter(fg_game__isnull=True, hidden=False)[:max_items]

        self.stdout.write("> Going to import {} new Fetched Games:".format(self.style.WARNING(str(len(fetched_games)))))

        source_display_names = {
            key: settings.CATALOG_SOURCES_ADAPTERS[key][constants.ADAPTER_DISPLAY_NAME]
            for key in settings.CATALOG_SOURCES_ADAPTERS.keys()
        }

        for fetched_game in fetched_games:
            self.stdout.write("{} ({}) ".format(fetched_game.name, fetched_game.id), ending="")

            available_platforms = []  # List[int]
            for platform in fetched_game.platforms.all():
                if platform.fg_platform:
                    available_platforms.append(platform.fg_platform.id)

            try:
                error_message = ""
                ImportManager.import_fetched_game(
                    name=fetched_game.name,
                    publish_date_string=fetched_game.publish_date,
                    dlc_or_expansion=fetched_game.dlc_or_expansion,
                    platforms=available_platforms,
                    fetched_game_id=fetched_game.id,
                    game_id=None,
                    parent_game_id=None,
                    source_display_name=source_display_names[fetched_game.source_id],
                    source_url=fetched_game.source_url
                )
            except GameImportSaveError as error:
                error_message = str(error)

            if error_message:
                self.stdout.write(self.style.ERROR("✗ - {}".format(error_message)))
            else:
                self.stdout.write(self.style.SUCCESS("✓"))

        self.stdout.write("> Finished importing new Fetched Games")
