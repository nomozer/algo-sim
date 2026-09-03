# -*- coding: utf-8 -*-
"""Ô TOÁN HẠNG NÓI RA VAI TRÒ CỦA NÓ. **0 lượt gọi model.**

    `OPERAND_ROLE_HINTS`, 2026-09-04.

─── LỖ ĐO ĐƯỢC ────────────────────────────────────────────────────────────

Thẻ nói ô ấy nhận *một cái tên, kiểu `point3`*, và im lặng về **vai trò**.
`OPERAND_NAME_CONVERGENCE_AUDIT` đo: năm phép nhận hai `point3` dùng bốn quy
ước tên, và **bốn trong năm đúng theo ngữ nghĩa** (kiểm bằng kernel: đảo thứ tự
hai toán hạng). Nên việc phải làm là NÓI RA vai trò, **không** phải xoá khác
biệt — `from_point`/`to_point` là tên đúng cho một phép CÓ THỨ TỰ.

`circumsphere` (probe V2) gửi sai tên cho `vector_from_points`; tôi mắc đúng
lỗi ấy khi viết bài chứng nhận. Cả hai đoán theo quy ước đông nhất (`a`/`b`).

⚠️ Các ca dưới đây khẳng định **quan hệ với thẩm quyền**, không khoá văn phong:
gợi ý phải BẰNG mô tả trong model (sau phép rút gọn tổng quát). Đổi mô tả ở
`contract.py` thì thẻ tự đổi và test vẫn xanh; chép tay một bảng gợi ý thì đỏ.
"""
from __future__ import annotations

import pytest

from app.simulation.geometry.exact import Vec3, Line3
from app.simulation.geometry.kernel import divide_segment, midpoint
from app.simulation.geometry import measure as M
from app.simulation.semantic_program import contract as C
from app.simulation.semantic_program.grammar_card import (
    _ten_phep,
    _vai_tro,
    grammar_card,
    manh_hop_dong,
)

THE = grammar_card("hinh_hoc")
DONG = {_ten_phep(d): d.strip()
        for d in THE.splitlines() if d.strip().startswith("[")}


def _mong(model: str, truong: str) -> str:
    """Gợi ý KỲ VỌNG — dẫn thẳng từ model, không gõ lại chuỗi nào."""
    return _vai_tro(getattr(C, model).model_fields[truong])


# ══ H6 — MỌI GỢI Ý ĐẾN TỪ METADATA, KHÔNG TỪ BẢNG CHÉP TAY ═══════════════
@pytest.mark.parametrize("phep,model,truong", [
    ("vector_from_points", "VectorFromPointsExpr", "from_point"),
    ("vector_from_points", "VectorFromPointsExpr", "to_point"),
    ("divide_segment", "DivideSegmentExpr", "a"),
    ("divide_segment", "DivideSegmentExpr", "b"),
    ("midpoint", "MidpointExpr", "a"),
    ("midpoint", "MidpointExpr", "b"),
    ("construct_line", "ConstructLineStmt", "through_a"),
    ("construct_line", "ConstructLineStmt", "through_b"),
    ("construct_curved_solid", "ConstructCurvedSolidStmt", "anchor"),
    ("construct_curved_solid", "ConstructCurvedSolidStmt", "apex_or_top"),
    ("construct_curved_solid", "ConstructCurvedSolidStmt", "rim_point"),
])
def test_H6_goi_y_bang_dung_mo_ta_cua_model(phep, model, truong):
    mong = _mong(model, truong)
    assert mong, f"{model}.{truong} mất mô tả — gợi ý sẽ rỗng"
    assert mong in DONG[phep], (DONG[phep], mong)


def test_H7_doi_MO_TA_thi_the_tu_doi(monkeypatch):
    """§19 — không có bảng kỳ vọng chép tay ở đâu cả."""
    f = C.VectorFromPointsExpr.model_fields["from_point"]
    monkeypatch.setattr(f, "description", "tên ĐIỂM KIỂM TRA")
    dong = next(d for d in grammar_card("hinh_hoc").splitlines()
                if _ten_phep(d) == "vector_from_points")
    assert "[ĐIỂM KIỂM TRA]" in dong, dong


def test_H6b_KHONG_co_bang_goi_y_chep_tay():
    """`ROLE_HINT_AUTHORITIES = 1`."""
    import ast
    import inspect

    from app.simulation.semantic_program import grammar_card as G

    # Tìm PHÉP GÁN thật, không tìm chữ trong chú thích: chính docstring của
    # `_vai_tro` nhắc tên bảng ấy để nói *đừng tạo nó*.
    cay = ast.parse(inspect.getsource(G))
    ten_gan = {t.id for n in ast.walk(cay) if isinstance(n, ast.Assign)
               for t in n.targets if isinstance(t, ast.Name)}
    for cam in ("OPERAND_ROLE_HINTS", "ROLE_HINTS", "VAI_TRO_THEO_PHEP"):
        assert cam not in ten_gan, cam
    # `_vai_tro` chỉ được đọc `description`, không khớp tên phép.
    than = inspect.getsource(G._vai_tro).split('"""')[-1]
    for cam in ("vector_from_points", "midpoint", "divide_segment"):
        assert cam not in than, than


