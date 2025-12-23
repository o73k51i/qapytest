# Browser Automation with Playwright

QaPyTest includes seamless integration with pytest-playwright for browser automation and end-to-end web testing.

## Features

- **Automatic browser management** — browsers are managed automatically by pytest-playwright
- **Page fixtures** — `page`, `browser`, `context` fixtures available in tests
- **Screenshot on failure** — automatic screenshots when tests fail
- **Video recording** — record test execution as videos for debugging
- **Trace collection** — collect detailed traces for debugging
- **Cross-browser testing** — support for Chromium, Firefox, and WebKit

## Installation

```bash
pip install "qapytest[web]"
```

After installation, download browser binaries:

```bash
playwright install
```

This downloads Chromium, Firefox, and WebKit binaries needed for browser automation.

## Available Fixtures

All standard pytest-playwright fixtures are available:

- `page` — Page instance for a test
- `browser` — Browser instance
- `context` — Browser context instance
- `browser_name` — Current browser name (chromium, firefox, webkit)

## Basic Usage

```python
import pytest
from qapytest import step, soft_assert, Faker

def test_web_app(page):
    """Test case demonstrating browser automation."""
    fake = Faker()
    
    with step("Navigate to login page"):
        page.goto("http://example.com/login")
    
    with step("Fill login form"):
        page.get_by_label("Username").fill(fake.user_name())
        page.get_by_label("Password").fill(fake.password())
    
    with step("Submit form"):
        page.get_by_role("button", name="Log in").click()
    
    with step("Verify login success"):
        # Wait for navigation
        page.wait_for_url("http://example.com/dashboard")
        heading = page.get_by_role("heading").text_content()
        soft_assert(heading is not None, "Dashboard heading exists")
```

## Common Locator Patterns

```python
# By role
page.get_by_role("button", name="Submit")
page.get_by_role("heading", level=1)

# By label (for form fields)
page.get_by_label("Email")
page.get_by_label("Password")

# By placeholder
page.get_by_placeholder("Enter your email")

# By text
page.get_by_text("Click me")

# By test ID (recommended for testing)
page.locator('[data-testid="submit-button"]')

# CSS selector
page.locator(".button-class")
page.locator("#button-id")

# XPath
page.locator("//button[@class='primary']")
```

## Interactions

```python
# Click
page.get_by_role("button").click()

# Fill text input
page.get_by_label("Email").fill("user@example.com")

# Select from dropdown
page.get_by_label("Country").select_option("US")

# Check checkbox
page.get_by_label("Accept terms").check()

# Type (character by character, triggers event handlers)
page.get_by_label("Search").type("query", delay=100)

# Press key
page.keyboard.press("Enter")

# Wait for element
page.get_by_role("button").wait_for(timeout=5000)
```

## Assertions and Waiting

```python
from qapytest import soft_assert

# Check if element is visible
soft_assert(page.get_by_role("button").is_visible(), "Button is visible")

# Check if element is enabled
soft_assert(page.get_by_role("button").is_enabled(), "Button is enabled")

# Check text content
heading = page.get_by_role("heading").text_content()
soft_assert(heading == "Welcome", f"Heading is: {heading}")

# Wait for navigation
page.wait_for_url("**/dashboard")

# Wait for function
page.wait_for_function("() => document.readyState === 'complete'")

# Wait for element
page.wait_for_selector("//button[@class='submit']")

# Wait for element to disappear
page.get_by_text("Loading...").wait_for(state="hidden")
```

## Screenshots and Debugging

```python
from qapytest import attach

def test_with_screenshots(page):
    page.goto("http://example.com")
    
    # Take screenshot
    screenshot = page.screenshot()
    attach(screenshot, "page_screenshot.png", mime="image/png")
    
    # Take screenshot of specific element
    element = page.get_by_role("button")
    element_screenshot = element.screenshot()
    attach(element_screenshot, "button_screenshot.png", mime="image/png")
    
    # Get page content
    content = page.content()
    attach(content, "page_html.html", mime="text/html")
```

