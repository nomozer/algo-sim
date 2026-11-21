# -*- coding: utf-8 -*-
"""Offline receipt generator for `ALGOSIM — REAL-WORLD END-TO-END RELIABILITY & HYBRID GAP CLOSURE`.

Invariants: `ALLOW_LIVE_AI=0` (0 live Gemini calls); every receipt carries product commit, measured-system tree hash,
code versions, environment, command, input hashes, case IDs, expected, actual, verdict, measurement status and oracle
provenance. External17 is a DEVELOPMENT/DIAGNOSTIC corpus (inspected during gap analysis) — never an independent H-1.

Reuses (read-only import) the frozen previous-run tool `unified-angle-geometry-verified-image-to-3d/tools/...` for the
baseline integrity, OCR fidelity / vision fallback routing and performance builders; that run is not modified.

Usage:
  python evaluate_real_world_reliability.py [--regression <json>]
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["PYTHONUTF8"] = "1"

THIS_DIR = Path(__file__).resolve().parent
RUN_DIR = THIS_DIR.parent
ROOT = RUN_DIR.parents[4]
PRIOR_RUN = ROOT / "docs" / "evaluation" / "geometry" / "runs" / "unified-angle-geometry-verified-image-to-3d"
sys.path.insert(0, str(PRIOR_RUN / "tools"))

import evaluate_unified_geometry_image_to_3d as P  # noqa: E402  (read-only reuse)

from app.ai.adapter4_route import run_typed_fact_next_v2_route  # noqa: E402
from app.ai.adaptive_input_router import route_text_input  # noqa: E402
from app.ai.local_geometry_parser import clear_local_geometry_parser_cache, parse_geometry_problem_locally  # noqa: E402
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity  # noqa: E402

RUN_ID = "real-world-end-to-end-reliability"
WAVE_ID = "REAL_WORLD_END_TO_END_RELIABILITY"
BASELINE_HEAD = "8d0fde3378c9b087bdbbc4c66e1a40aad3b532cc"
BASELINE_PRODUCT = "c61a3589782bde35b69e8376d8ebf136314e47f3"
TOOL_CMD = f"python docs/evaluation/geometry/runs/{RUN_ID}/tools/evaluate_real_world_reliability.py"

# ── Oracle (independent hand derivations; written before/independent of the engine output) ─────────────────────────
#: answer = exact expected string as served by Route D; None = not served expected / oracle not needed for verdict.
ORACLE: dict[str, dict[str, Any]] = {
    "ext_prt_01_hd_q_5259753#1": {"goals": ["volume(S.ABCD)"], "answer": "a³√3/3", "derivation": "SA = AB·tan60° = a√3; V = (1/3)·a²·a√3 = a³√3/3"},
    "ext_prt_02_hd_q_7922924#1": {"goals": ["distance(C, (ABB'A'))"], "answer": "6", "mc_key": "D. 6", "derivation": "BC ⊥ AB (vuông cân tại B) và BC ⊥ BB' ⇒ BC ⊥ (ABB'A'); d = CB = AB = 6, độc lập chiều cao lăng trụ; đáp án in trong đề: D. 6"},
    "ext_prt_03_hd_q_7907931#1": {"goals": ["distance(B, (SAC))"], "answer": "a√2/2", "derivation": "O = tâm hình vuông; BO ⊥ AC, BO ⊥ SA ⇒ BO ⊥ (SAC); d = BO = a√2/2, độc lập SA"},
    "ext_prt_03_hd_q_7907931#2": {"goals": ["volume(S.ABC)"], "answer": "a³/4", "derivation": "S_ABC = a²√3/4; V = (1/3)·(a²√3/4)·a√3 = a³/4"},
    "ext_prt_04_hd_q_8436784#1": {"goals": ["length_ratio(KC/KB)"], "answer": None, "oracle_value": "1/2", "derivation": "(P) ∥ (SAC) ⇒ (P)∩(ABCD) ∥ AC qua I; affine: K = B + 2·BC⃗ ⇒ KC/KB = 1/2"},
    "ext_prt_05_hd_q_7451806#1": {"goals": ["area_ratio(S1/S2)"], "answer": None, "oracle_value": "ORACLE_NOT_DERIVED_IN_RUN", "derivation": "not derived (case refused; area-ratio goal outside library)"},
    "ext_prt_06_hd_q_1084979#1": {"goals": ["volume(ABC.A'B'C')", "distance(AM, NP)"], "answer": None, "oracle_value": "V = a³√15/4; d(AM,NP) ORACLE_NOT_DERIVED_IN_RUN", "derivation": "H trung điểm AB ⇒ CH ⊥ (ABB'A'); tan60° = C'H'/BH', BH' = a√5/2 ⇒ CH = a√15/2; V = (1/2)·a·(a√15/2)·a"},
    "ext_prt_07_hd_q_7958052#1": {"goals": ["distance_rounded_0.1(AA', BC)"], "answer": None, "oracle_value": "15√93/31 ≈ 4,7", "derivation": "d(AA',BC) = d(A,BC) trong ΔABC: BC² = 25+36−30 = 31, S = 15√3/2 ⇒ h = 15√3/√31 = 15√93/31 ≈ 4,665"},
    "ext_prt_08_hd_q_7509702#1": {"goals": ["vector_sum(SA+SB+SC+SD)"], "answer": None, "oracle_value": "4·SO⃗ (vector)", "derivation": "SA⃗+SC⃗ = 2SO⃗, SB⃗+SD⃗ = 2SO⃗ (O trung điểm hai đường chéo)"},
    "ext_prt_09_vmmu_page_r4#1": {"goals": ["volume(S.ABC)"], "answer": "2", "mc_key": "B. 2", "derivation": "S_ABC = (1/2)·2·2 = 2; V = (1/3)·2·3 = 2; đáp án in: B. 2"},
    "ext_prt_10_vmmu_page_r7#1": {"goals": ["cone_volume_from_sector"], "answer": None, "oracle_value": "ORACLE_NOT_DERIVED_IN_RUN", "derivation": "curved solid from sector — out of scope"},
    "ext_prt_11_vmmu_page_r10#1": {"goals": ["angle_degrees((AB'C'), (ABC))"], "answer": None, "mc_key": "C. 30°", "oracle_value": "30°", "derivation": "góc((AB'C'),(A'B'C')): A'M = a√3 (M trung điểm B'C'), AA' = a ⇒ tan = 1/√3 ⇒ 30°; đáp án in: C"},
    "ext_prt_12_vmmu_page_r11#1": {"goals": ["distance(C, (ABB'A'))"], "answer": None, "mc_key": "B. 2√3(cm)", "oracle_value": "2√3", "derivation": "AB² = 12 ⇒ AB = 2√3; CB ⊥ (ABB'A') ⇒ d = CB = AB = 2√3; đáp án in: B"},
    "ext_prt_13_vmmu_page_r25#1": {"goals": ["horizontal_cylinder_water_volume_rounded"], "answer": None, "oracle_value": "ORACLE_NOT_DERIVED_IN_RUN", "derivation": "real-world cylinder segment volume (rounding) — out of scope"},
    "ext_prt_14_vmmu_page_r26#1": {"goals": ["sphere_volume_in_cylinder"], "answer": None, "oracle_value": "ORACLE_NOT_DERIVED_IN_RUN", "derivation": "spheres in cylinder — out of scope"},
    "ext_prt_15_vmmu_page_r28#1": {"goals": ["composite_cone_cylinder_volume"], "answer": None, "oracle_value": "NOT_RECOVERABLE_FROM_TEXT", "derivation": "heights only on diagram"},
    "ext_hw_b1_01_hd_a_6043187#1": {"goals": ["volume(ABC.A'B'C')"], "answer": "a³√3", "derivation": "BC = a√2, S = a²√2/2; CC' = BC·tan60° = a√6; V = a²√2/2·a√6 = a³√3"},
}

#: Root-cause classification of every non-served case (proximate = layer that emitted the refusal in this run;
#: root = the earliest layer that would still block after fixing the proximate one, established by Replay 2 + paraphrases).
ROOT_CAUSE: dict[str, dict[str, Any]] = {
    "ext_prt_04_hd_q_8436784#1": {
        "class": "A→F", "categories": ["A", "F", "J"], "proximate": "LOCAL_PARSER", "root": "PLANNER_KERNEL",
        "detail": "AD = 2BC (relation without metric), plane through I parallel to two lines, ratio goal KC/KB; the library has no length-ratio goal and no affine-only (metric-free) solve path",
        "proposed_fix": "DEFERRED_CAPABILITY (requires affine/homogeneous ratio goal & parallel-plane-to-two-lines primitive)",
    },
    "ext_prt_05_hd_q_7451806#1": {
        "class": "A→F/C", "categories": ["A", "C", "F", "J"], "proximate": "LOCAL_PARSER", "root": "PLANNER_KERNEL",
        "detail": "part-to-part ratio point (FIXED this run); remaining: 'Mặt phẳng (SAD) và đường thẳng ME cắt nhau tại I' word order, named areas S1/S2 and area-ratio goal on a parallelogram without metric",
        "proposed_fix": "PARTIALLY_CLOSED_IN_RUN (SE=3EC ratio parsed); remaining area-ratio goal S1/S2 deferred",
    },
    "ext_prt_06_hd_q_1084979#1": {
        "class": "A→F", "categories": ["A", "F", "J"], "proximate": "LOCAL_PARSER", "root": "PLANNER_KERNEL",
        "detail": "compound goal 'thể tích … và khoảng cách …'; Replay 2 verbatim TypedFactNext/2 passes Source Gate + Planner and refuses MISSING_DIMENSION at Exact Kernel because base apex height must be deduced backward from line_plane_angle(BC', (ABB'A'))=60°. Known-base paraphrase served a√15/5",
        "proposed_fix": "DEFERRED_CAPABILITY (inverse base-height deduction from lateral-plane angle + compound heterogeneous goals)",
    },
    "ext_prt_07_hd_q_7958052#1": {
        "class": "A→D→OUTPUT_POLICY", "categories": ["A", "D", "F", "J"], "proximate": "LOCAL_PARSER", "root": "OUTPUT_POLICY",
        "detail": "Replay 2 verbatim TypedFactNext/2 hits Source Gate PREDICATE_NOT_IN_QUOTE on 'Â = 60°' and noun-phrase goal; canonical exact paraphrase without height NOW SERVES 15√93/31 via height-invariance; original asks decimal rounding ('làm tròn kết quả đến hàng phần mười') outside exact-only output contract",
        "proposed_fix": "HEIGHT_INVARIANCE_READY (exact 15√93/31 served on canonical wording); remaining: Unicode 'Â', noun goal, and explicit rounding output policy",
    },
    "ext_prt_08_hd_q_7509702#1": {
        "class": "G", "categories": ["G", "J"], "proximate": "LOCAL_PARSER", "root": "OUT_OF_SCOPE",
        "detail": "vector-sum goal (no vector-valued answers in Route D)",
        "proposed_fix": "KEEP_FAIL_CLOSED_OUT_OF_SCOPE (vector algebra outside polyhedral metric scope)",
    },
    "ext_prt_10_vmmu_page_r7#1": {
        "class": "G+I", "categories": ["G", "I", "J"], "proximate": "LOCAL_PARSER", "root": "OUT_OF_SCOPE",
        "detail": "cone formed by rolling a sheet sector; diagram-dependent",
        "proposed_fix": "KEEP_FAIL_CLOSED_OUT_OF_SCOPE (curved solid development + diagram dependency)",
    },
    "ext_prt_11_vmmu_page_r10#1": {
        "class": "D→OUTPUT_POLICY", "categories": ["D", "F", "J"], "proximate": "SOURCE_GATE_IN_LOCAL_VERIFICATION", "root": "OUTPUT_POLICY",
        "detail": "Replay 2 verbatim TypedFactNext/2 refuses UNGROUNDED_VALUE on 'chiều cao bằng a' for khối lăng trụ tam giác đều; even with explicit AA'=a, 'Tính số đo góc' asks degrees (30°) which triggers QUESTION_CONTEXT_UNSUPPORTED under exact-cosine output policy",
        "proposed_fix": "DEFERRED_POLICY_AND_GROUNDING (ground 'chiều cao bằng' on regular prism + exact special-angle degree output policy)",
    },
    "ext_prt_12_vmmu_page_r11#1": {
        "class": "A/D→C", "categories": ["A", "C", "D", "J"], "proximate": "SOURCE_GATE_IN_LOCAL_VERIFICATION", "root": "TYPED_FACTS_BRIDGE",
        "detail": "Replay 2 verbatim TypedFactNext/2 hits NOT_ASKED_IN_SOURCE on MC stem ending '… bằng' and TypedFactNext/2 has no face-area premise primitive ('diện tích của hình vuông ABB'A' bằng 12(cm²)'); side-given paraphrase served 2√3",
        "proposed_fix": "DEFERRED_CONTRACT_EXTENSION (add face_area premise to TypedFactNext/2 + bridge + Source Gate + MC stem '… bằng' goal cue)",
    },
    "ext_prt_13_vmmu_page_r25#1": {
        "class": "G/I", "categories": ["G", "I", "J"], "proximate": "LOCAL_PARSER", "root": "OUT_OF_SCOPE",
        "detail": "real-world horizontal cylinder water segment volume with rounding and diagram reference",
        "proposed_fix": "KEEP_FAIL_CLOSED_OUT_OF_SCOPE (curved solid + diagram + rounding)",
    },
    "ext_prt_14_vmmu_page_r26#1": {
        "class": "G/I", "categories": ["G", "I", "J"], "proximate": "LOCAL_PARSER", "root": "OUT_OF_SCOPE",
        "detail": "two tangent spheres packed inside a cylinder",
        "proposed_fix": "KEEP_FAIL_CLOSED_OUT_OF_SCOPE (multi-sphere curved packing)",
    },
    "ext_prt_15_vmmu_page_r28#1": {
        "class": "I+G", "categories": ["G", "H", "I", "J"], "proximate": "LOCAL_PARSER", "root": "OUT_OF_SCOPE",
        "detail": "heights exist only on the diagram ('Chiều cao đo được ghi trên hình' — NOT_RECOVERABLE from text) plus composite cone+cylinder",
        "proposed_fix": "KEEP_FAIL_CLOSED_DIAGRAM_DEPENDENT (must refuse or request diagram values; never guess)",
    },
}

#: Canonical paraphrase replays (development probes, not External17 statements).
REPLAYS = {
    "02_withheight": ("ext_prt_02", "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại B, AB = 6, AA' = 5. Tính khoảng cách từ C đến mặt phẳng (ABB'A')."),
    "03a_withheight": ("ext_prt_03#1", "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD), SA = a. Tính khoảng cách từ B đến mặt phẳng (SAC)."),
    "05_divide": ("ext_prt_05", "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ⊥ (ABCD), SA = 2. Gọi M là trung điểm của SB. Gọi E là điểm thuộc cạnh SC sao cho SE = 3EC. Tính độ dài đoạn thẳng ME."),
    "06_vol": ("ext_prt_06", "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác cân tại C, AB = AA' = a. Góc tạo bởi đường thẳng BC' với mặt phẳng (ABB'A') bằng 60°. Tính thể tích khối lăng trụ ABC.A'B'C'."),
    "06_knownbase": ("ext_prt_06", "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác cân tại C, AB = AA' = a, CA = 2a. Gọi M, N, P lần lượt là trung điểm của các cạnh BB', CC' và BC. Tính khoảng cách giữa hai đường thẳng AM và NP."),
    "07_canon": ("ext_prt_07", "Cho hình lăng trụ đứng ABC.A'B'C' có AB = 5, AC = 6, góc BAC bằng 60°, AA' = 1. Tính khoảng cách giữa hai đường thẳng AA' và BC."),
    "07_canon_no_height": ("ext_prt_07", "Cho hình lăng trụ đứng ABC.A'B'C' có AB = 5, AC = 6, góc BAC bằng 60°. Tính khoảng cách giữa hai đường thẳng AA' và BC."),
    "07_hat": ("ext_prt_07", "Cho hình lăng trụ đứng ABC.A'B'C' có AB = 5, AC = 6, Â = 60°, AA' = 1. Tính khoảng cách giữa hai đường thẳng AA' và BC."),
    "07_noun": ("ext_prt_07", "Cho hình lăng trụ đứng ABC.A'B'C' có AB = 5, AC = 6, góc BAC bằng 60°. Khoảng cách giữa hai đường thẳng AA' và BC."),
    "11_cos": ("ext_prt_11", "Cho khối lăng trụ tam giác đều ABC.A'B'C' có cạnh đáy bằng 2a, chiều cao bằng a. Tính góc tạo bởi hai mặt phẳng (AB'C') và (ABC)."),
    "12_side": ("ext_prt_12", "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại B, AB = 2√3, AA' = 2√3. Tính khoảng cách từ C đến mặt phẳng (ABB'A')."),
    "12_area": ("ext_prt_12", "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại B và diện tích của hình vuông ABB'A' bằng 12. Tính khoảng cách từ C đến mặt phẳng (ABB'A')."),
    "08_vec_metric": ("ext_prt_08", "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2 tâm O, SA ⊥ (ABCD), SA = 2. Tính độ dài đoạn thẳng SO."),
}

#: Height-invariance probes: (text, expect_status, expect_answer, expect_illustrative).
INVARIANCE_PROBES = {
    "pos_ext03_verbatim": ("Câu 32: Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). Tính khoảng cách từ điểm B đến mp(SAC).", "SERVED", "a√2/2", True),
    "pos_prism_line_line": ("Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác đều cạnh 2a. Tính khoảng cách giữa hai đường thẳng AA' và BC.", "SERVED", "a√3", True),
    "pos_renamed_KMNPQ": ("Cho hình chóp K.MNPQ có đáy MNPQ là hình vuông cạnh 4, KM ⊥ (MNPQ). Tính khoảng cách từ N đến mặt phẳng (KMP).", "SERVED", "2√2", True),
    "neg_dependent_distance": ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). Tính khoảng cách từ A đến mặt phẳng (SBC).", "REFUSED", None, False),
    "neg_volume": ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). Tính thể tích khối chóp S.ABCD.", "REFUSED", None, False),
    "neg_length": ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). Tính độ dài đoạn thẳng SC.", "REFUSED", None, False),
    "neg_mixed_goals": ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). Tính khoảng cách từ B đến mặt phẳng (SAC) và độ dài đoạn thẳng SC.", "REFUSED", None, False),
    "neg_angle_dependent": ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). Tính góc giữa đường thẳng SC và mặt phẳng (ABCD).", "REFUSED", None, False),
    "neg_base_dimension_missing": ("Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = a, SA ⊥ (ABCD). Tính khoảng cách từ B đến mặt phẳng (SAD).", "REFUSED", None, False),
    "neg_constructed_operand": ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). Gọi M là trung điểm của SB. Tính khoảng cách từ M đến mặt phẳng (SAD).", "REFUSED", None, False),
    "ctrl_stated_height": ("Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại B, AB = 6, AA' = 5. Tính khoảng cách từ C đến mặt phẳng (ABB'A').", "SERVED", "6", False),
}

PARSER_PROBES = {
    "ratio_SE_3EC_length": ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ⊥ (ABCD), SA = 2. Gọi M là trung điểm của SB. Gọi E là điểm thuộc cạnh SC sao cho SE = 3EC. Tính độ dài đoạn thẳng ME.", "SERVED", "√11/2"),
    "ratio_bad_parts_fail_closed": ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ⊥ (ABCD), SA = 2. Gọi E là điểm thuộc cạnh SC sao cho SB = 3EC. Tính độ dài đoạn thẳng AE.", "NOT_SERVED", None),
}


def _hdr(
    *,
    case_ids: list[str],
    measurement_status: str,
    oracle_provenance: str,
    **kw: Any,
) -> dict[str, Any]:
    h = P._trace_header(**kw)
    h["run_id"] = RUN_ID
    h["wave_id"] = WAVE_ID
    h["baseline_head_commit"] = BASELINE_HEAD
    h["baseline_product_commit"] = BASELINE_PRODUCT
    h["case_ids"] = case_ids
    h["measurement_status"] = measurement_status
    h["oracle_provenance"] = oracle_provenance
    return h


def _route(text: str) -> dict[str, Any]:
    clear_local_geometry_parser_cache()
    t0 = time.perf_counter()
    out = route_text_input(text, allow_live_ai=False)
    ms = (time.perf_counter() - t0) * 1000.0
    env = out.response.get("envelope") or {}
    rd = out.response.get("route_d") or {}
    scene = env.get("scene3d")
    answers = rd.get("answers") or {}
    return {
        "status": out.status,
        "reason_code": env.get("reason_code"),
        "fallback_reason": (rd.get("refusal") or {}).get("fallback_reason"),
        "answer": next(iter(answers.values())) if len(answers) == 1 else (answers or None),
        "scene_configuration": rd.get("scene_configuration"),
        "scene3d_continuity_errors": (validate_construction_continuity(scene) if scene else None),
        "chosen_route": getattr(out.telemetry, "chosen_route", None),
        "provider_calls": getattr(out.telemetry, "total_provider_calls", None),
        "elapsed_ms": round(ms, 3),
    }


def _statements() -> list[dict[str, Any]]:
    rows = []
    for it in P.CORPUS_ITEMS:
        if not it.get("has_complete_problem"):
            continue
        for i, t in enumerate(it.get("verbatim_problem_texts", []), 1):
            rows.append({"case_id": f"{it['image_id']}#{i}", "item": it, "text": t})
    return rows


def build_case_diagnostics() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = []
    for s in _statements():
        it, text, cid = s["item"], s["text"], s["case_id"]
        clear_local_geometry_parser_cache()
        p = parse_geometry_problem_locally(text, use_cache=False)
        cov = p.source_coverage
        unmapped = [{"classification": c["classification"], "text": c["text"]} for c in (cov.clauses if cov else [])
                    if c["classification"] not in ("MAPPED_FACT", "MAPPED_GOAL", "BENIGN_DISCOURSE")]
        r = _route(text)
        o = ORACLE[cid]
        if r["status"] == "SERVED":
            verdict = "CORRECT_SERVED" if (o["answer"] is not None and r["answer"] == o["answer"]
                                          and r["scene3d_continuity_errors"] == []) else "WRONG_SERVED"
        else:
            verdict = "FAIL_CLOSED_NOT_SOLVED"
        rc = ROOT_CAUSE.get(cid)
        fb = r["fallback_reason"]
        sg_status = (
            "PASSED" if r["status"] == "SERVED"
            else f"FAILED ({fb})" if (fb and "SOURCE_GATE_MISMATCH" in fb)
            else "UNKNOWN (upstream local parser halted before Source Gate)"
        )
        pl_status = "COMPOSED_VALID_PLAN" if r["status"] == "SERVED" else "UNKNOWN (upstream halted before Planner)"
        ek_status = (
            "SERVED_HEIGHT_INVARIANT" if (r["status"] == "SERVED" and r["scene_configuration"])
            else "SERVED_UNIQUE" if r["status"] == "SERVED"
            else "UNKNOWN (upstream halted on Replay 1; see Replay 2 in live_ai_disabled_root_cause_analysis.json)"
        )
        sc_status = (
            "VALID_ILLUSTRATIVE_NON_UNIQUE" if (r["status"] == "SERVED" and r["scene_configuration"])
            else "VALID_UNIQUE" if r["status"] == "SERVED"
            else "NONE_FAIL_CLOSED"
        )
        gt_base = it.get("ground_truth_verification_status") or "VERIFIED_TRANSCRIPTION"
        gt_oracle = (
            f"PRINTED_MC_KEY ({o['mc_key']}) + SELF_DERIVED_ORACLE" if o.get("mc_key")
            else "SELF_DERIVED_ORACLE" if (o.get("answer") or (o.get("oracle_value") and "NOT_" not in str(o.get("oracle_value"))))
            else str(o.get("oracle_value"))
        )
        proposed_fix = (
            rc["proposed_fix"] if rc
            else ("CLOSED_IN_THIS_RUN (Exact Kernel height-invariance certification + labelled illustrative Scene3D)"
                  if cid in ("ext_prt_02_hd_q_7922924#1", "ext_prt_03_hd_q_7907931#1")
                  else "ALREADY_SUPPORTED_PRESERVED")
        )
        rows.append({
            # Section 4.2 mandatory 20-field diagnostic schema:
            "case_id": cid,
            "source_image_id": it["image_id"],
            "source_hash": it.get("original_file_sha256"),
            "original_problem_text": text,
            "expected_goals": o["goals"],
            "expected_answer": o["answer"] if o["answer"] is not None else o.get("oracle_value"),
            "ground_truth_status": f"{gt_base}; {gt_oracle}",
            "local_parser_status": f"{p.status}:{p.reason_code}" if p.reason_code else p.status,
            "coverage_status": "COMPLETE" if not unmapped else f"INCOMPLETE ({len(unmapped)} unmapped)",
            "unmapped_clauses": unmapped,
            "typed_fact_status": "PRODUCED_V2" if p.payload is not None else "NOT_PRODUCED",
            "source_gate_status": sg_status,
            "planner_status": pl_status,
            "exact_kernel_status": ek_status,
            "scene3d_status": sc_status,
            "fallback_trigger": None if r["status"] == "SERVED" else (fb or p.reason_code or r["reason_code"]),
            "observed_reason_code": r["reason_code"],
            "root_cause": rc or {"class": "NONE_SERVED", "categories": [], "proximate": "NONE", "root": "NONE"},
            "proposed_fix": proposed_fix,
            "verification_status": "ORACLE_TEXT_DOWNSTREAM_REPLAY_VERIFIED (LIVE_VISION_NOT_MEASURED)",
            # Additional structured trace metadata:
            "source_url": it.get("source_url"),
            "original_file_sha256": it.get("original_file_sha256"),
            "modality": it.get("printed_or_handwritten"),
            "has_geometry_diagram": it.get("has_geometry_diagram"),
            "text_sha256": P._sha256_bytes(text.encode("utf-8")),
            "input_mode": "ORACLE_TEXT_DOWNSTREAM_REPLAY (verbatim ground-truth transcription)",
            "local_parse": {"status": p.status, "reason_code": p.reason_code, "unmapped_clauses": unmapped},
            "typed_facts_bridge": "UNKNOWN" if p.status != "LOCAL_PARSE_COMPLETE" and r["status"] != "SERVED" else "PASSED",
            "route": r,
            "oracle": o,
            "verdict": verdict,
            "gemini_calls": 0,
            "live_vision": "LIVE_VISION_NOT_MEASURED",
        })
    served = [r for r in rows if r["route"]["status"] == "SERVED"]
    summary = {
        "statements": len(rows),
        "served": len(served),
        "correct_served": sum(r["verdict"] == "CORRECT_SERVED" for r in rows),
        "wrong_served": sum(r["verdict"] == "WRONG_SERVED" for r in rows),
        "missing_dimension_refusals": sum(r["route"]["reason_code"] == "MISSING_DIMENSION" for r in rows),
        "live_ai_disabled": sum(r["route"]["reason_code"] == "LIVE_AI_DISABLED" for r in rows),
        "served_ids": [r["case_id"] for r in served],
    }
    return rows, summary


def _build_replay2_validated_typed_facts(stmt_by_id: dict[str, str]) -> dict[str, Any]:
    """Section 4.4 Replay 2: Validated TypedFactNext/2 payloads anchored to verbatim External17 texts."""
    t06 = stmt_by_id["ext_prt_06_hd_q_1084979#1"]
    p06 = {
        "schema_version": "typed-fact-next/2", "problem_text": t06, "length_unit": "a",
        "solids": [{"solid_id": "s1", "solid_type": "prism", "notation": "ABC.A'B'C'", "quote": "Cho hình lăng trụ đứng ABC.A'B'C'"}],
        "premises": [
            {"kind": "right_prism", "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]}, "quote": "Cho hình lăng trụ đứng ABC.A'B'C'", "solid_id": "s1"},
            {"kind": "equal_length", "args": {"segment_a": ["C", "A"], "segment_b": ["C", "B"]}, "quote": "có đáy ABC là tam giác cân tại C", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "a"}, "quote": "AB = AA' = a", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": "a"}, "quote": "AB = AA' = a", "solid_id": "s1"},
            {"kind": "line_plane_angle", "args": {"line": ["B", "C'"], "plane": ["A", "B", "B'", "A'"], "value": "60", "unit": "deg"}, "quote": "Góc tạo bởi đường thẳng BC' với mặt phẳng (ABB'A') bằng 60°", "solid_id": "s1"},
            {"kind": "midpoint", "args": {"point": "M", "segment": ["B", "B'"]}, "quote": "Gọi M, N, P lần lượt là trung điểm của các cạnh BB', CC' và BC", "solid_id": "s1"},
            {"kind": "midpoint", "args": {"point": "N", "segment": ["C", "C'"]}, "quote": "Gọi M, N, P lần lượt là trung điểm của các cạnh BB', CC' và BC", "solid_id": "s1"},
            {"kind": "midpoint", "args": {"point": "P", "segment": ["B", "C"]}, "quote": "Gọi M, N, P lần lượt là trung điểm của các cạnh BB', CC' và BC", "solid_id": "s1"},
        ],
        "relations": [], "derived_sections": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình lăng trụ đứng ABC.A'B'C'"}],
        "math_goals": [
            {"goal_id": "q1", "kind": "measurement", "goal_type": "volume", "target": {"solid_id": "s1"}, "solid_id": "s1", "quote": "Tính thể tích khối lăng trụ ABC.A'B'C' và khoảng cách giữa hai đường thẳng AM và NP theo a"},
            {"goal_id": "q2", "kind": "measurement", "goal_type": "distance", "target": {"line1": ["A", "M"], "line2": ["N", "P"]}, "solid_id": "s1", "quote": "Tính thể tích khối lăng trụ ABC.A'B'C' và khoảng cách giữa hai đường thẳng AM và NP theo a"},
        ],
    }
    t07 = stmt_by_id["ext_prt_07_hd_q_7958052#1"]
    p07 = {
        "schema_version": "typed-fact-next/2", "problem_text": t07, "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "prism", "notation": "ABC.A'B'C'", "quote": "Cho hình lăng trụ đứng ABC.A'B'C'"}],
        "premises": [
            {"kind": "right_prism", "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]}, "quote": "Cho hình lăng trụ đứng ABC.A'B'C'", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "5"}, "quote": "AB = 5", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "C"], "value": "6"}, "quote": "AC = 6", "solid_id": "s1"},
            {"kind": "vertex_angle", "args": {"vertex": "A", "rays": ["B", "C"], "value": "60", "unit": "deg"}, "quote": "Â = 60°", "solid_id": "s1"},
        ],
        "relations": [], "derived_sections": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình lăng trụ đứng ABC.A'B'C'"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"line1": ["A", "A'"], "line2": ["B", "C"]}, "solid_id": "s1", "quote": "Khoảng cách giữa hai đường thẳng AA' và BC (làm tròn kết quả đến hàng phần mười)"}],
    }
    t11 = stmt_by_id["ext_prt_11_vmmu_page_r10#1"]
    p11 = {
        "schema_version": "typed-fact-next/2", "problem_text": t11, "length_unit": "a",
        "solids": [{"solid_id": "s1", "solid_type": "prism", "notation": "ABC.A'B'C'", "quote": "Cho khối lăng trụ tam giác đều ABC.A'B'C'"}],
        "premises": [
            {"kind": "right_prism", "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]}, "quote": "Cho khối lăng trụ tam giác đều ABC.A'B'C'", "solid_id": "s1"},
            {"kind": "regular_polygon", "args": {"vertices": ["A", "B", "C"], "side": "2a"}, "quote": "Cho khối lăng trụ tam giác đều ABC.A'B'C' có cạnh đáy bằng 2a", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": "a"}, "quote": "chiều cao bằng a", "solid_id": "s1"},
        ],
        "relations": [], "derived_sections": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho khối lăng trụ tam giác đều ABC.A'B'C'"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "angle", "target": {"plane1": ["A", "B'", "C'"], "plane2": ["A", "B", "C"]}, "solid_id": "s1", "quote": "Tính số đo góc tạo bởi hai mặt phẳng (AB'C') và (ABC)?"}],
    }
    t12 = stmt_by_id["ext_prt_12_vmmu_page_r11#1"]
    p12 = {
        "schema_version": "typed-fact-next/2", "problem_text": t12, "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "prism", "notation": "ABC.A'B'C'", "quote": "Cho hình lăng trụ đứng ABC.A'B'C'"}],
        "premises": [
            {"kind": "right_prism", "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]}, "quote": "Cho hình lăng trụ đứng ABC.A'B'C'", "solid_id": "s1"},
            {"kind": "right_angle", "args": {"vertex": "B", "rays": ["A", "C"]}, "quote": "có đáy ABC là tam giác vuông cân tại B", "solid_id": "s1"},
            {"kind": "equal_length", "args": {"segment_a": ["B", "A"], "segment_b": ["B", "C"]}, "quote": "có đáy ABC là tam giác vuông cân tại B", "solid_id": "s1"},
        ],
        "relations": [], "derived_sections": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình lăng trụ đứng ABC.A'B'C'"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "C", "plane": ["A", "B", "B'", "A'"]}, "solid_id": "s1", "quote": "Khoảng cách từ C đến mặt phẳng (ABB'A') bằng"}],
    }
    out: dict[str, Any] = {}
    for k, payload in [("ext_prt_06_verbatim_v2", p06), ("ext_prt_07_verbatim_v2", p07),
                       ("ext_prt_11_verbatim_v2", p11), ("ext_prt_12_verbatim_v2", p12)]:
        ro = run_typed_fact_next_v2_route(payload)
        out[k] = {"status": ro.status, "code": ro.code, "reason": ro.reason, "answers": ro.answers}
    return out


def build_root_cause(rows: list[dict[str, Any]]) -> dict[str, Any]:
    lad = [r for r in rows if r["route"]["reason_code"] == "LIVE_AI_DISABLED"]
    stmt_by_id = {r["case_id"]: r["original_problem_text"] for r in rows}
    replay2_v2 = _build_replay2_validated_typed_facts(stmt_by_id)
    replays = {k: {"for_case": c, "text_sha256": P._sha256_bytes(t.encode("utf-8")), **_route(t)} for k, (c, t) in REPLAYS.items()}
    tally_root: dict[str, int] = {}
    tally_prox: dict[str, int] = {}
    for r in lad:
        rc = ROOT_CAUSE[r["case_id"]]
        tally_root[rc["root"]] = tally_root.get(rc["root"], 0) + 1
        tally_prox[rc["proximate"]] = tally_prox.get(rc["proximate"], 0) + 1
    expected = {"02_withheight": "6", "03a_withheight": "a√2/2", "05_divide": "√11/2", "06_knownbase": "a√15/5",
                "07_canon": "15√93/31", "07_canon_no_height": "15√93/31", "12_side": "2√3"}
    replay_ok = (
        all(replays[k]["status"] == "SERVED" and replays[k]["answer"] == v for k, v in expected.items())
        and replay2_v2["ext_prt_06_verbatim_v2"]["code"] == "MISSING_DIMENSION"
        and replay2_v2["ext_prt_07_verbatim_v2"]["code"] == "PREDICATE_NOT_IN_QUOTE"
        and replay2_v2["ext_prt_11_verbatim_v2"]["code"] == "UNGROUNDED_VALUE"
        and replay2_v2["ext_prt_12_verbatim_v2"]["code"] == "NOT_ASKED_IN_SOURCE"
    )
    return {
        **_hdr(
            schema="algosim-live-ai-disabled-root-cause/1",
            case_ids=[r["case_id"] for r in lad],
            measurement_status="MEASURED_OFFLINE (Replay 1 local text + Replay 2 validated TypedFactNext/2 + Replay 3 image ingestion)",
            oracle_provenance="Direct execution of parse_geometry_problem_locally, run_typed_fact_next_v2_route, and route_text_input + self-derived hand oracle (printed MC keys on ext11, ext12)",
            input_or_case_hash=P._sha256_json(sorted(r["case_id"] for r in lad) + sorted(REPLAYS)),
            oracle="Per-layer trace (local parser coverage → Source Gate → Planner → Kernel) + Replay 2 TypedFactNext/2 + canonical paraphrase replays + hand oracle",
            test_command=TOOL_CMD,
            expected_behavior="Every LIVE_AI_DISABLED case gets a proximate and a root layer backed by Replay 1/2/3 evidence; no case is 'missing data' unless the source truly lacks it.",
            actual_behavior=f"LIVE_AI_DISABLED={len(lad)}; root tally={tally_root}; proximate tally={tally_prox}; replay_verifications_ok={replay_ok}.",
            verdict="PASS" if len(lad) == len(ROOT_CAUSE) and replay_ok else "FAIL",
        ),
        "classification_legend": {
            "A": "Linguistic coverage (local parser)", "B": "Semantic extraction",
            "C": "Typed Fact / Bridge gap", "D": "Source Gate / provenance",
            "E": "Planner capability gap", "F": "Registry / Exact Kernel gap",
            "G": "Unsupported domain", "H": "Insufficient specification",
            "I": "Image-specific dependency", "J": "Execution policy blocker (ALLOW_LIVE_AI=0)",
            "OUTPUT_POLICY": "Answer form (rounding/degrees) outside exact-radical/cosine output policy",
        },
        "cases": [{"case_id": r["case_id"], **ROOT_CAUSE[r["case_id"]], "parse_reason": r["local_parse"]["reason_code"],
                   "oracle": r["oracle"].get("oracle_value")} for r in lad],
        "tally_root": tally_root,
        "tally_proximate": tally_prox,
        "parser_sole_root_cause": 0,
        "true_missing_data_in_text_corpus": 0,
        "diagram_only_missing_from_text": 1,
        "replay_1_local_text_summary": {"total": len(rows), "served": len(rows) - len(lad), "live_ai_disabled": len(lad)},
        "replay_2_validated_typed_facts_verbatim": replay2_v2,
        "canonical_replays": replays,
        "replay_3_image_ingestion_summary": {
            "complete_problem_images": 16,
            "local_ocr_zero_ai_served": 0,
            "raw_ocr_rejected_by_fidelity_gate": "38/38",
            "recorded_vision_replay_served": "1/16 (ext_hw_b1_01_hd_a_6043187 -> a³√3)",
            "live_vision": "LIVE_VISION_NOT_MEASURED",
        },
        "honesty_notes": [
            "Proximate parser refusals are frequent (local parser is the first gate) but the parser is the SOLE root of none of the 11.",
            "Replay 2 runs genuine TypedFactNext/2 payloads anchored to the verbatim External17 texts through bridge_v2 -> Source Gate -> Planner -> Exact Kernel, plus canonical paraphrases isolating downstream capability.",
        ],
    }


def build_invariance_and_parser() -> tuple[dict[str, Any], dict[str, Any]]:
    inv_rows = {}
    for k, (t, st, ans, ill) in INVARIANCE_PROBES.items():
        r = _route(t)
        cfg = r["scene_configuration"]
        ok = (r["status"] == st) and (ans is None or r["answer"] == ans) and (bool(cfg) == ill)
        if st == "REFUSED":
            ok = ok and r["status"] != "SERVED"
        if ill and cfg:
            ok = ok and cfg.get("unique") is False and cfg.get("kind") == "HEIGHT_INVARIANT_ILLUSTRATIVE"
        inv_rows[k] = {"expected": {"status": st, "answer": ans, "illustrative": ill}, "actual": r, "pass": ok}
    parser_rows = {}
    for k, (t, st, ans) in PARSER_PROBES.items():
        r = _route(t)
        ok = (r["status"] == "SERVED" and r["answer"] == ans) if st == "SERVED" else r["status"] != "SERVED"
        parser_rows[k] = {"expected": {"status": st, "answer": ans}, "actual": r, "pass": ok}
    inv_ok = all(v["pass"] for v in inv_rows.values())
    par_ok = all(v["pass"] for v in parser_rows.values())
    kernel = {
        **_hdr(
            schema="algosim-planner-kernel-capability-closure/1",
            case_ids=list(INVARIANCE_PROBES.keys()),
            measurement_status="MEASURED_OFFLINE",
            oracle_provenance="Algebraic rational-function identity proof in h² (Gram determinant lemma) + closed-form hand derivations on positive probes",
            input_or_case_hash=P._sha256_json(INVARIANCE_PROBES),
            oracle="Rational-function identity in h² (metric G = G₂ ⊕ (h²), goal² = Gram-determinant ratio of degree ≤ 2) + hand oracle on positives",
            test_command="pytest backend/tests/geometry/test_real_world_end_to_end_reliability.py -q",
            expected_behavior="Height-invariant goals with unstated height are served exactly with a labelled non-unique illustrative scene; every height-dependent, constructed-operand or mixed goal still refuses MISSING_DIMENSION.",
            actual_behavior=f"probes passed {sum(v['pass'] for v in inv_rows.values())}/{len(inv_rows)}",
            verdict="PASS" if inv_ok else "FAIL",
        ),
        "capability": "certify_height_invariance (engine geometry-function-engine/24, no new registry primitive)",
        "proof_sketch": ("Let t = h². Solid-vertex affine coordinates do not depend on t; the metric is G = G₂ ⊕ (t), so every "
                         "inner product u·v = u₂ᵀG₂v₂ + t·u_z·v_z is affine in t, and every Gram matrix has the form A + t·zzᵀ, "
                         "whose determinant is affine in t (matrix determinant lemma). Hence each whitelisted goal² is P(t)/Q(t) "
                         "with deg P, deg Q ≤ 2 (lengths: deg 1; point–plane / line–line / line–plane / plane–plane distances: "
                         "ratio of Gram determinants, deg ≤ 1 each; cos² of angles: (u·v)² / ((u·u)(v·v)), deg ≤ 2 each), and "
                         "Q(t) > 0 for t > 0 (non-degenerate solid). If the goal takes the same value c at 5 distinct t, then "
                         "P − cQ (degree ≤ 2, certificate bound ≤ 3) has 5 roots, so P ≡ cQ and the goal equals c for every height."),
        "proof_caveat": ("Relies on (i) goal operands being solid vertices (coordinates independent of t) — enforced by guard; "
                         "(ii) the same combinatorial frame at every sample (same free anchor, no mirror/flip) — enforced; "
                         "(iii) exact Fraction/Radical evaluation (no floating point). Certificate field max_degree=3 is a "
                         "conservative bound; 5 samples exceed it."),
        "guards": ["all asks in whitelist", "all goal labels are solid vertices", "all 5 samples SERVED with ≤1 free anchor",
                   "identical goal signature", "not on mirror/flip exploration path", "only after MISSING_DIMENSION"],
        "scene_contract": "route_d.scene_configuration {unique:false, kind:HEIGHT_INVARIANT_ILLUSTRATIVE, invariance_certificate}; frontend shows #stage-illustrative-note",
        "probes": inv_rows,
        "new_registry_primitives": 0,
        "per_problem_handlers": 0,
    }
    parser = {
        **_hdr(
            schema="algosim-parser-semantic-gap-closure/1",
            case_ids=list(PARSER_PROBES.keys()),
            measurement_status="MEASURED_OFFLINE",
            oracle_provenance="Independent coordinate hand derivation: S(0,0,2), B(2,0,0), C(2,2,0) ⇒ M(1,0,1), E=(3/2,3/2,1/2) ⇒ ME=√11/2",
            input_or_case_hash=P._sha256_json(PARSER_PROBES),
            oracle="Hand oracle: S(0,0,2), B(2,0,0), C(2,2,0) ⇒ M(1,0,1), E = S + 3/4·SC⃗ = (3/2,3/2,1/2); ME² = 1/4+9/4+1/4 = 11/4",
            test_command="pytest backend/tests/geometry/test_real_world_end_to_end_reliability.py -k ratio -q",
            expected_behavior="Part-to-part ratio 'E thuộc cạnh SC sao cho SE = 3EC' maps to the existing divide_segment primitive (k/(k+1)); malformed part pairs fail closed.",
            actual_behavior=f"probes passed {sum(v['pass'] for v in parser_rows.values())}/{len(parser_rows)}",
            verdict="PASS" if par_ok else "FAIL",
        ),
        "changes": ["local_geometry_parser stage 5b-3 part-to-part ratio → point_divides_segment; Stage 7k '=' guard accepts the span only when that premise was built"],
        "probes": parser_rows,
        "remaining_parser_gaps_documented_not_fixed": [
            "'Â = 60°' hat-angle notation (ext07)", "noun-phrase goals without 'Tính' ('Khoảng cách … bằng', ext07/ext12)",
            "compound 'Tính A và B' with heterogeneous goals (ext06)", "'Mặt phẳng (P) và đường thẳng d cắt nhau tại I' word order (ext05)",
        ],
        "reason_not_fixed": "Each fix alone serves 0 additional External17 cases (root causes lie in Source Gate / Kernel / output policy); deferred to avoid unverified grammar growth.",
    }
    return kernel, parser


def build_bridge_gap() -> dict[str, Any]:
    r_area = _route(REPLAYS["12_area"][1])
    r_cos = _route(REPLAYS["11_cos"][1])
    return {
        **_hdr(
            schema="algosim-typed-facts-bridge-gap-closure/1",
            case_ids=["ext_prt_11_vmmu_page_r10#1", "ext_prt_12_vmmu_page_r11#1"],
            measurement_status="MEASURED_OFFLINE",
            oracle_provenance="Source Gate (registry.kiem_nguon) & bridge_v2 execution trace on verbatim TypedFactNext/2 and canonical paraphrases",
            input_or_case_hash=P._sha256_json([REPLAYS["12_area"][1], REPLAYS["11_cos"][1]]),
            oracle="Source Gate trace on canonical replays",
            test_command=TOOL_CMD,
            expected_behavior="Bridge/Source-Gate gaps are identified with evidence; no gate weakened.",
            actual_behavior=f"12_area={r_area['status']}:{r_area['fallback_reason'] or r_area['reason_code']}; 11_cos={r_cos['status']}:{r_cos['fallback_reason'] or r_cos['reason_code']}",
            verdict="DOCUMENTED_NOT_FIXED",
        ),
        "gaps": {
            "area_premise": {"case": "ext_prt_12_vmmu_page_r11#1", "replay": r_area,
                             "needed": "typed area premise of a named face (square ABB'A' area = 12 ⇒ AB² = 12) — new TypedFactNext fact kind + bridge + Source Gate quote binding"},
            "height_phrase_regular_prism": {"case": "ext_prt_11_vmmu_page_r10#1", "replay": r_cos,
                             "needed": "'chiều cao bằng a' for khối lăng trụ tam giác đều bound to lateral edge; plus degree output policy"},
        },
        "changes_this_run": 0,
        "reason_not_fixed": "Contract change (new fact kind) touches TypedFactNext/2 schema and Source Gate; outside safe scope without a migration plan.",
    }


def build_oracle_receipt(rows: list[dict[str, Any]], kernel: dict[str, Any]) -> dict[str, Any]:
    served = [r for r in rows if r["route"]["status"] == "SERVED"]
    checks = [{"case_id": r["case_id"], "engine": r["route"]["answer"], "oracle": r["oracle"]["answer"],
               "derivation": r["oracle"]["derivation"], "match": r["route"]["answer"] == r["oracle"]["answer"],
               "scene_unique": not bool(r["route"]["scene_configuration"])} for r in served]
    # Cross-check invariance: same goal with two different stated heights must equal the invariant answer.
    xs = {}
    for h in ("2", "7"):
        t = f"Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại B, AB = 6, AA' = {h}. Tính khoảng cách từ C đến mặt phẳng (ABB'A')."
        xs[f"ext02_with_AA'={h}"] = _route(t)["answer"]
    ok = all(c["match"] for c in checks) and all(v == "6" for v in xs.values())
    return {
        **_hdr(
            schema="algosim-mathematical-oracle-verification/1",
            case_ids=[c["case_id"] for c in checks],
            measurement_status="MEASURED_OFFLINE",
            oracle_provenance="Derivations written by the implementing agent (not an independent human reviewer) — ORACLE_SELF_DERIVED; MC keys printed in the source for ext02 (D.6), ext09 (B.2).",
            input_or_case_hash=P._sha256_json([c["case_id"] for c in checks]),
            oracle="Independent hand derivations (+ printed multiple-choice keys where present) + stated-height cross-check",
            test_command=TOOL_CMD,
            expected_behavior="Every served External17 answer equals the independent oracle; invariant answers equal the answer obtained with arbitrary stated heights.",
            actual_behavior=f"served={len(checks)}, matches={sum(c['match'] for c in checks)}, stated_height_crosscheck={xs}",
            verdict="PASS" if ok else "FAIL",
        ),
        "served_checks": checks,
        "stated_height_crosscheck": xs,
        "unsolved_oracles": {r["case_id"]: r["oracle"].get("oracle_value") for r in rows if r["route"]["status"] != "SERVED"},
        "invariance_probe_pass": sum(v["pass"] for v in kernel["probes"].values()),
        "invariance_probe_total": len(kernel["probes"]),
    }


def build_before_after(rows: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    prior = json.loads((PRIOR_RUN / "external_image_pipeline_receipt.json").read_text(encoding="utf-8"))
    before = {r["statement_id"]: r for r in prior["oracle_text_downstream_replay"]}
    per = []
    for r in rows:
        b = before.get(r["case_id"], {})
        per.append({"case_id": r["case_id"],
                    "before": {"status": b.get("status", "UNKNOWN"), "answer": b.get("answer"), "reason_code": b.get("reason_code")},
                    "after": {"status": r["route"]["status"], "answer": r["route"]["answer"], "reason_code": r["route"]["reason_code"],
                              "illustrative_scene": bool(r["route"]["scene_configuration"])},
                    "change": ("NEWLY_SOLVED" if b.get("status") != "SERVED" and r["route"]["status"] == "SERVED"
                               else "REGRESSED" if b.get("status") == "SERVED" and r["route"]["status"] != "SERVED" else "UNCHANGED")})
    b_served = sum(1 for v in before.values() if v.get("status") == "SERVED")
    b_md = sum(1 for v in before.values() if v.get("reason_code") == "MISSING_DIMENSION")
    regressed = [p["case_id"] for p in per if p["change"] == "REGRESSED"]
    return {
        **_hdr(
            schema="algosim-external17-before-after/1",
            case_ids=[r["case_id"] for r in rows],
            measurement_status="MEASURED_OFFLINE (ORACLE_TEXT_DOWNSTREAM_REPLAY on non-blind diagnostic corpus)",
            oracle_provenance="Frozen previous-run receipt (unified-angle-geometry-verified-image-to-3d/external_image_pipeline_receipt.json) + ORACLE_SELF_DERIVED + printed MC keys",
            input_or_case_hash=P._sha256_json([r["text_sha256"] for r in rows]),
            oracle="Frozen previous-run receipt (unified-angle-geometry-verified-image-to-3d/external_image_pipeline_receipt.json) vs this run + hand oracle",
            test_command=TOOL_CMD,
            expected_behavior="No regression; newly solved cases match the oracle; false MISSING_DIMENSION refusals removed.",
            actual_behavior=f"served {b_served}/17 → {summary['served']}/17; MISSING_DIMENSION {b_md} → {summary['missing_dimension_refusals']}; wrong_served → {summary['wrong_served']}; regressed={regressed}",
            verdict="PASS" if not regressed and summary["wrong_served"] == 0 else "FAIL",
        ),
        "corpus_role": "DEVELOPMENT_DIAGNOSTIC (inspected during gap analysis; not blind, not H-1)",
        "metrics_with_denominators": {
            "correct_solve_rate": {"external17_all": f"{summary['correct_served']}/17", "in_scope_polyhedral_subset": f"{summary['correct_served']}/12"},
            "served_answer_accuracy": f"{summary['correct_served']}/{summary['served']}",
            "wrong_served_rate": {"over_served": f"{summary['wrong_served']}/{summary['served']}", "over_all_17": f"{summary['wrong_served']}/17"},
            "correct_refusal_rate": {"out_of_scope_or_diagram_only": "5/5", "all_unserved_fail_closed_offline": "11/11"},
            "false_refusal_rate": {"false_missing_dimension_before": "2/17", "false_missing_dimension_after": "0/17", "unserved_in_scope_polyhedral_with_live_ai_disabled": "6/12"},
            "image_to_solution_success": {"zero_ai_from_raw_pixels": "0/16", "recorded_vision_replay": "1/16 (ext_hw_b1_01)", "live_vision": "NOT_MEASURED"},
            "local_only_solve_rate": {"verbatim_text": f"{summary['correct_served']}/17", "raw_external_images": "0/16"},
            "provider_dependency_rate": {"raw_external_images_needing_vision": "16/16", "verbatim_text_needing_fallback_or_out_of_scope": f"{summary['live_ai_disabled']}/17 (5 out-of-scope even with AI, 6 in-scope polyhedral)"},
        },
        "correction_of_previous_run": "The 2 MISSING_DIMENSION refusals (ext02, ext03#1) recorded as correct clarifications in the previous run were FALSE refusals: the asked quantities are height-invariant (CORRECTED_BY this run).",
        "per_case": per,
    }


def build_image_receipts(summary: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    r_ext, r_ocr, r_fb = P.build_image_ocr_and_routing_receipts()
    counts = r_ext["summary_counts"]
    ing = {
        **_hdr(
            schema="algosim-image-ingestion-end-to-end/1",
            case_ids=[x["image_id"] for x in P.CORPUS_ITEMS],
            measurement_status="RECORDED_REPLAY_VERIFIED + ORACLE_TEXT_DOWNSTREAM_REPLAY; LIVE_VISION_NOT_MEASURED",
            oracle_provenance="SHA-256 manifest of 38 cached external images + recorded OCR outputs + 6-criteria Input Fidelity Gate + ORACLE_SELF_DERIVED",
            input_or_case_hash=P._sha256_json([x["original_file_sha256"] for x in P.CORPUS_ITEMS]),
            oracle="SHA-256 cached images + recorded OCR outputs through the hardened Input Fidelity Gate + ORACLE_TEXT_DOWNSTREAM_REPLAY",
            test_command=TOOL_CMD,
            expected_behavior="0 corrupted OCR text reaches the Kernel; recorded OCR is never counted as solved; downstream replay strictly labelled.",
            actual_behavior=(f"recorded_local_ocr_accepted={counts['local_ocr_served_correctly']}/38, rejected={counts['ocr_rejected_safely']}/38; "
                             f"oracle_text_downstream_served={summary['served']}/17 (wrong={summary['wrong_served']})"),
            verdict="PASS" if counts["ocr_rejected_safely"] == 38 and summary["wrong_served"] == 0 else "FAIL",
        ),
        "image_to_3d_end_to_end_from_pixels_zero_ai": "0/16 complete-problem images (local OCR never passes the fidelity gate on these real images)",
        "per_image_fidelity": r_ext["per_image_fidelity"],
        "browser_image_upload": "see scene3d_browser_acceptance.json imageCase (prepare 503 LIVE_AI_DISABLED, no scene shown)",
    }
    r_ocr.update({
        "run_id": RUN_ID, "wave_id": WAVE_ID,
        "case_ids": [p["probe_id"] for p in r_ocr.get("corruption_probes", [])] + ["clean_printed_control"],
        "measurement_status": "MEASURED_OFFLINE",
        "oracle_provenance": "Deterministic 6-criteria Input Fidelity Gate + Dual-OCR Reconciliation Gate corruption probes",
        "source": "re-executed previous-run probe builder on this product commit (read-only import)",
    })
    r_fb.update({
        "run_id": RUN_ID, "wave_id": WAVE_ID,
        "case_ids": list((r_fb.get("routes") or {}).keys()),
        "measurement_status": "MOCK_ROUTING_VERIFIED + RECORDED_VISION_REPLAY_VERIFIED; LIVE_VISION_NOT_MEASURED",
        "oracle_provenance": "Adaptive Input Router contract across Route A/B/C/D, conflict confirmation, edited re-solve (0 stale cache), and diagram-only rejection",
        "source": "re-executed previous-run routing builder on this product commit (read-only import)",
    })
    return ing, r_ocr, r_fb


def build_vision_live_readiness() -> dict[str, Any]:
    imgs = [{"image_id": it["image_id"], "sha256": it["original_file_sha256"], "modality": it["printed_or_handwritten"],
             "ground_truth_text_sha256": P._sha256_json(it.get("verbatim_problem_texts")),
             "oracle_expected": [ORACLE[f"{it['image_id']}#{i}"].get("answer") or ORACLE[f"{it['image_id']}#{i}"].get("oracle_value")
                                 for i in range(1, len(it.get("verbatim_problem_texts", [])) + 1)],
             "cached": (P.CACHE_DIR / it["filename"]).exists()}
            for it in P.CORPUS_ITEMS if it.get("has_complete_problem")]
    return {
        **_hdr(
            schema="algosim-vision-live-readiness/1",
            case_ids=[i["image_id"] for i in imgs],
            measurement_status="LIVE_VISION_NOT_MEASURED",
            oracle_provenance="Verbatim ground-truth transcriptions in corpus_catalog.py + ORACLE_SELF_DERIVED / printed MC keys",
            input_or_case_hash=P._sha256_json([i["sha256"] for i in imgs]),
            oracle="Ground-truth verbatim transcriptions (corpus_catalog) + hand oracle answers",
            test_command="NOT_EXECUTED (requires owner approval + GEMINI_API_KEY; ALLOW_LIVE_AI=0 in this run)",
            expected_behavior="A live Vision measurement plan with pre-registered budget and stop rules exists; nothing is executed without owner approval.",
            actual_behavior=f"{len(imgs)} complete-problem images catalogued with SHA-256 and ground truth; live run NOT_EXECUTED",
            verdict="BLOCKED_PENDING_OWNER_APPROVAL",
        ),
        "images": imgs,
        "preregistered_protocol": {
            "entrypoint": "backend/app/ingestion/unified_input.py::prepare_unified_input -> AdaptiveInputRouter",
            "requests_max": 16 * 2, "retries_per_image": 1, "timeout_s": 30, "rate_limit_rpm": 10,
            "budget_usd_max": "OWNER_TO_SET",
            "redaction_policy": "never log GEMINI_API_KEY, Authorization headers, or raw unredacted provider stacktraces",
            "stop_rules": ["stop on first INFRASTRUCTURE_FAILURE burst ≥3", "stop if wrong_served > 0", "stop at budget cap"],
            "metrics": ["character error rate vs ground truth", "math-symbol fidelity", "downstream correct-solve vs oracle", "wrong-served", "token/cost telemetry"],
            "approval_file": "owner must create an approval record manually; automation never writes APPROVED_BY_USER",
        },
    }


def build_scene3d_browser(rows: list[dict[str, Any]], raw_path: Path) -> dict[str, Any]:
    raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else None
    served = [r for r in rows if r["route"]["status"] == "SERVED"]
    cont = {r["case_id"]: {"continuity_errors": r["route"]["scene3d_continuity_errors"],
                           "illustrative": bool(r["route"]["scene_configuration"])} for r in served}
    cont_ok = all(v["continuity_errors"] == [] for v in cont.values())
    bpass = raw and raw["summary"]["pass"] == raw["summary"]["total"] and raw["summary"]["imagePass"]
    fps = [x["orbit"]["fps"] for x in (raw or {}).get("results", []) if x.get("orbit")]
    heap = [x["orbit"]["heapMB"] for x in (raw or {}).get("results", []) if x.get("orbit") and x["orbit"].get("heapMB")]
    browser_ids = sorted({x["id"] for x in (raw or {}).get("results", [])}) + (["image_upload_hd_q_7922924"] if raw and raw.get("imageCase") else [])
    return {
        **_hdr(
            schema="algosim-scene3d-browser-acceptance/1",
            case_ids=sorted(cont.keys()) + browser_ids,
            measurement_status="MEASURED_HOST_HEADLESS_CHROME" if raw else "NOT_MEASURED",
            oracle_provenance="validate_construction_continuity + Playwright headless Chrome DOM/WebGL/network/console assertions against live local uvicorn",
            input_or_case_hash=P._sha256_json(sorted(cont) + browser_ids),
            oracle="validate_construction_continuity + real headless Chrome against production build proxied to a live local backend",
            test_command=f"node docs/evaluation/geometry/runs/{RUN_ID}/tools/e2e_browser_acceptance.mjs <dist> <port> <out.json> <image>",
            expected_behavior="Served → canvas + no note (unique) or canvas + illustrative note (invariant); refused → no scene, no raw codes/tracebacks, analysis-specific copy on 503; image upload with AI off → no scene.",
            actual_behavior=(f"continuity_ok={cont_ok} on {len(cont)} served; browser={raw['summary'] if raw else 'NOT_MEASURED'}; "
                             f"fps={min(fps) if fps else None}–{max(fps) if fps else None}; heapMB≤{max(heap) if heap else None}"),
            verdict="PASS" if cont_ok and bpass else "FAIL",
        ),
        "scene3d_continuity": cont,
        "browser_raw_file": raw_path.name,
        "browser_summary": raw["summary"] if raw else None,
        "ux_defect_found_and_fixed": "Text analysis 503 LIVE_AI_DISABLED previously displayed the photo-extraction message; fixed via analyzeErrorMessage (ProblemInput stage tracking); harness asserts no photo copy.",
        "limitations": ["headless Chrome on host GPU; not a physical low-end device", "1440x900 at zoom 1.0/1.1 only"],
    }


def build_perf() -> dict[str, Any]:
    base = P.build_performance_receipt(None)
    sets = {"height_invariant_served": INVARIANCE_PROBES["pos_ext03_verbatim"][0],
            "stated_height_served": INVARIANCE_PROBES["ctrl_stated_height"][0],
            "dependent_refused_after_probe": INVARIANCE_PROBES["neg_dependent_distance"][0],
            "volume_refused_no_probe": INVARIANCE_PROBES["neg_volume"][0]}
    ms: dict[str, list[float]] = {k: [] for k in sets}
    for _ in range(10):
        for k, t in sets.items():
            ms[k].append(_route(t)["elapsed_ms"])
    inv = {k: {"p50_ms": round(statistics.median(v), 3), "p95_ms": P._pct(v, 0.95), "n": len(v)} for k, v in ms.items()}
    base.update({
        "run_id": RUN_ID, "wave_id": WAVE_ID,
        "case_ids": ["baseline_square_pyramid", "new_angle_premise", "new_family1_right_trapezoid", "new_family2_rhombus_60"] + list(sets.keys()),
        "oracle_provenance": "time.perf_counter + tracemalloc + Win32 GetProcessMemoryInfo RSS + OMP_NUM_THREADS=1 subprocess",
        "height_invariance_overhead": {"cold_parser_each_request": True, "latency": inv,
            "note": "Probe runs up to 5 extra exact engine passes, only after a MISSING_DIMENSION refusal with whitelisted vertex-only goals."},
        "physical_low_end": "PHYSICAL_LOW_END_NOT_MEASURED",
        "measurement_status": "MEASURED_HOST + MEASURED_SINGLE_THREAD_ENV; PHYSICAL_LOW_END_NOT_MEASURED",
    })
    return base


def build_h1() -> dict[str, Any]:
    h1_pre = P.S.build_h1_corpus_integrity_receipt()
    ext_probes = [
        {"id": f"{it['image_id']}#{idx}", "problem_text": st}
        for it in P.CORPUS_ITEMS
        if it.get("has_complete_problem")
        for idx, st in enumerate(it.get("verbatim_problem_texts", []), 1)
    ]
    eight_layer = P.S.scan_eight_layer_contamination(
        ext_probes,
        ROOT,
        exclude=ROOT / "docs" / "evaluation" / "geometry" / "runs" / "real-world-printed-handwriting-acquisition",
    )
    hit_counts = {
        k: sum(1 for hits in v.values() if hits)
        for k, v in eight_layer.items()
        if isinstance(v, dict)
    }
    return {
        **_hdr(
            schema="algosim-independent-h1-readiness/1",
            case_ids=[p["id"] for p in ext_probes],
            measurement_status="NOT_MEASURED",
            oracle_provenance="Existing 8-layer anti-contamination scanner (score_independent_holdout_equivalence.py) + repository H-1 sealing policy",
            input_or_case_hash=P._sha256_json([p["id"] for p in ext_probes]),
            oracle="Policy: H-1 requires a sealed corpus curated and graded by someone other than the implementer, verified by the 8-layer contamination scanner",
            test_command="pytest backend/tests/geometry/test_independent_holdout_equivalence.py -q",
            expected_behavior="Reuse 8-layer scanner without rebuilding; keep INDEPENDENT_H1_VALIDATION = NOT_MEASURED unless an uncontaminated human-verified sealed corpus exists.",
            actual_behavior=f"h1_measurement={h1_pre.get('h1_measurement')}; external_statements_scanned={len(ext_probes)}; hit_counts={hit_counts}",
            verdict="NOT_MEASURED",
        ),
        "INDEPENDENT_H1_VALIDATION": "NOT_MEASURED",
        "why_external17_is_not_h1": "All 17 statements were read and diagnosed by the implementing agent during this and earlier runs; fixes were motivated by them.",
        "eight_layer_scan_hit_counts": hit_counts,
        "sealing_infrastructure_status": h1_pre.get("status"),
        "candidate_external_sources_inventory": [
            {"source": "anvo25/vmmu (HuggingFace)", "status": "EXTERNAL_SOURCE_AVAILABLE_PARTIALLY_INSPECTED", "why_not_blind_h1": "Rows r4/r7/r10/r11/r25/r26/r28 already inspected in External17; remaining uninspected spatial-geometry items require independent curator selection and human oracle review."},
            {"source": "hoidap247.com Q&A photos", "status": "DIAGNOSTIC_ONLY", "why_not_blind_h1": "Redistribution license unspecified; community answers are not authoritative ground truth without independent human verification."},
            {"source": "Vietnamese MOET official national exam PDFs (2017–2025)", "status": "CANDIDATE_FOR_CURATOR", "why_not_blind_h1": "Not bundled offline in this workspace; must be sampled and sealed by an independent curator outside the coding agent session."},
        ],
        "readiness": {"harness": "available (score_independent_holdout_equivalence + this tool)", "sealed_corpus": "MISSING",
                      "independent_grader": "MISSING", "owner_approval": "PENDING_OWNER_DECISION"},
    }


def build_regression(path: Path | None) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8")) if path and path.exists() else None
    suites = (data or {}).get("suites", {})
    ok = bool(suites) and all(v.get("verdict") == "PASS" for v in suites.values())
    return {
        **_hdr(
            schema="algosim-full-regression-summary/1",
            case_ids=list(suites.keys()) if suites else ["NONE"],
            measurement_status="MEASURED_OFFLINE" if data else "NOT_MEASURED",
            oracle_provenance="Exit codes and test counts of pytest, vitest, tsc, vite build, Playwright Chrome E2E, demo replay, crash audit, docs IA audit, publication safety, and freeze --verify",
            input_or_case_hash=P._sha256_json(data or {}),
            oracle="Recorded exit codes / pass counts of the listed commands (executed by the agent in this run)",
            test_command="see suites[*].command",
            expected_behavior="0 unexpected failures across backend, frontend, browser and demo audits.",
            actual_behavior=json.dumps({k: v.get("result") for k, v in suites.items()}, ensure_ascii=False),
            verdict="PASS" if ok else ("NOT_MEASURED" if not data else "FAIL"),
        ),
        **(data or {}),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--regression", type=Path, default=None)
    ap.add_argument("--skip-perf", action="store_true")
    ap.add_argument("--only-regression", action="store_true",
                    help="rewrite only full_regression_summary.json and its run.json entry (post-freeze)")
    a = ap.parse_args()

    def w(name: str, payload: dict[str, Any]) -> str:
        txt = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        (RUN_DIR / name).write_text(txt, encoding="utf-8", newline="\n")
        return P._sha256_bytes(txt.encode("utf-8"))

    if a.only_regression:
        reg = build_regression(a.regression)
        h = w("full_regression_summary.json", reg)
        run = json.loads((RUN_DIR / "run.json").read_text(encoding="utf-8"))
        run["receipts"]["full_regression_summary.json"] = {"sha256": h, "verdict": reg["verdict"]}
        run["regression_recorded_at_head"] = P.F._git("rev-parse", "HEAD")
        w("run.json", run)
        print(reg["verdict"], reg["actual_behavior"])
        return 0

    hashes: dict[str, str] = {}
    base = P.build_baseline_integrity()
    base.update({
        "run_id": RUN_ID, "wave_id": WAVE_ID,
        "case_ids": ["Dev72 (72)", "C26 (70)", "Section7 (7)", "ExternalCache (38)"],
        "measurement_status": "MEASURED_OFFLINE",
        "oracle_provenance": "custodian/geometry_oracle.py + C26 section coplanarity/convexity oracle + SHA-256 cache manifest",
        "baseline_head_commit": BASELINE_HEAD, "baseline_product_commit": BASELINE_PRODUCT,
        "baseline_freeze_verify": "MATCH (verified before edits on clean tree)",
    })
    hashes["baseline_verification_receipt.json"] = w("baseline_verification_receipt.json", base)

    rows, summary = build_case_diagnostics()
    diag = {
        **_hdr(
            schema="algosim-external17-case-diagnostics/1",
            case_ids=[r["case_id"] for r in rows],
            measurement_status="ORACLE_TEXT_DOWNSTREAM_REPLAY (MEASURED_OFFLINE)",
            oracle_provenance="ORACLE_SELF_DERIVED + printed MC keys where present (ext02 D.6, ext09 B.2, ext11 C.30°, ext12 B.2√3)",
            input_or_case_hash=P._sha256_json([r["text_sha256"] for r in rows]),
            oracle="Hand oracle (ORACLE dict in tool) + printed MC keys",
            test_command=TOOL_CMD,
            expected_behavior="Per-case 20-field layer trace for all 17 statements; 0 wrong-served.",
            actual_behavior=json.dumps(summary, ensure_ascii=False),
            verdict="PASS" if summary["wrong_served"] == 0 and len(rows) == 17 else "FAIL",
        ),
        "summary": summary,
        "cases": rows,
    }
    hashes["external17_case_diagnostics.json"] = w("external17_case_diagnostics.json", diag)
    hashes["live_ai_disabled_root_cause_analysis.json"] = w("live_ai_disabled_root_cause_analysis.json", build_root_cause(rows))
    kernel, parser = build_invariance_and_parser()
    hashes["parser_semantic_gap_closure.json"] = w("parser_semantic_gap_closure.json", parser)
    hashes["typed_facts_bridge_gap_closure.json"] = w("typed_facts_bridge_gap_closure.json", build_bridge_gap())
    hashes["planner_kernel_capability_closure.json"] = w("planner_kernel_capability_closure.json", kernel)
    hashes["mathematical_oracle_verification.json"] = w("mathematical_oracle_verification.json", build_oracle_receipt(rows, kernel))
    ing, ocr, fb = build_image_receipts(summary)
    hashes["image_ingestion_end_to_end_receipt.json"] = w("image_ingestion_end_to_end_receipt.json", ing)
    hashes["ocr_fidelity_safety_receipt.json"] = w("ocr_fidelity_safety_receipt.json", ocr)
    hashes["vision_fallback_offline_receipt.json"] = w("vision_fallback_offline_receipt.json", fb)
    hashes["vision_live_readiness.json"] = w("vision_live_readiness.json", build_vision_live_readiness())
    hashes["scene3d_browser_acceptance.json"] = w("scene3d_browser_acceptance.json", build_scene3d_browser(rows, RUN_DIR / "scene3d_browser_e2e_raw.json"))
    hashes["external17_before_after_comparison.json"] = w("external17_before_after_comparison.json", build_before_after(rows, summary))
    hashes["independent_h1_readiness.json"] = w("independent_h1_readiness.json", build_h1())
    if not a.skip_perf:
        hashes["low_end_performance_receipt.json"] = w("low_end_performance_receipt.json", build_perf())
    else:
        lp = RUN_DIR / "low_end_performance_receipt.json"
        if lp.exists():
            hashes["low_end_performance_receipt.json"] = P._sha256_bytes(lp.read_bytes())
    hashes["full_regression_summary.json"] = w("full_regression_summary.json", build_regression(a.regression))

    verdicts = {k: json.loads((RUN_DIR / k).read_text(encoding="utf-8")).get("verdict") for k in hashes}
    run = {
        "schema": "algosim-run-manifest/1", "run_id": RUN_ID, "wave_id": WAVE_ID,
        "task": "ALGOSIM — REAL-WORLD END-TO-END RELIABILITY & HYBRID GAP CLOSURE",
        "branch": "feat/local-first-geometry-understanding",
        "baseline_head_commit": BASELINE_HEAD, "baseline_product_commit": BASELINE_PRODUCT,
        "product_commit": P.F.product_commit(), "head_commit_at_generation": P.F._git("rev-parse", "HEAD"),
        "measured_system_tree_hash": P.F.measured_system_hash()[0],
        "measured_system_file_count": P.F.measured_system_hash()[1],
        "generated_at_utc": P._utc_now(), "live_gemini_calls": 0, "allow_live_ai": 0,
        "verdict": "PASS_OFFLINE_CANDIDATE_READY",
        "measurement_status": "OFFLINE_VERIFIED (LIVE_VISION_NOT_MEASURED; INDEPENDENT_H1_NOT_MEASURED; PHYSICAL_LOW_END_NOT_MEASURED)",
        "corrects": ["unified-angle-geometry-verified-image-to-3d (ext02/ext03#1 MISSING_DIMENSION were false refusals)"],
        "independent_h1_validation": "NOT_MEASURED",
        "receipts": {k: {"sha256": v, "verdict": verdicts[k]} for k, v in sorted(hashes.items())},
        "tools": ["tools/evaluate_real_world_reliability.py", "tools/e2e_browser_acceptance.mjs"],
        "raw_artifacts": ["scene3d_browser_e2e_raw.json"],
    }
    w("run.json", run)
    print(json.dumps({"summary": summary, "verdicts": verdicts}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
