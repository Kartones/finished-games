import time
from typing import Type

from catalogsources.adapters.base_adapter import BaseAdapter
from catalogsources.adapters.giant_bomb_adapter import GiantBombAdapter


def wait_if_needed(time_elapsed: float) -> None:
    # Most apis allow 1 request per second, so default to 1 fetch request per second
    if time_elapsed < 1.0:
        time.sleep(1.0 - time_elapsed)


def source_class_from_id(source_id: str) -> Type[BaseAdapter]:
    if source_id == GiantBombAdapter.source_id():
        return GiantBombAdapter

    raise ValueError("Unknown source id '{}'".format(source_id))


class TimeProfiler:
    def __init__(self, use_performance_counter=False):
        self.use_performance_counter = use_performance_counter
        self.duration = 0.0

    def __enter__(self):
        self.start = time.perf_counter() if self.use_performance_counter else time.time()
        return self

    def __exit__(self, *args):
        self.end = time.perf_counter() if self.use_performance_counter else time.time()
        self.duration = self.end - self.start
