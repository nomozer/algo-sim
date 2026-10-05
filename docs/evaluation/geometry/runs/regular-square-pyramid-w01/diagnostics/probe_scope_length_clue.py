# -*- coding: utf-8 -*-
"""regular-square-pyramid-w01 — acceptance probe of ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE (W18 rows B18/B19) through the
product boundary `run_pipeline`, frozen analyze + program from the W18 corpus builders, 0 model calls.

usage (from backend/): python ../docs/evaluation/geometry/runs/regular-square-pyramid-w01/diagnostics/probe_scope_length_clue.py
writes diagnostics/SCOPE_LENGTH_CLUE_PROBE_<sha8>.json next to this script; refuses to overwrite.
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO / "backend"))

from scripts.generate_generic_tier_a_fixtures import _run_frozen_program  # noqa: E402
from app.learner_messages import attach_learner_reason  # noqa: E402
from app.simulation.semantic_program.validator import validate_semantic_program  # noqa: E402
from tests.geometry import test_construction_binding as CB  # noqa: E402

sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
out = HERE / f"SCOPE_LENGTH_CLUE_PROBE_{sha[:8]}.json"
if out.exists():
    raise SystemExit(f"refusing to overwrite {out}")
rows = []
for ca, want in (("B18_prime_ok", "served"), ("B19_prime_wrong", "refused:construction_binding")):
    contract, program = CB.CA[ca]()
    spec = validate_semantic_program(program).spec
    env = attach_learner_reason(asyncio.run(_run_frozen_program(contract.problem_text, contract, spec)))
    got = "served" if env.get("status") == "ok" else f"refused:{env.get('stage_reached')}"
    rows.append({"id": ca, "text": contract.problem_text, "expected": want, "observed": got,
                 "reason_code": env.get("reason_code"), "pass": got == want})
out.write_text(json.dumps({"probe": "ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE acceptance", "commit": sha,
                           "boundary": "app.ai.pipeline.run_pipeline (frozen analyze + program)", "model_calls": 0,
                           "rows": rows, "pass": all(r["pass"] for r in rows)}, ensure_ascii=False, indent=2) + "\n",
               encoding="utf-8", newline="\n")
print(out.name, [(r["id"], r["observed"], r["pass"]) for r in rows])
