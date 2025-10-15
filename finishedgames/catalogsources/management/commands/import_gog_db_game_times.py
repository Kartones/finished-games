import json
import sqlite3
from dataclasses import dataclass
from typing import Any, cast, Dict, List

from core.models import Game, UserGame
from catalogsources.helpers import clean_string_field
from django.core.management.base import BaseCommand, CommandParser


# TODO: support other OSes
GOG_DB_MACOS_PATH = "/Users/Shared/GOG.com/Galaxy/Storage/galaxy-2.0.db"

# reverse-engineered from GOG Galaxy 2.0
GAME_PIECE_TYPE_TITLE = 557
GAME_PIECES_TABLE = "GamePieces"
GAME_TIME_TABLE = "GameTimes"

PLATFORM_PC = 3

# List of game titles to skip without any output
IGNORED_TITLES: List[str] = [
    "Soulstone Survivors: Prologue",
    "RESIDENT EVIL 2 / BIOHAZARD RE:2 \"1-Shot Demo\"",
    "The Planet Crafter: Prologue",
    "12 is Better than 6",
]

# Mappings to apply after cleaning the title
TITLE_MAPPINGS: Dict[str, str] = {
    "RUINER": "Ruiner",
    "1701 A.D.: Gold Edition": "1701 A.D.",
    "20 Minutes Till Dawn": "20 Minutes Until Dawn",
    "ADOM: Ancient Domains of Mystery": "Ancient Domains of Mystery",
    "Age of Empires III: Complete Collection": "Age of Empires III",
    "Alien Shooter 2: Reloaded": "Alien Shooter 2",
    "Alien Shooter: Revisited": "Alien Shooter",
    "Aliens Versus Predator Classic 2000": "Aliens Versus Predator",
    "Ark: Survival Evolved": "ARK: Survival Evolved",
    "Ashes of the Singularity: Escalation": "Ashes of the Singularity",
    "Assassin's Creed: Director's Cut": "Assassin's Creed",
    "Assassin's Creed: Odyssey": "Assassin's Creed Odyssey",
    "Assassin’s Creed III Remastered": "Assassin's Creed III",
    "Bad Rats": "Bad Rats: the Rats' Revenge",
    "Batman: Arkham Asylum - Game of the Year Edition": "Batman: Arkham Asylum",
    "Batman: Arkham City - Game of the Year Edition": "Batman: Arkham City",
    "Battlefield 2142 Deluxe Edition": "Battlefield 2142",
    "Battlefleet Gothic: Armada 2": "Battlefleet Gothic: Armada II",
    "Battletoads": "Battletoads (2019)",
    "BioShock Remastered": "BioShock",
    "Bioshock Infinite": "BioShock Infinite",
    "Bit.Trip Runner": "Bit.Trip RUNNER",
    "Ghost Recon Wildlands": "Tom Clancy's Ghost Recon: Wildlands",
}

@dataclass
class GameTimeData:
    title: str
    platform_id: int
    minutes_played: int


class Command(BaseCommand):
    help = "Imports GOG database game times"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--gog-user-id",
            type=int,
            required=True,
            help="GOG Galaxy user ID",
        )
        parser.add_argument(
            "--fg-user-id",
            type=int,
            required=True,
            help="Finished Games user ID",
        )

    def handle(self, *args: Any, **options: Dict) -> None:
        gog_user_id = str(options["gog_user_id"])
        fg_user_id = options["fg_user_id"]

        game_data = self._fetch_data(gog_user_id)
        for data in game_data:
            self.process_game_time(data.title, data.platform_id, data.minutes_played, fg_user_id)

    def _get_game(self, game_name: str, platform_id: int) -> Any:
        return Game.objects.filter(name=game_name, platforms__in=[platform_id]).first()

    def _game_exists(self, game_name: str, platform_id: int) -> bool:
        game = self._get_game(game_name, platform_id)
        return game is not None

    def _get_user_game(self, game_name: str, platform_id: int, fg_user_id: int) -> Any:
        game = self._get_game(game_name, platform_id)
        user_game = UserGame.objects.filter(user=fg_user_id, game=game, platform_id=platform_id).first()
        return user_game

    def _fetch_data(self, gog_user_id: str) -> List[GameTimeData]:
        connection = sqlite3.connect(GOG_DB_MACOS_PATH)
        cursor = connection.cursor()

        cursor.execute(
            f"""
            SELECT releaseKey, value
            FROM {GAME_PIECES_TABLE}
            WHERE gamePieceTypeId = ? AND userId = ?
            """,
            (GAME_PIECE_TYPE_TITLE, gog_user_id),
        )
        game_titles_data = cursor.fetchall()
        titles_map = {}
        for release_key, value_json in game_titles_data:
            try:
                value_dict = json.loads(value_json)
                title = value_dict.get("title")
                if title:
                    cleaned_title = cast(str, clean_string_field(title))
                    if cleaned_title in IGNORED_TITLES:
                        continue
                    mapped_title = TITLE_MAPPINGS.get(cleaned_title, cleaned_title)
                    titles_map[release_key] = mapped_title
            except (json.JSONDecodeError, KeyError):
                continue

        cursor.execute(
            f"""
            SELECT releaseKey, minutesInGame
            FROM {GAME_TIME_TABLE}
            WHERE userId = ?
            """,
            (gog_user_id,),
        )
        play_times_data = cursor.fetchall()

        connection.close()

        result = []
        for release_key, minutes_in_game in play_times_data:
            if release_key in titles_map:
                result.append(
                    GameTimeData(
                        title=titles_map[release_key],
                        platform_id=PLATFORM_PC,
                        minutes_played=minutes_in_game,
                    )
                )

        return sorted(result, key=lambda x: x.title)

    def process_game_time(self, game_name: str, platform_id: int, minutes_played: int, fg_user_id: int) -> None:
        if minutes_played == 0 or not game_name:
            return

        if not self._game_exists(game_name, platform_id):
            self.stdout.write(self.style.WARNING(f"{game_name} : Game title not found"))
            return

        user_game = self._get_user_game(game_name, platform_id, fg_user_id)
        if user_game:
            if user_game.minutes_played >= minutes_played:
                return

            old_minutes = user_game.minutes_played
            user_game.minutes_played = minutes_played
            user_game.save()
            self.stdout.write(self.style.SUCCESS(f"{game_name} : updated, {old_minutes} -> {minutes_played} minutes"))
        else:
            game = self._get_game(game_name, platform_id)
            UserGame.objects.create(
                user_id=fg_user_id,
                game=game,
                platform_id=platform_id,
                minutes_played=minutes_played,
            )
            self.stdout.write(self.style.SUCCESS(f"{game_name} : created, {minutes_played} minutes"))
