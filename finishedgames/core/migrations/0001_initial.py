# Generated by Django 2.1.5 on 2019-01-22 21:29

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Game",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=200, unique=True, verbose_name="Name")),
                (
                    "publish_date",
                    models.IntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1970),
                            django.core.validators.MaxValueValidator(3000),
                        ],
                        verbose_name="Year first published",
                    ),
                ),
                ("dlc_or_expansion", models.BooleanField(default=False, verbose_name="DLC/Expansion")),
                (
                    "parent_game",
                    models.ForeignKey(
                        blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to="core.Game"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Platform",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=100, unique=True, verbose_name="Name")),
                ("shortname", models.CharField(default=None, max_length=40, unique=True, verbose_name="Shortname")),
                (
                    "publish_date",
                    models.IntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1970),
                            django.core.validators.MaxValueValidator(3000),
                        ],
                        verbose_name="Year published",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserGame",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "currently_playing",
                    models.BooleanField(db_index=True, default=False, verbose_name="Currently playing"),
                ),
                (
                    "year_finished",
                    models.IntegerField(
                        blank=True,
                        db_index=True,
                        default=None,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(1970),
                            django.core.validators.MaxValueValidator(3000),
                        ],
                        verbose_name="Year finished",
                    ),
                ),
                ("game", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="core.Game")),
                ("platform", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="core.Platform")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="WishlistedUserGame",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("game", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="core.Game")),
                ("platform", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="core.Platform")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={"abstract": False},
        ),
        migrations.AddField(model_name="game", name="platforms", field=models.ManyToManyField(to="core.Platform"),),
        migrations.AlterUniqueTogether(name="wishlistedusergame", unique_together={("user", "game", "platform")},),
        migrations.AlterUniqueTogether(name="usergame", unique_together={("user", "game", "platform")},),
    ]
