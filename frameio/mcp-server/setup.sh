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

# Sync VERSION into manifest files before install
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
if [ -f "$PLUGIN_DIR/scripts/bump-version.sh" ]; then
    bash "$PLUGIN_DIR/scripts/bump-version.sh"
fi

uv pip install -e . --quiet

exec uv run python -m frameio_mcp.server
