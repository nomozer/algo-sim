# -*- coding: utf-8 -*-
"""M17 W2C — định tuyến + các CỔNG cho `algorithm.bounded_control_flow`.

Chạy qua **production `run_pipeline`** (bất biến #22) với provider kịch bản —
không tái dựng orchestration trong test.

Bất biến khoá:
- đề KHÔNG cho chương trình cụ thể → `insufficient_specification`, KHÔNG bịa;
- hàm/đệ quy → từ chối, KHÔNG rơi về generic;
- đề hỏi gán + rẽ nhánh mà spec chỉ dựng gán → bỏ sót bị bắt (status ≠ ok);
- spec hợp lệ → envelope `ok` đúng target, config KHÔNG mang kết quả.
"""
from __future__ import annotations

import asyncio

import pytest

from app.ai import pipeline
from app.evaluation.authenticity_fixtures import (
    _PG_DATA,
    _PG_OBJECTS,
    _program_cfg_assign,
    _program_cfg_branch,
    _program_cfg_loop,
)
from app.evaluation.m16_offline_scripts import (
    CaseScript,
    _analysis,
    _classify,
    build_scripted_provider,
)
from app.simulation.error_codes import ErrorCode
from app.simulation.input_requirements import (
    INPUT_REQUIREMENTS,
    InputKind,
    applicability_of,
    APPLICABLE,
)
from app.simulation.sufficiency_gate import check_input_sufficiency

TARGET = "algorithm.bounded_control_flow"


def _run(script: CaseScript, monkeypatch, text: str = "đề kiểm thử") -> dict:
    fake, _ = build_scripted_provider(script)
    monkeypatch.setattr(pipeline, "call_gemini", fake)
    return asyncio.run(pipeline.run_pipeline(text, "khoa-gia"))


def _program_analysis(**over) -> dict:
    kw = {"goal": "Chạy từng bước đoạn chương trình", "ownership": "provided",
          "objects": _PG_OBJECTS, "data": _PG_DATA}
    kw.update(over)
    return _analysis(**kw)


# ── hợp đồng dữ kiện ────────────────────────────────────────────

def test_target_khai_hop_dong_du_kien_va_APPLICABLE():
    assert TARGET in INPUT_REQUIREMENTS
    req = INPUT_REQUIREMENTS[TARGET]
    assert req.required_grounded_inputs == (InputKind.PROGRAM_STATEMENTS,)
    assert applicability_of(TARGET)[0] == APPLICABLE


def test_de_khong_cho_chuong_trinh_thi_chan_o_cong_du_du_kien():
    """CF-5: "Mô phỏng vòng lặp while." — một danh từ, KHÔNG giá trị nào."""
    analysis = _analysis(goal="Mô phỏng vòng lặp while",
                         objects=["vòng lặp while"], data=[])
    verdict = check_input_sufficiency(analysis, TARGET)
    assert verdict is not None, "đề trống mà vẫn cho qua ⇒ nguy cơ bịa chương trình"
    assert verdict[0] == ErrorCode.INPUT_INSUFFICIENT
    assert InputKind.PROGRAM_STATEMENTS.value in verdict[2]["missing_inputs"]


def test_de_co_bien_va_gia_tri_thi_qua_cong():
    assert check_input_sufficiency(_program_analysis(), TARGET) is None


def test_thong_diep_hoc_sinh_doi_dung_ba_thu_can_thiet():
    """Học sinh phải biết CẦN BỔ SUNG GÌ, không chỉ 'thiếu dữ kiện'."""
    msg = INPUT_REQUIREMENTS[TARGET].learner_prompt_template
    assert "ban đầu" in msg and "điều kiện" in msg
    assert "không tự nghĩ ra" in msg  # không bịa
    for token in ("insufficient", "InputKind", "PROGRAM_STATEMENTS", "None"):
        assert token not in msg, "thông điệp học sinh lộ token kỹ thuật"


# ── đường thành công qua pipeline thật ──────────────────────────

