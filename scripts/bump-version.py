#!/usr/bin/env python3
"""bump-version.py — Update version across all plugin files from VERSION file.

Usage:
    python scripts/bump-version.py [<new-version>]

If <new-version> is provided, VERSION is updated first.
If omitted, the current VERSION file value is synced to all locations.

Cross-platform replacement for bump-version.sh.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = PLUGIN_ROOT / "VERSION"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$")


def update_file(path: Path, pattern: str, replacement: str) -> bool:
    """Replace the first match of *pattern* in *path* with *replacement*.

    Returns True if the file was updated, False if the file was not found.
    """
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    new_text = re.sub(pattern, replacement, text)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
    return True


def main() -> None:
    if not VERSION_FILE.exists():
        print(f"Error: VERSION file not found at {VERSION_FILE}", file=sys.stderr)
        sys.exit(1)

    # Optionally accept a new version as argument
    if len(sys.argv) >= 2:
        new_version = sys.argv[1]
        if not SEMVER_RE.match(new_version):
            print(
                f"Error: Invalid version format '{new_version}'. "
                "Expected semver (e.g., 1.2.3 or 1.2.3-beta.1)",
                file=sys.stderr,
            )
            sys.exit(1)
        VERSION_FILE.write_text(new_version + "\n", encoding="utf-8")

    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    print(f"Syncing version: {version}")

    # 1. plugin.json
    plugin_json = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
    if update_file(plugin_json, r'"version": "[^"]*"', f'"version": "{version}"'):
        print(f"  Updated {plugin_json}")

    # 2. pyproject.toml
    pyproject = PLUGIN_ROOT / "mcp-server" / "pyproject.toml"
    if update_file(pyproject, r'^version = "[^"]*"', f'version = "{version}"'):
        print(f"  Updated {pyproject}")

    # 3. __init__.py
    init_py = PLUGIN_ROOT / "mcp-server" / "src" / "frameio_mcp" / "__init__.py"
    if update_file(init_py, r'__version__ = "[^"]*"', f'__version__ = "{version}"'):
        print(f"  Updated {init_py}")

    # 4. CLAUDE.md (version in Identity section)
    claude_md = PLUGIN_ROOT / "CLAUDE.md"
    if update_file(
        claude_md,
        r"\(v\d+\.\d+\.\d+[^)]*\)",
        f"(v{version})",
    ):
        print(f"  Updated {claude_md}")

    print(f"Done. All files now at version {version}.")


if __name__ == "__main__":
    main()
