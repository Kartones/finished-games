from typing import Any, Dict, cast

from catalogsources.managers import GameImportSaveError, ImportManager
from catalogsources.models import FetchedGame
from core.models import UNKNOWN_PUBLISH_DATE
from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from finishedgames import constants


class Command(BaseCommand):
    help = "Imports all Fetched Games that have no corresponding FG Game (new imports on the main plataform"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("max_items", type=int)
        parser.add_argument(
            "--exclude_unreleased",
            action="store_true",
            help="Exclude titles whose release date is unknown (set to 1970)",
        )

    def handle(self, *args: Any, **options: Dict) -> None:
        self.import_games(
            max_items=cast(int, options["max_items"]), exclude_unreleased=bool(options.get("exclude_unreleased", False))
        )

    def import_games(self, max_items: int, exclude_unreleased: bool) -> None:
        imports_ok_count = 0
        imports_ko_count = 0

        if max_items < 1:
            max_items = 1

        fetched_games = FetchedGame.objects.filter(fg_game__isnull=True, hidden=False)
        if exclude_unreleased:
            fetched_games.filter(publish_date__gt=UNKNOWN_PUBLISH_DATE)
            self.stdout.write("> Excluding unreleased or unknown release date Fetched Games")
        fetched_games = fetched_games[:max_items]

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
                    cover=fetched_game.cover,
                    game_id=None,
                    parent_game_id=None,
                    source_display_name=source_display_names[fetched_game.source_id],
                    source_url=fetched_game.source_url,
                )
            except GameImportSaveError as error:
                error_message = str(error)

            if error_message:
                self.stdout.write(self.style.ERROR("✗ - {}".format(error_message)))
                imports_ko_count += 1
            else:
                self.stdout.write(self.style.SUCCESS("✓"))
                imports_ok_count += 1

        self.stdout.write(
            "> Finished importing new Fetched Games (OK: {} KO: {})".format(imports_ok_count, imports_ko_count)
        )
