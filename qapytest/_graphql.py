"""Module providing a simple GraphQL client with using httpx for testing APIs."""

import json
import logging
import re

import httpx

from qapytest._config import AnyType


class GraphQLClient:
    """Client for convenient interaction with a GraphQL API.

    It adds automatic and structured logging for each request and response.
    It also mutes the standard logs from the `httpx` and `httpcore` libraries,
    leaving only the output from its own logger "GraphQLClient".

    This is a tool for testing GraphQL APIs.

    Args:
        endpoint_url: The full URL of the GraphQL endpoint.
        headers: Headers added to every request.
        timeout: Overall timeout for responses in seconds.
        max_log_size: Maximum size in bytes for logged request/response bodies. Default is 1024 bytes.
        sensitive_headers: Set of header names to mask in logs. If None, uses default sensitive headers.
        sensitive_json_fields: Set of JSON field names to mask in logs. If None, uses default sensitive fields.
        mask_sensitive_data: Whether to mask sensitive data in logs. Default is True.
        **kwargs: Other arguments passed directly to the `httpx.Client` constructor.

    ---
    ### Example usage:

    ```python
    # 1. Initialize the client by specifying the endpoint URL
    # Use the public SpaceX GraphQL API as an example
    client = GraphQLClient(endpoint_url="https://spacex-production.up.railway.app/")

    # 2. Define the GraphQL query as a string
    # This query retrieves company information
    company_query = \"\"\"
        query GetCompanyInfo {
            company {
                name
                summary
            }
        }
    \"\"\"

    # 3. Execute the query without variables
    response = client.execute(query=company_query)
    print(response.json())

    # 4. Define a query with a variable ($limit)
    launches_query = \"\"\"
        query GetLaunches($limit: Int!) {
            launches(limit: $limit) {
                mission_name
                launch_date_utc
            }
        }
    \"\"\"

    # 5. Execute the query with variables
    variables = {"limit": 5}
    response_with_vars = client.execute(query=launches_query, variables=variables)
    print(response_with_vars.json())
    ```
    """

    def __init__(
        self,
        endpoint_url: str,
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
        max_log_size: int = 1024,
        sensitive_headers: set[str] | None = None,
        sensitive_json_fields: set[str] | None = None,
        mask_sensitive_data: bool = True,
        **kwargs,
    ) -> None:
        """Constructor for GraphQLClient.

        Args:
            endpoint_url: The URL of the GraphQL endpoint.
            headers: Dictionary of headers for requests.
            timeout: Overall timeout for requests in seconds.
            max_log_size: Maximum size in bytes for logged request/response bodies. Default is 1024 bytes.
            sensitive_headers: Set of header names to mask in logs. If None, uses default sensitive headers.
            sensitive_json_fields: Set of JSON field names to mask in logs. If None, uses default sensitive fields.
            mask_sensitive_data: Whether to mask sensitive data in logs. Default is True.
            **kwargs: Standard arguments for the `httpx.Client` constructor.
        """
        self._endpoint_url = endpoint_url
        self._client = httpx.Client(headers=headers, timeout=timeout, **kwargs)
        self._max_log_size = max_log_size
        self._mask_sensitive_data = mask_sensitive_data

        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        self._logger = logging.getLogger("GraphQLClient")

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

    def _sanitize_content(self, content: str) -> str:
        """Sanitize content, falling back to text sanitization."""
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

    def _safe_get_response_preview(self, response: httpx.Response) -> str:
        """Get a safe preview of response content."""
        try:
            content_length = response.headers.get("content-length")
            if content_length:
                try:
                    if int(content_length) > self._max_log_size * 10:
                        return f"<large response body - {content_length} bytes - not logged for performance>"
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

            content_str = response.text
            truncated = self._truncate_content(content_str)
            return self._sanitize_content(truncated)
        except Exception as e:
            return f"<error reading response - {type(e).__name__}>"

    def execute(self, query: str, variables: dict[str, AnyType] | None = None) -> httpx.Response:
        """Performs an HTTP request with automatic logging of details."""
        payload: dict[str, AnyType] = {"query": query}
        if variables:
            payload["variables"] = variables

        self._logger.info(f"Sending GraphQL request to {self._endpoint_url}")
        self._logger.debug(f"Query:\n{query.strip()}")

        if variables:
            variables_str = json.dumps(variables)
            sanitized_variables = self._sanitize_content(variables_str)
            self._logger.debug(f"Variables:\n{sanitized_variables}")

        response = self._client.post(self._endpoint_url, json=payload)

        sanitized_request_headers = self._sanitize_headers(dict(response.request.headers))
        formatted_request_headers = self._format_headers(sanitized_request_headers)
        self._logger.debug(f"Request headers:\n{formatted_request_headers}")

        self._logger.info(f"Response status code: {response.status_code}")
        self._logger.info(f"Response time: {response.elapsed.total_seconds():.3f} s")

        sanitized_response_headers = self._sanitize_headers(dict(response.headers))
        formatted_response_headers = self._format_headers(sanitized_response_headers)
        self._logger.debug(f"Response headers:\n{formatted_response_headers}")

        response_body_log = self._safe_get_response_preview(response)
        self._logger.debug(f"Response body:\n{response_body_log}")

        return response
