# -*- coding: utf-8 -*-
"""W15 Task 6 — build the W15B addendum corpus from its hand labels (0 model calls).

`LABELS.json` (same directory) names, per row, a builder over committed test fixtures —
the tests that pin each Task 6 correction (`backend/tests/geometry`). This script only turns
labels into (contract, program) pairs; census round 2 measures them. Refuses to overwrite.
Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w15-assumption-closure/diagnostics/assumption_corpus_w15b/build_corpus.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[7]
LABELS = HERE.with_name("LABELS.json")
OUT = HERE.with_name("CORPUS.json")
NGUON_GOLD = "docs/evaluation/geometry/thesis-final-acceptance/CORPUS.json"
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "scripts"))

from app.simulation.semantic_program.request_contract import RequestContract  # noqa: E402
from app.simulation.semantic_program.validator import validate_semantic_program  # noqa: E402
from tests.geometry import test_assumption_certificate as X  # noqa: E402
from tests.geometry import test_segment_relation_consistency as SRC  # noqa: E402
from tests.geometry import test_segment_relation_coverage as SRV  # noqa: E402
from tests.geometry import w14_cases as W  # noqa: E402


def chop_SA_qua_cau(arg):
    return X._chop_SA_qua_cau(arg[0], sa=arg[1])


def chop_vuong_qua_duong_cheo(_arg):
    return X._chop_vuong_qua_duong_cheo()


def chop_cau(text):
    return W.hop_dong(text, W.chop_tam_giac_payload()), W.chuong_trinh(W.chop_tam_giac()[1])


def hop_doi_ten_phay(hau_to):
    return X._hop_doi_ten_phay(hau_to)


def doan_r3(_arg):
    r = SRC._r3()
    return SRC._hd(RequestContract.model_validate(r["request_contract"])), SRC._voi_t(r, "1/5")


def non_e4(_arg):
    d = SRV._nap_e4()
    p = json.loads(json.dumps(d["parsed_input"]))
    for s in p["statements"]:
        if s.get("target_var") == "T":
            s["expr"]["a"], s["expr"]["b"], s["expr"]["ratio"] = "P", "Q", "5/7"
    return SRV._hd(RequestContract.model_validate(d["request_contract"])), p


def _sha_lf(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    import thesis_acceptance_corpus as TA

    de_nghiem_thu = {ca["problem_text"] for ca in (*TA.CA_DUONG, *TA.CA_AM)}
    rows = []
    for cid, l in json.loads(LABELS.read_text(encoding="utf-8"))["rows"].items():
        ct, raw = globals()[l["builder"]](l.get("arg"))
        v = validate_semantic_program(raw)
        ok = bool(v.ok and v.spec is not None)
        rows.append({"id": cid, "group": l["group"], "label": l["label"], "expect": l["expect"],
                     **({"expect_route": l["expect_route"]} if "expect_route" in l else {}),
                     "reason": l["reason"],
                     **({"source_artifact_path": NGUON_GOLD} if ct.problem_text in de_nghiem_thu else {}),
                     "contract": ct.model_dump(mode="json"),
                     "program": v.spec.model_dump(mode="json", exclude_none=True) if ok else raw,
                     "program_schema_ok": ok})
    OUT.write_text(json.dumps({"corpus": "W15B_ASSUMPTION_ADDENDUM", "model_calls": 0,
                               "labels_sha256_lf": _sha_lf(LABELS), "rows": rows},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{OUT.name}: {len(rows)} rows; schema-invalid programs: "
          f"{[r['id'] for r in rows if not r['program_schema_ok']]}")


if __name__ == "__main__":
    main()
