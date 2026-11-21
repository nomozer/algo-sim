"""Deterministic-layer diagnosis (0 model calls): parser status on original text and on the v3-normalized text."""
import json, sys, os
sys.path.insert(0, os.getcwd())
from app.ai.local_geometry_parser import parse_geometry_problem_locally
from app.ai.slm_verified_normalizer import normalize_for_slm_grounding

R = sys.argv[1]
ids = set(sys.argv[2].split(",")) if len(sys.argv) > 2 and sys.argv[2] else None
r = json.load(open(f"{R}/LIVE_TEXT_ACCEPTANCE_RESULTS.json", encoding="utf-8"))
m = json.load(open(f"{R}/holdout-6/ACCEPTANCE_MANIFEST.json", encoding="utf-8"))
txt = {c["case_id"]: c["original_input"] for c in m["valid_cases"] + m["negative_cases"]}
out = []
for c in r["cases"]:
    if ids is not None and c["case_id"] not in ids:
        continue
    if ids is None and c["candidate_stratum"] != "SLM_REQUIRED":
        continue
    t = txt[c["case_id"]]
    p = parse_geometry_problem_locally(t, use_cache=False)
    v3 = normalize_for_slm_grounding(t, normalizer_version="v3")
    p3 = parse_geometry_problem_locally(v3.canonical_text, use_cache=False) if v3.changed else None
    cov = p.source_coverage
    row = {
        "case_id": c["case_id"], "live_status": c["route_status"], "live_reason": c["reason_code"],
        "parse_status": p.status, "parse_reason": p.reason_code,
        "unparsed_facts": list(cov.unparsed_fact_candidates), "unparsed_goals": list(cov.unparsed_goal_candidates),
        "unresolved_refs": list(cov.unresolved_references),
        "v3_changed": v3.changed, "v3_rules": [s.rule_id for s in v3.steps] if v3.changed else [],
        "v3_text": v3.canonical_text if v3.changed else None,
        "v3_parse_status": p3.status if p3 else None, "v3_parse_reason": p3.reason_code if p3 else None,
        "v3_unparsed_facts": list(p3.source_coverage.unparsed_fact_candidates) if p3 else None,
        "v3_unparsed_goals": list(p3.source_coverage.unparsed_goal_candidates) if p3 else None,
    }
    out.append(row)
    print(json.dumps(row, ensure_ascii=False))
if len(sys.argv) > 3:
    open(sys.argv[3], "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
