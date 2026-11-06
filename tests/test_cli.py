"""Tests for the command line interface."""

from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

from eval_report_html.__main__ import main


def make_case(case_id: str) -> dict[str, Any]:
    return {"id": case_id, "passed": True, "scores": {"f1": 1}, "output": "ok"}


def make_doc(
    run_id: str,
    created: str,
    metrics: dict[str, float],
    cases: list[dict[str, Any]],
) -> str:
    doc = {"run_id": run_id, "created": created, "metrics": metrics, "cases": cases}
    return json.dumps(doc)


def make_folder(tmp_path: Path) -> Path:
    folder = tmp_path / "results"
    folder.mkdir()
    cases = [make_case("c1"), make_case("c2"), make_case("c3")]
    first = {"accuracy": 0.8, "latency": 120}
    second = {"accuracy": 0.85, "latency": 100}
    (folder / "a.json").write_text(
        make_doc("a", "2026-01-01T09:00:00+00:00", first, cases), encoding="utf-8"
    )
    (folder / "b.json").write_text(
        make_doc("b", "2026-01-01T10:00:00+00:00", second, cases), encoding="utf-8"
    )
    return folder


def test_build_writes_the_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    folder = make_folder(tmp_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    target = out_dir / "report.html"
    code = main(["build", str(folder), "-o", str(target), "--title", "T", "--max-cases", "1"])
    assert code == 0
    html = target.read_text(encoding="utf-8")
    assert "<title>T</title>" in html
    assert '<td class="better">▲ +0.0500</td>' in html
    assert '<td class="worse">▼ -20.0000</td>' in html
    assert "2 more cases not shown" in html
    assert [path.name for path in out_dir.iterdir()] == ["report.html"]
    assert "wrote" in capsys.readouterr().out


def test_lower_is_better_option(tmp_path: Path) -> None:
    folder = make_folder(tmp_path)
    target = tmp_path / "report.html"
    args = ["build", str(folder), "-o", str(target), "--lower-is-better", "latency"]
    assert main(args) == 0
    assert '<td class="better">▼ -20.0000</td>' in target.read_text(encoding="utf-8")


def test_invalid_input_leaves_existing_output_untouched(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = make_folder(tmp_path)
    (folder / "bad.json").write_text("{not json", encoding="utf-8")
    target = tmp_path / "report.html"
    target.write_bytes(b"old report")
    assert main(["build", str(folder), "-o", str(target)]) == 2
    assert target.read_bytes() == b"old report"
    err = capsys.readouterr().err
    assert "input_invalid" in err
    assert "bad.json" in err
    assert sorted(path.name for path in tmp_path.iterdir()) == ["report.html", "results"]


def test_oversized_file_exits_two_and_keeps_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = tmp_path / "results"
    folder.mkdir()
    (folder / "big.json").write_bytes(b" " * 10_000_001)
    target = tmp_path / "report.html"
    target.write_bytes(b"old report")
    assert main(["build", str(folder), "-o", str(target)]) == 2
    assert target.read_bytes() == b"old report"
    assert "input_too_large" in capsys.readouterr().err


def test_empty_folder_is_invalid_input(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    folder = tmp_path / "empty"
    folder.mkdir()
    target = tmp_path / "report.html"
    assert main(["build", str(folder), "-o", str(target)]) == 2
    assert not target.exists()
    assert "input_invalid" in capsys.readouterr().err


def test_missing_folder_is_invalid_input(tmp_path: Path) -> None:
    target = tmp_path / "report.html"
    assert main(["build", str(tmp_path / "nope"), "-o", str(target)]) == 2
    assert not target.exists()


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["build"],
        ["build", "folder"],
        ["unknown"],
        ["build", "folder", "-o", "x.html", "--max-cases", "abc"],
    ],
)
def test_usage_errors_exit_two(argv: list[str]) -> None:
    assert main(argv) == 2


def test_negative_max_cases_is_a_usage_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = make_folder(tmp_path)
    target = tmp_path / "report.html"
    assert main(["build", str(folder), "-o", str(target), "--max-cases", "-1"]) == 2
    assert not target.exists()
    assert "usage" in capsys.readouterr().err


def test_missing_output_directory_is_a_usage_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = make_folder(tmp_path)
    target = tmp_path / "missing" / "report.html"
    assert main(["build", str(folder), "-o", str(target)]) == 2
    assert "usage" in capsys.readouterr().err


def test_output_that_is_a_directory_cleans_up(tmp_path: Path) -> None:
    folder = make_folder(tmp_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    assert main(["build", str(folder), "-o", str(out_dir)]) == 2
    assert sorted(path.name for path in tmp_path.iterdir()) == ["out", "results"]


def test_help_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--help"]) == 0
    assert "build" in capsys.readouterr().out


def test_main_reads_sys_argv(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["eval-report", "--help"])
    assert main() == 0
    assert "eval-report" in capsys.readouterr().out


def test_module_entry_point(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["eval-report", "--help"])
    with pytest.raises(SystemExit) as info:
        runpy.run_module("eval_report_html", run_name="__main__")
    assert info.value.code == 0
    assert "build" in capsys.readouterr().out
