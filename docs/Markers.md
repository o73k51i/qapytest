# Test Markers

QaPyTest supports custom pytest markers to enhance test reporting and organization.

## Available Markers

### Title Marker

Set a custom name for the test in reports.

#### Signature

```python
@pytest.mark.title(name: str)
```

#### Purpose

- Override the default test function name in reports
- Display more descriptive test names in HTML/JSON reports
- Make reports more user-friendly

#### Usage

```python
import pytest

@pytest.mark.title("User can login with valid credentials")
def test_login_valid():
    """This function name is less descriptive, title marker helps."""
    pass

@pytest.mark.title("Verify user profile data accuracy")
def test_profile_data():
    pass
```

### Component Marker

Tag tests with component/module identifiers.

#### Signature

```python
@pytest.mark.component(name: str, ...)
```

#### Purpose

- Categorize tests by component or module
- Filter tests by component in reports
- Organize large test suites

#### Single Component

```python
import pytest

@pytest.mark.component("API")
def test_api_endpoint():
    pass

@pytest.mark.component("Database")
def test_database_query():
    pass
```

#### Multiple Components

```python
@pytest.mark.component("API", "Database")
def test_api_with_db_validation():
    """Test that touches both API and Database."""
    pass

@pytest.mark.component("Auth", "API", "Security")
def test_auth_flow():
    """Complex test with multiple components."""
    pass
```