# ══ H1 — VECTOR_FROM_POINTS: VAI TRÒ CÓ HƯỚNG ════════════════════════════
def test_H1_vector_from_points_vai_tro_thay_duoc():
    """`VECTOR_FROM_POINTS_ROLE_DISCOVERABILITY`. Phép CÓ THỨ TỰ (kernel:
    `B−A ≠ A−B`), nên hai ô phải phân biệt được đầu ↔ ngọn ngay trên dòng."""
    v = Vec3.of
    A, B = v(0, 0, 0), v(4, 2, 0)
    assert (B - A) != (A - B), "tiền đề hỏng: phép này phải CÓ thứ tự"

    d = DONG["vector_from_points"]
    assert "from_point:" in d and "to_point:" in d
    assert _mong("VectorFromPointsExpr", "from_point") in d
    assert _mong("VectorFromPointsExpr", "to_point") in d
    # Hai gợi ý phải KHÁC nhau — giống nhau thì không phân biệt được vai trò.
    assert (_mong("VectorFromPointsExpr", "from_point")
            != _mong("VectorFromPointsExpr", "to_point"))


# ══ H2 — DIVIDE_SEGMENT: TÊN ĐỐI XỨNG, PHÉP CÓ THỨ TỰ ════════════════════
def test_H2_divide_segment_giam_mo_ho():
    """`DIVIDE_SEGMENT_ROLE_AMBIGUITY_REDUCED`. Đây là ca đáng giá nhất: tên
    `a`/`b` ĐỐI XỨNG trong khi kernel cho thấy phép CÓ THỨ TỰ."""
    v = Vec3.of
    A, B = v(0, 0, 0), v(4, 2, 0)
    assert divide_segment(A, B, 2) != divide_segment(B, A, 2), (
        "tiền đề hỏng: phép này phải CÓ thứ tự")

    d = DONG["divide_segment"]
    assert "a:" in d and "b:" in d, d
    assert _mong("DivideSegmentExpr", "a") in d
    assert _mong("DivideSegmentExpr", "b") in d
    assert _mong("DivideSegmentExpr", "a") != _mong("DivideSegmentExpr", "b")


# ══ H3 · H4 — KHÔNG BỊA THỨ TỰ CHO PHÉP KHÔNG THỨ TỰ ═════════════════════
_DINH_HUONG = ("đầu", "cuối", "gốc", "ngọn", "nguồn", "đích", "trước", "sau")


def test_H3_midpoint_KHONG_co_goi_y_dinh_huong():
    """`MIDPOINT_FALSE_DIRECTIONAL_HINT = 0`.

    Kernel: `midpoint(A,B) == midpoint(B,A)`. Mô tả CŨ ghi *"điểm đầu"/"điểm
    cuối"* — lối định hướng, và `midpoint` là phép KHÔNG THỨ TỰ duy nhất trong
    kho mắc lỗi ấy. Sửa ở model (`OPERAND_ROLE_HINTS`), không sửa ở thẻ.
    """
    v = Vec3.of
    A, B = v(0, 0, 0), v(4, 2, 0)
    assert midpoint(A, B) == midpoint(B, A), "tiền đề hỏng"

    for t in ("a", "b"):
        goi = _mong("MidpointExpr", t)
        assert not any(w in goi for w in _DINH_HUONG), (t, goi)


def test_H4_construct_line_KHONG_co_goi_y_dinh_huong():
    """`CONSTRUCT_LINE_FALSE_ORDERING = 0`. Đường qua A,B ≡ đường qua B,A."""
    v = Vec3.of
    A, B = v(0, 0, 0), v(4, 2, 0)
    l1, l2 = Line3.through(A, B), Line3.through(B, A)
    assert M.distance_sq_lines(l1, l2) == 0, "tiền đề hỏng"

    for t in ("through_a", "through_b"):
        goi = _mong("ConstructLineStmt", t)
        assert not any(w in goi for w in _DINH_HUONG), (t, goi)


def test_H3b_moi_phep_KHONG_THU_TU_deu_dung_loi_DANH_SO():
    """Quy ước của chính kho: cặp không thứ tự đánh số `1`/`2`. Giữ nó nhất
    quán, nếu không lần sau lại có một `midpoint` thứ hai."""
    for model, ts in (("ConstructLineStmt", ("through_a", "through_b")),
                      ("IntersectLineLineExpr", ("line_a", "line_b")),
                      ("IntersectPlanePlaneExpr", ("plane_a", "plane_b")),
                      ("MidpointExpr", ("a", "b"))):
        cls = getattr(C, model, None)
        if cls is None:
            continue
        goi = [_vai_tro(cls.model_fields[t]) for t in ts]
        assert goi[0] != goi[1], (model, goi)
        assert any(c.isdigit() for c in "".join(goi)), (model, goi)


