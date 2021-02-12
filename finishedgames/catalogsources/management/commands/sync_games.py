from typing import Any, Dict, List, cast

from catalogsources.managers import GameImportSaveError, ImportManager
from catalogsources.models import FetchedGame
from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from django.db.models import F

from finishedgames import constants


# TODO: generalize to sync whatever fields I specify
class Command(BaseCommand):
    help = "Syncs already imported, not hidden, Fetched Games cover"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("max_items", type=int)

    def handle(self, *args: Any, **options: Dict) -> None:
        imports_ok_count = 0
        imports_ko_count = 0
        count = 0

        max_items = cast(int, options["max_items"])
        if max_items < 1:
            max_items = 1

        self.stdout.write(self.style.WARNING("> Going to sync up to {} fetched games".format(max_items)))

        source_display_names = {
            key: settings.CATALOG_SOURCES_ADAPTERS[key][constants.ADAPTER_DISPLAY_NAME]
            for key in settings.CATALOG_SOURCES_ADAPTERS.keys()
        }

        fetched_games = FetchedGame.objects.filter(hidden=False, fg_game__isnull=False).exclude(
            last_sync_date=F("last_modified_date")
        )
        # cut to a threshold of as much as 50% failures
        fetched_games = fetched_games[: max_items * 2]

        for fetched_game in fetched_games:
            if count >= max_items:
                break

            self.stdout.write("{} ({}) ".format(fetched_game.name, fetched_game.id), ending="")

            available_platforms = [platform.id for platform in fetched_game.fg_game.platforms.all()]  # type: List[int]

            for platform in fetched_game.platforms.all():
                if platform.fg_platform and (platform.fg_platform.id not in available_platforms):
                    available_platforms.append(platform.fg_platform.id)

            if fetched_game.publish_date > fetched_game.fg_game.publish_date:
                publish_date = fetched_game.publish_date
            else:
                publish_date = fetched_game.fg_game.publish_date

            try:
                error_message = ""
                ImportManager.import_fetched_game(
                    fetched_game_id=fetched_game.id,
                    game_id=fetched_game.fg_game.id,
                    source_display_name=source_display_names[fetched_game.source_id],
                    source_url=fetched_game.source_url,
                    # name=fetched_game.name,
                    publish_date_string=publish_date,
                    # dlc_or_expansion=fetched_game.dlc_or_expansion,
                    platforms=available_platforms,
                    # parent_game_id=None,
                    cover=fetched_game.cover,
                    update_fields_filter=["cover", "publish_date", "platforms"],
                )
            except GameImportSaveError as error:
                error_message = str(error)

            if error_message:
                self.stdout.write(self.style.ERROR("✗ - {}".format(error_message)))
                imports_ko_count += 1
            else:
                self.stdout.write(self.style.SUCCESS("✓"))
                imports_ok_count += 1
                # only count oks towards max items
                count += 1

        self.stdout.write("> Finished importing games (OK: {} KO: {})".format(imports_ok_count, imports_ko_count))
