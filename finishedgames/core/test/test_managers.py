from typing import Any, Dict, Optional

from core.constants import DLC_DEFAULT_MINUTES_PLAYED, MAX_VALID_YEAR, MIN_VALID_YEAR, UNKNOWN_PUBLISH_DATE
from core.managers import CatalogManager
from core.models import UserGame, WishlistedUserGame
from core.test.tests_helpers import create_game, create_platform, create_user
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, TransactionTestCase


class UserGameTests(TestCase):
    def setUp(self) -> None:
        self.platform = create_platform()
        self.game = create_game(platforms=[self.platform])
        self.user = create_user()

        user_game_data = {
            "user_id": self.user.id,
            "game_id": self.game.id,
            "platform_id": self.platform.id,
        }
        self.user_game = UserGame(**user_game_data)
        self.user_game.save()

    def test_mark_user_game_as_no_longer_owner_sets_and_unsets_proper_fields(self) -> None:
        self.user_game.currently_playing = True
        self.user_game.year_abandoned = 2020
        self.user_game.save()

        CatalogManager.mark_as_no_longer_owned(self.user, self.game.id, self.platform.id)

        self.user_game.refresh_from_db()
        self.assertTrue(self.user_game.no_longer_owned)
        self.assertFalse(self.user_game.currently_playing)
        self.assertFalse(self.user_game.is_abandoned)

    def test_unmark_user_game_as_no_longer_owner_unsets_proper_field(self) -> None:
        CatalogManager.mark_as_no_longer_owned(self.user, self.game.id, self.platform.id)

        CatalogManager.unmark_as_no_longer_owned(self.user, self.game.id, self.platform.id)

        self.user_game.refresh_from_db()
        self.assertFalse(self.user_game.no_longer_owned)

    def test_mark_user_game_as_finished_sets_and_unsets_proper_fields(self) -> None:
        an_irrelevant_year = 2000

        self.user_game.year_abandoned = 2020
        self.user_game.save()

        CatalogManager.mark_as_finished(self.user, self.game.id, self.platform.id, an_irrelevant_year)

        self.user_game.refresh_from_db()
        self.assertTrue(self.user_game.is_finished)
        self.assertEqual(self.user_game.year_finished, an_irrelevant_year)
        self.assertFalse(self.user_game.is_abandoned)

    def test_mark_as_finished_accepts_valid_year_bounds(self) -> None:
        for valid_year in (MIN_VALID_YEAR, MAX_VALID_YEAR):
            with self.subTest(year=valid_year):
                CatalogManager.mark_as_finished(self.user, self.game.id, self.platform.id, valid_year)

                self.user_game.refresh_from_db()
                self.assertEqual(self.user_game.year_finished, valid_year)

    def test_unmark_user_game_as_finished_unsets_proper_field(self) -> None:
        an_irrelevant_year = 2000
        CatalogManager.mark_as_finished(self.user, self.game.id, self.platform.id, an_irrelevant_year)

        CatalogManager.unmark_as_finished(self.user, self.game.id, self.platform.id)

        self.user_game.refresh_from_db()
        self.assertFalse(self.user_game.is_finished)
        self.assertEqual(self.user_game.year_finished, None)

    def test_mark_user_game_as_currently_playing_sets_and_unsets_proper_fields(self) -> None:
        self.user_game.no_longer_owned = True
        self.user_game.year_abandoned = 2020
        self.user_game.save()

        CatalogManager.mark_as_currently_playing(self.user, self.game.id, self.platform.id)

        self.user_game.refresh_from_db()
        self.assertTrue(self.user_game.currently_playing)
        self.assertFalse(self.user_game.no_longer_owned)
        self.assertFalse(self.user_game.is_abandoned)

    def test_mark_as_currently_playing_does_not_unmark_finished_game(self) -> None:
        an_irrelevant_year = 2024
        CatalogManager.mark_as_finished(self.user, self.game.id, self.platform.id, an_irrelevant_year)

        CatalogManager.mark_as_currently_playing(self.user, self.game.id, self.platform.id)

        self.user_game.refresh_from_db()
        self.assertTrue(self.user_game.is_finished)
        self.assertEqual(self.user_game.year_finished, an_irrelevant_year)

    def test_unmark_user_game_as_currently_playing_unsets_proper_field(self) -> None:
        CatalogManager.mark_as_currently_playing(self.user, self.game.id, self.platform.id)

        CatalogManager.unmark_as_currently_playing(self.user, self.game.id, self.platform.id)

        self.user_game.refresh_from_db()
        self.assertFalse(self.user_game.currently_playing)

    def test_mark_user_game_as_wishlisted(self) -> None:
        CatalogManager.mark_as_wishlisted(self.user, self.game.id, self.platform.id)

        wishlisted_user_game = WishlistedUserGame.objects.get(
            user=self.user.id, game_id=self.game.id, platform_id=self.platform.id
        )
        self.assertTrue(wishlisted_user_game is not None)

    def test_remove_user_game_from_wishlisted(self) -> None:
        CatalogManager.mark_as_wishlisted(self.user, self.game.id, self.platform.id)

        CatalogManager.unmark_as_wishlisted(self.user, self.game.id, self.platform.id)

        with self.assertRaises(WishlistedUserGame.DoesNotExist) as error:
            WishlistedUserGame.objects.get(user=self.user.id, game_id=self.game.id, platform_id=self.platform.id)
        self.assertTrue("does not exist" in str(error.exception))

    def test_add_game_to_user_catalog(self) -> None:
        another_platform = create_platform()
        another_game = create_game(platforms=[self.platform, another_platform])

        with self.assertRaises(UserGame.DoesNotExist) as error:
            UserGame.objects.get(user=self.user.id, game_id=another_game.id, platform_id=another_platform.id)
        self.assertTrue("does not exist" in str(error.exception))

        # Add new game, new platform
        CatalogManager.add_to_catalog(self.user, another_game.id, another_platform.id)

        user_game_1 = UserGame.objects.get(user=self.user.id, game_id=another_game.id, platform_id=another_platform.id)
        self.assertTrue(user_game_1 is not None)
        self.assertEqual(user_game_1.game.id, another_game.id)
        self.assertEqual(user_game_1.platform.id, another_platform.id)

        # Can also add it with the other platform, and it's a different association
        CatalogManager.add_to_catalog(self.user, another_game.id, self.platform.id)

        user_game_2 = UserGame.objects.get(user=self.user.id, game_id=another_game.id, platform_id=self.platform.id)
        self.assertTrue(user_game_2 is not None)
        self.assertEqual(user_game_2.game.id, another_game.id)
        self.assertEqual(user_game_2.platform.id, self.platform.id)
        self.assertNotEqual(user_game_1, user_game_2)

    def test_cant_add_twice_same_game_to_user_catalog(self) -> None:
        # setup() already added this without the CatalogManager
        with self.assertRaises(ValidationError) as error:
            CatalogManager.add_to_catalog(self.user, self.game.id, self.platform.id)
        self.assertTrue("already exists" in str(error.exception))

    def different_users_can_add_same_game_to_their_catalog(self) -> None:
        another_user = create_user()

        CatalogManager.add_to_catalog(another_user, self.game.id, self.platform.id)

        another_user_game = UserGame.objects.get(
            user=another_user.id, game_id=self.game.id, platform_id=self.platform.id
        )
        self.assertNotEqual(self.user_game.id, another_user_game.id)
        self.assertNotEqual(self.user_game.user.id, another_user_game.user.id)
        self.assertEqual(self.user_game.game.id, another_user_game.game.id)
        self.assertEqual(self.user_game.platform.id, another_user_game.platform.id)

    def test_adding_game_to_catalog_removes_from_wishlisted_if_present(self) -> None:
        another_game = create_game(platforms=[self.platform])
        CatalogManager.mark_as_wishlisted(self.user, another_game.id, self.platform.id)

        CatalogManager.add_to_catalog(self.user, another_game.id, self.platform.id)

        with self.assertRaises(WishlistedUserGame.DoesNotExist) as error:
            WishlistedUserGame.objects.get(user=self.user.id, game_id=another_game.id, platform_id=self.platform.id)
        self.assertTrue("does not exist" in str(error.exception))

    def test_remove_game_from_user_catalog(self) -> None:
        another_platform = create_platform()
        another_game = create_game(platforms=[self.platform, another_platform])
        another_user = create_user()
        CatalogManager.add_to_catalog(self.user, another_game.id, self.platform.id)
        CatalogManager.add_to_catalog(self.user, another_game.id, another_platform.id)
        CatalogManager.add_to_catalog(another_user, another_game.id, self.platform.id)

        CatalogManager.remove_from_catalog(self.user, another_game.id, self.platform.id)

        with self.assertRaises(UserGame.DoesNotExist) as error:
            UserGame.objects.get(user=self.user.id, game_id=another_game.id, platform_id=self.platform.id)
        self.assertTrue("does not exist" in str(error.exception))

        # but other associations still exist/not removed by accident
        UserGame.objects.get(user=self.user.id, game_id=self.game.id, platform_id=self.platform.id)
        UserGame.objects.get(user=self.user.id, game_id=another_game.id, platform_id=another_platform.id)
        # and similar association but for other users also still exists
        UserGame.objects.get(user=another_user.id, game_id=another_game.id, platform_id=self.platform.id)

    def test_mark_as_abandoned_sets_and_unsets_proper_fields(self) -> None:
        an_irrelevant_finished_year = 2000
        an_irrelevant_abandoned_year = 2020
        self.user_game.currently_playing = True
        self.user_game.year_finished = an_irrelevant_finished_year
        self.user_game.save()

        CatalogManager.mark_as_abandoned(self.user, self.game.id, self.platform.id, an_irrelevant_abandoned_year)

        self.user_game.refresh_from_db()
        self.assertTrue(self.user_game.is_abandoned)
        self.assertFalse(self.user_game.currently_playing)
        self.assertFalse(self.user_game.is_finished)
        self.assertIsNone(self.user_game.year_finished)
        self.assertEqual(self.user_game.year_abandoned, an_irrelevant_abandoned_year)

    def test_mark_as_abandoned_when_not_finished_leaves_year_finished_empty(self) -> None:
        an_irrelevant_abandoned_year = 2020

        CatalogManager.mark_as_abandoned(self.user, self.game.id, self.platform.id, an_irrelevant_abandoned_year)

        self.user_game.refresh_from_db()
        self.assertIsNone(self.user_game.year_finished)
        self.assertEqual(self.user_game.year_abandoned, an_irrelevant_abandoned_year)

    def _persisted_state(self) -> Dict[str, Any]:
        return dict(
            UserGame.objects.filter(id=self.user_game.id)
            .values("currently_playing", "year_finished", "year_abandoned", "no_longer_owned", "minutes_played")
            .get()
        )

    def test_rejected_mark_as_abandoned_preserves_original_state(self) -> None:
        original_states = {
            "finished and currently playing": dict(year_finished=2018, currently_playing=True),
            "already abandoned and currently playing": dict(year_abandoned=2019, currently_playing=True),
            "finished and no longer owned": dict(year_finished=2018, no_longer_owned=True, minutes_played=30),
            "pending": dict(),
        }  # type: Dict[str, Dict[str, Optional[Any]]]

        for description, original_fields in original_states.items():
            with self.subTest(state=description):
                fields = dict(
                    currently_playing=False, year_finished=None, year_abandoned=None, no_longer_owned=False, minutes_played=0
                )  # type: Dict[str, Any]
                fields.update(original_fields)
                UserGame.objects.filter(id=self.user_game.id).update(**fields)
                state_before = self._persisted_state()

                with self.assertRaises(IntegrityError):
                    CatalogManager.mark_as_abandoned(self.user, self.game.id, self.platform.id, UNKNOWN_PUBLISH_DATE)

                self.assertEqual(self._persisted_state(), state_before)

    def test_unmark_as_abandoned_sets_proper_field(self) -> None:
        an_irrelevant_abandoned_year = 2020
        CatalogManager.mark_as_abandoned(self.user, self.game.id, self.platform.id, an_irrelevant_abandoned_year)

        CatalogManager.unmark_as_abandoned(self.user, self.game.id, self.platform.id)

        self.user_game.refresh_from_db()
        self.assertFalse(self.user_game.is_abandoned)
        self.assertIsNone(self.user_game.year_abandoned)
        self.assertIsNone(self.user_game.year_finished)

    def test_unmark_as_abandoned_keeps_year_finished_of_not_abandoned_game(self) -> None:
        an_irrelevant_year = 2000
        self.user_game.year_finished = an_irrelevant_year
        self.user_game.save()

        CatalogManager.unmark_as_abandoned(self.user, self.game.id, self.platform.id)

        self.user_game.refresh_from_db()
        self.assertEqual(self.user_game.year_finished, an_irrelevant_year)

    def test_mark_as_finished_on_abandoned_game_clears_year_abandoned(self) -> None:
        an_irrelevant_abandoned_year = 2020
        an_irrelevant_finished_year = 2022
        CatalogManager.mark_as_abandoned(self.user, self.game.id, self.platform.id, an_irrelevant_abandoned_year)

        CatalogManager.mark_as_finished(self.user, self.game.id, self.platform.id, an_irrelevant_finished_year)

        self.user_game.refresh_from_db()
        self.assertIsNone(self.user_game.year_abandoned)
        self.assertEqual(self.user_game.year_finished, an_irrelevant_finished_year)
        self.assertTrue(self.user_game.is_finished)

    def test_mark_as_currently_playing_on_abandoned_game_clears_year_abandoned(self) -> None:
        CatalogManager.mark_as_abandoned(self.user, self.game.id, self.platform.id, 2020)

        CatalogManager.mark_as_currently_playing(self.user, self.game.id, self.platform.id)

        self.user_game.refresh_from_db()
        self.assertIsNone(self.user_game.year_abandoned)
        self.assertTrue(self.user_game.currently_playing)

    def test_transitions_finished_abandoned_pending_finished(self) -> None:
        CatalogManager.mark_as_finished(self.user, self.game.id, self.platform.id, 2000)
        self.user_game.refresh_from_db()
        self.assertTrue(self.user_game.is_finished)
        self.assertFalse(self.user_game.is_abandoned)

        CatalogManager.mark_as_abandoned(self.user, self.game.id, self.platform.id, 2020)
        self.user_game.refresh_from_db()
        self.assertFalse(self.user_game.is_finished)
        self.assertTrue(self.user_game.is_abandoned)

        CatalogManager.unmark_as_abandoned(self.user, self.game.id, self.platform.id)
        self.user_game.refresh_from_db()
        self.assertFalse(self.user_game.is_finished)
        self.assertFalse(self.user_game.is_abandoned)

        CatalogManager.mark_as_finished(self.user, self.game.id, self.platform.id, 2022)
        self.user_game.refresh_from_db()
        self.assertTrue(self.user_game.is_finished)
        self.assertFalse(self.user_game.is_abandoned)

    def test_mark_as_finished_dlc_with_zero_time_sets_default_time(self) -> None:
        parent_game = create_game(platforms=[self.platform])
        dlc_game = create_game(platforms=[self.platform], dlc_or_expansion=True, parent_game=parent_game)
        dlc_user_game = UserGame(user_id=self.user.id, game_id=dlc_game.id, platform_id=self.platform.id)
        dlc_user_game.save()
        an_irrelevant_year = 2024

        CatalogManager.mark_as_finished(self.user, dlc_game.id, self.platform.id, an_irrelevant_year)

        dlc_user_game.refresh_from_db()
        self.assertTrue(dlc_user_game.is_finished)
        self.assertEqual(dlc_user_game.minutes_played, DLC_DEFAULT_MINUTES_PLAYED)

    def test_mark_as_finished_dlc_with_nonzero_time_keeps_time(self) -> None:
        parent_game = create_game(platforms=[self.platform])
        dlc_game = create_game(platforms=[self.platform], dlc_or_expansion=True, parent_game=parent_game)
        dlc_user_game = UserGame(user_id=self.user.id, game_id=dlc_game.id, platform_id=self.platform.id, minutes_played=5)
        dlc_user_game.save()
        an_irrelevant_year = 2024

        CatalogManager.mark_as_finished(self.user, dlc_game.id, self.platform.id, an_irrelevant_year)

        dlc_user_game.refresh_from_db()
        self.assertTrue(dlc_user_game.is_finished)
        self.assertEqual(dlc_user_game.minutes_played, 5)

    def test_mark_as_finished_non_dlc_with_zero_time_stays_zero(self) -> None:
        an_irrelevant_year = 2024

        CatalogManager.mark_as_finished(self.user, self.game.id, self.platform.id, an_irrelevant_year)

        self.user_game.refresh_from_db()
        self.assertTrue(self.user_game.is_finished)
        self.assertEqual(self.user_game.minutes_played, 0)


