---
description: "Upload a file or folder of renders to Frame.io. Validates the local file, selects a destination project and folder, uploads via the V4 API, and confirms success."
---

# /frameio:upload-asset

Upload a local file (or folder of files) to a Frame.io project folder.

## Inputs

| Input | Source | Required | Description |
|-------|--------|----------|-------------|
| File path | User prompt or argument | Yes | Absolute or relative path to a local file or directory. If a directory is given, all supported media files within it are queued for upload. |
| Project | User prompt or `frameio.local.md` default | Yes | The target Frame.io project. If `default_project_id` is set in `frameio.local.md`, offer it as the default. |
| Destination folder | User prompt | No | Folder within the project. Defaults to the project root folder. User may specify by name or path (e.g., `Dailies/2026-03-12`). |
| Description | User prompt | No | Optional description to attach to the uploaded asset. |

If the user does not supply a file path, prompt for one. If the user does not specify a project, list available projects via `frameio_list_projects` and ask them to choose.

## Workflow

1. **Validate local file.**
   - Confirm the path exists on disk.
   - If it is a directory, enumerate all files inside it (non-recursively by default; ask user before recursing).
   - Compute each file's size in bytes and MIME type.
   - Reject zero-byte files with a clear error message.

2. **Authenticate.**
   - Call `frameio_whoami` to verify the current session is valid. If it fails, see **Auth Handling** below.

3. **Resolve destination.**
   - If no project was specified, call `frameio_list_projects` using the account ID from `frameio.local.md` (or the account returned by `frameio_whoami`) and present a numbered list for the user to pick.
   - Once the project is selected, call `frameio_list_folder` on the project's `root_folder_id` to show top-level folders.
   - If the user specified a folder name or path, navigate into it. Create intermediate folders with `frameio_create_folder` if the user confirms.

4. **Create the file asset.**
   - Call `frameio_create_file` with `name`, `size`, `media_type`, and the target `folder_id`.
   - The response includes the `asset_id` and an array of presigned upload URLs.

5. **Upload file data.**
   - **If file size <= 5 GB:** Upload directly within this command.
     - Split the file into chunks matching the presigned URL count.
     - PUT each chunk to its corresponding presigned S3 URL with headers `Content-Type: {media_type}` and `x-amz-acl: private`.
     - Retry failed chunks up to 3 times with exponential backoff.
     - After all chunks succeed, call `frameio_complete_upload` with the `asset_id`.
   - **If file size > 5 GB:** Delegate to the **upload-agent** sub-agent.
     - Pass: `file_path`, `asset_id`, `presigned_urls`, `media_type`, `file_size`.
     - The upload-agent handles parallel chunking, checkpointing (`.frameio-upload-state.json`), and resume-on-failure.
     - Wait for the upload-agent to report completion, then call `frameio_complete_upload`.

6. **Set optional metadata.**
   - If the user provided a description, call `frameio_update_file` to set it on the asset.

7. **Confirm success.**
   - Call `frameio_get_file` to verify the asset status is `active` or `processing`.
   - Report the asset name, ID, file size, and a direct link if available.

8. **Batch handling (directory upload).**
   - If multiple files were queued, repeat steps 4-7 for each file.
   - Present a summary table when all uploads finish: file name, size, status, asset ID.
   - Report any failures separately with error details.

## Expected Output

**Single file:**
```
Uploaded "hero_v3.mp4" (1.2 GB) to Acme Project / Dailies / 2026-03-12
Asset ID: abc123-def456
Status: processing
```

**Multiple files (directory):**
```
Upload complete — 4 of 4 files succeeded.

| File               | Size   | Status     | Asset ID         |
|--------------------|--------|------------|------------------|
| hero_v3.mp4        | 1.2 GB | processing | abc123-def456    |
| cutdown_30s.mp4    | 340 MB | active     | ghi789-jkl012    |
| poster.png         | 8.4 MB | active     | mno345-pqr678    |
| subtitles.srt      | 12 KB  | active     | stu901-vwx234    |
```

**Failure case:**
```
Upload failed for "corrupted.mov": S3 returned 403 Forbidden after 3 retries.
The remaining 3 files uploaded successfully.
```

## Auth Handling

- Before any API call, verify authentication by calling `frameio_whoami`.
- If the call returns an authentication error (401 or token-missing):
  1. Inform the user: "You are not authenticated with Frame.io. Starting OAuth login..."
  2. The MCP server's auth module will initiate the Adobe IMS OAuth 2.0 device-code or authorization-code flow.
  3. Guide the user through any required browser-based steps.
  4. Once tokens are obtained, retry `frameio_whoami` to confirm success.
- If token refresh fails, surface the error clearly and ask the user to re-authenticate.

## Delegation

| Condition | Delegate To | Reason |
|-----------|-------------|--------|
| File size > 5 GB | **upload-agent** | Large files need parallel chunked uploads with checkpoint/resume logic to handle network interruptions reliably. |
| Directory with > 20 files | **upload-agent** | Batch uploads benefit from the agent's concurrency management and progress tracking. |

For files <= 5 GB, this command handles the upload directly without sub-agent delegation.
