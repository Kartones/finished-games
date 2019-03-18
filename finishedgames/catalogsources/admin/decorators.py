from typing import cast

from django.utils.html import format_html

from core.admin import FGModelAdmin


# Decorator to render source urls as hyperlinks on the listing pages
def hyperlink_source_url(model_instance: FGModelAdmin) -> str:
    return cast(str, format_html("<a href='{url}' target='_blank'>{url}</a>", url=model_instance.source_url))
hyperlink_source_url.short_description = "Source URL"  # type:ignore # NOQA: E305
