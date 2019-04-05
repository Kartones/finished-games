from django.test import TestCase

from catalogsources.helpers import clean_string_field


class HelpersTests(TestCase):

    def test_field_cleaning_helper_with_typical_string_field(self):
        unclean_name = " _A name needing cleaning: ñ-:!"
        cleaned_name = "A name needing cleaning: ñ"

        self.assertEqual(clean_string_field(unclean_name), cleaned_name)

    def test_field_cleaning_helper_with_null_field(self):
        # should not error
        self.assertEqual(clean_string_field(None), None)
