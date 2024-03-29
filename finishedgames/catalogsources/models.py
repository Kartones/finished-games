import hashlib
from typing import Any

from core.models import BaseGame, BasePlatform, Game, Platform
from django.db import models
from django.utils import timezone


class FetchedGame(BaseGame):
    source_id = models.CharField("Source identifier", max_length=50, db_index=True)
    last_modified_date = models.DateTimeField(
        "Last data modification", null=True, default=None, blank=True, db_index=True
    )
    last_sync_date = models.DateTimeField("Last synchronization", null=True, default=None, blank=True, db_index=True)
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
    cover = models.CharField("Cover filename", max_length=100, null=True, default=None, blank=True)

    @property
    def platforms_list(self) -> str:
        return ", ".join((platform.shortname for platform in self.platforms.all()))

    @property
    def is_sync(self) -> bool:
        if self.fg_game and self.last_sync_date == self.last_modified_date:
            return True
        return False

    @property
    def can_sync(self) -> bool:
        return True if self.fg_game else False

    def mark_as_synchronized(self) -> None:
        if not self.can_sync:
            raise ValueError("Cannot synchronize a not imported game")

        self.last_sync_date = self.last_modified_date

    def name_for_cover(self) -> str:
        name = "".join([char for char in self.name.lower() if any([char.isalnum(), char in [" "]])]).replace(" ", "_")
        if len(name) < 1:
            name = "{}_{}".format(self.source_id, self.source_game_id)
        return name.replace("%20", "_").replace("%", "")

    def save(self, *args: Any, **kwargs: Any) -> None:
        new_changes_hash = self._get_changes_hash()

        if new_changes_hash != self.change_hash:
            self.change_hash = new_changes_hash
            self.last_modified_date = timezone.now()

        super().save(*args, **kwargs)

    def _get_changes_hash(self) -> str:
        md5_hash = hashlib.md5()  # nosec
        md5_hash.update(str.encode(self._get_fields_for_hash()))
        return md5_hash.hexdigest()

    def _get_fields_for_hash(self) -> str:
        # Cannot use many to many relations until entity has an id
        if self.id:
            platforms = ",".join((str(platform.id) for platform in self.platforms.all()))
        else:
            platforms = ""

        return "{name}-{publish_date}-{dlc}-{platforms}-{parent}-{fg_game_id}-{source_game_id}-{source_url}-{cover}".format(  # NOQA: E501
            name=self.name,
            publish_date=self.publish_date,
            dlc=self.dlc_or_expansion,
            platforms=platforms,
            parent=self.parent_game,
            fg_game_id=self.fg_game if self.fg_game else "",
            source_game_id=self.source_game_id,
            source_url=self.source_url,
            cover="",
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
        md5_hash = hashlib.md5()  # nosec
        md5_hash.update(str.encode(self._get_fields_for_hash()))
        return md5_hash.hexdigest()

    def _get_fields_for_hash(self) -> str:
        return "{name}-{shortname}-{publish_date}-{fg_platform}-{source_platform_id}-{source_url}".format(
            name=self.name,
            shortname=self.shortname,
            publish_date=self.publish_date,
            fg_platform=self.fg_platform if self.fg_platform else "",
            source_platform_id=self.source_platform_id,
            source_url=self.source_url,
        )

    def __str__(self) -> str:
        return "{} [{}]".format(self.name, self.source_id)
