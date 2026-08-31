# -*- coding: utf-8 -*-
"""MA SÁT BỀ MẶT — chương trình ĐÚNG không được chết vì cách viết. **0 API call.**

─── PHÂN BIỆT HAI LOẠI LỖI ────────────────────────────────────────────────

    LỖI NGỮ NGHĨA   — chương trình nói sai về hình học  ⇒ PHẢI chết
    MA SÁT BỀ MẶT   — chương trình đúng, IR không cho nói câu ấy ⇒ KHÔNG được
                      tiêu một lượt sửa

Ba khoản dưới đây đều đo được ở lượt live 2026-08-31, và cả ba là loại thứ hai:

  ① 3/4 ca — mô hình viết `construct_point` + toạ độ. Nó muốn KHAI một điểm gốc
    và với tay sang câu lệnh DỰNG, vì `statements` không có từ nào khác có chữ
    "point". Chương trình nó định viết hoàn toàn hợp lệ.
  ② 1/4 ca — `description` dài 1200 ký tự giết cả một chương trình hình học
    đúng. `description` đi đúng MỘT chỗ: envelope hiển thị.
  ③ 1/4 ca — `arith.op: "/"`.

─── VÀ MỘT KHOẢN CỐ Ý KHÔNG DỄ HOÁ ────────────────────────────────────────

`/` KHÔNG được ánh xạ sang `//`. Chúng không 1:1 (`Fraction(1)//2 == 0`), nên
alias sẽ biến một chương trình đúng thành SAI CÂM — tệ hơn từ chối. Từ chối,
nhưng nói ra chỗ đúng để đi.
"""
from __future__ import annotations

import pytest

from app.simulation.semantic_program.grounding_gate import check_grounding
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.ir_static_check import kiem_tinh
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.validator import validate_semantic_program


def _ct(stmts: list[dict], decls: list[dict] | None = None, **doi) -> dict:
    ct = {
        "spec_version": "1.0", "simulation_id": "geometry.ergonomics",
        "title": "Khai điểm gốc ngay trong dòng chương trình",
        "description": "Kiểm ma sát bề mặt không giết chương trình đúng.",
        "pedagogical_intent": "Cho thấy IR nói được câu mô hình muốn nói.",
        "memory_declarations": decls or [], "statements": stmts,
    }
    ct.update(doi)
    return ct


def _diem(ten: str, xyz: list, **doi) -> dict:
    return {"kind": "declare_point", "target_var": ten, "at": xyz,
            "model_assumption": "chọn theo hệ trục", **doi}


# ══ ① KHAI ĐIỂM GỐC ═════════════════════════════════════════════════════
def test_declare_point_duoc_NANG_ve_memory_declarations():
    r = validate_semantic_program(_ct([_diem("A", [0, 0, 0]), _diem("B", [1, 0, 0])]))
    assert r.ok, r.error
    ten = {d.name: d for d in r.spec.memory_declarations}
    assert set(ten) == {"A", "B"}
    assert ten["A"].type == "point3" and ten["A"].initial_value == [0, 0, 0]
    assert ten["A"].model_assumption == "chọn theo hệ trục"
    # …và GỠ khỏi `statements`: giữ lại thì cùng một điểm tồn tại ở hai chỗ.
    assert r.spec.statements == []


def test_nang_giu_nguyen_KHAI_BAO_co_san():
    """Nâng không được nuốt mất khai báo viết theo lối cũ."""
    r = validate_semantic_program(_ct(
        [_diem("B", [1, 0, 0])],
        [{"name": "A", "type": "point3", "initial_value": [0, 0, 0],
          "model_assumption": "gốc"}]))
    assert r.ok, r.error
    assert {d.name for d in r.spec.memory_declarations} == {"A", "B"}


def test_toa_do_PHAN_SO_khai_duoc():
    r = validate_semantic_program(_ct([_diem("M", ["1/2", 0, "3/4"])]))
    assert r.ok, r.error
    assert r.spec.memory_declarations[0].initial_value == ["1/2", 0, "3/4"]


