---
name: review-workflow
description: Create share links for Frame.io reviews, set access levels and passwords, track approval status, manage reviewer access, set due dates
---

# Review Workflow

Create and manage review workflows in Frame.io. This skill covers creating share links with configurable access levels, tracking approval status via custom fields, managing reviewer access, and setting review deadlines.

## Prerequisites

- Authenticated Frame.io session (OAuth 2.0 via Adobe IMS)
- Account ID and asset IDs for the files to be reviewed
- Knowledge of the account's custom field definitions (especially approval status fields)

## MCP Tools Used

| Tool | Purpose |
|------|---------|
| `frameio_create_share` | Create a share link for one or more assets |
| `frameio_list_shares` | List existing share links in the account |
| `frameio_delete_share` | Delete a share link (requires explicit confirmation) |
| `frameio_get_custom_fields` | List custom field definitions (to find approval/status fields) |
| `frameio_update_custom_field` | Update a custom field value on a file (e.g., set approval status) |
| `frameio_bulk_update_fields` | Update custom fields across multiple files at once |

---

## Capability 1: Create a Share Link

### Overview

Shares are the V4 replacement for V2 "Review Links" and "Presentation Links." A share bundles one or more assets into a reviewable link that can be sent to internal or external reviewers.

### Step-by-Step

1. **Identify the assets to share.**
   Gather the file IDs for all assets that should be included in the review. Use `frameio_list_folder` or the `project-navigation` skill if the user provides names instead of IDs.

2. **Determine access level.**
   Ask the user which access level to use:
   - `public`: anyone with the link can view (no login required)
   - `password`: requires a password to access
   - `private`: only invited users can access (requires Frame.io login)

   **Safety rule**: never create a `public` share without explicit user approval. Confirm the choice before proceeding.

3. **Configure share options.**
   Collect optional parameters:
   - `title`: a descriptive name for the share (e.g., "Q2 Campaign Review - Round 2")
   - `expires_at`: expiration date/time in ISO 8601 format (e.g., `2026-04-15T00:00:00Z`)
   - For `password` access: the password string

4. **Check for existing shares.**
   Before creating a new share, call `frameio_list_shares` and check if any existing shares already contain the same assets. If found:
   - Inform the user that an existing share covers these assets.
   - Ask if they want to use the existing share or create a new one.
   - This avoids duplicate share links for the same review.

5. **Create the share.**
   Call `frameio_create_share` with:
   - `asset_ids`: array of file IDs
   - `access`: the chosen access level
   - `title`: descriptive title
   - `expires_at`: expiration (if set)
   - `password`: password string (if access is `password`)

6. **Report result to user.**
   Provide:
   - The share URL
   - Access level and any password
   - Expiration date (if set)
   - Number of assets included
   - Instructions for sharing with reviewers

---

## Capability 2: Track Approval Status

### Overview

Frame.io V4 uses custom fields to track approval status. There is no built-in "approval" concept in the API itself; instead, accounts configure custom fields of type `status` or `select` to represent approval states (e.g., "Needs Review", "Approved", "Changes Requested").

### Step-by-Step

1. **Discover approval fields.**
   Call `frameio_get_custom_fields` to list all field definitions. Look for fields with:
   - `type: "status"` or `type: "select"`
   - Names containing keywords like "approval", "status", "review"
   - Note the field `id` and available `options`

   If the user's `frameio.local.md` specifies a default approval field ID, use that.

2. **Read current approval status.**
   For each asset under review, call `frameio_get_file` (via the `asset-management` skill) to read the `custom_fields` object. Extract the value for the approval field ID.

