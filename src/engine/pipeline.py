"""End-to-end orchestration: detect -> exclude -> score -> cohort -> draft -> enroll.

`previous_cohorts` (email -> last effective cohort) enables the re-trigger behavior: a lead parked
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
        picked_lead: Lead = row["lead"]  # type: ignore[assignment]
        picked_cohort: EffectiveCohort = row["cohort"]  # type: ignore[assignment]
        prev = previous_cohorts.get(picked_lead.user_email)
        retrigger = prev is not None and should_retrigger(prev, picked_cohort)
        track = cadence_track(picked_cohort)
        message = draft_message(picked_lead, picked_cohort, llm)
        outreach.enroll(picked_lead, track, message)
        results.append(
            {
                "email": picked_lead.user_email,
                "cohort": picked_cohort.value,
                "track": track,
                "score": float(row["score"]),
                "retrigger": retrigger,
            }
        )
    return results


def main() -> None:
    # CLI entry: read seeded leads from the store and run the pipeline.
    from engine.store import load_leads

    results = run(load_leads())
    print(f"\nEnrolled {len(results)} leads.")
