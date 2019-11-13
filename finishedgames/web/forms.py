from core.models import Game
from dal import autocomplete
from django import forms
from django.db.models.functions import Lower


class GameSearchForm(forms.Form):
    game = forms.ModelChoiceField(
        label="Search for a game",
        queryset=Game.objects.order_by(Lower("name")),
        widget=autocomplete.ModelSelect2(
            url="game_autocomplete",
            attrs={"data-placeholder": "Input here game name", "data-minimum-input-length": 3, "data-width": "85%"},
        ),
    )
