# -*- coding: utf-8 -*-
"""NỀN HÌNH CONG — cầu · trụ · nón trên MỘT thẩm quyền. **0 API call.**

Phase 2 của `docs/CURVED_GEOMETRY_FOUNDATION_DESIGN.md`.

─── BA ĐIỀU FILE NÀY CANH, NGOÀI VIỆC CÔNG THỨC ĐÚNG ──────────────────────

**① MIỀN TOẠ ĐỘ KHÔNG ĐƯỢC MỞ.** Hình cong không được kéo theo một toạ độ vô
tỉ nào. Đó là ranh giới cứng hơn "chưa có mặt cong": giao *đường thẳng* với mặt
cong cho `t = (−B ± √Δ)/2A` và toạ độ rơi vào `ℚ(√Δ)³`, thứ `Vec3` không chở
nổi — nên phép ấy KHÔNG tồn tại, và `test_36_*` giữ nó không tồn tại.

**② KHÔNG NÓI DỐI HỢP ĐỒNG KIỂU.** `intersect_plane_curved` khai trả `circle3`
và **chỉ** trả `circle3`. Mọi ca suy biến từ chối có mã, và lời từ chối nêu tên
phép dựng đúng. Khai một kiểu rồi trả kiểu khác là nói dối với tầng duy nhất
bắt được lỗi mô hình trước khi tốn một lượt chạy.

**③ HÌNH MỚI KHÔNG PHẢI MÃ MỚI.** Sáu nhân chứng ở §38 chạy hết đường IR, và
nhân chứng thứ sáu — thiết diện qua trục — dùng **0 phép dựng mới**: điểm xuyên
tâm đối là `divide_segment(A, O, "2")`, nối là `construct_polygon`, đo là
`measure area` của Phase 1.
"""
from __future__ import annotations

from fractions import Fraction as F

import pytest

from app.simulation.geometry import curved as CV
from app.simulation.geometry.curved import (
    KHOI_CONG,
    Circle3,
    CurvedSolid,
    intersect_plane_curved,
)
from app.simulation.geometry.exact import GeometryError, Plane3, Vec3
from app.simulation.geometry.radical import Radical, display, radical
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.grounding_gate import check_grounding
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.ir_static_check import kiem_tinh

v = Vec3.of


# ══ HẠ TẦNG DÙNG CHUNG ═══════════════════════════════════════════════════
def _spec(khai: list[dict], statements: list[dict]) -> dict:
    return {
        "spec_version": "1.0", "title": "Khối cong",
        "description": "Dựng một khối cong rồi đo nó.",
        "pedagogical_intent": "Thấy khối cong là hệ quả của các điểm đã dựng.",
        "memory_declarations": khai, "statements": statements,
        "visual_bindings": {"containers": [], "pointers": [], "value_boxes": []},
    }


def _diem(*ten_toa: tuple[str, list]) -> list[dict]:
    return [{"name": t, "type": "point3", "initial_value": xy} for t, xy in ten_toa]


def _chay(raw: dict):
    spec = SemanticProgramSpec.model_validate(raw)
    r = kiem_tinh(spec)
    assert r.ok, [i.dong() for i in r.issues]
    return SemanticProgramInterpreter().execute(spec)


def _canh(raw: dict) -> dict:
    from app.simulation.semantic_program.simulation_state import build_scene

    spec = SemanticProgramSpec.model_validate(raw)
    return build_scene(spec, SemanticProgramInterpreter().execute(spec).final_memory)


def _do(ten: str, q: str, of: str) -> dict:
    return {"kind": "assign", "target_var": ten,
            "expr": {"kind": "measure", "quantity": q, "of": of}}


# ══ §4 · MỘT THẨM QUYỀN LOẠI KHỐI ════════════════════════════════════════
def test_04_dung_MOT_bang_loai_khoi_cho_ca_ba_hinh():
    assert set(KHOI_CONG) == {"ball", "cylinder", "cone"}
    for kc in KHOI_CONG.values():
        assert kc.the_tich and kc.mat_cong and kc.danh_tu


def test_04b_KHONG_module_rieng_cho_tung_hinh():
    """`SHAPE_SPECIFIC_PRODUCT_MODULES = 0` — kiểm bằng cây thư mục thật."""
    from pathlib import Path

    goc = Path(CV.__file__).resolve().parents[3]
    cam = {"sphere.py", "cylinder.py", "cone.py", "ball.py"}
    co = {p.name for p in goc.rglob("*.py") if p.name in cam}
    assert not co, f"có module riêng theo hình: {sorted(co)}"


def test_04c_dieu_phoi_theo_kind_KHONG_rai_khap_cac_tang():
    """Chuỗi `if ball / if cylinder / if cone` chỉ được tồn tại ở MỘT chỗ.

    Kiểm theo hướng yếu mà chắc: đếm số tệp sản phẩm nhắc tên cả ba hình. Bảng
    `KHOI_CONG` là một; hợp đồng khai enum là hai. Tệp thứ ba nghĩa là một tầng
    nào đó đã mọc bản điều phối của riêng nó.
    """
    from pathlib import Path

    goc = Path(CV.__file__).resolve().parents[2]
    hit = [p.relative_to(goc).as_posix() for p in goc.rglob("*.py")
           if all(t in p.read_text(encoding="utf-8")
                  for t in ('"ball"', '"cylinder"', '"cone"'))]
    assert sorted(hit) == ["simulation/geometry/curved.py",
                           "simulation/semantic_program/contract.py"], hit


