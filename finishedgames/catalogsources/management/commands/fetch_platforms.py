from typing import Any, Dict, List

from catalogsources.helpers import clean_string_field
from catalogsources.management.helpers import TimeProfiler, source_class_from_id, wait_if_needed
from catalogsources.models import FetchedPlatform
from django.core.management.base import BaseCommand, CommandParser


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
        self.stdout.write(self.style.WARNING("> Started fetching platforms from '{}'".format(source_id)))

        adapter_class = source_class_from_id(source_id)

        self.default_publish_date = adapter_class.DEFAULT_PUBLISH_DATE

        with adapter_class(stdout=self.stdout, stdout_color_style=self.style) as adapter:
            self.stdout.write(self.style.WARNING("> Batch size:{}".format(adapter.batch_size())))

            while adapter.has_more_items() and not had_errors:
                total = adapter.total_results if adapter.total_results != adapter.UNKOWN_TOTAL_RESULTS_VALUE else "-"
                self.stdout.write("\n> Fetch call: {current}/{total}".format(current=adapter.next_offset, total=total))

                with TimeProfiler(use_performance_counter=True) as profiler:
                    platforms = adapter.fetch_platforms_block()
                    self._upsert_results(results=platforms)
                had_errors = adapter.has_errored()
                wait_if_needed(profiler.duration)

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

            platform.name = clean_string_field(platform.name)
            platform.shortname = clean_string_field(platform.shortname)

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
                    self.stdout.write(self.style.SUCCESS("☑ "), ending="")
                else:
                    self.stdout.write("☐ ", ending="")
            except FetchedPlatform.DoesNotExist:
                platform.save()
                self.stdout.write(self.style.SUCCESS("✓ "), ending="")
            except Exception as error:
                errors.append(str(error))
                self.stdout.write(self.style.ERROR("✗ "), ending="")

            count += 1
            if count % 10 == 0:
                self.stdout.write("")

        if errors:
            self.stdout.write(self.style.ERROR("\nErrors:"))
            for error_item in errors:
                self.stdout.write(self.style.ERROR(error_item))

    def _display_legend(self) -> None:
        self.stdout.write(self.style.WARNING("Legend: "))
        self.stdout.write(self.style.SUCCESS("✓ "), ending="")
        self.stdout.write("Added new platform")
        self.stdout.write(self.style.SUCCESS("☑ "), ending="")
        self.stdout.write("Updated existing platform (new changes)")
        self.stdout.write("☐ ", ending="")
        self.stdout.write("Existing platform not updated (no changes)")
        self.stdout.write(self.style.ERROR("✗ "), ending="")
        self.stdout.write("Error adding/updating platform")
        self.stdout.write(self.style.WARNING("-------\n"))
