"""Module containing tests for the soft_assert function in QaPyTest."""

from unittest.mock import patch

import qapytest
from qapytest import _config as cfg


class TestSoftAssertFunction:
    """Tests for the soft_assert function."""

    def test_soft_assert_pass(self):
        """Test soft_assert with passing condition."""
        log_container = []
        stack = [log_container]

        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = stack

            result = qapytest.soft_assert(True, "Should pass")

            assert result is True
            assert len(log_container) == 1

            assert_entry = log_container[0]
            assert assert_entry["type"] == "assert"
            assert assert_entry["label"] == "Should pass"
            assert assert_entry["passed"] is True
            assert "details" not in assert_entry

    def test_soft_assert_fail_without_details(self):
        """Test soft_assert with failing condition and no custom details."""
        log_container = []
        stack = [log_container]

        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = stack

            result = qapytest.soft_assert(False, "Should fail")

            assert result is False
            assert len(log_container) == 1

            assert_entry = log_container[0]
            assert assert_entry["type"] == "assert"
            assert assert_entry["label"] == "Should fail"
            assert assert_entry["passed"] is False
            assert "details" not in assert_entry

    def test_soft_assert_fail_with_custom_details(self):
        """Test soft_assert with failing condition and custom details."""
        log_container = []
        stack = [log_container]

        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = stack

            result = qapytest.soft_assert(False, "Should fail", "Custom error message")

            assert result is False
            assert len(log_container) == 1

            assert_entry = log_container[0]
            assert assert_entry["details"] == "Custom error message"

    def test_soft_assert_various_conditions(self):
        """Test soft_assert with various condition types."""
        log_container = []
        stack = [log_container]

        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = stack

            assert qapytest.soft_assert(1, "Number 1") is True  # type: ignore
            assert qapytest.soft_assert(0, "Number 0") is False  # type: ignore
            assert qapytest.soft_assert("text", "Non-empty string") is True  # type: ignore
            assert qapytest.soft_assert("", "Empty string") is False  # type: ignore
            assert qapytest.soft_assert([1, 2], "Non-empty list") is True  # type: ignore
            assert qapytest.soft_assert([], "Empty list") is False  # type: ignore
            assert qapytest.soft_assert(None, "None value") is False  # type: ignore

    def test_soft_assert_without_context(self):
        """Test soft_assert behavior when no context is available."""
        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = None

            result = qapytest.soft_assert(True, "No context")
            assert result is True

            result = qapytest.soft_assert(False, "No context fail")
            assert result is False
