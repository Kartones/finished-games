import time

from django.test import TestCase

from catalogsources.adapters.helpers import check_rate_limit


class GameFormTests(TestCase):

    def test_bucket_decrements_if_tokens_available(self):
        max_tokens = 2
        time_window = 600  # 10 minutes
        bucket = max_tokens
        last_check_ts = 0.0

        token_bucket, current_timestamp, can_pass = check_rate_limit(
            max_tokens=max_tokens, time_window=time_window, token_bucket=bucket, last_check_timestamp=last_check_ts
        )

        # bucket not even modified
        self.assertEqual(token_bucket, max_tokens - 1)
        self.assertNotEqual(token_bucket, bucket)
        self.assertTrue(can_pass)
        self.assertNotEqual(current_timestamp, last_check_ts)

    def test_bucket_doesnt_decrements_if_no_tokens_available(self):
        max_tokens = 2
        time_window = 600  # 10 minutes
        bucket = 0
        last_check_ts = time.time()

        token_bucket, current_timestamp, can_pass = check_rate_limit(
            max_tokens=max_tokens, time_window=time_window, token_bucket=bucket, last_check_timestamp=last_check_ts
        )

        # Will generate 1 token each 5 minutes so impossible to have one already
        self.assertTrue(token_bucket < 1.0)
        # But should have generated some decimal part of a token
        self.assertTrue(token_bucket > 0.0)
        self.assertFalse(can_pass)
        self.assertNotEqual(current_timestamp, last_check_ts)

    # Could mock/patch time here, but due to a one second delay not a big deal...
    def test_when_new_token_generated_allows_to_pass_and_decrements_correctly(self):
        max_tokens = 2
        time_window = 2  # generates 1 new token per second
        bucket = 0
        last_check_ts = time.time()

        bucket, last_check_ts, can_pass = check_rate_limit(
            max_tokens=max_tokens, time_window=time_window, token_bucket=bucket, last_check_timestamp=last_check_ts
        )
        self.assertTrue(bucket < 1.0)
        self.assertFalse(can_pass)

        # Not yet...
        time.sleep(0.5)
        bucket, last_check_ts, can_pass = check_rate_limit(
            max_tokens=max_tokens, time_window=time_window, token_bucket=bucket, last_check_timestamp=last_check_ts
        )
        self.assertTrue(bucket < 1.0)
        self.assertFalse(can_pass)

        # But now should have a new token
        time.sleep(0.6)
        bucket, last_check_ts, can_pass = check_rate_limit(
            max_tokens=max_tokens, time_window=time_window, token_bucket=bucket, last_check_timestamp=last_check_ts
        )
        self.assertTrue(can_pass)
        # Why this? Because as was able to pass, the token it just obtained was consumed actually letting it pass
        self.assertTrue(bucket < 1.0)
