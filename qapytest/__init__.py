"""QAPyTest is a powerful package for QA specialists built on top of Pytest.

Unlike a simple plugin, it offers a comprehensive system for writing clear tests,
structuring them with steps, and generating informative interactive HTML reports.
"""

from qapytest._attach import attach
from qapytest._http import HttpClient
from qapytest._json_validation import validate_json
from qapytest._redis import RedisClient
from qapytest._soft_assert import soft_assert
from qapytest._sql import SqlClient
from qapytest._step import step

__all__ = [
    "HttpClient",
    "RedisClient",
    "SqlClient",
    "attach",
    "soft_assert",
    "step",
    "validate_json",
]
