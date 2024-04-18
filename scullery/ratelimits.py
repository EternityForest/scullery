"""Module for managing rate limits."""

import time


class RateLimiter:
    """
    Limit events to a certain rate, but allow building up
    "credits" for fast bursts.
    """

    def __init__(self, hz: float, burst=250) -> None:
        """The rate limiter will begin with accum_limit credits and
        cannot go above that.  rate is in number of credits added per second.
        """
        self.rate = hz
        self.accum_limit = burst
        self.current_limit = burst
        self.timestamp = time.monotonic()

    def limit(self) -> float:
        """If it hasn't been called too often, subtract one
        credit and return number of credits remaining, Otherwise return 0.

        Credits refill at "rate" per second up to a max of accum_limit
        """
        elapsed = time.monotonic() - self.timestamp
        self.current_limit += self.rate * elapsed
        self.current_limit = min(self.current_limit, self.accum_limit)
        if self.current_limit >= 1:
            self.current_limit -= 1
            return self.current_limit

        return 0.0
