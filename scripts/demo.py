"""End-to-end demo runner (the `make demo` target).

Seeds synthetic leads in-memory, runs the pipeline, prints the shortlist, then demonstrates the
re-trigger behavior with a second pass.
"""

from __future__ import annotations

from engine.cohorts import EffectiveCohort
from engine.pipeline import run

from seed_fake_data import generate_leads  # sibling module in scripts/


def main() -> None:
    leads = generate_leads()

    print("=== Pass 1: detect → score → cohort → draft → enroll ===\n")
    results = run(leads, limit=10)

    print("\n--- shortlist summary ---")
    for r in results:
        print(f"{r['score']:>7} {r['cohort']:<26} {r['track']:<8} {r['email']}")

    # Re-trigger demo: pretend everyone was last parked in steady nurture; anyone now urgent
    # should re-enter the rapid track.
    print("\n=== Pass 2: re-trigger check (all previously steady nurture) ===")
    previous = {l.user_email: EffectiveCohort.STEADY_NURTURE for l in leads}
    pass2 = run(leads, previous_cohorts=previous, limit=10)
    retriggered = [r["email"] for r in pass2 if r["retrigger"]]
    print(f"\nRe-triggered into rapid track: {len(retriggered)} leads")
    for email in retriggered:
        print(f"    {email}")