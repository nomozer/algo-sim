import sys; sys.path.insert(0, "."); sys.path.insert(0, sys.argv[1])
import probe as P
P.use_triangle()
def show(name, extra):
    r, _ = P.T.run("A", extra, solid="S.ABC")
    segs = [(o["id"], o["display_label"]) for o in r.scene3d["objects"] if o["type"] in ("polygon3", "segment3")]
    ann = [a for a in r.scene3d.get("annotations", [])] if isinstance(r.scene3d.get("annotations"), list) else r.scene3d.get("annotations")
    print("==", name, r.status, segs)
    print("   formation keys:", [k for k in r.scene3d if k not in ("objects",)])
show("no extra", [])
show("proj S->(ABC) forward (S known)", [P.proj("H", "S", "ABC")])
show("proj A->(SBC)", [P.proj("K", "A", "SBC")])
show("proj B->(SAC)", [P.proj("K", "B", "SAC")])
show("proj C->(SAB)", [P.proj("K", "C", "SAB")])
