"""Run from a backend/ directory: python <path>/probe.py — route outcome of every labelled C0 row + the
whole-solid kinds the server reader emits for its text (0 model calls). Cases: ../../c0-whole-solid-grounding."""
import json, os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, os.getcwd()); sys.path.insert(0, str(HERE.parents[1] / "c0-whole-solid-grounding" / "diagnostics"))
import c0_whole_solid_cases as M
from app.simulation.semantic_program.assumption_gate import _doc_de
from app.simulation.semantic_program.route import verify_and_compile
LABELS = json.loads((HERE.parent / "labels.json").read_text(encoding="utf-8"))["rows"]
KINDS = {"pyramid", "regular_square_pyramid", "regular_triangular_pyramid", "base_square", "base_equilateral"}
for rid, r in LABELS.items():
    M.LABELS[rid] = r
    de, c, sp = M.hop_dong_va_chuong_trinh(rid)
    o = verify_and_compile(c, sp)
    read = sorted({f"{x.kind}({','.join(x.entities)})" for x in _doc_de(de)[1] if x.kind in KINDS})
    print(json.dumps({"row": rid, "expect": r["expect"], "servable": o.servable, "stage": o.stage_reached,
                      "reason": o.reason_code, "certificate": o.assumption_certificate, "read": read},
                     ensure_ascii=False))
