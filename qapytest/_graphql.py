"""Module providing a simple GraphQL client with using httpx for testing APIs."""

import logging
from typing import Any

import httpx


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
        **kwargs,
    ) -> None:
        """Constructor for GraphQLClient.

        Args:
            endpoint_url: The URL of the GraphQL endpoint.
            headers: Dictionary of headers for requests.
            timeout: Overall timeout for requests in seconds.
            **kwargs: Standard arguments for the `httpx.Client` constructor.
        """
        self._endpoint_url = endpoint_url
        self._client = httpx.Client(headers=headers, timeout=timeout, **kwargs)

        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        self._logger = logging.getLogger("GraphQLClient")

    def execute(self, query: str, variables: dict[str, Any] | None = None) -> httpx.Response:
        """Sends a GraphQL request (query or mutation) with automatic logging.

        Args:
            query: The GraphQL query or mutation text.
            variables: A dictionary of variables for the query.

        Returns:
            An `httpx.Response` object with the response result.
        """
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        self._logger.info(f"Sending GraphQL request to {self._endpoint_url}")
        self._logger.debug(f"Query: {query.strip()}")
        if variables:
            self._logger.debug(f"Variables: {variables}")

        response = self._client.post(self._endpoint_url, json=payload)

        self._logger.info(f"Response status code: {response.status_code}")
        self._logger.info(f"Response time: {response.elapsed.total_seconds():.3f} s")
        self._logger.debug(f"Response headers: {dict(response.headers)}")
        self._logger.debug(f"Response body: {response.text}")

        return response
