# eval-report-html

[![PyPI version](https://img.shields.io/pypi/v/trysac-eval-report-html)](https://pypi.org/project/trysac-eval-report-html/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-eval-report-html)](LICENSE)
[![CI](https://github.com/Trysac/u036-eval-report-html/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u036-eval-report-html/actions/workflows/ci.yml)

Generate one self-contained, script-free static HTML report from evaluation result JSON files, with per-run tables and SVG trend lines

## Problem

Evaluation results end up as JSON files in CI artifacts that nobody opens, and trends across runs are
invisible. Dashboards need servers and accounts. This CLI turns a folder of result files into one offline
HTML file with a summary, a per-case table and inline SVG trend lines, safe to open even when outputs
contain hostile text (strict CSP, no JavaScript, everything escaped).

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

Input: every `*.json` directly in FOLDER (no recursion), one run per file:

```json
{
  "run_id": "run-1",
  "created": "2026-01-01T10:00:00+00:00",
  "metrics": {"accuracy": 0.8, "latency": 120},
  "cases": [{"id": "c1", "passed": true, "scores": {"accuracy": 1.0}, "output": "text"}]
}
```

`created` must carry a UTC offset. NaN/Infinity, boolean metrics, duplicate case ids and oversized files are
rejected with `ReportError`.

Exit codes: `0` report written; `2` input or usage error (the output file is left untouched).

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
