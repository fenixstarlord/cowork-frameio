"""MCP server entrypoint. Registers all Frame.io tools and runs via stdio."""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from frameio_mcp.auth import AuthManager
from frameio_mcp.client import FrameIOClient
from frameio_mcp.utils.errors import FrameIOError

# Tool functions and input models
from frameio_mcp.tools.account import (
    WhoAmIInput,
    ListWorkspacesInput,
    ListProjectsInput,
    frameio_whoami,
    frameio_list_workspaces,
    frameio_list_projects,
)
from frameio_mcp.tools.files import (
    ListFolderInput,
    CreateFolderInput,
    CreateFileInput,
    CompleteUploadInput,
    GetFileInput,
    UpdateFileInput,
    DeleteFileInput,
    frameio_list_folder,
    frameio_create_folder,
    frameio_create_file,
    frameio_complete_upload,
    frameio_get_file,
    frameio_update_file,
    frameio_delete_file,
)
from frameio_mcp.tools.comments import (
    ListCommentsInput,
    CreateCommentInput,
    ResolveCommentInput,
    frameio_list_comments,
    frameio_create_comment,
    frameio_resolve_comment,
)
from frameio_mcp.tools.shares import (
    CreateShareInput,
    ListSharesInput,
    DeleteShareInput,
    frameio_create_share,
    frameio_list_shares,
    frameio_delete_share,
)
from frameio_mcp.tools.metadata import (
    ListCollectionsInput,
    GetCustomFieldsInput,
    UpdateCustomFieldInput,
    BulkUpdateFieldsInput,
    frameio_list_collections,
    frameio_get_custom_fields,
    frameio_update_custom_field,
    frameio_bulk_update_fields,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool registry: maps tool name → (description, InputModel, handler)
# ---------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, tuple[str, type | None, Any]] = {
    "frameio_whoami": (
        "Get the current authenticated Frame.io user and their accounts.",
        None,
        frameio_whoami,
    ),
    "frameio_list_workspaces": (
        "List all workspaces in a Frame.io account.",
        ListWorkspacesInput,
        frameio_list_workspaces,
    ),
    "frameio_list_projects": (
        "List projects in a Frame.io workspace.",
        ListProjectsInput,
        frameio_list_projects,
    ),
    "frameio_list_folder": (
        "List the contents of a folder with pagination.",
        ListFolderInput,
        frameio_list_folder,
    ),
    "frameio_create_folder": (
        "Create a new folder inside a parent folder.",
        CreateFolderInput,
        frameio_create_folder,
    ),
    "frameio_create_file": (
        "Create a file record and get presigned upload URLs.",
        CreateFileInput,
        frameio_create_file,
    ),
    "frameio_complete_upload": (
        "Mark a file upload as complete and trigger transcoding.",
        CompleteUploadInput,
        frameio_complete_upload,
    ),
    "frameio_get_file": (
        "Get full metadata for a file.",
        GetFileInput,
        frameio_get_file,
    ),
    "frameio_update_file": (
        "Update file metadata fields.",
        UpdateFileInput,
        frameio_update_file,
    ),
    "frameio_delete_file": (
        "Delete a file. Requires explicit confirmation.",
        DeleteFileInput,
        frameio_delete_file,
    ),
    "frameio_list_comments": (
        "List comments on an asset with pagination.",
        ListCommentsInput,
        frameio_list_comments,
    ),
    "frameio_create_comment": (
        "Create a comment on an asset, optionally at a timecode.",
        CreateCommentInput,
        frameio_create_comment,
    ),
    "frameio_resolve_comment": (
        "Mark a comment as resolved.",
        ResolveCommentInput,
        frameio_resolve_comment,
    ),
    "frameio_create_share": (
        "Create a share link for one or more assets.",
        CreateShareInput,
        frameio_create_share,
    ),
    "frameio_list_shares": (
        "List share links, optionally filtered by project.",
        ListSharesInput,
        frameio_list_shares,
    ),
    "frameio_delete_share": (
        "Delete a share link. Requires explicit confirmation.",
        DeleteShareInput,
        frameio_delete_share,
    ),
    "frameio_list_collections": (
        "List collections (smart folders) in a project.",
        ListCollectionsInput,
        frameio_list_collections,
    ),
    "frameio_get_custom_fields": (
        "List custom field definitions for a project.",
        GetCustomFieldsInput,
        frameio_get_custom_fields,
    ),
    "frameio_update_custom_field": (
        "Update a custom field value on a file.",
        UpdateCustomFieldInput,
        frameio_update_custom_field,
    ),
    "frameio_bulk_update_fields": (
        "Update a custom field on multiple files.",
        BulkUpdateFieldsInput,
        frameio_bulk_update_fields,
    ),
}


def _build_tool_list() -> list[Tool]:
    """Build the MCP Tool objects from the registry."""
    tools: list[Tool] = []
    for name, (description, model_cls, _handler) in TOOL_REGISTRY.items():
        if model_cls is not None:
            schema = model_cls.model_json_schema()
        else:
            schema = {"type": "object", "properties": {}}
        tools.append(
            Tool(
                name=name,
                description=description,
                inputSchema=schema,
            )
        )
    return tools


async def _handle_tool_call(
    client: FrameIOClient,
    name: str,
    arguments: dict[str, Any],
) -> str:
    """Dispatch a tool call to the appropriate handler."""
    entry = TOOL_REGISTRY.get(name)
    if entry is None:
        return json.dumps({"error": True, "code": 404, "type": "not_found", "message": f"Unknown tool: {name}"})

    _desc, model_cls, handler = entry

    try:
        if model_cls is not None:
            params = model_cls(**arguments)
            result = await handler(client, params)
        else:
            result = await handler(client)
        return json.dumps(result, default=str)
    except FrameIOError as exc:
        return json.dumps(exc.to_dict())
    except Exception as exc:
        logger.exception("Unexpected error in tool %s", name)
        return json.dumps({
            "error": True,
            "code": 500,
            "type": "server_error",
            "message": str(exc),
        })


async def run_server() -> None:
    """Start the MCP server on stdio."""
    server = Server("frameio")
    auth = AuthManager()
    client = FrameIOClient(auth)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return _build_tool_list()

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        result_json = await _handle_tool_call(client, name, arguments)
        return [TextContent(type="text", text=result_json)]

    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    finally:
        await client.close()


def main() -> None:
    """Entry point for ``python -m frameio_mcp.server``."""
    import asyncio
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
