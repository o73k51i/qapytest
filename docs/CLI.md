# Run Parameters

QaPyTest adds a set of useful CLI options to `pytest` for generating an HTML report and controlling
the behavior of loading environment variables from a `.env` file.

Below are the available options, their purpose, and usage examples.

## CLI options

- **`--env-file [PATH]`** : path to a `.env` file with environment variables (by default it will try to load `./.env` if it exists).
- **`--env-override`** : if set, values from `.env` will override existing environment variables.
- **`--report-html [PATH]`** : create a self-contained HTML report; optionally specify a path (default — `./report.html`).
- **`--report-title NAME`** : set the HTML report title (default — "QAPyTest Report").
- **`--report-theme {light,dark,auto}`** : set the report theme: `light`, `dark`, or `auto` (default).
- **`--max-attachment-bytes N`** : maximum attachment size (in bytes) to embed in the HTML; larger files will be truncated (default is unlimited).

## Behavior with `.env`

- If the `--env-file` option is not provided, the plugin will try to load `.env` in the working directory.
- If `--env-file=PATH` is specified, the plugin will load variables from that file.
- If `--env-override` is set, values from `.env` will overwrite existing environment variables.
  Otherwise existing values are preserved and `.env` only supplements missing ones.

The `.env` format is plain: `KEY=VALUE`. Comments and empty lines are ignored.

### Usage examples

```bash
pytest --env-file
# or
pytest --env-file=tests/.env
# or
pytest --env-file=.env --env-override
```

## HTML report generation behavior

The plugin collects test execution logs and, if `--report-html` is specified, produces
a self-contained HTML file with all results, logs, and attachments.

### Usage examples

1) Simple run and create a report named `report.html`:

```bash
pytest --report-html
```

2) Specify the report path and title:

```bash
pytest --report-html=reports/run1.html --report-title="Nightly run"
```

3) Limit attachment size to avoid embedding very large files into the HTML:

```bash
pytest --report-html --max-attachment-bytes=50000
```

4) Use all options together with a custom theme:

```bash
pytest --env-file=.env.test --env-override \
       --report-html=reports/full-run.html \
       --report-title="Integration Tests" \
       --report-theme=dark \
       --max-attachment-bytes=100000
```

## Additional notes

- Plugin options are added to the `QaPyTest` group in the `pytest --help` output.
- Some features (`attach`, `step`) work fully only during test execution, when the internal logging context is active (configured by the plugin during `runtest`).
- **Logging in reports**: to show logs in the HTML report and console use:
  - `--log-level=INFO` — to show logs in the report and console for failed tests
  - `--log-cli-level=INFO` — to show logs in the report and console during execution of all tests
  - Recommended level: `INFO` or `DEBUG` for detailed client operation logging

### Recommended run

```bash
# Full run with all features
pytest --env-file=.env --report-html=report.html \
       --report-title="Test Run $(date)" \
       --log-level=INFO
```
