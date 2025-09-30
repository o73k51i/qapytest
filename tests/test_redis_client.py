"""Tests for RedisClient in QaPyTest."""

from unittest.mock import MagicMock, patch

import pytest
from redis.exceptions import RedisError

from qapytest import RedisClient


class TestRedisClient:
    """Test cases for RedisClient functionality."""

    def test_redis_client_initialization_default(self) -> None:
        """Test RedisClient initialization with default parameters."""
        client = RedisClient(host="localhost")

        assert client.connection_pool.connection_kwargs["host"] == "localhost"
        assert client.connection_pool.connection_kwargs["port"] == 6379
        assert hasattr(client, "_logger")
        assert client._logger.name == "RedisClient"  # noqa: SLF001

    def test_redis_client_initialization_with_params(self) -> None:
        """Test RedisClient initialization with custom parameters."""
        test_password = "test_password"  # noqa: S105
        client = RedisClient(host="redis.example.com", port=6380, db=1, password=test_password)

        assert client.connection_pool.connection_kwargs["host"] == "redis.example.com"
        assert client.connection_pool.connection_kwargs["port"] == 6380
        assert client.connection_pool.connection_kwargs["db"] == 1
        assert client.connection_pool.connection_kwargs["password"] == test_password

    def test_execute_command_logging_string_args(self) -> None:
        """Test execute_command method with string arguments and logging."""
        client = RedisClient(host="localhost")

        with (
            patch.object(client._logger, "info") as mock_info,  # noqa: SLF001
            patch.object(client._logger, "debug") as mock_debug,  # noqa: SLF001
            patch("redis.Redis.execute_command") as mock_parent_execute,
        ):
            mock_parent_execute.return_value = True

            result = client.execute_command("SET", "test_key", "test_value")

            mock_info.assert_called_with('Command: "SET" "test_key" "test_value"')
            mock_debug.assert_called_with("Executed: True")
            assert result is True

    def test_execute_command_logging_bytes_args(self) -> None:
        """Test execute_command method with bytes arguments."""
        client = RedisClient(host="localhost")

        with (
            patch.object(client._logger, "info") as mock_info,  # noqa: SLF001
            patch.object(client._logger, "debug") as mock_debug,  # noqa: SLF001
            patch("redis.Redis.execute_command") as mock_parent_execute,
        ):
            mock_parent_execute.return_value = b"OK"

            result = client.execute_command("GET", b"test_key")

            mock_info.assert_called_with('Command: "GET" "test_key"')
            mock_debug.assert_called_with('Executed: "OK"')
            assert result == b"OK"

    def test_execute_command_error_handling(self) -> None:
        """Test execute_command method error handling."""
        client = RedisClient(host="localhost")

        with (
            patch.object(client._logger, "error") as mock_error,  # noqa: SLF001
            patch("redis.Redis.execute_command") as mock_parent_execute,
        ):
            mock_parent_execute.side_effect = RedisError("Connection failed")

            with pytest.raises(RedisError):
                client.execute_command("SET", "test_key", "test_value")

            mock_error.assert_called_with('Command \'"SET" "test_key" "test_value"\' failed: Connection failed')

    @patch.object(RedisClient, "set")
    def test_redis_set_operation(self, mock_set: MagicMock) -> None:
        """Test standard Redis SET operation."""
        mock_set.return_value = True
        client = RedisClient(host="localhost")

        result = client.set("test_key", "test_value", ex=3600)

        assert result is True
        mock_set.assert_called_once_with("test_key", "test_value", ex=3600)

    @patch.object(RedisClient, "get")
    def test_redis_get_operation(self, mock_get: MagicMock) -> None:
        """Test standard Redis GET operation."""
        mock_get.return_value = b"test_value"
        client = RedisClient(host="localhost")

        result = client.get("test_key")

        assert result == b"test_value"
        mock_get.assert_called_once_with("test_key")

    @patch.object(RedisClient, "get")
    def test_redis_get_nonexistent_key(self, mock_get: MagicMock) -> None:
        """Test Redis GET operation for non-existent key."""
        mock_get.return_value = None
        client = RedisClient(host="localhost")

        result = client.get("nonexistent_key")

        assert result is None
        mock_get.assert_called_once_with("nonexistent_key")

    @patch.object(RedisClient, "exists")
    def test_redis_exists_operation(self, mock_exists: MagicMock) -> None:
        """Test standard Redis EXISTS operation."""
        mock_exists.return_value = 1
        client = RedisClient(host="localhost")

        result = client.exists("test_key")

        assert result == 1
        mock_exists.assert_called_once_with("test_key")

    @patch.object(RedisClient, "delete")
    def test_redis_delete_operation(self, mock_delete: MagicMock) -> None:
        """Test standard Redis DELETE operation."""
        mock_delete.return_value = 1
        client = RedisClient(host="localhost")

        result = client.delete("test_key")

        assert result == 1
        mock_delete.assert_called_once_with("test_key")

    @patch.object(RedisClient, "lpush")
    def test_redis_lpush_operation(self, mock_lpush: MagicMock) -> None:
        """Test standard Redis LPUSH operation."""
        mock_lpush.return_value = 3
        client = RedisClient(host="localhost")

        result = client.lpush("test_list", "item1", "item2", "item3")

        assert result == 3
        mock_lpush.assert_called_once_with("test_list", "item1", "item2", "item3")

    @patch.object(RedisClient, "rpop")
    def test_redis_rpop_operation(self, mock_rpop: MagicMock) -> None:
        """Test standard Redis RPOP operation."""
        mock_rpop.return_value = b"item1"
        client = RedisClient(host="localhost")

        result = client.rpop("test_list")

        assert result == b"item1"
        mock_rpop.assert_called_once_with("test_list")

    @patch.object(RedisClient, "sadd")
    def test_redis_sadd_operation(self, mock_sadd: MagicMock) -> None:
        """Test standard Redis SADD operation."""
        mock_sadd.return_value = 2
        client = RedisClient(host="localhost")

        result = client.sadd("test_set", "member1", "member2")

        assert result == 2
        mock_sadd.assert_called_once_with("test_set", "member1", "member2")

    @patch.object(RedisClient, "sismember")
    def test_redis_sismember_operation(self, mock_sismember: MagicMock) -> None:
        """Test standard Redis SISMEMBER operation."""
        mock_sismember.return_value = True
        client = RedisClient(host="localhost")

        result = client.sismember("test_set", "member1")

        assert result is True
        mock_sismember.assert_called_once_with("test_set", "member1")

    @patch.object(RedisClient, "hset")
    def test_redis_hset_operation(self, mock_hset: MagicMock) -> None:
        """Test standard Redis HSET operation."""
        mock_hset.return_value = 1
        client = RedisClient(host="localhost")

        result = client.hset("test_hash", "field1", "value1")

        assert result == 1
        mock_hset.assert_called_once_with("test_hash", "field1", "value1")

    @patch.object(RedisClient, "hget")
    def test_redis_hget_operation(self, mock_hget: MagicMock) -> None:
        """Test standard Redis HGET operation."""
        mock_hget.return_value = b"value1"
        client = RedisClient(host="localhost")

        result = client.hget("test_hash", "field1")

        assert result == b"value1"
        mock_hget.assert_called_once_with("test_hash", "field1")

    def test_json_workflow_with_redis_operations(self) -> None:
        """Test JSON serialization/deserialization workflow using standard Redis operations."""
        import json as json_module

        client = RedisClient(host="localhost")

        test_data = {"name": "John", "age": 30, "city": "New York"}
        json_data = json_module.dumps(test_data)

        with patch.object(client, "set") as mock_set, patch.object(client, "get") as mock_get:
            mock_set.return_value = True
            mock_get.return_value = json_data.encode("utf-8")
            client.set("user:1", json_data)
            retrieved_json = client.get("user:1")
            if hasattr(retrieved_json, "decode"):
                retrieved_data = json_module.loads(retrieved_json.decode("utf-8"))  # type: ignore[union-attr]
            else:
                retrieved_data = json_module.loads(str(retrieved_json))

            assert retrieved_data == test_data
            mock_set.assert_called_once_with("user:1", json_data)
            mock_get.assert_called_once_with("user:1")

    def test_logger_setup(self) -> None:
        """Test that logger is properly configured."""
        client = RedisClient(host="localhost")

        assert hasattr(client, "_logger")
        assert client._logger.name == "RedisClient"  # noqa: SLF001

    @patch.object(RedisClient, "ping")
    def test_connection_check(self, mock_ping: MagicMock) -> None:
        """Test Redis connection check."""
        mock_ping.return_value = True
        client = RedisClient(host="localhost")

        result = client.ping()

        assert result is True
        mock_ping.assert_called_once()

    @patch.object(RedisClient, "ping")
    def test_connection_failure(self, mock_ping: MagicMock) -> None:
        """Test Redis connection failure."""
        mock_ping.side_effect = RedisError("Connection failed")
        client = RedisClient(host="localhost")

        with pytest.raises(RedisError):
            client.ping()
