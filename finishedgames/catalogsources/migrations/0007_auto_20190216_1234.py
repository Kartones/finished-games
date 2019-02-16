# Generated by Django 2.1.5 on 2019-02-16 11:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_usergame_no_longer_owned'),
        ('catalogsources', '0006_fetchedgame'),
    ]

    operations = [
        migrations.AddField(
            model_name='fetchedgame',
            name='fg_game_id',
            field=models.ForeignKey(blank=True, default=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.Game'),
        ),
        migrations.AddField(
            model_name='fetchedplatform',
            name='fg_platform_id',
            field=models.ForeignKey(blank=True, default=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.Platform'),
        ),
    ]
