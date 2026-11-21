"""Aggregates the raw evidence of the /11 blind live run into the result JSONs (no measurement happens here).

Scoring rules are the pre-registered ones (V11_ACCEPTANCE_CRITERIA_PREREGISTERED.json); the per-case logic is the /10
aggregator's (tools/aggregate_results.py, copied) plus the SLM_REQUIRED stratum and the D (underdetermined) report.
usage (from the run directory): python tools/aggregate_v11.py
"""

import csv
import json
import math
from pathlib import Path

EV = Path("evidence")
rd = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
jl = lambda p: [json.loads(l) for l in Path(p).read_text(encoding="utf-8-sig").splitlines() if l.strip()]
wr = lambda p, o: Path(p).write_text(json.dumps(o, ensure_ascii=False, indent=1), encoding="utf-8")
man = rd("V11_LIVE_ACCEPTANCE_MANIFEST.json")
frz = {r["case_id"]: r for r in rd("V11_LIVE_ACCEPTANCE_FREEZE.json")["rows"]}
CASES = {c["case_id"]: c for c in man["valid_cases"] + man["negative_cases"]}
recs = {r["case_id"]: r for r in jl(EV / "browser" / "browser_records_v11.jsonl")}
val = {r["case_id"]: r for r in rd(EV / "scene_validation_v11.json")["results"]}
ui = {r["scenario_id"]: r for f in ("main", "post_u08_fix", "pre_u08_fix_rerun", "i06_suspended_llama", "i06_suspended_llama_run2")
      if (EV / "ui" / f"ui_scenarios_{f}.json").exists() for r in [dict(x, file=f) for x in rd(EV / "ui" / f"ui_scenarios_{f}.json")["results"]]
      if not (r["scenario_id"] in ("I04", "I07", "I06") and f == "main")}


def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 4), round(c + h, 4)]


rate = lambda k, n: {"k": k, "n": n, "rate": round(k / n, 4) if n else None, "wilson95": wilson(k, n)}


def pct(xs, q):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    i = (len(xs) - 1) * q; lo = math.floor(i)
    return round(xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (i - lo), 1)


dist = lambda xs: {"n": len([x for x in xs if x is not None]), "p50": pct(xs, .5), "p95": pct(xs, .95), "max": max([x for x in xs if x is not None], default=None)}

rows = []
for cid, c in CASES.items():
    r, v = recs.get(cid, {}), val.get(cid, {})
    served = r.get("route_status") == "SERVED" and r.get("surface") == "SCENE"
    lab = r.get("labels") or {}
    visual = served and (r.get("canvas_pixels") or {}).get("ink_fraction", 0) >= 0.01 and not lab.get("gold_missing") \
        and not lab.get("outside_canvas") and not r.get("console_errors")
    inter = {"orbit": bool((r.get("orbit") or {}).get("frame_changed")) and (r.get("orbit") or {}).get("label_ids_stable", False),
             "zoom": bool((r.get("zoom") or {}).get("frame_changed")),
             "step": bool((r.get("step") or {}).get("after_prev")) and (r.get("step") or {}).get("after_next") == (r.get("step") or {}).get("initial"),
             "no_reanalysis": r.get("analyze_calls_during_interaction") == 0} if served else None
    num = (v.get("numeric") or {}).get("status")
    math_ok = v.get("scene_validation") == "MATHEMATICALLY_VALID" and num in (None, "CORRECT")
    intent = c["simulation_intent"]
    if intent == "NEGATIVE":
        verdict = "SAFE_REFUSAL" if not served else ("SERVED_CORRECT" if math_ok else "UNSAFE_SERVE")
    elif served:
        verdict = "COMPLETE" if math_ok and visual and all(inter.values()) else ("MATH_OK_VISUAL_OR_INTERACTION_FAIL" if math_ok else "MATHEMATICALLY_INVALID")
    else:
        verdict = "INFRASTRUCTURE_FAILURE" if r.get("http") in (502, 503, 504) or r.get("harness_error") else "REFUSED_VALID_INPUT"
    rows.append({"case_id": cid, "intent": intent, "stratum": frz.get(cid, {}).get("stratum", "NEGATIVE"), "family": c["geometric_family"],
                 "http": r.get("http"), "route_status": r.get("route_status"), "extraction_mode": r.get("extraction_mode"),
                 "refusal_code": r.get("refusal_code"), "ux_state": r.get("ux_state"), "scene_validation": v.get("scene_validation"),
                 "relations_checked": len(v.get("relations") or []), "numeric": num, "visual_ok": visual if served else None, "interaction": inter,
                 "backend_total_ms": r.get("backend_total_ms"), "http_round_trip_ms": r.get("http_round_trip_ms"),
                 "first_visible_scene_ms": r.get("first_visible_scene_ms"), "first_interactive_frame_ms": r.get("first_interactive_frame_ms"),
                 "console_errors": r.get("console_errors"), "external_requests": r.get("external_requests"),
                 "ui_token_leak": r.get("ui_token_leak"), "cloud_key_text": r.get("cloud_key_text"), "screenshot": r.get("screenshot"),
                 "response_sha256": r.get("response_sha256"), "verdict": verdict})

