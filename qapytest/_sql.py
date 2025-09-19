"""Module for convenient interaction with SQL databases using SQLAlchemy."""

import logging

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from qapytest import _config as cfg


class SqlClient:
    """Client for convenient interaction with an SQL database using SQLAlchemy.

    This class is a wrapper around the SQLAlchemy Core Engine and provides simple methods
    for executing "raw" SQL queries: one for fetching data (`fetch_data`) and another for
    making changes (`execute_and_commit`) with automatic transaction management.

    It is suitable for cases where you need to quickly execute SQL queries without using
    a full-fledged ORM.

    This is a tool for database testing.

    Args:
        connection_string (str): Connection string for the database in SQLAlchemy format.
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
    db_client.execute_and_commit(create_query)

    # 3. Insert data (using parameters to prevent SQL injection)
    insert_query = "INSERT INTO employees (name, position) VALUES (:name, :position)"
    db_client.execute_and_commit(insert_query, params={"name": "User1", "position": "Developer"})
    db_client.execute_and_commit(insert_query, params={"name": "User2", "position": "Manager"})

    # 4. Fetch all data from the table
    select_query = "SELECT id, name, position FROM employees"
    all_employees = db_client.fetch_data(select_query)
    # >>> [{'id': 1, 'name': 'User1', 'position': 'Developer'},
    #      {'id': 2, 'name': 'User2', 'position': 'Manager'}]
    print(all_employees)

    # 5. Update data
    update_query = "UPDATE employees SET position = :new_pos WHERE name = :emp_name"
    params = {"new_pos": "Lead Developer", "emp_name": "User1"}
    db_client.execute_and_commit(update_query, params=params)

    # 6. Check updated data
    check_query = "SELECT * FROM employees WHERE id = 1"
    updated_employee = db_client.fetch_data(check_query)
    # >>> [{'id': 1, 'name': 'User1', 'position': 'Lead Developer'}]
    print(updated_employee)
    ```
    """

    def __init__(self, connection_string: str, **kwargs) -> None:
        """Constructor for SqlClient.

        Args:
            connection_string (str): Connection string for the database in SQLAlchemy format.
            **kwargs: Additional arguments passed directly to the `sqlalchemy.create_engine` function.
        """
        self._connection_string = connection_string
        self._logger = logging.getLogger("SqlClient")
        if kwargs.get("echo"):
            self._logger.warning("The 'echo=True' parameter is ignored. SQLAlchemy logging is controlled by QaPyTest.")
            kwargs.pop("echo")
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        try:
            self.engine = create_engine(url=connection_string, **kwargs)
        except Exception as e:
            self._logger.error(f"Failed to establish connection to the database: {e}")
            raise

    def fetch_data(
        self,
        query: str,
        params: dict[str, cfg.AnyType] | None = None,
    ) -> list[dict[cfg.AnyType, cfg.AnyType]]:
        """Executes a raw SQL query (SELECT) and returns the result as a list of dictionaries.

        Args:
            query: Raw SQL query to execute.
            params: Dictionary of parameters for safe query insertion.

        Returns:
            A list of dictionaries, where each dictionary represents a row of the result, or None in case of an error.
        """
        self._logger.info(f"Executing query: {query}")
        if params:
            self._logger.debug(f"With parameters: {params}")
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query), params or {})
                data = [dict(row) for row in result.mappings()]
                self._logger.info(f"Query executed successfully, retrieved {len(data)} rows.")
                self._logger.debug(f"Retrieved data: {data}")
                return data
        except SQLAlchemyError as e:
            self._logger.error(f"Error while executing query: {e}")
            return []

    def execute_and_commit(self, query: str, params: dict[str, cfg.AnyType] | None = None) -> bool:
        """Executes a raw SQL query for data modification (INSERT, UPDATE, DELETE) and commits the transaction.

        Args:
            query: Raw SQL query to execute.
            params: Dictionary of parameters for safe query insertion.

        Returns:
            True if the query was executed and the transaction was committed successfully, otherwise — False.
        """
        self._logger.info(f"Executing query: {query}")
        if params:
            self._logger.debug(f"With parameters: {params}")
        try:
            with self.engine.begin() as connection:
                connection.execute(text(query), params or {})
            self._logger.info("Query executed and committed successfully.")
            return True
        except SQLAlchemyError as e:
            self._logger.error(f"Error while executing query. Changes rolled back. Error: {e}")
            return False
