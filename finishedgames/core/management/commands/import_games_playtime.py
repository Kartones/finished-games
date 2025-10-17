import os
from typing import Any, cast, Dict

from core.models import UserGame
from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = "Imports playtime from files for specified user"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("names_file", type=str, help="File with game names (one per line)")
        parser.add_argument("times_file", type=str, help="File with playtimes in hours (one per line)")
        parser.add_argument("user_id", type=int, help="Finished Games user ID")

    def handle(self, *args: Any, **options: Dict) -> None:
        names_file = cast(str, options["names_file"])
        times_file = cast(str, options["times_file"])
        user_id = cast(int, options["user_id"])

        playtime_dict = self._load_playtime_data(names_file, times_file)
        self._update_user_games(user_id, playtime_dict)

    def _load_playtime_data(self, names_file: str, times_file: str) -> Dict[str, int]:
        """Load game names and playtimes from files and return a dictionary."""
        game_names = []
        playtimes = []

        if not os.path.isfile(names_file):
            self.stderr.write(f"Names file '{names_file}' not found.")
            return {}
        if not os.path.isfile(times_file):
            self.stderr.write(f"Times file '{times_file}' not found.")
            return {}

        with open(names_file, "r", encoding="utf-8") as f:
            game_names = [line.strip() for line in f.readlines()]

        with open(times_file, "r", encoding="utf-8") as f:
            playtimes = [line.strip() for line in f.readlines()]

        playtime_dict: Dict[str, int] = {}
        for name, time_str in zip(game_names, playtimes):
            if not time_str:
                self.stdout.write(f"{name} : empty playtime value, skipping")
                continue
            if not name:
                self.stdout.write(self.style.WARNING(f"Empty game name, skipping"))
                continue

            try:
                hours = float(time_str)
                # we want minutes
                playtime_dict[name] = int(hours * 60)
            except ValueError:
                self.stdout.write(self.style.WARNING(f"{name} : invalid playtime value '{time_str}', skipping"))

        return playtime_dict

    def _update_user_games(self, user_id: int, playtime_dict: Dict[str, int]) -> None:
        """Update UserGame records with playtime data."""
        for game_name, minutes in playtime_dict.items():
            user_game = UserGame.objects.filter(user_id=user_id, game__name=game_name).first()

            if not user_game:
                self.stdout.write(self.style.WARNING(f"{game_name} : game not found for user"))
                continue

            if user_game.minutes_played >= minutes:
                self.stdout.write(f"{game_name} : existing playtime ({user_game.minutes_played}) is greater or equal, skipping update to {minutes}")
                continue

            user_game.minutes_played = minutes
            user_game.save()
            self.stdout.write(self.style.SUCCESS(f"{game_name} : minutes updated to {minutes}"))
