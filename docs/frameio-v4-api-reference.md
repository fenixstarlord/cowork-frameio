# Frame.io V4 API Reference

> **Source**: Compiled from https://developer.adobe.com/frameio as of March 2026.
> **OpenAPI Spec**: https://api.frame.io/v4/openapi.json (machine-readable, use for code generation)
> **Postman Collection**: https://www.postman.com/adobe/frame-io-v4-public-api
> **Changelog**: https://developer.adobe.com/frameio/guides/Changelog/
> **Status**: V4 is the current API. V2 is deprecated. They are NOT compatible.

---

## Base URL & Conventions

```
https://api.frame.io/v4/
```

- All endpoints require `account_id` in the path: `/v4/accounts/{account_id}/...`
- Request/response payloads are JSON. Set `Content-Type: application/json`.
- Resource data is always nested under the `data` key in responses.
- Auth via Bearer token: `Authorization: Bearer <ACCESS_TOKEN>`

---

## Authentication

V4 uses **OAuth 2.0 via Adobe Identity Management Service (IMS)**. Developer tokens from V2 are NOT supported.

### Auth Types

| Type | Use Case | Requires User Login? |
|------|----------|---------------------|
| OAuth User Authentication (Web App) | Applications with a backend server | Yes — user logs in via browser redirect |
| OAuth User Authentication (Native App) | Desktop/mobile apps, CLI tools | Yes — user logs in via browser or device flow |
| OAuth Server-to-Server (S2S) | Automated systems, service accounts | No — uses client credentials only |

**S2S is only available to accounts administered via Adobe Admin Console.**

### OAuth Flow (User Authentication — Web App)

1. Register app in Adobe Developer Console, add Frame.io API, create OAuth Web App credential
2. Redirect user to: `https://ims-na1.adobelogin.com/ims/authorize/v2?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=openid,AdobeID,frameio.apps.readwrite&response_type=code`
3. User authenticates, Adobe IMS redirects back with `?code={AUTH_CODE}`
4. Exchange code for tokens:
   ```
   POST https://ims-na1.adobelogin.com/ims/token/v3
   Content-Type: application/x-www-form-urlencoded

   grant_type=authorization_code
   &client_id={CLIENT_ID}
   &client_secret={CLIENT_SECRET}
   &code={AUTH_CODE}
   ```
5. Response includes `access_token`, `refresh_token`, `expires_in` (typically 86400s / 24h)
6. Refresh tokens before expiry:
   ```
   POST https://ims-na1.adobelogin.com/ims/token/v3
   Content-Type: application/x-www-form-urlencoded

   grant_type=refresh_token
   &client_id={CLIENT_ID}
   &client_secret={CLIENT_SECRET}
   &refresh_token={REFRESH_TOKEN}
   ```

### Required Scopes

`openid,AdobeID,frameio.apps.readwrite`

---

## Resource Hierarchy

```
Account → Workspace → Project → Folder → Folder / Version Stack / File
```

- **Account**: Top-level org. Determines subscription, storage, user roles.
- **Workspace**: Organizational container (was "Team" in V2).
- **Project**: Contains all media for a body of work. Has a `root_folder_id`.
- **Folder**: Directory. Can be nested. Listed via `children` endpoint.
- **File**: Any uploaded asset (video, audio, image, PDF).
- **Version Stack**: Ordered container of Files (version 1, 2, 3...).

---

## Pagination

V4 uses **cursor-based pagination**. Unidirectional (forward only).

- Default page size: 50. Max: 100.
- Set page size: `?page_size=25`
- Response includes `links.next` with a cursor URL. Follow it until `links.next` is null.
- To include total count: `?include_total_count=true`
- **Never construct cursor strings yourself** — always use the `links.next` URL as-is.

```json
{
  "data": [...],
  "links": {
    "next": "/v4/accounts/{id}/folders/{id}/children?after=g3QAAAACZAAGb2Zmc2V0..."
  },
  "total_count": 142
}
```

---

## Rate Limiting

Leaky bucket algorithm, enforced per account.

| Header | Description |
|--------|-------------|
| `x-ratelimit-limit` | Max requests for this endpoint |
| `x-ratelimit-remaining` | Requests remaining in current window |
| `x-ratelimit-window` | Time window in milliseconds |

- Limits range from 10 req/min to 100 req/sec depending on endpoint.
- On 429: use exponential backoff (start 1s, double each retry, max 30s).
- Proactive: when `remaining < 20%` of `limit`, add a delay before next request.

---

## Error Responses

```json
{
  "errors": [
    {
      "detail": "Unexpected field: foo",
      "source": { "pointer": "/data/foo" },
      "title": "Invalid value"
    }
  ]
}
```

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created |
| 204 | No Content | Resource deleted (no body) |
| 400 | Bad Request | Malformed request |
| 401 | Unauthorized | Token missing or invalid |
| 403 | Forbidden | Insufficient permissions (or account locked) |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Valid syntax but invalid semantics |
| 429 | Too Many Requests | Rate limit exceeded |
| 5xx | Server Error | Wait 30s+ before retry, use exponential backoff |

