import io
import uuid
from contextlib import redirect_stdout
from importlib import import_module
from typing import Any, Dict, Optional, Tuple

from django.conf import settings
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.state import StateApps
from django.test import TransactionTestCase

APP_LABEL = "core"
MIGRATION_0009 = (APP_LABEL, "0009_usergame_minutes_played")
MIGRATION_0010 = (APP_LABEL, "0010_usergame_year_abandoned")
MIGRATION_0011 = (APP_LABEL, "0011_migrate_abandoned_to_year_abandoned")
MIGRATION_0012 = (APP_LABEL, "0012_remove_usergame_abandoned_add_abandoned_constraints")
MIGRATION_0013 = (APP_LABEL, "0013_reset_invalid_year_finished")
MIGRATION_0014 = (APP_LABEL, "0014_usergame_year_finished_constraint")

AN_IRRELEVANT_REAL_YEAR = 2018
AN_IRRELEVANT_FINISHED_YEAR = 2005


class MigrationTestCase(TransactionTestCase):
    def migrate_to(self, target: Tuple[str, str]) -> StateApps:
        executor = MigrationExecutor(connection)
        executor.migrate([target])
        executor.loader.build_graph()
        return executor.loader.project_state([target]).apps

    def tearDown(self) -> None:
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def create_user_game(self, apps: StateApps, **fields: Any) -> int:
        user_model = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
        game_model = apps.get_model(APP_LABEL, "Game")
        platform_model = apps.get_model(APP_LABEL, "Platform")
        user_game_model = apps.get_model(APP_LABEL, "UserGame")

        platform = platform_model.objects.create(name=str(uuid.uuid4()), shortname=str(uuid.uuid4()), publish_date=2000)
        game = game_model.objects.create(name=str(uuid.uuid4()), publish_date=2000)
        game.platforms.add(platform)
        user = user_model.objects.create(username=str(uuid.uuid4()))

        return int(user_game_model.objects.create(user=user, game=game, platform=platform, **fields).id)

    def user_game_values(self, apps: StateApps, user_game_id: int, *field_names: str) -> Dict[str, Any]:
        user_game_model = apps.get_model(APP_LABEL, "UserGame")
        return dict(user_game_model.objects.filter(id=user_game_id).values(*field_names).get())


