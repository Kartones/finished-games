import io
from typing import List

from core.test.tests_helpers import create_user, create_user_game
from django.core.management import call_command
from django.test import TestCase

A_FINISHED_YEAR = 2012
AN_ABANDONED_YEAR = 2014
SOME_MINUTES_PLAYED = 45


class ListGamesWithNoPlaytimeTests(TestCase):
    def setUp(self) -> None:
        self.user = create_user()
        create_user_game(self.user, name="finished game", year_finished=A_FINISHED_YEAR)
        create_user_game(self.user, name="abandoned game", year_abandoned=AN_ABANDONED_YEAR)
        create_user_game(self.user, name="pending game")
        create_user_game(self.user, name="played pending game", minutes_played=SOME_MINUTES_PLAYED)
        create_user_game(self.user, name="played abandoned game", year_abandoned=AN_ABANDONED_YEAR, minutes_played=5)
        create_user_game(create_user(), name="other user abandoned game", year_abandoned=AN_ABANDONED_YEAR)

    def listed_names(self, status: str) -> List[str]:
        output = io.StringIO()

        call_command("list_games_with_no_playtime", status, self.user.id, stdout=output)

        return [line.rsplit(" (", 1)[0] for line in output.getvalue().splitlines()]

    def test_pending_lists_games_with_both_years_null(self) -> None:
        self.assertEqual(["pending game"], self.listed_names("pending"))

    def test_abandoned_lists_games_with_year_abandoned(self) -> None:
        self.assertEqual(["abandoned game"], self.listed_names("abandoned"))

    def test_finished_lists_games_with_year_finished(self) -> None:
        self.assertEqual(["finished game"], self.listed_names("finished"))
