"""OAuth 2.0 authentication via Adobe IMS. Token storage and refresh."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

ADOBE_IMS_BASE = "https://ims-na1.adobelogin.com"
AUTHORIZE_URL = f"{ADOBE_IMS_BASE}/ims/authorize/v2"
TOKEN_URL = f"{ADOBE_IMS_BASE}/ims/token/v3"
SCOPES = "openid,AdobeID,frameio.apps.readwrite"
DEFAULT_TOKEN_PATH = os.path.expanduser("~/.frameio/tokens.json")

# Token is refreshed when it will expire within this many seconds
REFRESH_BUFFER_S = 300  # 5 minutes


class TokenStore:
    """Manages OAuth token persistence and refresh.

    Tokens are stored at ``FRAMEIO_TOKEN_PATH`` (default ``~/.frameio/tokens.json``).
    The file is created with restricted permissions (0600).
    """

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or os.environ.get("FRAMEIO_TOKEN_PATH", DEFAULT_TOKEN_PATH))
        self._tokens: dict[str, Any] = {}
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._tokens = json.loads(self.path.read_text())
            except (json.JSONDecodeError, OSError):
                self._tokens = {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._tokens, indent=2))
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Token access
    # ------------------------------------------------------------------

    def store(
        self,
        access_token: str,
        refresh_token: str,
        expires_in: int,
    ) -> None:
        """Persist a new token pair."""
        self._tokens = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": time.time() + expires_in,
        }
        self._save()

    @property
    def access_token(self) -> str | None:
        return self._tokens.get("access_token")

    @property
    def refresh_token(self) -> str | None:
        return self._tokens.get("refresh_token")

    @property
    def is_expired(self) -> bool:
        expires_at = self._tokens.get("expires_at", 0)
        return time.time() >= (expires_at - REFRESH_BUFFER_S)

    @property
    def has_tokens(self) -> bool:
        return bool(self._tokens.get("access_token"))

    def clear(self) -> None:
        self._tokens = {}
        if self.path.exists():
            try:
                self.path.unlink()
            except OSError:
                pass


class AuthManager:
    """Handles the full OAuth lifecycle: authorization URL, code exchange, refresh."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        token_path: str | None = None,
        redirect_uri: str = "http://localhost:9898/callback",
    ) -> None:
        self.client_id = client_id or os.environ.get("FRAMEIO_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("FRAMEIO_CLIENT_SECRET", "")
        self.redirect_uri = redirect_uri
        self.token_store = TokenStore(path=token_path)

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def get_authorization_url(self) -> str:
        """Build the Adobe IMS authorization URL for the user to visit."""
        return (
            f"{AUTHORIZE_URL}"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope={SCOPES}"
            f"&response_type=code"
        )

    async def exchange_code(self, code: str) -> dict[str, Any]:
        """Exchange an authorization code for tokens."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        self.token_store.store(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_in=data.get("expires_in", 86400),
        )
        return {"authenticated": True}

    async def refresh(self) -> bool:
        """Refresh the access token using the stored refresh token.

        Returns True on success, False on failure.
        """
        rt = self.token_store.refresh_token
        if not rt:
            return False

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    TOKEN_URL,
                    data={
                        "grant_type": "refresh_token",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": rt,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            self.token_store.store(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", rt),
                expires_in=data.get("expires_in", 86400),
            )
            return True
        except (httpx.HTTPStatusError, KeyError, httpx.RequestError):
            logger.warning("Token refresh failed")
            return False

    async def get_valid_token(self) -> str:
        """Return a valid access token, refreshing if necessary.

        Raises AuthExpiredError if no valid token can be obtained.
        """
        from frameio_mcp.utils.errors import AuthExpiredError

        if not self.token_store.has_tokens:
            raise AuthExpiredError(
                "Not authenticated. Visit the authorization URL to connect Frame.io."
            )

        if self.token_store.is_expired:
            success = await self.refresh()
            if not success:
                raise AuthExpiredError(
                    "Token refresh failed. Please re-authenticate with Frame.io."
                )

        token = self.token_store.access_token
        if not token:
            raise AuthExpiredError("No access token available.")
        return token
