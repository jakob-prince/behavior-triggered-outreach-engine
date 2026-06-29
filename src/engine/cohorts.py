"""Cohort derivation for the behavior-triggered outreach engine.

The single source of truth for a lead's cohort is :func:`effective_cohort`. It is a *pure*
function of two stored inputs:

- ``account_cohort``: the account-grain classification from behavioral signals
  (e.g. a recently-disengaged account).
- ``user_posture``: the person-grain posture (e.g. someone who signed up but never activated).

Storing only these two raw inputs — and *deriving* the cohort everywhere it is needed — is what
guarantees the **cross-stage consistency invariant**: staging, scoring, drafting, recording, the
dashboard, and auto-exit all call this one function, so a lead carries an identical label end to
end. Persisting a separate "cohort" column would let the label drift when one stage forgets to
recompute it.
"""

from __future__ import annotations

from enum import Enum


class AccountCohort(str, Enum):
    """Account-grain classification derived from product/usage signals."""

    DISENGAGED_RECENT = "DISENGAGED_RECENT"   # was active, momentum dropped / went quiet
    AT_RISK = "AT_RISK"                       # credits low / churn-risk behavior
    HEALTHY = "HEALTHY"                       # steady-state, no trigger
    EXPANSION = "EXPANSION"                   # growing usage, upsell candidate


class UserPosture(str, Enum):
    """Person-grain posture, independent of the account-level signal."""

    NEVER_ACTIVATED = "never_activated"       # signed up, no real usage (<= trivial activity)
    ACTIVATED = "activated"                   # has real product usage


class EffectiveCohort(str, Enum):
    """The derived cohort used for routing, drafting, and reporting."""

    DISENGAGED_NEVER_ENTERED = "DISENGAGED_NEVER_ENTERED"
    DISENGAGED_RECENT = "DISENGAGED_RECENT"
    AT_RISK_SAVE = "AT_RISK_SAVE"
    EXPANSION = "EXPANSION"
    STEADY_NURTURE = "STEADY_NURTURE"


def effective_cohort(account_cohort: AccountCohort, user_posture: UserPosture) -> EffectiveCohort:
    """Derive the effective cohort from the account signal and the user posture.

    The person-grain ``NEVER_ACTIVATED`` posture is *first-class*: a signed-up-but-never-activated
    lead is a real, eligible lead, but it must be treated honestly (warm "you signed up" framing,
    onboarding-call CTA) rather than routed as if it had usage. So it overrides the account signal
    and maps to its own derived cohort.

    >>> effective_cohort(AccountCohort.DISENGAGED_RECENT, UserPosture.NEVER_ACTIVATED).value
    'DISENGAGED_NEVER_ENTERED'
    >>> effective_cohort(AccountCohort.AT_RISK, UserPosture.ACTIVATED).value
    'AT_RISK_SAVE'
    """
    # Person-grain posture takes precedence: a never-activated lead is always nurtured as such,
    # regardless of what the account-level signal says.
    if user_posture is UserPosture.NEVER_ACTIVATED:
        return EffectiveCohort.DISENGAGED_NEVER_ENTERED

    mapping = {
        AccountCohort.DISENGAGED_RECENT: EffectiveCohort.DISENGAGED_RECENT,
        AccountCohort.AT_RISK: EffectiveCohort.AT_RISK_SAVE,
        AccountCohort.EXPANSION: EffectiveCohort.EXPANSION,
        AccountCohort.HEALTHY: EffectiveCohort.STEADY_NURTURE,
    }
    return mapping[account_cohort]


# Cohorts that should use a rapid (urgent) cadence vs. a steady nurture cadence.
RAPID_COHORTS = frozenset(
    {EffectiveCohort.AT_RISK_SAVE, EffectiveCohort.DISENGAGED_RECENT}
)


def cadence_track(cohort: EffectiveCohort) -> str:
    """Map an effective cohort to a cadence track.

    Urgency — not seniority — is the split axis. Cohorts whose signal is a behavioral cliff
    happening *now* get the rapid burst; everyone else gets steady nurture.
    """
    return "rapid" if cohort in RAPID_COHORTS else "nurture"


def should_retrigger(previous_cohort: EffectiveCohort, current_cohort: EffectiveCohort) -> bool:
    """Whether a lead should re-enter outreach.

    Warm cadences are re-triggerable: a lead previously parked in steady nurture that now shows a
    fresh urgent signal (e.g. went quiet again, or credits dropped) should re-enter the rapid
    track rather than be considered "already contacted, done".
    """
    return previous_cohort not in RAPID_COHORTS and current_cohort in RAPID_COHORTS