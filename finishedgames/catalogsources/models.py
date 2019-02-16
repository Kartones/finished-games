from datetime import datetime
import hashlib
from typing import Any

from django.db import models

from core.models import BasePlatform


class FetchedPlatform(BasePlatform):
    source_id = models.CharField("Source identifier", max_length=50, db_index=True)
    last_fetch_date = models.DateTimeField("Last data fetch", null=True, default=None, blank=True)
    last_modified_date = models.DateTimeField(
        "Last data modification", null=True, default=None, blank=True, db_index=True
    )
    source_id = models.CharField("Source identifier", max_length=50, db_index=True)
    source_url = models.CharField("Resource source URI", max_length=255)
    change_hash = models.CharField("Marker to detect data changes after a fetch", max_length=32)

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.shortname:
            self.shortname = self.name
        self.last_fetch_date = datetime.now()

        md5_hash = hashlib.md5()
        md5_hash.update(str.encode(self._fields_for_hash()))
        new_changes_hash = md5_hash.hexdigest()

        if new_changes_hash != self.change_hash:
            self.change_hash = new_changes_hash
            self.last_modified_date = self.last_fetch_date

        super().save(*args, **kwargs)

    def _fields_for_hash(self) -> str:
        return "{name}-{shortname}-{publish_date}-{source_id}-{source_url}".format(
            name=self.name, shortname=self.shortname, publish_date=self.publish_date, source_id=self.source_id,
            source_url=self.source_url
        )

    def __str__(self) -> str:
        return "{} [{}]".format(self.name, self.source_id)
