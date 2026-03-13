---
name: project-navigation
description: Browse Frame.io workspaces and projects, traverse folder trees, search for assets by name, navigate the resource hierarchy, list collections
allowed-tools: frameio_whoami, frameio_list_workspaces, frameio_list_projects, frameio_list_folder, frameio_list_collections
---

# Project Navigation

Navigate the Frame.io resource hierarchy to find workspaces, projects, folders, and files. This skill covers listing workspaces and projects, traversing folder trees from the project root, handling large folders with thousands of assets, searching by name or metadata, and working with collections.

## Prerequisites

- Authenticated Frame.io session (OAuth 2.0 via Adobe IMS)
- Account ID (retrieved via `frameio_whoami` if not configured in `frameio.local.md`)

## MCP Tools Used

| Tool | Purpose |
|------|---------|
| `frameio_whoami` | Get authenticated user info and available account IDs |
| `frameio_list_workspaces` | List all workspaces in an account |
| `frameio_list_projects` | List projects in a workspace or account |
| `frameio_list_folder` | List contents of a folder (files, subfolders, version stacks) |
| `frameio_list_collections` | List dynamic collections filtered by metadata |

---

## Capability 1: Identify Account and User Context

### Overview

Before navigating any resources, establish which account and user context you are operating in. This is especially important for users who belong to multiple Frame.io accounts.

### Step-by-Step

1. **Get current user info.**
   Call `frameio_whoami`. The response includes:
   - `id`: the authenticated user's ID
   - `email`: the user's email address
   - `name`: display name
   - `accounts`: array of accounts the user belongs to, each with `id` and `name`

2. **Select the account.**
   - If the user has configured `account_id` in `frameio.local.md`, use that.
   - If not, and the user belongs to multiple accounts, present the list and ask them to choose.
   - If only one account, use it automatically.

3. **Cache the account ID** for subsequent calls in this session. All V4 API paths require the account ID.

---

## Capability 2: List Workspaces

### Overview

Workspaces are organizational containers within an account. Each workspace contains projects.

### Step-by-Step

1. **List all workspaces.**
   Call `frameio_list_workspaces` with the account ID.

2. **Present workspace list.**
   For each workspace, show:
   - Name
   - ID
   - Number of projects (if available)

3. **Handle pagination.**
   Large accounts may have many workspaces. Follow pagination cursors to retrieve all.

4. **Let the user select a workspace** to drill into projects, or skip to listing all projects across the account.

---

## Capability 3: List Projects

### Overview

Projects contain all media for a body of work. Each project has a `root_folder_id` that serves as the entry point for folder traversal.

### Step-by-Step

1. **List projects.**
   Call `frameio_list_projects` with:
   - Account ID (required)
   - Workspace ID (optional — omit to list all projects across the account)

2. **Present project list.**
   For each project, show:
   - Name
   - ID
   - `root_folder_id` (needed for folder traversal)
   - Storage usage (if available)
   - Created/updated dates

3. **Handle pagination.**
   Accounts with many projects require pagination. Collect all pages before presenting.

4. **If the user has a default project** configured in `frameio.local.md` (`default_project_id`), highlight it in the list or use it automatically when the user does not specify a project.

---

## Capability 4: Traverse Folder Tree

### Overview

Navigate into a project by traversing its folder hierarchy starting from the `root_folder_id`. This is the primary way to locate specific files and folders.

### Step-by-Step

1. **Start at the project root.**
   Get the project's `root_folder_id` from the project details (Capability 3). Call `frameio_list_folder` with this ID.

2. **Present folder contents.**
   Show items grouped by type:
   ```
   ## Project: Campaign Q2

   ### Folders
   - Dailies/ (id: abc123)
   - Exports/ (id: def456)
   - Graphics/ (id: ghi789)

   ### Files
   - hero_cut_v3.mov (video/quicktime, 2.1 GB)
   - brief.pdf (application/pdf, 340 KB)

   ### Version Stacks
   - logo_animation (3 versions)
   ```

3. **Navigate deeper.**
   When the user selects a folder, call `frameio_list_folder` with that folder's ID. Repeat until the target is found.

4. **Track the navigation path.**
   Maintain a breadcrumb trail so the user knows where they are:
   ```
   Account > Workspace > Project > Dailies > Day 03 > Camera A
   ```

5. **Go back up.**
   Each folder's parent can be identified from its `parent_id` field. Use this to navigate up the tree.

---

## Capability 5: Handle Large Folders (10,000+ Items)

### Overview

Production projects may contain folders with thousands of assets. The API paginates at a max of 100 items per page. Fetching all items requires following cursor links through potentially hundreds of pages.

### Step-by-Step

1. **Detect large folders.**
   On the first page of results, request `include_total_count=true` (if supported by the tool). If the total count exceeds 500, warn the user that this is a large folder.

