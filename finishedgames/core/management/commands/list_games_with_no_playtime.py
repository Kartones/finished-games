from typing import Any, cast, Dict

from core.models import UserGame
from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = "Lists all games with no playtime for a user by status"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("status", type=str, choices=["pending", "abandoned", "finished"])
        parser.add_argument("user_id", type=int)
        parser.add_argument("--output-file", type=str, default=None, help="Write game names to file")

    def handle(self, *args: Any, **options: Dict) -> None:
        status = options["status"]
        user_id = options["user_id"]
        output_file = options.get("output_file", None)

        queryset = UserGame.objects.filter(user_id=user_id, minutes_played=0)

        if status == "pending":
            queryset = queryset.filter(year_finished__isnull=True, abandoned=False)
        elif status == "abandoned":
            queryset = queryset.filter(abandoned=True)
        elif status == "finished":
            queryset = queryset.filter(year_finished__isnull=False, abandoned=False)
        else:
            self.stderr.write(f"Unknown status: {status}")
            return

        queryset = queryset.select_related("game", "platform").order_by("game__name")

        game_names: list[str] = []
        for user_game in queryset:
            output_line = "{} ({})".format(user_game.game.name, user_game.platform.shortname)
            self.stdout.write(output_line)
            game_names.append(user_game.game.name)

        if output_file:
            with open(cast(str, output_file), "w", encoding="utf-8") as f:
                f.write("\n".join(game_names))
