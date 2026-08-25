# -*- coding: utf-8 -*-
"""MÀN HÌNH CÓ HAI NỬA — cổng bề mặt học sinh phải đọc cả hai. **0 API call.**

─── SỰ CỐ ─────────────────────────────────────────────────────────────────

Đề hình chóp dán vào sản phẩm nhận **"NGOÀI DANH MỤC MÔ PHỎNG"** sau ~7 lượt
LLM. Định tuyến miền đã đúng, IR dựng được, oracle khớp — nhưng
`check_learner_surface` chỉ biết một nửa màn hình:

    visual_bindings   nửa 2D — ngăn xếp, mảng, ô kết quả. Phải KHAI.
    Scene3D           nửa 3D — điểm, đường, mặt, khối. Chiếu TẤT ĐỊNH.

Chương trình hình học không khai binding nào, và nó **đúng** khi không khai. Cổng
đọc sót nửa kia nên từ chối **mọi** chương trình hình học — kể cả bốn bài đã qua
oracle độc lập ở Wave 4. `executable=True` mà `servable=False` ⇒ envelope rơi
xuống classifier ⇒ "ngoài danh mục".

─── THỨ FILE NÀY PHẢI KHOÁ ────────────────────────────────────────────────

Cổng nay TIN rằng "giá trị hình học ⇒ có trên hình". Niềm tin ấy đúng **chỉ vì**
`build_scene` chiếu đúng những giá trị ấy và `RENDER_HINT` vẽ đúng những loại
ấy. Ba thứ đó ở ba module không được biết tới nhau, nên nếu không ai khoá thì
chúng sẽ trôi khỏi nhau đúng vào ngày thêm một kiểu hình học mới — và khi ấy cổng
NÓI DỐI: bảo có trên hình, cảnh thì không vẽ. Một cổng nói dối tệ hơn không cổng.
"""
from __future__ import annotations

import ast
from fractions import Fraction
from pathlib import Path

import pytest

from app.simulation.geometry import Line3, Plane3, Vec3
from app.simulation.geometry.section import Polyhedron
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.geometry_exec import (
    KIEU_DAI_LUONG,
    la_dai_luong_do,
    la_doi_tuong_hinh_hoc,
)
from app.simulation.semantic_program.learner_surface import _tren_canh_3d
from app.simulation.semantic_program.scene3d import RENDER_HINT
from app.simulation.semantic_program.simulation_state import build_scene

GOC = Path(__file__).resolve().parents[3]

_A, _B, _C, _D = (Vec3(0, 0, 0), Vec3(1, 0, 0), Vec3(1, 1, 0), Vec3(0, 0, 1))

#: Một đại diện cho MỖI lớp giá trị mà vị từ chấp nhận.
GIA_TRI_HINH_HOC: dict[str, object] = {
    "point3": _A,
    "line3": Line3(point=_A, direction=Vec3(1, 0, 0)),
    "plane3": Plane3(point=_A, normal=Vec3(0, 0, 1)),
    "solid": Polyhedron(vertices=(_A, _B, _C, _D),
                        faces=((0, 1, 2), (0, 1, 3), (1, 2, 3), (0, 2, 3))),
    "polygon3": (_A, _B, _C),
}


def _spec(ten: str, kieu: str) -> SemanticProgramSpec:
    return SemanticProgramSpec.model_validate({
        "title": "khoá vị từ",
        "memory_declarations": [{"name": ten, "type": kieu}],
        "statements": [],
    })


# ══ LỜI HỨA CỦA CỔNG PHẢI ĐƯỢC CẢNH GIỮ ══════════════════════════════════
@pytest.mark.parametrize("kieu,gt", sorted(GIA_TRI_HINH_HOC.items()))
def test_moi_gia_tri_vi_tu_NHAN_deu_duoc_canh_VE(kieu, gt):
    """Vị từ nói "có trên hình" ⇒ `build_scene` phải thật sự sinh ra một đối
    tượng, và `RENDER_HINT` phải biết vẽ loại đó."""
    assert la_doi_tuong_hinh_hoc(gt), kieu
    objs = build_scene(_spec("x", kieu), {"x": gt})["objects"]
    assert len(objs) == 1, f"{kieu}: cảnh KHÔNG vẽ thứ cổng bảo là có trên hình"
    assert objs[0]["type"] in RENDER_HINT, objs[0]["type"]


@pytest.mark.parametrize("kieu", KIEU_DAI_LUONG)
def test_dai_luong_do_duoc_hien_thanh_readout(kieu):
    """Đại lượng đo không vẽ được, nhưng phải HIỆN — nó là đáp án của bài."""
    gt = Fraction(2, 3)
    assert la_dai_luong_do(gt, kieu)
    objs = build_scene(_spec("V", kieu), {"V": gt})["objects"]
    assert [o["type"] for o in objs] == ["quantity"]
    assert RENDER_HINT["quantity"] == "readout"


