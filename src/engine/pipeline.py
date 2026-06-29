"""End-to-end orchestration: detect → exclude → score → cohort → draft → enroll.

`previous_cohorts` (email → last effective cohort) enables the re-trigger behavior: a lead parked
in steady nurture that now shows a fresh urgent signal re-enters the rapid track.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from engine.cohorts import cadence_track, effective_cohort, should_retrigger, EffectiveCohort
from engine.exclusion import is_excluded
from engine.outreach import ConsoleOutreachClient, OutreachClient
from engine.personalize import FakeLLMClient, LLMClient, draft_message
from engine.scoring import score_lead, shortlist
from engine.signals import classify_account_cohort, classify_user_posture
from engine.models import Lead


def run(
    leads: List[Lead],
    llm: Optional[LLMClient] = None,
    outreach: Optional[OutreachClient] = None,
    previous_cohorts: Optional[Dict[str, EffectiveCohort]] = None,
    limit: int = 10,
) -> List[Dict]:
    llm = llm or FakeLLMClient()
    outreach = outreach or ConsoleOutreachClient()
    previous_cohorts = previous_cohorts or {}

    # detect + exclude + cohort + score
    candidates: List[Dict] = []
    for lead in leads:
        if is_excluded(lead):
            continue
        cohort = effective_cohort(
            classify_account_cohort(lead), classify_user_posture(lead)
        )
        candidates.append(
            {"lead": lead, "cohort": cohort, "score": score_lead(lead, cohort)}
        )

    # shortlist: who to contact today
    picked = shortlist(candidates, limit=limit)

    # draft + enroll
    results: List[Dict] = []
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