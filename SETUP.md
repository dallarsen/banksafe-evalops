# Setup Instructions — Stage 4 Update

This is the technical heart of the project. After Stage 4, you have a working evaluation pipeline: agent runs cases, six judges score every response, results aggregate into a pass/fail report.

---

## What this stage adds

- `src/banksafe/judges/` — six judges + base classes + calibration harness
  - `accuracy.py`, `grounding.py`, `hallucination.py`, `refusal.py`, `tone.py` — LLM-based
  - `pii.py` — deterministic regex (auditable, free, fast)
  - `calibration.py` — measures judge agreement with hand-labeled golden set
- `src/banksafe/eval/runner.py` — orchestrator that runs (cases × agent × judges)
- `data/calibration/golden-v1.jsonl` — 12 hand-labeled (case, response, expected_score) tuples
- `tests/test_judges.py`, `tests/test_runner.py` — 21 new tests (40 total now)
- New CLI commands: `banksafe eval calibrate`, `banksafe eval run`
- Stage 4 entry in study guide
- Version 0.3.0 → 0.4.0

---

## How to apply

### 1. Unzip Stage 4 over your existing folder

Use the terminal method we settled on last time, since macOS Finder skipped some files in earlier rounds:

```bash
cd ~/Desktop
unzip -o ~/Downloads/banksafe-evalops-stage4.zip -d ~/Desktop/
```

The `-o` flag forces overwrite without prompting. Your `.env` is not in the zip, so it stays put.

### 2. Verify version updated

```bash
cd ~/Desktop/banksafe-evalops
grep "^version" pyproject.toml
```

Must show `version = "0.4.0"`.

### 3. Reinstall

```bash
. .venv/bin/activate
pip install -e ".[dev]"
banksafe version    # should print: banksafe-evalops 0.4.0
```

### 4. Run the tests

```bash
pytest tests/ -v
```

You should see **40 passed**. The 21 new tests cover:
- 8 PII judge tests (clean responses, NID detection, account/phone/email/date detection, error propagation)
- 8 JSON parser tests (strict, clamping, regex fallback, error cases)
- 5 runner tests (orchestration, aggregation, threshold pass/fail, error handling)

### 5. Calibrate the judges ⭐

This is the first place we spend real API credit on Stage 4. Cost: ~$0.10-0.20.

```bash
banksafe eval calibrate
```

You'll see a calibration table with one row per dimension:

```
Calibration report
Dimension       N    MAE    Max Δ    Status
accuracy        2    0.05   0.10     ✓ calibrated
grounding       2    0.10   0.20     ✓ calibrated
hallucination   2    0.00   0.00     ✓ calibrated
pii             2    0.00   0.00     ✓ calibrated   (rule-based, no LLM call)
refusal         2    0.05   0.10     ✓ calibrated
tone            2    0.05   0.10     ✓ calibrated
```

**MAE ≤ 0.15 = calibrated.** The exact numbers will vary slightly between runs because we use temperature=0.0 but LLMs are still mildly non-deterministic. If any dimension is uncalibrated (MAE > 0.15), the rubric prompt may need work — but for our shipping rubrics this should pass cleanly.

If a dimension fails, paste the output and we'll tune the rubric.

### 6. Run a small evaluation ⭐

Don't run the full 32-case eval yet — let's do a 3-case smoke test first. Cost: ~$0.20.

```bash
banksafe eval run --limit 3
```

You'll see:
- A progress bar as cases run through the agent
- A run summary panel (dataset, agent, model, duration)
- A dimension scores table
- Saved JSON at `evals/output/last_run.json`

The agent should pass at least 4 of 6 dimensions on these 3 cases. If everything passes, run the full eval:

```bash
banksafe eval run
```

This is the big one — 32 cases × 6 judges = 192+ LLM calls. Cost: $1.50-3.00. Takes ~5-10 minutes.

**You don't have to do the full run tonight** — Stage 6's CI will run it for free on every PR. The point is just to verify it works.

### 7. Commit and push

```bash
git add src/banksafe/judges/ src/banksafe/eval/ data/calibration/ src/banksafe/cli.py tests/test_judges.py tests/test_runner.py
git commit -m "feat(stage-4): add 6-dimension judge stack, calibration harness, and eval runner"

git add docs/study-guide.md README.md pyproject.toml src/banksafe/__init__.py SETUP.md
git commit -m "docs: add Stage 4 design rationale to study guide"

git push
```

---

## What just got real

You now have the **complete evaluation pipeline**:

1. A 32-case dataset that exercises every policy area + every trap type
2. A compliance agent built with Strands + Anthropic API
3. Six judges scoring each response: accuracy, grounding, hallucination, PII (regex), refusal, tone
4. A calibration harness that validates judge agreement with human labels (MAE ≤ 0.15)
5. An orchestrator that aggregates per-dimension scores with configurable fail thresholds
6. JSON results artifact suitable for CI baseline comparison

Everything that comes next (MLflow tracking, OTel traces, GitHub Actions CI) is plumbing. **The substantive evaluation system is done.**

---

## Reply when done

When `banksafe eval calibrate` shows all six dimensions calibrated, reply with **"Stage 4 done"** and we move to Stage 5 (MLflow tracking + OpenTelemetry — fast and lightweight).

If anything errors, paste the output and I'll debug.
