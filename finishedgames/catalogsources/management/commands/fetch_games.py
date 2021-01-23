from typing import Dict, List, Tuple, cast

from catalogsources.helpers import clean_string_field
from catalogsources.management.helpers import TimeProfiler, source_class_from_id, wait_if_needed
from catalogsources.models import FetchedGame, FetchedPlatform
from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = "Fetches games from specified source ids"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("source", type=str)
        # NOTE: Offset only applies to 1st platform to fetch games from, remaining ones will start at offset 0
        parser.add_argument("offset", type=int)
        parser.add_argument("platforms", nargs="+", type=int)

    def handle(self, *args: str, **options: Dict) -> None:
        self._display_legend()
        self._fetch_source(
            source_id=cast(str, options["source"]),
            platforms=cast(List[int], options["platforms"]),
            initial_offset=cast(int, options["offset"]),
        )

    def _fetch_source(self, source_id: str, platforms: List[int], initial_offset: int = 0) -> None:
        had_errors = False
        self.stdout.write(
            self.style.WARNING(
                "> Started fetching games from '{source}' and source platform ids: {platforms}".format(
                    source=source_id, platforms=platforms
                )
            )
        )

        adapter_class = source_class_from_id(source_id)
        self.default_publish_date = adapter_class.DEFAULT_PUBLISH_DATE

        if not self._source_has_plaforms(source_id):
            self.stdout.write(
                self.style.ERROR(
                    "You must first fetch platforms from source '{}' as games needs to be linked to them".format(
                        source_id
                    )
                )
            )
            exit(1)

        with adapter_class(stdout=self.stdout, stdout_color_style=self.style) as adapter:
            self.stdout.write(
                self.style.WARNING("> Initial Offset:{}  Batch size:{}".format(initial_offset, adapter.batch_size()))
            )

            if initial_offset > 0:
                adapter.set_offset(initial_offset)

            try:
                for platform_id in platforms:
                    # For now at least, if fails gathering a platform, try with next one
                    while adapter.has_more_items() and not had_errors:
                        if adapter.total_results != adapter.UNKOWN_TOTAL_RESULTS_VALUE:
                            total = adapter.total_results
                        else:
                            total = "-"
                        self.stdout.write(
                            "\n> Fetch call (platform_id {id}): {current}/{total}".format(
                                id=platform_id, current=adapter.next_offset, total=total
                            )
                        )

                        with TimeProfiler(use_performance_counter=True) as profiler:
                            games = adapter.fetch_games_block(platform_id=platform_id)
                            self._upsert_results(results=games)
                        had_errors = adapter.has_errored()
                        wait_if_needed(profiler.duration)

                    adapter.reset()
                    had_errors = False

                self.stdout.write("")
            except KeyboardInterrupt:
                had_errors = True
                self.stdout.write(self.style.WARNING("> Keyboard interrupt issued"))

        if had_errors:
            self.stdout.write(self.style.WARNING("> Finished fetching '{}' with errors".format(source_id)))
        else:
            self.stdout.write(self.style.SUCCESS("> Finished fetching '{}'".format(source_id)))

    def _upsert_results(self, results: List[Tuple[FetchedGame, List[FetchedPlatform]]]) -> None:
        errors = []
        count = 0

        for (game, platforms) in results:
            self.stdout.write("{}:".format(game.source_game_id), ending="")

            game.name = clean_string_field(game.name)

            try:
                existing_game = FetchedGame.objects.get(source_game_id=game.source_game_id, source_id=game.source_id)
                existing_game.name = game.name
                if not existing_game.cover and game.cover is not None:
                    existing_game.cover = game.cover
                existing_game.source_game_id = game.source_game_id
                existing_game.source_id = game.source_id
                existing_game.source_url = game.source_url
                if game.publish_date != self.default_publish_date:
                    existing_game.publish_date = game.publish_date
                existing_game.platforms.set(platforms)
                last_modified_date = existing_game.last_modified_date
                existing_game.save()
                if existing_game.last_modified_date != last_modified_date:
                    self.stdout.write(self.style.SUCCESS("☑ "), ending="")
                else:
                    self.stdout.write("☐ ", ending="")
            except FetchedGame.DoesNotExist:
                game.save()
                # Need to have an id before can change a many-to-many field
                game.platforms.set(platforms)
                game.save()
                self.stdout.write(self.style.SUCCESS("✓ "), ending="")
            except Exception as error:
                errors.append(str(error))
                self.stdout.write(self.style.ERROR("✗ "), ending="")

            count += 1
            if count % 10 == 0:
                self.stdout.write("")

        if errors:
            self.stdout.write(self.style.ERROR("\nErrors:"))
            for error_item in errors:
                self.stdout.write(self.style.ERROR(error_item))

    @staticmethod
    def _source_has_plaforms(source_id: str) -> bool:
        return cast(bool, FetchedPlatform.objects.filter(source_id=source_id).count() > 0)

    def _display_legend(self) -> None:
        self.stdout.write(self.style.WARNING("Legend: "))
        self.stdout.write(self.style.SUCCESS("✓ "), ending="")
        self.stdout.write("Added new game")
        self.stdout.write(self.style.SUCCESS("☑ "), ending="")
        self.stdout.write("Updated existing game (new changes)")
        self.stdout.write("☐ ", ending="")
        self.stdout.write("Existing game not updated (no changes)")
        self.stdout.write(self.style.ERROR("✗ "), ending="")
        self.stdout.write("Error adding/updating game")
        self.stdout.write(self.style.WARNING("-------\n"))
