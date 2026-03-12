# skills.sh — Agent Skills Reference

> A reusable reference for AI agents on how to search, install, and manage skills using the skills.sh ecosystem.

## What is skills.sh?

skills.sh is an open agent skills directory and CLI built by Vercel. It provides a standardized way to discover, install, and manage reusable "skill packages" for AI coding agents. Skills are self-contained instruction sets (packaged as `SKILL.md` files) that encode workflows, best practices, and domain expertise — allowing agents to load procedural knowledge on demand instead of relying on monolithic system prompts.

The CLI is `npx skills` and requires no global installation. The directory is browsable at [skills.sh](https://skills.sh).

---

## Core Concepts

A **skill** is a directory containing a `SKILL.md` file with YAML frontmatter (`name` and `description`) followed by natural-language instructions. Optional subdirectories can include `scripts/`, `references/`, and `assets/`.

Agents use **progressive disclosure**: only the skill's metadata (~50–100 tokens) is loaded at startup. The full instructions are loaded only when the agent activates the skill.

Skills are **cross-platform** — the same skill works across Claude Code, Codex, Cursor, Copilot, Windsurf, and 30+ other agents.

---

## CLI Quick Reference

### Installing Skills

```bash
# Basic install (GitHub shorthand)
npx skills add <owner/repo>

# Full GitHub URL
npx skills add https://github.com/vercel-labs/agent-skills

# Direct path to a specific skill in a repo
npx skills add https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines

# GitLab or any git URL
npx skills add https://gitlab.com/org/repo
npx skills add git@github.com:vercel-labs/agent-skills.git

# Local path
npx skills add ./my-local-skills
```

### Install Options

| Option | Description |
|--------|-------------|
| `-g, --global` | Install to user directory instead of project |
| `-a, --agent <agents...>` | Target specific agents (e.g., `claude-code`, `codex`) |
| `-s, --skill <skills...>` | Install specific skills by name (use `'*'` for all) |
| `-l, --list` | List available skills in a repo without installing |
| `--copy` | Copy files instead of symlinking |
| `-y, --yes` | Skip all confirmation prompts |
| `--all` | Install all skills to all agents without prompts |

### Install Examples

```bash
# List skills available in a repo
npx skills add vercel-labs/agent-skills --list

# Install specific skills
npx skills add vercel-labs/agent-skills --skill frontend-design --skill skill-creator

# Install to specific agents
npx skills add vercel-labs/agent-skills -a claude-code -a opencode

# Non-interactive (CI/CD friendly)
npx skills add vercel-labs/agent-skills --skill frontend-design -g -a claude-code -y

# Install all skills from a repo to all agents
npx skills add vercel-labs/agent-skills --all

# Install all skills to a specific agent
npx skills add vercel-labs/agent-skills --skill '*' -a claude-code
```

### Other Commands

| Command | Description |
|---------|-------------|
| `npx skills list` | List all installed skills (alias: `ls`) |
| `npx skills list -g` | List only globally installed skills |
| `npx skills ls -a claude-code` | Filter installed skills by agent |
| `npx skills find` | Interactive search (fzf-style) |
| `npx skills find <keyword>` | Search skills by keyword |
| `npx skills check` | Check if installed skills have updates |
| `npx skills update` | Update all installed skills to latest |
| `npx skills init` | Create a SKILL.md template in current directory |
| `npx skills init <name>` | Create a new skill in a subdirectory |
| `npx skills remove` | Interactive removal of installed skills |
| `npx skills remove <skill-name>` | Remove a specific skill |
| `npx skills remove --all` | Remove all installed skills |
| `npx skills remove <skill> -a claude-code` | Remove from a specific agent |

---

## Installation Scope

| Scope | Flag | Location | Use Case |
|-------|------|----------|----------|
| **Project** | _(default)_ | `./<agent>/skills/` | Committed with your project, shared with team |
| **Global** | `-g` | `~/<agent>/skills/` | Available across all projects |

### Installation Methods

| Method | Description |
|--------|-------------|
| **Symlink** _(recommended)_ | Creates symlinks from each agent to a canonical copy. Single source of truth, easy updates. |
| **Copy** | Independent copies for each agent. Use when symlinks aren't supported. |

---

## Supported Agents

The CLI auto-detects which coding agents you have installed. Key agents and their `--agent` flags:

| Agent | Flag | Project Path | Global Path |
|-------|------|-------------|-------------|
| Claude Code | `claude-code` | `.claude/skills/` | `~/.claude/skills/` |
| Codex | `codex` | `.agents/skills/` | `~/.codex/skills/` |
| Cursor | `cursor` | `.agents/skills/` | `~/.cursor/skills/` |
| GitHub Copilot | `github-copilot` | `.agents/skills/` | `~/.copilot/skills/` |
| Windsurf | `windsurf` | `.windsurf/skills/` | `~/.codeium/windsurf/skills/` |
| OpenCode | `opencode` | `.agents/skills/` | `~/.config/opencode/skills/` |
| Roo Code | `roo` | `.roo/skills/` | `~/.roo/skills/` |
| Cline | `cline` | `.agents/skills/` | `~/.agents/skills/` |
| Gemini CLI | `gemini-cli` | `.agents/skills/` | `~/.gemini/skills/` |
| Antigravity | `antigravity` | `.agent/skills/` | `~/.gemini/antigravity/skills/` |
| Goose | `goose` | `.goose/skills/` | `~/.config/goose/skills/` |
| Amp | `amp` | `.agents/skills/` | `~/.config/agents/skills/` |
| Trae | `trae` | `.trae/skills/` | `~/.trae/skills/` |
| Droid | `droid` | `.factory/skills/` | `~/.factory/skills/` |

The full list includes 37+ agents. If no agents are detected, the CLI prompts you to select which agents to install to.

---

## Creating Your Own Skills

A skill is a directory with a `SKILL.md` file:

```markdown
---
name: my-skill
description: What this skill does and when to use it
---

# My Skill

Instructions for the agent to follow when this skill is activated.

## When to Use

Describe the scenarios where this skill should be used.

## Steps

1. First, do this
2. Then, do that
```

### Required Frontmatter

- `name`: Unique identifier (lowercase, hyphens allowed)
- `description`: Brief explanation of what the skill does and when to trigger it

### Best Practices

- Keep `SKILL.md` under 500 lines; move detailed reference material to `references/`
- Aim for under 5,000 tokens in the main instructions
- Use `scripts/` for deterministic operations, `assets/` for templates
- Test locally with `npx skills add .`

### Publishing

There's no separate publish step. Skills appear on skills.sh automatically when people install them via the CLI. To get listed: put your skill in a public GitHub repo with a valid `SKILL.md`, then share the install command.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DISABLE_TELEMETRY` | Set to `1` to disable anonymous usage telemetry |
| `DO_NOT_TRACK` | Alternative way to disable telemetry |
| `INSTALL_INTERNAL_SKILLS` | Set to `1` to show/install skills marked as `internal: true` |

---

## Browsing the Directory

- **Homepage / Leaderboard**: [skills.sh](https://skills.sh) — ranked by install count
- **Trending (24h)**: [skills.sh/trending](https://skills.sh/trending)
- **Hot**: [skills.sh/hot](https://skills.sh/hot)
- **Docs**: [skills.sh/docs](https://skills.sh/docs)
- **Security Audits**: [skills.sh/audits](https://skills.sh/audits)

---

## Related Links

- [Agent Skills Specification](https://agentskills.io)
- [GitHub: vercel-labs/skills](https://github.com/vercel-labs/skills) (the CLI source)
- [GitHub: vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) (Vercel's official skill collection)
- [Claude Code Skills Docs](https://code.claude.com/docs/en/skills)
- [Codex Skills Docs](https://developers.openai.com/codex/skills)
- [Cursor Skills Docs](https://cursor.com/docs/context/skills)
