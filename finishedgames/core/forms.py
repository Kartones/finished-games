from datetime import datetime
from typing import Any, Dict, cast

from core.models import Game, Platform
from django.forms import ModelForm, ValidationError


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
        if self.cleaned_data.get("dlc_or_expansion", False):
            if not self.cleaned_data.get("parent_game", None):
                raise ValidationError({"parent_game": "A Game DLC must specify a parent game"})
            if self.cleaned_data["parent_game"].dlc_or_expansion:
                raise ValidationError({"parent_game": "A Game DLC cannot have as parent another game DLC"})

            all_platforms = self.cleaned_data["platforms"].all()
            all_parent_game_platforms = self.cleaned_data["parent_game"].platforms.all()

            # platforms should be a subset of parent platforms
            new_game_platforms = sorted((item.id for item in all_platforms if item in all_parent_game_platforms))
            parent_game_platforms = sorted((item.id for item in all_platforms))
            if not new_game_platforms == parent_game_platforms:
                raise ValidationError(
                    {
                        "platforms": "Game DLC must be available on subset/all of parent game platforms: '{}'".format(
                            "','".join((platform.name for platform in all_parent_game_platforms))
                        )
                    }
                )

        return cast(Dict, self.cleaned_data)
