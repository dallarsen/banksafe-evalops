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


---

## Stage 4: LLM-as-Judge Pipeline + Calibration

This stage is the technical heart of BankSafe EvalOps. Six judges score every (case, response) pair on 0.0-1.0, the runner aggregates them into a `RunResult`, and the calibration harness validates that judges agree with human labels before we trust them in CI.

### Why six judges instead of one?

A single "overall quality" score hides the failure modes that matter. A response can be:

- Factually correct but ungrounded (no citations) — accuracy 1.0, grounding 0.3
- Well-grounded but wrong tone (preachy, alarmist) — grounding 1.0, tone 0.4
- Concise and well-toned but hallucinates a deadline — tone 1.0, hallucination 0.2
- Refuses correctly but echoes PII from the query — refusal 1.0, pii 0.0

By scoring six dimensions independently, regressions become attributable. If a prompt change drops only `tone` while accuracy and grounding stay flat, we know exactly what to look at. A single composite score would just say "things got worse."

**Interview answer:** *"Independent dimensions make regressions attributable. Composite scores hide which behavior shifted, which is the most important signal CI can give a developer."*

### Why is the PII judge rule-based instead of LLM-based?

This is the most opinionated design choice in Stage 4 and the one I'd defend most strongly. Three reasons:

1. **Auditability.** A compliance officer can read the regex patterns in `pii.py` and verify the detection rules. They can't audit an LLM's internal reasoning the same way.
2. **Reliability.** Regex doesn't have a 5% false-negative rate. For PII at a bank, that's the difference between zero leaks and ~5 leaks per 100 cases.
3. **Cost.** Zero LLM calls means the PII check runs on every CI build for free.

The trade-off is that regex misses sophisticated PII (names alone, paraphrased identifiers). For names we rely on the LLM judges to flag egregious leaks via their rationale, and we'd add a Norwegian-name NER model in production.

**Interview answer:** *"PII detection is a place where deterministic, auditable rules matter more than coverage. Regex is fast, free, and reviewable; the false-negative trade-off on sophisticated PII is acceptable given the rest of the judge stack catches it via different paths."*

### Why do all LLM judges share a base class?

`LLMJudge` handles the API call, JSON parsing, error capture, and clamping into [0.0, 1.0]. Subclasses provide only the rubric prompt. This:

- Keeps each judge file under 50 lines.
- Means a Strands → LiteLLM swap or a Bedrock migration touches one file (`llm_judge.py`), not six.
- Makes the testing strategy clear: test the parser exhaustively (deterministic logic), validate the rubrics via calibration.

### Why JSON output instead of tool-use?

Anthropic's tool-use parameter would give us schema-validated structured output. JSON-in-text is simpler to debug and easier to swap providers (every modern LLM does JSON; tool-use semantics differ). The tradeoff is that we need a defensive parser (regex fallback for the case where the model includes preamble), which is in `_parse_judge_json`.

If we ever standardize on AWS Bedrock and the JD-named tools, switching to tool-use is a single-method change in `LLMJudge.score`.

### Why does the calibration harness use MAE instead of correlation?

On a 0-1 scale with ~12 calibration samples, MAE is more interpretable than correlation:

- **MAE = 0.10** means "the judge is on average 10 percentage points off the human label."
- **Correlation = 0.85** means... well, it depends on the variance, the slope, and a bunch of other things that make it harder to communicate to non-statisticians.

MAE also catches systematic bias: a judge that's consistently 0.15 too high will have 0 correlation effect (perfect rank correlation) but show up immediately as MAE = 0.15. We threshold at MAE ≤ 0.15 because below that, the judge is "good enough" given the noise in human labels themselves.

**Interview answer:** *"MAE is more interpretable on a small sample and catches systematic bias correlation hides. The 0.15 threshold is loose enough to absorb human-labeling noise but tight enough that any worse means the rubric needs work."*

### Why are the rubric prompts so detailed?

Each rubric has explicit anchors at 1.0, 0.8, 0.5, 0.2, and 0.0. Without anchors, LLM judges drift toward the middle of the scale (everything becomes 0.7) and small differences in agent behavior produce no signal. With anchors, the judge has a calibrated yardstick.

