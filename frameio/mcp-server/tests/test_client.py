"""Tests for the Frame.io API client."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import respx

from frameio_mcp.auth import AuthManager
from frameio_mcp.client import BASE_URL, FrameIOClient
from frameio_mcp.utils.errors import (
    AuthExpiredError,
    NotFoundError,
    RateLimitError,
    ServerError,
    UploadFailedError,
)


@pytest.fixture
def auth() -> AuthManager:
    """AuthManager with a mock token store that always has a valid token."""
    am = AuthManager(client_id="test-id", client_secret="test-secret")
    am.token_store._tokens = {
        "access_token": "test-token",
        "refresh_token": "test-refresh",
        "expires_at": 9999999999,
    }
    return am


@pytest.fixture
def client(auth: AuthManager) -> FrameIOClient:
    return FrameIOClient(auth)


class TestClientRequest:
    """Test the core request method."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_success(self, client: FrameIOClient) -> None:
        route = respx.get(f"{BASE_URL}/v4/me").mock(
            return_value=httpx.Response(
                200,
                json={"data": {"id": "u1", "name": "Test"}},
                headers={
                    "x-ratelimit-limit": "100",
                    "x-ratelimit-remaining": "99",
                    "x-ratelimit-window": "60",
                },
            )
        )
        result = await client.get("/v4/me")
        assert result is not None
        assert result["data"]["id"] == "u1"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_delete_204(self, client: FrameIOClient) -> None:
        respx.delete(f"{BASE_URL}/v4/accounts/a1/files/f1").mock(
            return_value=httpx.Response(204)
        )
        result = await client.delete("/v4/accounts/a1/files/f1")
        assert result is None
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_404_raises(self, client: FrameIOClient) -> None:
        respx.get(f"{BASE_URL}/v4/accounts/a1/files/bad").mock(
            return_value=httpx.Response(
                404,
                json={"errors": [{"detail": "Not found", "title": "Not Found"}]},
            )
        )
        with pytest.raises(NotFoundError):
            await client.get("/v4/accounts/a1/files/bad")
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_500_raises(self, client: FrameIOClient) -> None:
        respx.get(f"{BASE_URL}/v4/accounts/a1/files/err").mock(
            return_value=httpx.Response(
                500,
                json={"errors": [{"detail": "Internal error"}]},
            )
        )
        with pytest.raises(ServerError):
            await client.get("/v4/accounts/a1/files/err")
        await client.close()


class TestClientRateLimit:
    """Test 429 handling with backoff."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_429_retries_then_succeeds(self, client: FrameIOClient) -> None:
        call_count = 0

        def side_effect(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return httpx.Response(
                    429,
                    json={"errors": [{"detail": "Rate limited"}]},
                    headers={"x-ratelimit-limit": "100", "x-ratelimit-remaining": "0", "x-ratelimit-window": "60"},
                )
            return httpx.Response(
                200,
                json={"data": {"id": "ok"}},
                headers={"x-ratelimit-limit": "100", "x-ratelimit-remaining": "50", "x-ratelimit-window": "60"},
            )

        respx.get(f"{BASE_URL}/v4/me").mock(side_effect=side_effect)
        # Patch sleep to avoid real delays in tests
        with patch("frameio_mcp.client.asyncio.sleep", new_callable=AsyncMock):
            result = await client.get("/v4/me")
        assert result is not None
        assert result["data"]["id"] == "ok"
        assert call_count == 3
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_429_exhausts_retries(self, client: FrameIOClient) -> None:
        respx.get(f"{BASE_URL}/v4/me").mock(
            return_value=httpx.Response(
                429,
                json={"errors": [{"detail": "Rate limited"}]},
                headers={"x-ratelimit-limit": "100", "x-ratelimit-remaining": "0", "x-ratelimit-window": "60"},
            )
        )
        with patch("frameio_mcp.client.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RateLimitError):
                await client.get("/v4/me")
        await client.close()


class TestClientAuth:
    """Test 401 handling and token refresh."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_401_triggers_refresh(self, client: FrameIOClient) -> None:
        call_count = 0

        def side_effect(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(401, json={"errors": [{"detail": "Unauthorized"}]})
            return httpx.Response(
                200,
                json={"data": {"id": "u1"}},
                headers={"x-ratelimit-limit": "100", "x-ratelimit-remaining": "99", "x-ratelimit-window": "60"},
            )

        respx.get(f"{BASE_URL}/v4/me").mock(side_effect=side_effect)

        # Mock the auth refresh to succeed
        client.auth.refresh = AsyncMock(return_value=True)
        client.auth.get_valid_token = AsyncMock(return_value="new-token")

        result = await client.get("/v4/me")
        assert result is not None
        assert result["data"]["id"] == "u1"
        client.auth.refresh.assert_called_once()
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_401_refresh_fails(self, client: FrameIOClient) -> None:
        respx.get(f"{BASE_URL}/v4/me").mock(
            return_value=httpx.Response(401, json={"errors": [{"detail": "Unauthorized"}]})
        )
        client.auth.refresh = AsyncMock(return_value=False)

        with pytest.raises(AuthExpiredError):
            await client.get("/v4/me")
        await client.close()


class TestClientPagination:
    """Test the paginate helper."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_paginate_first_page(self, client: FrameIOClient) -> None:
        respx.get(f"{BASE_URL}/v4/accounts/a1/folders/f1/children").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [{"id": "c1"}, {"id": "c2"}],
                    "links": {"next": "https://api.frame.io/v4/accounts/a1/folders/f1/children?cursor=abc123"},
                },
                headers={"x-ratelimit-limit": "100", "x-ratelimit-remaining": "99", "x-ratelimit-window": "60"},
            )
        )
        result = await client.paginate("/v4/accounts/a1/folders/f1/children", page_size=25)
        assert len(result["items"]) == 2
        assert result["next_cursor"] == "abc123"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_paginate_no_next(self, client: FrameIOClient) -> None:
        respx.get(f"{BASE_URL}/v4/accounts/a1/folders/f1/children").mock(
            return_value=httpx.Response(
                200,
                json={"data": [{"id": "c1"}], "links": {"next": None}},
                headers={"x-ratelimit-limit": "100", "x-ratelimit-remaining": "99", "x-ratelimit-window": "60"},
            )
        )
        result = await client.paginate("/v4/accounts/a1/folders/f1/children")
        assert len(result["items"]) == 1
        assert result["next_cursor"] is None
        await client.close()


class TestClientS3Upload:
    """Test S3 chunk upload."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_upload_chunk_success(self, client: FrameIOClient) -> None:
        respx.put("https://s3.amazonaws.com/upload/chunk1").mock(
            return_value=httpx.Response(200)
        )
        await client.upload_chunk(
            "https://s3.amazonaws.com/upload/chunk1",
            b"chunk-data",
            "video/mp4",
        )
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_upload_chunk_s3_error(self, client: FrameIOClient) -> None:
        xml_error = b"""<?xml version="1.0" encoding="UTF-8"?>
<Error>
  <Code>AccessDenied</Code>
  <Message>Request has expired</Message>
</Error>"""
        respx.put("https://s3.amazonaws.com/upload/chunk1").mock(
            return_value=httpx.Response(403, content=xml_error)
        )
        with pytest.raises(UploadFailedError, match="AccessDenied"):
            await client.upload_chunk(
                "https://s3.amazonaws.com/upload/chunk1",
                b"chunk-data",
                "video/mp4",
            )
        await client.close()
