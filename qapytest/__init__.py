"""QAPyTest is a powerful package for QA specialists built on top of Pytest.

Unlike a simple plugin, it offers a comprehensive system for writing clear tests,
structuring them with steps, and generating informative interactive HTML reports.
"""

from qapytest._external import HttpClient, attach, soft_assert, step

__all__ = [
    "HttpClient",
    "attach",
    "soft_assert",
    "step",
]
