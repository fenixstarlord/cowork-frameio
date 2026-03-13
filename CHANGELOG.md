# Changelog

All notable changes to the Frame.io Cowork plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-03-12

### Added
- Initial plugin release
- 4 skills: asset-management, review-workflow, comment-analysis, project-navigation
- 4 commands: upload-asset, review-status, collect-feedback, create-share
- 3 sub-agents: upload-agent, review-coordinator, feedback-synthesizer
- MCP server with 20 tools wrapping Frame.io V4 API
- OAuth 2.0 authentication via Adobe IMS
- Rate limiting with exponential backoff
- Chunked upload with resume support
