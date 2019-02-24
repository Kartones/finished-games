from abc import (ABC, abstractmethod)
from typing import (Any, List)

from catalogsources.models import FetchedPlatform


class BaseAdapter(ABC):

    FIELD_UNSUPPLIED = None

    @abstractmethod
    def __enter__(self) -> "BaseAdapter":
        pass

    @abstractmethod
    def __exit__(self, *args: Any) -> None:
        pass

    @staticmethod
    @abstractmethod
    def source_id() -> str:
        pass

    @abstractmethod
    def fetch_platforms_block(self) -> List[FetchedPlatform]:
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
