"""Render evaluation runs as one self-contained static HTML document."""

from __future__ import annotations

import html
import logging
from collections.abc import Mapping, Sequence

from .errors import ReportError
from .models import MAX_STRING_CHARS, CaseRow, Run
from .svg import trend_svg

logger = logging.getLogger(__name__)

MAX_RUNS = 10_000

_UP = "\u25b2"
_DOWN = "\u25bc"
_EQUAL = "="
_ELLIPSIS = "\u2026"
_ZERO_DELTA = format(0.0, "+.4f")
_POLICY = "default-src 'none'; style-src 'unsafe-inline'"
_CSP_META = f'<meta http-equiv="Content-Security-Policy" content="{_POLICY}">'
_CASE_HEADER = "<tr><th>Case</th><th>Result</th><th>Scores</th><th>Output</th></tr>"
_CSS = (
    "body{font-family:system-ui,sans-serif;margin:2rem;color:#1a1a1a;background:#fff}"
    "table{border-collapse:collapse;margin:1rem 0}"
    "th,td{border:1px solid #ccc;padding:.3rem .6rem;text-align:left;vertical-align:top}"
    "pre{margin:0;white-space:pre-wrap;overflow-wrap:anywhere;max-width:60rem}"
    ".better,.pass{color:#0a6b2d}.worse,.fail{color:#b00020}.same{color:#555}"
    "figure{margin:1rem 0}svg{border:1px solid #ddd;color:#245}text{font-size:10px;fill:#333}"
)


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _num(value: float) -> str:
    return format(value, ".4f")


def _cut(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + _ELLIPSIS


def _delta_cell(
    name: str,
    current: float,
    previous: Mapping[str, float] | None,
    lower_is_better: frozenset[str],
) -> str:
    if previous is None or name not in previous:
        return '<td class="same">n/a</td>'
    delta = current - previous[name]
    if delta == 0:
        return f'<td class="same">{_EQUAL} {_ZERO_DELTA}</td>'
    arrow = _UP if delta > 0 else _DOWN
    improved = (delta > 0) != (name in lower_is_better)
    css = "better" if improved else "worse"
    shown = format(delta, "+.4f")
    return f'<td class="{css}">{arrow} {shown}</td>'


def _summary_table(
    latest: Run,
    previous: Run | None,
    lower_is_better: frozenset[str],
) -> list[str]:
    if not latest.metrics:
        return ["<p>No metrics in the latest run.</p>"]
    before = previous.metrics if previous is not None else None
    lines = [
        "<table>",
        "<tr><th>Metric</th><th>Value</th><th>Change vs previous run</th></tr>",
    ]
    for name in sorted(latest.metrics):
        value = latest.metrics[name]
        delta = _delta_cell(name, value, before, lower_is_better)
        lines.append(f"<tr><td>{_esc(name)}</td><td>{_num(value)}</td>{delta}</tr>")
    lines.append("</table>")
    return lines


def _trends(ordered: Sequence[Run]) -> list[str]:
    if len(ordered) == 1:
        return ["<p>single run: no trend</p>"]
    names = sorted({name for run in ordered for name in run.metrics})
    if not names:
        return ["<p>No metrics.</p>"]
    lines: list[str] = []
    for name in names:
        values: list[float | None] = [run.metrics.get(name) for run in ordered]
        figure = f"<figure><figcaption>{_esc(name)}</figcaption>{trend_svg(values)}</figure>"
        lines.append(figure)
    return lines


def _case_row(case: CaseRow, max_output_chars: int) -> str:
    label = "pass" if case.passed else "fail"
    items = [f"{_esc(n)}: {_num(case.scores[n])}" for n in sorted(case.scores)]
    scores = "<br>".join(items)
    output = _esc(_cut(case.output, max_output_chars))
    cells = [
        f"<td>{_esc(case.id)}</td>",
        f'<td class="{label}">{label}</td>',
        f"<td>{scores}</td>",
        f"<td><pre>{output}</pre></td>",
    ]
    return "<tr>" + "".join(cells) + "</tr>"


def _cases_section(latest: Run, max_cases: int, max_output_chars: int) -> list[str]:
    if not latest.cases:
        return ["<p>No cases in the latest run.</p>"]
    ordered = sorted(latest.cases, key=lambda case: case.id)
    shown = ordered[:max_cases]
    lines = ["<table>", _CASE_HEADER]
    lines.extend(_case_row(case, max_output_chars) for case in shown)
    lines.append("</table>")
    hidden = len(ordered) - len(shown)
    if hidden:
        lines.append(f"<p>{hidden} more cases not shown</p>")
    return lines


def render_report(
    runs: Sequence[Run],
    title: str = "Evaluation report",
    lower_is_better: frozenset[str] = frozenset(),
    max_cases: int = 500,
    max_output_chars: int = 2000,
) -> str:
    """Render ``runs`` as one static HTML page without any JavaScript.

    The page has a header, a summary of the latest run with the change against the
    previous run, one inline SVG trend per metric and a per-case table of the latest run.
    Every input string is escaped with ``html.escape(s, quote=True)``, the first element
    of ``<head>`` is a Content-Security-Policy meta tag, and the output contains no
    timestamp, so equal inputs give byte-identical HTML.

    Args:
        runs: The runs to report (sorted by ``(created, run_id)`` internally).
        title: Page title.
        lower_is_better: Metric names for which a decrease is an improvement.
        max_cases: Largest number of case rows shown.
        max_output_chars: Case outputs are cut to this many characters plus U+2026.

    Raises:
        ReportError: ``input_invalid`` for no runs or a too long title,
            ``input_too_large`` for more than 10000 runs, ``usage`` for negative limits.
    """
    if not runs:
        raise ReportError("input_invalid", "no runs to report")
    if len(runs) > MAX_RUNS:
        raise ReportError("input_too_large", f"more than {MAX_RUNS} runs")
    if max_cases < 0 or max_output_chars < 0:
        raise ReportError("usage", "max_cases and max_output_chars must not be negative")
    if len(title) > MAX_STRING_CHARS:
        raise ReportError("input_invalid", "title is too long")
    ordered = sorted(runs, key=lambda run: (run.created, run.run_id))
    latest = ordered[-1]
    previous = ordered[-2] if len(ordered) > 1 else None
    count = len(ordered)
    plural = "run" if count == 1 else "runs"
    passed = sum(1 for case in latest.cases if case.passed)
    summary = (
        f"{count} {plural}; latest run {latest.run_id} created {latest.created.isoformat()}; "
        f"{passed} of {len(latest.cases)} cases passed"
    )
    head = (
        f"<head>{_CSP_META}"
        '<meta charset="utf-8">'
        f"<title>{_esc(title)}</title>"
        f"<style>{_CSS}</style></head>"
    )
    lines = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        head,
        "<body>",
        f"<h1>{_esc(title)}</h1>",
        f"<p>{_esc(summary)}</p>",
        "<h2>Summary</h2>",
        *_summary_table(latest, previous, lower_is_better),
        "<h2>Trends</h2>",
        *_trends(ordered),
        "<h2>Cases</h2>",
        *_cases_section(latest, max_cases, max_output_chars),
        "</body>",
        "</html>",
        "",
    ]
    logger.debug("rendered report for %d runs", count)
    return "\n".join(lines)
