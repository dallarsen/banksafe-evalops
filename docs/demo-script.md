# Loom Video Script — 3-minute project walkthrough

A short video makes the email much harder to ignore. Recording is optional — but if you want to do one, here's a tight script.

**Setup:** [Loom](https://www.loom.com/) (free tier is fine). Record screen + webcam-in-corner. 3-minute target. No edits needed.

**Tabs to have open before hitting record:**
1. Your GitHub repo home page
2. The `docs/study-guide.md` file on GitHub
3. Your terminal showing the repo
4. The GitHub Actions tab showing your green CI run

**One-take strategy:** Don't re-record per perfect take. A slightly-imperfect-but-genuine 3-minute walkthrough is better than a polished one. Hiring managers tell each other the difference.

---

## The script

### [0:00 — 0:25] Intro + the problem

> "Hi, I'm Dallin Larsen — I'm applying for the AI Evaluation Engineer role at DNB. I built this project, **BankSafe EvalOps**, to demonstrate fit. It's a CI/CD evaluation framework for agentic banking assistants — about 1,500 lines of Python, runs locally, and gates pull requests on quality and compliance regressions before they hit production."

**On screen:** GitHub repo home page.

### [0:25 — 0:55] Architecture in 30 seconds

> "It's structured in four layers. There's a Strands-based compliance agent that answers questions about Norwegian banking regulations. An evaluation harness that runs cases through it. Six judges that score each response — accuracy, grounding, hallucination, PII, refusal, and tone. And a CI gating layer that compares against a baseline and blocks merges on regression. The framework is provider-agnostic: any agent that implements the BaseAgent interface can drop in."

**On screen:** Scroll the README to the architecture diagram. Pause for 2 seconds on it.

### [0:55 — 1:35] Show the agent answering

> "Let me show you the agent in action."

```bash
banksafe agent ask "What's the deadline for reporting a major ICT incident under DORA?"
```

> "It calls the policy lookup tool, retrieves the DORA policy, and answers with the 4-hour, 72-hour, and one-month timeline — citing `policy:dora` inline. That citation is what the grounding judge will score against in CI."

**On screen:** Terminal output. Let it scroll naturally; don't speed it up.

### [1:35 — 2:15] Show the judges + calibration

> "Now the judges. Five of them are LLM-based; the PII judge is deterministic regex — that's a deliberate choice for auditability and zero cost. The calibration harness runs each judge against a hand-labeled golden set."

```bash
banksafe eval calibrate
```

> "Six dimensions, all calibrated under the 0.15 MAE threshold. The harness even flags my own scoring disagreements with the judge — that's exactly what calibration is supposed to do."

**On screen:** The calibration table from your earlier run (or take a screenshot if rerunning would cost too much).

### [2:15 — 2:50] Show CI gating

> "The killer feature is CI gating. Every PR runs the test suite and a regression-engine self-check. PRs labeled `run-eval` trigger the full live evaluation — it scores against a committed baseline and posts a results table to the PR conversation. If any dimension regresses by more than 5 points, the workflow fails and the merge is blocked."

**On screen:** GitHub Actions page with the green checkmark, then briefly show `live-eval.yml`.

### [2:50 — 3:00] Close

> "The repo is open source, MIT-licensed, and the design rationale for every choice is documented in the study guide. Link is in the email. Happy to walk through it on a call. Thanks for your time."

**On screen:** Repo home page with the README visible.

---

## Recording tips

- **Talk slightly faster than feels natural.** Recordings always sound slow on playback.
- **Don't apologize for typos or terminal pauses.** They're fine.
- **Look at the camera, not the screen, during intro/outro.** It's a small thing that lands.
- **Before recording, do one practice run** without recording. You'll be 30% better on take 1.
- **If you flub badly, restart from the section heading**, not from scratch. Your first attempt is usually the best.
