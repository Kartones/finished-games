from catalogsources.adapters.helpers import check_rate_limit
from django.test import TestCase


class AdapterHelpersTests(TestCase):
    def test_bucket_decrements_if_tokens_available(self):
        max_tokens = 2
        time_window = 600  # 10 minutes
        bucket = max_tokens
        last_check_ts = 0.0

        mock_ts = 1

        token_bucket, current_timestamp, can_pass = check_rate_limit(
            max_tokens=max_tokens,
            time_window=time_window,
            token_bucket=bucket,
            last_check_timestamp=last_check_ts,
            time=lambda: mock_ts,
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
        last_check_ts = 0

        mock_ts = 1

        token_bucket, current_timestamp, can_pass = check_rate_limit(
            max_tokens=max_tokens,
            time_window=time_window,
            token_bucket=bucket,
            last_check_timestamp=last_check_ts,
            time=lambda: mock_ts,
        )

        # Will generate 1 token each 5 minutes so impossible to have one already
        self.assertTrue(token_bucket < 1.0)
        # But should have generated some decimal part of a token
        self.assertTrue(token_bucket > 0.0)
        self.assertFalse(can_pass)
        self.assertNotEqual(current_timestamp, last_check_ts)

    def test_when_new_token_generated_allows_to_pass_and_decrements_correctly(self):
        max_tokens = 2
        time_window = 20  # generates 1 new token each 10 seconds
        bucket = 0
        last_check_ts = 0

        # 1/2 token generated
        mock_ts = time_window / max_tokens / 2
        bucket, last_check_ts, can_pass = check_rate_limit(
            max_tokens=max_tokens,
            time_window=time_window,
            token_bucket=bucket,
            last_check_timestamp=last_check_ts,
            time=lambda: mock_ts,
        )
        self.assertTrue(bucket < 1.0)  # should be ~0.5
        self.assertFalse(can_pass)

        # Not yet...
        mock_ts = time_window / max_tokens - 0.1
        bucket, last_check_ts, can_pass = check_rate_limit(
            max_tokens=max_tokens,
            time_window=time_window,
            token_bucket=bucket,
            last_check_timestamp=last_check_ts,
            time=lambda: mock_ts,
        )
        self.assertTrue(bucket < 1.0)  # should be ~ 0.99
        self.assertFalse(can_pass)

        # Now should have one token
        mock_ts = time_window / max_tokens + 0.1
        bucket, last_check_ts, can_pass = check_rate_limit(
            max_tokens=max_tokens,
            time_window=time_window,
            token_bucket=bucket,
            last_check_timestamp=last_check_ts,
            time=lambda: mock_ts,
        )
        self.assertTrue(can_pass)
        # Why this? Because as was able to pass, the token it just obtained was consumed actually letting it pass
        self.assertTrue(bucket < 1.0)  # should be ~ 0.01
