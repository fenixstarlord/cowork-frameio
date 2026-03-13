"""Frame.io MCP Server - V4 API integration for Claude Cowork."""

from pathlib import Path


def _read_version() -> str:
    """Read version from the VERSION file (single source of truth)."""
    version_file = Path(__file__).resolve().parent.parent.parent.parent / "VERSION"
    try:
        return version_file.read_text().strip()
    except FileNotFoundError:
        return "0.0.0"


__version__ = _read_version()
