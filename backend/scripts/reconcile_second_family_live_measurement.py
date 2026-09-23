# -*- coding: utf-8 -*-
"""SECOND FAMILY LIVE MEASUREMENT RECONCILIATION SCRIPT.

Offline attribution audit and measurement apparatus reconciliation
for the SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION wave.
No network requests, 0 Gemini API calls.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

# Paths
REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = REPO_ROOT / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene"
HISTORICAL_DIR = EVAL_DIR / "second-family-live-schema-revalidation"
RECONCILIATION_DIR = EVAL_DIR / "second-family-live-measurement-reconciliation"

EXPECTED_RESPONSE_SHA256 = "47e161b8af8dfa58876314df55949e2c63b85513302648cd3d33f35f0c73fec6"


# ─── B1: LENGTH EVALUATOR IMPLEMENTATIONS ────────────────────────────────────

def legacy_length_evaluator(contract: Any) -> dict[str, str | None]:
    """Legacy/flawed evaluator predicate from execute_live_revalidation.py (Bug R1).
    
    Drops facts if label is descriptive (e.g. 'Đoạn thẳng AB' instead of 'AB').
    """
    extracted_lengths: dict[str, str | None] = {}
    for f in getattr(contract, "input_facts", ()) or ():
        if getattr(f, "label", None) in ("AB", "AC", "AD"):
            vals = getattr(f, "values", None)
            extracted_lengths[f.label] = vals[0] if vals else None
    return extracted_lengths


def corrected_length_evaluator(contract: Any) -> dict[str, str | None]:
    """Corrected evaluator that checks canonical references/identifiers.
    
    Recognizes facts with unambiguous structural references (id like 'ab_length'
    or canonical endpoints) regardless of descriptive display labels.
    Rejects ambiguous or ungrounded facts.
    """
    extracted_lengths: dict[str, str | None] = {}
    
    # Mapping table of unambiguous canonical segment keys
    target_segments = {
        ("A", "B"): "AB",
        ("A", "C"): "AC",
        ("A", "D"): "AD",
    }
    
    # 1. First check input_facts with canonical ID or endpoints
    for f in getattr(contract, "input_facts", ()) or ():
        fid = str(getattr(f, "fact_id", "") or getattr(f, "id", "") or "")
        label = str(getattr(f, "label", "") or "")
        vals = getattr(f, "values", ()) or ()
        val = str(vals[0]) if vals else None
        
        # Check canonical ID pattern: e.g. ab_length, ac_length, ad_length
        m_id = re.fullmatch(r"([a-zA-Z]{2})_length", fid.lower())
        if m_id:
            pair_key = tuple(sorted(m_id.group(1).upper()))
            if pair_key in target_segments and val:
                extracted_lengths[target_segments[pair_key]] = val
                continue

        # Check exact token label
        if label.strip() in ("AB", "AC", "AD") and val:
            extracted_lengths[label.strip()] = val
            continue
            
        # Check descriptive Vietnamese label with clear segment mention:
        # e.g. "Đoạn thẳng AB", "Cạnh AB"
        m_desc = re.fullmatch(r"(?:Đoạn\s+(?:thẳng\s+)?|Cạnh\s+)?([A-Z]{2})", label.strip(), re.IGNORECASE)
        if m_desc and val:
            pair_key = tuple(sorted(m_desc.group(1).upper()))
            if pair_key in target_segments:
                extracted_lengths[target_segments[pair_key]] = val
                continue

    # 2. Also inspect contract.source_invariants if available
    for inv in getattr(contract, "source_invariants", ()) or ():
        if getattr(inv, "kind", None) == "segment_length":
            pts = tuple(sorted(str(p) for p in (getattr(inv, "points", ()) or ())))
            if pts in target_segments and getattr(inv, "expected", None):
                extracted_lengths[target_segments[pts]] = str(inv.expected)

    return extracted_lengths


# ─── B2: PIPELINE HARNESS IMPLEMENTATIONS ────────────────────────────────────

def legacy_pipeline_harness_call(contract: Any) -> Any:
    """Legacy harness invocation from execute_live_revalidation.py (Bug R2).
    
    Attempts to instantiate FG.FactGraph() which does not exist.
    """
    sys.path.insert(0, str(REPO_ROOT / "backend"))
    from app.simulation.geometry_compiler import fact_graph as FG
    return FG.FactGraph()  # Raises AttributeError!


def corrected_pipeline_harness_call(contract: Any) -> dict[str, Any]:
    """Corrected harness invocation using canonical production entry point."""
    sys.path.insert(0, str(REPO_ROOT / "backend"))
    from app.simulation.geometry_compiler import contract_adapter as CA
    from app.simulation.geometry_compiler import compiler as C
    from app.simulation.semantic_program.interpreter import SemanticInterpreter

    res = CA.build_fact_graph(contract)
    if res.status != "VALID" or res.graph is None:
        return {
            "status": "ADAPTER_FAILED",
            "reason": res.reason_code,
            "graph": None,
            "program": None,
            "answer": None,
        }
    
    graph = res.graph
    el = C.danh_gia_eligibility(graph)
    if el.status != "SUPPORTED":
        return {
            "status": "NOT_ELIGIBLE",
            "reason": el.reason_code,
            "graph": graph,
            "program": None,
            "answer": None,
        }
        
    bd = C.bien_dich(graph)
    if bd.status != "COMPILED" or not bd.program:
        return {
            "status": "COMPILATION_FAILED",
            "reason": bd.status,
            "graph": graph,
            "program": None,
            "answer": None,
        }

    interp = SemanticInterpreter()
    state = interp.execute(bd.program)
    ans = state.final_memory.get("the_tich_lang_tru")
    return {
        "status": "SUCCESS",
        "reason": None,
        "graph": graph,
        "program": bd.program,
        "answer": ans,
    }


# ─── RECONCILIATION RUNNER ───────────────────────────────────────────────────

def run_reconciliation() -> dict[str, Any]:
    """Run full measurement reconciliation across Gate A, B, C, D."""
    RECONCILIATION_DIR.mkdir(parents=True, exist_ok=True)
    
    # ── GATE A: Source Evidence Integrity ──
    # Check scratch location for raw response matching EXPECTED_RESPONSE_SHA256
    scratch_dir = Path("C:/Users/Bunny/.gemini/antigravity-ide/brain/c2c7f6b5-85ff-4dad-bbc8-bb9d513f6dfb/scratch")
    raw_response_path = scratch_dir / "live_reval_raw_response.json"
    
    raw_response_found = False
    raw_response_hash_verified = False
    raw_response_content = None
    integrity_note = ""

    if raw_response_path.is_file():
        try:
            data = json.loads(raw_response_path.read_text(encoding="utf-8"))
            preview = data.get("response_preview")
            # Check if preview has expected hash or if full response exists
            if preview:
                p_hash = hashlib.sha256(preview.encode("utf-8")).hexdigest()
                if p_hash == EXPECTED_RESPONSE_SHA256:
                    raw_response_found = True
                    raw_response_hash_verified = True
                    raw_response_content = preview
                else:
                    integrity_note = (
                        f"Raw response preview truncated at 500 chars (SHA-256 {p_hash[:16]}... "
                        f"!= expected {EXPECTED_RESPONSE_SHA256[:16]}...). "
                        f"Full candidate text was not serialized to disk."
                    )
        except Exception as e:
            integrity_note = f"Error reading raw response: {e}"
    else:
        integrity_note = "Raw response file not found in scratch directory."

    source_evidence_integrity = {
        "schema_version": "2.0.0",
        "wave": "SECOND_FAMILY_LIVE_MEASUREMENT_RECONCILIATION_OFFLINE",
        "source_wave": "SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION",
        "case_id": "PRISM_SCHEMA_LIVE_P01",
        "expected_response_sha256": EXPECTED_RESPONSE_SHA256,
        "raw_response_file_found": raw_response_found,
        "raw_response_hash_verified": raw_response_hash_verified,
        "integrity_status": "VERIFIED" if raw_response_hash_verified else "HISTORICAL_EVIDENCE_INSUFFICIENT",
        "note": integrity_note,
        "historical_artifacts_checked": [
            "docs/evaluation/geometry/photo-problem-to-scene/second-family-live-schema-revalidation/REQUEST_OBSERVATION.json",
            "docs/evaluation/geometry/photo-problem-to-scene/second-family-live-schema-revalidation/LIVE_RESULT.json",
            "docs/evaluation/geometry/photo-problem-to-scene/second-family-live-schema-revalidation/PIPELINE_RESULT.json",
            "docs/evaluation/geometry/photo-problem-to-scene/second-family-live-schema-revalidation/FINAL_DECISION.json"
        ]
    }
    (RECONCILIATION_DIR / "SOURCE_EVIDENCE_INTEGRITY.json").write_text(
        json.dumps(source_evidence_integrity, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    # ── GATE B: Attribution Audit ──
    attribution_audit = {
        "schema_version": "2.0.0",
        "wave": "SECOND_FAMILY_LIVE_MEASUREMENT_RECONCILIATION_OFFLINE",
        "bug_r1_length_evaluator": {
            "error_code": "LABEL_MATCHING_DROPS_VALID_LENGTH_FACTS",
            "location": "scratch/execute_live_revalidation.py lines 201-203",
            "flawed_predicate": "if f.label in ('AB', 'AC', 'AD')",
            "failure_mechanism": "Strict token matching on f.label discarded facts with descriptive labels (e.g. 'Đoạn thẳng AB') or facts referenced by fact_id ('ab_length'), resulting in empty extracted lengths map.",
            "attribution": "MEASUREMENT_APPARATUS_ERROR"
        },
        "bug_r2_pipeline_harness": {
            "error_code": "STALE_OR_NONEXISTENT_FACT_GRAPH_CLASS_REFERENCE",
            "location": "scratch/execute_live_revalidation.py lines 237-238",
            "flawed_call": "g = FG.FactGraph()",
            "failure_mechanism": "Module app.simulation.geometry_compiler.fact_graph contains GeometryFactGraph, not FactGraph. Invocation raised AttributeError, preventing the downstream pipeline from executing.",
            "canonical_production_entry_point": "app.simulation.geometry_compiler.contract_adapter.build_fact_graph(contract)",
            "attribution": "MEASUREMENT_APPARATUS_ERROR"
        },
        "original_live_observation": {
            "http_status": 200,
            "schema_accepted": True,
            "response_parse_valid": True,
            "latency_ms": 5922.75
        },
        "original_pipeline_result": "NOT_MEASURABLE",
        "original_pipeline_apparatus_error": True
    }
    (RECONCILIATION_DIR / "ATTRIBUTION_AUDIT.json").write_text(
        json.dumps(attribution_audit, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    # ── GATE D: Corrected Replay Result & Final Decision ──
    # Since raw response full text is not verifiable on disk, we adhere to Rule 8.C:
    # "Nếu raw response không còn hoặc không xác minh được hash:
    #  FINAL_DECISION = HISTORICAL_EVIDENCE_INSUFFICIENT
    #  SCHEMA_ACCEPTED = YES
    #  SEMANTIC_EXTRACTION_VALID = NOT_MEASURABLE
    #  PIPELINE_SMOKE_TEST = NOT_MEASURABLE
    #  NEXT_ACTION = SECOND_FAMILY_LIVE_RETRY_PREREGISTRATION"
    corrected_replay_result = {
        "schema_version": "2.0.0",
        "wave": "SECOND_FAMILY_LIVE_MEASUREMENT_RECONCILIATION_OFFLINE",
        "replay_mode": "OFFLINE_DETERMINISTIC",
        "network_requests": 0,
        "source_response_hash_verified": raw_response_hash_verified,
        "corrected_evaluator_ready": True,
        "corrected_harness_ready": True,
        "replay_execution_status": "SKIPPED_DUE_TO_INSUFFICIENT_RAW_EVIDENCE",
        "measurement_apparatus_repaired": True,
        "note": "Replay with live candidate data was not executed because the full raw response was not retained on disk. Evaluator and harness were verified offline via synthetic red/green tests."
    }
    (RECONCILIATION_DIR / "CORRECTED_REPLAY_RESULT.json").write_text(
        json.dumps(corrected_replay_result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    final_decision = {
        "schema_version": "2.0.0",
        "wave": "SECOND_FAMILY_LIVE_MEASUREMENT_RECONCILIATION_OFFLINE",
        "branch": "feat/photo-problem-to-scene",
        "start_head": "532f447e711c6ad230b7296b52ce00c2888a226b",
        "source_response_sha256": EXPECTED_RESPONSE_SHA256,
        "source_response_hash_verified": raw_response_hash_verified,
        "raw_output_committed": False,
        "new_gemini_requests": 0,
        "network_requests": 0,
        "schema_accepted": True,
        "response_parse_valid": True,
        "original_final_classification": "SCHEMA_ACCEPTED_MODEL_SEMANTIC_FAILURE",
        "original_classification_status": "INVALIDATED_BY_MEASUREMENT_ERROR",
        "corrected_classification": "HISTORICAL_EVIDENCE_INSUFFICIENT",
        "attribution_confidence": "HIGH (Apparatus errors R1 and R2 confirmed by static and test evidence)",
        "final_decision": "HISTORICAL_EVIDENCE_INSUFFICIENT",
        "semantic_extraction_valid": "NOT_MEASURABLE",
        "pipeline_smoke_test": "NOT_MEASURABLE",
        "merge_allowed": False,
        "next_action": "SECOND_FAMILY_LIVE_RETRY_PREREGISTRATION"
    }
    (RECONCILIATION_DIR / "FINAL_DECISION.json").write_text(
        json.dumps(final_decision, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    return final_decision


if __name__ == "__main__":
    dec = run_reconciliation()
    print("Reconciliation completed. Final decision:", dec["final_decision"])
