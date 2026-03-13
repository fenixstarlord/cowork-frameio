"""Comment tools: list, create, and resolve comments."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from frameio_mcp.client import FrameIOClient


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ListCommentsInput(BaseModel):
    account_id: str = Field(..., description="Frame.io account ID")
    asset_id: str = Field(..., description="Asset (file) ID to list comments for")
    page_size: int = Field(50, description="Number of comments per page (max 100)", ge=1, le=100)
    cursor: Optional[str] = Field(None, description="Pagination cursor for next page")


class CreateCommentInput(BaseModel):
    account_id: str = Field(..., description="Frame.io account ID")
    asset_id: str = Field(..., description="Asset (file) ID to comment on")
    text: str = Field(..., description="Comment text")
    timecode: Optional[str] = Field(None, description="Timecode to anchor the comment (e.g. '00:01:23:15')")
    annotation: Optional[str] = Field(None, description="Annotation data (drawing/region JSON)")


class ResolveCommentInput(BaseModel):
    account_id: str = Field(..., description="Frame.io account ID")
    comment_id: str = Field(..., description="Comment ID to resolve")


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


async def frameio_list_comments(
    client: FrameIOClient,
    params: ListCommentsInput,
) -> dict[str, Any]:
    """List comments on an asset with cursor-based pagination."""
    result = await client.paginate(
        f"/v4/accounts/{params.account_id}/comments",
        params={"asset_id": params.asset_id},
        page_size=params.page_size,
        cursor=params.cursor,
    )
    return {
        "comments": result["items"],
        "next_cursor": result["next_cursor"],
    }


async def frameio_create_comment(
    client: FrameIOClient,
    params: CreateCommentInput,
) -> dict[str, Any]:
    """Create a comment on an asset, optionally anchored to a timecode."""
    body: dict[str, Any] = {
        "asset_id": params.asset_id,
        "text": params.text,
    }
    if params.timecode is not None:
        body["timecode"] = params.timecode
    if params.annotation is not None:
        body["annotation"] = params.annotation

    resp = await client.post(
        f"/v4/accounts/{params.account_id}/comments",
        json_body={"data": body},
    )
    if resp is None:
        return {"error": True, "code": 500, "type": "server_error", "message": "Empty response"}
    data = resp.get("data", resp)
    return {
        "id": data.get("id", ""),
        "text": data.get("text", ""),
        "timecode": data.get("timecode"),
        "created_at": data.get("created_at", ""),
    }


async def frameio_resolve_comment(
    client: FrameIOClient,
    params: ResolveCommentInput,
) -> dict[str, Any]:
    """Mark a comment as resolved."""
    resp = await client.patch(
        f"/v4/accounts/{params.account_id}/comments/{params.comment_id}",
        json_body={"data": {"resolved": True}},
    )
    if resp is None:
        return {"error": True, "code": 500, "type": "server_error", "message": "Empty response"}
    data = resp.get("data", resp)
    return {
        "id": data.get("id", ""),
        "resolved": data.get("resolved", True),
    }
