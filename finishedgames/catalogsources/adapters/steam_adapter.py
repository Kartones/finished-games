from datetime import datetime
import json
import os
from pathlib import Path
import time
from typing import Any, Callable, List, Optional, Tuple

import requests
from catalogsources.adapters.base_adapter import BaseAdapter
from catalogsources.adapters.helpers import check_rate_limit
from catalogsources.models import FetchedGame, FetchedPlatform
from django.conf import settings
from django.core.management.base import OutputWrapper
from django.core.management.color import Style

from finishedgames import constants


# Steam doesn't have pagination
BATCH_SIZE = 50000

# If we change the game details to fetch more/different data
CACHE_FOLDER_NAME = "cache_steam_game_details_v1"

PC_PLATFORM_ID = 1
PC_PLATFORM_NAME = "PC"
PC_PLATFORM_SHORTNAME = "PC"
PC_PLATFORM_URL = "https://store.steampowered.com/"
PC_PLATFORM_PUBLISH_DATE = 2003

NEWLINE_AFTER_N_GAMES = 20


# Decorator
def rate_limit(decorated_function: Callable) -> Callable:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        instance = args[0]
        can_pass = False

        while not can_pass:
            instance.token_bucket, instance.last_check_timestamp, can_pass = check_rate_limit(
                max_tokens=instance.max_requests_per_time_window,
                time_window=instance.time_window,
                token_bucket=instance.token_bucket,
                last_check_timestamp=instance.last_check_timestamp,
            )
            if not can_pass:
                instance.stdout.write(
                    instance.stdout_style.WARNING(
                        "> Rate limit hit, waiting {} seconds (tokens remaining: {:.2f})".format(
                            instance.wait_seconds_when_rate_limited, instance.token_bucket
                        )
                    )
                )
                time.sleep(instance.wait_seconds_when_rate_limited)

        return decorated_function(*args, **kwargs)

    return wrapper


