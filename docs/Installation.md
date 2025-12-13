# Installation Guide

This guide explains how to install **qapytest** with optional components based on your needs.

## Basic Installation

Install the core framework with minimal dependencies:

```bash
pip install qapytest
```

This includes:
- Pytest integration
- Test steps and reporting
- Soft assertions
- Basic utilities

## Optional Components

qapytest supports optional dependencies for different features. You can install only what you need.

### HTTP Client

For HTTP/REST API testing with httpx:

```bash
pip install "qapytest[http]"
```

Includes:
- HTTP client with support for REST APIs
- Request/response handling
- Built-in assertions for HTTP responses

### SQL Client

For database testing with SQLAlchemy:

```bash
pip install "qapytest[sql]"
```

Includes:
- SQL database connections
- Query execution and result validation
- Support for multiple database engines

**Additional Step**: Install a database driver for your database engine:

- PostgreSQL: `pip install psycopg2`
- MySQL: `pip install mysql-connector-python`
- SQLite: built-in (no additional installation needed)
- Oracle: `pip install oracledb`
- SQL Server: `pip install pyodbc`
- Or any other driver supported by SQLAlchemy

For a complete list of supported databases and drivers, see [SQLAlchemy Dialects documentation](https://docs.sqlalchemy.org/en/20/dialects/).

### Web Testing (Playwright)

For browser automation and web UI testing:

```bash
pip install "qapytest[web]"
```

Includes:
- Playwright integration for browser testing
- Page object support
- Web element interaction

**Additional Step**: Install browser binaries:

```bash
playwright install
```

This downloads the necessary browser binaries (Chromium, Firefox, WebKit) for Playwright to use.

### Redis Client

For Redis database testing:

```bash
pip install "qapytest[redis]"
```

Includes:
- Redis client for caching and data store testing
- Key-value operations

## Multiple Components

Install multiple components at once:

```bash
# HTTP and SQL
pip install "qapytest[http,sql]"

# Web and Redis
pip install "qapytest[web,redis]"

# HTTP, SQL, and Web
pip install "qapytest[http,sql,web]"
```

## All Components

Install all optional dependencies:

```bash
pip install "qapytest[all]"
```

## Development Installation

For contributors who want development dependencies:

```bash
pip install "qapytest[all]"
pip install -e ".[dev]"
```

Development dependencies include:
- Code linting (ruff)
- Pre-commit hooks

## Compatibility

- **Python**: 3.10, 3.11, 3.12, 3.13
- **Platform**: Windows, macOS, Linux

## Troubleshooting

If you encounter import errors for missing modules, ensure you've installed the required optional dependencies for the features you're using.

For example, if you get `ModuleNotFoundError: No module named 'httpx'`, install the http extra:

```bash
pip install "qapytest[http]"
```
