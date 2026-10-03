# -*- coding: utf-8 -*-
"""W17 — build the operation-binding / goal-clause corpus from its hand labels (0 model calls).

`LABELS.json` (same directory, committed in Task 0 BEFORE the W17 fixes) names, per row, a builder
over the W17 tests: O rows = `PHEP_DUNG_SAI` / `PHEP_DUNG_DUNG` of
`backend/tests/geometry/test_assumption_certificate.py`, G rows = the goal-clause cases of
`backend/tests/geometry/test_source_grounding_closure.py`. This script only turns labels into
(contract, program) pairs; `../assumption_census_w17.py` measures them. Refuses to overwrite.
Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w17-operation-annotations/diagnostics/assumption_corpus_w17/build_corpus.py
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
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "scripts"))

from app.simulation.semantic_program.validator import validate_semantic_program  # noqa: E402
from tests.geometry import test_assumption_certificate as X  # noqa: E402
from tests.geometry import test_source_grounding_closure as GC  # noqa: E402

_O = {**X.PHEP_DUNG_SAI, **X.PHEP_DUNG_DUNG}
_G = {"G1_do_dai_chi_trong_yeu_cau_chung_minh": lambda: GC._g_chop(GC.G1_TEXT),
      "G2_tinh_biet_du_kien": lambda: GC._g_chop(GC.G2_TEXT)}
BUILDERS = {
    **{b: (lambda cid: _O[cid]()) for b in ("o", "o_solid", "o_target", "o_source", "o_passive")},
    "g": lambda cid: _G[cid](),
    "g_coord": lambda _c: GC._g_p1(),
    "g_p4": lambda _c: GC._g_p4(),
}


def _sha_lf(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    rows = []
    for cid, l in json.loads(LABELS.read_text(encoding="utf-8"))["rows"].items():
        ct, raw = BUILDERS[l["builder"]](cid)
        # The label text is the registered one; the builder must produce exactly that sentence (a
        # "gold …" label describes a transformation that its builder asserts itself, e.g. `_g_p4`).
        if l.get("text") and not l["text"].startswith("gold ") and l["text"] not in ct.problem_text:
            raise SystemExit(f"{cid}: builder text does not contain the labelled text")
        v = validate_semantic_program(raw)
        ok = bool(v.ok and v.spec is not None)
        rows.append({"id": cid, "group": l["group"], "label": l["label"], "expect": l["expect"],
                     "reason": l["reason"], "contract": ct.model_dump(mode="json"),
                     "program": v.spec.model_dump(mode="json", exclude_none=True) if ok else raw,
                     "program_schema_ok": ok})
    OUT.write_text(json.dumps({"corpus": "W17_OPERATION_AND_GOAL_CLAUSE", "model_calls": 0,
                               "labels_sha256_lf": _sha_lf(LABELS), "rows": rows},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{OUT.name}: {len(rows)} rows; schema-invalid programs: "
          f"{[r['id'] for r in rows if not r['program_schema_ok']]}")


if __name__ == "__main__":
    main()
