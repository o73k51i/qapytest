"""QAPyTest core logic and pytest plugin.

This module implements the core logic for the QAPyTest package and
functions as an internal plugin for Pytest.

It defines custom settings, hooks, and extends the functionality
of Pytest.
"""

from __future__ import annotations

import shutil
from collections.abc import Generator
from pathlib import Path

import pytest

from qapytest import _config as cfg
from qapytest import _internal as utils
from qapytest import _report as report


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("QAPyTest", "QAPyTest custom options")
    group.addoption(
        "--env-file",
        action="store",
        default=None,
        help="Path to a .env file.",
    )
    group.addoption(
        "--env-override",
        action="store_true",
        default=False,
        help="If set, values from the .env file will override already-set environment variables.",
    )
    group.addoption(
        "--report-html",
        action="store",
        dest="report_html",
        metavar="PATH",
        nargs="?",
        const="report.html",
        default=None,
        help="Create a self-contained HTML report.",
    )
    group.addoption(
        "--report-title",
        action="store",
        dest="report_title",
        metavar="NAME",
        default="QAPyTest Report",
        help="Title for the HTML report.",
    )
    group.addoption(
        "--report-theme",
        action="store",
        dest="report_theme",
        choices=["light", "dark", "auto"],
        default="auto",
        help="Theme for the HTML report: light, dark, or auto (default).",
    )
    group.addoption(
        "--max-attachment-bytes",
        action="store",
        dest="max_attachment_bytes",
        type=int,
        default=None,
        help="Max bytes to embed for any single attachment (text or binary). Larger data will be truncated.",
    )
    group.addoption(
        "--disable-unicode",
        action="store_true",
        default=False,
        help="Disable Unicode character display in terminal (for compatibility).",
    )


def pytest_configure(config: pytest.Config) -> None:
    env_file_path_str = config.getoption("--env-file")
    env_file = Path(env_file_path_str) if env_file_path_str else Path(".env")
    utils.load_env_file(env_file_path=env_file, override=bool(config.getoption("--env-override")))

    config.addinivalue_line("markers", "title(name): Custom display title for a test in the HTML report.")
    config.addinivalue_line("markers", "component(*names): Component labels for a test in the HTML report.")

    cfg.ATTACH_LIMIT_BYTES = config.getoption("max_attachment_bytes")

    if not config.getoption("--disable-unicode"):
        for i, arg in enumerate(config.args):
            if "::" in arg:
                path_part, test_part = arg.split("::", 1)
                path = Path(path_part)
                if not path.is_absolute():
                    path = Path.cwd() / path
                abs_path = str(path)
                try:
                    encoded_test = test_part.encode("ascii", "backslashreplace").decode("ascii")
                except Exception:
                    encoded_test = test_part
                config.args[i] = abs_path + "::" + encoded_test

        try:
            import _pytest.main as main

            spec_class = main.Spec  # type: ignore
            original_matches = spec_class.matches

            def new_matches(self, item):  # noqa: ANN001, ANN202
                if hasattr(item, "nodeid") and not item.config.getoption("--disable-unicode"):
                    encoded_item_nodeid = item.nodeid.encode("ascii", "backslashreplace").decode("ascii")
                    if encoded_item_nodeid == self.nodeid:
                        return True
                return original_matches(self, item)

            spec_class.matches = new_matches
        except Exception:  # noqa: S110
            pass

    report_path = config.getoption("report_html")
    if not report_path:
        return

    report_title = config.getoption("report_title")
    report_theme = config.getoption("report_theme")
    plugin = report.HtmlReportPlugin(config, report_path, report_title, report_theme)
    config._html_report_plugin = plugin  # type: ignore[attr-defined]  # noqa: SLF001
    config.pluginmanager.register(plugin, "_html_report_plugin")


def pytest_unconfigure(config: pytest.Config) -> None:
    plugin = getattr(config, "_html_report_plugin", None)
    if plugin is not None:
        config.pluginmanager.unregister(plugin, name="_html_report_plugin")


def pytest_runtest_setup(item: pytest.Item) -> None:
    root_list = []
    item._execution_log_token = cfg.CURRENT_EXECUTION_LOG.set(root_list)  # type: ignore[attr-defined]  # noqa: SLF001
    item._log_stack_token = cfg.CURRENT_LOG_CONTAINER_STACK.set([root_list])  # type: ignore[attr-defined]  # noqa: SLF001


