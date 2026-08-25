# -*- coding: utf-8 -*-
"""LỜI TỪ CHỐI PHẢI NÓI THẬT + R0 cho giá trị hình học. **0 API call.**

─── HAI THỨ ĐO ĐƯỢC Ở LƯỢT SMOKE 2026-08-25 ───────────────────────────────

**① Lời từ chối đổ lỗi cho đề bài.** Hệ nhận ra đề là hình học, chạy route sinh
**120 giây**, chương trình trượt ở cổng phủ — rồi học sinh nhận:

    "Bài này thuộc môn học khác, không nằm trong chương trình Tin học THPT"

Câu ấy SAI, và sai theo hướng tệ nhất: nó đổ cho ĐỀ BÀI cái lỗi thuộc về HỆ.
Học sinh đọc xong sẽ đi tìm bài khác, trong khi bài của em vốn đúng chủ đề.

**② Biến kiểu hình học giữ được rác.** Mô hình khai `ABCD` kiểu `polygon3` rồi
`assign ABCD = literal(["A","B","C","D"])` — một danh sách CHUỖI trong một biến
hình học. Không cổng nào kêu, và lỗi chỉ lộ ra tận `learner_surface` dưới dạng
*"ABCD đổi giá trị nhưng không có binding"*: một thông báo nói về TRIỆU CHỨNG ở
cách chỗ sai bốn tầng.

Prompt đã dạy luật ấy từ đầu (*"Đường, mặt, khối, thiết diện, số đo đều phải
đến từ một phép dựng hoặc một phép đo"*) — nhưng một câu trong prompt là lời
khuyên, không phải luật.
"""
from __future__ import annotations

import asyncio
import json

import pytest

from app.ai import pipeline
from app.learner_messages import learner_reason
from app.simulation.semantic_program.validator import validate_semantic_program

DE_HINH_HOC = (
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 3, SA vuông góc với "
    "mặt phẳng đáy và SA = 4. Tính thể tích khối chóp S.ABCD."
)
DE_MON_KHAC = "Cân bằng phương trình phản ứng NaOH + HCl rồi mô phỏng quá trình."


# ══ ① LỜI TỪ CHỐI ════════════════════════════════════════════════════════
def _analysis(scope: str = "OUT_OF_SCOPE") -> dict:
    return {
        "objects": ["hình chóp"], "data": [], "relations": [], "processes": [],
        "constraints": [], "goal": "Tính thể tích", "input_description": "x",
        "output_description": "y", "domain_scope": scope,
        "simulatability": "MEANINGFUL_TRACE", "result_ownership": "rule_derivable",
    }


def _chay(monkeypatch, text: str, scope: str = "OUT_OF_SCOPE") -> dict:
    tra = [json.dumps(_analysis(scope)),
           json.dumps({"status": "ok", "simulation_id": "generic.rule_scene",
                       "reason": None})]

    async def gia(api_key, system_prompt, user_text, response_schema=None,
                  temperature=0.2, image=None):
        return tra.pop(0) if tra else tra_cuoi[0]

    tra_cuoi = [tra[-1]]
    monkeypatch.setattr(pipeline, "call_gemini", gia)
    return asyncio.run(pipeline.run_pipeline(text, "khoa-gia"))


def test_de_HINH_HOC_khong_bi_goi_la_MON_KHAC(monkeypatch):
    env = _chay(monkeypatch, DE_HINH_HOC)
    assert env["status"] == "unsupported"
    assert env["failure_category"] == "geometry_generation_failed"
    assert "môn" not in learner_reason(env), learner_reason(env)


def test_loi_tu_choi_NOI_DUNG_thu_da_xay_ra(monkeypatch):
    """Học sinh phải đọc được: hệ ĐÃ hiểu đề, ĐÃ thử, và không hiển thị hình
    chưa kiểm chứng. Không phải "đề của em sai chủ đề"."""
    loi = learner_reason(_chay(monkeypatch, DE_HINH_HOC))
    assert "hình học không gian" in loi and "kiểm chứng" in loi


def test_de_MON_KHAC_THAT_van_bi_tu_choi_nhu_cu(monkeypatch):
    """Ngoại lệ hẹp đúng bằng chỗ cần. Đề hoá học không có từ khoá hình học ⇒
    bộ dò trả `tin_hoc` ⇒ lời từ chối phạm vi nguyên vẹn."""
    env = _chay(monkeypatch, DE_MON_KHAC)
    assert env["failure_category"] == "out_of_scope"
    assert "môn học khác" in learner_reason(env)


