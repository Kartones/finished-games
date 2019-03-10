import time

from typing import Tuple


def check_rate_limit(
    max_tokens: int, time_window: int, token_bucket: float, last_check_timestamp: float
) -> Tuple[float, float, bool]:
    """
    Token bucket algorithm implementation as rate limit.

    Allows up to `max_tokens` each `time_window` seconds.
    Upon each call will calculate time past since last call and add tokens to the bucket before checkint the limit.
    Note that bucket works with decimal tokens, as you usually get a fraction of a token if calling multiple
    times fast.
    e.g. if max_tokens = 10 and time_window = 300, you have 10 tokens in 5 minutes / 300 seconds, and will add/generate
    a "full" token each 30 seconds.

    Should provide predefined values for `max_tokens` and `time_window`, and just containers for `token_bucket` and
    `last_check_timestamp`.

    Based on:
    https://stackoverflow.com/questions/667508/whats-a-good-rate-limiting-algorithm &
    https://en.wikipedia.org/wiki/Token_bucket
    """
    max_tokens_float = float(max_tokens)

    current_timestamp = time.time()
    time_passed = current_timestamp - last_check_timestamp

    # 1st call will generate a huge tokens increment, and waiting long would also create many tokens
    increment = time_passed * (max_tokens_float / float(time_window))
    token_bucket += increment
    # so cap at maximum allowed
    if token_bucket > max_tokens_float:
        token_bucket = max_tokens_float

    if token_bucket < 1.0:
        can_pass = False
    else:
        can_pass = True
        token_bucket -= 1.0

    return (token_bucket, current_timestamp, can_pass)
