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

# TODO: This should also be a parameter
PLATFORM_PC = 3

# List of game titles to skip without any output
IGNORED_TITLES: List[str] = [
    "Soulstone Survivors: Prologue",
    "RESIDENT EVIL 2 / BIOHAZARD RE:2 \"1-Shot Demo\"",
    "The Planet Crafter: Prologue",
    "12 is Better than 6",
    "Call of Duty: Modern Warfare 2 Multiplayer",
    "Crust Crusaders",
    "DFHack - Dwarf Fortress Modding Engine",
    "DOOM Eternal (BATTLEMODE - PC)",
    "Halls of Torment Prelude",
    "Infection Free Zone - Prologue",
    "Metal Gear Solid Master Collection: Volume 1 - Bonus Content",
    "Project Borealis: Prologue",
    "Resident Evil 7 Teaser: Beginning Hour",
    "RetroArch",
    "Stones of Solace",
    "Train Simulator",
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
    "Blood Bowl: Dark Elves Edition": "Blood Bowl: Legendary Edition",
    "BloodRealm: Battlegrounds": "",
    "Brigador: Up-Armored Edition": "Brigador",
    "Burnout Paradise: The Ultimate Box": "Burnout Paradise",
    "CYGNI - All Guns Blazing": "Cygni: All Guns Blazing",
    "Carmageddon Max Pack": "Carmageddon",
    "Castle of Illusion Starring Mickey Mouse": "Disney Castle of Illusion Starring Mickey Mouse",
    "Castlevania: Lords of Shadow - Mirror of Fate HD": "Castlevania: Lords of Shadow - Mirror of Fate",
    "Chantelise - A Tale of Two Sisters": "Chantelise",
    "Colin McRae: Dirt 2": "DiRT 2",
    "Command & Conquer Generals Zero Hour": "Command & Conquer: Generals - Zero Hour",
    "Command & Conquer Remastered Collection": "Command & Conquer: Remastered Collection",
    "Command & Conquer and The Covert Operations": "Command & Conquer: The Covert Operations",
    "Crysis 2 Remastered": "Crysis 2",
    "Crysis 3 Remastered": "Crysis 3",
    "Crysis Remastered": "Crysis",
    "Cursed Castilla EX": "Maldita Castilla",
    "DEFCON": "DEFCON: Everybody Dies",
    "Dark Messiah of Might and Magic": "Dark Messiah of Might & Magic",
    "Dead Island: Riptide - Definitive Edition": "Dead Island Riptide",
    "Dead Space (2008)": "Dead Space",
    "Deus Ex: Human Revolution - Director's Cut": "Deus Ex: Human Revolution Director's Cut",
    "DiRT 3 Complete Edition": "DiRT 3",
    "Diablo + Hellfire": "Diablo",
    "DmC: Devil May Cry": "DmC Devil May Cry",
    "Dragon Age: Origins - Ultimate Edition": "Dragon Age: Origins",
    "Elite Dangerous": "Elite: Dangerous",
    "Epistory - Typing Chronicles": "Epistory: Typing Chronicles",
    "Fallout Classic": "Fallout",
    "Far Cry Primal": "Far Cry: Primal",
    "Gauntlet: Slayer Edition": "Gauntlet (2014)",
    "Grand Theft Auto III - The Definitive Edition": "Grand Theft Auto III",
    "Grand Theft Auto V Enhanced": "Grand Theft Auto V",
    "Grand Theft Auto: San Andreas - The Definitive Edition": "Grand Theft Auto: San Andreas",
    "Grand Theft Auto: Vice City - The Definitive Edition": "Grand Theft Auto: Vice City",
    "Half-Life: Source": "Half-Life",
    "Heart&Slash": "Heart & Slash",
    "Helldivers 2": "Helldivers II",
    "Horizon Zero Dawn Complete Edition": "Horizon Zero Dawn",
    "Kingdom: Classic": "Kingdom Classic",
    "Krater: Shadows over Solside": "Krater",
    "LEGO Builder's Journey": "LEGO Builder’s Journey",
    "Locomotion, Chris Sawyer's": "Chris Sawyer's Locomotion",
    "METAL GEAR SOLID 2: Sons of Liberty - Master Collection Version": "Metal Gear Solid 2: Substance",
    "METAL GEAR SOLID: MASTER COLLECTION Vol.1 METAL GEAR SOLID 3: Snake Eater": "Metal Gear Solid 3: Snake Eater",
    "Madballs in Babo: Invasion": "Madballs in... Babo: Invasion",
    "Magic: Legends": "Magic Legends",
    "Mass Effect Legendary Edition": "Mass Effect: Legendary Edition",
    "Metal Gear Solid Master Collection: Volume 1": "Metal Gear Solid: Master Collection Vol. 1",
    "Metro Exodus Enhanced Edition": "Metro Exodus",
    "Minecraft: Windows 10 Edition": "Minecraft",
    "Never Alone: Kisima Ingitchuna": "Never Alone",
    "Oddworld: Stranger's Wrath HD": "Oddworld: Stranger's Wrath",
    "OpenTTD": "Open Transport Tycoon Deluxe",
    "PAC-MAN Championship Edition DX+": "Pac-Man Championship Edition DX",
    "Painkiller: Black Edition": "Painkiller",
    "Peggle Deluxe": "Peggle (2007)",
    "Planescape: Torment - Enhanced Edition": "Planescape: Torment: Enhanced Edition",
    "Plants vs. Zombies: Game of the Year": "Plants vs. Zombies",
    "Portal with RTX": "Portal RTX",
    "Quake: Mission Pack 1 - Scourge of Armagon": "Quake Mission Pack 1: Scourge of Armagon",
    "Quake: Mission Pack 2 - Dissolution of Eternity": "Quake Mission Pack 2: Dissolution of Eternity",
    "RESIDENT EVIL 2 / BIOHAZARD RE:2": "Resident Evil 2 (2019)",
    "Red Dead Redemption 2": "Red Dead Redemption II",
    "Red Faction: Guerrilla - Steam Edition": "Red Faction: Guerrilla",
    "Red Faction: Guerrilla Re-Mars-tered": "Red Faction: Guerrilla",
    "Resident Evil: Revelations HD": "Resident Evil: Revelations",
    "Retro City Rampage DX": "Retro City Rampage",
    "Rise of the Tomb Raider: 20 Year Celebration": "Rise of the Tomb Raider",
    "STAR WARS Battlefront II: Celebration Edition": "Star Wars Battlefront II",
    "STAR WARS: TIE Fighter Collector's CD (1995)": "Star Wars: TIE Fighter",
    "Sacred Gold": "Sacred",
    "Scourge Outbreak": "Scourge: Outbreak",
    "Serious Sam HD: The First Encounter": "Serious Sam: The First Encounter",
    "Serious Sam HD: The Second Encounter": "Serious Sam: The Second Encounter",
    "Shadow of the Tomb Raider: Definitive Edition": "Shadow of the Tomb Raider",
    "Sid Meier's Alpha Centauri Planetary Pack": "Sid Meier's Alpha Centauri",
    "Sid Meier's Civilization III: Complete": "Sid Meier's Civilization III",
    "SimCity 2000 Special Edition": "SimCity 2000",
    "SimCity: Complete Edition": "SimCity",
    "Space Hulk: Ascension": "Space Hulk Ascension",
    "Space Hulk: Deathwing - Enhanced Edition": "Space Hulk: Deathwing",
    "Star Wars: Empire at War - Gold Pack": "Star Wars: Empire at War",
    "Starlink: Battler For Atlas": "Starlink: Battle for Atlas",
    "Strider": "Strider (2014)",
    "Super Bit Blaster XL": "Bit Blaster XL",
    "Talisman: Digital Edition": "Talisman Digital Edition",
    "Talisman: Prologue": "Talisman Prologue",
    "Teleglitch: Die More Edition": "Teleglitch",
    "The Elder Scrolls V: Skyrim - Special Edition": "The Elder Scrolls V: Skyrim",
    "The Lord of The Rings Return to Moria": "The Lord of the Rings: Return to Moria",
    "The Scourge Project: Episodes 1 and 2": "The Scourge Project",
    "The Secret of Monkey Island: Special Edition": "The Secret of Monkey Island",
    "The Textorcist": "The Textorcist: The Story of Ray Bibbia",
    "The Witcher 2: Assassins of Kings Enhanced Edition": "The Witcher 2: Assassins of Kings",
    "The Witcher 3: Wild Hunt - Game of the Year Edition": "The Witcher 3: Wild Hunt",
    "Ticket to Ride: Classic Edition": "Ticket to Ride",
    "Titan Quest Anniversary Edition": "Titan Quest: Anniversary Edition",
    "Trials 2: Second Edition": "Trials 2 Second Edition",
    "Ultima 8 Gold Edition": "Ultima VIII: Pagan",
    "Unreal Gold": "Unreal",
    "Unreal Tournament III: Black Edition": "Unreal Tournament 3",
    "Uplink": "Uplink: Hacker Elite",
    "Warhammer 40,000: Dawn of War - Game of the Year Edition": "Warhammer 40,000: Dawn of War",
    "Warhammer 40,000: Dawn of War II - Chaos Rising": "Warhammer 40,000: Dawn of War II: Chaos Rising",
    "Warhammer 40,000: Deathwatch - Enhanced Edition": "Warhammer 40,000: Deathwatch - Tyranid Invasion",
    "Warhammer 40,000: Inquisitor - Martyr": "Warhammer 40,000: Inquisitor Martyr",
    "Warhammer: The Horus Heresy - Legions": "The Horus Heresy: Legions",
    "Wasteland 2 Director's Cut": "Wasteland 2",
    "World of Tanks: Blitz": "World of Tanks Blitz",
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
        fg_user_id = cast(int, options["fg_user_id"])

        game_data = self._fetch_data(gog_user_id)
        for data in game_data:
            self.process_game_time(data.title, data.platform_id, data.minutes_played, fg_user_id)

    def _get_game(self, game_name: str, platform_id: int) -> Any:
        return Game.objects.filter(name__iexact=game_name, platforms__in=[platform_id]).first()

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