# ══ §6 · BẤT BIẾN BA ĐIỂM ════════════════════════════════════════════════
@pytest.mark.parametrize("loai,neo,vi_pham", [
    ("ball", (v(0, 0, 0), None, v(0, 0, 0)), "bán kính 0"),
    ("cylinder", (v(0, 0, 0), v(0, 0, 2), v(1, 0, 1)), "vành không ⊥ trục"),
    ("cylinder", (v(0, 0, 0), v(0, 0, 0), v(1, 0, 0)), "chiều cao 0"),
    ("cylinder", (v(0, 0, 0), v(0, 0, 2), v(0, 0, 0)), "bán kính 0"),
    ("cone", (v(0, 0, 0), v(0, 0, 2), v(1, 1, 1)), "vành không ⊥ trục"),
    ("cone", (v(0, 0, 0), None, v(1, 0, 0)), "thiếu đỉnh"),
    ("ball", (v(0, 0, 0), v(0, 0, 1), v(1, 0, 0)), "cầu mà có trục"),
])
def test_06_neo_HONG_bi_tu_choi(loai, neo, vi_pham):
    """So BẰNG trên `Fraction`, không epsilon — lệch một phần triệu vẫn là một
    hình không tồn tại, và cho nó qua là để renderer vẽ ra thứ trông hợp lý mà
    sai."""
    with pytest.raises(GeometryError) as e:
        CurvedSolid(loai, *neo)
    assert e.value.code in (CV.ERR_KHOI_CONG_HONG, CV.ERR_LOAI_KHOI_LA), vi_pham


def test_06b_vanh_lech_MOT_PHAN_TRIEU_van_bi_tu_choi():
    eps = F(1, 10**6)
    with pytest.raises(GeometryError):
        CurvedSolid("cylinder", v(0, 0, 0), v(0, 0, 2), v(1, 0, eps))


def test_06c_loai_khoi_LA_bi_tu_choi():
    with pytest.raises(GeometryError) as e:
        CurvedSolid("torus", v(0, 0, 0), None, v(1, 0, 0))
    assert e.value.code == CV.ERR_LOAI_KHOI_LA


# ══ §10 · MIỀN TOẠ ĐỘ KHÔNG ĐỔI ══════════════════════════════════════════
def test_10_moi_toa_do_cua_khoi_cong_deu_HUU_TI():
    """Kể cả khi bán kính vô tỉ và trục xiên."""
    s = CurvedSolid("cylinder", v(0, 0, 0), v(1, 2, 2), v(2, -1, 0))
    assert display(CV.ban_kinh(s)) == "√5", "bán kính phải vô tỉ ở ca này"
    for p in (s.anchor, s.apex_or_top, s.rim_point):
        assert all(isinstance(c, F) for c in (p.x, p.y, p.z))
    assert isinstance(s.radius_sq, F) and isinstance(s.height_sq, F)


def test_10b_tam_duong_tron_giao_luon_HUU_TI():
    c = intersect_plane_curved(
        CurvedSolid("ball", v(0, 0, 0), None, v(3, 0, 0)),
        Plane3(v(0, 0, 2), v(0, 0, 1)))
    assert all(isinstance(x, F) for x in (c.center.x, c.center.y, c.center.z))
    assert isinstance(c.radius_sq, F)


# ══ §11 + §36 · KHÔNG SINH ĐIỂM TRÊN MẶT CONG ════════════════════════════
def test_11_KHONG_co_phep_giao_duong_thang_voi_mat_cong():
    """`CURVED_POINT_SOLVER_ADDED = NO` — kiểm bằng bảng chữ ký, không bằng
    lời hứa trong chú thích."""
    from app.simulation.semantic_program.ir_static_check import _CHU_KY

    for cam in ("intersect_line_curved", "intersect_line_sphere",
                "intersect_line_ball", "point_on_curved"):
        assert cam not in _CHU_KY
    cong = [k for k in _CHU_KY if "curved" in k]
    assert cong == ["intersect_plane_curved"], cong


def test_11b_loi_tu_choi_CHUNG_ton_tai_va_noi_dung_ly_do():
    e = CV.khong_sinh_diem_tren_mat_cong("intersect_line_curved")
    assert e.code == CV.ERR_NGOAI_BAO_DONG
    assert "không hữu tỉ" in str(e)


# ══ §12–13 · CIRCLE3 + GIAO MẶT CẦU ══════════════════════════════════════
def test_13_ba_ca_cua_mat_phang_x_mat_cau():
    """`d² > r²` không cắt · `d² == r²` tiếp xúc · `d² < r²` đường tròn."""
    cau = CurvedSolid("ball", v(0, 0, 0), None, v(3, 0, 0))
    c = intersect_plane_curved(cau, Plane3(v(0, 0, 2), v(0, 0, 1)))
    assert (c.center.x, c.center.y, c.center.z) == (0, 0, 2)
    assert c.radius_sq == 5, "r'² = r² − d² = 9 − 4"
    with pytest.raises(GeometryError) as e1:
        intersect_plane_curved(cau, Plane3(v(0, 0, 3), v(0, 0, 1)))
    assert e1.value.code == CV.ERR_TIEP_XUC
    with pytest.raises(GeometryError) as e2:
        intersect_plane_curved(cau, Plane3(v(0, 0, 4), v(0, 0, 1)))
    assert e2.value.code == CV.ERR_KHONG_CAT


