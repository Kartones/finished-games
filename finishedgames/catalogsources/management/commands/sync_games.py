from typing import Any, Dict, cast

from catalogsources.managers import ImportManager
from catalogsources.models import FetchedGame
from django.core.management.base import BaseCommand, CommandParser
from django.db.models import F


class Command(BaseCommand):
    help = "Syncs already imported, not hidden, Fetched Games cover"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("max_items", type=int)

    def handle(self, *args: Any, **options: Dict) -> None:
        max_items = cast(int, options["max_items"])
        if max_items < 1:
            max_items = 1

        self.stdout.write(self.style.WARNING("> Going to sync up to {} fetched games".format(max_items)))

        fetched_games = FetchedGame.objects.filter(hidden=False, fg_game__isnull=False).exclude(
            last_sync_date=F("last_modified_date")
        )

        fetched_game_ids = fetched_games.values_list("id", flat=True)[:max_items]

        count_synced, count_skipped = ImportManager.sync_fetched_games(fetched_game_ids)

        self.stdout.write("> Finished syncing games (OK: {} KO: {})".format(count_synced, count_skipped))
