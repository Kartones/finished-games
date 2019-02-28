import time
from typing import (Any, cast, Dict, List, Tuple)

from django.core.management.base import (BaseCommand, CommandParser)

from catalogsources.management.helpers import (source_class_from_id, wait_if_needed)
from catalogsources.models import (FetchedGame, FetchedPlatform)


class Command(BaseCommand):
    help = "Fetches games from specified source ids"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("source", type=str)
        parser.add_argument("platforms", nargs="+", type=int)

    def handle(self, *args: Any, **options: Dict) -> None:
        self._fetch_source(source_id=cast(str, options["source"]), platforms=cast(List[int], options["platforms"]))

    def _fetch_source(self, source_id: str, platforms: List[int]) -> None:
        had_errors = False
        self.stdout.write(self.style.WARNING(
            "> Started fetching games from '{source}' and source platform ids: {platforms}".format(
                source=source_id, platforms=platforms)
        ))

        adapter_class = source_class_from_id(source_id)

        with adapter_class() as adapter:
            for platform_id in platforms:
                while adapter.has_more_items():
                    if adapter.total_results != adapter.UNKOWN_TOTAL_RESULTS_VALUE:
                        total = adapter.total_results
                    else:
                        total = "-"
                    self.stdout.write("\n>fetch call (platform_id {id}): {current}/{total}".format(
                        id=platform_id, current=adapter.next_offset, total=total))

                    time_start = time.perf_counter()
                    games = adapter.fetch_games_block(platform_id=platform_id)
                    self._upsert_results(results=games)
                    time_end = time.perf_counter()

                    if adapter.has_errored():
                        had_errors = True
                        self.stdout.write(self.style.ERROR("\nERROR: {}".format(adapter.error_info())))
                    wait_if_needed(time_start=time_start, time_end=time_end)
                adapter.reset()

            self.stdout.write("")

        if had_errors:
            self.stdout.write(self.style.WARNING("> Finished fetching '{}' with errors".format(source_id)))
        else:
            self.stdout.write(self.style.SUCCESS("> Finished fetching '{}'".format(source_id)))

    def _upsert_results(self, results: List[Tuple[FetchedGame, List[FetchedPlatform]]]) -> None:
        errors = []
        count = 0

        for (game, platforms) in results:
            self.stdout.write("{}:".format(game.source_game_id), ending="")

            try:
                existing_game = FetchedGame.objects.get(
                    source_game_id=game.source_game_id, source_id=game.source_id
                )
                existing_game.name = game.name
                existing_game.source_game_id = game.source_game_id
                existing_game.source_id = game.source_id
                existing_game.source_url = game.source_url
                # TODO: publish_date ?
                existing_game.platforms.set(platforms)
                last_modified_date = existing_game.last_modified_date
                existing_game.save()
                if existing_game.last_modified_date != last_modified_date:
                    self.stdout.write(self.style.SUCCESS("☑  "), ending="")
                else:
                    self.stdout.write(self.style.WARNING("☐  "), ending="")
            except FetchedGame.DoesNotExist:
                game.save()
                # Need to have an id before can change a many-to-many field
                game.platforms.set(platforms)
                game.save()
                self.stdout.write(self.style.SUCCESS("✓  "), ending="")
            except Exception as error:
                errors.append(str(error))
                self.stdout.write(self.style.ERROR("✗  "), ending="")

            count += 1
            if count % 10 == 0:
                self.stdout.write("")

        if errors:
            self.stdout.write(self.style.ERROR("\nErrors:"))
            for error_item in errors:
                self.stdout.write(self.style.ERROR(error_item))
