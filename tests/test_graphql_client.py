"""Tests for GraphQLClient in QaPyTest."""

import json
from unittest.mock import MagicMock, patch

import httpx

from qapytest import GraphQLClient


class TestGraphQLClient:
    """Test cases for GraphQLClient functionality."""

    def test_graphql_client_initialization(self) -> None:
        """Test GraphQLClient initialization with required parameters."""
        endpoint_url = "https://api.example.com/graphql"

        with patch("httpx.Client") as mock_client:
            client = GraphQLClient(endpoint_url)

            assert client._endpoint_url == endpoint_url  # noqa: SLF001
            mock_client.assert_called_once_with(headers=None, timeout=10.0)

    def test_graphql_client_initialization_with_options(self) -> None:
        """Test GraphQLClient initialization with custom options."""
        endpoint_url = "https://api.example.com/graphql"
        headers = {"Authorization": "Bearer token"}
        timeout = 30.0

        with patch("httpx.Client") as mock_client:
            client = GraphQLClient(endpoint_url, headers=headers, timeout=timeout)

            assert client._endpoint_url == endpoint_url  # noqa: SLF001
            mock_client.assert_called_once_with(headers=headers, timeout=timeout)

    def test_logger_setup(self) -> None:
        """Test that logger is properly configured."""
        with patch("httpx.Client"):
            client = GraphQLClient("https://api.example.com/graphql")
            assert hasattr(client, "_logger")
            assert client._logger.name == "GraphQLClient"  # noqa: SLF001

    @patch("httpx.Client")
    def test_execute_simple_query(self, mock_client_class: MagicMock) -> None:
        """Test executing a simple GraphQL query."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.123
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"data": {"user": {"name": "John"}}}'
        mock_client.post.return_value = mock_response

        endpoint_url = "https://api.example.com/graphql"
        client = GraphQLClient(endpoint_url)

        query = "query { user { name } }"

        with patch.object(client._logger, "info") as mock_info, patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.execute(query)

            assert response == mock_response

            expected_payload = {"query": query}
            mock_client.post.assert_called_once_with(endpoint_url, json=expected_payload)

            mock_info.assert_any_call(f"Sending GraphQL request to {endpoint_url}")
            mock_info.assert_any_call("Response status code: 200")
            mock_info.assert_any_call("Response time: 0.123 s")
            mock_debug.assert_any_call(f"Query:\n{query}")

    @patch("httpx.Client")
    def test_execute_query_with_variables(self, mock_client_class: MagicMock) -> None:
        """Test executing GraphQL query with variables."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.2
        mock_response.headers = {}
        mock_response.text = '{"data": {"user": {"id": 1, "name": "John"}}}'
        mock_client.post.return_value = mock_response

        endpoint_url = "https://api.example.com/graphql"
        client = GraphQLClient(endpoint_url)

        query = "query GetUser($id: ID!) { user(id: $id) { name } }"
        variables = {"id": "1"}

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.execute(query, variables)

            expected_payload = {"query": query, "variables": variables}
            mock_client.post.assert_called_once_with(endpoint_url, json=expected_payload)

            mock_debug.assert_any_call(f"Variables:\n{json.dumps(variables, separators=(',', ':'))}")

            assert response == mock_response

    @patch("httpx.Client")
    def test_execute_mutation(self, mock_client_class: MagicMock) -> None:
        """Test executing GraphQL mutation."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"data": {"createUser": {"id": "2", "name": "Jane"}}}'
        mock_client.post.return_value = mock_response

        client = GraphQLClient("https://api.example.com/graphql")

        mutation = """
            mutation CreateUser($input: CreateUserInput!) {
                createUser(input: $input) {
                    id
                    name
                }
            }
        """
        variables = {"input": {"name": "Jane", "email": "jane@example.com"}}

        response = client.execute(mutation, variables)

        expected_payload = {"query": mutation, "variables": variables}
        mock_client.post.assert_called_once_with(
            "https://api.example.com/graphql",
            json=expected_payload,
        )
        assert response.status_code == 200

    @patch("httpx.Client")
    def test_execute_with_error_response(self, mock_client_class: MagicMock) -> None:
        """Test executing query that returns GraphQL errors."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"errors": [{"message": "User not found"}]}'
        mock_client.post.return_value = mock_response

        client = GraphQLClient("https://api.example.com/graphql")

        with patch.object(client._logger, "info") as mock_info:  # noqa: SLF001
            response = client.execute("query { user(id: 999) { name } }")

            assert response.status_code == 200
            mock_info.assert_any_call("Response status code: 200")

    @patch("httpx.Client")
    def test_execute_with_http_error(self, mock_client_class: MagicMock) -> None:
        """Test executing query with HTTP error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.elapsed.total_seconds.return_value = 0.05
        mock_response.headers = {}
        mock_response.text = "Internal Server Error"
        mock_client.post.return_value = mock_response

        client = GraphQLClient("https://api.example.com/graphql")

        with patch.object(client._logger, "info") as mock_info:  # noqa: SLF001
            response = client.execute("query { user { name } }")

            assert response.status_code == 500
            mock_info.assert_any_call("Response status code: 500")

    def test_external_loggers_silenced(self) -> None:
        """Test that httpx and httpcore loggers are silenced."""
        import logging

        with patch("httpx.Client"):
            GraphQLClient("https://api.example.com/graphql")

            httpx_logger = logging.getLogger("httpx")
            httpcore_logger = logging.getLogger("httpcore")

            assert httpx_logger.level == logging.WARNING
            assert httpcore_logger.level == logging.WARNING

    @patch("httpx.Client")
    def test_custom_headers_passed_to_client(self, mock_client_class: MagicMock) -> None:
        """Test that custom headers are passed to httpx client."""
        headers = {
            "Authorization": "Bearer token",
            "X-API-Key": "secret-key",
        }

        GraphQLClient("https://api.example.com/graphql", headers=headers)

        mock_client_class.assert_called_once_with(headers=headers, timeout=10.0)
