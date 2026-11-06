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
| Tokens (input / output) | 414066 / 87987 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.6894 |

## Factory run u036 (measured from API usage)

| Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|
| generation | claude-sonnet-5-5 | yes | 2395 | 76689 | 0 | 4246 | 0.3863 |
| fix-1 | claude-sonnet-5-5 | no | 4 | 306 | 5705 | 24411 | 0.0198 |
| fix-2 | claude-sonnet-5-5 | no | 6 | 854 | 6614 | 39947 | 0.0291 |
| fix-3 | claude-sonnet-5-5 | no | 10 | 1239 | 7531 | 71304 | 0.0384 |
| audit | claude-sonnet-5-5 | no | 12 | 3533 | 26107 | 120432 | 0.1127 |
| fix-4 | claude-sonnet-5-5 | no | 6 | 1472 | 7729 | 40425 | 0.0381 |
| docs | claude-haiku-5-5 | no | 110868 | 3894 | 0 | 0 | 0.0652 |

Total: $0.6894. Prices: Anthropic list prices.