def test_13b_loi_TIEP_XUC_chi_sang_phep_dung_DUNG():
    """Một lời từ chối không nói được đường đi tiếp là một lời từ chối bắt
    người đọc tự đoán — và họ sẽ đoán sai."""
    with pytest.raises(GeometryError) as e:
        intersect_plane_curved(
            CurvedSolid("ball", v(0, 0, 0), None, v(3, 0, 0)),
            Plane3(v(0, 0, 3), v(0, 0, 1)))
    assert "project_onto" in str(e.value)


def test_12_circle3_KHONG_ton_tai_voi_ban_kinh_0():
    """Bán kính 0 nghĩa là hình ấy **là một điểm**; trả `Circle3` là nói dối
    về kiểu."""
    with pytest.raises(GeometryError):
        Circle3(v(0, 0, 0), v(0, 0, 1), F(0))
    with pytest.raises(GeometryError):
        Circle3(v(0, 0, 0), v(0, 0, 0), F(1))


# ══ §14–15 · BAO ĐÓNG TRỤ VÀ NÓN ═════════════════════════════════════════
def test_14_tru_mp_vuong_goc_truc_cho_duong_tron():
    tru = CurvedSolid("cylinder", v(0, 0, 0), v(0, 0, 2), v(1, 0, 0))
    c = intersect_plane_curved(tru, Plane3(v(0, 0, 1), v(0, 0, 1)))
    assert c.radius_sq == 1 and (c.center.x, c.center.y, c.center.z) == (0, 0, 1)


def test_15_non_ban_kinh_CO_theo_vi_tri_tren_truc():
    """`r(t) = (1−t)·r_đáy` ⇒ ở giữa thân, `r² = r_đáy²/4`. Kiểm tay."""
    non = CurvedSolid("cone", v(0, 0, 0), v(0, 0, 2), v(1, 0, 0))
    assert intersect_plane_curved(non, Plane3(v(0, 0, 1), v(0, 0, 1))).radius_sq \
        == F(1, 4)


@pytest.mark.parametrize("loai", ["cylinder", "cone"])
@pytest.mark.parametrize("mp,ma", [
    (Plane3(v(0, 0, 1), v(1, 0, 1)), CV.ERR_NGOAI_BAO_DONG),   # xiên → elip
    (Plane3(v(0, 0, 0), v(1, 0, 0)), CV.ERR_NGOAI_BAO_DONG),   # qua trục
    (Plane3(v(0, 0, 5), v(0, 0, 1)), CV.ERR_KHONG_CAT),        # ngoài biên
    (Plane3(v(0, 0, -1), v(0, 0, 1)), CV.ERR_KHONG_CAT),       # dưới đáy
])
def test_1415_ngoai_bao_dong_TU_CHOI_dung_ma(loai, mp, ma):
    """⚠️ Mã lỗi **không** được là `MALFORMED_SOLID`: một mặt phẳng xiên cắt
    một hình trụ HOÀN TOÀN LÀNH LẶN thì khối không hỏng — chỉ là kết quả nằm
    ngoài thứ v1 biểu diễn được. Dùng lại mã cũ ở đây là lặp đúng lỗi mà
    `SECTION_COPLANAR_EDGE_GAP` đã phải đi sửa."""
    s = CurvedSolid(loai, v(0, 0, 0), v(0, 0, 2), v(1, 0, 0))
    with pytest.raises(GeometryError) as e:
        intersect_plane_curved(s, mp)
    assert e.value.code == ma
    assert "MALFORMED" not in e.value.code


def test_15b_mp_qua_DINH_non_tu_choi_vi_giao_la_mot_diem():
    non = CurvedSolid("cone", v(0, 0, 0), v(0, 0, 2), v(1, 0, 0))
    with pytest.raises(GeometryError) as e:
        intersect_plane_curved(non, Plane3(v(0, 0, 2), v(0, 0, 1)))
    assert e.value.code == CV.ERR_TIEP_XUC


def test_14b_loi_QUA_TRUC_chi_sang_duong_dung():
    """Thiết diện qua trục dựng được bằng IR đã có — lời từ chối phải nói ra."""
    with pytest.raises(GeometryError) as e:
        intersect_plane_curved(
            CurvedSolid("cylinder", v(0, 0, 0), v(0, 0, 2), v(1, 0, 0)),
            Plane3(v(0, 0, 0), v(1, 0, 0)))
    assert "divide_segment" in str(e.value) and "construct_polygon" in str(e.value)


# ══ §16 · HỢP ĐỒNG KIỂU KHÔNG NÓI DỐI ════════════════════════════════════
def test_16_intersect_plane_curved_LUON_tra_circle3_hoac_nem():
    """Không có nhánh nào trả `Point3`/`polygon3` lén lút."""
    import inspect

    src = inspect.getsource(CV.intersect_plane_curved) + \
        inspect.getsource(CV._giao_cau) + inspect.getsource(CV._giao_tron_xoay)
    assert "Point3(" not in src and "Polyhedron(" not in src
    for mp in (Plane3(v(0, 0, 1), v(0, 0, 1)), Plane3(v(0, 0, 0), v(0, 0, 1))):
        kq = intersect_plane_curved(
            CurvedSolid("ball", v(0, 0, 0), None, v(3, 0, 0)), mp)
        assert isinstance(kq, Circle3)


