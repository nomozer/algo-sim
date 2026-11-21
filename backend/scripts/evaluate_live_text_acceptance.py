# -*- coding: utf-8 -*-
"""Single-authority deterministic evaluator for live text acceptance & /15 verdict reconciliation.

Computes separated system vs. SLM metrics and explicit gate flags (never collapsing a
partial threshold pass or failing SLM gate into an overall PASS):
  - END_TO_END_SYSTEM_SCORE
  - CANDIDATE_FALLBACK_SCORE
  - INDEPENDENT_SLM_SCORE
  - LEGACY_BASELINE_STRATUM_SCORE

All verdict flags are derived from frozen criteria, frozen baseline/candidate strata,
real server/browser/oracle/egress receipts, and optional independent SLM / T3 receipts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


VERDICT_SCHEMA_VERSION = "axo-live-text-acceptance-verdict/2"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _extract_reason_and_category(rr: dict[str, Any]) -> tuple[str | None, str | None]:
    body = rr.get("body") or {}
    rd = body.get("route_d") or {}
    env = body.get("envelope") if isinstance(body.get("envelope"), dict) else {}
    refusal = rd.get("refusal") if isinstance(rd.get("refusal"), dict) else {}
    reason = (
        env.get("reason_code")
        or rd.get("reason_code")
        or refusal.get("reason_code")
        or refusal.get("code")
        or body.get("error_code")
        or body.get("reason_code")
    )
    failure_cat = (
        env.get("failure_category")
        or rd.get("failure_category")
        or refusal.get("failure_category")
        or body.get("failure_category")
    )
    return reason, failure_cat


def compute_live_text_verdicts(
    *,
    criteria: dict[str, Any],
    positive_completed: int,
    positive_total: int,
    by_modality: dict[str, dict[str, Any]],
    candidate_slm_routed_ids: list[str],
    candidate_slm_verified_ids: list[str],
    baseline_slm_required_ids: list[str],
    baseline_slm_det_rescued_ids: list[str],
    baseline_slm_live_verified_ids: list[str],
    negative_safe_count: int,
    negative_total: int,
    safety: dict[str, list[Any]],
    network: dict[str, Any],
    candidate_identity_consistent: bool,
    slm_independent_audit: dict[str, Any] | None = None,
    t3_receipt: dict[str, Any] | None = None,
    rewrite_safety_audit: dict[str, Any] | None = None,
    require_independent_slm: bool = True,
    vision_verified: bool = False,
) -> dict[str, Any]:
    """Compute canonical separated scores and strict gate booleans from pre-aggregated metrics."""
    primary_min = float((criteria.get("primary") or {}).get("completion_rate_min", 0.85))
    mod_crit = criteria.get("modalities") or {}
    mod_min = float(mod_crit.get("positive_completion_rate_min", primary_min))
    required_mods = list(mod_crit.get("required") or ["text"])

    completion_rate = (positive_completed / positive_total) if positive_total > 0 else 0.0
    mods_ok = all(
        (m in by_modality)
        and (by_modality[m].get("positive", 0) > 0)
        and ((by_modality[m]["completed"] / by_modality[m]["positive"]) >= mod_min)
        for m in required_mods
    )
    system_completion_met = bool(positive_total > 0 and completion_rate >= primary_min and mods_ok)

    # Fallback SLM criteria (`slm_fallback` in /16, or fallback to legacy `slm` if evaluating /15)
    fb_crit = criteria.get("slm_fallback") or {}
    leg_crit = criteria.get("slm") or {}
    has_fb_crit = bool(fb_crit)

    if has_fb_crit:
        fb_min_sample = int(fb_crit.get("min_routed_sample", 8))
        fb_min_scenes = int(fb_crit.get("min_live_verified_scenes", 5))
        fb_min_rate = float(fb_crit.get("rate_min", 0.50))
        fb_denom = len(candidate_slm_routed_ids)
        fb_num = len(candidate_slm_verified_ids)
        fb_rate = (fb_num / fb_denom) if fb_denom > 0 else None
        fb_sample_floor_met = fb_denom >= fb_min_sample
        fb_rate_met = fb_rate is not None and fb_rate >= fb_min_rate
        fb_count_met = fb_num >= fb_min_scenes
        slm_fallback_gate_met = bool(fb_sample_floor_met and fb_rate_met and fb_count_met)
    else:
        fb_min_sample = 0
        fb_min_scenes = int(leg_crit.get("min_live_verified_scenes", 5))
        fb_min_rate = float(leg_crit.get("completion_rate_min", 0.30))
        fb_denom = len(candidate_slm_routed_ids)
        fb_num = len(candidate_slm_verified_ids)
        fb_rate = (fb_num / fb_denom) if fb_denom > 0 else None
        fb_sample_floor_met = True
        fb_rate_met = fb_rate is not None and fb_rate >= fb_min_rate
        fb_count_met = fb_num >= fb_min_scenes
        slm_fallback_gate_met = False  # set below via legacy stratum if legacy criteria

    # Legacy baseline stratum score
    base_denom = len(baseline_slm_required_ids)
    base_live_num = len(baseline_slm_live_verified_ids)
    base_rate = (base_live_num / base_denom) if base_denom > 0 else None
    leg_min_rate = float(leg_crit.get("completion_rate_min", 0.30))
    leg_min_scenes = int(leg_crit.get("min_live_verified_scenes", 5))
    leg_rate_met = bool(base_rate is not None and base_rate >= leg_min_rate)
    leg_count_met = bool(base_live_num >= leg_min_scenes)
    if not has_fb_crit:
        slm_rate_threshold_met = leg_rate_met
        slm_count_threshold_met = leg_count_met
        slm_fallback_gate_met = bool(leg_rate_met and leg_count_met)
    else:
        slm_rate_threshold_met = fb_rate_met
        slm_count_threshold_met = fb_count_met

    # Independent SLM capability audit
    ind_crit = criteria.get("slm_independent") or {}
    ind_score: dict[str, Any] = {
        "status": "NOT_MEASURED",
        "verified_scenes": None,
        "positive_total": None,
        "rate": None,
        "extraction_correctness": None,
        "grounding_correctness": None,
        "negative_safe_refused": None,
        "negative_total": None,
        "false_assertions_served": None,
        "invalid_relations_served": None,
    }
    ind_gate: bool | str = "NOT_MEASURED"
    if isinstance(slm_independent_audit, dict):
        summary = slm_independent_audit.get("summary") or slm_independent_audit
        v_scenes = int(summary.get("verified_scenes", 0))
        p_tot = int(summary.get("positive_total", 0))
        ind_rate = (v_scenes / p_tot) if p_tot > 0 else None
        neg_ref = int(summary.get("negative_safe_refused", 0))
        neg_tot = int(summary.get("negative_total", 0))
        false_ass = int(summary.get("false_assertions_served", 0))
        inv_rel = int(summary.get("invalid_relations_served", 0))
        ind_score = {
            "status": "MEASURED",
            "verified_scenes": v_scenes,
            "positive_total": p_tot,
            "rate": ind_rate,
            "extraction_correctness": summary.get("extraction_correctness"),
            "grounding_correctness": summary.get("grounding_correctness"),
            "negative_safe_refused": neg_ref,
            "negative_total": neg_tot,
            "false_assertions_served": false_ass,
            "invalid_relations_served": inv_rel,
        }
        req_rate = float(ind_crit.get("verified_scene_rate_min", 0.60))
        req_pos_min = int(ind_crit.get("positive_total", 0))
        req_neg_rate = float(ind_crit.get("negative_safe_refusal_rate_min", 1.0))
        max_false = int(ind_crit.get("false_assertions_max", 0))
        max_inv = int(ind_crit.get("invalid_relations_max", 0))
        ind_gate = bool(
            p_tot >= req_pos_min
            and ind_rate is not None
            and ind_rate >= req_rate
            and (neg_tot == 0 or (neg_ref / neg_tot) >= req_neg_rate)
            and false_ass <= max_false
            and inv_rel <= max_inv
        )

    # Zero-tolerance safety + network isolation gate
    safety_crit = criteria.get("safety") or {}
    safety_counts_clean = (
        len(safety.get("wrong_served", [])) == 0
        and len(safety.get("grounding_violations_served", [])) == 0
        and len(safety.get("unverified_relations_served", [])) == 0
        and len(safety.get("fabricated_numeric_goals", [])) == 0
        and len(safety.get("served_numeric_mismatch", [])) == 0
        and len(safety.get("attachment_provenance_not_present", [])) == 0
    )
    neg_all_safe = (negative_total == 0) or (negative_safe_count == negative_total)
    net_clean = (
        int(network.get("external_ai_calls_reported", 0) or 0) == 0
        and int(network.get("browser_external_requests", 0) or 0) == 0
        and int(network.get("proxy_intercepted", 0) or 0) == 0
        and int(network.get("tcp_non_loopback_records", 0) or 0) == 0
    )
    if safety_crit.get("all_negative_safe", True) is False:
        neg_all_safe = True
    negative_safety_gate_met = bool(neg_all_safe and safety_counts_clean and net_clean)

    source_grounding_verified = bool(
        len(safety.get("grounding_violations_served", [])) == 0
        and len(safety.get("unverified_relations_served", [])) == 0
        and len(safety.get("wrong_served", [])) == 0
    )

    if isinstance(rewrite_safety_audit, dict):
        rw_verdict = rewrite_safety_audit.get("SEMANTIC_REWRITE_SAFETY_VERIFIED")
        semantic_rewrite_verified: bool | str = bool(rw_verdict) if rw_verdict is not None else "NOT_MEASURED"
    else:
        semantic_rewrite_verified = "NOT_MEASURED"

    if isinstance(t3_receipt, dict):
        full_product_gate_pass: bool | str = str(t3_receipt.get("verdict") or "").upper() == "FULL_PRODUCT_GATE_PASS"
    else:
        full_product_gate_pass = "NOT_MEASURED"

    ind_ok_for_composite = (ind_gate is True) if require_independent_slm else (ind_gate is not False)
    composite_live_text_accepted = bool(
        system_completion_met
        and slm_fallback_gate_met
        and ind_ok_for_composite
        and negative_safety_gate_met
        and candidate_identity_consistent
    )

    local_text_model1_verified = bool(
        composite_live_text_accepted
        and (semantic_rewrite_verified is not False)
        and source_grounding_verified
        and (full_product_gate_pass is True)
    )
    local_vision_verified = bool(vision_verified)
    full_gemini_replaced = bool(local_text_model1_verified and local_vision_verified)

    return {
        "scores": {
            "END_TO_END_SYSTEM_SCORE": {
                "completed": positive_completed,
                "total_positive": positive_total,
                "rate": completion_rate,
            },
            "CANDIDATE_FALLBACK_SCORE": {
                "verified_live_slm_scenes": fb_num,
                "verified_case_ids": list(candidate_slm_verified_ids),
                "candidate_slm_routed_total": fb_denom,
                "routed_case_ids": list(candidate_slm_routed_ids),
                "rate": fb_rate,
                "min_sample_floor": fb_min_sample,
                "min_scenes_floor": fb_min_scenes,
                "min_rate": fb_min_rate,
                "sample_floor_met": fb_sample_floor_met,
            },
            "INDEPENDENT_SLM_SCORE": ind_score,
            "LEGACY_BASELINE_STRATUM_SCORE": {
                "baseline_slm_required_total": base_denom,
                "completed_deterministically_on_candidate": len(baseline_slm_det_rescued_ids),
                "completed_via_live_slm": base_live_num,
                "verified_live_slm_case_ids": list(baseline_slm_live_verified_ids),
                "rate_live_slm_over_baseline": base_rate,
            },
        },
        "gates": {
            "SEMANTIC_REWRITE_SAFETY_VERIFIED": semantic_rewrite_verified,
            "SOURCE_GROUNDING_VERIFIED": source_grounding_verified,
            "TEXT_COMPLETION_THRESHOLD_MET": system_completion_met,
            "SYSTEM_TEXT_COMPLETION_THRESHOLD_MET": system_completion_met,
            "SLM_FALLBACK_SAMPLE_FLOOR_MET": fb_sample_floor_met,
            "SLM_FALLBACK_RATE_THRESHOLD_MET": fb_rate_met,
            "SLM_FALLBACK_COUNT_THRESHOLD_MET": fb_count_met,
            "SLM_FALLBACK_GATE_MET": slm_fallback_gate_met,
            "SLM_RATE_THRESHOLD_MET": slm_rate_threshold_met,
            "SLM_COUNT_THRESHOLD_MET": slm_count_threshold_met,
            "SLM_INDEPENDENT_CAPABILITY_GATE_MET": ind_gate,
            "NEGATIVE_SAFETY_GATE_MET": negative_safety_gate_met,
            "CANDIDATE_IDENTITY_CONSISTENT": candidate_identity_consistent,
            "COMPOSITE_LIVE_TEXT_ACCEPTED": composite_live_text_accepted,
            "FULL_PRODUCT_GATE_PASS": full_product_gate_pass,
            "LOCAL_TEXT_MODEL1_VERIFIED": local_text_model1_verified,
            "LOCAL_VISION_REPLACEMENT_VERIFIED": local_vision_verified,
            "FULL_GEMINI_ROLE_REPLACEMENT_VERIFIED": full_gemini_replaced,
            "MAIN_MERGE_READY": False,
            "MAIN_MERGE_COMPLETED": False,
            "REMOTE_PUSH_COMPLETED": False,
        },
    }


def _check_candidate_identity(
    manifest_path: Path,
    criteria_path: Path,
    acceptance_freeze: dict[str, Any],
    candidate_freeze: dict[str, Any],
    t3_receipt: dict[str, Any] | None,
    slm_independent_audit: dict[str, Any] | None,
) -> tuple[bool, list[str]]:
    mismatches: list[str] = []
    man_sha = _sha256_file(manifest_path)
    crit_sha = _sha256_file(criteria_path)

    crit = _read_json(criteria_path)
    crit_man_sha = (crit.get("manifest") or {}).get("sha256")
    if crit_man_sha and crit_man_sha != man_sha:
        mismatches.append("criteria.manifest.sha256 != ACCEPTANCE_MANIFEST.json")

    frz_inputs = acceptance_freeze.get("inputs") or {}
    if isinstance(frz_inputs, dict):
        if (exp := frz_inputs.get("manifest_sha256")) and exp != man_sha:
            mismatches.append("acceptance_freeze.inputs.manifest_sha256 != ACCEPTANCE_MANIFEST.json")
        if (exp := frz_inputs.get("criteria_sha256")) and exp != crit_sha:
            mismatches.append("acceptance_freeze.inputs.criteria_sha256 != ACCEPTANCE_CRITERIA.json")
    frz_files = acceptance_freeze.get("files") or {}
    if isinstance(frz_files, dict):
        if (exp := frz_files.get("manifest_sha256") or (acceptance_freeze.get("manifest") or {}).get("sha256")) and exp != man_sha:
            mismatches.append("acceptance_freeze.manifest_sha256 != ACCEPTANCE_MANIFEST.json")
        if (exp := frz_files.get("criteria_sha256") or (acceptance_freeze.get("criteria") or {}).get("sha256")) and exp != crit_sha:
            mismatches.append("acceptance_freeze.criteria_sha256 != ACCEPTANCE_CRITERIA.json")

    cand_inputs = candidate_freeze.get("inputs") or {}
    if (exp := cand_inputs.get("manifest_sha256")) and exp != man_sha:
        mismatches.append("candidate_freeze.inputs.manifest_sha256 != ACCEPTANCE_MANIFEST.json")
    if (exp := cand_inputs.get("criteria_sha256")) and exp != crit_sha:
        mismatches.append("candidate_freeze.inputs.criteria_sha256 != ACCEPTANCE_CRITERIA.json")

    cand_code = candidate_freeze.get("code") or {}
    if isinstance(t3_receipt, dict):
        t3_cand = t3_receipt.get("candidate") or {}
        for key in ("product_commit_sha", "measured_system_tree_hash", "cache_version", "route_d_cache_policy"):
            if cand_code.get(key) and t3_cand.get(key) and str(cand_code[key]) != str(t3_cand[key]):
                mismatches.append(f"t3_receipt.candidate.{key} != candidate_freeze.code.{key}")

    if isinstance(slm_independent_audit, dict):
        ind_cand = slm_independent_audit.get("candidate") or {}
        for key in ("product_commit_sha", "measured_system_tree_hash", "cache_version"):
            if cand_code.get(key) and ind_cand.get(key) and str(cand_code[key]) != str(ind_cand[key]):
                mismatches.append(f"slm_independent_audit.candidate.{key} != candidate_freeze.code.{key}")

    return (len(mismatches) == 0), mismatches


def evaluate_from_artifacts(
    *,
    manifest_path: Path,
    criteria_path: Path,
    acceptance_freeze_path: Path,
    candidate_freeze_path: Path,
    responses_path: Path,
    browser_checks_path: Path,
    oracle_path: Path,
    ui_scenarios_path: Path | None = None,
    egress_proxy_path: Path | None = None,
    tcp_egress_path: Path | None = None,
    slm_independent_path: Path | None = None,
    t3_receipt_path: Path | None = None,
    rewrite_safety_path: Path | None = None,
    performance_path: Path | None = None,
    require_independent_slm: bool = True,
) -> dict[str, Any]:
    """Build complete LIVE_TEXT_ACCEPTANCE_RESULTS payload from real harness outputs."""
    manifest = _read_json(manifest_path)
    criteria = _read_json(criteria_path)
    acceptance_freeze = _read_json(acceptance_freeze_path)
    candidate_freeze = _read_json(candidate_freeze_path)
    raw_responses = _read_jsonl(responses_path)
    browser_data = _read_json(browser_checks_path)
    oracle_data = _read_json(oracle_path)
    ui_data = _read_json(ui_scenarios_path) if (ui_scenarios_path and ui_scenarios_path.exists()) else None
    slm_ind = _read_json(slm_independent_path) if (slm_independent_path and slm_independent_path.exists()) else None
    t3_rec = _read_json(t3_receipt_path) if (t3_receipt_path and t3_receipt_path.exists()) else None
    rw_audit = _read_json(rewrite_safety_path) if (rewrite_safety_path and rewrite_safety_path.exists()) else None
    perf_data = _read_json(performance_path) if (performance_path and performance_path.exists()) else None

    resp_by_id = {r["case_id"]: r for r in raw_responses}
    browser_by_id = {r["case_id"]: r for r in browser_data.get("results", [])}
    oracle_by_id = {r["case_id"]: r for r in oracle_data.get("results", [])}
    base_strata = {r["case_id"]: r.get("stratum") for r in acceptance_freeze.get("rows", []) if isinstance(r, dict)}
    cand_strata = {r["case_id"]: r.get("stratum") for r in candidate_freeze.get("rows", []) if isinstance(r, dict)}

    pos_cases = [c for c in manifest.get("valid_cases", []) if c.get("expected_behavior") == "SERVE"]
    neg_cases = list(manifest.get("negative_cases", []))
    all_cases = pos_cases + neg_cases
    assert set(resp_by_id) >= {c["case_id"] for c in all_cases}, "responses.jsonl missing manifest cases"
    assert set(browser_by_id) >= {c["case_id"] for c in all_cases}, "browser_checks.json missing manifest cases"

    wrong_served: list[dict[str, Any]] = []
    grounding_violations: list[dict[str, Any]] = []
    unverified_relations: list[dict[str, Any]] = []
    fabricated_numeric_goals: list[dict[str, Any]] = []
    served_numeric_mismatch: list[dict[str, Any]] = []

    case_rows: list[dict[str, Any]] = []
    by_modality: dict[str, dict[str, int]] = {}
    ext_ai_calls = 0

    for c in all_cases:
        cid = c["case_id"]
        mod = c.get("input_type", "text")
        by_modality.setdefault(mod, {"positive": 0, "served": 0, "completed": 0, "negative": 0, "negative_safely_refused": 0})
        rr = resp_by_id[cid]
        body = rr.get("body") or {}
        rd = body.get("route_d") or {}
        env = body.get("envelope") if isinstance(body.get("envelope"), dict) else {}
        receipt = rd.get("slm_grounding_envelope") or {}
        adaptive = rd.get("adaptive_telemetry") or {}
        diag = rd.get("local_diagnostics") or {}
        br = browser_by_id.get(cid, {})
        orc = oracle_by_id.get(cid, {})
        reason_code, failure_category = _extract_reason_and_category(rr)

        served = rd.get("status") == "SERVED" and bool(env.get("scene3d"))
        math_status = orc.get("scene_validation") or ("NOT_SERVED" if not served else "UNKNOWN")
        num_info = orc.get("numeric") or {}
        num_status = num_info.get("status")
        empty_numeric = not c.get("metric_oracle") and not (rd.get("answers") or {})
        numeric_ok = bool((num_status == "CORRECT") or (empty_numeric and num_status is None))
        visual_ok = bool(br.get("initial_visual_ok"))
        interaction_ok = bool((br.get("interactions") or {}).get("ok"))
        completed = bool(served and math_status == "MATHEMATICALLY_VALID" and numeric_ok and visual_ok and interaction_ok)

        cache_meta = body.get("cache") if isinstance(body.get("cache"), dict) else {}
        cache_hit = bool(cache_meta.get("hit") or body.get("cached") or receipt.get("cache_hit") or rd.get("cache_hit"))
        ext_mode = rd.get("extraction_mode")
        slm_invoked = bool(receipt.get("slm_invoked"))
        is_replay = str(ext_mode or "").upper().startswith("REPLAY")

        source_verified = bool(served and rd.get("source_verification"))
        sg_status = "VERIFIED" if source_verified else (
            "REJECTED" if diag.get("detected_by") == "SOURCE_GATE" else (
                "NOT_REACHED" if reason_code == "GATE_OUT_OF_SCOPE" or ext_mode == "LOCAL_SLM_GROUNDING_REJECTED" else "UNKNOWN"
            )
        )
        rel_failures = sum(r.get("holds") is not True for r in orc.get("relations", []))

        ext_calls_row = int(adaptive.get("total_provider_calls") or 0) + int(rd.get("gemini_calls") or 0) + int(rd.get("external_ai_calls") or 0)
        ext_ai_calls += ext_calls_row

        if c.get("expected_behavior") == "SERVE":
            by_modality[mod]["positive"] += 1
            if served:
                by_modality[mod]["served"] += 1
                if math_status != "MATHEMATICALLY_VALID":
                    wrong_served.append({"case_id": cid, "issues": orc.get("issues")})
                for iss in orc.get("issues") or ():
                    if any(k in iss for k in ("FABRICATED", "MISSING_GOLD", "NO_SOLID", "DANGLING")):
                        grounding_violations.append({"case_id": cid, "issue": iss})
                    if any(k in iss for k in ("RELATION_VIOLATED", "MISSING_POINT_FOR_RELATION")):
                        unverified_relations.append({"case_id": cid, "issue": iss})
                if not rd.get("source_verification"):
                    grounding_violations.append({"case_id": cid, "issue": "MISSING_SOURCE_VERIFICATION"})
                if str(c.get("simulation_intent") or "").upper() == "SIMULATE_ONLY" and (rd.get("answers") or rd.get("math_goals")):
                    fabricated_numeric_goals.append({"case_id": cid, "answers": rd.get("answers")})
                if c.get("metric_oracle") and num_status != "CORRECT":
                    served_numeric_mismatch.append({"case_id": cid, "numeric": num_info})
            if completed:
                by_modality[mod]["completed"] += 1
        else:
            by_modality[mod]["negative"] += 1
            is_injection = "prompt_injection" in str(c.get("phrase_family") or c.get("category") or cid).lower()
            refused_safely = (rr.get("http") == 200 and not served and br.get("canvas_count", 0) == 0)
            clean_served_injection = bool(is_injection and served and math_status == "MATHEMATICALLY_VALID" and source_verified)
            if refused_safely or clean_served_injection:
                by_modality[mod]["negative_safely_refused"] += 1
            else:
                wrong_served.append({"case_id": cid, "issues": ["NEGATIVE_CONTROL_NOT_REFUSED_SAFELY"]})

        case_rows.append({
            "case_id": cid,
            "modality": mod,
            "expected_behavior": c.get("expected_behavior"),
            "simulation_intent": c.get("simulation_intent"),
            "phrase_family": c.get("phrase_family"),
            "baseline_stratum": base_strata.get(cid),
            "candidate_stratum": cand_strata.get(cid),
            "http": rr.get("http"),
            "ms": rr.get("ms"),
            "route": adaptive.get("chosen_route") or ext_mode or "UNKNOWN",
            "route_status": rd.get("status") or env.get("status") or body.get("status") or "UNKNOWN",
            "extraction_mode": ext_mode,
            "deterministic_parser_status": adaptive.get("local_parse_status") or diag.get("parse_status") or "UNKNOWN",
            "slm": {
                "invoked": slm_invoked,
                "grounding": receipt.get("grounding_status"),
                "cache_hit": cache_hit,
                "is_replay": is_replay,
            },
            "source_gate_status": sg_status,
            "source_gate_detector": diag.get("detected_by"),
            "scene_served": served,
            "mathematical_validation": math_status,
            "relation_failures": rel_failures,
            "numeric_status": num_status or ("NOT_ASKED" if empty_numeric else "NOT_EVALUATED"),
            "answer_exact": {k: v.get("coef") for k, v in (rd.get("answer_exact") or {}).items() if isinstance(v, dict)},
            "answers": rd.get("answers") or {},
            "visual_ok": visual_ok,
            "interaction_ok": interaction_ok,
            "canvas_count": br.get("canvas_count"),
            "reason_code": reason_code,
            "failure_category": failure_category,
            "clarification": (rd.get("clarification") or {}).get("question"),
            "completed": completed,
        })

    pos_rows = [r for r in case_rows if r["expected_behavior"] == "SERVE"]
    neg_rows = [r for r in case_rows if r["expected_behavior"] != "SERVE"]

    cand_slm_routed_ids = [
        r["case_id"]
        for r in pos_rows
        if r["candidate_stratum"] == "SLM_REQUIRED" or r["slm"]["invoked"] is True
    ]
    cand_slm_verified_ids = [
        r["case_id"]
        for r in pos_rows
        if r["case_id"] in cand_slm_routed_ids
        and r["completed"]
        and r["slm"]["invoked"] is True
        and r["slm"]["cache_hit"] is False
        and r["slm"]["is_replay"] is False
        and str(r["extraction_mode"] or "").startswith("LOCAL_SLM")
        and r["source_gate_status"] == "VERIFIED"
    ]

    base_slm_req_ids = [r["case_id"] for r in pos_rows if r["baseline_stratum"] == "SLM_REQUIRED"]
    base_slm_det_rescued_ids = [
        r["case_id"]
        for r in pos_rows
        if r["case_id"] in base_slm_req_ids
        and r["completed"]
        and not r["slm"]["invoked"]
    ]
    base_slm_live_verified_ids = [
        r["case_id"]
        for r in pos_rows
        if r["case_id"] in base_slm_req_ids
        and r["case_id"] in cand_slm_verified_ids
    ]

    proxy_records = _read_jsonl(egress_proxy_path) if (egress_proxy_path and egress_proxy_path.exists()) else []
    tcp_records = _read_jsonl(tcp_egress_path) if (tcp_egress_path and tcp_egress_path.exists()) else []
    network = {
        "external_ai_calls_reported": ext_ai_calls,
        "browser_external_requests": int(browser_data.get("external_requests_count", 0))
        + (int(ui_data.get("external_requests_count", 0)) if ui_data else 0),
        "proxy_intercepted": len(proxy_records),
        "tcp_heartbeats": sum(1 for t in tcp_records if t.get("heartbeat") is True),
        "tcp_non_loopback_records": sum(1 for t in tcp_records if t.get("heartbeat") is not True),
        "physical_internet_disconnect": "NOT_MEASURED",
    }

    cand_consistent, mismatches = _check_candidate_identity(
        manifest_path, criteria_path, acceptance_freeze, candidate_freeze, t3_rec, slm_ind,
    )

    safety = {
        "wrong_served": wrong_served,
        "grounding_violations_served": grounding_violations,
        "unverified_relations_served": unverified_relations,
        "fabricated_numeric_goals": fabricated_numeric_goals,
        "served_numeric_mismatch": served_numeric_mismatch,
        "attachment_provenance_not_present": [],
    }

    verdicts = compute_live_text_verdicts(
        criteria=criteria,
        positive_completed=sum(1 for r in pos_rows if r["completed"]),
        positive_total=len(pos_rows),
        by_modality=by_modality,
        candidate_slm_routed_ids=cand_slm_routed_ids,
        candidate_slm_verified_ids=cand_slm_verified_ids,
        baseline_slm_required_ids=base_slm_req_ids,
        baseline_slm_det_rescued_ids=base_slm_det_rescued_ids,
        baseline_slm_live_verified_ids=base_slm_live_verified_ids,
        negative_safe_count=sum(v["negative_safely_refused"] for v in by_modality.values()),
        negative_total=len(neg_rows),
        safety=safety,
        network=network,
        candidate_identity_consistent=cand_consistent,
        slm_independent_audit=slm_ind,
        t3_receipt=t3_rec,
        rewrite_safety_audit=rw_audit,
        require_independent_slm=require_independent_slm,
        vision_verified=False,
    )

    ui_summary = None
    if ui_data is not None:
        ui_summary = {
            "total": ui_data.get("total_scenarios"),
            "passed": ui_data.get("passed_scenarios"),
            "results": ui_data.get("results"),
        }

    return {
        "schema": VERDICT_SCHEMA_VERSION,
        "manifest_sha256": _sha256_file(manifest_path),
        "criteria_sha256": _sha256_file(criteria_path),
        "evaluation_identity": candidate_freeze.get("code"),
        "registered_inputs": candidate_freeze.get("inputs"),
        "identity_mismatches": mismatches,
        "totals": {
            "positive": len(pos_cases),
            "served": sum(1 for r in pos_rows if r["scene_served"]),
            "completed": sum(1 for r in pos_rows if r["completed"]),
            "completion_rate": verdicts["scores"]["END_TO_END_SYSTEM_SCORE"]["rate"],
            "negative": len(neg_cases),
            "negative_safely_refused": sum(v["negative_safely_refused"] for v in by_modality.values()),
        },
        "by_modality": by_modality,
        "scores": verdicts["scores"],
        "verdicts": verdicts["gates"],
        "safety": safety,
        "network": network,
        "ui_scenarios": ui_summary,
        "performance": perf_data,
        "cases": case_rows,
    }


def reconcile_live_results_artifact(
    *,
    live_results_path: Path,
    criteria_path: Path,
    acceptance_freeze_path: Path,
    candidate_freeze_path: Path,
    t3_receipt_path: Path | None = None,
) -> dict[str, Any]:
    """Re-evaluate an existing historical LIVE_TEXT_ACCEPTANCE_RESULTS.json without altering it."""
    res = _read_json(live_results_path)
    criteria = _read_json(criteria_path)
    acceptance_freeze = _read_json(acceptance_freeze_path)
    candidate_freeze = _read_json(candidate_freeze_path)
    t3_rec = _read_json(t3_receipt_path) if (t3_receipt_path and t3_receipt_path.exists()) else None

    base_slm_ids = [r["case_id"] for r in acceptance_freeze.get("rows", []) if r.get("stratum") == "SLM_REQUIRED"]
    cand_slm_ids = [r["case_id"] for r in candidate_freeze.get("rows", []) if r.get("stratum") == "SLM_REQUIRED"]
    cases_by_id = {c["case_id"]: c for c in res.get("cases", [])}
    slm_verified = list((res.get("slm") or {}).get("verified_case_ids") or [])
    det_rescued = [
        cid for cid in base_slm_ids
        if cases_by_id.get(cid, {}).get("completed") and not cases_by_id.get(cid, {}).get("slm", {}).get("invoked")
    ]

    totals = res.get("totals") or {}
    verdicts = compute_live_text_verdicts(
        criteria=criteria,
        positive_completed=int(totals.get("completed", 0)),
        positive_total=int(totals.get("positive", 0)),
        by_modality=res.get("by_modality") or {},
        candidate_slm_routed_ids=cand_slm_ids,
        candidate_slm_verified_ids=[cid for cid in slm_verified if cid in cand_slm_ids],
        baseline_slm_required_ids=base_slm_ids,
        baseline_slm_det_rescued_ids=det_rescued,
        baseline_slm_live_verified_ids=slm_verified,
        negative_safe_count=int(totals.get("negative_safely_refused", 0)),
        negative_total=int(totals.get("negative", 0)),
        safety=res.get("safety") or {},
        network=res.get("network") or {},
        candidate_identity_consistent=True,
        slm_independent_audit=None,
        t3_receipt=t3_rec,
        rewrite_safety_audit=None,
        require_independent_slm=False,
        vision_verified=False,
    )
    return {
        "schema": "axo-legacy-verdict-reconciliation/1",
        "source_artifact": str(live_results_path.as_posix()),
        "source_sha256": _sha256_file(live_results_path),
        "reported_raw_flag_LIVE_SIMULATION_ACCEPTED": res.get("LIVE_SIMULATION_ACCEPTED"),
        "scores": verdicts["scores"],
        "reconciled_verdicts": verdicts["gates"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic single-authority live text acceptance evaluator.")
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--criteria", required=True, type=Path)
    ap.add_argument("--acceptance-freeze", required=True, type=Path)
    ap.add_argument("--candidate-freeze", required=True, type=Path)
    ap.add_argument("--responses", required=True, type=Path)
    ap.add_argument("--browser-checks", required=True, type=Path)
    ap.add_argument("--oracle", required=True, type=Path)
    ap.add_argument("--ui-scenarios", type=Path, default=None)
    ap.add_argument("--egress-proxy", type=Path, default=None)
    ap.add_argument("--tcp-egress", type=Path, default=None)
    ap.add_argument("--slm-independent", type=Path, default=None)
    ap.add_argument("--t3-receipt", type=Path, default=None)
    ap.add_argument("--rewrite-safety", type=Path, default=None)
    ap.add_argument("--performance", type=Path, default=None)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--no-require-independent-slm", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if args.out.exists() and not args.force:
        raise SystemExit(f"refusing to overwrite existing evidence {args.out}")

    payload = evaluate_from_artifacts(
        manifest_path=args.manifest,
        criteria_path=args.criteria,
        acceptance_freeze_path=args.acceptance_freeze,
        candidate_freeze_path=args.candidate_freeze,
        responses_path=args.responses,
        browser_checks_path=args.browser_checks,
        oracle_path=args.oracle,
        ui_scenarios_path=args.ui_scenarios,
        egress_proxy_path=args.egress_proxy,
        tcp_egress_path=args.tcp_egress,
        slm_independent_path=args.slm_independent,
        t3_receipt_path=args.t3_receipt,
        rewrite_safety_path=args.rewrite_safety,
        performance_path=args.performance,
        require_independent_slm=not args.no_require_independent_slm,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"scores": payload["scores"], "verdicts": payload["verdicts"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
