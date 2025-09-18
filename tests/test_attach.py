"""Module for testing the attach function in QaPyTest."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import qapytest
from qapytest import _config as cfg


class TestAttachFunction:
    """Tests for the attach function."""

    def test_attach_without_context(self):
        """Test attach function when no context is available."""
        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = None

            qapytest.attach("test data", "Test label")

    def test_attach_string_data(self):
        """Test attach function with string data."""
        log_container = []
        stack = [log_container]

        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = stack

            qapytest.attach("Hello, World!", "String attachment")

            assert len(log_container) == 1
            entry = log_container[0]
            assert entry["type"] == "attachment"
            assert entry["label"] == "String attachment"
            assert entry["data"] == "Hello, World!"
            assert entry["content_type"] == "text"

    def test_attach_dict_data(self):
        """Test attach function with dictionary data."""
        log_container = []
        stack = [log_container]

        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = stack

            test_dict = {"key": "value", "number": 42}
            qapytest.attach(test_dict, "Dict attachment")

            assert len(log_container) == 1
            entry = log_container[0]
            assert entry["type"] == "attachment"
            assert entry["label"] == "Dict attachment"
            assert entry["content_type"] == "json"

            parsed_data = json.loads(entry["data"])
            assert parsed_data == test_dict

    def test_attach_list_data(self):
        """Test attach function with list data."""
        log_container = []
        stack = [log_container]

        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = stack

            test_list = [1, 2, "three", {"four": 4}]
            qapytest.attach(test_list, "List attachment")

            entry = log_container[0]
            assert entry["content_type"] == "json"
            parsed_data = json.loads(entry["data"])
            assert parsed_data == test_list

    def test_attach_bytes_data(self):
        """Test attach function with bytes data."""
        log_container = []
        stack = [log_container]

        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = stack

            test_bytes = b"Hello, bytes!"
            qapytest.attach(test_bytes, "Bytes attachment")

            entry = log_container[0]
            assert entry["type"] == "attachment"
            assert entry["content_type"] == "image"

            assert entry["data"].startswith("data:")
            assert ";base64," in entry["data"]

    def test_attach_path_object(self):
        """Test attach function with Path object."""
        log_container = []
        stack = [log_container]

        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = stack

            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write("Test file content")
                temp_path = Path(f.name)

            try:
                qapytest.attach(temp_path, "Path attachment")

                entry = log_container[0]
                assert entry["content_type"] == "text"
                assert str(temp_path) in entry["data"]
            finally:
                temp_path.unlink()

    def test_attach_image_file_path(self):
        """Test attach function with image file path."""
        log_container = []
        stack = [log_container]

        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = stack

            png_header = b"\x89PNG\r\n\x1a\n"
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                f.write(png_header + b"fake png data")
                temp_path = Path(f.name)

            try:
                qapytest.attach(temp_path, "Image attachment")

                entry = log_container[0]
                assert entry["content_type"] == "image"
                assert entry["data"].startswith("data:image/png;base64,")
            finally:
                temp_path.unlink()

    def test_attach_custom_mime_type(self):
        """Test attach function with custom MIME type."""
        log_container = []
        stack = [log_container]

        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = stack

            test_bytes = b"custom data"
            qapytest.attach(test_bytes, "Custom MIME", mime="application/custom")

            entry = log_container[0]
            assert "data:application/custom;base64," in entry["data"]

    def test_attach_complex_object(self):
        """Test attach function with complex Python objects."""
        log_container = []
        stack = [log_container]

        with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
            mock_stack.get.return_value = stack

            class CustomObject:
                def __repr__(self) -> str:
                    return "<CustomObject instance>"

            obj = CustomObject()
            qapytest.attach(obj, "Object attachment")

            entry = log_container[0]
            assert entry["content_type"] == "text"
            assert "<CustomObject instance>" in entry["data"]

    def test_attach_truncation(self):
        """Test attach function with data truncation."""
        log_container = []
        stack = [log_container]

        original_limit = cfg.ATTACH_LIMIT_BYTES
        cfg.ATTACH_LIMIT_BYTES = 10

        try:
            with patch.object(cfg, "CURRENT_LOG_CONTAINER_STACK") as mock_stack:
                mock_stack.get.return_value = stack

                long_text = "x" * 100
                qapytest.attach(long_text, "Long text")

                entry = log_container[0]
                assert "(truncated)" in entry["label"]
                assert "[TRUNCATED]" in entry["data"]
        finally:
            cfg.ATTACH_LIMIT_BYTES = original_limit
