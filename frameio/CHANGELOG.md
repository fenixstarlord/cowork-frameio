# Changelog

All notable changes to the Frame.io Cowork plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-03-13

### Added
- VERSION file as single source of truth for version strings
- `scripts/bump-version.sh` to sync VERSION into manifests and bump with semver validation
- Runtime version reading in `__init__.py` from VERSION file
- Version sync step in `setup.sh` before package installation

### Changed
- Reset version to 0.1.0 to reflect pre-release status (previously declared as 1.0.0)

## [0.0.3] - 2026-03-12

### Changed
- Added URL-based installation support for the Cowork plugin (PR #2)

## [0.0.2] - 2026-03-12

### Fixed
- Removed all V2 legacy API references from plugin documentation (PR #1)

## [0.0.1] - 2026-03-11

### Added
- Initial project scaffolding and documentation
- Frame.io Cowork plugin with full MCP server (20 tools wrapping V4 API)
- 4 skills: asset-management, review-workflow, comment-analysis, project-navigation
- 4 commands: upload-asset, review-status, collect-feedback, create-share
- 3 sub-agents: upload-agent, review-coordinator, feedback-synthesizer
- OAuth 2.0 authentication via Adobe IMS
- Rate limiting with leaky bucket and exponential backoff
- Chunked upload with resume/checkpoint support
- Plugin manifest (plugin.json), MCP config (.mcp.json)
- CLAUDE.md with agent instructions (7 sections)
- CONNECTORS.md with Adobe Developer Console setup guide
- README.md with installation and quick-start guide
