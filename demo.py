"""Module containing demo test cases for various scenarios."""

import logging
from time import sleep

import pytest

from qapytest import attach, soft_assert, step


@pytest.mark.component("demo")
class TestDemo:
    """Demo test cases for various scenarios."""

    @pytest.mark.title("Default pass")
    def test_default_pass(self) -> None:
        """Default passing test case."""
        assert True  # noqa: S101

    @pytest.mark.title("Default fail")
    def test_default_fail(self) -> None:
        """Default failing test case."""
        assert False, "This test is designed to fail"  # noqa: B011, PT015, S101

    @pytest.mark.title("Default skip")
    @pytest.mark.skip(reason="Skipping this test for demonstration purposes")
    def test_default_skip(self) -> None:
        """Default skipped test case."""
        assert True  # noqa: S101

    @pytest.mark.title("Default xfail")
    @pytest.mark.xfail(reason="This test is expected to fail")
    def test_default_xfail(self) -> None:
        """Default expected to fail test case."""
        assert False, "This test is designed to fail"  # noqa: B011, PT015, S101

    @pytest.mark.title("Default xpass")
    @pytest.mark.xfail(reason="This test is expected to fail but will pass")
    def test_default_xpass(self) -> None:
        """Default expected to fail but will pass test case."""
        assert True  # noqa: S101

    @pytest.mark.title("Default error")
    def test_default_error(self) -> None:
        """Default error test case."""
        raise ValueError("This is an intentional error for demonstration purposes")

    @pytest.mark.title("Pass Scenario")
    @pytest.mark.component("one", "soft_assert")
    def test_pass(self) -> None:
        """Passing test case."""
        with step("Step 1: Passing step"):
            soft_assert(True, "This assertion should pass")
        with step("Step 2: Another passing step"):
            soft_assert(1 + 1 == 2, "Math works!", "1 + 1 == 2")

    @pytest.mark.title("Fail Scenario")
    @pytest.mark.component("two", "soft_assert")
    def test_fail(self) -> None:
        """Failing test case."""
        with step("Step 1: Failing step"):
            soft_assert(False, "This assertion should fail")
        with step("Step 2: Another failing step"):
            soft_assert(1 + 1 == 3, "Math is broken!", "1 + 1 != 3")

    @pytest.mark.title("Mixed Scenario")
    @pytest.mark.component("soft_assert")
    def test_mixed(self) -> None:
        """Test case with mixed pass and fail steps."""
        with step("Step 1: Passing step"):
            soft_assert(True, "This assertion should pass")
        with step("Step 2: Failing step"):
            soft_assert(False, "This assertion should fail")
        with step("Step 3: Another passing step"):
            soft_assert(2 * 2 == 4, "Math works again!", "2 * 2 == 4")
        with step("Step 4: Another failing step"):
            soft_assert(5 - 3 == 1, "Math is still broken!", "5 - 3 != 1")

    @pytest.mark.title("XFail Scenario")
    @pytest.mark.component("soft_assert")
    @pytest.mark.xfail(reason="This test is expected to fail")
    def test_xfail(self) -> None:
        """Test case expected to fail."""
        with step("Step 1: Failing step"):
            soft_assert(False, "This assertion should fail")
        with step("Step 2: Another failing step"):
            soft_assert(1 + 1 == 3, "Math is broken!", "1 + 1 != 3")

    @pytest.mark.title("Skip Scenario")
    @pytest.mark.component("soft_assert")
    @pytest.mark.skip(reason="Skipping this test for demonstration purposes")
    def test_skip(self) -> None:
        """Skipped test case."""
        with step("Step 1: This step will be skipped"):
            soft_assert(True, "This assertion should be skipped")
        with step("Step 2: Another skipped step"):
            soft_assert(1 + 1 == 2, "Math works!", "1 + 1 == 2")

    @pytest.mark.title("Error Scenario")
    @pytest.mark.component("soft_assert")
    def test_error(self) -> None:
        """Test case that raises an error."""
        raise RuntimeError("This is an intentional error for demonstration purposes")

    @pytest.mark.title("XPass Scenario")
    @pytest.mark.component("soft_assert")
    @pytest.mark.xfail(reason="This test is expected to fail but will pass")
    def test_xpass(self) -> None:
        """Test case expected to fail but will pass."""
        with step("Step 1: Passing step"):
            soft_assert(True, "This assertion should pass")
        with step("Step 2: Another passing step"):
            soft_assert(1 + 1 == 2, "Math works!", "1 + 1 == 2")

    @pytest.mark.title("Attachment Scenario")
    @pytest.mark.component("attach")
    def test_attachment(self) -> None:
        """Test case demonstrating various attachments."""
        with step("Attaching text file"):
            attach("This is a sample text", "string")
        with step("Attaching integer data"):
            attach(12345, "integer")
        with step("Attaching float data"):
            attach(123.45, "float")
        with step("Attaching boolean data"):
            attach(True, "boolean")
        with step("Attaching dictionary data"):
            attach({"key": "value", "number": 123}, "dictionary")
        with step("Attaching list data"):
            attach([1, 2, 3, 4, 5], "list")
        with step("Attaching large text data"):
            attach("A" * 10000, "large text")
        with step("Attaching image file"):
            attach(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01", "image.png")
        with step("Attaching JSON file"):
            attach('{"key": "value", "number": 123}', "data.json")
        with step("Attaching HTML file"):
            attach("<html><body><h1>Sample HTML</h1></body></html>", "page.html")
        with step("Attaching CSV file"):
            attach("col1,col2,col3\nval1,val2,val3", "data.csv")
        with step("Attaching XML file"):
            attach("<root><element>Value</element></root>", "data.xml")

    @pytest.mark.title("Logging Scenario")
    @pytest.mark.component("logging")
    def test_logging(self) -> None:
        """Test case demonstrating logging."""
        sleep(1)  # Simulate some processing time
        logging.info("This is an info message")
        logging.debug("This is a debug message")
        logging.warning("This is a warning message")
        logging.error("This is an error message")
