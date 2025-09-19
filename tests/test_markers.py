"""Tests for QaPyTest markers: title() and component()."""

import tempfile
from unittest.mock import Mock

import pytest


class TestTitleMarker:
    """Test cases for @pytest.mark.title() marker functionality."""

    def test_title_marker_basic_usage(self):
        """Test that title marker sets custom display title."""
        item = Mock()
        item.user_properties = []

        title_marker = Mock()
        title_marker.args = ["Custom Test Title"]
        item.get_closest_marker.return_value = title_marker
        item.iter_markers.return_value = []

        from qapytest._plugin import pytest_collection_modifyitems

        pytest_collection_modifyitems(Mock(), [item])

        assert ("title", "Custom Test Title") in item.user_properties

    def test_title_marker_with_empty_string(self):
        """Test title marker with empty string is ignored."""
        item = Mock()
        item.user_properties = []

        title_marker = Mock()
        title_marker.args = [""]
        item.get_closest_marker.return_value = title_marker
        item.iter_markers.return_value = []

        from qapytest._plugin import pytest_collection_modifyitems

        pytest_collection_modifyitems(Mock(), [item])

        assert ("title", "") not in item.user_properties

    def test_title_marker_with_none_value(self):
        """Test title marker with None value converts to string."""
        item = Mock()
        item.user_properties = []

        title_marker = Mock()
        title_marker.args = [None]
        item.get_closest_marker.return_value = title_marker
        item.iter_markers.return_value = []

        from qapytest._plugin import pytest_collection_modifyitems

        pytest_collection_modifyitems(Mock(), [item])

        assert ("title", "None") in item.user_properties

    def test_title_marker_with_numeric_value(self):
        """Test title marker converts numeric values to string."""
        item = Mock()
        item.user_properties = []

        title_marker = Mock()
        title_marker.args = [123]
        item.get_closest_marker.return_value = title_marker
        item.iter_markers.return_value = []

        from qapytest._plugin import pytest_collection_modifyitems

        pytest_collection_modifyitems(Mock(), [item])

        assert ("title", "123") in item.user_properties

    def test_title_marker_no_args(self):
        """Test title marker without arguments is ignored."""
        item = Mock()
        item.user_properties = []

        title_marker = Mock()
        title_marker.args = []
        item.get_closest_marker.return_value = title_marker
        item.iter_markers.return_value = []

        from qapytest._plugin import pytest_collection_modifyitems

        pytest_collection_modifyitems(Mock(), [item])

        title_properties = [prop for prop in item.user_properties if prop[0] == "title"]
        assert len(title_properties) == 0

    def test_title_marker_not_present(self):
        """Test when title marker is not present."""
        item = Mock()
        item.user_properties = []
        item.get_closest_marker.return_value = None
        item.iter_markers.return_value = []

        from qapytest._plugin import pytest_collection_modifyitems

        pytest_collection_modifyitems(Mock(), [item])

        title_properties = [prop for prop in item.user_properties if prop[0] == "title"]
        assert len(title_properties) == 0


