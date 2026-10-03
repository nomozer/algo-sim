# -*- coding: utf-8 -*-
"""W17 · §15.3 — mỗi lời từ chối mang NGUYÊN NHÂN có cấu trúc (`refusal_cause`).

Chạy đúng biên sản phẩm `run_pipeline` qua các trình chạy offline của bộ sinh fixture (0 lượt gọi
model). Câu hỏi của mỗi test: *ai gây ra lời từ chối — chính dữ kiện của đề (`SOURCE`), hay khâu
dựng của hệ trên một đề hợp lệ (`CONSTRUCTION`)?* Đề hợp lệ thì người học không bao giờ bị bảo sửa
đề (`test_learner_messages.py` khoá câu chữ).
"""
from __future__ import annotations

import asyncio
import json

from app.learner_messages import attach_learner_reason
from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.validator import validate_semantic_program
from scripts import generate_generic_tier_a_fixtures as GEN
from scripts import replay_negative_boundaries as RNB


def _compiler(text: str, contract) -> dict:
    return attach_learner_reason(asyncio.run(GEN._run_compiler(text, contract)))


def _frozen(text: str, contract, program: dict) -> dict:
    v = validate_semantic_program(program)
    assert v.ok and v.spec is not None, v.error
    return attach_learner_reason(asyncio.run(GEN._run_frozen_program(text, contract, v.spec)))


def test_w17_do_dai_khong_duong_DE_GHI_la_nguyen_nhan_nguon():
    """Đề ghi `AB = 0`: chính dữ kiện của đề làm đáy suy biến."""
    text, contract = GEN._zero_ab(*GEN._pyramid_control_contract())
    assert "AB = 0" in text
    env = _compiler(text, contract)
    assert (env["status"], env.get("refusal_cause"), env.get("reason_code"), env.get("reason_subjects")) == (
        "unsupported", "SOURCE", "NON_POSITIVE_LENGTH", ["AB"]), env


def test_w17_do_dai_khong_duong_DE_KHONG_GHI_la_nguyen_nhan_dung():
    """Ảnh lập phương W16: đề "cạnh bằng 4" hợp lệ (V = 64), hợp đồng bị tiêm AB = 0 ⇒ khâu dựng sai.
    Bộ tiêm riêng `_tiem_ab_bang_0` (Task 3 ruling): `_zero_ab` nay luôn GHI số 0 vào chính đề."""
    text, contract = GEN._tiem_ab_bang_0(*GEN._cube_contract())
    assert "cạnh bằng 4" in text and "0" not in text
    env = _compiler(text, contract)
    assert (env.get("refusal_cause"), env.get("reason_code"), env.get("reason_subjects")) == (
        "CONSTRUCTION", "NON_POSITIVE_LENGTH", ["AB"]), env


def test_w17_mat_phang_de_cho_khong_cat_khoi_la_nguyen_nhan_nguon():
    """Đề ghi (α): z = 9 — mặt phẳng của đề nằm ngoài khối, thiết diện rỗng."""
    _text, env, _gate = GEN._cross_section_negative()
    env = attach_learner_reason(env)
    assert (env.get("refusal_cause"), env.get("reason_code"), env.get("reason_subjects")) == (
        "SOURCE", "PLANE_DOES_NOT_CUT", ["(α)"]), env


def test_w17_mat_phang_chuong_trinh_tu_dat_khong_cat_khoi_la_nguyen_nhan_dung():
    """Đề ghi z = 3; chương trình cắt bằng z = 9 ⇒ đề hợp lệ, khâu dựng sai."""
    raw = RNB.doc_raw_theo_thu_tu(GEN.P1)
    text = RNB.doc_de_bai()[GEN.P1]
    contract = build_request_contract(json.loads(raw["semantic_analyze"][0]), problem_text=text, domain="hinh_hoc")
    program = json.loads(raw["semantic_program"][0])
    for s in program["statements"]:
        if s["kind"] == "construct_plane_from_equation":
            s["d"] = -9
    env = _frozen(text, contract, program)
    assert (env["status"], env.get("refusal_cause"), env.get("reason_code")) == (
        "unsupported", "CONSTRUCTION", "PLANE_DOES_NOT_CUT"), env


def test_w17_lech_phep_dung_la_nguyen_nhan_dung():
    """A′: đề cắt bằng (β), chương trình cắt bằng (α)."""
    from tests.geometry import test_assumption_certificate as AC

    contract, program = AC.PHEP_DUNG_SAI["O1_cat_bang_alpha_khi_de_noi_beta"]()
    env = _frozen(contract.problem_text, contract, program)
    assert (env["status"], env.get("refusal_cause"), env.get("reason_code")) == (
        "unsupported", "CONSTRUCTION", "CONSTRUCTION_NOT_TEXT_BOUND"), env


def test_w17_bang_nguyen_nhan_theo_ma_da_dang_ky():
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
