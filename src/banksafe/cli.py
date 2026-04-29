"""Command-line interface for BankSafe EvalOps."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

app = typer.Typer(
    name="banksafe",
    help="BankSafe EvalOps — evaluation framework for agentic banking systems.",
    no_args_is_help=True,
)
agent_app = typer.Typer(
    name="agent",
    help="Interact with the compliance agent.",
    no_args_is_help=True,
)
eval_app = typer.Typer(
    name="eval",
    help="Inspect, run, calibrate, and compare evaluations.",
    no_args_is_help=True,
)
app.add_typer(agent_app)
app.add_typer(eval_app)

console = Console()


# ---------------------------------------------------------------------------
# agent commands
# ---------------------------------------------------------------------------


@agent_app.command("ask")
def agent_ask(
    query: str = typer.Argument(..., help="Question to ask the compliance agent.")
) -> None:
    """Ask the compliance agent a single question."""
    from banksafe.agents import ComplianceAgent
    from banksafe.demo import render

    agent = ComplianceAgent()
    response = agent.answer(query)
    render(response)


@agent_app.command("demo")
def agent_demo() -> None:
    """Run the bundled sample queries against the compliance agent."""
    from banksafe.demo import main

    main()


# ---------------------------------------------------------------------------
# eval — dataset inspection
# ---------------------------------------------------------------------------


@eval_app.command("list")
def eval_list() -> None:
    """List every available evaluation dataset."""
    from banksafe.datasets import list_datasets

    names = list_datasets()
    if not names:
        console.print("[yellow]No evaluation datasets found in data/eval_sets/[/yellow]")
        raise typer.Exit(code=1)
    console.print("[bold]Available evaluation datasets:[/bold]")
    for name in names:
        console.print(f"  - {name}")


@eval_app.command("show")
def eval_show(
    dataset: str = typer.Argument(..., help="Dataset name (without .jsonl).")
) -> None:
    """Print summary statistics for an evaluation dataset."""
    from banksafe.datasets import summarize_dataset

    stats = summarize_dataset(dataset)
    console.print(f"\n[bold cyan]Dataset:[/bold cyan] {stats.name}")
    console.print(f"[bold]Total cases:[/bold] {stats.total_cases}")
    console.print(f"[bold]Must-refuse cases:[/bold] {stats.must_refuse_count}")
    console.print(f"[bold]Multi-policy cases:[/bold] {stats.multi_policy_count}")

    cat_table = Table(title="By category", show_lines=False)
    cat_table.add_column("Category", style="cyan")
    cat_table.add_column("Count", justify="right")
    for cat, n in sorted(stats.by_category.items(), key=lambda kv: (-kv[1], kv[0])):
        cat_table.add_row(cat, str(n))
    console.print(cat_table)

    trap_table = Table(title="By trap type", show_lines=False)
    trap_table.add_column("Trap type", style="magenta")
    trap_table.add_column("Count", justify="right")
    for trap, n in sorted(stats.by_trap_type.items(), key=lambda kv: (-kv[1], kv[0])):
        trap_table.add_row(trap, str(n))
    console.print(trap_table)


@eval_app.command("cases")
def eval_cases(
    dataset: str = typer.Argument(..., help="Dataset name (without .jsonl)."),
    category: str | None = typer.Option(None, "--category", "-c", help="Filter by category."),
    trap: str | None = typer.Option(None, "--trap", "-t", help="Filter by trap_type."),
    limit: int = typer.Option(10, "--limit", "-n", help="Max cases to show."),
) -> None:
    """List cases in an evaluation dataset, with optional filters."""
    from banksafe.datasets import load_dataset

    cases = load_dataset(dataset)
    if category:
        cases = [c for c in cases if c.category == category]
    if trap:
        cases = [c for c in cases if (c.trap_type or "") == trap]

    if not cases:
        console.print("[yellow]No cases match those filters.[/yellow]")
        raise typer.Exit(code=1)

    table = Table(show_lines=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Category")
    table.add_column("Trap", style="magenta")
    table.add_column("Refuse?", justify="center")
    table.add_column("Input", overflow="fold")

    for case in cases[:limit]:
        refuse_marker = "[green]Y[/green]" if case.must_refuse else ""
        table.add_row(case.id, case.category, case.trap_type or "", refuse_marker, case.input)

    console.print(table)
    if len(cases) > limit:
        console.print(f"[dim]Showing {limit} of {len(cases)}. Use --limit to see more.[/dim]")


# ---------------------------------------------------------------------------
# eval — run + calibrate
# ---------------------------------------------------------------------------


@eval_app.command("run")
def eval_run(
    dataset: str = typer.Option("compliance-v1", "--dataset", "-d", help="Dataset to evaluate."),
    limit: int | None = typer.Option(
        None, "--limit", "-n", help="Run only the first N cases (cost control)."
    ),
    output: Path = typer.Option(
        Path("evals/output/last_run.json"),
        "--output",
        "-o",
        help="Where to save the full RunResult JSON.",
    ),
) -> None:
    """Run the full evaluation pipeline and report dimension scores."""
    from banksafe.agents import ComplianceAgent
    from banksafe.datasets import load_dataset
    from banksafe.eval import run_evaluation, save_run_result

    cases = load_dataset(dataset)
    if limit is not None:
        cases = cases[:limit]
    console.print(
        f"[bold]Running evaluation:[/bold] {len(cases)} cases × 6 judges. "
        "This may take several minutes and incur API costs."
    )

    agent = ComplianceAgent()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Evaluating…", total=len(cases))

        def _cb(idx: int, total: int, case) -> None:
            progress.update(
                task, description=f"[{idx + 1}/{total}] {case.id} ({case.category})"
            )
            progress.advance(task)

        result = run_evaluation(cases, agent, dataset_name=dataset, progress_callback=_cb)

    save_run_result(result, output)

    _render_run_result(result)
    console.print(f"\n[dim]Full results saved to {output}[/dim]")
    if not result.overall_passed:
        raise typer.Exit(code=1)


@eval_app.command("calibrate")
def eval_calibrate(
    golden_set: str = typer.Option("golden-v1", "--golden", "-g", help="Golden set name."),
) -> None:
    """Calibrate judges against the hand-labeled golden set."""
    from banksafe.judges.calibration import run_calibration

    console.print(f"[bold]Calibrating against {golden_set}…[/bold]")
    reports = run_calibration(name=golden_set)

    table = Table(title="Calibration report", show_lines=True)
    table.add_column("Dimension", style="cyan")
    table.add_column("N", justify="right")
    table.add_column("MAE", justify="right")
    table.add_column("Max Δ", justify="right")
    table.add_column("Status", justify="center")

    any_uncalibrated = False
    for dim in ("accuracy", "grounding", "hallucination", "pii", "refusal", "tone"):
        report = reports.get(dim)
        if not report:
            table.add_row(dim, "-", "-", "-", "[dim](no samples)[/dim]")
            continue
        status = "[green]✓ calibrated[/green]" if report.calibrated else "[red]✗ uncalibrated[/red]"
        if not report.calibrated:
            any_uncalibrated = True
        table.add_row(
            dim,
            str(report.sample_count),
            f"{report.mean_absolute_error:.3f}",
            f"{report.max_delta:.3f}",
            status,
        )

    console.print(table)

    for dim, report in reports.items():
        worst = sorted(report.deltas, key=lambda d: -abs(d.delta))[:1]
        for d in worst:
            if abs(d.delta) > 0.001:
                console.print(
                    f"\n[yellow]worst {dim}:[/yellow] {d.case_id} "
                    f"expected={d.expected:.2f}, actual={d.actual:.2f} "
                    f"(Δ={d.delta:+.2f})"
                )
                if d.rationale:
                    console.print(f"  [dim]judge said:[/dim] {d.rationale[:200]}")

    if any_uncalibrated:
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# eval — Stage 6: regression detection (compare current run to baseline)
# ---------------------------------------------------------------------------


@eval_app.command("compare")
def eval_compare(
    current: Path = typer.Option(
        Path("evals/output/last_run.json"),
        "--current",
        "-c",
        help="Path to current run result JSON.",
    ),
    baseline: Path = typer.Option(
        Path("evals/baseline/main-baseline.json"),
        "--baseline",
        "-b",
        help="Path to baseline run result JSON to compare against.",
    ),
    threshold: float = typer.Option(
        0.05,
        "--threshold",
        "-t",
        help="Maximum allowed regression per dimension (default 0.05 = 5%).",
    ),
    pr_comment: Path | None = typer.Option(
        None,
        "--pr-comment",
        help="If set, write a Markdown PR comment summary to this path.",
    ),
) -> None:
    """Compare current eval run to a baseline and detect regressions.

    Exits 0 if no dimension regresses by more than `threshold`. Exits 1 if
    any dimension regresses more, or if the current run failed any
    threshold check at all. Designed for use as the gating step in CI.
    """
    from banksafe.eval.regression import compare_runs, render_comparison_table
    from banksafe.eval import load_run_result

    if not current.exists():
        console.print(f"[red]Current run not found at {current}[/red]")
        raise typer.Exit(code=2)
    if not baseline.exists():
        console.print(
            f"[yellow]No baseline at {baseline} — skipping regression check. "
            "Commit the current run as the baseline if it represents healthy behavior.[/yellow]"
        )
        # No baseline = first run. Don't fail; record current as candidate.
        return

    current_run = load_run_result(current)
    baseline_run = load_run_result(baseline)
    report = compare_runs(current_run, baseline_run, regression_threshold=threshold)

    render_comparison_table(report, console)

    if pr_comment is not None:
        from banksafe.eval.regression import render_pr_comment

        pr_comment.parent.mkdir(parents=True, exist_ok=True)
        pr_comment.write_text(render_pr_comment(report), encoding="utf-8")
        console.print(f"\n[dim]PR comment markdown written to {pr_comment}[/dim]")

    if report.has_regressions or not current_run.overall_passed:
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _render_run_result(result) -> None:
    """Pretty-print a RunResult to the console."""
    console.print(
        Panel.fit(
            f"Dataset: [cyan]{result.dataset}[/cyan]   "
            f"Agent: [cyan]{result.agent_name}[/cyan]   "
            f"Model: [cyan]{result.agent_model}[/cyan]\n"
            f"Cases: {result.case_count}   Duration: {result.duration_s:.1f}s",
            title="Run Summary",
        )
    )

    table = Table(title="Dimension scores", show_lines=False)
    table.add_column("Dimension", style="cyan")
    table.add_column("Mean", justify="right")
    table.add_column("Min", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("Threshold", justify="right")
    table.add_column("Status", justify="center")

    for s in result.dimension_summaries:
        status = "[green]PASS[/green]" if s.passed else "[red]FAIL[/red]"
        table.add_row(
            s.dimension,
            f"{s.mean_score:.3f}",
            f"{s.min_score:.3f}",
            f"{s.max_score:.3f}",
            f"{s.fail_threshold:.2f}",
            status,
        )
    console.print(table)

    overall = "[green]PASSED[/green]" if result.overall_passed else "[red]FAILED[/red]"
    console.print(f"[bold]Overall:[/bold] {overall}")


# ---------------------------------------------------------------------------
# top-level
# ---------------------------------------------------------------------------


@app.command("version")
def version() -> None:
    """Print the package version."""
    from banksafe import __version__

    console.print(f"banksafe-evalops {__version__}")


if __name__ == "__main__":
    app()
