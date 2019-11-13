# Generated by Django 2.1.7 on 2019-02-26 23:23

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0002_usergame_no_longer_owned"),
    ]

    operations = [
        migrations.CreateModel(
            name="FetchedGame",
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
                ("source_id", models.CharField(db_index=True, max_length=50, verbose_name="Source identifier")),
                (
                    "last_modified_date",
                    models.DateTimeField(
                        blank=True, db_index=True, default=None, null=True, verbose_name="Last data modification"
                    ),
                ),
                (
                    "source_game_id",
                    models.CharField(db_index=True, max_length=50, verbose_name="Source game identifier"),
                ),
                ("source_url", models.CharField(max_length=255, verbose_name="Resource source URI")),
                (
                    "change_hash",
                    models.CharField(max_length=32, verbose_name="Marker to detect data changes after fetch"),
                ),
                ("hidden", models.BooleanField(db_index=True, default=False, verbose_name="Item hidden")),
                (
                    "fg_game_id",
                    models.ForeignKey(
                        blank=True,
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="core.Game",
                    ),
                ),
                (
                    "parent_game",
                    models.ForeignKey(
                        blank=True,
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="catalogsources.FetchedGame",
                    ),
                ),
                ("platforms", models.ManyToManyField(to="core.Platform")),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="FetchedPlatform",
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
                ("source_id", models.CharField(db_index=True, max_length=50, verbose_name="Source identifier")),
                (
                    "last_modified_date",
                    models.DateTimeField(
                        blank=True, db_index=True, default=None, null=True, verbose_name="Last data modification"
                    ),
                ),
                (
                    "source_platform_id",
                    models.CharField(db_index=True, max_length=50, verbose_name="Source platform identifier"),
                ),
                ("source_url", models.CharField(max_length=255, verbose_name="Resource source URI")),
                (
                    "change_hash",
                    models.CharField(max_length=32, verbose_name="Marker to detect data changes after fetch"),
                ),
                ("hidden", models.BooleanField(db_index=True, default=False, verbose_name="Item hidden")),
                (
                    "fg_platform",
                    models.ForeignKey(
                        blank=True,
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="core.Platform",
                    ),
                ),
            ],
            options={"abstract": False},
        ),
    ]
