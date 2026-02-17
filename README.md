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
- **JSON report generation:** structured data report at `report.json` for
  programmatic processing and CI/CD integration.
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

## 📚 Documentation

Complete documentation organized by topic:

- [Quick Start Guide](https://github.com/o73k51i/qapytest/blob/main/docs/QuickStart.md)
- [Installation Guide](https://github.com/o73k51i/qapytest/blob/main/docs/Installation.md)
- [Core Tools](https://github.com/o73k51i/qapytest/blob/main/docs/CoreTools.md)
- [Test Data Generation](https://github.com/o73k51i/qapytest/blob/main/docs/TestDataGeneration.md)
- [Test Markers](https://github.com/o73k51i/qapytest/blob/main/docs/Markers.md)
- [CLI Options](https://github.com/o73k51i/qapytest/blob/main/docs/CLI.md)
- [Integration Clients](https://github.com/o73k51i/qapytest/blob/main/docs/Clients.md)
- [Browser Automation](https://github.com/o73k51i/qapytest/blob/main/docs/BrowserAutomation.md)

## 📑 License

This project is distributed under the
[license](https://github.com/o73k51i/qapytest/blob/main/LICENSE).
