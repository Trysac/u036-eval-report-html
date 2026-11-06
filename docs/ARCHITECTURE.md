# Architecture

## Purpose

`trysac-eval-report-html` is a small, dependency-free Python package (import name `eval_report_html`) that reads evaluation result JSON files from a folder and renders one static HTML page with a latest-run summary, per-metric SVG trends and a per-case table.

## Shape

```text
caller code / CLI (__main__.py)
        |
        +-- loader.load_runs   reads *.json files, validates, returns Run objects
        +-- report.render_report  builds the HTML string
                |
                +-- svg.trend_svg  builds inline SVG per metric
```

- **Public API**: the names in `__all__` of `src/eval_report_html/__init__.py`: `CaseRow`, `ReportError`, `Run`, `__version__`, `load_runs`, `render_report`, `trend_svg`.
- **Models**: `models.py` defines the frozen dataclasses `CaseRow` and `Run`.
- **Errors**: `errors.py` defines `ReportError(code, message, path=None)`; messages are cut to 80 characters of reason and 118 characters of path.
- **Side effects**: `load_runs` reads files; the CLI writes the output through a temporary file in the target folder followed by `os.replace`. `render_report` and `trend_svg` are pure.
- **Logging**: a logger named after the package with a `NullHandler`.

## Decisions

No architecture decision records exist in the reviewed files.
