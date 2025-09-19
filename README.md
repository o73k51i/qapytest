# QaPyTest

[![PyPI version](https://img.shields.io/pypi/v/qapytest.svg)](https://pypi.org/project/qapytest/)
[![Python versions](https://img.shields.io/pypi/pyversions/qapytest.svg)](https://pypi.org/project/qapytest/)
[![License](https://img.shields.io/github/license/o73k51i/qapytest.svg)](https://github.com/o73k51i/qapytest/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/o73k51i/qapytest.svg?style=social)](https://github.com/o73k51i/qapytest)

`QaPyTest` — a powerful testing framework based on pytest, specifically designed for QA engineers.
Turn your ordinary tests into detailed, structured reports with built-in HTTP, SQL, Redis and GraphQL clients.

🎯 **QA made for QA** — every feature is designed for real testing and debugging needs.

## ⚡ Why QaPyTest?

- **🚀 Ready to use:** Install → run → get a beautiful report
- **🔧 Built-in clients:** HTTP, SQL, Redis, GraphQL — all in one package
- **📊 Professional reports:** HTML reports with attachments and logs
- **🎯 Soft assertions:** Collect multiple failures in one run instead of stopping at the first
- **📝 Structured steps:** Make your tests self-documenting
- **🔍 Debugging friendly:** Full traceability of every action in the test

## ⚙️ Key features

- **HTML report generation:** simple report at `report.html`.
- **Soft assertions:** allow collecting multiple failures in a single run without immediately ending the test.
- **Advanced steps:** structured logging of test steps for better report readability.
- **Attachments:** ability to add files, logs and screenshots to test reports.
- **HTTP client:** client for performing HTTP requests.
- **SQL client:** client for executing raw SQL queries.
- **Redis client:** client for working with Redis with automatic JSON (de)serialization.
- **GraphQL client:** client for executing GraphQL requests.
- **JSON Schema validation:** function to validate API responses or test artifacts with support for soft-assert and strict mode.

## 👥 Ideal for

- **QA Engineers** — automate testing of APIs, databases and web services
- **Test Automation specialists** — get a ready toolkit for comprehensive testing

## 🚀 Quick start

### 1️⃣ Installation

```bash
pip install qapytest
```

### 2️⃣ Your first powerful test

```python
from qapytest import step, attach, soft_assert, HttpClient, SqlClient

def test_comprehensive_api_validation():
    # Structured steps for readability
    with step('🌐 Testing API endpoint'):
        client = HttpClient(base_url="https://api.example.com")
        response = client.get("/users/1")
        assert response.status_code == 200
    
    # Add artifacts for debugging
    attach(response.text, 'api_response.json')
    
    # Soft assertions - collect all failures
    soft_assert(response.json()['id'] == 1, 'User ID check')
    soft_assert(response.json()['active'], 'User is active')
    
    # Database integration
    with step('🗄️ Validate data in DB'):
        db = SqlClient("postgresql://user:pass@localhost/db")
        user_data = db.fetch_data("SELECT * FROM users WHERE id = 1")
        assert len(user_data) == 1
```

### 3️⃣ Run with beautiful reports

```bash
pytest --report-html
# Open report.html 🎨
```

## 🔌 Built-in clients — everything QA needs

### 🌐 HttpClient — HTTP testing on steroids
```python
client = HttpClient(base_url="https://api.example.com", timeout=30)
response = client.post("/auth/login", json={"username": "test"})
# Automatic logging of requests/responses + timing + headers
```

### 🗄️ SqlClient — Direct DB access  
```python
db = SqlClient("postgresql://localhost/testdb")
users = db.fetch_data("SELECT * FROM users WHERE active = true")
db.execute_and_commit("UPDATE users SET last_login = NOW() WHERE id = 1")
```

### 📊 GraphQL client — Modern APIs with minimal effort
```python
gql = GraphQLClient("https://api.github.com/graphql", 
                   headers={"Authorization": "Bearer token"})
result = gql.execute("query { viewer { login } }")
```

### 🔴 RedisClient — Caching and sessions under control
```python
redis = RedisClient(host="localhost", port=6379)
redis.set_value("session:123", {"user_id": 1, "expires": "2024-01-01"})
session_data = redis.get_value("session:123")  # Automatic JSON serialization!
```

## 🎛️ Core testing tools

### 📝 Structured steps
```python
with step('🔍 Check authorization'):
    with step('Send login request'):
        response = client.post("/login", json=creds)
    with step('Validate token'):
        assert "token" in response.json()
```

### 🎯 Soft Assertions — collect all failures  
```python
soft_assert(user.id == 1, 'User ID')
soft_assert(user.active, 'Active status')
soft_assert('admin' == user.roles, 'Access rights')
# The test will continue and show all failures together!
```

### 📎 Attachments — full context
```python
attach(response.json(), 'server response')
attach(screenshot_bytes, 'error page') 
attach(content, 'application', mime='text/plain')
```

### ✅ JSON Schema validation
```python
# Strict validation — stop the test on schema validation error
validate_json(api_response, schema_path="user_schema.json", strict=True)

# Soft mode — collect all schema errors and continue test execution
validate_json(api_response, schema=user_schema, strict=False)
```

More about the API on the [documentation page](./docs/API.md).

## Test markers

QaPyTest also supports custom pytest markers to improve reporting:

- **`@pytest.mark.title("Custom Test Name")`** : sets a custom test name in the HTML report
- **`@pytest.mark.component("API", "Database")`** : adds component tags to the test

### Example usage of markers

```python
import pytest

@pytest.mark.title("User authorization check")
@pytest.mark.component("Auth", "API")
def test_user_login():
    # test code
    pass
```

## ⚙️ CLI options

- **`--env-file`** : path to an `.env` file with environment settings (default — `./.env`).
- **`--env-override`** : if set, values from the `.env` file will override existing environment variables.
- **`--report-html [PATH]`** : create a self-contained HTML report; optionally specify a path (default — `report.html`).
- **`--report-title NAME`** : set the HTML report title.
- **`--report-theme {light,dark,auto}`** : choose the report theme: `light`, `dark` or `auto` (default).
- **`--max-attachment-bytes N`** : maximum size of an attachment (in bytes) that will be inlined in the HTML; larger files will be truncated.

More about CLI options on the [documentation page](./docs/CLI.md).

## 📑 License

This project is distributed under the [license](./LICENSE).
