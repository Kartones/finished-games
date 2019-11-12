from typing import Any, Dict, List, Union

from django.core.management.base import BaseCommand, CommandParser
from django.db.utils import IntegrityError

from catalogsources.helpers import clean_string_field
from catalogsources.models import FetchedGame
from core.models import Game


class Command(BaseCommand):
    help = "Sanitizes names of Fetched Games and Games"

    def add_arguments(self, parser: CommandParser) -> None:
        pass

    def handle(self, *args: Any, **options: Dict) -> None:
        block_size = 100
        self.sanitize(games=Game.objects.all(), model_name="Games", block_size_for_feedback=block_size)

    def sanitize(self, games: List[Union[FetchedGame, Game]], model_name: str, block_size_for_feedback: int) -> None:
        count = 0
        self.stdout.write(self.style.WARNING("> Going to sanitize {} {}".format(len(games), model_name)))
        for game in games:
            game.name = clean_string_field(game.name)
            try:
                game.save()
            except IntegrityError as error:
                self.stdout.write(self.style.ERROR("{} - {}".format(game.name, error)))
            count += 1
            if count % block_size_for_feedback == 0:
                self.stdout.write(str(count))
