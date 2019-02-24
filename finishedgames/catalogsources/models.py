import hashlib
from typing import Any

from django.db import models
from django.utils import timezone

from core.models import (BaseGame, BasePlatform, Game, Platform)


class FetchedGame(BaseGame):
    source_id = models.CharField("Source identifier", max_length=50, db_index=True)
    last_fetch_date = models.DateTimeField("Last data fetch", null=True, default=None, blank=True)
    last_modified_date = models.DateTimeField(
        "Last data modification", null=True, default=None, blank=True, db_index=True
    )
    source_game_id = models.CharField("Source game identifier", max_length=50, db_index=True)
    source_url = models.CharField("Resource source URI", max_length=255)
    change_hash = models.CharField("Marker to detect data changes after fetch", max_length=32)
    hidden = models.BooleanField("Item hidden", default=False, db_index=True)
    fg_game_id = models.ForeignKey(Game, on_delete=models.SET_NULL, null=True, default=None, blank=True)
    # Override parent FK
    parent_game = models.ForeignKey("FetchedGame", on_delete=models.CASCADE, null=True, default=None, blank=True)

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.last_fetch_date = timezone.now()

        new_changes_hash = self._get_changes_hash()
        if new_changes_hash != self.change_hash:
            self.change_hash = new_changes_hash
            self.last_modified_date = self.last_fetch_date

        super().save(*args, **kwargs)

    @property
    def modified(self) -> bool:
        return bool(self.last_modified_date == self.last_fetch_date)

    def _get_changes_hash(self) -> str:
        md5_hash = hashlib.md5()
        md5_hash.update(str.encode(self._get_fields_for_hash()))
        return md5_hash.hexdigest()

    def _get_fields_for_hash(self) -> str:
        # Cannot use many to many relations until entity has an id
        if self.id:
            platforms = self.platforms
        else:
            platforms = None

        return "{name}-{publish_date}-{dlc}-{platforms}-{parent}-{source_game_id}-{fg_game_id}-{source_url}".format(
            name=self.name, publish_date=self.publish_date, dlc=self.dlc_or_expansion, platforms=platforms,
            parent=self.parent_game, source_game_id=self.source_game_id, fg_game_id=self.fg_game_id,
            source_url=self.source_url
        )

    def __str__(self) -> str:
        return "{} [{}]".format(self.name, self.source_id)


class FetchedPlatform(BasePlatform):
    source_id = models.CharField("Source identifier", max_length=50, db_index=True)
    last_fetch_date = models.DateTimeField("Last data fetch", null=True, default=None, blank=True)
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

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.shortname:
            self.shortname = self.name
        self.last_fetch_date = timezone.now()

        new_changes_hash = self._get_changes_hash()
        if new_changes_hash != self.change_hash:
            self.change_hash = new_changes_hash
            self.last_modified_date = self.last_fetch_date

        super().save(*args, **kwargs)

    @property
    def modified(self) -> bool:
        return bool(self.last_modified_date == self.last_fetch_date)

    def _get_changes_hash(self) -> str:
        md5_hash = hashlib.md5()
        md5_hash.update(str.encode(self._get_fields_for_hash()))
        return md5_hash.hexdigest()

    def _get_fields_for_hash(self) -> str:
        return "{name}-{shortname}-{publish_date}-{source_platform_id}-{fg_platform_id}-{source_url}".format(
            name=self.name, shortname=self.shortname, publish_date=self.publish_date,
            source_platform_id=self.source_platform_id, fg_platform_id=self.fg_platform_id, source_url=self.source_url
        )

    def __str__(self) -> str:
        return "{} [{}]".format(self.name, self.source_id)