---

## Include Parameter

Many endpoints support `?include=` to embed related resources in the response, reducing round trips:

```
GET /v4/accounts/{id}/folders/{id}/children?include=project
```

Common includes: `project`, `creator`, `metadata`, `media_links`, `media_links.original`, `media_links.thumbnail`, `media_links.high_quality`

---

## Endpoints by Resource

### Users

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v4/me` | Get authenticated user info. Use to verify auth token. |

**Response:**
```json
{
  "data": {
    "id": "8ea72912-...",
    "email": "user@example.com",
    "name": "Jane Editor",
    "accounts": [{ "id": "6f70f1bd-...", "name": "Studio XYZ" }]
  }
}
```

### Accounts

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v4/accounts` | List accounts for the authenticated user |
| GET | `/v4/accounts/{account_id}` | Get account details |

### Workspaces

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v4/accounts/{account_id}/workspaces` | List workspaces (replaces V2 "teams") |
| GET | `/v4/accounts/{account_id}/workspaces/{workspace_id}` | Get workspace details |

### Projects

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v4/accounts/{account_id}/projects` | List all projects in account |
| GET | `/v4/accounts/{account_id}/workspaces/{workspace_id}/projects` | List projects in workspace |
| GET | `/v4/accounts/{account_id}/projects/{project_id}` | Get project details |

**Key fields in project response:** `id`, `name`, `root_folder_id`, `workspace_id`, `storage`, `created_at`, `updated_at`

### Folders

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v4/accounts/{account_id}/folders/{folder_id}/children` | List folder contents (files, folders, version stacks) |
| POST | `/v4/accounts/{account_id}/folders` | Create folder |
| GET | `/v4/accounts/{account_id}/folders/{folder_id}` | Get folder details |
| PATCH | `/v4/accounts/{account_id}/folders/{folder_id}` | Update folder |
| DELETE | `/v4/accounts/{account_id}/folders/{folder_id}` | Delete folder |

**Create folder request:**
```json
{
  "data": {
    "name": "Client Review",
    "parent_id": "{parent_folder_id}"
  }
}
```

**Children response fields:** `id`, `name`, `type` ("file" | "folder" | "version_stack"), `file_size`, `media_type`, `status`, `created_at`, `updated_at`, `project_id`, `parent_id`

### Files

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v4/accounts/{account_id}/files` | Create file (local upload) — returns presigned upload URLs |
| POST | `/v4/accounts/{account_id}/files` | Create file (remote upload) — provide source URL |
| GET | `/v4/accounts/{account_id}/files/{file_id}` | Get file details |
| PATCH | `/v4/accounts/{account_id}/files/{file_id}` | Update file metadata |
| DELETE | `/v4/accounts/{account_id}/files/{file_id}` | Delete file |

**Create file (local upload) request:**
```json
{
  "data": {
    "name": "hero_cut_v3.mov",
    "file_size": 2147483648,
    "parent_id": "{folder_id}"
  }
}
```

**Response (includes upload URLs):**
```json
{
  "data": {
    "id": "93e4079d-...",
    "name": "hero_cut_v3.mov",
    "status": "created",
    "upload_urls": [
      { "url": "https://frameio-uploads-production.s3-accelerate.amazonaws.com/parts/.../part_1?..." },
      { "url": "https://frameio-uploads-production.s3-accelerate.amazonaws.com/parts/.../part_2?..." },
      { "url": "https://frameio-uploads-production.s3-accelerate.amazonaws.com/parts/.../part_3?..." }
    ],
    "view_url": "https://next.frame.io/project/.../view/..."
  }
}
```

**Create file (remote upload) request:**
```json
{
  "data": {
    "name": "interview_b_roll.mp4",
    "source_url": "https://storage.example.com/interview_b_roll.mp4",
    "parent_id": "{folder_id}"
  }
}
```

### File Upload Process

1. **Create the file** via `POST /v4/accounts/{id}/files` with `name`, `file_size`, and `parent_id`
2. **Response includes `upload_urls`** — array of presigned S3 PUT URLs
3. **Calculate chunk size**: `chunk_size = ceil(file_size / len(upload_urls))` (typically ~25 MB each)
4. **Upload each chunk** via `PUT` to the corresponding URL:
   - **Method**: PUT
   - **Headers**: `Content-Type: {media_type}` (must match file type), `x-amz-acl: private`
   - **Body**: raw binary chunk data
   - Chunks must match the order of upload_urls (1st URL = 1st chunk, etc.)
   - Chunks CAN be uploaded in parallel for speed
   - Chunks CAN be re-uploaded (same URL) on failure
5. **Presigned URLs expire after 24 hours**
6. **S3 errors are XML, not JSON** — handle differently from Frame.io API errors
7. Once all chunks are uploaded, the file will automatically begin processing (proxy generation, etc.)

