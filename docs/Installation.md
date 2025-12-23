# Installation Guide

This guide explains how to install **QaPyTest** with optional components based
on your needs.

- [Basic Installation](#basic-installation)
- [Optional Components](#optional-components)
  - [HTTP Client](#http-client)
  - [SQL Client](#sql-client)
  - [Redis Client](#redis-client)
  - [Web Testing (Playwright)](#web-testing-playwright)
- [Multiple Components](#multiple-components)
- [All Components](#all-components)
- [Compatibility](#compatibility)


## Basic Installation

Install the core framework with minimal dependencies:

```bash
pip install qapytest
```

This includes:
- Pytest integration
- Test steps
- Soft assertions
- Attachment
- Reporting
- Basic utilities

## Optional Components

**QaPyTest** supports optional dependencies for different features. You can
install only what you need.

### HTTP Client

For HTTP/REST API testing with httpx:

```bash
pip install "qapytest[http]"
```

Includes:
- HTTP client with support for REST APIs
- Request/response handling

### SQL Client

For database testing with SQLAlchemy:

```bash
pip install "qapytest[sql]"
```

Includes:
- SQL database connections
- Query execution
- Support for multiple database engines

**Additional Step**: Install a database driver for your database engine:

- PostgreSQL: `pip install psycopg2`
- MySQL: `pip install mysql-connector-python`
- SQLite: built-in (no additional installation needed)
- Oracle: `pip install oracledb`
- SQL Server: `pip install pyodbc`
- Or any other driver supported by SQLAlchemy

For a complete list of supported databases and drivers, see
[SQLAlchemy Dialects documentation](https://docs.sqlalchemy.org/en/20/dialects/).

### Redis Client

For Redis database testing:

```bash
pip install "qapytest[redis]"
```

Includes:
- Redis client for caching and data store testing
- Key-value operations

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

## Compatibility

- **Python**: 3.10, 3.11, 3.12, 3.13
- **Platform**: Windows, macOS, Linux
