from typing import Any, Dict

from core.models import Game
from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from django.urls import reverse


class Command(BaseCommand):
    help = "Lists all Games with 'urls' field unpopulated"

    def add_arguments(self, parser: CommandParser) -> None:
        pass

    def handle(self, *args: Any, **options: Dict) -> None:
        games = Game.objects.filter(urls="")

        host = settings.ALLOWED_HOSTS[-1]
        if settings.DEBUG:
            protocol = "http"
            # NOTE: This is the same port configured in Docker
            port = ":5000"
        else:
            protocol = "https"
            # assumes 443
            port = ""

        for game in games:
            url = "{protocol}://{host}{port}{path}".format(
                protocol=protocol, host=host, port=port, path=reverse("admin:core_game_change", args=[game.id])
            )
            self.stdout.write("{} - {}".format(game.name, url))
