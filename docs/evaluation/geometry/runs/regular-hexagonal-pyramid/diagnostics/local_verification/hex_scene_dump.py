"""LOCAL: dump the Scene3D payload of every served hexagonal row and check its structure (0 model calls).
Run from backend/: python hex_scene_dump.py <run dir> <out dir>"""
import json, os, sys
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(sys.argv[1], "diagnostics"))
from cases import LABELS, hop_dong_va_chuong_trinh
from app.ai.pipeline import _dung_scene3d
from app.simulation.semantic_program.route import verify_and_compile

out = sys.argv[2]
os.makedirs(out, exist_ok=True)
for rid, r in LABELS.items():
    c, sp = hop_dong_va_chuong_trinh(rid)
    o = verify_and_compile(c, sp)
    if not o.servable:
        continue
    scene = _dung_scene3d(sp, c)
    solids = [x for x in scene["objects"] if x.get("type") == "solid"]
    s = solids[0]
    faces = s["faces"]
    edges = {frozenset((f[i], f[(i + 1) % len(f)])) for f in faces for i in range(len(f))}
    nv = len(s["vertices"])
    kinds = sorted(len(f) for f in faces)
    degenerate = any(len(set(f)) != len(f) or len(f) < 3 for f in faces)
    print(json.dumps({"row": rid, "solids": len(solids), "vertices": nv, "faces": len(faces), "face_sizes": kinds,
                      "euler": nv - len(edges) + len(faces), "degenerate": degenerate,
                      "chart_metric": "chart_metric" in scene}))
    with open(os.path.join(out, f"{rid}.json"), "w", encoding="utf-8") as f:
        json.dump(scene, f, ensure_ascii=False)
