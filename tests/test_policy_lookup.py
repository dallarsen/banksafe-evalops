"""Tests for the policy_lookup tool.

Verify the deterministic keyword router returns the expected policies for
common queries, and handles edge cases like unknown topics gracefully.
"""

from __future__ import annotations

from banksafe.tools.policy_lookup import _CORPUS, _score


def test_corpus_loaded() -> None:
    """All six policy documents should be loaded from disk."""
    assert set(_CORPUS.keys()) == {
        "policy:gdpr",
        "policy:dora",
        "policy:aml-kyc",
        "policy:mifid-ii",
        "policy:psd2",
        "policy:code-of-conduct",
    }


def test_score_routes_gdpr_query() -> None:
    """GDPR-related queries should match the GDPR policy."""
    assert _score("What is the GDPR breach notification timeline?", "policy:gdpr") > 0
    assert _score("What is the GDPR breach notification timeline?", "policy:psd2") == 0


def test_score_routes_dora_query() -> None:
    """DORA / incident reporting queries should match the DORA policy."""
    assert _score("DORA incident reporting deadline", "policy:dora") > 0


def test_score_routes_aml_query() -> None:
    """AML / suspicious transactions should match aml-kyc."""
    assert _score("How do I report suspicious transactions?", "policy:aml-kyc") > 0


def test_score_handles_unrelated_query() -> None:
    """Unrelated queries should not match any policy."""
    for pid in _CORPUS:
        assert _score("What is the recipe for kjøttkaker?", pid) == 0
