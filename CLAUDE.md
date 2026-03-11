# Frame.io Plugin for Claude Cowork

## What This Project Is

This is a Cowork plugin that brings Frame.io video review and collaboration workflows into Claude's agentic desktop environment. It follows the standard Cowork plugin structure (skills + commands + connectors + sub-agents) and targets the Frame.io V4 API.

The full specification is in `docs/frameio-plugin-spec.docx`. That document is the source of truth for architecture decisions, tool signatures, edge cases, and acceptance criteria. Read it before building anything.

## Build Sequence

Build this plugin in phases. Complete each phase and verify its acceptance criteria before moving to the next. Do not skip ahead.

### Phase 1: Scaffolding (do this first)

1. Create the directory structure:

```
frameio/
├── .claude-plugin/
│   └── plugin.json
├── .mcp.json
├── CLAUDE.md              ← Copy from Appendix A of the spec
├── CHANGELOG.md
├── CONNECTORS.md
├── README.md
├── frameio.local.md
├── commands/
│   ├── upload-asset.md
│   ├── review-status.md
│   ├── collect-feedback.md
│   ├── create-share.md
│   └── sync-comments.md
├── skills/
│   ├── asset-management/SKILL.md
│   ├── review-workflow/SKILL.md
│   ├── comment-analysis/SKILL.md
│   ├── project-navigation/SKILL.md
│   └── resolve-bridge/SKILL.md
├── agents/
│   ├── upload-agent.md
│   ├── review-coordinator.md
│   └── feedback-synthesizer.md
└── mcp-server/
    ├── setup.sh               ← Installs uv + creates venv + installs deps
    ├── pyproject.toml          ← Project metadata + dependencies
    ├── src/
    │   └── frameio_mcp/
    │       ├── __init__.py
    │       ├── server.py       ← MCP server entrypoint
    │       ├── auth.py         ← OAuth 2.0 / Adobe IMS handling
    │       ├── client.py       ← Frame.io V4 API client with rate limiting
    │       ├── tools/
    │       │   ├── __init__.py
    │       │   ├── account.py  ← frameio_whoami, list_workspaces, list_projects
    │       │   ├── files.py    ← list_folder, create_folder/file, upload, delete
    │       │   ├── comments.py ← list/create/resolve comments
    │       │   ├── shares.py   ← create/list/delete shares
    │       │   └── metadata.py ← collections, custom fields, bulk updates
    │       └── utils/
    │           ├── __init__.py
    │           ├── rate_limit.py   ← Leaky bucket + exponential backoff
    │           └── errors.py       ← Standardized error response format
    └── tests/
        ├── __init__.py
        ├── test_client.py
        ├── test_rate_limit.py
        └── test_tools.py
```

2. Write `plugin.json`:
```json
{
  "name": "frameio",
  "version": "1.0.0",
  "description": "Video review and collaboration with Frame.io. Upload assets, manage reviews, collect feedback, and orchestrate approval workflows.",
  "author": { "name": "" }
}
```

3. Write `.mcp.json` pointing to the local Python MCP server via setup.sh:
```json
{
  "mcpServers": {
    "frameio": {
      "type": "stdio",
      "command": "bash",
      "args": ["mcp-server/setup.sh"],
      "env": {
        "FRAMEIO_CLIENT_ID": "",
        "FRAMEIO_CLIENT_SECRET": ""
      }
    }
  }
}
```
4. Write `CLAUDE.md` using the full draft from spec Appendix A.
5. Write `CONNECTORS.md` explaining Adobe Developer Console setup and OAuth 2.0 flow.
6. Write `frameio.local.md` as a template with placeholder fields for account_id, workspace_id, default_project_id, render_output_folder, and custom field schema.
7. Write `README.md` with installation steps, prerequisites, and quick-start.
8. Write `CHANGELOG.md` with the initial 1.0.0 entry.

**Done when:** All files exist. plugin.json is valid JSON. CLAUDE.md contains all 8 sections (Identity, Terminology, API Context, Resource Hierarchy, Safety Boundaries, Resolve Context, Workflow Patterns, Error Handling). frameio.local.md has clearly marked template fields. .mcp.json uses stdio type pointing to mcp-server/setup.sh. The mcp-server/ directory structure exists with empty __init__.py files and a skeleton pyproject.toml.

### Phase 2: Skills

Write all 5 skill SKILL.md files. Use the asset-management skill in spec Appendix C as the quality reference — every other skill should match that level of detail.

| Skill | Spec Section | Key Requirements |
|-------|-------------|-----------------|
| asset-management | Appendix C (complete draft provided) | Multi-part upload flow, folder organization, version stacks, metadata, download |
| review-workflow | Section 4 + Section 11 | Share link creation, approval tracking, access levels, due dates, custom field status gates |
| comment-analysis | Section 4 + Appendix D (D.4) | Fetch all comments with pagination, timecode parsing, theme synthesis, EDL export |
| project-navigation | Section 4 + Appendix D (D.3) | Workspace/project listing, folder traversal from root_folder_id, search, large project pagination |
| resolve-bridge | Section 8 + Section 4 | EDL generation from comments, render folder detection, timecode format handling (HH:MM:SS:FF), frame rate awareness |

