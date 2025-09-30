# API documentation `QaPyTest`

This document describes the public APIs exported by the `QaPyTest` package intended for use in tests. All examples are short usage snippets.

## [Integration clients](#integration-clients)
- `HttpClient` — HTTP client
- `GraphQLClient` — GraphQL client
- `SqlClient` — SQL client
- `RedisClient` — Redis client

## [Test organization helpers](#test-organization-helpers)
- `step(message)` — context manager for structuring tests
- `soft_assert(condition, label, details)` — soft assertion that does not stop the test
- `attach(data, label, mime)` — add attachments to reports
- `validate_json(data, schema, schema_path, message, strict)` — JSON schema validation with soft-assert support

### Integration clients

#### `HttpClient`
- Signature: `HttpClient(base_url: str = "", headers: dict[str, str] | None = None, verify: bool = True, timeout: float = 10.0, sensitive_headers: set[str] | None = None, sensitive_json_fields: set[str] | None = None, sensitive_text_patterns: list[str] | None = None, mask_sensitive_data: bool = True, **kwargs)` — subclass of `httpx.Client`
- Description: full-featured HTTP client with automatic request/response logging and sensitive data masking
- Logging: automatically logs requests, responses, durations and status codes via the `HttpClient` logger
- Methods: all `httpx.Client` methods (`get`, `post`, `put`, `delete`, `patch`, `request`)
- Features: context manager support, automatic suppression of internal httpx/httpcore loggers, sensitive data masking
- Example:

```python
from qapytest import HttpClient

# Use as a regular httpx.Client with logging and sensitive data masking
client = HttpClient(
    base_url="https://jsonplaceholder.typicode.com", 
    timeout=30,
    headers={"Authorization": "Bearer token"},
    mask_sensitive_data=True
)
response = client.get("/posts/1")
assert response.status_code == 200

# Context manager support
with HttpClient(base_url="https://api.example.com") as client:
  response = client.post("/auth/login", json={"username": "test"})
```

#### `GraphQLClient`
- Signature: `GraphQLClient(endpoint_url: str, headers: dict[str, str] | None = None, verify: bool = True, timeout: float = 10.0, sensitive_headers: set[str] | None = None, sensitive_json_fields: set[str] | None = None, sensitive_text_patterns: list[str] | None = None, mask_sensitive_data: bool = True, **kwargs)`
- Description: specialized client for GraphQL APIs with automatic logging of requests and responses and sensitive data masking
- Logging: records GraphQL queries, variables, response time and status via the `GraphQLClient` logger
- Methods:
  - `execute(query: str, variables: dict | None = None) -> httpx.Response`
- Features: automatic POST request formation, variable logging, headers support, sensitive data masking
- Example:

```python
from qapytest import GraphQLClient

client = GraphQLClient(
  endpoint_url="https://spacex-production.up.railway.app/",
  headers={"Authorization": "Bearer token"},
  verify=True,
  timeout=15.0,
  mask_sensitive_data=True
)

query = """
query GetLaunches($limit: Int) {
  launchesPast(limit: $limit) {
  id
  mission_name
  }
}
"""
response = client.execute(query, variables={"limit": 3})
assert response.status_code == 200
data = response.json()
```

#### `SqlClient`
- Constructor: `SqlClient(connection_string: str, **kwargs)` — creates a SQLAlchemy engine with logging
- Description: client for executing raw SQL queries with automatic transaction management
- Logging: logs all SQL queries, parameters, results and errors via the `SqlClient` logger
- Methods:
  - `fetch_data(query: str, params: dict | None = None) -> list[dict]` — SELECT queries, returns list of dicts
  - `execute_and_commit(query: str, params: dict | None = None) -> bool` — INSERT/UPDATE/DELETE with auto-commit
- Features: safe parameterization, automatic rollback on errors
- Example:

```python
from qapytest import SqlClient

# Connect to the database
db = SqlClient("postgresql://user:pass@localhost:5432/testdb")

# Safe query execution with parameters
users = db.fetch_data(
  "SELECT * FROM users WHERE active = :status AND age > :min_age", 
  params={"status": True, "min_age": 18}
)

# Execute INSERT/UPDATE with automatic commit
success = db.execute_and_commit(
  "INSERT INTO users (name, email) VALUES (:name, :email)",
  params={"name": "John", "email": "john@example.com"}
)
```

