"""Module for testing environment variable handling in QAPyTest."""

from os import getenv


def test_read_env_variable():
    # For this test, create a .env file in the root directory of the project with the content:
    # PWD="test"
    actual_value = getenv("PWD")
    expect_value = "test"
    assert actual_value == expect_value, f"Expected {expect_value}, got {actual_value}"
