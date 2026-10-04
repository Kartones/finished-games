import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_usergame_minutes_played"),
    ]

    operations = [
        migrations.AddField(
            model_name="usergame",
            name="year_abandoned",
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
                verbose_name="Year abandoned",
            ),
        ),
    ]
