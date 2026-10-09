"""Run from backend/: python <path>/probe.py — route outcome + served value + Scene3D chart metric per row."""
import json, os, sys
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cases import LABELS, hop_dong_va_chuong_trinh
from app.ai.pipeline import _dung_scene3d
from app.simulation.semantic_program.route import verify_and_compile
for rid, r in LABELS.items():
    c, sp = hop_dong_va_chuong_trinh(rid)
    o = verify_and_compile(c, sp)
    val = metric = None
    if o.servable:
        canh = _dung_scene3d(sp, c)
        w = "V" if r["ask"] == "volume" else "d_SA"
        val = next((x.get("value") for x in canh["objects"] if x["id"] == w), None)
        metric = "chart_metric" in canh
    print(json.dumps({"row": rid, "expect": r["expect"], "servable": o.servable, "value": val, "stage": o.stage_reached,
                      "reason": o.reason_code, "certificate": o.assumption_certificate, "chart_metric": metric},
                     ensure_ascii=False))
