"""Synthetic lead data model for the demo engine.

Time is expressed as integer "days ago" rather than real timestamps to keep the demo deterministic
and dependency-free. In a real implementation these would be derived from event/usage tables.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Lead:
    project_id: str
    user_email: str
    name: str
    signed_up_days_ago: int
    last_active_days_ago: int
    total_events: int
    events_last_7d: int
    events_prev_7d: int
    credits_remaining: float
    credits_granted: float
    integrations_connected: list[str] = field(default_factory=list)
