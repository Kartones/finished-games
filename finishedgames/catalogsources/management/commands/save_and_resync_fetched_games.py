from typing import Any, Dict, List

from catalogsources.models import FetchedGame
from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = "Saves and Resyncs all Fetched Games that unsync due to the saving"

    def add_arguments(self, parser: CommandParser) -> None:
        pass

    def handle(self, *args: Any, **options: Dict) -> None:
        block_size = 100

        fetched_games = FetchedGame.objects.filter(hidden=False)

        self.sanitize(fetched_games=fetched_games, block_size_for_feedback=block_size)

        self.stdout.write("> Finished")

    def sanitize(self, fetched_games: List[FetchedGame], block_size_for_feedback: int) -> None:
        count = 0
        self.stdout.write(self.style.WARNING("> Going to sanitize {} fetched games".format(len(fetched_games))))
        for fetched_game in fetched_games:
            # this will update change hash and last modified date if proceeds
            fetched_game.save()

            if not fetched_game.is_sync and fetched_game.can_sync:
                fetched_game.mark_as_synchronized()
                fetched_game.save()

            count += 1
            if count % block_size_for_feedback == 0:
                self.stdout.write(str(count))
