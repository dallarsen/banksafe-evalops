"""LLM-as-judge evaluators.

Stage 4 will populate this package with multi-dimensional judges:

- accuracy.py        — factual correctness vs. ground truth
- grounding.py       — claims supported by retrieved policy
- hallucination.py   — claims contradicting source documents
- pii.py             — personal data leakage detection
- refusal.py         — appropriate decline behavior
- tone.py            — professional, neutral, advisory-not-prescriptive
- calibration.py     — golden-set agreement harness

Until then, this package is intentionally empty.
"""
