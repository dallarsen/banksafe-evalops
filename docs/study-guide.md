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

---

## Stage 2: Compliance Agent + Mock Policy Tool

### Why a separate `BaseAgent` interface?

The eval harness, judges, and tracking layers should never know whether the agent is built with Strands, LangGraph, Bedrock AgentCore, or a hand-rolled ReAct loop. Having a single `answer(query) -> AgentResponse` contract means:

- We can swap agent frameworks without touching the eval pipeline.
- Multiple agent types (compliance, loan, fraud) can share the same eval harness.
- Mock agents are trivial to build for testing the judge layer in isolation.

**Interview answer:** *"The agent interface is intentionally minimal — one method, one return type. That keeps every other layer of the framework provider-agnostic, so DNB teams can plug in whatever agent framework they want and inherit all the evaluation, tracking, and CI gating for free."*

### Why Strands instead of LangGraph or plain Python?

- It's named in the JD's tech stack — strongest signal that DNB is using or evaluating it.
- It's model-agnostic by design (Bedrock, Anthropic, OpenAI, Ollama, …) which matches a bank's likely need to switch between providers based on cost, latency, and data-residency requirements.
- It has first-class MCP support, which is also in the JD.

The cost is that Strands' result API has shifted between versions, so I wrote defensive accessors in `_extract_text`, `_extract_tool_calls`, and `_extract_usage` rather than binding to a specific Strands version. That isolates churn to a few helpers.

**Interview answer:** *"Strands is in your tech stack and its model-agnostic design fits a bank's need to move between providers. I wrote defensive trajectory extraction so the eval framework isn't pinned to a specific Strands release."*

### Why a deterministic keyword retrieval tool instead of a real vector store?

Counterintuitive but important: **for evaluation, deterministic retrieval is better than realistic retrieval.**

A vector store introduces a moving variable — embedding model drift, index updates, ranking changes — that confound the eval signal. If the agent hallucinates, was it because the retriever returned bad context, or because the agent ignored good context? With a deterministic keyword index, we always know what the agent saw, so any quality regression is unambiguously attributable to the agent or judge layer.

In production, the retrieval layer would have its *own* eval harness measuring recall@k and ranking quality. That's a separable concern.

**Interview answer:** *"Deterministic retrieval gives us a stable ground-truth context surface. It means a quality regression in eval is always attributable to the agent or judge — not a flaky retriever. Retrieval quality is its own evaluation problem with its own metrics, and they should be measured separately."*

### Why are the policies synthetic instead of real Norwegian regulations?

Three reasons:

1. **Copyright** — actual regulation text is publicly available but I don't want to reproduce paragraphs verbatim in a public repo.
2. **Demo clarity** — synthetic policies can be tuned to surface specific evaluation behaviors (refusal cases, citation grounding, PII traps).
3. **Honesty** — labeling them as synthetic up-front avoids any impression that the project is a working substitute for real legal interpretation. The framework is the deliverable, not the legal advice.

The policies are written to *feel* realistic — they cite Norwegian regulations by name (Hvitvaskingsloven, Verdipapirhandelloven), reference real authorities (Datatilsynet, Finanstilsynet, Økokrim), and use realistic structural elements (scope, obligations, out-of-scope sections).

**Interview answer:** *"The framework is the product. Using synthetic policies keeps the demo focused on evaluation mechanics and avoids any implication that this replaces legal interpretation."*

### Why are the system prompt rules so explicit?

Each rule in the system prompt maps deliberately to a judge dimension we'll evaluate in Stage 4:

| System prompt rule | Judge it triggers |
|---|---|
| "Use the policy_lookup tool" | Tool-use grounding |
| "Cite the policy ID" | Grounding |
| "If no policy supports a claim, do not make the claim" | Hallucination |
| "Never give personalized investment advice" | Refusal |
| "Never include personal data" | PII Leakage |
| "Refuse out-of-scope" | Refusal |
| "Be concise / professional tone" | Tone |

This makes the system prompt itself an instrumentation layer: changing a rule should produce a measurable shift in the corresponding judge score, and that's exactly the regression-detection story we want to demonstrate in CI.

**Interview answer:** *"The system prompt isn't just behavioral guidance — every rule in it maps to a judge dimension. So a change to the prompt should produce a measurable, attributable shift in eval scores. That's the regression detection signal."*

### Why capture tool trajectories at all?

Final-answer evaluation only catches a fraction of agent failures. The richer story is in the trajectory — wrong tool selection, missing tool calls, redundant calls, or tool-result-ignored patterns. By capturing `tool_calls` on every response, the judge layer (Stage 4) can score *grounding* by checking whether claims in the answer are actually supported by content the agent retrieved.

**Interview answer:** *"Output-only evaluation hides half the failure modes in agentic systems. Capturing the trajectory lets us evaluate whether the agent actually used what it retrieved — that's where grounding and hallucination diverge."*

### Likely interview questions

- *"How would you handle a Strands version bump that changes the result format?"* — The `_extract_*` helpers in `compliance.py` isolate the surface area. A new Strands version would need at most three small fixes there; the rest of the framework is untouched.
- *"Why fail with `error=...` instead of raising?"* — Failures are themselves a signal we want to measure. A timing-out or refusing agent should be visible in the eval report, not crash the run.
- *"How would you make this work with AWS Bedrock instead of Anthropic API?"* — Replace `AnthropicModel(...)` with `BedrockModel(...)` in `compliance.py`. The rest of the codebase is unchanged. The `BaseAgent` interface guarantees this portability.
- *"How does retrieval scale beyond 6 policy documents?"* — In production, swap the keyword router for a vector store fronted by the same `policy_lookup` tool signature. The agent doesn't change, the eval harness doesn't change. Retrieval becomes a separately-evaluated component.

