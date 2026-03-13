"""Frame.io MCP tool modules."""

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

__all__ = [
    # Account
    "WhoAmIInput",
    "ListWorkspacesInput",
    "ListProjectsInput",
    "frameio_whoami",
    "frameio_list_workspaces",
    "frameio_list_projects",
    # Files
    "ListFolderInput",
    "CreateFolderInput",
    "CreateFileInput",
    "CompleteUploadInput",
    "GetFileInput",
    "UpdateFileInput",
    "DeleteFileInput",
    "frameio_list_folder",
    "frameio_create_folder",
    "frameio_create_file",
    "frameio_complete_upload",
    "frameio_get_file",
    "frameio_update_file",
    "frameio_delete_file",
    # Comments
    "ListCommentsInput",
    "CreateCommentInput",
    "ResolveCommentInput",
    "frameio_list_comments",
    "frameio_create_comment",
    "frameio_resolve_comment",
    # Shares
    "CreateShareInput",
    "ListSharesInput",
    "DeleteShareInput",
    "frameio_create_share",
    "frameio_list_shares",
    "frameio_delete_share",
    # Metadata
    "ListCollectionsInput",
    "GetCustomFieldsInput",
    "UpdateCustomFieldInput",
    "BulkUpdateFieldsInput",
    "frameio_list_collections",
    "frameio_get_custom_fields",
    "frameio_update_custom_field",
    "frameio_bulk_update_fields",
]
