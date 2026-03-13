# Frame.io Plugin for Claude Cowork

## What This Project Is

A Cowork plugin that brings Frame.io video review and collaboration workflows into Claude's agentic desktop environment. Targets the Frame.io V4 API. Follows the standard Cowork plugin structure (skills + commands + connectors + sub-agents).

This plugin focuses exclusively on the Frame.io API. It does not integrate with or depend on any other plugins.

## Reference Documents

Read these before building. They are the source of truth.

- `docs/frameio-plugin-spec.docx` — Full spec (sections + appendices: CLAUDE.md draft, sequence diagrams, sample skill, edge cases, glossary)
- `docs/frameio-v4-api-reference.md` — V4 API endpoints, auth flow, upload process, pagination, errors
- `docs/skills-sh-reference.md` — How to search, install, and manage agent skills via skills.sh CLI
- `CLAUDE.md` — Plugin-level agent instructions (you create this in Wave 1, using Appendix A of the spec)
- `frameio.local.md` — User-specific config template (you create this in Wave 1)

---

## Execution Strategy: 3 Waves

This build is structured for **maximum parallelism**. Work is organized into 3 waves. Within each wave, all workstreams run **concurrently as sub-agents**. A wave must complete before the next wave begins.

```
WAVE 1: Scaffolding (sequential — must finish first, creates the directory structure)
   └── One agent: scaffold all directories + write all config/doc files

WAVE 2: All content + MCP server (parallel — 4 concurrent workstreams)
   ├── Agent A: Skills (4 SKILL.md files)
   ├── Agent B: Commands (4 command .md files)
   ├── Agent C: Agents (3 agent .md files)
   └── Agent D: MCP Server (Python package: setup.sh, pyproject.toml, all modules)

WAVE 3: Validation (single agent)
   └── Agent E: Run acceptance criteria across all waves, report results
```

---

## WAVE 1: Scaffolding

**One agent, runs first, blocks everything else.**

Create the complete directory structure and all boilerplate files:

```
.claude-plugin/
│   └── plugin.json
.mcp.json
├── CLAUDE.md
├── CHANGELOG.md
├── CONNECTORS.md
├── README.md
├── frameio.local.md
├── commands/              ← create directory, files written in Wave 2
├── skills/                ← create directory tree, files written in Wave 2
│   ├── asset-management/
│   ├── review-workflow/
│   ├── comment-analysis/
│   └── project-navigation/
├── agents/                ← create directory, files written in Wave 2
└── mcp-server/
    ├── setup.sh
    ├── pyproject.toml
    ├── src/
    │   └── frameio_mcp/
    │       ├── __init__.py
    │       ├── server.py       ← stub: imports only
    │       ├── auth.py         ← stub
    │       ├── client.py       ← stub
    │       ├── tools/
    │       │   ├── __init__.py
    │       │   ├── account.py  ← stub
    │       │   ├── files.py    ← stub
    │       │   ├── comments.py ← stub
    │       │   ├── shares.py   ← stub
    │       │   └── metadata.py ← stub
    │       └── utils/
    │           ├── __init__.py
    │           ├── rate_limit.py ← stub
    │           └── errors.py    ← stub
    └── tests/
        ├── __init__.py
        ├── test_client.py   ← stub
        ├── test_rate_limit.py ← stub
        └── test_tools.py    ← stub
```

### Files to write in full during Wave 1:

**plugin.json:**
```json
{
  "name": "frameio",
  "version": "1.0.0",
  "description": "Video review and collaboration with Frame.io. Upload assets, manage reviews, collect feedback, and orchestrate approval workflows.",
  "author": { "name": "" }
}
```

**.mcp.json:**
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

**CLAUDE.md** — Copy the full draft from spec Appendix A. Must contain all 7 sections: Identity, Frame.io Terminology, API Context, Resource Hierarchy, Safety Boundaries, Workflow Patterns, Error Handling.

**CONNECTORS.md** — Document Adobe Developer Console setup, OAuth 2.0 credential creation, env var configuration.

