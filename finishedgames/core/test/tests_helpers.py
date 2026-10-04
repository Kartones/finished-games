import os
import shutil
import tempfile
import uuid
from datetime import datetime
from typing import List, Optional, Union, cast

from core.forms import GameForm, PlatformForm
from core.models import Game, Platform, UserGame
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase

# When set, working directories are created inside it and never deleted
TEST_TMP_ROOT_ENV_VAR = "FG_TEST_TMP_ROOT"


def create_platform(name: Optional[str] = None, shortname: Optional[str] = None) -> Platform:
    platform_form = PlatformForm(
        {
            "name": name if name else str(uuid.uuid4()),
            "shortname": shortname if name else str(uuid.uuid4()),
            "publish_date": datetime.now().year,
        }
    )
    return cast(Platform, platform_form.save())


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
    return cast(Game, game_form.save())


def create_user(username: Optional[str] = None, username_slug: Optional[str] = None) -> settings.AUTH_USER_MODEL:
    user = get_user_model().objects.create_user(  # nosec
        username=username if username else str(uuid.uuid4()),
        email="an_irrelevant_email@test.test",
        password="a password",
    )
    return user


def create_user_game(
    user: settings.AUTH_USER_MODEL,
    platform: Optional[Platform] = None,
    name: Optional[str] = None,
    year_finished: Optional[int] = None,
    year_abandoned: Optional[int] = None,
    currently_playing: bool = False,
    minutes_played: int = 0,
) -> UserGame:
    platform = platform if platform else create_platform(name=str(uuid.uuid4()), shortname=str(uuid.uuid4()))
    game = create_game(name=name, platforms=[platform])

    return cast(
        UserGame,
        UserGame.objects.create(
            user=user,
            game=game,
            platform=platform,
            year_finished=year_finished,
            year_abandoned=year_abandoned,
            currently_playing=currently_playing,
            minutes_played=minutes_played,
        ),
    )


def create_working_directory(test_case: SimpleTestCase) -> str:
    """Creates a directory and makes it the cwd until the test ends (for commands that write to cwd)."""
    root = os.environ.get(TEST_TMP_ROOT_ENV_VAR)
    directory = tempfile.mkdtemp(dir=root)

    original_directory = os.getcwd()
    os.chdir(directory)
    test_case.addCleanup(os.chdir, original_directory)
    if not root:
        test_case.addCleanup(shutil.rmtree, directory, True)

    return directory
