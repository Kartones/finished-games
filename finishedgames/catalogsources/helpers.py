from typing import Optional
import unicodedata


def clean_string_field(field: Optional[str]) -> Optional[str]:
    if field is None:
        return None
    else:
        return unicodedata.normalize("NFC", field.strip(" _!-:"))
