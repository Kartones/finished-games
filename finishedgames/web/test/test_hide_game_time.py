from typing import Any, Dict, Tuple

from core.test.tests_helpers import create_user, create_user_game
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from web.context_processors import app_settings

GAME_TIME_HEADER = "Game Time"
TOTAL_GAME_TIME = "Total game time"
GAME_TIME_INPUT = 'name="minutes_played"'


class AppSettingsContextProcessorTests(TestCase):
    def test_exposes_hide_game_time_as_false_by_default(self) -> None:
        self.assertFalse(app_settings(RequestFactory().get("/"))["HIDE_GAME_TIME"])

    @override_settings(HIDE_GAME_TIME=True)
    def test_exposes_hide_game_time_when_enabled(self) -> None:
        self.assertTrue(app_settings(RequestFactory().get("/"))["HIDE_GAME_TIME"])


class HideGameTimeViewsTests(TestCase):
    def setUp(self) -> None:
        self.user = create_user()
        self.user_game = create_user_game(self.user, name="a game")
        create_user_game(self.user, name="finished game", year_finished=2020)
        create_user_game(self.user, name="abandoned game", year_abandoned=2021)
        create_user_game(self.user, name="playing game", currently_playing=True)
        self.client.force_login(self.user)

    def get(self, url_name: str, *args: Any) -> str:
        response = self.client.get(reverse(url_name, args=args))

        return str(response.content.decode())

    def list_pages(self) -> Dict[str, Tuple[Any, ...]]:
        username = self.user.username
        return {
            "user_games": (username,),
            "user_finished_games": (username,),
            "user_pending_games": (username,),
            "user_abandoned_games": (username,),
            "user_currently_playing_games": (username,),
            "user_games_by_platform": (username, self.user_game.platform_id),
        }

    def test_list_pages_show_game_time_by_default(self) -> None:
        for url_name, args in self.list_pages().items():
            with self.subTest(url_name):
                content = self.get(url_name, *args)

                self.assertIn(GAME_TIME_HEADER, content)
                self.assertIn(GAME_TIME_INPUT, content)

    @override_settings(HIDE_GAME_TIME=True)
    def test_list_pages_hide_game_time_header_and_cell_when_enabled(self) -> None:
        for url_name, args in self.list_pages().items():
            with self.subTest(url_name):
                content = self.get(url_name, *args)

                self.assertNotIn(GAME_TIME_HEADER, content)
                self.assertNotIn(GAME_TIME_INPUT, content)

    def test_catalog_shows_total_game_time_by_default(self) -> None:
        self.assertIn(TOTAL_GAME_TIME, self.get("user_catalog", self.user.username))

    @override_settings(HIDE_GAME_TIME=True)
    def test_catalog_hides_total_game_time_when_enabled(self) -> None:
        self.assertNotIn(TOTAL_GAME_TIME, self.get("user_catalog", self.user.username))

    def test_game_details_shows_game_time_by_default(self) -> None:
        content = self.get("game_details", self.user_game.game_id)

        self.assertIn(GAME_TIME_HEADER, content)
        self.assertIn(GAME_TIME_INPUT, content)

    @override_settings(HIDE_GAME_TIME=True)
    def test_game_details_hides_game_time_header_and_cell_when_enabled(self) -> None:
        content = self.get("game_details", self.user_game.game_id)

        self.assertNotIn(GAME_TIME_HEADER, content)
        self.assertNotIn(GAME_TIME_INPUT, content)
