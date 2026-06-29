"""End-to-end orchestration: detect → exclude → score → cohort → draft → enroll.

`previous_cohorts` (email → last effective cohort) enables the re-trigger behavior: a lead parked
in steady nurture that now shows a fresh urgent signal re-enters the rapid track.
"""

from __future__ import annotations

from engine.cohorts import (
    EffectiveCohort,
    cadence_track,
    effective_cohort,
    should_retrigger,
)
from engine.exclusion import is_excluded
from engine.models import Lead
from engine.outreach import (
    ConsoleOutreachClient,
    OutreachClient,
)
from engine.personalize import (
    draft_message,
    FakeLLMClient,
    LLMClient,
)
from engine.scoring import (
    score_lead,
    shortlist,
)
from engine.signals import (
    classify_account_cohort,
    classify_user_posture,
)


def run(
    leads: list[Lead],
    llm: LLMClient | None = None,
    outreach: OutreachClient | None = None,
    previous_cohorts: dict[str, EffectiveCohort] | None = None,
    limit: int = 10,
) -> list[dict[str, str | float | bool]]:
    llm = llm or FakeLLMClient()
    outreach = outreach or ConsoleOutreachClient()
    previous_cohorts = previous_cohorts or {}

    # detect + exclude + score in one pass
    candidates: list[dict[str, object]] = []
    for lead in leads:
        if is_excluded(lead):
            continue
        acct = classify_account_cohort(lead)
        posture = classify_user_posture(lead)
        cohort = effective_cohort(acct, posture)
        candidates.append(
            {"lead": lead, "cohort": cohort, "score": score_lead(lead, cohort)}
        )

    # shortlist: who to contact today
    picked = shortlist(candidates, limit=limit)

    # draft + enroll
    results: list[dict[str, str | float | bool]] = []
    for row in picked:
        lead: Lead = row["lead"]  # type: ignore[assignment]
        cohort: EffectiveCohort = row["cohort"]  # type: ignore[assignment]
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
                "score": row["score"],  # type: ignore[arg-type]
                "retrigger": retrigger,
            }
        )
    return results


def main() -> None:
    # CLI entry: read seeded leads from the store and run the pipeline.
    from engine.store import load_leads

    results = run(load_leads())
    print(f"\nEnrolled {len(results)} leads.")
