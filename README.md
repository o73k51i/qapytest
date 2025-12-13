# QaPyTest

[![PyPI version](https://img.shields.io/pypi/v/qapytest.svg)](https://pypi.org/project/qapytest/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/qapytest?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLUE&right_color=YELLOW&left_text=downloads)](https://pepy.tech/projects/qapytest)
[![Python versions](https://img.shields.io/pypi/pyversions/qapytest.svg)](https://pypi.org/project/qapytest/)
[![License](https://img.shields.io/github/license/o73k51i/qapytest.svg)](https://github.com/o73k51i/qapytest/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/o73k51i/qapytest.svg?style=social)](https://github.com/o73k51i/qapytest)

`QaPyTest` — a powerful testing framework based on pytest, specifically
designed for QA engineers. Turn your ordinary tests into detailed, structured
reports with built-in HTTP, SQL, Redis and GraphQL clients.

🎯 **QA made for QA** — every feature is designed for real testing and
debugging needs.

## ⚡ Why QaPyTest?

- **🚀 Ready to use:** Install → run → get a beautiful report
- **🔧 Built-in clients:** HTTP, SQL, Redis, GraphQL — all in one package
- **📊 Professional reports:** HTML reports with attachments and logs
- **🎯 Soft assertions:** Collect multiple failures in one run instead of
  stopping at the first
- **📝 Structured steps:** Make your tests self-documenting
- **🔍 Debugging friendly:** Full traceability of every action in the test

## ⚙️ Key features

- **HTML report generation:** beautiful self-contained report at `report.html`.
- **JSON report generation:** structured data report at `report.json` for programmatic processing and CI/CD integration.
- **Soft assertions:** allow collecting multiple failures in a single run
  without immediately ending the test.
- **Advanced steps:** structured logging of test steps for better report
  readability.
- **Attachments:** ability to add files, logs and screenshots to test reports.
- **HTTP client:** client for performing HTTP requests.
- **SQL client:** client for executing raw SQL queries.
- **Redis client:** client for working with Redis.
- **GraphQL client:** client for executing GraphQL requests.
- **Browser automation:** seamless integration with pytest-playwright for
  end-to-end web testing.
- **Test data generation:** built-in Faker support for creating realistic test
  data.
- **JSON Schema validation:** function to validate API responses or test
  artifacts with support for soft-assert and strict mode.
- **Unicode support:** proper display of Unicode characters (Cyrillic, Arabic,
  Chinese, etc.) in terminal and HTML reports.

## 👥 Ideal for

- **QA Engineers** — automate testing of APIs, databases, web services and
  browser interfaces
- **Test Automation specialists** — get a ready toolkit for comprehensive
  testing including web automation

## 🚀 Quick start

### 1️⃣ Installation

```bash
pip install qapytest
```

### 2️⃣ Your first powerful test

```python
from qapytest import step, attach, soft_assert, HttpClient, SqlClient, Faker

def test_comprehensive_api_validation():
    fake = Faker()

    # Generate realistic test data
    user_data = {"name": fake.name(), "email": fake.email()}

    # Structured steps for readability
    with step('🌐 Testing API endpoint'):
        client = HttpClient(base_url="https://api.example.com")
        response = client.post("/users", json=user_data)
        assert response.status_code == 201

    # Add artifacts for debugging
    attach(response.text, 'api_response.json')

    # Soft assertions - collect all failures
    soft_assert(response.json()['id'] > 0, 'User ID check')
    soft_assert(
      response.json()['email'] == user_data['email'],
      'Email matches'
    )

    # Database integration
    with step('🗄️ Validate data in DB'):
        db = SqlClient("sqlite:///:memory:")
        user_db_data = db.fetch_data(
            "SELECT * FROM users WHERE email = :email",
            params={"email": user_data['email']}
        )
        assert len(user_db_data) == 1
```

### 3️⃣ Run with beautiful reports

```bash
pytest --report-html
# Open report.html 🎨
```

## 🔌 Built-in clients — everything QA needs

### 🌐 HttpClient — HTTP testing on steroids

```python
client = HttpClient(base_url="https://api.example.com")
response = client.post("/auth/login", json={"foo": "bar"})
```

### 📊 GraphQL client — Modern APIs with minimal effort

```python
gql = GraphQLClient("https://api.github.com/graphql")
result = gql.execute("query { viewer { foo } }")
```

### 🗄️ SqlClient — Direct DB access

```python
db = SqlClient("sqlite:///:memory:")
users = db.fetch_data("SELECT foo FROM bar")
```

### 🔴 RedisClient — Enhanced Redis operations with logging

```python
redis_client = RedisClient(host="localhost")
redis_client.set("foo", "bar")
foo = redis_client.get("foo")
```

### 🎭 Browser automation — powered by Playwright

```python
def test_web_app(page):
    fake = Faker()
    # Navigate to login page
    page.goto("https://example.com/login")
    # Generate and fill test data
    page.get_by_label("Username").fill(fake.user_name())
    page.get_by_label("Password").fill(fake.password())
    page.get_by_role("button", name="Log in").click()
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
soft_assert(user.id == 1, "Check user ID")
soft_assert(user.active, 'Check status')
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
validate_json(api_response, schema=user_schema)
```

### 🎲 Faker — Realistic test data generation

```python
fake = Faker()
fake.text(max_nb_chars=200)  # Random text
fake.random_int(min=1, max=100)  # Random numbers
```

More about the API on the [documentation page](https://github.com/o73k51i/qapytest/blob/main/docs/API.md).

## Test markers

QaPyTest also supports custom pytest markers to improve reporting:

- **`@pytest.mark.title("Custom Test Name")`** : sets a custom test name in
  the HTML report
- **`@pytest.mark.component("API", "Database")`** : adds component tags to
  the test

### Example usage of markers

```python
import pytest

@pytest.mark.title("User authorization check")
@pytest.mark.component("Auth", "API")
def test_user_login():
    pass
```

## ⚙️ CLI options

- **`--env-file`** : path to an `.env` file with environment settings
  (default — `./.env`).
- **`--env-override`** : if set, values from the `.env` file will override
  existing environment variables.
- **`--report-json [PATH]`** : create a JSON report with test results; optionally
  specify a path (default — `./report.json`).
- **`--report-html [PATH]`** : create a self-contained HTML report; optionally
  specify a path (default — `report.html`).
- **`--report-title NAME`** : set the HTML report title.
- **`--report-theme {light,dark,auto}`** : choose the report theme: `light`,
  `dark` or `auto` (default).
- **`--disable-unicode`** : disable Unicode character display in 
  terminal output for compatibility with older terminals or CI systems.

More about CLI options on the [documentation page](https://github.com/o73k51i/qapytest/blob/main/docs/CLI.md).

## 📑 License

This project is distributed under the [license](https://github.com/o73k51i/qapytest/blob/main/LICENSE).
