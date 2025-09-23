"""Module for convenient interaction with HTTP APIs using httpx."""

import json
import logging
import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from httpx import Client, Response


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

        default_sensitive = {
            "authorization",
            "cookie",
            "set-cookie",
            "api-key",
            "x-api-key",
            "auth-token",
            "access-token",
        }

        if sensitive_headers is None:
            self._sensitive_headers = default_sensitive
        else:
            self._sensitive_headers = {header.lower() for header in sensitive_headers}

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
            self._sensitive_json_fields = {field.lower() for field in sensitive_json_fields}

    def _truncate_content(self, content: bytes | str) -> str:
        """Truncate content to max_log_size and add summary information.

        Args:
            content: Content to truncate (bytes or string)

        Returns:
            Truncated content as string with size information
        """
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
        """Sanitize headers by masking sensitive values.

        Args:
            headers: Dictionary of headers to sanitize

        Returns:
            Dictionary with sensitive headers masked
        """
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
        """Format headers for logging with smart formatting based on size.

        Args:
            headers: Dictionary of headers to format

        Returns:
            Formatted headers string (compact for small, pretty for large)
        """
        headers_str = str(headers)

        if len(headers_str) > 100:
            formatted_lines = []
            for key, value in headers.items():
                formatted_lines.append(f"  {key}: {value}")
            return "{\n" + ",\n".join(formatted_lines) + "\n}"

        return headers_str

    def _sanitize_json_content(self, content: str) -> str:
        """Sanitize JSON content by masking sensitive fields.

        Args:
            content: JSON string content to sanitize

        Returns:
            Sanitized JSON string with sensitive fields masked
        """
        if not self._mask_sensitive_data:
            return content

        try:
            data = json.loads(content)
            sanitized_data = self._mask_sensitive_json_fields(data)
            if len(content) > 100:
                return json.dumps(sanitized_data, indent=2, ensure_ascii=False)
            return json.dumps(sanitized_data, separators=(",", ":"))
        except (json.JSONDecodeError, TypeError):
            return self._mask_sensitive_text_patterns(content)

    def _mask_sensitive_json_fields(
        self,
        data: dict | list | str | int | float | bool | None,
    ) -> dict | list | str | int | float | bool | None:
        """Recursively mask sensitive fields in JSON data.

        Args:
            data: JSON data structure to sanitize

        Returns:
            Sanitized data structure
        """
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
        """Mask sensitive patterns in plain text using regex.

        Args:
            content: Text content to sanitize

        Returns:
            Text with sensitive patterns masked
        """
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
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result

    def _sanitize_url(self, url: str) -> str:
        """Sanitize URL by masking sensitive query parameters.

        Args:
            url: URL string to sanitize

        Returns:
            URL with sensitive query parameters masked
        """
        if not self._mask_sensitive_data:
            return url

        try:
            parsed = urlparse(url)

            if not parsed.query:
                return url

            query_params = parse_qs(parsed.query, keep_blank_values=True)

            sensitive_params = {
                "access_token",
                "api_key",
                "apikey",
                "auth_token",
                "authorization",
                "bearer",
                "client_secret",
                "jwt",
                "password",
                "passwd",
                "pwd",
                "secret",
                "token",
                "x-api-key",
                "private_key",
                "auth",
                "authentication",
                "credential",
                "credentials",
            }

            sanitized_params = {}
            for param_name, param_values in query_params.items():
                if param_name.lower() in sensitive_params:
                    masked_values = []
                    for value in param_values:
                        if isinstance(value, str) and len(value) > 4:
                            masked_values.append(f"{value[:4]}***MASKED***")
                        else:
                            masked_values.append("***MASKED***")
                    sanitized_params[param_name] = masked_values
                else:
                    sanitized_params[param_name] = param_values

            sanitized_query = urlencode(sanitized_params, doseq=True)

            return urlunparse(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    sanitized_query,
                    parsed.fragment,
                ),
            )

        except Exception as e:
            return f"{url} <URL sanitization error: {type(e).__name__}>"

    def _safe_read_content(self, content_source: bytes | str | None, content_type: str = "content") -> str:
        """Safely read content without consuming streaming data or causing memory issues.

        Args:
            content_source: Source to read content from (can be bytes, str, or stream)
            content_type: Type description for logging purposes

        Returns:
            Safe representation of content for logging
        """
        try:
            if hasattr(content_source, "read"):
                return f"<streaming {content_type} - not consumed>"

            if hasattr(content_source, "__iter__") and not isinstance(content_source, str | bytes):
                return f"<iterable {content_type} - not consumed>"

            if content_source is None:
                return ""

            truncated_body = self._truncate_content(content_source)
            return self._sanitize_json_content(truncated_body)

        except Exception as e:
            return f"<error reading {content_type} - {type(e).__name__}: {str(e)[:100]}>"

    def _safe_get_response_preview(self, response: Response) -> str:
        """Get a safe preview of response content without consuming the stream.

        Args:
            response: httpx Response object

        Returns:
            Safe preview of response content
        """
        try:
            content_length = response.headers.get("content-length")
            if content_length:
                try:
                    length = int(content_length)
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
                "application/zip",
                "application/gzip",
                "text/event-stream",
                "multipart/form-data",
            ]

            if any(st in content_type for st in streaming_types):
                return f"<streaming content type '{content_type}' - not logged>"

            try:
                content = response.text
                return self._safe_read_content(content, "response body")
            except Exception as e:
                return f"<error reading response - {type(e).__name__}>"

        except Exception as e:
            return f"<error getting response preview - {type(e).__name__}>"

    def request(self, *args, **kwargs) -> Response:
        """Performs an HTTP request with automatic logging of details.

        This method overrides the standard `request` from `httpx.Client`.
        It first performs the request using the parent method, and then logs
        key information about the request (URL, headers, body) and the response
        (status code, time, headers, body).

        Args:
            *args: Positional arguments passed to `httpx.Client.request`.
            **kwargs: Named arguments passed to `httpx.Client.request`
                      (e.g., `method`, `url`, `json`, `params`, `headers`).

        Returns:
            An `httpx.Response` object with the result of the response.
        """
        response = super().request(*args, **kwargs)

        sanitized_url = self._sanitize_url(str(response.url))
        self._logger.info(f"Request made to {sanitized_url}")

        sanitized_headers = self._sanitize_headers(dict(response.request.headers))
        formatted_headers = self._format_headers(sanitized_headers)
        self._logger.debug(f"Request headers: {formatted_headers}")

        try:
            request_body_log = self._safe_read_content(response.request.content, "request body")
        except Exception as e:
            request_body_log = f"<streaming content - {type(e).__name__}>"
        self._logger.debug(f"Request body: {request_body_log}")

        self._logger.info(f"Response status code: {response.status_code}")
        self._logger.info(f"Response time: {response.elapsed.total_seconds():.3f} s")

        sanitized_response_headers = self._sanitize_headers(dict(response.headers))
        formatted_response_headers = self._format_headers(sanitized_response_headers)
        self._logger.debug(f"Response headers: {formatted_response_headers}")

        response_body_log = self._safe_get_response_preview(response)
        self._logger.debug(f"Response body: {response_body_log}")

        return response
