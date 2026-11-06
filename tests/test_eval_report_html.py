"""Package level tests: public API, errors and logging."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import eval_report_html
from eval_report_html import ReportError, load_runs, render_report


def test_public_api_and_version() -> None:
    assert eval_report_html.__version__ == "0.1.0"
    for name in eval_report_html.__all__:
        assert hasattr(eval_report_html, name)


def test_package_logger_has_null_handler() -> None:
    handlers = logging.getLogger("eval_report_html").handlers
    assert any(isinstance(handler, logging.NullHandler) for handler in handlers)


def test_error_message_is_capped_and_keeps_attributes() -> None:
    error = ReportError("usage", "m" * 1000, "p" * 1000)
    assert len(str(error)) <= 200
    assert error.code == "usage"
    assert error.path == "p" * 1000


def test_error_without_path_is_the_plain_message() -> None:
    error = ReportError("input_invalid", "boom")
    assert str(error) == "boom"
    assert error.path is None


def test_error_keeps_the_end_of_a_long_path() -> None:
    error = ReportError("input_invalid", "bad", "/" + "d" * 500 + "/bad.json")
    assert str(error).endswith("/bad.json")
    assert len(str(error)) <= 200


def test_readme_style_usage(tmp_path: Path) -> None:
    doc = {
        "run_id": "nightly",
        "created": "2026-01-01T10:00:00+00:00",
        "metrics": {"accuracy": 0.9},
        "cases": [{"id": "c1", "passed": True, "scores": {"f1": 1}, "output": "ok"}],
    }
    (tmp_path / "run.json").write_text(json.dumps(doc), encoding="utf-8")
    html = render_report(load_runs(tmp_path), title="Nightly")
    assert "<title>Nightly</title>" in html
    assert "0.9000" in html
