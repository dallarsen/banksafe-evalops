"""Calibration harness — judging the judges.

Loads a golden set of hand-labeled `(case, response, expected_score)`
tuples, runs each judge against the corresponding pre-recorded responses,
and reports per-dimension Mean Absolute Error (MAE) plus the worst-case
disagreements.

Why MAE instead of correlation? On a 0-1 scale with limited samples, MAE
is more interpretable: a 0.10 MAE means "the judge is on average 10
percentage points off the human label." Correlation can hide systematic
bias.

A judge is considered CALIBRATED if MAE is below 0.15 across the golden
set for that dimension. Above that, the rubric prompt likely needs work.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from banksafe.datasets.schema import AgentResponse, EvalCase, ToolCall
from banksafe.judges import build_default_judges
from banksafe.judges.base import BaseJudge, JudgeResult

_CALIBRATION_DIR = Path(__file__).resolve().parents[3] / "data" / "calibration"


class CalibrationItem(BaseModel):
    """A single hand-labeled calibration tuple."""

    case_id: str
    dimension: str
    case: EvalCase
    response: AgentResponse
    expected_score: float = Field(..., ge=0.0, le=1.0)
    label_notes: str = ""


class CalibrationDelta(BaseModel):
    """Disagreement between judge score and expected score."""

    case_id: str
    dimension: str
    expected: float
    actual: float
    delta: float
    rationale: str = ""


class CalibrationReport(BaseModel):
    """Per-dimension calibration summary."""

    dimension: str
    sample_count: int
    mean_absolute_error: float
    max_delta: float
    calibrated: bool = Field(
        ...,
        description="True if MAE is below the calibration threshold (default 0.15).",
    )
    deltas: list[CalibrationDelta] = Field(default_factory=list)


CALIBRATION_THRESHOLD = 0.15


def load_golden_set(name: str = "golden-v1") -> list[CalibrationItem]:
    """Load and validate the calibration golden set."""
    path = _CALIBRATION_DIR / f"{name}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"Calibration set not found: {path}")

    items: list[CalibrationItem] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            payload = json.loads(line)
            case = EvalCase(
                id=payload["case_id"],
                input=payload["input"],
                category=payload["category"],
                expected_behavior=payload["expected_behavior"],
                ground_truth_citations=payload.get("ground_truth_citations", []),
                trap_type=payload.get("trap_type"),
                must_refuse=payload.get("must_refuse", False),
            )
            tool_calls = [
                ToolCall(**tc) for tc in payload.get("agent_tool_calls", [])
            ]
            response = AgentResponse(
                output_text=payload["agent_response"],
                tool_calls=tool_calls,
                model="(pre-recorded)",
            )
            items.append(
                CalibrationItem(
                    case_id=payload["case_id"],
                    dimension=payload["dimension"],
                    case=case,
                    response=response,
                    expected_score=float(payload["expected_score"]),
                    label_notes=payload.get("label_notes", ""),
                )
            )
            if items[-1].dimension not in {
                "accuracy",
                "grounding",
                "hallucination",
                "pii",
                "refusal",
                "tone",
            }:
                raise ValueError(
                    f"{path}:{line_no}: unknown dimension {items[-1].dimension!r}"
                )
    return items


def run_calibration(
    name: str = "golden-v1",
    judges: list[BaseJudge] | None = None,
    threshold: float = CALIBRATION_THRESHOLD,
) -> dict[str, CalibrationReport]:
    """Run calibration and return one report per dimension."""
    items = load_golden_set(name)
    judge_list = judges if judges is not None else build_default_judges()
    judges_by_dim: dict[str, BaseJudge] = {j.dimension: j for j in judge_list}

    # Group items by dimension for per-judge scoring.
    by_dim: dict[str, list[CalibrationItem]] = {}
    for item in items:
        by_dim.setdefault(item.dimension, []).append(item)

    reports: dict[str, CalibrationReport] = {}
    for dim, dim_items in by_dim.items():
        judge = judges_by_dim.get(dim)
        if judge is None:
            continue
        deltas: list[CalibrationDelta] = []
        for item in dim_items:
            result: JudgeResult = judge.score(item.case, item.response)
            delta_val = result.score - item.expected_score
            deltas.append(
                CalibrationDelta(
                    case_id=item.case_id,
                    dimension=dim,
                    expected=item.expected_score,
                    actual=result.score,
                    delta=delta_val,
                    rationale=result.rationale,
                )
            )

        abs_deltas = [abs(d.delta) for d in deltas]
        mae = sum(abs_deltas) / len(abs_deltas) if abs_deltas else 0.0
        max_delta = max(abs_deltas) if abs_deltas else 0.0
        reports[dim] = CalibrationReport(
            dimension=dim,
            sample_count=len(deltas),
            mean_absolute_error=mae,
            max_delta=max_delta,
            calibrated=mae <= threshold,
            deltas=deltas,
        )
    return reports
