# Email Draft — for hiring managers at DNB

This is the email that delivers the project. Two variants below — pick the one that matches your read of the situation, or mash them together. Both end with a clear, low-pressure ask.

**Before sending:**
1. Add screenshots (see "What screenshots to include" at the bottom)
2. Replace bracketed `[placeholders]` with your actual details
3. Trim aggressively — shorter is better; aim for under 200 words in the body
4. Send to whoever is named on the job posting; if no name, addresses for AI Tech leads at DNB are usually findable on LinkedIn

---

## Variant A: Direct & confident (recommended)

**Subject:** AI Evaluation Engineer — built a project to demonstrate fit

Hi [Name],

I'm Dallin Larsen — applying for the AI Evaluation Engineer role on AI Tech. I read the job description carefully and decided the best way to demonstrate fit was to build a project that solves the problem you'd be hiring me to solve.

It's called **BankSafe EvalOps**: a CI/CD evaluation framework for agentic banking assistants. The reference implementation is a Strands-based compliance agent that answers questions about Norwegian banking regulations (GDPR, DORA, AML, MiFID II, PSD2). Six independent judges score every response — accuracy, grounding, hallucination, PII leakage, refusal appropriateness, and tone — with a calibration harness that validates the rubrics against hand-labeled examples (MAE ≤ 0.15). Every PR runs the eval; regressions beyond 5 percentage points on any dimension automatically block merge with a comment posted to the PR conversation.

Repo (public, MIT-licensed): **https://github.com/dallarsen/banksafe-evalops**

Three things I'd point you to if you only have a minute:

1. The README walks through the architecture and shows what `banksafe eval run` produces.
2. `docs/study-guide.md` documents the rationale behind every design choice — including a calibration trade-off I deliberately shipped because the safer choice would have hidden a real signal.
3. `.github/workflows/live-eval.yml` is the CI gate — it runs the full eval on PR labels and blocks merges on regression.

It builds on the JD's stated tech stack (Python, Strands, Anthropic via Bedrock-portable interface, GitHub Actions, Docker) and is designed to extend cleanly to other agent types — loan guidance, fraud triage, customer support — by adding a config and a dataset.

Happy to walk through it on a call, or to pair on a problem you're actually facing right now in the AI Tech division. Either is more useful than another interview question, in my view.

Best,
Dallin Larsen
[your phone] · [your LinkedIn]

---

## Variant B: Curious & lighter touch

**Subject:** Built something for the AI Evaluation Engineer role — quick read?

Hi [Name],

After reading the AI Evaluation Engineer JD, I had an itch to build the thing it described rather than just describe what I'd build. The result is **BankSafe EvalOps** — a CI/CD evaluation framework for agentic banking assistants:

- A Strands-based compliance agent that answers questions about Norwegian/EU banking regulations
- Six calibrated judges (accuracy, grounding, hallucination, PII, refusal, tone) — five LLM-based and one deterministic regex
- A 32-case eval dataset covering all six policy areas plus traps for each judge dimension
- GitHub Actions workflows that run the eval on PR and block merges on regression with a comment posted inline
- A study guide explaining every design choice, including a couple of trade-offs I wrestled with

Repo: https://github.com/dallarsen/banksafe-evalops

It's under 1500 lines of Python and runs locally with one Anthropic API key. The framework is intentionally generic — adding a loan-guidance or fraud-triage agent is a config + dataset change, not a code change.

If any of this looks relevant to what AI Tech is solving, I'd love a 30-minute conversation to learn more about the actual problems on your roadmap.

Thanks for reading,
Dallin Larsen
[your LinkedIn] · [your phone]

---

## What screenshots to include

Attach 3 images (or paste inline if your email client supports it):

1. **Terminal showing the eval run pass.** From your Stage 4 run — the dimension scores table with all green PASS rows. Crop tightly.
2. **Terminal showing the regression check.** From Stage 6 — the side-by-side identity check (all flat) and simulated regression (accuracy flagged red). Even better if you can fit both in one screenshot.
3. **GitHub Actions green checkmark.** Your "Tests & fast checks" run from earlier today.

If you have time and want a fourth: a **PR with the auto-posted regression comment** (from running the optional live-eval bonus). That one is the killer. If you don't have it, the three above are plenty.

## Notes on tone

- **Don't** apologize for sending unsolicited material or hedge that you "hope this is okay."
- **Do** be direct about what you built and why.
- **Don't** explain at length how you used AI to build it (mention it once in the README, where it belongs — `Built with AI-First Engineering` section).
- **Do** invite specificity — "to pair on a problem you're actually facing" beats "to discuss further."
- **Don't** mention salary, location, or visa unless they ask.
- **Do** make sure your LinkedIn and phone are accurate before hitting send.

## When to send

Tuesday-Thursday morning, Oslo time (08:00-10:00 local). Avoid Mondays (full inbox) and Fridays (deferred reading).

Oslo is UTC+2. Send the email so it arrives in their inbox between 08:00 and 10:00 Oslo time on a weekday — that's 23:00-01:00 the previous night your time, or set up scheduled send.

## Follow-up rule

If no reply in 7 calendar days, send ONE follow-up. One line:

> Hi [Name] — checking back on the BankSafe EvalOps project I shared on [date]. Happy to walk through it whenever works for you. https://github.com/dallarsen/banksafe-evalops

After that, leave it. Push too hard and you become the candidate who doesn't take signals.
