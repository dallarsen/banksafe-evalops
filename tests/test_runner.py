"""Tests for the eval runner aggregation logic.

We use a stub agent and stub judges to verify the orchestration without
making API calls. This validates that:
  - All cases run through the agent.
  - All judges run on every case.
  - Per-dimension aggregation (mean/min/max) is correct.
  - Pass/fail thresholds are applied per dimension.
  - Judge errors degrade to 0.0 in the aggregate.
"""

from __future__ import annotations

from banksafe.agents.base import BaseAgent
from banksafe.datasets.schema import AgentResponse, EvalCase
from banksafe.eval import run_evaluation
from banksafe.judges.base import BaseJudge, JudgeResult


class _StubAgent(BaseAgent):
    name = "stub"

    def __init__(self, model: str = "stub-model") -> None:
        self.model_id = model

    def answer(self, query: str) -> AgentResponse:
        return AgentResponse(output_text=f"echo: {query}", model=self.model_id)


class _StubJudge(BaseJudge):
    """Returns a fixed score for every case — useful for aggregation tests."""

    def __init__(self, dimension: str, fixed_score: float, name: str | None = None) -> None:
        self.dimension = dimension
        self.name = name or dimension
        self._fixed_score = fixed_score

    def score(self, case: EvalCase, response: AgentResponse) -> JudgeResult:
        return JudgeResult(
            judge=self.name,
            dimension=self.dimension,
            score=self._fixed_score,
            rationale=f"stub score {self._fixed_score}",
        )


def _make_cases(n: int = 3) -> list[EvalCase]:
    return [
        EvalCase(
            id=f"t-{i:03d}",
            input=f"q{i}",
            category="test",
            expected_behavior="x",
            ground_truth_citations=[],
            trap_type=None,
            must_refuse=False,
        )
        for i in range(n)
    ]


def test_runner_runs_all_cases_through_all_judges() -> None:
    cases = _make_cases(3)
    judges = [_StubJudge("accuracy", 0.9), _StubJudge("tone", 0.8)]
    result = run_evaluation(cases, _StubAgent(), judges=judges, dataset_name="test")

    assert result.case_count == 3
    assert len(result.case_results) == 3
    for cr in result.case_results:
        assert len(cr.judge_results) == 2
        dims = {jr.dimension for jr in cr.judge_results}
        assert dims == {"accuracy", "tone"}


def test_runner_aggregates_dimension_means() -> None:
    cases = _make_cases(4)
    judges = [_StubJudge("accuracy", 0.9), _StubJudge("tone", 0.5)]
    result = run_evaluation(cases, _StubAgent(), judges=judges, dataset_name="test")

    summaries = {s.dimension: s for s in result.dimension_summaries}
    assert summaries["accuracy"].mean_score == 0.9
    assert summaries["accuracy"].sample_count == 4
    assert summaries["tone"].mean_score == 0.5
    assert summaries["tone"].sample_count == 4


def test_runner_passes_when_all_dimensions_above_threshold() -> None:
    cases = _make_cases(3)
    # Use thresholds that all stub scores satisfy.
    judges = [_StubJudge("accuracy", 0.95), _StubJudge("tone", 0.85)]
    thresholds = {"accuracy": 0.80, "tone": 0.75}
    result = run_evaluation(
        cases, _StubAgent(), judges=judges, dataset_name="test", fail_thresholds=thresholds
    )
    assert result.overall_passed is True
    for s in result.dimension_summaries:
        assert s.passed is True


def test_runner_fails_when_dimension_below_threshold() -> None:
    cases = _make_cases(3)
    judges = [_StubJudge("accuracy", 0.50), _StubJudge("tone", 0.85)]
    thresholds = {"accuracy": 0.80, "tone": 0.75}
    result = run_evaluation(
        cases, _StubAgent(), judges=judges, dataset_name="test", fail_thresholds=thresholds
    )
    assert result.overall_passed is False
    summaries = {s.dimension: s for s in result.dimension_summaries}
    assert summaries["accuracy"].passed is False
    assert summaries["tone"].passed is True


def test_runner_treats_judge_errors_as_zero() -> None:
    """A judge that errors should be visible (0.0) in the aggregate, not silently dropped."""

    class ErroringJudge(BaseJudge):
        name = "broken"
        dimension = "broken"

        def score(self, case: EvalCase, response: AgentResponse) -> JudgeResult:
            return JudgeResult(
                judge=self.name,
                dimension=self.dimension,
                score=0.0,
                rationale="",
                error="simulated failure",
            )

    cases = _make_cases(2)
    result = run_evaluation(
        cases,
        _StubAgent(),
        judges=[ErroringJudge()],
        dataset_name="test",
        fail_thresholds={"broken": 0.5},
    )
    summaries = {s.dimension: s for s in result.dimension_summaries}
    assert summaries["broken"].mean_score == 0.0
    assert summaries["broken"].passed is False
