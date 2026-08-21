# -*- coding: utf-8 -*-
"""Thẻ văn phạm KHÔNG ĐƯỢC trôi khỏi hợp đồng.

Thẻ này thay `responseSchema` — thứ Gemini không nhận được vì schema IR đệ quy
và nội suy `$ref` nổ ~10× mỗi bậc. Nó là hợp đồng giao diện DUY NHẤT mà mô hình
nhìn thấy, nên một `kind` mới bị bỏ sót trong thẻ nghĩa là mô hình không bao giờ
biết `kind` ấy tồn tại — và nó im lặng, vì validator chỉ nói "chương trình sai",
không nói "tại thẻ thiếu".

Vì thẻ SINH TỪ Pydantic nên nó tự đúng; các test dưới đây khoá đúng điều đó lại,
để lần sau ai đó viết tay một bản "cho gọn" thì ĐỎ.
"""
from __future__ import annotations

import typing

from pydantic import BaseModel

from app.simulation.semantic_program import contract as C
from app.simulation.semantic_program.grammar_card import grammar_card


def _nhan_cua(alias) -> set[str]:
    ra = set()
    for arg in typing.get_args(typing.get_args(alias)[0]):
        m = typing.get_args(arg)[0] if typing.get_args(arg) else arg
        if isinstance(m, type) and issubclass(m, BaseModel):
            k = m.model_fields.get("kind")
            if k:
                ra.add(typing.get_args(k.annotation)[0])
    return ra


def test_the_liet_ke_DU_moi_statement_kind():
    the = grammar_card()
    thieu = [k for k in _nhan_cua(C.SemanticStatement) if f"  {k}:" not in the]
    assert not thieu, (
        f"thẻ thiếu statement kind: {thieu}. Mô hình sẽ không bao giờ biết "
        "chúng tồn tại, và nó hỏng CÂM."
    )


def test_the_liet_ke_DU_moi_bieu_thuc_va_dieu_kien():
    the = grammar_card()
    for alias, ten in ((C.ValueExpr, "biểu thức"), (C.ConditionExpr, "điều kiện")):
        thieu = [k for k in _nhan_cua(alias) if f"  {k}:" not in the]
        assert not thieu, f"thẻ thiếu {ten} kind: {thieu}"


def test_the_liet_ke_DU_moi_MemoryType_va_primitive():
    the = grammar_card()
    for t in typing.get_args(C.MemoryType):
        assert t in the, f"thẻ thiếu MemoryType `{t}`"
    prims = typing.get_args(
        C.VisualContainerBinding.model_fields["primitive"].annotation
    )
    for p in prims:
        assert p in the, f"thẻ thiếu visual primitive `{p}`"


def test_the_neu_dung_ten_truong_cap_cao_nhat():
    """Đúng ba trường bắt buộc này là chỗ mô hình đã đặt sai tên ở lượt pilot 2."""
    the = grammar_card()
    for truong in ("title", "memory_declarations", "statements"):
        assert truong in the, truong


def test_the_CHAN_DUNG_cac_ten_mo_hinh_da_tu_bia():
    """Lượt pilot 2 đo được: mô hình bọc trong `semantic_program` và gọi
    `variables`. Thẻ phải nói thẳng là không có hai thứ đó."""
    the = grammar_card()
    assert "KHÔNG có khoá" in the
    assert "`variables`" in the and "`semantic_program`" in the


def test_the_du_gon_de_khong_thanh_nhoi_prompt():
    """Nó là hợp đồng giao diện, không phải chỗ chép luật. Phình lên nghĩa là ai
    đó đang nhồi văn xuôi vào — thứ đề tài này cố ý tránh."""
    n = len(grammar_card().encode("utf-8"))
    assert n <= 2600, (
        f"thẻ = {n} byte. Luật nào mã hoá được thì để validator giữ, đừng viết "
        "vào thẻ."
    )


def test_the_khong_phai_van_ban_viet_tay():
    """Sinh từ nguồn ⇒ thêm một kind vào contract là thẻ tự có. Test này khoá
    tính chất ấy bằng cách đối chiếu SỐ LƯỢNG."""
    the = grammar_card()
    tong = (len(_nhan_cua(C.SemanticStatement))
            + len(_nhan_cua(C.ValueExpr))
            + len(_nhan_cua(C.ConditionExpr)))
    dem = sum(1 for d in the.splitlines() if d.startswith("  ") and ":" in d)
    assert dem >= tong, f"thẻ liệt kê {dem} dòng kind, contract có {tong}"


def test_the_liet_ke_GIA_TRI_cua_truong_enum():
    """Tên trường nói được *chỗ nào điền*, không nói được *điền gì*.

    Đo được ở lượt kiểm sau khi thêm thẻ: mô hình dựng đúng cấu trúc lồng nhưng
    viết `op: "add"` thay vì `"+"`, nên chương trình vẫn trượt thẩm định.
    """
    the = grammar_card()
    for gt in ("+", "//", "==", "<=", "and", "or"):
        assert gt in the, f"thẻ thiếu giá trị toán tử `{gt}`"


def test_khong_in_duong_dan_module_vao_the():
    """Bẫy đã sập một lần: `typing.get_args` của union phân biệt trả về
    `Annotated[...]`, và nếu nhận nhầm chúng là giá trị enum thì thẻ in ra cả
    đường dẫn module — 19.759 byte thay vì ~2 KB."""
    the = grammar_card()
    for rac in ("typing.Annotated", "app.simulation", "Tag(tag="):
        assert rac not in the, f"thẻ lọt rác kiểu: {rac}"
