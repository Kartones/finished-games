from core.models import Game
from django.test import TestCase


class GameTests(TestCase):
    def test_can_add_new_url_to_empty_urls_list(self):
        a_display_name = "an irrelevant name"
        a_url = "an irrelevant url"

        game = Game()
        self.assertEqual(game.urls_dict, {})

        game.upsert_url(display_name=a_display_name, url=a_url)
        self.assertEqual(game.urls_dict, {a_display_name: a_url})

    def test_can_add_new_url_to_existing_urls_list(self):
        a_display_name = "an irrelevant name"
        another_display_name = "another irrelevant name"
        a_url = "an irrelevant url"
        another_url = "another irrelevant url"

        game = Game()
        game.upsert_url(display_name=a_display_name, url=a_url)
        self.assertEqual(game.urls_dict, {a_display_name: a_url})

        game.upsert_url(display_name=another_display_name, url=another_url)
        self.assertEqual(game.urls_dict, {a_display_name: a_url, another_display_name: another_url})

    def test_updates_existing_url_with_new_data(self):
        a_display_name = "an irrelevant name"
        another_display_name = "another irrelevant name"
        a_url = "an irrelevant url"
        another_url = "another irrelevant url"
        a_new_url = "a new irrelevant url"

        game = Game()
        game.upsert_url(display_name=a_display_name, url=a_url)
        game.upsert_url(display_name=another_display_name, url=another_url)

        game.upsert_url(display_name=a_display_name, url=a_new_url)
        self.assertEqual(game.urls_dict, {a_display_name: a_new_url, another_display_name: another_url})

    def test_stores_searchable_name_on_creation(self):
        name = "F.E.A.R.: Perseus Mandate"
        expected_searchable_name = "f.e.a.r. perseus mandate"

        game = Game(name=name, publish_date=1970)
        game.save()
        self.assertEqual(game.name_for_search, expected_searchable_name)

    def test_updates_searchable_name_on_modification(self):
        initial_name = "F.E.A.R.: Perseus Mandate"
        updated_name = "F.E.A.R.: First Encounter Assault Recon"
        expected_searchable_name = "f.e.a.r. first encounter assault recon"

        game = Game(name=initial_name, publish_date=1970)
        game.save()

        game.name = updated_name
        game.save()

        self.assertEqual(game.name_for_search, expected_searchable_name)
