import django.core.validators
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_reset_invalid_year_finished"),
    ]

    operations = [
        migrations.AlterField(
            model_name="usergame",
            name="year_finished",
            field=models.IntegerField(
                blank=True,
                db_index=True,
                default=None,
                null=True,
                validators=[
                    # Frozen bounds from core/constants.py keep migration history stable.
                    django.core.validators.MinValueValidator(1971),
                    django.core.validators.MaxValueValidator(3000),
                ],
                verbose_name="Year finished",
            ),
        ),
        migrations.AddConstraint(
            model_name="usergame",
            constraint=models.CheckConstraint(
                # Frozen bounds from core/constants.py keep migration history stable.
                condition=Q(year_finished__isnull=True) | Q(year_finished__gte=1971, year_finished__lte=3000),
                name="usergame_year_finished_in_range",
            ),
        ),
    ]
