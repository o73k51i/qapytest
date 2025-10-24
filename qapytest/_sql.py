"""Module for convenient interaction with SQL databases using SQLAlchemy."""

import logging
import re

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from qapytest._config import AnyType


class SqlClient:
    """Client for convenient interaction with an SQL database using SQLAlchemy.

    This class is a wrapper around the SQLAlchemy Core Engine and provides simple methods
    for executing "raw" SQL queries: one for fetching data (`fetch_data`) and another for
    making changes (`execute_query`) with automatic transaction management.

    It is suitable for cases where you need to quickly execute SQL queries without using
    a full-fledged ORM.

    This is a tool for database testing.

    Args:
        connection_string: Connection string for the database in SQLAlchemy format.
        **kwargs: Additional arguments passed directly to the `sqlalchemy.create_engine` function.

    ---
    ### General template for connection string
    `"dialect+driver://username:password@host:port/database"`

    ---
    ### Examples of connection strings (`connection_string`)

    **PostgreSQL (with psycopg2):**
        `"postgresql+psycopg2://user:password@hostname:5432/database_name"`

    **MySQL (with mysqlclient):**
        `"mysql+mysqldb://user:password@hostname:3306/database_name"`

    **SQLite (file):**
        `"sqlite:///path/to/database.db"`

    **SQLite (in-memory):**
        `"sqlite:///:memory:"`

    **Microsoft SQL Server (with pyodbc):**
        `"mssql+pyodbc://user:password@dsn_name"`

    ---
    ### Example usage:

    ```python
    # 1. Initialize the client for SQLite in-memory
    db_client = SqlClient("sqlite:///:memory:")

    # 2. Create a table
    create_query = "CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, position TEXT)"
    db_client.execute_query(create_query)

    # 3. Insert data (using parameters to prevent SQL injection)
    insert_query = "INSERT INTO employees (name, position) VALUES (:name, :position)"
    result = db_client.execute_query(insert_query, params={"name": "User1", "position": "Developer"})
    print(f"Inserted {result['rowcount']} row(s), last ID: {result['last_inserted_id']}")

    # 4. Fetch all data from the table
    select_query = "SELECT id, name, position FROM employees"
    all_employees = db_client.fetch_data(select_query)
    # >>> [{'id': 1, 'name': 'User1', 'position': 'Developer'},
    #      {'id': 2, 'name': 'User2', 'position': 'Manager'}]
    print(all_employees)

    # 5. Get single value (count, max, etc.)
    count = db_client.fetch_single_value("SELECT COUNT(*) FROM employees")
    print(f"Total employees: {count}")

    # 6. Update data
    update_query = "UPDATE employees SET position = :new_pos WHERE name = :emp_name"
    params = {"new_pos": "Lead Developer", "emp_name": "User1"}
    result = db_client.execute_query(update_query, params=params)
    print(f"Updated {result['rowcount']} row(s)")

    # 7. Check updated data
    check_query = "SELECT * FROM employees WHERE id = 1"
    updated_employee = db_client.fetch_data(check_query)
    # >>> [{'id': 1, 'name': 'User1', 'position': 'Lead Developer'}]
    print(updated_employee)
    ```
    """

    def __init__(
        self,
        connection_string: str,
        name_logger: str = "SqlClient",
        mask_sensitive_data: bool = True,
        sensitive_data: set[str] | None = None,
        **kwargs,
    ) -> None:
        """Constructor for SqlClient.

        Args:
            connection_string: Connection string for the database in SQLAlchemy format.
            name_logger: Name of the logger to use for logging SQL commands.
            mask_sensitive_data: Whether to mask sensitive data in logs. Default is True.
            sensitive_data: Set of keywords to identify sensitive data in parameters for masking.
            **kwargs: Additional arguments passed directly to the `sqlalchemy.create_engine` function.

        Raises:
            Exception: If connection to database fails.
        """
        self._connection_string = connection_string
        self._logger = logging.getLogger(name_logger)
        self._hide_sensitive_data = mask_sensitive_data

        if kwargs.get("echo"):
            self._logger.warning("The 'echo=True' parameter is ignored. SQLAlchemy logging is controlled by QaPyTest.")
            kwargs.pop("echo")
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        try:
            self.engine = create_engine(url=connection_string, **kwargs)
        except Exception as e:
            self._logger.error(f"Failed to establish connection to the database: {e}")
            raise

        # Default sensitive data
        default_sensitive_data = {
            "password",
            "passwd",
            "pwd",
            "token",
            "secret",
        }
        if sensitive_data is None:
            self._sensitive_data = default_sensitive_data
        else:
            self._sensitive_data = default_sensitive_data | {h.lower() for h in sensitive_data}

    def fetch_data(self, query: str, params: dict[str, AnyType] | None = None) -> list[dict[str, AnyType]]:
        """Executes a SELECT query and returns the result as a list of dictionaries.

        This method is designed for data retrieval only. For INSERT/UPDATE/DELETE operations,
        use execute_query() instead.

        Args:
            query: SQL SELECT query to execute. Must start with SELECT or WITH.
            params: Dictionary of parameters for safe query insertion (e.g., {'id': 123}).

        Returns:
            A list of dictionaries, where each dictionary represents a row.
            Returns empty list [] if no rows match the query.

        Raises:
            ValueError: If query is not a SELECT statement or contains multiple statements.
            SQLAlchemyError: If query execution fails (syntax error, table not found, etc.).

        Examples:
            >>> db.fetch_data("SELECT * FROM users WHERE age > :min_age", {'min_age': 18})
            [{'id': 1, 'name': 'Alice', 'age': 25}, {'id': 2, 'name': 'Bob', 'age': 30}]

            >>> db.fetch_data("SELECT COUNT(*) as total FROM users")
            [{'total': 42}]

            >>> db.fetch_data("SELECT * FROM users WHERE id = 999")
            []
        """
        self._validate_select_query(query)
        self._logger.info(f"Executing SELECT query: {query}")
        if params:
            safe_params = self._mask_sensitive_data(params)
            self._logger.debug(f"With parameters: {safe_params}")

        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query), params or {})
                try:
                    data = [dict(row) for row in result.mappings()]
                except (AttributeError, TypeError) as e:
                    self._logger.warning(f"Cannot convert result to mappings, trying fetchall(): {e}")
                    try:
                        raw_result = result.fetchall()
                        data = [] if not raw_result else [dict(row) for row in raw_result]
                    except Exception as e:
                        raise ValueError(
                            f"Cannot convert query result to list of dictionaries. "
                            f"This might not be a valid SELECT statement. Error: {e}",
                        ) from e

                rows_count = len(data)
                self._logger.info(f"Query executed successfully, retrieved {rows_count} rows.")

                if rows_count > 0:
                    safe_row = self._mask_sensitive_data(data)
                    self._logger.debug(f"Sample data: {safe_row}")

                return data

        except SQLAlchemyError as e:
            self._logger.error(f"SQLAlchemy error while executing query: {e}")
            raise
        except ValueError:
            raise

    def execute_query(
        self,
        query: str,
        params: list[dict[str, AnyType]] | dict[str, AnyType] | None = None,
        return_inserted_ids: bool = False,
    ) -> dict[str, AnyType]:
        """Executes INSERT/UPDATE/DELETE queries and returns execution result.

        This method automatically handles transactions (commits on success, rolls back on error).
        Use fetch_data() for SELECT queries instead.

        Args:
            query: SQL query to execute (INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, etc.).
            params: Dictionary of parameters for safe query insertion.
            return_inserted_ids: If True, tries to return inserted IDs (PostgreSQL RETURNING).

        Returns:
            Dictionary with execution results:
            {
                'rowcount': int,           # Number of affected rows
                'last_inserted_id': int | None,   # Last inserted ID (if available)
                'inserted_ids': list[int] | None, # List of inserted IDs (if return_inserted_ids=True)
            }

        Raises:
            ValueError: If query appears to be a SELECT statement or contains multiple statements.
            SQLAlchemyError: If query execution fails.

        Examples:
            >>> result = db.execute_query(
            ...     "INSERT INTO users (name, age) VALUES (:name, :age)",
            ...     {'name': 'Alice', 'age': 25}
            ... )
            >>> print(result)
            {'rowcount': 1, 'last_inserted_id': 42, 'inserted_ids': None}

            >>> result = db.execute_query("UPDATE users SET active = true WHERE age > :age", {'age': 18})
            >>> print(f"Updated {result['rowcount']} users")
            Updated 15 users

            >>> result = db.execute_query("DELETE FROM users WHERE id = :id", {'id': 999})
            >>> if result['rowcount'] == 0:
            ...     print("User not found")
            User not found

            >>> # PostgreSQL with RETURNING
            >>> result = db.execute_query(
            ...     "INSERT INTO users (name) VALUES ('Bob') RETURNING id",
            ...     return_inserted_ids=True
            ... )
            >>> print(result['inserted_ids'])
            [43]
        """
        self._validate_modifying_query(query)
        self._logger.info(f"Executing modifying query: {query}")
        if params:
            safe_params = self._mask_sensitive_data(params)
            self._logger.debug(f"With parameters: {safe_params}")

        try:
            with self.engine.begin() as connection:
                result = connection.execute(text(query), params or {})
                affected_rows = result.rowcount
                last_id = None
                inserted_ids = None

                try:
                    if hasattr(result, "lastrowid") and result.lastrowid:
                        last_id = result.lastrowid
                except Exception:  # noqa: S110
                    pass

                if return_inserted_ids:
                    try:
                        rows = result.fetchall()
                        if rows:
                            inserted_ids = [row[0] for row in rows]
                    except Exception as e:
                        self._logger.debug(f"Could not fetch inserted IDs: {e}")

                self._logger.info(f"Query executed successfully, {affected_rows} row(s) affected.")
                if last_id:
                    self._logger.debug(f"Last inserted ID: {last_id}")
                if inserted_ids:
                    self._logger.debug(f"Inserted IDs: {inserted_ids}")

                return {
                    "rowcount": affected_rows,
                    "last_inserted_id": last_id,
                    "inserted_ids": inserted_ids,
                }

        except SQLAlchemyError as e:
            self._logger.error(f"SQLAlchemy error while executing query: {e}")
            raise
        except ValueError:
            raise

    def fetch_single_value(
        self,
        query: str,
        params: dict[str, AnyType] | None = None,
    ) -> AnyType:
        """Executes a SELECT query and returns a single value from the first row.

        Useful for queries like SELECT COUNT(*), SELECT MAX(id), etc.
        You don't need to know the column name - it returns the first value.

        Args:
            query: SQL SELECT query that returns a single value.
            params: Dictionary of parameters for safe query insertion.

        Returns:
            The first value from the first row of the result.

        Raises:
            ValueError: If query returns no rows or is not a SELECT statement.
            SQLAlchemyError: If query execution fails.

        Examples:
            >>> db.fetch_single_value("SELECT COUNT(*) FROM users")
            42

            >>> db.fetch_single_value("SELECT MAX(age) FROM users WHERE city = :city", {'city': 'Kyiv'})
            65

            >>> db.fetch_single_value("SELECT name FROM users WHERE id = :id", {'id': 1})
            'Alice'
        """
        result = self.fetch_data(query, params)
        if not result:
            raise ValueError(f"Query returned no rows: {query}")
        first_row = result[0]
        return next(iter(first_row.values()))

    def _validate_select_query(self, query: str) -> None:
        """Validates that query is a SELECT statement.

        Args:
            query: SQL query to validate.

        Raises:
            ValueError: If query is not a SELECT or contains multiple statements.
        """
        query_stripped = query.strip()
        query_upper = query_stripped.upper()
        self._check_multiple_statements(query_stripped)
        if not query_upper.startswith(("SELECT", "WITH")):
            modifying_keywords = [
                "INSERT",
                "UPDATE",
                "DELETE",
                "CREATE",
                "ALTER",
                "DROP",
                "TRUNCATE",
            ]
            if any(query_upper.startswith(kw) for kw in modifying_keywords):
                raise ValueError(
                    f"fetch_data() is for SELECT queries only. "
                    f"Your query starts with '{query_stripped.split()[0]}'. "
                    f"Use execute_query() for INSERT/UPDATE/DELETE operations.",
                )
            raise ValueError(
                f"Only SELECT or WITH queries are allowed in fetch_data(). Query starts with: {query_stripped[:50]}...",
            )

    def _validate_modifying_query(self, query: str) -> None:
        """Validates that query is appropriate for execute_query.

        Args:
            query: SQL query to validate.

        Raises:
            ValueError: If query appears to be a SELECT or contains multiple statements.
        """
        query_stripped = query.strip()
        query_upper = query_stripped.upper()

        self._check_multiple_statements(query_stripped)

        if query_upper.startswith("SELECT") and "RETURNING" not in query_upper:
            raise ValueError(
                "execute_query() is for INSERT/UPDATE/DELETE operations. "
                "Your query starts with 'SELECT'. "
                "Use fetch_data() for SELECT queries.",
            )

    def _check_multiple_statements(self, query: str) -> None:
        """Checks if query contains multiple statements.

        Args:
            query: SQL query to check.

        Raises:
            ValueError: If multiple statements detected.
        """
        query_no_strings = re.sub(r"'[^']*'", "", query)
        query_no_strings = re.sub(r'"[^"]*"', "", query_no_strings)
        if ";" in query_no_strings.rstrip(";"):
            raise ValueError(
                "Multiple statements detected (semicolon found). "
                "Only single queries are allowed for security reasons. "
                "If you need to execute multiple queries, call the method separately for each.",
            )

    def _mask_sensitive_params(self, params: dict[str, AnyType]) -> dict[str, AnyType]:
        """Masks potentially sensitive parameters for logging.

        Args:
            params: Dictionary of parameters.

        Returns:
            Dictionary with masked sensitive values.
        """
        if not self._hide_sensitive_data:
            return params
        masked = {}
        for key, value in params.items():
            if any(sensitive in key.lower() for sensitive in self._sensitive_data):
                masked[key] = "***MASKED***"
            else:
                masked[key] = value
        return masked

    def _mask_sensitive_data(
        self,
        row: dict[str, AnyType] | list[dict[str, AnyType]],
    ) -> dict[str, AnyType] | list[dict[str, AnyType]]:
        """Masks potentially sensitive data in a row for logging.

        Args:
            row: List or dictionary representing a database row.

        Returns:
            Dictionary with masked sensitive values.
        """
        if isinstance(row, list):
            return [self._mask_sensitive_params(r) for r in row]
        return self._mask_sensitive_params(row)

    def close(self) -> None:
        """Closes the database connection and disposes of the engine.

        Call this method when you're done working with the database to free resources.
        """
        try:
            self.engine.dispose()
        except Exception as e:
            self._logger.error(f"Error while closing database connection: {e}")
            raise

    def __enter__(self) -> "SqlClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:  # noqa: ANN001
        """Context manager exit - closes connection."""
        self.close()
        return False
