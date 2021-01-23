from unittest.mock import MagicMock, patch

from catalogsources.managers import ImportManager
from catalogsources.models import FetchedGame
from core.models import Game
from core.test.tests_helpers import create_game, create_platform, create_user
from django.test import TestCase

AN_IRRELEVANT_YEAR = 2000


class ManagersTests(TestCase):
    def setUp(self):
        self.platform = create_platform()
        self.game = create_game(platforms=[self.platform])
        self.user = create_user()

        self.fetched_game = FetchedGame(publish_date=AN_IRRELEVANT_YEAR, name=self.game.name)
        self.fetched_game.fg_game = self.game
        self.fetched_game.save()

    @patch("catalogsources.managers.copyfile")
    def test_cover_is_set_if_fetched_and_not_existing(self, copyfile_mock: MagicMock):
        cover = "an_irrelevant_cover_filename"

        ImportManager.import_fetched_game(
            fetched_game_id=self.fetched_game.id,
            game_id=self.game.id,
            platforms=[],
            cover=cover,
            update_fields_filter=["cover"],
        )

        copyfile_mock.assert_called_once()

        modified_game = Game.objects.filter(id=self.game.id).get()
        self.assertTrue(modified_game.cover is not None)
        self.assertEqual(modified_game.cover, cover)

    @patch("catalogsources.managers.copyfile")
    def test_cover_is_not_modified_if_exists(self, copyfile_mock: MagicMock):
        cover = "an_irrelevant_cover_filename"
        new_cover = "another_irrelevant_cover_filename"

        self.game.cover = cover
        self.game.save()

        ImportManager.import_fetched_game(
            fetched_game_id=self.fetched_game.id,
            game_id=self.game.id,
            platforms=[],
            cover=new_cover,
            update_fields_filter=["cover"],
        )

        copyfile_mock.assert_not_called()

        modified_game = Game.objects.filter(id=self.game.id).get()
        self.assertTrue(modified_game.cover is not None)
        self.assertEqual(modified_game.cover, cover)
        self.assertNotEqual(modified_game.cover, new_cover)