def test_16b_chu_ky_tinh_KHOP_kieu_runtime():
    from app.simulation.semantic_program.ir_static_check import _CHU_KY

    assert _CHU_KY["intersect_plane_curved"][1] == "circle3"


# ══ §41 · CHÍNH XÁC ══════════════════════════════════════════════════════
def test_41_cau_R2_bang_3():
    s = CurvedSolid("ball", v(0, 0, 0), None, v(1, 1, 1))
    assert s.radius_sq == 3
    assert display(CV.ban_kinh(s)) == "√3"
    assert display(CV.the_tich(s)) == "4π√3", "V = (4/3)π·3√3"
    assert display(CV.dien_tich_mat_cong(s)) == "12π", "S = 4π·3"


def test_41b_tru_ban_kinh_VO_TI_neo_HUU_TI():
    """Trục xiên `(1,2,2)`, `A(2,−1,0)` ⊥ trục ⇒ `r = √5`, `h = 3`.
    `V = π·5·3 = 15π`, `S_xq = 2π·√5·3 = 6π√5`. Kiểm tay."""
    s = CurvedSolid("cylinder", v(0, 0, 0), v(1, 2, 2), v(2, -1, 0))
    assert (s.radius_sq, s.height_sq) == (5, 9)
    assert display(CV.the_tich(s)) == "15π"
    assert display(CV.dien_tich_mat_cong(s)) == "6π√5"


def test_41c_non_duong_sinh_can_5():
    """`r = 1, h = 2` ⇒ `l = √5` ⇒ `S_xq = πrl = π√5`, `V = (1/3)π·1·2`."""
    s = CurvedSolid("cone", v(0, 0, 0), v(0, 0, 2), v(1, 0, 0))
    assert display(CV.dien_tich_mat_cong(s)) == "π√5"
    assert display(CV.the_tich(s)) == "2π/3"


def test_41d_KHONG_float_o_bat_ky_ket_qua_ngu_nghia_nao():
    for s in (CurvedSolid("ball", v(0, 0, 0), None, v(1, 1, 1)),
              CurvedSolid("cylinder", v(0, 0, 0), v(1, 2, 2), v(2, -1, 0)),
              CurvedSolid("cone", v(0, 0, 0), v(0, 0, 2), v(1, 0, 0))):
        for x in (CV.the_tich(s), CV.dien_tich_mat_cong(s), CV.ban_kinh(s)):
            assert isinstance(x, (F, Radical)), f"{x!r} không phải số chính xác"


def test_41e_dien_tich_hinh_tron_la_pi_nhan_ban_kinh_binh():
    c = Circle3(v(0, 0, 0), v(0, 0, 1), F(5))
    assert display(CV.dien_tich_hinh_tron(c)) == "5π"
    assert CV.dien_tich_hinh_tron(c) == radical(5, 1, 1)


# ══ §19 + §42 · KHÔNG HỨA DIỆN TÍCH TOÀN PHẦN ════════════════════════════
def test_42_KHONG_co_phep_do_surface_area_tong_quat():
    from app.simulation.semantic_program.measure_contract import BANG_PHEP_DO

    assert "surface_area" not in BANG_PHEP_DO
    assert "total_area" not in BANG_PHEP_DO
    assert "lateral_area" in BANG_PHEP_DO


def test_42b_TAI_SAO_khong_hua_toan_phan__chung_minh_bang_mien_so():
    """Ca đối kháng: `S_tp` nón `= πrl + πr²` với `r = 1, h = 2` là
    `π√5 + π` — hai căn thức khác nhau, miền số TỪ CHỐI.

    Nếu một ngày ai đó thêm `surface_area`, ca này vẫn đỏ ở đúng chỗ: phép
    cộng, không phải ở tên phép đo.
    """
    from app.simulation.geometry.radical import RadicalDomainError, add

    non = CurvedSolid("cone", v(0, 0, 0), v(0, 0, 2), v(1, 0, 0))
    xq = CV.dien_tich_mat_cong(non)
    day = radical(non.radius_sq, 1, 1)
    assert display(xq) == "π√5" and display(day) == "π"
    with pytest.raises(RadicalDomainError):
        add(xq, day)


def test_19_ba_cong_thuc_mat_cong_LUON_bieu_dien_duoc():
    """Chứng minh bằng liệt kê trên một lưới neo hữu tỉ, không bằng lập luận.

    Mỗi kết quả là *một hữu tỉ × π × đúng một căn của một hữu tỉ không âm*, và
    `sqrt_rational` không có nhánh thất bại trên miền ấy.
    """
    n = 0
    for a in (1, 2, 3):
        for b in (1, 3, 5):
            for c in (1, 2, 7):
                for loai in ("ball", "cylinder", "cone"):
                    dinh = None if loai == "ball" else v(0, 0, c)
                    s = CurvedSolid(loai, v(0, 0, 0), dinh, v(a, b, 0))
                    assert isinstance(CV.dien_tich_mat_cong(s), (F, Radical))
                    assert isinstance(CV.the_tich(s), (F, Radical))
                    n += 1
    assert n == 81


