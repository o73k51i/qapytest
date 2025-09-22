"""Module with internal utility functions."""

from __future__ import annotations

import datetime
import re
from pathlib import Path
from typing import TypedDict

import pytest
from dotenv import load_dotenv

from qapytest import _config as cfg


def load_env_file(env_file_path: Path, *, override: bool = False) -> None:
    if env_file_path.is_file():
        load_dotenv(dotenv_path=env_file_path, override=override)


def load_asset(filename: str) -> str:
    asset_path = Path(__file__).parent / "_assets" / filename
    return asset_path.read_text(encoding="utf-8")


def add_log_entry(entry: dict) -> None:
    stack = cfg.CURRENT_LOG_CONTAINER_STACK.get()
    if stack:
        current_container = stack[-1]
        current_container.append(entry)


def detect_mime_from_bytes(data: bytes) -> str:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if data[:4] == b"\x00\x00\x01\x00":
        return "image/x-icon"
    return cfg.DEFAULT_IMAGE_MIME


def mime_from_suffix(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".ico": "image/x-icon",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }.get(ext, cfg.DEFAULT_IMAGE_MIME)


def maybe_truncate_text(s: str) -> tuple[str, bool]:
    if cfg.ATTACH_LIMIT_BYTES is None:
        return s, False
    b = s.encode("utf-8", errors="replace")
    if len(b) <= cfg.ATTACH_LIMIT_BYTES:
        return s, False
    truncated = b[: cfg.ATTACH_LIMIT_BYTES].decode("utf-8", errors="ignore")
    return truncated + "\n\n[TRUNCATED]", True


def maybe_truncate_bytes(b: bytes) -> tuple[bytes, bool]:
    if cfg.ATTACH_LIMIT_BYTES is None or len(b) <= cfg.ATTACH_LIMIT_BYTES:
        return b, False
    return b[: cfg.ATTACH_LIMIT_BYTES], True


def has_failures_in_log(log_list: list) -> bool:
    for entry in log_list:
        if entry.get("type") == "assert" and not entry.get("passed", False):
            return True
        if entry.get("type") == "step" and has_failures_in_log(entry.get("children", [])):
            return True
    return False


def generate_terminal_summary(log_list: list) -> list[str]:
    error_lines: list[str] = []

    def find_failures_recursive(log_entries: list) -> None:
        for entry in log_entries:
            if entry.get("type") == "assert" and not entry.get("passed", False):
                label = entry.get("label", "")
                details = entry.get("details")
                if details:
                    error_lines.append(f"\t✖︎ {label} [{details}]")
                else:
                    error_lines.append(f"\t✖︎ {label}")
            elif entry.get("type") == "step":
                find_failures_recursive(entry.get("children", []))

    find_failures_recursive(log_list)
    return error_lines


def _strip_ansi_codes(text: str) -> str:
    ansi_escape = re.compile(r"\x1b(?:\[[0-9;]*[a-zA-Z]|\([0-9;]*[a-zA-Z]|\].*?\x07|\[[0-9]+[mK])")
    return ansi_escape.sub("", text)


def get_effective_outcome(report: pytest.TestReport) -> str:
    outcome = getattr(report, "outcome", "unknown")
    exc_name = getattr(report, "_exc_class_name", None)
    if outcome == "failed" and exc_name and exc_name != "AssertionError":
        outcome = "error"

    if getattr(report, "wasxfail", None):
        if getattr(report, "outcome", None) == "skipped":
            return "xfailed"
        if getattr(report, "outcome", None) == "passed":
            return "xpassed"

    return outcome


def _assert_message_from_longrepr(longrepr: cfg.AnyType) -> str:
    if not longrepr:
        return ""
    try:
        text = str(longrepr)
        text = _strip_ansi_codes(text)  # Strip ANSI codes
        if "One or more assertions failed." in text:
            return "One or more assertions failed"
    except Exception:  # noqa: S110
        pass

    try:
        if hasattr(longrepr, "reprcrash") and getattr(
            longrepr.reprcrash,
            "message",
            None,
        ):
            msg = longrepr.reprcrash.message or ""
            msg = _strip_ansi_codes(msg)  # Strip ANSI codes
            if "AssertionError:" in msg:
                return msg.split("AssertionError:", 1)[1].strip() or "assertion failed"
            return msg.strip()
    except Exception:  # noqa: S110
        pass

    try:
        text = str(longrepr)
        text = _strip_ansi_codes(text)  # Strip ANSI codes
        for line in text.splitlines():
            if "AssertionError:" in line:
                return line.split("AssertionError:", 1)[1].strip() or ""
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if lines:
            tail = lines[-1]
            if tail.startswith("E ") and ":" in tail:
                tail = tail.split(":", 1)[1].strip()
            return tail
        return ""
    except Exception:
        return ""


