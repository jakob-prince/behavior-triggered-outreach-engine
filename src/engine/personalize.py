"""Per-lead message drafting.

The LLM is hidden behind the :class:`LLMClient` interface so the engine can run fully offline with
a deterministic fake (used in tests/demo) and swap in a real model in production. The cohort
chooses the *angle*; the CTA is always the onboarding/activation call.
"""

from __future__ import annotations

# The honest, behavior-grounded angle for each cohort. Note DISENGAGED_NEVER_ENTERED uses a
# truthful "you signed up but haven't dived in" framing — never an implied-usage line.
COHORT_ANGLE = {
    EffectiveCohort.AT_RISK_SAVE: "noticed your credits are running low",
    EffectiveCohort.DISENGAGED_RECENT: "saw you were active recently and then things went quiet",
    EffectiveCohort.DISENGAGED_NEVER_ENTERED: (
        "saw you signed up but haven't had a chance to dive in yet"
    ),
    EffectiveCohort.EXPANSION: "saw your usage is really picking up",
    EffectiveCohort.STEADY_NURTURE: "wanted to check in on how things are going",
}


class LLMClient(Protocol):
    def draft(self, context: dict) -> str: ...


class FakeLLMClient:
    """Deterministic stand-in for a real LLM — no network, stable output for tests."""

    def draft(self, context: dict) -> str:
        return (
            f"Hi {context['name']}, I {context['angle']}. "
            f"Would you be open to {context['cta']}?"
        )


def build_context(lead: Lead, cohort: EffectiveCohort) -> dict:
    return {
        "name": lead.name or "there",
        "angle": COHORT_ANGLE[cohort],
        "cta": CTA,
        "events": lead.total_events,
    }


def draft_message(lead: Lead, cohort: EffectiveCohort, client: LLMClient) -> str:
    return client.draft(build_context(lead, cohort))