# ══ H5 — KHỐI CONG: BA VAI TRÒ KHÁC HẲN ══════════════════════════════════
def test_H5_curved_solid_ba_vai_tro_phan_biet_duoc():
    """`CURVED_OPERAND_ROLE_DISCOVERABILITY`. ROLE_DISTINCT: ba ô không thể
    hoán cho nhau."""
    d = DONG["construct_curved_solid"]
    goi = [_mong("ConstructCurvedSolidStmt", t)
           for t in ("anchor", "apex_or_top", "rim_point")]
    assert len(set(goi)) == 3, goi
    for g in goi:
        assert g in d, (g, d)


def test_H13_KHONG_co_mau_theo_DANG_BAI():
    """§10/§29 — không template cầu/trụ/nón."""
    for cam in ("ví dụ", "Ví dụ", "chẳng hạn", "mặt cầu ngoại tiếp",
                "hình chóp", "tứ diện"):
        assert cam not in THE, cam


# ══ H8 — NHÃN LOẠI KHÔNG BỊ PHÁ ══════════════════════════════════════════
def test_H8_nhan_loai_van_con_nguyen():
    """`CARD_CATEGORY_AFFORDANCE_REGRESSION = 0`."""
    assert DONG["construct_section"].startswith("[LỆNH]")
    assert DONG["intersect_plane_curved"].startswith("[BIỂU THỨC→assign]")
    assert DONG["midpoint"].startswith("[BIỂU THỨC→assign|construct_point]")


# ══ H9 — MẢNH SỬA MANG THEO GỢI Ý ════════════════════════════════════════
def test_H9_manh_sua_giu_goi_y_vai_tro():
    """`REPAIR_ROLE_HINT_ALIGNMENT` — mảnh cắt từ thẻ nên nó tự có; không có
    lời riêng cho lượt sửa."""
    loi = ("statements.1.assign.expr.vector_from_points.from_point\n"
           "  Input should be a valid string")
    m = manh_hop_dong(loi, "hinh_hoc")
    d = next(x for x in m.splitlines() if _ten_phep(x) == "vector_from_points")
    assert _mong("VectorFromPointsExpr", "from_point") in d
    assert _mong("VectorFromPointsExpr", "to_point") in d


# ══ H10 · H11 — KHÔNG ALIAS, KHÔNG ĐỔI TÊN ═══════════════════════════════
def test_H10_khong_them_alias_nao():
    """`MODEL_FACING_ALIASES_ADDED = 0`."""
    for model in ("VectorFromPointsExpr", "MidpointExpr", "DivideSegmentExpr",
                  "ConstructLineStmt", "ConstructCurvedSolidStmt"):
        cls = getattr(C, model)
        for ten, f in cls.model_fields.items():
            assert f.alias is None, f"{model}.{ten} có alias"
            assert f.validation_alias is None, f"{model}.{ten} có validation_alias"
        assert not cls.model_config.get("populate_by_name")


def test_H11_ten_truong_chinh_tac_KHONG_doi():
    """`CANONICAL_FIELD_NAMES_CHANGED = 0`."""
    mong = {
        "VectorFromPointsExpr": {"kind", "from_point", "to_point"},
        "MidpointExpr": {"kind", "a", "b"},
        "DivideSegmentExpr": {"kind", "a", "b", "ratio"},
        "ConstructLineStmt": {"kind", "target_var", "through_a", "through_b",
                              "label"},
    }
    for model, ts in mong.items():
        assert set(getattr(C, model).model_fields) == ts, model


# ══ H12 — CHƯƠNG TRÌNH LỊCH SỬ VẪN PARSE ═════════════════════════════════
def test_H12_chuong_trinh_lich_su_van_parse():
    """`HISTORICAL_PROGRAM_COMPATIBILITY`. Gợi ý chỉ là cách IN thẻ — tập chấp
    nhận không đổi một byte."""
    import json
    from pathlib import Path

    from app.simulation.semantic_program.contract import SemanticProgramSpec

    goc = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry"
    f = goc / "curved-ergonomics-v2-run2/cases/ball_1/final.json"
    spec = SemanticProgramSpec.model_validate(
        json.loads(f.read_text(encoding="utf-8"))["chuong_trinh"])
    assert spec.statements

    # Và tên toán hạng CŨ vẫn được nhận nguyên vẹn.
    raw = {"kind": "vector_from_points", "from_point": "O", "to_point": "A"}
    assert C.VectorFromPointsExpr.model_validate(raw).from_point == "O"