Note: A corresponding DB driver is required (psycopg2, pymysql, sqlite3). [See list of supported dialects](https://docs.sqlalchemy.org/en/20/dialects/index.html).

#### `RedisClient`
- Constructor: `RedisClient(host: str, port: int = 6379, **kwargs)` — extends `redis.Redis` with enhanced logging
- Description: Redis client wrapper that adds comprehensive logging for all Redis commands. Inherits all functionality from the standard `redis-py` library.
- Logging: logs all Redis commands at INFO level and results at DEBUG level via the `RedisClient` logger
- Methods: all standard `redis.Redis` methods (`set`, `get`, `delete`, `exists`, `lpush`, `rpop`, `sadd`, `sismember`, `hset`, `hget`, etc.)
- Features: command execution logging, result logging, error logging, automatic suppression of internal redis loggers
- Example:

```python
from qapytest import RedisClient
import json

# Connect to Redis with enhanced logging
redis_client = RedisClient(host="localhost", port=6379, db=0)

# Use all standard Redis methods with automatic logging
redis_client.set("user:123:status", "active", ex=3600)  # TTL 1 hour
status = redis_client.get("user:123:status")  # Returns b"active"

# Working with JSON data (manual serialization)
user_data = {"id": 123, "name": "John", "roles": ["admin", "user"]}
redis_client.set("user:123:data", json.dumps(user_data))
retrieved_data = json.loads(redis_client.get("user:123:data"))

# Standard Redis operations with logging
if redis_client.exists("user:123:status"):
    redis_client.delete("user:123:status")

# Working with lists
redis_client.lpush("tasks", "task1", "task2", "task3")
task = redis_client.rpop("tasks")  # Returns b"task1"

# Working with sets  
redis_client.sadd("users:active", "user1", "user2", "user3")
is_member = redis_client.sismember("users:active", "user1")  # Returns True

# Working with hashes
redis_client.hset("user:123:profile", "name", "John")
name = redis_client.hget("user:123:profile", "name")  # Returns b"John"
```

### JSON Schema Validation

#### `validate_json`
- Signature: `validate_json(data, *, schema: dict | None = None, schema_path: str | Path | None = None, message: str = "Validate JSON schema", strict: bool = False) -> None`
- Description: Validator that checks `data` against a JSON Schema. The result is recorded as a soft assert via `soft_assert` and does not stop the test by default. If `strict=True`, a mismatch calls `pytest.fail()` and the test fails immediately.
- Parameters:
  - `data` — object to validate (`dict`, `list`, primitives).
  - `schema` — Schema itself as a `dict` (mutually exclusive with `schema_path`).
  - `schema_path` — path to a JSON file with the schema (used if `schema` is not provided).
  - `message` — message for logging/assertion.
  - `strict` — if `True`, calls `pytest.fail()` on error.
- Returns: `None` — result is recorded in logs/soft-asserts.
- Example:

```python
from qapytest import validate_json

data = {"id": 1, "name": "A"}
schema = {
  "type": "object",
  "properties": {
    "id": {"type": "integer"},
    "name": {"type": "string"}
  },
  "required": ["id", "name"]
}

validate_json(data, schema=schema)
```

### Test organization helpers

#### `step(message: str)`
- Purpose: group processing and logging of steps in a test; creates a hierarchical `step` record.
- Usage:

```python
from qapytest import step

with step("Login check"):
  with step("Open page"):
    ...
  with step("Enter data"):
    ...
```

- Notes: After exiting the context, `passed` is automatically set to `False` if any child records contain errors.

#### `soft_assert(condition, label, details=None)`
- Signature: `soft_assert(condition: bool, label: str, details: str | list[str] | None = None) -> bool`
- Purpose: soft assertion function that logs the result but does not stop test execution
- Parameters:
  - `condition` — boolean condition to check (`True` = success, `False` = failure)
  - `label` — short description of what is being checked
  - `details` — additional debugging information (string or list of strings)
- Returns: `bool` — result of the check (`True` on success)
- Example:

```python
from qapytest import soft_assert

def test_user_validation():
  user_data = {"name": "John", "age": 31, "status": "active"}
  
  # Successful check
  soft_assert(user_data["name"] == "John", "User name is correct")
  
  # Failing check, but the test continues
  soft_assert(
    user_data["age"] == 30,
    "User age should be 30",
    details=f"Expected: 30, Actual: {user_data['age']}"
  )
  
  # Another successful check
  soft_assert(user_data["status"] == "active", "User status is active")
```

#### `attach(data, label, mime=None)`
- Signature: `attach(data, label, mime: str | None = None) -> None`
- Purpose: add an attachment to the current log container (text, JSON, image in base64).
- Supported `data` types: `dict`, `list`, `bytes`, `str` (also `Path`) and others.
- Parameters:
  - `data` — data to attach;
  - `label` — attachment name shown in the report;
  - `mime` — optional MIME type for `bytes` or when overriding the type.
- Example:

```python
from qapytest import attach, step
with step("API call"):
  response = {"id": 1, "ok": True}
  attach(response, "API response")
  attach(b"\x89PNG...", "Screenshot", mime="image/png")
```
