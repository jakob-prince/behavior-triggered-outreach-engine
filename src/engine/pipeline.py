"""End-to-end orchestration: detect → exclude → score → cohort → draft → enroll.

`previous_cohorts` (email → last effective cohort) enables the re-trigger behavior: a lead parked
in steady nurture that now shows a fresh urgent signal re-enters the rapid track.
"""

from __future__ import annotations

from engine.cohorts import EffectiveCohort
from engine.cohorts import cadence_track
from engine.cohorts import effective_cohort
from engine.cohorts import should_retrigger
from engine.exclusion import is_excluded
from engine.models import Lead
from engine.outreach import ConsoleOutreachClient
from engine.outreach import OutreachClient
from engine.personalize import FakeLLMClient
from engine.personalize import LLMClient
from engine.personalize import draft_message
from engine.scoring import score_lead
from engine.scoring import shortlist
from engine.signals import classify_account_cohort
from engine.signals import classify_user_posture


def run(
    leads: list[Lead],
    llm: LLMClient | None = None,
    outreach: OutreachClient | None = None,
    previous_cohorts: dict[str, EffectiveCohort] | None = None,
    limit: int = 10,
) -> list[dict]:
    llm = llm or FakeLLMClient()
    outreach = outreach or ConsoleOutreachClient()
    previous_cohorts = previous_cohorts or {}

    # detect
    signals = [
        {
            "lead": lead,
            "account_cohort": classify_account_cohort(lead),
            "user_posture": classify_user_posture(lead),
        }
        for lead in leads
    ]

    # exclude
    not_excluded = [s for s in signals if not is_excluded(s["lead"])]

    # score
    candidates = []
    for row in not_excluded:
        lead = row["lead"]
        cohort = effective_cohort(row["account_cohort"], row["user_posture"])
        candidates.append(
            {"lead": lead, "cohort": cohort, "score": score_lead(lead, cohort)}
        )

    # shortlist: who to contact today
    picked = shortlist(candidates, limit=limit)

    # draft + enroll
    results: list[dict] = []
    for row in picked:
        lead, cohort = row["lead"], row["cohort"]
        prev = previous_cohorts.get(lead.user_email)
        retrigger = prev is not None and should_retrigger(prev, cohort)
        track = cadence_track(cohort)
        message = draft_message(lead, cohort, llm)
        outreach.enroll(lead, track, message)
        results.append(
            {
                "email": lead.user_email,
                "cohort": cohort.value,
                "track": track,
                "score": row["score"],
                "retrigger": retrigger,
            }
        )
    return results


def main() -> None:
    # CLI entry: read seeded leads from the store and run the pipeline.
    from engine.store import load_leads

    results = run(load_leads())
    print(f"\nEnrolled {len(results)} leads.")
