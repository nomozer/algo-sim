# -*- coding: utf-8 -*-
"""W18 census — the construction-binding stage (amendment §16) on every registered corpus (W14, W15,
W15B, W16, W16B, W17, W17C) and on the W18 corpus. 0 model calls.

Reuses the W15 measurement code as is (`w15-assumption-closure/diagnostics/assumption_census_w15.py`
and `_r2.py`, immutable) and adds the W18 route facts (refusal cause, reason subjects, binding
statuses). Judges:
  (1) the registered SHIP rule (§9, unchanged) on W14 + W15 + W15B;
  (2) every route outcome (stage, reason code, servable) that changed since the W17 round-2 census,
      row by row — a change made by any stage other than `construction_binding` is a regression;
      a served row now refused by `construction_binding` is listed for explanation in REPORT;
  (3) the W18 rows by their labels (route outcome and binding status of the key constructions).
Refuses to overwrite. Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w18-binding-focus/diagnostics/construction_binding_census_w18.py
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
sys.argv = sys.argv[:1]                       # R2 reads a round number from argv at import
sys.path.insert(0, str(RUNS / "w15-assumption-closure/diagnostics"))
import assumption_census_w15 as R1  # noqa: E402
import assumption_census_w15_r2 as R2  # noqa: E402
from app.simulation.semantic_program.contract import SemanticProgramSpec  # noqa: E402
from app.simulation.semantic_program.request_contract import RequestContract  # noqa: E402
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402

W16_DIR = RUNS / "w16-premerge-closure/diagnostics"
W17_DIR = RUNS / "w17-operation-annotations/diagnostics"
CORPORA = {"W14": R1.W14_CORPUS, "W15": R1.W15_CORPUS, "W15B": R2.W15B_CORPUS,
           "W16": W16_DIR / "assumption_corpus_w16/CORPUS.json", "W16B": W16_DIR / "assumption_corpus_w16b/CORPUS.json",
           "W17": W17_DIR / "assumption_corpus_w17/CORPUS.json", "W17C": W17_DIR / "assumption_corpus_w17c/CORPUS.json",
           "W18": HERE.parent / "construction_corpus_w18/CORPUS.json"}
PREV = W17_DIR / "ASSUMPTION_CENSUS_W17_R2.json"
OUT_C = HERE.with_name("CONSTRUCTION_BINDING_CENSUS_W18.json")
OUT_D = HERE.with_name("CONSTRUCTION_BINDING_DECISION_W18.json")
CHANG = "construction_binding"


def do_hang(row: dict, lop: str) -> dict:
    out = R2.do_hang(row, lop)
    if out.get("measured"):
        r = verify_and_compile(RequestContract.model_validate(row["contract"]),
                               SemanticProgramSpec.model_validate(row["program"]))
        out["route_today"] |= {"refusal_cause": r.refusal_cause, "reason_subjects": list(r.reason_subjects or []),
                               "construction_binding": dict(r.construction_binding)}
    if "binding" in row:
        out["binding"] = row["binding"]
    return out


def _w18_dung(r: dict) -> bool:
    e, rt = r["expect"], r["route_today"]
    tuyen = (bool(rt["servable"]) if e == "served"
             else not rt["servable"] and [rt["stage"], rt["reason_code"], rt["refusal_cause"]] == e.split(":")[1:])
    return tuyen and all(rt["construction_binding"].get(k) == v for k, v in r["binding"].items())


def _tuyen(r: dict) -> tuple:
    rt = r["route_today"]
    return rt["stage"], rt["reason_code"], rt["servable"]


def main() -> None:
    for p in (OUT_C, OUT_D):
        if p.exists():
            raise SystemExit(f"refusing to overwrite {p}")
    rows = []
    for ten, p in CORPORA.items():
        lop = {"W16B": "W16"}.get(ten, ten)                 # W16 round 2 filed W16B rows under "W16"
        rows += [do_hang(r, lop) | ({"corpus_layer": ten} if ten != lop else {})
                 for r in json.loads(p.read_text(encoding="utf-8"))["rows"]]
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    census = {"census": "W18_CONSTRUCTION_BINDING_CENSUS", "model_calls": 0, "measured_at_commit": head,
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
    dec = R1.quyet_dinh([r for r in rows if r["corpus"] in ("W14", "W15", "W15B")], R1._sha_lf(raw), mm.returncode)
    dec["rule"] += " — W18 re-run on W14 + W15 + W15B with the construction-binding stage (§9 unchanged)"
    dec["f_metamorphic_tests_tail"] = mm.stdout.strip().splitlines()[-1:] if mm.stdout else []
    # (2) every route change since W17 round 2, row by row.
    truoc = {(r.get("corpus_layer", r["corpus"]), r["id"]): r for r in json.loads(PREV.read_text(encoding="utf-8"))["rows"]
             if r.get("measured")}
    doi = {}
    for r in rows:
        k = (r.get("corpus_layer", r["corpus"]), r["id"])
        if r.get("measured") and k in truoc and _tuyen(truoc[k]) != _tuyen(r):
            doi[f"{k[0]}:{k[1]}"] = {"label": r["label"], "w17_r2": list(_tuyen(truoc[k])), "w18": list(_tuyen(r)),
                                     "subjects": r["route_today"]["reason_subjects"],
                                     "binding": r["route_today"]["construction_binding"]}
    dec["route_changes_since_w17_r2"] = doi
    dec["route_changes_not_by_binding"] = sorted(k for k, v in doi.items() if v["w18"][0] != CHANG)
    dec["served_before_refused_by_binding"] = sorted(k for k, v in doi.items() if v["w17_r2"][2] and v["w18"][0] == CHANG)
    dec["binding_statuses_by_corpus"] = {}
    for r in rows:
        if r.get("measured"):
            dem = dec["binding_statuses_by_corpus"].setdefault(r.get("corpus_layer", r["corpus"]), {})
            for st in r["route_today"]["construction_binding"].values():
                dem[st] = dem.get(st, 0) + 1
    # (3) W18 rows by their labels.
    w18 = [r for r in rows if r["corpus"] == "W18"]
    dec["w18_unmeasured"] = [r["id"] for r in w18 if not r.get("measured")]
    dec["w18_expectation_mismatches"] = {
        r["id"]: {"expect": r["expect"], "binding": r["binding"], "route_today": r["route_today"]}
        for r in w18 if r.get("measured") and not _w18_dung(r)}
    dec["w18_rows"] = {r["id"]: {"label": r["label"], "expect": r["expect"], "route": list(_tuyen(r)),
                                 "refusal_cause": r["route_today"]["refusal_cause"],
                                 "binding": r["route_today"]["construction_binding"]} for r in w18 if r.get("measured")}
    dec["w18_pass"] = (dec["decision"] == "SHIP" and not dec["route_changes_not_by_binding"]
                       and not dec["w18_unmeasured"] and not dec["w18_expectation_mismatches"])
    OUT_D.write_text(json.dumps(dec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: dec[k] for k in dec if k not in ("verdicts_by_group", "w18_rows", "route_changes_since_w17_r2")},
                     ensure_ascii=False, indent=1))
    print("route changes since W17 R2:", json.dumps(doi, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