# ══ §26 · KHÔNG THÊM CHECKER ═════════════════════════════════════════════
def test_26_KHONG_them_checker_nao():
    """`CHECKERS_ADDED = 0`, và đó là quyết định có lý do kép:

    ① Taxonomy nghĩa vụ **đã niêm phong** cùng baseline nghiên cứu; thêm một
       checker là đổi băm taxonomy, thứ `§44` cấm chạm.
    ② Không nghĩa vụ v1 nào ĐÒI một checker cong: bao đóng v1 không có mệnh đề
       *"chứng minh M thuộc mặt cầu"*. Thêm cho đối xứng là thêm mã chết.
    """
    from app.simulation.semantic_program.geometry_obligations import (
        GEOMETRY_CHECKERS,
    )

    assert set(GEOMETRY_CHECKERS) == {
        "point_on_line", "point_on_plane", "parallel", "perpendicular",
        "coplanar", "section_matches", "distance", "angle", "volume"}


# ══ §38 · SÁU NHÂN CHỨNG, 0 LƯỢT GỌI MODEL ═══════════════════════════════
_CAU = _diem(("I", [0, 0, 0]), ("A", [1, 1, 1]))
_TRU = _diem(("O", [0, 0, 0]), ("Ot", [0, 0, 2]), ("A", [1, 0, 0]))
_NON = _diem(("O", [0, 0, 0]), ("S", [0, 0, 2]), ("A", [1, 0, 0]))


def test_38_BALL_1_dung_va_do_ban_kinh_the_tich():
    kq = _chay(_spec(
        _CAU + [{"name": "cau", "type": "curved_solid"},
                {"name": "R", "type": "float"}, {"name": "V", "type": "float"}],
        [{"kind": "construct_curved_solid", "target_var": "cau",
          "curved_kind": "ball", "anchor": "I", "rim_point": "A",
          "label": "(S)"},
         _do("R", "radius", "cau"), _do("V", "volume", "cau")]))
    assert display(kq.final_memory["R"]) == "√3"
    assert display(kq.final_memory["V"]) == "4π√3"


def test_38_BALL_2_mat_phang_cat_cho_duong_tron_roi_do():
    kq = _chay(_spec(
        _diem(("I", [0, 0, 0]), ("A", [3, 0, 0]))
        + [{"name": "cau", "type": "curved_solid"},
           {"name": "mp", "type": "plane3", "initial_value": {
               "through": [[0, 0, 2], [1, 0, 2], [0, 1, 2]]}},
           {"name": "C", "type": "circle3"},
           {"name": "r", "type": "float"}, {"name": "S", "type": "float"}],
        [{"kind": "construct_curved_solid", "target_var": "cau",
          "curved_kind": "ball", "anchor": "I", "rim_point": "A"},
         {"kind": "assign", "target_var": "C",
          "expr": {"kind": "intersect_plane_curved", "solid": "cau",
                   "plane": "mp"}},
         _do("r", "radius", "C"), _do("S", "area", "C")]))
    assert isinstance(kq.final_memory["C"], Circle3)
    assert display(kq.final_memory["r"]) == "√5"
    assert display(kq.final_memory["S"]) == "5π"


def test_38_CYLINDER_1_the_tich_va_dien_tich_xung_quanh():
    kq = _chay(_spec(
        _TRU + [{"name": "tru", "type": "curved_solid"},
                {"name": "V", "type": "float"}, {"name": "Sxq", "type": "float"}],
        [{"kind": "construct_curved_solid", "target_var": "tru",
          "curved_kind": "cylinder", "anchor": "O", "apex_or_top": "Ot",
          "rim_point": "A"},
         _do("V", "volume", "tru"), _do("Sxq", "lateral_area", "tru")]))
    assert display(kq.final_memory["V"]) == "2π"
    assert display(kq.final_memory["Sxq"]) == "4π"


def test_38_CYLINDER_2_mat_phang_vuong_goc_truc_cho_duong_tron():
    """Mặt đáy dựng bằng `plane_perpendicular_to_line` — phép của G4, không
    phải phép mới của wave này."""
    kq = _chay(_spec(
        _TRU + [{"name": "tru", "type": "curved_solid"},
                {"name": "M", "type": "point3"},
                {"name": "truc", "type": "line3"},
                {"name": "mp", "type": "plane3"},
                {"name": "C", "type": "circle3"},
                {"name": "r", "type": "float"}],
        [{"kind": "construct_curved_solid", "target_var": "tru",
          "curved_kind": "cylinder", "anchor": "O", "apex_or_top": "Ot",
          "rim_point": "A"},
         {"kind": "construct_point", "target_var": "M",
          "expr": {"kind": "midpoint", "a": "O", "b": "Ot"}},
         {"kind": "construct_line", "target_var": "truc",
          "through_a": "O", "through_b": "Ot"},
         {"kind": "assign", "target_var": "mp",
          "expr": {"kind": "plane_perpendicular_to_line", "point": "M",
                   "line": "truc"}},
         {"kind": "assign", "target_var": "C",
          "expr": {"kind": "intersect_plane_curved", "solid": "tru",
                   "plane": "mp"}},
         _do("r", "radius", "C")]))
    assert kq.final_memory["r"] == 1


