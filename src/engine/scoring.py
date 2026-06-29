"""Lead scoring and shortlist selection.

Priority is dominated by *urgency* (the effective cohort), then nudged by how warm the lead is
(prior engagement) and how depleted their credits are. The shortlist is simply the top-N by score —
"who to contact today".
"""

from __future__ import annotations

from engine.cohorts import EffectiveCohort
from engine.models import Lead

# Urgency weight per effective cohort — the primary driver of priority.
URGENCY_WEIGHT = {
    EffectiveCohort.AT_RISK_SAVE: 100,
    EffectiveCohort.DISENGAGED_RECENT: 80,
    EffectiveCohort.EXPANSION: 60,
    EffectiveCohort.DISENGAGED_NEVER_ENTERED: 40,
    EffectiveCohort.STEADY_NURTURE: 10,
}


def score_lead(lead: Lead, cohort: EffectiveCohort) -> float:
    score = float(URGENCY_WEIGHT[cohort])
    # Warmer leads (more prior product activity) get a modest boost.
    score += min(lead.total_events, 50) * 0.5
    # More depleted credits => more urgent.
    if lead.credits_granted > 0:
        score += (1 - lead.credits_remaining / lead.credits_granted) * 20
    return round(score, 2)


def shortlist(scored: list[dict[str, object]], limit: int = 10) -> list[dict[str, object]]:
    return sorted(scored, key=lambda r: r["score"], reverse=True)[:limit]
