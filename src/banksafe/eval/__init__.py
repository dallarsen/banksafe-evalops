"""Evaluation orchestration — runs cases through agents and judges.

  - runner.run_evaluation(cases, agent, judges) -> RunResult
  - RunResult, CaseResult, DimensionSummary types
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
