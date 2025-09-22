"""Module for pytest plugin that generates HTML reports."""

import datetime
from collections import defaultdict
from pathlib import Path

import jinja2
import pytest

from qapytest import _config as cfg
from qapytest import _internal as utils

_DEF_CSS = utils.load_asset("styles.css")
_DEF_JS = utils.load_asset("scripts.js")


class HtmlReportPlugin:
    def __init__(self, config: pytest.Config, path: str, title: str, theme: str) -> None:  # noqa: ARG002
        self.path, self.title, self.theme = path, title, theme
        self.session_start = datetime.datetime.now()
        self.results: dict[str, dict[str, cfg.AnyType]] = {}
        self.test_order: list[str] = []
        self.totals: dict[str, int] = defaultdict(int)
        self.collection_errors: list[dict[str, cfg.AnyType]] = []

    def _safe_location(self, report: pytest.TestReport) -> tuple[str, int, str]:
        try:
            loc = getattr(report, "location", None)
            if loc and isinstance(loc, tuple) and len(loc) >= 2:
                return str(loc[0] or ""), int(loc[1] or 0), report.nodeid
        except Exception:  # noqa: S110
            pass
        try:
            path = getattr(report, "fspath", "") or ""
            return str(path), 0, report.nodeid
        except Exception:
            return "", 0, getattr(report, "nodeid", "")

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        nodeid = report.nodeid
        if nodeid not in self.results:
            self.test_order.append(nodeid)
            path, lineno, _ = self._safe_location(report)
            self.results[nodeid] = {
                "nodeid": nodeid,
                "path": path,
                "lineno": lineno,
                "outcome": None,
                "duration": 0.0,
                "title": nodeid,
                "components": [],
                "details": {},
                "execution_log": [],
            }

        record = self.results[nodeid]
        record["duration"] += report.duration

        for key, value in getattr(report, "user_properties", []):
            if key == "title" and value:
                record["title"] = str(value)
            elif key == "components" and value:
                record["components"] = [str(v) for v in value]
            elif key == "execution_log":
                record["execution_log"] = value

        if getattr(report, "_soft_assert_only", False):
            record["soft_assert_only"] = True

        effective_outcome = utils.get_effective_outcome(report)

        if report.when == "call":
            record["outcome"] = effective_outcome
        elif report.when in {"setup", "teardown"} and getattr(report, "outcome", None) in ("failed", "error"):
            record["outcome"] = "error"

        if details := utils.extract_report_details(report):
            candidate = {**details, "_outcome": effective_outcome, "_phase": report.when}
            if utils.is_better_details(record.get("details"), candidate, report):
                record["details"] = candidate

    def pytest_collectreport(self, report: pytest.TestReport) -> None:
        if report.failed:
            try:
                path = str(getattr(report, "fspath", "") or getattr(report, "nodeid", ""))
            except Exception:
                path = str(getattr(report, "nodeid", ""))
            self.collection_errors.append(
                {
                    "nodeid": getattr(report, "nodeid", "<collection>"),
                    "path": path,
                    "outcome": "error",
                    "duration": report.duration,
                    "details": {**utils.extract_report_details(report), "_outcome": "error", "_phase": "collect"},
                },
            )

    def pytest_sessionfinish(self, session: cfg.AnyType, exitstatus: int) -> None:  # noqa: ARG002
        results = self.collection_errors + [self.results[k] for k in self.test_order]

        for r in results:
            outcome = r.get("outcome") or "skipped"
            r["outcome"] = outcome
            self.totals[outcome] += 1

            attachments = []

            def _find_attachments(log_entries) -> None:  # noqa: ANN001
                for entry in log_entries:
                    if entry.get("type") == "attachment":
                        attachments.append(entry)  # noqa: B023
                    if entry.get("type") == "step":
                        _find_attachments(entry.get("children", []))

            _find_attachments(r.get("execution_log", []))
            r["attachments"] = attachments

        total = sum(self.totals.values())
        passed = self.totals.get("passed", 0)
        pass_rate = (passed / total * 100.0) if total else 0.0

        context = {
            "title": self.title,
            "theme": self.theme,
            "session_start": self.session_start,
            "session_finish": datetime.datetime.now(),
            "stats": {
                "total": total,
                "duration_total": sum(r.get("duration", 0.0) for r in results),
                "pass_rate": f"{pass_rate:.1f}%",
                **self.totals,
            },
            "results": results,
            "css_content": _DEF_CSS,
            "js_content": _DEF_JS,
        }

        try:
            template_dir = Path(__file__).parent / "_assets"
            env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(template_dir),
                autoescape=jinja2.select_autoescape(["html", "xml"]),
            )
            env.globals["fmt_datetime"] = utils.fmt_datetime
            env.globals["fmt_seconds"] = utils.fmt_seconds
            env.globals["parse_params_from_nodeid"] = utils.parse_params_from_nodeid
            env.globals["decode_unicode_escapes"] = utils.decode_unicode_escapes

            template = env.get_template("report.html.jinja2")
            html_content = template.render(context)

            report_path = Path(self.path).resolve()
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(html_content, encoding="utf-8")
        except Exception as e:
            print(f"\nERROR: Could not generate HTML report: {e}")  # noqa: T201

    def pytest_terminal_summary(self, terminalreporter: cfg.AnyType, exitstatus: int, config: pytest.Config) -> None:  # noqa: ARG002
        report_uri = Path(self.path).resolve().as_uri()
        terminalreporter.write_sep("=", f"HTML report: {report_uri}", blue=True)
