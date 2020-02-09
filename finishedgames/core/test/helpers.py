import uuid
from datetime import datetime
from typing import List, Optional, Union

from core.forms import GameForm, PlatformForm
from core.models import Game, Platform
from django.conf import settings
from django.contrib.auth import get_user_model


def create_platform(name: Optional[str] = None, shortname: Optional[str] = None) -> Platform:
    platform_form = PlatformForm(
        {
            "name": name if name else str(uuid.uuid4()),
            "shortname": shortname if name else str(uuid.uuid4()),
            "publish_date": datetime.now().year,
        }
    )
    return platform_form.save()


def create_game(
    name: Optional[str] = None,
    platforms: List = [],
    dlc_or_expansion: bool = False,
    parent_game: Union[int, Game, None] = None,
) -> Game:
    game_form = GameForm(
        {
            "name": name if name else str(uuid.uuid4()),
            "platforms": platforms,
            "publish_date": datetime.now().year,
            "dlc_or_expansion": dlc_or_expansion,
            "parent_game": parent_game,
        }
    )
    return game_form.save()


def create_user(username: Optional[str] = None, username_slug: Optional[str] = None) -> settings.AUTH_USER_MODEL:
    user = get_user_model().objects.create_user(  # nosec
        username=username if username else str(uuid.uuid4()),
        email="an_irrelevant_email@test.test",
        password="a password",
    )
    return user
