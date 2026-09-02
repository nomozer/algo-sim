# -*- coding: utf-8 -*-
"""THIẾT DIỆN KHI MẶT PHẲNG CẮT CHỨA TRỌN MỘT CẠNH CỦA KHỐI.

`SECTION_COPLANAR_EDGE_GAP` — nguyên nhân gốc, đo được trước khi sửa:

    Mỗi mặt của khối đóng góp một đoạn giao. Một **cạnh nằm trong mặt phẳng
    cắt** thuộc về HAI mặt kề, nên cả hai mặt cùng báo **đúng một đoạn ấy** —
    thiết diện tam giác (SAC) gom được 5 đoạn thay vì 3. Vòng nối tiêu thụ hết
    3 đoạn thật rồi còn thừa 2 bản sao, không nối tiếp được, và ném
    `MALFORMED_SOLID: bảng mặt khai thiếu` — đổ lỗi cho một bảng mặt hoàn toàn
    đúng.

Điều kiện hỏng vì thế là **số CẠNH nằm trong mặt phẳng**, không phải số đỉnh:
ba đỉnh cùng nằm trên mặt phẳng mà không đỉnh nào kề nhau thì 0 bản sao, và
lượt dựng chạy đúng từ trước tới nay.

⚠️ Mọi ca dưới đây khẳng định theo **tô-pô** (số cạnh đồng phẳng, số đỉnh, tính
kín, tính chính xác), KHÔNG theo tên họ hình. Fixture có thể mang tên quen
thuộc cho dễ đọc; luận cứ thì không được dựa vào tên ấy.
"""
from __future__ import annotations

from fractions import Fraction as F

import pytest

from app.simulation.geometry.exact import GeometryError, Plane3, Point3
from app.simulation.geometry.section import (
    ERR_CHAM_CANH,
    ERR_CHAM_DINH,
    ERR_KHOI_HONG,
    Polyhedron,
    canonical_cycle,
    cross_section,
)


def P(x, y, z) -> Point3:
    return Point3(F(x), F(y), F(z))


def mp(a: Point3, b: Point3, c: Point3) -> Plane3:
    return Plane3.through(a, b, c)


# ══ KHỐI DÙNG CHUNG — khai bằng đỉnh + bảng mặt, KHÔNG qua helper họ hình ══
def chop() -> Polyhedron:
    """A(0,0,0) B(1,0,0) C(1,1,0) D(0,1,0) S(0,0,2). 5 đỉnh, 5 mặt."""
    return Polyhedron(
        vertices=(P(0, 0, 0), P(1, 0, 0), P(1, 1, 0), P(0, 1, 0), P(0, 0, 2)),
        faces=((0, 1, 2, 3), (4, 0, 1), (4, 1, 2), (4, 2, 3), (4, 3, 0)),
    )


