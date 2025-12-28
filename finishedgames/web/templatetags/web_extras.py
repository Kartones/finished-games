from functools import lru_cache
from typing import Any, Dict, List, Optional, cast

from core.helpers import generic_id as generic_id_helper
from core.models import Game, Platform, UserGame, WishlistedUserGame
from django import template
from django.conf import settings
from django.db.models.functions import Length, Lower
from django.http import HttpRequest
from django.utils.safestring import mark_safe
from web import constants

register = template.Library()


@register.filter
def get_item(dictionary: Dict, key: Any) -> Any:
    """Access dictionary item by key in templates."""
    return dictionary.get(key)


@register.filter
def generic_id(game_id: int, platform_id: int) -> str:
    return generic_id_helper(game_id, platform_id)


@register.inclusion_tag("templatetags/actions.html")
def render_actions(
    user: settings.AUTH_USER_MODEL, game_id: int, platform_id: int, authenticated_user_catalog: Dict
) -> Dict:
    return {
        "user": user,
        "game_id": game_id,
        "platform_id": platform_id,
        "item_generic_id": generic_id(game_id, platform_id),
        "authenticated_user_catalog": authenticated_user_catalog,
        "constants": constants,
    }


@register.inclusion_tag("templatetags/game_time.html")
def render_game_time(user: settings.AUTH_USER_MODEL, user_game_id: int, game_time: int) -> Dict:
    return {
        "user": user,
        "user_game_id": user_game_id,
        "game_time": game_time,
        "constants": constants,
    }

@register.inclusion_tag("templatetags/field_filters_headers.html")
def field_filters_headers(request: HttpRequest, sort_by: str, exclude: str, enabled_fields: List[str]) -> Dict:
    # NOTE: Name column is implicitly enabled
    return {
        "request": request,
        "sort_by": sort_by,
        "exclude": exclude,
        "enabled_fields": enabled_fields,
        "constants": constants,
    }


@register.inclusion_tag("templatetags/status_filters_headers.html")
def status_filters_headers(request: HttpRequest, sort_by: str, exclude: str, enabled_statuses: List[str]) -> Dict:
    return {
        "request": request,
        "sort_by": sort_by,
        "exclude": exclude,
        "enabled_statuses": enabled_statuses,
        "constants": constants,
    }


@register.inclusion_tag("templatetags/status_filters_row.html")
def status_filters_row(user_game: UserGame, enabled_statuses: List[str]) -> Dict:
    return {
        "user_game": user_game,
        "enabled_statuses": enabled_statuses,
        "constants": constants,
    }


@register.simple_tag
def send_action_data(action_id: str, item_generic_id: str) -> str:
    return cast(str, mark_safe(_build_action_data(action_id).format(item_generic_id=item_generic_id)))  # nosec


# Source: https://stackoverflow.com/a/24658162
@register.simple_tag
def query_update(request: HttpRequest, **kwargs: Any) -> str:
    updated = request.GET.copy()
    for key, value in kwargs.items():
        # we can live with this small hack, as else cannot do empty assignments like 'sort_by=' when using the tag
        if value == "None":
            updated[key] = None
        else:
            updated[key] = value
    return cast(str, updated.urlencode())


@lru_cache(maxsize=12)
def _build_action_data(action_id: str) -> str:
    display_div_ids = constants.ACTIONS_BUTTONS_MAPPING[action_id]["show"]
    hide_div_ids = constants.ACTIONS_BUTTONS_MAPPING[action_id]["hide"]
    # Small hack to overcome lack of partial string format substitution, using a partial function makes it more messy
    item_template = "'{div_id}{{item_generic_id}}'"

    return "sendAction(this, [{display_div_ids}], [{hide_div_ids}]); return false;".format(
        display_div_ids=",".join([item_template.format(div_id=div_id) for div_id in display_div_ids]),
        hide_div_ids=",".join([item_template.format(div_id=div_id) for div_id in hide_div_ids]),
    )


@register.inclusion_tag("templatetags/datalist_autocomplete.html")
def datalist_autocomplete(
    entity_type: str,
    action_url: str,
    input_id: str,
    username: Optional[str] = None,
    filter_type: Optional[str] = None,
    size: Optional[str] = None,
    placeholder: str = "",
) -> Dict:
    """
    Render an HTML5 datalist-based autocomplete component.

    Args:
        entity_type: Either 'game' or 'platform'
        action_url: The form action URL (where to submit)
        input_id: Unique ID for the input element
        username: Optional username for filtering
        filter_type: Optional filter type
        placeholder: Placeholder text for the input field
    """
    options = []

    if entity_type == "game":
        queryset = Game.objects.order_by(Lower("name"))
        options = [{"value": game.name, "id": game.id} for game in queryset]
    elif entity_type == "platform":
        queryset = Platform.objects.order_by(Lower("shortname"))

        if username and filter_type:
            if filter_type == constants.PLATFORM_FILTER_WISHLISTED:
                queryset = queryset.filter(
                    id__in=WishlistedUserGame.objects.filter(user__username=username)
                    .values_list("platform__id", flat=True)
                    .distinct()
                )
            elif filter_type == constants.PLATFORM_FILTER_FINISHED:
                queryset = queryset.filter(
                    id__in=UserGame.objects.filter(user__username=username, year_finished__isnull=False)
                    .values_list("platform__id", flat=True)
                    .distinct()
                )
            elif filter_type == constants.PLATFORM_FILTER_PENDING:
                queryset = queryset.filter(
                    id__in=UserGame.objects.filter(user__username=username)
                    .exclude(year_finished__isnull=False)
                    .exclude(abandoned=True)
                    .values_list("platform__id", flat=True)
                    .distinct()
                )
            elif filter_type == constants.PLATFORM_FILTER_ABANDONED:
                queryset = queryset.filter(
                    id__in=UserGame.objects.filter(user__username=username, abandoned=True)
                    .values_list("platform__id", flat=True)
                    .distinct()
                )
            elif filter_type == constants.PLATFORM_FILTER_CURRENTLY_PLAYING:
                queryset = queryset.filter(
                    id__in=UserGame.objects.filter(user__username=username, currently_playing=True)
                    .values_list("platform__id", flat=True)
                    .distinct()
                )

        queryset = queryset.only("id", "shortname")
        options = [{"value": platform.shortname, "id": platform.id} for platform in queryset]

    datalist_id = f"{input_id}_list"

    return {
        "input_id": input_id,
        "datalist_id": datalist_id,
        "action_url": action_url,
        "options": options,
        "placeholder": placeholder,
        "entity_type": entity_type,
        "size": size,
    }
