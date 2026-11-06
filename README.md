# eval-report-html

[![PyPI version](https://img.shields.io/pypi/v/trysac-eval-report-html)](https://pypi.org/project/trysac-eval-report-html/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-eval-report-html)](LICENSE)
[![CI](https://github.com/Trysac/u036-eval-report-html/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u036-eval-report-html/actions/workflows/ci.yml)

Generate one self-contained, script-free static HTML report from evaluation result JSON files, with per-run tables and SVG trend lines.

## Problem

Evaluation results end up as JSON files in CI artifacts that nobody opens, and trends across runs are invisible. Dashboards need servers and accounts. This CLI turns a folder of result files into one offline HTML file with a summary, a per-case table and inline SVG trend lines, safe to open even when outputs contain hostile text (strict CSP, no JavaScript, everything escaped).

## Install

```sh
pip install trysac-eval-report-html
# or
uv add trysac-eval-report-html
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
from pathlib import Path
from eval_report_html import load_runs, render_report

runs = load_runs(Path("results"))
html = render_report(runs, lower_is_better=frozenset({"latency"}))
Path("report.html").write_text(html, encoding="utf-8")
```

Command line:

```sh
eval-report build FOLDER -o report.html [--title T] [--lower-is-better METRIC]... [--max-cases N]
```

Public API: `load_runs(folder, max_file_bytes=10_000_000, max_files=1000)` returns runs sorted by `(created, run_id)`; `render_report(runs, title, lower_is_better, max_cases=500, max_output_chars=2000)` returns the HTML string; `trend_svg(values, width=320, height=80)` returns an inline SVG; `CaseRow` and `Run` are frozen dataclasses; `ReportError` carries `code` (`input_invalid`, `input_too_large`, `usage`) and `path`.

Input: every `*.json` directly in FOLDER (no recursion, symbolic links skipped), one run per file:

```json
{
  "run_id": "run-1",
  "created": "2026-01-01T10:00:00+00:00",
  "metrics": {"accuracy": 0.8, "latency": 120},
  "cases": [{"id": "c1", "passed": true, "scores": {"accuracy": 1.0}, "output": "text"}]
}
```

Limits: `created` must carry a UTC offset; NaN and Infinity, boolean numbers, duplicate object keys, duplicate case ids, strings over 100000 characters and files above `max_file_bytes` are rejected. Integers beyond 2**53 lose precision because numbers are converted with `float()`. A report holds at most 10000 runs, and a trend at most 10000 values.

Exit codes: `0` report written; `2` input or usage error (an empty folder is an input error; an existing output file is left untouched).

## Why not Grafana or a notebook?

The specification does not name a best-known alternative, so this section is omitted.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
