from django.db import migrations
from django.db.models import F

# Frozen bounds from core/constants.py keep migration history stable.
MIN_VALID_YEAR = 1971
MAX_VALID_YEAR = 3000


def migrate_abandoned_to_year_abandoned(apps, _):
    UserGame = apps.get_model("core", "UserGame")

    # Rows with year_abandoned already set were copied by a previous run
    pending_rows = UserGame.objects.filter(abandoned=True, year_abandoned__isnull=True)
    movable_rows = pending_rows.filter(year_finished__gte=MIN_VALID_YEAR, year_finished__lte=MAX_VALID_YEAR)
    moved_count = movable_rows.count()
    reset_count = pending_rows.count() - moved_count

    movable_rows.update(year_abandoned=F("year_finished"))
    UserGame.objects.filter(abandoned=True).update(year_finished=None)

    print("\n  abandoned games moved to year_abandoned: {}".format(moved_count))
    print("  abandoned games reset to pending (NULL or unknown year): {}".format(reset_count))


def restore_year_finished_from_year_abandoned(apps, _):
    UserGame = apps.get_model("core", "UserGame")

    UserGame.objects.filter(year_abandoned__isnull=False).update(
        year_finished=F("year_abandoned"), year_abandoned=None
    )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_usergame_year_abandoned"),
    ]

    operations = [
        migrations.RunPython(migrate_abandoned_to_year_abandoned, restore_year_finished_from_year_abandoned),
    ]