## CLI Options for Browser Testing

When running tests with Playwright, use these CLI options:

```bash
# Run with specific browser
pytest --browser chromium --report-html
pytest --browser firefox --report-html
pytest --browser webkit --report-html

# Run in headed mode (show browser window)
pytest --browser chromium --headed --report-html

# Run with specific device emulation
pytest --device "iPhone 12" --report-html

# Record videos
pytest --video retain-on-failure --report-html

# Capture screenshots
pytest --screenshot only-on-failure --report-html

# Collect traces for debugging
pytest --tracing retain-on-failure --report-html

# Slow down execution (useful for debugging)
pytest --slowmo 1000 --headed --report-html

# Save test artifacts to directory
pytest --output test-artifacts --report-html
```

## Complete Example with Multiple Browsers

```python
import pytest
from qapytest import step, soft_assert, attach, Faker

@pytest.mark.parametrize("browser_name", ["chromium", "firefox", "webkit"])
def test_multi_browser(browser_name, page):
    """Test that runs on multiple browsers."""
    fake = Faker()
    
    with step(f"Test on {browser_name}"):
        page.goto("http://example.com")
        
        # Interact with page
        page.get_by_label("Username").fill(fake.user_name())
        page.get_by_label("Password").fill(fake.password())
        page.get_by_role("button", name="Sign in").click()
        
        # Wait for result
        page.wait_for_url("**/dashboard")
        
        # Verify and screenshot
        title = page.title()
        soft_assert(title is not None, f"Page title: {title}")
        
        attach(page.screenshot(), f"dashboard_{browser_name}.png", mime="image/png")
```

## Mobile Device Emulation

```python
def test_mobile_app(page):
    """Test mobile version."""
    # Page fixture already configured with device if --device was used
    page.goto("http://example.com")
    
    # Use viewport info
    size = page.viewportSize
    print(f"Viewport: {size['width']}x{size['height']}")
```

## Debugging Tips

### Use headed mode for interactive debugging

```bash
pytest --headed --slowmo 1000 -s
```

### Enable trace recording to inspect failures

```bash
pytest --tracing retain-on-failure
```

### View trace in Playwright Inspector

```bash
playwright show-trace trace.zip
```

### Use page.pause() for step-by-step debugging

```python
def test_with_pause(page):
    page.goto("http://example.com")
    page.pause()  # Browser will pause here, use Playwright Inspector
    page.get_by_role("button").click()
```

## Performance Considerations

- **Parallel execution**: Run tests in parallel for faster results
  ```bash
  pytest -n auto --report-html
  ```

- **Headless mode** (default): Faster execution, no visual overhead

- **Limit artifacts**: Control screenshot and video recording
  ```bash
  pytest --screenshot only-on-failure --video off
  ```

## Troubleshooting

### Browsers not installed

If you get errors about missing browsers:

```bash
playwright install
```

### Test timeout issues

Increase timeout for slow operations:

```python
page.goto("http://example.com", timeout=30000)  # 30 seconds
page.wait_for_selector("//button", timeout=10000)  # 10 seconds
```

### Flaky tests (intermittent failures)

- Use explicit waits instead of fixed delays
- Use `wait_for_*` methods instead of `page.wait_for_timeout(1000)`
- Make selectors more robust (prefer `get_by_role` or `data-testid`)

### Element not found errors

- Use `page.pause()` to inspect the page in Playwright Inspector
- Check if element is in iframe or different frame
- Verify selector is correct with Playwright Inspector

```bash
playwright codegen http://example.com  # Interactive mode for generating selectors
```

## Further Resources

- [Pytest-Playwright Documentation](https://playwright.dev/python/docs/intro)
- [Playwright Python API Reference](https://playwright.dev/python/docs/api/class-playwright)
