"""Module containing tests for the step context manager in QaPyTest."""

from unittest.mock import patch

import qapytest
from qapytest import _config as cfg


class TestStepFunction:
    """Tests for the step context manager."""

    def test_step_without_context(self):
        """Test step function when no log container stack is available."""
        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = None

            with qapytest.step("Test step"):
                assert True

    def test_step_with_context(self):
        """Test step function with proper context."""
        log_container = []
        stack = [log_container]

        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = stack

            with qapytest.step("Test step"):
                pass

            assert len(log_container) == 1
            step_entry = log_container[0]
            assert step_entry["type"] == "step"
            assert step_entry["message"] == "Test step"
            assert step_entry["passed"] is True
            assert "children" in step_entry

    def test_nested_steps(self):
        """Test nested step functionality."""
        log_container = []
        stack = [log_container]

        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = stack

            with qapytest.step("Outer step"), qapytest.step("Inner step"):
                pass

            assert len(log_container) == 1
            outer_step = log_container[0]
            assert outer_step["message"] == "Outer step"
            assert len(outer_step["children"]) == 1

            inner_step = outer_step["children"][0]
            assert inner_step["message"] == "Inner step"
            assert inner_step["passed"] is True

    def test_step_with_failed_assertion(self):
        """Test step marked as failed when containing failed assertions."""
        log_container = []
        stack = [log_container]

        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = stack

            with qapytest.step("Step with failure"):
                qapytest.soft_assert(False, "Failed assertion")

            step_entry = log_container[0]
            assert step_entry["passed"] is False
