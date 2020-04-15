from core.managers import CatalogManager
from core.models import UserGame, WishlistedUserGame
from core.test.helpers import create_game, create_platform, create_user
from django.test import TestCase


class UserGameTests(TestCase):
    def setUp(self):
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

    def test_mark_user_game_as_no_longer_owner_sets_and_unsets_proper_fields(self):
        self.user_game.currently_playing = True
        self.user_game.abandoned = True
        self.user_game.save()

        CatalogManager.mark_game_as_no_longer_owned(self.user, self.game.id, self.platform.id)

        self.user_game.refresh_from_db()
        self.assertTrue(self.user_game.no_longer_owned)
        self.assertFalse(self.user_game.currently_playing)
        self.assertFalse(self.user_game.abandoned)

    def test_unmark_user_game_as_no_longer_owner_unsets_proper_field(self):
        CatalogManager.mark_game_as_no_longer_owned(self.user, self.game.id, self.platform.id)

        CatalogManager.unmark_game_from_no_longer_owned(self.user, self.game.id, self.platform.id)

        self.user_game.refresh_from_db()
        self.assertFalse(self.user_game.no_longer_owned)

    def test_mark_user_game_as_finished_sets_and_unsets_proper_fields(self):
        an_irrelevant_year = 2000

        self.user_game.abandoned = True
        self.user_game.save()

        CatalogManager.mark_game_as_finished(self.user, self.game.id, self.platform.id, an_irrelevant_year)

        self.user_game.refresh_from_db()
        self.assertTrue(self.user_game.finished)
        self.assertEqual(self.user_game.year_finished, an_irrelevant_year)
        self.assertFalse(self.user_game.abandoned)

    def test_unmark_user_game_as_finished_unsets_proper_field(self):
        an_irrelevant_year = 2000
        CatalogManager.mark_game_as_finished(self.user, self.game.id, self.platform.id, an_irrelevant_year)

        CatalogManager.unmark_game_from_finished(self.user, self.game.id, self.platform.id)

        self.user_game.refresh_from_db()
        self.assertFalse(self.user_game.finished)
        self.assertEqual(self.user_game.year_finished, None)

    def test_mark_user_game_as_currently_playing_sets_and_unsets_proper_fields(self):
        self.no_longer_owned = True
        self.user_game.abandoned = True
        self.user_game.save()

        CatalogManager.mark_game_as_currently_playing(self.user, self.game.id, self.platform.id)

        self.user_game.refresh_from_db()
        self.assertTrue(self.user_game.currently_playing)
        self.assertFalse(self.user_game.no_longer_owned)
        self.assertFalse(self.user_game.abandoned)

    def test_unmark_user_game_as_currently_playing_unsets_proper_field(self):
        CatalogManager.mark_game_as_currently_playing(self.user, self.game.id, self.platform.id)

        CatalogManager.unmark_game_from_currently_playing(self.user, self.game.id, self.platform.id)

        self.user_game.refresh_from_db()
        self.assertFalse(self.user_game.currently_playing)

    def test_mark_user_game_as_wishlisted(self):
        CatalogManager.mark_game_as_wishlisted(self.user, self.user.id, self.game.id, self.platform.id)

        wishlisted_user_game = WishlistedUserGame.objects.get(
            user=self.user.id, game_id=self.game.id, platform_id=self.platform.id
        )

        self.assertTrue(wishlisted_user_game is not None)
