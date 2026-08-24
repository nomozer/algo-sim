# -*- coding: utf-8 -*-
"""Oracle hình học ĐỘC LẬP — và độc lập phải CHỨNG MINH được. **0 API call.**

Ba mức, tăng dần độ thuyết phục, và chỉ mức 3 mới là bằng chứng thật:

    1. oracle không import mã sản phẩm      — kiểm bằng mắt, đọc mã nguồn
    2. oracle KHỚP kernel trên bài kiểm tay — cần, nhưng CHƯA đủ
    3. TIÊM LỖI vào kernel ⇒ oracle BẮT ĐƯỢC — đây mới là bằng chứng

Mức 2 một mình không chứng minh gì: hai bản cài cùng một thuật toán, cùng một
lỗi, sẽ khớp nhau hoàn hảo và cùng sai. Mức 3 hỏi đúng câu cần hỏi — *khi
kernel sai, oracle có nói được không?*
"""
from __future__ import annotations

import importlib.util
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.simulation.geometry import Plane3, Vec3
from app.simulation.geometry import measure as M
from app.simulation.geometry import section as SEC

_ORACLE = (Path(__file__).resolve().parents[3] / "docs" / "evaluation" /
           "geometry" / "custodian" / "geometry_oracle.py")


@pytest.fixture(scope="module")
def O():
    spec = importlib.util.spec_from_file_location("geometry_oracle", _ORACLE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["geometry_oracle"] = mod
    spec.loader.exec_module(mod)
    return mod


def _day(v: Vec3):
    """Kiểu sản phẩm → dạng DÂY. Không có đường nào cho hai bên chung kiểu."""
    return (v.x, v.y, v.z)


def _khoi_day(sol):
    return [_day(v) for v in sol.vertices], [list(f) for f in sol.faces]


HOP = SEC.box(1, 1, 1)
CHOP = SEC.pyramid_square(1, 2)


# ── MỨC 1: độc lập kiểm được BẰNG MẮT ─────────────────────────────────────
#: Chỉ ba module chuẩn được phép. Danh sách ĐÓNG — thêm một cái là phải giải
#: thích vì sao oracle cần nó.
_CHO_PHEP = {"fractions", "typing", "__future__"}


def test_oracle_KHONG_import_ma_san_pham():
    """Điều kiện tiên quyết. Import kernel là oracle đang kiểm chính cái nó
    vừa dựng ra — cùng luật `sealed_ground_truth.py` của miền Tin học.

    Soi bằng `ast`, KHÔNG quét chuỗi: bản đầu của test này quét chuỗi và đỏ
    ngay vì chính DOCSTRING nhắc tên module bị cấm để giải thích điều cấm.
    Quét chuỗi cũng bỏ sót được `importlib.import_module("app...")`, nên nó
    vừa bắt oan vừa bỏ sót.
    """
    import ast

    cay = ast.parse(_ORACLE.read_text(encoding="utf-8"))
    goc: list[str] = []
    for nut in ast.walk(cay):
        if isinstance(nut, ast.Import):
            goc += [a.name.split(".")[0] for a in nut.names]
        elif isinstance(nut, ast.ImportFrom) and nut.module:
            goc.append(nut.module.split(".")[0])
    la = sorted(set(goc) - _CHO_PHEP)
    assert not la, f"oracle import ngoài thư viện chuẩn: {la}"


def test_oracle_KHONG_goi_import_dong():
    """`importlib.import_module("app…")` lách được mọi phép soi import tĩnh."""
    import ast

    cay = ast.parse(_ORACLE.read_text(encoding="utf-8"))
    for nut in ast.walk(cay):
        if isinstance(nut, ast.Call) and isinstance(nut.func, ast.Name):
            assert nut.func.id not in ("__import__", "exec", "eval"), \
                f"oracle dùng {nut.func.id}() — có thể nạp mã sản phẩm lúc chạy"


# ── MỨC 2: khớp trên bài kiểm tay (CẦN, chưa ĐỦ) ──────────────────────────
def test_the_tich_chop_khop_giua_hai_phep_phan_ra(O):
    """Kernel chia quạt từ ĐỈNH CHÓP; oracle chia tứ diện từ MỘT ĐIỂM TRONG
    tới mọi tam giác của mọi mặt. Hai đường khác nhau, kiểm tay `V = 2/3`."""
    v_kernel = M.volume_pyramid_fan(CHOP.vertices[4], list(CHOP.vertices[:4]))
    dinh, mat = _khoi_day(CHOP)
    v_oracle = O.volume_from_interior_point(dinh, mat)
    assert v_kernel == v_oracle == F(2, 3)


def test_the_tich_hop_khop(O):
    dinh, mat = _khoi_day(HOP)
    assert O.volume_from_interior_point(dinh, mat) == 1


def test_khoang_cach_khop(O):
    day = Plane3.through(*CHOP.vertices[:3])
    S = CHOP.vertices[4]
    assert M.distance_sq_point_plane(S, day) == \
        O.distance_sq_point_plane(_day(S), (_day(day.point), _day(day.normal))) == 4


def test_thiet_dien_dung_thi_oracle_KHONG_bao_loi(O):
    mp = Plane3(Vec3.of(0, 0, F(1, 2)), Vec3.of(0, 0, 1))
    s = SEC.cross_section(HOP, mp)
    dinh, mat = _khoi_day(HOP)
    loi = O.verify_section(dinh, mat, (_day(mp.point), _day(mp.normal)),
                           [_day(p) for p in s.polygon])
    assert loi == [], loi


# ── MỨC 3: TIÊM LỖI — bằng chứng thật của tính độc lập ────────────────────
def test_oracle_BAT_DUOC_dinh_bi_day_lech_khoi_mat_phang(O):
    """Lỗi hay gặp nhất: nội suy sai tham số `t` ⇒ đỉnh trượt khỏi mặt cắt."""
    mp = Plane3(Vec3.of(0, 0, F(1, 2)), Vec3.of(0, 0, 1))
    s = SEC.cross_section(HOP, mp)
    hong = [_day(p) for p in s.polygon]
    hong[0] = (hong[0][0], hong[0][1], hong[0][2] + F(1, 100))  # lệch 0.01
    dinh, mat = _khoi_day(HOP)
    loi = O.verify_section(dinh, mat, (_day(mp.point), _day(mp.normal)), hong)
    assert any("KHÔNG thuộc mặt phẳng cắt" in x for x in loi), loi


def test_oracle_BAT_DUOC_dinh_nam_NGOAI_khoi(O):
    """Kéo dài giao tuyến quá biên mặt — bug kinh điển khi dựng thiết diện."""
    mp = Plane3(Vec3.of(0, 0, F(1, 2)), Vec3.of(0, 0, 1))
    s = SEC.cross_section(HOP, mp)
    hong = [_day(p) for p in s.polygon]
    hong[1] = (F(5), hong[1][1], F(1, 2))       # vẫn thuộc mp, nhưng ngoài khối
    dinh, mat = _khoi_day(HOP)
    loi = O.verify_section(dinh, mat, (_day(mp.point), _day(mp.normal)), hong)
    assert any("không nằm trên mặt nào" in x for x in loi), loi


def test_oracle_BAT_DUOC_thu_tu_dinh_bi_dao(O):
    """Sắp sai thứ tự ⇒ cạnh thành dây cung XUYÊN QUA khối. Trên ảnh tĩnh nhìn
    vẫn ra một tứ giác — đây là loại lỗi mắt thường bỏ sót."""
    mp = Plane3(Vec3.of(0, 0, F(1, 2)), Vec3.of(0, 0, 1))
    s = SEC.cross_section(HOP, mp)
    p = [_day(x) for x in s.polygon]
    dinh, mat = _khoi_day(HOP)
    loi = O.verify_section(dinh, mat, (_day(mp.point), _day(mp.normal)),
                           [p[0], p[2], p[1], p[3]])   # hoán vị chéo
    assert any("xuyên qua khối" in x for x in loi), loi


def test_oracle_BAT_DUOC_thiet_dien_thieu_dinh(O):
    mp = Plane3(Vec3.of(0, 0, F(1, 2)), Vec3.of(0, 0, 1))
    s = SEC.cross_section(HOP, mp)
    p = [_day(x) for x in s.polygon]
    dinh, mat = _khoi_day(HOP)
    loi = O.verify_section(dinh, mat, (_day(mp.point), _day(mp.normal)),
                           [p[0], p[1]])
    assert loi and "cần ≥3" in loi[0]


def test_oracle_BAT_DUOC_the_tich_sai_khi_kernel_bi_pha(O, monkeypatch):
    """Tiêm thẳng vào kernel: chia 5 thay vì chia 6 trong công thức tứ diện.

    Sai số 20 % — đủ nhỏ để một mô phỏng vẫn *trông* hợp lý, đủ lớn để đáp án
    sai. Nếu oracle dùng chung công thức thì nó cũng sai y hệt và test này xanh
    oan; nó đỏ nghĩa là hai bên thật sự tính khác nhau.
    """
    goc = M.volume_tetrahedron
    monkeypatch.setattr(M, "volume_tetrahedron",
                        lambda a, b, c, d: goc(a, b, c, d) * 6 / 5)
    v_kernel = M.volume_pyramid_fan(CHOP.vertices[4], list(CHOP.vertices[:4]))
    dinh, mat = _khoi_day(CHOP)
    assert v_kernel != O.volume_from_interior_point(dinh, mat)


# ── Ranh giới: oracle KHÔNG được bắt oan ──────────────────────────────────
def test_oracle_KHONG_bao_loi_voi_thiet_dien_tam_giac_hop_le(O):
    """Bắt oan cũng tệ ngang bỏ sót — nó tạo ra `false rejection` ở chỗ khó cãi."""
    mp = Plane3.through(Vec3.of(1, 0, 0), Vec3.of(0, 1, 0), Vec3.of(0, 0, 1))
    s = SEC.cross_section(HOP, mp)
    dinh, mat = _khoi_day(HOP)
    loi = O.verify_section(dinh, mat, (_day(mp.point), _day(mp.normal)),
                           [_day(p) for p in s.polygon])
    assert loi == [], loi


def test_oracle_KHONG_bao_loi_voi_thiet_dien_chop(O):
    mp = Plane3(Vec3.of(0, 0, 1), Vec3.of(0, 0, 1))
    s = SEC.cross_section(CHOP, mp)
    dinh, mat = _khoi_day(CHOP)
    loi = O.verify_section(dinh, mat, (_day(mp.point), _day(mp.normal)),
                           [_day(p) for p in s.polygon])
    assert loi == [], loi
