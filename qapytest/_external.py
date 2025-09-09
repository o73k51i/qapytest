"""Module providing external API for test logging and reporting."""

import base64
import json
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from qapytest import _config as cfg
from qapytest import _internal as utils


@contextmanager
def step(message: str) -> Generator[None, None, None]:
    stack = cfg.CURRENT_LOG_CONTAINER_STACK.get()
    if not stack:
        yield
        return

    step_node = {
        "type": "step",
        "message": message,
        "passed": True,
        "children": [],
    }
    utils.add_log_entry(step_node)
    stack.append(step_node["children"])
    try:
        yield
    finally:
        stack.pop()
        step_node["passed"] = not utils.has_failures_in_log(step_node.get("children", []))


def soft_assert(condition: bool, label: str, details: str | None = None) -> bool:
    passed = bool(condition)
    log_entry: dict[str, cfg.AnyType] = {"type": "assert", "label": label, "passed": passed}

    if not passed:
        log_entry["details"] = details if details else "Condition evaluated to False"

    utils.add_log_entry(log_entry)
    return passed


def attach(data: cfg.AnyType, label: str, mime: str | None = None) -> None:
    if cfg.CURRENT_LOG_CONTAINER_STACK.get() is None:
        return

    content_type = "text"
    formatted_data = ""
    extra_note = ""

    try:
        if isinstance(data, dict | list):
            content_type = "json"
            try:
                text = json.dumps(data, indent=2, ensure_ascii=False)
            except TypeError:
                text = repr(data)
                content_type = "text"
            text, truncated = utils.maybe_truncate_text(text)
            if truncated:
                extra_note = " (truncated)"
            formatted_data = text

        elif isinstance(data, bytes):
            content_type = "image"
            b, truncated = utils.maybe_truncate_bytes(data)
            this_mime = mime or utils.detect_mime_from_bytes(b)
            b64 = base64.b64encode(b).decode("utf-8")
            formatted_data = f"data:{this_mime};base64,{b64}"
            if truncated:
                extra_note = " (truncated)"

        elif isinstance(data, str | Path):
            p = None
            if isinstance(data, Path):
                p = data
            else:
                try:
                    p = Path(data)
                except Exception:
                    p = None

            if (
                p
                and p.suffix.lower() in [".png", ".jpg", ".jpeg", ".gif", ".ico", ".bmp", ".webp", ".svg"]
                and p.is_file()
            ):
                content_type = "image"
                with p.open("rb") as f:
                    raw = f.read()
                raw, truncated = utils.maybe_truncate_bytes(raw)
                this_mime = mime or utils.mime_from_suffix(p)
                b64 = base64.b64encode(raw).decode("utf-8")
                formatted_data = f"data:{this_mime};base64,{b64}"
                if truncated:
                    extra_note = " (truncated from file)"
            else:
                content_type = "text"
                text = str(data)
                text, truncated = utils.maybe_truncate_text(text)
                if truncated:
                    extra_note = " (truncated)"
                formatted_data = text

        else:
            content_type = "text"
            text = repr(data)
            text, truncated = utils.maybe_truncate_text(text)
            if truncated:
                extra_note = " (truncated)"
            formatted_data = text

    except Exception as e:
        content_type = "text"
        formatted_data = f"ERROR while attaching data: {e}"

    label = f"{label}{extra_note}"

    utils.add_log_entry(
        {
            "type": "attachment",
            "label": label,
            "data": formatted_data,
            "content_type": content_type,
        },
    )
