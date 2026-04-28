# Study Guide — BankSafe EvalOps

This document explains the *why* behind every design decision in the project. Use it to prepare for interview questions.

> **Note:** This is a living document. Each build stage adds a new section.

---

## Stage 1: Foundation

### Why this directory structure?

The repo is organized by **architectural concern**, not by technology:

- `agents/`, `tools/`, `judges/`, `datasets/`, `tracking/` — these are the layers of the evaluation platform
- A new contributor can find "where do judges live?" in one second

Compare this to a tech-organized layout (`models/`, `controllers/`, `utils/`) which is fine for web apps but obscures *what the system does* in an evaluation framework.

**Interview answer:** *"I organized the codebase around evaluation concerns rather than tech layers because it makes the framework's purpose self-documenting and lowers the friction for other DNB teams to extend it."*

### Why Pydantic Settings for config?

Three reasons:
1. **Type safety** — settings are typed, validated at startup, fail fast on bad config
2. **12-factor compliance** — environment variables are the standard for cloud deployment
3. **Local + CI parity** — `.env` for local dev, real env vars in GitHub Actions, no code change

**Interview answer:** *"Pydantic Settings gives us validated, typed config from environment variables — same pattern works locally with `.env` and in CI without modification."*

### Why MIT license?

Permissive, recognizable, common in evaluation tooling. Not a hill worth dying on.

### Why pin Python 3.11+?

3.11 introduced significant typing improvements (`Self`, exception groups, better error messages) that make the codebase cleaner. 3.10 would also work but 3.11 is a sensible floor in 2026.

### Why a `.env.example` file?

Onboarding. A new contributor (or hiring manager exploring the repo) can copy it to `.env` and immediately see what configuration is required, without reading every Python file to discover env var names.

### Likely interview questions

- *"Why MLflow over Weights & Biases or LangSmith?"* — Answer in Stage 5
- *"Why Strands over LangGraph or plain Python?"* — Answer in Stage 2
- *"How do you prevent secrets from leaking?"* — `.env` is gitignored, real secrets only in CI secret store, `.env.example` shows shape only
- *"Why version eval datasets as JSONL files instead of in a database?"* — Versioning, diffability, reproducibility, no infra dependency. Answered in Stage 3.

---

*Stages 2–7 sections will be appended as we build.*
