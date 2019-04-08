from typing import Dict

from django import template
from django.conf import settings

from core.helpers import generic_id as generic_id_helper
from web import constants

register = template.Library()


@register.filter
def generic_id(game_id: int, platform_id: int) -> str:
    return generic_id_helper(game_id, platform_id)


@register.inclusion_tag("actions.html")
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
