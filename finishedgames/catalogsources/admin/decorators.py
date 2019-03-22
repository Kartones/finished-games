from typing import cast

from django.urls import reverse
from django.utils.html import format_html

from core.admin import FGModelAdmin
from catalogsources.models import (FetchedGame, FetchedPlatform)


# Decorator to render source urls as hyperlinks on the listing pages
def hyperlink_source_url(model_instance: FGModelAdmin) -> str:
    return cast(str, format_html("<a href='{url}' target='_blank'>{url}</a>", url=model_instance.source_url))
hyperlink_source_url.short_description = "Source URL"  # type:ignore # NOQA: E305


def hyperlink_fg_game(fetched_game: FetchedGame) -> str:
    if fetched_game.fg_game:
        url = reverse("admin:core_game_change", args=[fetched_game.fg_game.id])
        return cast(str, format_html("<a href='{url}' target='_blank'>{name}</a>", url=url, name=fetched_game.fg_game))
    else:
        return "-"
hyperlink_fg_game.short_description = "FG Game"  # type:ignore # NOQA: E305


def hyperlink_fg_platform(fetched_platform: FetchedPlatform) -> str:
    if fetched_platform.fg_platform:
        url = reverse("admin:core_platform_change", args=[fetched_platform.fg_platform.id])
        return cast(str, format_html(
            "<a href='{url}' target='_blank'>{name}</a>", url=url, name=fetched_platform.fg_platform)
        )
    else:
        return "-"
hyperlink_fg_platform.short_description = "FG Platform"  # type:ignore # NOQA: E305
