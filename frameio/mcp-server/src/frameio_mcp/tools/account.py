"""Account tools: frameio_whoami, frameio_list_workspaces, frameio_list_projects."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from frameio_mcp.client import FrameIOClient


# ---------------------------------------------------------------------------
# Pydantic models for tool inputs
# ---------------------------------------------------------------------------


class WhoAmIInput(BaseModel):
    """No parameters required."""
    pass


class ListWorkspacesInput(BaseModel):
    account_id: str = Field(..., description="Frame.io account ID")


class ListProjectsInput(BaseModel):
    account_id: str = Field(..., description="Frame.io account ID")
    workspace_id: str = Field(..., description="Workspace ID to list projects from")


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


async def frameio_whoami(client: FrameIOClient) -> dict[str, Any]:
    """Return the current authenticated user's profile and linked accounts."""
    me = await client.get("/v4/me")
    if me is None:
        return {"error": True, "code": 500, "type": "server_error", "message": "Empty response from /v4/me"}

    accounts_resp = await client.get("/v4/accounts")
    accounts: list[dict[str, Any]] = []
    if accounts_resp and "data" in accounts_resp:
        accounts = [
            {"id": a["id"], "name": a.get("name", "")}
            for a in accounts_resp["data"]
        ]

    user_data = me.get("data", me)
    return {
        "user_id": user_data.get("id", ""),
        "email": user_data.get("email", ""),
        "name": user_data.get("name", ""),
        "accounts": accounts,
    }


async def frameio_list_workspaces(
    client: FrameIOClient,
    params: ListWorkspacesInput,
) -> list[dict[str, Any]]:
    """List all workspaces in the given account."""
    resp = await client.get(f"/v4/accounts/{params.account_id}/workspaces")
    if resp is None:
        return []
    items = resp.get("data", [])
    return [
        {
            "id": w["id"],
            "name": w.get("name", ""),
            "member_count": w.get("member_count", 0),
        }
        for w in items
    ]


async def frameio_list_projects(
    client: FrameIOClient,
    params: ListProjectsInput,
) -> list[dict[str, Any]]:
    """List projects in a workspace."""
    resp = await client.get(
        f"/v4/accounts/{params.account_id}/workspaces/{params.workspace_id}/projects"
    )
    if resp is None:
        return []
    items = resp.get("data", [])
    return [
        {
            "id": p["id"],
            "name": p.get("name", ""),
            "root_folder_id": p.get("root_folder_id", ""),
            "created_at": p.get("created_at", ""),
        }
        for p in items
    ]
