# behavior-triggered-outreach-engine

A reference implementation of a **behavior-triggered, AI-personalized outreach engine** for
product-led growth (PLG). Leads enter outreach on *product signals* — not cold lists — and get
per-lead messages drafted from their actual behavior.

> This is a teaching/demo project. It ships with **synthetic data only** and stubs out the CRM
> and LLM behind interfaces. Nothing here talks to a real customer database, mail system, or
> production model.

## Why behavior-triggered?

Cold outbound starts from a firmographic list ("companies that look like X") and blasts a fixed
drip. Warm PLG outreach is the opposite: the person is **already in your product**, so you have
real behavior to act on. Enrollment should be *triggered by what they do*:

- credits running low
- usage momentum dropped
- went quiet after early activity
- signed up but never actually activated

Because every message is personalized from behavior, the cadence is just a **container**: the
split that matters is **urgency** (a behavioral cliff happening *now* vs. steady-state nurture),
not seniority.

## Pipeline

```
 product signals (usage · credits · activation · momentum)
        │  detect on a schedule + on behavior-change
        ▼
   exclusion filter ──► score ──► cohort ──► draft ──► enroll
        │                  │         │         │         │
        │                  │         │         │         └─ OutreachClient (console stub)
        │                  │         │         └─ LLMClient (fake / real)
        │                  │         └─ effective_cohort(account_cohort, user_posture)
        │                  └─ shortlist: who to contact today
        └─ synthetic exclusion list (illustrative only)
```

## Design highlights worth a look

1. **Two-axis status model** — engagement state × lifecycle stage, instead of a single linear
   pipeline column. A lead can be "saved" yet later "re-at-risk" without losing history.

2. **Derived cohorts via a pure function.** `effective_cohort(account_cohort, user_posture)` is
   the single source of truth for a lead's cohort, applied identically at *every* stage
   (staging, scoring, drafting, recording, dashboard, auto-exit). This **cross-stage
   consistency invariant** is what keeps the label from drifting between steps — see
   `src/engine/cohorts.py` and the tests.

3. **Re-triggerable cadences.** A saved lead who goes quiet again **re-enters** the rapid
   track. Outreach is modeled as short event-triggered bursts, not a one-shot drip.

4. **Swappable AI + CRM.** `LLMClient` and `OutreachClient` are interfaces; the demo ships a
   deterministic fake LLM and a console CRM stub so the whole thing runs offline.

## Quick start

```bash
uv sync
python scripts/seed_fake_data.py     # generate synthetic projects/users/usage
python -m engine.pipeline            # detect → score → cohort → draft → print
pytest                               # cohort-consistency + re-trigger tests
```

## Sample output

Running `python demo.py` against 30 synthetic leads produces a scored shortlist
(urgency-first) and demonstrates re-triggering:

```
=== Pass 1: detect → score → cohort → draft → enroll ===

[enroll → rapid] user4@initech.test
    Hi Taylor, I noticed your credits are running low. Would you be open to a
    quick ~30-min onboarding call to get you to your first real win?

--- shortlist summary ---
 144.08  AT_RISK_SAVE        rapid  user4@initech.test
 143.40  AT_RISK_SAVE        rapid  user26@acme.test
 120.74  DISENGAGED_RECENT   rapid  user29@globex.test
 ...

=== Pass 2: re-trigger check (all previously steady nurture) ===
Re-triggered into rapid track: 10 leads
```

> `AT_RISK_SAVE` leads (credits low) sort above `DISENGAGED_RECENT` (went quiet),
> all on the `rapid` cadence; leads previously parked in nurture that now show a
> fresh urgent signal re-enter the rapid track.

## Project layout

```
behavior-triggered-outreach-engine/
├── README.md
├── pyproject.toml
├── src/engine/
│   ├── signals.py       # detect credits-low / momentum-drop / quiet / never-activated
│   ├── cohorts.py       # effective_cohort() pure helper  ← start here
│   ├── scoring.py       # lead scoring / shortlist
│   ├── personalize.py   # LLMClient interface + deterministic fake
│   ├── outreach.py      # OutreachClient interface + console stub
│   └── pipeline.py      # detect→score→cohort→draft→enroll orchestration
├── scripts/seed_fake_data.py
└── tests/
    └── test_cohorts.py  # invariants: consistency across stages + re-trigger
```

## Sanitization rules (non-negotiable for this repo)

- Synthetic data only — no real emails, domains, project IDs, or usage numbers.
- No real exclusion list — a trivial illustrative example only.
- CRM and LLM are abstracted behind interfaces; no provider names, sequence IDs, or keys.
- Generic local store (SQLite/Postgres via SQLAlchemy); no managed-DB references.

## License

MIT (demo code).