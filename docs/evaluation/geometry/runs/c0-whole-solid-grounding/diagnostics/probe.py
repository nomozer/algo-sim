"""Run from a backend/ directory: python <path>/probe.py — prints each labelled row's route outcome (0 model calls)."""
import json, os, sys
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c0_whole_solid_cases import LABELS, hop_dong_va_chuong_trinh
from app.simulation.semantic_program.route import verify_and_compile
for rid, r in LABELS.items():
    _t, c, sp = hop_dong_va_chuong_trinh(rid)
    o = verify_and_compile(c, sp)
    print(json.dumps({"row": rid, "expect": r["expect"], "servable": o.servable, "stage": o.stage_reached,
                      "reason": o.reason_code, "certificate": o.assumption_certificate}, ensure_ascii=False))
