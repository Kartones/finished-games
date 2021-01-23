from datetime import datetime
from typing import Any, Dict

from core.forms import GameForm
from core.test.tests_helpers import create_game, create_platform
from django.core.exceptions import ValidationError
from django.test import TestCase


class GameFormTests(TestCase):
    def setUp(self) -> None:
        self.platform_1 = create_platform()

    def test_game_needs_at_least_one_platform(self) -> None:
        game_data = {
            "name": "a unique name",
            "platforms": [],
            "publish_date": datetime.now().year,
        }  # type: Dict[str, Any]

        game_form = GameForm(game_data)
        self.assertFalse(game_form.is_valid())

        game_data["platforms"] = [self.platform_1]
        game_form = GameForm(game_data)
        self.assertTrue(game_form.is_valid(), game_form.errors)

    def test_game_name_is_unique(self) -> None:
        game_data = {
            "name": "a unique name",
            "platforms": [self.platform_1.id],
            "publish_date": datetime.now().year,
        }  # type: Dict[str, Any]

        create_game(platforms=game_data["platforms"], name=game_data["name"])

        game_form = GameForm(game_data)
        self.assertFalse(game_form.is_valid())
        self.assertTrue("name" in game_form.errors.keys())

    def test_game_name_uniqueness_is_case_insensitive(self) -> None:
        game_data = {
            "name": "A Case Sensitive Unique Name",
            "platforms": [self.platform_1.id],
            "publish_date": datetime.now().year,
        }  # type: Dict[str, Any]

        create_game(platforms=game_data["platforms"], name=game_data["name"])

        game_data["name"] = game_data["name"].lower()
        game_form = GameForm(game_data)

        with self.assertRaises(ValidationError) as error:
            game_form.is_valid()
        self.assertTrue("already exists" in str(error.exception))

    def test_game_dlc_needs_parent_game(self) -> None:
        game_1 = create_game(platforms=[self.platform_1])

        game_data = {
            "name": "an irrelevant name",
            "platforms": [self.platform_1.id],
            "publish_date": datetime.now().year,
            "dlc_or_expansion": True,
            "parent_game": None,
        }  # type: Dict[str, Any]

        game_form = GameForm(game_data)
        self.assertFalse(game_form.is_valid())
        self.assertTrue("parent_game" in game_form.errors.keys())
        self.assertTrue("must specify a parent game" in game_form.errors["parent_game"][0])

        game_data["parent_game"] = game_1.id
        game_form = GameForm(game_data)
        self.assertTrue(game_form.is_valid(), game_form.errors)

    def test_game_dlc_parent_cannot_be_also_a_dlc(self) -> None:
        game_1 = create_game(platforms=[self.platform_1])
        game_1_dlc = create_game(platforms=[self.platform_1], dlc_or_expansion=True, parent_game=game_1.id)

        game_data = {
            "name": "an irrelevant name",
            "platforms": [self.platform_1.id],
            "publish_date": datetime.now().year,
            "dlc_or_expansion": True,
            "parent_game": game_1_dlc.id,
        }  # type: Dict[str, Any]

        game_form = GameForm(game_data)
        self.assertFalse(game_form.is_valid())
        self.assertTrue("parent_game" in game_form.errors.keys())
        self.assertTrue("cannot have as parent another game DLC" in game_form.errors["parent_game"][0])

    def test_game_dlc_platform_must_be_subset_of_parent_game(self) -> None:
        platform_2 = create_platform()
        platform_3 = create_platform()

        game_1 = create_game(platforms=[self.platform_1, platform_2])

        # subset = superset
        game_data = {
            "name": "an irrelevant name",
            "platforms": (platform.id for platform in game_1.platforms.all()),
            "publish_date": datetime.now().year,
            "dlc_or_expansion": True,
            "parent_game": game_1.id,
        }  # type: Dict[str, Any]
        game_form = GameForm(game_data)
        self.assertTrue(game_form.is_valid(), game_form.errors)

        # subset < superset
        game_data["platforms"] = [self.platform_1]
        game_form = GameForm(game_data)
        self.assertTrue(game_form.is_valid(), game_form.errors)

        # subset != superset
        game_data["platforms"] = [self.platform_1, platform_3]
        game_form = GameForm(game_data)
        self.assertFalse(game_form.is_valid())
        self.assertTrue("platforms" in game_form.errors.keys())
        self.assertTrue("subset/all of parent game platforms" in game_form.errors["platforms"][0])

        game_data["platforms"] = [platform_3]
        game_form = GameForm(game_data)
        self.assertFalse(game_form.is_valid())
        self.assertTrue("platforms" in game_form.errors.keys())
        self.assertTrue("subset/all of parent game platforms" in game_form.errors["platforms"][0])
