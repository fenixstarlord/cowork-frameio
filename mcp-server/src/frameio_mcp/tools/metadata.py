"""Metadata tools: collections, custom fields, bulk updates."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from frameio_mcp.client import FrameIOClient


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ListCollectionsInput(BaseModel):
    account_id: str = Field(..., description="Frame.io account ID")
    project_id: str = Field(..., description="Project ID")


class GetCustomFieldsInput(BaseModel):
    account_id: str = Field(..., description="Frame.io account ID")
    project_id: str = Field(..., description="Project ID")


class UpdateCustomFieldInput(BaseModel):
    account_id: str = Field(..., description="Frame.io account ID")
    file_id: str = Field(..., description="File ID to update")
    field_id: str = Field(..., description="Custom field definition ID")
    value: Any = Field(..., description="New value for the field")


class BulkUpdateFieldsInput(BaseModel):
    account_id: str = Field(..., description="Frame.io account ID")
    file_ids: list[str] = Field(..., description="List of file IDs to update")
    field_id: str = Field(..., description="Custom field definition ID")
    value: Any = Field(..., description="New value for the field")


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


async def frameio_list_collections(
    client: FrameIOClient,
    params: ListCollectionsInput,
) -> list[dict[str, Any]]:
    """List collections (smart folders) in a project."""
    resp = await client.get(
        f"/v4/accounts/{params.account_id}/collections",
        params={"project_id": params.project_id},
    )
    if resp is None:
        return []
    items = resp.get("data", [])
    return [
        {
            "id": c["id"],
            "name": c.get("name", ""),
            "asset_count": c.get("asset_count", 0),
            "filter_criteria": c.get("filter_criteria", {}),
        }
        for c in items
    ]


async def frameio_get_custom_fields(
    client: FrameIOClient,
    params: GetCustomFieldsInput,
) -> list[dict[str, Any]]:
    """List custom field definitions for a project."""
    resp = await client.get(
        f"/v4/accounts/{params.account_id}/projects/{params.project_id}/field_definitions",
    )
    if resp is None:
        return []
    items = resp.get("data", [])
    return [
        {
            "id": f["id"],
            "name": f.get("name", ""),
            "type": f.get("type", ""),
            "allowed_values": f.get("allowed_values", []),
        }
        for f in items
    ]


async def frameio_update_custom_field(
    client: FrameIOClient,
    params: UpdateCustomFieldInput,
) -> dict[str, Any]:
    """Update a custom field value on a file."""
    resp = await client.patch(
        f"/v4/accounts/{params.account_id}/files/{params.file_id}",
        json_body={"data": {"custom_fields": {params.field_id: params.value}}},
    )
    if resp is None:
        return {"error": True, "code": 500, "type": "server_error", "message": "Empty response"}
    data = resp.get("data", resp)
    custom_fields = data.get("custom_fields", {})
    return {
        "file_id": params.file_id,
        "field_id": params.field_id,
        "value": custom_fields.get(params.field_id, params.value),
    }


async def frameio_bulk_update_fields(
    client: FrameIOClient,
    params: BulkUpdateFieldsInput,
) -> dict[str, Any]:
    """Update a custom field on multiple files. Returns success/failure counts."""
    updated_count = 0
    failed: list[dict[str, Any]] = []

    for file_id in params.file_ids:
        try:
            await client.patch(
                f"/v4/accounts/{params.account_id}/files/{file_id}",
                json_body={"data": {"custom_fields": {params.field_id: params.value}}},
            )
            updated_count += 1
        except Exception as exc:
            failed.append({"id": file_id, "error": str(exc)})

    return {
        "updated_count": updated_count,
        "failed": failed,
    }
