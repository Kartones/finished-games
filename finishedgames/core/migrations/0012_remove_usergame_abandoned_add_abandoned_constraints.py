from django.db import migrations, models
from django.db.models import Q


def repopulate_flag(apps, _):
    UserGame = apps.get_model("core", "UserGame")

    UserGame.objects.filter(year_abandoned__isnull=False).update(abandoned=True)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_migrate_abandoned_to_year_abandoned"),
    ]

    operations = [
        migrations.RunPython(migrations.RunPython.noop, repopulate_flag),
        migrations.RemoveField(
            model_name="usergame",
            name="abandoned",
        ),
        migrations.AddConstraint(
            model_name="usergame",
            constraint=models.CheckConstraint(
                condition=Q(year_finished__isnull=True) | Q(year_abandoned__isnull=True),
                name="usergame_not_finished_and_abandoned",
            ),
        ),
        migrations.AddConstraint(
            model_name="usergame",
            constraint=models.CheckConstraint(
                # Frozen bounds from core/constants.py keep migration history stable.
                condition=Q(year_abandoned__isnull=True) | Q(year_abandoned__gte=1971, year_abandoned__lte=3000),
                name="usergame_year_abandoned_in_range",
            ),
        ),
    ]