**frameio.local.md** — Template with placeholder fields: `account_id`, `workspace_id`, `default_project_id`, and custom field schema section.

**README.md** — Installation steps, prerequisites (Adobe Dev Console account, Python 3.11+, uv), quick-start guide, plugin structure overview.

**CHANGELOG.md** — Initial `[1.0.0] - {today}` entry.

**setup.sh:**
```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

if [ ! -d ".venv" ]; then
    uv venv
fi

uv pip install -e . --quiet

exec uv run python -m frameio_mcp.server
```

**pyproject.toml:**
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

**All Python stubs** — Create `__init__.py` files and minimal module stubs with docstrings explaining what will be implemented. Just enough that `uv pip install -e .` succeeds.

### Skills Discovery (run after scaffolding, before Wave 2)

Before writing any skills from scratch, search the skills.sh directory for existing community skills that may be relevant to Frame.io, video review, media management, or API development patterns. See `docs/skills-sh-reference.md` for full CLI usage.

**Step 1: Search for relevant skills**
```bash
# Search by keywords relevant to this plugin
npx skills find frameio
npx skills find video-review
npx skills find media-upload
npx skills find oauth
npx skills find api-client
npx skills find mcp-server
```

**Step 2: Browse trending and popular skills**
Check https://skills.sh and https://skills.sh/trending for skills that might provide useful patterns for API wrappers, MCP server development, or media workflows.

**Step 3: List skills from known repos**
```bash
# Check Vercel's official skill collection for relevant patterns
npx skills add vercel-labs/agent-skills --list
```

**Step 4: Install any useful skills**
```bash
# Install relevant skills to the project for Claude Code to reference
npx skills add <owner/repo> --skill <skill-name> -a claude-code -y
```

**What to look for:**
- Skills for building MCP servers (patterns for tool registration, error handling, auth)
- Skills for API client development (httpx patterns, rate limiting, pagination)
- Skills for OAuth 2.0 / Adobe IMS authentication
- Skills for file upload workflows (chunked uploads, resume logic)
- Skills for Frame.io specifically (unlikely but check)
- Skills for Cowork plugin development (skill/command/agent structure patterns)

**How to use found skills:** If you find relevant community skills, install them and reference their patterns when building the plugin's own skills and MCP server in Wave 2. Do not blindly copy — adapt patterns to fit the Frame.io V4 API and this plugin's architecture. If no relevant skills are found, proceed with building from the spec alone.

### Wave 1 Acceptance Criteria
- [ ] All directories exist
- [ ] plugin.json is valid JSON with name, version, description, author
- [ ] .mcp.json uses stdio type, points to mcp-server/setup.sh
- [ ] CLAUDE.md contains all 7 sections from Appendix A
- [ ] frameio.local.md has clearly marked template fields
- [ ] README.md includes installation steps and prerequisites
- [ ] `uv pip install -e .` succeeds in mcp-server/ (stubs only, no runtime errors)
- [ ] Skills discovery completed: searched skills.sh for relevant community skills, installed any that apply

---

## WAVE 2: Content + MCP Server (4 parallel agents)

All 4 agents start simultaneously once Wave 1 is complete. They write to separate directories and do NOT depend on each other.

### Agent A: Skills

Write all 4 SKILL.md files. Reference `docs/frameio-v4-api-reference.md` for endpoint details and `docs/frameio-plugin-spec.docx` Appendix C for the asset-management reference implementation.

**Before writing:** Check if any community skills were installed during Wave 1's skills discovery step (`npx skills list`). If relevant skills were found, study their structure, frontmatter patterns, and instruction style — then adapt those patterns for this plugin's skills. If none were installed, build from the spec alone.

