# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.4] - 2025-11-23

### Enhanced

- 📊 **Interactive HTML Report** - significantly improved report interactivity with new features:
  - **JSON Viewer** - interactive tree view for JSON attachments with search and expand/collapse capabilities
  - **Log Filtering** - filter logs by logger name and level, with search functionality
  - **Component Filtering** - easily filter test results by component
  - **Step Management** - expand/collapse all steps with a single click
  - **Navigation** - added "Scroll to top" button for easier navigation in long reports
- 🛠️ **Soft Assertions** - improved display of soft assertion failures in the report

## [0.3.3] - 2025-10-31

### Fixed

- ⚙️ **CLI option renamed** - `--disable-unicode-terminal` renamed to `--disable-unicode`
- 🖥️ **Unicode display in IDE** - fixed Unicode rendering issues in integrated development environments
- 🔧 **Minor bug fixes** - resolved small issues to improve overall stability

## [0.3.2] - 2025-10-29

### Added

- 🌍 **Terminal Unicode support** - proper display of Unicode characters (Cyrillic, Arabic, Chinese, etc.) in terminal output for parametrized test names
- ⚙️ **`--disable-unicode-terminal`** CLI option - compatibility flag for older terminals and CI systems

### Enhanced

- 📝 **Terminal output** - Unicode escape sequences in test names are now automatically decoded for better readability
- 🛠️ **Compatibility** - added fallback option for environments that don't support Unicode display

## [0.3.1] - 2025-10-28

### Fixed

- 🔇 **Faker logging** - suppressed Faker library logging to WARNING level for cleaner HTML report output

## [0.3.0] - 2025-10-24

### Added

- 🎭 **Playwright integration** - pytest-playwright support with cross-browser testing (Chromium, Firefox, WebKit)
- 🌐 **Browser automation** - video recording, screenshots, traces, and mobile device emulation
- 🎲 **Faker integration** - built-in test data generation
- 🏷️ **Logger naming** - added ability to provide custom names for client loggers

### Changed

- 📚 **Documentation updates** - CLI and API docs
- 📚 **Third-party notices** - added Playwright and Faker licenses
- 🔧 **Project structure** - enhanced with browser testing capabilities
- 🧪 **Demo examples** - enhanced demo.py with comprehensive test scenarios

### Fixed

- 🔧 **Internal fixes** - resolved internal bugs and improved stability

## [0.2.0] - 2025-10-06

### 🔧 Refactoring

- **Refactored public methods** - updated SqlClient API structure
- **Updated documentation** - aligned with current SqlClient implementation
- **Fixed tests** - updated test cases to match current SqlClient implementation

## [0.1.6] - 2025-09-30

### Fixed

- 🔴 **RedisClient** - improved connection handling and management
- 🔧 **Configuration** - fixed Redis client configuration and connection parameters
- 🔇 **HTTP library logging** - suppressed verbose logging from httpx, httpcore, and urllib3 to WARNING level to reduce noise in test output

## [0.1.5] - 2025-09-25

### Fixed

- 🔒 **HTTP request logging** - fixed data masking in HTTP request/response logging to properly sanitize sensitive information
- 🌐 **Response headers logging** - improved logging of response headers with enhanced data sanitization

## [0.1.4] - 2025-09-25

### Enhanced

- 🔒 **Sensitive data masking** - comprehensive masking for headers, JSON fields, and text patterns in HTTP/GraphQL clients
- 🌐 **HttpClient & GraphQLClient** - unified BaseHttpClient architecture with enhanced logging and data sanitization
- 📝 **Documentation** - updated API documentation with complete parameter descriptions and sensitive data masking features
- 🔗 **README links** - fixed GitHub documentation links to use absolute URLs

### Added

- 🛡️ **New configuration options** for HttpClient and GraphQLClient:
  - `sensitive_headers` - set of header names to mask in logs
  - `sensitive_json_fields` - set of JSON field names to mask
  - `sensitive_text_patterns` - regex patterns for text masking
  - `mask_sensitive_data` - toggle for sensitive data masking

### Fixed

- 🧪 **Test improvements** - enhanced test coverage for logging assertions and header sanitization
- 📊 **GraphQL client** - removed unnecessary mocks and improved test assertions
- 🔧 **Import organization** - refactored client imports for better maintainability

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

[0.3.4]: https://github.com/o73k51i/qapytest/releases/tag/v0.3.4
[0.3.3]: https://github.com/o73k51i/qapytest/releases/tag/v0.3.3
[0.3.2]: https://github.com/o73k51i/qapytest/releases/tag/v0.3.2
[0.3.1]: https://github.com/o73k51i/qapytest/releases/tag/v0.3.1
[0.3.0]: https://github.com/o73k51i/qapytest/releases/tag/v0.3.0
[0.3.0]: https://github.com/o73k51i/qapytest/releases/tag/v0.3.0
[0.2.0]: https://github.com/o73k51i/qapytest/releases/tag/v0.2.0
[0.1.6]: https://github.com/o73k51i/qapytest/releases/tag/v0.1.6
[0.1.5]: https://github.com/o73k51i/qapytest/releases/tag/v0.1.5
[0.1.4]: https://github.com/o73k51i/qapytest/releases/tag/v0.1.4
[0.1.3]: https://github.com/o73k51i/qapytest/releases/tag/v0.1.3
[0.1.2]: https://github.com/o73k51i/qapytest/releases/tag/v0.1.2
[0.1.1]: https://github.com/o73k51i/qapytest/releases/tag/v0.1.1
[0.1.0]: https://github.com/o73k51i/qapytest/releases/tag/v0.1.0
