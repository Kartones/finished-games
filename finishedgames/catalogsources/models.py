import hashlib
from typing import Any

from django.db import models
from django.utils import timezone

from core.models import (BaseGame, BasePlatform, Game, Platform)


class FetchedGame(BaseGame):
    source_id = models.CharField("Source identifier", max_length=50, db_index=True)
    last_modified_date = models.DateTimeField(
        "Last data modification", null=True, default=None, blank=True, db_index=True
    )
    source_game_id = models.CharField("Source game identifier", max_length=50, db_index=True)
    source_url = models.CharField("Resource source URI", max_length=255)
    change_hash = models.CharField("Marker to detect data changes after fetch", max_length=32)
    hidden = models.BooleanField("Item hidden", default=False, db_index=True)
    fg_game = models.ForeignKey(Game, on_delete=models.SET_NULL, null=True, default=None, blank=True)
    # Override parent fields
    # Allow repeated names as for sure will be duplicates once using multiple sources
    name = models.CharField("Name", max_length=200, unique=False, db_index=True)
    platforms = models.ManyToManyField("FetchedPlatform")
    parent_game = models.ForeignKey("FetchedGame", on_delete=models.CASCADE, null=True, default=None, blank=True)

    def save(self, *args: Any, **kwargs: Any) -> None:
        new_changes_hash = self._get_changes_hash()
        if new_changes_hash != self.change_hash:
            self.change_hash = new_changes_hash
            self.last_modified_date = timezone.now()

        super().save(*args, **kwargs)

    def _get_changes_hash(self) -> str:
        md5_hash = hashlib.md5()
        md5_hash.update(str.encode(self._get_fields_for_hash()))
        return md5_hash.hexdigest()

    def _get_fields_for_hash(self) -> str:
        # Cannot use many to many relations until entity has an id
        if self.id:
            platforms = ",".join([str(platform.id) for platform in self.platforms.all()])
        else:
            platforms = ""

        return "{name}-{publish_date}-{dlc}-{platforms}-{parent}-{source_game_id}-{source_url}".format(
            name=self.name, publish_date=self.publish_date, dlc=self.dlc_or_expansion, platforms=platforms,
            parent=self.parent_game, source_game_id=self.source_game_id, source_url=self.source_url
        )

    def __str__(self) -> str:
        return "{} [{}]".format(self.name, self.source_id)


class FetchedPlatform(BasePlatform):
    source_id = models.CharField("Source identifier", max_length=50, db_index=True)
    last_modified_date = models.DateTimeField(
        "Last data modification", null=True, default=None, blank=True, db_index=True
    )
    source_platform_id = models.CharField("Source platform identifier", max_length=50, db_index=True)
    source_url = models.CharField("Resource source URI", max_length=255)
    change_hash = models.CharField("Marker to detect data changes after fetch", max_length=32)
    hidden = models.BooleanField("Item hidden", default=False, db_index=True)
    # This basic mapping allows to aggregate multiple source platform ids to same destination platform
    # e.g iOS, Android & J2ME -> Mobile
    fg_platform = models.ForeignKey(Platform, on_delete=models.SET_NULL, null=True, default=None, blank=True)
    # Override parent fields
    # Allow repeated names as for sure will be duplicates once using multiple sources
    name = models.CharField("Name", max_length=100, unique=False, db_index=True)
    shortname = models.CharField("Shortname", max_length=40, unique=False, default=None)

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.shortname:
            self.shortname = self.name

        new_changes_hash = self._get_changes_hash()
        if new_changes_hash != self.change_hash:
            self.change_hash = new_changes_hash
            self.last_modified_date = timezone.now()

        super().save(*args, **kwargs)

    def _get_changes_hash(self) -> str:
        md5_hash = hashlib.md5()
        md5_hash.update(str.encode(self._get_fields_for_hash()))
        return md5_hash.hexdigest()

    def _get_fields_for_hash(self) -> str:
        return "{name}-{shortname}-{publish_date}-{source_platform_id}-{source_url}".format(
            name=self.name, shortname=self.shortname, publish_date=self.publish_date,
            source_platform_id=self.source_platform_id, source_url=self.source_url
        )

    def __str__(self) -> str:
        return "{} [{}]".format(self.name, self.source_id)