### Version Stacks

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v4/accounts/{account_id}/version_stacks/{version_stack_id}` | Get version stack details |
| GET | `/v4/accounts/{account_id}/version_stacks/{version_stack_id}/children` | List versions in stack |

**Note**: V4 supports listing and reading version stacks. Endpoints for creating and updating version stacks are coming soon.

### Comments

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v4/accounts/{account_id}/comments?asset_id={file_id}` | List comments on a file |
| POST | `/v4/accounts/{account_id}/comments` | Create a comment |
| GET | `/v4/accounts/{account_id}/comments/{comment_id}` | Get comment details |
| PATCH | `/v4/accounts/{account_id}/comments/{comment_id}` | Update a comment |
| DELETE | `/v4/accounts/{account_id}/comments/{comment_id}` | Delete a comment |

**Create comment request:**
```json
{
  "data": {
    "asset_id": "{file_id}",
    "text": "The color grading at 01:23:15:08 needs to be warmer",
    "timecode": "01:23:15:08"
  }
}
```

**Comment response fields:** `id`, `text`, `asset_id`, `timecode`, `creator_id`, `created_at`, `updated_at`, `resolved`

**Sorting**: `?sort=created_at_asc`, `?sort=created_at_desc`, `?sort=timecode_asc` (experimental)

### Shares

Shares replace V2 "Review Links" and "Presentation Links".

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v4/accounts/{account_id}/shares` | List shares |
| POST | `/v4/accounts/{account_id}/shares` | Create a share |
| GET | `/v4/accounts/{account_id}/shares/{share_id}` | Get share details |
| PATCH | `/v4/accounts/{account_id}/shares/{share_id}` | Update a share |
| DELETE | `/v4/accounts/{account_id}/shares/{share_id}` | Delete a share |

**Create share request:**
```json
{
  "data": {
    "asset_ids": ["{file_id_1}", "{file_id_2}"],
    "access": "public",
    "title": "Q2 Campaign Review",
    "expires_at": "2026-04-15T00:00:00Z"
  }
}
```

**Access levels**: `public`, `password`, `private`

### Custom Fields (Metadata)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v4/accounts/{account_id}/field_definitions` | List account-level field definitions |
| GET | `/v4/accounts/{account_id}/projects/{project_id}/field_definitions` | List project-level field definitions |

**Field types**: `select`, `multi_select`, `text`, `number`, `date`, `rating`, `status`, `user`, `url`

**Updating custom fields on a file:**
```
PATCH /v4/accounts/{account_id}/files/{file_id}
```
```json
{
  "data": {
    "custom_fields": {
      "{field_id}": "Approved"
    }
  }
}
```

### Collections

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v4/accounts/{account_id}/collections` | List collections |
| GET | `/v4/accounts/{account_id}/collections/{collection_id}` | Get collection details |

Collections are dynamic groupings filtered by metadata. They update in real time as field values change.

### Webhooks

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v4/accounts/{account_id}/webhooks` | List webhooks |
| POST | `/v4/accounts/{account_id}/webhooks` | Create a webhook |
| DELETE | `/v4/accounts/{account_id}/webhooks/{webhook_id}` | Delete a webhook |

**Webhook events** include: `file.created`, `file.updated`, `file.deleted`, `comment.created`, `comment.updated`, `share.created`, `project.created`, etc.

### Audit Logs (Stable)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v4/accounts/{account_id}/audit_logs` | List audit log entries |

Supports `?include=user` and filtering.

---

## V2 → V4 Terminology Map

| V2 (Legacy) | V4 | Notes |
|-------------|-----|-------|
| Teams | Workspaces | Organizational containers |
| Assets | Files / Folders | Distinct endpoints in V4 |
| Review Links | Shares | Consolidated with Presentation Links |
| Presentation Links | Shares | Same as above |
| Developer Tokens | OAuth 2.0 (Adobe IMS) | JWT auth not supported |
| Team-only Comments | Internal Comments | Hidden by default after V3→V4 migration |
| root_asset_id | root_folder_id | Project root for folder traversal |

---

## V4 API Stability Tiers

The V4 API has multiple stability tiers accessed via the API reference navigation:

| Tier | URL Path | Description |
|------|----------|-------------|
| Stable (Current) | `/frameio/api/current/` | Production-ready. Breaking changes follow deprecation periods. |
| Experimental | `/frameio/api/experimental/` | May change without notice. New features appear here first. |
| Alpha | `/frameio/api/alpha/` | Early access. Schema may shift significantly. |

Use the Stable tier for all core plugin functionality. Experimental can be used for optional/advanced features with appropriate error handling.

---

## Key Differences from V2

1. **No developer tokens** — must use OAuth 2.0
2. **Separate File and Folder endpoints** — V2 had unified "asset" endpoints
3. **Cursor-based pagination** — V2 used offset-based
4. **Custom Fields are a first-class concept** — V2 had no metadata framework
5. **Shares replace Review Links and Presentation Links** — single concept in V4
6. **Leaner response payloads** — V4 returns less data by default, use `?include=` to expand
7. **Account ID in every path** — V2 inferred from token, V4 requires explicit account_id
8. **Version Stacks are read-only for now** — create/update endpoints coming soon
9. **S2S auth available** — V2 only supported user tokens and developer tokens
10. **All paths use /v4/ prefix** — no backward compatibility with /v2/ paths
