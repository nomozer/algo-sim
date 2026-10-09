"""Run from backend/: python <path>/summarize_unnamed_gap.py <probe_c1_equivalence log> — for the `unnamed_everywhere`
variant (no solid notation in givens or question ⇒ outside the route's polyhedron refusal zone), compare every served
outcome with the corpus label of the canonical row. Prints JSON."""
import json, os, sys
sys.path.insert(0, os.getcwd())
from tests.geometry import test_regular_square_pyramid as SQ, test_regular_triangular_pyramid as TR
mods = {"square": SQ, "triangular": TR}
out = {"served_matching_label": [], "served_other_value": [], "served_label_refused": [], "refused": []}
for line in open(sys.argv[1], encoding="utf-8"):
    r = json.loads(line)
    if r["variant"] != "unnamed_everywhere":
        continue
    lab = mods[r["corpus"]].NHAN[r["row"]]["expect"]
    key = f"{r['corpus']}/{r['row']}"
    if not r["outcome"].startswith("served"):
        out["refused"].append(key); continue
    v = r["outcome"].split(":", 1)[1]
    k = ("served_matching_label" if lab == f"served:{v}" else "served_other_value" if lab.startswith("served:")
         else "served_label_refused")
    out[k].append({"row": key, "label": lab, "served": v} if k != "served_matching_label" else key)
print(json.dumps({k: (len(v), v) for k, v in out.items()}, ensure_ascii=False, indent=1))
