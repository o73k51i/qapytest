"""Tests for RedisClient in QaPyTest."""

import json
from unittest.mock import MagicMock, patch

import pytest
from redis.exceptions import RedisError

from qapytest import RedisClient


class TestRedisClient:
    """Test cases for RedisClient functionality."""

    @patch("redis.Redis")
    def test_redis_client_initialization(self, mock_redis: MagicMock) -> None:
        """Test RedisClient initialization with default parameters."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True

        RedisClient()

        mock_redis.assert_called_once_with(host="localhost", port=6379, db=0)
        mock_redis_instance.ping.assert_called_once()

    @patch("redis.Redis")
    def test_redis_client_initialization_with_params(self, mock_redis: MagicMock) -> None:
        """Test RedisClient initialization with custom parameters."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True

        RedisClient(host="redis.example.com", port=6380, db=1, password="secret")  # noqa: S106

        mock_redis.assert_called_once_with(
            host="redis.example.com",
            port=6380,
            db=1,
            password="secret",  # noqa: S106
        )

    @patch("redis.Redis")
    def test_connection_failure(self, mock_redis: MagicMock) -> None:
        """Test RedisClient initialization failure handling."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.side_effect = RedisError("Connection failed")

        with pytest.raises(RedisError):
            RedisClient()

    @patch("redis.Redis")
    def test_set_value_string(self, mock_redis: MagicMock) -> None:
        """Test setting string values."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.set.return_value = True

        client = RedisClient()

        with patch.object(client._logger, "info") as mock_info:  # noqa: SLF001
            result = client.set_value("test_key", "test_value")

            assert result is True
            mock_redis_instance.set.assert_called_once_with("test_key", "test_value", ex=None)
            mock_info.assert_called_with("SET: Key 'test_key' successfully saved (ex=Nones).")

    @patch("redis.Redis")
    def test_set_value_dict(self, mock_redis: MagicMock) -> None:
        """Test setting dictionary values with JSON serialization."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.set.return_value = True

        client = RedisClient()
        test_dict = {"name": "John", "age": 30}

        result = client.set_value("test_key", test_dict, ex=3600)

        expected_json = json.dumps(test_dict, ensure_ascii=False)
        mock_redis_instance.set.assert_called_once_with("test_key", expected_json, ex=3600)
        assert result is True

    @patch("redis.Redis")
    def test_set_value_list(self, mock_redis: MagicMock) -> None:
        """Test setting list values with JSON serialization."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.set.return_value = True

        client = RedisClient()
        test_list = [1, 2, 3, "test"]

        result = client.set_value("test_key", test_list)

        expected_json = json.dumps(test_list, ensure_ascii=False)
        mock_redis_instance.set.assert_called_once_with("test_key", expected_json, ex=None)
        assert result is True

    @patch("redis.Redis")
    def test_set_value_bytes(self, mock_redis: MagicMock) -> None:
        """Test setting bytes values."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.set.return_value = True

        client = RedisClient()
        test_bytes = b"binary data"

        result = client.set_value("test_key", test_bytes)

        mock_redis_instance.set.assert_called_once_with("test_key", test_bytes, ex=None)
        assert result is True

    @patch("redis.Redis")
    def test_set_value_redis_error(self, mock_redis: MagicMock) -> None:
        """Test set_value with Redis error."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.set.side_effect = RedisError("Redis error")

        client = RedisClient()

        with patch.object(client._logger, "error") as mock_error:  # noqa: SLF001
            result = client.set_value("test_key", "test_value")

            assert result is False
            mock_error.assert_called_with("Error during SET operation for key 'test_key': Redis error")

    @patch("redis.Redis")
    def test_get_value_string(self, mock_redis: MagicMock) -> None:
        """Test getting string values."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = b"test_value"

        client = RedisClient()

        with patch.object(client._logger, "info") as mock_info:  # noqa: SLF001
            result = client.get_value("test_key")

            assert result == "test_value"
            mock_info.assert_called_with("GET: Key 'test_key' found (plain string).")

    @patch("redis.Redis")
    def test_get_value_json(self, mock_redis: MagicMock) -> None:
        """Test getting JSON values with deserialization."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True

        test_dict = {"name": "John", "age": 30}
        json_value = json.dumps(test_dict, ensure_ascii=False)
        mock_redis_instance.get.return_value = json_value.encode("utf-8")

        client = RedisClient()

        with patch.object(client._logger, "info") as mock_info:  # noqa: SLF001
            result = client.get_value("test_key")

            assert result == test_dict
            mock_info.assert_called_with("GET: Key 'test_key' found and deserialized from JSON.")

    @patch("redis.Redis")
    def test_get_value_not_found(self, mock_redis: MagicMock) -> None:
        """Test getting non-existent key."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = None

        client = RedisClient()

        with patch.object(client._logger, "info") as mock_info:  # noqa: SLF001
            result = client.get_value("nonexistent_key")

            assert result is None
            mock_info.assert_called_with("GET: Key 'nonexistent_key' not found.")

    @patch("redis.Redis")
    def test_get_value_redis_error(self, mock_redis: MagicMock) -> None:
        """Test get_value with Redis error."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.side_effect = RedisError("Redis error")

        client = RedisClient()

        with patch.object(client._logger, "error") as mock_error:  # noqa: SLF001
            result = client.get_value("test_key")

            assert result is None
            mock_error.assert_called_with("Error during GET operation for key 'test_key': Redis error")

    @patch("redis.Redis")
    def test_delete_key_success(self, mock_redis: MagicMock) -> None:
        """Test successful key deletion."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.delete.return_value = 1

        client = RedisClient()

        with patch.object(client._logger, "info") as mock_info:  # noqa: SLF001
            result = client.delete_key("test_key")

            assert result is True
            mock_info.assert_called_with("DELETE: Key 'test_key' successfully deleted.")

    @patch("redis.Redis")
    def test_delete_key_not_found(self, mock_redis: MagicMock) -> None:
        """Test deleting non-existent key."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.delete.return_value = 0

        client = RedisClient()

        with patch.object(client._logger, "info") as mock_info:  # noqa: SLF001
            result = client.delete_key("nonexistent_key")

            assert result is False
            mock_info.assert_called_with("DELETE: Key 'nonexistent_key' not found for deletion.")

    @patch("redis.Redis")
    def test_key_exists_true(self, mock_redis: MagicMock) -> None:
        """Test key_exists when key exists."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.exists.return_value = 1

        client = RedisClient()

        with patch.object(client._logger, "info") as mock_info:  # noqa: SLF001
            result = client.key_exists("test_key")

            assert result is True
            mock_info.assert_called_with("EXISTS: Key 'test_key' check: found.")

    @patch("redis.Redis")
    def test_key_exists_false(self, mock_redis: MagicMock) -> None:
        """Test key_exists when key does not exist."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.exists.return_value = 0

        client = RedisClient()

        with patch.object(client._logger, "info") as mock_info:  # noqa: SLF001
            result = client.key_exists("nonexistent_key")

            assert result is False
            mock_info.assert_called_with("EXISTS: Key 'nonexistent_key' check: not found.")

    @patch("redis.Redis")
    def test_logger_setup(self, mock_redis: MagicMock) -> None:
        """Test that logger is properly configured."""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True

        client = RedisClient()
        assert hasattr(client, "_logger")
        assert client._logger.name == "RedisClient"  # noqa: SLF001
