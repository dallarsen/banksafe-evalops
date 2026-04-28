"""Tests for the evaluation dataset loader.

These verify the loader correctly parses, validates, and aggregates the
shipping `compliance-v1` dataset. Failing any of these would mean the
dataset itself is malformed — surfaces dataset bugs immediately.
"""

from __future__ import annotations

import pytest

from banksafe.datasets import (
    EvalCase,
    list_datasets,
    load_dataset,
    summarize_dataset,
)


def test_list_datasets_includes_compliance_v1() -> None:
    """The shipping compliance dataset should be discoverable."""
    assert "compliance-v1" in list_datasets()


def test_load_dataset_parses_all_cases() -> None:
    """Every line in compliance-v1.jsonl must parse and validate."""
    cases = load_dataset("compliance-v1")
    # Sanity bounds — we don't pin the exact count to avoid brittleness when
    # adding cases, but it should be at least 30.
    assert len(cases) >= 30
    assert all(isinstance(c, EvalCase) for c in cases)


def test_dataset_ids_are_unique() -> None:
    """Duplicate IDs would silently overwrite results — must be unique."""
    cases = load_dataset("compliance-v1")
    ids = [c.id for c in cases]
    assert len(ids) == len(set(ids))


def test_dataset_covers_all_judge_dimensions() -> None:
    """The dataset should exercise every category we expect to evaluate."""
    cases = load_dataset("compliance-v1")
    categories = {c.category for c in cases}
    expected = {
        "gdpr",
        "dora",
        "aml-kyc",
        "mifid-ii",
        "psd2",
        "code-of-conduct",
        "multi-policy",
        "out-of-scope",
    }
    missing = expected - categories
    assert not missing, f"Missing categories: {missing}"


def test_dataset_includes_trap_cases() -> None:
    """Every important trap type should have at least one case."""
    cases = load_dataset("compliance-v1")
    traps = {c.trap_type for c in cases if c.trap_type}
    expected = {"investment_advice", "pii_leak", "hallucination", "jailbreak", "out_of_scope"}
    missing = expected - traps
    assert not missing, f"Missing trap types: {missing}"


def test_must_refuse_cases_have_no_or_minimal_citations() -> None:
    """When the agent must refuse, ground-truth citations should be empty
    or limited to the code-of-conduct policy that justifies the refusal."""
    cases = load_dataset("compliance-v1")
    for case in cases:
        if not case.must_refuse:
            continue
        for cite in case.ground_truth_citations:
            assert cite == "policy:code-of-conduct", (
                f"Case {case.id}: must_refuse=True but cites {cite}; "
                "refusal cases should only cite code-of-conduct, if anything."
            )


def test_summarize_dataset_aggregates_correctly() -> None:
    stats = summarize_dataset("compliance-v1")
    cases = load_dataset("compliance-v1")
    assert stats.total_cases == len(cases)
    assert stats.must_refuse_count == sum(1 for c in cases if c.must_refuse)
    assert stats.multi_policy_count == sum(
        1 for c in cases if len(c.ground_truth_citations) >= 2
    )
    # Each category in stats should appear in the actual cases.
    actual_categories = {c.category for c in cases}
    assert set(stats.by_category.keys()) == actual_categories


def test_load_dataset_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_dataset("nonexistent-dataset-xyz")
