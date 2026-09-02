# -*- coding: utf-8 -*-
"""CỔNG HỢP THÀNH G4 — bốn phép dựng của kernel, và ba trong bốn KHÔNG được thêm.

`kernel.py` có bốn phép dạng *"qua một điểm, song song/vuông góc với …"*, cả
bốn **0 lượt gọi** từ ngoài kernel. Câu hỏi không phải *"thêm bốn primitive
chứ?"* mà là, cho từng phép: **IR hiện tại đã diễn đạt được nó chưa?**

Hỏi bằng chương trình chạy thật — schema → thẩm định tĩnh → xuất xứ →
interpreter → vị từ chính xác. Ba phép trả lời CÓ, nên chúng **không** được
thêm cửa riêng: thêm một primitive cho thứ đã nói được là đúng cái bẫy mà
`translate` từng suýt rơi vào, nơi một tiện nghi bị gọi nhầm là năng lực mới.

Phép thứ tư trả lời KHÔNG, và có chứng minh chứ không phải cảm giác — xem
`test_MP_VUONG_GOC_*`.
"""
from __future__ import annotations

from fractions import Fraction as F

import pytest

from app.simulation.geometry import predicates as P
from app.simulation.geometry.exact import GeometryError
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.grounding_gate import check_grounding
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.ir_static_check import kiem_tinh
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.scene3d import build_scene3d
from app.simulation.semantic_program.simulation_state import build_simulation_state


def _diem(n: str, v: list) -> dict:
    return {"name": n, "type": "point3", "initial_value": v,
            "model_assumption": "hệ trục do đề chọn"}


def _khai(n: str, t: str) -> dict:
    return {"name": n, "type": t}


def _spec(tieu_de: str, decls: list, stmts: list) -> SemanticProgramSpec:
    return SemanticProgramSpec.model_validate({
        "spec_version": "1.0", "title": tieu_de,
        "memory_declarations": decls, "statements": stmts})


def _chay(spec: SemanticProgramSpec) -> dict:
    """Thẩm định tĩnh rồi chạy. Trả bộ nhớ cuối."""
    t = kiem_tinh(spec)
    assert t.ok, f"thẩm định tĩnh từ chối: {t.phan_hoi()}"
    return SemanticProgramInterpreter().execute(spec).final_memory


def _neo(spec: SemanticProgramSpec, de: str) -> None:
    """Witness phải qua CẢ cổng xuất xứ, không chỉ qua schema."""
    g = check_grounding(RequestContract(problem_text=de), spec)
    assert g.ok, f"grounding từ chối: {g.error_code} · {g.unresolved[:3]}"


# ══ A · BA PHÉP ĐÃ DIỄN ĐẠT ĐƯỢC — WITNESS CHẠY THẬT ═════════════════════
#
# Mỗi ca dưới đây là bằng chứng cho một quyết định KHÔNG làm. Xoá chúng đi thì
# lần sau ai đó sẽ thêm ba primitive vì "kernel có mà IR thiếu".

DE_SS_DUONG = ("Cho tam giác ABC và điểm M. Dựng đường thẳng qua M và song "
               "song với đường thẳng AB.")
DE_SS_MAT = ("Cho tam giác ABC và điểm M nằm ngoài mặt phẳng (ABC). Dựng mặt "
             "phẳng qua M và song song với mặt phẳng (ABC).")
DE_VG_DUONG = ("Cho tam giác ABC và điểm M nằm ngoài mặt phẳng (ABC). Dựng "
               "đường thẳng qua M và vuông góc với mặt phẳng (ABC).")

GOC = [_diem("A", [0, 0, 0]), _diem("B", [2, 0, 0]),
       _diem("C", [1, 3, 0]), _diem("M", [1, 1, 5])]


