from typing import (Dict, Optional)

from django import template
from django.conf import settings

from core.helpers import generic_id as generic_id_helper

register = template.Library()


@register.filter
def generic_id(game_id: int, platform_id: int) -> str:
    return generic_id_helper(game_id, platform_id)


@register.inclusion_tag("actions.html")
def render_actions(
    user: settings.AUTH_USER_MODEL,
    viewed_user: Optional[settings.AUTH_USER_MODEL],
    game_id: int,
    platform_id: int,
    next_url: str,
    authenticated_user_catalog: Dict,
    constants: Dict
) -> Dict:
    return {
        "user": user,
        "viewed_user": viewed_user,
        "game_id": game_id,
        "platform_id": platform_id,
        "item_generic_id": generic_id(game_id, platform_id),
        "next_url": next_url,
        "authenticated_user_catalog": authenticated_user_catalog,
        "constants": constants,
    }
