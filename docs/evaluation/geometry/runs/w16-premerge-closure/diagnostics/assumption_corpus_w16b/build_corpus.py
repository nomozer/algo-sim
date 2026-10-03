# -*- coding: utf-8 -*-
"""W16B — build the primed-name addendum corpus from its hand labels (0 model calls).

Same builders as `../assumption_corpus_w16/build_corpus.py` (imported, not copied); only the
labels and the output differ. Refuses to overwrite. Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w16-premerge-closure/diagnostics/assumption_corpus_w16b/build_corpus.py
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve()
_spec = importlib.util.spec_from_file_location("w16_corpus", HERE.parents[1] / "assumption_corpus_w16" / "build_corpus.py")
W16 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(W16)
LABELS = HERE.with_name("LABELS.json")
OUT = HERE.with_name("CORPUS.json")


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    rows = []
    for cid, l in json.loads(LABELS.read_text(encoding="utf-8"))["rows"].items():
        ct, raw = W16.BUILDERS[l["builder"]](cid, l.get("arg"))
        v = W16.validate_semantic_program(raw)
        ok = bool(v.ok and v.spec is not None)
        rows.append({"id": cid, "group": l["group"], "label": l["label"], "expect": l["expect"],
                     "reason": l["reason"], "contract": ct.model_dump(mode="json"),
                     "program": v.spec.model_dump(mode="json", exclude_none=True) if ok else raw,
                     "program_schema_ok": ok})
    OUT.write_text(json.dumps({"corpus": "W16B_PRIMED_NAME_ADDENDUM", "model_calls": 0,
                               "labels_sha256_lf": W16._sha_lf(LABELS), "rows": rows},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{OUT.name}: {len(rows)} rows; schema-invalid programs: "
          f"{[r['id'] for r in rows if not r['program_schema_ok']]}")


if __name__ == "__main__":
    main()
