from typing import Any, List, Optional, cast

from django import forms
from django.contrib.postgres.utils import prefix_validation_error
from django.contrib.postgres.validators import ArrayMaxLengthValidator, ArrayMinLengthValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class SimpleArrayField(forms.Field):
    """
    Source from https://docs.djangoproject.com/en/2.2/_modules/django/contrib/postgres/forms/array/#SimpleArrayField
    but as trying to import it causes requiring psycopg2 module, this is non-postgresql dependant
    """

    default_error_messages = {
        "item_invalid": _("Item %(nth)s in the array did not validate:"),
    }

    def __init__(
        self,
        base_field: forms.Field,
        *,
        delimiter: str = ",",
        max_length: Optional[int] = None,
        min_length: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        self.base_field = base_field
        self.delimiter = delimiter
        super().__init__(**kwargs)
        if min_length is not None:
            self.min_length = min_length
            self.validators.append(ArrayMinLengthValidator(int(min_length)))
        if max_length is not None:
            self.max_length = max_length
            self.validators.append(ArrayMaxLengthValidator(int(max_length)))

    def clean(self, value: Any) -> List[Any]:
        value = super().clean(value)
        return [self.base_field.clean(val) for val in value]

    def prepare_value(self, value: Any) -> Any:
        if isinstance(value, list):
            return self.delimiter.join(str(self.base_field.prepare_value(v)) for v in value)
        return value

    def to_python(self, value: Any) -> List[Any]:
        if isinstance(value, list):
            items = value
        elif value:
            items = value.split(self.delimiter)
        else:
            items = []
        errors = []
        values = []
        for index, item in enumerate(items):
            try:
                values.append(self.base_field.to_python(item))
            except ValidationError as error:
                errors.append(
                    prefix_validation_error(
                        error,
                        prefix=self.error_messages["item_invalid"],
                        code="item_invalid",
                        params={"nth": index + 1},
                    )
                )
        if errors:
            raise ValidationError(errors)
        return values

    def validate(self, value: Any) -> None:
        super().validate(value)
        errors = []
        for index, item in enumerate(value):
            try:
                self.base_field.validate(item)
            except ValidationError as error:
                errors.append(
                    prefix_validation_error(
                        error,
                        prefix=self.error_messages["item_invalid"],
                        code="item_invalid",
                        params={"nth": index + 1},
                    )
                )
        if errors:
            raise ValidationError(errors)

    def run_validators(self, value: Any) -> None:
        super().run_validators(value)
        errors = []
        for index, item in enumerate(value):
            try:
                self.base_field.run_validators(item)
            except ValidationError as error:
                errors.append(
                    prefix_validation_error(
                        error,
                        prefix=self.error_messages["item_invalid"],
                        code="item_invalid",
                        params={"nth": index + 1},
                    )
                )
        if errors:
            raise ValidationError(errors)

    def has_changed(self, initial: Any, data: Any) -> bool:
        try:
            value = self.to_python(data)
        except ValidationError:
            pass
        else:
            if initial in self.empty_values and value in self.empty_values:
                return False
        return cast(bool, super().has_changed(initial, data))