3. **Update approval status.**
   Call `frameio_update_custom_field` with:
   - `file_id`: the asset to update
   - `field_id`: the approval field ID
   - `value`: the new status (must match one of the field's configured options)

   Common status transitions:
   - "Needs Review" -> "In Review" (when share link is created)
   - "In Review" -> "Approved" (when reviewer approves)
   - "In Review" -> "Changes Requested" (when reviewer requests revisions)

4. **Bulk status update.**
   To update approval status on multiple files at once (e.g., marking an entire folder as "In Review"), use `frameio_bulk_update_fields` with the list of file IDs and the field/value pair.

5. **Generate approval summary.**
   For a project-level overview:
   - List all files in the review folder using `frameio_list_folder` (paginate fully).
   - Read the approval field value for each file.
   - Summarize as a table: file name, current status, last updated.
   - Highlight any files still pending review.

---

## Capability 3: Manage Reviewer Access

### Overview

Control who can access review shares and what they can do.

### Step-by-Step

1. **List existing shares.**
   Call `frameio_list_shares` to see all active shares. Each share includes:
   - `id`, `title`, `access` level, `expires_at`
   - `asset_ids`: which files are included

2. **Review share settings.**
   For a specific share, check:
   - Is it still active (not expired)?
   - What access level is set?
   - Are the correct assets included?

3. **Update share access.**
   To change access level or expiration:
   - If a share needs to be more restrictive, consider deleting it and creating a new one with the desired settings.
   - Note: `frameio_delete_share` requires `confirmed: true` and explicit user approval.

4. **Revoke access.**
   To revoke a reviewer's access:
   - Delete the share link via `frameio_delete_share` (with user confirmation).
   - If needed, create a new share excluding the revoked reviewer's assets.

---

## Capability 4: Set Review Due Dates

### Overview

Use share expiration dates and custom date fields to enforce review deadlines.

### Step-by-Step

1. **Set share expiration.**
   When creating a share, set the `expires_at` parameter to the review deadline. After expiration, the share link becomes inaccessible.

2. **Use a custom date field.**
   If the account has a custom field of type `date` for due dates:
   - Find the field ID via `frameio_get_custom_fields`.
   - Set the due date on each file via `frameio_update_custom_field` with the date in ISO 8601 format.

3. **Check overdue reviews.**
   Compare the current date against:
   - Share expiration dates (from `frameio_list_shares`)
   - Custom due date fields on files
   - Report any assets where the due date has passed but approval status is not "Approved."

---

## Capability 5: Generate Review Status Report

### Overview

Produce a summary of the current review state for a project or set of assets.

### Step-by-Step

1. **Gather share data.**
   Call `frameio_list_shares` and filter to shares relevant to the project.

2. **Gather approval data.**
   For each asset in the review:
   - Read the approval custom field value
   - Read comment count (via the `comment-analysis` skill)

3. **Compile the report.**
   Present a structured summary including:
   - **Share links**: title, URL, access level, expiration, number of assets
   - **Approval status breakdown**: count of Approved, Changes Requested, Needs Review, etc.
   - **Comment activity**: total comments per asset, unresolved comment count
   - **Overdue items**: assets past their due date without approval
   - **Reviewer activity**: who has commented, who has not

---

## Error Handling

### Authentication Errors (401)
Token expired or invalid. Trigger token refresh. If refresh fails, prompt user to re-authenticate.

### Permission Errors (403)
The user may not have permission to create shares or modify custom fields. This is common for viewer-level roles. Suggest the user contact their account admin.

### Share Creation Failures
- `400`: missing required fields (asset_ids, access level).
- `422`: invalid asset IDs (files do not exist or are in a different account).
- If asset_ids contains deleted or inaccessible files, identify which ones and report to the user.

### Custom Field Errors
- **Invalid field ID**: the field definition does not exist. Re-check available fields with `frameio_get_custom_fields`.
- **Invalid value**: the value does not match the field's type or options. For `select` and `status` fields, verify the value is one of the configured options.
- **Read-only fields**: some fields may be system-managed and cannot be updated via the API.

### Rate Limiting (429)
Bulk operations (updating many files' custom fields) may trigger rate limits. The MCP server handles backoff automatically. For large batches, expect slower throughput.

### Duplicate Share Prevention
If `frameio_list_shares` returns a share that already covers the same assets:
- Do not create a duplicate without informing the user.
- Present the existing share and ask if they want to reuse it, update it, or create a new one.

### Expired Shares
If a user tries to check the status of an expired share:
- Report that the share has expired and is no longer accessible to reviewers.
- Offer to create a new share with an updated expiration date.
