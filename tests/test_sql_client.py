"""Tests for SQL client functionality."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from qapytest import SqlClient


class TestSqlClient:
    """Test cases for SqlClient class."""

    @patch("qapytest._sql.create_engine")
    def test_sql_client_initialization_basic(self, mock_create_engine: MagicMock) -> None:
        """Test SqlClient initialization with connection string."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        connection_string = "sqlite:///:memory:"
        client = SqlClient(connection_string)

        assert client._connection_string == connection_string  # noqa: SLF001
        assert client.engine == mock_engine
        assert client._hide_sensitive_data is True  # noqa: SLF001
        assert "password" in client._sensitive_data  # noqa: SLF001

        mock_create_engine.assert_called_once_with(url=connection_string)

    @patch("qapytest._sql.create_engine")
    def test_sql_client_initialization_with_parameters(self, mock_create_engine: MagicMock) -> None:
        """Test SqlClient initialization with all parameters."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        connection_string = "sqlite:///:memory:"
        custom_sensitive = {"api_key", "auth_token"}

        client = SqlClient(
            connection_string,
            mask_sensitive_data=False,
            sensitive_data=custom_sensitive,
            pool_size=10,
        )

        assert client._connection_string == connection_string  # noqa: SLF001
        assert client._hide_sensitive_data is False  # noqa: SLF001
        assert "api_key" in client._sensitive_data  # noqa: SLF001
        assert "password" in client._sensitive_data  # noqa: SLF001 (default should be merged)

        mock_create_engine.assert_called_once_with(url=connection_string, pool_size=10)

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
    def test_fetch_data_with_parameters(self, mock_create_engine: MagicMock) -> None:
        """Test data fetching with parameters."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value = [{"id": 1, "name": "John"}]
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        client = SqlClient("sqlite:///:memory:")

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            result = client.fetch_data("SELECT * FROM users WHERE id = :user_id", {"user_id": 1})

            assert len(result) == 1
            mock_debug.assert_called()

    @patch("qapytest._sql.create_engine")
    def test_fetch_data_mappings_fallback(self, mock_create_engine: MagicMock) -> None:
        """Test data fetching with mappings fallback to fetchall."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.mappings.side_effect = AttributeError("No mappings")
        mock_result.fetchall.return_value = [{"id": 1, "name": "John"}]
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        client = SqlClient("sqlite:///:memory:")

        with patch.object(client._logger, "warning") as mock_warning:  # noqa: SLF001
            result = client.fetch_data("SELECT * FROM users")

            assert result == [{"id": 1, "name": "John"}]
            mock_warning.assert_called()

    @patch("qapytest._sql.create_engine")
    def test_fetch_data_validation_error(self, mock_create_engine: MagicMock) -> None:
        """Test data fetching with invalid query."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        client = SqlClient("sqlite:///:memory:")

        with pytest.raises(ValueError, match=r"fetch_data\(\) is for SELECT queries only"):
            client.fetch_data("INSERT INTO users (name) VALUES ('test')")

    @patch("qapytest._sql.create_engine")
    def test_fetch_data_sql_error(self, mock_create_engine: MagicMock) -> None:
        """Test data fetching with SQL error."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_connection = MagicMock()
        mock_connection.execute.side_effect = SQLAlchemyError("Table not found")
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        client = SqlClient("sqlite:///:memory:")

        with pytest.raises(SQLAlchemyError):
            client.fetch_data("SELECT * FROM nonexistent")

    @patch("qapytest._sql.create_engine")
    def test_execute_query_success(self, mock_create_engine: MagicMock) -> None:
        """Test successful query execution."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_result.lastrowid = 42
        mock_connection.execute.return_value = mock_result
        mock_engine.begin.return_value.__enter__.return_value = mock_connection

        client = SqlClient("sqlite:///:memory:")

        with patch.object(client._logger, "info") as mock_info:  # noqa: SLF001
            result = client.execute_query("INSERT INTO users (name) VALUES ('John')")

            expected = {
                "rowcount": 1,
                "last_inserted_id": 42,
                "inserted_ids": None,
            }
            assert result == expected
            mock_info.assert_called()

    @patch("qapytest._sql.create_engine")
    def test_execute_query_with_returning(self, mock_create_engine: MagicMock) -> None:
        """Test query execution with RETURNING clause."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.rowcount = 2
        mock_result.lastrowid = None
        mock_result.fetchall.return_value = [(1,), (2,)]
        mock_connection.execute.return_value = mock_result
        mock_engine.begin.return_value.__enter__.return_value = mock_connection

        client = SqlClient("sqlite:///:memory:")

        result = client.execute_query(
            "INSERT INTO users (name) VALUES ('John'), ('Jane') RETURNING id",
            return_inserted_ids=True,
        )

        expected = {
            "rowcount": 2,
            "last_inserted_id": None,
            "inserted_ids": [1, 2],
        }
        assert result == expected

    @patch("qapytest._sql.create_engine")
    def test_execute_query_batch_insert(self, mock_create_engine: MagicMock) -> None:
        """Test batch insert with list of parameters."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.rowcount = 2
        mock_result.lastrowid = 42
        mock_connection.execute.return_value = mock_result
        mock_engine.begin.return_value.__enter__.return_value = mock_connection

        client = SqlClient("sqlite:///:memory:")

        params_list = [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"},
        ]

        with patch.object(client._logger, "info") as mock_info:  # noqa: SLF001
            result = client.execute_query(
                "INSERT INTO users (name, email) VALUES (:name, :email)",
                params=params_list,
            )

            expected = {
                "rowcount": 2,
                "last_inserted_id": 42,
                "inserted_ids": None,
            }
            assert result == expected
            mock_info.assert_called()

    @patch("qapytest._sql.create_engine")
    def test_execute_query_validation_error(self, mock_create_engine: MagicMock) -> None:
        """Test execute query with invalid SELECT query."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        client = SqlClient("sqlite:///:memory:")

        with pytest.raises(ValueError, match="execute_query\\(\\) is for INSERT/UPDATE/DELETE operations"):
            client.execute_query("SELECT * FROM users")

    @patch("qapytest._sql.create_engine")
    def test_execute_query_sql_error(self, mock_create_engine: MagicMock) -> None:
        """Test query execution with SQL error and rollback."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_connection = MagicMock()
        mock_connection.execute.side_effect = SQLAlchemyError("Constraint violation")
        mock_engine.begin.return_value.__enter__.return_value = mock_connection

        client = SqlClient("sqlite:///:memory:")

        with pytest.raises(SQLAlchemyError):
            client.execute_query("INSERT INTO users (id) VALUES (1)")

    @patch("qapytest._sql.create_engine")
    def test_fetch_single_value_success(self, mock_create_engine: MagicMock) -> None:
        """Test successful single value fetching."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value = [{"count": 42}]
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        client = SqlClient("sqlite:///:memory:")

        result = client.fetch_single_value("SELECT COUNT(*) as count FROM users")
        assert result == 42

    @patch("qapytest._sql.create_engine")
    def test_fetch_single_value_no_rows(self, mock_create_engine: MagicMock) -> None:
        """Test single value fetching with no rows."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_connection = MagicMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value = []
        mock_connection.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        client = SqlClient("sqlite:///:memory:")

        with pytest.raises(ValueError, match="Query returned no rows"):
            client.fetch_single_value("SELECT COUNT(*) FROM empty_table")

    def test_validate_select_query_valid(self) -> None:
        """Test validation of valid SELECT queries."""
        with patch("qapytest._sql.create_engine"):
            client = SqlClient("sqlite:///:memory:")

            # Should not raise exceptions
            client._validate_select_query("SELECT * FROM users")  # noqa: SLF001
            client._validate_select_query("  SELECT id FROM users  ")  # noqa: SLF001
            client._validate_select_query("WITH cte AS (SELECT 1) SELECT * FROM cte")  # noqa: SLF001

    def test_validate_select_query_invalid(self) -> None:
        """Test validation of invalid SELECT queries."""
        with patch("qapytest._sql.create_engine"):
            client = SqlClient("sqlite:///:memory:")

            with pytest.raises(ValueError, match="fetch_data\\(\\) is for SELECT queries only"):
                client._validate_select_query("INSERT INTO users VALUES (1)")  # noqa: SLF001

            with pytest.raises(ValueError, match=r"fetch_data\(\) is for SELECT queries only"):
                client._validate_select_query("CREATE TABLE test (id INT)")  # noqa: SLF001

    def test_validate_modifying_query_valid(self) -> None:
        """Test validation of valid modifying queries."""
        with patch("qapytest._sql.create_engine"):
            client = SqlClient("sqlite:///:memory:")

            # Should not raise exceptions
            client._validate_modifying_query("INSERT INTO users VALUES (1)")  # noqa: SLF001
            client._validate_modifying_query("UPDATE users SET name = 'test'")  # noqa: SLF001
            client._validate_modifying_query("DELETE FROM users WHERE id = 1")  # noqa: SLF001
            client._validate_modifying_query("SELECT * FROM users RETURNING id")  # noqa: SLF001

    def test_validate_modifying_query_invalid(self) -> None:
        """Test validation of invalid modifying queries."""
        with patch("qapytest._sql.create_engine"):
            client = SqlClient("sqlite:///:memory:")

            with pytest.raises(ValueError, match="execute_query\\(\\) is for INSERT/UPDATE/DELETE operations"):
                client._validate_modifying_query("SELECT * FROM users")  # noqa: SLF001

    def test_check_multiple_statements_valid(self) -> None:
        """Test validation of single statements."""
        with patch("qapytest._sql.create_engine"):
            client = SqlClient("sqlite:///:memory:")

            # Should not raise exceptions
            client._check_multiple_statements("SELECT * FROM users")  # noqa: SLF001
            client._check_multiple_statements("SELECT 'test;string' FROM users")  # noqa: SLF001
            client._check_multiple_statements("INSERT INTO users VALUES ('name;with;semicolon')")  # noqa: SLF001

    def test_check_multiple_statements_invalid(self) -> None:
        """Test validation of multiple statements."""
        with patch("qapytest._sql.create_engine"):
            client = SqlClient("sqlite:///:memory:")

            with pytest.raises(ValueError, match="Multiple statements detected"):
                client._check_multiple_statements("SELECT * FROM users; DROP TABLE users")  # noqa: SLF001

    def test_mask_sensitive_params(self) -> None:
        """Test sensitive parameter masking."""
        with patch("qapytest._sql.create_engine"):
            client = SqlClient("sqlite:///:memory:")

            params = {
                "username": "john",
                "password": "secret123",
                "api_token": "abc123",
                "normal_field": "value",
            }

            masked = client._mask_sensitive_params(params)  # noqa: SLF001

            assert masked["username"] == "john"
            assert masked["password"] == "***MASKED***"  # noqa: S105
            assert masked["api_token"] == "***MASKED***"  # noqa: S105
            assert masked["normal_field"] == "value"

    def test_mask_sensitive_params_disabled(self) -> None:
        """Test sensitive parameter masking when disabled."""
        with patch("qapytest._sql.create_engine"):
            client = SqlClient("sqlite:///:memory:", mask_sensitive_data=False)

            params = {
                "password": "secret123",
                "token": "abc123",
            }

            masked = client._mask_sensitive_params(params)  # noqa: SLF001

            assert masked == params

    def test_mask_sensitive_data_list(self) -> None:
        """Test sensitive data masking for list of dictionaries."""
        with patch("qapytest._sql.create_engine"):
            client = SqlClient("sqlite:///:memory:")

            data = [
                {"id": 1, "password": "secret1"},
                {"id": 2, "password": "secret2"},
            ]

            masked = client._mask_sensitive_data(data)  # noqa: SLF001

            assert masked[0]["password"] == "***MASKED***"  # type: ignore  # noqa: S105
            assert masked[1]["password"] == "***MASKED***"  # type: ignore  # noqa: S105
            assert masked[0]["id"] == 1  # type: ignore
            assert masked[1]["id"] == 2  # type: ignore

    @patch("qapytest._sql.create_engine")
    def test_close_success(self, mock_create_engine: MagicMock) -> None:
        """Test successful connection closing."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        client = SqlClient("sqlite:///:memory:")
        client.close()

        mock_engine.dispose.assert_called_once()

    @patch("qapytest._sql.create_engine")
    def test_close_error(self, mock_create_engine: MagicMock) -> None:
        """Test connection closing with error."""
        mock_engine = MagicMock()
        mock_engine.dispose.side_effect = Exception("Dispose failed")
        mock_create_engine.return_value = mock_engine

        client = SqlClient("sqlite:///:memory:")

        with pytest.raises(Exception, match="Dispose failed"):
            client.close()

    @patch("qapytest._sql.create_engine")
    def test_context_manager(self, mock_create_engine: MagicMock) -> None:
        """Test context manager functionality."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        with SqlClient("sqlite:///:memory:") as client:
            assert isinstance(client, SqlClient)

        mock_engine.dispose.assert_called_once()
