"""Tests for trajectory extraction from Strands AgentResult.

These verify our defensive accessors handle the current Strands response
shape correctly. They do not require an API key — we feed in synthetic
result objects.
"""

from __future__ import annotations

from types import SimpleNamespace

from banksafe.agents.compliance import (
    _extract_text,
    _extract_tool_calls,
    _extract_usage,
)


def test_extract_text_from_message_content_blocks() -> None:
    """Strands typically returns message.content as list of text blocks."""
    result = SimpleNamespace(
        message={
            "role": "assistant",
            "content": [
                {"type": "text", "text": "DNB must report major incidents within 4 hours "},
                {"type": "text", "text": "(policy:dora)."},
            ],
        }
    )
    assert _extract_text(result) == (
        "DNB must report major incidents within 4 hours (policy:dora)."
    )


def test_extract_text_from_string_content() -> None:
    """Some result shapes put a string directly on content."""
    result = SimpleNamespace(message={"role": "assistant", "content": "Hello"})
    assert _extract_text(result) == "Hello"


def test_extract_tool_calls_pairs_use_with_result() -> None:
    """Tool uses should be paired with their tool_result blocks by id."""
    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "toolUse",
                    "toolUseId": "tu_1",
                    "name": "policy_lookup",
                    "input": {"query": "DORA incident reporting"},
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "toolResult",
                    "toolUseId": "tu_1",
                    "content": [
                        {"type": "text", "text": "--- policy:dora ---\nMajor incidents..."}
                    ],
                }
            ],
        },
    ]
    result = SimpleNamespace(messages=messages)
    calls = _extract_tool_calls(result)
    assert len(calls) == 1
    assert calls[0].name == "policy_lookup"
    assert calls[0].input == {"query": "DORA incident reporting"}
    assert "policy:dora" in calls[0].output


def test_extract_tool_calls_handles_no_messages() -> None:
    result = SimpleNamespace()
    assert _extract_tool_calls(result) == []


def test_extract_usage_from_metrics() -> None:
    """Strands exposes accumulated_usage on result.metrics."""
    metrics = SimpleNamespace(
        accumulated_usage={"inputTokens": 1234, "outputTokens": 567, "totalTokens": 1801}
    )
    result = SimpleNamespace(metrics=metrics)
    usage = _extract_usage(result)
    assert usage == {"input_tokens": 1234, "output_tokens": 567, "total_tokens": 1801}


def test_extract_usage_handles_missing() -> None:
    result = SimpleNamespace()
    assert _extract_usage(result) == {}
