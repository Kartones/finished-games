# Generated by Django 2.1.7 on 2019-03-22 16:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_usergame_no_longer_owned"),
    ]

    operations = [
        migrations.AddField(
            model_name="game",
            name="urls",
            field=models.CharField(blank=True, default="", max_length=2000, verbose_name="URLs"),
        ),
    ]