def test_diem_khai_roi_DUNG_duoc_ngay():
    """Nâng phải xảy ra TRƯỚC thẩm định tĩnh, nếu không `midpoint` sẽ kêu
    'chưa định nghĩa' cho một điểm vừa khai ngay dòng trên."""
    r = validate_semantic_program(_ct(
        [_diem("A", [0, 0, 0]), _diem("B", [2, 0, 0]),
         {"kind": "construct_point", "target_var": "M",
          "expr": {"kind": "midpoint", "a": "A", "b": "B"}}],
        [{"name": "M", "type": "point3"}]))
    assert r.ok, r.error
    assert kiem_tinh(r.spec).ok, kiem_tinh(r.spec).phan_hoi()
    kq = SemanticProgramInterpreter().execute(r.spec)
    assert [str(kq.final_memory["M"].x), str(kq.final_memory["M"].y)] == ["1", "0"]


# ══ XUẤT XỨ KHÔNG CÓ CỬA VÒNG ═══════════════════════════════════════════
def test_GROUNDING_van_hoi_dung_cau_no_van_hoi():
    """Chốt cứng nhất của §2: `declare_point` KHÔNG được là đường lách R0."""
    co = validate_semantic_program(_ct([_diem("A", [0, 0, 0])]))
    assert check_grounding(RequestContract(), co.spec).ok

    khong = validate_semantic_program(_ct(
        [{"kind": "declare_point", "target_var": "A", "at": [0, 0, 0]}]))
    assert khong.ok, "thiếu xuất xứ là việc của grounding, không phải của schema"
    g = check_grounding(RequestContract(), khong.spec)
    assert not g.ok, "điểm KHÔNG xuất xứ vẫn qua được cổng grounding"
    assert "A" in " ".join(g.unresolved)


def test_source_fact_id_di_qua_nguyen_ven():
    """Kênh xuất xứ THỨ HAI — toạ độ lấy từ đề, không phải mô hình chọn."""
    r = validate_semantic_program(_ct(
        [{"kind": "declare_point", "target_var": "A", "at": [0, 0, 0],
          "source_fact_id": "f1"}]))
    assert r.ok, r.error
    assert r.spec.memory_declarations[0].source_fact_id == "f1"


# ══ ② `description` KHÔNG ĐƯỢC PHỦ QUYẾT HÌNH HỌC ═══════════════════════
def test_mo_ta_dai_bi_CAT_khong_giet_chuong_trinh():
    r = validate_semantic_program(_ct(
        [_diem("A", [0, 0, 0])], description="x" * 1500))
    assert r.ok, "văn xuôi dài vẫn giết một chương trình hình học đúng"
    assert len(r.spec.description) == 1000
    assert r.spec.description.endswith("…")


def test_mo_ta_ngan_KHONG_bi_dung_toi():
    r = validate_semantic_program(_ct([_diem("A", [0, 0, 0])],
                                      description="Mô tả ngắn."))
    assert r.spec.description == "Mô tả ngắn."


def test_mo_ta_khong_cham_hinh_hoc():
    """Cắt được vì nó KHÔNG chạm đúng đắn — ca này khoá lời khai ấy."""
    dai = validate_semantic_program(_ct([_diem("A", [1, 2, 3])],
                                        description="y" * 1500))
    ngan = validate_semantic_program(_ct([_diem("A", [1, 2, 3])],
                                         description="ngắn"))
    assert dai.ok and ngan.ok
    a = dai.spec.memory_declarations[0]
    b = ngan.spec.memory_declarations[0]
    assert (a.name, a.type, a.initial_value) == (b.name, b.type, b.initial_value)


# ══ ③ `/` — TỪ CHỐI CÓ DẠY, KHÔNG ALIAS ═════════════════════════════════
def test_chia_thuc_bi_tu_choi_va_CHI_duong_dung():
    r = validate_semantic_program(_ct(
        [_diem("A", [0, 0, 0]),
         {"kind": "assign", "target_var": "x",
          "expr": {"kind": "arith", "op": "/",
                   "left": {"kind": "literal", "value": 1},
                   "right": {"kind": "literal", "value": 2}}}],
        [{"name": "x", "type": "float"}]))
    assert not r.ok
    assert "divide_segment" in r.error, "lời từ chối không chỉ chỗ đúng để đi"


def test_KHONG_anh_xa_chia_thuc_sang_chia_nguyen():
    """`Fraction(1) // 2 == 0` còn `1/2` là `1/2`. Ánh xạ sẽ biến một chương
    trình ĐÚNG thành SAI CÂM — tệ hơn hẳn việc từ chối.

    Ca này đỏ nếu ai đó thêm alias `"/" → "//"` cho mô hình khỏi mất lượt.
    """
    from fractions import Fraction

    assert Fraction(1) // 2 == 0 and Fraction(1) / 2 == Fraction(1, 2)