2. **Paginate efficiently.**
   - Use maximum page size (100) to minimize API calls.
   - Follow `links.next` cursor URLs until null.
   - Do NOT construct cursor strings manually — use the URLs as-is.

3. **Progressive reporting.**
   For very large folders, report progress:
   ```
   Fetching folder contents... 200/10,432 items loaded
   Fetching folder contents... 500/10,432 items loaded
   ```

4. **Filter early when possible.**
   If the user is looking for a specific file or type:
   - Ask for the file name or type before fetching all pages.
   - Scan each page as it arrives and stop early if the target is found.
   - This avoids unnecessary API calls for simple lookups.

5. **Memory considerations.**
   For 10,000+ items, avoid holding all items in memory simultaneously if possible. Process in batches:
   - Summarize counts by type (files, folders, version stacks)
   - Only retain items matching the user's search criteria

---

## Capability 6: Search by Name

### Overview

Find assets by name within a project or folder. The V4 API does not have a dedicated search endpoint, so search is implemented by traversing the folder tree and filtering by name.

### Step-by-Step

1. **Get the search scope.**
   Ask the user for:
   - The name or partial name to search for
   - The scope: entire project, specific folder, or recursive from a folder

2. **For project-wide search:**
   Start from the project's `root_folder_id` and recursively list all folders.
   - For each folder, fetch its children.
   - Check each child's `name` against the search query (case-insensitive partial match).
   - Collect matching results.

3. **For folder-specific search:**
   List the folder's contents (with full pagination) and filter by name.

4. **Present results.**
   ```
   ## Search Results for "hero_cut"

   Found 3 matches:

   1. hero_cut_v1.mov
      Path: Exports / Round 1
      Type: file, Size: 1.8 GB

   2. hero_cut_v2.mov
      Path: Exports / Round 2
      Type: file, Size: 2.0 GB

   3. hero_cut_v3.mov
      Path: Exports / Final
      Type: file, Size: 2.1 GB
   ```

5. **Performance considerations.**
   Recursive project-wide search on large projects (1000+ folders) can be slow and may trigger rate limits. Warn the user and suggest narrowing the scope if the project is large.

---

## Capability 7: Browse Collections

### Overview

Collections are dynamic groupings of assets filtered by metadata (custom field values). They update in real time as field values change. Collections are a powerful way to find assets without traversing folders.

### Step-by-Step

1. **List available collections.**
   Call `frameio_list_collections` with the account ID.

2. **Present collection list.**
   For each collection, show:
   - Name
   - ID
   - Description or filter criteria (if available)

3. **View collection contents.**
   Collections behave like smart folders. Use the collection to identify assets matching specific metadata criteria (e.g., all assets with status "Approved").

---

## Common Navigation Patterns

### "Find a file to upload a new version"
1. `frameio_whoami` -> get account ID
2. `frameio_list_projects` -> find the project
3. `frameio_list_folder` (root) -> navigate to the target folder
4. Locate the existing file -> hand off to `asset-management` skill for upload

### "Show me everything in this project"
1. `frameio_list_projects` -> get `root_folder_id`
2. `frameio_list_folder` (root) -> show top-level contents
3. Recursively list subfolders on request

### "Which projects am I working on?"
1. `frameio_whoami` -> confirm identity and account
2. `frameio_list_workspaces` -> show workspaces
3. `frameio_list_projects` -> show all projects with recent activity

---

## Error Handling

### Authentication Errors (401)
Token expired or invalid. Trigger token refresh. If refresh fails, prompt user to re-authenticate.

### No Account Found
If `frameio_whoami` returns no accounts:
- The user may not have been added to any Frame.io accounts.
- Suggest they check their Frame.io invitation or contact their team admin.

### Empty Workspaces/Projects
If `frameio_list_workspaces` or `frameio_list_projects` returns empty:
- The account may be new or the user may lack permission to view workspaces.
- Verify the account ID is correct.
- Check if the user's role allows listing projects.

### Permission Errors (403)
The user may not have access to certain workspaces or projects. This is common with role-based access control:
- Report which resources are inaccessible.
- Suggest the user request access from their team admin.

### Invalid IDs (404)
If a folder, project, or workspace ID returns 404:
- The resource may have been deleted or the ID is incorrect.
- Re-navigate from a known starting point (account -> workspace -> project).

### Rate Limiting (429)
Recursive folder traversal and large folder pagination can generate many API calls. The MCP server handles backoff automatically. To minimize impact:
- Use maximum page sizes (100 items per page).
- Avoid unnecessary recursive traversals.
- Search with a narrow scope when possible.
- Report progress to the user during long traversals.

### Pagination Interruptions
If pagination fails mid-traversal:
- Report how many items were successfully fetched.
- Offer to retry from where it left off.
- Present partial results if useful.

### Large Project Performance
Projects with deep folder hierarchies or thousands of assets:
- Warn the user before starting a full recursive traversal.
- Suggest using collections or narrowing search scope as alternatives.
- Report estimated time based on total count (if available).