class RejectedFinishTests(TransactionTestCase):
    """Runs in autocommit, as production does: a failed finish must not leave partial changes."""

    def setUp(self) -> None:
        self.platform = create_platform()
        self.game = create_game(platforms=[self.platform])
        self.user = create_user()
        self.user_game = UserGame.objects.create(user_id=self.user.id, game_id=self.game.id, platform_id=self.platform.id)

    def _assert_rejected_finish_preserves_persisted_data(
        self,
        user_game: UserGame,
        invalid_year: int,
        year_finished: Optional[int],
        year_abandoned: Optional[int],
        minutes_played: int,
    ) -> None:
        with self.assertRaises(IntegrityError):
            CatalogManager.mark_as_finished(self.user, user_game.game_id, self.platform.id, invalid_year)

        user_game.refresh_from_db()
        self.assertEqual(
            (user_game.year_finished, user_game.year_abandoned, user_game.minutes_played),
            (year_finished, year_abandoned, minutes_played),
        )

    def _create_dlc_user_game(self, minutes_played: int, **fields: Any) -> UserGame:
        parent_game = create_game(platforms=[self.platform])
        dlc_game = create_game(platforms=[self.platform], dlc_or_expansion=True, parent_game=parent_game)
        user_game: UserGame = UserGame.objects.create(
            user_id=self.user.id, game_id=dlc_game.id, platform_id=self.platform.id, minutes_played=minutes_played, **fields
        )
        return user_game

    def test_rejected_finish_keeps_abandoned_year_of_base_game(self) -> None:
        self.user_game.year_abandoned = 2019
        self.user_game.save()

        for invalid_year in (UNKNOWN_PUBLISH_DATE, MAX_VALID_YEAR + 1):
            with self.subTest(year=invalid_year):
                self._assert_rejected_finish_preserves_persisted_data(self.user_game, invalid_year, None, 2019, 0)

    def test_rejected_finish_keeps_previous_finished_year(self) -> None:
        self.user_game.year_finished = 2000
        self.user_game.save()

        for invalid_year in (UNKNOWN_PUBLISH_DATE, MAX_VALID_YEAR + 1):
            with self.subTest(year=invalid_year):
                self._assert_rejected_finish_preserves_persisted_data(self.user_game, invalid_year, 2000, None, 0)

    def test_rejected_finish_keeps_pending_game_pending(self) -> None:
        for invalid_year in (UNKNOWN_PUBLISH_DATE, MAX_VALID_YEAR + 1):
            with self.subTest(year=invalid_year):
                self._assert_rejected_finish_preserves_persisted_data(self.user_game, invalid_year, None, None, 0)

    def test_rejected_finish_keeps_abandoned_dlc_with_zero_playtime_untouched(self) -> None:
        dlc_user_game = self._create_dlc_user_game(minutes_played=0, year_abandoned=2019)

        for invalid_year in (UNKNOWN_PUBLISH_DATE, MAX_VALID_YEAR + 1):
            with self.subTest(year=invalid_year):
                self._assert_rejected_finish_preserves_persisted_data(dlc_user_game, invalid_year, None, 2019, 0)

    def test_rejected_finish_keeps_abandoned_dlc_playtime(self) -> None:
        dlc_user_game = self._create_dlc_user_game(minutes_played=5, year_abandoned=2019)

        for invalid_year in (UNKNOWN_PUBLISH_DATE, MAX_VALID_YEAR + 1):
            with self.subTest(year=invalid_year):
                self._assert_rejected_finish_preserves_persisted_data(dlc_user_game, invalid_year, None, 2019, 5)
