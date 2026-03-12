"""Rate limiting with leaky bucket tracking and exponential backoff."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field


@dataclass
class _BucketState:
    """Tracks the state of a rate-limit bucket."""

    limit: int = 0
    remaining: int = 0
    window: float = 0.0
    last_updated: float = field(default_factory=time.monotonic)


class RateLimiter:
    """Proactive rate limiter that reads Frame.io response headers.

    - Tracks ``x-ratelimit-limit``, ``x-ratelimit-remaining``, ``x-ratelimit-window``.
    - When remaining drops below 20% of limit, introduces a small delay.
    - On 429 responses, performs exponential backoff (1s base, doubles, max 30s).
    """

    BASE_BACKOFF_S: float = 1.0
    MAX_BACKOFF_S: float = 30.0
    MAX_RETRIES: int = 3
    PROACTIVE_THRESHOLD: float = 0.20  # 20%

    def __init__(self) -> None:
        self._bucket = _BucketState()
        self._consecutive_429s: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_from_headers(self, headers: dict[str, str] | None) -> None:
        """Read rate-limit headers from an API response and update state."""
        if headers is None:
            return
        # httpx returns case-insensitive headers; normalise keys just in case
        h = {k.lower(): v for k, v in headers.items()}
        try:
            limit = int(h.get("x-ratelimit-limit", "0"))
            remaining = int(h.get("x-ratelimit-remaining", "0"))
            window = float(h.get("x-ratelimit-window", "0"))
        except (ValueError, TypeError):
            return

        self._bucket.limit = limit
        self._bucket.remaining = remaining
        self._bucket.window = window
        self._bucket.last_updated = time.monotonic()

        # Reset backoff counter on successful (non-429) responses
        self._consecutive_429s = 0

    async def wait_if_needed(self) -> None:
        """Proactively wait when remaining capacity is low."""
        b = self._bucket
        if b.limit <= 0:
            return  # no data yet
        ratio = b.remaining / b.limit
        if ratio < self.PROACTIVE_THRESHOLD:
            # Spread remaining capacity over the window
            delay = b.window / max(b.remaining, 1)
            delay = min(delay, 2.0)  # cap proactive delay
            await asyncio.sleep(delay)

    def backoff_delay(self) -> float:
        """Return the next exponential backoff delay after a 429, in seconds."""
        self._consecutive_429s += 1
        delay = self.BASE_BACKOFF_S * (2 ** (self._consecutive_429s - 1))
        return min(delay, self.MAX_BACKOFF_S)

    @property
    def should_retry(self) -> bool:
        """Whether we haven't exceeded the max retry count."""
        return self._consecutive_429s < self.MAX_RETRIES

    def reset_backoff(self) -> None:
        """Reset the consecutive 429 counter."""
        self._consecutive_429s = 0

    @property
    def remaining(self) -> int:
        return self._bucket.remaining

    @property
    def limit(self) -> int:
        return self._bucket.limit
