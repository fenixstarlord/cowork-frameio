"""Tests for MCP tool implementations."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import respx

from frameio_mcp.auth import AuthManager
from frameio_mcp.client import BASE_URL, FrameIOClient
from frameio_mcp.tools.account import (
    ListProjectsInput,
    ListWorkspacesInput,
    frameio_list_projects,
    frameio_list_workspaces,
    frameio_whoami,
)
from frameio_mcp.tools.files import (
    CreateFileInput,
    CreateFolderInput,
    DeleteFileInput,
    GetFileInput,
    ListFolderInput,
    UpdateFileInput,
    frameio_create_file,
    frameio_create_folder,
    frameio_delete_file,
    frameio_get_file,
    frameio_list_folder,
    frameio_update_file,
)
from frameio_mcp.tools.comments import (
    CreateCommentInput,
    ListCommentsInput,
    ResolveCommentInput,
    frameio_create_comment,
    frameio_list_comments,
    frameio_resolve_comment,
)
from frameio_mcp.tools.shares import (
    CreateShareInput,
    DeleteShareInput,
    ListSharesInput,
    frameio_create_share,
    frameio_delete_share,
    frameio_list_shares,
)
from frameio_mcp.tools.metadata import (
    BulkUpdateFieldsInput,
    GetCustomFieldsInput,
    ListCollectionsInput,
    UpdateCustomFieldInput,
    frameio_bulk_update_fields,
    frameio_get_custom_fields,
    frameio_list_collections,
    frameio_update_custom_field,
)
from frameio_mcp.server import TOOL_REGISTRY, _build_tool_list, _handle_tool_call


RL_HEADERS = {
    "x-ratelimit-limit": "100",
    "x-ratelimit-remaining": "99",
    "x-ratelimit-window": "60",
}


@pytest.fixture
def auth() -> AuthManager:
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


# ---------------------------------------------------------------------------
# Server / registry tests
# ---------------------------------------------------------------------------


class TestToolRegistry:
    """Verify all 20 tools are registered."""

    def test_all_20_tools_registered(self) -> None:
        assert len(TOOL_REGISTRY) == 20

    def test_tool_names(self) -> None:
        expected = {
            "frameio_whoami",
            "frameio_list_workspaces",
            "frameio_list_projects",
            "frameio_list_folder",
            "frameio_create_folder",
            "frameio_create_file",
            "frameio_complete_upload",
            "frameio_get_file",
            "frameio_update_file",
            "frameio_delete_file",
            "frameio_list_comments",
            "frameio_create_comment",
            "frameio_resolve_comment",
            "frameio_create_share",
            "frameio_list_shares",
            "frameio_delete_share",
            "frameio_list_collections",
            "frameio_get_custom_fields",
            "frameio_update_custom_field",
            "frameio_bulk_update_fields",
        }
        assert set(TOOL_REGISTRY.keys()) == expected

    def test_build_tool_list(self) -> None:
        tools = _build_tool_list()
        assert len(tools) == 20
        names = {t.name for t in tools}
        assert "frameio_whoami" in names
        assert "frameio_delete_file" in names

    @pytest.mark.asyncio
    async def test_handle_unknown_tool(self, client: FrameIOClient) -> None:
        result = await _handle_tool_call(client, "frameio_nonexistent", {})
        parsed = json.loads(result)
        assert parsed["error"] is True
        assert parsed["code"] == 404


# ---------------------------------------------------------------------------
# Account tools
# ---------------------------------------------------------------------------


class TestAccountTools:

    @respx.mock
    @pytest.mark.asyncio
    async def test_whoami(self, client: FrameIOClient) -> None:
        respx.get(f"{BASE_URL}/v4/me").mock(
            return_value=httpx.Response(
                200,
                json={"data": {"id": "u1", "email": "test@example.com", "name": "Test User"}},
                headers=RL_HEADERS,
            )
        )
        respx.get(f"{BASE_URL}/v4/accounts").mock(
            return_value=httpx.Response(
                200,
                json={"data": [{"id": "a1", "name": "Acme Corp"}]},
                headers=RL_HEADERS,
            )
        )
        result = await frameio_whoami(client)
        assert result["user_id"] == "u1"
        assert result["email"] == "test@example.com"
        assert len(result["accounts"]) == 1
        assert result["accounts"][0]["id"] == "a1"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_workspaces(self, client: FrameIOClient) -> None:
        respx.get(f"{BASE_URL}/v4/accounts/a1/workspaces").mock(
            return_value=httpx.Response(
                200,
                json={"data": [{"id": "w1", "name": "Design", "member_count": 5}]},
                headers=RL_HEADERS,
            )
        )
        result = await frameio_list_workspaces(client, ListWorkspacesInput(account_id="a1"))
        assert len(result) == 1
        assert result[0]["id"] == "w1"
        assert result[0]["member_count"] == 5
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_projects(self, client: FrameIOClient) -> None:
        respx.get(f"{BASE_URL}/v4/accounts/a1/workspaces/w1/projects").mock(
            return_value=httpx.Response(
                200,
                json={"data": [{"id": "p1", "name": "Campaign", "root_folder_id": "rf1", "created_at": "2024-01-01"}]},
                headers=RL_HEADERS,
            )
        )
        result = await frameio_list_projects(
            client, ListProjectsInput(account_id="a1", workspace_id="w1")
        )
        assert len(result) == 1
        assert result[0]["root_folder_id"] == "rf1"
        await client.close()


# ---------------------------------------------------------------------------
# File tools
# ---------------------------------------------------------------------------


class TestFileTools:

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_folder(self, client: FrameIOClient) -> None:
        respx.get(f"{BASE_URL}/v4/accounts/a1/folders/f1/children").mock(
            return_value=httpx.Response(
                200,
                json={"data": [{"id": "c1", "name": "video.mp4"}], "links": {"next": None}},
                headers=RL_HEADERS,
            )
        )
        result = await frameio_list_folder(client, ListFolderInput(account_id="a1", folder_id="f1"))
        assert len(result["items"]) == 1
        assert result["next_cursor"] is None
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_folder(self, client: FrameIOClient) -> None:
        respx.post(f"{BASE_URL}/v4/accounts/a1/folders").mock(
            return_value=httpx.Response(
                201,
                json={"data": {"id": "f2", "name": "Dailies", "created_at": "2024-01-01"}},
                headers=RL_HEADERS,
            )
        )
        result = await frameio_create_folder(
            client, CreateFolderInput(account_id="a1", parent_id="f1", name="Dailies")
        )
        assert result["id"] == "f2"
        assert result["name"] == "Dailies"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_file(self, client: FrameIOClient) -> None:
        respx.post(f"{BASE_URL}/v4/accounts/a1/files").mock(
            return_value=httpx.Response(
                201,
                json={"data": {"id": "file1", "upload_urls": ["https://s3/1", "https://s3/2"]}},
                headers=RL_HEADERS,
            )
        )
        result = await frameio_create_file(
            client,
            CreateFileInput(account_id="a1", parent_id="f1", name="video.mp4", size=10_000_000, type="video/mp4"),
        )
        assert result["id"] == "file1"
        assert len(result["upload_urls"]) == 2
        assert result["chunk_size"] == 5_000_000
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_file(self, client: FrameIOClient) -> None:
        respx.get(f"{BASE_URL}/v4/accounts/a1/files/file1").mock(
            return_value=httpx.Response(
                200,
                json={"data": {"id": "file1", "name": "video.mp4", "status": "ready"}},
                headers=RL_HEADERS,
            )
        )
        result = await frameio_get_file(client, GetFileInput(account_id="a1", file_id="file1"))
        assert result["id"] == "file1"
        assert result["name"] == "video.mp4"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_file(self, client: FrameIOClient) -> None:
        respx.patch(f"{BASE_URL}/v4/accounts/a1/files/file1").mock(
            return_value=httpx.Response(
                200,
                json={"data": {"id": "file1", "name": "renamed.mp4"}},
                headers=RL_HEADERS,
            )
        )
        result = await frameio_update_file(
            client, UpdateFileInput(account_id="a1", file_id="file1", fields={"name": "renamed.mp4"})
        )
        assert result["name"] == "renamed.mp4"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_delete_file_confirmed(self, client: FrameIOClient) -> None:
        respx.delete(f"{BASE_URL}/v4/accounts/a1/files/file1").mock(
            return_value=httpx.Response(204)
        )
        result = await frameio_delete_file(
            client, DeleteFileInput(account_id="a1", file_id="file1", confirmed=True)
        )
        assert result["deleted"] is True
        await client.close()

    @pytest.mark.asyncio
    async def test_delete_file_not_confirmed(self, client: FrameIOClient) -> None:
        result = await frameio_delete_file(
            client, DeleteFileInput(account_id="a1", file_id="file1", confirmed=False)
        )
        assert result["deleted"] is False
        assert "not confirmed" in result["message"].lower()
        await client.close()


# ---------------------------------------------------------------------------
# Comment tools
# ---------------------------------------------------------------------------


class TestCommentTools:

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_comments(self, client: FrameIOClient) -> None:
        respx.get(f"{BASE_URL}/v4/accounts/a1/comments").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [{"id": "cm1", "text": "Nice shot!", "timecode": "00:01:05:00"}],
                    "links": {"next": None},
                },
                headers=RL_HEADERS,
            )
        )
        result = await frameio_list_comments(
            client, ListCommentsInput(account_id="a1", asset_id="file1")
        )
        assert len(result["comments"]) == 1
        assert result["comments"][0]["text"] == "Nice shot!"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_comment(self, client: FrameIOClient) -> None:
        respx.post(f"{BASE_URL}/v4/accounts/a1/comments").mock(
            return_value=httpx.Response(
                201,
                json={"data": {"id": "cm2", "text": "Fix color", "timecode": "00:00:30:00", "created_at": "2024-01-01"}},
                headers=RL_HEADERS,
            )
        )
        result = await frameio_create_comment(
            client,
            CreateCommentInput(account_id="a1", asset_id="file1", text="Fix color", timecode="00:00:30:00"),
        )
        assert result["id"] == "cm2"
        assert result["timecode"] == "00:00:30:00"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_comment(self, client: FrameIOClient) -> None:
        respx.patch(f"{BASE_URL}/v4/accounts/a1/comments/cm1").mock(
            return_value=httpx.Response(
                200,
                json={"data": {"id": "cm1", "resolved": True}},
                headers=RL_HEADERS,
            )
        )
        result = await frameio_resolve_comment(
            client, ResolveCommentInput(account_id="a1", comment_id="cm1")
        )
        assert result["resolved"] is True
        await client.close()


# ---------------------------------------------------------------------------
# Share tools
# ---------------------------------------------------------------------------


class TestShareTools:

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_share(self, client: FrameIOClient) -> None:
        respx.post(f"{BASE_URL}/v4/accounts/a1/shares").mock(
            return_value=httpx.Response(
                201,
                json={"data": {"id": "s1", "url": "https://app.frame.io/s/abc", "access": "public", "expires_at": None}},
                headers=RL_HEADERS,
            )
        )
        result = await frameio_create_share(
            client,
            CreateShareInput(account_id="a1", asset_ids=["file1"], access="public"),
        )
        assert result["id"] == "s1"
        assert "frame.io" in result["url"]
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_shares(self, client: FrameIOClient) -> None:
        respx.get(f"{BASE_URL}/v4/accounts/a1/shares").mock(
            return_value=httpx.Response(
                200,
                json={"data": [{"id": "s1", "url": "https://app.frame.io/s/abc", "access": "public", "asset_count": 3, "comment_count": 12}]},
                headers=RL_HEADERS,
            )
        )
        result = await frameio_list_shares(client, ListSharesInput(account_id="a1"))
        assert len(result) == 1
        assert result[0]["asset_count"] == 3
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_delete_share_confirmed(self, client: FrameIOClient) -> None:
        respx.delete(f"{BASE_URL}/v4/accounts/a1/shares/s1").mock(
            return_value=httpx.Response(204)
        )
        result = await frameio_delete_share(
            client, DeleteShareInput(account_id="a1", share_id="s1", confirmed=True)
        )
        assert result["deleted"] is True
        await client.close()

    @pytest.mark.asyncio
    async def test_delete_share_not_confirmed(self, client: FrameIOClient) -> None:
        result = await frameio_delete_share(
            client, DeleteShareInput(account_id="a1", share_id="s1", confirmed=False)
        )
        assert result["deleted"] is False
        await client.close()


# ---------------------------------------------------------------------------
# Metadata tools
# ---------------------------------------------------------------------------


class TestMetadataTools:

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_collections(self, client: FrameIOClient) -> None:
        respx.get(f"{BASE_URL}/v4/accounts/a1/collections").mock(
            return_value=httpx.Response(
                200,
                json={"data": [{"id": "col1", "name": "Approved", "asset_count": 10, "filter_criteria": {"status": "approved"}}]},
                headers=RL_HEADERS,
            )
        )
        result = await frameio_list_collections(
            client, ListCollectionsInput(account_id="a1", project_id="p1")
        )
        assert len(result) == 1
        assert result[0]["name"] == "Approved"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_custom_fields(self, client: FrameIOClient) -> None:
        respx.get(f"{BASE_URL}/v4/accounts/a1/projects/p1/field_definitions").mock(
            return_value=httpx.Response(
                200,
                json={"data": [{"id": "fd1", "name": "Review Status", "type": "select", "allowed_values": ["pending", "approved", "rejected"]}]},
                headers=RL_HEADERS,
            )
        )
        result = await frameio_get_custom_fields(
            client, GetCustomFieldsInput(account_id="a1", project_id="p1")
        )
        assert len(result) == 1
        assert result[0]["type"] == "select"
        assert "approved" in result[0]["allowed_values"]
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_custom_field(self, client: FrameIOClient) -> None:
        respx.patch(f"{BASE_URL}/v4/accounts/a1/files/file1").mock(
            return_value=httpx.Response(
                200,
                json={"data": {"id": "file1", "custom_fields": {"fd1": "approved"}}},
                headers=RL_HEADERS,
            )
        )
        result = await frameio_update_custom_field(
            client,
            UpdateCustomFieldInput(account_id="a1", file_id="file1", field_id="fd1", value="approved"),
        )
        assert result["value"] == "approved"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_bulk_update_fields(self, client: FrameIOClient) -> None:
        respx.patch(f"{BASE_URL}/v4/accounts/a1/files/file1").mock(
            return_value=httpx.Response(200, json={"data": {"id": "file1"}}, headers=RL_HEADERS)
        )
        respx.patch(f"{BASE_URL}/v4/accounts/a1/files/file2").mock(
            return_value=httpx.Response(200, json={"data": {"id": "file2"}}, headers=RL_HEADERS)
        )
        result = await frameio_bulk_update_fields(
            client,
            BulkUpdateFieldsInput(account_id="a1", file_ids=["file1", "file2"], field_id="fd1", value="approved"),
        )
        assert result["updated_count"] == 2
        assert result["failed"] == []
        await client.close()


# ---------------------------------------------------------------------------
# Error response format tests
# ---------------------------------------------------------------------------


class TestErrorFormat:
    """Verify errors from tools match the standardized format."""

    def test_error_response_shape(self) -> None:
        from frameio_mcp.utils.errors import format_error_response

        err = format_error_response(429, "rate_limit_exceeded", "Too fast", retry_after_ms=2300)
        assert err["error"] is True
        assert err["code"] == 429
        assert err["type"] == "rate_limit_exceeded"
        assert err["retry_after_ms"] == 2300

    def test_error_response_no_retry(self) -> None:
        from frameio_mcp.utils.errors import format_error_response

        err = format_error_response(404, "not_found", "Missing")
        assert "retry_after_ms" not in err
