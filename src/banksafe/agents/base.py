"""Abstract interface every banking agent must implement.

Keeping this minimal — `answer(query) -> AgentResponse` — means the eval
harness never needs to know whether an agent is built with Strands,
LangGraph, Bedrock AgentCore, or a custom ReAct loop. Adding a new agent
type is a matter of subclassing `BaseAgent` and providing `_run`.
"""

from __future__ import annotations

import abc

from banksafe.datasets.schema import AgentResponse


class BaseAgent(abc.ABC):
    """Contract for any agent that participates in evaluation."""

    name: str = "base"

    @abc.abstractmethod
    def answer(self, query: str) -> AgentResponse:
        """Run the agent on a single query and return a structured response.

        Implementations are responsible for:
        - Capturing tool calls into the response (`tool_calls`).
        - Measuring latency in milliseconds (`latency_ms`).
        - Recording token usage where available (`usage`).
        - Recording the model identifier used (`model`).
        - Setting `error` on failure rather than raising (so the eval harness
          can score the failure as part of the run).
        """
        raise NotImplementedError
