"""Module for convenient interaction with HTTP APIs using httpx."""

import logging

from httpx import Client, Response


class HttpClient(Client):
    """Client for convenient interaction with HTTP APIs, extending `httpx.Client`.

    This class inherits all the functionality of the standard `httpx.Client`,
    adding automatic and structured logging for each request and response.
    It also suppresses the default logs from the `httpx` and `httpcore` libraries,
    leaving only clean output from its own logger "HttpClient".

    This is a tool for API testing.

    Args:
        **kwargs: Arguments passed directly to the constructor of the base
                  `httpx.Client` class. The most common ones are:
                  `base_url` (str): Base URL for all requests.
                  `headers` (dict): Headers added to each request.
                  `timeout` (float): Overall response timeout.

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

    def __init__(self, base_url: str = "", verify: bool = True, timeout: float = 10.0, **kwargs) -> None:
        """Constructor for HttpClient.

        Args:
            base_url: Base URL for all requests. Default is an empty string.
            verify: Whether to verify SSL certificates. Default is True.
            timeout: Overall timeout for requests in seconds. Default is 10.0 seconds
            **kwargs: Standard arguments for the `httpx.Client` constructor.
        """
        super().__init__(base_url=base_url, verify=verify, timeout=timeout, **kwargs)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        self._logger = logging.getLogger("HttpClient")

    def request(self, *args, **kwargs) -> Response:
        """Performs an HTTP request with automatic logging of details.

        This method overrides the standard `request` from `httpx.Client`.
        It first performs the request using the parent method, and then logs
        key information about the request (URL, headers, body) and the response
        (status code, time, headers, body).

        Args:
            *args: Positional arguments passed to `httpx.Client.request`.
            **kwargs: Named arguments passed to `httpx.Client.request`
                      (e.g., `method`, `url`, `json`, `params`, `headers`).

        Returns:
            An `httpx.Response` object with the result of the response.
        """
        response = super().request(*args, **kwargs)
        self._logger.info(f"Request made to {response.url}")
        self._logger.debug(f"Request headers: {dict(response.request.headers)}")

        try:
            request_body = response.request.content
            self._logger.debug(f"Request body: {request_body}")
        except Exception as e:
            self._logger.debug(f"Request body: <streaming content - {type(e).__name__}>")

        self._logger.info(f"Response status code: {response.status_code}")
        self._logger.info(f"Response time: {response.elapsed.total_seconds():.3f} s")
        self._logger.debug(f"Response headers: {dict(response.headers)}")

        try:
            response_body = response.text
            self._logger.debug(f"Response body: {response_body}")
        except Exception as e:
            self._logger.debug(f"Response body: <error reading content - {type(e).__name__}>")

        return response
