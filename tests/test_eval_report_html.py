"""Behavior tests for the public API of eval_report_html."""

from __future__ import annotations

import pytest

import eval_report_html


def test_normalize_trims_and_lowercases() -> None:
    assert eval_report_html.normalize("  Hello World ") == "hello world"


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_normalize_rejects_blank_input(value: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        eval_report_html.normalize(value)


def test_version_is_semver() -> None:
    parts = eval_report_html.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
