from typing import Optional

from core.constants import MAX_VALID_YEAR, MIN_VALID_YEAR, UNKNOWN_PUBLISH_DATE
from core.models import UserGame
from core.test.tests_helpers import create_game, create_platform, create_user
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase


class UserGameTests(TestCase):
    def setUp(self) -> None:
        self.platform_1 = create_platform()
        self.platform_2 = create_platform()
        self.game_1 = create_game(platforms=[self.platform_1, self.platform_2])
        self.user = create_user()

    def test_same_user_cannot_own_same_title_multiple_times(self) -> None:
        user_game_data = {
            "user_id": self.user.id,
            "game_id": self.game_1.id,
            "platform_id": self.platform_1.id,
        }

        user_game = UserGame(**user_game_data)
        user_game.save()

        user_game = UserGame(**user_game_data)
        with self.assertRaises(ValidationError) as error:
            user_game.full_clean()
        self.assertTrue("already exists" in str(error.exception))

    def test_different_users_can_own_same_title(self) -> None:
        another_user = create_user()

        user_game_data = {
            "user_id": self.user.id,
            "game_id": self.game_1.id,
            "platform_id": self.platform_1.id,
        }

        user_game = UserGame(**user_game_data)
        user_game.save()

        user_game_data["user_id"] = another_user.id
        user_game = UserGame(**user_game_data)
        user_game.save()

    def test_can_own_same_title_on_different_platforms(self) -> None:
        user_game_data = {
            "user_id": self.user.id,
            "game_id": self.game_1.id,
            "platform_id": self.platform_1.id,
        }

        user_game = UserGame(**user_game_data)
        user_game.save()

        user_game_data["platform_id"] = self.platform_2.id
        user_game = UserGame(**user_game_data)
        user_game.save()

    def test_cannot_own_game_on_unavailable_platform(self) -> None:
        platform_3 = create_platform()

        user_game_data = {
            "user_id": self.user.id,
            "game_id": self.game_1.id,
            "platform_id": platform_3.id,
        }

        user_game = UserGame(**user_game_data)
        with self.assertRaises(ValidationError) as error:
            user_game.full_clean()
        self.assertTrue("not available in platform" in str(error.exception))

    def test_object_equality(self) -> None:
        user_game_data = {
            "user_id": self.user.id,
            "game_id": self.game_1.id,
            "platform_id": self.platform_1.id,
        }

        user_game_1 = UserGame(**user_game_data)
        user_game_1.save()

        user_game_data["platform_id"] = self.platform_2.id
        user_game_2 = UserGame(**user_game_data)
        user_game_2.save()

        self.assertNotEqual(user_game_1.id, user_game_2.id)
        self.assertNotEqual(user_game_1, user_game_2)

    def _build_user_game(self, year_finished: Optional[int] = None, year_abandoned: Optional[int] = None) -> UserGame:
        return UserGame(
            user_id=self.user.id,
            game_id=self.game_1.id,
            platform_id=self.platform_1.id,
            year_finished=year_finished,
            year_abandoned=year_abandoned,
        )

    def test_min_valid_year_is_the_first_year_after_unknown_publish_date(self) -> None:
        self.assertEqual(MIN_VALID_YEAR, UNKNOWN_PUBLISH_DATE + 1)

    def test_full_clean_rejects_year_abandoned_below_min_valid_year(self) -> None:
        for invalid_year in (UNKNOWN_PUBLISH_DATE, UNKNOWN_PUBLISH_DATE - 1, MIN_VALID_YEAR - 1):
            with self.subTest(year=invalid_year):
                with self.assertRaises(ValidationError) as error:
                    self._build_user_game(year_abandoned=invalid_year).full_clean()
                self.assertIn("year_abandoned", error.exception.message_dict)

    def test_full_clean_rejects_year_abandoned_above_max_valid_year(self) -> None:
        with self.assertRaises(ValidationError) as error:
            self._build_user_game(year_abandoned=MAX_VALID_YEAR + 1).full_clean()
        self.assertIn("year_abandoned", error.exception.message_dict)

    def test_full_clean_accepts_year_abandoned_bounds(self) -> None:
        for valid_year in (MIN_VALID_YEAR, MAX_VALID_YEAR):
            with self.subTest(year=valid_year):
                self._build_user_game(year_abandoned=valid_year).full_clean()

    def test_is_finished_and_is_abandoned_truth_table(self) -> None:
        pending = self._build_user_game()
        finished = self._build_user_game(year_finished=2000)
        abandoned = self._build_user_game(year_abandoned=2020)

        self.assertEqual((pending.is_finished, pending.is_abandoned), (False, False))
        self.assertEqual((finished.is_finished, finished.is_abandoned), (True, False))
        self.assertEqual((abandoned.is_finished, abandoned.is_abandoned), (False, True))

    def test_saving_both_years_raises_integrity_error(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._build_user_game(year_finished=2000, year_abandoned=2020).save()

    def test_saving_year_abandoned_of_unknown_publish_date_raises_integrity_error(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._build_user_game(year_abandoned=UNKNOWN_PUBLISH_DATE).save()

    def test_full_clean_rejects_year_finished_below_min_valid_year(self) -> None:
        for invalid_year in (UNKNOWN_PUBLISH_DATE, UNKNOWN_PUBLISH_DATE - 1, MIN_VALID_YEAR - 1):
            with self.subTest(year=invalid_year):
                with self.assertRaises(ValidationError) as error:
                    self._build_user_game(year_finished=invalid_year).full_clean()
                self.assertIn("year_finished", error.exception.message_dict)

    def test_full_clean_rejects_year_finished_above_max_valid_year(self) -> None:
        with self.assertRaises(ValidationError) as error:
            self._build_user_game(year_finished=MAX_VALID_YEAR + 1).full_clean()
        self.assertIn("year_finished", error.exception.message_dict)

    def test_full_clean_accepts_year_finished_bounds(self) -> None:
        for valid_year in (MIN_VALID_YEAR, MAX_VALID_YEAR):
            with self.subTest(year=valid_year):
                self._build_user_game(year_finished=valid_year).full_clean()

    def test_saving_out_of_range_year_finished_raises_integrity_error(self) -> None:
        for invalid_year in (UNKNOWN_PUBLISH_DATE, MIN_VALID_YEAR - 1, MAX_VALID_YEAR + 1):
            with self.subTest(year=invalid_year):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    self._build_user_game(year_finished=invalid_year).save()

    def test_saving_year_finished_bounds_succeeds(self) -> None:
        self._build_user_game(year_finished=MIN_VALID_YEAR).save()
        self.assertEqual(UserGame.objects.filter(year_finished=MIN_VALID_YEAR).count(), 1)
