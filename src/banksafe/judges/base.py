"""Base classes and result types for judges.

Every judge produces a `JudgeResult` containing a 0.0-1.0 score and a
human-readable rationale. The rationale is what makes the framework
auditable — a hiring manager (or compliance officer) can read why the
judge scored an answer the way it did.
"""

from __future__ import annotations

import abc

from pydantic import BaseModel, Field

from banksafe.datasets.schema import AgentResponse, EvalCase


class JudgeResult(BaseModel):
    """The output of a single judge invocation."""

    judge: str = Field(..., description="Identifier of the judge, e.g. 'accuracy'.")
    dimension: str = Field(..., description="Evaluation dimension, e.g. 'grounding'.")
    score: float = Field(..., ge=0.0, le=1.0, description="0.0-1.0 score (1.0 = perfect).")
    rationale: str = Field("", description="Human-readable justification.")
    model: str = Field("", description="Judge model used, if LLM-based.")
    error: str | None = Field(None, description="If non-null, scoring failed.")


class BaseJudge(abc.ABC):
    """Contract every judge must implement."""

    name: str = "base"
    dimension: str = "base"

    @abc.abstractmethod
    def score(self, case: EvalCase, response: AgentResponse) -> JudgeResult:
        """Score one (case, response) pair on this judge's dimension.

        Implementations must return a JudgeResult with `score` in [0.0, 1.0]
        and a `rationale` string. Failures should be captured in `error`
        rather than raised — eval runs should continue even when one judge
        misbehaves.
        """
        raise NotImplementedError