| Skill | File | Key Requirements |
|-------|------|-----------------|
| asset-management | `skills/asset-management/SKILL.md` | **Write this first — use Appendix C of the spec as the template.** Multi-part upload flow (create → presigned URLs → chunk PUT → complete), folder organization, version stacks, metadata/custom fields, download. Reference: MCP tools `frameio_create_file`, `frameio_complete_upload`, `frameio_list_folder`, `frameio_create_folder`, `frameio_get_file`, `frameio_update_file`, `frameio_delete_file` |
| review-workflow | `skills/review-workflow/SKILL.md` | Share link creation with access levels (public/password/private), approval tracking via custom field status, reviewer access management, due dates. Reference: `frameio_create_share`, `frameio_list_shares`, `frameio_get_custom_fields`, `frameio_update_custom_field` |
| comment-analysis | `skills/comment-analysis/SKILL.md` | Fetch all comments with full pagination, parse timecode-anchored comments, group by reviewer, summarize feedback themes, identify unresolved threads. Reference: `frameio_list_comments`, `frameio_resolve_comment` |
| project-navigation | `skills/project-navigation/SKILL.md` | List workspaces/projects, traverse folder tree from root_folder_id, handle 10K+ asset pagination, search by name/metadata. Reference: `frameio_whoami`, `frameio_list_workspaces`, `frameio_list_projects`, `frameio_list_folder`, `frameio_list_collections` |

**Each SKILL.md must have:**
- Valid frontmatter: `name` and `description` (use natural trigger phrases)
- Overview section
- Step-by-step instructions for each capability
- Error handling section
- References to specific MCP tools by name

### Agent A Acceptance Criteria
- [ ] All 4 SKILL.md files exist with valid frontmatter
- [ ] asset-management matches Appendix C quality and structure
- [ ] Each skill references MCP tools by name
- [ ] Each skill has an error handling section

---

### Agent B: Commands

Write all 4 command markdown files. Each is an independent slash command workflow.

| Command | File | Workflow Summary |
|---------|------|-----------------|
| /frameio:upload-asset | `commands/upload-asset.md` | Prompt for file path → validate locally → prompt for project + folder → create file via API → upload chunks (delegate to upload-agent if > 5 GB) → confirm |
| /frameio:review-status | `commands/review-status.md` | Prompt for project → fetch shares → fetch comment counts + approval statuses → present summary table |
| /frameio:collect-feedback | `commands/collect-feedback.md` | Find asset → fetch all comments with timecodes → group by reviewer → synthesize themes + action items |
| /frameio:create-share | `commands/create-share.md` | Select assets → configure access level/expiration/password → create share link → return URL + settings |

**Each command .md must have:**
- Frontmatter with `description`
- **Inputs** section (what user provides or is prompted for)
- **Workflow** section (numbered steps)
- **Expected Output** section
- **Auth handling**: what happens if user hasn't authenticated yet
- **Delegation**: which sub-agent handles heavy lifting, if any

### Agent B Acceptance Criteria
- [ ] All 4 command files exist with valid frontmatter
- [ ] Each has Inputs, Workflow, Expected Output, and auth handling sections
- [ ] upload-asset delegates to upload-agent for files > 5 GB
- [ ] collect-feedback groups comments by reviewer and timecode

---

### Agent C: Sub-Agents

Write all 3 agent markdown files.

| Agent | File | Key Requirements |
|-------|------|-----------------|
| upload-agent | `agents/upload-agent.md` | Chunked upload with resume/checkpoint (.frameio-upload-state.json). Parallel chunk uploads (4-8 concurrent). Handle S3 errors (XML format). Exponential backoff on failure. |
| review-coordinator | `agents/review-coordinator.md` | Check for existing shares before creating new ones. Track per-reviewer approval status. Apply approval criteria from frameio.local.md. Generate review summary reports. |
| feedback-synthesizer | `agents/feedback-synthesizer.md` | Paginate all comments. Group by theme + reviewer. Identify consensus vs. disagreements. Extract action items with timecodes. |

**Each agent .md must have:**
- Frontmatter: `name`, `description`, `model` (sonnet), `tools` (list of MCP tools needed)
- System prompt instructions
- Input/output format specification
- Error handling behavior

### Agent C Acceptance Criteria
- [ ] All 3 agent files exist with valid frontmatter
- [ ] upload-agent includes .frameio-upload-state.json checkpoint logic
- [ ] feedback-synthesizer specifies structured output format (themes, action items, unresolved)
- [ ] Each agent lists its required MCP tools

