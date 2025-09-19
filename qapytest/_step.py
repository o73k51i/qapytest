"""Module for managing hierarchical logging steps in QA testing scenarios."""

import logging
from collections.abc import Generator
from contextlib import contextmanager

from qapytest import _config as cfg
from qapytest import _internal as utils

step_logger = logging.getLogger("Step")


@contextmanager
def step(message: str) -> Generator[None, None, None]:
    """Creates a hierarchical step in the log structure.

    This is a context manager designed to group log entries
    into logical blocks or "steps". All log entries made within
    the `with` block become child elements of this step.

    After the block is completed, the step's "passed" status is
    automatically set to `False` if any of its child entries are
    marked as failed. This makes it easy to track the result of
    complex operations.

    Args:
        message (str): A descriptive message for the step that will
                       be displayed in the logs.

    Yields:
        None: Control is passed inside the `with` block.

    ---
    ### Example usage:

    ```python
    # Usage in tests or scenarios
    with step("Checking the login process"):
        with step("Step 1: Open the login page"):
            # ... code to open the page ...

        with step("Step 2: Enter user data"):
            # ... code to enter data ...
    ```
    """
    step_logger.info(f"{message}")
    stack = cfg.CURRENT_LOG_CONTAINER_STACK.get()
    if not stack:
        yield
        return

    step_node = {
        "type": "step",
        "message": message,
        "passed": True,
        "children": [],
    }
    utils.add_log_entry(step_node)
    stack.append(step_node["children"])
    try:
        yield
    finally:
        stack.pop()
        step_node["passed"] = not utils.has_failures_in_log(step_node.get("children", []))
