"""Tests for HttpClient in qapytest."""

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
        # Skip transport verification test as it's implementation detail    def test_logger_setup(self):
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
        # Setup mock response
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.url = "https://api.example.com/test"
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

            # Verify the response is returned
            assert response == mock_response

            # Verify logging calls
            mock_info.assert_any_call("Request made to https://api.example.com/test")
            mock_info.assert_any_call("Response status code: 200")
            mock_info.assert_any_call("Response time: 0.123 s")

            mock_debug.assert_any_call("Request headers: {'Content-Type': 'application/json'}")
            mock_debug.assert_any_call('Request body: b\'{"test": "data"}\'')
            mock_debug.assert_any_call("Response headers: {'Content-Type': 'application/json'}")
            mock_debug.assert_any_call('Response body: {"result": "success"}')

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
        mock_response.url = "https://api.example.com/notfound"
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

            mock_info.assert_any_call("Request made to https://api.example.com/notfound")
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
        mock_response.url = "https://api.example.com/test"
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

            # Check that headers are logged
            mock_debug.assert_any_call("Request headers: {'Authorization': 'Bearer token', 'Custom': 'value'}")
