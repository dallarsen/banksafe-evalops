# Setup Instructions — Stage 6 Update

This is the showpiece stage. **GitHub Actions CI** that runs your eval pipeline on every PR, compares scores against a committed baseline, posts a results table as a PR comment, and blocks merges when regressions are detected.

This is the single most impressive piece for the email to hiring managers. It turns "I built an eval framework" into "I built an EvalOps framework that gates production deployments."

---

## What this stage adds

- `src/banksafe/eval/regression.py` — comparison engine producing structured `RegressionReport`s
- `src/banksafe/agents/stub.py` — deterministic stub agent for cheap CI
- `evals/baseline/main-baseline.json` — synthetic baseline for the regression check
- `.github/workflows/tests.yml` — fast CI (every push, free)
- `.github/workflows/live-eval.yml` — full-eval CI (manual or `run-eval` label, ~$2/run)
- New CLI command: `banksafe eval compare`
- 7 new tests (47 total now)
- Stage 6 entry in study guide
- Version bump 0.4.0 → 0.6.0 (we're skipping 0.5 since Stage 5 was deferred)

---

## How to apply

### 1. Unzip Stage 6 over your existing folder

```bash
cd ~/Desktop
unzip -o ~/Downloads/banksafe-evalops-stage6.zip -d ~/Desktop/
```

### 2. Verify version

```bash
cd ~/Desktop/banksafe-evalops
grep "^version" pyproject.toml
```

Must show `version = "0.6.0"`.

### 3. Reinstall

```bash
. .venv/bin/activate
pip install -e ".[dev]"
banksafe version
```

Should print `banksafe-evalops 0.6.0`.

### 4. Run the tests

```bash
python -m pytest tests/ -v
```

You should see **47 passed**. Seven new tests verify the regression-comparison engine and PR-comment renderer.

### 5. Try the new `banksafe eval compare` command locally ⭐

```bash
# Simulate what CI does — copy the baseline as if it were the current run
mkdir -p evals/output
cp evals/baseline/main-baseline.json evals/output/last_run.json

# Compare current vs baseline (should be all flat, exit code 0)
banksafe eval compare
```

You should see a comparison table with all dimensions showing `+0.000` and "No regressions detected." Exit code is 0.

Now simulate a regression — drop the accuracy score:

```bash
python -c "
import json
data = json.load(open('evals/output/last_run.json'))
for s in data['dimension_summaries']:
    if s['dimension'] == 'accuracy':
        s['mean_score'] = 0.65
        s['passed'] = False
data['overall_passed'] = False
json.dump(data, open('evals/output/last_run.json', 'w'), indent=2)
"

banksafe eval compare
echo "exit code: $?"
```

You should see `accuracy` flagged as `REGRESSION` with `Δ = -0.270`, and exit code 1. **This is exactly what CI uses to block the merge.**

Restore the baseline before continuing:

```bash
cp evals/baseline/main-baseline.json evals/output/last_run.json
```

### 6. Add your Anthropic API key as a GitHub Secret ⭐

This is required for the `live-eval.yml` workflow to actually run.

1. Go to https://github.com/dallarsen/banksafe-evalops/settings/secrets/actions
2. Click **"New repository secret"**
3. **Name:** `ANTHROPIC_API_KEY`
4. **Secret:** paste your real Anthropic API key (the same one in your `.env`)
5. Click **"Add secret"**

You'll see the secret listed but its value is hidden — that's correct.

### 7. Commit and push

```bash
git add src/banksafe/eval/regression.py src/banksafe/agents/stub.py src/banksafe/agents/__init__.py src/banksafe/cli.py src/banksafe/eval/__init__.py src/banksafe/eval/runner.py evals/baseline/ tests/test_regression.py
git commit -m "feat(stage-6): add regression-comparison engine and CI workflows"

git add .github/workflows/tests.yml .github/workflows/live-eval.yml docs/study-guide.md README.md pyproject.toml src/banksafe/__init__.py SETUP.md
git commit -m "ci: add tests + live-eval workflows with PR-comment regression gating"

git push
```

### 8. Watch CI run ⭐

Open https://github.com/dallarsen/banksafe-evalops/actions

You should see **"Tests & fast checks"** run on your push. It should complete in under 2 minutes with a green checkmark. **Take a screenshot of this** — green CI on a project with judges, calibration, and regression detection is the screenshot that goes in your hiring-manager email.

### 9. (Optional) Trigger the live eval ⭐

If you want to see the full thing in action — the live-eval workflow running the real evaluation against the real Anthropic API and posting a comment to a PR:

1. Create a new branch with a small change:
   ```bash
   git checkout -b demo-pr
   echo "" >> README.md
   git add README.md
   git commit -m "demo: trigger live eval"
   git push -u origin demo-pr
   ```
2. Open https://github.com/dallarsen/banksafe-evalops/pulls and create a PR from `demo-pr` to `main`
3. Add the label `run-eval` to the PR
4. Wait ~5-10 minutes
5. The workflow runs, posts a comment with the full regression table

This costs ~$2 of API credit. **The PR comment that lands is the second key screenshot for your email.** Once it's done, close the PR without merging (it was just a demo).

---

## What just got real

You now have **production-grade CI gating** for an LLM-based system:

- Every push runs unit tests + a self-check of the regression engine (free, fast)
- PRs labeled `run-eval` get a full live evaluation with PR comment
- Regressions beyond 5pp on any dimension automatically block merges
- The baseline is version-controlled so updates require deliberate review

The framework is now genuinely an *EvalOps* system, not just an evaluation library.

---

## Reply when done

Reply with:
- **"Stage 6 done"** + (ideally) screenshots of green CI and any PR comment → final stage (Stage 7: polish + Medium article + email draft)
- **"CI failed: [paste the actions log]"** → I'll debug

If you want to stop here and ship the email tomorrow, what you have right now is genuinely impressive:
- Working compliance agent
- 32-case eval dataset
- 6 calibrated judges
- 47 tests passing
- CI/CD with regression gating
- ~$3-5 of API credit spent
- Demonstrated and documented

That's a portfolio piece. Stage 7 just makes it shine.
