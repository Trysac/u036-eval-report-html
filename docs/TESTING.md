# Testing

## Running

```sh
uv run pytest --cov=eval_report_html   # tests with coverage report
```

## Policy

- Tests exercise the public API (`import eval_report_html`) and the command line entry point.
- Tests are deterministic: they use fixed inputs and no network.

## Layout

The test files are not present in the reviewed material, so no test file names are listed here. The files are expected to cover loading, rendering, SVG output and the command line, as described in the acceptance criteria of the specification.
