from abc import ABC, abstractmethod
from typing import Any, List, Tuple

from catalogsources.models import FetchedGame, FetchedPlatform
from core.models import UNKNOWN_PUBLISH_DATE
from django.core.management.base import OutputWrapper
from django.core.management.color import Style


class BaseAdapter(ABC):

    FIELD_UNSUPPLIED = None

    UNKNOWN_TOTAL_RESULTS_VALUE = -1

    DEFAULT_PUBLISH_DATE = UNKNOWN_PUBLISH_DATE

    @abstractmethod
    def __init__(self, stdout: OutputWrapper, stdout_color_style: Style) -> None:
        self.total_results = 0
        self.next_offset = 0

    @abstractmethod
    def __enter__(self) -> "BaseAdapter":
        pass

    @abstractmethod
    def __exit__(self, *args: Any) -> None:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass

    @abstractmethod
    def set_offset(self, offset: int) -> None:
        pass

    @abstractmethod
    def batch_size(self) -> int:
        pass

    @staticmethod
    @abstractmethod
    def source_id() -> str:
        pass

    @abstractmethod
    def fetch_platforms_block(self) -> List[FetchedPlatform]:
        pass

    @abstractmethod
    def fetch_games_block(self, platform_id: int) -> List[Tuple[FetchedGame, List[FetchedPlatform]]]:
        pass

    @abstractmethod
    def has_more_items(self) -> bool:
        pass

    @abstractmethod
    def has_errored(self) -> bool:
        pass
