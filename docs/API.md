# API documentation `QaPyTest`

This document describes the public APIs exported by the `QaPyTest` package intended for use in tests. All examples are short usage snippets.

## [Integration clients](#clients)

- [`HttpClient`](#httpclient) — HTTP client
- [`GraphQLClient`](#graphqlclient) — GraphQL client
- [`SqlClient`](#sqlclient) — SQL client
- [`RedisClient`](#redisclient) — Redis client

## [Browser automation](#browser-automation)

- [`playwright integration`](#playwright-integration) — Browser automation

## [Data generation](#test-data-generation)

- [`Faker`](#faker) — Test data generation

## [Validation](#json-schema-validation)

- [`validation_json`](#validate_json) - validation JSONSChema

## [Test organization](#test-organization-helpers)

- [`step(message)`](#stepmessage-str) — context manager for structuring tests
- [`soft_assert(condition, label, details)`](#soft_assertcondition-label-detailsnone) — soft assertion that does not stop the test
- [`attach(data, label, mime)`](#attachdata-label-mimenone) — add attachments to reports
- [`validate_json(data, schema, schema_path, message, strict)`](#validate_json) — JSON schema validation with soft-assert support

## Clients

### `HttpClient`
- Signature:

```
HttpClient(
  base_url: str = "",
  headers: dict[str, str] | None = None,
  verify: bool = True,
  timeout: float = 10.0,
  sensitive_headers: set[str] | None = None,
  sensitive_json_fields: set[str] | None = None,
  sensitive_text_patterns: list[str] | None = None,
  mask_sensitive_data: bool = True,
  name_logger: str = "HttpClient",
  enable_log: bool = True,
  **kwargs,
) — subclass of `httpx.Client`
```

- Description: full-featured HTTP client with automatic request/response logging and sensitive data masking
- Logging: automatically logs requests, responses, durations and status codes via the logger specified by `name_logger` parameter (default: `HttpClient`) when `enable_log=True`
- Methods: all `httpx.Client` methods (`get`, `post`, `put`, `delete`, `patch`, `request`)
- Features: context manager support, automatic suppression of internal httpx/httpcore loggers, sensitive data masking, optional request/response logging
- Example:

```python
from qapytest import HttpClient

# Use as a regular httpx.Client with logging and sensitive data masking
client = HttpClient(
    base_url="https://jsonplaceholder.typicode.com", 
    timeout=30,
    headers={"Authorization": "Bearer token"},
    mask_sensitive_data=True,
    name_logger="HttpClient",  # Custom logger name (default: "HttpClient")
    enable_log=True  # Enable automatic request/response logging (default)
)
response = client.get("/posts/1")
assert response.status_code == 200

# Disable logging for high-volume requests
silent_client = HttpClient(
    base_url="https://api.example.com",
    enable_log=False  # Disable automatic logging
)
response = silent_client.get("/data")

# Context manager support
with HttpClient(base_url="https://api.example.com") as client:
  response = client.post("/auth/login", json={"username": "test"})
```

### `GraphQLClient`
- Signature: 
 
```
GraphQLClient(
  endpoint_url: str,
  headers: dict[str, str] | None = None,
  verify: bool = True,
  timeout: float = 10.0,
  sensitive_headers: set[str] | None = None,
  sensitive_json_fields: set[str] | None = None,
  sensitive_text_patterns: list[str] | None = None,
  mask_sensitive_data: bool = True,
  name_logger: str = "GraphQLClient",
  enable_log: bool = True,
  **kwargs
) — subclass of httpx.Client
```

- Description: specialized client for GraphQL APIs with automatic logging of requests and responses and sensitive data masking
- Logging: records GraphQL queries, variables, response time and status via the logger specified by `name_logger` parameter (default: `GraphQLClient`) when `enable_log=True`
- Methods:
  - `execute(query: str, variables: dict | None = None) -> httpx.Response`
- Features: automatic POST request formation, variable logging, headers support, sensitive data masking, optional request/response logging
- Example:

```python
from qapytest import GraphQLClient

# Client with automatic logging enabled
client = GraphQLClient(
  endpoint_url="https://spacex-production.up.railway.app/",
  headers={"Authorization": "Bearer token"},
  verify=True,
  timeout=15.0,
  mask_sensitive_data=True,
  name_logger="GraphQLClient",  # Custom logger name (default: "GraphQLClient")
  enable_log=True  # Enable automatic request/response logging (default)
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

# Client without logging for high-frequency queries
silent_client = GraphQLClient(
  endpoint_url="https://api.example.com/graphql",
  enable_log=False  # Disable automatic logging
)
```

### `SqlClient`

- Signature: 
  
```
SqlClient(
  connection_string: str,
  name_logger: str = "SqlClient",
  mask_sensitive_data: bool = True,
  sensitive_data: set[str] | None = None,
  **kwargs
) — class with `SQLAlchemy`
```

Note: A corresponding DB driver is required (psycopg2, pymysql, sqlite3). [See list of supported dialects](https://docs.sqlalchemy.org/en/20/dialects/index.html).


- Description: client for executing raw SQL queries with automatic transaction management and comprehensive logging
- Logging: logs all SQL queries, parameters, results and errors via the logger specified by `name_logger` parameter (default: `SqlClient`) with automatic sensitive data masking
- Methods:
  - `fetch_data(query: str, params: dict | None = None) -> list[dict]` — SELECT queries, returns list of dicts
  - `execute_query(query: str, params: list[dict[str, Any]] | dict[str, Any] | None = None, return_inserted_ids: bool = False) -> dict[str, Any]` — INSERT/UPDATE/DELETE with auto-commit, returns execution stats
  - `fetch_single_value(query: str, params: dict | None = None) -> Any` — returns single value from first row (useful for COUNT, MAX, etc.)
  - `close()` — close database connection and dispose engine
- Features: safe parameterization, automatic rollback on errors, query validation, sensitive data masking, context manager support, batch operations support
- Example:

```python
from qapytest import SqlClient

# Connect to the database with sensitive data masking
db = SqlClient(
  "postgresql://user:pass@localhost:5432/testdb",
  name_logger="SqlClient",  # Custom logger name (default: "SqlClient")
  mask_sensitive_data=True,
  sensitive_data={"api_key", "auth_token"}
)

# Safe query execution with parameters
users = db.fetch_data(
  "SELECT * FROM users WHERE active = :status AND age > :min_age", 
  params={"status": True, "min_age": 18}
)

# Execute INSERT/UPDATE with detailed execution info
result = db.execute_query(
  "INSERT INTO users (name, email) VALUES (:name, :email)",
  params={"name": "John", "email": "john@example.com"}
)
print(f"Inserted {result['rowcount']} rows, last ID: {result['last_inserted_id']}")

# Batch insert with list of dictionaries
batch_result = db.execute_query(
  "INSERT INTO users (name, email) VALUES (:name, :email)",
  params=[
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"}
  ]
)
print(f"Batch inserted {batch_result['rowcount']} rows")

# Get single values efficiently
user_count = db.fetch_single_value("SELECT COUNT(*) FROM users WHERE active = true")
max_age = db.fetch_single_value("SELECT MAX(age) FROM users")

# PostgreSQL with RETURNING clause
result = db.execute_query(
  "INSERT INTO users (name) VALUES ('Alice'), ('Bob') RETURNING id",
  return_inserted_ids=True
)
print(f"New user IDs: {result['inserted_ids']}")

# Context manager support
with SqlClient("sqlite:///:memory:") as db:
    db.execute_query("CREATE TABLE test (id INTEGER, name TEXT)")
    db.execute_query("INSERT INTO test VALUES (1, 'Test')")
    data = db.fetch_data("SELECT * FROM test")
# Connection automatically closed
```

### `RedisClient`

- Signature: 
  
```
RedisClient(
  host: str,
  port: int = 6379,
  name_logger: str = "RedisClient",
  **kwargs
) — subclass of `redis.Redis`
```

- Description: Redis client wrapper that adds comprehensive logging for all Redis commands. Inherits all functionality from the standard `redis-py` library.
- Logging: logs all Redis commands at INFO level and results at DEBUG level via the logger specified by `name_logger` parameter (default: `RedisClient`)
- Methods: all standard `redis.Redis` methods (`set`, `get`, `delete`, `exists`, `lpush`, `rpop`, `sadd`, `sismember`, `hset`, `hget`, etc.)
- Features: command execution logging, result logging, error logging, automatic suppression of internal redis loggers
- Example:

```python
from qapytest import RedisClient
import json

# Connect to Redis with enhanced logging
redis_client = RedisClient(host="localhost", port=6379, db=0, name_logger="RedisClient")

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

## Browser automation

### `playwright integration`

- Description: QaPyTest includes seamless integration with pytest-playwright for browser automation testing
- Features: automatic browser management, page fixtures, screenshot on failure, video recording, trace collection
- Setup: Install browser binaries with `playwright install` after installing qapytest
- Test fixtures: all standard pytest-playwright fixtures are available (`page`, `browser`, `context`, etc.)
- Configuration: supports all pytest-playwright configuration options
- Example:

```python
import pytest
from qapytest import step, soft_assert

@pytest.mark.title("Browser Automation")
@pytest.mark.component("playwright")
def test_browser_with_faker(page) -> None:
    """Test case demonstrating browser automation."""
    with step("Open page"):
        page.goto("http://example.com/")
    with step("Check element on page"):
        title = page.get_by_role("heading").text_content()
        expect_title = "Example Domain"
        soft_assert(
            title == expect_title,
            "Check title",
            [f"Expected: {expect_title}", f"Actual: {title}"],
        )
```

## Test data generation

### `Faker`
- Import: `from qapytest import Faker`
- Description: Python Faker library for generating realistic test data. QaPyTest includes Faker as a built-in dependency
- Usage: Create a `Faker` instance and use its methods to generate various types of fake data
- Features: locale support, custom providers, seeded generation for reproducible tests
- Categories: personal data, addresses, dates, text, numbers, internet data, financial data, and more
- Example:

```python
from qapytest import Faker

def test_user_profile_creation():
    fake = Faker()
    
    with step("Generate user profile data"):
        profile = {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "full_name": fake.name(),
        }
        attach(profile, "Generated user profile")
```

Common Faker methods:
- **Personal**: `name()`, `first_name()`, `last_name()`, `email()`, `phone_number()`
- **Address**: `address()`, `city()`, `country()`, `postcode()`, `street_address()`
- **Date/Time**: `date()`, `date_time()`, `date_of_birth()`, `future_date()`
- **Text**: `text()`, `sentence()`, `paragraph()`, `word()`
- **Numbers**: `random_int()`, `random_float()`, `pyfloat()`
- **Internet**: `url()`, `domain_name()`, `ipv4()`, `user_name()`, `password()`
- **Financial**: `credit_card_number()`, `currency_code()`, `iban()`
- **Identifiers**: `uuid4()`, `ssn()`, `ean()`

## JSON Schema Validation

### `validate_json`

- Signature:

```
`validate_json(
  data,
  *,
  schema: dict | None = None,
  schema_path: str | Path | None = None,
  message: str = "Validate JSON schema",
  strict: bool = False
) -> None
```

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

## Test organization helpers

### step
- Purpose: group processing and logging of steps in a test; creates a hierarchical `step` record.
- Usage:

```python
from qapytest import step

def test_organization():
  with step("Login check"):
    with step("Open page"):
      ...
    with step("Enter data"):
      ...
```

- Notes: After exiting the context, `passed` is automatically set to `False` if any child records contain errors.

### soft assertion
- Signature: 

```
soft_assert(
  condition: bool,
  label: str,
  details: str | list[str] | None = None
) -> bool
```

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
```

### attach
- Signature:

```
attach(
  data,
  label,
  mime: str | None = None
) -> None
```

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
