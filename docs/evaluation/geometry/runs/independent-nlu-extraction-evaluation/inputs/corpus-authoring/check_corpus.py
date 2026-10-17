# Structural validator for corpus.json (stdlib only).
import sys; sys.stdout.reconfigure(encoding="utf-8")
import json, os
from collections import Counter
from difflib import SequenceMatcher

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "corpus.json"), encoding="utf-8"))
cases = D["cases"]
errs = []
def need(ok, msg):
    if not ok:
        errs.append(msg)

need(D["schema"] == "NLU_EVAL_CORPUS/1", "schema")
ids = [c["id"] for c in cases]
need(len(ids) == len(set(ids)), "duplicate ids")
split = {s: [c for c in cases if c["split"] == s] for s in ("dev", "locked")}
need(len(split["dev"]) == 16 and len(split["locked"]) == 44, "split sizes")
need(sorted(c["id"] for c in split["dev"]) == [f"D{i:02d}" for i in range(1, 17)], "dev ids")
need(sorted(c["id"] for c in split["locked"]) == [f"L{i:02d}" for i in range(1, 45)], "locked ids")

INTENTS = {"compute_value", "construct", "prove", "interaction", "explain", "define"}
QTY = {"distance_point_line", "distance_point_segment", "distance_point_plane", "distance_line_line", "length",
       "length_squared", "angle_line_plane", "angle_line_line", "angle_plane_plane", "cos_squared_angle", "area",
       "volume", "intersection_line", "section", "projection", "other"}
DISP = {"answer_all", "refuse_contradictory", "refuse_missing_info", "refuse_nonexistent_object", "refuse_ambiguous",
        "clarification_required", "out_of_scope_request", "answer_supported_part_and_flag_rest"}
n_quotes = 0
for c in cases:
    cid, txt = c["id"], c["source_text"]
    need(c["group"] in "ABCDEF" and len(c["group"]) == 1, f"{cid} group")
    need(c["gold_disposition"] in DISP, f"{cid} disposition")
    need((c["context"] is None) or c["group"] == "E", f"{cid} context only for group E")
    for p in c["premises"]:
        where = p.get("quote_in", "source_text")
        hay = txt if where == "source_text" else c["context"]["prior_turn"] if where == "context.prior_turn" else None
        need(hay is not None and p["quote"] in hay, f"{cid} premise quote not found in {where}: {p['quote']!r}")
        n_quotes += 1
    rids = [r["rid"] for r in c["requests"]]
    need(len(rids) == len(set(rids)), f"{cid} dup rid")
    for r in c["requests"]:
        need(r["quote"] in txt, f"{cid} request quote not in source_text: {r['quote']!r}")
        need(r["intent"] in INTENTS and r["quantity"] in QTY, f"{cid} {r['rid']} intent/quantity")
        need(set(r.get("depends_on", [])) <= set(rids), f"{cid} depends_on")
        n_quotes += 1
    need(c["n_source_requests"] == len(c["requests"]) or "unanswerable" in c["notes"], f"{cid} n_source_requests")
    need(set(c["expected_values"]) <= set(rids), f"{cid} expected rid unknown")
    for rid, e in c["expected_values"].items():
        need(e.get("computed_by") == "agent1_oracle.py", f"{cid} computed_by")
    need(not c["expected_values"] or c["gold_disposition"] in ("answer_all", "answer_supported_part_and_flag_rest"),
         f"{cid} numeric values on a refusal case")

for s, cs in split.items():
    g = Counter(c["group"] for c in cs)
    need(all(g[x] >= (2 if s == "dev" else 5) for x in "ABCDEF"), f"{s} group coverage {dict(g)}")
need(len({c["structure_id"] for c in split["locked"]}) >= 22, "locked distinct structure_ids < 22")
need(not ({c["structure_id"] for c in split["dev"]} & {c["structure_id"] for c in split["locked"]}), "structure_id overlap")
multi_locked = sum(len(c["requests"]) > 1 for c in split["locked"])
need(multi_locked >= 10, "locked multi-request < 10")
# same structure_id => same figure+question: requests must agree on (intent, quantity)
by_sid = {}
for c in cases:
    by_sid.setdefault(c["structure_id"], set()).add(tuple((r["intent"], r["quantity"]) for r in c["requests"]))
need(all(len(v) == 1 for v in by_sid.values()), "structure_id groups disagree on intent/quantity")
# near-duplicate wording across splits
worst = max(((SequenceMatcher(None, a["source_text"], b["source_text"]).ratio(), a["id"], b["id"])
             for a in split["dev"] for b in split["locked"]))
need(worst[0] < 0.85, f"near-identical dev/locked wording {worst}")

for s, cs in split.items():
    print(f"{s}: {len(cs)} cases, groups {dict(sorted(Counter(c['group'] for c in cs).items()))}, "
          f"structure_ids {len({c['structure_id'] for c in cs})}, multi-request {sum(len(c['requests']) > 1 for c in cs)}, "
          f"with numeric values {sum(bool(c['expected_values']) for c in cs)} "
          f"({sum(len(c['expected_values']) for c in cs)} values), "
          f"dispositions {dict(Counter(c['gold_disposition'] for c in cs))}")
print(f"quotes verified: {n_quotes}; max dev/locked similarity {worst[0]:.3f} ({worst[1]} vs {worst[2]})")
if errs:
    print("CHECK FAIL:\n  " + "\n  ".join(errs))
    raise SystemExit(1)
print("CHECK PASS")
