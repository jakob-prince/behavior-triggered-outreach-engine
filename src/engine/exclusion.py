"""Exclusion filter (illustrative only).

A real deployment maintains a curated exclusion list (internal domains, already-engaged customers,
test accounts). Here it is a trivial example so the shape is clear without exposing any real list.
"""

from __future__ import annotations

from engine.models import Lead

EXCLUDED_DOMAINS = {"internal.test", "competitor.test"}
EXCLUDED_EMAILS = {"do-not-contact@acme.test"}


def is_excluded(lead: Lead) -> bool:
    domain = lead.user_email.split("@")[-1].lower()
    return domain in EXCLUDED_DOMAINS or lead.user_email.lower() in EXCLUDED_EMAILS