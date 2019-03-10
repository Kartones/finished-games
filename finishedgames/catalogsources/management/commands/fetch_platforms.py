import time
from typing import (Any, Dict, List)

from django.core.management.base import (BaseCommand, CommandParser)

from catalogsources.management.helpers import (source_class_from_id, wait_if_needed)
from catalogsources.models import FetchedPlatform


class Command(BaseCommand):
    help = "Fetches platforms from specified source ids"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("sources", nargs="+", type=str)

    def handle(self, *args: Any, **options: Dict) -> None:
        self._display_legend()
        for source_id in options["sources"]:
            self._fetch_source(source_id=source_id)

    def _fetch_source(self, source_id: str) -> None:
        had_errors = False
        self.stdout.write(self.style.WARNING(f"> Started fetching platforms from '{source_id}'"))

        adapter_class = source_class_from_id(source_id)

        self.default_publish_date = adapter_class.DEFAULT_PUBLISH_DATE

        with adapter_class(stdout=self.stdout, stdout_color_style=self.style) as adapter:
            while adapter.has_more_items() and not had_errors:
                total = adapter.total_results if adapter.total_results != adapter.UNKOWN_TOTAL_RESULTS_VALUE else "-"
                self.stdout.write(f"\n> Fetch call: {adapter.next_offset}/{total}")

                time_start = time.perf_counter()
                platforms = adapter.fetch_platforms_block()
                self._upsert_results(results=platforms)
                time_end = time.perf_counter()

                had_errors = adapter.has_errored()
                wait_if_needed(time_start=time_start, time_end=time_end)

            self.stdout.write("")

        if had_errors:
            self.stdout.write(self.style.WARNING(f"> Finished fetching '{source_id}' with errors"))
        else:
            self.stdout.write(self.style.SUCCESS(f"> Finished fetching '{source_id}'"))

    def _upsert_results(self, results: List[FetchedPlatform]) -> None:
        errors = []
        count = 0

        for platform in results:
            self.stdout.write(f"{platform.source_platform_id}:", ending="")

            try:
                existing_platform = FetchedPlatform.objects.get(
                    source_platform_id=platform.source_platform_id, source_id=platform.source_id
                )
                existing_platform.name = platform.name
                existing_platform.source_platform_id = platform.source_platform_id
                existing_platform.source_id = platform.source_id
                existing_platform.source_url = platform.source_url
                if platform.publish_date != self.default_publish_date:
                    existing_platform.publish_date = platform.publish_date
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

        if errors:
            self.stdout.write(self.style.ERROR("\nErrors:"))
            for error_item in errors:
                self.stdout.write(self.style.ERROR(error_item))

    def _display_legend(self) -> None:
        self.stdout.write("Legend: ")
        self.stdout.write(self.style.SUCCESS("✓ "), ending="")
        self.stdout.write("Added new platform")
        self.stdout.write(self.style.SUCCESS("☑ "), ending="")
        self.stdout.write("Updated existing platform (new changes)")
        self.stdout.write(self.style.WARNING("☐ "), ending="")
        self.stdout.write("Existing platform not updated (no changes)")
        self.stdout.write(self.style.ERROR("✗ "), ending="")
        self.stdout.write("Error adding/updating platform\n\n")
