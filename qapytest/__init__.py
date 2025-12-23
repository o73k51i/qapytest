"""QAPyTest is a powerful package for QA specialists built on top of Pytest."""

import logging
from typing import TYPE_CHECKING, Any

from faker import Faker

from qapytest._attach import attach
from qapytest._json_validation import validate_json
from qapytest._soft_assert import soft_assert
from qapytest._step import step

if TYPE_CHECKING:
    from qapytest._client_http import GraphQLClient, HttpClient
    from qapytest._redis import RedisClient
    from qapytest._sql import SqlClient

logging.getLogger("faker").setLevel(logging.WARNING)

__all__ = [
    "Faker",
    "GraphQLClient",
    "HttpClient",
    "RedisClient",
    "SqlClient",
    "attach",
    "soft_assert",
    "step",
    "validate_json",
]


def __getattr__(name: str) -> Any:  # noqa: ANN401
    if name == "GraphQLClient":
        from qapytest._client_http import GraphQLClient

        return GraphQLClient

    if name == "HttpClient":
        from qapytest._client_http import HttpClient

        return HttpClient

    if name == "RedisClient":
        from qapytest._redis import RedisClient

        return RedisClient

    if name == "SqlClient":
        from qapytest._sql import SqlClient

        return SqlClient

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