---

*Stages 3–7 sections will be appended as we build.*

---

## Stage 3: Evaluation Dataset

### Why JSONL instead of YAML, CSV, or a database?

JSONL (JSON Lines) — one JSON object per line — is the industry standard for ML evaluation datasets. The reasons matter:

- **Diff-friendly.** Adding a single test case shows up as a single-line PR diff. With YAML or pretty-printed JSON, a one-case addition can produce a 20-line diff if formatting shifts. With CSV you lose nested structure (citations, trap types).
- **Streamable.** Large datasets (10k+ cases) don't need to fit in memory; the loader iterates line by line.
- **Portable.** Every language and tool reads JSONL. No infra dependency, no schema migration, no migration tool needed when you fork the dataset.
- **Versionable.** Each version of the dataset is a separate immutable file (`compliance-v1.jsonl`, `compliance-v2.jsonl`). Git history shows exactly what changed between versions.
- **Reproducible.** Fixing the dataset version in an MLflow run pins the eval to an exact set of cases. Re-running the same eval on the same dataset months later produces directly comparable scores.

**Interview answer:** *"JSONL gives us small diffs, streaming, no infra, and immutable versioning. It's the format I'd reach for any time the dataset is going to live next to source code in version control."*

### Why 32 cases and not 200 or 1000?

Small, hand-crafted, well-covered eval sets outperform large auto-generated ones at the scale this project demonstrates. The dataset is deliberately structured to:

- **Cover every policy area** (GDPR, DORA, AML, MiFID II, PSD2, code-of-conduct) with 3–4 cases each, so each policy contributes signal.
- **Stress every judge dimension** — at least one case per trap type (investment advice, PII leak, hallucination, jailbreak, out-of-scope).
- **Include multi-policy cases** that require the agent to reason across two policies (e.g., a breach that triggers both GDPR notification *and* DORA incident reporting).
- **Stay reviewable by a human in <30 minutes**, so a domain expert can inspect every case for correctness.

In production, this seed dataset would grow to hundreds of cases — but the value of the framework is independent of the dataset size.

**Interview answer:** *"Hand-crafted seed datasets that cover every dimension are more valuable than large auto-generated ones at this stage. Once the framework is in place, scaling the dataset is a separate, almost mechanical exercise."*

### Why include "trap" cases at all?

Most evaluation datasets only include cases the agent should answer correctly. That misses the entire failure-mode surface. Trap cases test the *negative* behaviors:

- **Investment advice traps** verify the refusal judge is doing real work.
- **PII traps** verify the PII judge catches data echoed from the user's prompt.
- **Hallucination traps** ask about regulations *not* in the policy library, so the agent's correct behavior is "I don't know, consult Compliance" — anything else is a hallucination.
- **Jailbreak traps** verify system-prompt adherence under adversarial input.
- **Out-of-scope traps** verify the agent maintains its scope boundaries.

A regression in any of these — say, a future prompt change that makes the agent slightly more agreeable — will show up as a measurable drop in trap-case scores.

**Interview answer:** *"Trap cases turn 'wrong behavior' into a first-class evaluation signal. They're how the framework catches subtle prompt regressions that an output-quality-only eval would miss entirely."*

### Why is `must_refuse` separate from `trap_type`?

`trap_type` describes *why* the case exists (its design intent). `must_refuse` describes *what correct behavior looks like*. They overlap a lot but aren't identical:

- A PII trap case has `trap_type=pii_leak` but `must_refuse=False` — the agent should answer the underlying compliance question, just without echoing the PII.
- A hallucination trap has `trap_type=hallucination` but `must_refuse=False` — the agent should *answer* by stating the policy isn't in the library, not refuse outright.
- A jailbreak attempt has `trap_type=jailbreak` and `must_refuse=True` — those align.

Splitting them lets us write more precise judge logic in Stage 4.

**Interview answer:** *"Trap type is the case's design intent; `must_refuse` is its scoring rule. Keeping them orthogonal lets us write more precise judges."*

### Why ground-truth citations as policy IDs and not full text?

Three reasons:

1. **Stable.** Policy text can be edited; policy IDs are stable identifiers.
2. **Cheaper to author.** Human reviewers can label citations as "this answer should ground in policy:gdpr" without copying paragraphs.
3. **Easy to score.** The grounding judge in Stage 4 will check whether the agent's response cites the expected IDs, with optional fuzzy-match for missing or extra IDs.

### Likely interview questions

- *"How do you prevent overfitting to the eval set?"* — Hold out a portion as a separate "test" dataset that we don't tune against. Real production usage replaces synthetic cases with logged real queries (with PII scrubbed) over time.
- *"How do you keep this dataset evergreen as regulations change?"* — Each dataset version is a frozen artifact. When a regulation changes, we add a new dataset version, rerun the eval, and ship if scores hold. The old version stays in git for reproducibility.
- *"How do you avoid bias in trap cases?"* — Have multiple authors contribute traps; review for representativeness; track per-trap-type pass rates as separate metrics rather than averaging into a global score.
- *"How would you scale this to thousands of cases?"* — Same JSONL format, parallelized eval runs, deduplication via embedding similarity, semi-automated trap generation guided by failure patterns observed in production.

