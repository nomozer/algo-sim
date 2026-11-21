"""Derives the per-topic JSON deliverables from LIVE_SIMULATION_ACCEPTANCE_RESULTS.json + raw evidence (no new measurement).
usage: python derive_reports.py   (from the run directory)
"""

import json
from collections import defaultdict
from pathlib import Path

R = json.loads(Path("LIVE_SIMULATION_ACCEPTANCE_RESULTS.json").read_text(encoding="utf-8"))
P2 = {r["case_id"]: r for r in R["cases"]["pass2"]}
P1 = {r["case_id"]: r for r in R["cases"]["pass1"]}
man = json.loads(Path("LIVE_SIMULATION_ACCEPTANCE_MANIFEST.json").read_text(encoding="utf-8"))
UI = {x["scenario_id"]: x for x in json.loads(Path("evidence/ui4/ui_scenarios.json").read_text(encoding="utf-8"))["results"]}
jl = lambda p: [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]
dump = lambda name, obj: Path(name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
NOTE = "derived from LIVE_SIMULATION_ACCEPTANCE_RESULTS.json (pass2 = candidate a0f979392 unless stated)"

# capability matrix: family x intent, served / tried, plus the dominant refusal codes
cap = defaultdict(lambda: {"tried": 0, "served": 0, "refusal_codes": defaultdict(int), "cases": []})
for c in man["valid_cases"]:
    r = P2[c["case_id"]]; k = f'{c["geometric_family"]}|{c["simulation_intent"]}'
    cap[k]["tried"] += 1; cap[k]["served"] += r["route_status"] == "SERVED"; cap[k]["cases"].append(c["case_id"])
    if r["route_status"] != "SERVED": cap[k]["refusal_codes"][str(r["refusal_code"])] += 1
dump("PRODUCT_SCENE3D_CAPABILITY_MATRIX.json", {
    "schema": "axo-product-scene3d-capability-matrix/1", "note": NOTE, "level": "LIVE_PRODUCT (browser, local-only-scoped)",
    "matrix": [{"family": k.split("|")[0], "intent": k.split("|")[1], "served": v["served"], "tried": v["tried"],
                "refusal_codes": dict(v["refusal_codes"]), "cases": v["cases"]} for k, v in sorted(cap.items())],
    "out_of_scope_confirmed_refused": ["sphere", "cone", "cylinder", "Oxyz analytic", "planar-only triangle", "calculus", "programming"],
    "interactions_in_product": ["orbit", "zoom", "reset view", "step prev/next/play", "x-ray", "layer toggles incl. labels",
                                "entity selection", "fullscreen"],
    "not_in_product": ["DYNAMIC_CONSTRUCTION_STEPS (Construction /2)", "ILLUSTRATIVE scene for simulate-only inputs without dimensions",
                       "image/photo input in local-only (LOCAL_ONLY_CLOUD_VISION_DISABLED)"]})

# simulation-only input evaluation
rows = []
for c in man["valid_cases"] + man["negative_cases"]:
    r2, r1 = P2[c["case_id"]], P1[c["case_id"]]
    rows.append({"case_id": c["case_id"], "intent": c["simulation_intent"], "determinacy": c["geometry_determinacy"],
                 "input": c["original_input"], "pass2": {k: r2[k] for k in ("route_status", "extraction_mode", "refusal_code", "verdict")},
                 "pass1": {k: r1[k] for k in ("route_status", "extraction_mode", "refusal_code", "verdict")},
                 "numeric_required": bool(c["metric_oracle"]), "numeric_served": (r2["numeric"] or {}).get("served")})
dump("SIMULATION_ONLY_INPUT_EVALUATION.json", {
    "schema": "axo-simulation-intent-evaluation/1", "note": NOTE,
    "completion_by_intent_pass2": R["passes"]["pass2"]["rates"]["completion_by_intent"],
    "completion_by_intent_pass1": R["passes"]["pass1"]["rates"]["completion_by_intent"],
    "simulate_only_served_without_numeric_goal": sum(1 for x in rows if x["intent"] == "SIMULATE_ONLY" and x["pass2"]["route_status"] == "SERVED" and not x["numeric_served"]),
    "fabricated_numeric_goal_on_simulate_only": sum(1 for x in rows if x["intent"] == "SIMULATE_ONLY" and x["numeric_served"]),
    "underdetermined_handling": [x for x in rows if x["determinacy"] in ("ILLUSTRATIVE_GEOMETRY", "INSUFFICIENT_FOR_REQUESTED_MEASUREMENT", "CONTRADICTORY_GEOMETRY")],
    "cases": rows})

# mathematical validation (oracle v2 on both passes; v1 kept)
v2 = json.loads(Path("evidence/scene_validation_pass2.json").read_text(encoding="utf-8"))
v1p = json.loads(Path("evidence/scene_validation_pass1_oracle_v2.json").read_text(encoding="utf-8"))
v1o = json.loads(Path("evidence/scene_validation_acceptance.json").read_text(encoding="utf-8"))
cnt = lambda res: {k: sum(r.get("scene_validation") == k for r in res) for k in ("MATHEMATICALLY_VALID", "MATHEMATICALLY_INVALID", "VALIDATION_ERROR", "NOT_SERVED")}
dump("SCENE3D_MATHEMATICAL_VALIDATION.json", {
    "schema": "axo-scene3d-mathematical-validation-summary/1", "validator": "tools/scene_oracle.py (independent; exact Fraction under chart_metric)",
    "oracle_v1_frozen_output_pass1": {"file": "evidence/scene_validation_acceptance.json", "counts": cnt(v1o["results"]),
        "flags_explained": "13 flags, all evaluator limitations verified by hand: cos²=v angle format (4), base-centre O treated as fabricated (6, O proven centroid with apex⊥base), tetrahedron edges drawn from solid without segment3 objects (5; overlaps)"},
    "oracle_v2_amendments": ["A1 parse cos²/sin²/tan answers as angles", "A2 free point equal to a solid face centroid = layout centre (finding, not fabrication)",
                             "A3 only solid + point3 object types are required"],
    "pass1_oracle_v2": cnt(v1p["results"]), "pass2_oracle_v2": cnt(v2["results"]),
    "relations_checked_pass2": sum(len(r.get("relations") or []) for r in v2["results"]),
    "relations_violated_pass2": sum(1 for r in v2["results"] for x in (r.get("relations") or []) if x["holds"] is False),
    "numeric_pass2": {s: sum((r.get("numeric") or {}).get("status") == s for r in v2["results"] if r.get("route_status") == "SERVED") for s in ("CORRECT", "MISMATCH", "UNPARSED")},
    "findings_pass2": sorted({f for r in v2["results"] for f in r.get("findings") or []}),
    "cases_with_findings_pass2": [r["case_id"] for r in v2["results"] if r.get("findings")],
    "results_pass2": v2["results"]})

# interaction results
inter = [{"case_id": cid, **(r["interaction"] or {}), "labels_shown": (r["labels"] or {}).get("shown")} for cid, r in P2.items() if r["interaction"]]
dump("SCENE3D_INTERACTION_TEST_RESULTS.json", {
    "schema": "axo-scene3d-interaction-results/1", "note": NOTE,
    "per_served_scene_pass2": {"ops": R["passes"]["pass2"]["rates"]["interaction_success_rate"], "failures": [x for x in inter if not all(v for k, v in x.items() if k not in ("case_id", "labels_shown"))], "cases": inter},
    "ui_scenarios": UI, "ui_scenarios_source": "evidence/ui4/ui_scenarios.json (earlier attempts ui/, ui2/, ui3/ kept: selector and measurement fixes, see BROWSER_RENDER_VERIFICATION_REPORT.md)",
    "dynamic_construction_steps": "NOT_IN_PRODUCT"})

# smoke = representative subset of the live runs (declared derived; no separate smoke execution)
smoke_map = {"tri_pyramid": "V01", "quad_pyramid": "V02", "square_base": "V15", "rect_base": "V03", "tetrahedron": "V07", "prism": "V21",
             "cuboid": "V09", "cube": "V25", "perpendicular": "V20", "parallel": "V16", "simulate_only": "V15", "simulate_and_query": "Q01",
             "missing_dimension": "N01", "contradictory": "N03", "out_of_scope": "N06", "natural_phrasing": "V15", "long_problem": "V16"}
smoke = [{"scope": k, "case_id": v, "verdict": P2[v]["verdict"], "refusal_code": P2[v]["refusal_code"]} for k, v in smoke_map.items()]
smoke += [{"scope": "runtime_model_not_loaded", "source": "evidence/runtime/u11_model_not_provisioned.jsonl + browser_records_u11.jsonl", "verdict": "PASS"},
          {"scope": "runtime_timeout", "source": "pass 1 observed 504 LOCAL_SLM_TIMEOUT (9 cases); UI kept loading through client retries", "verdict": "OBSERVED_NOT_INJECTED"},
          {"scope": "two_consecutive_inputs", "source": "U02", "verdict": "PASS" if UI["U02"]["pass"] else "FAIL"}]
dump("LIVE_SMOKE_TEST_RESULTS.json", {"schema": "axo-live-smoke/1", "derived_from": "pass2 browser run + runtime/UI scenarios", "results": smoke})

# performance
perf = {"schema": "axo-e2e-simulation-performance/1", "host": "Windows 11 Pro dev host, 15.78 GiB RAM, CPU only (llama.cpp b12470, 6 threads)",
        "browser": json.loads(Path("evidence/browser/browser_env_pass2.json").read_text(encoding="utf-8")),
        "definitions": {"backend_total_ms": "route_d.adaptive_telemetry.total_ms (server side)",
                        "http_round_trip_ms": "click on Dựng hình → responseEnd of POST /api/analyze (Resource Timing, page clock)",
                        "first_visible_scene_ms": "click → first WebGL draw call after the response arrived",
                        "first_interactive_frame_ms": "click → first WebGL draw after a pointer drag started as soon as the canvas was visible (includes ~0.5 s of harness waits)"},
        "pass2": R["passes"]["pass2"]["performance"], "pass1_with_keepalive_bug": R["passes"]["pass1"]["performance"],
        "cold_start": "pass2 V01 (first request after backend start): backend 875 ms, first visible 1455 ms; llama-server cold load measured in U14 restart ≈ 6.2 s total request",
        "target_reference": "p95 ≤ 5000 ms first visible scene: met for served scenes on this host (p95 455.6 ms, all deterministic route); SLM route round trip p95 8425 ms (no SLM scene was served)",
        "physical_target_hardware_4_8_gib": "NOT_MEASURED"}
dump("END_TO_END_SIMULATION_PERFORMANCE.json", perf)
print("ok")
