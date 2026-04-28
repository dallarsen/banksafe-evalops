"""Shared data schemas for evaluation.

These Pydantic models define the contract between the agent (system under test)
and the evaluation harness. Every agent must return an `AgentResponse`, and
every eval test case is an `EvalCase`.

Keeping these as plain data classes (not tied to any framework) means we can
swap Strands for LangGraph, Bedrock, or anything else without touching the
eval pipeline.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """A single tool invocation made by the agent during a turn."""

    name: str = Field(..., description="Name of the tool that was called.")
    input: dict[str, Any] = Field(default_factory=dict, description="Arguments passed to the tool.")
    output: str = Field("", description="String representation of the tool's return value.")


class AgentResponse(BaseModel):
    """The complete output of one agent turn.

    The eval harness consumes this — judges read `output_text`, grounding judges
    inspect `tool_calls`, and observability layers read `latency_ms` and `usage`.
    """

    output_text: str = Field(..., description="Final natural-language answer from the agent.")
    tool_calls: list[ToolCall] = Field(
        default_factory=list,
        description="Ordered list of tool calls made during this turn.",
    )
    latency_ms: float = Field(0.0, description="Wall-clock time in milliseconds.")
    usage: dict[str, int] = Field(
        default_factory=dict,
        description="Token usage: {'input_tokens': N, 'output_tokens': N}.",
    )
    model: str = Field("", description="Model identifier that produced this response.")
    error: str | None = Field(None, description="Populated only if the agent failed to respond.")


class EvalCase(BaseModel):
    """A single test case in an evaluation dataset."""

    id: str = Field(..., description="Stable identifier, e.g. 'comp-001'.")
    input: str = Field(..., description="The user query or prompt to send to the agent.")
    category: str = Field(..., description="Topic area, e.g. 'gdpr', 'dora', 'aml'.")
    expected_behavior: str = Field(
        ...,
        description="Plain-language description of what a correct answer looks like.",
    )
    ground_truth_citations: list[str] = Field(
        default_factory=list,
        description="Policy IDs the agent should cite, e.g. ['policy:gdpr', 'policy:dora'].",
    )
    trap_type: str | None = Field(
        None,
        description=(
            "If non-null, this case is designed to elicit a specific failure mode. "
            "Values: 'hallucination', 'pii_leak', 'out_of_scope', 'investment_advice', "
            "'jailbreak', 'ambiguous'."
        ),
    )
    must_refuse: bool = Field(
        False,
        description="If true, the correct behavior is to decline to answer.",
    )
