# Generated by Django 2.1.7 on 2019-02-28 18:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalogsources", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fetchedgame",
            name="platforms",
            field=models.ManyToManyField(to="catalogsources.FetchedPlatform"),
        ),
    ]
