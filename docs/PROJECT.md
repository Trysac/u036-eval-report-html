# Project record

## Objective

Generate one self-contained, script-free static HTML report from evaluation result JSON files, with per-run tables and SVG trend lines. The problem addressed: evaluation results sit as JSON in CI artifacts and trends across runs are not visible, while dashboards need servers and accounts.

## Scope

- In scope: loading and validating a folder of result JSON files; rendering one offline HTML report with a latest-run summary and deltas, a per-metric inline SVG trend, and a per-case table; the `eval-report build` command line interface.
- Out of scope: interactivity, hosting, PDF output. No runtime dependencies.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Measured values only; a value that has not been measured stays "pending measurement".

| Metric | Value |
|---|---|
| Tokens (input / output) | pending measurement |
| Hours (human) | pending measurement |
| Cost (USD) | pending measurement |