def pytest_runtest_teardown(item: pytest.Item, nextitem: pytest.Item | None) -> None:  # noqa: ARG001
    log_token = getattr(item, "_execution_log_token", None)
    if log_token:
        cfg.CURRENT_EXECUTION_LOG.reset(log_token)
    stack_token = getattr(item, "_log_stack_token", None)
    if stack_token:
        cfg.CURRENT_LOG_CONTAINER_STACK.reset(stack_token)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: cfg.AnyType) -> Generator[cfg.AnyType, None, None]:
    outcome = yield
    report: pytest.TestReport = outcome.get_result()  # type: ignore

    if not item.config.getoption("disable_unicode"):
        if hasattr(report, "nodeid") and report.nodeid and "\\" in report.nodeid:
            report.nodeid = utils.decode_unicode_escapes(report.nodeid)
        if hasattr(report, "location") and getattr(report, "location", None):
            try:
                path, lineno, domain = report.location  # type: ignore[misc]
                if isinstance(domain, str) and "\\" in domain:
                    report.location = (path, lineno, utils.decode_unicode_escapes(domain))
            except Exception:  # noqa: S110
                pass

    try:
        if call and getattr(call, "excinfo", None) is not None and call.excinfo.type is not None:
            report._exc_class_name = getattr(  # noqa: SLF001 # type: ignore
                call.excinfo.type,
                "__name__",
                str(call.excinfo.type),
            )  # type: ignore[attr-defined]
        else:
            report._exc_class_name = None  # type: ignore[attr-defined]  # noqa: SLF001
    except Exception:
        report._exc_class_name = None  # type: ignore[attr-defined]  # noqa: SLF001

    execution_log = cfg.CURRENT_EXECUTION_LOG.get()
    if isinstance(execution_log, list):
        report.execution_log = list(execution_log)  # type: ignore[attr-defined]
        report.user_properties.append(("execution_log", report.execution_log))  # type: ignore[attr-defined]

        if report.when == "call" and report.outcome == "passed" and utils.has_failures_in_log(report.execution_log):
            report._softfailed = True  # type: ignore[attr-defined]  # noqa: SLF001
            report._soft_assert_only = True  # type: ignore[attr-defined]  # noqa: SLF001  # Marker for soft assertion failures
            if getattr(report, "wasxfail", None):
                report.outcome = "skipped"
            else:
                report.outcome = "failed"

            header = "One or more assertions failed."
            error_summary_lines = utils.generate_terminal_summary(report.execution_log)  # type: ignore[attr-defined]
            full_summary = [header, *error_summary_lines]
            report.longrepr = "\n".join(full_summary)

    if (
        not item.config.getoption("disable_unicode")
        and hasattr(report, "longrepr")
        and report.longrepr
        and "\\u" in str(report.longrepr)
    ):
        report.longrepr = utils.decode_unicode_escapes(str(report.longrepr))


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:  # noqa: ARG001
    for item in items:
        title_marker = item.get_closest_marker("title")
        if title_marker and title_marker.args:  # noqa: SIM102
            if title := str(title_marker.args[0]):
                item.user_properties.append(("title", title))
        components, seen_components = [], set()
        for marker in item.iter_markers(name="component"):
            for arg in marker.args:
                if isinstance(arg, str) and arg and arg not in seen_components:
                    seen_components.add(arg)
                    components.append(arg)
        if components:
            item.user_properties.append(("components", tuple(components)))


def pytest_itemcollected(item: pytest.Item) -> None:
    if not item.config.getoption("disable_unicode"):
        if "\\" in item.nodeid:
            item._nodeid = utils.decode_unicode_escapes(item.nodeid)  # noqa: SLF001
        try:
            if isinstance(getattr(item, "name", None), str) and "\\u" in item.name:
                decoded_name = utils.decode_unicode_escapes(item.name)
                object.__setattr__(item, "name", decoded_name)
        except Exception:  # noqa: S110
            pass


def pytest_sessionstart(session):  # noqa: ANN001, ANN202
    """Patch terminal reporter at session start."""
    if session.config.getoption("disable_unicode"):
        return

    try:
        terminal_reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if terminal_reporter and hasattr(terminal_reporter, "_tw"):
            tw = terminal_reporter._tw  # noqa: SLF001
            if hasattr(tw, "write"):
                original_write = tw.write

                def unicode_write(s, **kwargs):  # noqa: ANN001, ANN202
                    if isinstance(s, str) and "\\" in s:
                        decoded_s = utils.decode_unicode_escapes(s)
                        if decoded_s.startswith("_") and decoded_s.endswith("_") and " " in decoded_s:
                            stripped = decoded_s.strip("_")
                            if stripped.startswith(" ") and stripped.endswith(" "):
                                nodeid = stripped.strip()
                                total_width = shutil.get_terminal_size().columns - 2
                                nodeid_len = len(nodeid)
                                if nodeid_len + 4 <= total_width:
                                    left_underscores = (total_width - nodeid_len - 2) // 2
                                    right_underscores = total_width - left_underscores - len(nodeid) - 2
                                    decoded_s = "_" * left_underscores + " " + nodeid + " " + "_" * right_underscores
                        s = decoded_s
                    return original_write(s, **kwargs)

                tw.write = unicode_write
    except Exception:  # noqa: S110
        pass
