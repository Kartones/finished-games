from django import forms
from django.core.validators import (MaxValueValidator, MinValueValidator)
from django.db.models.functions import Lower

from core.models import (
    Game,
    Platform,
)
from catalogsources.admin.form_fields import SimpleArrayField


class SingleFetchedPlatformImportForm(forms.Form):
    """
    This form will only display field data, is not meant to be sent back.
    Field values will be used at the template to either display some data or populate SinglePlatformImportForm fields.
    """
    fetched_name = forms.CharField(label="Name", max_length=100, disabled=True)
    fetched_shortname = forms.CharField(label="Shortname", max_length=40, disabled=True)
    fetched_publish_date = forms.IntegerField(
        label="Year published",
        validators=[MinValueValidator(1970), MaxValueValidator(3000)],
        disabled=True,
    )
    source_id = forms.CharField(label="Source", max_length=50, disabled=True)
    source_platform_id = forms.CharField(label="Source platform identifier", max_length=50, disabled=True)
    source_url = forms.CharField(label="Source URI", max_length=255, disabled=True)
    hidden = forms.BooleanField(label="Item hidden", disabled=True)
    last_modified_date = forms.DateTimeField(label="Last data modification", disabled=True)
    fg_platform_id = forms.IntegerField(label="Mapped Platform id", disabled=True)
    fg_platform_name = forms.CharField(label="Mapped Platform name", max_length=100, disabled=True)


class SinglePlatformImportForm(forms.Form):
    fetched_platform_id = forms.IntegerField(widget=forms.HiddenInput)
    platform_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    name = forms.CharField(
        label="Name",
        max_length=100,
        initial="",
        widget=forms.TextInput(attrs={"size": "60", "class": "vTextField"})
    )
    shortname = forms.CharField(
        label="Shortname",
        max_length=40,
        initial="",
        widget=forms.TextInput(attrs={"size": "40", "class": "vTextField"})
    )
    publish_date = forms.IntegerField(
        label="Year published",
        validators=[MinValueValidator(1970), MaxValueValidator(3000)],
        widget=forms.NumberInput(attrs={"class": "vIntegerField"})
    )


class PlatformsImportForm(forms.Form):
    fields = SimpleArrayField(forms.CharField(max_length=15))
    fetched_platform_ids = SimpleArrayField(forms.IntegerField())
    fg_platform_ids = SimpleArrayField(forms.IntegerField())
    names = SimpleArrayField(forms.CharField(max_length=100))
    shortnames = SimpleArrayField(forms.CharField(max_length=40))
    publish_date_strings = SimpleArrayField(forms.CharField(max_length=4))


class SingleFetchedGameImportForm(forms.Form):
    """
    This form will only display field data, is not meant to be sent back.
    Field values will be used at the template to either display some data or populate SingleGameImportForm fields.
    """
    fetched_name = forms.CharField(label="Name", max_length=200, disabled=True)
    fetched_publish_date = forms.IntegerField(
        label="Year published",
        validators=[MinValueValidator(1970), MaxValueValidator(3000)],
        disabled=True,
    )
    fg_platform_ids = forms.CharField(label="Fetched Platform Ids", disabled=True)
    fg_platforms = forms.CharField(label="Fetched Platforms", disabled=True)
    fetched_dlc_or_expansion = forms.BooleanField(label="DLC/Expansion", disabled=True)
    source_id = forms.CharField(label="Source identifier", max_length=50, disabled=True)
    source_game_id = forms.CharField(label="Source game identifier", max_length=50, disabled=True)
    source_url = forms.CharField(label="Resource source URI", max_length=255, disabled=True)

    hidden = forms.BooleanField(label="Item hidden", disabled=True)
    last_modified_date = forms.DateTimeField(label="Last data modification", disabled=True)
    fg_game_id = forms.IntegerField(disabled=True)
    fg_game_name = forms.CharField(label="Mapped to Game", max_length=200, disabled=True)
    fetched_parent_game_name = forms.CharField(label="Parent Fetched Game", max_length=200, disabled=True)
    parent_game_fg_game_id = forms.IntegerField(disabled=True)


class SingleGameImportForm(forms.Form):
    fetched_game_id = forms.IntegerField(widget=forms.HiddenInput)
    game_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    name = forms.CharField(
        label="Name",
        max_length=200,
        initial="",
        widget=forms.TextInput(attrs={"size": "60", "class": "vTextField"})
    )
    publish_date = forms.IntegerField(
        label="Year published",
        validators=[MinValueValidator(1970), MaxValueValidator(3000)],
        widget=forms.NumberInput(attrs={"class": "vIntegerField"})
    )
    platforms = forms.ModelMultipleChoiceField(queryset=Platform.objects.order_by(Lower("name")))
    dlc_or_expansion = forms.BooleanField(label="DLC/Expansion", initial=False, required=False)
    # TODO: Use https://django-autocomplete-light.readthedocs.io/en/master/tutorial.html
    parent_game = forms.ModelChoiceField(
        label="Parent game",
        queryset=Game.objects.order_by(Lower("name")),
        required=False,
    )
    source_display_name = forms.CharField(
        label="Source display name (for URL button)",
        max_length=255,
        widget=forms.TextInput(attrs={"size": "30", "readonly": ""}),
    )
    source_url = forms.CharField(
        label="Source URL (will be added/updated to existing ones)",
        max_length=255,
        widget=forms.TextInput(attrs={"size": "60", "readonly": ""}),
    )
