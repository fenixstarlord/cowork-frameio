---
name: asset-management
description: Upload files to Frame.io, organize folders, manage version stacks, update metadata and custom fields, download assets
---

# Asset Management

Manage files and folders in Frame.io. This skill covers uploading assets (including multi-part chunked uploads for large files), organizing content into folders, working with version stacks, reading and updating metadata and custom fields, and downloading files.

## Prerequisites

- Authenticated Frame.io session (OAuth 2.0 via Adobe IMS)
- Account ID and target project/folder IDs (use the `project-navigation` skill if unknown)
- For uploads: local file path and knowledge of the target folder

## MCP Tools Used

| Tool | Purpose |
|------|---------|
| `frameio_create_file` | Create a file record and obtain presigned upload URLs |
| `frameio_complete_upload` | Signal upload completion (for resumed/checkpoint uploads) |
| `frameio_list_folder` | List contents of a folder (files, subfolders, version stacks) |
| `frameio_create_folder` | Create a new folder |
| `frameio_get_file` | Get file details including status, media links, custom fields |
| `frameio_update_file` | Update file name, description, or custom field values |
| `frameio_delete_file` | Delete a file (requires explicit confirmation) |

---

## Capability 1: Upload a File

### Overview

Uploading a file to Frame.io is a multi-step process. You create a file record via the API, receive presigned S3 URLs, then upload binary chunks to those URLs. The file auto-processes (generates proxies, thumbnails) once all chunks arrive.

### Upload Size Tiers

| File Size | Strategy | Chunk Size | Concurrency |
|-----------|----------|------------|-------------|
| < 5 GB | Single-part upload | Equal split across URLs | Sequential |
| 5 - 50 GB | Multi-part chunked | ~256 MB | 4-8 concurrent |
| > 50 GB | Multi-part with checkpoint/resume | ~256 MB | 4-8 concurrent |

### Step-by-Step

1. **Validate the local file exists.** Confirm the file path is accessible and read the file size. Determine the media type from the file extension (e.g., `.mov` -> `video/quicktime`, `.mp4` -> `video/mp4`, `.jpg` -> `image/jpeg`).

2. **Identify the target folder.** The user must specify or confirm a `parent_id` (folder ID). If unknown, use `frameio_list_folder` or the `project-navigation` skill to browse the project tree.

3. **Create the file record.**
   Call `frameio_create_file` with:
   - `name`: the file name (e.g., `hero_cut_v3.mov`)
   - `file_size`: size in bytes
   - `parent_id`: the target folder ID

   The response includes:
   - `id`: the new file's ID
   - `upload_urls`: an array of presigned S3 PUT URLs
   - `status`: should be `"created"`

4. **Calculate chunk boundaries.**
   ```
   chunk_size = ceil(file_size / len(upload_urls))
   ```
   Each URL corresponds to one chunk, in order. The last chunk may be smaller.

5. **Upload each chunk.**
   For each `upload_urls[i]`:
   - Read `chunk_size` bytes from offset `i * chunk_size`
   - Send a `PUT` request to the presigned URL
   - Required headers:
     - `Content-Type: {media_type}` (must match the actual file type)
     - `x-amz-acl: private`
   - Body: raw binary chunk data
   - Chunks MUST match the order of `upload_urls` (1st URL = 1st chunk of file)

6. **Handle chunk failures.**
   - If a PUT fails, retry the same URL. Presigned URLs can be reused.
   - Use exponential backoff: 1s, 2s, 4s, 8s, up to 30s max.
   - S3 errors are returned as **XML, not JSON**. Parse the `<Code>` and `<Message>` elements.
   - Presigned URLs expire after **24 hours**. If expired, you must create a new file record.

