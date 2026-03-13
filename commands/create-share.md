---
description: "Create a share or review link for Frame.io assets. Configure access level, expiration, and password protection, then return the shareable URL."
disable-model-invocation: true
argument-hint: "[asset-name-or-id]"
---

# /frameio:create-share

Create a share link (review link) for one or more Frame.io assets so stakeholders can view and comment.

## Inputs

| Input | Source | Required | Description |
|-------|--------|----------|-------------|
| Assets | User prompt | Yes | One or more assets to include in the share. Can be asset IDs, names, or paths. Multiple assets create a single shared review session. |
| Project | User prompt or `frameio.local.md` default | Conditional | Required if assets are specified by name or path. |
| Access level | User prompt | No | `public` (anyone with link), `password` (link + password), or `private` (email-invited only). Defaults to prompting the user — never default to public without explicit confirmation. |
| Password | User prompt | Conditional | Required if access level is `password`. |
| Expiration | User prompt | No | When the link expires. Accepts relative (`7 days`, `2 weeks`) or absolute (`2026-03-20`) values. No expiration if not specified. |
| Allow downloads | User prompt | No | Whether reviewers can download the original files. Defaults to `false`. |

If the user does not specify assets, prompt for them. If access level is not specified, ask the user to choose — do not silently create public links.

## Workflow

1. **Authenticate.**
   - Call `frameio_whoami` to verify the session. Handle auth failure per **Auth Handling** below.

2. **Resolve assets.**
   - If asset IDs were provided, call `frameio_get_file` for each to confirm they exist.
   - If names or paths were provided:
     - Resolve the project (from input or `frameio.local.md` default).
     - Navigate the folder tree with `frameio_list_folder` to locate each asset.
     - If an asset name is ambiguous, present matching options for the user to select.
   - Collect all resolved `asset_id` values.

3. **Check for existing shares.**
   - Call `frameio_list_shares` for the project.
   - Check if any active (non-expired) share already covers the exact same set of assets.
   - If a matching share exists, inform the user:
     "An active share link already exists for these assets: {url}. Do you want to create a new one anyway?"
   - Proceed only if the user confirms, or if no matching share exists.

4. **Prompt for access configuration (if not already provided).**
   - If access level was not specified, present the options:
     ```
     How should this share link be accessed?
     1. Public — anyone with the link can view
     2. Password-protected — requires a password to view
     3. Private — only invited email addresses can view
     ```
   - If `password` is selected and no password was provided, prompt for one.
   - If expiration was not specified, ask: "Set an expiration? (e.g., '7 days', '2026-03-20', or 'none')"

5. **Create the share link.**
   - Call `frameio_create_share` with:
     - `asset_ids`: list of asset IDs
     - `access_level`: public / password / private
     - `password`: (if applicable)
     - `expires_at`: ISO 8601 timestamp (if applicable)
     - `allow_downloads`: boolean
   - Capture the returned share `id` and `url`.

6. **Confirm and present the result.**
   - Display the share link URL and all configured settings.
   - If private access, remind the user to invite reviewers by email through the Frame.io UI or a follow-up action.

## Expected Output

```
Share link created successfully.

URL: https://app.frame.io/reviews/xyz789
Access: Password-protected
Password: ••••••••
Expiration: 2026-03-20
Downloads: Disabled
Assets included:
  - hero_v3.mp4 (abc123)
  - cutdown_30s.mp4 (def456)
  - poster.png (ghi789)
```

**If an existing share was found:**
```
An active share already exists for these assets:
  URL: https://app.frame.io/reviews/abc123
  Created: 2026-03-05 | Expires: 2026-03-20 | Access: Public

Create a new share link anyway? (yes/no)
```

**Error case:**
```
Could not create share link: Asset "deleted_file.mp4" (ID: xxx) no longer exists.
Please verify the assets and try again.
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
| Complex review setup with approval tracking | **review-coordinator** | When the user wants to set up a review with approval criteria, due dates, or per-reviewer tracking, the review-coordinator agent manages the full lifecycle beyond just creating a link. |

For simple share link creation, this command handles everything directly. The review-coordinator is invoked only when the user requests structured review workflows with approval tracking or custom criteria from `frameio.local.md`.
