from catalogsources.models import FetchedGame
from core.models import Game
from django.test import TestCase

AN_IRRELEVANT_YEAR = 2000


class ModelsTests(TestCase):
    def test_can_be_synced(self):
        game = Game(publish_date=AN_IRRELEVANT_YEAR, name="an_irrelevant_name")
        game.save()

        fetched_game = FetchedGame(publish_date=AN_IRRELEVANT_YEAR, name="an_irrelevant_name")
        fetched_game.fg_game = game
        fetched_game.save()

        self.assertFalse(fetched_game.is_sync)

        fetched_game.mark_as_synchronized()
        fetched_game.save()

        self.assertTrue(fetched_game.is_sync)

    def test_becomes_unsync_when_modified(self):
        game = Game(publish_date=AN_IRRELEVANT_YEAR, name="an_irrelevant_name")
        game.save()

        fetched_game = FetchedGame(publish_date=AN_IRRELEVANT_YEAR, name="an_irrelevant_name")
        fetched_game.fg_game = game
        # As it is a new entity, upon saving its modified date will change, so need to sync afterwards
        fetched_game.save()
        fetched_game.mark_as_synchronized()
        fetched_game.save()
        self.assertTrue(fetched_game.is_sync)

        fetched_game.name = "another_irrelevant_name"
        fetched_game.save()
        self.assertFalse(fetched_game.is_sync)

    def test_keeps_synced_if_not_modified(self):
        name = "an_irrelevant_name"
        publish_date = AN_IRRELEVANT_YEAR

        game = Game(publish_date=publish_date, name=name)
        game.save()
        fetched_game = FetchedGame(publish_date=publish_date, name=name)
        fetched_game.fg_game = game
        # As it is a new entity, upon saving its modified date will change, so need to sync afterwards
        fetched_game.save()
        fetched_game.mark_as_synchronized()
        fetched_game.save()
        self.assertTrue(fetched_game.is_sync)

        fetched_game.name = name
        fetched_game.save()
        self.assertTrue(fetched_game.is_sync)

        fetched_game.publish_date = publish_date
        fetched_game.save()
        self.assertTrue(fetched_game.is_sync)
