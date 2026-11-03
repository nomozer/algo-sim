# -*- coding: utf-8 -*-
"""W17 · §15.3 — mỗi lời từ chối mang NGUYÊN NHÂN có cấu trúc (`refusal_cause`)."""
from __future__ import annotations

import json

from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.route import verify_and_compile
from app.simulation.semantic_program.validator import validate_semantic_program
from scripts import replay_negative_boundaries as RNB


def _frozen_outcome(contract, program: dict):
    v = validate_semantic_program(program)
    assert v.ok and v.spec is not None, v.error
    return verify_and_compile(contract, v.spec)


def test_mat_phang_chuong_trinh_tu_dat_khong_cat_khoi_la_nguyen_nhan_dung():
    """Đề ghi z = 3; chương trình cắt bằng z = 9 ⇒ đề hợp lệ, khâu dựng sai."""
    p1 = "p1_chop_thiet_dien_khoang_cach"
    raw = RNB.doc_raw_theo_thu_tu(p1)
    text = RNB.doc_de_bai()[p1]
    contract = build_request_contract(json.loads(raw["semantic_analyze"][0]), problem_text=text, domain="hinh_hoc")
    program = json.loads(raw["semantic_program"][0])
    for s in program["statements"]:
        if s["kind"] == "construct_plane_from_equation":
            s["d"] = -9
    out = _frozen_outcome(contract, program)
    assert (out.servable, out.refusal_cause, out.reason_code) == (
        False, "CONSTRUCTION", "PLANE_DOES_NOT_CUT")


def test_lech_phep_dung_la_nguyen_nhan_dung():
    """A′: đề cắt bằng (β), chương trình cắt bằng (α)."""
    from tests.geometry import test_assumption_certificate as AC

    contract, program = AC.PHEP_DUNG_SAI["O1_cat_bang_alpha_khi_de_noi_beta"]()
    out = _frozen_outcome(contract, program)
    assert (out.servable, out.refusal_cause, out.reason_code) == (
        False, "CONSTRUCTION", "CONSTRUCTION_NOT_TEXT_BOUND")


def test_bang_nguyen_nhan_theo_ma_da_dang_ky():
    """§15.3 (đính chính Task 1): mã có cấu trúc → nguyên nhân, một bảng duy nhất."""
    from app.simulation.semantic_program import refusal_cause as RC

    assert {m: RC.NGUYEN_NHAN_THEO_MA[m] for m in (
        "GIVEN_VALUE_NOT_IN_SOURCE", "ASSUMPTION_DETERMINES_ANSWER", "GIVEN_ONLY_IN_GOAL_CLAUSE",
        "SOURCE_TEXT_MISSING", "CONSTRUCTION_NOT_TEXT_BOUND", "SOURCE_EVIDENCE_CONFLICT",
        "SOURCE_SPAN_MISMATCH")} == {
        "GIVEN_VALUE_NOT_IN_SOURCE": "SOURCE", "ASSUMPTION_DETERMINES_ANSWER": "SOURCE",
        "GIVEN_ONLY_IN_GOAL_CLAUSE": "SOURCE", "SOURCE_TEXT_MISSING": "SOURCE",
        "CONSTRUCTION_NOT_TEXT_BOUND": "CONSTRUCTION", "SOURCE_EVIDENCE_CONFLICT": "CONSTRUCTION",
        "SOURCE_SPAN_MISMATCH": "CONSTRUCTION"}
    assert "ASSUMPTION_INVARIANCE_UNPROVEN" not in RC.NGUYEN_NHAN_THEO_MA
