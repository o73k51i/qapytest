"""Module for testing internal utility functions in QaPyTest."""

import datetime
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from qapytest import _config as cfg
from qapytest import _internal as utils


class TestInternalUtilities:
    """Tests for internal utility functions."""

    def test_mime_detection_from_bytes(self):
        """Test MIME type detection from byte data."""
        jpeg_header = b"\xff\xd8\xff"
        assert utils.detect_mime_from_bytes(jpeg_header) == "image/jpeg"

        png_header = b"\x89PNG\r\n\x1a\n"
        assert utils.detect_mime_from_bytes(png_header) == "image/png"

        gif_header = b"GIF87a"
        assert utils.detect_mime_from_bytes(gif_header) == "image/gif"

        unknown_data = b"unknown"
        assert utils.detect_mime_from_bytes(unknown_data) == cfg.DEFAULT_IMAGE_MIME

    def test_mime_from_suffix(self):
        """Test MIME type detection from file extension."""
        assert utils.mime_from_suffix(Path("test.png")) == "image/png"
        assert utils.mime_from_suffix(Path("test.jpg")) == "image/jpeg"
        assert utils.mime_from_suffix(Path("test.jpeg")) == "image/jpeg"
        assert utils.mime_from_suffix(Path("test.gif")) == "image/gif"
        assert utils.mime_from_suffix(Path("test.ico")) == "image/x-icon"
        assert utils.mime_from_suffix(Path("test.unknown")) == cfg.DEFAULT_IMAGE_MIME

    def test_has_failures_in_log(self):
        """Test failure detection in log entries."""
        log_no_failures = [
            {"type": "assert", "passed": True},
            {"type": "step", "children": [{"type": "assert", "passed": True}]},
        ]
        assert utils.has_failures_in_log(log_no_failures) is False

        log_with_failures = [
            {"type": "assert", "passed": False},
        ]
        assert utils.has_failures_in_log(log_with_failures) is True

        log_nested_failures = [
            {"type": "step", "children": [{"type": "assert", "passed": False}]},
        ]
        assert utils.has_failures_in_log(log_nested_failures) is True

    def test_maybe_truncate_text(self):
        """Test text truncation functionality."""
        original_limit = cfg.ATTACH_LIMIT_BYTES
        cfg.ATTACH_LIMIT_BYTES = 10

        try:
            short_text = "short"
            result, truncated = utils.maybe_truncate_text(short_text)
            assert result == short_text
            assert truncated is False

            long_text = "x" * 100
            result, truncated = utils.maybe_truncate_text(long_text)
            assert truncated is True
            assert "[TRUNCATED]" in result
            assert len(result.encode()) <= len(long_text.encode())
        finally:
            cfg.ATTACH_LIMIT_BYTES = original_limit

    def test_maybe_truncate_bytes(self):
        """Test bytes truncation functionality."""
        original_limit = cfg.ATTACH_LIMIT_BYTES
        cfg.ATTACH_LIMIT_BYTES = 10

        try:
            short_bytes = b"short"
            result, truncated = utils.maybe_truncate_bytes(short_bytes)
            assert result == short_bytes
            assert truncated is False

            long_bytes = b"x" * 100
            result, truncated = utils.maybe_truncate_bytes(long_bytes)
            assert truncated is True
            assert len(result) == 10
        finally:
            cfg.ATTACH_LIMIT_BYTES = original_limit


