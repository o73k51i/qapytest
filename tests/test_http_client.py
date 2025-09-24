"""Tests for HttpClient in QaPyTest."""

import logging
from unittest.mock import MagicMock, patch

import httpx

from qapytest import HttpClient


class TestHttpClient:
    """Test cases for HttpClient functionality."""

    def test_http_client_initialization(self) -> None:
        """Test HttpClient initialization with default parameters."""
        client = HttpClient()
        assert isinstance(client, httpx.Client)
        assert client.base_url == ""
        assert str(client.timeout) == "Timeout(timeout=10.0)"

    def test_http_client_initialization_with_params(self) -> None:
        """Test HttpClient initialization with custom parameters."""
        base_url = "https://api.example.com"
        timeout = 30.0
        verify = False

        client = HttpClient(base_url=base_url, timeout=timeout, verify=verify)
        assert client.base_url == base_url
        assert str(client.timeout) == f"Timeout(timeout={timeout})"
        """Test that logger is properly configured."""
        client = HttpClient()
        assert hasattr(client, "_logger")
        assert client._logger.name == "HttpClient"  # noqa: SLF001

    def test_external_loggers_silenced(self) -> None:
        """Test that httpx and httpcore loggers are set to WARNING level."""
        HttpClient()

        httpx_logger = logging.getLogger("httpx")
        httpcore_logger = logging.getLogger("httpcore")

        assert httpx_logger.level == logging.WARNING
        assert httpcore_logger.level == logging.WARNING

    @patch("httpx.Client.request")
    def test_request_logging(self, mock_request: MagicMock) -> None:
        """Test that requests are properly logged."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/test"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.123
        mock_response.request.headers = {"Content-Type": "application/json"}
        mock_response.request.content = b'{"test": "data"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"result": "success"}'
        mock_request.return_value = mock_response

        client = HttpClient()

        with patch.object(client._logger, "info") as mock_info, patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.request("GET", "https://api.example.com/test")

            assert response == mock_response

            assert any("Sending HTTP" in str(call) for call in mock_info.call_args_list)
            mock_info.assert_any_call("Response status code: 200")
            mock_info.assert_any_call("Response time: 0.123 s")

            mock_debug.assert_any_call("Request headers:\n{'Content-Type': 'application/json'}")
            mock_debug.assert_any_call('Request body:\n{"test":"data"}')
            mock_debug.assert_any_call("Response headers:\n{'Content-Type': 'application/json'}")
            mock_debug.assert_any_call('Response body:\n{"result":"success"}')

    @patch("httpx.Client.get")
    def test_get_method_delegation(self, mock_get: MagicMock) -> None:
        """Test that GET method is properly delegated."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.url = "https://api.example.com/users"
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_response.request.headers = {}
        mock_response.request.content = b""
        mock_response.headers = {}
        mock_response.text = "[]"
        mock_get.return_value = mock_response

        client = HttpClient(base_url="https://api.example.com")
        response = client.get("/users")

        mock_get.assert_called_once_with("/users")
        assert response == mock_response

    @patch("httpx.Client.post")
    def test_post_method_delegation(self, mock_post: MagicMock) -> None:
        """Test that POST method is properly delegated."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.url = "https://api.example.com/users"
        mock_response.status_code = 201
        mock_response.elapsed.total_seconds.return_value = 0.2
        mock_response.request.headers = {"Content-Type": "application/json"}
        mock_response.request.content = b'{"name": "John"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"id": 1, "name": "John"}'
        mock_post.return_value = mock_response

        client = HttpClient(base_url="https://api.example.com")
        data = {"name": "John"}
        response = client.post("/users", json=data)

        mock_post.assert_called_once_with("/users", json=data)
        assert response == mock_response

    @patch("httpx.Client.request")
    def test_request_with_error_response(self, mock_request: MagicMock) -> None:
        """Test logging when request returns error status code."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/notfound"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 404
        mock_response.elapsed.total_seconds.return_value = 0.05
        mock_response.request.headers = {}
        mock_response.request.content = b""
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"error": "Not Found"}'
        mock_request.return_value = mock_response

        client = HttpClient()

        with patch.object(client._logger, "info") as mock_info:  # noqa: SLF001
            response = client.request("GET", "https://api.example.com/notfound")

            assert any("Sending HTTP" in str(call) for call in mock_info.call_args_list)
            mock_info.assert_any_call("Response status code: 404")
            assert response.status_code == 404

    def test_context_manager_support(self) -> None:
        """Test that HttpClient can be used as context manager."""
        with HttpClient(base_url="https://api.example.com") as client:
            assert isinstance(client, HttpClient)
            assert client.base_url == "https://api.example.com"

    @patch("httpx.Client.request")
    def test_custom_headers_in_request(self, mock_request: MagicMock) -> None:
        """Test that custom headers are properly handled."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/test"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_response.request.headers = {"Authorization": "Bearer token", "Custom": "value"}
        mock_response.request.content = b""
        mock_response.headers = {}
        mock_response.text = "OK"
        mock_request.return_value = mock_response

        client = HttpClient()
        headers = {"Authorization": "Bearer token", "Custom": "value"}

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            client.request("GET", "https://api.example.com/test", headers=headers)

            debug_calls = [str(call) for call in mock_debug.call_args_list]
            assert any("Request headers:" in call for call in debug_calls)
            headers_calls = [call for call in debug_calls if "Request headers:" in call]
            assert len(headers_calls) > 0
            headers_call = headers_calls[0]
            assert "Bear***MASKED***" in headers_call
            assert "Custom" in headers_call

    @patch("httpx.Client.request")
    def test_request_with_streaming_content(self, mock_request: MagicMock) -> None:
        """Test that streaming content (e.g., file uploads) is handled gracefully."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/upload"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 1.5
        mock_response.request.headers = {"Content-Type": "multipart/form-data"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"success": true}'

        mock_response.request.content = iter([b"chunk1", b"chunk2"])
        mock_request.return_value = mock_response

        client = HttpClient()

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.request("POST", "https://api.example.com/upload")

            assert response == mock_response

            debug_calls = [str(call) for call in mock_debug.call_args_list]
            request_body_calls = [call for call in debug_calls if "Request body:" in call]
            assert len(request_body_calls) > 0
            request_body_call = request_body_calls[0]
            assert "streaming content" in request_body_call

    @patch("httpx.Client.request")
    def test_request_with_large_content_truncation(self, mock_request: MagicMock) -> None:
        """Test that large request/response bodies are truncated in logs."""
        large_request_body = b"x" * 2048
        large_response_body = "y" * 2048

        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/large"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 2.0
        mock_response.request.headers = {"Content-Type": "application/octet-stream"}
        mock_response.request.content = large_request_body
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = large_response_body
        mock_request.return_value = mock_response

        client = HttpClient()  # Default max_log_size is 1024

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.request("POST", "https://api.example.com/large")

            assert response == mock_response

            debug_calls = [call.args[0] for call in mock_debug.call_args_list]

            request_body_log = next((call for call in debug_calls if call.startswith("Request body:")), None)
            assert request_body_log is not None
            assert "truncated, total size: 2048 bytes" in request_body_log
            assert len(request_body_log) < 2048

            response_body_log = next((call for call in debug_calls if call.startswith("Response body:")), None)
            assert response_body_log is not None
            assert "truncated, total size: 2048 bytes" in response_body_log
            assert len(response_body_log) < 2048

    def test_custom_max_log_size(self) -> None:
        """Test that custom max_log_size parameter works correctly."""
        custom_size = 100
        client = HttpClient(max_log_size=custom_size)
        assert client._max_log_size == custom_size  # noqa: SLF001

    def test_truncate_content_method(self) -> None:
        """Test the _truncate_content method directly."""
        client = HttpClient(max_log_size=10)

        small_text = "hello"
        result = client._truncate_content(small_text)  # noqa: SLF001
        assert result == "hello"

        large_text = "a" * 100
        result = client._truncate_content(large_text)  # noqa: SLF001
        assert "truncated, total size: 100 bytes" in result
        assert len(result) < 100

        small_bytes = b"hello"
        result = client._truncate_content(small_bytes)  # noqa: SLF001
        assert result == "hello"

        large_bytes = b"b" * 100
        result = client._truncate_content(large_bytes)  # noqa: SLF001
        assert "truncated, total size: 100 bytes" in result
        assert len(result) < 100

    def test_sensitive_header_sanitization(self) -> None:
        """Test that sensitive headers are masked in logs."""
        client = HttpClient()

        headers = {
            "Authorization": "Bearer super_secret_token_12345",
            "X-API-Key": "api_key_67890",
            "Cookie": "session=abc123def456",
            "Content-Type": "application/json",
            "User-Agent": "TestAgent/1.0",
        }

        sanitized = client._sanitize_headers(headers)  # noqa: SLF001

        assert sanitized["Authorization"] == "Bear***MASKED***"
        assert sanitized["X-API-Key"] == "api_***MASKED***"
        assert sanitized["Cookie"] == "sess***MASKED***"

        assert sanitized["Content-Type"] == "application/json"
        assert sanitized["User-Agent"] == "TestAgent/1.0"

    def test_sensitive_header_sanitization_disabled(self) -> None:
        """Test that header sanitization can be disabled."""
        client = HttpClient(mask_sensitive_data=False)

        headers = {
            "Authorization": "Bearer super_secret_token_12345",
            "X-API-Key": "api_key_67890",
        }

        sanitized = client._sanitize_headers(headers)  # noqa: SLF001

        assert sanitized["Authorization"] == "Bearer super_secret_token_12345"
        assert sanitized["X-API-Key"] == "api_key_67890"

    def test_sensitive_json_content_sanitization(self) -> None:
        """Test that sensitive JSON fields are masked."""
        client = HttpClient()

        json_content = '{"password": "secret123", "email": "user@example.com", "safe_field": "visible"}'

        sanitized = client._sanitize_json_content(json_content)  # noqa: SLF001

        import json

        sanitized_data = json.loads(sanitized)

        assert sanitized_data["password"] == "secr***MASKED***"  # noqa: S105
        assert sanitized_data["email"] == "user@example.com"

        assert sanitized_data["safe_field"] == "visible"

    def test_sensitive_text_pattern_sanitization(self) -> None:
        """Test that sensitive patterns in text are masked."""
        client = HttpClient()

        text_content = 'password=secret123 and api_key="abc123def" token: xyz789'

        sanitized = client._mask_sensitive_text_patterns(text_content)  # noqa: SLF001

        assert "***MASKED***" in sanitized
        assert "secret123" not in sanitized
        assert "abc123def" not in sanitized
        assert "xyz789" not in sanitized

    def test_custom_sensitive_headers(self) -> None:
        """Test that custom sensitive headers can be configured."""
        custom_sensitive = {"x-custom-secret", "special-header"}
        client = HttpClient(sensitive_headers=custom_sensitive)

        headers = {
            "Authorization": "Bearer token123",
            "X-Custom-Secret": "very_secret",
            "Special-Header": "confidential",
        }

        sanitized = client._sanitize_headers(headers)  # noqa: SLF001

        assert sanitized["Authorization"] == "Bearer token123"
        assert sanitized["X-Custom-Secret"] == "very***MASKED***"
        assert sanitized["Special-Header"] == "conf***MASKED***"

    @patch("httpx.Client.request")
    def test_request_with_sensitive_data_logging(self, mock_request: MagicMock) -> None:
        """Test that sensitive data in real request/response is masked."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/login"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_response.request.headers = {
            "Authorization": "Bearer sensitive_token_123",
            "Content-Type": "application/json",
        }
        mock_response.request.content = b'{"password": "user_secret", "username": "testuser"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"token": "response_token_456", "user_id": 123}'
        mock_request.return_value = mock_response

        client = HttpClient()

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.request("POST", "https://api.example.com/login")

            assert response == mock_response

            debug_calls = [call.args[0] for call in mock_debug.call_args_list]

            request_headers_log = next((call for call in debug_calls if call.startswith("Request headers:")), None)
            assert request_headers_log is not None
            assert "Bear***MASKED***" in request_headers_log
            assert "sensitive_token_123" not in request_headers_log

            request_body_log = next((call for call in debug_calls if call.startswith("Request body:")), None)
            assert request_body_log is not None
            assert "***MASKED***" in request_body_log
            assert "user_secret" not in request_body_log

            response_body_log = next((call for call in debug_calls if call.startswith("Response body:")), None)
            assert response_body_log is not None
            assert "***MASKED***" in response_body_log
            assert "response_token_456" not in response_body_log

    @patch("httpx.Client.request")
    def test_url_parameter_sanitization(self, mock_request: MagicMock) -> None:
        """Test that sensitive URL parameters are masked in logs."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/data"
        from httpx import QueryParams

        mock_params = QueryParams([("access_token", "secret123"), ("api_key", "apikey456"), ("user_id", "789")])
        mock_url.params = mock_params
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.3
        mock_response.request.headers = {"Content-Type": "application/json"}
        mock_response.request.content = b'{"query": "test"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"result": "success"}'
        mock_request.return_value = mock_response

        client = HttpClient()

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.request("GET", "https://api.example.com/data")

            assert response == mock_response

            debug_calls = [call.args[0] for call in mock_debug.call_args_list]
            params_log = next((call for call in debug_calls if call.startswith("Query parameters:")), None)

            assert params_log is not None
            assert "%2A%2A%2AMASKED%2A%2A%2A" in params_log
            assert "user_id=789" in params_log
            assert "secret123" not in params_log
            assert "apikey456" not in params_log

    @patch("httpx.Client.request")
    def test_custom_sensitive_json_fields(self, mock_request: MagicMock) -> None:
        """Test that custom sensitive JSON fields configuration works."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/custom"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.2
        mock_response.request.headers = {"Content-Type": "application/json"}
        mock_response.request.content = b'{"custom_secret": "should_be_masked", "public_info": "visible"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"custom_secret": "should_be_masked", "public_info": "visible"}'
        mock_request.return_value = mock_response

        client = HttpClient(sensitive_json_fields={"custom_secret"})

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.request("POST", "https://api.example.com/custom")

            assert response == mock_response

            debug_calls = [call.args[0] for call in mock_debug.call_args_list]

            request_body_log = next((call for call in debug_calls if call.startswith("Request body:")), None)
            assert request_body_log is not None
            assert "***MASKED***" in request_body_log
            assert "should_be_masked" not in request_body_log
            assert "public_info" in request_body_log
            assert "visible" in request_body_log

            response_body_log = next((call for call in debug_calls if call.startswith("Response body:")), None)
            assert response_body_log is not None
            assert "***MASKED***" in response_body_log
            assert "should_be_masked" not in response_body_log

    def test_header_formatting(self) -> None:
        """Test smart header formatting based on size."""
        client = HttpClient()

        small_headers = {"Content-Type": "application/json", "Accept": "*/*"}
        formatted_small = client._format_headers(small_headers)  # noqa: SLF001
        assert formatted_small == "{'Content-Type': 'application/json', 'Accept': '*/*'}"

        large_headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "Accept": "*/*",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        formatted_large = client._format_headers(large_headers)  # noqa: SLF001

        assert formatted_large.startswith("{\n")
        assert formatted_large.endswith("\n}")
        assert "  Content-Type: application/json; charset=utf-8," in formatted_large
        assert "  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9," in formatted_large