def test_38_CONE_1_duong_sinh_the_tich_dien_tich_xung_quanh():
    """⚠️ Đường sinh đo bằng `distance(S, A)` — **KHÔNG** có lượng đo `slant`,
    vì hai toán hạng đều là điểm CÓ TÊN. Đó là cổng hợp thành G4 áp ở đây."""
    kq = _chay(_spec(
        _NON + [{"name": "non", "type": "curved_solid"},
                {"name": "l", "type": "float"}, {"name": "V", "type": "float"},
                {"name": "Sxq", "type": "float"}],
        [{"kind": "construct_curved_solid", "target_var": "non",
          "curved_kind": "cone", "anchor": "O", "apex_or_top": "S",
          "rim_point": "A"},
         {"kind": "assign", "target_var": "l",
          "expr": {"kind": "measure", "quantity": "distance", "of": "S",
                   "wrt": "A"}},
         _do("V", "volume", "non"), _do("Sxq", "lateral_area", "non")]))
    assert display(kq.final_memory["l"]) == "√5"
    assert display(kq.final_memory["V"]) == "2π/3"
    assert display(kq.final_memory["Sxq"]) == "π√5"


def test_38_CONE_2_thiet_dien_qua_truc_KHONG_can_phep_dung_moi():
    """**Nhân chứng quan trọng nhất của §37.**

    Thiết diện qua trục là tam giác `S·A·B` với `B = 2O − A`. Ba phép dùng tới
    đều có TRƯỚC wave này: `divide_segment` (ratio `2`), `construct_polygon`,
    `measure area` (Phase 1). `NEW_PROBLEM_WITHIN_CURVED_IR_REQUIRES_CODE = NO`
    được chứng minh ở đây, bằng một chương trình chạy thật.

    Kiểm tay: đáy `AB = 2`, cao `SO = 2` ⇒ `S = 2`.
    """
    kq = _chay(_spec(
        _NON + [{"name": "non", "type": "curved_solid"},
                {"name": "B", "type": "point3"},
                {"name": "td", "type": "polygon3"},
                {"name": "Std", "type": "float"}],
        [{"kind": "construct_curved_solid", "target_var": "non",
          "curved_kind": "cone", "anchor": "O", "apex_or_top": "S",
          "rim_point": "A"},
         {"kind": "construct_point", "target_var": "B",
          "expr": {"kind": "divide_segment", "a": "A", "b": "O", "ratio": "2"}},
         {"kind": "construct_polygon", "target_var": "td",
          "vertices": ["S", "A", "B"], "label": "thiết diện qua trục"},
         _do("Std", "area", "td")]))
    B = kq.final_memory["B"]
    assert (B.x, B.y, B.z) == (-1, 0, 0), "điểm xuyên tâm đối"
    assert kq.final_memory["Std"] == 2


# ══ §39 · TRỤC KHÔNG SONG SONG TRỤC TOẠ ĐỘ ═══════════════════════════════
def test_39_truc_XIEN_di_het_duong_IR():
    """Chống việc cài đặt lặng lẽ giả định hình dựng đứng theo `z`."""
    kq = _chay(_spec(
        _diem(("O", [0, 0, 0]), ("Ot", [1, 2, 2]), ("A", [2, -1, 0]))
        + [{"name": "tru", "type": "curved_solid"},
           {"name": "V", "type": "float"}, {"name": "Sxq", "type": "float"},
           {"name": "R", "type": "float"}],
        [{"kind": "construct_curved_solid", "target_var": "tru",
          "curved_kind": "cylinder", "anchor": "O", "apex_or_top": "Ot",
          "rim_point": "A"},
         _do("V", "volume", "tru"), _do("Sxq", "lateral_area", "tru"),
         _do("R", "radius", "tru")]))
    assert display(kq.final_memory["V"]) == "15π"
    assert display(kq.final_memory["Sxq"]) == "6π√5"
    assert display(kq.final_memory["R"]) == "√5"


# ══ §7 + §40 · R0 ════════════════════════════════════════════════════════
def test_40_khoi_cong_KHONG_khai_duoc_bang_gia_thiet_mo_hinh():
    """`_KIEU_DUOC_GIA_THIET` là danh sách TRẮNG — hai kiểu cong không có tên
    trong đó, nên không có đường nào khai một mặt cầu bằng toạ độ."""
    from app.simulation.semantic_program.grounding_gate import (
        _KIEU_DUOC_GIA_THIET,
    )

    assert _KIEU_DUOC_GIA_THIET == frozenset({"point3", "vector3"})


def test_40b_khoi_cong_KHONG_co_o_nao_nhan_MOT_CON_SO():
    """R0 ở tầng LƯỢC ĐỒ, không ở tầng lời dặn: mọi toán hạng hình học của câu
    lệnh dựng khối cong đều là TÊN."""
    from app.simulation.semantic_program.contract import ConstructCurvedSolidStmt

    truong = ConstructCurvedSolidStmt.model_fields
    for t in ("anchor", "apex_or_top", "rim_point"):
        assert "str" in str(truong[t].annotation)
    for cam in ("radius", "height", "axis", "center"):
        assert cam not in truong, f"`{cam}` là một con số mô hình tự khai"


