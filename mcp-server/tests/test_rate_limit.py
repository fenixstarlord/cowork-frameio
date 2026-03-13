"""Tests for rate limiting logic."""

from __future__ import annotations

import asyncio
import time

import pytest

from frameio_mcp.utils.rate_limit import RateLimiter


class TestRateLimiterHeaders:
    """Test rate-limit header parsing and state tracking."""

    def test_update_from_headers(self) -> None:
        rl = RateLimiter()
        rl.update_from_headers({
            "x-ratelimit-limit": "100",
            "x-ratelimit-remaining": "80",
            "x-ratelimit-window": "60",
        })
        assert rl.limit == 100
        assert rl.remaining == 80

    def test_update_from_headers_none(self) -> None:
        rl = RateLimiter()
        rl.update_from_headers(None)
        assert rl.limit == 0
        assert rl.remaining == 0

    def test_update_from_headers_invalid(self) -> None:
        rl = RateLimiter()
        rl.update_from_headers({"x-ratelimit-limit": "not-a-number"})
        assert rl.limit == 0

    def test_update_resets_backoff_counter(self) -> None:
        rl = RateLimiter()
        # Simulate some 429s
        rl.backoff_delay()
        rl.backoff_delay()
        assert rl._consecutive_429s == 2
        # A successful response resets
        rl.update_from_headers({"x-ratelimit-limit": "100", "x-ratelimit-remaining": "50", "x-ratelimit-window": "60"})
        assert rl._consecutive_429s == 0


class TestRateLimiterBackoff:
    """Test exponential backoff calculations."""

    def test_backoff_doubles(self) -> None:
        rl = RateLimiter()
        d1 = rl.backoff_delay()  # 1s
        d2 = rl.backoff_delay()  # 2s
        d3 = rl.backoff_delay()  # 4s
        assert d1 == 1.0
        assert d2 == 2.0
        assert d3 == 4.0

    def test_backoff_caps_at_max(self) -> None:
        rl = RateLimiter()
        for _ in range(10):
            delay = rl.backoff_delay()
        assert delay <= rl.MAX_BACKOFF_S

    def test_should_retry_limit(self) -> None:
        rl = RateLimiter()
        assert rl.should_retry  # 0 < 3
        rl.backoff_delay()  # 1
        assert rl.should_retry  # 1 < 3
        rl.backoff_delay()  # 2
        assert rl.should_retry  # 2 < 3
        rl.backoff_delay()  # 3
        assert not rl.should_retry  # 3 >= 3

    def test_reset_backoff(self) -> None:
        rl = RateLimiter()
        rl.backoff_delay()
        rl.backoff_delay()
        rl.reset_backoff()
        assert rl.should_retry
        assert rl._consecutive_429s == 0


class TestRateLimiterProactive:
    """Test proactive waiting when capacity is low."""

    @pytest.mark.asyncio
    async def test_no_wait_when_no_data(self) -> None:
        rl = RateLimiter()
        start = time.monotonic()
        await rl.wait_if_needed()
        elapsed = time.monotonic() - start
        assert elapsed < 0.1  # should return immediately

    @pytest.mark.asyncio
    async def test_no_wait_when_plenty_remaining(self) -> None:
        rl = RateLimiter()
        rl.update_from_headers({
            "x-ratelimit-limit": "100",
            "x-ratelimit-remaining": "80",
            "x-ratelimit-window": "60",
        })
        start = time.monotonic()
        await rl.wait_if_needed()
        elapsed = time.monotonic() - start
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_waits_when_low_remaining(self) -> None:
        rl = RateLimiter()
        rl.update_from_headers({
            "x-ratelimit-limit": "100",
            "x-ratelimit-remaining": "5",  # 5% < 20%
            "x-ratelimit-window": "60",
        })
        start = time.monotonic()
        await rl.wait_if_needed()
        elapsed = time.monotonic() - start
        # Should have waited some amount (delay = 60/5 = 12, capped to 2.0)
        assert elapsed >= 1.5
