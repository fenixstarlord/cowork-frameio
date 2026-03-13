#!/usr/bin/env bash
# Reads the version from frameio/VERSION and updates all manifest files
# to keep version strings in sync. Run before packaging or installing.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION_FILE="$SCRIPT_DIR/VERSION"

if [ ! -f "$VERSION_FILE" ]; then
    echo "ERROR: VERSION file not found at $VERSION_FILE" >&2
    exit 1
fi

VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"

if [ -z "$VERSION" ]; then
    echo "ERROR: VERSION file is empty" >&2
    exit 1
fi

echo "Syncing version $VERSION into manifests..."

# Update plugin.json
PLUGIN_JSON="$SCRIPT_DIR/.claude-plugin/plugin.json"
if [ -f "$PLUGIN_JSON" ]; then
    tmp=$(mktemp)
    python3 -c "
import json, sys
with open('$PLUGIN_JSON') as f:
    data = json.load(f)
data['version'] = '$VERSION'
with open('$tmp', 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
"
    mv "$tmp" "$PLUGIN_JSON"
    echo "  Updated $PLUGIN_JSON"
fi

# Update pyproject.toml
PYPROJECT="$SCRIPT_DIR/mcp-server/pyproject.toml"
if [ -f "$PYPROJECT" ]; then
    sed -i "s/^version = \".*\"/version = \"$VERSION\"/" "$PYPROJECT"
    echo "  Updated $PYPROJECT"
fi

echo "Version sync complete."