@pytest.mark.parametrize("cfg_builder", [
    _program_cfg_assign, _program_cfg_branch, _program_cfg_loop,
])
def test_spec_hop_le_ra_envelope_ok_dung_target(cfg_builder, monkeypatch):
    env = _run(CaseScript(_program_analysis(), [_classify(TARGET)], [cfg_builder()]),
               monkeypatch)
    assert env["status"] == "ok", env
    assert env["simulation_id"] == TARGET
    cfg = env["config"]
    assert cfg["program_version"] == "program-1.0"
    # R0 — config KHÔNG mang diễn biến/kết quả
    for banned in ("trace", "steps", "final_environment", "result", "iterations"):
        assert banned not in cfg


def test_de_thieu_du_kien_khong_bao_gio_dung_mo_phong(monkeypatch):
    """CF-5 end-to-end: cổng chặn TRƯỚC simulate ⇒ LLM không có cơ hội bịa."""
    script = CaseScript(
        _analysis(goal="Mô phỏng vòng lặp while", objects=["vòng lặp while"], data=[]),
        [_classify(TARGET)],
        [_program_cfg_loop()],  # nếu cổng hỏng, kịch bản này SẼ dựng một chương trình
    )
    env = _run(script, monkeypatch, "Mô phỏng vòng lặp while.")
    assert env["status"] == "unsupported"
    assert env.get("failure_category") == "insufficient_specification"
    assert env.get("simulation_id") is None
    assert "config" not in env


def test_ham_va_de_quy_bi_tu_choi_khong_ro_ri_sang_generic(monkeypatch):
    """CF-6: ngữ pháp không có `call` ⇒ validator chặn CẢ BA lượt simulate; hệ
    KHÔNG dựng mô phỏng nào và KHÔNG hạ về generic.rule_scene.

    Cạn lượt thì `run_pipeline` ném RuntimeError (hành vi CHUNG của mọi target
    khi validator từ chối hết lượt, không phải điều W2C nghĩ ra) — điều quan
    trọng là KHÔNG có envelope `ok` và KHÔNG có config nào lọt ra."""
    bad = _program_cfg_assign().replace('"kind": "assign"', '"kind": "call"')
    script = CaseScript(_program_analysis(goal="Mô phỏng hàm đệ quy tính giai thừa"),
                        [_classify(TARGET)], [bad, bad, bad])
    with pytest.raises(RuntimeError) as exc:
        _run(script, monkeypatch, "Mô phỏng hàm đệ quy tính giai thừa n!")
    assert "không hỗ trợ" in str(exc.value)


# ── đủ ngữ nghĩa: không được bỏ sót cấu trúc đề hỏi ─────────────

def test_de_hoi_gan_VA_re_nhanh_ma_spec_chi_co_gan_thi_bi_bat(monkeypatch):
    """Bất biến: `status=ok` ⇒ không yêu cầu nào bị bỏ im lặng.

    Đề hỏi hai cấu trúc (gán + rẽ nhánh); spec chỉ dựng gán ⇒ phải KHÔNG ok."""
    analysis = _program_analysis(goal="Gán rồi rẽ nhánh theo điều kiện")
    analysis["requested_operations"] = [
        "bounded_control_flow:assignment", "bounded_control_flow:conditional",
    ]
    env = _run(CaseScript(analysis, [_classify(TARGET)], [_program_cfg_assign()] * 3),
               monkeypatch)
    assert env["status"] != "ok", "spec thiếu rẽ nhánh mà vẫn trả ok ⇒ bỏ sót im lặng"


def test_de_hoi_dung_cac_cau_truc_spec_dung_du_thi_ok(monkeypatch):
    analysis = _program_analysis(goal="Gán rồi rẽ nhánh theo điều kiện")
    analysis["requested_operations"] = [
        "bounded_control_flow:assignment", "bounded_control_flow:conditional",
    ]
    env = _run(CaseScript(analysis, [_classify(TARGET)], [_program_cfg_branch()]),
               monkeypatch)
    assert env["status"] == "ok", env
    assert env["simulation_id"] == TARGET
