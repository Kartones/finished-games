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

        self.default_publish_date = adapter_class.DEFAULT_PUBLISH_DATE

        with adapter_class(stdout=self.stdout, stdout_color_style=self.style) as adapter:
            for platform_id in platforms:
                # For now at least, if fails gathering a platform, try with next one
                while adapter.has_more_items() and not had_errors:
                    if adapter.total_results != adapter.UNKOWN_TOTAL_RESULTS_VALUE:
                        total = adapter.total_results
                    else:
                        total = "-"
                    self.stdout.write("\n> Fetch call (platform_id {id}): {current}/{total}".format(
                        id=platform_id, current=adapter.next_offset, total=total))

                    time_start = time.perf_counter()
                    games = adapter.fetch_games_block(platform_id=platform_id)
                    self._upsert_results(results=games)
                    time_end = time.perf_counter()

                    had_errors = adapter.has_errored()
                    wait_if_needed(time_start=time_start, time_end=time_end)

                adapter.reset()
                had_errors = False

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
                if game.publish_date != self.default_publish_date:
                    existing_game.publish_date = game.publish_date
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
