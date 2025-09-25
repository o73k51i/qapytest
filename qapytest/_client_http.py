"""Module providing a simple GraphQL client with using httpx for testing APIs."""

from httpx import Response

from qapytest._config import AnyType
from qapytest._config_http import BaseHttpClient


class HttpClient(BaseHttpClient):
    """Client for convenient interaction with HTTP APIs, extending `httpx.Client`.

    This class inherits all the functionality of the standard `httpx.Client`,
    adding automatic and structured logging for each request and response.
    It also suppresses the default logs from the `httpx` and `httpcore` libraries,
    leaving only clean output from its own logger "HttpClient".

    This is a tool for API testing.

    Args:
        base_url: Base URL for all requests. Default is an empty string.
        headers: Dictionary of headers for requests. Default is None.
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
        headers: dict[str, str] | None = None,
        verify: bool = True,
        timeout: float = 10.0,
        sensitive_headers: set[str] | None = None,
        sensitive_json_fields: set[str] | None = None,
        sensitive_text_patterns: list[str] | None = None,
        mask_sensitive_data: bool = True,
        **kwargs,
    ) -> None:
        """Constructor for HttpClient.

        Args:
            base_url: Base URL for all requests. Default is an empty string.
            headers: Dictionary of headers for requests. Default is None.
            verify: Whether to verify SSL certificates. Default is True.
            timeout: Overall timeout for requests in seconds.
                     Default is 10.0 seconds.
            sensitive_headers: Set of header names to mask in logs. If None,
                               uses default sensitive headers.
            sensitive_json_fields: Set of JSON field names to mask in logs.
                                   If None, uses default sensitive fields.
            sensitive_text_patterns: List of regex patterns to mask in text logs.
                                     If None, uses default patterns.
            mask_sensitive_data: Whether to mask sensitive data in logs.
                                 Default is True.
            **kwargs: Standard arguments for the `httpx.Client` constructor.
        """
        super().__init__(
            base_url=base_url,
            headers=headers,
            verify=verify,
            timeout=timeout,
            sensitive_headers=sensitive_headers,
            sensitive_json_fields=sensitive_json_fields,
            sensitive_text_patterns=sensitive_text_patterns,
            mask_sensitive_data=mask_sensitive_data,
            name_logger="HttpClient",
            **kwargs,
        )


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
        max_log_size: Maximum size in bytes for logged request/response bodies.
                      Default is 1024 bytes.
        sensitive_headers: Set of header names to mask in logs.
                           If None, uses default sensitive headers.
        sensitive_json_fields: Set of JSON field names to mask in logs.
                               If None, uses default sensitive fields.
        mask_sensitive_data: Whether to mask sensitive data in logs.
                             Default is True.
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
        verify: bool = True,
        timeout: float = 10.0,
        sensitive_headers: set[str] | None = None,
        sensitive_json_fields: set[str] | None = None,
        sensitive_text_patterns: list[str] | None = None,
        mask_sensitive_data: bool = True,
        **kwargs,
    ) -> None:
        """Constructor for GraphQLClient.

        Args:
            endpoint_url: The URL of the GraphQL endpoint.
            headers: Dictionary of headers for requests. Default is None.
            verify: Whether to verify SSL certificates. Default is True.
            timeout: Overall timeout for requests in seconds.
                     Default is 10.0 seconds.
            sensitive_headers: Set of header names to mask in logs. If None,
                               uses default sensitive headers.
            sensitive_json_fields: Set of JSON field names to mask in logs.
                                   If None, uses default sensitive fields.
            sensitive_text_patterns: List of regex patterns to mask in text logs.
                                     If None, uses default patterns.
            mask_sensitive_data: Whether to mask sensitive data in logs.
                                 Default is True.
            **kwargs: Standard arguments for the `httpx.Client` constructor.
        """
        self._endpoint_url = endpoint_url
        self._client = BaseHttpClient(
            headers=headers,
            verify=verify,
            timeout=timeout,
            sensitive_headers=sensitive_headers,
            sensitive_json_fields=sensitive_json_fields,
            sensitive_text_patterns=sensitive_text_patterns,
            mask_sensitive_data=mask_sensitive_data,
            name_logger="GraphQLClient",
            **kwargs,
        )

    def execute(self, query: str, variables: dict[str, AnyType] | None = None) -> Response:
        """Execute a GraphQL query or mutation.

        Args:
            query: The GraphQL query or mutation as a string.
            variables: Optional dictionary of variables for the query.

        Returns:
            The HTTP response from the GraphQL server.
        """
        payload: dict[str, AnyType] = {"query": query}
        if variables:
            payload["variables"] = variables
        return self._client.post(self._endpoint_url, json=payload)
