import time
from typing import (Any, Dict, List, Type)

from django.core.management.base import (BaseCommand, CommandParser)

from catalogsources.adapters.base_adapter import BaseAdapter
from catalogsources.adapters.giant_bomb_adapter import GiantBombAdapter
from catalogsources.models import FetchedPlatform


class Command(BaseCommand):
    help = "Fetches platforms from specified source ids"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('sources', nargs='+', type=str)

    def handle(self, *args: Any, **options: Dict) -> None:
        for source_id in options['sources']:
            self._fetch_source(source_id=source_id)

    def _fetch_source(self, source_id: str) -> None:
        had_errors = False
        self.stdout.write("> Started fetching platforms from '{}'".format(source_id))

        adapter_class = self._source_class_from_id(source_id)

        with adapter_class() as adapter:
            while adapter.has_more_items():
                self.stdout.write("\n>fetch call...")

                time_start = time.perf_counter()
                platforms = adapter.fetch_platforms_block()
                self._upsert_results(results=platforms)
                time_end = time.perf_counter()

                if adapter.has_errored():
                    had_errors = True
                    self.stdout.write(self.style.ERROR("\nERROR: {}".format(adapter.error_info())))
                self._wait_if_needed(time_start=time_start, time_end=time_end)

            self.stdout.write("")

        if had_errors:
            self.stdout.write(self.style.WARNING("> Finished fetching '{}' with errors".format(source_id)))
        else:
            self.stdout.write(self.style.SUCCESS("> Finished fetching '{}'".format(source_id)))

    def _upsert_results(self, results: List[FetchedPlatform]) -> None:
        errors = []
        count = 0

        for platform in results:
            self.stdout.write("{}:".format(platform.source_platform_id), ending="")

            try:
                existing_platform = FetchedPlatform.objects.get(
                    source_platform_id=platform.source_platform_id, source_id=platform.source_id
                )
                existing_platform.name = platform.name
                existing_platform.source_platform_id = platform.source_platform_id
                existing_platform.source_id = platform.source_id
                existing_platform.source_url = platform.source_url
                last_modified_date = existing_platform.last_modified_date
                existing_platform.save()
                if existing_platform.last_modified_date != last_modified_date:
                    self.stdout.write(self.style.SUCCESS("☑  "), ending="")
                else:
                    self.stdout.write(self.style.WARNING("☐  "), ending="")
            except FetchedPlatform.DoesNotExist:
                platform.save()
                self.stdout.write(self.style.SUCCESS("✓  "), ending="")
            except Exception as error:
                errors.append(str(error))
                self.stdout.write(self.style.ERROR("✗  "), ending="")

            count += 1
            if count % 10 == 0:
                self.stdout.write("")

        # TODO: output errors

    def _wait_if_needed(self, time_start, time_end) -> None:
        time_elapsed = time_end - time_start
        # Most apis allow 1 request per second, so default to 1 fetch request per second
        if time_elapsed < 1.0:
            time.sleep(1.0 - time_elapsed)

    def _source_class_from_id(self, source_id: str) -> Type[BaseAdapter]:
        if source_id == GiantBombAdapter.source_id():
            return GiantBombAdapter

        raise ValueError("Unknown source id '{}'".format(source_id))