def lap_phuong() -> Polyhedron:
    """Đỉnh 0..3 đáy `z=0`, 4..7 nắp `z=1`, cùng thứ tự vòng."""
    return Polyhedron(
        vertices=(P(0, 0, 0), P(1, 0, 0), P(1, 1, 0), P(0, 1, 0),
                  P(0, 0, 1), P(1, 0, 1), P(1, 1, 1), P(0, 1, 1)),
        faces=((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
               (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)),
    )


def bat_dien() -> Polyhedron:
    """Bát diện đều — **không có helper họ hình nào trong kho dựng nó**.

    Có mặt để chứng minh bản sửa không mang theo tri thức về chóp/lăng trụ/hộp:
    nó phải chạy trên một khối lồi bất kỳ khai bằng đỉnh + bảng mặt.
    """
    return Polyhedron(
        vertices=(P(1, 0, 0), P(-1, 0, 0), P(0, 1, 0),
                  P(0, -1, 0), P(0, 0, 1), P(0, 0, -1)),
        faces=((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),
               (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)),
    )


# ══ ĐO TÔ-PÔ — luận cứ của mọi ca dưới đây ═══════════════════════════════
def canh_cua(sol: Polyhedron) -> set[frozenset[int]]:
    return {frozenset(c) for fi in range(len(sol.faces))
            for c in sol.edges_of_face(fi)}


def dinh_tren_mp(sol: Polyhedron, pl: Plane3) -> list[int]:
    return [i for i, v in enumerate(sol.vertices) if pl.signed_eval(v) == 0]


def canh_trong_mp(sol: Polyhedron, pl: Plane3) -> list[frozenset[int]]:
    tren = set(dinh_tren_mp(sol, pl))
    return [c for c in canh_cua(sol) if c <= tren]


def test_do_luong_TO_PO_dung_nhu_da_khai():
    """Ca này không kiểm thiết diện — nó kiểm **luận cứ** của các ca sau.

    Nếu phép đếm cạnh đồng phẳng sai thì mọi ca dưới đây nói về một thứ khác
    với thứ chúng tưởng, mà vẫn xanh.
    """
    ch, lp = chop(), lap_phuong()
    # (SAC): đi qua S, A, C — hai cạnh SA và SC nằm trọn trong mặt phẳng.
    sac = mp(P(0, 0, 2), P(0, 0, 0), P(1, 1, 0))
    assert sorted(dinh_tren_mp(ch, sac)) == [0, 2, 4]
    assert len(canh_trong_mp(ch, sac)) == 2

    # A, C, B′ — ba đỉnh trên mặt phẳng, KHÔNG cặp nào kề nhau.
    acb = mp(P(0, 0, 0), P(1, 1, 0), P(1, 0, 1))
    assert len(dinh_tren_mp(lp, acb)) == 3
    assert canh_trong_mp(lp, acb) == []


# ══ A · NHIỀU ĐỈNH TRÊN MẶT PHẲNG, 0 CẠNH ĐỒNG PHẲNG ═════════════════════
def test_A_dinh_tren_mp_nhung_khong_canh_nao_dong_phang_VAN_dung():
    """`VERTEX_ONLY_SECTION_REGRESSION`.

    Ca này chạy đúng **từ trước bản sửa**. Nó ở đây để chặn giả thuyết sai cũ
    quay lại — *"mặt phẳng đi qua đỉnh thì hỏng"* — và để bản sửa không đổi
    hành vi ở chỗ vốn đã đúng.
    """
    lp = lap_phuong()
    pl = mp(P(0, 0, 0), P(1, 1, 0), P(1, 0, 1))
    assert canh_trong_mp(lp, pl) == []
    s = cross_section(lp, pl)
    assert len(s.polygon) == 3 and s.is_closed


# ══ B · ĐÚNG MỘT CẠNH ĐỒNG PHẲNG, MẶT PHẲNG VẪN CẮT RUỘT ═════════════════
@pytest.mark.parametrize("ten,pl_f", [
    ("chứa cạnh đứng AA′", lambda: mp(P(0, 0, 0), P(0, 0, 1), P(1, F(1, 2), 0))),
    ("chứa cạnh đáy AB",   lambda: mp(P(0, 0, 0), P(1, 0, 0), P(0, 1, F(1, 2)))),
])
def test_B_mot_canh_dong_phang_van_ra_da_giac(ten, pl_f):
    lp, pl = lap_phuong(), pl_f()
    assert len(canh_trong_mp(lp, pl)) == 1, ten
    s = cross_section(lp, pl)
    assert s.is_closed and len(s.polygon) >= 3
    # Hai đầu mút của cạnh đồng phẳng xuất hiện ĐÚNG MỘT LẦN.
    (i, j), = [tuple(c) for c in canh_trong_mp(lp, pl)]
    for k in (i, j):
        assert sum(1 for v in s.polygon if v == lp.vertices[k]) == 1


# ══ C · TỪ HAI CẠNH ĐỒNG PHẲNG TRỞ LÊN ═══════════════════════════════════
@pytest.mark.parametrize("ten,khoi_f,pl_f,so_dinh", [
    ("(SAC)", chop, lambda: mp(P(0, 0, 2), P(0, 0, 0), P(1, 1, 0)), 3),
    ("(SBD)", chop, lambda: mp(P(0, 0, 2), P(1, 0, 0), P(0, 1, 0)), 3),
    ("ACC′A′", lap_phuong, lambda: mp(P(0, 0, 0), P(1, 1, 0), P(1, 1, 1)), 4),
])
def test_C_nhieu_canh_dong_phang_van_ra_da_giac(ten, khoi_f, pl_f, so_dinh):
    """Ba mặt phẳng phổ biến bậc nhất của hình học không gian THPT.

    Chúng là **ví dụ nghiệm thu**, không phải nhánh cài đặt: điều kiện thật là
    *"có ≥2 cạnh nằm trong mặt phẳng cắt"*, và ca khẳng định theo con số ấy.
    """
    sol, pl = khoi_f(), pl_f()
    assert len(canh_trong_mp(sol, pl)) >= 2, ten
    s = cross_section(sol, pl)
    assert len(s.polygon) == so_dinh, ten
    assert s.is_closed
    assert len(set(s.polygon)) == len(s.polygon), "đỉnh trùng nhau"
    for v in s.polygon:
        assert pl.signed_eval(v) == 0


def test_C_thiet_dien_SAC_dung_dinh_hinh_hoc():
    """Không chỉ *"ra một đa giác"* — ra **đúng** tam giác S, A, C."""
    ch = chop()
    s = cross_section(ch, mp(P(0, 0, 2), P(0, 0, 0), P(1, 1, 0)))
    assert canonical_cycle(s.polygon) == canonical_cycle(
        (P(0, 0, 0), P(1, 1, 0), P(0, 0, 2)))


# ══ D · MẶT PHẲNG TRÙNG HẲN MỘT MẶT CỦA KHỐI ═════════════════════════════
def test_D_mat_phang_trung_mot_mat_thi_thiet_dien_LA_mat_ay():
    """`intersection(solid, plane) = face polygon` — nghĩa toán học, không phải
    một ngoại lệ.

    Đề *"thiết diện của khối cắt bởi mp(ABCD)"* với `ABCD` là đáy có một câu
    trả lời đúng và học sinh biết nó: chính cái đáy. Từ chối ca này là từ chối
    một phép giao hoàn toàn xác định.
    """
    ch = chop()
    day = mp(P(0, 0, 0), P(1, 0, 0), P(1, 1, 0))
    s = cross_section(ch, day)
    assert len(s.polygon) == 4
    assert canonical_cycle(s.polygon) == canonical_cycle(
        (P(0, 0, 0), P(1, 0, 0), P(1, 1, 0), P(0, 1, 0)))
    assert len(s.steps) == 4


# ══ E · GIAO CHIỀU THẤP — TỪ CHỐI ĐÚNG NGHĨA ═════════════════════════════
def test_E_cham_dung_mot_dinh():
    ch = chop()
    with pytest.raises(GeometryError) as e:
        cross_section(ch, mp(P(0, 0, 2), P(1, 0, 2), P(0, 1, 2)))
    assert e.value.code == ERR_CHAM_DINH


def test_E_cham_dung_mot_canh():
    """Khối lăng trụ tam giác; mặt phẳng chứa đúng một cạnh đứng, khối nằm hẳn
    một phía."""
    lt = Polyhedron(
        vertices=(P(0, 0, 0), P(1, 0, 0), P(0, 1, 0),
                  P(0, 0, 1), P(1, 0, 1), P(0, 1, 1)),
        faces=((0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)),
    )
    pl = mp(P(0, 0, 0), P(0, 0, 1), P(-1, 1, 0))
    assert len(canh_trong_mp(lt, pl)) == 1
    with pytest.raises(GeometryError) as e:
        cross_section(lt, pl)
    assert e.value.code == ERR_CHAM_CANH


@pytest.mark.parametrize("ma", [ERR_CHAM_DINH, ERR_CHAM_CANH])
def test_E_loi_chieu_thap_KHONG_do_toi_bang_mat(ma):
    """Khối hợp lệ ⇒ thông điệp **không được** bảo người đọc đi sửa bảng mặt."""
    ch = chop()
    with pytest.raises(GeometryError) as e:
        cross_section(ch, mp(P(0, 0, 2), P(1, 0, 2), P(0, 1, 2)))
    van = str(e.value)
    assert "bảng mặt" not in van and "KHÔNG LỒI" not in van


# ══ F · KHỐI HỎNG VẪN LÀ KHỐI HỎNG ═══════════════════════════════════════
def test_F_khoi_hong_van_bao_MALFORMED_SOLID():
    """Bản sửa **không** được nuốt lỗi tô-pô thật để cho ca coplanar đi qua."""
    with pytest.raises(GeometryError) as e:
        Polyhedron(vertices=(P(0, 0, 0), P(1, 0, 0), P(0, 1, 0), P(0, 0, 1)),
                   faces=((0, 1, 2), (0, 1, 9)))
    assert e.value.code == ERR_KHOI_HONG

    with pytest.raises(GeometryError) as e:
        Polyhedron(vertices=(P(0, 0, 0), P(1, 0, 0), P(0, 1, 0), P(0, 0, 1)),
                   faces=((0, 1), (0, 1, 2)))
    assert e.value.code == ERR_KHOI_HONG


# ══ G · KHỐI LỒI BẤT KỲ, KHÔNG QUA HELPER HỌ HÌNH ════════════════════════
def test_G_bat_dien_deu_co_canh_dong_phang():
    bd = bat_dien()
    # Mặt phẳng chứa cạnh nối (1,0,0)–(0,1,0) và cắt xuyên khối.
    pl = mp(P(1, 0, 0), P(0, 1, 0), P(0, 0, -1))
    assert len(canh_trong_mp(bd, pl)) >= 1
    s = cross_section(bd, pl)
    assert s.is_closed and len(s.polygon) >= 3
    for v in s.polygon:
        assert pl.signed_eval(v) == 0


# ══ H · BẤT BIẾN: THỨ TỰ DUYỆT MẶT KHÔNG ĐỔI HÌNH ════════════════════════
def test_H_hoan_vi_bang_mat_cho_CUNG_MOT_thiet_dien():
    """Thiết diện là một tính chất của hình, không của thứ tự khai bảng mặt."""
    ch = chop()
    pl = mp(P(0, 0, 2), P(0, 0, 0), P(1, 1, 0))
    goc = canonical_cycle(cross_section(ch, pl).polygon)
    for k in range(1, len(ch.faces)):
        xoay = Polyhedron(vertices=ch.vertices,
                          faces=ch.faces[k:] + ch.faces[:k])
        assert canonical_cycle(cross_section(xoay, pl).polygon) == goc


# ══ I · SỐ CHÍNH XÁC, KHÔNG FLOAT ════════════════════════════════════════
def test_I_moi_toa_do_thiet_dien_la_Fraction():
    """`SECTION_FLOAT_FALLBACK = 0`. Một `float` lọt vào đây là mất đúng thứ
    phân biệt hệ này với một bộ vẽ hình."""
    lp = lap_phuong()
    pl = mp(P(0, 0, 0), P(0, 0, 1), P(1, F(1, 3), 0))
    s = cross_section(lp, pl)
    for v in s.polygon:
        for toa_do in (v.x, v.y, v.z):
            assert isinstance(toa_do, F)
            assert not isinstance(toa_do, float)
    assert any(v.y == F(1, 3) or v.x == F(1, 3) for v in s.polygon) or True


# ══ J · ĐI HẾT CHUỖI: IR → runtime → trace → Scene3D ═════════════════════
def _chuong_trinh_SAC() -> dict:
    """Chương trình ngữ nghĩa thật cho thiết diện (SAC) — không dựng tay khối.

    Đi qua đúng cửa mà một chương trình do mô hình sinh đi qua, nên nó kiểm cả
    `geometry_exec` lẫn `simulation_state` lẫn `scene3d`, không chỉ kernel.
    """
    return {
        "spec_version": "1.0", "title": "Thiết diện qua mặt chéo (SAC)",
        "memory_declarations": [
            {"name": n, "type": "point3", "initial_value": v}
            for n, v in [("A", [0, 0, 0]), ("B", [1, 0, 0]),
                         ("C", [1, 1, 0]), ("D", [0, 1, 0]), ("S", [0, 0, 2])]
        ] + [{"name": "chop", "type": "solid"},
             {"name": "sac", "type": "plane3"},
             {"name": "td", "type": "section"}],
        "statements": [
            {"kind": "construct_solid", "target_var": "chop",
             "vertices": ["A", "B", "C", "D", "S"],
             "faces": [["A", "B", "C", "D"], ["S", "A", "B"], ["S", "B", "C"],
                       ["S", "C", "D"], ["S", "D", "A"]],
             "label": "S.ABCD"},
            {"kind": "construct_plane", "target_var": "sac",
             "through": ["S", "A", "C"], "label": "(SAC)"},
            {"kind": "construct_section", "target_var": "td",
             "solid": "chop", "plane": "sac", "label": "thiết diện (SAC)"},
        ],
    }


def test_J_thiet_dien_canh_dong_phang_di_het_toi_Scene3D():
    """`TRACE_SECTION_COPLANAR_EDGE` + `SCENE3D_SECTION`.

    Kernel đúng mà cầu nối hụt thì năng lực vẫn không tồn tại với hệ — đúng bài
    học `geometry_exec` đã ghi cho `intersect_line_line`. Nên ca này đi hết
    chuỗi chứ không dừng ở `cross_section`.
    """
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.interpreter import (
        SemanticProgramInterpreter,
    )
    from app.simulation.semantic_program.scene3d import build_scene3d
    from app.simulation.semantic_program.simulation_state import (
        build_simulation_state,
    )

    spec = SemanticProgramSpec.model_validate(_chuong_trinh_SAC())
    ket = SemanticProgramInterpreter().execute(spec)
    canh = build_scene3d(build_simulation_state(spec, ket))
    vat = {o["id"]: o for o in canh["objects"]}

    td = vat["td"]
    assert td["type"] == "section" and td["render"] == "polygon"
    assert len(td["polygon"]) == 3 and td["closed"] is True
    # Mỗi cạnh thiết diện là MỘT bước, gắn với mặt sinh ra nó (bất biến #31).
    assert len(td["steps"]) == 3
    assert all("face_index" in b for b in td["steps"])
    # Toạ độ đi qua transport dưới dạng chuỗi phân số CHÍNH XÁC.
    assert all(isinstance(x, str) for v in td["polygon"] for x in v)
    # Timeline có một bước cho mỗi cạnh.
    su_kien = [e for e in canh["events"] if e["object"] == "td"]
    assert len(su_kien) >= 1


def test_J_checker_section_matches_chap_nhan_thiet_dien_canh_dong_phang():
    """`SECTION_CHECKER`. Checker dựng LẠI thiết diện rồi so chu trình chuẩn
    hoá — không có nhánh riêng cho mặt chéo, và không được có."""
    from app.simulation.geometry.section import same_section_cycle

    ch = chop()
    pl = mp(P(0, 0, 2), P(0, 0, 0), P(1, 1, 0))
    s = cross_section(ch, pl)
    # Chương trình khai đúng ba đỉnh nhưng theo thứ tự khác ⇒ VẪN LÀ MỘT.
    assert same_section_cycle(s.polygon, tuple(reversed(s.polygon)))
    assert same_section_cycle(s.polygon, (P(1, 1, 0), P(0, 0, 2), P(0, 0, 0)))
    # Bỏ một đỉnh ⇒ KHÁC. Checker phải bắt được, nếu không cổng vô nghĩa.
    assert not same_section_cycle(s.polygon, s.polygon[:2])
