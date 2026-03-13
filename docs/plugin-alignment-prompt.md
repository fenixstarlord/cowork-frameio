# Cowork Plugin Documentation Alignment Prompt

Use this prompt with another Claude Code instance working on a different Cowork plugin. Copy everything below the line and paste it as a message.

---

## Task: Align this Cowork plugin with the official Claude Code plugin documentation

You need to audit this plugin against the official Claude Code plugin specs and fix any misalignments. Follow this exact workflow.

### Step 1: Fetch the official documentation

Fetch ALL of these pages and extract the full content. Do them in parallel:

1. **Plugin creation guide**: https://code.claude.com/docs/en/plugins
   - Extract: plugin structure, manifest format, component locations, testing instructions

2. **Plugins reference**: https://code.claude.com/docs/en/plugins-reference
   - Extract: complete plugin.json schema, directory structure, component specs, CLI commands, debugging tools, environment variables

3. **Skills documentation**: https://code.claude.com/docs/en/skills
   - Extract: SKILL.md format, ALL frontmatter fields (name, description, disable-model-invocation, user-invocable, allowed-tools, model, context, agent, hooks, argument-hint), $ARGUMENTS substitution, supporting files, invocation control

4. **Subagents documentation**: https://code.claude.com/docs/en/sub-agents
   - Extract: agent markdown format, ALL frontmatter fields (name, description, tools, disallowedTools, model, permissionMode, maxTurns, skills, mcpServers, hooks, memory, background, isolation), built-in agents, scoping rules

5. **Knowledge work plugins repo**: https://github.com/anthropics/knowledge-work-plugins
   - Extract: directory structure patterns, how official Anthropic plugins are organized

6. **Hooks documentation**: https://code.claude.com/docs/en/hooks
   - Extract: hook events (PreToolUse, PostToolUse, SessionStart, SubagentStart, etc.), hook types (command, prompt, agent), exit codes, input schemas

7. **MCP documentation**: https://code.claude.com/docs/en/mcp
   - Extract: MCP server configuration format, stdio/http/sse transport types, environment variables, server lifecycle

8. **Plugin marketplaces**: https://code.claude.com/docs/en/plugin-marketplaces
   - Extract: marketplace.json format, distribution patterns, versioning requirements

9. **Discover and install plugins**: https://code.claude.com/docs/en/discover-plugins
   - Extract: installation scopes (user, project, local, managed), team marketplace configuration

**Additional reference repos on GitHub:**
- https://github.com/anthropics/knowledge-work-plugins — 11 official Anthropic plugins (sales, legal, finance, etc.)
- https://github.com/anthropics/financial-services-plugins — Financial data partner plugins
- https://github.com/anthropics/claude-plugins-official — Curated plugin directory
- https://github.com/anthropics/claude-code/tree/main/plugins — Example plugins from Claude Code repo
- https://github.com/ComposioHQ/awesome-claude-plugins — Community curated plugin list

Save key findings as you read — you'll need them for the audit.

### Step 2: Audit the current plugin

Explore the entire plugin directory structure. Read every file. Build a complete inventory:

**Configuration files:**
- [ ] `.claude-plugin/plugin.json` — Does it have: name (required), version, description, author? Does `name` use kebab-case?
- [ ] `.mcp.json` — Does it exist? Is the server config valid (type, command, args, env)?
- [ ] `settings.json` — Does it exist? Is it needed?

**CLAUDE.md:**
- [ ] Does `CLAUDE.md` contain runtime agent instructions (domain knowledge, safety rules, terminology)?
- [ ] Or does it contain build/development instructions that should be in a different file?
- [ ] Is there a separate file (like PLUGIN_CLAUDE.md or similar) that has the actual agent instructions?
- **Key rule**: CLAUDE.md is loaded as persistent context when the plugin is active. It MUST contain agent instructions, NOT build specs.

