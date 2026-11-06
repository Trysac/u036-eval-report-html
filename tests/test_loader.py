"""Tests for load_runs."""

from __future__ import annotations

import json
import os
from dataclasses import FrozenInstanceError
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

from eval_report_html import CaseRow, ReportError, Run, load_runs

CREATED = "2026-01-01T10:00:00+00:00"


def make_doc(
    run_id: str = "r1",
    created: Any = CREATED,
    metrics: Any = None,
    cases: Any = None,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "created": created,
        "metrics": {"accuracy": 0.8} if metrics is None else metrics,
        "cases": [] if cases is None else cases,
    }


def write_doc(folder: Path, name: str, doc: Any) -> Path:
    path = folder / name
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def metrics_with(raw: str) -> str:
    return json.dumps(make_doc(metrics={"a": "VALUE"})).replace('"VALUE"', raw)


def test_sorted_by_aware_created_then_run_id(tmp_path: Path) -> None:
    write_doc(tmp_path, "a.json", make_doc(run_id="a", created="2026-01-01T09:00:00+00:00"))
    write_doc(tmp_path, "b.json", make_doc(run_id="b", created="2026-01-01T10:00:00+02:00"))
    assert [run.run_id for run in load_runs(tmp_path)] == ["b", "a"]


def test_ties_are_broken_by_run_id(tmp_path: Path) -> None:
    write_doc(tmp_path, "1.json", make_doc(run_id="z"))
    write_doc(tmp_path, "2.json", make_doc(run_id="a"))
    assert [run.run_id for run in load_runs(tmp_path)] == ["a", "z"]


def test_fields_are_parsed_and_numbers_become_floats(tmp_path: Path) -> None:
    case = {"id": "c1", "passed": True, "scores": {"f1": 1}, "output": "ok"}
    doc = make_doc(metrics={"accuracy": 1, "latency": 0.5}, cases=[case])
    write_doc(tmp_path, "one.json", doc)
    (run,) = load_runs(tmp_path)
    assert isinstance(run, Run)
    assert run.metrics == {"accuracy": 1.0, "latency": 0.5}
    assert isinstance(run.metrics["accuracy"], float)
    assert run.cases == (CaseRow(id="c1", passed=True, scores={"f1": 1.0}, output="ok"),)


def test_z_suffix_is_utc(tmp_path: Path) -> None:
    write_doc(tmp_path, "z.json", make_doc(created="2026-01-01T10:00:00Z"))
    (run,) = load_runs(tmp_path)
    assert run.created.utcoffset() == timedelta(0)


def test_models_are_frozen(tmp_path: Path) -> None:
    write_doc(tmp_path, "one.json", make_doc())
    (run,) = load_runs(tmp_path)
    with pytest.raises(FrozenInstanceError):
        run.run_id = "other"


def test_no_recursion_and_only_json_files(tmp_path: Path) -> None:
    write_doc(tmp_path, "real.json", make_doc(run_id="real"))
    (tmp_path / "notes.txt").write_text("{}", encoding="utf-8")
    (tmp_path / "dir.json").mkdir()
    sub = tmp_path / "sub"
    sub.mkdir()
    write_doc(sub, "nested.json", make_doc(run_id="nested"))
    assert [run.run_id for run in load_runs(tmp_path)] == ["real"]


def test_symlinks_are_skipped(tmp_path: Path) -> None:
    folder = tmp_path / "in"
    outside = tmp_path / "outside"
    folder.mkdir()
    outside.mkdir()
    write_doc(folder, "real.json", make_doc(run_id="real"))
    target = write_doc(outside, "target.json", make_doc(run_id="linked"))
    try:
        os.symlink(target, folder / "link.json")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available")
    assert [run.run_id for run in load_runs(folder)] == ["real"]


def test_empty_folder_gives_no_runs(tmp_path: Path) -> None:
    assert load_runs(tmp_path) == []