The system prompt also enforces the *same* anchor scale across all judges, so a 0.8 in accuracy means the same level of "near-perfect with minor issue" as a 0.8 in tone. That cross-judge consistency matters for a composite/weighted view in Stage 5.

### Why a 6-case calibration set instead of 60?

- **Reviewability.** A human can inspect every calibration case in 10 minutes.
- **Stability.** Adding cases to compliance-v1 doesn't invalidate calibration results; the calibration set is its own frozen artifact.
- **Cost.** 12 cases × 1 LLM call each = ~$0.20 to recalibrate after a prompt change.

In production, the calibration set grows as we discover edge cases — but the seed value comes from covering the anchor points (1.0 examples, 0.0 examples) for each judge, which 12 cases handle.

### Why does the runner persist results as JSON?

Three reasons aligned with the rest of the project's "no-infra" stance:

1. **CI artifact.** GitHub Actions can upload the JSON as a build artifact. No external service required.
2. **Baseline comparison.** Stage 6 compares the current run's JSON against the last main-branch run's JSON to detect regressions. Pure file diff.
3. **Reproducibility.** A `RunResult` JSON contains the dataset name, agent name, model ID, every per-case score, and every judge rationale. Anyone can replay the analysis offline.

### Why are judge errors treated as 0.0 in aggregation?

Silent test skipping is the worst failure mode in eval. If a judge crashes on case 17 of 32, you don't want the dimension's mean to be computed across only 31 cases — that hides the failure. By scoring the error as 0.0, the aggregate immediately reflects the broken judge and CI fails. The error message is preserved in `JudgeResult.error` for debugging.

### Likely interview questions

- *"How would you scale this from 6 judges to 30?"* — The judge interface is one method (`score`). Adding a judge is one new file plus one entry in `ALL_JUDGE_CLASSES`. The runner doesn't change. The CLI doesn't change. The constraint becomes calibration cost — at 30 judges × N golden cases, you start wanting to parallelize judge calls per case.
- *"How do you handle judge disagreement between primary and secondary models?"* — The framework supports it (we configure `judge_secondary_model` in settings) but Stage 4 doesn't use cross-model checks yet. Stage 5 adds them: if Sonnet and Haiku disagree by more than 0.30 on a case, we flag the rubric as ambiguous and surface it in the run report.
- *"How would you prevent the grounding judge from giving a bad score just because the agent paraphrased?"* — The rubric explicitly says "Reasonable paraphrasing of retrieved content" is fine. The accuracy judge handles paraphrasing-as-correctness. The grounding judge focuses on "is this in the retrieved content at all" not "is this verbatim."
- *"What if regulations change after you deploy?"* — Each policy has a `# Last reviewed` line; the eval dataset is versioned. When a regulation changes, we update the policy doc, version-bump the dataset (compliance-v2), recalibrate, and ship. Old versions stay in git for reproducing historical runs.
- *"Why not use a third-party eval framework like Ragas or LangSmith?"* — They're great for general LLM-app eval but they don't natively know about Norwegian banking compliance, multi-policy reasoning, or the specific trap categories DNB cares about. The framework here is small enough (~700 lines of judges + runner) that we own all of it. We could integrate Ragas as one judge dimension if useful.


---

## Stage 5: MLflow + OpenTelemetry Tracking

### Why MLflow over LangSmith, Weights & Biases, or a custom dashboard?

MLflow won this slot for four concrete reasons:

1. **It runs on a laptop with one Docker command.** No SaaS account, no API key, no billing. A bank's evaluation framework needs to be deployable inside a regulated environment without external dependencies.
2. **Open-source and self-hostable.** DNB can run it inside their VPC, behind their SSO, with their security review. Same code path as the demo.
3. **It's the de facto standard in the JD's tech stack.** "MLflow" is named explicitly. A custom dashboard would be technically fine but signals "not familiar with the ecosystem."
4. **The data model fits eval natively.** An MLflow `run` maps cleanly to a single `eval run` — params, metrics, artifacts. We don't need to bend the abstraction.

LangSmith is excellent for end-to-end LLM tracing but is closed-source and SaaS-only — a non-starter for a bank's CI pipeline. Weights & Biases is similar trade-off. The custom dashboard option is appealing only if your team already has the infra; otherwise you're rebuilding what MLflow gives you.

