# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2025-09-24

### Fixed
- 🌐 **HTTP request logging** - improved logging format and sensitive data sanitization in HTTP requests/responses
- 📊 **GraphQL client** - enhanced logging and data masking capabilities for GraphQL operations
- 🧪 **Internal testing improvements** - updated test suite to align with current HttpClient and GraphQLClient implementations

## [0.1.2] - 2025-09-22

### Fixed
- 🌐 **Unicode support in HTML reports** - fixed display of Cyrillic and other non-ASCII characters in parametrized test names
- 📊 **Parameter display** - test parameters with Unicode characters now show properly instead of escape sequences
- 🔧 **NodeID formatting** - improved Unicode handling in test identification strings

### Added
- ✅ **Unicode decoding functions** - added `decode_unicode_escapes()` utility for proper character rendering
- 📝 **Enhanced parameter parsing** - improved `parse_params_from_nodeid()` with Unicode escape sequence support
- 🧪 **Comprehensive tests** - added test coverage for Unicode handling functions

## [0.1.1] - 2025-09-19

### Changed
- 🔧 **Internal improvements** - enhanced project structure and configuration
- 📝 **Documentation updates** - improved README with badges and better formatting
- ⚙️ **Build configuration** - optimized pyproject.toml for PyPI publishing
- 📋 **Project metadata** - added comprehensive classifiers and project URLs
- 🏷️ **Type support** - maintained py.typed file for better IDE integration

## [0.1.0] - 2025-09-19

### Added
- 🚀 **Initial release** of QaPyTest - powerful testing framework for QA engineers
- 📊 **HTML report generation** with customizable themes (light/dark/auto)
- 🎯 **Soft assertions** - collect multiple failures in single test run
- 📝 **Structured test steps** with nested hierarchy support
- 📎 **Attachments system** - add files, logs, and screenshots to reports
- 🌐 **HttpClient** - built-in HTTP client with automatic request/response logging
- 🗄️ **SqlClient** - direct database access for SQL queries and validation
- 🔴 **RedisClient** - Redis integration with automatic JSON serialization
- 📊 **GraphQLClient** - GraphQL query execution with error handling
- ✅ **JSON Schema validation** - validate API responses with soft-assert support
- 🏷️ **Custom pytest markers** - `@pytest.mark.title()` and `@pytest.mark.component()`
- ⚙️ **CLI options** - environment file loading, report customization, theme selection
- 🔧 **Environment configuration** - `.env` file support with override options
- 📚 **Comprehensive documentation** - API reference and CLI guide

### Features
- Python 3.10+ support
- Pytest plugin architecture
- Self-contained HTML reports
- Automatic request/response timing
- Configurable attachment size limits
- Professional report styling with responsive design

[0.1.3]: https://github.com/o73k51i/qapytest/releases/tag/v0.1.3
[0.1.2]: https://github.com/o73k51i/qapytest/releases/tag/v0.1.2
[0.1.1]: https://github.com/o73k51i/qapytest/releases/tag/v0.1.1
[0.1.0]: https://github.com/o73k51i/qapytest/releases/tag/v0.1.0