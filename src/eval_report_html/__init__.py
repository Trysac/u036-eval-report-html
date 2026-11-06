"""Generate one self-contained, script-free static HTML report from evaluation result files."""

from __future__ import annotations

import logging

from .errors import ReportError
from .loader import load_runs
from .models import CaseRow, Run
from .report import render_report
from .svg import trend_svg

__all__ = [
    "CaseRow",
    "ReportError",
    "Run",
    "__version__",
    "load_runs",
    "render_report",
    "trend_svg",
]

__version__ = "0.1.0"

logging.getLogger(__name__).addHandler(logging.NullHandler())
