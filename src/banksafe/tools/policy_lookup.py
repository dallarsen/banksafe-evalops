"""Mock policy lookup tool for the compliance agent.

Simulates retrieval against an internal regulation database. In production,
this would back onto an actual vector store or document service. For
evaluation purposes, a deterministic keyword index is *better* — it gives us
a stable ground-truth retrieval surface that doesn't shift run-to-run, so
when an eval regression appears, we know it came from the agent or judge
layer and not from a flaky retriever.

The tool is registered with Strands via the `@tool` decorator; the docstring
is what the model sees when deciding whether to call it.
"""

from __future__ import annotations

from pathlib import Path

from strands import tool

# Policy corpus lives at <repo>/data/policies relative to this file.
_POLICY_DIR = Path(__file__).resolve().parents[3] / "data" / "policies"


def _load_policy_corpus() -> dict[str, str]:
    """Load all policies from disk into an in-memory dict keyed by policy ID."""
    corpus: dict[str, str] = {}
    if not _POLICY_DIR.exists():
        return corpus
    for path in sorted(_POLICY_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        # The policy ID is encoded in the second line: `# ID: policy:gdpr`
        policy_id = path.stem  # filename without extension
        for line in text.splitlines()[:5]:
            if line.lower().startswith("# id:"):
                policy_id = line.split(":", 1)[1].strip().split()[-1]
                break
        corpus[policy_id] = text
    return corpus


_CORPUS = _load_policy_corpus()


# Curated synonym map. In production this would be a vector retriever; for
# evaluation we want determinism, so we use explicit keyword routing.
_KEYWORDS: dict[str, list[str]] = {
    "policy:gdpr": [
        "gdpr",
        "personvern",
        "data protection",
        "personal data",
        "privacy",
        "datatilsynet",
        "breach notification",
        "right to be forgotten",
        "data subject",
        "consent",
    ],
    "policy:dora": [
        "dora",
        "operational resilience",
        "ict risk",
        "incident reporting",
        "incident classification",
        "tlpt",
        "penetration test",
        "third-party risk",
        "ict third party",
        "finanstilsynet incident",
    ],
    "policy:aml-kyc": [
        "aml",
        "kyc",
        "money laundering",
        "hvitvaskingsloven",
        "customer due diligence",
        "cdd",
        "edd",
        "enhanced due diligence",
        "pep",
        "politically exposed",
        "sanctions",
        "suspicious transaction",
        "str",
        "okokrim",
    ],
    "policy:mifid-ii": [
        "mifid",
        "verdipapirhandelloven",
        "investment advice",
        "suitability",
        "appropriateness",
        "client classification",
        "retail client",
        "professional client",
        "best execution",
        "inducement",
        "product governance",
    ],
    "policy:psd2": [
        "psd2",
        "payment services",
        "strong customer authentication",
        "sca",
        "open banking",
        "aisp",
        "pisp",
        "tpp",
        "third party provider",
        "unauthorized transaction",
        "surcharging",
    ],
    "policy:code-of-conduct": [
        "code of conduct",
        "ethics",
        "conflict of interest",
        "whistleblow",
        "ai tool",
        "ai assistant",
        "acceptable use",
        "confidentiality",
        "best interest",
    ],
}


def _score(query: str, policy_id: str) -> int:
    """Number of keyword hits for `policy_id` in `query` (case-insensitive)."""
    q = query.lower()
    return sum(1 for kw in _KEYWORDS.get(policy_id, []) if kw in q)


@tool
def policy_lookup(query: str, max_results: int = 2) -> str:
    """Search DNB internal policy documents for relevant excerpts.

    Use this whenever the user asks about a regulation, internal rule, or
    compliance procedure. Returns the most relevant policies as Markdown
    with their IDs (e.g. `policy:gdpr`). Always cite the policy ID when
    using its content in an answer.

    Args:
        query: Plain-language description of the topic to look up.
        max_results: Maximum number of policy documents to return (1-3).

    Returns:
        Concatenated Markdown of the top-matching policies, or a "no match"
        message if nothing scored above zero.
    """
    if not _CORPUS:
        return "ERROR: policy corpus not loaded. Verify data/policies/ exists."

    capped = max(1, min(max_results, 3))
    scored = [(pid, _score(query, pid)) for pid in _CORPUS]
    scored = [(pid, s) for pid, s in scored if s > 0]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    if not scored:
        return (
            f"No policies matched the query: {query!r}. "
            f"Available policy IDs: {sorted(_CORPUS.keys())}."
        )

    parts: list[str] = []
    for pid, score in scored[:capped]:
        parts.append(f"--- {pid} (relevance: {score}) ---\n{_CORPUS[pid]}")
    return "\n\n".join(parts)


@tool
def list_policies() -> str:
    """List every policy available in the internal policy library.

    Use this when the user asks what policies exist or when you need to
    confirm a topic is covered before answering.
    """
    if not _CORPUS:
        return "ERROR: policy corpus not loaded."
    lines = ["Available DNB internal policies:"]
    for pid in sorted(_CORPUS.keys()):
        # Pull first heading from each policy as a label.
        first_heading = next(
            (line for line in _CORPUS[pid].splitlines() if line.startswith("# Policy:")),
            f"# Policy: {pid}",
        )
        label = first_heading.removeprefix("# Policy:").strip()
        lines.append(f"  - {pid}: {label}")
    return "\n".join(lines)
