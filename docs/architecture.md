# Architecture

## Overview

BankSafe EvalOps is structured as a **layered evaluation platform** with four logical layers:

1. **System Under Test (SUT)** — the agent being evaluated
2. **Evaluation Harness** — orchestrates eval runs, manages datasets
3. **Judge Layer** — LLM-as-judge with calibration
4. **Tracking & Gating** — MLflow, OTel, and CI integration

## Layer 1: System Under Test

The reference SUT is a **Compliance Assistant** built with Strands. It exposes a single `answer(query: str) -> AgentResponse` interface so the eval harness is agnostic to the agent's internals.

The agent has access to one mock tool (`policy_lookup`) that simulates retrieval from an internal regulation database. This is intentionally minimal — the framework's value is in the *evaluation*, not the agent.

## Layer 2: Evaluation Harness

The harness:
- Loads a versioned eval dataset (JSONL)
- Runs each test case through the SUT
- Captures the response, tool trajectory, latency, and token usage
- Hands results to the judge layer

Datasets are versioned in `data/eval_sets/` and never mutated — new versions are appended (`compliance-v1.jsonl`, `compliance-v2.jsonl`).

## Layer 3: Judge Layer

Six independent judges score each response:

| Judge | What it measures |
|---|---|
| Accuracy | Factual correctness vs. ground truth |
| Grounding | Are claims supported by retrieved policy? |
| Hallucination | Statements contradicting source documents |
| PII Leakage | Presence of personal data in output |
| Refusal | Did the agent appropriately refuse out-of-scope? |
| Tone | Professional, neutral, advisory-not-prescriptive |

**Calibration:** A small (~15-example) human-labeled golden set is run on each judge change to verify the judge still agrees with humans within a tolerance. If calibration drops below threshold, the judge is rejected.

**Multi-model:** The primary judge runs on `claude-sonnet-4-5`. A secondary judge runs on `claude-haiku-4-5` to flag disagreements — significant divergence is a signal that the rubric is ambiguous.

## Layer 4: Tracking & Gating

- **MLflow** logs every run as an experiment with parameters (prompt hash, model, dataset version), metrics (per-dimension scores), and artifacts (full judge outputs).
- **OpenTelemetry** instruments agent calls and judge calls for end-to-end traces.
- **GitHub Actions** runs the eval suite on every PR, compares results against the baseline (last successful main run), comments results on the PR, and exits non-zero if a configured regression threshold is breached.

## Design Decisions

See [`study-guide.md`](study-guide.md) for the rationale behind each architectural choice.
