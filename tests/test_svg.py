"""Tests for trend_svg."""

from __future__ import annotations

import pytest

from eval_report_html import ReportError, trend_svg


def test_gap_splits_runs_and_draws_a_lone_point() -> None:
    svg = trend_svg([0.5, None, 0.7, 0.9])
    assert '<circle cx="4.00" cy="76.00"' in svg
    assert '<polyline points="212.00,40.00 316.00,4.00"' in svg
    assert svg.count("<polyline") == 1
    assert svg.count("<circle") == 1


def test_flat_series_is_drawn_at_mid_height() -> None:
    svg = trend_svg([0.3, 0.3])
    assert '<polyline points="4.00,40.00 316.00,40.00"' in svg
    assert svg.count("<polyline") == 1
    assert 'y="40.00"' not in svg or "40.00" in svg


def test_single_value_is_centered() -> None:
    svg = trend_svg([2.0])
    assert '<circle cx="160.00" cy="40.00"' in svg
    assert "<polyline" not in svg


def test_custom_size_and_integer_values() -> None:
    svg = trend_svg([0, 10], width=108, height=58)
    assert svg.startswith('<svg width="108" height="58" viewBox="0 0 108 58"')
    assert 'points="4.00,54.00 104.00,4.00"' in svg


def test_min_and_max_labels() -> None:
    svg = trend_svg([0.5, None, 0.7, 0.9])
    assert "max 0.9000" in svg
    assert "min 0.5000" in svg


def test_no_namespace_links_or_scripts() -> None:
    svg = trend_svg([1.0, 2.0, 3.0])
    for needle in ("xmlns", "http", "<script", "href", "onload"):
        assert needle not in svg


def test_multiple_runs_and_lone_points() -> None:
    assert trend_svg([1.0, 2.0, None, 3.0, 4.0]).count("<polyline") == 2
    lone = trend_svg([1.0, None, 2.0, None, 3.0])
    assert lone.count("<circle") == 3
    assert "<polyline" not in lone


@pytest.mark.parametrize("values", [[], [None], [None, None]])
def test_nothing_to_draw(values: list[None]) -> None:
    svg = trend_svg(values)
    for needle in ("<polyline", "<circle", "<text"):
        assert needle not in svg
    assert svg.endswith("</svg>")


def test_output_is_deterministic() -> None:
    assert trend_svg([0.1, 0.4, None, 0.2]) == trend_svg([0.1, 0.4, None, 0.2])


@pytest.mark.parametrize(
    ("width", "height"),
    [(8, 80), (320, 8), (10_001, 80), (320, 10_001), (0, 0)],
)
def test_bad_sizes_are_usage_errors(width: int, height: int) -> None:
    with pytest.raises(ReportError) as info:
        trend_svg([1.0, 2.0], width=width, height=height)
    assert info.value.code == "usage"


@pytest.mark.parametrize(
    "values",
    [
        [float("nan")],
        [float("inf")],
        [True],
        ["x"],
        [10**400],
        [1e308, -1e308],
    ],
)
def test_bad_values_are_invalid(values: list[object]) -> None:
    with pytest.raises(ReportError) as info:
        trend_svg(values)  # type: ignore[arg-type]
    assert info.value.code == "input_invalid"


def test_point_limit() -> None:
    assert trend_svg([None] * 10_000).endswith("</svg>")
    with pytest.raises(ReportError) as info:
        trend_svg([None] * 10_001)
    assert info.value.code == "input_too_large"
