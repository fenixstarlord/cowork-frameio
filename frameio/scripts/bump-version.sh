#!/usr/bin/env bash
set -euo pipefail

# bump-version.sh — Update version across all plugin files from VERSION file.
#
# Usage:
#   ./scripts/bump-version.sh [<new-version>]
#
# If <new-version> is provided, VERSION is updated first.
# If omitted, the current VERSION file value is synced to all locations.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

VERSION_FILE="$PLUGIN_ROOT/VERSION"

if [ ! -f "$VERSION_FILE" ]; then
    echo "Error: VERSION file not found at $VERSION_FILE" >&2
    exit 1
fi

# If a new version was passed, write it to VERSION first
if [ $# -ge 1 ]; then
    NEW_VERSION="$1"
    # Validate semver format (major.minor.patch with optional pre-release)
    if ! echo "$NEW_VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$'; then
        echo "Error: Invalid version format '$NEW_VERSION'. Expected semver (e.g., 1.2.3 or 1.2.3-beta.1)" >&2
        exit 1
    fi
    echo "$NEW_VERSION" > "$VERSION_FILE"
fi

VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"
echo "Syncing version: $VERSION"

# 1. plugin.json
PLUGIN_JSON="$PLUGIN_ROOT/.claude-plugin/plugin.json"
if [ -f "$PLUGIN_JSON" ]; then
    tmp=$(mktemp)
    sed "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/" "$PLUGIN_JSON" > "$tmp" && mv "$tmp" "$PLUGIN_JSON"
    echo "  Updated $PLUGIN_JSON"
fi

# 2. pyproject.toml
PYPROJECT="$PLUGIN_ROOT/mcp-server/pyproject.toml"
if [ -f "$PYPROJECT" ]; then
    tmp=$(mktemp)
    sed "s/^version = \"[^\"]*\"/version = \"$VERSION\"/" "$PYPROJECT" > "$tmp" && mv "$tmp" "$PYPROJECT"
    echo "  Updated $PYPROJECT"
fi

# 3. __init__.py
INIT_PY="$PLUGIN_ROOT/mcp-server/src/frameio_mcp/__init__.py"
if [ -f "$INIT_PY" ]; then
    tmp=$(mktemp)
    sed "s/__version__ = \"[^\"]*\"/__version__ = \"$VERSION\"/" "$INIT_PY" > "$tmp" && mv "$tmp" "$INIT_PY"
    echo "  Updated $INIT_PY"
fi

# 4. CLAUDE.md (plugin-level, version in Identity section)
CLAUDE_MD="$PLUGIN_ROOT/CLAUDE.md"
if [ -f "$CLAUDE_MD" ]; then
    tmp=$(mktemp)
    sed "s/(v[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*[^)]*)/(v$VERSION)/" "$CLAUDE_MD" > "$tmp" && mv "$tmp" "$CLAUDE_MD"
    echo "  Updated $CLAUDE_MD"
fi

echo "Done. All files now at version $VERSION."
