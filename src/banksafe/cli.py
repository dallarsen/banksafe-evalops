"""Command-line interface for BankSafe EvalOps.

Available subcommands grow per stage:

    banksafe agent ask "<query>"        # ask the compliance agent
    banksafe agent demo                 # run the sample queries
    banksafe eval list                  # list available datasets
    banksafe eval show <dataset>        # summary stats for a dataset
    banksafe eval cases <dataset>       # browse test cases

Stage 4+ will add:
    banksafe eval run --dataset <name>
    banksafe eval calibrate
"""

from __future__ import annotations

import typer
from rich.console import Console
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
    help="Inspect and (later) run evaluations.",
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
# eval commands (Stage 3: dataset inspection only)
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
    dataset: str = typer.Argument(..., help="Dataset name (without .jsonl), e.g. 'compliance-v1'.")
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
        table.add_row(
            case.id,
            case.category,
            case.trap_type or "",
            refuse_marker,
            case.input,
        )

    console.print(table)
    if len(cases) > limit:
        console.print(f"[dim]Showing {limit} of {len(cases)}. Use --limit to see more.[/dim]")


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
