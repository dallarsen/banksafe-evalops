"""LLM-as-judge evaluators.

Each judge scores one dimension on a 0.0-1.0 scale:

  - accuracy       — factual correctness vs. expected behavior  (LLM)
  - grounding      — claims supported by retrieved policy        (LLM)
  - hallucination  — absence of fabricated/contradicted content  (LLM)
  - pii            — personal data leakage detection             (deterministic regex)
  - refusal        — appropriate decline behavior                (LLM)
  - tone           — professional, neutral, advisory             (LLM)

PII is deliberately rule-based for auditability and zero-cost operation.
The five LLM-based judges share infrastructure in `llm_judge.py` so the
per-dimension judges only need to provide a rubric prompt.
"""

from banksafe.judges.accuracy import AccuracyJudge
from banksafe.judges.base import BaseJudge, JudgeResult
from banksafe.judges.grounding import GroundingJudge
from banksafe.judges.hallucination import HallucinationJudge
from banksafe.judges.llm_judge import LLMJudge
from banksafe.judges.pii import PIIJudge
from banksafe.judges.refusal import RefusalJudge
from banksafe.judges.tone import ToneJudge

# Canonical judge order. The eval runner uses this for consistent reporting.
ALL_JUDGE_CLASSES: list[type[BaseJudge]] = [
    AccuracyJudge,
    GroundingJudge,
    HallucinationJudge,
    PIIJudge,
    RefusalJudge,
    ToneJudge,
]


def build_default_judges() -> list[BaseJudge]:
    """Instantiate the canonical judge stack with default settings."""
    return [cls() for cls in ALL_JUDGE_CLASSES]


__all__ = [
    "ALL_JUDGE_CLASSES",
    "AccuracyJudge",
    "BaseJudge",
    "GroundingJudge",
    "HallucinationJudge",
    "JudgeResult",
    "LLMJudge",
    "PIIJudge",
    "RefusalJudge",
    "ToneJudge",
    "build_default_judges",
]
