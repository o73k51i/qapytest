"""Module for convenient interaction with HTTP APIs using httpx."""

import json
import logging
import re

from httpx import Client, QueryParams, Response

from qapytest._config import AnyType


class HttpClient(Client):
    """Client for convenient interaction with HTTP APIs, extending `httpx.Client`.

    This class inherits all the functionality of the standard `httpx.Client`,
    adding automatic and structured logging for each request and response.
    It also suppresses the default logs from the `httpx` and `httpcore` libraries,
    leaving only clean output from its own logger "HttpClient".

    This is a tool for API testing.

    Args:
        base_url: Base URL for all requests. Default is an empty string.
        verify: Whether to verify SSL certificates. Default is True.
        timeout: Overall timeout for requests in seconds. Default is 10.0 seconds.
        max_log_size: Maximum size in bytes for logged request/response bodies.
                      Bodies larger than this will be truncated. Default is 1024 bytes.
        sensitive_headers: Set of header names to mask in logs.
                           If None, uses default sensitive headers.
        sensitive_json_fields: Set of JSON field names to mask in logs.
                               If None, uses default sensitive fields.
        mask_sensitive_data: Whether to mask sensitive data in logs. Default is True.
        **kwargs: Additional arguments passed directly to the constructor of the base
                 `httpx.Client` class (e.g., `headers`, `cookies`, `proxies`).

    ---
    ### Example usage:

    ```python
    # 1. Initialize the client with a base URL
    # We use jsonplaceholder as an example
    api_client = HttpClient(base_url="https://jsonplaceholder.typicode.com")

    # 2. Perform a GET request
    response_get = api_client.get("/posts/1")

    # 3. Perform a POST request with a body
    new_post = {"title": "foo", "body": "bar", "userId": 1}
    response_post = api_client.post("/posts", json=new_post)

    # 4. Perform a PUT request to update a resource
    updated_post = {"id": 1, "title": "updated title", "body": "updated body", "userId": 1}
    response_put = api_client.put("/posts/1", json=updated_post)

    # 5. Perform a DELETE request to remove a resource
    response_delete = api_client.delete("/posts/1")
    ```
    """

    def __init__(
        self,
        base_url: str = "",
        verify: bool = True,
        timeout: float = 10.0,
        max_log_size: int = 1024,
        sensitive_headers: set[str] | None = None,
        sensitive_json_fields: set[str] | None = None,
        mask_sensitive_data: bool = True,
        **kwargs,
    ) -> None:
        """Constructor for HttpClient.

        Args:
            base_url: Base URL for all requests. Default is an empty string.
            verify: Whether to verify SSL certificates. Default is True.
            timeout: Overall timeout for requests in seconds. Default is 10.0 seconds.
            max_log_size: Maximum size in bytes for logged request/response bodies. Default is 1024 bytes.
            sensitive_headers: Set of header names to mask in logs. If None, uses default sensitive headers.
            sensitive_json_fields: Set of JSON field names to mask in logs. If None, uses default sensitive fields.
            mask_sensitive_data: Whether to mask sensitive data in logs. Default is True.
            **kwargs: Standard arguments for the `httpx.Client` constructor.
        """
        super().__init__(base_url=base_url, verify=verify, timeout=timeout, **kwargs)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        self._logger = logging.getLogger("HttpClient")
        self._max_log_size = max_log_size
        self._mask_sensitive_data = mask_sensitive_data

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
            self._sensitive_headers = {h.lower() for h in sensitive_headers}

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
            self._sensitive_json_fields = {f.lower() for f in sensitive_json_fields}

    def _truncate_content(self, content: bytes | str) -> str:
        """Truncate content to max_log_size and add summary information."""
        if isinstance(content, bytes | bytearray | memoryview):
            content_bytes = bytes(content) if not isinstance(content, bytes) else content
            original_size = len(content_bytes)
            if original_size > self._max_log_size:
                truncated = content_bytes[: self._max_log_size].decode("utf-8", errors="replace")
                return f"{truncated}... <truncated, total size: {original_size} bytes>"
            return content_bytes.decode("utf-8", errors="replace")
        if isinstance(content, str):
            original_size = len(content.encode("utf-8"))
            if original_size > self._max_log_size:
                content_bytes = content.encode("utf-8")
                truncated = content_bytes[: self._max_log_size].decode("utf-8", errors="ignore")
                return f"{truncated}... <truncated, total size: {original_size} bytes>"
            return content
        return str(content)

    def _sanitize_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """Sanitize headers by masking sensitive values."""
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

    def _format_headers(self, headers: dict[str, str]) -> str:
        """Format headers for logging with smart formatting based on size."""
        headers_str = str(headers)
        if len(headers_str) > 150 or "\n" in headers_str:
            formatted_lines = [f"    {key}: {value}" for key, value in headers.items()]
            return "{\n" + ",\n".join(formatted_lines) + "\n}"
        return headers_str

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
        return data

    def _mask_sensitive_text_patterns(self, content: str) -> str:
        """Mask sensitive patterns in plain text using regex."""
        patterns = [
            # Authorization patterns
            (r"(authorization[\"\s]*[:=][\"\s]*)(bearer\s+)([a-zA-Z0-9._-]+)", r"\1\2***MASKED***"),
            (r"(api[_-]?key[\"\s]*[:=][\"\s]*[\"\'']?)([a-zA-Z0-9._-]+)", r"\1***MASKED***"),
            # Password patterns
            (r"(password[\"\s]*[:=][\"\s]*[\"\'']?)([^\s\"\']+)", r"\1***MASKED***"),
            (r"(passwd[\"\s]*[:=][\"\s]*[\"\'']?)([^\s\"\']+)", r"\1***MASKED***"),
            # Token patterns
            (r"(token[\"\s]*[:=][\"\s]*[\"\'']?)([a-zA-Z0-9._-]+)", r"\1***MASKED***"),
        ]
        result = content
        if self._mask_sensitive_data:
            for pattern, replacement in patterns:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result

    def _sanitize_json_content(self, content: str) -> str:
        """Sanitize JSON content, falling back to text sanitization."""
        if not self._mask_sensitive_data:
            return content
        try:
            data = json.loads(content)
            sanitized_data = self._mask_sensitive_json_fields(data)
            if len(content) > 100 or "\n" in content:
                return json.dumps(sanitized_data, indent=2, ensure_ascii=False)
            return json.dumps(sanitized_data, separators=(",", ":"))
        except (json.JSONDecodeError, TypeError):
            return self._mask_sensitive_text_patterns(content)

    def _sanitize_url_params(self, params: QueryParams) -> QueryParams:
        """Sanitize query parameters by masking sensitive values."""
        if not self._mask_sensitive_data:
            return params

        sensitive_keys = {"access_token", "api_key", "auth_token", "secret", "token"}

        sanitized_items = []
        for key, value in params.multi_items():
            if key.lower() in sensitive_keys:
                sanitized_items.append((key, "***MASKED***"))
            else:
                sanitized_items.append((key, value))

        return QueryParams(sanitized_items)

    def _safe_read_content(self, content_source: bytes | str | None) -> str:
        """Safely read content without consuming streams."""
        try:
            if hasattr(content_source, "read") or (
                hasattr(content_source, "__iter__") and not isinstance(content_source, str | bytes)
            ):
                return "<streaming content - not consumed>"
            if content_source is None:
                return ""
            truncated_body = self._truncate_content(content_source)
            return self._sanitize_json_content(truncated_body)
        except Exception as e:
            return f"<error reading content - {type(e).__name__}>"

    def _safe_get_response_preview(self, response: Response) -> str:
        """Get a safe preview of response content."""
        try:
            if "content-length" in response.headers:
                try:
                    length = int(response.headers["content-length"])
                    if length > self._max_log_size * 10:
                        return f"<large response body - {length} bytes - not logged for performance>"
                except ValueError:
                    pass
            content_type = response.headers.get("content-type", "").lower()
            streaming_types = [
                "application/octet-stream",
                "video/",
                "audio/",
                "image/",
                "zip",
                "gzip",
                "text/event-stream",
            ]
            if any(st in content_type for st in streaming_types):
                return f"<streaming content type '{content_type}' - not logged>"
            return self._safe_read_content(response.text)
        except Exception as e:
            return f"<error reading response - {type(e).__name__}>"

    def request(self, *args, **kwargs) -> Response:
        """Performs an HTTP request with automatic logging of details."""
        response = super().request(*args, **kwargs)

        url = response.url
        method = response.request.method

        self._logger.info(
            f"Sending HTTP [{method}] request to {url.scheme}://{url.host}{url.path}",
        )

        if url.params:
            sanitized_params = self._sanitize_url_params(url.params)
            self._logger.debug(f"Query parameters:\n{sanitized_params}")

        sanitized_req_headers = self._sanitize_headers(dict(response.request.headers))
        formatted_req_headers = self._format_headers(sanitized_req_headers)
        self._logger.debug(f"Request headers:\n{formatted_req_headers}")

        request_body_log = self._safe_read_content(response.request.content)
        if request_body_log:
            self._logger.debug(f"Request body:\n{request_body_log}")

        self._logger.info(f"Response status code: {response.status_code}")
        self._logger.info(f"Response time: {response.elapsed.total_seconds():.3f} s")

        sanitized_res_headers = self._sanitize_headers(dict(response.headers))
        formatted_res_headers = self._format_headers(sanitized_res_headers)
        self._logger.debug(f"Response headers:\n{formatted_res_headers}")

        response_body_log = self._safe_get_response_preview(response)
        if response_body_log:
            self._logger.debug(f"Response body:\n{response_body_log}")

        return response