def test_KHONG_nuot_lời_tu_choi_NOT_SIMULATION_SUITABLE(monkeypatch):
    """Ngoại lệ CHỈ mở `GATE_OUT_OF_SCOPE`. `simulatability` là phán quyết sư
    phạm và enum của nó CÓ giá trị đúng cho hình học, nên nó vẫn được tôn trọng."""
    an = _analysis("THPT_INFORMATICS")
    an["simulatability"] = "EXPLANATION_ONLY"
    tra = [json.dumps(an), json.dumps({"status": "ok",
                                       "simulation_id": "generic.rule_scene",
                                       "reason": None})]

    async def gia(api_key, system_prompt, user_text, response_schema=None,
                  temperature=0.2, image=None):
        return tra.pop(0)

    monkeypatch.setattr(pipeline, "call_gemini", gia)
    env = asyncio.run(pipeline.run_pipeline(DE_HINH_HOC, "khoa-gia"))
    assert env["failure_category"] == "not_simulation_suitable"


def test_reason_KY_THUAT_van_giu_nguyen_cho_harness(monkeypatch):
    """Hai bề mặt, hai mục đích: `reason` nuôi harness/diagnostics,
    `learner_reason` là thứ học sinh đọc. Gộp chúng là mất một trong hai."""
    env = _chay(monkeypatch, DE_HINH_HOC)
    assert env["reason"] and env["reason"] != learner_reason(env)


# ══ ② R0: GIÁ TRỊ HÌNH HỌC KHÔNG ĐƯỢC LÀ LITERAL ═════════════════════════
def _spec(expr: dict, kieu: str = "polygon3") -> dict:
    return {
        "title": "kiem tra R0 gia tri hinh hoc",
        "memory_declarations": [
            {"name": "A", "type": "point3", "initial_value": [0, 0, 0]},
            {"name": "B", "type": "point3", "initial_value": [1, 0, 0]},
            {"name": "X", "type": kieu},
        ],
        "statements": [{"kind": "assign", "target_var": "X", "expr": expr}],
    }


@pytest.mark.parametrize("kieu", sorted(
    {"point3", "vector3", "line3", "plane3", "polygon3", "solid"}))
def test_moi_kieu_hinh_hoc_deu_CAM_gan_literal(kieu):
    """Hiện trường thật: `assign ABCD = literal(["A","B","C","D"])` — một danh
    sách CHUỖI nằm trong một biến `polygon3`."""
    r = validate_semantic_program(
        _spec({"kind": "literal", "value": ["A", "B", "C", "D"]}, kieu))
    assert not r.ok
    assert "literal" in r.error and kieu in r.error


def test_loi_NEU_RO_cach_lam_dung():
    """Lỗi đi ngược cho mô hình sửa (≤3 lượt), nên nó phải nói phải làm gì —
    không chỉ nói sai."""
    r = validate_semantic_program(
        _spec({"kind": "literal", "value": [[0, 0, 0]]}))
    assert "construct_" in r.error and "ĐO" in r.error


def test_gan_tu_PHEP_DUNG_van_hop_le():
    """Cấm literal, KHÔNG cấm gán. Bắt oan ở đây là đóng luôn đường đúng."""
    r = validate_semantic_program(
        _spec({"kind": "midpoint", "a": "A", "b": "B"}, "point3"))
    assert r.ok, r.error


def test_bien_TIN_HOC_van_gan_literal_binh_thuong():
    """Luật chỉ chạm kiểu hình học. Một `array` khởi tạo bằng literal là chuyện
    thường ngày của miền Tin học — chạm vào đó là phá 24 module."""
    r = validate_semantic_program({
        "title": "mien tin hoc khong doi",
        "memory_declarations": [{"name": "arr", "type": "array",
                                 "element_type": "int"}],
        "statements": [{"kind": "assign", "target_var": "arr",
                        "expr": {"kind": "literal", "value": [1, 2, 3]}}],
    })
    assert r.ok, r.error


def test_initial_value_cua_KHAI_BAO_khong_bi_dung_toi():
    """Đó là kênh HỢP LỆ cho điểm gốc và dữ kiện đề cho, và P2 đã gác nó rồi."""
    r = validate_semantic_program({
        "title": "diem goc khai toa do",
        "memory_declarations": [
            {"name": "A", "type": "point3", "initial_value": [0, 0, 0]}],
        "statements": [],
    })
    assert r.ok, r.error


def test_danh_sach_kieu_DAN_tu_kernel_khong_chep_tay():
    """Thêm một kiểu hình học vào kernel là nó tự vào luật — không ai phải nhớ."""
    from app.simulation.semantic_program.geometry_exec import GEOMETRY_TYPES
    from app.simulation.semantic_program.validator import _KIEU_HINH_HOC

    assert _KIEU_HINH_HOC is GEOMETRY_TYPES
