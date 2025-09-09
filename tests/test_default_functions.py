"""Module with default test functions."""

import pytest


def test_pass():
    assert True


def test_fail():
    assert False, "This test is designed to fail"


@pytest.mark.skip(reason="Skipping this test")
def test_skip():
    assert False, "This test is skipped"


@pytest.mark.xfail(reason="Expected to fail")
def test_expected_fail():
    assert False, "This test is expected to fail"


@pytest.mark.xfail(reason="Expected to fail but passes")
def test_unexpected_pass():
    assert True, "This test is expected to fail but passes"