def test_40c_TIEM_rua_nang_luc__diem_BIA_de_gia_tam_mat_cau():
    """Lớp lỗi lịch sử `gm_10`, dựng lại nguyên hình.

    Mô hình bịa `P_doi_dien` với một `model_assumption` nghe hợp lý để lấy tâm
    mặt cầu. Cổng xuất xứ phải từ chối vì cái tên ấy **không có trong đề**.
    """
    raw = _spec(
        _diem(("A", [0, 0, 0]), ("B", [2, 0, 0]))
        + [{"name": "P_doi_dien", "type": "point3", "initial_value": [2, 2, 2],
            "model_assumption": "điểm đối diện A trong hình hộp bao quanh"},
           {"name": "I", "type": "point3"},
           {"name": "cau", "type": "curved_solid"}],
        [{"kind": "construct_point", "target_var": "I",
          "expr": {"kind": "midpoint", "a": "A", "b": "P_doi_dien"}},
         {"kind": "construct_curved_solid", "target_var": "cau",
          "curved_kind": "ball", "anchor": "I", "rim_point": "A"}])
    from app.simulation.semantic_program.request_contract import RequestContract

    spec = SemanticProgramSpec.model_validate(raw)
    hd = RequestContract(problem_text=(
        "Cho tứ diện ABCD. Tính bán kính mặt cầu ngoại tiếp tứ diện."))
    kq = check_grounding(hd, spec)
    assert not kq.ok, "điểm BỊA lọt qua cổng xuất xứ"
    assert any("P_doi_dien" in x for x in kq.unresolved), kq.unresolved


# ══ §8 · MẶT CẦU NGOẠI TIẾP — ĐƯỜNG HỢP LỆ, KHÔNG SPECIAL-CASE ═══════════
def test_08_tam_mat_cau_ngoai_tiep_DUNG_DUOC_bang_IR_hien_co():
    """Nửa còn lại của `test_40c`: sau khi cấm đường bịa, đường ĐÚNG phải tồn
    tại — nếu không thì ta chỉ vừa cấm một năng lực.

    Tâm mặt cầu ngoại tiếp = giao ba **mặt trung trực**, và mặt trung trực dựng
    được bằng `plane_perpendicular_to_line(midpoint, line)` — phép của G4, có
    trước wave này. Không primitive nào được thêm cho riêng bài toán này.

    Tứ diện vuông `A(0,0,0) B(2,0,0) C(0,2,0) D(0,0,2)` ⇒ tâm `(1,1,1)`,
    `R = √3`. Kiểm tay, và kiểm CẢ tính cách đều bốn đỉnh.
    """
    def mtt(P: str, Q: str, i: int) -> list[dict]:
        return [
            {"kind": "construct_point", "target_var": f"M{i}",
             "expr": {"kind": "midpoint", "a": P, "b": Q}},
            {"kind": "construct_line", "target_var": f"d{i}",
             "through_a": P, "through_b": Q},
            {"kind": "assign", "target_var": f"p{i}",
             "expr": {"kind": "plane_perpendicular_to_line",
                      "point": f"M{i}", "line": f"d{i}"}}]

    kq = _chay(_spec(
        _diem(("A", [0, 0, 0]), ("B", [2, 0, 0]), ("C", [0, 2, 0]),
              ("D", [0, 0, 2]))
        + [{"name": f"M{i}", "type": "point3"} for i in (1, 2, 3)]
        + [{"name": f"d{i}", "type": "line3"} for i in (1, 2, 3)]
        + [{"name": f"p{i}", "type": "plane3"} for i in (1, 2, 3)]
        + [{"name": "g", "type": "line3"}, {"name": "I", "type": "point3"},
           {"name": "cau", "type": "curved_solid"},
           {"name": "R", "type": "float"}, {"name": "V", "type": "float"}],
        [*mtt("A", "B", 1), *mtt("A", "C", 2), *mtt("A", "D", 3),
         {"kind": "assign", "target_var": "g",
          "expr": {"kind": "intersect_plane_plane", "plane_a": "p1",
                   "plane_b": "p2"}},
         {"kind": "construct_point", "target_var": "I",
          "expr": {"kind": "intersect_line_plane", "line": "g", "plane": "p3"}},
         {"kind": "construct_curved_solid", "target_var": "cau",
          "curved_kind": "ball", "anchor": "I", "rim_point": "A",
          "label": "(S) ngoại tiếp"},
         _do("R", "radius", "cau"), _do("V", "volume", "cau")]))

    I = kq.final_memory["I"]
    assert (I.x, I.y, I.z) == (1, 1, 1), "tâm do KERNEL tính, không do mô hình khai"
    assert display(kq.final_memory["R"]) == "√3"
    assert display(kq.final_memory["V"]) == "4π√3"
    # Cách đều BỐN đỉnh — tính chất định nghĩa của mặt cầu ngoại tiếp, kiểm
    # bằng kernel chứ không tin vào tên biến.
    from app.simulation.geometry.measure import distance_sq

    assert {distance_sq(I, kq.final_memory[t]) for t in "ABCD"} == {3}


