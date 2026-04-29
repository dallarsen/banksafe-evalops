"""Tests for the regression-comparison engine.

Verifies that compare_runs correctly identifies regressions, improvements,
and flat dimensions, and that the PR-comment renderer produces sensible
markdown for each scenario.
"""

from __future__ import annotations

from banksafe.datasets.schema import AgentResponse
from banksafe.eval.regression import (
    compare_runs,
    render_pr_comment,
)
from banksafe.eval.runner import (
    CaseResult,
    DimensionSummary,
    RunResult,
)


def _make_run(
    *,
    name: str = "test",
    accuracy: float = 0.90,
    grounding: float = 0.90,
    overall_passed: bool = True,
) -> RunResult:
    response = AgentResponse(output_text="ok", model="m")
    return RunResult(
        dataset=name,
        agent_name="a",
        agent_model="m",
        started_at="2026-04-28T00:00:00+00:00",
        finished_at="2026-04-28T00:00:01+00:00",
        duration_s=1.0,
        case_count=1,
        case_results=[
            CaseResult(
                case_id="c-1",
                category="x",
                trap_type=None,
                must_refuse=False,
                agent_response=response,
                judge_results=[],
            )
        ],
        dimension_summaries=[
            DimensionSummary(
                dimension="accuracy",
                mean_score=accuracy,
                min_score=accuracy,
                max_score=accuracy,
                sample_count=1,
                fail_threshold=0.80,
                passed=accuracy >= 0.80,
            ),
            DimensionSummary(
                dimension="grounding",
                mean_score=grounding,
                min_score=grounding,
                max_score=grounding,
                sample_count=1,
                fail_threshold=0.85,
                passed=grounding >= 0.85,
            ),
        ],
        overall_passed=overall_passed,
    )


def test_no_regression_when_runs_identical() -> None:
    baseline = _make_run(accuracy=0.90, grounding=0.90)
    current = _make_run(accuracy=0.90, grounding=0.90)
    report = compare_runs(current, baseline)
    assert not report.has_regressions
    assert all(not d.is_regression for d in report.deltas)


def test_regression_detected_when_score_drops_more_than_threshold() -> None:
    baseline = _make_run(accuracy=0.90, grounding=0.90)
    current = _make_run(accuracy=0.80, grounding=0.90)  # 10pp drop, threshold 5pp
    report = compare_runs(current, baseline, regression_threshold=0.05)
    assert report.has_regressions
    accuracy_delta = next(d for d in report.deltas if d.dimension == "accuracy")
    assert accuracy_delta.is_regression
    grounding_delta = next(d for d in report.deltas if d.dimension == "grounding")
    assert not grounding_delta.is_regression


def test_no_regression_when_drop_within_threshold() -> None:
    baseline = _make_run(accuracy=0.90, grounding=0.90)
    current = _make_run(accuracy=0.87, grounding=0.90)  # 3pp drop, threshold 5pp
    report = compare_runs(current, baseline, regression_threshold=0.05)
    assert not report.has_regressions


def test_improvement_recorded_but_not_treated_as_regression() -> None:
    baseline = _make_run(accuracy=0.80, grounding=0.85)
    current = _make_run(accuracy=0.95, grounding=0.85)
    report = compare_runs(current, baseline)
    assert not report.has_regressions
    assert report.has_improvements


def test_pr_comment_for_passing_run() -> None:
    baseline = _make_run(accuracy=0.90, grounding=0.90)
    current = _make_run(accuracy=0.91, grounding=0.90)
    report = compare_runs(current, baseline)
    md = render_pr_comment(report)
    assert "✅" in md
    assert "regression" not in md.lower() or "regression detected" not in md.lower()
    assert "| `accuracy` |" in md
    assert "| `grounding` |" in md


def test_pr_comment_for_regression() -> None:
    baseline = _make_run(accuracy=0.90, grounding=0.90)
    current = _make_run(accuracy=0.50, grounding=0.90, overall_passed=False)
    report = compare_runs(current, baseline)
    md = render_pr_comment(report)
    assert "❌" in md
    assert "regression" in md.lower()
    # accuracy row should show the regression status
    assert "❌ regression" in md


def test_pr_comment_for_failed_thresholds_without_regression() -> None:
    """If a run drops just enough to fail threshold but not enough to trigger
    a regression vs baseline, the PR comment should still flag the failure."""
    baseline = _make_run(accuracy=0.82, grounding=0.86)
    current = _make_run(accuracy=0.79, grounding=0.86, overall_passed=False)
    report = compare_runs(current, baseline, regression_threshold=0.10)
    md = render_pr_comment(report)
    assert not report.has_regressions
    assert "fell below" in md or "failed thresholds" in md
