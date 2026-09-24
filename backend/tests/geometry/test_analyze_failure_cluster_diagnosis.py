# -*- coding: utf-8 -*-
"""Test suite for ANALYZE_FAILURE_CLUSTER_DIAGNOSIS (P03/P05 offline diagnosis wave).

Ràng buộc wave:
- 0 request mạng · 0 request Gemini · không nạp .env.
- Đo riêng P03 và P05; không ép cùng nguyên nhân chỉ vì cùng mã.
- Thiếu raw model output ⇒ bắt buộc phân loại HISTORICAL_EVIDENCE_INSUFFICIENT.
- Schema capability & prompt coverage & counterfactual replay được kiểm offline.
- Đối chứng âm & 10 phép tiêm lỗi (F1 - F10) bắt buộc bị chặn.
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
REPO = GOC.parent
for _p in (str(GOC), str(GOC / "scripts"), str(Path(__file__).parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import diagnose_analyze_failure_cluster as D


# ══ §1 · CỔNG AN TOÀN: KHÔNG MẠNG, KHÔNG KHOÁ, KHÔNG DOTENV ════════════════
def test_cong_khong_mang_khong_khoa_khong_dotenv():
    assert "GEMINI_API_KEY" not in os.environ
    assert os.environ.get("ALLOW_LIVE_AI") != "1"
    # Kiểm module script không nạp dotenv hay app.main
    script_path = GOC / "scripts" / "diagnose_analyze_failure_cluster.py"
    cay = ast.parse(script_path.read_text(encoding="utf-8"))
    nhap = {n.module for n in ast.walk(cay) if isinstance(n, ast.ImportFrom) and n.module} | {
        a.name for n in ast.walk(cay) if isinstance(n, ast.Import) for a in n.names}
    assert not {m for m in nhap if m and (m.startswith("dotenv") or m in ("app.main", "app.persistence.db"))}


# ══ §2 · TIỀN KIỂM: HASH, BẤT BIẾN, KHÔNG RAW OUTPUT ═══════════════════════
def test_tien_kiem_kho():
    pk = D.precheck()
    curr_branch = subprocess.run(["git", "branch", "--show-current"], cwd=D.REPO,
                                 capture_output=True, text=True).stdout.strip()
    assert pk["BRANCH"] in (curr_branch, "feat/photo-problem-to-scene", "HEAD")
    is_ancestor = (subprocess.run(["git", "merge-base", "--is-ancestor", "12df583", pk["HEAD"]],
                                  cwd=D.REPO).returncode == 0)
    assert pk["HEAD"].startswith("12df583") or is_ancestor
    is_main_ancestor = (subprocess.run(["git", "merge-base", "--is-ancestor", "085cae6", pk["MAIN"]],
                                       cwd=D.REPO).returncode == 0)
    assert pk["MAIN"].startswith("085cae6") or is_main_ancestor
    assert pk["CANDIDATE_VERIFY"] is True
    assert pk["CACHE_IDENTITY_VERIFY"] is True
    assert pk["CACHE_VERSION"] == 99
    assert pk["MANIFEST_LF_MATCH"] is True
    assert pk["GROUND_TRUTH_LF_MATCH"] is True
    assert pk["REGISTRY_V1_LF_MATCH"] is True
    assert pk["REGISTRY_V2_LF_MATCH"] is True
    assert pk["RAW_HISTORICAL_OUTPUT_AVAILABLE"] is False
    assert pk["PRECHECK_STATUS"] == "PASS"


# ══ §3 · TÁI HIỆN MÃ LỖI LỊCH SỬ TỪ ARTIFACT ══════════════════════════════
def test_tai_hien_ma_loi_p03_va_p05():
    ev = D.extract_historical_evidence()
    assert ev["P03"]["HISTORICAL_FAILURE_CODE"] == "MODEL_MALFORMED_RELATION"
    assert ev["P03"]["RAW_RELATION_COUNT"] == 2
    assert ev["P03"]["ACTUAL_GIVEN_RELATION_COUNT"] == 0
    assert ev["P03"]["POINT_REFERENCE_VALIDATION"] == "PASS"
    assert ev["P03"]["SOURCE_FACT_RESOLUTION"] == "PASS"
    assert ev["P03"]["RAW_PAYLOAD_AVAILABLE"] is False
    assert len(ev["P03"]["REJECTED_RELATION_CODES"]) == 2
    assert ev["P03"]["REJECTED_RELATION_CODES"][0]["code"] == "STRUCTURED_RELATION_INVALID"
    assert ev["P03"]["REJECTED_RELATION_CODES"][1]["code"] == "STRUCTURED_RELATION_INVALID"

    assert ev["P05"]["HISTORICAL_FAILURE_CODE"] == "MODEL_MALFORMED_RELATION"
    assert ev["P05"]["RAW_RELATION_COUNT"] == 2
    assert ev["P05"]["ACTUAL_GIVEN_RELATION_COUNT"] == 0
    assert ev["P05"]["POINT_REFERENCE_VALIDATION"] == "PASS"
    assert ev["P05"]["SOURCE_FACT_RESOLUTION"] == "PASS"
    assert ev["P05"]["RAW_PAYLOAD_AVAILABLE"] is False
    assert len(ev["P05"]["REJECTED_RELATION_CODES"]) == 2
    assert ev["P05"]["REJECTED_RELATION_CODES"][0]["code"] == "STRUCTURED_RELATION_INVALID"
    assert ev["P05"]["REJECTED_RELATION_CODES"][1]["code"] == "STRUCTURED_RELATION_INVALID"


# ══ §4 · SO SÁNH VỚI NHÓM ĐỐI CHỨNG THÀNH CÔNG 6 CA ════════════════════════
def test_so_sanh_nhom_doi_chung_thanh_cong():
    cmp = D.compare_success_controls()
    assert cmp["CONTROLS"] == ["P01", "P02", "P04", "P06", "P07", "P08"]
    assert len(cmp["CONTROLS"]) == 6
    for cid in cmp["CONTROLS"]:
        assert cmp["CASE_DATA"][cid]["OUTCOME"] == "FULL_PIPELINE_PASS"
        assert cmp["CASE_DATA"][cid]["CORRECT_RELATIONS"] == 2
    # Trục chẩn đoán đầy đủ
    assert "AXES" in cmp
    assert "DEFINITIONAL_NORMALIZATION" in cmp["AXES"]
    assert "EXPLICIT_SURFACE_RELATION" in cmp["AXES"]
    assert "CANONICALIZATION" in cmp["AXES"]


# ══ §5 · KIỂM NĂNG LỰC SCHEMA ══════════════════════════════════════════════
def test_kiem_nang_luc_schema_p03_p05():
    sch = D.prove_schema_capability()
    assert sch["P03_VALID_CONTRACT_PASS"] is True
    assert sch["P05_VALID_CONTRACT_PASS"] is True
    assert sch["P03_SCHEMA_CAPABILITY"] == "PRESENT"
    assert sch["P05_SCHEMA_CAPABILITY"] == "PRESENT"
    assert sch["SCHEMA_CHANGE_REQUIRED"] is False


# ══ §6 · KIỂM PROMPT COVERAGE ══════════════════════════════════════════════
def test_kiem_prompt_coverage():
    cov = D.audit_prompt_coverage()
    assert cov["P03_WORDING_COVERAGE"] == "EXPLICITLY_COVERED"
    assert cov["P05_WORDING_COVERAGE"] in ("EXPLICITLY_COVERED", "IMPLICITLY_COVERED")
    assert cov["PROMPT_PROPERTIES"]["DEFINITIONAL_NORMALIZATION"] == "EXPLICITLY_COVERED"
    assert cov["PROMPT_PROPERTIES"]["RIGHT_ANGLE_90_DEG"] == "EXPLICITLY_COVERED"
    assert cov["PROMPT_PROPERTIES"]["PERPENDICULAR_LINES"] == "EXPLICITLY_COVERED"
    assert cov["PROMPT_PROPERTIES"]["PERPENDICULAR_LINE_PLANE"] == "EXPLICITLY_COVERED"
    assert cov["PROMPT_PROPERTIES"]["NO_DERIVED_AS_GIVEN"] == "EXPLICITLY_COVERED"
    assert cov["PROMPT_PROPERTIES"]["SOURCE_FACT_ID"] == "EXPLICITLY_COVERED"
    assert cov["PROMPT_PROPERTIES"]["MODEL_ASSUMPTION"] == "EXPLICITLY_COVERED"
    assert cov["PROMPT_CHANGED"] is False


# ══ §7 · COUNTERFACTUAL CORRECTED-CONTRACT REPLAY ══════════════════════════
def test_counterfactual_corrected_contract_replay():
    rep = D.replay_corrected_contracts()
    assert rep["P03"]["FULL_PIPELINE_PASS"] is True
    assert rep["P03"]["ANSWER_OK"] is True
    assert rep["P03"]["TOPOLOGY_RESULT"] == "PASS"
    assert rep["P03"]["DETERMINISTIC_PASS"] is True
    assert rep["P03"]["PERMUTATION_INVARIANT_PASS"] is True

    assert rep["P05"]["FULL_PIPELINE_PASS"] is True
    assert rep["P05"]["ANSWER_OK"] is True
    assert rep["P05"]["TOPOLOGY_RESULT"] == "PASS"
    assert rep["P05"]["DETERMINISTIC_PASS"] is True
    assert rep["P05"]["PERMUTATION_INVARIANT_PASS"] is True
    assert rep["P05"]["FRACTIONAL_LENGTH_HANDLED"] is True


# ══ §8 · ĐÁNH GIÁ KHẢ NĂNG CHUẨN HOÁ TẤT ĐỊNH ══════════════════════════════
def test_danh_gia_kha_nang_chuan_hoa_tat_dinh():
    norm = D.evaluate_normalization_feasibility()
    # Bắt buộc là NOT_MEASURABLE_FROM_HISTORICAL_EVIDENCE vì không có raw output
    assert norm["NORMALIZATION_FEASIBILITY"] == "NOT_MEASURABLE_FROM_HISTORICAL_EVIDENCE"
    assert norm["CAN_READ_PROBLEM_TEXT"] is False
    assert norm["CAN_READ_GROUND_TRUTH"] is False
    assert norm["CAN_READ_EXPECTED_ANSWER"] is False
    assert norm["CAN_GUESS_FROM_CASE_ID"] is False
    assert norm["DETERMINISTIC_NORMALIZER_CANDIDATE"] == "NONE_IN_THIS_WAVE"


# ══ §9 · PHÂN LOẠI NGUYÊN NHÂN RÀNG BUỘC ══════════════════════════════════
def test_phan_loai_nguyen_nhan_rang_buoc():
    cls = D.classify_failure_cluster()
    assert cls["P03_ROOT_CAUSE"] == "HISTORICAL_EVIDENCE_INSUFFICIENT"
    assert cls["P03_CAUSALITY_CONFIDENCE"] == "NOT_ESTABLISHED"
    assert cls["P05_ROOT_CAUSE"] == "HISTORICAL_EVIDENCE_INSUFFICIENT"
    assert cls["P05_CAUSALITY_CONFIDENCE"] == "NOT_ESTABLISHED"
    assert cls["CLUSTER_HOMOGENEITY"] in ("PARTIAL", "YES")
    assert cls["CLUSTER_ROOT_CAUSE"] == "HISTORICAL_EVIDENCE_INSUFFICIENT"
    assert cls["CLUSTER_CAUSALITY_CONFIDENCE"] == "NOT_ESTABLISHED"
    assert cls["NEXT_ACTION"] == "FRESH_PREREGISTERED_FAILURE_REPRODUCTION"


# ══ §10 · ĐỐI CHỨNG ÂM & FIXTURES PHÂN BIỆT NGUYÊN NHÂN ════════════════════
def test_fixtures_phan_biet_nguyen_nhan():
    f_schema = D.evaluate_fixture_classification({
        "schema_capable": False,
        "prompt_covers": True,
        "corrected_replay_pass": False,
        "raw_output_available": True,
        "normalizable": False,
    })
    assert f_schema == "SCHEMA_CAPABILITY_GAP"

    f_prompt = D.evaluate_fixture_classification({
        "schema_capable": True,
        "prompt_covers": False,
        "corrected_replay_pass": True,
        "raw_output_available": True,
        "normalizable": False,
    })
    assert f_prompt == "PROMPT_INSTRUCTION_GAP"

    f_norm = D.evaluate_fixture_classification({
        "schema_capable": True,
        "prompt_covers": True,
        "corrected_replay_pass": True,
        "raw_output_available": True,
        "normalizable": True,
    })
    assert f_norm == "DETERMINISTIC_NORMALIZATION_GAP"

    f_model = D.evaluate_fixture_classification({
        "schema_capable": True,
        "prompt_covers": True,
        "corrected_replay_pass": True,
        "raw_output_available": True,
        "normalizable": False,
        "model_noncompliant": True,
    })
    assert f_model == "MODEL_NONCOMPLIANCE"

    f_downstream = D.evaluate_fixture_classification({
        "schema_capable": True,
        "prompt_covers": True,
        "corrected_replay_pass": False,
        "raw_output_available": True,
        "downstream_error": True,
    })
    assert f_downstream == "DOWNSTREAM_GAP"

    f_insufficient = D.evaluate_fixture_classification({
        "schema_capable": True,
        "prompt_covers": True,
        "corrected_replay_pass": True,
        "raw_output_available": False,
    })
    assert f_insufficient == "HISTORICAL_EVIDENCE_INSUFFICIENT"


# ══ §11 · HAI AUDIT PHỤ: N03 CODE ALIGNMENT & NEXT_ACTION ALIAS ════════════
def test_hai_audit_phu():
    n03 = D.audit_n03_code_alignment()
    assert n03["ACTUAL_REJECTION_CODE"] == "LINE_PLANE_RELATION_MISSING"
    assert "LINE_PLANE_RELATION_MISSING" not in n03["GROUND_TRUTH_ACCEPTABLE_CODES"]
    assert "LINE_PLANE_RELATION_MISSING" in n03["REGISTRY_V1_ALLOWED_EXACT_CODES"]
    assert n03["TARGETED_RESULT"] == "YES"
    assert n03["PRIMARY_CLASSIFICATION_CHANGED"] is False
    assert n03["N03_ACCEPTABLE_CODE_CORRECTION_LAYER_REQUIRED"] is True

    alias = D.audit_next_action_alias()
    assert alias["AGGREGATOR_ALIAS"] == "STRUCTURED_ANALYZE_GENERALIZATION_DIAGNOSIS"
    assert alias["DIAGNOSIS_ACTION"] == "ANALYZE_FAILURE_CLUSTER_DIAGNOSIS"
    assert alias["SAME_FAILURE_CLUSTER_TARGET"] is True
    assert alias["IS_SEMANTIC_ALIAS"] is True
    assert alias["AGGREGATOR_ALIGNMENT_REQUIRED_FUTURE"] is True
    assert alias["AGGREGATOR_CHANGED_IN_WAVE"] is False


# ══ §12 · MƯỜI PHÉP TIÊM LỖI (F1 ĐẾN F10) ═════════════════════════════════
def test_10_phep_tiem_loi():
    kq = D.run_fault_injections()
    assert len(kq) == 10
    for f_id, res in kq.items():
        assert res["CAUGHT"] is True, f"Phép tiêm lỗi {f_id} không bị bắt!"
        assert res["REVERTED_EXACT_BYTE"] is True, f"Phép tiêm lỗi {f_id} chưa hoàn nguyên sạch!"
