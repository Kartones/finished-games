from django.test import TestCase

from core.forms import WishlistedUserGameForm
from core.test.helpers import (create_game, create_platform, create_user)


class WishlistedUserGameFormTests(TestCase):

    def setUp(self):
        self.platform_1 = create_platform()
        self.platform_2 = create_platform()
        self.game_1 = create_game(platforms=[self.platform_1, self.platform_2])
        self.user = create_user()

    def test_same_user_cannot_wishlist_same_title_multiple_times(self):
        wishlist_game_data = {
            "user": self.user.id,
            "game": self.game_1.id,
            "platform": self.platform_1.id,
        }

        wishlist_game_form = WishlistedUserGameForm(wishlist_game_data)
        self.assertTrue(wishlist_game_form.is_valid(), wishlist_game_form.errors)
        wishlist_game_form.save()
        wishlist_game_form = WishlistedUserGameForm(wishlist_game_data)
        self.assertFalse(wishlist_game_form.is_valid())
        self.assertTrue("already exists" in str(wishlist_game_form.errors))

    def test_different_users_can_wishlist_same_title(self):
        another_user = create_user()

        wishlist_game_data = {
            "user": self.user.id,
            "game": self.game_1.id,
            "platform": self.platform_1.id,
        }

        wishlist_game_form = WishlistedUserGameForm(wishlist_game_data)
        self.assertTrue(wishlist_game_form.is_valid(), wishlist_game_form.errors)
        wishlist_game_form.save()

        wishlist_game_data["user"] = another_user.id
        wishlist_game_form = WishlistedUserGameForm(wishlist_game_data)
        self.assertTrue(wishlist_game_form.is_valid(), wishlist_game_form.errors)

    def test_can_wishlist_same_title_on_different_platforms(self):
        wishlist_game_data = {
            "user": self.user.id,
            "game": self.game_1.id,
            "platform": self.platform_1.id,
        }

        wishlist_game_form = WishlistedUserGameForm(wishlist_game_data)
        self.assertTrue(wishlist_game_form.is_valid(), wishlist_game_form.errors)
        wishlist_game_form.save()

        wishlist_game_data["platform"] = self.platform_2.id
        wishlist_game_form = WishlistedUserGameForm(wishlist_game_data)
        self.assertTrue(wishlist_game_form.is_valid(), wishlist_game_form.errors)

    def test_cannot_wishlist_game_on_unavailable_platform(self):
        platform_3 = create_platform()

        wishlist_game_data = {
            "user": self.user.id,
            "game": self.game_1.id,
            "platform": platform_3.id,
        }

        wishlist_game_form = WishlistedUserGameForm(wishlist_game_data)
        self.assertFalse(wishlist_game_form.is_valid())
        self.assertTrue("platform" in wishlist_game_form.errors.keys())
        self.assertTrue("not available in platform" in wishlist_game_form.errors["platform"][0])
