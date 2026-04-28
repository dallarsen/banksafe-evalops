"""Command-line interface for BankSafe EvalOps.

Available subcommands grow per stage:

    banksafe agent ask "<query>"   # ask the compliance agent
    banksafe agent demo            # run the sample queries

Stage 4+ will add:
    banksafe eval run --dataset <name>
    banksafe eval calibrate
"""

from __future__ import annotations

import typer
from rich.console import Console

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
app.add_typer(agent_app)

console = Console()


@agent_app.command("ask")
def ask(query: str = typer.Argument(..., help="Question to ask the compliance agent.")) -> None:
    """Ask the compliance agent a single question."""
    from banksafe.agents import ComplianceAgent
    from banksafe.demo import render

    agent = ComplianceAgent()
    response = agent.answer(query)
    render(response)


@agent_app.command("demo")
def demo() -> None:
    """Run the bundled sample queries against the compliance agent."""
    from banksafe.demo import main

    main()


@app.command("version")
def version() -> None:
    """Print the package version."""
    from banksafe import __version__

    console.print(f"banksafe-evalops {__version__}")


if __name__ == "__main__":
    app()