7. **For files > 50 GB: use checkpoint/resume.**
   - Before starting, check for an existing `.frameio-upload-state.json` in the working directory.
   - The state file tracks: `file_id`, `file_path`, `upload_urls`, `completed_chunks` (list of indices), `started_at`.
   - After each successful chunk, update the state file.
   - On resume, skip chunks already in `completed_chunks`.
   - Delete the state file after all chunks succeed.
   - For files > 5 GB, delegate to the `upload-agent` sub-agent for parallel chunked upload.

8. **Confirm upload completion.**
   After all chunks are uploaded, the file auto-processes. Call `frameio_get_file` to verify:
   - `status` transitions from `"created"` -> `"uploading"` -> `"processing"` -> `"complete"`
   - Once `"complete"`, proxies and thumbnails are available.

9. **Report result to user.**
   Provide: file name, file ID, status, and the `view_url` for browser access.

### Remote Upload (URL-based)

If the source file is accessible via a public URL (e.g., cloud storage), you can skip the chunked upload entirely:

1. Call `frameio_create_file` with `name`, `source_url`, and `parent_id` (omit `file_size`).
2. Frame.io will fetch the file server-side.
3. Monitor status via `frameio_get_file` until processing completes.

---

## Capability 2: Organize Folders

### Overview

Create folder hierarchies to keep project assets organized. Frame.io folders mirror a traditional file system within each project.

### Step-by-Step

1. **List current folder contents.**
   Call `frameio_list_folder` with the `folder_id`. This returns all children: files, subfolders, and version stacks. Each item includes `type` ("file", "folder", or "version_stack"), `name`, `id`, and `created_at`.