class TestEnvironmentUtilities:
    """Tests for environment and asset loading utilities."""

    def test_load_env_file_existing_file(self):
        """Test loading existing .env file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as tmp_file:
            tmp_file.write("TEST_VAR=test_value\n")
            tmp_file.write("ANOTHER_VAR=another_value\n")
            tmp_file_path = tmp_file.name

        try:
            os.environ.pop("TEST_VAR", None)
            os.environ.pop("ANOTHER_VAR", None)

            utils.load_env_file(Path(tmp_file_path))

            assert os.environ.get("TEST_VAR") == "test_value"
            assert os.environ.get("ANOTHER_VAR") == "another_value"
        finally:
            Path(tmp_file_path).unlink()
            os.environ.pop("TEST_VAR", None)
            os.environ.pop("ANOTHER_VAR", None)

    def test_load_env_file_nonexistent_file(self):
        """Test loading non-existent .env file."""
        utils.load_env_file(Path("nonexistent.env"))

    def test_load_env_file_with_override(self):
        """Test loading .env file with override option."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as tmp_file:
            tmp_file.write("OVERRIDE_VAR=new_value\n")
            tmp_file_path = tmp_file.name

        try:
            os.environ["OVERRIDE_VAR"] = "old_value"

            utils.load_env_file(Path(tmp_file_path), override=False)
            assert os.environ.get("OVERRIDE_VAR") == "old_value"

            utils.load_env_file(Path(tmp_file_path), override=True)
            assert os.environ.get("OVERRIDE_VAR") == "new_value"
        finally:
            Path(tmp_file_path).unlink()
            os.environ.pop("OVERRIDE_VAR", None)

    def test_load_asset(self):
        """Test loading asset files."""
        css_content = utils.load_asset("styles.css")
        assert isinstance(css_content, str)
        assert len(css_content) > 0

        js_content = utils.load_asset("scripts.js")
        assert isinstance(js_content, str)
        assert len(js_content) > 0

        html_content = utils.load_asset("report.html.jinja2")
        assert isinstance(html_content, str)
        assert len(html_content) > 0


class TestLogUtilities:
    """Tests for logging-related utility functions."""

    def test_add_log_entry(self):
        """Test adding log entries to current container."""
        mock_stack = [[]]
        with patch("qapytest._config.CURRENT_LOG_CONTAINER_STACK") as mock_context_var:
            mock_context_var.get.return_value = mock_stack

            entry = {"type": "assert", "passed": True, "label": "Test assertion"}
            utils.add_log_entry(entry)

            assert len(mock_stack[0]) == 1
            assert mock_stack[0][0] == entry
            mock_context_var.get.assert_called_once()

    def test_add_log_entry_no_stack(self):
        """Test adding log entry when no stack is available."""
        with patch("qapytest._config.CURRENT_LOG_CONTAINER_STACK") as mock_context_var:
            mock_context_var.get.return_value = None
            utils.add_log_entry({"type": "assert", "passed": True})

    def test_generate_terminal_summary(self):
        """Test generating terminal summary from log entries."""
        log_with_failures = [
            {"type": "assert", "passed": False, "label": "First assertion", "details": "Expected True"},
            {
                "type": "step",
                "children": [
                    {"type": "assert", "passed": False, "label": "Nested assertion", "details": "Expected 5, got 3"},
                ],
            },
            {"type": "assert", "passed": True, "label": "Passing assertion"},
        ]

        summary = utils.generate_terminal_summary(log_with_failures)

        assert len(summary) == 2
        assert "First assertion [Expected True]" in summary[0]
        assert "Nested assertion [Expected 5, got 3]" in summary[1]

    def test_generate_terminal_summary_no_failures(self):
        """Test generating terminal summary with no failures."""
        log_no_failures = [
            {"type": "assert", "passed": True, "label": "Passing assertion"},
            {
                "type": "step",
                "children": [
                    {"type": "assert", "passed": True, "label": "Another passing assertion"},
                ],
            },
        ]

        summary = utils.generate_terminal_summary(log_no_failures)
        assert len(summary) == 0

    def test_generate_terminal_summary_without_details(self):
        """Test generating terminal summary with failures without details."""
        log_with_failures_no_details = [
            {"type": "assert", "passed": False, "label": "Failed assertion without details"},
            {"type": "assert", "passed": False, "label": "Another failure", "details": "With details"},
        ]

        summary = utils.generate_terminal_summary(log_with_failures_no_details)

        assert len(summary) == 2
        assert summary[0] == "\t✖︎ Failed assertion without details"
        assert summary[1] == "\t✖︎ Another failure [With details]"


