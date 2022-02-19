import json
from typing import Any, Dict, List

from core.models import Game, Platform
from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = "Exports all Games and Platforms"

    def add_arguments(self, parser: CommandParser) -> None:
        pass

    def handle(self, *args: Any, **options: Dict) -> None:
        self._export_games()
        self._export_platforms()

    def _export_games(self) -> None:
        filename = "games.json"
        counter = 0
        games: List[Dict] = []

        self.stdout.write("> Exporting Games")

        for game in Game.objects.all():
            counter += 1

            games.append(
                {
                    "id": game.id,
                    "name": game.name,
                    "publish_date": game.publish_date,
                    "dlc_or_expansion": game.dlc_or_expansion,
                    "platforms": [platform.id for platform in game.platforms.only("id")],
                    "parent_game": game.parent_game.id if game.parent_game else None,
                    "urls": game.urls_dict,
                    "name_for_search": game.name_for_search,
                }
            )

            self.stdout.write(".", ending="")
            if counter % 50 == 0:
                self.stdout.write(" {}".format(counter))

        print("\nRead {} Games".format(counter))

        with open(filename, "w") as file_handle:
            json.dump(games, file_handle, separators=(",\n", ":"))

        print("Written Games to {}", filename)

    def _export_platforms(self) -> None:
        filename = "platforms.json"
        counter = 0
        platforms: List[Dict] = []

        self.stdout.write("> Reading Platforms")

        for platform in Platform.objects.all():
            counter += 1

            platforms.append(
                {
                    "id": platform.id,
                    "name": platform.name,
                    "shortname": platform.shortname,
                    "publish_date": platform.publish_date,
                }
            )

            self.stdout.write(".", ending="")
            if counter % 50 == 0:
                self.stdout.write(" {}".format(counter))

        print("\nRead {} Platforms".format(counter))

        with open(filename, "w") as file_handle:
            json.dump(platforms, file_handle, separators=(",\n", ":"))

        print("Written Platforms to {}", filename)
