# Frame.io Plugin for Claude Cowork

Video review and collaboration workflows powered by the Frame.io V4 API.

## Prerequisites

- [Adobe Developer Console](https://developer.adobe.com/console) account with Frame.io API access
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (installed automatically by `setup.sh`)

## Installation

1. Clone or copy the `frameio/` directory into your Cowork plugins folder.

2. Configure OAuth credentials — see [CONNECTORS.md](CONNECTORS.md) for full setup:
   ```bash
   # Edit .mcp.json with your Adobe Developer Console credentials
   vim .mcp.json
   ```

3. Set your account details in `frameio.local.md`:
   ```
   account_id: <your-account-id>
   workspace_id: <your-workspace-id>
   ```

4. The MCP server starts automatically via `setup.sh` when Claude connects.

## Quick Start

```
/frameio:upload-asset      Upload a file to Frame.io
/frameio:review-status     Check review progress on a project
/frameio:collect-feedback   Gather and summarize comments on an asset
/frameio:create-share      Create a share link for reviewers
```

## Plugin Structure

```
frameio/
├── .claude-plugin/plugin.json   Plugin manifest
├── .mcp.json                    MCP server configuration
├── CLAUDE.md                    Agent instructions
├── CONNECTORS.md                OAuth setup guide
├── frameio.local.md             User-specific config
├── skills/                      Domain expertise (4 skills)
│   ├── asset-management/        Upload, organize, version files
│   ├── review-workflow/         Share links, approvals, reviews
│   ├── comment-analysis/        Feedback parsing and synthesis
│   └── project-navigation/      Browse projects and folders
├── commands/                    Slash commands (4 commands)
├── agents/                      Sub-agents (3 agents)
└── mcp-server/                  Python MCP server (20 tools)
```

## Skills

| Skill | Description |
|-------|-------------|
| asset-management | Upload, download, organize, and version files |
| review-workflow | Create share links, track approvals, manage reviews |
| comment-analysis | Fetch, parse, and summarize reviewer feedback |
| project-navigation | Browse workspaces, projects, and folder trees |

## API

This plugin targets the Frame.io V4 API exclusively. It does not use the deprecated V2 API or the legacy `frameioclient` Python SDK.
