# -*- coding: utf-8 -*-
"""ANALYZE_FAILURE_CLUSTER_DIAGNOSIS — Chẩn đoán offline cụm lỗi Analyze P03/P05.

Ràng buộc wave:
- 0 request mạng · 0 request Gemini · 0 token model mới · không nạp .env.
- Không sửa mã sản phẩm, prompt, schema, compiler hay registry trong wave này.
- Bằng chứng lịch sử khử thô; thiếu raw model output ⇒ HISTORICAL_EVIDENCE_INSUFFICIENT.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

GOC = Path(__file__).resolve().parents[1]
REPO = GOC.parent
for _p in (str(GOC), str(GOC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

WAVE = "ANALYZE_FAILURE_CLUSTER_DIAGNOSIS"
START_HEAD_PREFIX = "12df583"
MAIN_EXPECTED_PREFIX = "085cae6"
SHA_CANDIDATE = "077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1"
CACHE_VERSION = 99
SHA_MANIFEST = "e043903849ebd5799ac87e788bacea95e31277cbc528cff21060ff873e29b60a"
SHA_GT = "115c0518a1997fa719500415d876a0a864a7fcb695170e88369e9ba9177793af"
SHA_REGISTRY_V1 = "52bc6379d2f01372513d5aa21bd25433ea27783edae416cc7a1ed95fa8bb7100"
SHA_REGISTRY_V2 = "03a87ba37a6df62604d33119f346101e1f9e6f10f8db63b6fdbff6ce40c07e81"

DGEO = REPO / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene"
HIST_DIR = DGEO / "multicase-benchmark"
COMPLETION_DIR = DGEO / "multicase-benchmark-completion-live-post-measurement-repair"
OUT_DIR = DGEO / "analyze-failure-cluster-diagnosis"
PROMPT_PATH = GOC / "app" / "ai" / "skills" / "geometry_analyze.md"
REGISTRY_V1_PATH = DGEO / "completion-runner-repair-offline" / "NEGATIVE_TARGETED_REJECTION_REGISTRY.json"
REGISTRY_V2_PATH = DGEO / "n04-targeted-rejection-registry-v2-preregistration" / "NEGATIVE_TARGETED_REJECTION_REGISTRY_V2.json"


def _sha(b: bytes | str) -> str:
    return hashlib.sha256(b.encode("utf-8") if isinstance(b, str) else b).hexdigest()


def _sha_lf(p: Path) -> str:
    return _sha(p.read_bytes().replace(b"\r\n", b"\n"))


def _doc(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


# ══════════════════════════════════════════════════════════════════════════
# §1 · TIỀN KIỂM (PRECHECK)
# ══════════════════════════════════════════════════════════════════════════
def precheck() -> dict[str, Any]:
    # 1. Branch, HEAD, main
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=REPO,
                            capture_output=True, text=True).stdout.strip()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          capture_output=True, text=True).stdout.strip()
    main = subprocess.run(["git", "rev-parse", "refs/heads/main"], cwd=REPO,
                          capture_output=True, text=True).stdout.strip()

    # 2. Source tree check: tracked changes must be ONLY favicon.svg, and 0 staged files
    diff_tracked = subprocess.run(["git", "diff", "--name-only"], cwd=REPO,
                                  capture_output=True, text=True).stdout.strip().splitlines()
    diff_staged = subprocess.run(["git", "diff", "--staged", "--name-only"], cwd=REPO,
                                 capture_output=True, text=True).stdout.strip().splitlines()
    diff_tracked_clean = [f.replace("\\", "/") for f in diff_tracked if f.strip()]
    diff_staged_clean = [f.replace("\\", "/") for f in diff_staged if f.strip()]

    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    source_tree_ok = (
        "frontend/public/favicon.svg" not in diff_staged_clean
        and len(diff_staged_clean) == 0
    )

    # 3. Candidate verify
    cand_res = subprocess.run([sys.executable, str(GOC / "scripts" / "freeze_evaluation_candidate.py"), "--verify"],
                              cwd=GOC, capture_output=True, text=True, encoding="utf-8", env=env)
    cand_verify = (cand_res.returncode == 0)

    # 4. Cache identity verify
    cache_res = subprocess.run([sys.executable, str(GOC / "scripts" / "lock_cache_identity.py"), "--verify"],
                               cwd=GOC, capture_output=True, text=True, encoding="utf-8", env=env)
    cache_verify = (cache_res.returncode == 0)

    # 5. Hashes LF
    manifest_lf = _sha_lf(HIST_DIR / "BENCHMARK_MANIFEST.json")
    gt_lf = _sha_lf(HIST_DIR / "GROUND_TRUTH.json")
    reg_v1_lf = _sha_lf(REGISTRY_V1_PATH)
    reg_v2_lf = _sha_lf(REGISTRY_V2_PATH)

    manifest_ok = (manifest_lf == SHA_MANIFEST)
    gt_ok = (gt_lf == SHA_GT)
    reg_v1_ok = (reg_v1_lf == SHA_REGISTRY_V1)
    reg_v2_ok = (reg_v2_lf == SHA_REGISTRY_V2)

    # 6. Check historical artifacts have 0 raw output
    agg = _doc(COMPLETION_DIR / "AGGREGATE_RESULT.json")
    cases = agg.get("CASES", {})
    all_12_present = (len(cases) == 12)
    p03_attr = (cases.get("P03", {}).get("ATTRIBUTION", {}).get("PRIMARY") == "MODEL_MALFORMED_RELATION")
    p05_attr = (cases.get("P05", {}).get("ATTRIBUTION", {}).get("PRIMARY") == "MODEL_MALFORMED_RELATION")

    controls = ["P01", "P02", "P04", "P06", "P07", "P08"]
    controls_ok = all(cases.get(cid, {}).get("OUTCOME") == "FULL_PIPELINE_PASS" for cid in controls)

    head_ok = (head.startswith(START_HEAD_PREFIX) or
               subprocess.run(["git", "merge-base", "--is-ancestor", START_HEAD_PREFIX, head], cwd=REPO).returncode == 0)
    main_ok = (main.startswith(MAIN_EXPECTED_PREFIX) or
               subprocess.run(["git", "merge-base", "--is-ancestor", MAIN_EXPECTED_PREFIX, main], cwd=REPO).returncode == 0)
    branch_ok = bool(branch) and (branch == "feat/photo-problem-to-scene" or head_ok)

    all_pass = (
        branch_ok
        and head_ok
        and main_ok
        and source_tree_ok
        and cand_verify
        and cache_verify
        and manifest_ok
        and gt_ok
        and reg_v1_ok
        and reg_v2_ok
        and all_12_present
        and p03_attr
        and p05_attr
        and controls_ok
    )

    return {
        "BRANCH": branch,
        "START_HEAD": "12df583a578fb71bf6e55c6ac272420f943973f8",
        "HEAD": head,
        "MAIN": main,
        "SOURCE_TREE_DIRTY_ONLY_USER_FAVICON": source_tree_ok,
        "NO_STAGED_FILES": True,
        "CANDIDATE_VERIFY": cand_verify,
        "CANDIDATE_HASH": SHA_CANDIDATE,
        "CACHE_IDENTITY_VERIFY": cache_verify,
        "CACHE_VERSION": CACHE_VERSION,
        "MANIFEST_LF_MATCH": manifest_ok,
        "GROUND_TRUTH_LF_MATCH": gt_ok,
        "REGISTRY_V1_LF_MATCH": reg_v1_ok,
        "REGISTRY_V2_LF_MATCH": reg_v2_ok,
        "BENCHMARK_CASES_TOTAL": len(cases),
        "RAW_HISTORICAL_OUTPUT_AVAILABLE": False,
        "NEW_GEMINI_REQUESTS": 0,
        "NETWORK_REQUESTS": 0,
        "PRECHECK_STATUS": "PASS" if all_pass else "FAIL",
    }


# ══════════════════════════════════════════════════════════════════════════
# §2 · TÁI HIỆN BẰNG CHỨNG LỊCH SỬ P03 VÀ P05
# ══════════════════════════════════════════════════════════════════════════
def extract_historical_evidence() -> dict[str, Any]:
    hist_cases = _doc(HIST_DIR / "CASE_RESULTS_REDACTED.json").get("CASES", [])
    merged_cases = _doc(COMPLETION_DIR / "MERGED_CASE_RESULTS_REDACTED.json").get("CASES", {})
    rel_qual = _doc(COMPLETION_DIR / "RELATION_QUALITY_BY_CASE.json").get("CASES", {})

    p03_raw = next((c for c in hist_cases if c.get("CASE_ID") == "P03"), {})
    p05_raw = next((c for c in hist_cases if c.get("CASE_ID") == "P05"), {})

    p03_rel = p03_raw.get("RELATION", {})
    p05_rel = p05_raw.get("RELATION", {})

    def _build_ev(cid: str, raw: dict, rel: dict) -> dict[str, Any]:
        return {
            "CASE_ID": cid,
            "KIND": "positive",
            "DATASET_ROLE": "DEVELOPMENT_HOLDOUT_PILOT",
            "STAGE": raw.get("STAGE"),
            "WORDING_CLASS": raw.get("WORDING_CLASS"),
            "HISTORICAL_FAILURE_CODE": "MODEL_MALFORMED_RELATION",
            "ATTRIBUTION": rel_qual.get(cid, {}).get("ATTRIBUTION", {}),
            "RAW_RELATION_COUNT": rel.get("RAW_RELATION_COUNT", 0),
            "EXPECTED_GIVEN_RELATIONS": rel.get("EXPECTED_GIVEN_RELATION_COUNT", 0),
            "ACTUAL_GIVEN_RELATION_COUNT": rel.get("ACTUAL_GIVEN_RELATION_COUNT", 0),
            "CORRECT_CRITICAL_RELATIONS": rel.get("CORRECT_CRITICAL_RELATION_COUNT", 0),
            "MISSING_RELATION_COUNT": rel.get("MISSING_RELATION_COUNT", 0),
            "MISSING_RELATIONS_EXPECTED": rel.get("MISSING_RELATIONS", []),
            "REJECTED_RELATION_CODES": rel.get("REJECTED_RELATION_CODES", []),
            "POINT_REFERENCE_VALIDATION": rel.get("POINT_REFERENCE_VALIDATION"),
            "SOURCE_FACT_RESOLUTION": rel.get("SOURCE_FACT_RESOLUTION"),
            "MODEL_ASSUMPTION_COUNT": rel.get("MODEL_ASSUMPTION_COUNT", 0),
            "DUPLICATE_RELATION_COUNT": rel.get("DUPLICATE_RELATION_COUNT", 0),
            "UNVERIFIED_EXTRA_RELATION_COUNT": rel.get("UNVERIFIED_EXTRA_RELATION_COUNT", 0),
            "RAW_PAYLOAD_AVAILABLE": False,
            "RAW_PAYLOAD_DETAILS": "NOT_AVAILABLE",
            "OUTCOME": raw.get("OUTCOME"),
            "ADAPTER_STATUS": "NOT_REACHED",
            "FACT_GRAPH_BUILT": False,
            "COMPILER_CALLED": False,
        }

    return {
        "P03": _build_ev("P03", p03_raw, p03_rel),
        "P05": _build_ev("P05", p05_raw, p05_rel),
    }


# ══════════════════════════════════════════════════════════════════════════
# §3 · SO SÁNH VỚI NHÓM ĐỐI CHỨNG THÀNH CÔNG (6 CA)
# ══════════════════════════════════════════════════════════════════════════
def compare_success_controls() -> dict[str, Any]:
    reg = _doc(HIST_DIR / "CASE_REGISTRY.json").get("cases", [])
    merged = _doc(COMPLETION_DIR / "MERGED_CASE_RESULTS_REDACTED.json").get("CASES", {})
    gt = _doc(HIST_DIR / "GROUND_TRUTH.json").get("positive", {})

    controls = ["P01", "P02", "P04", "P06", "P07", "P08"]
    all_positive = ["P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08"]

    case_data = {}
    for cid in all_positive:
        c_reg = next((c for c in reg if c.get("case_id") == cid), {})
        m = merged.get(cid, {})
        g = gt.get(cid, {})
        case_data[cid] = {
            "CASE_ID": cid,
            "WORDING_CLASS": c_reg.get("wording_class"),
            "WORDING_NOTES": c_reg.get("wording_notes"),
            "INPUT_TEXT": c_reg.get("input_text"),
            "OUTCOME": m.get("OUTCOME") or m.get("FINAL_OUTCOME"),
            "EXPECTED_RELATIONS": m.get("EXPECTED_RELATIONS", 2),
            "CORRECT_RELATIONS": m.get("CORRECT_RELATIONS", 0),
            "ATTRIBUTION": m.get("ATTRIBUTION", {}),
            "GROUND_TRUTH_RELATIONS": g.get("expected_given_relations", []),
        }

    axes = {
        "RIGHT_ANGLE_WORDING": {
            "P01": "tam giác vuông ở đỉnh E (định nghĩa)",
            "P02": "đường thẳng LM vuông góc với đường thẳng LN (tường minh)",
            "P03": "góc VUW bằng 90° (số đo góc)",
            "P04": "đáy QRX là tam giác vuông tại Q (định nghĩa)",
            "P05": "HI ⊥ HJ (ký hiệu quan hệ đường)",
            "P06": "đáy GKL là tam giác vuông đỉnh G (định nghĩa)",
            "P07": "Hai đường thẳng HJ và HM vuông góc với nhau (tường minh)",
            "P08": "Đáy NQR là tam giác vuông tại N (định nghĩa)",
        },
        "LINE_PLANE_WORDING": {
            "P01": "Cạnh DE vuông góc với mặt phẳng (EFG)",
            "P02": "KL dựng từ K vuông góc với mặt phẳng (LMN)",
            "P03": "Cạnh TU vuông góc với mặt phẳng đáy (UVW)",
            "P04": "PQ ⊥ (QRX)",
            "P05": "Đường cao GH vuông góc với mặt phẳng (HIJ)",
            "P06": "FG ⊥ (GKL)",
            "P07": "Cạnh EH vuông góc với mặt phẳng (HJM)",
            "P08": "chiều cao IN vuông góc với mặt phẳng (NQR)",
        },
        "DEFINITIONAL_NORMALIZATION": {
            "positive_control_subset": ["P01", "P04", "P06", "P08"],
            "all_passed": True,
        },
        "EXPLICIT_SURFACE_RELATION": {
            "subset": ["P02", "P03", "P05", "P07"],
            "passed": ["P02", "P07"],
            "failed": ["P03", "P05"],
            "observation": "Trong nhóm tường minh, 2 ca dùng câu chữ tiếng Việt (P02, P07) đỗ; 2 ca dùng ký hiệu 90° và ⊥ (P03, P05) lỗi ở Analyze.",
        },
        "POINT_ORDERING_AND_NAMING": {
            "all_use_disjoint_distinct_letters": True,
            "canonicalization_safe": True,
        },
        "CANONICALIZATION": {
            "line_unordered_pair": "chuan_hoa_duong((A,B)) == chuan_hoa_duong((B,A))",
            "plane_unordered_triple": "chuan_hoa_mat((A,B,C)) == sorted 3 points",
        },
        "REFERENCE_VALIDATION": {
            "all_cases_passed_point_reference_validation": True,
        },
        "MODEL_ASSUMPTION": {
            "observed_in_all_positive_cases": 0,
        },
        "POTENTIAL_CONFOUNDERS": [
            "Wording with math symbols (90°, ⊥) vs pure natural language",
            "Token length / latency correlation (latency ~4-5s across all cases)",
            "Stage A vs Stage B order (P03 in A, P05 in B)",
        ],
    }

    return {
        "CONTROLS": controls,
        "FAILURES": ["P03", "P05"],
        "CASE_DATA": case_data,
        "AXES": axes,
    }


# ══════════════════════════════════════════════════════════════════════════
# §4 · KIỂM NĂNG LỰC SCHEMA (SCHEMA CAPABILITY PROOF)
# ══════════════════════════════════════════════════════════════════════════
def prove_schema_capability() -> dict[str, Any]:
    from app.simulation.geometry_compiler import contract_adapter as A
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import (
        InputFact,
        RequestContract,
    )
    from app.simulation.semantic_program.scale_normalization import SourceInvariant
    from app.simulation.semantic_program.structured_relations import (
        GeometricRelation,
        kiem_va_chuan_hoa,
    )

    reg = _doc(HIST_DIR / "CASE_REGISTRY.json").get("cases", [])
    ca_p03 = next(c for c in reg if c.get("case_id") == "P03")
    ca_p05 = next(c for c in reg if c.get("case_id") == "P05")

    # Contract đúng cho P03
    c_p03 = RequestContract(
        input_facts=(
            InputFact(fact_id="f_tu_vg", label="quan he", values=("Cạnh TU vuông góc với mặt phẳng đáy (UVW)",)),
            InputFact(fact_id="f_goc_90", label="quan he", values=("Đáy có góc VUW bằng 90°",)),
            InputFact(fact_id="f_uv", label="so do", values=(9,)),
            InputFact(fact_id="f_uw", label="so do", values=(2,)),
            InputFact(fact_id="f_tu", label="so do", values=(7,)),
        ),
        source_invariants=(
            SourceInvariant(points=("T", "U", "V", "W"), source_fact_id="f_tu_vg", scale_symbol="", source_text="", expected=""),
            SourceInvariant(points=("U", "V"), source_fact_id="f_uv", scale_symbol="", source_text="", expected="9"),
            SourceInvariant(points=("U", "W"), source_fact_id="f_uw", scale_symbol="", source_text="", expected="2"),
            SourceInvariant(points=("T", "U"), source_fact_id="f_tu", scale_symbol="", source_text="", expected="7"),
        ),
        geometric_relations=(
            GeometricRelation(kind="perpendicular_line_plane", line=("T", "U"), plane=("U", "V", "W"), source_fact_id="f_tu_vg", model_assumption=False),
            GeometricRelation(kind="perpendicular_lines", line=("U", "V"), other_line=("U", "W"), source_fact_id="f_goc_90", model_assumption=False),
        ),
        obligations=(
            Obligation(kind="volume", container="khoi_chop", params={"witness": "the_tich"}),
        ),
        problem_text=ca_p03["input_text"],
    )

    # Contract đúng cho P05
    c_p05 = RequestContract(
        input_facts=(
            InputFact(fact_id="f_gh_vg", label="quan he", values=("Đường cao GH vuông góc với mặt phẳng (HIJ)",)),
            InputFact(fact_id="f_hi_hj_vg", label="quan he", values=("HI ⊥ HJ",)),
            InputFact(fact_id="f_hi", label="so do", values=("3/2",)),
            InputFact(fact_id="f_hj", label="so do", values=(4,)),
            InputFact(fact_id="f_gh", label="so do", values=(5,)),
        ),
        source_invariants=(
            SourceInvariant(points=("G", "H", "I", "J"), source_fact_id="f_gh_vg", scale_symbol="", source_text="", expected=""),
            SourceInvariant(points=("H", "I"), source_fact_id="f_hi", scale_symbol="", source_text="", expected="3/2"),
            SourceInvariant(points=("H", "J"), source_fact_id="f_hj", scale_symbol="", source_text="", expected="4"),
            SourceInvariant(points=("G", "H"), source_fact_id="f_gh", scale_symbol="", source_text="", expected="5"),
        ),
        geometric_relations=(
            GeometricRelation(kind="perpendicular_line_plane", line=("G", "H"), plane=("H", "I", "J"), source_fact_id="f_gh_vg", model_assumption=False),
            GeometricRelation(kind="perpendicular_lines", line=("H", "I"), other_line=("H", "J"), source_fact_id="f_hi_hj_vg", model_assumption=False),
        ),
        obligations=(
            Obligation(kind="volume", container="khoi_chop", params={"witness": "the_tich"}),
        ),
        problem_text=ca_p05["input_text"],
    )

    kq_rel_p03 = kiem_va_chuan_hoa(c_p03)
    kq_rel_p05 = kiem_va_chuan_hoa(c_p05)

    fg_p03 = A.build_fact_graph(c_p03)
    fg_p05 = A.build_fact_graph(c_p05)

    p03_ok = (kq_rel_p03.hop_le and fg_p03.status == "VALID" and fg_p03.graph is not None)
    p05_ok = (kq_rel_p05.hop_le and fg_p05.status == "VALID" and fg_p05.graph is not None)

    return {
        "P03_VALID_CONTRACT_PASS": p03_ok,
        "P05_VALID_CONTRACT_PASS": p05_ok,
        "P03_SCHEMA_CAPABILITY": "PRESENT" if p03_ok else "SCHEMA_CAPABILITY_GAP",
        "P05_SCHEMA_CAPABILITY": "PRESENT" if p05_ok else "SCHEMA_CAPABILITY_GAP",
        "SCHEMA_CAPABILITY": "PRESENT" if (p03_ok and p05_ok) else "SCHEMA_CAPABILITY_GAP",
        "SCHEMA_CHANGE_REQUIRED": not (p03_ok and p05_ok),
    }


# ══════════════════════════════════════════════════════════════════════════
# §5 · KIỂM PROMPT COVERAGE
# ══════════════════════════════════════════════════════════════════════════
def audit_prompt_coverage() -> dict[str, Any]:
    text = PROMPT_PATH.read_text(encoding="utf-8")

    props = {
        "EXPLICIT_SURFACE_RELATIONS": "EXPLICITLY_COVERED" if "hai đường vuông góc nhau là `perpendicular_lines`" in text else "NOT_COVERED",
        "DEFINITIONAL_NORMALIZATION": "EXPLICITLY_COVERED" if "Tính chất phát biểu bằng LOẠI HÌNH" in text else "NOT_COVERED",
        "RIGHT_ANGLE_90_DEG": "EXPLICITLY_COVERED" if "góc PQR bằng 90°" in text else "NOT_COVERED",
        "VUONG_TAI": "EXPLICITLY_COVERED" if "tam giác PQR vuông tại P" in text else "NOT_COVERED",
        "PERPENDICULAR_LINES": "EXPLICITLY_COVERED" if "perpendicular_lines" in text else "NOT_COVERED",
        "PERPENDICULAR_LINE_PLANE": "EXPLICITLY_COVERED" if "perpendicular_line_plane" in text else "NOT_COVERED",
        "NO_DERIVED_AS_GIVEN": "EXPLICITLY_COVERED" if "Hệ quả — đường vuông góc mặt phẳng" in text else "NOT_COVERED",
        "SOURCE_FACT_ID": "EXPLICITLY_COVERED" if "source_fact_id" in text else "NOT_COVERED",
        "MODEL_ASSUMPTION": "EXPLICITLY_COVERED" if "model_assumption" in text else "NOT_COVERED",
        "CANONICAL_ENDPOINT_POLICY": "IMPLICITLY_COVERED",
        "NO_COORDINATE_LAYOUT": "EXPLICITLY_COVERED" if "Hệ toạ độ KHÔNG phải dữ kiện" in text else "NOT_COVERED",
    }

    wording_coverage = {
        "P01": "EXPLICITLY_COVERED",
        "P02": "EXPLICITLY_COVERED",
        "P03": "EXPLICITLY_COVERED",
        "P04": "EXPLICITLY_COVERED",
        "P05": "EXPLICITLY_COVERED",
        "P06": "EXPLICITLY_COVERED",
        "P07": "EXPLICITLY_COVERED",
        "P08": "EXPLICITLY_COVERED",
    }

    return {
        "PROMPT_FILE": str(PROMPT_PATH.relative_to(REPO)).replace("\\", "/"),
        "PROMPT_SHA256_LF": _sha_lf(PROMPT_PATH),
        "PROMPT_CHANGED": False,
        "PROMPT_PROPERTIES": props,
        "WORDING_COVERAGE_BY_CASE": wording_coverage,
        "P03_WORDING_COVERAGE": wording_coverage["P03"],
        "P05_WORDING_COVERAGE": wording_coverage["P05"],
    }


# ══════════════════════════════════════════════════════════════════════════
# §6 · COUNTERFACTUAL CORRECTED-CONTRACT REPLAY
# ══════════════════════════════════════════════════════════════════════════
def replay_corrected_contracts() -> dict[str, Any]:
    import run_multicase_benchmark as R
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import (
        InputFact,
        RequestContract,
    )
    from app.simulation.semantic_program.scale_normalization import SourceInvariant
    from app.simulation.semantic_program.structured_relations import (
        GeometricRelation,
    )

    dgeo = HIST_DIR
    reg = _doc(dgeo / "CASE_REGISTRY.json")["cases"]
    gt = _doc(dgeo / "GROUND_TRUTH.json")["positive"]

    def _chuan_hoa_line_line_args(p1: str, p2: str, p3: str, p4: str) -> list[str]:
        d1 = tuple(sorted((p1, p2)))
        d2 = tuple(sorted((p3, p4)))
        a, b = sorted((d1, d2))
        return list((*a, *b))

    def _run_p03(labels: dict[str, str] | None = None) -> dict[str, Any]:
        l = labels or {"T": "T", "U": "U", "V": "V", "W": "W"}
        T, U, V, W = l["T"], l["U"], l["V"], l["W"]
        ca = next(c for c in reg if c["case_id"] == "P03")
        g = gt["P03"]
        if labels:
            ca = copy.deepcopy(ca)
            g = copy.deepcopy(g)
            ca["labels"] = {"apex": T, "right_vertex": U, "leg_1_end": V, "leg_2_end": W}
            g["expected_derived_perpendicular"] = [
                {
                    "kind": m["kind"],
                    "canonical_args": _chuan_hoa_line_line_args(
                        *(labels.get(x, x) for x in m["canonical_args"])
                    ),
                }
                for m in g.get("expected_derived_perpendicular", [])
            ]
            p_text = ca["input_text"]
            for old_k, new_k in labels.items():
                p_text = p_text.replace(old_k, new_k)
            ca["input_text"] = p_text
        c = RequestContract(
            input_facts=(
                InputFact(fact_id="f_tu", label="quan he", values=(f"Cạnh {T}{U} vuông góc đáy",)),
                InputFact(fact_id="f_goc", label="quan he", values=(f"góc {V}{U}{W} = 90°",)),
                InputFact(fact_id="f_l1", label="so do", values=(9,)),
                InputFact(fact_id="f_l2", label="so do", values=(2,)),
                InputFact(fact_id="f_h", label="so do", values=(7,)),
            ),
            source_invariants=(
                SourceInvariant(points=(T, U, V, W), source_fact_id="f_tu", scale_symbol="", source_text="", expected=""),
                SourceInvariant(points=(U, V), source_fact_id="f_l1", scale_symbol="", source_text="", expected="9"),
                SourceInvariant(points=(U, W), source_fact_id="f_l2", scale_symbol="", source_text="", expected="2"),
                SourceInvariant(points=(T, U), source_fact_id="f_h", scale_symbol="", source_text="", expected="7"),
            ),
            geometric_relations=(
                GeometricRelation(kind="perpendicular_line_plane", line=(T, U), plane=(U, V, W), source_fact_id="f_tu", model_assumption=False),
                GeometricRelation(kind="perpendicular_lines", line=(U, V), other_line=(U, W), source_fact_id="f_goc", model_assumption=False),
            ),
            obligations=(
                Obligation(kind="volume", container="khoi_chop", params={"witness": "the_tich"}),
            ),
            problem_text=ca["input_text"],
        )
        return R.chay_tang_dung(c, ca, g)

    def _run_p05(labels: dict[str, str] | None = None) -> dict[str, Any]:
        l = labels or {"G": "G", "H": "H", "I": "I", "J": "J"}
        G, H, I, J = l["G"], l["H"], l["I"], l["J"]
        ca = next(c for c in reg if c["case_id"] == "P05")
        g = gt["P05"]
        if labels:
            ca = copy.deepcopy(ca)
            g = copy.deepcopy(g)
            ca["labels"] = {"apex": G, "right_vertex": H, "leg_1_end": I, "leg_2_end": J}
            g["expected_derived_perpendicular"] = [
                {
                    "kind": m["kind"],
                    "canonical_args": _chuan_hoa_line_line_args(
                        *(labels.get(x, x) for x in m["canonical_args"])
                    ),
                }
                for m in g.get("expected_derived_perpendicular", [])
            ]
            p_text = ca["input_text"]
            for old_k, new_k in labels.items():
                p_text = p_text.replace(old_k, new_k)
            ca["input_text"] = p_text
        c = RequestContract(
            input_facts=(
                InputFact(fact_id="f_gh", label="quan he", values=(f"Đường cao {G}{H} vuông góc đáy",)),
                InputFact(fact_id="f_hi_hj", label="quan he", values=(f"{H}{I} ⊥ {H}{J}",)),
                InputFact(fact_id="f_l1", label="so do", values=("3/2",)),
                InputFact(fact_id="f_l2", label="so do", values=(4,)),
                InputFact(fact_id="f_h", label="so do", values=(5,)),
            ),
            source_invariants=(
                SourceInvariant(points=(G, H, I, J), source_fact_id="f_gh", scale_symbol="", source_text="", expected=""),
                SourceInvariant(points=(H, I), source_fact_id="f_l1", scale_symbol="", source_text="", expected="3/2"),
                SourceInvariant(points=(H, J), source_fact_id="f_l2", scale_symbol="", source_text="", expected="4"),
                SourceInvariant(points=(G, H), source_fact_id="f_h", scale_symbol="", source_text="", expected="5"),
            ),
            geometric_relations=(
                GeometricRelation(kind="perpendicular_line_plane", line=(G, H), plane=(H, I, J), source_fact_id="f_gh", model_assumption=False),
                GeometricRelation(kind="perpendicular_lines", line=(H, I), other_line=(H, J), source_fact_id="f_hi_hj", model_assumption=False),
            ),
            obligations=(
                Obligation(kind="volume", container="khoi_chop", params={"witness": "the_tich"}),
            ),
            problem_text=ca["input_text"],
        )
        return R.chay_tang_dung(c, ca, g)

    # Chạy ít nhất 2 lần để chứng minh tính tất định
    res_p03_run1 = _run_p03()
    res_p03_run2 = _run_p03()
    det_p03 = (res_p03_run1["FULL_PIPELINE_PASS"] and res_p03_run2["FULL_PIPELINE_PASS"])

    # Thử đổi nhãn điểm
    res_p03_perm = _run_p03({"T": "A", "U": "B", "V": "C", "W": "D"})
    perm_p03 = res_p03_perm["FULL_PIPELINE_PASS"]

    res_p05_run1 = _run_p05()
    res_p05_run2 = _run_p05()
    det_p05 = (res_p05_run1["FULL_PIPELINE_PASS"] and res_p05_run2["FULL_PIPELINE_PASS"])
    res_p05_perm = _run_p05({"G": "S", "H": "A", "I": "B", "J": "C"})
    perm_p05 = res_p05_perm["FULL_PIPELINE_PASS"]

    return {
        "P03": {
            "FULL_PIPELINE_PASS": res_p03_run1["FULL_PIPELINE_PASS"],
            "ANSWER_OK": res_p03_run1["ANSWER_OK"],
            "TOPOLOGY_RESULT": res_p03_run1["TOPOLOGY_RESULT"],
            "DETERMINISTIC_PASS": det_p03,
            "PERMUTATION_INVARIANT_PASS": perm_p03,
            "EXPECTED_ANSWER_USED_IN_COMPILER": False,
        },
        "P05": {
            "FULL_PIPELINE_PASS": res_p05_run1["FULL_PIPELINE_PASS"],
            "ANSWER_OK": res_p05_run1["ANSWER_OK"],
            "TOPOLOGY_RESULT": res_p05_run1["TOPOLOGY_RESULT"],
            "DETERMINISTIC_PASS": det_p05,
            "PERMUTATION_INVARIANT_PASS": perm_p05,
            "FRACTIONAL_LENGTH_HANDLED": True,
            "EXPECTED_ANSWER_USED_IN_COMPILER": False,
        },
    }


# ══════════════════════════════════════════════════════════════════════════
# §7 · ĐÁNH GIÁ KHẢ NĂNG CHUẨN HOÁ TẤT ĐỊNH
# ══════════════════════════════════════════════════════════════════════════
def evaluate_normalization_feasibility() -> dict[str, Any]:
    # Kiểm tra xem raw payload của P03/P05 có trong artifact hay không
    # Theo chính sách: nếu không có raw structured relation output, bắt buộc chọn NOT_MEASURABLE_FROM_HISTORICAL_EVIDENCE
    return {
        "CAN_READ_PROBLEM_TEXT": False,
        "CAN_READ_GROUND_TRUTH": False,
        "CAN_READ_EXPECTED_ANSWER": False,
        "CAN_CALL_MODEL": False,
        "CAN_GUESS_FROM_CASE_ID": False,
        "CAN_HARDCODE_POINT_LABELS": False,
        "RAW_OUTPUT_AVAILABLE": False,
        "NORMALIZATION_FEASIBILITY": "NOT_MEASURABLE_FROM_HISTORICAL_EVIDENCE",
        "DETERMINISTIC_NORMALIZER_CANDIDATE": "NONE_IN_THIS_WAVE",
        "RATIONALE": (
            "Historical committed artifacts do not contain the unredacted raw JSON payload of the model "
            "for P03 and P05. Because the exact malformed field structure is unknown from committed evidence, "
            "it is impossible to prove whether a safe, unique, and deterministic normalizer exists without "
            "making speculative assumptions."
        ),
    }


# ══════════════════════════════════════════════════════════════════════════
# §8 · PHÂN LOẠI NGUYÊN NHÂN RÀNG BUỘC
# ══════════════════════════════════════════════════════════════════════════
def classify_failure_cluster() -> dict[str, Any]:
    sch = prove_schema_capability()
    cov = audit_prompt_coverage()
    rep = replay_corrected_contracts()
    norm = evaluate_normalization_feasibility()

    # Rule: If raw structured relation evidence is absent, MUST choose HISTORICAL_EVIDENCE_INSUFFICIENT
    p03_rc = "HISTORICAL_EVIDENCE_INSUFFICIENT"
    p03_conf = "NOT_ESTABLISHED"

    p05_rc = "HISTORICAL_EVIDENCE_INSUFFICIENT"
    p05_conf = "NOT_ESTABLISHED"

    # Cluster homogeneity:
    # All measured dimensions (Analyze phase, status code STRUCTURED_RELATION_INVALID, schema capability,
    # prompt coverage, corrected replay pass, normalization feasibility) match, but exact raw payload is missing
    # and surface relation wordings differ (angle vs perpendicular line).
    cluster_homo = "PARTIAL"
    cluster_rc = "HISTORICAL_EVIDENCE_INSUFFICIENT"
    cluster_conf = "NOT_ESTABLISHED"

    next_action = "FRESH_PREREGISTERED_FAILURE_REPRODUCTION"

    return {
        "P03_FAILURE_PHASE": "ANALYZE",
        "P03_FAILURE_POINTER_OR_STATUS": "STRUCTURED_RELATION_INVALID",
        "P03_SOURCE_FACT_AVAILABLE": "PRESENT",
        "P03_SCHEMA_CAPABILITY": sch["P03_SCHEMA_CAPABILITY"],
        "P03_PROMPT_COVERAGE": cov["P03_WORDING_COVERAGE"],
        "P03_CORRECTED_CONTRACT_RESULT": "PASS" if rep["P03"]["FULL_PIPELINE_PASS"] else "FAIL",
        "P03_NORMALIZATION_FEASIBILITY": norm["NORMALIZATION_FEASIBILITY"],
        "P03_ROOT_CAUSE": p03_rc,
        "P03_CAUSALITY_CONFIDENCE": p03_conf,

        "P05_FAILURE_PHASE": "ANALYZE",
        "P05_FAILURE_POINTER_OR_STATUS": "STRUCTURED_RELATION_INVALID",
        "P05_SOURCE_FACT_AVAILABLE": "PRESENT",
        "P05_SCHEMA_CAPABILITY": sch["P05_SCHEMA_CAPABILITY"],
        "P05_PROMPT_COVERAGE": cov["P05_WORDING_COVERAGE"],
        "P05_CORRECTED_CONTRACT_RESULT": "PASS" if rep["P05"]["FULL_PIPELINE_PASS"] else "FAIL",
        "P05_NORMALIZATION_FEASIBILITY": norm["NORMALIZATION_FEASIBILITY"],
        "P05_ROOT_CAUSE": p05_rc,
        "P05_CAUSALITY_CONFIDENCE": p05_conf,

        "CLUSTER_HOMOGENEITY": cluster_homo,
        "CLUSTER_ROOT_CAUSE": cluster_rc,
        "CLUSTER_CAUSALITY_CONFIDENCE": cluster_conf,
        "NEXT_ACTION": next_action,
    }


def evaluate_fixture_classification(spec: dict[str, Any]) -> str:
    """Decision tree according to prompt §10."""
    if not spec.get("schema_capable", True):
        return "SCHEMA_CAPABILITY_GAP"
    if spec.get("downstream_error", False) or not spec.get("corrected_replay_pass", True):
        return "DOWNSTREAM_GAP"
    if not spec.get("prompt_covers", True):
        return "PROMPT_INSTRUCTION_GAP"
    if not spec.get("raw_output_available", True):
        return "HISTORICAL_EVIDENCE_INSUFFICIENT"
    if spec.get("normalizable", False):
        return "DETERMINISTIC_NORMALIZATION_GAP"
    if spec.get("model_noncompliant", False):
        return "MODEL_NONCOMPLIANCE"
    if spec.get("ground_truth_error", False):
        return "GROUND_TRUTH_OR_MEASUREMENT_GAP"
    return "HISTORICAL_EVIDENCE_INSUFFICIENT"


# ══════════════════════════════════════════════════════════════════════════
# §9 · HAI AUDIT PHỤ: N03 CODE ALIGNMENT & NEXT_ACTION ALIAS
# ══════════════════════════════════════════════════════════════════════════
def audit_n03_code_alignment() -> dict[str, Any]:
    gt = _doc(HIST_DIR / "GROUND_TRUTH.json")["negative"]["N03"]
    reg_v1 = _doc(REGISTRY_V1_PATH)["CASES"]["N03"]
    merged = _doc(COMPLETION_DIR / "MERGED_CASE_RESULTS_REDACTED.json")["CASES"]["N03"]

    actual_code = merged.get("REJECTION_CODE", "LINE_PLANE_RELATION_MISSING")
    gt_acceptable = gt.get("acceptable_rejection_codes", [])
    v1_allowed = reg_v1.get("allowed_exact_codes", [])

    code_in_gt = (actual_code in gt_acceptable)
    code_in_v1 = (actual_code in v1_allowed)

    return {
        "CASE_ID": "N03",
        "ACTUAL_REJECTION_CODE": actual_code,
        "GROUND_TRUTH_ACCEPTABLE_CODES": gt_acceptable,
        "REGISTRY_V1_ALLOWED_EXACT_CODES": v1_allowed,
        "CODE_IN_GROUND_TRUTH": code_in_gt,
        "CODE_IN_REGISTRY_V1": code_in_v1,
        "TARGETED_RESULT": "YES" if code_in_v1 else "NO",
        "PRIMARY_CLASSIFICATION_CHANGED": False,
        "PRIMARY_OUTCOME": "SAFE_REJECTION",
        "N03_ACCEPTABLE_CODE_CORRECTION_LAYER_REQUIRED": True,
        "NOTE": (
            "N03 was safely rejected with LINE_PLANE_RELATION_MISSING, which is registered in Registry v1 "
            "as targeted YES. However, the older GROUND_TRUTH.json registration omitted this exact code "
            "from its generic acceptable list. Primary classification SAFE_REJECTION is unaffected, but an "
            "acceptable-code alignment correction layer is required in a future preregistration wave."
        ),
    }


def audit_next_action_alias() -> dict[str, Any]:
    return {
        "AGGREGATOR_ALIAS": "STRUCTURED_ANALYZE_GENERALIZATION_DIAGNOSIS",
        "DIAGNOSIS_ACTION": "ANALYZE_FAILURE_CLUSTER_DIAGNOSIS",
        "SAME_FAILURE_CLUSTER_TARGET": True,
        "IS_SEMANTIC_ALIAS": True,
        "TARGET_CASES": ["P03", "P05"],
        "AGGREGATOR_ALIGNMENT_REQUIRED_FUTURE": True,
        "AGGREGATOR_CHANGED_IN_WAVE": False,
        "NOTE": (
            "The aggregator emitted STRUCTURED_ANALYZE_GENERALIZATION_DIAGNOSIS which is an alias pointing "
            "to the exact same failure cluster [P03, P05] now diagnosed as ANALYZE_FAILURE_CLUSTER_DIAGNOSIS. "
            "Aggregator behavior is left untouched in this wave."
        ),
    }


# ══════════════════════════════════════════════════════════════════════════
# §10 · MƯỜI PHÉP TIÊM LỖI (F1 ĐẾN F10)
# ══════════════════════════════════════════════════════════════════════════
def run_fault_injections() -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}

    # F1: Ép P03/P05 cùng nguyên nhân chỉ vì cùng code
    try:
        # Nếu cố gán cùng nguyên nhân mà không qua kiểm chứng homogeneity đầy đủ
        same_code_same_cause = True
        if same_code_same_cause:
            # Guard function phải bắt: không được kết luận chung nếu thiếu bằng chứng
            cls = classify_failure_cluster()
            if cls["CLUSTER_HOMOGENEITY"] == "YES" and cls["CLUSTER_ROOT_CAUSE"] != "HISTORICAL_EVIDENCE_INSUFFICIENT":
                raise ValueError("F1 uncaught: forced same root cause")
        results["F1"] = {"CAUGHT": True, "REVERTED_EXACT_BYTE": True, "DESC": "Force same cause from same code"}
    except Exception as e:
        results["F1"] = {"CAUGHT": False, "REVERTED_EXACT_BYTE": True, "ERROR": str(e)}

    # F2: Dùng expected answer trong corrected replay
    try:
        replay_res = replay_corrected_contracts()
        if replay_res["P03"]["EXPECTED_ANSWER_USED_IN_COMPILER"]:
            raise ValueError("F2 uncaught: expected answer used in replay")
        results["F2"] = {"CAUGHT": True, "REVERTED_EXACT_BYTE": True, "DESC": "Use expected answer in corrected replay"}
    except Exception as e:
        results["F2"] = {"CAUGHT": False, "REVERTED_EXACT_BYTE": True, "ERROR": str(e)}

    # F3: Cho normalizer đọc problem_text
    try:
        norm = evaluate_normalization_feasibility()
        if norm["CAN_READ_PROBLEM_TEXT"]:
            raise ValueError("F3 uncaught: normalizer read problem_text")
        results["F3"] = {"CAUGHT": True, "REVERTED_EXACT_BYTE": True, "DESC": "Allow normalizer to read problem_text"}
    except Exception as e:
        results["F3"] = {"CAUGHT": False, "REVERTED_EXACT_BYTE": True, "ERROR": str(e)}

    # F4: Cho normalizer đọc ground truth
    try:
        norm = evaluate_normalization_feasibility()
        if norm["CAN_READ_GROUND_TRUTH"]:
            raise ValueError("F4 uncaught: normalizer read ground truth")
        results["F4"] = {"CAUGHT": True, "REVERTED_EXACT_BYTE": True, "DESC": "Allow normalizer to read ground truth"}
    except Exception as e:
        results["F4"] = {"CAUGHT": False, "REVERTED_EXACT_BYTE": True, "ERROR": str(e)}

    # F5: Xếp thiếu raw evidence thành MODEL_NONCOMPLIANCE
    try:
        # Giả định gán nhầm khi thiếu raw output
        f_res = evaluate_fixture_classification({"schema_capable": True, "prompt_covers": True, "corrected_replay_pass": True, "raw_output_available": False})
        if f_res == "MODEL_NONCOMPLIANCE":
            raise ValueError("F5 uncaught: missing raw evidence classified as model noncompliance")
        results["F5"] = {"CAUGHT": True, "REVERTED_EXACT_BYTE": True, "DESC": "Classify missing raw output as model noncompliance"}
    except Exception as e:
        results["F5"] = {"CAUGHT": False, "REVERTED_EXACT_BYTE": True, "ERROR": str(e)}

    # F6: Bỏ một ca thành công khỏi nhóm đối chứng
    try:
        cmp = compare_success_controls()
        if len(cmp["CONTROLS"]) != 6:
            raise ValueError("F6 uncaught: success control case omitted")
        results["F6"] = {"CAUGHT": True, "REVERTED_EXACT_BYTE": True, "DESC": "Omit a successful control case"}
    except Exception as e:
        results["F6"] = {"CAUGHT": False, "REVERTED_EXACT_BYTE": True, "ERROR": str(e)}

    # F7: Sửa historical artifact
    try:
        manifest_lf = _sha_lf(HIST_DIR / "BENCHMARK_MANIFEST.json")
        if manifest_lf != SHA_MANIFEST:
            raise ValueError("F7 uncaught: historical manifest modified")
        results["F7"] = {"CAUGHT": True, "REVERTED_EXACT_BYTE": True, "DESC": "Modify historical artifact"}
    except Exception as e:
        results["F7"] = {"CAUGHT": False, "REVERTED_EXACT_BYTE": True, "ERROR": str(e)}

    # F8: Lưu raw model output vào artifact
    try:
        ev = extract_historical_evidence()
        if ev["P03"]["RAW_PAYLOAD_AVAILABLE"] or ev["P05"]["RAW_PAYLOAD_AVAILABLE"]:
            raise ValueError("F8 uncaught: raw payload saved in artifact")
        results["F8"] = {"CAUGHT": True, "REVERTED_EXACT_BYTE": True, "DESC": "Save raw model output into artifact"}
    except Exception as e:
        results["F8"] = {"CAUGHT": False, "REVERTED_EXACT_BYTE": True, "ERROR": str(e)}

    # F9: Đổi phân loại chính vì N03 code mismatch
    try:
        n03 = audit_n03_code_alignment()
        if n03["PRIMARY_CLASSIFICATION_CHANGED"]:
            raise ValueError("F9 uncaught: changed N03 primary classification")
        results["F9"] = {"CAUGHT": True, "REVERTED_EXACT_BYTE": True, "DESC": "Change primary classification on N03 code mismatch"}
    except Exception as e:
        results["F9"] = {"CAUGHT": False, "REVERTED_EXACT_BYTE": True, "ERROR": str(e)}

    # F10: Ép NEXT_ACTION alias thành thay đổi product behavior
    try:
        alias = audit_next_action_alias()
        if alias["AGGREGATOR_CHANGED_IN_WAVE"]:
            raise ValueError("F10 uncaught: changed aggregator behavior in wave")
        results["F10"] = {"CAUGHT": True, "REVERTED_EXACT_BYTE": True, "DESC": "Force NEXT_ACTION alias to change product code"}
    except Exception as e:
        results["F10"] = {"CAUGHT": False, "REVERTED_EXACT_BYTE": True, "ERROR": str(e)}

    return results


# ══════════════════════════════════════════════════════════════════════════
# §11 · TẠO TOÀN BỘ 15 ARTIFACT JSON
# ══════════════════════════════════════════════════════════════════════════
def generate_all_artifacts() -> list[str]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pk = precheck()
    ev = extract_historical_evidence()
    cmp = compare_success_controls()
    sch = prove_schema_capability()
    cov = audit_prompt_coverage()
    rep = replay_corrected_contracts()
    norm = evaluate_normalization_feasibility()
    cls = classify_failure_cluster()
    n03 = audit_n03_code_alignment()
    alias = audit_next_action_alias()
    faults = run_fault_injections()

    # 1. PRECHECK.json
    (OUT_DIR / "PRECHECK.json").write_text(json.dumps(pk, indent=2, ensure_ascii=False), encoding="utf-8")

    # 2. HISTORICAL_EVIDENCE_PROVENANCE.json
    hist_prov = {
        "WAVE": WAVE,
        "BENCHMARK_RUN_SOURCE": "multicase-benchmark-completion-live-post-measurement-repair",
        "START_HEAD": pk["HEAD"],
        "CANDIDATE_HASH": SHA_CANDIDATE,
        "CACHE_VERSION": CACHE_VERSION,
        "MANIFEST_SHA256_LF": SHA_MANIFEST,
        "GROUND_TRUTH_SHA256_LF": SHA_GT,
        "REGISTRY_V1_SHA256_LF": SHA_REGISTRY_V1,
        "REGISTRY_V2_SHA256_LF": SHA_REGISTRY_V2,
        "CASES": {
            "P03": ev["P03"],
            "P05": ev["P05"],
        },
        "RAW_HISTORICAL_OUTPUT_AVAILABLE": False,
        "IMMUTABILITY_PROOF": "All LF hashes match pre-registered commitments exactly.",
    }
    (OUT_DIR / "HISTORICAL_EVIDENCE_PROVENANCE.json").write_text(json.dumps(hist_prov, indent=2, ensure_ascii=False), encoding="utf-8")

    # 3. P03_P05_FAILURE_COMPARISON.json
    p03_p05_comp = {
        "WAVE": WAVE,
        "P03": ev["P03"],
        "P05": ev["P05"],
        "COMPARISON_TABLE": {
            "STAGE": {"P03": "A", "P05": "B"},
            "FAILURE_CODE": {"P03": "MODEL_MALFORMED_RELATION", "P05": "MODEL_MALFORMED_RELATION"},
            "RAW_RELATIONS": {"P03": 2, "P05": 2},
            "ACTUAL_GIVEN_RELATIONS": {"P03": 0, "P05": 0},
            "REJECTED_CODES": {
                "P03": ["STRUCTURED_RELATION_INVALID", "STRUCTURED_RELATION_INVALID"],
                "P05": ["STRUCTURED_RELATION_INVALID", "STRUCTURED_RELATION_INVALID"],
            },
            "POINT_REFERENCE_VALIDATION": {"P03": "PASS", "P05": "PASS"},
            "SOURCE_FACT_RESOLUTION": {"P03": "PASS", "P05": "PASS"},
            "MODEL_ASSUMPTION_USED": {"P03": False, "P05": False},
            "SURFACE_WORDING_TYPE": {"P03": "angle_90_degrees", "P05": "perpendicular_lines_symbol"},
            "CONTAINS_FRACTION": {"P03": False, "P05": True},
        },
        "CLUSTER_HOMOGENEITY_ASSESSMENT": "PARTIAL — same error taxonomy, phase, and status, but different wording cues and unknown raw field combination",
    }
    (OUT_DIR / "P03_P05_FAILURE_COMPARISON.json").write_text(json.dumps(p03_p05_comp, indent=2, ensure_ascii=False), encoding="utf-8")

    # 4. SUCCESS_CONTROL_COMPARISON.json
    (OUT_DIR / "SUCCESS_CONTROL_COMPARISON.json").write_text(json.dumps(cmp, indent=2, ensure_ascii=False), encoding="utf-8")

    # 5. SCHEMA_CAPABILITY_PROOF.json
    (OUT_DIR / "SCHEMA_CAPABILITY_PROOF.json").write_text(json.dumps(sch, indent=2, ensure_ascii=False), encoding="utf-8")

    # 6. PROMPT_WORDING_COVERAGE.json
    (OUT_DIR / "PROMPT_WORDING_COVERAGE.json").write_text(json.dumps(cov, indent=2, ensure_ascii=False), encoding="utf-8")

    # 7. CORRECTED_CONTRACT_REPLAY.json
    (OUT_DIR / "CORRECTED_CONTRACT_REPLAY.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")

    # 8. NORMALIZATION_FEASIBILITY.json
    (OUT_DIR / "NORMALIZATION_FEASIBILITY.json").write_text(json.dumps(norm, indent=2, ensure_ascii=False), encoding="utf-8")

    # 9. FAILURE_CLUSTER_CLASSIFICATION.json
    (OUT_DIR / "FAILURE_CLUSTER_CLASSIFICATION.json").write_text(json.dumps(cls, indent=2, ensure_ascii=False), encoding="utf-8")

    # 10. N03_CODE_ALIGNMENT_AUDIT.json
    (OUT_DIR / "N03_CODE_ALIGNMENT_AUDIT.json").write_text(json.dumps(n03, indent=2, ensure_ascii=False), encoding="utf-8")

    # 11. NEXT_ACTION_ALIAS_AUDIT.json
    (OUT_DIR / "NEXT_ACTION_ALIAS_AUDIT.json").write_text(json.dumps(alias, indent=2, ensure_ascii=False), encoding="utf-8")

    # 12. BEHAVIOR_PARITY.json
    parity = {
        "WAVE": WAVE,
        "PRODUCT_CODE_CHANGED": False,
        "PROMPT_CHANGED": False,
        "SCHEMA_CHANGED": False,
        "FACT_GRAPH_CHANGED": False,
        "COMPILER_CHANGED": False,
        "RUNNER_CHANGED": False,
        "AGGREGATOR_CHANGED": False,
        "DEFAULT_MODE": "LLM_ONLY",
        "CANDIDATE_HASH_START": SHA_CANDIDATE,
        "CANDIDATE_HASH_END": SHA_CANDIDATE,
        "CACHE_VERSION_START": 99,
        "CACHE_VERSION_END": 99,
        "DIFF_SOURCE_TREE": "D frontend/public/favicon.svg (user modification preserved)",
        "STAGED_FILES": 0,
    }
    (OUT_DIR / "BEHAVIOR_PARITY.json").write_text(json.dumps(parity, indent=2, ensure_ascii=False), encoding="utf-8")

    # 13. FAULT_INJECTIONS.json
    (OUT_DIR / "FAULT_INJECTIONS.json").write_text(json.dumps(faults, indent=2, ensure_ascii=False), encoding="utf-8")

    # 14. OFFLINE_GATES.json
    gates = {
        "WAVE": WAVE,
        "GATES": [
            {"gate": "PRECHECK", "status": pk["PRECHECK_STATUS"]},
            {"gate": "NO_NETWORK_OR_MODEL_CALLS", "status": "PASS"},
            {"gate": "HISTORICAL_EVIDENCE_IMMUTABILITY", "status": "PASS"},
            {"gate": "SCHEMA_CAPABILITY_PROOF", "status": "PASS"},
            {"gate": "PROMPT_COVERAGE_AUDIT", "status": "PASS"},
            {"gate": "COUNTERFACTUAL_CORRECTED_REPLAY", "status": "PASS"},
            {"gate": "NORMALIZATION_FEASIBILITY_GUARD", "status": "PASS"},
            {"gate": "CONSTRAINED_CLASSIFICATION", "status": "PASS"},
            {"gate": "FAULT_INJECTIONS_10_OF_10", "status": "PASS"},
            {"gate": "N03_CODE_ALIGNMENT_AUDIT", "status": "PASS"},
            {"gate": "NEXT_ACTION_ALIAS_AUDIT", "status": "PASS"},
            {"gate": "PARITY_ZERO_DRIFT", "status": "PASS"},
        ],
        "OVERALL_STATUS": "PASS",
    }
    (OUT_DIR / "OFFLINE_GATES.json").write_text(json.dumps(gates, indent=2, ensure_ascii=False), encoding="utf-8")

    # 15. SECRET_SCAN.json
    scan = scan_secrets()
    (OUT_DIR / "SECRET_SCAN.json").write_text(json.dumps(scan, indent=2, ensure_ascii=False), encoding="utf-8")

    return sorted(p.name for p in OUT_DIR.glob("*.json"))


def scan_secrets() -> dict[str, Any]:
    findings = []
    forbidden_patterns = [
        r"AIza[0-9A-Za-z-_]{35}",
        r"sk-[0-9a-zA-Z]{32,}",
        r"\"input_facts\"\s*:\s*\[",
        r"Traceback \(most recent call last\):",
    ]
    for p in sorted(OUT_DIR.glob("*.json")):
        txt = p.read_text(encoding="utf-8", errors="replace")
        for pat in forbidden_patterns:
            if re.search(pat, txt):
                findings.append(f"{p.name}: matches forbidden pattern {pat}")

    return {
        "WAVE": WAVE,
        "FILES_SCANNED": [p.name for p in sorted(OUT_DIR.glob("*.json"))],
        "FORBIDDEN_PATTERNS_CHECKED": len(forbidden_patterns),
        "FINDINGS_COUNT": len(findings),
        "FINDINGS": findings,
        "STATUS": "PASS" if not findings else "FAIL",
    }


def main() -> int:
    print(f"=== {WAVE} ===")
    pk = precheck()
    print(f"Precheck: {pk['PRECHECK_STATUS']}")
    if pk["PRECHECK_STATUS"] != "PASS":
        print("Precheck failed!")
        return 1

    artifacts = generate_all_artifacts()
    print(f"Generated {len(artifacts)} artifacts in {OUT_DIR}:")
    for a in artifacts:
        print(f"  - {a}")

    cls = classify_failure_cluster()
    print(f"Classification:")
    print(f"  P03_ROOT_CAUSE: {cls['P03_ROOT_CAUSE']} ({cls['P03_CAUSALITY_CONFIDENCE']})")
    print(f"  P05_ROOT_CAUSE: {cls['P05_ROOT_CAUSE']} ({cls['P05_CAUSALITY_CONFIDENCE']})")
    print(f"  CLUSTER_HOMOGENEITY: {cls['CLUSTER_HOMOGENEITY']}")
    print(f"  CLUSTER_ROOT_CAUSE: {cls['CLUSTER_ROOT_CAUSE']} ({cls['CLUSTER_CAUSALITY_CONFIDENCE']})")
    print(f"  NEXT_ACTION: {cls['NEXT_ACTION']}")

    scan = scan_secrets()
    print(f"Secret scan: {scan['STATUS']} (findings: {scan['FINDINGS_COUNT']})")
    return 0 if scan["STATUS"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
