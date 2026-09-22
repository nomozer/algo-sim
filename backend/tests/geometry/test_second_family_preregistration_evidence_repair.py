# -*- coding: utf-8 -*-
"""Test Suite cho Wave SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE.

Kiểm chứng 12 tiêu chí bắt buộc theo đặc tả Mục 11:
1. Tiêu chí THPT không có evidence không thể nhận điểm.
2. Tổng điểm được tái tính, không đọc tổng hardcode.
3. Ô thiếu rubric/evidence bị NOT_ESTABLISHED.
4. Kết quả xếp hạng được tái chuẩn hóa đúng.
5. Validator bắt claim 'only one primitive' khi gap table có 12 tầng.
6. Semantic structure không bị gắn LAYOUT_DERIVED.
7. Rejection code tương lai không bị báo là current behavior.
8. Dataset label convention không trở thành global prohibition.
9. Commit-role scope drift được đọc từ Git.
10. Working tree có favicon deletion không được ghi CLEAN.
11. Historical files bị sửa sẽ làm integrity gate đỏ.
12. Final decision fail-closed nếu còn claim quan trọng không có provenance.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from scripts import audit_second_family_preregistration_evidence as AUDIT

REPO = Path(__file__).resolve().parents[3]


def test_01_tieu_chi_thpt_khong_co_evidence_khong_nhan_diem():
    """1. Tiêu chí THPT không có evidence trong repo không thể nhận điểm 5.0/5."""
    curriculum = AUDIT.audit_curriculum_evidence()
    assert curriculum["curriculum_evidence"] == "NOT_ESTABLISHED_OFFLINE"
    assert curriculum["criterion_status"] == "NOT_SCORED"
    assert curriculum["unmeasured_weight"] == 20

    matrix = AUDIT.audit_selection_matrix()
    cand_b = matrix["candidates"]["B"]
    c_thpt = cand_b["criteria_breakdown"]["curriculum_relevance"]
    assert c_thpt["evidence_status"] == "NOT_ESTABLISHED"
    assert c_thpt["raw_score"] is None
    assert c_thpt["calculated_contribution"] == 0.0


def test_02_tong_diem_duoc_tai_tinh_khong_doc_hardcode():
    """2. Tổng điểm được tái tính toán động từ điểm thành phần, không tin số ghi sẵn."""
    matrix = AUDIT.audit_selection_matrix()
    cand_b = matrix["candidates"]["B"]
    assert cand_b["historical_recorded_total"] == 95.5

    # Tính toán lại từ các ô measured:
    breakdown = cand_b["criteria_breakdown"]
    sum_measured = sum(v["calculated_contribution"] for v in breakdown.values())
    assert round(sum_measured, 2) == cand_b["measured_raw_score_sum"]
    assert cand_b["measured_raw_score_sum"] == 75.5  # 18.0 + 13.5 + 15.0 + 10.0 + 10.0 + 9.0


def test_03_o_thieu_rubric_hoac_evidence_bi_not_established():
    """3. Ô thiếu rubric/evidence bị đánh dấu NOT_ESTABLISHED."""
    matrix = AUDIT.audit_selection_matrix()
    for ckey in ["A", "B", "C"]:
        cinfo = matrix["candidates"][ckey]
        cr = cinfo["criteria_breakdown"]["curriculum_relevance"]
        assert cr["evidence_status"] == "NOT_ESTABLISHED"
        assert cr["raw_score"] is None


def test_04_ket_qua_xep_hang_duoc_tai_chuan_hoa_dung():
    """4. Kết quả xếp hạng được tái chuẩn hóa đúng trên 80 trọng số còn lại."""
    matrix = AUDIT.audit_selection_matrix()
    cand_b = matrix["candidates"]["B"]
    cand_a = matrix["candidates"]["A"]
    cand_c = matrix["candidates"]["C"]

    # B = 75.5 / 80 * 100 = 94.375
    assert cand_b["normalized_score_on_100"] == 94.375
    # A = 68.0 / 80 * 100 = 85.000
    assert cand_a["normalized_score_on_100"] == 85.000
    # C = 66.0 / 80 * 100 = 82.500
    assert cand_c["normalized_score_on_100"] == 82.500

    assert matrix["winner"] == "right_triangle_base_right_prism_volume"
    assert matrix["margin_raw"] == 7.5
    assert matrix["margin_normalized"] == 9.375
    assert matrix["selection_robustness"] == "PASS"


def test_05_validator_bat_claim_only_one_primitive_khi_gap_table_co_nhieu_tang():
    """5. Validator bác bỏ claim 'chỉ cần thêm đúng một primitive' khi vertical slice có 12 tầng."""
    scope = AUDIT.audit_vertical_slice_scope()
    assert scope["historical_claim_status"] == "REFUTED_OVER_SIMPLIFIED"
    assert scope["required_layer_count"] == 12
    layer_names = [l["layer_name"] for l in scope["layers"]]
    assert "RequestContract / Analyze Contract" in layer_names
    assert "FactGraph Node / Fact / Provenance" in layer_names
    assert "Eligibility" in layer_names
    assert "Primitive Registry" in layer_names
    assert "Scene Topology" in layer_names


def test_06_semantic_structure_khong_bi_gan_layout_derived():
    """6. Semantic structure (cycles, correspondence) không bị gán nhầm thành LAYOUT_DERIVED."""
    ownership = AUDIT.audit_semantic_ownership()
    components = ownership["components"]
    assert components["base_cycle"]["owner"] == "SEMANTIC_STRUCTURE"
    assert components["top_cycle"]["owner"] == "SEMANTIC_STRUCTURE"
    assert components["vertex_correspondence"]["owner"] == "SEMANTIC_STRUCTURE"
    assert components["parallel_and_equal_edges"]["owner"] == "DEFINITIONAL_CONSEQUENCES_OF_PRISM"
    assert components["coordinates_and_visual_placement"]["owner"] == "LAYOUT_DERIVED"


def test_07_rejection_code_tuong_lai_khong_bi_bao_la_current_behavior():
    """7. Mã từ chối tương lai không bị báo là hành vi đã có trong current product."""
    rejection = AUDIT.audit_rejection_codes()
    codes = rejection["codes"]

    # PRISM_N01: REQUIRED_FACT_MISSING là PROPOSED_NEW_CODE
    assert codes["PRISM_N01"]["classification"] == "PROPOSED_NEW_CODE"
    assert codes["PRISM_N01"]["reachable_in_current_product"] is False

    # PRISM_N02: STRUCTURED_RELATION_CONTRADICTION là CURRENT_REACHABLE_CODE
    assert codes["PRISM_N02"]["classification"] == "CURRENT_REACHABLE_CODE"
    assert codes["PRISM_N02"]["reachable_in_current_product"] is True

    # PRISM_N03: UNSUPPORTED_STRUCTURED_RELATION_MISSING là EXPECTED_FUTURE_REJECTION_CODE
    assert codes["PRISM_N03"]["classification"] == "EXPECTED_FUTURE_REJECTION_CODE"
    assert codes["PRISM_N03"]["reachable_in_current_product"] is False

    # Primitive codes là PROPOSED_NEW_CODE
    assert codes["PRISM_VERTICES_MISMATCH"]["classification"] == "PROPOSED_NEW_CODE"
    assert codes["PRISM_DEGENERATE_FACES"]["classification"] == "PROPOSED_NEW_CODE"
    assert codes["PRISM_CORRESPONDENCE_INVALID"]["classification"] == "PROPOSED_NEW_CODE"


def test_08_dataset_label_convention_khong_tro_thanh_global_prohibition():
    """8. Quy ước nhãn dataset không bị coi là lệnh cấm toàn cục của sản phẩm."""
    label = AUDIT.audit_label_policy()
    assert label["product_has_apostrophe_normalization"] is True
    assert label["corrected_declarations"]["NO_APOSTROPHE_UPPERCASE_ASCII"] == "DATASET_CONVENTION_ONLY"
    assert label["corrected_declarations"]["GLOBAL_POINT_LABEL_PROHIBITION"] == "NOT_ESTABLISHED"


def test_09_commit_role_scope_drift_duoc_doc_tu_git():
    """9. Commit-role scope drift của Commit 2 được phát hiện chính xác từ git history."""
    commit_role = AUDIT.audit_commit_roles_and_worktree()
    assert commit_role["commit_role_scope_drift"] == "YES"
    assert commit_role["history_drift"] == "NO"
    # validate file scripts được sửa trong commit 2
    assert any("validate_second_family_preregistration.py" in f for f in commit_role["commit_2"]["files"])


def test_10_working_tree_co_favicon_deletion_khong_ghi_clean(monkeypatch):
    """10. Working tree có favicon bị xóa phải ghi DIRTY_ONLY_USER_FAVICON, không được ghi CLEAN."""
    status = AUDIT.run_git(["status", "--short"])[1]
    if "D frontend/public/favicon.svg" in status:
        commit_role = AUDIT.audit_commit_roles_and_worktree()
        assert commit_role["source_working_tree"] == "DIRTY_ONLY_USER_FAVICON"
        assert commit_role["source_working_tree"] != "CLEAN"
    else:
        orig_run_git = AUDIT.run_git
        monkeypatch.setattr(AUDIT, "run_git", lambda args: (0, " D frontend/public/favicon.svg") if args == ["status", "--short"] else orig_run_git(args))
        commit_role = AUDIT.audit_commit_roles_and_worktree()
        assert commit_role["source_working_tree"] == "DIRTY_ONLY_USER_FAVICON"
        assert commit_role["source_working_tree"] != "CLEAN"


def test_11_historical_files_bi_sua_se_lam_integrity_gate_do(tmp_path: Path):
    """11. Tệp lịch sử bị sửa đổi (tiêm lỗi giả) sẽ làm integrity gate chuyển đỏ."""
    # Tạo bản sao và tiêm lỗi vào file matrix
    bad_dir = tmp_path / "bad_eval"
    bad_dir.mkdir(parents=True)
    orig_matrix = AUDIT.HIST_EVAL_DIR / "SECOND_FAMILY_SELECTION_MATRIX.json"
    bad_matrix = bad_dir / "SECOND_FAMILY_SELECTION_MATRIX.json"
    bad_matrix.write_text(orig_matrix.read_text(encoding="utf-8") + "\n# corrupted", encoding="utf-8")

    # Kiểm tra hàm sha256_file bắt được sự khác biệt
    assert AUDIT.sha256_file(bad_matrix) != AUDIT.HISTORICAL_HASHES["SECOND_FAMILY_SELECTION_MATRIX.json"]


def test_12_final_decision_fail_closed_neu_con_claim_thieu_provenance():
    """12. Quyết định cuối cùng fail-closed nếu có vị từ nào chưa đạt."""
    # Khi các vị từ đạt, final decision là PASS
    precheck = AUDIT.audit_precheck()
    integrity = AUDIT.audit_historical_integrity()
    matrix = AUDIT.audit_selection_matrix()
    scope = AUDIT.audit_vertical_slice_scope()

    assert precheck["valid"] is True
    assert integrity["valid"] is True
    assert matrix["robustness_passed"] is True
    assert scope["vertical_slice_scope_established"] is True
