from django.db import migrations
from django.db.models import Q

# Frozen bounds from core/constants.py keep migration history stable.
MIN_VALID_YEAR = 1971
MAX_VALID_YEAR = 3000


def reset_invalid_year_finished(apps, _):
    UserGame = apps.get_model("core", "UserGame")

    invalid_rows = UserGame.objects.filter(Q(year_finished__lt=MIN_VALID_YEAR) | Q(year_finished__gt=MAX_VALID_YEAR))
    reset_count = invalid_rows.update(year_finished=None)

    print("\n  finished games reset to pending (invalid year): {}".format(reset_count))


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_remove_usergame_abandoned_add_abandoned_constraints"),
    ]

    operations = [
        # Reverse is a no-op: reset years are lost (accepted)
        migrations.RunPython(reset_invalid_year_finished, migrations.RunPython.noop),
    ]
