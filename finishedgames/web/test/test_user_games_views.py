from typing import Any, Dict, List

from core.models import UserGame
from core.test.tests_helpers import create_platform, create_user, create_user_game
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse
from web import constants
from web.admin import UserGameAdmin
from web.templatetags.web_extras import datalist_autocomplete, status_filters_row

A_FINISHED_YEAR = 2012
AN_ABANDONED_YEAR = 2014
OLDEST_ABANDONED_YEAR = 2011
MIDDLE_ABANDONED_YEAR = 2016
NEWEST_ABANDONED_YEAR = 2021


def game_names(response: HttpResponse, context_key: str) -> List[str]:
    return [user_game.game.name for user_game in response.context[context_key]]


def get_as(test_case: TestCase, user: Any, url_name: str, username: str, **query: str) -> HttpResponse:
    test_case.client.force_login(user)
    return test_case.client.get(reverse(url_name, args=[username]), query)


class ListsByStatusTests(TestCase):
    def setUp(self) -> None:
        self.user = create_user()
        self.finished = create_user_game(self.user, name="finished one", year_finished=A_FINISHED_YEAR)
        self.abandoned = create_user_game(self.user, name="abandoned one", year_abandoned=AN_ABANDONED_YEAR)
        self.pending = create_user_game(self.user, name="pending one")

    def test_finished_list_excludes_abandoned_games(self) -> None:
        response = self.client.get(reverse("user_finished_games", args=[self.user.username]))

        self.assertEqual(["finished one"], game_names(response, "finished_games"))
        self.assertEqual(1, response.context["finished_games_count"])

    def test_abandoned_list_contains_only_abandoned_games(self) -> None:
        response = self.client.get(reverse("user_abandoned_games", args=[self.user.username]))

        self.assertEqual(["abandoned one"], game_names(response, "abandoned_games"))
        self.assertEqual(1, response.context["abandoned_games_count"])

    def test_pending_list_excludes_finished_and_abandoned_games(self) -> None:
        response = self.client.get(reverse("user_pending_games", args=[self.user.username]))

        self.assertEqual(["pending one"], game_names(response, "pending_games"))
        self.assertEqual(1, response.context["pending_games_count"])

    def test_lists_can_be_filtered_by_platform(self) -> None:
        response = self.client.get(
            reverse("user_abandoned_games", args=[self.user.username]), {"platform": self.abandoned.platform_id}
        )
        self.assertEqual(["abandoned one"], game_names(response, "abandoned_games"))

        response = self.client.get(
            reverse("user_abandoned_games", args=[self.user.username]), {"platform": self.finished.platform_id}
        )
        self.assertEqual([], game_names(response, "abandoned_games"))


class AbandonedListYearTests(TestCase):
    def setUp(self) -> None:
        self.user = create_user()
        create_user_game(self.user, name="middle", year_abandoned=MIDDLE_ABANDONED_YEAR)
        create_user_game(self.user, name="newest", year_abandoned=NEWEST_ABANDONED_YEAR)
        create_user_game(self.user, name="oldest", year_abandoned=OLDEST_ABANDONED_YEAR)

    @staticmethod
    def header_pattern(sort_by: str, arrow: str) -> str:
        return r"sort_by={}[^>]*>Year{}</a>".format(sort_by, arrow)

    def test_shows_abandoned_year_column_with_each_year(self) -> None:
        response = self.client.get(reverse("user_abandoned_games", args=[self.user.username]))

        self.assertRegex(response.content.decode(), self.header_pattern(constants.SORT_BY_YEAR_ABANDONED, ""))
        self.assertNotContains(response, "Abandoned Year")
        for year in (OLDEST_ABANDONED_YEAR, MIDDLE_ABANDONED_YEAR, NEWEST_ABANDONED_YEAR):
            self.assertRegex(response.content.decode(), r'<td class="is-centered">\s*{}\s*</td>'.format(year))

    def test_sorts_by_year_abandoned_ascending(self) -> None:
        response = self.client.get(
            reverse("user_abandoned_games", args=[self.user.username]),
            {"sort_by": constants.SORT_BY_YEAR_ABANDONED},
        )

        self.assertEqual(["oldest", "middle", "newest"], game_names(response, "abandoned_games"))

    def test_sorts_by_year_abandoned_descending(self) -> None:
        response = self.client.get(
            reverse("user_abandoned_games", args=[self.user.username]),
            {"sort_by": constants.SORT_BY_YEAR_ABANDONED_DESC},
        )

        self.assertEqual(["newest", "middle", "oldest"], game_names(response, "abandoned_games"))

    def test_header_toggles_between_both_sort_directions(self) -> None:
        url = reverse("user_abandoned_games", args=[self.user.username])

        ascending = self.client.get(url, {"sort_by": constants.SORT_BY_YEAR_ABANDONED})
        descending = self.client.get(url, {"sort_by": constants.SORT_BY_YEAR_ABANDONED_DESC})

        self.assertContains(ascending, "sort_by={}".format(constants.SORT_BY_YEAR_ABANDONED_DESC))
        self.assertRegex(
            ascending.content.decode(), self.header_pattern(constants.SORT_BY_YEAR_ABANDONED_DESC, " &#8595;")
        )
        self.assertContains(descending, "sort_by={}".format(constants.SORT_BY_YEAR_ABANDONED))
        self.assertRegex(
            descending.content.decode(), self.header_pattern(constants.SORT_BY_YEAR_ABANDONED, " &#8593;")
        )

    def test_other_lists_do_not_show_abandoned_year_column(self) -> None:
        response = self.client.get(reverse("user_finished_games", args=[self.user.username]))

        self.assertNotContains(response, "Abandoned Year")
        self.assertNotContains(response, "sort_by={}".format(constants.SORT_BY_YEAR_ABANDONED))


