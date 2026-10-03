# -*- coding: utf-8 -*-
"""W15 census, round 2 — the gate as wired, after the Task 6 corrections (0 model calls).

Round 1 (`assumption_census_w15.py`, ae64946b) measured the gate before it was wired and
before three corrections (6fa6e582 fully-read rule, 2305f072 right-angle phrasings, a1b17fef
symbol-key binding) and the U3 enforcement scope (45d014b0). Round 2 re-runs the SAME row
measurement and the SAME registered SHIP rule (§9) on W14 + W15 + the W15B addendum, and
also records the route's `assumption_enforced`. Never overwrites round 1. Run from the
repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w15-assumption-closure/diagnostics/assumption_census_w15_r2.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))
import assumption_census_w15 as R1  # noqa: E402

from app.simulation.semantic_program.contract import SemanticProgramSpec  # noqa: E402
from app.simulation.semantic_program.request_contract import RequestContract  # noqa: E402
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402

ROOT = R1.ROOT
W15B_CORPUS = HERE.parent / "assumption_corpus_w15b" / "CORPUS.json"
ROUND1 = HERE.with_name("ASSUMPTION_CENSUS_W15.json")
OUT_C = HERE.with_name("ASSUMPTION_CENSUS_W15_R2.json")
OUT_D = HERE.with_name("ASSUMPTION_MECHANISM_DECISION_W15_R2.json")


def do_hang(row: dict, corpus: str) -> dict:
    out = R1.do_hang(row, corpus)
    if out.get("measured"):
        r = verify_and_compile(RequestContract.model_validate(row["contract"]),
                               SemanticProgramSpec.model_validate(row["program"]))
        out["route_today"] |= {"assumption_enforced": r.assumption_enforced,
                               "assumption_status": r.assumption_status}
    if "expect_route" in row:
        out["expect_route"] = row["expect_route"]
    return out


def main() -> None:
    for p in (OUT_C, OUT_D):
        if p.exists():
            raise SystemExit(f"refusing to overwrite {p}")
    rows = [do_hang(r, "W14") for r in json.loads(R1.W14_CORPUS.read_text(encoding="utf-8"))["rows"]]
    rows += [do_hang(r, "W15") for r in json.loads(R1.W15_CORPUS.read_text(encoding="utf-8"))["rows"]]
    rows += [do_hang(r, "W15B") for r in json.loads(W15B_CORPUS.read_text(encoding="utf-8"))["rows"]]
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    census = {"census": "W15_ASSUMPTION_CENSUS_ROUND_2", "model_calls": 0, "measured_at_commit": head,
              "corpora": {k: {"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256_lf": R1._sha_lf(p.read_bytes())}
                          for k, p in (("W14", R1.W14_CORPUS), ("W15", R1.W15_CORPUS), ("W15B", W15B_CORPUS))},
              "re_execution_budget": R1.G.NGAN_SACH_CHAY_LAI, "rows": rows}
    raw = (json.dumps(census, ensure_ascii=False, indent=1, default=str) + "\n").encode("utf-8")
    OUT_C.write_bytes(raw)
    mm = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                         "tests/geometry/test_assumption_certificate.py", "-k", R1.METAMORPHIC],
                        cwd=ROOT / "backend", capture_output=True, text=True,
                        env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    dec = R1.quyet_dinh(rows, R1._sha_lf(raw), mm.returncode)
    dec["rule"] += " — round 2 at the commit above, the gate as wired"
    dec["f_metamorphic_tests_tail"] = mm.stdout.strip().splitlines()[-1:] if mm.stdout else []
    w15b = [r for r in rows if r["corpus"] == "W15B"]
    dec["report_w15b_expectation_mismatches"] = {
        r["id"]: [r["expect"], r["status"], r["certificate"], r["subjects"]] for r in w15b if R1._du_doan_dung(r) is False}
    dec["report_w15b_route_mismatches"] = {
        r["id"]: r["route_today"] for r in w15b if r.get("expect_route") == "SERVED_NOT_ENFORCED"
        and not (r["route_today"]["servable"] and r["route_today"]["assumption_enforced"] is False)}
    do = [r for r in rows if r.get("measured")]
    # The registered SHIP rule judges the gate's status; with the U3 scope the ROUTE outcome is a
    # separate fact: no DEPENDS / MUST_REFUSE row may be served by the route either.
    dec["report_route_served_depends_or_must_refuse"] = sorted(
        f"{r['corpus']}:{r['id']}" for r in do if r["label"] in ("DEPENDS", "MUST_REFUSE")
        and not r["before_gate"] and r["route_today"]["servable"])
    dec["report_enforcement"] = {
        "enforced_rows": sum(1 for r in do if r["route_today"].get("assumption_enforced")),
        "not_enforced_rows": sum(1 for r in do if r["route_today"].get("assumption_enforced") is False),
        "enforced_and_refused_at_assumption": sum(1 for r in do if r["route_today"]["stage"] == "assumption"),
        "not_enforced_but_not_proven_and_served": sorted(
            r["id"] for r in do if r["route_today"].get("assumption_enforced") is False
            and r["status"] not in (R1.G.PROVEN_SAFE, R1.G.NOT_APPLICABLE) and r["route_today"]["servable"])}
    truoc = {(r["corpus"], r["id"]): (r.get("status"), r.get("certificate"), r.get("subjects"))
             for r in json.loads(ROUND1.read_text(encoding="utf-8"))["rows"]}
    dec["report_round1_to_round2_gate_changes"] = {
        f"{r['corpus']}:{r['id']}": [list(truoc[(r["corpus"], r["id"])]), [r.get("status"), r.get("certificate"), r.get("subjects")]]
        for r in rows if (r["corpus"], r["id"]) in truoc
        and truoc[(r["corpus"], r["id"])] != (r.get("status"), r.get("certificate"), r.get("subjects"))}
    OUT_D.write_text(json.dumps(dec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: dec[k] for k in dec if k not in ("verdicts_by_group",)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
