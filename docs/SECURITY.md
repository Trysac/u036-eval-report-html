# Security notes

## Threat model

`trysac-eval-report-html` reads local JSON files and writes one HTML file. It makes no network calls and runs no scripts.

Defended:

- **Hostile text in results**: every input string (title, run id, metric names, case ids, outputs) is escaped with `html.escape(s, quote=True)` before insertion, in text, attributes and SVG labels.
- **Script execution in the report**: the page contains no JavaScript. The first child of `<head>` is a Content-Security-Policy meta tag with `default-src 'none'; style-src 'unsafe-inline'`, which blocks scripts, remote loads and other sources.
- **Malformed or hostile JSON**: NaN and Infinity constants, duplicate object keys, booleans used as numbers, naive timestamps and duplicate case ids are rejected with `ReportError`.
- **Resource exhaustion**: files above `max_file_bytes` (default 10 MB) are rejected as `input_too_large`; more than `max_files` (default 1000) JSON files, strings over 100000 characters, more than 10000 runs and more than 10000 trend values are rejected.
- **Symbolic links and special files**: symbolic links are skipped when listing; files are opened with `O_NOFOLLOW` where available and only regular files are read.
- **Partial output**: the CLI writes to a temporary file in the target folder and replaces the target only on success.

Not defended:

- Only a shallow directory listing is protected; the library does not sandbox the process or limit total memory across files.
- Numbers beyond 2**53 lose precision silently after `float()` conversion.
- Output cut limits apply to case outputs only; other fields are not truncated beyond the length check.
- The CSP does not protect a reader who copies and runs the HTML outside a browser.
- Supply-chain controls (dependency pinning, secret scanning in CI) are not described by the reviewed code.

To report a vulnerability, see [SECURITY.md](../SECURITY.md).