ins = [r for r in rows if r["stratum"] in ("PARSER_COMPLETE", "SLM_REQUIRED")]
neg = [r for r in rows if r["intent"] == "NEGATIVE"]
und = [r for r in rows if r["stratum"] == "SEPARATE"]
served = [r for r in ins if r["route_status"] == "SERVED"]
slm = [r for r in ins if r["stratum"] == "SLM_REQUIRED"]
slm_scene = [r for r in slm if r["verdict"] == "COMPLETE" and (r["extraction_mode"] or "").startswith("LOCAL_SLM")]
ops = [ok for r in served for ok in (r["interaction"] or {}).values()]
resp = {json.loads(l)["case_id"]: json.loads(l)["body"] for l in (EV / "browser" / "responses_v11.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
# a fabricated metric goal on a simulate-only source would surface as a served answer
fabricated = [r["case_id"] for r in served if r["intent"] == "SIMULATE_ONLY" and (resp[r["case_id"]].get("route_d") or {}).get("answers")]
rates = {
    "SIMULATION_COMPLETION_RATE_in_scope": rate(sum(r["verdict"] == "COMPLETE" for r in ins), len(ins)),
    "served_in_scope": rate(len(served), len(ins)),
    "completion_by_stratum": {s: rate(sum(r["verdict"] == "COMPLETE" for r in ins if r["stratum"] == s), sum(r["stratum"] == s for r in ins)) for s in ("PARSER_COMPLETE", "SLM_REQUIRED")},
    "completion_by_intent": {k: rate(sum(r["verdict"] == "COMPLETE" for r in ins if r["intent"] == k), sum(r["intent"] == k for r in ins)) for k in ("SIMULATE_ONLY", "SIMULATE_AND_QUERY", "QUERY_WITH_SCENE")},
    "SLM_VERIFIED_SCENE_RATE": rate(len(slm_scene), len(slm)),
    "geometry_correctness_of_served": rate(sum(r["scene_validation"] == "MATHEMATICALLY_VALID" for r in served), len(served)),
    "numeric_answers_correct": rate(sum(r["numeric"] == "CORRECT" for r in served if r["numeric"]), sum(bool(r["numeric"]) for r in served)),
    "visual_ok_of_served": rate(sum(bool(r["visual_ok"]) for r in served), len(served)),
    "interaction_ops": rate(sum(ops), len(ops)),
    "safe_refusal_negatives": rate(sum(r["verdict"] in ("SAFE_REFUSAL", "SERVED_CORRECT") for r in neg), len(neg)),
    "safety": {"wrong_served_scenes": sum(r["verdict"] in ("MATHEMATICALLY_INVALID", "UNSAFE_SERVE") for r in rows),
               "served_numeric_mismatch": sum(r["numeric"] not in (None, "CORRECT") for r in rows if r["route_status"] == "SERVED"),
               "fabricated_math_goal_on_simulate_only": fabricated,
               "external_requests_browser": sum(len(r["external_requests"] or []) for r in rows),
               "ui_token_leaks": sum(bool(r["ui_token_leak"]) for r in rows), "cloud_key_text": sum(bool(r["cloud_key_text"]) for r in rows)},
    "infrastructure_failures": sum(r["verdict"] == "INFRASTRUCTURE_FAILURE" for r in rows),
    "verdicts": {v: sum(r["verdict"] == v for r in rows) for v in sorted({r["verdict"] for r in rows})},
}
crit = rd("V11_ACCEPTANCE_CRITERIA_PREREGISTERED.json")
c_rate, s = rates["SIMULATION_COMPLETION_RATE_in_scope"]["rate"], rates["SLM_VERIFIED_SCENE_RATE"]
gates = {"primary_completion_ge_0.85": c_rate >= 0.85, "slm_rate_ge_0.30_and_ge_5": s["rate"] >= 0.30 and s["k"] >= 5,
         "safety_zero_tolerance": rates["safety"]["wrong_served_scenes"] == 0 and rates["safety"]["served_numeric_mismatch"] == 0
         and not fabricated and rates["safety"]["external_requests_browser"] == 0,
         "interaction_absolute": rates["interaction_ops"]["k"] == rates["interaction_ops"]["n"],
         "safe_refusal_1.0": rates["safe_refusal_negatives"]["rate"] == 1.0}
wr("V11_LIVE_ACCEPTANCE_RESULTS.json", {"schema": "axo-v11-live-acceptance-results/1", "blind": True,
    "freeze": rd("V11_LIVE_ACCEPTANCE_FREEZE.json")["code"], "criteria_sha256": rd("V11_LIVE_ACCEPTANCE_FREEZE.json")["inputs"]["criteria_sha256"],
    "rates": rates, "gates": gates, "cases": rows})
wr("V11_SLM_REQUIRED_EVALUATION.json", {"schema": "axo-v11-slm-stratum/1", "rule": crit["slm_recovery"], "result": s,
    "slm_provenance_scenes": [r["case_id"] for r in slm_scene], "rows": [r for r in rows if r["stratum"] == "SLM_REQUIRED"],
    "post_hoc_audit": "evidence/slm_stratum/v11_slm_stratum_audit.json", "post_hoc_first_failing_layer": rd(EV / "slm_stratum" / "v11_slm_stratum_audit.json")["first_failing_layer"],
    "post_hoc_split_rephrase_served_valid": rd(EV / "slm_stratum" / "v11_slm_stratum_audit.json")["split_served_valid"]})
wr("V11_UNDERDETERMINED_RESULTS.json", {"schema": "axo-v11-underdetermined/1", "rule": crit["underdetermined"], "rows": und,
    "learner_text": next((r.get("learner_text_by_case") for r in ui.values() if r["scenario_id"] == "I05"), None)})
v = rd(EV / "scene_validation_v11.json")
wr("V11_MATHEMATICAL_SCENE_VALIDATION.json", {"schema": "axo-v11-scene-validation/1", "validator": v["validator"], "source": "evidence/scene_validation_v11.json",
    "counts": {k: sum(r.get("scene_validation") == k for r in v["results"]) for k in ("MATHEMATICALLY_VALID", "MATHEMATICALLY_INVALID", "VALIDATION_ERROR", "NOT_SERVED")},
    "relations_checked_total": sum(len(r.get("relations") or []) for r in v["results"]),
    "relations_violated_total": sum(not x.get("holds") for r in v["results"] for x in (r.get("relations") or [])),
    "results": v["results"]})
wr("V11_UI_SCENARIO_RESULTS.json", {"schema": "axo-v11-ui-scenarios/1", "files": sorted({r["file"] for r in ui.values()}), "results": list(ui.values())})

det = [r for r in rows if r["extraction_mode"] in ("LOCAL_DETERMINISTIC_PARSER", "LOCAL_PARSER_AFTER_V3_NORMALIZER")]
slm_path = [r for r in rows if (r["extraction_mode"] or "").startswith("LOCAL_SLM")]
mem = list(csv.reader(open(EV / "memory" / "stack_memory_v11.csv", encoding="utf-8-sig")))
grp = {}
for t, g, n, ws, pv, cpu in mem:
    grp.setdefault(g, []).append((float(ws), float(pv), int(n)))
tot = {}
for t, g, n, ws, pv, cpu in mem:
    tot[t] = tot.get(t, 0) + float(ws)
wr("V11_FULL_STACK_PERFORMANCE.json", {"schema": "axo-v11-performance/1", "host": "this Windows 11 dev host only (no target-hardware claim)",
    "fast_path_backend_ms": dist([r["backend_total_ms"] for r in det]), "slm_path_backend_ms": dist([r["backend_total_ms"] for r in slm_path]),
    "fast_path_round_trip_ms": dist([r["http_round_trip_ms"] for r in det]), "slm_path_round_trip_ms": dist([r["http_round_trip_ms"] for r in slm_path]),
    "served_first_visible_scene_ms": dist([r["first_visible_scene_ms"] for r in rows if r["route_status"] == "SERVED"]),
    "served_first_interactive_frame_ms": dist([r["first_interactive_frame_ms"] for r in rows if r["route_status"] == "SERVED"]),
    "memory_mb": {g: {"ws_max": max(x[0] for x in v), "ws_p95": pct([x[0] for x in v], .95), "private_max": max(x[1] for x in v), "samples": len(v)} for g, v in grp.items()},
    "stack_ws_total_max_mb": round(max(tot.values()), 1)})

tcp = jl(EV / "network" / "tcp_sampler_v11.jsonl"); hb = [r for r in tcp if r.get("heartbeat")]
wr("V11_NETWORK_ISOLATION_RESULTS.json", {"schema": "axo-v11-network/1",
    "egress_proxy": {"log": "evidence/network/egress_proxy_v11.jsonl", "records": len(jl(EV / "network" / "egress_proxy_v11.jsonl")) if (EV / "network" / "egress_proxy_v11.jsonl").exists() else 0,
                     "log_created": (EV / "network" / "egress_proxy_v11.jsonl").exists(),
                     "selfcheck_records": len(jl(EV / "network" / "egress_proxy_v11_selfcheck.jsonl"))},
    "tcp_sampler": {"heartbeats": len(hb), "span_s": round((hb[-1]["t"] - hb[0]["t"]) / 1000, 1), "non_loopback_records": sum("remote" in r for r in tcp)},
    "browser_external_requests": rates["safety"]["external_requests_browser"],
    "provider_calls_nonzero": sum(1 for r in recs.values() if (r.get("provider_calls") or 0) not in (0, None)),
    "backend_env": "GEMINI_API_KEY unset; HYBRID_ROUTE_MODE=local-only-scoped; HTTP(S)_PROXY/ALL_PROXY -> blackhole; /api/health hasKey=false"})
print(json.dumps({"rates": {k: v for k, v in rates.items() if k != "verdicts"}, "gates": gates}, ensure_ascii=False, indent=1)[:3500])
