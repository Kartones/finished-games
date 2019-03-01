from abc import (ABC, abstractmethod)
from typing import (Any, List, Tuple)

from catalogsources.models import (FetchedGame, FetchedPlatform)


class BaseAdapter(ABC):

    FIELD_UNSUPPLIED = None

    UNKOWN_TOTAL_RESULTS_VALUE = -1

    DEFAULT_PUBLISH_DATE = 1970

    @abstractmethod
    def __enter__(self) -> "BaseAdapter":
        pass

    @abstractmethod
    def __exit__(self, *args: Any) -> None:
        pass

    @abstractmethod
    def reset(self) -> None:
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

    @abstractmethod
    def error_info(self) -> str:
        pass
