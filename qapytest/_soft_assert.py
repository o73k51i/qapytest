"""Module providing a soft assertion mechanism for tests."""

import logging

from qapytest import _config as cfg
from qapytest import _internal as utils

soft_assert_logger = logging.getLogger("SoftAssert")


def soft_assert(condition: bool, label: str, details: str | list[str] | None = None) -> bool:
    """Performs a "soft" assertion that logs the result but does not interrupt the test execution.

    Unlike the standard `assert`, which raises an `AssertionError` and immediately
    stops the test, this function only records the result of the check (success or failure)
    in a structured log. This allows all checks within a single test to be executed,
    even if some of them fail, and provides a complete report of all failures.

    Args:
        condition: The logical condition being checked (e.g., `a == b`).
                   `True` means success, `False` means failure.
        label: A short, clear description of what is being checked.
        details: Additional information that may help with debugging,
                 such as expected and actual values.

    Returns:
        bool: Returns `True` if the check is successful (`condition` is `True`),
              and `False` otherwise.

    ---
    ### Example usage:

    ```python
    def test_user_profile_details():
        user_data = {"name": "User", "age": 31, "status": "active"}

        # Successful check
        soft_assert(user_data["name"] == "User", "User name is correct")

        # Failed check, but the test execution will continue
        soft_assert(
            user_data["age"] == 30,
            "User age should be 30",
            details=f"Expected: 30, Actual: {user_data['age']}"
        )

        # Another successful check
        soft_assert(user_data["status"] == "active", "User status is active")

    # After running this test, the final report will indicate
    # that one of the three checks failed, but the test as a whole will complete.
    ```
    """
    log_string = f"Soft assert: {label} - {'PASSED' if condition else 'FAILED'}"
    if details:
        if isinstance(details, list):
            log_string += "\nDetails:\n" + "\n".join(f"- {line}" for line in details)
        else:
            log_string += f"\nDetails: {details}"
    soft_assert_logger.info(log_string)
    passed = bool(condition)
    log_entry: dict[str, cfg.AnyType] = {"type": "assert", "label": label, "passed": passed}

    if details is not None:
        log_entry["details"] = details

    utils.add_log_entry(log_entry)
    return passed