class DetailsDict(TypedDict, total=False):
    headline: str
    longrepr: str
    captured_stdout: str
    captured_logs: str
    _outcome: str
    _phase: str


def extract_report_details(report: pytest.TestReport) -> dict[str, str]:
    details: DetailsDict = {
        "headline": "",
        "longrepr": "",
        "captured_stdout": "",
        "captured_logs": "",
    }
    try:
        outcome = get_effective_outcome(report)
        longrepr_obj = getattr(report, "longrepr", None)
        longrepr_text = ""
        try:
            longrepr_text = str(longrepr_obj or "")
            longrepr_text = _strip_ansi_codes(longrepr_text)  # Strip ANSI codes
            if hasattr(longrepr_obj, "reprtraceback"):
                longrepr_text = str(longrepr_obj)
                longrepr_text = _strip_ansi_codes(longrepr_text)  # Strip ANSI codes
        except Exception:
            longrepr_text = str(longrepr_obj or "")
            longrepr_text = _strip_ansi_codes(longrepr_text)  # Strip ANSI codes

        result_msg, why_text = "", ""
        if outcome in ("failed", "error"):
            result_msg, why_text = (_assert_message_from_longrepr(longrepr_obj) or "test failed", longrepr_text)
        elif outcome == "xfailed":
            result_msg, why_text = (getattr(report, "wasxfail", "Expected to fail"), longrepr_text)
        elif outcome == "skipped":
            if isinstance(report.longrepr, tuple) and len(report.longrepr) == 3:
                result_msg = str(report.longrepr[2])
                result_msg = _strip_ansi_codes(result_msg)  # Strip ANSI codes
                if result_msg.lower().startswith("skipped: "):
                    result_msg = result_msg[len("skipped: ") :]
            else:
                result_msg = longrepr_text.replace("Skipped: ", "")
                result_msg = _strip_ansi_codes(result_msg)  # Strip ANSI codes
            result_msg = result_msg or "skipped"
        elif outcome == "xpassed":
            result_msg, why_text = (
                "All assertions passed",
                "This test was marked as xfail, but unexpectedly passed",
            )
        elif outcome == "passed":
            result_msg = "All assertions passed"
        else:
            result_msg = outcome

        captured_stdout, captured_logs = [], []
        for name, content in getattr(report, "sections", []):
            name_lower = name.lower()
            clean_content = _strip_ansi_codes(content.strip())

            if name_lower.startswith(("caplog", "captured log")):
                captured_logs.append(clean_content)
            elif name_lower.startswith("captured std"):
                captured_stdout.append(f"--- {name} ---\n{clean_content}")

        details.update(
            {
                "captured_stdout": "\n\n".join(captured_stdout),
                "captured_logs": "\n\n".join(captured_logs),
                "headline": str(result_msg),
                "longrepr": str(why_text),
            },
        )
    except Exception:  # noqa: S110
        pass
    return details  # type: ignore[return-value]


def is_better_details(
    old: dict[str, cfg.AnyType] | None,
    new: dict[str, cfg.AnyType],
    report: pytest.TestReport,
) -> bool:
    if not new:
        return False
    if not old:
        return True
    new_rank = cfg.OUTCOME_RANK.get(get_effective_outcome(report), 0)
    new_phase_rank = cfg.PHASE_RANK.get(report.when, 0)
    old_rank = cfg.OUTCOME_RANK.get(old.get("_outcome", "unknown"), 0)
    old_phase_rank = cfg.PHASE_RANK.get(old.get("_phase"), 0)  # type: ignore
    if new_rank != old_rank:
        return new_rank > old_rank
    return new_phase_rank > old_phase_rank


def fmt_datetime(dt: datetime.datetime) -> str:
    return dt.isoformat(sep=" ", timespec="seconds")


def fmt_seconds(s: float) -> str:
    return f"{float(s or 0.0):.2f}".rstrip("0").rstrip(".")


def parse_params_from_nodeid(nodeid: str) -> str:
    try:
        start = nodeid.rfind("[")
        end = nodeid.rfind("]")
        if start != -1 and end != -1 and end > start:
            param_str = nodeid[start + 1 : end]
            try:
                import codecs

                return codecs.decode(param_str, "unicode_escape")
            except Exception:
                return param_str
    except Exception:  # noqa: S110
        pass
    return ""


def decode_unicode_escapes(text: str) -> str:
    """Decode Unicode escape sequences in text to readable characters."""
    try:
        if "\\u" in text:
            import codecs

            return codecs.decode(text, "unicode_escape")
        return text
    except Exception:
        return text
