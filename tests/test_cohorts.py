"""Tests for the cohort derivation invariants.

These are the two properties worth proving in a demo repo:

1. **Cross-stage consistency** — because every stage calls the same pure :func:`effective_cohort`,
   the derived label is identical no matter where/when it is computed.
2. **Re-trigger** — a parked (nurture) lead that shows a fresh urgent signal re-enters the rapid
   track.
"""

import itertools

import pytest

from engine.cohorts import (
    AccountCohort,
    UserPosture,
    EffectiveCohort,
    effective_cohort,
    cadence_track,
    should_retrigger,
)


# --- effective_cohort derivation -------------------------------------------------------------

@pytest.mark.parametrize(
    "account_cohort, user_posture, expected",
    [
        (AccountCohort.DISENGAGED_RECENT, UserPosture.ACTIVATED, EffectiveCohort.DISENGAGED_RECENT),
        (AccountCohort.AT_RISK, UserPosture.ACTIVATED, EffectiveCohort.AT_RISK_SAVE),
        (AccountCohort.EXPANSION, UserPosture.ACTIVATED, EffectiveCohort.EXPANSION),
        (AccountCohort.HEALTHY, UserPosture.ACTIVATED, EffectiveCohort.STEADY_NURTURE),
    ],
)
def test_activated_leads_map_by_account_signal(account_cohort, user_posture, expected):
    assert effective_cohort(account_cohort, user_posture) is expected


@pytest.mark.parametrize("account_cohort", list(AccountCohort))
def test_never_activated_posture_overrides_every_account_signal(account_cohort):
    # The person-grain posture is first-class: never-activated always derives the same cohort,
    # regardless of the account-level signal.
    assert (
        effective_cohort(account_cohort, UserPosture.NEVER_ACTIVATED)
        is EffectiveCohort.DISENGAGED_NEVER_ENTERED
    )


# --- cross-stage consistency invariant -------------------------------------------------------

def _stage_staging(account_cohort, user_posture):
    return effective_cohort(account_cohort, user_posture)


def _stage_drafting(account_cohort, user_posture):
    return effective_cohort(account_cohort, user_posture)


def _stage_recording(account_cohort, user_posture):
    return effective_cohort(account_cohort, user_posture)


def _stage_dashboard(account_cohort, user_posture):
    return effective_cohort(account_cohort, user_posture)


def test_cohort_is_identical_across_every_stage():
    """Any stage that needs the cohort derives it from the same two raw inputs, so the label can
    never drift between staging, drafting, recording, and the dashboard."""
    stages = (_stage_staging, _stage_drafting, _stage_recording, _stage_dashboard)
    for account_cohort, user_posture in itertools.product(AccountCohort, UserPosture):
        labels = {stage(account_cohort, user_posture) for stage in stages}
        assert len(labels) == 1, (account_cohort, user_posture, labels)


# --- cadence + re-trigger --------------------------------------------------------------------

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