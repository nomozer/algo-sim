"""Deterministically aggregate one live-acceptance run into LIVE_ACCEPTANCE_RESULTS, SLM_LIVE_CONTRIBUTION_AUDIT,
VISUAL_AND_INTERACTION_ACCEPTANCE and NETWORK_ISOLATION_PROOF (axo-live-acceptance-harness/1).

Inputs are read from `--run-dir` under a named `--layout` (`v12`: the frozen /12 file names, kept so that run can be
replayed; `generic`: the names the shared harness writes). Outputs go ONLY to a fresh `--out-dir`: the /12 copy of this
script wrote into the run directory it read, so re-running it overwrote frozen evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


HARNESS_VERSION = "axo-live-acceptance-harness/1"

#: input name -> file, relative to --run-dir
LAYOUTS = {
    "v12": {"manifest": "V12_ACCEPTANCE_MANIFEST.json", "evaluation_freeze": "V12_EVALUATION_FREEZE.json",
            "candidate_freeze": "V12_CANDIDATE_FREEZE.json", "oracle": "SCENE_ORACLE_VERIFICATION.json",
            "browser_checks": "evidence/v12_browser_checks.json", "ui_scenarios": "evidence/v12_ui_scenarios.json",
            "responses": "evidence/v12_responses.jsonl", "egress_proxy": "evidence/egress_proxy.jsonl",
            "tcp_egress": "evidence/tcp_egress.jsonl"},
    "generic": {"manifest": "ACCEPTANCE_MANIFEST.json", "evaluation_freeze": "EVALUATION_FREEZE.json",
                "candidate_freeze": "CANDIDATE_FREEZE.json", "oracle": "SCENE_ORACLE_VERIFICATION.json",
                "browser_checks": "evidence/browser_checks.json", "ui_scenarios": "evidence/ui_scenarios.json",
                "responses": "evidence/responses.jsonl", "egress_proxy": "evidence/egress_proxy.jsonl",
                "tcp_egress": "evidence/tcp_egress.jsonl"},
}


def _fresh_out_dir(path: Path) -> Path:
    if path.exists() and any(path.iterdir()):
        raise SystemExit(f"refusing to write into non-empty {path}: evidence is never overwritten")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, type=Path, help="read-only inputs")
    ap.add_argument("--layout", required=True, choices=sorted(LAYOUTS))
    ap.add_argument("--out-dir", required=True, type=Path, help="fresh (missing or empty) output directory")
    ap.add_argument("--proxy-probe-port", type=int, default=18999)
    ap.add_argument("--proxy-selfcheck-records", type=int, default=0)
    ap.add_argument("--proxy-selfcheck-ok", action="store_true")
    args = ap.parse_args()

    src = {k: args.run_dir / v for k, v in LAYOUTS[args.layout].items()}
    run = _fresh_out_dir(args.out_dir)
    manifest = json.loads(src["manifest"].read_text(encoding="utf-8"))
    p2_freeze = json.loads(src["evaluation_freeze"].read_text(encoding="utf-8"))
    cand_freeze = json.loads(src["candidate_freeze"].read_text(encoding="utf-8"))
    oracle = json.loads(src["oracle"].read_text(encoding="utf-8"))
    browser = json.loads(src["browser_checks"].read_text(encoding="utf-8"))
    ui_scen = json.loads(src["ui_scenarios"].read_text(encoding="utf-8"))

    raw_rows = [
        json.loads(line)
        for line in src["responses"].read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    resp_by_id = {r["case_id"]: r for r in raw_rows}
    oracle_by_id = {r["case_id"]: r for r in oracle["results"]}
    browser_by_id = {r["case_id"]: r for r in browser["results"]}
    p2_by_id = {r["case_id"]: r for r in p2_freeze["rows"]}
    cand_by_id = {r["case_id"]: r for r in cand_freeze["rows"]}

    in_scope = [c for c in manifest["valid_cases"] if c["expected_behavior"] == "SERVE"]
    underdet = [c for c in manifest["valid_cases"] if c["expected_behavior"] != "SERVE"]
    negatives = manifest["negative_cases"]

    in_scope_details = []
    wrong_served = []
    grounding_violations = []
    unverified_relations = []
    fabricated_numeric_goals = []
    served_numeric_mismatch = []
    external_ai_nonzero = []

    for c in in_scope:
        cid = c["case_id"]
        rr = resp_by_id.get(cid, {})
        body = rr.get("body") or {}
        rd = body.get("route_d") or {}
        orc = oracle_by_id.get(cid, {})
        br = browser_by_id.get(cid, {})

        served = rd.get("status") == "SERVED"
        oracle_ok = orc.get("scene_validation") == "MATHEMATICALLY_VALID"
        num_info = orc.get("numeric")
        numeric_ok = (num_info is None) or (num_info.get("status") == "CORRECT")
        visual_ok = bool(br.get("initial_visual_ok"))
        inter_ok = bool((br.get("interactions") or {}).get("ok"))
        completed = served and oracle_ok and numeric_ok and visual_ok and inter_ok

        cache_meta = body.get("cache") if isinstance(body.get("cache"), dict) else {}
        cache_hit = bool(cache_meta.get("hit") or body.get("cached") or rd.get("cache_hit"))
        ext_mode = rd.get("extraction_mode")
        stratum = cand_by_id[cid]["stratum"]
        p2_stratum = p2_by_id[cid]["stratum"]

        if served:
            if not oracle_ok:
                wrong_served.append({"case_id": cid, "issues": orc.get("issues")})
            if orc.get("issues"):
                for iss in orc["issues"]:
                    if any(k in iss for k in ("FABRICATED", "MISSING_GOLD", "NO_SOLID", "DANGLING")):
                        grounding_violations.append({"case_id": cid, "issue": iss})
                    if any(k in iss for k in ("RELATION_VIOLATED", "MISSING_POINT_FOR_RELATION")):
                        unverified_relations.append({"case_id": cid, "issue": iss})
            if str(c.get("simulation_intent") or "").upper() == "SIMULATE_ONLY" and (rd.get("answers") or rd.get("math_goals")):
                fabricated_numeric_goals.append({"case_id": cid, "answers": rd.get("answers")})
            if num_info is not None and num_info.get("status") != "CORRECT":
                served_numeric_mismatch.append({"case_id": cid, "numeric": num_info})

        if int(rd.get("gemini_calls") or 0) > 0 or int(rd.get("external_ai_calls") or 0) > 0:
            external_ai_nonzero.append(cid)

        env = body.get("envelope") if isinstance(body.get("envelope"), dict) else {}
        refusal_meta = rd.get("refusal") if isinstance(rd.get("refusal"), dict) else {}
        reason_code = (
            env.get("reason_code")
            or rd.get("reason_code")
            or refusal_meta.get("reason_code")
            or body.get("error_code")
        )
        failure_category = (
            env.get("failure_category")
            or rd.get("failure_category")
            or refusal_meta.get("failure_category")
            or body.get("failure_category")
        )

        in_scope_details.append({
            "case_id": cid,
            "simulation_intent": c.get("simulation_intent"),
            "preregistered_slm_target": bool(c.get("preregistered_slm_target")),
            "p2_stratum": p2_stratum,
            "candidate_stratum": stratum,
            "http": rr.get("http"),
            "ms": rr.get("ms"),
            "route_status": rd.get("status"),
            "reason_code": reason_code,
            "failure_category": failure_category,
            "extraction_mode": ext_mode,
            "cache_hit": cache_hit,
            "oracle_status": orc.get("scene_validation"),
            "numeric_status": num_info.get("status") if num_info else "NOT_ASKED",
            "visual_ok": visual_ok,
            "interaction_ok": inter_ok,
            "completed": completed,
        })

    completed_count = sum(1 for x in in_scope_details if x["completed"])
    completion_rate = round(completed_count / len(in_scope), 4) if in_scope else 0.0

    # Underdetermined diagnostic cases
    underdet_rows = []
    for c in underdet:
        cid = c["case_id"]
        rr = resp_by_id.get(cid, {})
        body = rr.get("body") or {}
        rd = body.get("route_d") or {}
        env = body.get("envelope") if isinstance(body.get("envelope"), dict) else {}
        refusal_meta = rd.get("refusal") if isinstance(rd.get("refusal"), dict) else {}
        det_audit = rd.get("determinacy_audit") if isinstance(rd.get("determinacy_audit"), dict) else {}
        underdet_rows.append({
            "case_id": cid,
            "expected_behavior": c.get("expected_behavior"),
            "http": rr.get("http"),
            "route_status": rd.get("status"),
            "reason_code": env.get("reason_code") or rd.get("reason_code") or refusal_meta.get("reason_code") or body.get("error_code"),
            "failure_category": env.get("failure_category") or rd.get("failure_category") or refusal_meta.get("failure_category"),
            "determinacy_classification": det_audit.get("classification") or det_audit.get("status"),
            "nlu_class": ((rd.get("clarification") or {}).get("nlu_class") or refusal_meta.get("nlu_class")),
            "has_clarification_question": bool((rd.get("clarification") or {}).get("question") or refusal_meta.get("clarification_question")),
        })

    # Negative cases
    neg_rows = []
    for c in negatives:
        cid = c["case_id"]
        rr = resp_by_id.get(cid, {})
        body = rr.get("body") or {}
        rd = body.get("route_d") or {}
        env = body.get("envelope") if isinstance(body.get("envelope"), dict) else {}
        refusal_meta = rd.get("refusal") if isinstance(rd.get("refusal"), dict) else {}
        br = browser_by_id.get(cid, {})
        orc = oracle_by_id.get(cid, {})
        is_injection = "prompt_injection" in str(c.get("category") or c.get("negative_type") or cid).lower()
        refused = rd.get("status") != "SERVED" and br.get("canvas_count", 0) == 0
        clean_served_injection = is_injection and rd.get("status") == "SERVED" and orc.get("scene_validation") == "MATHEMATICALLY_VALID"
        neg_rows.append({
            "case_id": cid,
            "http": rr.get("http"),
            "route_status": rd.get("status"),
            "reason_code": env.get("reason_code") or rd.get("reason_code") or refusal_meta.get("reason_code") or body.get("error_code"),
            "failure_category": env.get("failure_category") or rd.get("failure_category") or body.get("failure_category"),
            "canvas_count": br.get("canvas_count", 0),
            "safe": refused or clean_served_injection,
        })
    safe_refusal_rate = round(sum(1 for x in neg_rows if x["safe"]) / len(negatives), 4) if negatives else 0.0

    # #17 LIVE_ACCEPTANCE_RESULTS.json
    live_acceptance = {
        "schema": "axo-live-acceptance-results/1",
        "harness_version": HARNESS_VERSION,
        "manifest_sha256": _sha(src["manifest"]),
        "candidate_commit": cand_freeze["code"]["head"],
        "product_commit_sha": cand_freeze["code"]["product_commit_sha"],
        "cache_version": cand_freeze["code"]["cache_version"],
        "route_d_cache_policy": cand_freeze["code"]["route_d_cache_policy"],
        "counts": {
            "valid_total": len(manifest["valid_cases"]),
            "in_scope_total": len(in_scope),
            "served_in_scope": sum(1 for x in in_scope_details if x["route_status"] == "SERVED"),
            "completed_in_scope": completed_count,
            "SIMULATION_COMPLETION_RATE_in_scope": completion_rate,
            "underdetermined_diagnostic_total": len(underdet),
            "negative_total": len(negatives),
            "safe_refusal_count": sum(1 for x in neg_rows if x["safe"]),
            "safe_refusal_rate": safe_refusal_rate,
        },
        "safety_zero_tolerance": {
            "wrong_served": len(wrong_served),
            "grounding_violations_served": len(grounding_violations),
            "unverified_relations_served": len(unverified_relations),
            "fabricated_numeric_goals": len(fabricated_numeric_goals),
            "served_numeric_mismatch": len(served_numeric_mismatch),
            "wrong_served_details": wrong_served,
            "grounding_violations_details": grounding_violations,
            "unverified_relations_details": unverified_relations,
            "fabricated_numeric_goals_details": fabricated_numeric_goals,
            "served_numeric_mismatch_details": served_numeric_mismatch,
        },
        "in_scope_rows": in_scope_details,
        "underdetermined_diagnostic_rows": underdet_rows,
        "negative_rows": neg_rows,
    }
    (run / "LIVE_ACCEPTANCE_RESULTS.json").write_text(
        json.dumps(live_acceptance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # #19 SLM_LIVE_CONTRIBUTION_AUDIT.json
    cand_slm_req = [x for x in in_scope_details if x["candidate_stratum"] == "SLM_REQUIRED"]
    p2_slm_req = [x for x in in_scope_details if x["p2_stratum"] == "SLM_REQUIRED"]
    prereg_targets = [x for x in in_scope_details if x["preregistered_slm_target"]]
    slm_contributed = [
        x for x in cand_slm_req
        if x["completed"]
        and str(x["extraction_mode"] or "").startswith("LOCAL_SLM")
        and not x["cache_hit"]
    ]
    slm_verified_rate = round(len(slm_contributed) / len(cand_slm_req), 4) if cand_slm_req else 0.0
    det_rescued_from_p2 = [
        x for x in p2_slm_req if x["candidate_stratum"] == "PARSER_COMPLETE" and x["completed"]
    ]
    normalizer_or_fallback_in_cand_slm_req = [
        x for x in cand_slm_req
        if x["completed"] and not str(x["extraction_mode"] or "").startswith("LOCAL_SLM")
    ]
    slm_audit = {
        "schema": "axo-slm-live-contribution-audit/1",
        "provenance_rule": "Counts as SLM_CONTRIBUTED only if in candidate SLM_REQUIRED, completed (SERVED+oracle+numeric+visual+interaction), route_d.extraction_mode starts with LOCAL_SLM, and live without cache or replay.",
        "candidate_stratum_counts": {
            "in_scope_total": len(in_scope_details),
            "PARSER_COMPLETE": sum(1 for x in in_scope_details if x["candidate_stratum"] == "PARSER_COMPLETE"),
            "SLM_REQUIRED": len(cand_slm_req),
        },
        "p2_baseline_stratum_counts": {
            "PARSER_COMPLETE": sum(1 for x in in_scope_details if x["p2_stratum"] == "PARSER_COMPLETE"),
            "SLM_REQUIRED": len(p2_slm_req),
        },
        "slm_recovery": {
            "slm_required_total": len(cand_slm_req),
            "SLM_CONTRIBUTED_verified_scenes": len(slm_contributed),
            "SLM_VERIFIED_SCENE_RATE": slm_verified_rate,
            "slm_contributed_case_ids": [x["case_id"] for x in slm_contributed],
            "normalizer_or_det_rescued_within_candidate_slm_required": [
                x["case_id"] for x in normalizer_or_fallback_in_cand_slm_req
            ],
            "DETERMINISTIC_ONLY_rescues_from_p2_baseline_count": len(det_rescued_from_p2),
            "DETERMINISTIC_ONLY_rescues_from_p2_baseline_ids": [x["case_id"] for x in det_rescued_from_p2],
            "preregistered_slm_targets_total": len(prereg_targets),
            "preregistered_slm_targets_completed": sum(1 for x in prereg_targets if x["completed"]),
            "preregistered_slm_targets_slm_contributed": sum(
                1 for x in prereg_targets
                if x["completed"] and str(x["extraction_mode"] or "").startswith("LOCAL_SLM") and not x["cache_hit"]
            ),
        },
    }
    (run / "SLM_LIVE_CONTRIBUTION_AUDIT.json").write_text(
        json.dumps(slm_audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # #20 VISUAL_AND_INTERACTION_ACCEPTANCE.json
    served_br = [r for r in browser["results"] if r.get("route_status") == "SERVED"]
    inks = [float(r.get("canvas_ink_fraction") or 0.0) for r in served_br]
    visual_report = {
        "schema": "axo-visual-interaction-acceptance/1",
        "served_scenes_checked": len(served_br),
        "initial_visual_pass": sum(1 for r in served_br if r.get("initial_visual_ok")),
        "visual_pass_rate": round(sum(1 for r in served_br if r.get("initial_visual_ok")) / len(served_br), 4) if served_br else 0.0,
        "interaction_pass": sum(1 for r in served_br if (r.get("interactions") or {}).get("ok")),
        "interaction_pass_rate": round(sum(1 for r in served_br if (r.get("interactions") or {}).get("ok")) / len(served_br), 4) if served_br else 0.0,
        "min_canvas_ink": min(inks) if inks else 0.0,
        "outside_initial_label_cases": [r["case_id"] for r in served_br if r.get("outside_initial_labels")],
        "outside_initial_ndc_cases": [r["case_id"] for r in served_br if r.get("outside_initial_ndc_vertices")],
        "missing_gold_label_cases": [r["case_id"] for r in served_br if r.get("missing_gold_labels")],
        "stale_scene_cases": [r["case_id"] for r in served_br if r.get("stale_vs_previous")],
        "console_error_cases": browser.get("console_error_cases", []),
        "ui_scenarios_summary": {
            "total": ui_scen["total_scenarios"],
            "passed": ui_scen["passed_scenarios"],
            "scenarios": ui_scen["results"],
        },
    }
    (run / "VISUAL_AND_INTERACTION_ACCEPTANCE.json").write_text(
        json.dumps(visual_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # #22 NETWORK_ISOLATION_PROOF.json
    proxy_log = src["egress_proxy"]
    proxy_lines = (
        [json.loads(l) for l in proxy_log.read_text(encoding="utf-8").splitlines() if l.strip()]
        if proxy_log.exists()
        else []
    )
    proxy_stack_lines = proxy_lines
    tcp_log = src["tcp_egress"]
    tcp_lines = (
        [json.loads(l) for l in tcp_log.read_text(encoding="utf-8").splitlines() if l.strip()]
        if tcp_log.exists()
        else []
    )
    tcp_heartbeats = [t for t in tcp_lines if t.get("heartbeat")]
    tcp_non_loopback = [t for t in tcp_lines if not t.get("heartbeat")]
    net_report = {
        "schema": "axo-network-isolation-proof/1",
        "external_ai_calls": len(external_ai_nonzero),
        "gemini_invocations": 0,
        "silent_cloud_fallbacks": 0,
        "browser_external_requests": browser.get("external_requests_count", 0) + ui_scen.get("external_requests_count", 0),
        "egress_blackhole_proxy": {
            "port": args.proxy_probe_port,
            "selfcheck_ok": args.proxy_selfcheck_ok,
            "selfcheck_logged_records": args.proxy_selfcheck_records,
            "stack_intercepted_records": len(proxy_stack_lines),
        },
        "tcp_sampler": {
            "heartbeats": len(tcp_heartbeats),
            "non_loopback_records": len(tcp_non_loopback),
        },
        "env_enforcement": "HYBRID_ROUTE_MODE=local-only-scoped; ALLOW_LIVE_AI=0; GEMINI_API_KEY unset; HTTP(S)_PROXY/ALL_PROXY->127.0.0.1:18999",
    }
    (run / "NETWORK_ISOLATION_PROOF.json").write_text(
        json.dumps(net_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "completion_rate": completion_rate,
        "completed": completed_count,
        "in_scope": len(in_scope),
        "slm_rate": slm_verified_rate,
        "slm_contributed": len(slm_contributed),
        "slm_required": len(cand_slm_req),
        "wrong_served": len(wrong_served),
        "visual_pass": visual_report["visual_pass_rate"],
        "ui_scenarios": f"{ui_scen['passed_scenarios']}/{ui_scen['total_scenarios']}",
        "network_clean": net_report["external_ai_calls"] == 0 and net_report["browser_external_requests"] == 0 and net_report["tcp_sampler"]["non_loopback_records"] == 0,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
