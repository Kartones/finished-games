import io
import json
import os
from contextlib import redirect_stdout
from typing import Any, Dict, List

from core.models import UserGame
from core.test.tests_helpers import create_user, create_user_game, create_working_directory
from django.core.management import call_command
from django.test import TestCase

A_FINISHED_YEAR = 2012
AN_ABANDONED_YEAR = 2014
USER_GAME_EXPORT_KEYS = [
    "game_id",
    "platform_id",
    "currently_playing",
    "finished",
    "year_finished",
    "year_abandoned",
    "minutes_played",
]


class ExportUserCatalogTests(TestCase):
    def setUp(self) -> None:
        self.directory = create_working_directory(self)
        self.user = create_user()

    def export_user_games(self) -> Dict[int, Dict[str, Any]]:
        with redirect_stdout(io.StringIO()):
            call_command("export_user_catalog", self.user.username, stdout=io.StringIO())

        with open(os.path.join(self.directory, "user_{}_games.json".format(self.user.id))) as file_handle:
            records: List[Dict[str, Any]] = json.load(file_handle)

        return {record["game_id"]: record for record in records}

    def export_of(self, user_game: UserGame) -> Dict[str, Any]:
        return self.export_user_games()[user_game.game_id]

    def test_abandoned_game_exports_year_abandoned_and_no_finished_data(self) -> None:
        user_game = create_user_game(self.user, year_abandoned=AN_ABANDONED_YEAR, minutes_played=30)

        self.assertEqual(
            {
                "game_id": user_game.game_id,
                "platform_id": user_game.platform_id,
                "currently_playing": False,
                "finished": False,
                "year_finished": None,
                "year_abandoned": AN_ABANDONED_YEAR,
                "minutes_played": 30,
            },
            self.export_of(user_game),
        )

    def test_finished_game_exports_year_finished_and_no_abandoned_year(self) -> None:
        user_game = create_user_game(self.user, year_finished=A_FINISHED_YEAR)

        exported = self.export_of(user_game)

        self.assertTrue(exported["finished"])
        self.assertEqual(A_FINISHED_YEAR, exported["year_finished"])
        self.assertIsNone(exported["year_abandoned"])

    def test_pending_game_exports_both_years_as_null(self) -> None:
        user_game = create_user_game(self.user, currently_playing=True)

        exported = self.export_of(user_game)

        self.assertFalse(exported["finished"])
        self.assertTrue(exported["currently_playing"])
        self.assertIsNone(exported["year_finished"])
        self.assertIsNone(exported["year_abandoned"])

    def test_exports_exactly_the_approved_keys_without_legacy_flag(self) -> None:
        user_game = create_user_game(self.user, year_abandoned=AN_ABANDONED_YEAR)

        exported = self.export_of(user_game)

        self.assertEqual(USER_GAME_EXPORT_KEYS, list(exported.keys()))
        self.assertNotIn("abandoned", exported)

    def test_only_exports_games_of_the_requested_user(self) -> None:
        create_user_game(create_user(), year_abandoned=AN_ABANDONED_YEAR)
        own = create_user_game(self.user)

        self.assertEqual([own.game_id], list(self.export_user_games().keys()))
