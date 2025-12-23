# Quick Start Guide

Get up and running with QaPyTest in 3 simple steps.

## 🚀 Quick start

### 1️⃣ installation

```bash
pip install "qapytest[http,sql]"
```

### 2️⃣ Writing test

```python
import pytest

from qapytest import attach, soft_assert, step


@pytest.mark.title("Sample test")
@pytest.mark.parametrize(("a", "b"), [(1, 2), (1, 1)])
def test_example(a: int, b: int) -> None:
    """Example test function demonstrating steps, soft assertions, and attachments."""
    with step("Descriptive step name"):
        result = a + b
        with step("Check if result is even"):
            soft_assert(result % 2 == 0, f"Sum of {a} and {b} should be even")
        with step("Attach the result"):
            attach(f"Result {a} + {b} = {result}", "Result")

```

### 3️⃣ Run with report

```bash
pytest --report-html
```
