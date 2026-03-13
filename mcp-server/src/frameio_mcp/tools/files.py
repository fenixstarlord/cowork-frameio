"""File and folder tools: create, list, get, update, delete files and folders."""

from __future__ import annotations

import math
from typing import Any, Optional

from pydantic import BaseModel, Field

from frameio_mcp.client import FrameIOClient


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ListFolderInput(BaseModel):
    account_id: str = Field(..., description="Frame.io account ID")
    folder_id: str = Field(..., description="Folder ID to list children of")
    page_size: int = Field(50, description="Number of items per page (max 100)", ge=1, le=100)
    cursor: Optional[str] = Field(None, description="Pagination cursor for next page")


class CreateFolderInput(BaseModel):
    account_id: str = Field(..., description="Frame.io account ID")
    parent_id: str = Field(..., description="Parent folder ID")
    name: str = Field(..., description="Name for the new folder")


class CreateFileInput(BaseModel):
    account_id: str = Field(..., description="Frame.io account ID")
    parent_id: str = Field(..., description="Parent folder ID")
    name: str = Field(..., description="File name")
    size: int = Field(..., description="File size in bytes", gt=0)
    type: str = Field(..., description="MIME type of the file (e.g. video/mp4)")


class CompleteUploadInput(BaseModel):
    account_id: str = Field(..., description="Frame.io account ID")
    file_id: str = Field(..., description="File ID to mark upload complete")


class GetFileInput(BaseModel):
    account_id: str = Field(..., description="Frame.io account ID")
    file_id: str = Field(..., description="File ID")


class UpdateFileInput(BaseModel):
    account_id: str = Field(..., description="Frame.io account ID")
    file_id: str = Field(..., description="File ID")
    fields: dict[str, Any] = Field(..., description="Fields to update")


class DeleteFileInput(BaseModel):
    account_id: str = Field(..., description="Frame.io account ID")
    file_id: str = Field(..., description="File ID to delete")
    confirmed: bool = Field(..., description="Must be true to confirm deletion")


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


async def frameio_list_folder(
    client: FrameIOClient,
    params: ListFolderInput,
) -> dict[str, Any]:
    """List the contents of a folder with cursor-based pagination."""
    result = await client.paginate(
        f"/v4/accounts/{params.account_id}/folders/{params.folder_id}/children",
        page_size=params.page_size,
        cursor=params.cursor,
    )
    return {
        "items": result["items"],
        "next_cursor": result["next_cursor"],
    }


async def frameio_create_folder(
    client: FrameIOClient,
    params: CreateFolderInput,
) -> dict[str, Any]:
    """Create a new folder inside a parent folder."""
    resp = await client.post(
        f"/v4/accounts/{params.account_id}/folders",
        json_body={"data": {"name": params.name, "parent_id": params.parent_id}},
    )
    if resp is None:
        return {"error": True, "code": 500, "type": "server_error", "message": "Empty response"}
    data = resp.get("data", resp)
    return {
        "id": data.get("id", ""),
        "name": data.get("name", ""),
        "created_at": data.get("created_at", ""),
    }


async def frameio_create_file(
    client: FrameIOClient,
    params: CreateFileInput,
) -> dict[str, Any]:
    """Create a file record and get presigned upload URLs.

    Returns the file ID, upload URLs, and computed chunk size.
    """
    resp = await client.post(
        f"/v4/accounts/{params.account_id}/files",
        json_body={
            "data": {
                "name": params.name,
                "file_size": params.size,
                "parent_id": params.parent_id,
            }
        },
    )
    if resp is None:
        return {"error": True, "code": 500, "type": "server_error", "message": "Empty response"}
    data = resp.get("data", resp)
    upload_urls = data.get("upload_urls", [])
    chunk_size = math.ceil(params.size / max(len(upload_urls), 1))
    return {
        "id": data.get("id", ""),
        "upload_urls": upload_urls,
        "chunk_size": chunk_size,
    }


async def frameio_complete_upload(
    client: FrameIOClient,
    params: CompleteUploadInput,
) -> dict[str, Any]:
    """Mark a file upload as complete and trigger transcoding."""
    resp = await client.get(
        f"/v4/accounts/{params.account_id}/files/{params.file_id}",
    )
    if resp is None:
        return {"error": True, "code": 500, "type": "server_error", "message": "Empty response"}
    data = resp.get("data", resp)
    return {
        "id": data.get("id", ""),
        "status": data.get("status", ""),
        "proxies": {"status": data.get("proxies", {}).get("status", "pending")},
    }


async def frameio_get_file(
    client: FrameIOClient,
    params: GetFileInput,
) -> dict[str, Any]:
    """Get full metadata for a file."""
    resp = await client.get(
        f"/v4/accounts/{params.account_id}/files/{params.file_id}",
    )
    if resp is None:
        return {"error": True, "code": 500, "type": "server_error", "message": "Empty response"}
    return resp.get("data", resp)


async def frameio_update_file(
    client: FrameIOClient,
    params: UpdateFileInput,
) -> dict[str, Any]:
    """Update file metadata fields."""
    resp = await client.patch(
        f"/v4/accounts/{params.account_id}/files/{params.file_id}",
        json_body={"data": params.fields},
    )
    if resp is None:
        return {"error": True, "code": 500, "type": "server_error", "message": "Empty response"}
    return resp.get("data", resp)


async def frameio_delete_file(
    client: FrameIOClient,
    params: DeleteFileInput,
) -> dict[str, Any]:
    """Delete a file. Requires confirmed=True."""
    if not params.confirmed:
        return {
            "deleted": False,
            "message": "Deletion not confirmed. Set confirmed=true to proceed.",
        }
    await client.delete(
        f"/v4/accounts/{params.account_id}/files/{params.file_id}",
    )
    return {"deleted": True}
