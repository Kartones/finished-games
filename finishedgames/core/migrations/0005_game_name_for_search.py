# Generated by Django 2.2.16 on 2020-09-17 21:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_usergame_abandoned"),
    ]

    operations = [
        migrations.AddField(
            model_name="game",
            name="name_for_search",
            field=models.CharField(
                blank=True, db_index=True, default="", max_length=200, verbose_name="Simplified name for searches"
            ),
        ),
    ]