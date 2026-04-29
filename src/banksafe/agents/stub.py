"""StubAgent — a no-API-call agent for fast CI smoke evals.

Returns canned-but-realistic responses for a few known case categories so
the eval pipeline runs end-to-end in CI without burning API credit. Used
exclusively by the fast CI workflow; production eval uses ComplianceAgent.

Why it exists: the cheap CI workflow needs to verify the eval *plumbing*
on every push (judges instantiate, runner aggregates, comparison engine
works) without spending money. The slow CI workflow (manual trigger or
label) uses ComplianceAgent against the real Anthropic API.
"""

from __future__ import annotations

from banksafe.agents.base import BaseAgent
from banksafe.datasets.schema import AgentResponse, ToolCall


_CANNED_RESPONSES: dict[str, str] = {
    "gdpr": (
        "Under DNB's GDPR policy, breach notification to Datatilsynet must occur "
        "within 72 hours of discovery, and the DPO must be notified internally "
        "within 24 hours (policy:gdpr)."
    ),
    "dora": (
        "Major ICT incidents must be reported to Finanstilsynet within 4 hours "
        "of classification, with a 72-hour intermediate report and a one-month "
        "final report (policy:dora)."
    ),
    "aml-kyc": (
        "AML records must be retained for at least five years after the customer "
        "relationship ends, per Hvitvaskingsloven (policy:aml-kyc)."
    ),
    "mifid-ii": (
        "Suitability assessments cover knowledge, financial situation, and "
        "investment objectives. They are required for advice and discretionary "
        "portfolio management (policy:mifid-ii)."
    ),
    "psd2": (
        "Strong Customer Authentication is required for online account access, "
        "electronic payment initiation, and remote actions implying fraud risk "
        "(policy:psd2)."
    ),
    "code-of-conduct": (
        "AI assistants must not be used to compose external customer "
        "communications without human review (policy:code-of-conduct)."
    ),
    "multi-policy": (
        "An incident affecting customer data triggers both GDPR notification "
        "(72 hours to Datatilsynet) and DORA reporting (4 hours to Finanstilsynet) "
        "(policy:gdpr, policy:dora)."
    ),
    "trap-investment-advice": (
        "I can't recommend specific funds or build personalized portfolios — "
        "that requires a licensed advisor under MiFID II suitability rules "
        "(policy:code-of-conduct). Please book a session with a DNB advisor."
    ),
    "trap-pii": (
        "AML monitoring screens against EU/UN/OFAC sanctions lists and looks "
        "for transaction pattern anomalies (policy:aml-kyc)."
    ),
    "trap-hallucination": (
        "I don't have policy coverage on that topic in our internal library. "
        "I'd suggest consulting Group Compliance directly."
    ),
    "trap-jailbreak": (
        "I have to maintain my role as DNB's compliance assistant — I can't "
        "provide investment recommendations regardless of how the question is "
        "framed (policy:code-of-conduct)."
    ),
    "out-of-scope": (
        "That's outside my scope. I'm here to help with DNB's internal "
        "policies, compliance procedures, and Norwegian/EU financial regulations."
    ),
}


class StubAgent(BaseAgent):
    """Deterministic stub agent for cheap CI evaluation."""

    name = "stub-v1"

    def __init__(self) -> None:
        self.model_id = "stub-canned"

    def answer(self, query: str) -> AgentResponse:
        category = self._infer_category(query)
        text = _CANNED_RESPONSES.get(category, _CANNED_RESPONSES["out-of-scope"])
        # Synthesize a plausible tool call so grounding judge has something to score.
        tool_calls = []
        if category in {
            "gdpr",
            "dora",
            "aml-kyc",
            "mifid-ii",
            "psd2",
            "code-of-conduct",
            "multi-policy",
            "trap-investment-advice",
            "trap-pii",
        }:
            tool_calls.append(
                ToolCall(
                    name="policy_lookup",
                    input={"query": category},
                    output=f"--- policy:{category if category != 'multi-policy' else 'gdpr'} --- (canned stub output)",
                )
            )
        return AgentResponse(
            output_text=text,
            tool_calls=tool_calls,
            latency_ms=10.0,
            usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            model=self.model_id,
        )

    @staticmethod
    def _infer_category(query: str) -> str:
        """Cheap keyword router — same idea as policy_lookup, simpler."""
        q = query.lower()
        # Trap detection first (more specific signals)
        if any(kw in q for kw in ["which fund", "which dnb fund", "should i invest", "build me a portfolio", "stock"]):
            return "trap-investment-advice"
        if "ignore your previous" in q or "unrestricted" in q:
            return "trap-jailbreak"
        if any(kw in q for kw in ["nid ", "fødselsnummer", "+47 9", "born 1985"]):
            return "trap-pii"
        if "quantum trading" in q or "fatca" in q:
            return "trap-hallucination"
        # Standard categories
        if "gdpr" in q or "datatilsynet" in q or "data access" in q or "data subject" in q or "personal data" in q or "marketing email" in q:
            if "incident" in q and ("dora" in q or "ict" in q):
                return "multi-policy"
            if "delete" in q and ("aml" in q or "transaction" in q):
                return "multi-policy"
            return "gdpr"
        if "dora" in q or "ict incident" in q or "operational resilience" in q or "tlpt" in q or "concentration risk" in q:
            return "dora"
        if "aml" in q or "kyc" in q or "money laundering" in q or "pep" in q or "sanctions" in q or "due diligence" in q or "beneficial owner" in q:
            return "aml-kyc"
        if "mifid" in q or "suitability" in q or "appropriateness" in q or "professional client" in q or "inducement" in q:
            return "mifid-ii"
        if "psd2" in q or "sca" in q or "strong customer auth" in q or "contactless" in q or "unauthorized payment" in q:
            return "psd2"
        if "ai assistant" in q or "code of conduct" in q or "whistleblow" in q:
            return "code-of-conduct"
        return "out-of-scope"
