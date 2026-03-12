---
description: "Check the status of reviews on a Frame.io project. Shows share links, comment counts, and approval statuses in a summary table."
---

# /frameio:review-status

Get a quick overview of all active reviews in a Frame.io project, including share links, comment activity, and approval status.

## Inputs

| Input | Source | Required | Description |
|-------|--------|----------|-------------|
| Project | User prompt or `frameio.local.md` default | Yes | The Frame.io project to check. If `default_project_id` is set in `frameio.local.md`, use it automatically. Otherwise, prompt the user. |
| Filter | User prompt | No | Optional filter: `active` (default), `expired`, or `all` share links. |

If no project is specified and no default is configured, list available projects via `frameio_list_projects` and ask the user to choose.

## Workflow

1. **Authenticate.**
   - Call `frameio_whoami` to verify the session is valid. Handle auth failure per **Auth Handling** below.

2. **Resolve the project.**
   - If the user provided a project name (not an ID), call `frameio_list_projects` and match by name (case-insensitive). If ambiguous, present options.
   - Store the `project_id` and `root_folder_id`.

3. **Fetch all share links.**
   - Call `frameio_list_shares` for the project.
   - Paginate fully — follow `links.next` until all shares are retrieved.
   - Apply the user's filter (active / expired / all). Default to active only.

4. **For each share link, gather asset details.**
   - For each share, extract the list of asset IDs it covers.
   - Call `frameio_get_file` for each unique asset to get the asset name and current status.
   - Call `frameio_list_comments` for each asset to get the total comment count and count of unresolved comments.

5. **Fetch approval status.**
   - Call `frameio_get_custom_fields` on each asset to check for approval-related fields (e.g., `status`, `approval_status`).
   - Map values to human-readable labels: `approved`, `needs_changes`, `pending`, `none`.

6. **Compile the summary.**
   - Group results by share link.
   - For each share: link URL, creation date, expiration, access level, and a sub-table of assets with their comment counts and approval status.
   - Calculate totals: total shares, total assets under review, total comments, assets approved vs. pending.

7. **Present the report.**
   - Output the summary table(s) and headline stats.

## Expected Output

```
Review Status for "Acme Campaign Q1"
=====================================

3 active share links | 7 assets under review | 42 total comments | 3 approved, 4 pending

Share: "Client Review - March"
  URL: https://app.frame.io/reviews/abc123
  Access: Password-protected | Expires: 2026-03-20
  Created: 2026-03-05

  | Asset              | Comments | Unresolved | Approval     |
  |--------------------|----------|------------|--------------|
  | hero_v3.mp4        | 12       | 3          | needs_changes|
  | cutdown_30s.mp4    | 8        | 0          | approved     |
  | poster.png         | 5        | 2          | pending      |

Share: "Internal Review"
  URL: https://app.frame.io/reviews/def456
  Access: Private (email-only) | No expiration
  Created: 2026-03-01

  | Asset              | Comments | Unresolved | Approval     |
  |--------------------|----------|------------|--------------|
  | hero_v2.mp4        | 14       | 0          | approved     |
  | hero_v3.mp4        | 3        | 1          | pending      |
```

If no share links are found:
```
No active share links found for "Acme Campaign Q1".
Use /frameio:create-share to create a review link.
```

## Auth Handling

- Before any API call, verify authentication by calling `frameio_whoami`.
- If the call returns an authentication error (401 or token-missing):
  1. Inform the user: "You are not authenticated with Frame.io. Starting OAuth login..."
  2. The MCP server's auth module will initiate the Adobe IMS OAuth 2.0 flow.
  3. Guide the user through any required browser-based steps.
  4. Once tokens are obtained, retry the original request.
- If token refresh fails, surface the error and ask the user to re-authenticate.

## Delegation

| Condition | Delegate To | Reason |
|-----------|-------------|--------|
| Deep approval analysis or custom criteria | **review-coordinator** | When the user wants to evaluate approval status against custom criteria defined in `frameio.local.md`, the review-coordinator agent applies the rules and generates a richer report. |

For standard status checks, this command handles everything directly. The review-coordinator is only invoked if the user requests detailed approval analysis or tracking against custom approval criteria.
