"""Standardized error handling for Frame.io API and S3 upload errors."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any


class FrameIOError(Exception):
    """Base error for all Frame.io API errors."""

    def __init__(
        self,
        message: str,
        code: int = 500,
        error_type: str = "server_error",
        retry_after_ms: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.error_type = error_type
        self.retry_after_ms = retry_after_ms

    def to_dict(self) -> dict[str, Any]:
        """Convert to the standardized MCP error response dict."""
        return format_error_response(
            code=self.code,
            error_type=self.error_type,
            message=self.message,
            retry_after_ms=self.retry_after_ms,
        )


class AuthExpiredError(FrameIOError):
    """401 — token expired or invalid."""

    def __init__(self, message: str = "Authentication token expired or invalid") -> None:
        super().__init__(message, code=401, error_type="auth_expired")


class PermissionDeniedError(FrameIOError):
    """403 — insufficient permissions."""

    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message, code=403, error_type="permission_denied")


class NotFoundError(FrameIOError):
    """404 — resource not found."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, code=404, error_type="not_found")


class RateLimitError(FrameIOError):
    """429 — rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after_ms: int = 1000) -> None:
        super().__init__(
            message, code=429, error_type="rate_limit_exceeded", retry_after_ms=retry_after_ms
        )


class ServerError(FrameIOError):
    """5xx — Frame.io server error."""

    def __init__(self, message: str = "Frame.io server error", code: int = 500) -> None:
        super().__init__(message, code=code, error_type="server_error")


class UploadFailedError(FrameIOError):
    """Upload to S3 failed."""

    def __init__(self, message: str = "Upload failed") -> None:
        super().__init__(message, code=500, error_type="upload_failed")


class ValidationError(FrameIOError):
    """422 — validation error."""

    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(message, code=422, error_type="validation_error")


def format_error_response(
    code: int,
    error_type: str,
    message: str,
    retry_after_ms: int | None = None,
) -> dict[str, Any]:
    """Build the standardized error dict returned by MCP tools."""
    resp: dict[str, Any] = {
        "error": True,
        "code": code,
        "type": error_type,
        "message": message,
    }
    if retry_after_ms is not None:
        resp["retry_after_ms"] = retry_after_ms
    return resp


# Mapping of HTTP status codes to error classes
_STATUS_MAP: dict[int, type[FrameIOError]] = {
    401: AuthExpiredError,
    403: PermissionDeniedError,
    404: NotFoundError,
    429: RateLimitError,
    422: ValidationError,
}


def parse_api_error(status_code: int, body: dict[str, Any] | None = None) -> FrameIOError:
    """Parse a Frame.io API JSON error response into the appropriate exception.

    The API returns errors in the shape:
    {"errors": [{"detail": "...", "title": "...", "source": {"pointer": "..."}}]}
    """
    detail = ""
    if body:
        errors = body.get("errors", [])
        if errors and isinstance(errors, list):
            first = errors[0]
            detail = first.get("detail", "") or first.get("title", "")
        if not detail:
            detail = body.get("message", "") or body.get("error", "")

    detail = detail or f"API error {status_code}"

    # Handle 429 specially to extract retry-after
    if status_code == 429:
        return RateLimitError(message=detail)

    error_cls = _STATUS_MAP.get(status_code)
    if error_cls is not None:
        return error_cls(message=detail)

    if 500 <= status_code < 600:
        return ServerError(message=detail, code=status_code)

    return FrameIOError(message=detail, code=status_code, error_type="api_error")


def parse_s3_error(xml_body: str | bytes) -> UploadFailedError:
    """Parse an S3 XML error response into an UploadFailedError.

    S3 returns XML like:
    <Error>
      <Code>AccessDenied</Code>
      <Message>Request has expired</Message>
      ...
    </Error>
    """
    try:
        root = ET.fromstring(xml_body if isinstance(xml_body, str) else xml_body.decode("utf-8"))
        code_el = root.find("Code")
        msg_el = root.find("Message")
        s3_code = code_el.text if code_el is not None and code_el.text else "Unknown"
        s3_msg = msg_el.text if msg_el is not None and msg_el.text else "S3 upload error"
        return UploadFailedError(message=f"S3 error ({s3_code}): {s3_msg}")
    except ET.ParseError:
        text = xml_body if isinstance(xml_body, str) else xml_body.decode("utf-8", errors="replace")
        return UploadFailedError(message=f"S3 error (unparseable): {text[:200]}")
