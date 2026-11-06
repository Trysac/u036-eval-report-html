"""Command line interface: ``eval-report build FOLDER -o report.html``."""

from __future__ import annotations

import argparse
import contextlib
import logging
import os
import sys
import tempfile
from pathlib import Path

from .errors import ReportError
from .loader import load_runs
from .report import render_report

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eval-report",
        description="Build a static HTML report from evaluation result files.",
        allow_abbrev=False,
    )
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="write one HTML report", allow_abbrev=False)
    build.add_argument("folder", metavar="FOLDER", type=Path)
    build.add_argument("-o", "--output", required=True, type=Path)
    build.add_argument("--title", default="Evaluation report")
    build.add_argument(
        "--lower-is-better",
        action="append",
        default=[],
        dest="lower_is_better",
        metavar="METRIC",
    )
    build.add_argument("--max-cases", type=int, default=500)
    return parser


def _write_atomic(target: Path, document: str) -> None:
    try:
        fd, tmp_name = tempfile.mkstemp(dir=target.parent, prefix=".eval-report-", suffix=".tmp")
    except OSError as exc:
        raise ReportError("usage", "cannot create output file", str(target)) from exc
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(document.encode("utf-8"))
        os.replace(tmp_name, target)
    except OSError as exc:
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise ReportError("usage", "cannot write output file", str(target)) from exc


def main(argv: list[str] | None = None) -> int:
    """Run the command line interface.

    Returns:
        0 when the report was written, 2 for any input or usage error. An existing
        output file is never touched when an error occurs.
    """
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        runs = load_runs(args.folder)
        if not runs:
            raise ReportError("input_invalid", "no *.json result files found", str(args.folder))
        document = render_report(
            runs,
            title=args.title,
            lower_is_better=frozenset(args.lower_is_better),
            max_cases=args.max_cases,
        )
        _write_atomic(args.output, document)
    except ReportError as exc:
        print(f"error[{exc.code}]: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
