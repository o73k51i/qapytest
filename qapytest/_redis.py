"""Module for convenient interaction with Redis."""

import json
import logging

import redis
from redis.exceptions import RedisError

from qapytest import _config as cfg


class RedisClient:
    """Client for convenient interaction with Redis.

    This class is a wrapper around the `redis-py` library and provides simple
    methods for performing basic operations (get, set, delete) with
    additional logging and automatic serialization/deserialization
    of data in JSON format.

    It simplifies working with Redis by hiding the details of data encoding
    and connection handling.

    Args:
        host: Redis server address. Default is "localhost".
        port: Redis server port. Default is 6379.
        db: Database number to connect to. Default is 0.
        **kwargs: Other keyword arguments passed directly to the
                  `redis.Redis` constructor (e.g., `password`, `ssl`).

    ---
    ### Example usage:

    ```python
    # Initialize the client
    redis_client = RedisClient(host='localhost', port=6379, db=0)

    # 1. Save a simple string
    redis_client.set_value('user:1:status', 'active', ex=3600) # ex - time-to-live in seconds

    # 2. Retrieve the string
    status = redis_client.get_value('user:1:status')
    print(f"User status: {status}") # >>> User status: active

    # 3. Save a dictionary (automatically converted to JSON)
    user_data = {'name': 'User', 'email': 'user@example.com'}
    redis_client.set_value('user:1:data', user_data)

    # 4. Retrieve and deserialize the dictionary
    retrieved_data = redis_client.get_value('user:1:data')
    print(f"User data: {retrieved_data}") # >>> User data: {'name': 'User', 'email': 'user@example.com'}

    # 5. Check if a key exists and delete it
    if redis_client.key_exists('user:1:status'):
        print("Key 'user:1:status' exists.")
        redis_client.delete_key('user:1:status')
        print("Key deleted.")

    # 6. Check a non-existent key
    non_existent = redis_client.get_value('user:1:non_existent')
    print(f"Non-existent key: {non_existent}") # >>> Non-existent key: None
    ```
    """

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, **kwargs) -> None:
        """Constructor for RedisClient.

        Args:
            host: Redis server address. Default is "localhost".
            port: Redis server port. Default is 6379.
            db: Database number to connect to. Default is 0.
            **kwargs: Other keyword arguments passed directly to the
                      `redis.Redis` constructor (e.g., `password`, `ssl`).
        """
        self._logger = logging.getLogger("RedisClient")

        logging.getLogger("redis").setLevel(logging.WARNING)

        try:
            self._client = redis.Redis(host=host, port=port, db=db, **kwargs)
            self._client.ping()
        except RedisError as e:
            self._logger.error(f"Failed to connect to Redis: {e}")
            raise

    def set_value(self, key: str, value: cfg.AnyType, ex: int | None = None) -> bool:
        """Stores a value by key, automatically serializing it.

        Args:
            key: The key under which the value is stored.
            value: The value to store. Dictionaries and lists
                   are automatically converted to JSON.
            ex: Time-to-live of the key in seconds.

        Returns:
            True if the operation is successful, otherwise False.
        """
        try:
            if isinstance(value, dict | list):
                processed_value = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, bytes):
                processed_value = value
            else:
                processed_value = str(value)

            self._client.set(key, processed_value, ex=ex)
            self._logger.info(f"SET: Key '{key}' successfully saved (ex={ex}s).")
            return True
        except RedisError as e:
            self._logger.error(f"Error during SET operation for key '{key}': {e}")
            return False

    def get_value(self, key: str) -> cfg.AnyType:
        """Retrieves and automatically deserializes the value by key.

        Args:
            key: The key to retrieve the value for.

        Returns:
            The stored value. If the value was in JSON format,
            it will be deserialized. If the key is not found, returns None.
        """
        try:
            value_bytes = self._client.get(key)
            if value_bytes is None:
                self._logger.info(f"GET: Key '{key}' not found.")
                return None

            value_str = value_bytes.decode("utf-8")  # type: ignore

            try:
                deserialized_value = json.loads(value_str)
                self._logger.info(f"GET: Key '{key}' found and deserialized from JSON.")
                self._logger.debug(f"Deserialized value: {deserialized_value}")
                return deserialized_value
            except json.JSONDecodeError:
                self._logger.info(f"GET: Key '{key}' found (plain string).")
                self._logger.debug(f"String value: {value_str}")
                return value_str
        except RedisError as e:
            self._logger.error(f"Error during GET operation for key '{key}': {e}")
            return None

    def delete_key(self, key: str) -> bool:
        """Deletes a key from Redis.

        Args:
            key: The key to delete.

        Returns:
            True if the key was found and deleted, otherwise False.
        """
        try:
            deleted_count = self._client.delete(key)
            if deleted_count > 0:  # type: ignore
                self._logger.info(f"DELETE: Key '{key}' successfully deleted.")
                return True
            self._logger.info(f"DELETE: Key '{key}' not found for deletion.")
            return False
        except RedisError as e:
            self._logger.error(f"Error during DELETE operation for key '{key}': {e}")
            return False

    def key_exists(self, key: str) -> bool:
        """Checks if a key exists in Redis.

        Args:
            key: The key to check.

        Returns:
            True if the key exists, otherwise False.
        """
        try:
            exists = self._client.exists(key) > 0  # type: ignore
            self._logger.info(f"EXISTS: Key '{key}' check: {'found' if exists else 'not found'}.")
            return exists
        except RedisError as e:
            self._logger.error(f"Error during EXISTS operation for key '{key}': {e}")
            return False
