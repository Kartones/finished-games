from datetime import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase

from core.forms import PlatformForm
from core.test.helpers import create_platform


class PlatformFormTests(TestCase):

    def setUp(self):
        self.platform_1 = create_platform()

    def test_platform_names_are_unique(self):
        platform_data = {
            "name": "a unique name",
            "shortname": "a unique shortname",
            "publish_date": datetime.now().year
        }
        create_platform(name=platform_data["name"], shortname=platform_data["shortname"])

        platform_form = PlatformForm(platform_data)
        self.assertFalse(platform_form.is_valid())
        self.assertTrue("name" in platform_form.errors.keys())
        self.assertTrue("already exists" in platform_form.errors["name"][0])
        self.assertTrue("shortname" in platform_form.errors.keys())
        self.assertTrue("already exists" in platform_form.errors["shortname"][0])

    def test_platform_name_uniqueness_is_case_insensitive(self):
        platform_data = {
            "name": "A Case Sensitive Unique Name",
            "shortname": "A Case Sensitive Unique Shortname",
            "publish_date": datetime.now().year
        }
        create_platform(name=platform_data["name"], shortname=platform_data["shortname"])

        platform_2_data = platform_data.copy()
        platform_2_data["name"] = platform_2_data["name"].lower()
        platform_form = PlatformForm(platform_2_data)
        with self.assertRaises(ValidationError) as error:
            platform_form.is_valid()
        self.assertTrue("already exists" in str(error.exception))

        platform_2_data = platform_data.copy()
        platform_2_data["shortname"] = platform_2_data["shortname"].lower()
        platform_form = PlatformForm(platform_2_data)
        with self.assertRaises(ValidationError) as error:
            platform_form.is_valid()
        self.assertTrue("already exists" in str(error.exception))
