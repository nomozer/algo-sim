"""Run from a backend/ directory: python <path>/probe.py — route outcome of every labelled C0 row (0 model calls).
C1 rows: ../../c0-whole-solid-reader/diagnostics/probe_c1_equivalence.py (variant `unnamed_everywhere`)."""
import json, os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, os.getcwd()); sys.path.insert(0, str(HERE.parents[1] / "c0-whole-solid-grounding" / "diagnostics"))
import c0_whole_solid_cases as M
from app.simulation.semantic_program.route import verify_and_compile
ROWS = json.loads((HERE.parent / "labels.json").read_text(encoding="utf-8"))["c0_rows"]
for rid, r in ROWS.items():
    M.LABELS[rid] = r
    _de, c, sp = M.hop_dong_va_chuong_trinh(rid)
    o = verify_and_compile(c, sp)
    print(json.dumps({"row": rid, "expect": r["expect"], "servable": o.servable, "stage": o.stage_reached,
                      "reason": o.reason_code, "certificate": o.assumption_certificate}, ensure_ascii=False))
