import json, sys
ids = ["C05", "C07", "C10", "R06", "P08", "S02", "Q01b", "L06"]
rows = {}
for l in open(sys.argv[1], encoding="utf-8"):
    b = json.loads(l)
    if b["source"].endswith("holdout-6/ACCEPTANCE_MANIFEST.json") and b["case_id"] in ids:
        rows[b["case_id"]] = b["body"]


def short(x, n=700):
    return json.dumps(x, ensure_ascii=False)[:n]


for cid in ids:
    body = rows[cid]
    rd = body.get("route_d") or {}
    env = rd.get("slm_grounding_envelope") or {}
    print("=" * 20, cid, rd.get("status"), rd.get("extraction_mode"))
    print(" refusal:", short(rd.get("refusal"), 900))
    print(" grounding:", env.get("grounding_status"), "| rejected_ops:", short(env.get("rejected_ops"), 600))
    print(" unresolved:", short(env.get("unresolved") or env.get("slm_unresolved"), 400))
    print(" accepted_ops:", short(env.get("accepted_ops"), 400))
    print(" env keys:", sorted(env.keys())[:40])
    print(" rd keys:", sorted(rd.keys()))
    print(" top:", short({k: body.get(k) for k in ("reason_code", "failure_category", "status", "error")}, 300))
