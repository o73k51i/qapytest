# Core Testing Tools

QaPyTest provides essential tools for organizing tests, making assertions, and generating report.

- [Step](#step)
- [Soft Assertion](#soft-assertion)
- [Attach](#attach)
- [JSON Schema Validation](#json-schema-validation)
- [JSON Query](#json-query)


## Step

Group and log processing of test steps in a hierarchical structure.

### Purpose

The `step` context manager creates a named block of test execution that:
- Groups related operations together
- Creates hierarchical logs for better readability
- Automatically tracks success/failure of the step
- Improves report structure

### Signature

```python
step(message: str) → ContextManager
```

### Usage

```python
from qapytest import step

def test_user_authentication():
    with step("Prepare test data"):
        user = {"email": "test@example.com", "password": "secret123"}
    
    with step("Login process"):
        with step("Send login request"):
            response = client.post("/login", json=user)
        
        with step("Validate response"):
            assert response.status_code == 200
```

### Output in Report

```
✓ Prepare test data
✓ Login process
  ✓ Send login request
  ✓ Validate response
```

### Notes

- After exiting the step context, `passed` is automatically set to `False` if any child records contain errors
- Steps can be nested to any depth
- If any assertion inside a step fails, the step is marked as failed

---

## Soft Assertion

Log assertion results without stopping test execution.

### Signature

```python
soft_assert(
    condition: bool,
    label: str = "",
    details: str | list[str] | None = None
) → bool
```

### Parameters

- `condition` — boolean condition to check (`True` = success, `False` = failure)
- `label` — description of what is being checked
- `details` — additional debugging information (string or list of strings)

### Returns

- `bool` — result of the check (`True` on success, `False` on failure)

### Usage

```python
from qapytest import soft_assert, step

def test_user_validation():
    user_data = {
        "id": 31,
        "status": "closed"
    }
    
    with step("Validate user fields"):
        soft_assert(user_data["id"] >= 18, f"Age valid: {user_data['age']}")
        soft_assert(user_data["status"] == "active", "Status is active")
```

### When Test Fails

If any soft assertion fails, the test continues but is ultimately marked as failed. All failures are collected and reported together:

```
✖ One or more assertions failed
  ✖ Status is active
```

### Difference from Standard Assertions

```python
# Hard assertion - stops immediately
assert user["id"] >= 18  # Stops here if false

# Soft assertion - continues, collects failure
soft_assert(user["id"] >= 18, "ID is 18+")  # Continues even if false
```

---

## Attach

Add attachments to test logs for debugging and documentation.

### Signature

```python
attach(
    data,
    label: str = "",
    mime: str | None = None
) → None
```

### Parameters

- `data` — data to attach (dict, list, bytes, str, Path, or other objects)
- `label` — description/name for the attachment
- `mime` — optional MIME type (auto-detected for common types)

### Supported Data Types

- `dict`, `list` — automatically serialized to JSON
- `str` — plain text
- `bytes` — binary data (images, PDFs, etc.)
- `other objects` — converted to string representation

### Usage

```python
from qapytest import attach, step

def test_api_with_attachments(page):
    with step("Make API request"):
        response = client.get("/users/123")
        attach(response.json(), "API Response")
    
    with step("Take screenshot"):
        screenshot = page.screenshot()
        attach(screenshot, "Page Screenshot", mime="image/png")
    
    with step("Save page HTML"):
        html = page.content()
        attach(html, "Page HTML", mime="text/html")
```

### MIME Types

Common MIME types (auto-detected):

- `text/plain` — `.txt`, `str`
- `application/json` — `dict`, `list`
- `text/html` — `.html`
- `image/png` — `.png`, PNG bytes
- `image/jpeg` — `.jpg`, `.jpeg`
- `application/pdf` — `.pdf`
- `text/csv` — `.csv`

### Explicit MIME Type

```python
# Override auto-detection
attach(b"\x89PNG...", "Screenshot", mime="image/png")
attach("<html>...</html>", "HTML Output", mime="text/html")
attach("raw,data,csv", "CSV Export", mime="text/csv")
```

---

## JSON Schema Validation

Validate data against JSON Schema with soft assert or strict mode.

### Signature

```python
validate_json(
    data,
    *,
    schema: dict | None = None,
    schema_path: str | Path | None = None,
    message: str = "Validate JSON schema",
    strict: bool = False
) → None
```

### Parameters

- `data` — object to validate (dict, list, primitives)
- `schema` — JSON Schema as dict (mutually exclusive with `schema_path`)
- `schema_path` — path to JSON file with schema (used if `schema` is not provided)
- `message` — message for logging/assertion
- `strict` — if `True`, calls `pytest.fail()` on error and stops execution

### Usage Examples

#### Simple Inline Schema

```python
from qapytest import validate_json, soft_assert

def test_api_response_structure():
    response_data = {
        "id": 1,
        "name": "John",
        "age": 30
    }
    
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0}
        },
        "required": ["id", "name"]
    }
    
    validate_json(response_data, schema=schema)
```

#### Strict Mode (Stop on Error)

```python
def test_critical_api_response():
    response = client.get("/api/data")
    
    schema = {
        "type": "object",
        "properties": {
            "data": {"type": "array"},
            "status": {"type": "string"}
        },
        "required": ["data", "status"]
    }
    
    # Strict mode - stop test if validation fails
    validate_json(
        response.json(),
        schema=schema,
        message="API response must match schema",
        strict=True
    )
```

#### Schema from File

```python
from pathlib import Path

def test_with_schema_file():
    response = client.get("/users/123")
    
    # Load schema from file
    validate_json(
        response.json(),
        schema_path="schemas/user_response.json",
        strict=True
    )
```

### Soft vs Strict Mode

#### Soft Mode (default)

```python
validate_json(data, schema=schema)  # strict=False
# - Validation errors are logged
# - Test continues even if validation fails
# - Useful for non-critical validations
```

#### Strict Mode

```python
validate_json(data, schema=schema, strict=True)
# - Validation errors cause test to fail immediately
# - Uses pytest.fail() to stop execution
# - Useful for critical API response validation
```

### JSON Schema Resources

- [JSON Schema Official Documentation](https://json-schema.org/)
- [JSON Schema Validator](https://www.jsonschemavalidator.net/)
- Common validators:
  - `type` — data type check
  - `required` — required fields
  - `minimum`/`maximum` — numeric bounds
  - `minLength`/`maxLength` — string length
  - `pattern` — regex pattern matching
  - `enum` — allowed values
  - `format` — email, date-time, uri, etc.

---

## JSON Query

Navigate and extract values from nested JSON-like Python objects using a concise query syntax.

### Functions

```python
find_values(obj, path) → list
find_value(obj, path)  → Any | None
```

- `find_values` — returns **all** matches as a list (empty list when nothing matches)
- `find_value` — returns the **first** match, or `None` when nothing matches

### Path Syntax

| Token           | Description                                   | Example            |
| --------------- | --------------------------------------------- | ------------------ |
| `.key`          | Navigate into a dict key                      | `.name`            |
| `[]`            | Fan out over every element of a list          | `.users[]`         |
| `[N]` / `[-N]`  | Pick element by index                         | `[0]`, `[-1]`      |
| `[?key=value]`  | Filter — keep elements where key equals value | `[?status=active]` |
| `[?key!=value]` | Filter — keep elements where key differs      | `[?role!=admin]`   |
| `[?key]`        | Filter — keep elements where key is truthy    | `[?active]`        |
| `..key`         | Recursive descent — collect key at any depth  | `..id`             |

Filter values support JSON literals: `null`, `true`, `false`, integers, and floats.

### Pipe Operators

Append `|operator` to transform the result set:

| Operator         | Description                                    |
| ---------------- | ---------------------------------------------- |
| `unique`         | Deduplicate values                             |
| `count`          | Return count as a single-element list          |
| `first`          | Keep only the first element                    |
| `last`           | Keep only the last element                     |
| `sort(key)`      | Sort ascending by a field                      |
| `sort_desc(key)` | Sort descending by a field                     |
| `min(key)`       | Keep the element with the smallest field value |
| `max(key)`       | Keep the element with the largest field value  |

### Usage

```python
from qapytest import find_value, find_values

response = {
    "users": [
        {"id": 1, "name": "Alice", "role": "admin", "score": 95},
        {"id": 2, "name": "Bob",   "role": "user",  "score": 72},
        {"id": 3, "name": "Carol", "role": "user",  "score": 88},
    ]
}

# Extract all IDs
find_values(response, ".users[].id")               # [1, 2, 3]

# First match only
find_value(response, ".users[].name")              # 'Alice'

# Index access
find_value(response, ".users[-1].name")            # 'Carol'

# Filter by equality
find_values(response, ".users[?role=admin].name")  # ['Alice']

# Recursive descent
find_values(response, "..name")                    # ['Alice', 'Bob', 'Carol']

# Sort ascending
find_values(response, ".users[]|sort(score)")
# [{'id': 2, ...score: 72}, {'id': 3, ...score: 88}, {'id': 1, ...score: 95}]

# Top scorer
find_value(response, ".users[]|max(score).name")   # 'Alice'

# Count users with role=user
find_value(response, ".users[?role=user]|count")   # 2
```

### Combining with Assertions

```python
from qapytest import find_value, find_values, soft_assert, step

def test_order_api():
    response = client.get("/orders").json()

    with step("Validate active orders"):
        active_ids = find_values(response, ".orders[?status=active].id")
        soft_assert(len(active_ids) > 0, "At least one active order exists")

    with step("Validate most recent order total"):
        total = find_value(response, ".orders[-1].total")
        soft_assert(total is not None, "Last order has a total")
        soft_assert(total > 0, f"Total is positive: {total}")
```