class TestComponentMarker:
    """Test cases for @pytest.mark.component() marker functionality."""

    def test_component_marker_single_component(self):
        """Test component marker with single component."""
        item = Mock()
        item.user_properties = []
        item.get_closest_marker.return_value = None

        component_marker = Mock()
        component_marker.args = ["Authentication"]
        item.iter_markers.return_value = [component_marker]

        from qapytest._plugin import pytest_collection_modifyitems

        pytest_collection_modifyitems(Mock(), [item])

        assert ("components", ("Authentication",)) in item.user_properties

    def test_component_marker_multiple_components(self):
        """Test component marker with multiple components."""
        item = Mock()
        item.user_properties = []
        item.get_closest_marker.return_value = None

        component_marker = Mock()
        component_marker.args = ["Authentication", "Login", "Security"]
        item.iter_markers.return_value = [component_marker]

        from qapytest._plugin import pytest_collection_modifyitems

        pytest_collection_modifyitems(Mock(), [item])

        assert ("components", ("Authentication", "Login", "Security")) in item.user_properties

    def test_component_marker_multiple_decorators(self):
        """Test multiple component markers on same test."""
        item = Mock()
        item.user_properties = []
        item.get_closest_marker.return_value = None

        component_marker1 = Mock()
        component_marker1.args = ["Authentication"]
        component_marker2 = Mock()
        component_marker2.args = ["Login", "UI"]

        item.iter_markers.return_value = [component_marker1, component_marker2]

        from qapytest._plugin import pytest_collection_modifyitems

        pytest_collection_modifyitems(Mock(), [item])

        assert ("components", ("Authentication", "Login", "UI")) in item.user_properties

    def test_component_marker_duplicate_components(self):
        """Test component marker filters duplicate components."""
        item = Mock()
        item.user_properties = []
        item.get_closest_marker.return_value = None

        component_marker1 = Mock()
        component_marker1.args = ["Authentication", "Login"]
        component_marker2 = Mock()
        component_marker2.args = ["Login", "Security"]

        item.iter_markers.return_value = [component_marker1, component_marker2]

        from qapytest._plugin import pytest_collection_modifyitems

        pytest_collection_modifyitems(Mock(), [item])

        components = None
        for prop in item.user_properties:
            if prop[0] == "components":
                components = prop[1]
                break

        assert components == ("Authentication", "Login", "Security")
        assert components.count("Login") == 1  # type: ignore

    def test_component_marker_empty_strings_ignored(self):
        """Test component marker ignores empty strings."""
        item = Mock()
        item.user_properties = []
        item.get_closest_marker.return_value = None

        component_marker = Mock()
        component_marker.args = ["Authentication", "", "Login", ""]
        item.iter_markers.return_value = [component_marker]

        from qapytest._plugin import pytest_collection_modifyitems

        pytest_collection_modifyitems(Mock(), [item])

        assert ("components", ("Authentication", "Login")) in item.user_properties

    def test_component_marker_non_string_values_ignored(self):
        """Test component marker ignores non-string values."""
        item = Mock()
        item.user_properties = []
        item.get_closest_marker.return_value = None

        component_marker = Mock()
        component_marker.args = ["Authentication", 123, None, "Login", []]
        item.iter_markers.return_value = [component_marker]

        from qapytest._plugin import pytest_collection_modifyitems

        pytest_collection_modifyitems(Mock(), [item])

        assert ("components", ("Authentication", "Login")) in item.user_properties

    def test_component_marker_no_args(self):
        """Test component marker without arguments."""
        item = Mock()
        item.user_properties = []
        item.get_closest_marker.return_value = None

        component_marker = Mock()
        component_marker.args = []
        item.iter_markers.return_value = [component_marker]

        from qapytest._plugin import pytest_collection_modifyitems

        pytest_collection_modifyitems(Mock(), [item])

        component_properties = [prop for prop in item.user_properties if prop[0] == "components"]
        assert len(component_properties) == 0

    def test_component_marker_not_present(self):
        """Test when component marker is not present."""
        item = Mock()
        item.user_properties = []
        item.get_closest_marker.return_value = None
        item.iter_markers.return_value = []

        from qapytest._plugin import pytest_collection_modifyitems

        pytest_collection_modifyitems(Mock(), [item])

        component_properties = [prop for prop in item.user_properties if prop[0] == "components"]
        assert len(component_properties) == 0


class TestMarkersIntegration:
    """Integration tests for both title and component markers together."""

    def test_both_markers_together(self):
        """Test using both title and component markers on same test."""
        item = Mock()
        item.user_properties = []

        title_marker = Mock()
        title_marker.args = ["Login Test with Authentication"]
        item.get_closest_marker.return_value = title_marker

        component_marker = Mock()
        component_marker.args = ["Authentication", "Login"]
        item.iter_markers.return_value = [component_marker]

        from qapytest._plugin import pytest_collection_modifyitems

        pytest_collection_modifyitems(Mock(), [item])

        assert ("title", "Login Test with Authentication") in item.user_properties
        assert ("components", ("Authentication", "Login")) in item.user_properties

    def test_multiple_items_processing(self):
        """Test processing multiple test items with different markers."""
        item1 = Mock()
        item1.user_properties = []
        title_marker1 = Mock()
        title_marker1.args = ["First Test"]
        item1.get_closest_marker.return_value = title_marker1
        item1.iter_markers.return_value = []

        item2 = Mock()
        item2.user_properties = []
        item2.get_closest_marker.return_value = None
        component_marker2 = Mock()
        component_marker2.args = ["Database"]
        item2.iter_markers.return_value = [component_marker2]

        item3 = Mock()
        item3.user_properties = []
        title_marker3 = Mock()
        title_marker3.args = ["Third Test"]
        item3.get_closest_marker.return_value = title_marker3
        component_marker3 = Mock()
        component_marker3.args = ["API", "Integration"]
        item3.iter_markers.return_value = [component_marker3]

        from qapytest._plugin import pytest_collection_modifyitems

        pytest_collection_modifyitems(Mock(), [item1, item2, item3])

        assert ("title", "First Test") in item1.user_properties
        assert len([p for p in item1.user_properties if p[0] == "components"]) == 0

        assert len([p for p in item2.user_properties if p[0] == "title"]) == 0
        assert ("components", ("Database",)) in item2.user_properties

        assert ("title", "Third Test") in item3.user_properties
        assert ("components", ("API", "Integration")) in item3.user_properties


