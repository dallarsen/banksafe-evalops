"""Evaluation orchestration — runs cases through agents and judges.

Stage 4 ships:
  - runner.run_evaluation(cases, agent, judges) -> RunResult
  - RunResult, CaseResult, DimensionSummary types

Stage 5 will wrap this with MLflow tracking; Stage 6 will run it in CI.
"""

from banksafe.eval.runner import (
    CaseResult,
    DEFAULT_FAIL_THRESHOLDS,
    DimensionSummary,
    RunResult,
    load_run_result,
    run_evaluation,
    save_run_result,
)

__all__ = [
    "CaseResult",
    "DEFAULT_FAIL_THRESHOLDS",
    "DimensionSummary",
    "RunResult",
    "load_run_result",
    "run_evaluation",
    "save_run_result",
]
