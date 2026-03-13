"""Async HTTP client for Frame.io V4 API using httpx."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from frameio_mcp.auth import AuthManager
from frameio_mcp.utils.errors import (
    AuthExpiredError,
    FrameIOError,
    RateLimitError,
    parse_api_error,
    parse_s3_error,
)
from frameio_mcp.utils.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

BASE_URL = "https://api.frame.io/v4"


class FrameIOClient:
    """Async client for the Frame.io V4 API.

    Wraps ``httpx.AsyncClient`` with:
    - Automatic Bearer token injection (via AuthManager)
    - Rate-limit header tracking and proactive throttling
    - Exponential backoff on 429 responses
    - Automatic token refresh on 401
    - Standardised error handling
    """

    def __init__(self, auth: AuthManager) -> None:
        self.auth = auth
        self.rate_limiter = RateLimiter()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=BASE_URL,
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # Core request method
    # ------------------------------------------------------------------

    async def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Send an authenticated request to the Frame.io V4 API.

        Handles 401 refresh, 429 backoff, and error parsing.
        Returns the parsed JSON body, or None for 204 responses.
        """
        client = await self._get_client()

        # Proactive rate-limit wait
        await self.rate_limiter.wait_if_needed()

        token = await self.auth.get_valid_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        for _attempt in range(self.rate_limiter.MAX_RETRIES + 1):
            resp = await client.request(
                method,
                path,
                headers=headers,
                json=json_body,
                params=params,
            )

            # Update rate-limit state from response headers
            self.rate_limiter.update_from_headers(dict(resp.headers))

            if resp.status_code == 204:
                return None

            if resp.status_code == 401:
                # Try refreshing the token once
                refreshed = await self.auth.refresh()
                if not refreshed:
                    raise AuthExpiredError("Token refresh failed. Please re-authenticate.")
                token = await self.auth.get_valid_token()
                headers["Authorization"] = f"Bearer {token}"
                continue

            if resp.status_code == 429:
                if not self.rate_limiter.should_retry:
                    raise RateLimitError("Rate limit exceeded after max retries")
                delay = self.rate_limiter.backoff_delay()
                await asyncio.sleep(delay)
                continue

            if resp.status_code >= 400:
                try:
                    body = resp.json()
                except Exception:
                    body = None
                raise parse_api_error(resp.status_code, body)

            # Success
            self.rate_limiter.reset_backoff()
            return resp.json()

        raise RateLimitError("Rate limit exceeded after max retries")

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    async def get(self, path: str, **kwargs: Any) -> dict[str, Any] | None:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> dict[str, Any] | None:
        return await self.request("POST", path, **kwargs)

    async def patch(self, path: str, **kwargs: Any) -> dict[str, Any] | None:
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> dict[str, Any] | None:
        return await self.request("DELETE", path, **kwargs)

    # ------------------------------------------------------------------
    # Pagination helper
    # ------------------------------------------------------------------

    async def paginate(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        page_size: int = 50,
        cursor: str | None = None,
        max_pages: int | None = None,
    ) -> dict[str, Any]:
        """Fetch a single page and return items + next_cursor.

        If cursor is None, fetches the first page.
        Returns {"items": [...], "next_cursor": str | None}.
        """
        p = dict(params or {})
        p["page_size"] = min(page_size, 100)
        if cursor:
            p["cursor"] = cursor

        resp = await self.get(path, params=p)
        if resp is None:
            return {"items": [], "next_cursor": None}

        items = resp.get("data", [])
        next_cursor = None
        links = resp.get("links", {})
        if links and links.get("next"):
            # Extract cursor from next URL or use the value directly
            next_url = links["next"]
            if "cursor=" in next_url:
                next_cursor = next_url.split("cursor=")[-1].split("&")[0]
            else:
                next_cursor = next_url

        return {"items": items, "next_cursor": next_cursor}

    # ------------------------------------------------------------------
    # S3 upload helper
    # ------------------------------------------------------------------

    async def upload_chunk(
        self,
        presigned_url: str,
        chunk_data: bytes,
        media_type: str,
    ) -> None:
        """Upload a single chunk to S3 via a presigned PUT URL.

        S3 errors are XML — parsed into UploadFailedError.
        """
        client = await self._get_client()
        resp = await client.put(
            presigned_url,
            content=chunk_data,
            headers={
                "Content-Type": media_type,
                "x-amz-acl": "private",
            },
            timeout=httpx.Timeout(300.0),  # large chunks may take a while
        )

        if resp.status_code >= 400:
            raise parse_s3_error(resp.content)
