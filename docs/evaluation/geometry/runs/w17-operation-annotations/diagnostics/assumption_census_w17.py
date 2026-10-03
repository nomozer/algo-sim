# -*- coding: utf-8 -*-
"""W17 census — the gate after the W17 fixes on every registered corpus (W14, W15, W15B, W16, W16B)
plus the W17 operation-binding / goal-clause corpus (§15.1, §15.2). 0 model calls.

Reuses the W15 measurement code as is (`w15-assumption-closure/diagnostics/assumption_census_w15.py`
and `_r2.py`, immutable). Judges:
  (1) the registered SHIP rule (§9, unchanged) on W14 + W15 + W15B — incl. 18/18 AC2 gold rows;
  (2) the W16 + W16B rows by their labels; the W16 declared limit A′ (A2b, registered expectation
      PROVEN_SAFE:C0 = "known wrongly certified") is now judged by §15.1: refused at `assumption`
      with CONSTRUCTION_NOT_TEXT_BOUND and not servable;
  (3) the W17 rows by their registered expectations (gate status + reason for O rows, route stage +
      reason or `served` for G rows);
  (4) every gate change since W16 round 2, row by row (reported; each one is explained in REPORT).
Refuses to overwrite. Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w17-operation-annotations/diagnostics/assumption_census_w17.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[6]
RUNS = ROOT / "docs/evaluation/geometry/runs"
sys.argv = sys.argv[:1]                       # R2 reads its round number from argv at import
sys.path.insert(0, str(RUNS / "w15-assumption-closure/diagnostics"))
import assumption_census_w15 as R1  # noqa: E402
import assumption_census_w15_r2 as R2  # noqa: E402

W16_DIR = RUNS / "w16-premerge-closure/diagnostics"
CORPORA = {"W14": R1.W14_CORPUS, "W15": R1.W15_CORPUS, "W15B": R2.W15B_CORPUS,
           "W16": W16_DIR / "assumption_corpus_w16/CORPUS.json", "W16B": W16_DIR / "assumption_corpus_w16b/CORPUS.json",
           "W17": HERE.parent / "assumption_corpus_w17/CORPUS.json"}
PREV = W16_DIR / "ASSUMPTION_CENSUS_W16_R2.json"
OUT_C = HERE.with_name("ASSUMPTION_CENSUS_W17.json")
OUT_D = HERE.with_name("ASSUMPTION_MECHANISM_DECISION_W17.json")
A_PRIME = "A2b_cat_bang_alpha_khi_de_noi_beta"
MA_LECH = "CONSTRUCTION_NOT_TEXT_BOUND"


def _w17_dung(r: dict) -> bool:
    e, rt = r["expect"], r["route_today"]
    if e == "served":
        return bool(rt["servable"])
    if e.startswith("grounding:"):
        return (rt["stage"], rt["reason_code"], rt["servable"]) == ("grounding", e.split(":", 1)[1], False)
    if e.startswith("PROVEN_SAFE"):
        return bool(R1._du_doan_dung(r)) and bool(rt["servable"])
    trang_thai, ma = e.split(":", 1)
    return r["status"] == trang_thai and r["reason_code"] == ma and not rt["servable"]


def main() -> None:
    for p in (OUT_C, OUT_D):
        if p.exists():
            raise SystemExit(f"refusing to overwrite {p}")
    rows = []
    for ten, p in CORPORA.items():
        lop = {"W16B": "W16"}.get(ten, ten)                 # W16 round 2 filed W16B rows under "W16"
        rows += [R2.do_hang(r, lop) | ({"corpus_layer": ten} if ten != lop else {})
                 for r in json.loads(p.read_text(encoding="utf-8"))["rows"]]
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    census = {"census": "W17_ASSUMPTION_CENSUS", "model_calls": 0, "measured_at_commit": head,
              "corpora": {k: {"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256_lf": R1._sha_lf(p.read_bytes())}
                          for k, p in CORPORA.items()},
              "re_execution_budget": R1.G.NGAN_SACH_CHAY_LAI, "rows": rows}
    raw = (json.dumps(census, ensure_ascii=False, indent=1, default=str) + "\n").encode("utf-8")
    OUT_C.write_bytes(raw)
    mm = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                         "tests/geometry/test_assumption_certificate.py", "-k", R1.METAMORPHIC],
                        cwd=ROOT / "backend", capture_output=True, text=True,
                        env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    # (1) the registered SHIP rule on the corpora it was registered for — unchanged.
    w15 = [r for r in rows if r["corpus"] in ("W14", "W15", "W15B")]
    dec = R1.quyet_dinh(w15, R1._sha_lf(raw), mm.returncode)
    dec["rule"] += " — W17 re-run on W14 + W15 + W15B after the W17 fixes (§9 unchanged)"
    dec["f_metamorphic_tests_tail"] = mm.stdout.strip().splitlines()[-1:] if mm.stdout else []
    # (2) W16 + W16B rows by their labels; A′ judged by §15.1 (no longer a declared limit).
    w16 = [r for r in rows if r["corpus"] == "W16" and r.get("measured")]
    dec["w16_a_proven_safe_on_depends_or_must_refuse"] = [
        r["id"] for r in w16 if r["label"] in ("DEPENDS", "MUST_REFUSE") and r["status"] == "PROVEN_SAFE"]
    dec["w16_c_dependent_on_invariant"] = [r["id"] for r in w16 if r["label"] == "INVARIANT"
                                           and r["status"] == R1.G.DEPENDENT]
    dec["w16_expectation_mismatches"] = {
        r["id"]: [r["expect"], r["status"], r["certificate"]] for r in w16
        if r["id"] != A_PRIME and R1._du_doan_dung(r) is False}
    dec["w16_route_served_depends_or_must_refuse"] = sorted(
        r["id"] for r in w16 if r["label"] in ("DEPENDS", "MUST_REFUSE") and r["route_today"]["servable"])
    a = next(r for r in w16 if r["id"] == A_PRIME)
    dec["w17_a_prime_closed"] = {
        "id": A_PRIME, "w16_registered_expectation": a["expect"], "status": a["status"],
        "reason_code": a["reason_code"], "subjects": a["subjects"], "route_today": a["route_today"],
        "pass": a["status"] != "PROVEN_SAFE" and a["reason_code"] == MA_LECH and not a["route_today"]["servable"]
        and a["route_today"]["stage"] == "assumption"}
    # (3) W17 rows by their registered expectations.
    w17 = [r for r in rows if r["corpus"] == "W17"]
    dec["w17_unmeasured"] = [r["id"] for r in w17 if not r.get("measured")]
    dec["w17_expectation_mismatches"] = {
        r["id"]: {"expect": r["expect"], "status": r["status"], "certificate": r["certificate"],
                  "reason_code": r["reason_code"], "route_today": r["route_today"]}
        for r in w17 if r.get("measured") and not _w17_dung(r)}
    dec["w17_rows"] = {r["id"]: {"label": r["label"], "expect": r["expect"], "status": r.get("status"),
                                 "certificate": r.get("certificate"), "reason_code": r.get("reason_code"),
                                 "route": [r["route_today"]["stage"], r["route_today"]["reason_code"],
                                           r["route_today"]["servable"]] if r.get("measured") else None}
                       for r in w17}
    dec["w17_pass"] = (dec["decision"] == "SHIP" and not dec["w16_a_proven_safe_on_depends_or_must_refuse"]
                       and not dec["w16_c_dependent_on_invariant"] and not dec["w16_expectation_mismatches"]
                       and not dec["w16_route_served_depends_or_must_refuse"] and dec["w17_a_prime_closed"]["pass"]
                       and not dec["w17_unmeasured"] and not dec["w17_expectation_mismatches"])
    # (4) every gate change since W16 round 2, row by row.
    truoc = {(r["corpus"], r["id"]): (r.get("status"), r.get("certificate"), r.get("subjects"))
             for r in json.loads(PREV.read_text(encoding="utf-8"))["rows"]}
    dec["report_w16r2_to_w17_gate_changes"] = {
        f"{r['corpus']}:{r['id']}": [list(truoc[(r["corpus"], r["id"])]),
                                     [r.get("status"), r.get("certificate"), r.get("subjects")]]
        for r in rows if (r["corpus"], r["id"]) in truoc
        and truoc[(r["corpus"], r["id"])] != (r.get("status"), r.get("certificate"), r.get("subjects"))}
    do = [r for r in rows if r.get("measured")]
    dec["report_route_served_depends_or_must_refuse"] = sorted(
        f"{r['corpus']}:{r['id']}" for r in do if r["label"] in ("DEPENDS", "MUST_REFUSE")
        and not r.get("before_gate") and r["route_today"]["servable"])
    OUT_D.write_text(json.dumps(dec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: dec[k] for k in dec if k not in ("verdicts_by_group", "w17_rows")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
