# BankSafe EvalOps

> CI/CD evaluation framework for agentic banking assistants. Catches quality, safety, and compliance regressions *before* they reach production.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Built with Claude](https://img.shields.io/badge/Built_with-Claude-orange.svg)](https://www.anthropic.com/claude)

---

## The Problem

Banks deploying agentic AI systems face a unique evaluation challenge. A single change — a prompt tweak, a model upgrade, a new retrieval source, a swapped MCP tool — can silently introduce:

- **Hallucinations** in regulatory advice
- **PII leakage** in customer-facing responses
- **Policy violations** (e.g., unauthorized investment recommendations)
- **Citation drift** away from authoritative internal sources
- **Latency or cost regressions** that break SLOs

Manual QA doesn't scale. Generic LLM eval frameworks don't understand banking context. **BankSafe EvalOps fills that gap.**

## What This Is

A reusable evaluation platform that:

1. **Runs multi-dimensional LLM-as-judge evaluation** on agentic banking assistants — accuracy, citation grounding, hallucination, PII leakage, refusal appropriateness, tone
2. **Calibrates judges** against a small human-labeled golden set to validate consistency before trusting them
3. **Tracks every experiment in MLflow** — prompts, models, datasets, metrics, and judge artifacts
4. **Integrates with GitHub Actions** to automatically detect regressions on every pull request, comment results inline, and *block merges* when critical thresholds are breached
5. **Emits OpenTelemetry traces** for end-to-end observability into agent and judge behavior

The reference implementation evaluates an **Internal Compliance Assistant** — a Strands-based agent that answers DNB-internal questions about Norwegian banking regulations (GDPR, DORA, AML, MiFID II, PSD2) using a mock policy retrieval tool. The framework is designed to extend to other agent types (customer support, loan guidance, fraud triage) by adding a config and a dataset.

## Architecture

```mermaid
flowchart LR
    PR[Pull Request] --> CI[GitHub Actions]
    CI --> Eval[Eval Runner]
    Eval --> Agent[Compliance Agent<br/>Strands + Anthropic]
    Agent --> Tools[Mock Policy<br/>Lookup Tool]
    Eval --> Judges[LLM-as-Judge<br/>Multi-dimensional]
    Judges --> Calibrate[Calibration<br/>Harness]
    Eval --> MLflow[(MLflow<br/>Tracking)]
    Eval --> OTel[(OTel Traces)]
    Eval --> Gate{Regression<br/>Detected?}
    Gate -- Yes --> Block[Block PR]
    Gate -- No --> Pass[Allow Merge]
```

See [`docs/architecture.md`](docs/architecture.md) for component details.

## Quick Start

```bash
# Clone and enter
git clone https://github.com/dallarsen/banksafe-evalops.git
cd banksafe-evalops

# Install (Python 3.11+ required)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run a sample evaluation (after Stage 4)
banksafe agent demo
```

## Try the Compliance Agent (Stage 2)

After installing, run the bundled demo to see the agent answer three sample queries:

```bash
banksafe agent demo
```

Or ask your own:

```bash
banksafe agent ask "What is DNB's deadline for reporting a major ICT incident under DORA?"
```

The agent will retrieve relevant policies via the `policy_lookup` tool, cite policy IDs in its answer, decline out-of-scope or investment-advice questions, and return a structured response capturing the full tool trajectory.

## Browse the Evaluation Dataset (Stage 3)

The `compliance-v1` dataset contains 32 carefully-crafted test cases covering every policy area, multi-policy scenarios, and traps for each judge dimension (PII leak, hallucination, investment advice, jailbreak, out-of-scope).

```bash
# List datasets
banksafe eval list

# Summary statistics
banksafe eval show compliance-v1

# Browse cases (filter by category or trap type)
banksafe eval cases compliance-v1 --category gdpr
banksafe eval cases compliance-v1 --trap pii_leak
```

## Project Structure

```
banksafe-evalops/
├── src/banksafe/
│   ├── agents/          # Strands-based banking agents + base interface
│   ├── tools/           # Mock internal tools (policy lookup, etc.)
│   ├── judges/          # LLM-as-judge evaluators (Stage 4)
│   ├── datasets/        # Eval dataset loaders & shared schema
│   ├── tracking/        # MLflow + OTel integration (Stage 5)
│   └── cli.py           # banksafe command-line entry point
├── data/
│   ├── policies/        # Synthetic regulatory documents (GDPR, DORA, AML, …)
│   └── eval_sets/       # Versioned evaluation datasets (Stage 3)
├── evals/               # Eval runner & demo scripts
├── docker/              # MLflow + OTel collector compose (Stage 5)
├── .github/workflows/   # CI/CD evaluation pipeline (Stage 6)
├── docs/                # Architecture, extension guide, study guide
└── tests/
```

## Key Features

| Feature | Implementation |
|---|---|
| Multi-dimensional eval | Accuracy, grounding, hallucination, PII, refusal, tone |
| Judge calibration | Cross-model + human golden-set validation |
| Experiment tracking | MLflow with runs, params, metrics, artifacts |
| Observability | OpenTelemetry traces for agent + judge calls |
| CI/CD gating | GitHub Actions with PR comments + merge blocking |
| Reproducibility | Docker-composed MLflow & collector |
| Extensibility | Add a new agent in <1 day via config + dataset |

## Extending to Other Agents

The framework is intentionally generic. To evaluate a new agent (e.g., Loan Guidance):

1. Add agent definition under `src/banksafe/agents/` (subclass `BaseAgent`)
2. Add eval dataset under `data/eval_sets/loan-guidance-v1.jsonl`
3. Define dimension weights in `configs/loan-guidance.yaml`
4. Register the agent in the eval runner

See [`docs/extending.md`](docs/extending.md) for a full walkthrough.

## Tech Stack

**Python · Strands · Anthropic API · MLflow · OpenTelemetry · Docker · GitHub Actions · Pydantic**

Designed to be portable to AWS Bedrock + AgentCore by swapping the model provider in `src/banksafe/agents/` (the `BaseAgent` interface is provider-agnostic).

## Built with AI-First Engineering

This project itself was built using AI-assisted engineering — Claude (via Claude.ai Projects) for architecture, design decisions, and judge prompt authoring; standard developer tooling for implementation. The codebase, judge rubrics, and synthetic datasets were iteratively refined through structured AI collaboration. See [`docs/study-guide.md`](docs/study-guide.md) for design rationale.

## Status & Roadmap

- [x] Stage 1: Foundation & scaffolding
- [x] Stage 2: Compliance agent + mock policy tool
- [x] Stage 3: Synthetic evaluation dataset (32 cases)
- [ ] Stage 4: LLM-as-judge pipeline + calibration
- [ ] Stage 5: MLflow + OTel integration
- [ ] Stage 6: GitHub Actions CI gating
- [ ] Stage 7: Documentation & demo polish

## License

MIT — see [LICENSE](LICENSE).
