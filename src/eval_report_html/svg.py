"""Inline SVG trend lines."""

from __future__ import annotations

import html
import math
from collections.abc import Sequence

from .errors import ReportError

MAX_POINTS = 10_000
_MAX_SIZE = 10_000
_PAD = 4
_LINE_ATTRS = 'fill="none" stroke="currentColor" stroke-width="1.5"'


def _valid_size(size: int) -> bool:
    return 2 * _PAD < size <= _MAX_SIZE


def _label(text: str) -> str:
    return html.escape(text, quote=True)


def _check(values: Sequence[float | None]) -> list[float | None]:
    checked: list[float | None] = []
    for value in values:
        if value is None:
            checked.append(None)
            continue
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ReportError("input_invalid", "values must be numbers or None")
        try:
            number = float(value)
        except OverflowError as exc:
            raise ReportError("input_invalid", "value is out of range") from exc
        if not math.isfinite(number):
            raise ReportError("input_invalid", "values must be finite")
        checked.append(number)
    return checked


def _segments(
    checked: list[float | None],
    width: int,
    height: int,
    low: float,
    high: float,
) -> list[list[tuple[float, float]]]:
    count = len(checked)
    span = high - low
    inner = height - 2 * _PAD
    segments: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    for index, value in enumerate(checked):
        if value is None:
            if current:
                segments.append(current)
                current = []
            continue
        x = width / 2 if count == 1 else _PAD + index * (width - 2 * _PAD) / (count - 1)
        y = height / 2 if span == 0 else _PAD + (high - value) / span * inner
        current.append((x, y))
    if current:
        segments.append(current)
    return segments


def trend_svg(values: Sequence[float | None], width: int = 320, height: int = 80) -> str:
    """Return an inline ``<svg>`` trend line for ``values``.

    ``None`` entries are gaps. Every contiguous run of two or more values is one
    ``<polyline>``, a lone value is a ``<circle>``, and the minimum and maximum are
    printed as text labels. The element has no namespace attribute, no links and no
    timestamp, so the output is deterministic.

    Raises:
        ReportError: ``usage`` for a bad size, ``input_too_large`` for more than
            10000 values, ``input_invalid`` for non-finite or non-numeric values.
    """
    if not _valid_size(width) or not _valid_size(height):
        raise ReportError("usage", "width and height must be between 9 and 10000")
    if len(values) > MAX_POINTS:
        raise ReportError("input_too_large", f"more than {MAX_POINTS} values")
    checked = _check(values)
    box = f"0 0 {width} {height}"
    parts = [f'<svg width="{width}" height="{height}" viewBox="{box}" role="img">']
    present = [value for value in checked if value is not None]
    if present:
        low, high = min(present), max(present)
        if not math.isfinite(high - low):
            raise ReportError("input_invalid", "value range is too large")
        for segment in _segments(checked, width, height, low, high):
            if len(segment) >= 2:
                points = " ".join(f"{x:.2f},{y:.2f}" for x, y in segment)
                parts.append(f'<polyline points="{points}" {_LINE_ATTRS}/>')
            else:
                x, y = segment[0]
                parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2" fill="currentColor"/>')
        label_x = width - _PAD
        min_y = height - _PAD
        max_text = _label(f"max {format(high, '.4f')}")
        min_text = _label(f"min {format(low, '.4f')}")
        parts.append(f'<text x="{label_x}" y="12" text-anchor="end">{max_text}</text>')
        parts.append(f'<text x="{label_x}" y="{min_y}" text-anchor="end">{min_text}</text>')
    parts.append("</svg>")
    return "".join(parts)