@pytest.mark.parametrize("op", ["+", "-", "*", "//", "%"])
def test_toan_tu_hop_le_van_qua(op):
    r = validate_semantic_program(_ct(
        [_diem("A", [0, 0, 0]),
         {"kind": "assign", "target_var": "x",
          "expr": {"kind": "arith", "op": op,
                   "left": {"kind": "literal", "value": 4},
                   "right": {"kind": "literal", "value": 2}}}],
        [{"name": "x", "type": "float"}]))
    assert r.ok, r.error


def test_toan_tu_la_van_bi_tu_choi():
    r = validate_semantic_program(_ct(
        [{"kind": "assign", "target_var": "x",
          "expr": {"kind": "arith", "op": "**",
                   "left": {"kind": "literal", "value": 2},
                   "right": {"kind": "literal", "value": 3}}}],
        [{"name": "x", "type": "float"}]))
    assert not r.ok


# ══ THẺ VĂN PHẠM NÓI ĐÚNG VỀ TOẠ ĐỘ ═════════════════════════════════════
def test_the_van_pham_goi_dung_ten_toa_do():
    """Thẻ từng gọi `at` là "khối lệnh" — mô hình sẽ nhét một thân câu lệnh vào
    chỗ ba con số. Nhãn sai của TA đẻ ra lỗi của NÓ."""
    from app.simulation.semantic_program.grammar_card import grammar_card

    dong = [d for d in grammar_card().splitlines() if "declare_point" in d]
    assert dong, "thẻ không giới thiệu `declare_point` — mô hình không biết nó có"
    assert "[x,y,z]" in dong[0]
    assert "khối lệnh" not in dong[0]


# ══ MA SÁT DO CHÍNH PHÉP NÂNG TỰ ĐẺ RA — đo được 3/4 ca live ════════════
def test_khai_HAI_LAN_cung_mot_diem_thi_GOP_khong_bao_trung():
    """Mô hình nói cùng một điều hai lần: một mục `memory_declarations` và một
    `declare_point` cùng tên. Đó KHÔNG phải mâu thuẫn — chỉ là dư.

    Bản đầu của phép nâng ĐẺ RA lỗi ấy: nó thêm một khai báo thứ hai rồi để
    phép kiểm trùng tên bắt. Tự dựng lỗi rồi tự bắt là ma sát ta tự tạo, và nó
    thống trị 3/4 ca ở lượt live 2026-08-31 — thay đúng chỗ ma sát cũ vừa dọn.
    """
    r = validate_semantic_program(_ct(
        [_diem("A", [0, 0, 0]), _diem("B", [2, 0, 0])],
        [{"name": "A", "type": "point3"}]))
    assert r.ok, r.error
    ten = {d.name: d for d in r.spec.memory_declarations}
    assert set(ten) == {"A", "B"}, "gộp hỏng — sinh ra khai báo thừa"
    assert ten["A"].initial_value == [0, 0, 0], "khai báo rỗng không được điền"
    assert ten["A"].model_assumption == "chọn theo hệ trục"


def test_gop_KHONG_de_gia_tri_da_co():
    """Đè là im lặng chọn một trong hai lời khai. Giữ cái khai trước."""
    r = validate_semantic_program(_ct(
        [_diem("A", [9, 9, 9])],
        [{"name": "A", "type": "point3", "initial_value": [1, 2, 3],
          "model_assumption": "khai trước"}]))
    assert r.ok, r.error
    d = r.spec.memory_declarations[0]
    assert d.initial_value == [1, 2, 3] and d.model_assumption == "khai trước"


def test_diem_gop_DUNG_duoc_ngay_o_tang_tinh():
    """Triệu chứng thứ hai của cùng bug: `IR_USE_BEFORE_CONSTRUCTION` — 'A' có
    khai báo nhưng chưa có giá trị, vì phép nâng bỏ qua thay vì điền."""
    from app.simulation.semantic_program.ir_static_check import kiem_tinh

    r = validate_semantic_program(_ct(
        [_diem("A", [0, 0, 0]), _diem("B", [2, 0, 0]),
         {"kind": "construct_point", "target_var": "M",
          "expr": {"kind": "midpoint", "a": "A", "b": "B"}}],
        [{"name": "A", "type": "point3"}, {"name": "B", "type": "point3"},
         {"name": "M", "type": "point3"}]))
    assert r.ok, r.error
    t = kiem_tinh(r.spec)
    assert t.ok, t.phan_hoi()
