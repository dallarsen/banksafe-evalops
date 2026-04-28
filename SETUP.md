# Setup Instructions — Stage 3 Update

This file is for **you** (Dallin). Stage 3 adds the evaluation dataset and dataset CLI commands. Follow the steps below.

---

## What this stage adds

- `data/eval_sets/compliance-v1.jsonl` — 32 carefully-crafted test cases
- `src/banksafe/datasets/loader.py` — dataset loader with validation + statistics
- `tests/test_dataset_loader.py` — 8 new tests (19 total now)
- New CLI commands: `banksafe eval list`, `banksafe eval show`, `banksafe eval cases`
- Updated study guide with Stage 3 design rationale
- Version bump 0.2.0 → 0.3.0
- A few internal `__init__.py` files made more substantive (defensive against unzip skipping)

No demo costs API credit this time — Stage 3 is pure dataset work.

---

## How to apply

### 1. Unzip Stage 3 over your existing folder

Stage 3 zip contains the full project — Stage 1 + 2 + 3 combined. Unzip and replace all when prompted. Your `.env` is not in the zip, so it stays put.

> **Tip from last time:** if the zip flow on macOS skipped any files, your `pyproject.toml` will still say `version = "0.1.0"`. Check after unzip with:
> ```bash
> grep "^version" pyproject.toml
> ```
> It should say `version = "0.3.0"`. If not, the unzip didn't fully replace — try again, or use the terminal: `unzip -o ~/Downloads/banksafe-evalops-stage3.zip -d ~/Desktop/`

### 2. Reinstall (version bumped)

```bash
cd ~/Desktop/banksafe-evalops
. .venv/bin/activate
pip install -e ".[dev]"
```

You should see `Successfully installed banksafe-evalops-0.3.0` at the end.

### 3. Verify version

```bash
banksafe version
```

Should print `banksafe-evalops 0.3.0`.

### 4. Run the tests

```bash
pytest tests/ -v
```

You should see **19 passed**. The new ones are in `test_dataset_loader.py` and they verify:
- The shipping dataset is discoverable
- Every case parses and validates
- IDs are unique (no silent overwrites)
- Every category and trap type is represented
- Must-refuse cases don't have ungrounded citations
- Statistics aggregation is correct

### 5. Try the new CLI commands

```bash
# List datasets
banksafe eval list

# Summary statistics for the compliance dataset
banksafe eval show compliance-v1

# Browse cases — try different filters
banksafe eval cases compliance-v1
banksafe eval cases compliance-v1 --category gdpr
banksafe eval cases compliance-v1 --trap pii_leak
banksafe eval cases compliance-v1 --trap investment_advice
```

You'll see something like:
- 32 total cases
- 6 must-refuse cases
- 3 multi-policy cases
- 12 categories
- 5 trap types covered

### 6. Commit and push

```bash
git add data/eval_sets/ src/banksafe/datasets/loader.py src/banksafe/cli.py src/banksafe/demo.py tests/test_dataset_loader.py
git commit -m "feat(stage-3): add compliance-v1 eval dataset, loader, and inspection CLI"

git add docs/study-guide.md README.md pyproject.toml src/banksafe/__init__.py src/banksafe/datasets/__init__.py src/banksafe/judges/__init__.py src/banksafe/tracking/__init__.py SETUP.md
git commit -m "docs: add Stage 3 design rationale to study guide"

git push
```

---

## What just got real

You now have a **versioned evaluation dataset** with 32 cases that:

- Exercise every policy area (4 GDPR, 4 DORA, 4 AML, 3 MiFID II, 3 PSD2, 2 code-of-conduct)
- Include 2 multi-policy cases that require reasoning across two policies
- Include 7 trap cases (2 investment-advice refusals, 2 PII echoes, 2 hallucinations, 1 jailbreak)
- Include 3 out-of-scope refusals
- Each carry a `must_refuse` flag and `ground_truth_citations` for the grounding judge

In Stage 4, the LLM-as-judge pipeline will run each case through your compliance agent and score the responses on six dimensions. **The dataset is what makes that scoring meaningful.**

---

## Reply when done

When `pytest tests/ -v` shows 19 passed and `banksafe eval show compliance-v1` prints the stats table, reply with **"Stage 3 done"** and I'll start Stage 4 (the judges — the technical heart of the project).

If anything errors, paste the output and we'll fix it before moving on.
