"""Module with configuration variables."""

from contextvars import ContextVar
from typing import Any

AnyType = Any  # Alias for any type

# Global configuration variables
CURRENT_EXECUTION_LOG: ContextVar[list[dict] | None] = ContextVar(
    "_CURRENT_EXECUTION_LOG",
    default=None,
)
CURRENT_LOG_CONTAINER_STACK: ContextVar[list[list[dict]] | None] = ContextVar(
    "_CURRENT_LOG_CONTAINER_STACK",
    default=None,
)
ATTACH_LIMIT_BYTES: int | None = None  # None = unlimited
DEFAULT_IMAGE_MIME = "image/png"


# Constants configuration variables
OUTCOME_RANK = {
    "error": 6,
    "failed": 5,
    "xpassed": 4,
    "xfailed": 3,
    "skipped": 2,
    "passed": 1,
    "unknown": 0,
}
PHASE_RANK = {
    "call": 3,
    "setup": 2,
    "teardown": 1,
}