Each SKILL.md must have:
- Valid frontmatter with `name` and `description` (description should use natural user phrasing)
- Overview section
- Step-by-step instructions for each capability
- Error handling section
- References to specific MCP tools by name (from Section 12 of the spec)

**Done when:** All 5 SKILL.md files exist with valid frontmatter. Each references MCP tools by name. Each has error handling. asset-management matches Appendix C.

### Phase 3: Slash Commands

Write all 5 command markdown files. Each command must have:
- Frontmatter with `description`
- Inputs section (what the user provides or is prompted for)
- Workflow section (numbered steps)
- Expected Output section
- Auth check: handle the case where user hasn't authenticated yet
- Delegation note: which agent to delegate to, if applicable

| Command | Key Workflow | Delegates To |
|---------|-------------|-------------|
| upload-asset.md | Prompt for file → validate → create file → upload → complete → confirm | upload-agent (if > 5 GB) |
| review-status.md | Prompt for project → fetch shares → fetch comment counts → summary table | review-coordinator |
| collect-feedback.md | Find asset → fetch all comments → group/sort → synthesize → offer EDL | feedback-synthesizer |
| create-share.md | Select assets → configure access/expiration/password → create → return URL | — |
| sync-comments.md | Fetch comments → format as EDL → save locally → offer reverse import | — |

**Done when:** All 5 command files exist. Each has Inputs, Workflow, Expected Output, and auth handling. upload-asset delegates to upload-agent for large files.

### Phase 4: Sub-Agents

Write all 3 agent markdown files with frontmatter: `name`, `description`, `model`, `tools`.

| Agent | Model | Tools Needed | Key Requirement |
|-------|-------|-------------|----------------|
| upload-agent.md | sonnet | frameio-connector, filesystem | Resume/checkpoint via .frameio-upload-state.json. Parallel chunk uploads (4-8 concurrent). |
| review-coordinator.md | sonnet | frameio-connector | Check for existing shares before creating new ones. Track per-reviewer approval status. |
| feedback-synthesizer.md | sonnet | frameio-connector, filesystem | Paginate all comments. Group by theme and reviewer. Generate EDL output. |

**Done when:** All 3 agent files exist with valid frontmatter. upload-agent includes resume logic. feedback-synthesizer produces structured output format.

### Phase 5: MCP Server (Python + uv)

Build the MCP server as a Python package in `frameio/mcp-server/`, managed by `uv` and installed via `setup.sh`. This matches the pattern used by the existing DaVinci Resolve plugin.

#### setup.sh

The setup script is the entrypoint referenced by `.mcp.json`. It must:
1. Check if `uv` is installed; if not, install it via `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Create a virtual environment if one doesn't exist: `uv venv`
3. Install/sync dependencies: `uv pip install -e .` (or `uv sync` if using uv lockfile)
4. Run the MCP server: `exec uv run python -m frameio_mcp.server`

The script must be idempotent — safe to run repeatedly. On first run it sets up everything; on subsequent runs it just starts the server (skipping install if deps are already satisfied).

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Install uv if not present
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Create venv + install deps (idempotent)
if [ ! -d ".venv" ]; then
    uv venv
fi

uv pip install -e . --quiet

# Run the server
exec uv run python -m frameio_mcp.server
```

#### pyproject.toml

```toml
[project]
name = "frameio-mcp"
version = "1.0.0"
description = "MCP server for Frame.io V4 API"
requires-python = ">=3.11"
dependencies = [
    "mcp",
    "httpx>=0.27",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-asyncio",
    "respx",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Use `httpx` (async) for HTTP requests to Frame.io API — do NOT use `requests` (sync) or the legacy `frameioclient` SDK (which targets V2). The V4 API requires direct HTTP calls.

#### Server Architecture

```
mcp-server/src/frameio_mcp/
├── server.py       ← MCP server entrypoint. Registers all tools. Reads env vars.
├── auth.py         ← OAuth 2.0 flow: authorization_code grant, token storage,
│                      refresh token rotation. Tokens stored in ~/.frameio/tokens.json
├── client.py       ← Async Frame.io V4 HTTP client. All requests go through here.
│                      Handles base URL, auth headers, pagination, error normalization.
├── tools/
│   ├── account.py  ← frameio_whoami, frameio_list_workspaces, frameio_list_projects
│   ├── files.py    ← frameio_list_folder, frameio_create_folder, frameio_create_file,
│   │                  frameio_complete_upload, frameio_get_file, frameio_update_file,
│   │                  frameio_delete_file
│   ├── comments.py ← frameio_list_comments, frameio_create_comment, frameio_resolve_comment
│   ├── shares.py   ← frameio_create_share, frameio_list_shares, frameio_delete_share
│   └── metadata.py ← frameio_list_collections, frameio_get_custom_fields,
│                      frameio_update_custom_field, frameio_bulk_update_fields
└── utils/
    ├── rate_limit.py   ← Read X-RateLimit-* headers, proactive throttle at < 20%,
    │                      exponential backoff on 429 (base 1s, max 30s, 3 retries)
    └── errors.py       ← Normalize all API errors to standardized format:
                           { error: true, code, type, message, retry_after_ms? }
