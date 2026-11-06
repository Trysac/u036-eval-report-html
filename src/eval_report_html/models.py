"""Immutable data model for evaluation runs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

MAX_STRING_CHARS = 100_000


@dataclass(frozen=True)
class CaseRow:
    """One evaluated case of a run.

    Attributes:
        id: Case identifier, unique inside a run.
        passed: Whether the case passed.
        scores: Named numeric scores.
        output: Model output text (shown truncated in the report).
    """

    id: str
    passed: bool
    scores: Mapping[str, float]
    output: str


@dataclass(frozen=True)
class Run:
    """One evaluation run.

    Attributes:
        run_id: Run identifier.
        created: Timezone-aware creation time.
        metrics: Named aggregate metrics.
        cases: The evaluated cases.
    """

    run_id: str
    created: datetime
    metrics: Mapping[str, float]
    cases: tuple[CaseRow, ...]
