"""Behavioral signal detection.

This is the entry point of the engine: leads are classified purely from *product behavior*, not
firmographics. Each detector answers one question; the two classifiers roll detectors up into the
account-grain signal and the person-grain posture that :func:`cohorts.effective_cohort` consumes.
"""

from __future__ import annotations
from collections.abc import Iterable


from engine.cohorts import AccountCohort, UserPosture
from engine.models import Lead

# --- tunable thresholds ----------------------------------------------------------------------
LOW_CREDIT_FRACTION = 0.15      # <=15% of granted credits remaining => at risk
QUIET_DAYS = 7                  # no activity for a week after real usage => went quiet
MOMENTUM_DROP_FRACTION = 0.5    # this week <= half of last week => momentum dropped
ACTIVATION_MIN_EVENTS = 2       # <2 lifetime events => never really activated


# --- individual detectors --------------------------------------------------------------------
def is_never_activated(lead: Lead) -> bool:
    return lead.total_events < ACTIVATION_MIN_EVENTS


def is_credits_low(lead: Lead) -> bool:
    if lead.credits_granted <= 0:
        return False
    return lead.credits_remaining / lead.credits_granted <= LOW_CREDIT_FRACTION


def went_quiet(lead: Lead) -> bool:
    return lead.total_events >= ACTIVATION_MIN_EVENTS and lead.last_active_days_ago >= QUIET_DAYS


def momentum_dropped(lead: Lead) -> bool:
    if lead.events_prev_7d == 0:
        return False
    return lead.events_last_7d <= lead.events_prev_7d * MOMENTUM_DROP_FRACTION


def is_expanding(lead: Lead) -> bool:
    return lead.events_prev_7d > 0 and lead.events_last_7d > lead.events_prev_7d


# --- classifiers -----------------------------------------------------------------------------
def classify_user_posture(lead: Lead) -> UserPosture:
    return UserPosture.NEVER_ACTIVATED if is_never_activated(lead) else UserPosture.ACTIVATED


def classify_account_cohort(lead: Lead) -> AccountCohort:
    # Order matters: the most urgent signal wins.
    if is_credits_low(lead):
        return AccountCohort.AT_RISK
    if went_quiet(lead) or momentum_dropped(lead):
        return AccountCohort.DISENGAGED_RECENT
    if is_expanding(lead):
        return AccountCohort.EXPANSION
    return AccountCohort.HEALTHY


def detect(leads: Iterable[Lead]) -> list[dict]:
    """Classify each lead into (account_cohort, user_posture)."""
    return [
        {
            "lead": lead,
            "account_cohort": classify_account_cohort(lead),
            "user_posture": classify_user_posture(lead),
        }
        for lead in leads
    ]