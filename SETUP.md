# Setup Instructions — Stage 7 (Final Polish)

This is the last stage. **No new code.** Just polished docs and the materials you need to send the project to hiring managers.

---

## What this stage adds

- **`docs/email-draft.md`** — two ready-to-send email variants to hiring managers
- **`docs/medium-article.md`** — a 1500-word LinkedIn/Medium article version
- **`docs/demo-script.md`** — 3-minute Loom video script (recording is optional)
- **`docs/architecture.md`** — fully refreshed to reflect what actually shipped
- **`docs/extending.md`** — refreshed with a worked Loan Guidance example
- **README final pass** — accurate tech stack, accurate diagram, no aspirational claims about MLflow
- **Version bump 0.6.0 → 0.7.0** to mark the polished release

---

## How to apply

### 1. Unzip Stage 7 over your existing folder

```bash
cd ~/Desktop
unzip -o ~/Downloads/banksafe-evalops-stage7.zip -d ~/Desktop/
```

### 2. Verify version and tests still pass

```bash
cd ~/Desktop/banksafe-evalops
. .venv/bin/activate
pip install -e ".[dev]"
banksafe version       # → 0.7.0
python -m pytest tests/ -v
```

Should still show **47 passed**. No code changed; this is sanity check only.

### 3. Read the email draft and customize it ⭐

Open `docs/email-draft.md` and:
- Pick Variant A (direct) or Variant B (lighter touch) — **A is recommended**
- Replace `[Name]` with the actual hiring manager's name (find on LinkedIn, or use "AI Tech team")
- Replace `[your phone]` and `[your LinkedIn]` with your actual details
- Trim if needed — under 200 words is the goal
- **Don't send yet.** Sleep on it. Send tomorrow morning Oslo time.

### 4. Take the screenshots ⭐

The email links the repo, but screenshots make the email impossible to ignore. You need three:

1. **Eval run passing** — your terminal from earlier today showing `Overall: PASSED` with the dimension scores table
2. **Regression detection working** — the side-by-side from your Stage 6 verification (identity check + simulated regression)
3. **Green CI** — the GitHub Actions page showing your "Tests & fast checks" workflow with the green checkmark

Save them to your desktop or wherever you'll attach them from.

If you didn't keep the terminal output from the earlier eval run, just rerun:

```bash
banksafe eval run --limit 3
```

### 5. (Optional, ~$2) Trigger the live-eval workflow on a demo PR

This produces the killer screenshot — a PR with an auto-posted regression-table comment.

```bash
git checkout -b demo-pr
echo "" >> README.md
git add README.md
git commit -m "demo: trigger live eval"
git push -u origin demo-pr
```

Then on GitHub:
1. Open https://github.com/dallarsen/banksafe-evalops/pulls
2. Click "Compare & pull request" for the `demo-pr` branch
3. Add the label `run-eval` (you may need to create the label first)
4. Wait ~5-10 min
5. The workflow runs, posts a comment with the full regression table

Take a screenshot of the PR with the comment visible. Close the PR without merging.

### 6. (Optional) Record the Loom

`docs/demo-script.md` has a 3-minute script. Recording is optional; the email + repo + screenshots are sufficient.

If you do record: **don't perfectionist it.** A genuine 3-minute walkthrough beats a polished one. The hiring manager will tell.

### 7. (Optional) Publish the article

`docs/medium-article.md` is a 1500-word LinkedIn / Medium post. Posting is optional — it adds a public signal, but isn't required for the email.

If you post: link to it from your LinkedIn profile and mention it in the email's P.S. line.

### 8. Commit and push the final polish

```bash
git add docs/email-draft.md docs/medium-article.md docs/demo-script.md docs/architecture.md docs/extending.md README.md pyproject.toml src/banksafe/__init__.py SETUP.md
git commit -m "docs(stage-7): final polish — email draft, article, demo script, refreshed architecture"

git push
```

### 9. Final repo check

Open https://github.com/dallarsen/banksafe-evalops one more time:
- README renders cleanly
- Architecture diagram displays
- The green CI badge at the top is green
- 11+ commits in history showing intentional iteration

Take a screenshot of the repo home page. **This is the screenshot you might pin to the top of the email.**

---

## Sending the email — checklist

When you're ready to send (tomorrow morning, Oslo time, between 8-10am their time):

- [ ] Subject line is direct and specific
- [ ] Body is under 200 words
- [ ] Three screenshots attached (or four if you got the live-eval comment)
- [ ] Repo link is correct
- [ ] Your name, phone, LinkedIn at the bottom
- [ ] Sent to the actual hiring manager (LinkedIn search "DNB AI Tech")
- [ ] No typos in the recipient's name (this is the easiest unforced error)
- [ ] You read the whole email out loud once before hitting send

Then send it.

---

## After sending

- **Do not refresh your inbox every 5 minutes.** Norwegians take their time. A reply may take 3-7 business days.
- **One follow-up after 7 days max.** One line, friendly. Then leave it.
- **In the meantime, apply elsewhere.** A great project + a great cover letter can be sent to multiple companies. Don't put all your hope on one inbox.

---

## What you built tonight

In one extended session, you went from "I'd like to apply for an AI eval engineering role" to having a public, MIT-licensed, CI-tested, calibrated, multi-dimensional evaluation framework with regression detection and PR-comment automation, plus a full study guide explaining every design decision, plus polished email and article drafts.

That's a lot. Be proud of it. Get some sleep. Send the email when you're sharp. Good luck.