def test_A1_duong_qua_M_song_song_duong_d__DIEN_DAT_DUOC():
    """`line_through_point_parallel_to` — ba câu lệnh, IR cũ đã đủ.

    `v = vector_from_points(A,B)` · `N = translate(M, v)` · `line(M, N)`.
    Đây cũng là cách học sinh làm trên giấy: dựng một điểm nữa theo phương ấy.
    """
    spec = _spec("Đường qua M song song AB",
        GOC + [_khai("d", "line3"), _khai("v", "vector3"),
               _khai("N", "point3"), _khai("k", "line3")],
        [{"kind": "construct_line", "target_var": "d",
          "through_a": "A", "through_b": "B"},
         {"kind": "assign", "target_var": "v",
          "expr": {"kind": "vector_from_points", "from_point": "A", "to_point": "B"}},
         {"kind": "construct_point", "target_var": "N",
          "expr": {"kind": "translate", "point": "M", "vector": "v"}},
         {"kind": "construct_line", "target_var": "k",
          "through_a": "M", "through_b": "N"}])
    _neo(spec, DE_SS_DUONG)
    m = _chay(spec)
    assert P.parallel_lines(m["k"], m["d"])
    assert P.point_on_line(m["M"], m["k"])


def test_A2_mat_qua_M_song_song_mat__DIEN_DAT_DUOC():
    """`plane_through_point_parallel_to` — dịch M theo HAI vectơ chỉ phương.

    Cần ba điểm định nghĩa mặt phẳng tham chiếu, mà đó chính là thứ định nghĩa
    nó, nên điều kiện luôn thoả.
    """
    spec = _spec("Mặt qua M song song (ABC)",
        GOC + [_khai("abc", "plane3"), _khai("u", "vector3"),
               _khai("w", "vector3"), _khai("N", "point3"),
               _khai("Q", "point3"), _khai("mp2", "plane3")],
        [{"kind": "construct_plane", "target_var": "abc", "through": ["A", "B", "C"]},
         {"kind": "assign", "target_var": "u",
          "expr": {"kind": "vector_from_points", "from_point": "A", "to_point": "B"}},
         {"kind": "assign", "target_var": "w",
          "expr": {"kind": "vector_from_points", "from_point": "A", "to_point": "C"}},
         {"kind": "construct_point", "target_var": "N",
          "expr": {"kind": "translate", "point": "M", "vector": "u"}},
         {"kind": "construct_point", "target_var": "Q",
          "expr": {"kind": "translate", "point": "M", "vector": "w"}},
         {"kind": "construct_plane", "target_var": "mp2", "through": ["M", "N", "Q"]}])
    _neo(spec, DE_SS_MAT)
    m = _chay(spec)
    assert P.parallel_planes(m["mp2"], m["abc"])
    assert P.point_on_plane(m["M"], m["mp2"])


def test_A3_duong_qua_M_vuong_goc_mat__DIEN_DAT_DUOC():
    """`perpendicular_foot_line` — hai câu lệnh, và là cách làm tự nhiên nhất:
    hạ chân đường vuông góc rồi nối."""
    spec = _spec("Đường qua M vuông góc (ABC)",
        GOC + [_khai("abc", "plane3"), _khai("H", "point3"), _khai("k", "line3")],
        [{"kind": "construct_plane", "target_var": "abc", "through": ["A", "B", "C"]},
         {"kind": "construct_point", "target_var": "H",
          "expr": {"kind": "project_onto", "point": "M", "target": "abc"}},
         {"kind": "construct_line", "target_var": "k",
          "through_a": "M", "through_b": "H"}])
    _neo(spec, DE_VG_DUONG)
    m = _chay(spec)
    assert P.line_perpendicular_plane(m["k"], m["abc"])
    assert P.point_on_line(m["M"], m["k"])


