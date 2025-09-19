"""Module for attaching various data types (text, JSON, images) to reports."""

import base64
import json
from pathlib import Path

from qapytest import _config as cfg
from qapytest import _internal as utils


def attach(data: cfg.AnyType, label: str, mime: str | None = None) -> None:
    """Attaches various data (text, JSON, images) as an attachment to the log.

    This function enriches reports and logs by attaching contextual information.
    It automatically determines the data type and formats it for convenient viewing
    in the final report:
    - `dict` and `list` are formatted as JSON.
    - `bytes` and image file paths (`.png`, `.jpg`, etc.) are embedded
      as images (base64 data URI).
    - Other data types are converted to text.

    The function also automatically truncates overly large data to avoid
    log overflow, adding a note "(truncated)" to the label.
    Works only within an active log container (e.g., inside a `step` block).

    Args:
        data (Any): The data to attach. Can be of any type, but `dict`, `list`,
                    `bytes`, `str`, and `Path` are specifically handled.
        label (str): The name of the attachment that will be displayed in the report.
        mime (str | None, optional): MIME type for `bytes` data if it cannot
                    be determined automatically (e.g., "image/jpeg").

    Returns:
        None

    ---
    ### Example usage:

    ```python
    with step("Checking API and UI"):
        # 1. Attach a dictionary as formatted JSON
        api_response = {"user_id": 123, "status": "active", "roles": ["admin", "editor"]}
        attach(api_response, "API server response")

        # 2. Attach an SQL query as plain text
        sql_query = "SELECT * FROM users WHERE status = 'active';"
        attach(sql_query, "SQL query to the database")

        # 3. Attach an image from a file on disk
        attach("path/to/screenshot_of_page.png", "Page screenshot")

        # 4. Attach an image from bytes (e.g., taken by Playwright)
        screenshot_bytes = page.locator("#user-avatar").screenshot()
        attach(screenshot_bytes, "User avatar screenshot")
    ```
    """
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
