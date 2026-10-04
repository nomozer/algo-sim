# -*- coding: utf-8 -*-
"""W18 — build the construction-binding corpus from its hand labels (0 model calls).

`LABELS.json` (same directory) was committed in `c479f377`, BEFORE the W18 fix it judges. Every row
has a builder of the same id in `backend/tests/geometry/test_construction_binding.py` (`CA`): the
gold p1 text and points (or the W14 cuboid family) plus the row's sentence and program statements.
Refuses to overwrite. Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w18-binding-focus/diagnostics/construction_corpus_w18/build_corpus.py
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
from tests.geometry import test_construction_binding as T  # noqa: E402


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    rows = []
    for cid, l in json.loads(LABELS.read_text(encoding="utf-8"))["rows"].items():
        ct, raw = T.CA[cid]()
        if l["text"].removeprefix("cuboid + ") not in ct.problem_text:
            raise SystemExit(f"{cid}: builder text does not contain the labelled text")
        v = validate_semantic_program(raw)
        ok = bool(v.ok and v.spec is not None)
        rows.append({"id": cid, "group": l["group"], "label": l["label"], "expect": l["expect"],
                     "binding": l["binding"], "reason": l["reason"], "contract": ct.model_dump(mode="json"),
                     "program": v.spec.model_dump(mode="json", exclude_none=True) if ok else raw,
                     "program_schema_ok": ok})
    OUT.write_text(json.dumps({"corpus": "W18_CONSTRUCTION_BINDING", "model_calls": 0,
                               "labels_sha256_lf": hashlib.sha256(LABELS.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
                               "rows": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{OUT.name}: {len(rows)} rows; schema-invalid programs: "
          f"{[r['id'] for r in rows if not r['program_schema_ok']]}")


if __name__ == "__main__":
    main()
