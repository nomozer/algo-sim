# -*- coding: utf-8 -*-
"""W16 census — the gate after the W16 fixes, on the W14 + W15 + W15B corpora (registered
SHIP rule of ASSUMPTION_CERTIFICATE_AMENDMENT §9, unchanged) plus the W16 adversarial
corpus (§14). 0 model calls.

Reuses the W15 measurement code as is (`w15-assumption-closure/diagnostics/assumption_census_w15.py`
and `_r2.py`, immutable) and compares every W14/W15/W15B row with W15 round 3. W16 rows are
judged by their own labels and expectations; the declared limit A' (§14.1) is reported, not
gated. Refuses to overwrite. Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w16-premerge-closure/diagnostics/assumption_census_w16.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[6]
W15 = ROOT / "docs/evaluation/geometry/runs/w15-assumption-closure/diagnostics"
sys.argv = sys.argv[:1]                       # R2 reads its round number from argv at import
sys.path.insert(0, str(W15))
import assumption_census_w15 as R1  # noqa: E402
import assumption_census_w15_r2 as R2  # noqa: E402

W16_CORPUS = HERE.parent / "assumption_corpus_w16" / "CORPUS.json"
R3 = W15 / "ASSUMPTION_CENSUS_W15_R3.json"
OUT_C = HERE.with_name("ASSUMPTION_CENSUS_W16.json")
OUT_D = HERE.with_name("ASSUMPTION_MECHANISM_DECISION_W16.json")
GIOI_HAN = "W16_A_PRIME_LIMIT"


def main() -> None:
    for p in (OUT_C, OUT_D):
        if p.exists():
            raise SystemExit(f"refusing to overwrite {p}")
    rows = [R2.do_hang(r, "W14") for r in json.loads(R1.W14_CORPUS.read_text(encoding="utf-8"))["rows"]]
    rows += [R2.do_hang(r, "W15") for r in json.loads(R1.W15_CORPUS.read_text(encoding="utf-8"))["rows"]]
    rows += [R2.do_hang(r, "W15B") for r in json.loads(R2.W15B_CORPUS.read_text(encoding="utf-8"))["rows"]]
    rows += [R2.do_hang(r, "W16") for r in json.loads(W16_CORPUS.read_text(encoding="utf-8"))["rows"]]
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    census = {"census": "W16_ASSUMPTION_CENSUS", "model_calls": 0, "measured_at_commit": head,
              "corpora": {k: {"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256_lf": R1._sha_lf(p.read_bytes())}
                          for k, p in (("W14", R1.W14_CORPUS), ("W15", R1.W15_CORPUS), ("W15B", R2.W15B_CORPUS),
                                       ("W16", W16_CORPUS))},
              "re_execution_budget": R1.G.NGAN_SACH_CHAY_LAI, "rows": rows}
    raw = (json.dumps(census, ensure_ascii=False, indent=1, default=str) + "\n").encode("utf-8")
    OUT_C.write_bytes(raw)
    mm = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                         "tests/geometry/test_assumption_certificate.py", "-k", R1.METAMORPHIC],
                        cwd=ROOT / "backend", capture_output=True, text=True,
                        env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    # (1) the W15 registered SHIP rule, on the corpora it was registered for — unchanged.
    w15 = [r for r in rows if r["corpus"] != "W16"]
    dec = R1.quyet_dinh(w15, R1._sha_lf(raw), mm.returncode)
    dec["rule"] += " — W16 re-run on W14 + W15 + W15B after the W16 fixes (§9 unchanged)"
    dec["f_metamorphic_tests_tail"] = mm.stdout.strip().splitlines()[-1:] if mm.stdout else []
    # (2) W16 rows: labels and registered expectations (§14); the declared limit is reported apart.
    w16 = [r for r in rows if r["corpus"] == "W16" and r.get("measured")]
    trong = [r for r in w16 if r["group"] != GIOI_HAN]
    dec["w16_a_proven_safe_on_depends_or_must_refuse"] = [
        r["id"] for r in trong if r["label"] in ("DEPENDS", "MUST_REFUSE") and r["status"] == "PROVEN_SAFE"]
    dec["w16_c_dependent_on_invariant"] = [r["id"] for r in trong if r["label"] == "INVARIANT"
                                           and r["status"] == R1.G.DEPENDENT]
    dec["w16_expectation_mismatches"] = {
        r["id"]: [r["expect"], r["status"], r["certificate"]] for r in w16 if R1._du_doan_dung(r) is False}
    dec["w16_route_served_depends_or_must_refuse"] = sorted(
        r["id"] for r in trong if r["label"] in ("DEPENDS", "MUST_REFUSE") and r["route_today"]["servable"])
    dec["w16_declared_limit_rows"] = {r["id"]: {"label": r["label"], "status": r["status"],
                                                "certificate": r["certificate"],
                                                "route_servable": r["route_today"]["servable"]}
                                      for r in w16 if r["group"] == GIOI_HAN}
    dec["w16_pass"] = not (dec["w16_a_proven_safe_on_depends_or_must_refuse"] or dec["w16_c_dependent_on_invariant"]
                           or dec["w16_expectation_mismatches"] or dec["w16_route_served_depends_or_must_refuse"])
    # (3) every W14/W15/W15B gate change since W15 round 3, row by row.
    truoc = {(r["corpus"], r["id"]): (r.get("status"), r.get("certificate"), r.get("subjects"))
             for r in json.loads(R3.read_text(encoding="utf-8"))["rows"]}
    dec["report_w15r3_to_w16_gate_changes"] = {
        f"{r['corpus']}:{r['id']}": [list(truoc[(r["corpus"], r["id"])]),
                                     [r.get("status"), r.get("certificate"), r.get("subjects")]]
        for r in w15 if (r["corpus"], r["id"]) in truoc
        and truoc[(r["corpus"], r["id"])] != (r.get("status"), r.get("certificate"), r.get("subjects"))}
    do = [r for r in rows if r.get("measured")]
    dec["report_route_served_depends_or_must_refuse_w14_w15"] = sorted(
        f"{r['corpus']}:{r['id']}" for r in do if r["corpus"] != "W16" and r["label"] in ("DEPENDS", "MUST_REFUSE")
        and not r["before_gate"] and r["route_today"]["servable"])
    OUT_D.write_text(json.dumps(dec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: dec[k] for k in dec if k not in ("verdicts_by_group",)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
