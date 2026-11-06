# Stack

## Used

| Tool | Why |
|---|---|
| Python >= 3.10 | Minimum version declared in the README; the code uses `from __future__ import annotations` and `int | float` in isinstance checks. |
| hatchling | Build backend declared for the package. |
| pytest + pytest-cov | Test runner and branch coverage used in `docs/TESTING.md`. |

The package has no runtime dependencies; only the standard library is imported (`json`, `math`, `os`, `stat`, `html`, `argparse`, `tempfile`, `datetime`, `dataclasses`, `typing`, `logging`, `pathlib`).

## Discarded

No discarded tools are recorded in the reviewed material.
