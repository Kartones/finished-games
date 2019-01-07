from django.test import TestCase

from core.forms import UserGameForm
from core.test.helpers import (create_game, create_platform, create_user)


class UserGameFormTests(TestCase):

    def setUp(self):
        self.platform_1 = create_platform()
        self.platform_2 = create_platform()
        self.game_1 = create_game(platforms=[self.platform_1, self.platform_2])
        self.user = create_user()

    def test_same_user_cannot_own_same_title_multiple_times(self):
        user_game_data = {
            "user": self.user.id,
            "game": self.game_1.id,
            "platform": self.platform_1.id,
        }

        user_game_form = UserGameForm(user_game_data)
        self.assertTrue(user_game_form.is_valid(), user_game_form.errors)
        user_game_form.save()
        user_game_form = UserGameForm(user_game_data)
        self.assertFalse(user_game_form.is_valid())
        self.assertTrue("already exists" in str(user_game_form.errors))

    def test_different_users_can_own_same_title(self):
        another_user = create_user()

        user_game_data = {
            "user": self.user.id,
            "game": self.game_1.id,
            "platform": self.platform_1.id,
        }

        user_game_form = UserGameForm(user_game_data)
        self.assertTrue(user_game_form.is_valid(), user_game_form.errors)
        user_game_form.save()

        user_game_data["user"] = another_user.id
        user_game_form = UserGameForm(user_game_data)
        self.assertTrue(user_game_form.is_valid(), user_game_form.errors)

    def test_can_own_same_title_on_different_platforms(self):
        user_game_data = {
            "user": self.user.id,
            "game": self.game_1.id,
            "platform": self.platform_1.id,
        }

        user_game_form = UserGameForm(user_game_data)
        self.assertTrue(user_game_form.is_valid(), user_game_form.errors)
        user_game_form.save()

        user_game_data["platform"] = self.platform_2.id
        user_game_form = UserGameForm(user_game_data)
        self.assertTrue(user_game_form.is_valid(), user_game_form.errors)

    def test_cannot_own_game_on_unavailable_platform(self):
        platform_3 = create_platform()

        user_game_data = {
            "user": self.user.id,
            "game": self.game_1.id,
            "platform": platform_3.id,
        }

        user_game_form = UserGameForm(user_game_data)
        self.assertFalse(user_game_form.is_valid())
        self.assertTrue("platform" in user_game_form.errors.keys())
        self.assertTrue("not available in platform" in user_game_form.errors["platform"][0])
