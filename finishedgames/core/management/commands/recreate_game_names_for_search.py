from typing import Any, Dict

from core.models import Game
from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = "(Re)Creates all Game searchable names"

    def add_arguments(self, parser: CommandParser) -> None:
        pass

    def handle(self, *args: Any, **options: Dict) -> None:
        games_count = Game.objects.count()
        games = Game.objects.all()

        counter = 0

        self.stdout.write("Recreating searchable names for Games")

        for game in games:
            game.save()
            counter += 1
            if counter % 50 == 0:
                self.stdout.write(" {:.3f}%".format(counter * 100 / games_count))

        self.stdout.write("\nFinished")
