# Run Parameters

QaPyTest adds a set of useful CLI options to `pytest` for generating an HTML
report and controlling the behavior of loading environment variables from
a `.env` file. When browser automation is used, additional Playwright options
become available.

Below are the available options, their purpose, and usage examples.

## CLI options

### QaPyTest Options

- **`--env-file [PATH]`** : path to a `.env` file with environment variables
  (by default it will try to load `./.env` if it exists).
- **`--env-override`** : if set, values from `.env` will override existing
  environment variables.
- **`--report-json [PATH]`** : create a JSON report with test results; optionally
  specify a path (default — `./report.json`).
- **`--report-html [PATH]`** : create a self-contained HTML report; optionally
  specify a path (default — `./report.html`).
- **`--report-title NAME`** : set the HTML report title (default — "QAPyTest
  Report").
- **`--report-theme {light,dark,auto}`** : set the report theme: `light`,
  `dark`, or `auto` (default).
- **`--max-attachment-bytes N`** : maximum attachment size (in bytes) to embed
  in the HTML; larger files will be truncated (default is unlimited).
- **`--disable-unicode`** : disable Unicode character display in 
  terminal output for compatibility with older terminals or CI systems.

## Behavior with `.env`

- If the `--env-file` option is not provided, the plugin will try to load
  `.env` in the working directory.
- If `--env-file=PATH` is specified, the plugin will load variables from that
  file.
- If `--env-override` is set, values from `.env` will overwrite existing
  environment variables. Otherwise existing values are preserved and `.env`
  only supplements missing ones.

The `.env` format is plain: `KEY=VALUE`. Comments and empty lines are ignored.

### Usage examples (env)

```bash
pytest --env-file
# or
pytest --env-file=tests/.env
# or
pytest --env-file=.env --env-override
```

## Unicode display in terminal

By default, QaPyTest displays Unicode characters (Cyrillic, Arabic, Chinese, etc.) 
correctly in terminal output for test names with parametrized IDs. If you 
experience issues with Unicode display in older terminals or CI systems, 
you can disable this feature:

```bash
# Disable Unicode character display in terminal
pytest --disable-unicode --report-html

# Normal run with Unicode support (default)
pytest --report-html
```

## Playwright Options (when using browser automation)

For browser automation testing, install Playwright browsers:

```bash
playwright install
```

This command downloads the browser binaries needed for automated testing.

QaPyTest includes pytest-playwright, which adds these additional CLI options:

- **`--browser {chromium,firefox,webkit}`** : browser to use for tests
  (default: chromium).
- **`--headed`** : run tests in headed mode (show browser window).
- **`--browser-channel CHANNEL`** : browser channel to use (chrome, msedge, etc.).
- **`--slowmo MILLISECONDS`** : slow down operations by the specified amount
  of milliseconds.
- **`--device DEVICE`** : device name to emulate.
- **`--video {on,off,retain-on-failure}`** : record videos for tests.
- **`--screenshot {on,off,only-on-failure}`** : capture screenshots.
- **`--full-page-screenshot`** : capture full page screenshots.
- **`--tracing {on,off,retain-on-failure}`** : record traces for tests.
- **`--output DIR`** : directory for test output (videos, screenshots, traces).

### Browser automation examples

```bash
# Run browser tests with default browser (chromium)
pytest --browser chromium --report-html

# Run tests in headed mode for debugging
pytest --browser firefox --headed --report-html

# Run tests with WebKit (Safari engine)
pytest --browser webkit --report-html
```

## JSON report generation behavior

The plugin collects test execution logs and, if `--report-json` is specified,
produces a JSON file with all test results, metrics, execution logs, and attachments.
This is useful for programmatic processing, CI/CD integration, or feeding data
into custom dashboards and analysis tools.

### JSON report structure

The JSON report contains:
- **session metadata**: start and finish timestamps
- **stats**: aggregated statistics (total tests, pass rate, failed/passed counts, duration)
- **results**: detailed information for each test including outcome, duration, execution logs, steps, and attachments

### Example JSON report

```json
{
  "session_start": "2025-12-13T07:52:08.659266",
  "session_finish": "2025-12-13T07:52:08.724639",
  "stats": {
    "total": 3,
    "duration_total": 0.025369666051119566,
    "pass_rate": 66.66666666666666,
    "failed": 1,
    "passed": 2
  },
  "results": [
    {
      "nodeid": "test_example.py::test_sample[1]",
      "path": "test_example.py",
      "lineno": 5,
      "outcome": "failed",
      "duration": 0.024913958040997386,
      "title": "Sample test",
      "components": ["smoke"],
      "details": {
        "headline": "One or more assertions failed",
        "longrepr": "One or more assertions failed.\n\t✖︎ Check failed [Value = 1]"
      },
      "execution_log": [
        {
          "type": "step",
          "message": "Verify value",
          "passed": false,
          "children": [
            {
              "type": "assert",
              "label": "Value check",
              "passed": false,
              "details": "Expected 2, got 1"
            }
          ]
        }
      ],
      "attachments": [
        {
          "type": "attachment",
          "label": "Screenshot",
          "data": "base64_encoded_data...",
          "content_type": "image/png"
        }
      ]
    }
  ]
}
```

### Usage examples (json)

- Simple run and create a JSON report:

```bash
pytest --report-json
```

- Specify a custom path for the JSON report:

```bash
pytest --report-json=reports/run1.json
```

## HTML report generation behavior

The plugin collects test execution logs and, if `--report-html` is specified,
produces a self-contained HTML file with all results, logs, and attachments.

### Usage examples (html)

- Simple run and create a report named `report.html`:

```bash
pytest --report-html
```

- Specify the report path and title:

```bash
pytest --report-html=reports/run1.html --report-title="Nightly run"
```

- Limit attachment size to avoid embedding very large files into the HTML:

```bash
pytest --report-html --max-attachment-bytes=50000
```

- Use all options together with a custom theme:

```bash
pytest --env-file=.env.test --env-override \
       --report-html=reports/full-run.html \
       --report-title="Integration Tests" \
       --report-theme=dark \
       --max-attachment-bytes=100000
```

## Additional notes

- Plugin options are added to the `QaPyTest` group in the `pytest --help`
  output.
- Some features (`attach`, `step`) work fully only during test execution, when
  the internal logging context is active (configured by the plugin during
  `runtest`).
- **Logging in reports**: to show logs in the HTML report and console use:
  - `--log-level=INFO` — to show logs in the report and console for failed
    tests
  - `--log-cli-level=INFO` — to show logs in the report and console during
    execution of all tests
  - Recommended level: `INFO` or `DEBUG` for detailed client operation logging

### Complete example with all features

```bash
pytest --env-file=.env \
       --browser chromium \
       --headed \
       --video retain-on-failure \
       --screenshot only-on-failure \
       --tracing retain-on-failure \
       --output test-results \
       --report-html=reports/browser-tests.html \
       --report-title="Browser Automation Tests" \
       --report-theme=auto \
       --log-level=INFO
```
