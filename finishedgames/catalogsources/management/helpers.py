import time
from typing import Type

from catalogsources.adapters.base_adapter import BaseAdapter
from catalogsources.adapters.giant_bomb_adapter import GiantBombAdapter


def wait_if_needed(time_start, time_end) -> None:
    time_elapsed = time_end - time_start
    # Most apis allow 1 request per second, so default to 1 fetch request per second
    if time_elapsed < 1.0:
        time.sleep(1.0 - time_elapsed)


def source_class_from_id(source_id: str) -> Type[BaseAdapter]:
    if source_id == GiantBombAdapter.source_id():
        return GiantBombAdapter

    raise ValueError("Unknown source id '{}'".format(source_id))
