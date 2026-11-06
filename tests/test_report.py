"""Tests for render_report."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from eval_report_html import CaseRow, ReportError, Run, render_report

META = """
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">
""".strip()
PAYLOAD = '"><script>alert(1)</script><svg onload=x>'


def make_run(
    run_id: str = "r1",
    minute: int = 0,
    metrics: dict[str, float] | None = None,
    cases: tuple[CaseRow, ...] = (),
) -> Run:
    return Run(
        run_id=run_id,
        created=datetime(2026, 1, 1, 10, minute, tzinfo=timezone.utc),
        metrics={"accuracy": 0.8} if metrics is None else metrics,
        cases=cases,
    )


def make_case(
    case_id: str,
    passed: bool = True,
    scores: dict[str, float] | None = None,
    output: str = "",
) -> CaseRow:
    return CaseRow(id=case_id, passed=passed, scores=scores or {}, output=output)


def test_head_starts_with_the_csp_meta() -> None:
    html = render_report([make_run()])
    assert html.split("<head>", 1)[1].startswith(META)
    assert "<script" not in html


def test_hostile_text_is_inert_everywhere() -> None:
    case = make_case(PAYLOAD, scores={PAYLOAD: 1.0}, output=PAYLOAD)
    runs = [
        make_run(PAYLOAD, 0, {PAYLOAD: 0.5}, (case,)),
        make_run(PAYLOAD + "2", 1, {PAYLOAD: 0.7}, (case,)),
    ]
    html = render_report(runs, title=PAYLOAD).lower()
    for needle in ("<script", "<svg onload", "javascript:", "http:", "https:"):
        assert needle not in html
    assert html.count("<svg") == 1


def test_acceptance_literals_verbatim() -> None:
    first = "The head's first child is exactly "
    hostile = ", and with title, run_id, metric name, case id and output all set to "
    none = " the report contains no "
    sep = ", no "
    last = " and no "
    html = render_report([make_run(PAYLOAD)], title=PAYLOAD)
    assert META in html, first + META
    assert "<script" not in html, hostile + PAYLOAD + none + "<script"
    assert "<svg onload" not in html, sep + "<svg onload"
    assert "javascript:" not in html, sep + "javascript:" + last + "http:"


def test_output_is_escaped_inside_pre() -> None:
    output = '<script>alert(1)</script>" onmouseover=x'
    html = render_report([make_run(cases=(make_case("c1", output=output),))])
    expected = "&lt;script&gt;alert(1)&lt;/script&gt;&quot; onmouseover=x"
    assert f"<pre>{expected}</pre>" in html
    assert "<script" not in html


def test_single_quotes_are_escaped_in_attributes_and_text() -> None:
    html = render_report([make_run(cases=(make_case("it's", output="it's"),))])
    assert "it&#x27;s" in html
    assert "it's" not in html


def test_increase_is_better_by_default() -> None:
    runs = [make_run("a", 0, {"accuracy": 0.8}), make_run("b", 1, {"accuracy": 0.85})]
    html = render_report(runs)
    assert '<td class="better">▲ +0.0500</td>' in html
    assert "<td>0.8500</td>" in html


def test_decrease_of_a_higher_is_better_metric_is_worse() -> None:
    runs = [make_run("a", 0, {"accuracy": 0.8}), make_run("b", 1, {"accuracy": 0.7})]
    assert '<td class="worse">▼ -0.1000</td>' in render_report(runs)


def test_lower_is_better_flips_the_direction() -> None:
    runs = [make_run("a", 0, {"latency": 120}), make_run("b", 1, {"latency": 100})]
    html = render_report(runs, lower_is_better=frozenset({"latency"}))
    assert '<td class="better">▼ -20.0000</td>' in html
    assert '<td class="worse">▼ -20.0000</td>' in render_report(runs)
    rising = [make_run("a", 0, {"latency": 100}), make_run("b", 1, {"latency": 120})]
    assert '<td class="worse">▲ +20.0000</td>' in render_report(
        rising, lower_is_better=frozenset({"latency"})
    )


def test_equal_values_are_same() -> None:
    runs = [make_run("a", 0, {"accuracy": 0.5}), make_run("b", 1, {"accuracy": 0.5})]
    assert '<td class="same">= +0.0000</td>' in render_report(runs)


def test_missing_previous_value_is_not_available() -> None:
    assert '<td class="same">n/a</td>' in render_report([make_run()])
    runs = [make_run("a", 0, {"x": 1.0}), make_run("b", 1, {"x": 1.0, "y": 2.0})]
    assert '<td class="same">n/a</td>' in render_report(runs)


def test_single_run_has_no_trend() -> None:
    assert "single run: no trend" in render_report([make_run()])
    two = render_report([make_run("a", 0), make_run("b", 1)])
    assert "single run: no trend" not in two
    assert two.count("<svg") == 1


def test_missing_metrics_become_gaps() -> None:
    runs = [
        make_run("a", 0, {"a": 1.0}),
        make_run("b", 1, {"a": 2.0, "b": 3.0}),
        make_run("c", 2, {"a": 3.0}),
    ]
    html = render_report(runs)
    assert html.count("<svg") == 2
    assert html.count("<polyline") == 1
    assert html.count("<circle") == 1


def test_runs_without_metrics() -> None:
    runs = [make_run("a", 0, {}), make_run("b", 1, {})]
    html = render_report(runs)
    assert "No metrics in the latest run." in html
    assert "<svg" not in html


def test_cases_are_sorted_with_results_and_scores() -> None:
    cases = (
        make_case("b", passed=False, scores={"f1": 0.5, "em": 1.0}),
        make_case("a"),
    )
    html = render_report([make_run(cases=cases)])
    assert html.index("<td>a</td>") < html.index("<td>b</td>")
    assert '<td class="pass">pass</td>' in html
    assert '<td class="fail">fail</td>' in html
    assert "em: 1.0000<br>f1: 0.5000" in html
    assert "1 of 2 cases passed" in html


def test_no_cases_message() -> None:
    assert "No cases in the latest run." in render_report([make_run()])


def test_case_cap() -> None:
    cases = tuple(make_case(f"c{n}") for n in (5, 1, 3, 2, 4))
    html = render_report([make_run(cases=cases)], max_cases=2)
    assert "<td>c1</td>" in html
    assert "<td>c2</td>" in html
    assert "<td>c3</td>" not in html
    assert "3 more cases not shown" in html
    assert "more cases not shown" not in render_report([make_run(cases=cases)], max_cases=5)
    assert "5 more cases not shown" in render_report([make_run(cases=cases)], max_cases=0)


def test_output_is_cut_with_an_ellipsis() -> None:
    long_case = make_case("c1", output="x" * 2001)
    html = render_report([make_run(cases=(long_case,))], max_output_chars=2000)
    assert "<pre>" + "x" * 2000 + "…</pre>" in html
    assert "x" * 2001 not in html
    exact = make_case("c1", output="x" * 2000)
    assert "<pre>" + "x" * 2000 + "</pre>" in render_report([make_run(cases=(exact,))])


def test_output_is_cut_before_escaping() -> None:
    case = make_case("c1", output="<<<<")
    html = render_report([make_run(cases=(case,))], max_output_chars=2)
    assert "<pre>&lt;&lt;…</pre>" in html


def test_rendering_is_deterministic_and_order_independent() -> None:
    runs = [make_run("a", 0, {"m": 1.0}), make_run("b", 1, {"m": 2.0})]
    first = render_report(runs)
    assert first == render_report(runs)
    assert first == render_report(list(reversed(runs)))
    assert first.encode("utf-8") == render_report(runs).encode("utf-8")


def test_header_counts_runs() -> None:
    assert "1 run;" in render_report([make_run()])
    assert "2 runs;" in render_report([make_run("a", 0), make_run("b", 1)])
    assert "<title>Evaluation report</title>" in render_report([make_run()])


def test_page_has_no_javascript_or_remote_references() -> None:
    html = render_report([make_run("a", 0), make_run("b", 1)]).lower()
    for needle in ("<script", "javascript:", "http:", "https:", "src=", "href=", "url("):
        assert needle not in html
    assert html.count("<style>") == 1


def test_empty_runs_are_rejected() -> None:
    with pytest.raises(ReportError) as info:
        render_report([])
    assert info.value.code == "input_invalid"


def test_too_many_runs_are_rejected() -> None:
    with pytest.raises(ReportError) as info:
        render_report([make_run()] * 10_001)
    assert info.value.code == "input_too_large"


def test_negative_limits_are_usage_errors() -> None:
    with pytest.raises(ReportError) as cases:
        render_report([make_run()], max_cases=-1)
    assert cases.value.code == "usage"
    with pytest.raises(ReportError) as chars:
        render_report([make_run()], max_output_chars=-1)
    assert chars.value.code == "usage"


def test_title_length_is_limited() -> None:
    with pytest.raises(ReportError) as info:
        render_report([make_run()], title="t" * 100_001)
    assert info.value.code == "input_invalid"
