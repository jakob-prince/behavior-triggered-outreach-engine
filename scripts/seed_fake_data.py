"""Generate synthetic leads.

Uses only the stdlib `random` (seeded for determinism) so the demo runs anywhere. A real project
could swap in Faker for richer fake data. NO real emails, domains, project IDs, or usage numbers.
"""

from __future__ import annotations

import random
from typing import List

from engine.models import Lead

FIRST_NAMES = ["Alex", "Sam", "Jordan", "Taylor", "Morgan", "Riley", "Casey", "Jamie", "Drew", "Quinn"]
DOMAINS = ["acme.test", "globex.test", "initech.test", "umbrella.test"]


def generate_leads(n: int = 30, seed: int = 42) -> List[Lead]:
    rng = random.Random(seed)
    leads: List[Lead] = []
    for i in range(n):
        signed = rng.randint(1, 60)
        never = rng.random() < 0.25
        total = rng.randint(0, 1) if never else rng.randint(2, 200)
        prev7 = 0 if never else rng.randint(0, 40)
        last7 = 0 if never else rng.randint(0, prev7 + 10)
        last_active = signed if never else rng.randint(0, 20)
        granted = 50.0
        remaining = round(rng.uniform(0, 50), 2)
        name = "" if (never and rng.random() < 0.5) else rng.choice(FIRST_NAMES)
        leads.append(
            Lead(
                project_id=f"proj_{1000 + i}",
                user_email=f"user{i}@{rng.choice(DOMAINS)}",
                name=name,
                signed_up_days_ago=signed,
                last_active_days_ago=last_active,
                total_events=total,
                events_last_7d=last7,
                events_prev_7d=prev7,
                credits_remaining=remaining,
                credits_granted=granted,
                integrations_connected=rng.sample(
                    ["github", "slack", "postgres", "notion"], rng.randint(0, 3)
                ),
            )
        )
    return leads


def main() -> None:
    from engine.store import save_leads

    leads = generate_leads()
    save_leads(leads)
    print(f"Wrote {len(leads)} synthetic leads to leads.json")