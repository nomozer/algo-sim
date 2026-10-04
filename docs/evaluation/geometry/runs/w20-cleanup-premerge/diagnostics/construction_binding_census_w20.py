# -*- coding: utf-8 -*-
"""W20 census — the construction-binding stage with amendment §17 on every registered corpus (W14, W15, W15B,
W16, W16B, W17, W17C, W18), compared row by row with the W18 census. 0 model calls.

Reuses the W18 census code as is (`w18-binding-focus/diagnostics/construction_binding_census_w18.py`, immutable:
imported, never edited). Judges:
  (1) the registered SHIP rule (§9, unchanged) on W14 + W15 + W15B;
  (2) every route outcome (stage, reason code, servable) that changed since the W18 census, row by row — a change
      made by any stage other than `construction_binding` is a regression; a served row now refused is listed;
  (3) the W18 rows by their labels (route outcome and binding status of the key constructions).
Refuses to overwrite. Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w20-cleanup-premerge/diagnostics/construction_binding_census_w20.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[6]
W18 = ROOT / "docs/evaluation/geometry/runs/w18-binding-focus/diagnostics"
sys.path.insert(0, str(W18))
import construction_binding_census_w18 as C18  # noqa: E402

PREV = W18 / "CONSTRUCTION_BINDING_CENSUS_W18.json"
OUT_C = HERE.with_name("CONSTRUCTION_BINDING_CENSUS_W20.json")
OUT_D = HERE.with_name("CONSTRUCTION_BINDING_DECISION_W20.json")


def main() -> None:
    for p in (OUT_C, OUT_D):
        if p.exists():
            raise SystemExit(f"refusing to overwrite {p}")
    rows = []
    for ten, p in C18.CORPORA.items():
        lop = {"W16B": "W16"}.get(ten, ten)                 # W16 round 2 filed W16B rows under "W16"
        rows += [C18.do_hang(r, lop) | ({"corpus_layer": ten} if ten != lop else {})
                 for r in json.loads(p.read_text(encoding="utf-8"))["rows"]]
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    R1 = C18.R1
    census = {"census": "W20_CONSTRUCTION_BINDING_CENSUS", "model_calls": 0, "measured_at_commit": head,
              "working_tree": "measured on the commit above plus the uncommitted §17 change when run before its commit",
              "corpora": {k: {"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256_lf": R1._sha_lf(p.read_bytes())}
                          for k, p in C18.CORPORA.items()},
              "re_execution_budget": R1.G.NGAN_SACH_CHAY_LAI, "rows": rows}
    raw = (json.dumps(census, ensure_ascii=False, indent=1, default=str) + "\n").encode("utf-8")
    OUT_C.write_bytes(raw)
    mm = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                         "tests/geometry/test_assumption_certificate.py", "-k", R1.METAMORPHIC],
                        cwd=ROOT / "backend", capture_output=True, text=True,
                        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"})
    # (1) the registered SHIP rule on the corpora it was registered for — unchanged.
    dec = R1.quyet_dinh([r for r in rows if r["corpus"] in ("W14", "W15", "W15B")], R1._sha_lf(raw), mm.returncode)
    dec["rule"] += " — W20 re-run on W14 + W15 + W15B with the §17 construction-binding stage (§9 unchanged)"
    dec["f_metamorphic_tests_tail"] = mm.stdout.strip().splitlines()[-1:] if mm.stdout else []
    # (2) every route change since the W18 census, row by row.
    truoc = {(r.get("corpus_layer", r["corpus"]), r["id"]): r for r in json.loads(PREV.read_text(encoding="utf-8"))["rows"]
             if r.get("measured")}
    doi = {}
    for r in rows:
        k = (r.get("corpus_layer", r["corpus"]), r["id"])
        if r.get("measured") and k in truoc and C18._tuyen(truoc[k]) != C18._tuyen(r):
            doi[f"{k[0]}:{k[1]}"] = {"label": r["label"], "w18": list(C18._tuyen(truoc[k])), "w20": list(C18._tuyen(r)),
                                     "subjects": r["route_today"]["reason_subjects"],
                                     "binding": r["route_today"]["construction_binding"]}
    dec["previous_census"] = {"path": str(PREV.relative_to(ROOT)).replace("\\", "/"),
                              "sha256_lf": R1._sha_lf(PREV.read_bytes())}
    dec["rows_compared"] = sum(1 for r in rows if r.get("measured")
                               and (r.get("corpus_layer", r["corpus"]), r["id"]) in truoc)
    dec["route_changes_since_w18"] = doi
    dec["route_changes_not_by_binding"] = sorted(k for k, v in doi.items() if v["w20"][0] != C18.CHANG)
    dec["served_before_refused_now"] = sorted(k for k, v in doi.items() if v["w18"][2] and not v["w20"][2])
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
        for r in w18 if r.get("measured") and not C18._w18_dung(r)}
    dec["w20_pass"] = (dec["decision"] == "SHIP" and not dec["route_changes_not_by_binding"]
                       and not dec["w18_unmeasured"] and not dec["w18_expectation_mismatches"])
    OUT_D.write_text(json.dumps(dec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: dec[k] for k in dec if k not in ("verdicts_by_group", "route_changes_since_w18")},
                     ensure_ascii=False, indent=1))
    print("route changes since W18:", json.dumps(doi, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
