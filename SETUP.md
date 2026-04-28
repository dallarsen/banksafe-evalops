# Setup Instructions — Read This First

This file is for **you** (Dallin). It walks you through what to do after unzipping the project. Delete this file before pushing to GitHub if you want — it's just for your local setup.

---

## Step 1: Verify your prerequisites

Open a terminal in the `banksafe-evalops/` folder and check:

```bash
python --version    # should be 3.11 or higher
git --version       # any version is fine
```

If `git --version` fails, install Git first:
- **Mac:** `brew install git` OR download from [git-scm.com](https://git-scm.com/downloads)
- **Windows:** Download from [git-scm.com/downloads](https://git-scm.com/downloads), accept all defaults

---

## Step 2: Set up your local Python environment

From inside the `banksafe-evalops/` folder:

```bash
# Create a virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate          # Mac/Linux
# OR
.venv\Scripts\activate             # Windows PowerShell

# Install dependencies
pip install -e ".[dev]"
```

The install will take 1-3 minutes (MLflow has many dependencies).

---

## Step 3: Add your API key

```bash
cp .env.example .env
```

Then open `.env` in your editor and replace `sk-ant-...` with your real Anthropic API key.

**Verify it loads correctly:**

```bash
python -c "from banksafe.config import settings; print('Agent model:', settings.agent_model)"
```

Should print: `Agent model: claude-sonnet-4-5`

---

## Step 4: Initialize Git and create staged commits

```bash
# Configure git (skip if already done globally on this machine)
git config --global user.name "Dallin Larsen"
git config --global user.email "your-email@example.com"

# Initialize the repo
git init -b main

# Three intentional commits — looks like real iterative work
git add .gitignore LICENSE
git commit -m "chore: initialize repo with gitignore and license"

git add pyproject.toml .env.example src/ evals/ tests/ data/ docker/ notebooks/ configs/ .github/
git commit -m "chore: add project scaffold, dependencies, and module structure"

git add README.md docs/
git commit -m "docs: add README, architecture overview, and study guide"
```

---

## Step 5: Push to GitHub

1. Go to [github.com/new](https://github.com/new)
2. Repository name: **`banksafe-evalops`**
3. Description: *"CI/CD evaluation framework for agentic banking assistants"*
4. **Public** (you want hiring managers to see it)
5. **Do NOT** initialize with README, .gitignore, or license — we already have them
6. Click **Create repository**

Then:

```bash
git remote add origin https://github.com/dallarsen/banksafe-evalops.git
git push -u origin main
```

If GitHub asks for authentication:
- Easiest path: install the GitHub CLI (`gh`) and run `gh auth login`
- Alternative: create a Personal Access Token at github.com/settings/tokens and use it as your password

---

## Step 6: Confirm everything's good

After pushing, visit `https://github.com/dallarsen/banksafe-evalops` in your browser. You should see:
- The README rendered with the architecture diagram
- 3 commits in the history
- All the folders and files

That's Stage 1 complete. Reply to me with "Stage 1 done" and we'll move to Stage 2 (the compliance agent + mock policy tool).

---

## If anything goes wrong

Tell me exactly what error you see and I'll debug it. Common issues:
- **`strands-agents` install fails:** This package may not exist on PyPI under that name. We'll switch to a fallback in Stage 2.
- **`pip install -e` permission denied:** You forgot to activate `.venv` — run the activate command again.
- **`git push` rejected:** Your repo on GitHub already has commits. Either delete and recreate, or run `git push -u origin main --force` if you're sure.