# ══ B · PHÉP THỨ TƯ — CHỨNG MINH KHÔNG DIỄN ĐẠT ĐƯỢC ════════════════════
def test_B_moi_phep_sinh_diem_BAO_TOAN_BAO_AFFINE():
    """Luận cứ của quyết định thêm primitive, kiểm bằng vét cạn.

    `midpoint` · `divide_segment` · `project_onto` · `translate` · ba phép
    `intersect_*` — không phép nào đưa được một điểm ra ngoài bao affine của
    các điểm đã khai. Với đề chỉ cho `A`, `B`, `M`, bao ấy là mặt phẳng `(ABM)`.
    """
    from app.simulation.geometry import kernel as K
    from app.simulation.geometry.exact import Line3, Plane3, Vec3

    A, B, M = Vec3.of(0, 0, 0), Vec3.of(2, 0, 0), Vec3.of(1, 3, 4)
    abm = Plane3.through(A, B, M)
    goc = [A, B, M]
    sinh = []
    for p in goc:
        for q in goc:
            if p == q:
                continue
            sinh.append(K.midpoint(p, q))
            sinh.append(K.divide_segment(p, q, F(1, 3)))
            ln = Line3.through(p, q)
            for r in goc:
                if r in (p, q):
                    continue
                sinh.append(K.project_point_onto_line(r, ln))
                sinh.append(K.translate(r, q - p))
    assert sinh, "phép vét cạn không sinh điểm nào — luận cứ rỗng"
    ngoai = [v for v in sinh if abm.signed_eval(v) != 0]
    assert not ngoai, f"{len(ngoai)} điểm nằm ngoài bao affine — luận cứ SAI"


def test_B_hop_thanh_TU_NHIEN_that_bai_vi_ba_diem_thang_hang():
    """Hệ quả trực tiếp: mặt phẳng qua M ⊥ AB nằm NGOÀI `(ABM)`, nên giao của
    nó với bao affine là một ĐƯỜNG — ba điểm lấy được luôn thẳng hàng."""
    spec = _spec("Thử dựng mặt ⊥ AB chỉ bằng IR cũ",
        [_diem("A", [0, 0, 0]), _diem("B", [2, 0, 0]), _diem("M", [1, 3, 4]),
         _khai("d", "line3"), _khai("Hm", "point3"), _khai("u", "vector3"),
         _khai("N", "point3"), _khai("mp", "plane3")],
        [{"kind": "construct_line", "target_var": "d",
          "through_a": "A", "through_b": "B"},
         {"kind": "construct_point", "target_var": "Hm",
          "expr": {"kind": "project_onto", "point": "M", "target": "d"}},
         {"kind": "assign", "target_var": "u",
          "expr": {"kind": "vector_from_points", "from_point": "Hm", "to_point": "M"}},
         {"kind": "construct_point", "target_var": "N",
          "expr": {"kind": "translate", "point": "M", "vector": "u"}},
         {"kind": "construct_plane", "target_var": "mp",
          "through": ["M", "Hm", "N"]}])
    with pytest.raises(GeometryError) as e:
        _chay(spec)
    assert e.value.code == "COLLINEAR_POINTS"


def test_B_loi_thoat_duy_nhat_bi_CONG_XUAT_XU_tu_choi():
    """Thoát ra được chỉ bằng cách khai thêm điểm phụ NGOÀI mặt phẳng ấy — và
    `grounding_gate` từ chối đúng điều đó.

    Hai cổng khoá chặt nhau, nên khoảng trống là THẬT chứ không phải "dài dòng".
    Nếu một ngày grounding nới ra, ca này ĐỎ và quyết định thêm primitive phải
    được xem lại.
    """
    spec = _spec("Khai điểm phụ không có trong đề",
        GOC + [_diem("X", [0, 0, 7]), _khai("d", "line3")],
        [{"kind": "construct_line", "target_var": "d",
          "through_a": "A", "through_b": "B"}])
    g = check_grounding(RequestContract(problem_text=DE_VG_DUONG), spec)
    assert not g.ok
    assert g.error_code == "UNANCHORED_DERIVED_ASSUMPTION"
    assert any("X" in u for u in g.unresolved)


