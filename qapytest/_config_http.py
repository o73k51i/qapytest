"""Module for config httpx Client."""

import json
import logging
import re

from httpx import Client, Response

from qapytest._config import AnyType


class BaseHttpClient(Client):
    """Base HTTP client with detailed logging and sensitive data masking."""

    def __init__(
        self,
        base_url: str = "",
        headers: dict[str, str] | None = None,
        verify: bool = True,
        timeout: float = 10.0,
        sensitive_headers: set[str] | None = None,
        sensitive_json_fields: set[str] | None = None,
        sensitive_text_patterns: list[str] | None = None,
        mask_sensitive_data: bool = True,
        name_logger: str = "HttpClient",
        **kwargs,
    ) -> None:
        """Constructor for BaseHttpClient."""
        super().__init__(base_url=base_url, headers=headers, verify=verify, timeout=timeout, **kwargs)
        for name in ("httpx", "httpcore", "urllib3"):
            logging.getLogger(name).setLevel(logging.WARNING)
        self._logger = logging.getLogger(name_logger)
        self._mask_sensitive_data = mask_sensitive_data

        # Default sensitive headers
        default_sensitive_headers = {
            "authorization",
            "cookie",
            "set-cookie",
            "api-key",
            "x-api-key",
            "auth-token",
            "access-token",
        }
        if sensitive_headers is None:
            self._sensitive_headers = default_sensitive_headers
        else:
            self._sensitive_headers = default_sensitive_headers | {h.lower() for h in sensitive_headers}

        # Default sensitive JSON fields
        default_sensitive_json = {
            "password",
            "secret",
            "api_key",
            "private_key",
            "token",
            "access_token",
            "refresh_token",
            "authorization",
            "session",
        }
        if sensitive_json_fields is None:
            self._sensitive_json_fields = default_sensitive_json
        else:
            self._sensitive_json_fields = default_sensitive_json | {f.lower() for f in sensitive_json_fields}

        # Default sensitive text patterns (regex only)
        default_sensitive_text_regex = [
            r"(authorization[\"\s]*[:=][\"\s]*)(bearer\s+)([a-zA-Z0-9._-]+)",
            r"(api[_-]?key[\"\s]*[:=][\"\s]*[\"\'']?)([a-zA-Z0-9._-]+)",
            r"(password[\"\s]*[:=][\"\s]*[\"\'']?)([^\s\"\']+)",
            r"(passwd[\"\s]*[:=][\"\s]*[\"\'']?)([^\s\"\']+)",
            r"(token[\"\s]*[:=][\"\s]*[\"\'']?)([a-zA-Z0-9._-]+)",
        ]

        all_regex_patterns = default_sensitive_text_regex[:]
        if sensitive_text_patterns is not None:
            all_regex_patterns.extend(sensitive_text_patterns)

        self._sensitive_text_patterns = []
        for pattern in all_regex_patterns:
            if pattern == r"(authorization[\"\s]*[:=][\"\s]*)(bearer\s+)([a-zA-Z0-9._-]+)":
                replacement = r"\1\2***MASKED***"
            else:
                replacement = r"\1***MASKED***"
            self._sensitive_text_patterns.append((pattern, replacement))

    def _is_streaming_content_type(self, content_type: str) -> bool:
        """Check if the content type indicates streaming or binary data."""
        content_type = content_type.lower()
        streaming_types = [
            "multipart/form-data",
            "multipart/byteranges",
            "application/octet-stream",
            "video/",
            "audio/",
            "image/",
            "zip",
            "gzip",
            "text/event-stream",
        ]
        return any(st in content_type for st in streaming_types)

    def _sanitize_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """Mask sensitive headers."""
        if not self._mask_sensitive_data:
            return headers
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self._sensitive_headers:
                if len(value) > 4:
                    sanitized[key] = f"{value[:4]}***MASKED***"
                else:
                    sanitized[key] = "***MASKED***"
            else:
                sanitized[key] = value
        return sanitized

    def _mask_sensitive_json_fields(self, data: AnyType) -> AnyType:
        """Recursively mask sensitive fields in JSON data."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key.lower() in self._sensitive_json_fields:
                    if isinstance(value, str) and len(value) > 4:
                        result[key] = f"{value[:4]}***MASKED***"
                    else:
                        result[key] = "***MASKED***"
                else:
                    result[key] = self._mask_sensitive_json_fields(value)
            return result
        if isinstance(data, list):
            return [self._mask_sensitive_json_fields(item) for item in data]
        if isinstance(data, str):
            return self._mask_sensitive_text_patterns(data)
        return data

    def _mask_sensitive_text_patterns(self, content: str) -> str:
        """Mask sensitive patterns in plain text using regex."""
        if not self._mask_sensitive_data:
            return content

        result = content
        for pattern, replacement in self._sensitive_text_patterns:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result

    def _log_request(self, resp: Response) -> None:
        """Log details of the HTTP request."""
        # Connected URL and method
        self._logger.info(
            f"Sending HTTP [{resp.request.method}] request to: {resp.url.scheme}://{resp.url.host}{resp.url.path}",
        )

        # Query params
        if resp.url.params:
            sanitized_params = self._mask_sensitive_text_patterns(str(resp.url.params))
            self._logger.debug(f"Request query params: {sanitized_params}")

        # Headers
        sanitized_headers = self._sanitize_headers(dict(resp.request.headers))
        self._logger.debug(
            f"Request headers: {json.dumps(sanitized_headers, ensure_ascii=False)}",
        )

        # Body
        content_type = resp.request.headers.get("Content-Type", "")

        if self._is_streaming_content_type(content_type):
            self._logger.debug("Request body: <binary/streaming content - not logged>")
            return

        try:
            request_content = getattr(resp.request, "content", None)
            if request_content is not None and len(request_content) > 0:
                if "application/json" in content_type:
                    try:
                        sanitized_body = self._mask_sensitive_json_fields(
                            json.loads(request_content.decode("utf-8")),
                        )
                        self._logger.debug(
                            f"Request body (JSON): {json.dumps(sanitized_body, ensure_ascii=False)}",
                        )
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        self._logger.debug(
                            f"Request body (raw bytes): {request_content}",
                        )
                elif any(ct in content_type for ct in ["text/", "application/xml", "application/html"]):
                    try:
                        sanitized_body = self._mask_sensitive_text_patterns(
                            request_content.decode("utf-8"),
                        )
                        self._logger.debug(f"Request body (text): {sanitized_body}")
                    except UnicodeDecodeError:
                        self._logger.debug(
                            f"Request body (raw bytes): {request_content}",
                        )
                else:
                    self._logger.debug(f"Request body (raw bytes): {request_content}")
            else:
                self._logger.debug("Request body: <empty>")
        except Exception as e:
            self._logger.debug(f"Request body: not logged, reason: {type(e).__name__}")

    def _log_response(self, resp: Response) -> None:
        """Log details of the HTTP response."""
        self._logger.info(f"Response status code: {resp.status_code}")
        self._logger.info(
            f"Response time: {resp.elapsed.total_seconds():.3f} s"
            if resp.elapsed
            else "Response time: <not available>",
        )
        sanitized_headers = self._sanitize_headers(dict(resp.headers))
        self._logger.debug(
            f"Response headers: {json.dumps(sanitized_headers, ensure_ascii=False)}",
        )
        content_type = resp.headers.get("Content-Type", "")

        if self._is_streaming_content_type(content_type):
            self._logger.debug("Response body: <binary/streaming content - not logged>")
            return

        try:
            if resp.content is not None and len(resp.content) > 0:
                if "application/json" in content_type:
                    try:
                        sanitized_json = self._mask_sensitive_json_fields(resp.json())
                        self._logger.debug(
                            f"Response body (JSON): {json.dumps(sanitized_json, ensure_ascii=False)}",
                        )
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        self._logger.debug(f"Response body (raw bytes): {resp.content}")
                elif "text/" in content_type or "application/xml" in content_type or "application/html" in content_type:
                    try:
                        self._logger.debug(f"Response body (text): {resp.text}")
                    except UnicodeDecodeError:
                        self._logger.debug(f"Response body (raw bytes): {resp.content}")
                else:
                    self._logger.debug(
                        "Response body: <binary/streaming content - not logged>",
                    )
            else:
                self._logger.debug("Response body: <empty>")
        except Exception as e:
            self._logger.debug(f"Response body: not logged, reason: {type(e).__name__}")

    def request(self, *args, **kwargs) -> Response:
        """Root method to perform HTTP requests with logging."""
        response = super().request(*args, **kwargs)
        self._log_request(response)
        self._log_response(response)
        return response