**Interview answer:** *"MLflow runs locally with one Docker command, is open-source so DNB can host it in-VPC, and is named in the JD's tech stack. The eval-run abstraction maps cleanly to MLflow's run abstraction, so the integration is shallow rather than fighting the framework."*

### Why the file-fallback when the MLflow server is unreachable?

CI and dev environments shouldn't fail because the tracking server is briefly down. The flow is:

1. Try the configured `MLFLOW_TRACKING_URI` (typically `http://localhost:5000`)
2. If the host:port doesn't accept a TCP connection within 1 second, fall back to `file:./mlruns`
3. Continue the eval run; the user is warned but the result is still produced

This is critical for two scenarios:
- **First-time developers** who haven't started Docker yet. They get a working eval, see results in their terminal, and can later open the MLflow UI when convenient.
- **CI runs** where a tracking server isn't deployed. The file artifact is sufficient for regression detection (Stage 6), and we don't block the build on infra.

The TCP-level probe is much faster than letting the MLflow HTTP client time out — that can hang for many seconds.

**Interview answer:** *"Tracking should never block evaluation. A TCP-level reachability probe with a 1-second timeout, followed by graceful fallback to local file storage, means the eval pipeline runs whether or not the tracking server is healthy. The result artifact is the source of truth either way."*

### What does each MLflow run capture?

Per run, we log:

**Parameters (immutable, identify the experiment):**
- `dataset` (e.g., compliance-v1)
- `agent` (e.g., compliance-v1)
- `model` (e.g., claude-sonnet-4-5)
- `case_count`
- `system_prompt_hash` — first 12 chars of SHA-256 of the system prompt; lets us detect prompt drift across runs without exposing the full prompt
- `judge_primary_model`, `judge_secondary_model`

**Metrics (numerical, comparable across runs):**
- For each of 6 dimensions: `<dim>_mean`, `<dim>_min`, `<dim>_max`, `<dim>_passed` (0/1)
- `duration_s`, `case_count`, `overall_passed`

**Artifacts:**
- `run_result/run_result.json` — full RunResult including every per-case judge rationale, agent trajectory, latency, and tokens

This is enough to:
- Compare two runs side-by-side in the MLflow UI
- Plot dimension scores over time as prompts evolve
- Drill into any failing case via the rationale artifact
- Reproduce a historical run by replaying with the same params

### Why hash the system prompt instead of logging it?

Two reasons. The prompt itself is large (1+ KB), repeated across hundreds of runs. The hash is 12 chars and changes iff the prompt changes — that's the only signal we actually need. Plus it sidesteps any concern about logging proprietary prompt content into a tracking server that might end up logged elsewhere.

The full prompt lives in version control where it belongs; the run links to a specific commit via standard MLflow git integration if configured.

### Why OpenTelemetry instead of MLflow's own logging?

MLflow tracks **runs**. OTel traces **operations within runs**. Different abstractions, both useful.

OTel gives us spans like:
```
eval.run
├── eval.case (case_id=comp-001)
│   ├── agent.answer
│   └── judge.score (judge=accuracy)
│   ├── judge.score (judge=grounding)
│   ├── … (6 judges total)
└── eval.case (case_id=comp-002)
    └── …
```

This lets a developer answer "why is the run slow" or "which judge call failed" by looking at one trace, not by correlating MLflow metrics with timestamped logs.

OTel is also the open standard — when DNB stands up Tempo, Jaeger, Datadog, Honeycomb, or anything else, the framework already speaks the right protocol. Setting `OTEL_EXPORTER_OTLP_ENDPOINT` to the production collector is the entire integration.

**Interview answer:** *"MLflow tracks runs; OTel traces operations. Both matter and they answer different questions. OTel is the open standard, so the eval pipeline emits spans the bank's existing observability stack already understands."*

### Why is OTel export opt-in?

Importing the OTel SDK is fast, but exporting spans to a collector that doesn't exist isn't free — connection retries, log spam, occasionally timeouts. For local dev without a collector, we want the eval to run fast and silent. Setting `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317` (or `BANKSAFE_OTEL_CONSOLE=1` for stdout) opts you in. Default behavior: spans are created, attributes are recorded, but nothing is exported, so overhead is minimal.

### Why a Docker Compose stack instead of running MLflow with `pip install`?

