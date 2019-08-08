import json
import time
from typing import (Any, Callable, cast, Dict, List, Optional, Tuple)  # NOQA: F401

from django.conf import settings
from django.core.management.base import OutputWrapper
from django.core.management.color import Style
import requests

from catalogsources.adapters.base_adapter import BaseAdapter
from catalogsources.adapters.helpers import (check_rate_limit, games_json_fetch_to_file, platforms_json_fetch_to_file)
from catalogsources.models import (FetchedGame, FetchedPlatform)
from finishedgames import constants


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
                last_check_timestamp=instance.last_check_timestamp
            )
            if not can_pass:
                instance.stdout.write(instance.stdout_style.WARNING(
                    "> Rate limit hit, waiting {} seconds".format(instance.wait_seconds_when_rate_limited))
                )
                time.sleep(instance.wait_seconds_when_rate_limited)

        return decorated_function(*args, **kwargs)
    return wrapper


class GiantBombAdapter(BaseAdapter):
    """
    Adapter for fetching data from GiantBomb.com's API. See https://www.giantbomb.com/api/ for further details.
    """

    SOURCE_ID = "giantbomb"

    def __init__(self, stdout: OutputWrapper, stdout_color_style: Style) -> None:
        super().__init__(stdout=stdout, stdout_color_style=stdout_color_style)

        self.stdout = stdout
        self.stdout_style = stdout_color_style

        # This block is all related with rate limits
        self.api_key = settings.CATALOG_SOURCES_ADAPTERS[self.SOURCE_ID][constants.ADAPTER_API_KEY]
        self.max_requests_per_time_window = \
            settings.CATALOG_SOURCES_ADAPTERS[self.SOURCE_ID][constants.ADAPTER_REQUESTS_PER_HOUR]
        self.wait_seconds_when_rate_limited = \
            settings.CATALOG_SOURCES_ADAPTERS[self.SOURCE_ID][constants.ADAPTER_WAIT_SECONDS_WHEN_RATE_LIMITED]
        self.time_window = 3600  # X requests allowed in Y seconds
        self.token_bucket = self.max_requests_per_time_window  # start with bucket full of tokens
        self.last_check_timestamp = 0.0
        self._batch_size = cast(int, settings.CATALOG_SOURCES_ADAPTERS[self.SOURCE_ID][constants.ADAPTER_BATCH_SIZE])

        self.offset = 0
        self.next_offset = 0
        self.total_results = GiantBombAdapter.UNKOWN_TOTAL_RESULTS_VALUE
        self.errored = False
        self.last_request_data = {}  # type: Dict
        self.platforms_cache = {}  # type: Dict[int, Optional[FetchedPlatform]]

    def __enter__(self) -> "GiantBombAdapter":
        self.fetching = True

        return self

    def reset(self) -> None:
        self.offset = 0
        self.next_offset = 0
        self.total_results = GiantBombAdapter.UNKOWN_TOTAL_RESULTS_VALUE
        self.error = False
        self.last_request_data = {}

    def __exit__(self, *args: Any) -> None:
        self.fetching = False
        self.platforms_cache = {}

    @staticmethod
    def source_id() -> str:
        return GiantBombAdapter.SOURCE_ID

    def set_offset(self, offset: int) -> None:
        self.next_offset = max(0, offset)

    def batch_size(self) -> int:
        return self._batch_size

    @rate_limit
    def fetch_platforms_block(self) -> List[FetchedPlatform]:
        self.offset = self.next_offset

        request = requests.get("https://www.giantbomb.com/api/platforms/?api_key={api_key}&format=json&limit={limit}&offset={offset}&field_list=id,name,release_date,site_detail_url".format(   # NOQA: E501
                api_key=self.api_key, offset=self.offset, limit=self._batch_size
            ),
            headers={
                "user-agent": settings.CATALOG_SOURCES_ADAPTER_USER_AGENT
            }
        )

        if request.status_code == 200:
            try:
                self.last_request_data = request.json()
            except json.decoder.JSONDecodeError:
                self.stdout.write(self.stdout_style.ERROR("Unable to decode content as JSON"))
                self.errored = True
        else:
            self.errored = True
            self.stdout.write(self.stdout_style.ERROR(
                "{code}: {error}.\nInfo: S:{status_code} O:{offset} NO:{next_offset} T:{total_results} L:{limit}".format(  # NOQA: E501
                    code=request.status_code, error=request.text, status_code=request.status_code, offset=self.offset,
                    next_offset=self.next_offset, total_results=self.total_results, limit=self._batch_size)
            ))

        if self.errored:
            return []

        if settings.DEBUG:
            platforms_json_fetch_to_file(
                json_data=self.last_request_data, source_id=self.source_id(), offset=self.offset
            )

        self.next_offset += self.last_request_data["number_of_page_results"]
        self.total_results = self.last_request_data["number_of_total_results"]
        fetched_platforms = self._results_to_platform_entities(self.last_request_data["results"])

        return fetched_platforms

    @rate_limit
    def fetch_games_block(self, platform_id: int) -> List[Tuple[FetchedGame, List[FetchedPlatform]]]:
        self.offset = self.next_offset

        # Limit is implicitly 100
        # `platforms` parameter is actually a single platform id filter
        url = "https://www.giantbomb.com/api/games/?api_key={api_key}&format=json&limit={limit}&offset={offset}&platforms={platform}&field_list=id,name,aliases,platforms,original_release_date,releases,dlcs,site_detail_url".format(   # NOQA: E501
            api_key=self.api_key, offset=self.offset, platform=platform_id, limit=self._batch_size
        )
        request = requests.get(url, headers={
            "user-agent": settings.CATALOG_SOURCES_ADAPTER_USER_AGENT
        })

        if request.status_code == 200:
            try:
                self.last_request_data = request.json()
            except json.decoder.JSONDecodeError:
                self.stdout.write(self.stdout_style.ERROR("Unable to decode content as JSON"))
                self.errored = True
        else:
            self.errored = True
            self.stdout.write(self.stdout_style.ERROR(
                "{code}: {error}.\nInfo: S:{status_code} O:{offset} NO:{next_offset} T:{total_results} L:{limit}".format(  # NOQA: E501
                    code=request.status_code, error=request.text, status_code=request.status_code, offset=self.offset,
                    next_offset=self.next_offset, total_results=self.total_results, limit=self._batch_size)
            ))

        if self.errored:
            return []

        if settings.DEBUG:
            games_json_fetch_to_file(
                json_data=self.last_request_data, source_id=self.source_id(), platform_id=platform_id,
                offset=self.offset
            )

        self.next_offset += self.last_request_data["number_of_page_results"]
        self.total_results = self.last_request_data["number_of_total_results"]

        fetched_games_and_platforms = self._results_to_game_entities(self.last_request_data["results"])

        return fetched_games_and_platforms

    def has_more_items(self) -> bool:
        # Context manager not setup
        if not self.fetching:
            return False
        # In case of any error, stop
        if self.errored:
            return False
        # First fetch call
        if self.total_results == GiantBombAdapter.UNKOWN_TOTAL_RESULTS_VALUE:
            return True
        # >1 calls with more results
        elif self.next_offset < self.total_results:
            return True

        return False

    def has_errored(self) -> bool:
        return self.errored

    @staticmethod
    def _results_to_platform_entities(results: Dict) -> List[FetchedPlatform]:
        entities = []  # type: List[FetchedPlatform]

        for result in results:
            data = {
                "name": result["name"],
                "shortname": GiantBombAdapter.FIELD_UNSUPPLIED,  # Shortnames not fetched
                "source_platform_id": result["id"],
                "source_id": GiantBombAdapter.source_id(),
                "source_url": result["site_detail_url"],
            }
            if result["release_date"]:
                # Cheating here, instead of parsing as datetime and extracting year. sample: `1985-07-23 00:00:00`
                data["publish_date"] = int(result["release_date"].split("-")[0])
            else:
                # Some items don't have publish/release date
                data["publish_date"] = GiantBombAdapter.DEFAULT_PUBLISH_DATE
            entities.append(FetchedPlatform(**data))

        return entities

    def _results_to_game_entities(self, results: Dict) -> List[Tuple[FetchedGame, List[FetchedPlatform]]]:
        entities = []  # type: List[Tuple[FetchedGame, List[FetchedPlatform]]]

        for result in results:
            data = {
                "name": result["name"],
                "source_game_id": result["id"],
                "source_id": GiantBombAdapter.source_id(),
                "source_url": result["site_detail_url"],
                # TODO: Handle DLCs and parent games
            }
            if result["original_release_date"]:
                # Cheating here, instead of parsing as datetime and extracting year. sample: `1985-07-23 00:00:00`
                data["publish_date"] = int(result["original_release_date"].split("-")[0])
            else:
                # Some items don't have publish/release date
                data["publish_date"] = GiantBombAdapter.DEFAULT_PUBLISH_DATE

            game = FetchedGame(**data)

            platforms = []  # type: List[FetchedPlatform]
            for platform_result in result["platforms"]:
                # NOTE: Only platforms not hidden will be linked
                fetched_platform = self._get_platform_cached(source_platform_id=platform_result["id"])
                if fetched_platform:
                    platforms.append(fetched_platform)

            entities.append((game, platforms,))

        return entities

    def _get_platform_cached(self, source_platform_id: int) -> Optional[FetchedPlatform]:
        if source_platform_id not in self.platforms_cache:
            try:
                fetched_platform = FetchedPlatform.objects.get(
                    source_platform_id=source_platform_id, hidden=False, source_id=GiantBombAdapter.source_id()
                )
            except FetchedPlatform.DoesNotExist:
                fetched_platform = None
            self.platforms_cache[source_platform_id] = fetched_platform

        return self.platforms_cache[source_platform_id]