@pytest.mark.parametrize(
    "payload",
    [
        "{not json",
        "",
        metrics_with("NaN"),
        metrics_with("Infinity"),
        metrics_with("-Infinity"),
        metrics_with("1e999"),
        metrics_with("true"),
        metrics_with('"0.5"'),
        metrics_with("null"),
        json.dumps(make_doc(created="2026-01-01T10:00:00")),
        json.dumps(make_doc(created="not-a-date")),
        json.dumps(make_doc(created="2026-01-01")),
        json.dumps(make_doc(created=5)),
        json.dumps(
            make_doc(
                cases=[
                    {"id": "c", "passed": True, "scores": {}, "output": ""},
                    {"id": "c", "passed": False, "scores": {}, "output": ""},
                ]
            )
        ),
        '{"run_id": "a", "run_id": "b"}',
        "[]",
        '"text"',
        json.dumps({"run_id": "r"}),
        json.dumps(make_doc(run_id=5)),
        json.dumps(make_doc(metrics=[])),
        json.dumps(make_doc(cases={})),
        json.dumps(make_doc(cases=[1])),
        json.dumps(make_doc(cases=[{"id": "c", "passed": "yes", "scores": {}, "output": ""}])),
        json.dumps(make_doc(cases=[{"id": 1, "passed": True, "scores": {}, "output": ""}])),
        json.dumps(make_doc(cases=[{"id": "c", "passed": True, "scores": {"s": "x"}, "output": ""}])),
        json.dumps(make_doc(cases=[{"id": "c", "passed": True, "scores": {}, "output": 3}])),
        json.dumps(make_doc(cases=[{"id": "c", "passed": True, "scores": {}}])),
        json.dumps(make_doc(run_id="x" * 100_001)),
        "[" * 100_000,
        b"\xff\xfe not utf-8",
    ],
)
def test_invalid_documents_name_the_path(tmp_path: Path, payload: str | bytes) -> None:
    data = payload.encode("utf-8") if isinstance(payload, str) else payload
    path = tmp_path / "bad.json"
    path.write_bytes(data)
    with pytest.raises(ReportError) as info:
        load_runs(tmp_path)
    assert info.value.code == "input_invalid"
    assert "bad.json" in str(info.value)
    assert info.value.path == str(path)


def test_string_at_the_limit_is_accepted(tmp_path: Path) -> None:
    write_doc(tmp_path, "long.json", make_doc(run_id="x" * 100_000))
    assert len(load_runs(tmp_path)[0].run_id) == 100_000


def test_error_message_stays_short_for_huge_names(tmp_path: Path) -> None:
    write_doc(tmp_path, "bad.json", make_doc(metrics={"k" * 50_000: True}))
    with pytest.raises(ReportError) as info:
        load_runs(tmp_path)
    assert len(str(info.value)) <= 200


def test_file_over_limit_is_too_large(tmp_path: Path) -> None:
    (tmp_path / "big.json").write_bytes(b" " * 101)
    with pytest.raises(ReportError) as info:
        load_runs(tmp_path, max_file_bytes=100)
    assert info.value.code == "input_too_large"
    assert "big.json" in str(info.value)


def test_file_exactly_at_limit_is_accepted(tmp_path: Path) -> None:
    body = json.dumps(make_doc()).encode("utf-8")
    (tmp_path / "ok.json").write_bytes(body + b" " * (500 - len(body)))
    assert len(load_runs(tmp_path, max_file_bytes=500)) == 1
    with pytest.raises(ReportError) as info:
        load_runs(tmp_path, max_file_bytes=499)
    assert info.value.code == "input_too_large"


def test_too_many_files_is_invalid(tmp_path: Path) -> None:
    for name in ("a.json", "b.json", "c.json"):
        write_doc(tmp_path, name, make_doc(run_id=name))
    assert len(load_runs(tmp_path, max_files=3)) == 3
    with pytest.raises(ReportError) as info:
        load_runs(tmp_path, max_files=2)
    assert info.value.code == "input_invalid"


@pytest.mark.parametrize(
    ("max_file_bytes", "max_files"),
    [(0, 10), (10, 0), (-1, 10)],
)
def test_non_positive_limits_are_usage_errors(
    tmp_path: Path, max_file_bytes: int, max_files: int
) -> None:
    with pytest.raises(ReportError) as info:
        load_runs(tmp_path, max_file_bytes=max_file_bytes, max_files=max_files)
    assert info.value.code == "usage"


def test_missing_folder_and_file_instead_of_folder(tmp_path: Path) -> None:
    with pytest.raises(ReportError) as missing:
        load_runs(tmp_path / "nope")
    assert missing.value.code == "input_invalid"
    file_path = write_doc(tmp_path, "x.json", make_doc())
    with pytest.raises(ReportError) as not_dir:
        load_runs(file_path)
    assert not_dir.value.code == "input_invalid"
