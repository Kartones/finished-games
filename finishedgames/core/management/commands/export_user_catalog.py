import json
from typing import Any, Dict, List, Set, Union, cast

from core.models import Game, Platform, UserGame, WishlistedUserGame
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandParser

COUNTER_NEWLINE_AFTER_AMOUNT = 250


class Command(BaseCommand):
    help = "Exports all data of a given User"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("username", type=str)

    def handle(self, *args: Any, **options: Dict) -> None:
        username = cast(str, options["username"])
        user = get_user_model().objects.get(username=username)

        self._export_user_data(user)

        self._export_user_games(user)

        self._export_user_wishlisted_games(user)

        self._export_filtered_games(user)

        # always exporting all platforms as the list is small and we want to know on which platforms a game is available
        self._export_platforms()

        print("\n> Export finished")

    def _export_user_data(self, user: settings.AUTH_USER_MODEL) -> None:
        self.stdout.write("> Exporting User data from '{}'".format(user.username))

        user_data: Dict = {
            "id": user.id,
            "username": user.username,
        }

        self._write_to_file(filename="user.json", data=user_data)

    def _export_user_games(self, user: settings.AUTH_USER_MODEL) -> None:
        counter = 0
        user_games: List[Dict] = []

        self.stdout.write("> Exporting User Games")

        for user_game in UserGame.objects.filter(user=user):
            counter += 1

            user_games.append(
                {
                    "game_id": user_game.game.id,
                    "platform_id": user_game.platform.id,
                    "currently_playing": user_game.currently_playing,
                    "finished": user_game.finished,
                    # Not exporting: `no_longer_owned`
                    "year_finished": user_game.year_finished,
                    "abandoned": user_game.abandoned,
                    "minutes_played": user_game.minutes_played,
                }
            )

            if counter % COUNTER_NEWLINE_AFTER_AMOUNT == 0:
                self.stdout.write("{}".format(counter))

        print("\nRead {} User Games".format(counter))

        self._write_to_file(filename="user_{}_games.json".format(user.id), data=user_games)

    def _export_user_wishlisted_games(self, user: settings.AUTH_USER_MODEL) -> None:
        counter = 0
        user_games: List[Dict] = []

        self.stdout.write("> Exporting User Wishlisted Games")

        for user_game in WishlistedUserGame.objects.filter(user=user):
            counter += 1

            user_games.append(
                {
                    "game_id": user_game.game.id,
                    "platform_id": user_game.platform.id,
                }
            )

            if counter % COUNTER_NEWLINE_AFTER_AMOUNT == 0:
                self.stdout.write("{}".format(counter))

        print("\nRead {} User Wishlisted Games".format(counter))

        self._write_to_file(filename="user_{}_wishlisted_games.json".format(user.id), data=user_games)

    # We could want to export every game in the future (using `Game.objects.all()`)
    def _export_filtered_games(self, user: settings.AUTH_USER_MODEL) -> None:
        counter = 0
        games: Dict[str, Dict] = {}
        parent_game_ids: Set[int] = set()

        self.stdout.write("> Exporting Games filtered to '{}'".format(user.username))

        for user_game in UserGame.objects.filter(user=user):
            counter = self._add_user_game(user_game.game, games, counter, parent_game_ids)

        for wishlisted_user_game in WishlistedUserGame.objects.filter(user=user):
            counter = self._add_user_game(wishlisted_user_game.game, games, counter, parent_game_ids)

        old_parent_game_ids_length = len(parent_game_ids)

        for game in Game.objects.filter(id__in=parent_game_ids):
            counter = self._add_user_game(game, games, counter, parent_game_ids)

        # hierarchy is only DLC -> parent game, so only need to do this once
        if len(parent_game_ids) > old_parent_game_ids_length:
            for game in Game.objects.filter(id__in=parent_game_ids):
                counter = self._add_user_game(game, games, counter, parent_game_ids)

        print("\nRead {} Games".format(len(games)))

        self._write_to_file(filename="games.json", data=list(games.values()))

    def _export_platforms(self) -> None:
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

            if counter % 50 == 0:
                self.stdout.write("{}".format(counter))

        print("\nRead {} Platforms".format(counter))

        self._write_to_file(filename="platforms.json", data=platforms)

    def _add_user_game(self, game: Game, games_list: Dict[str, Dict], counter: int, parent_game_ids: Set[int]) -> int:
        if game.id in games_list:
            return counter

        counter += 1

        games_list[game.id] = {
            "id": game.id,
            "name": game.name,
            "publish_date": game.publish_date,
            "dlc_or_expansion": game.dlc_or_expansion,
            "platforms": [platform.id for platform in game.platforms.only("id")],
            "parent_game": game.parent_game.id if game.parent_game else None,
            "urls": game.urls_dict,
            "name_for_search": game.name_for_search,
        }

        if game.parent_game:
            parent_game_ids.add(game.parent_game.id)

        if counter % COUNTER_NEWLINE_AFTER_AMOUNT == 0:
            self.stdout.write("{}".format(counter))

        return counter

    @staticmethod
    def _write_to_file(filename: str, data: Union[Dict, List, Set]) -> None:
        with open(filename, "w") as file_handle:
            json.dump(data, file_handle, separators=(",", ":"))

        print("> Exported '{}'".format(filename))