2. **Create a new folder.**
   Call `frameio_create_folder` with:
   - `name`: the folder name
   - `parent_id`: the parent folder ID (use the project's `root_folder_id` for top-level)

3. **Nested folder creation.**
   To create a path like `Dailies/Day 03/Camera A`:
   - Create `Dailies` under the root -> get its ID
   - Create `Day 03` under `Dailies` -> get its ID
   - Create `Camera A` under `Day 03`
   - Always check if intermediate folders already exist before creating duplicates.

4. **Move files between folders.**
   Call `frameio_update_file` with the file ID and a new `parent_id` to move a file into a different folder.

### Pagination for Large Folders

Folders with many children are paginated. When `frameio_list_folder` returns results:
- Check if there are more pages (the tool handles cursor-based pagination internally).
- For folders with 10,000+ items, collect all pages before presenting results.
- Default page size is 50, max is 100.

---

## Capability 3: Version Stacks

### Overview

Version stacks group multiple versions of the same asset (v1, v2, v3...) into a single logical unit. In V4, version stacks are **read-only** (create/update endpoints are coming soon).

### Step-by-Step

1. **Identify version stacks.**
   When listing folder contents with `frameio_list_folder`, items with `type: "version_stack"` are version stacks.

2. **View versions in a stack.**
   Call `frameio_get_file` with the version stack ID to see stack metadata. The children of a version stack are the individual file versions, ordered by version number.

3. **Upload a new version.**
   Until V4 adds version stack management endpoints, upload a new file to the same folder with a naming convention that indicates the version (e.g., `hero_cut_v4.mov`). Inform the user that automatic version stacking is not yet available via the API.

---

## Capability 4: Metadata and Custom Fields

### Overview

Frame.io V4 supports custom fields on files. Field definitions are configured at the account or project level. Values are set per-file. Common field types: `select`, `multi_select`, `text`, `number`, `date`, `rating`, `status`, `user`, `url`.

### Step-by-Step

1. **Read current metadata.**
   Call `frameio_get_file` with the file ID. The response includes a `custom_fields` object mapping field IDs to their current values.

2. **Update a single custom field.**
   Call `frameio_update_file` with:
   - `file_id`: the target file
   - `custom_fields`: an object mapping `{field_id: new_value}`

   Example: setting an approval status field:
   ```json
   { "custom_fields": { "cf_abc123": "Approved" } }
   ```

3. **Update multiple fields at once.**
   Include multiple field ID/value pairs in the same `custom_fields` object.

4. **Understand field types.**
   - `select`: provide the exact option string
   - `multi_select`: provide an array of option strings
   - `date`: use ISO 8601 format (`2026-04-15T00:00:00Z`)
   - `rating`: integer value within the defined range
   - `status`: one of the configured status options
   - `user`: a valid user ID
   - `url`: a valid URL string

5. **Check field definitions.**
   If unsure what fields are available or what values are valid, use `frameio_get_custom_fields` to list field definitions for the account or project. Each definition includes `id`, `name`, `type`, and `options` (for select/multi_select).

---

## Capability 5: Download and Access Files

### Overview

Retrieve download URLs and media links for files stored in Frame.io.

### Step-by-Step

1. **Get file details.**
   Call `frameio_get_file` with the file ID and request media link includes.

2. **Available media links.**
   The response may include:
   - `original`: full-resolution source file download URL
   - `thumbnail`: static thumbnail image
   - `high_quality`: high-quality proxy (for video files)

3. **Present links to user.**
   Provide the appropriate URL based on what the user needs. Note that media link URLs are **temporary** (signed URLs with expiration). Do not cache them long-term.

---

## Capability 6: Delete Files

### Overview

Permanently remove files from Frame.io. This is a destructive operation.

### Step-by-Step

1. **Always confirm with the user before deleting.** The `frameio_delete_file` tool requires a `confirmed: bool` parameter. Never set this to `true` without explicit user approval.

2. **Single file deletion.**
   Call `frameio_delete_file` with the `file_id` and `confirmed: true` (after user confirms).

3. **Bulk deletion.**
   If the user wants to delete multiple files:
   - List the files to be deleted with names and IDs.
   - Present the full list to the user for review.
   - If more than 50 files, warn the user about the scope before proceeding.
   - Delete one at a time, reporting progress.

4. **Deletion is permanent.** Frame.io V4 does not have a trash/recycle bin via the API. Make this clear to the user.

---

## Error Handling

### Authentication Errors (401)
Token is missing, expired, or invalid. Trigger a token refresh. If refresh fails, prompt the user to re-authenticate via the OAuth flow.

### Permission Errors (403)
The user lacks permission to access or modify the resource. Report the specific resource and suggest the user check their role in the Frame.io account settings.

### Not Found (404)
The file, folder, or project ID does not exist or has been deleted. Verify the ID is correct. If the user provided a name instead of an ID, use `frameio_list_folder` or `project-navigation` to look it up.

### Rate Limiting (429)
The API rate limit has been exceeded. The MCP server handles backoff automatically, but if you see repeated 429s:
- Reduce request frequency
- Avoid unnecessary polling
- Batch operations where possible

### S3 Upload Errors (XML)
During chunk uploads, S3 returns errors as XML, not JSON. Common errors:
- `AccessDenied`: presigned URL expired or malformed. Create a new file record to get fresh URLs.
- `RequestTimeout`: the upload took too long. Retry the chunk.
- `SlowDown`: S3 throttling. Apply exponential backoff.
- `InternalError`: S3 server issue. Retry after a short delay.

### Upload State Recovery
If an upload is interrupted (network failure, process crash):
1. Check for `.frameio-upload-state.json` in the working directory.
2. If found, verify the file ID still exists via `frameio_get_file`.
3. Resume from the last completed chunk.
4. If the file record no longer exists or URLs have expired (>24h), start fresh.

### File Processing Failures
After upload, if `frameio_get_file` shows `status: "error"`:
- The file may be corrupt or in an unsupported format.
- Report the error to the user.
- Suggest re-uploading or checking the source file.

### Validation Errors (400/422)
- `400`: malformed request (missing required fields, invalid JSON).
- `422`: valid syntax but invalid values (e.g., parent_id does not exist, file_size is negative).
- Report the specific error detail from the API response to help the user correct the issue.