# ══ §30–31 · VẾT VÀ VẬN CHUYỂN ═══════════════════════════════════════════
def test_30_mot_khoi_cong_la_MOT_buoc_vet():
    """Bất biến #31 (`frame k ⇔ trace[k]`) không đổi: không có gì liên tục đi
    vào dòng thời gian, không mesh animation, không hình học lấy mẫu."""
    kq = _chay(_spec(
        _CAU + [{"name": "cau", "type": "curved_solid"}],
        [{"kind": "construct_curved_solid", "target_var": "cau",
          "curved_kind": "ball", "anchor": "I", "rim_point": "A"}]))
    buoc = [t for t in kq.trace if t.target == "cau"]
    assert len(buoc) == 1
    assert buoc[0].action == "construct_curved_solid"
    assert buoc[0].tier1_narration


def test_31_canh_cho_THAM_SO_khong_cho_LUOI():
    """`CURVED_SCENE_HAS_VERTICES = NO` · `CURVED_SCENE_HAS_FACES = NO`.

    Đây là bảo đảm CẤU TRÚC, không phải lời dặn: không có ô nào để một đỉnh
    nội suy đi ngược lên checker hay phép đo.
    """
    canh = _canh(_spec(
        _TRU + [{"name": "tru", "type": "curved_solid"},
                {"name": "mp", "type": "plane3", "initial_value": {
                    "through": [[0, 0, 1], [1, 0, 1], [0, 1, 1]]}},
                {"name": "C", "type": "circle3"}],
        [{"kind": "construct_curved_solid", "target_var": "tru",
          "curved_kind": "cylinder", "anchor": "O", "apex_or_top": "Ot",
          "rim_point": "A", "label": "hình trụ"},
         {"kind": "assign", "target_var": "C",
          "expr": {"kind": "intersect_plane_curved", "solid": "tru",
                   "plane": "mp"}}]))
    vat = {o["id"]: o for o in canh["objects"]}
    for ten in ("tru", "C"):
        assert "vertices" not in vat[ten] and "faces" not in vat[ten]
    assert vat["tru"]["curved_kind"] == "cylinder"
    assert vat["tru"]["anchor"] and vat["tru"]["rim_point"]
    assert vat["C"]["center"] and vat["C"]["radius_sq"] == "1"


# ══ §27 · TÊN HIỂN THỊ DO BACKEND SỞ HỮU ═════════════════════════════════
def test_27_ten_hien_thi_do_BACKEND_dat_khong_phai_id():
    canh = _canh(_spec(
        _NON + [{"name": "non", "type": "curved_solid"},
                {"name": "Sxq", "type": "float"}],
        [{"kind": "construct_curved_solid", "target_var": "non",
          "curved_kind": "cone", "anchor": "O", "apex_or_top": "S",
          "rim_point": "A"},
         _do("Sxq", "lateral_area", "non")]))
    vat = {o["id"]: o for o in canh["objects"]}
    assert vat["non"]["label"] != "non", "nhãn rơi về `id`"
    assert "nón" in vat["non"]["label"].lower(), vat["non"]["label"]
    assert vat["non"]["role"] and vat["non"]["type"] == "curved_solid"
    assert "iện tích" in vat["Sxq"]["label"], vat["Sxq"]["label"]


@pytest.mark.parametrize("loai,tu", [("ball", "cầu"), ("cylinder", "trụ"),
                                     ("cone", "nón")])
def test_27b_moi_hinh_co_danh_tu_rieng__DAN_TU_bang_loai(loai, tu):
    """Danh từ dẫn từ `KHOI_CONG`, không từ một bảng thứ hai ở tầng trình bày."""
    assert tu in KHOI_CONG[loai].danh_tu.lower()


# ══ §29 + §45 · NĂNG LỰC HỆ ≠ NĂNG LỰC SẢN PHẨM ══════════════════════════
def test_29_prompt_VAN_tu_choi_hinh_cong__san_pham_chua_mo():
    """`CURVED_PRODUCT_ENABLED = NO`.

    Phase 2 dựng **năng lực hệ**, không tuyên **năng lực sản phẩm**. Lời từ
    chối trong prompt giữ nguyên cho tới khi Phase 3 đo được rằng mô hình dùng
    đúng từ vựng mới. Gỡ nó sớm là hứa một thứ chưa ai kiểm.

    ⚠️ Hệ quả phải khai, không giấu: thẻ văn phạm nay DẠY `construct_curved_
    solid` trong khi prompt vẫn BẢO từ chối — hai câu mâu thuẫn cùng gửi cho
    mô hình. Đó là trạng thái Phase 2 cố ý dừng lại ở, và là việc đầu tiên
    Phase 3 phải dọn.
    """
    from pathlib import Path

    from app.ai import gemini

    md = (Path(gemini.SKILLS_DIR) / "geometry_program_generator.md").read_text(
        encoding="utf-8")
    assert "không diễn đạt" in md and "mặt cầu" in md, (
        "lời từ chối hình cong đã bị gỡ — đó là việc của Phase 3")


def test_45_khong_bai_mau_nao_dung_hinh_cong():
    """Nút trên giao diện chỉ được hiện khi có đường hợp lệ qua CẢ BẢY tầng.

    Bài mẫu là bề mặt sản phẩm; thêm một bài cong ở đây là bật năng lực với
    người dùng trước khi Phase 3 đo.
    """
    import json
    from pathlib import Path

    goc = Path(__file__).resolve().parents[3]
    js = (goc / "frontend/src/data/geometry-samples.json").read_text(
        encoding="utf-8")
    assert "curved_solid" not in js and "circle3" not in js
    assert json.loads(js), "bài mẫu rỗng — kiểm lại đường dẫn"