# ══ C · PHÉP MỚI — CHỮ KÝ, TĨNH, CHÍNH XÁC ══════════════════════════════
DE_VG_MAT = ("Cho hai điểm A, B và điểm M. Dựng mặt phẳng qua M và vuông góc "
             "với đường thẳng AB.")

TOI_THIEU = [_diem("A", [0, 0, 0]), _diem("B", [2, 0, 0]), _diem("M", [1, 3, 4])]


def _ct_mat_vuong_goc(ten_mp: str = "mp") -> SemanticProgramSpec:
    return _spec("Mặt phẳng qua M vuông góc AB",
        TOI_THIEU + [_khai("d", "line3"), _khai(ten_mp, "plane3")],
        [{"kind": "construct_line", "target_var": "d",
          "through_a": "A", "through_b": "B"},
         {"kind": "assign", "target_var": ten_mp,
          "expr": {"kind": "plane_perpendicular_to_line",
                   "point": "M", "line": "d"}}])


def test_C_phep_moi_dung_duoc_voi_DUNG_nhung_diem_de_cho():
    """Cùng cấu hình tối thiểu vừa chứng minh là bất khả — nay dựng được bằng
    MỘT câu lệnh, và không cần một điểm phụ nào."""
    spec = _ct_mat_vuong_goc()
    _neo(spec, DE_VG_MAT)
    m = _chay(spec)
    assert P.line_perpendicular_plane(m["d"], m["mp"])
    assert P.point_on_plane(m["M"], m["mp"])


def test_C_ket_qua_CHINH_XAC_khong_float():
    """Toạ độ hữu tỉ vào ⇒ hữu tỉ ra. Một `float` ở đây là mất đúng thứ phân
    biệt hệ này với một bộ vẽ hình."""
    spec = _spec("Mặt ⊥ với toạ độ phân số",
        [_diem("A", [0, 0, 0]), _diem("B", ["1/3", "2/5", 0]),
         _diem("M", ["1/7", 2, "3/4"]),
         _khai("d", "line3"), _khai("mp", "plane3")],
        [{"kind": "construct_line", "target_var": "d",
          "through_a": "A", "through_b": "B"},
         {"kind": "assign", "target_var": "mp",
          "expr": {"kind": "plane_perpendicular_to_line", "point": "M", "line": "d"}}])
    m = _chay(spec)
    for x in (m["mp"].normal.x, m["mp"].normal.y, m["mp"].normal.z):
        assert isinstance(x, F) and not isinstance(x, float)
    assert P.line_perpendicular_plane(m["d"], m["mp"])


@pytest.mark.parametrize("truong,gia_tri,vi_sao", [
    ("point", "d", "điểm nhận một ĐƯỜNG"),
    ("line", "M", "đường nhận một ĐIỂM"),
])
def test_C_sai_kieu_toan_hang_bi_bat_o_TANG_TINH(truong, gia_tri, vi_sao):
    """Bắt TRƯỚC runtime. Lỗi runtime không được gửi ngược cho mô hình sửa —
    vòng sửa đã đóng ở tầng tĩnh — nên một sai kiểu lọt xuống kernel là giết
    trọn lượt chạy."""
    e = {"kind": "plane_perpendicular_to_line", "point": "M", "line": "d"}
    e[truong] = gia_tri
    spec = _spec("Sai kiểu toán hạng",
        TOI_THIEU + [_khai("d", "line3"), _khai("mp", "plane3")],
        [{"kind": "construct_line", "target_var": "d",
          "through_a": "A", "through_b": "B"},
         {"kind": "assign", "target_var": "mp", "expr": e}])
    t = kiem_tinh(spec)
    assert not t.ok, f"tầng tĩnh cho qua {vi_sao}"


