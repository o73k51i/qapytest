"""JSON Schema validation with soft assertions."""

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import ValidationError, validators
from referencing.jsonschema import EMPTY_REGISTRY

from qapytest._soft_assert import soft_assert


def _load_json_schema(path: str | Path) -> dict[str, Any]:
    """Load a JSON schema from a file.

    Args:
        path: Path to the JSON schema file.

    Returns:
        The loaded JSON schema as a dictionary.

    Raises:
        FileNotFoundError: If the schema file doesn't exist.
        json.JSONDecodeError: If the schema file contains invalid JSON.
    """
    path_obj = Path(path)
    try:
        with path_obj.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Schema file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in schema file: {path}", e.doc, e.pos) from e


def _format_validation_errors(errors: list[ValidationError]) -> list[str]:
    """Format validation errors for human-readable output.

    Args:
        errors: List of validation errors from jsonschema.

    Returns:
        List of formatted error messages.
    """
    return [f" - ({'/'.join(str(p) for p in error.absolute_path)}) {error.message}" for error in errors]


def _validate_json_data(
    data: dict[str, Any] | list[Any] | str | int | float | bool | None,
    schema: dict[str, Any],
    message: str,
) -> tuple[bool, str, str | list[str] | None]:
    """Validate JSON data against a schema.

    Args:
        data: The data to validate.
        schema: The JSON schema to validate against.
        message: Custom message for the validation result.

    Returns:
        A tuple of (is_valid, error_message).
    """
    try:
        validator_class = validators.validator_for(schema)
        validator = validator_class(schema, registry=EMPTY_REGISTRY)

        validation_errors = list(validator.iter_errors(data))
        if validation_errors:
            formatted_errors = _format_validation_errors(validation_errors)
            return (False, message, formatted_errors)

        return (True, message, None)
    except Exception as e:
        error_details = [
            f"Schema validation error: {type(e).__name__}",
            f"Error message: {e}",
            "This usually indicates an invalid JSON Schema definition",
        ]
        return (False, message, error_details)


def validate_json(
    data: dict[str, Any] | list[Any] | str | int | float | bool | None,
    *,
    schema: dict[str, Any] | None = None,
    schema_path: str | Path | None = None,
    message: str = "Validate JSON schema",
    strict: bool = False,
) -> None:
    """Validate JSON data against a schema using soft assertions.

    This function performs JSON schema validation and records the result
    as a soft assertion, allowing the test to continue even if validation fails.
    When strict mode is enabled, validation failures cause the test to fail
    immediately using pytest.fail().

    Args:
        data: The JSON data to validate.
        schema: JSON Schema as a dictionary (optional, mutually exclusive with schema_path).
        schema_path: Path to a JSON Schema file (optional, used if schema is not provided).
        message: Custom message for the assertion.
        strict: If True, calls pytest.fail() on validation failure instead of soft assertion.

    Raises:
        ValueError: If no schema is provided via either parameter.

    Example:
        >>> user_data = {"id": 123, "name": "John", "email": "john@example.com"}
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "id": {"type": "integer"},
        ...         "name": {"type": "string"},
        ...         "email": {"type": "string", "format": "email"}
        ...     },
        ...     "required": ["id", "name", "email"]
        ... }
        >>> validate_json(user_data, schema=schema)
        >>> # For strict validation:
        >>> validate_json(user_data, schema=schema, strict=True)
    """
    if schema is None and schema_path is not None:
        schema = _load_json_schema(schema_path)

    if schema is None:
        raise ValueError("No JSON Schema provided")

    is_valid, error_message, formatted_errors = _validate_json_data(data, schema, message or "Validate JSON schema")

    if strict and not is_valid:
        if isinstance(formatted_errors, list):
            detailed_message = f"{error_message}:\n" + "\n".join(formatted_errors)
        else:
            detailed_message = f"{error_message}: {formatted_errors}"
        pytest.fail(reason=detailed_message)

    soft_assert(is_valid, error_message, formatted_errors)
