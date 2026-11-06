"""Typed errors raised by ``eval_report_html``."""

from __future__ import annotations

from typing import Literal

ErrorCode = Literal["input_invalid", "input_too_large", "usage"]

_REASON_CHARS = 80
_PATH_CHARS = 118


def _head(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    keep = limit - 1
    return text[:keep] + "\u2026"


def _tail(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    keep = limit - 1
    return "\u2026" + text[-keep:]


class ReportError(Exception):
    """Base error of the library.

    Attributes:
        code: Stable machine-readable code: ``input_invalid``, ``input_too_large`` or ``usage``.
        path: The file or folder the error is about, if any (full value, not truncated).

    The rendered message never exceeds 200 characters.
    """

    def __init__(self, code: ErrorCode, message: str, path: str | None = None) -> None:
        reason = _head(message, _REASON_CHARS)
        text = reason if path is None else f"{reason}: {_tail(path, _PATH_CHARS)}"
        super().__init__(text)
        self.code: ErrorCode = code
        self.path = path
