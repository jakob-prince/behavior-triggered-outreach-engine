"""CRM/outreach enrollment, behind an interface.

The real implementation would push the lead into a sequence on whatever outreach platform is in
use. The demo ships a console stub so the pipeline runs end to end without any external system or
credentials.
"""

from __future__ import annotations

from typing import Protocol

from engine.models import Lead


class OutreachClient(Protocol):
    def enroll(self, lead: Lead, cadence_track: str, message: str) -> None: ...


class ConsoleOutreachClient:
    """Prints enrollments instead of calling a real outreach API."""

    def __init__(self) -> None:
        self.enrolled: list[tuple[str, str]] = []

    def enroll(self, lead: Lead, cadence_track: str, message: str) -> None:
        self.enrolled.append((lead.user_email, cadence_track))
        print(f"[enroll → {cadence_track}] {lead.user_email}")
        print(f"    {message}")
