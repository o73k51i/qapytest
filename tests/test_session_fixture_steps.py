"""Integration tests for session-scoped fixture step injection.

Verifies that steps from non-function-scoped fixtures appear in the
execution_log of every test that uses those fixtures, including
parametrized tests where the fixture is served from cache.
"""

import pytest

CONFTEST = """
import pytest
from qapytest import step

@pytest.fixture(scope="session")
def base_resource():
    with step("Create base resource"):
        pass

@pytest.fixture(scope="session")
def derived_resource(base_resource):
    with step("Extend base resource"):
        pass

@pytest.fixture(scope="module")
def module_resource():
    with step("Create module resource"):
        pass

@pytest.fixture
def function_resource():
    with step("Create function resource"):
        pass
"""


def _steps_from_log(execution_log: list) -> list[str]:
    """Recursively extract step messages from an execution log."""
    result = []
    for entry in execution_log:
        if entry.get("type") == "step":
            result.append(entry["message"])
            result.extend(_steps_from_log(entry.get("children", [])))
    return result


class TestSessionScopedFixtureSteps:
    """Steps from session-scoped fixtures must appear in all tests that use them."""

    def test_steps_appear_in_first_parametrized_test(self, pytester: pytest.Pytester) -> None:
        """Steps from a session fixture are logged for the test that triggers setup."""
        pytester.makeconftest(CONFTEST)
        pytester.makepyfile("""
            import pytest

            @pytest.mark.parametrize("x", [1, 2])
            def test_example(base_resource, x):
                pass
        """)
        result = pytester.runpytest()
        result.assert_outcomes(passed=2)

    def test_steps_appear_in_subsequent_parametrized_tests(self, pytester: pytest.Pytester) -> None:
        """Steps from a cached session fixture are injected into subsequent tests."""
        pytester.makeconftest(CONFTEST)
        pytester.makepyfile("""
            import pytest
            from qapytest import _config as cfg

            LOGS = []

            @pytest.mark.parametrize("x", [1, 2, 3])
            def test_example(base_resource, x):
                log = cfg.CURRENT_EXECUTION_LOG.get() or []
                LOGS.append(list(log))

            def test_verify_all_logs_have_step():
                assert len(LOGS) == 3, f"Expected 3 logs, got {len(LOGS)}"
                for i, log in enumerate(LOGS):
                    messages = [e["message"] for e in log if e.get("type") == "step"]
                    assert "Create base resource" in messages, (
                        f"test_example[{i+1}] missing 'Create base resource' step, got: {messages}"
                    )
        """)
        result = pytester.runpytest("-v")
        result.assert_outcomes(passed=4)

    def test_dependency_steps_in_correct_order(self, pytester: pytest.Pytester) -> None:
        """Dependency fixture steps appear before dependent fixture steps."""
        pytester.makeconftest(CONFTEST)
        pytester.makepyfile("""
            import pytest
            from qapytest import _config as cfg

            LOGS = []

            @pytest.mark.parametrize("x", [1, 2])
            def test_example(derived_resource, x):
                log = cfg.CURRENT_EXECUTION_LOG.get() or []
                LOGS.append(list(log))

            def test_verify_order():
                assert len(LOGS) == 2
                for i, log in enumerate(LOGS):
                    messages = [e["message"] for e in log if e.get("type") == "step"]
                    assert messages.index("Create base resource") < messages.index("Extend base resource"), (
                        f"test_example[{i+1}] wrong order: {messages}"
                    )
        """)
        result = pytester.runpytest("-v")
        result.assert_outcomes(passed=3)

    def test_function_scoped_fixture_unaffected(self, pytester: pytest.Pytester) -> None:
        """Function-scoped fixture steps still run for every test individually."""
        pytester.makeconftest(CONFTEST)
        pytester.makepyfile("""
            import pytest
            from qapytest import _config as cfg

            LOGS = []

            @pytest.mark.parametrize("x", [1, 2, 3])
            def test_example(function_resource, x):
                log = cfg.CURRENT_EXECUTION_LOG.get() or []
                LOGS.append(list(log))

            def test_verify_all_logs_have_step():
                assert len(LOGS) == 3
                for i, log in enumerate(LOGS):
                    messages = [e["message"] for e in log if e.get("type") == "step"]
                    assert messages.count("Create function resource") == 1, (
                        f"test_example[{i+1}]: expected exactly 1 step, got {messages}"
                    )
        """)
        result = pytester.runpytest("-v")
        result.assert_outcomes(passed=4)

    def test_session_fixture_runs_exactly_once(self, pytester: pytest.Pytester) -> None:
        """Pytest behavior is unchanged: session fixture executes only once."""
        pytester.makeconftest(CONFTEST)
        pytester.makepyfile("""
            import pytest

            RUN_COUNT = []

            @pytest.fixture(scope="session")
            def counted_fixture():
                RUN_COUNT.append(1)

            @pytest.mark.parametrize("x", [1, 2, 3])
            def test_example(counted_fixture, x):
                pass

            def test_fixture_ran_once():
                assert len(RUN_COUNT) == 1, f"Expected 1 run, got {len(RUN_COUNT)}"
        """)
        result = pytester.runpytest("-v")
        result.assert_outcomes(passed=4)


class TestModuleScopedFixtureSteps:
    """Steps from module-scoped fixtures appear in all tests within the module."""

    def test_steps_appear_in_all_module_tests(self, pytester: pytest.Pytester) -> None:
        """Module-scoped fixture steps appear in every test of the module."""
        pytester.makeconftest(CONFTEST)
        pytester.makepyfile("""
            import pytest
            from qapytest import _config as cfg

            LOGS = []

            @pytest.mark.parametrize("x", [1, 2, 3])
            def test_example(module_resource, x):
                log = cfg.CURRENT_EXECUTION_LOG.get() or []
                LOGS.append(list(log))

            def test_verify_all_logs_have_step():
                assert len(LOGS) == 3
                for i, log in enumerate(LOGS):
                    messages = [e["message"] for e in log if e.get("type") == "step"]
                    assert "Create module resource" in messages, (
                        f"test_example[{i+1}] missing module step, got: {messages}"
                    )
        """)
        result = pytester.runpytest("-v")
        result.assert_outcomes(passed=4)