class TestTextUtilities:
    """Tests for text processing utilities."""

    def test_strip_ansi_codes(self):
        """Test ANSI code stripping."""
        text_with_ansi = "\x1b[31mRed text\x1b[0m and \x1b[1mbold text\x1b[0m"
        clean_text = utils._strip_ansi_codes(text_with_ansi)  # noqa: SLF001
        assert clean_text == "Red text and bold text"

        normal_text = "Normal text without codes"
        assert utils._strip_ansi_codes(normal_text) == normal_text  # noqa: SLF001

        assert utils._strip_ansi_codes("") == ""  # noqa: SLF001

    def test_fmt_datetime(self):
        """Test datetime formatting."""
        dt = datetime.datetime(2023, 12, 25, 15, 30, 45, 123456)
        formatted = utils.fmt_datetime(dt)
        assert formatted == "2023-12-25 15:30:45"

    def test_fmt_seconds(self):
        """Test seconds formatting."""
        assert utils.fmt_seconds(123.456) == "123.46"

        assert utils.fmt_seconds(123.00) == "123"

        assert utils.fmt_seconds(123.10) == "123.1"

        assert utils.fmt_seconds(0.0) == "0"

    def test_parse_params_from_nodeid(self):
        """Test parsing parameters from pytest nodeid."""
        nodeid_with_params = "test_file.py::test_function[param1-param2]"
        params = utils.parse_params_from_nodeid(nodeid_with_params)
        assert params == "param1-param2"

        nodeid_without_params = "test_file.py::test_function"
        params = utils.parse_params_from_nodeid(nodeid_without_params)
        assert params == ""

        nodeid_complex = "test_file.py::TestClass::test_method[complex-param-with-dashes]"
        params = utils.parse_params_from_nodeid(nodeid_complex)
        assert params == "complex-param-with-dashes"

    def test_parse_params_from_nodeid_with_unicode_escapes(self):
        """Test parsing parameters with Unicode escape sequences from pytest nodeid."""
        nodeid_cyrillic = "test_file.py::test_function[\\u041f\\u0435\\u0440\\u0448\\u0438\\u0439]"
        params = utils.parse_params_from_nodeid(nodeid_cyrillic)
        assert params == "Перший"

        nodeid_multiple = (
            "test_file.py::test_function[\\u041f\\u0435\\u0440\\"
            "u0448\\u0438\\u0439-\\u0414\\u0440\\u0443\\u0433\\u0438\\u0439]"
        )
        params = utils.parse_params_from_nodeid(nodeid_multiple)
        assert params == "Перший-Другий"

        nodeid_mixed = "test_file.py::test_function[test-\\u0422\\u0440\\u0435\\u0442\\u0456\\u0439-param]"
        params = utils.parse_params_from_nodeid(nodeid_mixed)
        assert params == "test-Третій-param"

        nodeid_malformed = "test_file.py::test_function[\\u041Z-invalid]"
        params = utils.parse_params_from_nodeid(nodeid_malformed)
        assert params == "\\u041Z-invalid"  # Should return original string on decode error

    def test_decode_unicode_escapes(self):
        """Test decoding Unicode escape sequences in text."""
        text_with_escapes = "\\u041f\\u0435\\u0440\\u0448\\u0438\\u0439"
        decoded = utils.decode_unicode_escapes(text_with_escapes)
        assert decoded == "Перший"

        regular_text = "Regular text without escapes"
        decoded = utils.decode_unicode_escapes(regular_text)
        assert decoded == "Regular text without escapes"

        cyrillic_text = "Перевірка відображення параметризації"
        decoded = utils.decode_unicode_escapes(cyrillic_text)
        assert decoded == "Перевірка відображення параметризації"

        mixed_text = "Test \\u041f\\u0435\\u0440\\u0448\\u0438\\u0439 and regular text"
        decoded = utils.decode_unicode_escapes(mixed_text)
        assert decoded == "Test Перший and regular text"

        empty_text = ""
        decoded = utils.decode_unicode_escapes(empty_text)
        assert decoded == ""

        malformed_text = "\\u041Z invalid escape"
        decoded = utils.decode_unicode_escapes(malformed_text)
        assert decoded == "\\u041Z invalid escape"  # Should return original on error

        emoji_text = "\\u2764\\ufe0f"  # Heart emoji ❤️
        decoded = utils.decode_unicode_escapes(emoji_text)
        assert decoded == "❤️"

        no_escapes_text = "This text has no unicode escapes"
        decoded = utils.decode_unicode_escapes(no_escapes_text)
        assert decoded == "This text has no unicode escapes"

    def test_unicode_functions_integration(self):
        """Test integration of Unicode functions with realistic pytest nodeid examples."""
        realistic_nodeid = "temp.py::test_parametrized[\\u041f\\u0435\\u0440\\u0448\\u0438\\u0439]"

        params = utils.parse_params_from_nodeid(realistic_nodeid)
        assert params == "Перший"

        decoded_nodeid = utils.decode_unicode_escapes(realistic_nodeid)
        assert decoded_nodeid == "temp.py::test_parametrized[Перший]"

        title_with_escapes = (
            "\\u041f\\u0435\\u0440\\u0435\\u0432\\u0456\\u0440\\u043a\\u0430 "
            "\\u0432\\u0456\\u0434\\u043e\\u0431\\u0440\\u0430\\u0436\\u0435\\u043d\\u043d\\u044f "
            "\\u043f\\u0430\\u0440\\u0430\\u043c\\u0435\\u0442\\u0440\\u0438\\u0437\\u0430\\u0446\\u0456\\u0457"
        )
        decoded_title = utils.decode_unicode_escapes(title_with_escapes)
        assert decoded_title == "Перевірка відображення параметризації"

        multi_param_nodeid = (
            "test.py::test_func[\\u041f\\u0435\\u0440\\u0448\\u0438\\u0439-"
            "\\u0414\\u0440\\u0443\\u0433\\u0438\\u0439-\\u0422\\u0440\\u0435\\u0442\\u0456\\u0439]"
        )
        multi_params = utils.parse_params_from_nodeid(multi_param_nodeid)
        assert multi_params == "Перший-Другий-Третій"


