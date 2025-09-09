"""QAPyTest core logic and pytest plugin.

This module implements the core logic for the QAPyTest package and
functions as an internal plugin for Pytest.

It defines custom settings, hooks, and extends the functionality
of Pytest.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from qapytest import _utils as utils


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("QAPyTest", "QAPyTest custom options")
    group.addoption(
        "--env-file",
        action="store",
        default=None,
        help="Path to a .env file.",
    )
    group.addoption(
        "--env-override",
        action="store_true",
        default=False,
        help="If set, values from the .env file will override already-set environment variables.",
    )


def pytest_configure(config: pytest.Config) -> None:
    env_file_path_str = config.getoption("--env-file")
    env_file = Path(env_file_path_str) if env_file_path_str else Path(".env")
    utils.load_env_file(env_file_path=env_file, override=bool(config.getoption("--env-override")))
