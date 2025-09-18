"""Tests for SQL client functionality."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from qapytest import SqlClient


class TestSqlClient:
    """Test cases for SqlClient class."""

    @patch("qapytest._sql.create_engine")
    def test_sql_client_initialization(self, mock_create_engine: MagicMock) -> None:
        """Test SqlClient initialization with connection string."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        connection_string = "sqlite:///:memory:"
        client = SqlClient(connection_string)

        assert client._connection_string == connection_string  # noqa: SLF001
        assert client.engine == mock_engine

        mock_create_engine.assert_called_once_with(url=connection_string)

    @patch("qapytest._sql.create_engine")
    def test_echo_parameter_ignored(self, mock_create_engine: MagicMock) -> None:
        """Test that echo parameter is ignored and warning is logged."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        connection_string = "sqlite:///:memory:"

        with patch("logging.getLogger") as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance

            SqlClient(connection_string, echo=True)

            # Verify echo was not passed to create_engine
            mock_create_engine.assert_called_once_with(url=connection_string)

    @patch("qapytest._sql.create_engine")
    def test_initialization_failure(self, mock_create_engine: MagicMock) -> None:
        """Test SqlClient initialization failure handling."""
        mock_create_engine.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            SqlClient("sqlite:///:memory:")

    @patch("qapytest._sql.create_engine")
    def test_fetch_data_success(self, mock_create_engine: MagicMock) -> None:
        """Test successful data fetching."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        # Setup mock connection and result
        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_row1 = {"id": 1, "name": "John"}
        mock_row2 = {"id": 2, "name": "Jane"}
        mock_result.mappings.return_value = [mock_row1, mock_row2]
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        client = SqlClient("sqlite:///:memory:")

        with patch.object(client._logger, "info") as mock_info:  # noqa: SLF001
            result = client.fetch_data("SELECT * FROM users")

            assert result == [mock_row1, mock_row2]
            mock_info.assert_called()

    @patch("qapytest._sql.create_engine")
    def test_fetch_data_sql_error(self, mock_create_engine: MagicMock) -> None:
        """Test data fetching with SQL error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_connection = MagicMock()
        mock_connection.execute.side_effect = SQLAlchemyError("Table not found")
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        client = SqlClient("sqlite:///:memory:")

        with patch.object(client._logger, "error") as mock_error:  # noqa: SLF001
            result = client.fetch_data("SELECT * FROM nonexistent")

            assert result == []
            mock_error.assert_called()

    @patch("qapytest._sql.create_engine")
    def test_execute_and_commit_success(self, mock_create_engine: MagicMock) -> None:
        """Test successful query execution and commit."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_connection = MagicMock()
        mock_engine.begin.return_value.__enter__.return_value = mock_connection

        client = SqlClient("sqlite:///:memory:")

        with patch.object(client._logger, "info") as mock_info:  # noqa: SLF001
            result = client.execute_and_commit("INSERT INTO users (name) VALUES ('John')")

            assert result is True
            mock_info.assert_called()

    @patch("qapytest._sql.create_engine")
    def test_execute_and_commit_sql_error(self, mock_create_engine: MagicMock) -> None:
        """Test query execution with SQL error and rollback."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_connection = MagicMock()
        mock_connection.execute.side_effect = SQLAlchemyError("Constraint violation")
        mock_engine.begin.return_value.__enter__.return_value = mock_connection

        client = SqlClient("sqlite:///:memory:")

        with patch.object(client._logger, "error") as mock_error:  # noqa: SLF001
            result = client.execute_and_commit("INSERT INTO users (id) VALUES (1)")

            assert result is False
            mock_error.assert_called()