def test_moi_kieu_HINH_HOC_deu_co_o_trong_RENDER_HINT():
    """Thêm một `MemoryType` hình học mà quên mở `RENDER_HINT` thì cổng sẽ bảo
    "có trên hình" cho một thứ không ai vẽ. Bắt ở đây, lúc còn sửa được."""
    from app.simulation.semantic_program.geometry_exec import GEOMETRY_TYPES

    thieu = sorted(GEOMETRY_TYPES - set(RENDER_HINT) - {"vector3"})
    assert not thieu, f"kiểu hình học không có cách vẽ: {thieu}"


# ══ CHƯA DỰNG XONG THÌ CHƯA CÓ TRÊN HÌNH ═════════════════════════════════
def test_bien_hinh_hoc_chua_dung_KHONG_duoc_tinh_la_da_hien():
    """Đối tượng khai mà câu lệnh chưa chạy tới mang `None` trong bộ nhớ, và nó
    **không** có trên hình thật. Cổng phải thấy đúng như vậy — suy từ KIỂU KHAI
    thay vì từ giá trị là tự cho mình một lời hứa không ai giữ."""
    spec = _spec("P", "point3")
    ket = type("K", (), {"final_memory": {"P": None}})()
    assert _tren_canh_3d(spec, ket) == set()
    assert build_scene(spec, {"P": None})["objects"] == []


# ══ MIỀN TIN HỌC KHÔNG ĐƯỢC ĐỔI MỘT BIT ══════════════════════════════════
def test_chuong_trinh_TIN_HOC_khong_co_gi_tren_canh_3D():
    """Nửa 3D rỗng cho miền Tin học ⇒ cổng vẫn chặn ngăn xếp không có binding,
    đúng như sự cố vNext mà nó sinh ra để chặn."""
    spec = SemanticProgramSpec.model_validate({
        "title": "khoá miền Tin học",
        "memory_declarations": [
            {"name": "st", "type": "stack", "initial_value": []},
            {"name": "n", "type": "int", "initial_value": 3},
        ],
        "statements": [],
    })
    ket = type("K", (), {"final_memory": {"st": ["("], "n": 3}})()
    assert _tren_canh_3d(spec, ket) == set()


def test_so_thuong_KHONG_phai_dai_luong_do():
    """`la_dai_luong_do` đòi `Fraction`. Một `int` đếm vòng lặp không được lẻn
    lên hình chỉ vì nó khai kiểu `int`."""
    assert not la_dai_luong_do(3, "int")
    assert not la_dai_luong_do(3.5, "float")
    assert not la_dai_luong_do(Fraction(1, 2), "array")


def test_tuple_rong_va_tuple_khong_phai_diem_deu_BI_TU_CHOI():
    assert not la_doi_tuong_hinh_hoc(())
    assert not la_doi_tuong_hinh_hoc((1, 2, 3))
    assert not la_doi_tuong_hinh_hoc((_A, "x"))


# ══ RANH GIỚI PHỤ THUỘC KHÔNG ĐƯỢC ĐẢO ═══════════════════════════════════
def test_learner_surface_KHONG_nhap_tang_trinh_bay():
    """Cổng không được biết tới tầng mô phỏng — nếu không, một thay đổi thẩm mỹ
    sẽ đụng vào thứ đang gác cửa. Vị từ dùng chung nằm ở tầng KERNEL, và đó là
    lý do nó ở `geometry_exec` chứ không ở `simulation_state`."""
    f = (GOC / "backend" / "app" / "simulation" / "semantic_program"
         / "learner_surface.py")
    cay = ast.parse(f.read_text(encoding="utf-8"))
    nhap = [n.module for n in ast.walk(cay)
            if isinstance(n, ast.ImportFrom) and n.module]
    xau = [m for m in nhap if "simulation_state" in m or "scene3d" in m]
    assert not xau, f"cổng nhập tầng trình bày: {xau}"


def test_CHI_MOT_nguon_su_that_cho_phep_phan_loai():
    """`build_scene` phải DÙNG vị từ chung, không tự viết lại chuỗi `isinstance`.

    Hai bản song song sẽ trôi khỏi nhau, và khi ấy cổng nói dối mà không ai đỏ.
    """
    f = (GOC / "backend" / "app" / "simulation" / "semantic_program"
         / "simulation_state.py")
    src = f.read_text(encoding="utf-8")
    assert "la_doi_tuong_hinh_hoc" in src and "la_dai_luong_do" in src
    assert 'isinstance(gt, Fraction) and kieu.get' not in src