class TestMarkersInHTMLReport:
    """Tests for how markers appear in HTML reports."""

    def test_title_in_html_report(self):
        """Test that title marker affects HTML report generation."""
        from qapytest._report import HtmlReportPlugin

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp_file:
            plugin = HtmlReportPlugin(Mock(), tmp_file.name, "Test Report", "light")

            report = Mock()
            report.nodeid = "test_file.py::test_function"
            report.duration = 1.5
            report.user_properties = [("title", "Custom Test Title")]
            report.outcome = "passed"
            report.when = "call"

            plugin._safe_location = Mock(return_value=("test_file.py", 10, "test_function"))  # noqa: SLF001

            plugin.pytest_runtest_logreport(report)

            result = plugin.results["test_file.py::test_function"]
            assert result["title"] == "Custom Test Title"

    def test_components_in_html_report(self):
        """Test that component marker affects HTML report generation."""
        from qapytest._report import HtmlReportPlugin

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp_file:
            plugin = HtmlReportPlugin(Mock(), tmp_file.name, "Test Report", "light")

            report = Mock()
            report.nodeid = "test_file.py::test_function"
            report.duration = 1.5
            report.user_properties = [("components", ("Authentication", "Login"))]
            report.outcome = "passed"
            report.when = "call"

            plugin._safe_location = Mock(return_value=("test_file.py", 10, "test_function"))  # noqa: SLF001

            plugin.pytest_runtest_logreport(report)

            result = plugin.results["test_file.py::test_function"]
            assert result["components"] == ["Authentication", "Login"]

    def test_both_markers_in_html_report(self):
        """Test both title and component markers in HTML report."""
        from qapytest._report import HtmlReportPlugin

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp_file:
            plugin = HtmlReportPlugin(Mock(), tmp_file.name, "Test Report", "light")

            report = Mock()
            report.nodeid = "test_file.py::test_function"
            report.duration = 1.5
            report.user_properties = [
                ("title", "Authentication Login Test"),
                ("components", ("Authentication", "Login", "UI")),
            ]
            report.outcome = "passed"
            report.when = "call"

            plugin._safe_location = Mock(return_value=("test_file.py", 10, "test_function"))  # noqa: SLF001

            plugin.pytest_runtest_logreport(report)

            result = plugin.results["test_file.py::test_function"]
            assert result["title"] == "Authentication Login Test"
            assert result["components"] == ["Authentication", "Login", "UI"]


class TestMarkersErrorHandling:
    """Test error handling and edge cases for markers."""

    def test_title_marker_with_invalid_marker_object(self):
        """Test title marker handling when marker object is malformed."""
        item = Mock()
        item.user_properties = []

        title_marker = Mock()
        del title_marker.args  # Remove args attribute
        item.get_closest_marker.return_value = title_marker
        item.iter_markers.return_value = []

        from qapytest._plugin import pytest_collection_modifyitems

        with pytest.raises(AttributeError):
            pytest_collection_modifyitems(Mock(), [item])

    def test_component_marker_with_invalid_marker_object(self):
        """Test component marker handling when marker object is malformed."""
        item = Mock()
        item.user_properties = []
        item.get_closest_marker.return_value = None

        component_marker = Mock()
        del component_marker.args  # Remove args attribute
        item.iter_markers.return_value = [component_marker]

        from qapytest._plugin import pytest_collection_modifyitems

        with pytest.raises(AttributeError):
            pytest_collection_modifyitems(Mock(), [item])

    def test_markers_with_existing_user_properties(self):
        """Test markers don't interfere with existing user_properties."""
        item = Mock()
        item.user_properties = [("custom_prop", "custom_value")]

        title_marker = Mock()
        title_marker.args = ["Test Title"]
        item.get_closest_marker.return_value = title_marker

        component_marker = Mock()
        component_marker.args = ["TestComponent"]
        item.iter_markers.return_value = [component_marker]

        from qapytest._plugin import pytest_collection_modifyitems

        pytest_collection_modifyitems(Mock(), [item])

        assert ("custom_prop", "custom_value") in item.user_properties
        assert ("title", "Test Title") in item.user_properties
        assert ("components", ("TestComponent",)) in item.user_properties
