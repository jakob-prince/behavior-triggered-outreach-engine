"""Tests for the cohort derivation invariants.

These are the two properties worth proving in a demo repo:

1. **Cross-stage consistency** — because every stage calls the same pure :func:`effective_cohort`,
   the derived label is identical no matter where/when it is computed.
2. **Re-trigger** — a parked (nurture) lead that shows a fresh urgent signal re-enters the rapid
   track.
"""

import pytest

from engine.cohorts import (
    AccountCohort,
    cadence_track,
    EffectiveCohort,
    effective_cohort,
    should_retrigger,
    UserPosture,
)


# --- effective_cohort derivation -------------------------------------------------------------

@pytest.mark.parametrize(
    "account_cohort, user_posture, expected",
    [
        (AccountCohort.DISENGAGED_RECENT, UserPosture.ACTIVATED, EffectiveCohort.DISENGAGED_RECENT),
        (AccountCohort.AT_RISK, UserPosture.ACTIVATED, EffectiveCohort.AT_RISK_SAVE),
        (AccountCohort.EXPANSION, UserPosture.ACTIVATED, EffectiveCohort.EXPANSION),
        (AccountCohort.HEALTHY, UserPosture.ACTIVATED, EffectiveCohort.STEADY_NURTURE),
        (AccountCohort.HEALTHY, UserPosture.NEVER_ACTIVATED, EffectiveCohort.DISENGAGED_NEVER_ENTERED),
    ],
)
def test_effective_cohort_consistency(account_cohort, user_posture, expected):
    assert effective_cohort(account_cohort, user_posture) == expected


@pytest.mark.parametrize(
    "account_cohort, user_posture, expected",
    [
        (AccountCohort.DISENGAGED_RECENT, UserPosture.ACTIVATED, EffectiveCohort.DISENGAGED_RECENT),
        (AccountCohort.AT_RISK, UserPosture.ACTIVATED, EffectiveCohort.AT_RISK_SAVE),
    ],
)
def test_effective_cohort_is_pure(account_cohort, user_posture, expected):
    """Calling it twice gives the same result (no side effects, no randomness)."""
    first = effective_cohort(account_cohort, user_posture)
    second = effective_cohort(account_cohort, user_posture)
    assert first == expected
    assert second == expected
    assert first == second


# --- cadence_track and retrigger ------------------------------------------------------------

@pytest.mark.parametrize(
    "cohort, expected_track",
    [
        (EffectiveCohort.AT_RISK_SAVE, "rapid"),
        (EffectiveCohort.DISENGAGED_RECENT, "rapid"),
        (EffectiveCohort.EXPANSION, "nurture"),
        (EffectiveCohort.STEADY_NURTURE, "nurture"),
        (EffectiveCohort.DISENGAGED_NEVER_ENTERED, "nurture"),
    ],
)
def test_cadence_track_splits_on_urgency(cohort, expected_track):
    assert cadence_track(cohort) == expected_track


def test_parked_lead_retriggers_on_fresh_urgent_signal():
    # Was steady; now shows an at-risk signal -> should re-enter the rapid track.
    assert should_retrigger(EffectiveCohort.STEADY_NURTURE, EffectiveCohort.AT_RISK_SAVE) is True


def test_already_rapid_lead_does_not_double_trigger():
    assert should_retrigger(EffectiveCohort.AT_RISK_SAVE, EffectiveCohort.AT_RISK_SAVE) is False


def test_staying_in_nurture_does_not_trigger():
    assert should_retrigger(EffectiveCohort.STEADY_NURTURE, EffectiveCohort.EXPANSION) is False