class StatusSortingTests(TestCase):
    def test_status_column_sorts_abandoned_games_first_and_last(self) -> None:
        user = create_user()
        create_user_game(user, name="a pending")
        create_user_game(user, name="b abandoned", year_abandoned=AN_ABANDONED_YEAR)
        url = reverse("user_games", args=[user.username])

        first = self.client.get(url, {"sort_by": constants.SORT_BY_ABANDONED})
        last = self.client.get(url, {"sort_by": constants.SORT_BY_ABANDONED_DESC})

        self.assertEqual(["b abandoned", "a pending"], game_names(first, "user_games"))
        self.assertEqual(["a pending", "b abandoned"], game_names(last, "user_games"))


class CountersTests(TestCase):
    def setUp(self) -> None:
        self.user = create_user()
        self.platform = create_platform(name="counters", shortname="counters")
        create_user_game(self.user, self.platform, year_finished=A_FINISHED_YEAR)
        create_user_game(self.user, self.platform, year_finished=A_FINISHED_YEAR)
        create_user_game(self.user, self.platform, year_abandoned=AN_ABANDONED_YEAR)
        create_user_game(self.user, self.platform)
        create_user_game(self.user, self.platform, currently_playing=True)
        create_user_game(self.user, self.platform)
        # Other users must not interfere
        create_user_game(create_user(), self.platform, year_abandoned=AN_ABANDONED_YEAR)

    def assert_counters(self, context: Dict[str, Any], total_key: str) -> None:
        self.assertEqual(6, context[total_key])
        self.assertEqual(1, context["currently_playing_games_count"])
        self.assertEqual(2, context["finished_games_count"])
        self.assertEqual(1, context["abandoned_games_count"])
        self.assertEqual(3, context["completed_games_count"])
        self.assertEqual(3, context["pending_games_count"])
        self.assertEqual(50, context["completed_games_progress"])

    def test_catalog_counters(self) -> None:
        response = self.client.get(reverse("user_catalog", args=[self.user.username]))

        self.assert_counters(response.context, "user_games_count")

    def test_games_list_counters(self) -> None:
        response = self.client.get(reverse("user_games", args=[self.user.username]))

        self.assert_counters(response.context, "user_games_count")

    def test_games_by_platform_counters(self) -> None:
        response = self.client.get(reverse("user_games_by_platform", args=[self.user.username, self.platform.id]))

        self.assert_counters(response.context, "games_count")


class StatusIconsTests(TestCase):
    def render_row(self, user_game: UserGame) -> str:
        context = status_filters_row(user_game, [constants.KEY_GAMES_FINISHED, constants.KEY_GAMES_ABANDONED])
        return str(render_to_string("templatetags/status_filters_row.html", context))

    def test_abandoned_game_has_no_trophy_but_has_skull(self) -> None:
        row = self.render_row(create_user_game(create_user(), year_abandoned=AN_ABANDONED_YEAR))

        self.assertIn('title="Not finished"', row)
        self.assertNotIn('title="Finished"', row)
        self.assertIn('title="Abandoned"', row)

    def test_finished_game_has_trophy_and_no_skull(self) -> None:
        row = self.render_row(create_user_game(create_user(), year_finished=A_FINISHED_YEAR))

        self.assertIn('title="Finished"', row)
        self.assertIn('title="Pending"', row)
        self.assertNotIn('title="Abandoned"', row)


class PlatformFiltersTests(TestCase):
    def setUp(self) -> None:
        self.user = create_user()
        self.finished_platform = create_platform(name="finished platform", shortname="fin")
        self.abandoned_platform = create_platform(name="abandoned platform", shortname="aba")
        self.pending_platform = create_platform(name="pending platform", shortname="pen")
        create_user_game(self.user, self.finished_platform, year_finished=A_FINISHED_YEAR)
        create_user_game(self.user, self.abandoned_platform, year_abandoned=AN_ABANDONED_YEAR)
        create_user_game(self.user, self.pending_platform)
        other_platform = create_platform(name="other user platform", shortname="oth")
        create_user_game(create_user(), other_platform, year_abandoned=AN_ABANDONED_YEAR)

    def platform_ids(self, filter_type: str) -> List[int]:
        context = datalist_autocomplete(
            entity_type="platform",
            action_url="/irrelevant/",
            input_id="irrelevant",
            username=self.user.username,
            filter_type=filter_type,
        )
        return sorted(option["id"] for option in context["options"])

    def test_finished_filter_only_lists_platforms_with_finished_games(self) -> None:
        self.assertEqual([self.finished_platform.id], self.platform_ids(constants.PLATFORM_FILTER_FINISHED))

    def test_abandoned_filter_only_lists_platforms_with_abandoned_games(self) -> None:
        self.assertEqual([self.abandoned_platform.id], self.platform_ids(constants.PLATFORM_FILTER_ABANDONED))

    def test_pending_filter_only_lists_platforms_with_pending_games(self) -> None:
        self.assertEqual([self.pending_platform.id], self.platform_ids(constants.PLATFORM_FILTER_PENDING))


