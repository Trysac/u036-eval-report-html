# Standard-library only static report with escaping at every sink and a CSP backstop

Status: accepted (generated, pending human review)

## Context

Evaluation results sit in CI artifacts as JSON files and the outputs they contain are untrusted model text. The report must open offline, need no server or account, and stay safe even when outputs contain hostile markup.

## Decision

Generate one HTML file with the standard library only. Every input string passes through html.escape(s, quote=True) before insertion, in text and attributes alike. The page has no JavaScript and a single style element, and its first head element is a Content-Security-Policy meta with default-src 'none'. Trends are inline SVG built by a pure function with a deterministic layout and no timestamp, so equal inputs give byte-identical output. Input loading enforces named limits (file bytes, file count, string length, run and point counts) and a single ReportError class with stable codes. The CLI renders fully in memory, then writes a temp file in the target folder and uses os.replace, so a failure never touches an existing report.

## Consequences

The library has no runtime dependencies and a small attack surface. The CSP is defence in depth rather than the primary control, since escaping is applied everywhere. There is no interactivity and no hosting, as designed. Integers beyond 2^53 lose precision through float(), which is documented. Truncating outputs bounds the page size, but the whole report is still held in memory while it is built, so very large folders are bounded by the file and run limits.