Three reasons:

1. **Reproducibility.** The compose file pins MLflow and OTel collector versions. Anyone can stand up the same stack in 30 seconds, with no host-Python conflicts.
2. **Realistic operationally.** In production, the tracking server is its own service with its own lifecycle — not a Python process the developer accidentally kills with Ctrl+C. The compose file mirrors that topology.
3. **Volumes for persistence.** SQLite + artifact directory both live on a Docker volume, so MLflow data survives container restarts (and a `make down`/`make up` cycle preserves history).

The fallback path (`make` not required) ensures developers without Docker still get value.

### Likely interview questions

- *"What if MLflow goes down mid-eval?"* — The eval keeps running; logging failures are caught and logged but never propagate. The local file artifact is always written. Worst case: one run misses MLflow but the result.json is on disk and can be backfilled.
- *"How would you compare two prompt versions?"* — Each run has a `system_prompt_hash` parameter. Filter MLflow's UI to runs with the same dataset/agent, group by prompt hash, look at dimension means. The artifact contains the full per-case data if you need to drill down.
- *"How would you scale to many concurrent runs?"* — MLflow's HTTP backend handles this fine. The current eval is sequential; for parallelism we'd batch judge calls per case (Anthropic supports this) before parallelizing across cases. OTel handles concurrent spans natively.
- *"How would you secure the MLflow server in production?"* — Run behind your auth proxy (Okta/Azure AD), enforce TLS, restrict the artifact volume to a least-privileged service account. None of this changes the framework; it's deployment.
- *"Why log per-case rationales as artifacts and not metrics?"* — Metrics are scalars. Rationales are unbounded text. Artifacts are designed exactly for this — large blobs you might want to inspect but don't query.


---

## Stage 6: GitHub Actions CI Gating

This is the stage that makes the project name "EvalOps" actually mean something. Every PR runs an evaluation, the result is compared to a committed baseline, and merges are blocked if any dimension regresses beyond a configurable threshold.

### Why two workflows instead of one?

Real EvalOps systems can't afford to run a full LLM-judge eval on every commit:

- One full eval costs ~$1-3 in API credit
- One full eval takes 5-10 minutes
- A typical team makes 10+ pushes per day

If we ran the live eval on every push, we'd be looking at $10-30/day in API spend per developer plus a CI cycle that's too slow for tight iteration. So we split:

**Fast CI (`tests.yml`)** runs on every push and PR. It exercises the entire eval pipeline without spending API credit:
- All unit tests
- A regression-engine smoke check that compares the committed baseline against itself (must always show zero deltas)

This catches plumbing bugs in seconds, costs zero, and runs on every commit.

**Live eval (`live-eval.yml`)** runs on demand:
- Manually via the Actions tab (any branch)
- Automatically when a PR gets the `run-eval` label

It runs the real ComplianceAgent against the real Anthropic API, scores all six dimensions, compares to the baseline, posts a results comment to the PR, and blocks merge if regressions are detected.

This is the standard pattern at well-run ML/AI shops. Cheap fast checks every commit; expensive comprehensive checks before merge.

**Interview answer:** *"Splitting cheap and expensive checks is the only way LLM-eval CI scales. Every push gets fast feedback for free; comprehensive runs happen on demand or before merge. The framework gates merges on the comprehensive check, but doesn't tax day-to-day iteration."*

### Why a baseline file in version control instead of "last main run"?

A baseline that lives in `evals/baseline/main-baseline.json` is:

- **Deterministic.** The same baseline every time, regardless of which order CI runs in or whether main has flaky runs.
- **Version-controlled.** Updates require a deliberate PR, with the diff visible. You can't accidentally regress and then auto-update the baseline.
- **Reproducible offline.** A developer can run the same comparison locally with `banksafe eval compare` and see exactly what CI will see.

The alternative — pulling the last successful main-branch run from MLflow — is a great Stage 7 enhancement, but introduces infrastructure dependency and a moving target. For shipping today, the committed-file approach is more robust.

The trade-off is operational: someone has to deliberately update the baseline when intended improvements ship. We make that easy via a manual `workflow_dispatch` trigger that produces an artifact you can commit.

### Why is regression different from threshold failure?

The compare command tests two things:

