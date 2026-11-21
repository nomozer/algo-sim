"""Ablation of the /11 simulation-only GBNF variant on the /10 regression set (64 valid cases, exposed — not a holdout).

Real AxoV9 via the product runtime, SLM extraction called directly (no parser routing), lowered payload through the real
downstream (Source Gate → planner → engine → adapter), oracle-checked.
  U  SIM_ONLY_UNRESOLVED_WITHOUT_FACTS = False   (unresolved allowed next to facts)
  S  SIM_ONLY_UNRESOLVED_WITHOUT_FACTS = True    (unresolved only with r:[])
Caveat recorded per row: when the deterministic parser has a payload, lowering reconciles premises with it, so a served
SLM payload is "SLM_PURE" only when `parser_has_payload` is false.
usage (from backend/): python <this> <out.json>
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, ".")
RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "tools"))
import scene_oracle as so  # noqa: E402

import app.ai.local_slm_extractor as X  # noqa: E402
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.local_geometry_parser import parse_geometry_problem_locally  # noqa: E402
from app.ai.typed_fact_next_extraction import ReplayExtractor  # noqa: E402

POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
man = json.loads((RUN.parent / "axo-hybrid-local-only-3d-simulation-live-acceptance-cutover" / "LIVE_SIMULATION_ACCEPTANCE_MANIFEST.json").read_text(encoding="utf-8"))
rows = []
for variant, flag in (("U", False), ("S", True)):
    X.SIM_ONLY_UNRESOLVED_WITHOUT_FACTS = flag
    for c in man["valid_cases"]:
        t0 = time.perf_counter()
        r = X.run_local_slm_extraction(c["original_input"], model_key="v9", closure_mode=X.V9_CLOSURE_MODE, normalizer_version="v3", use_cache=False)
        row = {"variant": variant, "case_id": c["case_id"], "intent": c["simulation_intent"],
               "parser_has_payload": parse_geometry_problem_locally(c["original_input"], use_cache=False).payload is not None,
               "slm_ok": r.ok, "grounding": (r.grounding_envelope or {}).get("grounding_status"), "raw": r.inference.raw_content if r.inference else None}
        if r.canonical_payload:
            h = run_hybrid_offline(r.norm_text, ReplayExtractor({r.norm_text: r.canonical_payload}), policy=POLICY, timeout_seconds=30)
            rd = h.response.get("route_d") or {}
            row["downstream"] = rd.get("status")
            row["code"] = (rd.get("refusal") or {}).get("code")
            if rd.get("status") == "SERVED":
                v = so.validate(c, h.response)
                row["oracle"] = v.get("scene_validation"); row["numeric"] = (v.get("numeric") or {}).get("status")
        row["seconds"] = round(time.perf_counter() - t0, 1)
        rows.append(row)
        print(variant, c["case_id"], row["slm_ok"], row["grounding"], row.get("downstream"), row.get("oracle"), row.get("numeric"), flush=True)


def summary(v):
    rs = [r for r in rows if r["variant"] == v]
    pure = [r for r in rs if not r["parser_has_payload"]]
    ok = lambda xs: sum(r.get("downstream") == "SERVED" and r.get("oracle") == "MATHEMATICALLY_VALID" and r.get("numeric") in (None, "CORRECT") for r in xs)
    wrong = sum(r.get("downstream") == "SERVED" and (r.get("oracle") != "MATHEMATICALLY_VALID" or r.get("numeric") not in (None, "CORRECT")) for r in rs)
    return {"cases": len(rs), "slm_ok": sum(r["slm_ok"] for r in rs), "served_valid": ok(rs), "wrong_served": wrong,
            "slm_pure_cases": len(pure), "slm_pure_served_valid": ok(pure),
            "simulate_only_served_valid": ok([r for r in rs if r["intent"] == "SIMULATE_ONLY"]),
            "unresolved_with_facts": sum(bool(r["raw"]) and '"u":[{' in r["raw"] and '"r":[{' in r["raw"] for r in rs)}


out = {"schema": "axo-slm-grammar-ablation/1", "set": "/10 valid cases (64, exposed regression set)", "model": "qwen3-0.6b-axo-v9-q4_k_m",
       "summary": {v: summary(v) for v in ("U", "S")}, "rows": rows}
Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out["summary"], indent=1))
