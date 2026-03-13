# Frame.io Plugin for Claude Cowork

Video review and collaboration workflows powered by the Frame.io V4 API.

## Prerequisites

- [Adobe Developer Console](https://developer.adobe.com/console) account with Frame.io API access
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (installed automatically by `setup.sh`)

## Installation

### Install via URL (recommended)

Install directly in Claude Cowork using the GitHub repository URL:

```
https://github.com/fenixstarlord/cowork-frameio
```

In Cowork, use the plugin installer and provide the URL above. Cowork will clone the repository and register the `frameio/` directory as a plugin automatically.

### Install manually

1. Clone or copy the `frameio/` directory into your Cowork plugins folder.

### Post-install configuration

1. Configure OAuth credentials — see [CONNECTORS.md](CONNECTORS.md) for full setup:
   ```bash
   # Edit .mcp.json with your Adobe Developer Console credentials
   vim .mcp.json
   ```

2. Set your account details in `frameio.local.md`:
   ```
   account_id: <your-account-id>
   workspace_id: <your-workspace-id>
   ```

3. The MCP server starts automatically via `setup.sh` when Claude connects.

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

This plugin targets the Frame.io V4 API exclusively.

## Disclaimer

This software was vibe coded with reckless optimism and minimal understanding of what's actually happening under the hood. The developer (generous term) cannot guarantee that anything works, will continue to work, or ever worked in the first place. Use at your own risk, amusement, or horror. By the way, this disclaimer was AI-generated, because that's how not involved I am in this code.