**Skills (skills/\*/SKILL.md):**
For each skill, check the frontmatter against the official spec:
- [ ] `name` — present?
- [ ] `description` — present and descriptive enough for Claude to know when to auto-invoke?
- [ ] `allowed-tools` — MISSING? Should list only the tools this skill needs (MCP tool names + built-in tools like Read, Grep, Glob)
- [ ] `disable-model-invocation` — should it be `true`? (Yes if the skill has side effects)
- [ ] `user-invocable` — should it be `false`? (Yes if it's background knowledge only)
- [ ] `argument-hint` — would it benefit from showing expected args in autocomplete?
- [ ] `model` — does it need a specific model override?
- [ ] `context` — should it run in a forked subagent (`context: fork`)?

**Commands (commands/\*.md):**
For each command, check:
- [ ] `description` — present?
- [ ] `disable-model-invocation: true` — MUST be present for commands with side effects (uploads, deletions, sending messages, creating external resources). The official docs say: "Use disable-model-invocation: true for workflows with side effects or that you want to control timing."
- [ ] `argument-hint` — would it benefit from autocomplete hints?
- [ ] Does it have Inputs, Workflow, Expected Output sections?
- [ ] Does it document auth handling?

**Agents (agents/\*.md):**
For each agent, check the frontmatter:
- [ ] `name` — present? (required)
- [ ] `description` — present? (required) Does it include delegation trigger language?
- [ ] `model` — set appropriately? (sonnet, opus, haiku, inherit)
- [ ] `tools` — lists Claude Code built-in tools the agent needs (Read, Write, Edit, Bash, Grep, Glob)
- [ ] `mcpServers` — MISSING? Should reference MCP servers by name so the agent has access to MCP tools. Example: `mcpServers: [my-server-name]`
- [ ] `maxTurns` — MISSING? Should be set to prevent runaway agents (30-50 is typical)
- [ ] `permissionMode` — needed? (default, acceptEdits, dontAsk, bypassPermissions, plan)
- [ ] `skills` — should any skills be preloaded into this agent's context?
- [ ] `memory` — would persistent memory across sessions be useful? (user, project, local)

**Other files:**
- [ ] `README.md` — installation steps, prerequisites, quick-start
- [ ] `CHANGELOG.md` — version history
- [ ] `hooks/hooks.json` — any event handlers needed?
- [ ] `.lsp.json` — any language server configs needed?

### Step 3: Create a prioritized findings report

Organize findings into three tiers:

**P0 — Critical (breaks plugin loading or causes wrong behavior):**
- CLAUDE.md containing build instructions instead of agent instructions
- Missing or malformed plugin.json
- Broken .mcp.json configuration

**P1 — Important (safety, correctness, user experience):**
- Commands missing `disable-model-invocation: true` (allows Claude to auto-trigger side effects)
- Skills missing `allowed-tools` (gives Claude unrestricted tool access during skill)
- Agents missing `mcpServers` (may not have MCP tool access)
- Agents missing `maxTurns` (can loop indefinitely)

**P2 — Nice-to-have (polish and best practices):**
- Missing `argument-hint` on commands/skills
- Agent descriptions not optimized for delegation triggers
- Commands in `commands/` instead of `skills/` (legacy but still works)
- Missing `hooks/` for event-driven automation

### Step 4: Present the plan

Write a plan file with:
1. **Context** section explaining why changes are needed
2. **Changes by priority** with specific file paths and exact frontmatter additions
3. **Files to modify** table
4. **What does NOT need to change** section (to confirm you're not over-engineering)
5. **Verification** section describing how to test

### Step 5: Implement the changes

For each change:
1. Read the file first
2. Make the minimal edit (add frontmatter fields, swap file contents)
3. Do NOT rewrite entire files — use targeted edits
4. Do NOT add features, refactor code, or make improvements beyond what the docs require

### Step 6: Commit and push

Commit with a message like:
```
Align plugin with official Claude Code plugin documentation

- [list each category of change]
```

---

## Quick Reference: Official Frontmatter Fields

### SKILL.md frontmatter
```yaml
---
name: my-skill                        # directory name if omitted
description: What it does and when    # how Claude decides to auto-invoke
disable-model-invocation: true        # only user can invoke (for side effects)
user-invocable: false                 # only Claude can invoke (for background knowledge)
allowed-tools: Read, Grep, mcp_tool   # restrict tool access during skill
model: sonnet                         # model override
context: fork                         # run in isolated subagent
agent: Explore                        # which subagent type for context: fork
argument-hint: "[file-path]"          # autocomplete hint
hooks:                                # lifecycle hooks scoped to this skill
  PostToolUse:
    - matcher: "Edit"
      hooks:
        - type: command
          command: "./scripts/lint.sh"
---
```

### Agent frontmatter
```yaml
---
name: my-agent                        # required, kebab-case
description: When to delegate here    # required, delegation trigger
tools: Read, Write, Bash, Grep        # built-in tools allowlist
disallowedTools: Edit                 # tools to deny
model: sonnet                         # sonnet, opus, haiku, inherit
mcpServers:                           # MCP server access
  - my-server-name                    # reference by name (reuses parent connection)
maxTurns: 30                          # prevent runaway loops
permissionMode: default               # default, acceptEdits, dontAsk, bypassPermissions, plan
skills:                               # preload skill content into agent context
  - my-skill-name
memory: user                          # persistent memory: user, project, local
background: false                     # run as background task
isolation: worktree                   # isolated git worktree
hooks:                                # lifecycle hooks
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate.sh"
---

System prompt instructions go here as markdown body.
```

### Command frontmatter (same as skills)
```yaml
---
description: What this command does
disable-model-invocation: true        # ALWAYS set for commands with side effects
argument-hint: "[arg1] [arg2]"
allowed-tools: tool1, tool2
---
```

### plugin.json schema
```json
{
  "name": "my-plugin",           // required, kebab-case, becomes namespace prefix
  "version": "1.0.0",            // semver
  "description": "Brief desc",   // shown in plugin manager
  "author": {
    "name": "Name",
    "email": "email@example.com",
    "url": "https://github.com/author"
  },
  "homepage": "https://docs.example.com",
  "repository": "https://github.com/author/plugin",
  "license": "MIT",
  "keywords": ["keyword1"]
}
```

### Standard directory structure
```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # only manifest goes here
├── .mcp.json                # MCP server configs
├── CLAUDE.md                # runtime agent instructions (NOT build docs)
├── README.md
├── CHANGELOG.md
├── commands/                # slash commands (legacy, still works)
│   └── my-command.md
├── skills/                  # preferred over commands/
│   └── my-skill/
│       ├── SKILL.md
│       └── reference.md     # optional supporting files
├── agents/                  # subagent definitions
│   └── my-agent.md
├── hooks/                   # event handlers
│   └── hooks.json
├── settings.json            # default settings (only "agent" key supported)
└── .lsp.json                # language server configs
```