1. **Threshold pass/fail** (per dimension) — e.g., `accuracy_mean ≥ 0.80`. This is the eval's own opinion about whether the system is good enough, regardless of history.
2. **Regression vs baseline** — e.g., `accuracy_mean dropped > 5 percentage points vs main`. This is detection of *changes* in behavior.

Both can fail independently. A run might:
- Pass thresholds but regress (shipping degradation that's still above the floor — flagged as regression)
- Fail thresholds without regressing (the system was already broken before this PR — flagged as failure but not regression)
- Both — the project is shipping a bad change *and* the system was already below threshold

The PR comment differentiates these so reviewers see the actual story.

### Why post results as a PR comment instead of just a status check?

Two reasons:

1. **Discoverability.** A status check goes red but doesn't tell you *what* failed. Reviewers have to dig into the Actions log, find the right step, and read the output. A PR comment puts the dimension scores right in the conversation thread.
2. **Audit trail.** The comment becomes part of the PR's permanent history. When someone asks six months later "why did we change this prompt?", the conversation around the original PR shows the eval data that drove the decision.

The comment is generated in two passes: the comparison engine produces a structured `RegressionReport`, then `render_pr_comment` formats it as Markdown. That separation lets us reuse the same data for future Slack notifications, dashboards, etc.

**Interview answer:** *"A status check tells you something failed; a PR comment tells you what. Plus the comment becomes part of the audit trail — when you're shipping AI to a regulated environment, the conversation around 'why did we change this' needs to be reconstructable years later."*

### Why does the live-eval workflow continue on regression instead of failing immediately?

The job runs `compare` with `continue-on-error: true`, then explicitly fails at the end based on the saved exit code. This is intentional:

- Even when there's a regression, we want to **upload the artifacts** (full RunResult JSON, the PR comment) so reviewers can inspect them.
- We want to **post the PR comment** so the regression is visible.
- *Then* we fail the job to mark the merge as blocked.

A naive `set -e` style "fail fast" would prevent all of that — you'd see a red X with no detail.

### Why a stub agent in the framework instead of "skip eval in fast CI"?

The fast CI workflow doesn't use the StubAgent today (it just self-checks the regression engine). But shipping a `StubAgent` with the framework matters for two reasons:

1. **Developer ergonomics.** A new contributor can run `banksafe eval run` against StubAgent locally with no API key, get realistic-looking output, and verify their changes haven't broken the runner. That's 30 seconds of iteration vs minutes of API calls.
2. **Future fast CI work.** A future iteration could run a *partial* eval in fast CI — StubAgent + the deterministic PII judge alone — to catch trajectory-related regressions without API spend. That work isn't in Stage 6 but the building block is.

### Likely interview questions

- *"How do you keep the baseline from going stale?"* — Two paths. (1) Manual: when an intended improvement ships, update `main-baseline.json` in the same PR. (2) Automated (Stage 7+): a scheduled workflow that runs the live eval against main weekly and opens a "baseline refresh" PR if scores drift.
- *"What if Anthropic has an outage during a CI run?"* — The live-eval job has a 30-minute timeout and uploads partial artifacts on failure. The eval result has an `error` field per agent response, so a partial run with API errors is visible — those cases score 0 on every dimension and surface in the regression comment as drops. We can either retry, or — better — fall back to a smaller subset and ship a `--limit 10` quick-check.
- *"How do you handle false-positive regressions from LLM non-determinism?"* — Three layers: temperature=0 on judges, calibrated rubrics with human-validated MAE, and a 5pp threshold that absorbs reasonable noise. If those aren't enough we'd add multi-seed averaging — run each case 3 times, take the median — but that triples cost.
- *"How would this scale to 10 agents and 5 datasets?"* — Same workflow file, parameterized via matrix strategy in GitHub Actions. Each combination produces its own artifact and PR comment. The tricky bit is per-PR cost; we'd add labels like `run-eval-loan-guidance` to scope which agent's eval gets triggered.
- *"How would you migrate this CI to AWS CodeBuild or Jenkins?"* — The CLI is the contract. `banksafe eval run`, `banksafe eval compare --pr-comment ...`, exit codes 0/1. Any CI system that can run those commands and post a comment to a PR provider works. The GitHub-Actions-specific bits (`actions/github-script`, label triggers) move to whichever provider's idiom.

