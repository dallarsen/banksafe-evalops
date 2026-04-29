"""Regression detection between a current eval run and a baseline.

The comparison emits both a structured `RegressionReport` (for programmatic
use in CI) and a Markdown PR-comment renderer (for posting back to GitHub).
A regression is defined per-dimension: if `mean_score` drops by more than
`regression_threshold` (default 0.05 = 5pp), that dimension is flagged.

We DO NOT flag improvements as regressions. Score gains are recorded with a
`+` prefix in the comment so reviewers can see the wins too.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from banksafe.eval.runner import RunResult


class DimensionDelta(BaseModel):
    dimension: str
    current: float
    baseline: float
    delta: float
    is_regression: bool
    current_passed: bool
    baseline_passed: bool


class RegressionReport(BaseModel):
    """Structured comparison between two runs."""

    dataset: str
    current_passed: bool
    baseline_passed: bool
    threshold: float
    deltas: list[DimensionDelta] = Field(default_factory=list)
    has_regressions: bool
    has_improvements: bool
    current_overall_mean: float
    baseline_overall_mean: float


def compare_runs(
    current: RunResult,
    baseline: RunResult,
    *,
    regression_threshold: float = 0.05,
) -> RegressionReport:
    """Compute a per-dimension comparison between current and baseline runs.

    A dimension regresses if `current.mean_score - baseline.mean_score < -threshold`.
    Improvements are recorded but never trigger failure.
    """
    baseline_by_dim = {s.dimension: s for s in baseline.dimension_summaries}
    current_by_dim = {s.dimension: s for s in current.dimension_summaries}

    all_dims = sorted(set(baseline_by_dim) | set(current_by_dim))
    deltas: list[DimensionDelta] = []
    for dim in all_dims:
        b = baseline_by_dim.get(dim)
        c = current_by_dim.get(dim)
        baseline_mean = b.mean_score if b else 0.0
        current_mean = c.mean_score if c else 0.0
        delta = current_mean - baseline_mean
        deltas.append(
            DimensionDelta(
                dimension=dim,
                current=current_mean,
                baseline=baseline_mean,
                delta=delta,
                is_regression=delta < -regression_threshold,
                current_passed=c.passed if c else False,
                baseline_passed=b.passed if b else False,
            )
        )

    has_regressions = any(d.is_regression for d in deltas)
    has_improvements = any(d.delta > regression_threshold for d in deltas)

    current_overall = (
        sum(s.mean_score for s in current.dimension_summaries)
        / max(len(current.dimension_summaries), 1)
    )
    baseline_overall = (
        sum(s.mean_score for s in baseline.dimension_summaries)
        / max(len(baseline.dimension_summaries), 1)
    )

    return RegressionReport(
        dataset=current.dataset,
        current_passed=current.overall_passed,
        baseline_passed=baseline.overall_passed,
        threshold=regression_threshold,
        deltas=deltas,
        has_regressions=has_regressions,
        has_improvements=has_improvements,
        current_overall_mean=current_overall,
        baseline_overall_mean=baseline_overall,
    )


def render_comparison_table(report: RegressionReport, console) -> None:
    """Pretty-print the report to the console."""
    from rich.panel import Panel
    from rich.table import Table

    summary_lines = [
        f"Dataset: [cyan]{report.dataset}[/cyan]",
        f"Threshold: ±{report.threshold:.2f} per dimension",
        f"Current overall mean: {report.current_overall_mean:.3f}   "
        f"Baseline: {report.baseline_overall_mean:.3f}   "
        f"Δ: {report.current_overall_mean - report.baseline_overall_mean:+.3f}",
    ]
    console.print(Panel("\n".join(summary_lines), title="Regression check"))

    table = Table(show_lines=False)
    table.add_column("Dimension", style="cyan")
    table.add_column("Current", justify="right")
    table.add_column("Baseline", justify="right")
    table.add_column("Δ", justify="right")
    table.add_column("Verdict", justify="center")

    for d in report.deltas:
        if d.is_regression:
            verdict = "[red]REGRESSION[/red]"
        elif d.delta > report.threshold:
            verdict = "[green]+improved[/green]"
        else:
            verdict = "[dim]flat[/dim]"
        table.add_row(
            d.dimension,
            f"{d.current:.3f}",
            f"{d.baseline:.3f}",
            f"{d.delta:+.3f}",
            verdict,
        )
    console.print(table)

    if report.has_regressions:
        console.print("[bold red]One or more dimensions regressed beyond threshold.[/bold red]")
    elif report.has_improvements:
        console.print("[bold green]No regressions. Some dimensions improved![/bold green]")
    else:
        console.print("[bold]No regressions detected.[/bold]")


def render_pr_comment(report: RegressionReport) -> str:
    """Render the report as Markdown suitable for posting as a PR comment."""
    lines: list[str] = []
    if report.has_regressions:
        lines.append("## ❌ BankSafe EvalOps — regression detected")
    elif not report.current_passed:
        lines.append("## ❌ BankSafe EvalOps — eval run failed thresholds")
    else:
        lines.append("## ✅ BankSafe EvalOps — eval passed")

    lines.append("")
    lines.append(f"**Dataset:** `{report.dataset}`  ")
    lines.append(f"**Regression threshold:** ±{report.threshold:.2f} per dimension")
    lines.append("")
    lines.append(
        f"**Overall mean:** `{report.current_overall_mean:.3f}` "
        f"(baseline `{report.baseline_overall_mean:.3f}`, "
        f"Δ `{report.current_overall_mean - report.baseline_overall_mean:+.3f}`)"
    )
    lines.append("")
    lines.append("| Dimension | Current | Baseline | Δ | Status |")
    lines.append("|---|---:|---:|---:|---|")
    for d in report.deltas:
        if d.is_regression:
            status = "❌ regression"
        elif d.delta > report.threshold:
            status = "🟢 improved"
        else:
            status = "⚪ flat"
        lines.append(
            f"| `{d.dimension}` | {d.current:.3f} | {d.baseline:.3f} | "
            f"{d.delta:+.3f} | {status} |"
        )

    lines.append("")
    if report.has_regressions:
        lines.append(
            "> One or more dimensions regressed beyond the configured "
            "threshold. Investigate the affected judges and per-case rationales "
            "in the workflow run artifacts before merging."
        )
    elif not report.current_passed:
        lines.append(
            "> Run did not regress vs baseline, but at least one dimension "
            "fell below its absolute pass threshold. Check the run summary."
        )
    else:
        lines.append("> All dimensions held within tolerance of the baseline. ✅")

    return "\n".join(lines)