---

### Agent D: MCP Server

Build the full Python MCP server in `mcp-server/`. Replace all stubs from Wave 1 with production implementations. Reference `docs/frameio-v4-api-reference.md` for all endpoint paths, request/response schemas, auth flow, and upload process.

**Before writing:** Check if any MCP server, API client, or OAuth skills were installed during Wave 1's skills discovery step (`npx skills list`). If found, study their patterns for tool registration, error handling, rate limiting, and auth flows — then adapt to this server's architecture.

**Implementation order within this agent (sequential, not parallel):**
1. `utils/errors.py` + `utils/rate_limit.py` — foundation, no dependencies
2. `auth.py` — OAuth flow, token storage at ~/.frameio/tokens.json
3. `client.py` — async httpx client using auth + rate_limit + errors
4. `tools/account.py` — simplest tools, validates client works
5. `tools/files.py` — most complex (upload flow with presigned S3 URLs)
6. `tools/comments.py`
7. `tools/shares.py`
8. `tools/metadata.py`
9. `server.py` — imports and registers all 20 tools
10. `tests/` — test all modules

**Key rules:**
- Use `httpx.AsyncClient` with a shared session
- Use `mcp` Python package, register tools with Pydantic models
- Server communicates via stdio
- NEVER log or print tokens
- `frameio_delete_file` and `frameio_delete_share` require `confirmed: bool` param
- Upload chunks go directly to S3 via presigned PUT URLs with headers: `Content-Type: {media_type}`, `x-amz-acl: private`
- S3 errors are XML, not JSON — handle separately
- Use `httpx` (async) — do NOT use `requests` or the legacy `frameioclient` SDK (V2 only). See `docs/frameio-v4-api-reference.md` for all endpoint details.

**Environment variables** (passed via .mcp.json env block):

| Variable | Required | Description |
|----------|----------|-------------|
| FRAMEIO_CLIENT_ID | Yes | OAuth client ID from Adobe Dev Console |
| FRAMEIO_CLIENT_SECRET | Yes | OAuth client secret |
| FRAMEIO_ACCOUNT_ID | No | Default account ID |
| FRAMEIO_TOKEN_PATH | No | Token storage path (default: ~/.frameio/tokens.json) |

### Agent D Acceptance Criteria
- [ ] `uv pip install -e .` succeeds
- [ ] `bash setup.sh` starts the server without errors
- [ ] All 20 tools are registered in server.py
- [ ] frameio_whoami returns correct response shape
- [ ] Rate limiting: 429 triggers backoff, subsequent requests succeed
- [ ] Token refresh works on expired token
- [ ] Error responses use standardized format
- [ ] `uv run pytest` passes

---

## WAVE 3: Validation

### Agent E: Validation

Run acceptance criteria from ALL waves and produce a final report. Check every file exists, every frontmatter is valid, every MCP tool is registered, and tests pass. Output a markdown checklist with pass/fail for every item.

---

## Frame.io V4 API Quick Reference

- Base URL: `https://api.frame.io/v4/`
- Auth: OAuth 2.0 via Adobe IMS (no developer tokens)
- All paths include account_id: `/v4/accounts/{account_id}/...`
- Pagination: cursor-based, follow `links.next` until null
- Rate limits: leaky bucket, read `x-ratelimit-remaining` header
- Detailed reference: `docs/frameio-v4-api-reference.md`

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

## Tech Stack

- Plugin: Markdown files (skills, commands, agents)
- Manifests: JSON (plugin.json, .mcp.json)
- MCP server: Python 3.11+, async
- Package manager: uv (installed by setup.sh)
- HTTP client: httpx (async) — do NOT use requests or the legacy frameioclient SDK (V2 only)
- Validation: pydantic
- Testing: pytest + pytest-asyncio + respx
- API: Frame.io V4 REST via direct httpx calls
- Auth: OAuth 2.0 via Adobe IMS
- Transport: stdio
