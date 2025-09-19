from unittest.mock import patch

import qapytest
from qapytest import _config as cfg


class TestIntegrationScenarios:
    """Integration tests combining multiple qapytest features."""

    def test_complete_test_scenario(self):
        """Test a complete scenario using all qapytest features."""
        log_container = []
        stack = [log_container]

        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = stack

            with qapytest.step("Setup test environment"):
                qapytest.attach("Initial setup", "Setup note")
                qapytest.soft_assert(True, "Environment ready")

            with qapytest.step("Execute main test logic"):
                qapytest.attach({"status": "running", "progress": 50}, "Test progress")
                qapytest.soft_assert(2 + 2 == 4, "Basic math works")

                with qapytest.step("Validate results"):
                    qapytest.soft_assert(True, "Results are valid")
                    qapytest.attach("Validation complete", "Validation status")

            with qapytest.step("Cleanup"):
                qapytest.soft_assert(True, "Cleanup successful")

        assert len(log_container) == 3

        setup_step = log_container[0]
        assert setup_step["message"] == "Setup test environment"
        assert len(setup_step["children"]) == 2

        main_step = log_container[1]
        assert main_step["message"] == "Execute main test logic"
        assert len(main_step["children"]) == 3

        nested_step = main_step["children"][2]
        assert nested_step["message"] == "Validate results"
        assert len(nested_step["children"]) == 2

    def test_error_handling_in_attach(self):
        """Test error handling in attach function."""
        log_container = []
        stack = [log_container]

        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = stack

            class UnserializableObject:
                def __init__(self) -> None:
                    self.circular_ref = self

            obj = UnserializableObject()

            qapytest.attach(obj, "Problematic object")

            entry = log_container[0]
            assert entry["content_type"] == "text"
            assert "UnserializableObject" in entry["data"]

    def test_step_with_exception(self):
        """Test step behavior when an exception occurs inside."""
        log_container = []
        stack = [log_container]

        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = stack

            try:
                with qapytest.step("Step with exception"):
                    qapytest.soft_assert(False, "This will fail")
                    raise ValueError("Test exception")
            except ValueError:
                pass

            step_entry = log_container[0]
            assert step_entry["passed"] is False