class TestReportUtilities:
    """Tests for report-related utility functions."""

    def test_get_effective_outcome_basic(self):
        """Test getting effective outcome for basic cases."""
        report = Mock()
        report.outcome = "passed"
        report._exc_class_name = None  # noqa: SLF001
        report.wasxfail = None
        assert utils.get_effective_outcome(report) == "passed"

        report.outcome = "failed"
        report._exc_class_name = "AssertionError"  # noqa: SLF001
        assert utils.get_effective_outcome(report) == "failed"

        report.outcome = "failed"
        report._exc_class_name = "ValueError"  # noqa: SLF001
        assert utils.get_effective_outcome(report) == "error"

        report.outcome = "skipped"
        report._exc_class_name = None  # noqa: SLF001
        assert utils.get_effective_outcome(report) == "skipped"

    def test_get_effective_outcome_xfail(self):
        """Test getting effective outcome for xfail cases."""
        report = Mock()

        report.outcome = "skipped"
        report._exc_class_name = None  # noqa: SLF001
        report.wasxfail = "Expected to fail"
        assert utils.get_effective_outcome(report) == "xfailed"

        report.outcome = "passed"
        report.wasxfail = "Expected to fail"
        assert utils.get_effective_outcome(report) == "xpassed"

    def test_assert_message_from_longrepr(self):
        """Test extracting assertion message from longrepr."""
        longrepr = Mock()
        longrepr.reprcrash = Mock()
        longrepr.reprcrash.message = "AssertionError: Expected True, got False"

        message = utils._assert_message_from_longrepr(longrepr)  # noqa: SLF001
        assert message == "Expected True, got False"

        longrepr_str = "One or more assertions failed.\nDetails..."
        message = utils._assert_message_from_longrepr(longrepr_str)  # noqa: SLF001
        assert message == "One or more assertions failed"

        message = utils._assert_message_from_longrepr(None)  # noqa: SLF001
        assert message == ""

    def test_extract_report_details(self):
        """Test extracting report details."""
        report = Mock()
        report.outcome = "failed"
        report._exc_class_name = "AssertionError"  # noqa: SLF001
        report.wasxfail = None
        report.longrepr = "AssertionError: Test failed"
        report.sections = [
            ("Captured stdout", "Some output"),
            ("Captured log call", "Log message"),
        ]

        details = utils.extract_report_details(report)

        assert "headline" in details
        assert "longrepr" in details
        assert "captured_stdout" in details
        assert "captured_logs" in details
        assert "Some output" in details["captured_stdout"]
        assert "Log message" in details["captured_logs"]

    def test_is_better_details(self):
        """Test comparing detail quality."""
        report = Mock()
        report.when = "call"

        new_details = {"headline": "Test failed"}
        assert utils.is_better_details(None, new_details, report) is True

        assert utils.is_better_details(None, {}, report) is False

        old_details = {"_outcome": "passed", "_phase": "call"}
        new_details = {"_outcome": "failed", "_phase": "call"}

        with patch.object(utils, "get_effective_outcome", return_value="failed"):
            assert utils.is_better_details(old_details, new_details, report) is True
