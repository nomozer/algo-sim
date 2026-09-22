# -*- coding: utf-8 -*-
"""Unit Test Suite cho Tiền Đăng Ký Họ Thứ Hai (Second Family Preregistration).

Wave: PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION
Kiểm tra 18 tiêu chí bắt buộc theo đặc tả Mục 13:
1. Đúng ba ứng viên (A, B, C).
2. Trọng số cộng bằng 100.
3. Mỗi điểm có evidence, gap, risk, rationale.
4. Chỉ đúng một họ được chọn (right_triangle_base_right_prism_volume).
5. Manifest có đúng tám ca.
6. Có đúng năm positive và ba negative.
7. Case ID duy nhất.
8. Input hash duy nhất.
9. Ground truth phủ đủ case.
10. Không có expected_answer / expected_volume trong compiler input của manifest.
11. Không có case ID hoặc nhãn điểm hardcode trong product code (backend/app).
12. Ca đổi nhãn P02 giữ nguyên eligibility và kết quả toán học.
13. Ca phân số P03 không bị ép float không kiểm soát (giữ đúng Fraction 5/4).
14. Ca âm N01, N02, N03 có mã từ chối đã đăng ký và cô lập lỗi.
15. Manifest, ground truth và selection matrix có SHA-256 xác định.
16. Product code không thay đổi (git diff backend/app frontend/src rỗng).
17. Candidate và cache giữ nguyên (verify-only).
18. Favicon không bị stage.
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
REPO = GOC.parent
for _p in (str(GOC), str(GOC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import validate_second_family_preregistration as V  # noqa: E402


@pytest.fixture(scope="module")
def matrix_res():
    res = V.validate_selection_matrix()
    assert res.get("valid") is True, f"Selection matrix invalid: {res}"
    return res


@pytest.fixture(scope="module")
def manifest_gt_res():
    res = V.validate_manifest_and_ground_truth()
    assert res.get("valid") is True, f"Manifest / Ground Truth invalid: {res}"
    return res


@pytest.fixture(scope="module")
def sys_res():
    res = V.validate_product_and_system_invariants()
    assert res.get("valid") is True, f"System invariants invalid: {res}"
    return res


def test_01_three_candidates(matrix_res):
    """1. Đúng ba ứng viên (A, B, C)."""
    assert matrix_res["three_candidates"] is True


def test_02_weights_sum_100(matrix_res):
    """2. Trọng số cộng bằng 100."""
    assert matrix_res["weights_valid"] is True


def test_03_each_score_has_evidence(matrix_res):
    """3. Mỗi điểm có evidence, gap, risk, rationale."""
    assert matrix_res["evidence_complete"] is True


def test_04_only_one_family_selected(matrix_res):
    """4. Chỉ đúng một họ được chọn với điểm cao nhất."""
    assert matrix_res["selected_family"] == "right_triangle_base_right_prism_volume"
    assert matrix_res["b_is_highest"] is True


def test_05_manifest_has_eight_cases(manifest_gt_res):
    """5. Manifest có đúng tám ca."""
    assert manifest_gt_res["counts_valid"] is True


def test_06_five_positive_three_negative(manifest_gt_res):
    """6. Có đúng năm positive và ba negative."""
    assert manifest_gt_res["counts_valid"] is True


def test_07_unique_case_ids(manifest_gt_res):
    """7. Case ID duy nhất."""
    assert manifest_gt_res["unique_case_ids"] is True


def test_08_unique_input_hashes(manifest_gt_res):
    """8. Input hash duy nhất."""
    assert manifest_gt_res["unique_input_hashes"] is True


def test_09_ground_truth_covers_all_cases(manifest_gt_res):
    """9. Ground truth phủ đủ case."""
    assert manifest_gt_res["gt_covered"] is True


def test_10_no_expected_answer_in_compiler_input(manifest_gt_res):
    """10. Không có expected_answer trong compiler input của manifest."""
    assert manifest_gt_res["no_expected_in_input"] is True


def test_11_no_hardcoded_case_ids_in_product_code(sys_res):
    """11. Không có case ID hoặc nhãn điểm hardcode trong product code."""
    assert sys_res["no_hardcoded_case_ids"] is True


def test_12_p02_label_swap_preserves_eligibility_and_math(manifest_gt_res):
    """12. Ca đổi nhãn P02 giữ nguyên eligibility và kết quả toán học."""
    assert manifest_gt_res["p02_valid"] is True


def test_13_p03_fraction_exact_without_forced_float(manifest_gt_res):
    """13. Ca phân số P03 không bị ép float không kiểm soát."""
    assert manifest_gt_res["p03_exact_frac"] is True


def test_14_negative_cases_have_preregistered_rejection_codes(manifest_gt_res):
    """14. Ca âm có mã từ chối đã đăng ký và cô lập lỗi."""
    assert manifest_gt_res["neg_valid"] is True


def test_15_manifest_and_gt_sha256_present(manifest_gt_res, matrix_res):
    """15. Manifest, ground truth và selection matrix có SHA-256 hợp lệ."""
    assert len(manifest_gt_res["manifest_sha256"]) == 64
    assert len(manifest_gt_res["ground_truth_sha256"]) == 64
    assert len(matrix_res["file_sha256"]) == 64


def test_16_product_code_unmodified(sys_res):
    """16. Product code không thay đổi."""
    assert sys_res["product_unmodified"] is True


def test_17_candidate_and_cache_match(sys_res):
    """17. Candidate và cache giữ nguyên (verify-only)."""
    assert sys_res["candidate_valid"] is True
    assert sys_res["cache_valid"] is True


def test_18_favicon_not_staged(sys_res):
    """18. Favicon không bị stage."""
    assert sys_res["favicon_clean"] is True
