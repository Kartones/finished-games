# Generated by Django 2.1.7 on 2019-03-09 12:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("catalogsources", "0003_auto_20190303_2035"),
    ]

    operations = [
        migrations.RenameField(model_name="fetchedgame", old_name="fg_game_id", new_name="fg_game",),
    ]
