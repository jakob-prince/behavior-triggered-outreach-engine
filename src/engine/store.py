"""A trivial JSON-backed lead store.

This stands in for whatever real persistence a deployment uses (e.g. local Postgres/SQLite via
SQLAlchemy). It is deliberately generic — no managed-DB or vendor references.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from engine.models import Lead

DEFAULT_PATH = "leads.json"


def save_leads(leads: list[Lead], path: str = DEFAULT_PATH) -> None:
    Path(path).write_text(json.dumps([asdict(l) for l in leads], indent=2))


def load_leads(path: str = DEFAULT_PATH) -> list[Lead]:
    return [Lead(**d) for d in json.loads(Path(path).read_text())]
