from core.managers import CatalogManager
from core.models import UserGame, WishlistedUserGame
from core.test.tests_helpers import create_game, create_platform, create_user
from django.core.exceptions import ValidationError
from django.test import TestCase


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
        self.user_game.abandoned = True
        self.user_game.save()

        CatalogManager.mark_as_no_longer_owned(self.user, self.game.id, self.platform.id)

        self.user_game.refresh_from_db()
        self.assertTrue(self.user_game.no_longer_owned)
        self.assertFalse(self.user_game.currently_playing)
        self.assertFalse(self.user_game.abandoned)

    def test_unmark_user_game_as_no_longer_owner_unsets_proper_field(self) -> None:
        CatalogManager.mark_as_no_longer_owned(self.user, self.game.id, self.platform.id)

        CatalogManager.unmark_as_no_longer_owned(self.user, self.game.id, self.platform.id)

        self.user_game.refresh_from_db()
        self.assertFalse(self.user_game.no_longer_owned)

    def test_mark_user_game_as_finished_sets_and_unsets_proper_fields(self) -> None:
        an_irrelevant_year = 2000

        self.user_game.abandoned = True
        self.user_game.save()

        CatalogManager.mark_as_finished(self.user, self.game.id, self.platform.id, an_irrelevant_year)

        self.user_game.refresh_from_db()
        self.assertTrue(self.user_game.finished)
        self.assertEqual(self.user_game.year_finished, an_irrelevant_year)
        self.assertFalse(self.user_game.abandoned)

    def test_unmark_user_game_as_finished_unsets_proper_field(self) -> None:
        an_irrelevant_year = 2000
        CatalogManager.mark_as_finished(self.user, self.game.id, self.platform.id, an_irrelevant_year)

        CatalogManager.unmark_as_finished(self.user, self.game.id, self.platform.id)

        self.user_game.refresh_from_db()
        self.assertFalse(self.user_game.finished)
        self.assertEqual(self.user_game.year_finished, None)

    def test_mark_user_game_as_currently_playing_sets_and_unsets_proper_fields(self) -> None:
        self.user_game.no_longer_owned = True
        self.user_game.abandoned = True
        self.user_game.save()

        CatalogManager.mark_as_currently_playing(self.user, self.game.id, self.platform.id)

        self.user_game.refresh_from_db()
        self.assertTrue(self.user_game.currently_playing)
        self.assertFalse(self.user_game.no_longer_owned)
        self.assertFalse(self.user_game.abandoned)

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
        self.assertTrue(self.user_game.abandoned)
        self.assertFalse(self.user_game.currently_playing)
        self.assertFalse(self.user_game.finished)
        self.assertEqual(self.user_game.year_finished, an_irrelevant_abandoned_year)

    def test_unmark_as_abandoned_sets_proper_field(self) -> None:
        an_irrelevant_abandoned_year = 2020
        CatalogManager.mark_as_abandoned(self.user, self.game.id, self.platform.id, an_irrelevant_abandoned_year)

        CatalogManager.unmark_as_abandoned(self.user, self.game.id, self.platform.id)

        self.user_game.refresh_from_db()
        self.assertFalse(self.user_game.abandoned)
        self.assertEqual(self.user_game.year_finished, None)
