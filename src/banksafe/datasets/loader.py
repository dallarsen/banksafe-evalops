"""Loader and statistics for versioned evaluation datasets.

Datasets live in `data/eval_sets/<name>.jsonl`. Each line is a JSON object
matching the `EvalCase` schema. Versioning is by filename — `compliance-v1`,
`compliance-v2`, never mutate an existing file.

Why JSONL? Three reasons:
- Diff-friendly: a one-line addition produces a one-line diff in PRs.
- Streamable: large datasets don't need to fit in memory.
- Portable: every language and tool can read it; no infra dependency.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from pydantic import BaseModel, Field

from banksafe.datasets.schema import EvalCase

# Repo-root-relative location of eval datasets.
_EVAL_SETS_DIR = Path(__file__).resolve().parents[3] / "data" / "eval_sets"


class DatasetStats(BaseModel):
    """Summary statistics for a loaded dataset."""

    name: str = Field(..., description="Dataset filename without extension.")
    total_cases: int = Field(..., description="Total number of test cases.")
    by_category: dict[str, int] = Field(default_factory=dict)
    by_trap_type: dict[str, int] = Field(default_factory=dict)
    must_refuse_count: int = Field(0, description="Number of cases where refusal is correct.")
    multi_policy_count: int = Field(
        0, description="Cases requiring 2+ ground-truth citations."
    )


def list_datasets() -> list[str]:
    """Return the names (without extension) of all available eval datasets."""
    if not _EVAL_SETS_DIR.exists():
        return []
    return sorted(p.stem for p in _EVAL_SETS_DIR.glob("*.jsonl"))


def load_dataset(name: str) -> list[EvalCase]:
    """Load and validate every test case in `data/eval_sets/<name>.jsonl`.

    Raises a clean error if the file is missing or any line fails validation.
    Validation surfaces dataset bugs immediately rather than letting them
    silently corrupt eval results.
    """
    path = _EVAL_SETS_DIR / f"{name}.jsonl"
    if not path.exists():
        available = list_datasets()
        raise FileNotFoundError(
            f"Eval dataset not found: {name!r}. Available: {available}"
        )

    cases: list[EvalCase] = []
    seen_ids: set[str] = set()

    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw_line in enumerate(fh, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{path}:{line_no}: invalid JSON ({exc.msg})"
                ) from exc
            try:
                case = EvalCase(**payload)
            except Exception as exc:
                raise ValueError(f"{path}:{line_no}: schema mismatch — {exc}") from exc
            if case.id in seen_ids:
                raise ValueError(
                    f"{path}:{line_no}: duplicate case id {case.id!r}"
                )
            seen_ids.add(case.id)
            cases.append(case)

    return cases


def summarize_dataset(name: str) -> DatasetStats:
    """Compute summary statistics for a dataset without keeping cases in memory long-term."""
    cases = load_dataset(name)
    by_cat = Counter(c.category for c in cases)
    by_trap = Counter(c.trap_type or "<none>" for c in cases)
    return DatasetStats(
        name=name,
        total_cases=len(cases),
        by_category=dict(by_cat),
        by_trap_type=dict(by_trap),
        must_refuse_count=sum(1 for c in cases if c.must_refuse),
        multi_policy_count=sum(1 for c in cases if len(c.ground_truth_citations) >= 2),
    )
