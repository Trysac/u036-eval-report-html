# eval-report-html

[![PyPI version](https://img.shields.io/pypi/v/trysac-eval-report-html)](https://pypi.org/project/trysac-eval-report-html/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-eval-report-html)](LICENSE)
[![CI](https://github.com/Trysac/u036-eval-report-html/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u036-eval-report-html/actions/workflows/ci.yml)

Generate one self-contained, script-free static HTML report from evaluation result JSON files, with per-run tables and SVG trend lines

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-eval-report-html
# or
uv add trysac-eval-report-html
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import eval_report_html

# normalize() trims surrounding whitespace and lower-cases the text.
print(eval_report_html.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    eval_report_html.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
