"""Share tools: create, list, and delete share links."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from frameio_mcp.client import FrameIOClient


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class CreateShareInput(BaseModel):
    account_id: str = Field(..., description="Frame.io account ID")
    asset_ids: list[str] = Field(..., description="List of asset IDs to include in the share")
    access: str = Field(..., description="Access level: 'public', 'password', or 'private'")
    expires_at: Optional[str] = Field(None, description="Expiration datetime (ISO 8601)")
    password: Optional[str] = Field(None, description="Password for password-protected shares")


class ListSharesInput(BaseModel):
    account_id: str = Field(..., description="Frame.io account ID")
    project_id: Optional[str] = Field(None, description="Filter shares by project ID")


class DeleteShareInput(BaseModel):
    account_id: str = Field(..., description="Frame.io account ID")
    share_id: str = Field(..., description="Share ID to delete")
    confirmed: bool = Field(..., description="Must be true to confirm deletion")


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


async def frameio_create_share(
    client: FrameIOClient,
    params: CreateShareInput,
) -> dict[str, Any]:
    """Create a share link for one or more assets."""
    body: dict[str, Any] = {
        "asset_ids": params.asset_ids,
        "access": params.access,
    }
    if params.expires_at is not None:
        body["expires_at"] = params.expires_at
    if params.password is not None:
        body["password"] = params.password

    resp = await client.post(
        f"/v4/accounts/{params.account_id}/shares",
        json_body={"data": body},
    )
    if resp is None:
        return {"error": True, "code": 500, "type": "server_error", "message": "Empty response"}
    data = resp.get("data", resp)
    return {
        "id": data.get("id", ""),
        "url": data.get("url", ""),
        "access": data.get("access", ""),
        "expires_at": data.get("expires_at"),
    }


async def frameio_list_shares(
    client: FrameIOClient,
    params: ListSharesInput,
) -> list[dict[str, Any]]:
    """List share links, optionally filtered by project."""
    request_params: dict[str, Any] = {}
    if params.project_id:
        request_params["project_id"] = params.project_id

    resp = await client.get(
        f"/v4/accounts/{params.account_id}/shares",
        params=request_params,
    )
    if resp is None:
        return []
    items = resp.get("data", [])
    return [
        {
            "id": s["id"],
            "url": s.get("url", ""),
            "access": s.get("access", ""),
            "asset_count": s.get("asset_count", 0),
            "comment_count": s.get("comment_count", 0),
        }
        for s in items
    ]


async def frameio_delete_share(
    client: FrameIOClient,
    params: DeleteShareInput,
) -> dict[str, Any]:
    """Delete a share link. Requires confirmed=True."""
    if not params.confirmed:
        return {
            "deleted": False,
            "message": "Deletion not confirmed. Set confirmed=true to proceed.",
        }
    await client.delete(
        f"/v4/accounts/{params.account_id}/shares/{params.share_id}",
    )
    return {"deleted": True}
