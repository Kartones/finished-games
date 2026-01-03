from dataclasses import dataclass
import json
from typing import Any, cast, Dict, List, Optional

import requests

from core.models import Game, UserGame
from catalogsources.models import FetchedGame
from catalogsources.helpers import clean_string_field
from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from finishedgames import constants


# TODO: This should also be a parameter
PLATFORM_PC = 3

SOURCE_ID = "steam"

# List of game titles to skip without any output
IGNORED_TITLES: List[str] = [
    "Call of Duty: Modern Warfare 2 (2009) - Multiplayer",
    "Left 4 Dead 2 Demo",
    "METAL GEAR SOLID: MASTER COLLECTION Vol.1 BONUS CONTENT",
    "Manual Samuel - Last Tuesday Edition",
    "Sentinels of the Multiverse",
]

# Mappings to apply before cleaning the title, when searching in the catalog/DB
CATALOG_TITLE_MAPPINGS: Dict[str, str] = {
}

# Mappings to apply after cleaning the title
CLEANED_TITLE_MAPPINGS: Dict[str, str] = {
}

@dataclass
class GameTimeData:
    title: str
    platform_id: int
    minutes_played: int


class Command(BaseCommand):
    help = "Imports Steam game times"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--fg-user-id",
            type=int,
            required=True,
            help="Finished Games user ID",
        )

    def handle(self, *args: Any, **options: Dict) -> None:
        steam_user_id = settings.CATALOG_SOURCES_ADAPTERS[SOURCE_ID][constants.ADAPTER_USER_ID]
        steam_api_key = settings.CATALOG_SOURCES_ADAPTERS[SOURCE_ID][constants.ADAPTER_API_KEY]

        fg_user_id = cast(int, options["fg_user_id"])

        self.stdout.write(f"Going to import Steam game times for user ID {steam_user_id} into Finished Games user ID {fg_user_id}")

        game_data = self._fetch_data(steam_user_id, steam_api_key)
        for data in game_data:
            self.process_game_time(data.title, data.platform_id, data.minutes_played, fg_user_id)

    def _get_game(self, game_name: str, platform_id: int) -> Any:
        mapped_name = CATALOG_TITLE_MAPPINGS.get(game_name, game_name)
        return Game.objects.filter(name__iexact=mapped_name, platforms__in=[platform_id]).first()

    def _get_game_by_id(self, game_id: int) -> Any:
        return Game.objects.filter(id=game_id).first()

    def _get_fetched_game(self, game_name: str) -> Any:
        return FetchedGame.objects.filter(name__iexact=game_name, source_id=SOURCE_ID).first()

    def _get_user_game(self, game_name: str, platform_id: int, fg_user_id: int) -> Any:
        game = self._get_game(game_name, platform_id)
        user_game = UserGame.objects.filter(user=fg_user_id, game=game, platform_id=platform_id).first()
        return user_game

    def _fetch_data(self, steam_user_id: str, steam_api_key: str) -> List[GameTimeData]:
        url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={api_key}&steamid={steam_id}&format=json&include_appinfo=true".format(
            api_key=steam_api_key, steam_id=steam_user_id
        )

        request = requests.get(url, headers={"user-agent": settings.CATALOG_SOURCES_ADAPTER_USER_AGENT})
        if request.status_code == 200:
            try:
                response_data = request.json()
            except json.decoder.JSONDecodeError:
                self.stdout.write(self.style.ERROR("Unable to decode content as JSON"))
                return []
        else:
            self.stdout.write(
                self.style.ERROR(
                    "{code}: {error}.\n".format(
                        code=request.status_code,
                        error=request.text,
                    )
                )
            )
            return []

        if "response" not in response_data or "games" not in response_data["response"]:
            self.stdout.write(self.style.ERROR("Unexpected response structure:\n{}".format(response_data)))
            return []

        games = response_data["response"]["games"]

        result: List[GameTimeData] = []

        for game in games:
            name = game.get("name")
            # in minutes
            playtime_forever = game.get("playtime_forever", 0)
            if name:
                cleaned_name = cast(str, clean_string_field(name))
                if cleaned_name in IGNORED_TITLES:
                    continue
                mapped_name = CLEANED_TITLE_MAPPINGS.get(cleaned_name, cleaned_name)
                result.append(
                    GameTimeData(
                        title=mapped_name,
                        platform_id=PLATFORM_PC,
                        minutes_played=playtime_forever,
                    )
                )

        return sorted(result, key=lambda x: x.title)

    def process_game_time(self, game_name: str, platform_id: int, minutes_played: int, fg_user_id: int) -> None:
        if minutes_played == 0 or not game_name:
            return

        user_game: Optional[UserGame] = None

        # Steam has sometimes confusing names, so we always match through FetchedGame
        # e.g. Resident Evil 4 is the new remake in steam, but might not be the case in the main Game catalog
        fetched_game = self._get_fetched_game(game_name)
        if fetched_game:
            game = self._get_game_by_id(fetched_game.fg_game_id)
            if game:
                user_game = self._get_user_game(game.name, platform_id, fg_user_id)
            else:
                self.stdout.write(self.style.WARNING(
                    f"{game_name} : Fetched game exists but linked Finished Games entry not found"
                ))
                return
        else:
            self.stdout.write(self.style.WARNING(f"{game_name} : Game title not found for platform ID {platform_id}"))
            return

        if user_game:
            if user_game.minutes_played >= minutes_played:
                return

            old_minutes = user_game.minutes_played
            user_game.minutes_played = minutes_played
            user_game.save()
            self.stdout.write(self.style.SUCCESS(f"{game_name} : updated, {old_minutes} -> {minutes_played} minutes"))
        else:
            # Do not create new entries
            self.stdout.write(self.style.WARNING(
                f"{game_name} : UserGame entry not found for user ID {fg_user_id} and platform ID {platform_id}"
            ))
