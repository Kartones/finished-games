from typing import Any, Dict, List

from catalogsources.models import FetchedGame
from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = "Resets (removes) covers from all fetched games"

    def add_arguments(self, parser: CommandParser) -> None:
        pass

    def handle(self, *args: Any, **options: Dict) -> None:
        block_size = 100

        # at least don't unsync those without cover
        fetched_games = FetchedGame.objects.filter(cover__isnull=False)

        self.reset_cover(fetched_games=fetched_games, block_size_for_feedback=block_size)

        self.stdout.write("> Finished")

    def reset_cover(self, fetched_games: List[FetchedGame], block_size_for_feedback: int) -> None:
        count = 0
        self.stdout.write(self.style.WARNING("> Going to reset cover of fetched games (doesn't delete cover images)"))
        for fetched_game in fetched_games:
            fetched_game.cover = None
            # this will update change hash and last modified date if proceeds
            fetched_game.save()

            count += 1
            if count % block_size_for_feedback == 0:
                self.stdout.write(str(count))
