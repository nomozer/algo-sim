# -*- coding: utf-8 -*-
"""GÓC CÓ DẤU `angle_cos` — đóng miền góc mà KHÔNG thêm primitive nhị diện.

─── LỖ NÓ BỊT ─────────────────────────────────────────────────────────────

`angle_cos_sq` giữa hai ĐƯỜNG gộp `θ` với `180°−θ`. Với hai đường thẳng, gộp
ấy ĐÚNG — một đường không có chiều. Nhưng góc nhị diện có miền, và câu trả lời
"nhọn hay tù" nằm đúng ở cái dấu `cos²` vứt đi.

─── BA QUYẾT ĐỊNH THIẾT KẾ, VÀ CA KIỂM CỦA TỪNG CÁI ───────────────────────

① **Dấu đến từ một đối tượng KHAI là có hướng**, không từ thứ tự hai điểm lúc
   dựng một đường. `angle_cos` trên `line3` bị TỪ CHỐI Ở VALIDATOR — không phải
   hạn chế kỹ thuật mà là từ chối để một quy ước cài đặt quyết một mệnh đề toán.

② **Miền số không phải mở thêm.** `cos² ` hữu tỉ ⇒ `|cos| = √(cos²)` luôn viết
   được dạng `a·√b`. Dấu là `sign(u·v)`, một phép so nguyên.

③ **KHÔNG có primitive nhị diện.** Góc nhị diện có miền dựng bằng TỔ HỢP:
   giao tuyến → hai vectơ đại diện → `angle_cos`.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from app.simulation.geometry import measure as M
from app.simulation.geometry.exact import GeometryError, Plane3, Vec3
from app.simulation.geometry.radical import Radical, radical, square
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.validator import validate_semantic_program

F = Fraction
V = Vec3.of


# ══ ① NHÂN: DẤU + ĐỘ LỚN, CHÍNH XÁC ══════════════════════════════════════
@pytest.mark.parametrize("u, v, mong", [
    (V(1, 0, 0), V(1, 0, 0), F(1)),                    # 0°   — cùng chiều
    (V(1, 0, 0), V(3, 0, 0), F(1)),                    # cùng chiều, khác độ dài
    (V(1, 0, 0), V(-1, 0, 0), F(-1)),                  # 180° — ngược chiều
    (V(1, 0, 0), V(-5, 0, 0), F(-1)),
    (V(1, 0, 0), V(0, 1, 0), F(0)),                    # 90°  — tích vô hướng 0
    (V(1, 0, 0), V(1, 1, 0), radical(F(1, 2), 2)),     # 45°  →  √2/2
    (V(1, 0, 0), V(-1, 1, 0), radical(F(-1, 2), 2)),   # 135° → -√2/2
    (V(1, 0, 0), V(1, 1, 1), radical(F(1, 3), 3)),     # →  √3/3
    (V(1, 0, 0), V(-1, 1, 1), radical(F(-1, 3), 3)),   # → -√3/3
    (V(1, 0, 0), V(1, 3, 0), radical(F(1, 10), 10)),   # →  √10/10
])
def test_cos_co_dau_chinh_xac(u, v, mong):
    assert M.cos_between_vectors(u, v) == mong


def test_cos_VUONG_GOC_la_HUU_TI_khong_phai_0_can():
    """`cos = 0` phải là `Fraction(0)`, không phải `0·√b` — miền số chính tắc."""
    kq = M.cos_between_vectors(V(1, 0, 0), V(0, 1, 0))
    assert isinstance(kq, Fraction) and not isinstance(kq, Radical)


def test_binh_phuong_cos_KHOP_cos_sq_cu():
    """Hồi quy: `angle_cos` và `angle_cos_sq` phải nói cùng một điều về ĐỘ LỚN.

    Hai hàm trôi khỏi nhau thì một bài chấm bằng `cos_sq` và một bài chấm bằng
    `cos` sẽ cho hai kết luận khác nhau về cùng một hình.
    """
    for u, v in [(V(1, 0, 0), V(1, 1, 0)), (V(1, 0, 0), V(-1, 1, 0)),
                 (V(2, 1, 0), V(0, 3, 1)), (V(1, 1, 1), V(-1, 2, 0))]:
        assert square(M.cos_between_vectors(u, v)) == M.cos_sq_between_vectors(u, v)


def test_DAU_la_thu_DUY_NHAT_phan_biet_hai_goc_bu_nhau():
    """`cos²` gộp; `cos` không. Đây là toàn bộ lý do wave này tồn tại."""
    u, nhon, tu = V(1, 0, 0), V(1, 1, 0), V(-1, 1, 0)
    assert M.cos_sq_between_vectors(u, nhon) == M.cos_sq_between_vectors(u, tu)
    assert M.cos_between_vectors(u, nhon) != M.cos_between_vectors(u, tu)


def test_vector_KHONG_thi_tu_choi():
    with pytest.raises(GeometryError):
        M.cos_between_vectors(V(0, 0, 0), V(1, 0, 0))


def test_khong_float_tren_duong_goc_co_dau():
    from tests.source_scan import con_du, than_ma

    src = than_ma(M.cos_between_vectors)
    assert con_du(src, "sqrt_rational"), "bóc hỏng — không còn mã để soi"
    for cam in ["float(", "math.sqrt", "**0.5", "** 0.5", "round(", "acos"]:
        assert cam not in src, f"đường góc có dấu dùng {cam}"


# ══ ② HỢP ĐỒNG TĨNH: HƯỚNG PHẢI KHAI, KHÔNG SUY ═════════════════════════
def _ct(stmts: list[dict], decls: list[dict]) -> dict:
    return {
        "spec_version": "1.0", "simulation_id": "geometry.signed_angle",
        "title": "Góc có dấu giữa hai vectơ",
        "description": "Dựng hai vectơ rồi đo cosin có dấu giữa chúng.",
        "pedagogical_intent": "Cho thấy nhọn và tù là hai câu trả lời khác nhau.",
        "memory_declarations": decls, "statements": stmts,
    }


DIEM = [
    {"name": "O", "type": "point3", "initial_value": [0, 0, 0],
     "model_assumption": "gốc"},
    {"name": "A", "type": "point3", "initial_value": [1, 0, 0],
     "model_assumption": "trục x"},
    {"name": "B", "type": "point3", "initial_value": [1, 1, 0],
     "model_assumption": "phân giác xy"},
    {"name": "C", "type": "point3", "initial_value": [-1, 1, 0],
     "model_assumption": "đối xứng qua Oy"},
]


def test_angle_cos_tren_VECTO_KHAI_thi_qua():
    r = validate_semantic_program(_ct(
        [{"kind": "assign", "target_var": "u",
          "expr": {"kind": "vector_from_points", "from_point": "O", "to_point": "A"}},
         {"kind": "assign", "target_var": "v",
          "expr": {"kind": "vector_from_points", "from_point": "O", "to_point": "B"}},
         {"kind": "assign", "target_var": "c",
          "expr": {"kind": "measure", "quantity": "angle_cos", "of": "u", "wrt": "v"}}],
        DIEM + [{"name": "u", "type": "vector3"}, {"name": "v", "type": "vector3"},
                {"name": "c", "type": "float"}]))
    assert r.ok, r.error


def test_angle_cos_tren_DUONG_THANG_bi_TU_CHOI_o_VALIDATOR():
    """Ca chốt của §2. Đường thẳng không có chiều ⇒ không cho được dấu.

    Phải chết ở VALIDATOR chứ không ở kernel: lỗi validator được gửi ngược cho
    mô hình sửa, lỗi runtime thì không — bài học đã đo được ở wave trước.
    """
    r = validate_semantic_program(_ct(
        [{"kind": "construct_line", "target_var": "l1",
          "through_a": "O", "through_b": "A"},
         {"kind": "construct_line", "target_var": "l2",
          "through_a": "O", "through_b": "B"},
         {"kind": "assign", "target_var": "c",
          "expr": {"kind": "measure", "quantity": "angle_cos", "of": "l1", "wrt": "l2"}}],
        DIEM + [{"name": "l1", "type": "line3"}, {"name": "l2", "type": "line3"},
                {"name": "c", "type": "float"}]))
    assert not r.ok, "`angle_cos` trên hai đường thẳng vẫn lọt qua thẩm định"
    assert "VECTƠ" in r.error or "vector" in r.error.lower()


def test_angle_cos_tren_DIEM_cung_bi_tu_choi():
    """`point3` và `vector3` cùng là `Vec3` ở runtime — nên chỉ tầng KHAI phân
    biệt nổi, và ca này khoá đúng điều đó."""
    r = validate_semantic_program(_ct(
        [{"kind": "assign", "target_var": "c",
          "expr": {"kind": "measure", "quantity": "angle_cos", "of": "A", "wrt": "B"}}],
        DIEM + [{"name": "c", "type": "float"}]))
    assert not r.ok


def test_angle_cos_THIEU_wrt_chet_o_tham_dinh():
    r = validate_semantic_program(_ct(
        [{"kind": "assign", "target_var": "u",
          "expr": {"kind": "vector_from_points", "from_point": "O", "to_point": "A"}},
         {"kind": "assign", "target_var": "c",
          "expr": {"kind": "measure", "quantity": "angle_cos", "of": "u"}}],
        DIEM + [{"name": "u", "type": "vector3"}, {"name": "c", "type": "float"}]))
    assert not r.ok and "wrt" in r.error


def test_construct_point_KHONG_nhan_vector_from_points():
    """Ở runtime vectơ và điểm cùng lớp `Vec3`. Nếu `construct_point` nhận phép
    này, chương trình dựng ra một "điểm" thật ra là một PHƯƠNG — và không tầng
    nào phía sau phát hiện nổi."""
    r = validate_semantic_program(_ct(
        [{"kind": "construct_point", "target_var": "P",
          "expr": {"kind": "vector_from_points", "from_point": "O", "to_point": "A"}}],
        DIEM + [{"name": "P", "type": "point3"}]))
    assert not r.ok


# ══ ③ NHỊ DIỆN CÓ MIỀN — BẰNG TỔ HỢP, KHÔNG PRIMITIVE MỚI ═══════════════
def _ct_nhi_dien(dinh_S: list[int]) -> dict:
    """Nhị diện cạnh Ox giữa nửa mặt chứa A và nửa mặt chứa S.

    Đổi `S` sang phía âm là đổi nhị diện từ nhọn sang tù — CÙNG một chương
    trình, chỉ khác dữ liệu.
    """
    return {
        "spec_version": "1.0", "simulation_id": "geometry.dihedral_signed",
        "title": "Góc nhị diện có miền",
        "description": "Dựng hai vectơ đại diện vuông góc cạnh chung rồi đo cosin.",
        "pedagogical_intent": "Cho thấy nhị diện tù khác nhị diện nhọn.",
        "memory_declarations": [
            {"name": "O", "type": "point3", "initial_value": [0, 0, 0],
             "model_assumption": "gốc trên cạnh chung"},
            {"name": "X", "type": "point3", "initial_value": [1, 0, 0],
             "model_assumption": "hướng cạnh chung"},
            {"name": "A", "type": "point3", "initial_value": [0, 1, 0],
             "model_assumption": "điểm của nửa mặt thứ nhất"},
            {"name": "S", "type": "point3", "initial_value": dinh_S,
             "model_assumption": "điểm của nửa mặt thứ hai"},
            {"name": "u", "type": "vector3"}, {"name": "v", "type": "vector3"},
            {"name": "cos_nhi_dien", "type": "float"},
        ],
        "statements": [
            {"kind": "assign", "target_var": "u",
             "expr": {"kind": "vector_from_points", "from_point": "O", "to_point": "A"},
             "label": "Vectơ đại diện trong nửa mặt thứ nhất"},
            {"kind": "assign", "target_var": "v",
             "expr": {"kind": "vector_from_points", "from_point": "O", "to_point": "S"},
             "label": "Vectơ đại diện trong nửa mặt thứ hai"},
            {"kind": "assign", "target_var": "cos_nhi_dien",
             "expr": {"kind": "measure", "quantity": "angle_cos",
                      "of": "u", "wrt": "v"},
             "label": "Cosin góc nhị diện — CÓ DẤU"},
        ],
    }


@pytest.mark.parametrize("S, mong, ten", [
    ([0, 1, 1], radical(F(1, 2), 2), "nhọn 45°"),
    ([0, -1, 1], radical(F(-1, 2), 2), "tù 135°"),
])
def test_nhi_dien_NHON_va_TU_ra_hai_gia_tri_KHAC_nhau(S, mong, ten):
    val = validate_semantic_program(_ct_nhi_dien(S))
    assert val.ok, val.error
    kq = SemanticProgramInterpreter().execute(val.spec)
    assert kq.final_memory["cos_nhi_dien"] == mong, ten


def test_hai_cau_hinh_BU_NHAU_khong_con_bi_gop():
    """Trước wave này cả hai cho `cos² = 1/2` — không phân biệt được.

    Nếu ca này thôi đỏ khi ai đó đổi `angle_cos` về không dấu, miền góc lại
    đóng và toàn bộ wave mất tác dụng.
    """
    gt = []
    for S in ([0, 1, 1], [0, -1, 1]):
        val = validate_semantic_program(_ct_nhi_dien(S))
        kq = SemanticProgramInterpreter().execute(val.spec)
        gt.append(kq.final_memory["cos_nhi_dien"])
    assert gt[0] != gt[1], "nhọn và tù vẫn bị gộp"
    assert square(gt[0]) == square(gt[1]), "độ lớn phải bằng nhau — chỉ dấu khác"


def test_KHONG_MOT_tu_vung_nhi_dien_nao_ton_tai():
    """Chốt của cả wave: năng lực có, primitive chuyên biệt KHÔNG."""
    from app.simulation.semantic_program.contract import SemanticProgramSpec

    schema = SemanticProgramSpec.model_json_schema()
    import json as _j

    chuoi = _j.dumps(schema, ensure_ascii=False).lower()
    for cam in ["dihedral", "nhi_dien", "nhị diện"]:
        assert cam not in chuoi, f"từ vựng chuyên biệt lọt vào hợp đồng: {cam}"


# ══ ④ HỒI QUY: `angle_cos_sq` KHÔNG ĐỔI ═════════════════════════════════
def test_angle_cos_sq_van_nguyen_hanh_vi_cu():
    """Thêm `angle_cos` không được đụng phép đo cũ — mọi bài đã đo vẫn đúng."""
    assert M.cos_sq_between_vectors(V(1, 0, 0), V(1, 1, 0)) == F(1, 2)
    assert M.cos_sq_between_vectors(V(1, 0, 0), V(-1, 1, 0)) == F(1, 2)
    a = Plane3(V(0, 0, 0), V(0, 0, 1))
    b = Plane3(V(0, 0, 0), V(0, 1, 1))
    assert M.cos_sq_between_planes(a, b) == F(1, 2)
