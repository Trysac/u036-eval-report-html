"""Load evaluation result files from a folder."""

from __future__ import annotations

import json
import logging
import math
import os
import stat
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, NoReturn

from .errors import ReportError
from .models import MAX_STRING_CHARS, CaseRow, Run

logger = logging.getLogger(__name__)

_FILE_FLAGS = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)


def _invalid(reason: str, path: str) -> ReportError:
    return ReportError("input_invalid", reason, path)


def _reject_constant(name: str) -> NoReturn:
    raise ValueError("non-finite JSON constant: " + name)


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate object key")
        result[key] = value
    return result


def _text(value: object, what: str, path: str) -> str:
    if not isinstance(value, str):
        raise _invalid(f"{what} must be a string", path)
    if len(value) > MAX_STRING_CHARS:
        raise _invalid(f"{what} is longer than {MAX_STRING_CHARS} characters", path)
    return value


def _number(value: object, what: str, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise _invalid(f"{what} must be a number", path)
    try:
        result = float(value)
    except OverflowError as exc:
        raise _invalid(f"{what} is out of range", path) from exc
    if not math.isfinite(result):
        raise _invalid(f"{what} must be finite", path)
    return result


def _mapping(value: object, what: str, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _invalid(f"{what} must be an object", path)
    return value


def _number_map(value: object, what: str, path: str) -> dict[str, float]:
    mapping = _mapping(value, what, path)
    result: dict[str, float] = {}
    for key, item in mapping.items():
        name = _text(key, f"{what} name", path)
        result[name] = _number(item, f"{what} {name[:20]!r}", path)
    return result


def _require(obj: dict[str, Any], key: str, path: str) -> object:
    if key not in obj:
        raise _invalid(f"missing key {key!r}", path)
    value: object = obj[key]
    return value


def _parse_created(value: object, path: str) -> datetime:
    text = _text(value, "created", path)
    candidate = text[:-1] + "+00:00" if text.endswith(("Z", "z")) else text
    try:
        created = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise _invalid("created is not an ISO 8601 timestamp", path) from exc
    if created.tzinfo is None or created.utcoffset() is None:
        raise _invalid("created must carry a UTC offset", path)
    return created


def _parse_case(raw: object, index: int, path: str) -> CaseRow:
    obj = _mapping(raw, f"case {index}", path)
    case_id = _text(_require(obj, "id", path), "case id", path)
    passed = _require(obj, "passed", path)
    if not isinstance(passed, bool):
        raise _invalid("passed must be a boolean", path)
    scores = _number_map(_require(obj, "scores", path), "score", path)
    output = _text(_require(obj, "output", path), "output", path)
    return CaseRow(id=case_id, passed=passed, scores=MappingProxyType(scores), output=output)


def _parse_cases(value: object, path: str) -> tuple[CaseRow, ...]:
    if not isinstance(value, list):
        raise _invalid("cases must be an array", path)
    rows: list[CaseRow] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        row = _parse_case(item, index, path)
        if row.id in seen:
            raise _invalid(f"duplicate case id {row.id[:20]!r}", path)
        seen.add(row.id)
        rows.append(row)
    return tuple(rows)


def _parse_document(data: bytes, path: str) -> Run:
    try:
        raw: object = json.loads(
            data.decode("utf-8"),
            parse_constant=_reject_constant,
            object_pairs_hook=_no_duplicates,
        )
    except (ValueError, RecursionError) as exc:
        raise _invalid("not valid JSON", path) from exc
    obj = _mapping(raw, "document", path)
    run_id = _text(_require(obj, "run_id", path), "run_id", path)
    created = _parse_created(_require(obj, "created", path), path)
    metrics = _number_map(_require(obj, "metrics", path), "metric", path)
    cases = _parse_cases(_require(obj, "cases", path), path)
    return Run(run_id=run_id, created=created, metrics=MappingProxyType(metrics), cases=cases)


def _read_file(path: Path, limit: int) -> bytes:
    try:
        fd = os.open(path, _FILE_FLAGS)
        with os.fdopen(fd, "rb") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise _invalid("not a regular file", str(path))
            data = handle.read(limit + 1)
    except OSError as exc:
        raise _invalid("cannot read file", str(path)) from exc
    if len(data) > limit:
        raise ReportError("input_too_large", f"file is larger than {limit} bytes", str(path))
    return data


def load_runs(
    folder: Path,
    max_file_bytes: int = 10_000_000,
    max_files: int = 1000,
) -> list[Run]:
    """Read every ``*.json`` file directly inside ``folder`` and return the runs.

    The folder is not searched recursively and symbolic links are skipped. Runs are
    sorted by ``(created, run_id)``, comparing ``created`` as an aware datetime.
    JSON numbers must be ints or floats (not booleans) and are converted with
    ``float()``; integers beyond 2**53 therefore lose precision. ``NaN``, ``Infinity``,
    duplicate object keys, naive timestamps, duplicate case ids and strings longer than
    100000 characters are rejected.

    Args:
        folder: Folder holding the result files.
        max_file_bytes: Largest accepted file size in bytes.
        max_files: Largest accepted number of ``*.json`` files.

    Returns:
        The runs sorted by creation time then run id (empty for an empty folder).

    Raises:
        ReportError: ``input_invalid`` for malformed content or a bad folder,
            ``input_too_large`` for an oversized file, ``usage`` for bad limits.
    """
    if max_file_bytes < 1 or max_files < 1:
        raise ReportError("usage", "limits must be positive")
    root = Path(folder)
    if not root.is_dir():
        raise _invalid("not a directory", str(root))
    names: list[str] = []
    try:
        with os.scandir(root) as entries:
            for entry in entries:
                if not entry.name.endswith(".json"):
                    continue
                if entry.is_symlink() or not entry.is_file(follow_symlinks=False):
                    continue
                if len(names) >= max_files:
                    raise _invalid(f"more than {max_files} JSON files", str(root))
                names.append(entry.name)
    except OSError as exc:
        raise _invalid("cannot list folder", str(root)) from exc
    runs: list[Run] = []
    for name in sorted(names):
        file_path = root / name
        data = _read_file(file_path, max_file_bytes)
        runs.append(_parse_document(data, str(file_path)))
    runs.sort(key=lambda run: (run.created, run.run_id))
    logger.debug("loaded %d result files", len(runs))
    return runs