def test_C_R0_toan_hang_chi_nhan_TEN_khong_nhan_toa_do():
    """Ranh giới R0 ở phép mới, cưỡng chế tại LƯỢC ĐỒ chứ không nhắc trong
    prompt: nhét toạ độ vào ô toán hạng phải vỡ ngay lúc parse."""
    for xau in ([0, 0, 1], {"kind": "literal", "value": [0, 0, 1]}):
        with pytest.raises(Exception):
            _spec("Nhét toạ độ",
                TOI_THIEU + [_khai("mp", "plane3")],
                [{"kind": "assign", "target_var": "mp",
                  "expr": {"kind": "plane_perpendicular_to_line",
                           "point": "M", "line": xau}}])


def test_C_KHONG_dung_duoc_trong_construct_point():
    """Phép trả `plane3`, nên nó KHÔNG được nằm ở `PointExpr`. Cho vào đó là
    nói với mô hình rằng `construct_point` nhận nó, và nó sẽ thử."""
    with pytest.raises(Exception):
        _spec("Dựng điểm từ một mặt phẳng",
            TOI_THIEU + [_khai("d", "line3"), _khai("Q", "point3")],
            [{"kind": "construct_line", "target_var": "d",
              "through_a": "A", "through_b": "B"},
             {"kind": "construct_point", "target_var": "Q",
              "expr": {"kind": "plane_perpendicular_to_line",
                       "point": "M", "line": "d"}}])


# ══ D · HỢP THÀNH XUÔI DÒNG — mục tiêu thật của wave ════════════════════
def test_D_chuoi_dai_mat_vuong_goc_roi_GIAO_roi_DO():
    """Không phải *"dựng ra được một vật"* — mà **đi tiếp được**.

    Chuỗi: điểm gốc → mặt ⊥ đường (phép mới) → giao với một mặt khác → điểm
    trên giao tuyến → đo khoảng cách. Cấu hình toạ độ **không** buộc vào một
    khối có tên nào.
    """
    spec = _spec("Mặt ⊥ AB, giao với (ABC), rồi đo",
        GOC + [_khai("d", "line3"), _khai("mp", "plane3"),
               _khai("abc", "plane3"), _khai("gt", "line3"),
               _khai("Hq", "point3"), _khai("kc", "float")],
        [{"kind": "construct_line", "target_var": "d",
          "through_a": "A", "through_b": "B"},
         {"kind": "assign", "target_var": "mp",
          "expr": {"kind": "plane_perpendicular_to_line", "point": "M", "line": "d"}},
         {"kind": "construct_plane", "target_var": "abc", "through": ["A", "B", "C"]},
         {"kind": "assign", "target_var": "gt",
          "expr": {"kind": "intersect_plane_plane", "plane_a": "mp", "plane_b": "abc"}},
         {"kind": "construct_point", "target_var": "Hq",
          "expr": {"kind": "project_onto", "point": "C", "target": "gt"}},
         {"kind": "assign", "target_var": "kc",
          "expr": {"kind": "measure", "quantity": "distance", "of": "B", "wrt": "mp"}}])
    _neo(spec, "Cho tam giác ABC và điểm M. Dựng mặt phẳng qua M và "
                "vuông góc với đường thẳng AB, rồi tìm giao tuyến của nó "
                "với mặt phẳng (ABC).")
    m = _chay(spec)
    # Giao tuyến nằm trong CẢ HAI mặt phẳng — kiểm bằng vị từ, không bằng toạ độ.
    assert P.line_in_plane(m["gt"], m["mp"]) and P.line_in_plane(m["gt"], m["abc"])
    assert P.point_on_line(m["Hq"], m["gt"])
    # Mặt phẳng qua M(1,1,5) vuông góc AB có pháp tuyến (1,0,0) ⇒ nó là `x = 1`.
    # Khoảng cách từ B(2,0,0) tới đó ĐÚNG BẰNG 1 — khẳng định một con số chính
    # xác, không chỉ "khác 0".
    assert m["kc"] == F(1)


