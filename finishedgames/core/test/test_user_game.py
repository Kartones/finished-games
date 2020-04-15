from core.models import UserGame
from core.test.helpers import create_game, create_platform, create_user
from django.core.exceptions import ValidationError
from django.test import TestCase


class UserGameTests(TestCase):
    def setUp(self):
        self.platform_1 = create_platform()
        self.platform_2 = create_platform()
        self.game_1 = create_game(platforms=[self.platform_1, self.platform_2])
        self.user = create_user()

    def test_same_user_cannot_own_same_title_multiple_times(self):
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

    def test_different_users_can_own_same_title(self):
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

    def test_can_own_same_title_on_different_platforms(self):
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

    def test_cannot_own_game_on_unavailable_platform(self):
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
