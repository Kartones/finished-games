from typing import Dict, cast

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.helpers import generic_id as generic_id_helper

URLS_KEY_VALUE_GLUE = "||"
URLS_ITEMS_GLUE = "@@"


class BasePlatform(models.Model):
    name = models.CharField("Name", max_length=100, unique=True, db_index=True)
    shortname = models.CharField("Shortname", max_length=40, unique=True, default=None)
    publish_date = models.IntegerField(
        "Year published",
        validators=[MinValueValidator(1970), MaxValueValidator(3000)],
    )

    class Meta:
        abstract = True


class Platform(BasePlatform):

    def __str__(self) -> str:
        return cast(str, self.name)


class BaseGame(models.Model):
    name = models.CharField("Name", max_length=200, unique=True, db_index=True)
    publish_date = models.IntegerField(
        "Year first published",
        validators=[MinValueValidator(1970), MaxValueValidator(3000)],
    )
    dlc_or_expansion = models.BooleanField("DLC/Expansion", default=False)
    platforms = models.ManyToManyField(Platform)
    parent_game = models.ForeignKey("Game", on_delete=models.CASCADE, null=True, default=None, blank=True)

    class Meta:
        abstract = True


class Game(BaseGame):
    urls = models.CharField("URLs", max_length=2000, blank=True, default="")

    @property
    def platforms_list(self) -> str:
        return ", ".join((platform.shortname for platform in self.platforms.all()))

    @property
    def urls_dict(self) -> Dict[str, str]:
        _urls_dict = {}  # type: Dict[str, str]

        for urldata in self.urls.split(URLS_ITEMS_GLUE):
            fragments = urldata.split(URLS_KEY_VALUE_GLUE)
            if len(fragments) == 2:
                _urls_dict[fragments[0]] = fragments[1]

        return _urls_dict

    def upsert_url(self, display_name: str, url: str) -> None:
        _urls_dict = self.urls_dict
        _urls_dict[display_name] = url

        self.urls = URLS_ITEMS_GLUE.join(
            ("{}{}{}".format(key, URLS_KEY_VALUE_GLUE, _urls_dict[key]) for key in _urls_dict.keys())
        )

    def __str__(self) -> str:
        dlc_fragment = " [DLC/Expansion]" if self.dlc_or_expansion else ""
        return "{}{}".format(self.name, dlc_fragment)


class BaseUserGame(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, db_index=True)
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, db_index=True)

    class Meta:
        abstract = True
        unique_together = (("user", "game", "platform"),)

    @property
    def generic_id(self) -> str:
        return generic_id_helper(self.game.id, self.platform.id)


class UserGame(BaseUserGame):
    currently_playing = models.BooleanField("Currently playing", default=False, db_index=True)
    year_finished = models.IntegerField(
        "Year finished", null=True, default=None, blank=True,
        validators=[MinValueValidator(1970), MaxValueValidator(3000)], db_index=True
    )
    no_longer_owned = models.BooleanField("No longer owned", default=False, db_index=True)
    abandoned = models.BooleanField("Abandoned", default=False, db_index=True)

    def finished(self) -> bool:
        return self.year_finished is not None

    def __str__(self) -> str:
        return "{}: {} ({})".format(self.user.get_username(), self.game.name, self.platform.shortname)

    def clean(self) -> None:
        game_platforms = self.game.platforms.all()
        if self.platform not in game_platforms:
            raise ValidationError({
                "platform": "'{}'  not available in platform '{}'. Available platforms: '{}'".format(
                    self.game.name,
                    self.platform.name,
                    "','".join((platform.name for platform in game_platforms))
                )
            })


class WishlistedUserGame(BaseUserGame):

    def __str__(self) -> str:
        return "{}: {} ({})".format(self.user.get_username(), self.game.name, self.platform.shortname)

    def clean(self) -> None:
        game_platforms = self.game.platforms.all()
        if self.platform not in game_platforms:
            raise ValidationError({
                "platform": "'{}'  not available in platform '{}'. Available platforms: '{}'".format(
                    self.game.name,
                    self.platform.name,
                    "','".join((platform.name for platform in game_platforms))
                )
            })