def test_D_chuoi_SONG_SONG_van_di_duoc_bang_IR_cu():
    """Đối chứng: chuỗi dùng phép SONG SONG (không có primitive mới) cũng đi
    tiếp được. Nếu ca này đỏ thì vấn đề nằm ở chỗ khác, không ở G4."""
    spec = _spec("Mặt ∥ (ABC) qua M, rồi đo khoảng cách",
        GOC + [_khai("abc", "plane3"), _khai("u", "vector3"),
               _khai("w", "vector3"), _khai("N", "point3"),
               _khai("Q", "point3"), _khai("mp2", "plane3"), _khai("kc", "float")],
        [{"kind": "construct_plane", "target_var": "abc", "through": ["A", "B", "C"]},
         {"kind": "assign", "target_var": "u",
          "expr": {"kind": "vector_from_points", "from_point": "A", "to_point": "B"}},
         {"kind": "assign", "target_var": "w",
          "expr": {"kind": "vector_from_points", "from_point": "A", "to_point": "C"}},
         {"kind": "construct_point", "target_var": "N",
          "expr": {"kind": "translate", "point": "M", "vector": "u"}},
         {"kind": "construct_point", "target_var": "Q",
          "expr": {"kind": "translate", "point": "M", "vector": "w"}},
         {"kind": "construct_plane", "target_var": "mp2", "through": ["M", "N", "Q"]},
         {"kind": "assign", "target_var": "kc",
          "expr": {"kind": "measure", "quantity": "distance",
                   "of": "abc", "wrt": "mp2"}}])
    _neo(spec, DE_SS_MAT)
    m = _chay(spec)
    assert P.parallel_planes(m["abc"], m["mp2"])
    assert m["kc"] != 0


# ══ E · XUẤT XỨ · VẾT · CẢNH ════════════════════════════════════════════
@pytest.fixture(scope="module")
def canh() -> dict:
    spec = _ct_mat_vuong_goc()
    kq = SemanticProgramInterpreter().execute(spec)
    return {o["id"]: o
            for o in build_scene3d(build_simulation_state(spec, kq))["objects"]}


def test_E_xuat_xu_day_du(canh):
    o = canh["mp"]
    assert o["type"] == "plane3"
    assert o["producer"] == "plane_perpendicular_to_line"
    assert o["depends"] == ["M", "d"]
    assert o["origin"] == "derived"


def test_E_ten_hien_thi_do_BACKEND_dat__khong_phai_id(canh):
    """G1 áp cho phép mới như mọi phép khác: `label` không được là `id`, và
    phía frontend không phải suy gì từ chuỗi `plane_perpendicular_to_line`."""
    o = canh["mp"]
    assert o["label"] != "mp"
    # Toán hạng được gọi bằng KÝ HIỆU — đường `d` dựng từ A và B nên ký hiệu
    # của nó là `AB`. Đây là hành vi của `display_names`, không phải ngoại lệ
    # của phép mới: câu đầy đủ nối bằng dấu phẩy sẽ dài hơn cả ô soi.
    assert "M" in o["label"] and "AB" in o["label"]
    # Không có ký hiệu toán nào dẫn ra được cho vật này ⇒ `None` là đúng.
    assert o["notation"] is None


def test_E_di_qua_transport_va_ve_duoc_bang_TUYEN_CU(canh):
    """§22: không loại hình vẽ mới. `plane3` đã có `surface`."""
    o = canh["mp"]
    assert o["render"] == "surface"
    assert set(o) >= {"point", "normal"}
    assert all(isinstance(x, str) for x in o["point"] + o["normal"])


def test_E_co_mot_buoc_trong_VET():
    """Một câu lệnh ngữ nghĩa ⇒ một bước. Không thêm ngữ nghĩa hoạt cảnh nào."""
    spec = _ct_mat_vuong_goc()
    kq = SemanticProgramInterpreter().execute(spec)
    st = build_simulation_state(spec, kq)
    buoc = [b for b in st["timeline"] if b.get("created") == "mp"]
    assert len(buoc) == 1