class ExcludeAbandonedTests(TestCase):
    def setUp(self) -> None:
        self.user = create_user()
        create_user_game(self.user, name="finished", year_finished=A_FINISHED_YEAR)
        create_user_game(self.user, name="abandoned", year_abandoned=AN_ABANDONED_YEAR)
        create_user_game(self.user, name="pending")

    def test_exclude_mapping_uses_year_abandoned(self) -> None:
        self.assertEqual(
            {"year_abandoned__isnull": False}, constants.EXCLUDE_FIELDS_MAPPING[constants.EXCLUDE_ABANDONED]
        )

    def test_query_string_excludes_abandoned_games_but_counters_stay_unfiltered(self) -> None:
        response = self.client.get(
            reverse("user_games", args=[self.user.username]), {"exclude": constants.EXCLUDE_ABANDONED}
        )

        self.assertEqual(["finished", "pending"], game_names(response, "user_games"))
        self.assertEqual(3, response.context["user_games_count"])
        self.assertEqual(1, response.context["abandoned_games_count"])

    def test_cookie_excludes_abandoned_games(self) -> None:
        self.client.cookies[constants.USER_OPTIONS_EXCLUDE_COOKIE_NAME] = constants.EXCLUDE_ABANDONED

        response = self.client.get(reverse("user_pending_games", args=[self.user.username]))

        self.assertEqual(["pending"], game_names(response, "pending_games"))

    def test_without_exclude_all_games_are_listed(self) -> None:
        response = self.client.get(reverse("user_games", args=[self.user.username]))

        self.assertEqual(["abandoned", "finished", "pending"], game_names(response, "user_games"))


class AuthenticatedUserCatalogTests(TestCase):
    def test_flags_games_by_status(self) -> None:
        user = create_user()
        finished = create_user_game(user, year_finished=A_FINISHED_YEAR)
        abandoned = create_user_game(user, year_abandoned=AN_ABANDONED_YEAR)

        response = get_as(self, user, "user_games", user.username)
        catalog = response.context["authenticated_user_catalog"]

        self.assertEqual([finished.generic_id], catalog[constants.KEY_GAMES_FINISHED])
        self.assertEqual([abandoned.generic_id], catalog[constants.KEY_GAMES_ABANDONED])


class AbandonActionTests(TestCase):
    def setUp(self) -> None:
        self.user = create_user()
        self.client.force_login(self.user)
        self.url = reverse("user_abandoned_games", args=[self.user.username])

    def payload(self, user_game: UserGame, **extra: str) -> Dict[str, Any]:
        return {"game": user_game.game_id, "platform": user_game.platform_id, **extra}

    def test_abandoning_a_finished_game_stores_year_abandoned_and_clears_year_finished(self) -> None:
        user_game = create_user_game(self.user, year_finished=A_FINISHED_YEAR)

        response = self.client.post(self.url, self.payload(user_game))

        self.assertEqual(204, response.status_code)
        user_game.refresh_from_db()
        self.assertIsNotNone(user_game.year_abandoned)
        self.assertIsNone(user_game.year_finished)

    def test_unabandoning_clears_year_abandoned(self) -> None:
        user_game = create_user_game(self.user, year_abandoned=AN_ABANDONED_YEAR)

        response = self.client.post(self.url, self.payload(user_game, _method=constants.FORM_METHOD_DELETE))

        self.assertEqual(204, response.status_code)
        user_game.refresh_from_db()
        self.assertIsNone(user_game.year_abandoned)


class AdminTests(TestCase):
    def test_admin_uses_year_abandoned_instead_of_flag(self) -> None:
        self.assertIn("year_abandoned", UserGameAdmin.list_display)
        self.assertIn("year_abandoned", UserGameAdmin.list_filter)
        self.assertNotIn("abandoned", UserGameAdmin.list_display)
        self.assertNotIn("abandoned", UserGameAdmin.list_filter)

    def test_changelist_renders(self) -> None:
        superuser = create_user()
        superuser.is_staff = True
        superuser.is_superuser = True
        superuser.save()
        create_user_game(create_user(), year_abandoned=AN_ABANDONED_YEAR)
        self.client.force_login(superuser)

        response = self.client.get(reverse("admin:core_usergame_changelist"))

        self.assertEqual(200, response.status_code)
