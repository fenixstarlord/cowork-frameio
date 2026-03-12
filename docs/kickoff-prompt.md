Read the CLAUDE.md in the project root. It defines a 3-wave parallel build strategy for a Frame.io Cowork plugin. Also read docs/frameio-v4-api-reference.md, docs/skills-sh-reference.md, and docs/frameio-plugin-spec.docx (especially Appendix A for the CLAUDE.md draft, Appendix C for the sample skill, and Appendix D for edge cases).

Execute all 3 waves:

**Wave 1**: Scaffold the full directory structure under frameio/, write all config files (plugin.json, .mcp.json, CLAUDE.md from Appendix A, CONNECTORS.md, frameio.local.md, README.md, CHANGELOG.md), write setup.sh and pyproject.toml, create all Python stubs so uv pip install -e . succeeds. Then run skills discovery: use `npx skills find` to search for relevant community skills (frameio, video-review, media-upload, oauth, api-client, mcp-server) and install any useful ones. See docs/skills-sh-reference.md for CLI usage. This must complete before Wave 2 starts.

**Wave 2**: Launch 4 sub-agents in parallel:
- Agent A: Write all 4 skill SKILL.md files (check installed community skills for patterns first, use Appendix C as the quality bar for asset-management, match that quality for the other 3)
- Agent B: Write all 4 command .md files
- Agent C: Write all 3 agent .md files
- Agent D: Build the full MCP server in Python — check installed community skills for MCP/API patterns first, then implement all 20 tools, auth, rate limiting, error handling, and tests

**Wave 3**: Once Wave 2 completes, run the full validation checklist from the CLAUDE.md acceptance criteria and output a markdown report with pass/fail for every item.

Use docs/frameio-v4-api-reference.md as the API reference for all endpoint implementations. Do not search the web for API details — everything is in the local docs.
