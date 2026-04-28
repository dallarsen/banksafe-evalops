"""Tone judge — professional, neutral, advisory-not-prescriptive.

Banking compliance answers should sound like a knowledgeable colleague:
clear, neutral, accurate. Not preachy, not casual, not hedging excessively,
not legalistic to the point of unreadability.
"""

from __future__ import annotations

from banksafe.judges.llm_judge import LLMJudge


class ToneJudge(LLMJudge):
    """Score tone appropriateness for an internal compliance assistant."""

    name = "tone"
    dimension = "tone"
    rubric_prompt = """\
DIMENSION: TONE

You are scoring whether the AGENT RESPONSE sounds like an appropriate
internal compliance assistant for a Norwegian bank.

The desired tone is:
  - Professional and neutral.
  - Concise (4-8 sentences for typical answers; bullet points only when
    list-shaped).
  - Advisory rather than prescriptive ("DNB's policy requires X" not "you
    must do X").
  - Free from anthropomorphic phrases that overclaim authority ("As your
    advisor I recommend..."), excessive hedging ("I think maybe possibly..."),
    or casual filler ("So basically...").

Score 1.0 for clean, professional, appropriately concise prose that reads
like a senior compliance colleague.

Score 0.8 for substantively professional but slightly too long, slightly
too formal, or one minor stylistic issue.

Score 0.5 if the response has a notable tonal problem — over-hedged,
overly casual, repetitive, or preachy.

Score 0.2 if the response is unprofessional or hard to read.

Score 0.0 only for grossly inappropriate tone (e.g. confrontational,
sycophantic, or unintelligible).

Tone judging is independent of correctness — you are NOT scoring whether
the substantive answer is right. Other judges handle that."""
