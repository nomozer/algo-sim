# -*- coding: utf-8 -*-
"""REPLAY OFFLINE các thất bại live đã ghi — **0 API call**.

─── ĐIỀU FILE NÀY LÀM ĐƯỢC, VÀ ĐIỀU NÓ KHÔNG ─────────────────────────────

§9 muốn chạy lại **chính chương trình mô hình đã sinh** qua pipeline mới.
Không làm được: ba lượt probe trước chỉ lưu THÔNG ĐIỆP LỖI, không lưu chương
trình thô. Đó là một lỗ của bộ đo, đã bịt (`probe_dihedral_synthesis` nay ghi
`programs`), nhưng bịt về sau không hồi tố được dữ liệu cũ.

Thứ làm được, và nó không phải hạng hai: mỗi thất bại đã ghi được TÁI DỰNG
thành ca tối thiểu, rồi hỏi *"kết cục nay có khác không"*. Ca tối thiểu dựng
từ chính câu lỗi trong artifact, không dựng từ trí nhớ.

    artifact                              →  ca tối thiểu  →  kết cục MỚI
    "construct_point.expr … 'literal'"    →  §A            →  có `declare_point`
    "angle_cos cần VECTƠ … 'line3'"       →  §B            →  vẫn từ chối, DẠY
    "arith.op Input should be '+' …"      →  §C            →  từ chối, CHỈ ĐƯỜNG
    "description String should have at    →  §D            →  CẮT, không giết
     most 1000 characters"
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.simulation.semantic_program.validator import validate_semantic_program

_ARTIFACT = (Path(__file__).resolve().parents[3] / "docs" / "evaluation"
             / "geometry" / "dihedral-probe-after3" / "dihedral-probe.json")


def _loi_da_ghi() -> list[str]:
    """Mọi thông điệp lỗi trong artifact lượt live cuối."""
    d = json.loads(_ARTIFACT.read_text(encoding="utf-8"))
    return [e.get("error", "") for c in d["cases"] for e in c.get("attempt_log") or []]


def test_artifact_con_do_va_van_doc_duoc():
    """Rỗng-là-hỏng: artifact mất thì mọi ca dưới đây xanh vô nghĩa."""
    loi = _loi_da_ghi()
    assert len(loi) >= 8, f"chỉ đọc được {len(loi)} lỗi — artifact hỏng?"


def _ct(stmts: list[dict], decls: list[dict] | None = None, **doi) -> dict:
    ct = {
        "spec_version": "1.0", "simulation_id": "geometry.replay",
        "title": "Tái dựng thất bại live",
        "description": "Chạy lại ca lỗi đã ghi qua hợp đồng mới.",
        "pedagogical_intent": "Cho thấy ma sát bề mặt đã hết.",
        "memory_declarations": decls or [], "statements": stmts,
    }
    ct.update(doi)
    return ct


# ── §A · `construct_point` + toạ độ (3/4 ca) ──────────────────────────────
def test_A_loi_nay_CO_THAT_trong_artifact():
    assert any("construct_point" in x for x in _loi_da_ghi())


def test_A_nay_co_DUONG_DUNG_de_di():
    """Lỗi cũ vẫn bị chặn — nhưng nay tồn tại một cách viết ĐÚNG cho cùng ý."""
    hong = validate_semantic_program(_ct(
        [{"kind": "construct_point", "target_var": "A",
          "expr": {"kind": "literal", "value": [0, 0, 0]}}],
        [{"name": "A", "type": "point3"}]))
    assert not hong.ok, "toạ độ trong construct_point KHÔNG được nới"

    dung = validate_semantic_program(_ct(
        [{"kind": "declare_point", "target_var": "A", "at": [0, 0, 0],
          "model_assumption": "chọn A làm gốc"}]))
    assert dung.ok, dung.error
    assert dung.spec.memory_declarations[0].initial_value == [0, 0, 0]


# ── §B · `angle_cos` trên `line3` (2/4 ca) ────────────────────────────────
def test_B_loi_nay_CO_THAT_trong_artifact():
    assert any("angle_cos" in x and "line3" in x for x in _loi_da_ghi())


def test_B_van_TU_CHOI_nhung_o_dung_MOT_tang():
    """Từ chối là ĐÚNG — dấu không được đến từ một đường vô hướng.

    Điều đổi: hai cổng nay nói CÙNG một luật. Trước đó `_KIEU_DO` chưa biết
    `vector3`, nên mô hình sửa đúng rồi vẫn bị cổng thứ hai đánh trượt.
    """
    from app.simulation.semantic_program.ir_static_check import _KIEU_DO, kiem_tinh

    diem = [{"name": n, "type": "point3", "initial_value": v,
             "model_assumption": "trục"} for n, v in
            [("O", [0, 0, 0]), ("A", [1, 0, 0]), ("B", [1, 1, 0])]]
    tren_duong = validate_semantic_program(_ct(
        [{"kind": "construct_line", "target_var": "l1",
          "through_a": "O", "through_b": "A"},
         {"kind": "construct_line", "target_var": "l2",
          "through_a": "O", "through_b": "B"},
         {"kind": "assign", "target_var": "c",
          "expr": {"kind": "measure", "quantity": "angle_cos",
                   "of": "l1", "wrt": "l2"}}],
        diem + [{"name": "l1", "type": "line3"}, {"name": "l2", "type": "line3"},
                {"name": "c", "type": "float"}]))
    assert not tren_duong.ok and "vector" in tren_duong.error.lower()

    tren_vecto = validate_semantic_program(_ct(
        [{"kind": "assign", "target_var": "u",
          "expr": {"kind": "vector_from_points", "from_point": "O", "to_point": "A"}},
         {"kind": "assign", "target_var": "v",
          "expr": {"kind": "vector_from_points", "from_point": "O", "to_point": "B"}},
         {"kind": "assign", "target_var": "c",
          "expr": {"kind": "measure", "quantity": "angle_cos", "of": "u", "wrt": "v"}}],
        diem + [{"name": "u", "type": "vector3"}, {"name": "v", "type": "vector3"},
                {"name": "c", "type": "float"}]))
    assert tren_vecto.ok, tren_vecto.error
    # …VÀ qua nốt cổng thứ hai. Đây là chỗ bốn ca live chết ở lượt trước.
    assert kiem_tinh(tren_vecto.spec).ok
    assert _KIEU_DO["angle_cos"] == (("vector3",), ("vector3",))


# ── §C · `arith.op = "/"` (1/4 ca) ────────────────────────────────────────
def test_C_loi_nay_CO_THAT_trong_artifact():
    assert any("'+', '-', '*'" in x or "arith" in x for x in _loi_da_ghi())


def test_C_van_tu_choi_nhung_CHI_duong():
    r = validate_semantic_program(_ct(
        [{"kind": "assign", "target_var": "x",
          "expr": {"kind": "arith", "op": "/",
                   "left": {"kind": "literal", "value": 1},
                   "right": {"kind": "literal", "value": 2}}}],
        [{"name": "x", "type": "float"}]))
    assert not r.ok
    assert "divide_segment" in r.error, "từ chối mà không chỉ chỗ đúng để đi"


# ── §D · `description` > 1000 (1/4 ca) ────────────────────────────────────
def test_D_loi_nay_CO_THAT_trong_artifact():
    assert any("1000 characters" in x for x in _loi_da_ghi())


def test_D_KHONG_con_giet_chuong_trinh():
    r = validate_semantic_program(_ct(
        [{"kind": "declare_point", "target_var": "A", "at": [0, 0, 0],
          "model_assumption": "gốc"}],
        description="x" * 1500))
    assert r.ok, "văn xuôi dài vẫn giết một chương trình hình học đúng"
    assert len(r.spec.description) == 1000


# ── TỔNG: bốn lớp ma sát, bốn kết cục đổi ────────────────────────────────
@pytest.mark.parametrize("dau_hieu", [
    "construct_point", "angle_cos", "1000 characters",
])
def test_moi_lop_ma_sat_deu_co_ca_tai_dung(dau_hieu):
    """Guard chống tự lừa: mỗi lớp lỗi trong artifact phải có ca ở file này.

    Không có ca tái dựng thì "đã sửa" chỉ là một lời khai.
    """
    assert any(dau_hieu in x for x in _loi_da_ghi()), (
        f"artifact không còn lỗi '{dau_hieu}' — ca tái dựng đang nói về "
        "một thất bại không tồn tại")
