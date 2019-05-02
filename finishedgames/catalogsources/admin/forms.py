from django import forms
from django.core.validators import (MaxValueValidator, MinValueValidator)


class SingleFetchedPlatformImportForm(forms.Form):
    """
    This form mostly will only display field data, and is not meant to be sent back.
    Field values will be used at the template to either display some data or populate SinglePlatformImportForm fields.
    """
    fetched_name = forms.CharField(label="Name", max_length=100, disabled=True)
    fetched_shortname = forms.CharField(label="Shortname", max_length=40, disabled=True)
    fetched_publish_date = forms.IntegerField(
        label="Year published", validators=[MinValueValidator(1970), MaxValueValidator(3000)], disabled=True
    )
    source_id = forms.CharField(label="Source", max_length=50, disabled=True)
    source_platform_id = forms.CharField(label="Source platform identifier", max_length=50, disabled=True)
    source_url = forms.CharField(label="Source URI", max_length=255, disabled=True)
    hidden = forms.BooleanField(label="Item hidden", disabled=True)
    last_modified_date = forms.DateTimeField(label="Last data modification", disabled=True)
    fg_platform_id = forms.IntegerField(label="Mapped Platform id", disabled=True)
    fg_platform_name = forms.CharField(label="Mapped Platform name", max_length=100, disabled=True)


class SinglePlatformImportForm(forms.Form):
    platform_id = forms.IntegerField()
    name = forms.CharField(label="Name", max_length=100)
    shortname = forms.CharField(label="Shortname", max_length=40)
    publish_date = forms.IntegerField(
        label="Year published", validators=[MinValueValidator(1970), MaxValueValidator(3000)]
    )
    fetched_platform_id = forms.IntegerField()
