"""Module containing utility functions for QAPyTest."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def load_env_file(env_file_path: Path, *, override: bool = False) -> None:
    """Load environment variables from a .env file.

    Args:
        env_file_path (Path): Path to the .env file.
        override (bool, optional): Whether to override existing environment variables.
            Defaults to False.
    """
    if env_file_path.is_file():
        load_dotenv(dotenv_path=env_file_path, override=override)
