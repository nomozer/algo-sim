# -*- coding: utf-8 -*-
"""Retired Classroom fixture entrypoint guard (BLOCKER-DB-2 resolution).

Classroom routes (`classroom_router.py`, `session_router.py`) and Classroom ORM
models (`Classroom`, `ClassMembership`, `Assignment`, `PracticeSession`,
`ClassroomSession`) were retired from active application code in `bf1ee2a57`
while existing persisted Classroom tables/rows remain safely retained in-place.

This script no longer imports removed ORM symbols or creates legacy tables.
Use `scripts/seed_demo_accounts.py` to seed the 3 active demo accounts
(`admin`, `teacher`, `student`) into an isolated SQLite DB.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Verify active non-Classroom persistence and demo-account seeder remain importable.
from app.persistence.classroom_models import User  # noqa: E402, F401
from scripts import seed_demo_accounts  # noqa: E402, F401

RETIRED_REASON_CODE = "CLASSROOM_FEATURE_RETIRED"
EXIT_RETIRED = 2


def status_payload() -> dict[str, object]:
    """Return structured status explaining why Classroom fixture seeding is retired."""
    return {
        "ok": False,
        "status": RETIRED_REASON_CODE,
        "message": (
            "Classroom fixture seeding is retired (Classroom ORM/routers removed in bf1ee2a57; "
            "existing legacy tables are retained non-destructively in DB). "
            "Use `python scripts/seed_demo_accounts.py` instead."
        ),
        "replacement": "scripts/seed_demo_accounts.py",
        "legacy_tables_untouched": True,
    }


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        prog="seed_classroom_fixture.py",
        description=(
            "Retired Classroom fixture entrypoint. Does not touch any database; "
            "use scripts/seed_demo_accounts.py for supported demo accounts."
        ),
    )
    parser.add_argument("--json", action="store_true", help="Print structured JSON status")
    args = parser.parse_args(argv)

    payload = status_payload()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"{payload['status']}: {payload['message']}", file=sys.stderr)
    return EXIT_RETIRED


if __name__ == "__main__":
    raise SystemExit(main())
