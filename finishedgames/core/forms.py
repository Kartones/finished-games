from datetime import datetime
from typing import (Any, cast, Dict)

from django.forms import (ModelForm, ValidationError)

from core.models import (Game, Platform, UserGame, WishlistedUserGame)


# TODO: Use when adding data fields for the user, like an avatar (or fully remove)
"""
class UserDataForm(ModelForm):
    class Meta:
        model = UserData
        fields = "__all__"
"""


class UserGameForm(ModelForm):
    class Meta:
        model = UserGame
        fields = "__all__"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def clean(self) -> Dict:
        super().clean()

        game_platforms = self.cleaned_data["game"].platforms.all()
        if self.cleaned_data["platform"] not in game_platforms:
            raise ValidationError({
                "platform": "'{}'  not available in platform '{}'. Available platforms: '{}'".format(
                    self.cleaned_data["game"].name,
                    self.cleaned_data["platform"].name,
                    "','".join([platform.name for platform in game_platforms])
                    )
                })

        return cast(Dict, self.cleaned_data)


class PlatformForm(ModelForm):
    class Meta:
        model = Platform
        fields = "__all__"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if "publish_date" not in self.initial:
            self.initial["publish_date"] = datetime.now().year

    def validate_unique(self) -> None:
        super().validate_unique()

        exiting_existing = not self.instance._state.adding

        if "name" in self.cleaned_data:
            try:
                existing_platform = Platform.objects.get(name__iexact=self.cleaned_data["name"])
            except Platform.DoesNotExist:
                pass
            else:
                if self.instance._state.adding or (exiting_existing and existing_platform.pk != self.instance.pk):
                    raise ValidationError({"name": "Platform with this name already exists."})

        if "shortname" in self.cleaned_data:
            try:
                existing_platform = Platform.objects.get(shortname__iexact=self.cleaned_data["shortname"])
            except Platform.DoesNotExist:
                pass
            else:
                if self.instance._state.adding or (exiting_existing and existing_platform.pk != self.instance.pk):
                    raise ValidationError({"shortname": "Platform with this shortname already exists."})


class GameForm(ModelForm):
    class Meta:
        model = Game
        fields = ["name", "platforms", "publish_date", "dlc_or_expansion", "parent_game"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if "publish_date" not in self.initial:
            self.initial["publish_date"] = datetime.now().year

    def validate_unique(self) -> None:
        super().validate_unique()

        exiting_existing = not self.instance._state.adding

        if "name" in self.cleaned_data:
            try:
                existing_game = Game.objects.get(name__iexact=self.cleaned_data["name"])
            except Game.DoesNotExist:
                pass
            else:
                if self.instance._state.adding or (exiting_existing and existing_game.pk != self.instance.pk):
                    raise ValidationError({"name": "Game with this name already exists."})

    def clean(self) -> Dict:
        super().clean()

        # If a game is DLC:
        if "dlc_or_expansion" in self.cleaned_data and self.cleaned_data["dlc_or_expansion"]:
            if "parent_game" not in self.cleaned_data or not self.cleaned_data["parent_game"]:
                raise ValidationError({"parent_game": "A Game DLC must specify a parent game"})
            if self.cleaned_data["parent_game"].dlc_or_expansion:
                raise ValidationError({"parent_game": "A Game DLC cannot have as parent another game DLC"})

            # platforms should be a subset of parent platforms
            new_game_platforms = sorted([
                item.id
                for item in self.cleaned_data["platforms"].all()
                if item in self.cleaned_data["parent_game"].platforms.all()
            ])
            parent_game_platforms = sorted([item.id for item in self.cleaned_data["platforms"].all()])
            if not new_game_platforms == parent_game_platforms:
                raise ValidationError({
                    "platforms": "Game DLC must be available on subset or all of parent game platforms: '{}'".format(
                        "','".join([platform.name for platform in self.cleaned_data["parent_game"].platforms.all()])
                    )
                })

        return cast(Dict, self.cleaned_data)


class WishlistedUserGameForm(ModelForm):
    class Meta:
        model = WishlistedUserGame
        fields = "__all__"

    def clean(self) -> Dict:
        super().clean()

        game_platforms = self.cleaned_data["game"].platforms.all()
        if self.cleaned_data["platform"] not in game_platforms:
            raise ValidationError({
                "platform": "'{}'  not available in platform '{}'. Available platforms: '{}'".format(
                    self.cleaned_data["game"].name,
                    self.cleaned_data["platform"].name,
                    "','".join([platform.name for platform in game_platforms])
                    )
                })

        return cast(Dict, self.cleaned_data)
