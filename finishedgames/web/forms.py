from core.models import Game, Platform
from dal import autocomplete
from django import forms
from django.db.models.functions import Lower


class GameSearchForm(forms.Form):
    game = forms.ModelChoiceField(
        label="Search for a game",
        queryset=Game.objects.order_by(Lower("name")),
        widget=autocomplete.ModelSelect2(
            url="game_autocomplete",
            attrs={
                "data-placeholder": "Input game name",
                "data-minimum-input-length": 3,
                "data-maximum-input-length": 200,
                "data-width": "85%",
            },
        ),
    )


class PlatformFilterform(forms.Form):
    platform = forms.ModelChoiceField(
        label="Filter by platform",
        queryset=Platform.objects.only("id", "shortname").order_by(Lower("shortname")),
        widget=autocomplete.ModelSelect2(
            url="platform_autocomplete",
            forward=["username", "filter_type"],
            attrs={
                "data-placeholder": "Input platform name",
                "data-minimum-input-length": 2,
                "data-maximum-input-length": 100,
                "data-width": "50%",
                "data-allow-clear": "true",
            },
        ),
    )
    username = forms.CharField(max_length=100, widget=forms.HiddenInput)
    filter_type = forms.CharField(min_length=7, max_length=10, widget=forms.HiddenInput)