class MigrateAbandonedToYearAbandonedTests(MigrationTestCase):
    def setUp(self) -> None:
        super().setUp()
        apps = self.migrate_to(MIGRATION_0010)
        self.abandoned_with_year_id = self._create(apps, abandoned=True, year_finished=AN_IRRELEVANT_REAL_YEAR)
        self.abandoned_with_unknown_year_id = self._create(apps, abandoned=True, year_finished=1970)
        self.abandoned_with_no_year_id = self._create(apps, abandoned=True, year_finished=None)
        self.abandoned_with_future_year_id = self._create(apps, abandoned=True, year_finished=3001)
        self.finished_id = self._create(apps, abandoned=False, year_finished=AN_IRRELEVANT_FINISHED_YEAR)
        self.pending_id = self._create(apps, abandoned=False, year_finished=None)

    def _create(self, apps: StateApps, abandoned: bool, year_finished: Optional[int]) -> int:
        return self.create_user_game(apps, abandoned=abandoned, year_finished=year_finished)

    def _years(self, apps: StateApps, user_game_id: int) -> Tuple[Optional[int], Optional[int]]:
        values = self.user_game_values(apps, user_game_id, "year_finished", "year_abandoned")
        return values["year_finished"], values["year_abandoned"]

    def test_forward_moves_valid_year_to_year_abandoned_and_clears_year_finished(self) -> None:
        apps = self.migrate_to(MIGRATION_0011)

        self.assertEqual(self._years(apps, self.abandoned_with_year_id), (None, AN_IRRELEVANT_REAL_YEAR))

    def test_forward_resets_abandoned_rows_with_unknown_missing_or_out_of_range_year(self) -> None:
        apps = self.migrate_to(MIGRATION_0011)

        for user_game_id in (
            self.abandoned_with_unknown_year_id,
            self.abandoned_with_no_year_id,
            self.abandoned_with_future_year_id,
        ):
            with self.subTest(user_game_id=user_game_id):
                self.assertEqual(self._years(apps, user_game_id), (None, None))

    def test_forward_leaves_finished_and_pending_rows_untouched(self) -> None:
        apps = self.migrate_to(MIGRATION_0011)

        self.assertEqual(self._years(apps, self.finished_id), (AN_IRRELEVANT_FINISHED_YEAR, None))
        self.assertEqual(self._years(apps, self.pending_id), (None, None))

    def test_forward_twice_is_a_no_op_and_keeps_copied_year_abandoned(self) -> None:
        apps = self.migrate_to(MIGRATION_0011)
        migration_module = import_module("core.migrations.0011_migrate_abandoned_to_year_abandoned")

        migration_module.migrate_abandoned_to_year_abandoned(apps, None)

        self.assertEqual(self._years(apps, self.abandoned_with_year_id), (None, AN_IRRELEVANT_REAL_YEAR))
        self.assertEqual(self._years(apps, self.abandoned_with_no_year_id), (None, None))
        self.assertEqual(self._years(apps, self.finished_id), (AN_IRRELEVANT_FINISHED_YEAR, None))

    def test_forward_prints_moved_and_reset_counts(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            self.migrate_to(MIGRATION_0011)

        self.assertIn("moved to year_abandoned: 1", output.getvalue())
        self.assertIn("reset to pending (NULL or unknown year): 3", output.getvalue())

    def test_reverse_restores_year_finished_for_rows_with_year_abandoned(self) -> None:
        self.migrate_to(MIGRATION_0011)

        apps = self.migrate_to(MIGRATION_0010)

        self.assertEqual(self._years(apps, self.abandoned_with_year_id), (AN_IRRELEVANT_REAL_YEAR, None))
        self.assertEqual(self._years(apps, self.abandoned_with_no_year_id), (None, None))
        self.assertEqual(self._years(apps, self.finished_id), (AN_IRRELEVANT_FINISHED_YEAR, None))


class RemoveAbandonedFlagTests(MigrationTestCase):
    def test_reverse_repopulates_flag_and_year_finished_from_year_abandoned(self) -> None:
        apps = self.migrate_to(MIGRATION_0012)
        abandoned_id = self.create_user_game(apps, year_abandoned=AN_IRRELEVANT_REAL_YEAR)
        finished_id = self.create_user_game(apps, year_finished=AN_IRRELEVANT_FINISHED_YEAR)
        pending_id = self.create_user_game(apps)

        apps = self.migrate_to(MIGRATION_0009)

        abandoned = self.user_game_values(apps, abandoned_id, "abandoned", "year_finished")
        self.assertEqual(abandoned, {"abandoned": True, "year_finished": AN_IRRELEVANT_REAL_YEAR})
        finished = self.user_game_values(apps, finished_id, "abandoned", "year_finished")
        self.assertEqual(finished, {"abandoned": False, "year_finished": AN_IRRELEVANT_FINISHED_YEAR})
        pending = self.user_game_values(apps, pending_id, "abandoned", "year_finished")
        self.assertEqual(pending, {"abandoned": False, "year_finished": None})


class ResetInvalidYearFinishedTests(MigrationTestCase):
    def setUp(self) -> None:
        super().setUp()
        apps = self.migrate_to(MIGRATION_0012)
        self.unknown_year_id = self.create_user_game(apps, year_finished=1970)
        self.old_year_id = self.create_user_game(apps, year_finished=1900)
        self.future_year_id = self.create_user_game(apps, year_finished=3001)
        self.valid_year_id = self.create_user_game(apps, year_finished=AN_IRRELEVANT_FINISHED_YEAR)
        self.first_valid_year_id = self.create_user_game(apps, year_finished=1971)
        self.last_valid_year_id = self.create_user_game(apps, year_finished=3000)
        self.pending_id = self.create_user_game(apps, year_finished=None)

    def _year_finished(self, apps: StateApps, user_game_id: int) -> Optional[int]:
        year_finished: Optional[int] = self.user_game_values(apps, user_game_id, "year_finished")["year_finished"]
        return year_finished

    def test_forward_resets_out_of_range_years_to_null(self) -> None:
        apps = self.migrate_to(MIGRATION_0013)

        for user_game_id in (self.unknown_year_id, self.old_year_id, self.future_year_id):
            with self.subTest(user_game_id=user_game_id):
                self.assertIsNone(self._year_finished(apps, user_game_id))

    def test_forward_keeps_valid_and_null_years(self) -> None:
        apps = self.migrate_to(MIGRATION_0013)

        self.assertEqual(self._year_finished(apps, self.valid_year_id), AN_IRRELEVANT_FINISHED_YEAR)
        self.assertEqual(self._year_finished(apps, self.first_valid_year_id), 1971)
        self.assertEqual(self._year_finished(apps, self.last_valid_year_id), 3000)
        self.assertIsNone(self._year_finished(apps, self.pending_id))

    def test_forward_prints_reset_count(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            self.migrate_to(MIGRATION_0013)

        self.assertIn("finished games reset to pending (invalid year): 3", output.getvalue())

    def test_forward_twice_is_a_no_op_and_prints_zero(self) -> None:
        apps = self.migrate_to(MIGRATION_0013)
        migration_module = import_module("core.migrations.0013_reset_invalid_year_finished")
        output = io.StringIO()

        with redirect_stdout(output):
            migration_module.reset_invalid_year_finished(apps, None)

        self.assertIn("finished games reset to pending (invalid year): 0", output.getvalue())
        self.assertEqual(self._year_finished(apps, self.valid_year_id), AN_IRRELEVANT_FINISHED_YEAR)
        self.assertIsNone(self._year_finished(apps, self.unknown_year_id))

    def test_reverse_is_a_lossy_no_op(self) -> None:
        self.migrate_to(MIGRATION_0013)

        apps = self.migrate_to(MIGRATION_0012)

        self.assertIsNone(self._year_finished(apps, self.unknown_year_id))
        self.assertEqual(self._year_finished(apps, self.valid_year_id), AN_IRRELEVANT_FINISHED_YEAR)

    def test_constraint_migration_applies_after_reset_and_rejects_invalid_years(self) -> None:
        apps = self.migrate_to(MIGRATION_0014)

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_user_game(apps, year_finished=1970)