class SteamAdapter(BaseAdapter):

    SOURCE_ID = "steam"

    def __init__(self, stdout: OutputWrapper, stdout_color_style: Style) -> None:
        super().__init__(stdout=stdout, stdout_color_style=stdout_color_style)

        self.stdout = stdout
        self.stdout_style = stdout_color_style

        self.api_key = settings.CATALOG_SOURCES_ADAPTERS[self.SOURCE_ID][constants.ADAPTER_API_KEY]
        self.user_id = settings.CATALOG_SOURCES_ADAPTERS[self.SOURCE_ID][constants.ADAPTER_USER_ID]

       # Steam in theory allows 100k requests per day, which would be ~4166 per hour,
       # but internet mentions around 200 in 5-minute buckets, and I've hit it myself with less than 500 requests, so this adapter works in 5-minute windows.
       # Seems that the rate limit also resets around every 5 minutes.

        self.max_requests_per_time_window = settings.CATALOG_SOURCES_ADAPTERS[self.SOURCE_ID][
            constants.ADAPTER_REQUESTS_PER_HOUR
        ]  / 12  # per 5 minutes
        self.wait_seconds_when_rate_limited = settings.CATALOG_SOURCES_ADAPTERS[self.SOURCE_ID][
            constants.ADAPTER_WAIT_SECONDS_WHEN_RATE_LIMITED
        ] / 12  # per 5 minutes
        self.time_window = 300  # X requests allowed in 5 minutes
        self.token_bucket = float(self.max_requests_per_time_window)  # Start with bucket full
        self.last_check_timestamp = 0.0

        self.offset = 0
        self.next_offset = 0
        self.total_results = SteamAdapter.UNKOWN_TOTAL_RESULTS_VALUE
        self.errored = False
        self.fetching = False
        self.pc_platform_cache = None  # type: Optional[FetchedPlatform]

        # just a counter to show progress after each N games
        self.counter = 0

    def __enter__(self) -> "SteamAdapter":
        self.fetching = True
        return self

    def __exit__(self, *args: Any) -> None:
        self.fetching = False
        self.pc_platform_cache = None

    def reset(self) -> None:
        self.offset = 0
        self.next_offset = 0
        self.total_results = SteamAdapter.UNKOWN_TOTAL_RESULTS_VALUE
        self.errored = False

    @staticmethod
    def source_id() -> str:
        return SteamAdapter.SOURCE_ID

    def set_offset(self, offset: int) -> None:
        self.next_offset = max(0, offset)

    def batch_size(self) -> int:
        return BATCH_SIZE

    def fetch_platforms_block(self) -> List[FetchedPlatform]:
        """
        Steam games are PC only, so we return a single platform.
        """
        platform = FetchedPlatform(
            name=PC_PLATFORM_NAME,
            shortname=PC_PLATFORM_SHORTNAME,
            source_platform_id=PC_PLATFORM_ID,
            source_id=self.source_id(),
            source_url=PC_PLATFORM_URL,
            publish_date=PC_PLATFORM_PUBLISH_DATE,
        )
        self.total_results = 1
        self.next_offset = 1
        return [platform]

    def fetch_games_block(self, platform_id: int) -> List[Tuple[FetchedGame, List[FetchedPlatform]]]:
        """
        Note: platform_id is ignored, as Steam is PC only.
        """
        self.offset = self.next_offset

        url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={api_key}&steamid={steam_id}&format=json&include_appinfo=true".format(
            api_key=self.api_key, steam_id=self.user_id
        )

        request = requests.get(url, headers={"user-agent": settings.CATALOG_SOURCES_ADAPTER_USER_AGENT})

        if request.status_code == 200:
            try:
                response_data = request.json()
            except json.decoder.JSONDecodeError:
                self.stdout.write(self.stdout_style.ERROR("Unable to decode content as JSON"))
                self.errored = True
                return []
        else:
            self.errored = True
            self.stdout.write(
                self.stdout_style.ERROR(
                    "{code}: {error}.\nInfo: S:{status_code} T:{total_results}".format(
                        code=request.status_code,
                        error=request.text,
                        status_code=request.status_code,
                        total_results=self.total_results,
                    )
                )
            )
            return []

        if "response" not in response_data or "games" not in response_data["response"]:
            self.stdout.write(self.stdout_style.ERROR("Unexpected response structure:\n{}".format(response_data)))
            self.errored = True
            return []

        games = response_data["response"]["games"]
        game_count = response_data["response"]["game_count"]

        if len(games) != game_count:
            self.stdout.write(
                self.stdout_style.WARNING(
                    "Game count mismatch: expected {}, got {}".format(game_count, len(games))
                )
            )

        # Steam returns all games in one call (not paginated)
        self.total_results = game_count
        self.next_offset = game_count

        fetched_games_and_platforms = self._results_to_game_entities(games)

        return fetched_games_and_platforms

    def has_more_items(self) -> bool:
        if not self.fetching:
            return False
        if self.errored:
            return False
        if self.total_results == SteamAdapter.UNKOWN_TOTAL_RESULTS_VALUE:
            return True
        elif self.next_offset < self.total_results:
            return True
        return False

    def has_errored(self) -> bool:
        return self.errored

    def _results_to_game_entities(self, games: List) -> List[Tuple[FetchedGame, List[FetchedPlatform]]]:
        entities = []  # type: List[Tuple[FetchedGame, List[FetchedPlatform]]]

        pc_platform = self._get_pc_platform_cached()
        if pc_platform is None:
            self.stdout.write(self.stdout_style.ERROR("PC platform not found in database, can't import"))
            self.errored = True
            return []
        platforms = [pc_platform]

        self.stdout.write("Fetching game details for {} games:".format(len(games)))

        for game in games:
            data = {
                "name": game["name"],
                "source_game_id": str(game["appid"]),
                "source_id": SteamAdapter.source_id(),
                "source_url": "{}/app/{}".format(PC_PLATFORM_URL, game["appid"]),
                "publish_date": SteamAdapter.DEFAULT_PUBLISH_DATE,
            }

            game_details = self._get_game_details(game["appid"])
            """
            Sample:
            {"data":{"release_date":{"coming_soon":false,"date":"27 Oct, 2017"}}}
            """
            if "release_date" in game_details and "date" in game_details["release_date"]:
                release_date_str = game_details["release_date"]["date"]
                try:
                    # Observeed format: "27 Oct, 2017"
                    if "," in release_date_str:
                        parsed_date = datetime.strptime(release_date_str, "%d %b, %Y")
                        data["publish_date"] = parsed_date.year
                    else:
                        # some games have the field present but empty
                        if release_date_str:
                            # just pick the year from the end of the string
                            data["publish_date"] = int(release_date_str.strip()[-4:])
                except ValueError:
                    self.stdout.write(
                        self.stdout_style.WARNING(
                            "\nUnrecognized date format '{}' for app ID {}".format(release_date_str, game["appid"])
                        )
                    )

            fetched_game = FetchedGame(**data)

            entities.append((fetched_game, platforms))

        self.stdout.write("\n")

        return entities

    def _get_pc_platform_cached(self) -> Optional[FetchedPlatform]:
        if self.pc_platform_cache is None:
            try:
                self.pc_platform_cache = FetchedPlatform.objects.get(
                    source_platform_id=PC_PLATFORM_ID, hidden=False, source_id=SteamAdapter.source_id()
                )
            except FetchedPlatform.DoesNotExist:
                self.stdout.write(
                    self.stdout_style.WARNING("PC platform not found in database, ensure platforms are fetched first")
                )
                self.pc_platform_cache = None

        return self.pc_platform_cache

    def _cache_read(self, app_id: int) -> Optional[dict]:
        cache_dir = Path(CACHE_FOLDER_NAME)
        cache_file = cache_dir / f"{app_id}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as file_handle:
                return json.load(file_handle)
        except (json.decoder.JSONDecodeError, IOError) as e:
            self.stdout.write(
                self.stdout_style.WARNING(f"Failed to read cache for app ID {app_id}: {e}")
            )
            return None

    def _cache_write(self, app_id: int, data: dict) -> None:
        cache_dir = Path(CACHE_FOLDER_NAME)
        cache_file = cache_dir / f"{app_id}.json"

        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            with open(cache_file, "w", encoding="utf-8") as file_handle:
                json.dump(data, file_handle, indent=2)
        except IOError as e:
            self.stdout.write(
                self.stdout_style.WARNING(f"Failed to write cache for app ID {app_id}: {e}")
            )

    def _get_game_details(self, app_id: int) -> dict:
        self.counter += 1

        cached_data = self._cache_read(app_id)
        if cached_data is not None:
            self.stdout.write("c", ending="")
            if self.counter % NEWLINE_AFTER_N_GAMES == 0:
                self.stdout.write("\n", ending="")
            return cached_data

        return self._fetch_game_details(app_id)

    @rate_limit
    def _fetch_game_details(self, app_id: int) -> dict:
        """
        More info at https://wiki.teamfortress.com/wiki/User:RJackson/StorefrontAPI#appdetails
        """

        filters = "release_date"
        """
        Sample response:
        {"582160":{"success":true,"data":{"release_date":{"coming_soon":false,"date":"27 Oct, 2017"}}}}
        """

        url = "https://store.steampowered.com/api/appdetails?l=en&appids={app_id}&filters={filters}".format(app_id=app_id, filters=filters)

        request = requests.get(url, headers={"user-agent": settings.CATALOG_SOURCES_ADAPTER_USER_AGENT})

        result = {}
        write_to_cache = False
        if request.status_code == 200:
            try:
                response_data = request.json()
                if str(app_id) in response_data and response_data[str(app_id)]["success"]:
                    result = response_data[str(app_id)]["data"]
                else:
                    self.stdout.write(
                        self.stdout_style.WARNING(
                            "\nFailed to get valid data for app ID {} (maybe not present?): {}".format(
                                app_id, response_data
                            )
                        )
                    )
                    # Assume there is no data, e.g. '590' is 'Left 4 Dead 2 Demo'
                    result = {}
                write_to_cache = True
            except json.decoder.JSONDecodeError:
                self.stdout.write(self.stdout_style.ERROR("Unable to decode content as JSON"))
        elif request.status_code == 429:
            self.stdout.write(
                self.stdout_style.ERROR(
                    "\nRate limit exceeded while fetching details for app ID {} (bucket tokens {}/{}): {}".format(
                        app_id, self.token_bucket, self.max_requests_per_time_window, request.text
                    )
                )
            )
            time.sleep(self.wait_seconds_when_rate_limited)
            return self._fetch_game_details(app_id)

        else:
            self.stdout.write(
                self.stdout_style.ERROR(
                    "HTTP {code} error while fetching details for app ID {app_id}: {error}".format(
                        code=request.status_code, app_id=app_id, error=request.text
                    )
                )
            )

        if write_to_cache:
            self._cache_write(app_id, result)

        self.stdout.write(".", ending="")
        if self.counter % NEWLINE_AFTER_N_GAMES == 0:
                self.stdout.write("\n", ending="")

        return result