```

#### Key Implementation Notes

- **server.py** uses the `mcp` Python package. Register each tool with typed parameters using Pydantic models. The server communicates via stdio (not HTTP).
- **auth.py** stores tokens at `~/.frameio/tokens.json`. On startup, check for existing token → validate with frameio_whoami → refresh if expired → prompt for re-auth if refresh fails. NEVER log or print tokens.
- **client.py** is the single point for all HTTP calls. Every request goes through `_request()` which: adds auth header, checks rate limit budget, retries on 429, normalizes errors. Use `httpx.AsyncClient` with a shared session.
- **rate_limit.py** reads three headers from every response: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`. When remaining < 20% of limit, add a `sleep()` before the next request. On 429, use `retry_after` from response or exponential backoff.
- **errors.py** maps HTTP status codes to error types: 401→auth_expired, 403→permission_denied, 404→not_found, 422→validation_error, 429→rate_limit_exceeded, 500→server_error. Include `retry_after_ms` for 429s.
- **frameio_delete_file** and **frameio_delete_share** must accept a `confirmed: bool` parameter. If `confirmed` is false, return an error prompting for confirmation instead of deleting.

#### Environment Variables

The MCP server reads these from the environment (passed via `.mcp.json` env block or shell):

| Variable | Required | Description |
|----------|----------|-------------|
| `FRAMEIO_CLIENT_ID` | Yes | OAuth client ID from Adobe Developer Console |
| `FRAMEIO_CLIENT_SECRET` | Yes | OAuth client secret |
| `FRAMEIO_ACCOUNT_ID` | No | Default account ID (overrides per-request) |
| `FRAMEIO_TOKEN_PATH` | No | Custom token storage path (default: ~/.frameio/tokens.json) |

**Done when:** `bash mcp-server/setup.sh` installs deps and starts the server without errors. frameio_whoami returns valid user info with a real token. All 20 tools are registered and return correct response shapes. Rate limiting handles 429 correctly. `uv pip install -e .` succeeds cleanly. Tests pass with `uv run pytest`.

### Phase 6: DaVinci Resolve Integration

Refine the resolve-bridge skill and verify cross-plugin workflows:
- EDL export: comments with timecodes → EDL file with frame-accurate markers
- EDL import: EDL markers → Frame.io comments (reverse direction)
- Render pickup: detect files in ~/cowork-media/ (or configured path)
- Frame rate handling: ask user for fps before EDL export (24, 25, 29.97, 30)

**Done when:** EDL export produces valid EDL. Both plugins can be active without conflicts. Render → Upload flow works end-to-end.

## Frame.io V4 API Quick Reference

- Base URL: `https://api.frame.io/v4/`
- Auth: OAuth 2.0 via Adobe IMS (no developer tokens in V4)
- All paths include account_id: `/v4/accounts/{account_id}/...`
- Pagination: cursor-based, follow `links.next` until null
- Rate limits: leaky bucket, read `X-RateLimit-Remaining` header
- V2 terminology is deprecated: Teams → Workspaces, Assets → Files/Folders, Review Links → Shares

## Resource Hierarchy

```
Account → Workspace → Project → Folder → Folder / Version Stack / File
```

## Safety Rules

1. NEVER delete files without explicit user confirmation
2. NEVER create public share links without user approval
3. NEVER bulk-operate on > 50 assets without warning
4. ALWAYS respect rate limit headers
5. NEVER expose OAuth tokens in output

## Key Files to Reference

- `docs/frameio-plugin-spec.docx` — Full specification (15 sections + 5 appendices)
- `frameio/CLAUDE.md` — Plugin-level agent instructions (built in Phase 1)
- `frameio/frameio.local.md` — User-specific config (account IDs, custom fields)

## Tech Stack

- Plugin files: Markdown (skills, commands, agents, CLAUDE.md)
- Plugin manifest: JSON (plugin.json, .mcp.json)
- MCP server: Python 3.11+ (async, using `mcp` package)
- Package manager: `uv` (installed automatically by setup.sh)
- HTTP client: `httpx` (async) — do NOT use `requests` or the legacy `frameioclient` SDK
- Validation: `pydantic` for tool parameter/response models
- Testing: `pytest` + `pytest-asyncio` + `respx` (httpx mock)
- Frame.io API: V4 REST (https://developer.adobe.com/frameio)
- Auth: OAuth 2.0 via Adobe IMS (authorization_code + refresh token grant)
- Server transport: stdio (launched via setup.sh, referenced in .mcp.json)

### Why These Choices

- **uv over pip/poetry**: Matches the DaVinci Resolve plugin pattern. Fast, deterministic installs. setup.sh is idempotent.
- **httpx over requests**: Async support for parallel chunk uploads. httpx also has better timeout handling.
- **httpx over frameioclient SDK**: The official SDK targets V2 API. V4 requires direct HTTP calls. Don't introduce a legacy dependency.
- **stdio over HTTP transport**: Simpler for local Cowork plugins. No port management. .mcp.json just runs setup.sh.
