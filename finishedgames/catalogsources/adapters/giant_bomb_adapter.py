import json
from typing import (Any, cast, Dict, List, Optional, Tuple)  # NOQA: F401

from django.conf import settings
import requests

from catalogsources.adapters.base_adapter import BaseAdapter
from catalogsources.models import (FetchedGame, FetchedPlatform)
from finishedgames import constants


class GiantBombAdapter(BaseAdapter):
    """
    Adapter for fetching data from GiantBomb.com's API. See https://www.giantbomb.com/api/ for further details.
    """

    SOURCE_ID = "giantbomb"

    def __init__(self) -> None:
        super().__init__()

        self.api_key = settings.CATALOG_SOURCES_ADAPTERS[self.SOURCE_ID][constants.ADAPTER_API_KEY]

        self.offset = 0
        self.next_offset = 0
        self.total_results = GiantBombAdapter.UNKOWN_TOTAL_RESULTS_VALUE
        self.error = None  # type: Optional[str]
        self.last_request_data = {}  # type: Dict

    def __enter__(self) -> "GiantBombAdapter":
        self.fetching = True
        self.reset()

        return self

    def reset(self) -> None:
        self.offset = 0
        self.next_offset = 0
        self.total_results = GiantBombAdapter.UNKOWN_TOTAL_RESULTS_VALUE
        self.error = None  # type: Optional[str]
        self.last_request_data = {}  # type: Dict

    def __exit__(self, *args: Any) -> None:
        self.fetching = False

    @staticmethod
    def source_id() -> str:
        return GiantBombAdapter.SOURCE_ID

    def fetch_platforms_block(self) -> List[FetchedPlatform]:
        self.offset = self.next_offset

        # Limit is implicitly 100
        request = requests.get("https://www.giantbomb.com/api/platforms/?api_key={api_key}&format=json&offset={offset}&field_list=id,name,release_date,site_detail_url".format(   # NOQA: E501
            api_key=self.api_key, offset=self.offset),
            headers={
                "user-agent": settings.CATALOG_SOURCES_ADAPTER_USER_AGENT
            }
        )

        if request.status_code == 200:
            try:
                self.last_request_data = request.json()
            except json.decoder.JSONDecodeError:
                self.error = "Unable to decode content as JSON"
        else:
            self.error = request.text
        if self.error:
            self.error = "{error}.\nInfo: S:{status_code} O:{offset} NO:{next_offset} T:{total_results}".format(
                error=self.error, status_code=request.status_code, offset=self.offset, next_offset=self.next_offset,
                total_results=self.total_results
            )
            return []

        self.next_offset += self.last_request_data["number_of_page_results"]
        self.total_results = self.last_request_data["number_of_total_results"]
        fetched_platforms = self._results_to_platform_entities(self.last_request_data["results"])

        return fetched_platforms

    def fetch_games_block(self, platform_id: int) -> List[Tuple[FetchedGame, List[FetchedPlatform]]]:
        self.offset = self.next_offset

        # Limit is implicitly 100
        # `platforms` parameter is actually a single platform id filter
        url = "https://www.giantbomb.com/api/games/?api_key={api_key}&format=json&offset={offset}&platforms={platform}&field_list=id,name,aliases,platforms,original_release_date,releases,dlcs,site_detail_url".format(   # NOQA: E501
            api_key=self.api_key, offset=self.offset, platform=platform_id
        )
        request = requests.get(url, headers={
            "user-agent": settings.CATALOG_SOURCES_ADAPTER_USER_AGENT
        })

        # TODO: generalize this? too similar to previous one
        if request.status_code == 200:
            try:
                self.last_request_data = request.json()
            except json.decoder.JSONDecodeError:
                self.error = "Unable to decode content as JSON"
        else:
            self.error = request.text
        if self.error:
            self.error = "{error}.\nInfo: S:{status_code} O:{offset} NO:{next_offset} T:{total_results}".format(
                error=self.error, status_code=request.status_code, offset=self.offset, next_offset=self.next_offset,
                total_results=self.total_results
            )
            return []

        self.next_offset += self.last_request_data["number_of_page_results"]
        self.total_results = self.last_request_data["number_of_total_results"]

        fetched_games_and_platforms = self._results_to_game_entities(self.last_request_data["results"])

        return fetched_games_and_platforms

    def has_more_items(self) -> bool:
        # Context manager not setup
        if not self.fetching:
            return False
        # In case of any error, stop
        if self.error:
            return False
        # First fetch call
        if self.total_results == GiantBombAdapter.UNKOWN_TOTAL_RESULTS_VALUE:
            return True
        # >1 calls with more results
        elif self.next_offset < self.total_results:
            return True

        return False

    def has_errored(self) -> bool:
        return self.error is not None

    def error_info(self) -> str:
        return self.error if self.error else ""

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
                data["publish_date"] = 1970
            entities.append(FetchedPlatform(**data))

        return entities

    @staticmethod
    def _results_to_game_entities(results: Dict) -> List[Tuple[FetchedGame, List[FetchedPlatform]]]:
        entities = []  # type: List[Tuple[FetchedGame, List[FetchedPlatform]]]

        for result in results:
            data = {
                "name": result["name"],
                "source_game_id": result["id"],
                "source_id": GiantBombAdapter.source_id(),
                "source_url": result["site_detail_url"],
            }
            if result["original_release_date"]:
                # Cheating here, instead of parsing as datetime and extracting year. sample: `1985-07-23 00:00:00`
                data["publish_date"] = int(result["original_release_date"].split("-")[0])
            else:
                # Some items don't have publish/release date
                data["publish_date"] = 1970

            game = FetchedGame(**data)

            platforms = []  # type: List[FetchedPlatform]
            for platform_result in result["platforms"]:
                try:
                    # TODO: Cache loaded platforms to not load each one more than once
                    fetched_platform = FetchedPlatform.objects.get(source_platform_id=platform_result["id"])
                    platforms.append(fetched_platform)
                except FetchedPlatform.DoesNotExist:
                    pass

            entities.append((game, platforms,))

        return entities
