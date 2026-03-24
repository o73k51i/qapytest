# Integration Clients

QaPyTest provides built-in clients for testing different types of services and APIs.

- [HttpClient](#httpclient)
- [GraphQLClient](#graphqlclient)
- [SqlClient](#sqlclient)
- [RedisClient](#redisclient)
- [GrpcClient](#grpcclient)
- [Troubleshooting](#troubleshooting)


## HttpClient

HTTP client with automatic request/response logging and sensitive data masking.

### Signature

```python
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
) → subclass of `httpx.Client`
```

### Features

- Full-featured HTTP client with automatic request/response logging
- Sensitive data masking for headers and JSON fields
- Automatic suppression of internal httpx/httpcore loggers
- Context manager support
- All `httpx.Client` methods: `get`, `post`, `put`, `delete`, `patch`, `request`

### Installation

```bash
pip install "qapytest[http]"
```

### Example Usage

```python
from qapytest import HttpClient

client = HttpClient(
    base_url="https://jsonplaceholder.typicode.com",
    timeout=30,
    headers={"Authorization": "Bearer token"},
    mask_sensitive_data=True,
    enable_log=True,
)
```

---

## GraphQLClient

Specialized client for GraphQL APIs with automatic logging and sensitive data masking.

### Signature

```python
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
    **kwargs,
) # -> subclass of `httpx.Client`
```

### Features

- Automatic POST request formation
- GraphQL query and variables logging
- Response time tracking
- Sensitive data masking
- Status code logging

### Installation

```bash
pip install "qapytest[http]"
```

### Methods

- `execute(query: str, variables: dict | None = None) → httpx.Response`

### Example Usage

```python
from qapytest import GraphQLClient

client = GraphQLClient(
    endpoint_url="https://spacex-production.up.railway.app/",
    headers={"Authorization": "Bearer token"},
    verify=True,
    timeout=15.0,
    mask_sensitive_data=True,
    enable_log=True,
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
```

---

## SqlClient

Client for executing SQL queries with automatic transaction management and logging.

### Signature

```python
SqlClient(
    connection_string: str,
    name_logger: str = "SqlClient",
    mask_sensitive_data: bool = True,
    sensitive_data: set[str] | None = None,
    **kwargs,
)
```

### Requirements

**A corresponding database driver is required.** See [SQLAlchemy Dialects](https://docs.sqlalchemy.org/en/20/dialects/index.html) for the complete list.

Popular drivers:
- PostgreSQL: `pip install psycopg2-binary`
- MySQL: `pip install mysql-connector-python`
- SQLite: built-in (no additional installation needed)
- Oracle: `pip install oracledb`
- SQL Server: `pip install pyodbc`

### Installation

```bash
pip install "qapytest[sql]"
# Plus the appropriate database driver
pip install psycopg2-binary  # For PostgreSQL example
```

### Features

- Safe parameterized queries
- Automatic rollback on errors
- Query validation
- Sensitive data masking
- Context manager support
- Batch operations support

### Methods

- `fetch_data(query: str, params: dict | None = None) → list[dict]`
  - Execute SELECT queries, returns list of dictionaries

- `execute_query(query: str, params: list[dict[str, Any]] | dict[str, Any] | None = None, return_inserted_ids: bool = False) → dict[str, Any]`
  - Execute INSERT/UPDATE/DELETE with auto-commit, returns execution statistics

- `fetch_single_value(query: str, params: dict | None = None) → Any`
  - Returns single value from first row (useful for COUNT, MAX, etc.)

- `close()`
  - Close database connection and dispose engine

### Example Usage

```python
from qapytest import SqlClient

db = SqlClient(
    "postgresql://user:pass@localhost:5432/testdb",
    name_logger="SqlClient",
    mask_sensitive_data=True,
    sensitive_data={"api_key", "auth_token"}
)
users = db.fetch_data(
    "SELECT * FROM users WHERE active = :status AND age > :min_age",
    params={"status": True, "min_age": 18}
)
```

---

## RedisClient

Redis client wrapper with comprehensive logging for all Redis commands.

### Signature

```python
RedisClient(
    host: str,
    port: int = 6379,
    name_logger: str = "RedisClient",
    **kwargs,
) → subclass of `redis.Redis`
```

### Features

- Inherits all functionality from `redis-py`
- Comprehensive logging of all Redis commands
- Result logging at DEBUG level
- Automatic suppression of internal redis loggers

### Installation

```bash
pip install "qapytest[redis]"
```

### Methods

All standard `redis.Redis` methods:
- `set`, `get`, `delete`, `exists`
- `lpush`, `rpop`, `lpop`, `rpush`
- `sadd`, `sismember`, `smembers`
- `hset`, `hget`, `hgetall`
- And many more...

### Example Usage

```python
from qapytest import RedisClient

redis_client = RedisClient(
    host="localhost",
    port=6379,
    db=0,
    name_logger="RedisClient",
)
redis_client.set("user:123:status", "active", ex=3600)
status = redis_client.get("user:123:status")
```

---

## GrpcClient

gRPC client for convenient interaction with gRPC APIs, with support for server reflection and compiled stubs, plus automatic structured logging.

### Signature

```python
GrpcClient(
    base_url: str,
    pb2_modules: list[AnyType] | None = None,
    timeout: float = 10.0,
    name_logger: str = "GrpcClient",
    enable_log: bool = True,
    verify: bool = True,
    **kwargs,
)
```

### Features

- Support for both reflection (automatic discovery) and compiled python stubs
- Automatic and structured logging for each request and response
- Execution time tracking and error details logging
- `verify=False` flag to automatically bypass SSL verification on test environments (similar to `grpcurl -insecure`)
- Native DNS fallback automatically enabled under the hood for VPNs and macOS compatibility
- Context manager support and proper connection closing

### Installation

```bash
pip install "qapytest[grpc]"
```

### Methods

- `request(service: str, method: str, data: dict | list[dict] | None = None, **kwargs) → dict | Any`
  - Perform a gRPC request with logging. Supports both unary and stream responses.
- `close()`
  - Close the underlying gRPC channel.

### Example Usage

```python
from qapytest import GrpcClient

# 1. Plaintext connection (without SSL, typically local development like `grpcurl -plaintext`)
client_local = GrpcClient(
    base_url="localhost:50051", 
    ssl=False, 
    enable_log=True
)

# 2. With SSL and Certificate Bypass (for test environments like `grpcurl -insecure`)
client = GrpcClient(
    base_url="test.lan:443",
    verify=False,
    enable_log=True
)
response = client.request("helloworld.Greeter", "SayHello", {"name": "QA"})
print(response)

# 3. Without Reflection (with compiled python stubs):
import helloworld_pb2

client_stub = GrpcClient(
    base_url="prod.com:443", # verify=True by default for production
    pb2_modules=[helloworld_pb2],
)
response = client_stub.request("helloworld.Greeter", "SayHello", {"name": "QA"})
print(response)
```

---

## Troubleshooting

If you encounter import errors for missing modules, ensure you've installed the required optional dependencies:

```bash
# HTTP/GraphQL client not found?
pip install "qapytest[http]"

# SQL client not found?
pip install "qapytest[sql]"
# Plus database driver

# Redis client not found?
pip install "qapytest[redis]"

# All clients at once
pip install "qapytest[all]"
```
