"""LOCAL: dump the Scene3D payload of every served prism row and check its structure (0 model calls).
Closed solid: every edge in exactly two faces, opposite orientation in the two (consistent winding), Euler 2, no
degenerate face, 2 base k-gons + k quads, chart_metric present.
Run from backend/: python prism_scene_dump.py <run dir> <out dir>"""
import json, os, sys
from collections import Counter
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(sys.argv[1], "diagnostics"))
from cases import LABELS, hop_dong_va_chuong_trinh
from app.ai.pipeline import _dung_scene3d
from app.simulation.semantic_program.route import verify_and_compile

def orientable(faces):
    """Independent of the kernel: flip faces by BFS so every shared edge is traversed in opposite directions; True iff
    no conflict (closed, consistently orientable surface)."""
    flip, todo = {0: False}, [0]
    def de(f, fl):
        e = [(f[i], f[(i + 1) % len(f)]) for i in range(len(f))]
        return {(b, a) for a, b in e} if fl else set(e)
    while todo:
        i = todo.pop()
        for j, g in enumerate(faces):
            if j == i or not {frozenset(e) for e in de(faces[i], False)} & {frozenset(e) for e in de(g, False)}:
                continue
            need = bool(de(faces[i], flip[i]) & de(g, False))      # same direction on the shared edge ⇒ flip g
            if j not in flip:
                flip[j] = need
                todo.append(j)
            elif flip[j] != need:
                return False
    return len(flip) == len(faces)


out = sys.argv[2]
os.makedirs(out, exist_ok=True)
ok = True
for rid, r in LABELS.items():
    c, sp = hop_dong_va_chuong_trinh(rid)
    if not verify_and_compile(c, sp).servable:
        continue
    scene = _dung_scene3d(sp, c)
    solids = [x for x in scene["objects"] if x.get("type") == "solid"]
    s, k = solids[0], r["k"]
    faces = s["faces"]
    directed = Counter((f[i], f[(i + 1) % len(f)]) for f in faces for i in range(len(f)))
    edges = Counter(frozenset((f[i], f[(i + 1) % len(f)])) for f in faces for i in range(len(f)))
    nv = len(s["vertices"])
    row = {"row": rid, "solids": len(solids), "vertices": nv, "faces": len(faces), "edges": len(edges),
           "face_sizes": sorted(len(f) for f in faces), "euler": nv - len(edges) + len(faces),
           "each_edge_two_faces": all(n == 2 for n in edges.values()),
           # informational: the model-style program's own winding (the kernel re-orients, section.py; mesh is DoubleSide)
           "program_winding_consistent": all(n == 1 for n in directed.values()),
           "orientable": orientable(faces),
           "degenerate": any(len(set(f)) != len(f) or len(f) < 3 for f in faces),
           "chart_metric": "chart_metric" in scene}
    row["ok"] = (row["solids"] == 1 and nv == 2 * k and row["faces"] == k + 2 and row["edges"] == 3 * k
                 and row["face_sizes"] == sorted([k, k] + [4] * k) and row["euler"] == 2 and row["each_edge_two_faces"]
                 and row["orientable"] and not row["degenerate"] and row["chart_metric"])
    ok &= row["ok"]
    print(json.dumps(row))
    with open(os.path.join(out, f"{rid}.json"), "w", encoding="utf-8") as f:
        json.dump(scene, f, ensure_ascii=False)
print("SCENE_OK" if ok else "SCENE_FAILED")
