"""Run from backend/: python <path>/probe.py — route outcome, served V, Scene3D solid counts per labelled row."""
import json, os, sys
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cases import LABELS, hop_dong_va_chuong_trinh
from app.ai.pipeline import _dung_scene3d
from app.simulation.semantic_program.route import verify_and_compile
for rid, r in LABELS.items():
    c, sp = hop_dong_va_chuong_trinh(rid)
    o = verify_and_compile(c, sp)
    val = shape = None
    if o.servable:
        canh = _dung_scene3d(sp, c)
        val = next((x.get("value") for x in canh["objects"] if x["id"] == "V"), None)
        k = next(x for x in canh["objects"] if x["id"] == "khoi")
        canh_k = {frozenset((f[i], f[(i + 1) % len(f)])) for f in k["faces"] for i in range(len(f))}
        shape = {"V": len(k["vertex_ids"]), "F": len(k["faces"]), "E": len(canh_k), "chart_metric": "chart_metric" in canh}
    print(json.dumps({"row": rid, "expect": r["expect"], "servable": o.servable, "value": val, "stage": o.stage_reached,
                      "reason": o.reason_code, "certificate": o.assumption_certificate, "scene": shape},
                     ensure_ascii=False))
