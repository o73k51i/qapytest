"""Module for convenient interaction with Redis."""

import logging

import redis


class RedisClient(redis.Redis):
    """Client for convenient interaction with Redis with enhanced logging.

    This class extends the `redis-py` Redis client by adding comprehensive
    logging for all Redis commands. It logs each command execution at INFO level
    and results at DEBUG level, making it easier to trace Redis operations
    during development and debugging.

    The client inherits all functionality from the standard Redis client,
    so you can use any Redis command available in the `redis-py` library.

    Args:
        host: Redis server address.
        port: Redis server port. Default is 6379.
        **kwargs: Other keyword arguments passed directly to the
                  `redis.Redis` constructor (e.g., `password`, `ssl`, `db`).

    ---
    ### Example usage:

    ```python
    # Initialize the client
    redis_client = RedisClient(host='localhost', port=6379, db=0)

    # 1. Save a simple string value
    redis_client.set('user:1:status', 'active', ex=3600)  # ex - time-to-live in seconds

    # 2. Retrieve the string value
    status = redis_client.get('user:1:status')
    print(f"User status: {status}")  # >>> User status: b'active'

    # 3. Save a JSON string (manual serialization)
    import json
    user_data = {'name': 'User', 'email': 'user@example.com'}
    redis_client.set('user:1:data', json.dumps(user_data))

    # 4. Retrieve and deserialize the JSON data
    retrieved_data = json.loads(redis_client.get('user:1:data'))
    print(f"User data: {retrieved_data}")  # >>> User data: {'name': 'User', 'email': 'user@example.com'}

    # 5. Check if a key exists and delete it
    if redis_client.exists('user:1:status'):
        print("Key 'user:1:status' exists.")
        redis_client.delete('user:1:status')
        print("Key deleted.")

    # 6. Check a non-existent key
    non_existent = redis_client.get('user:1:non_existent')
    print(f"Non-existent key: {non_existent}")  # >>> Non-existent key: None

    # 7. Working with lists
    redis_client.lpush('tasks', 'task1', 'task2', 'task3')
    task = redis_client.rpop('tasks')
    print(f"Retrieved task: {task}")  # >>> Retrieved task: b'task1'

    # 8. Working with sets
    redis_client.sadd('users:active', 'user1', 'user2', 'user3')
    is_member = redis_client.sismember('users:active', 'user1')
    print(f"User1 is active: {is_member}")  # >>> User1 is active: True
    ```
    """

    def __init__(self, host: str, port: int = 6379, **kwargs) -> None:
        """Constructor for RedisClient.

        Args:
            host: Redis server address.
            port: Redis server port. Default is 6379.
            **kwargs: Other keyword arguments passed directly to the
                      `redis.Redis` constructor (e.g., `password`, `ssl`).
        """
        super().__init__(host=host, port=port, **kwargs)
        self._logger = logging.getLogger("RedisClient")
        for name in ("redis", "redis.connection", "redis.client"):
            logging.getLogger(name).setLevel(logging.WARNING)

    def execute_command(self, *args, **kwargs) -> object:
        parts = []
        for arg in args:
            if isinstance(arg, str):
                parts.append(f'"{arg}"')
            elif isinstance(arg, bytes | bytearray):
                try:
                    parts.append(f'"{arg.decode()}"')
                except Exception:
                    parts.append(repr(arg))
            else:
                parts.append(str(arg))

        command = " ".join(parts)
        self._logger.info(f"Command: {command}")

        try:
            result = super().execute_command(*args, **kwargs)
            if isinstance(result, bytes | bytearray):
                try:
                    self._logger.debug(f'Executed: "{result.decode()}"')
                except Exception:
                    self._logger.debug(f"Executed: {result!r}")
            else:
                self._logger.debug(f"Executed: {result}")
            return result
        except Exception as e:
            self._logger.error(f"Command '{command}' failed: {e}")
            raise
