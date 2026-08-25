# -*- coding: utf-8 -*-
"""PHASE 5F — Scene3D vào luồng mô phỏng chính. **0 API call.**

    Semantic Program → Interpreter → SimulationState → Scene3D → Playback UI

Điều bộ test này khoá, và nó là luận điểm của đề tài chứ không phải một chi tiết
kĩ thuật:

    **Chương trình không qua thẩm định thì KHÔNG CÓ HÌNH.**

Nếu nới chỗ ấy, renderer sẽ bày ra thứ chưa ai kiểm — và hệ tụt xuống thành một
bộ vẽ hình có thêm một con AI ở đầu vào.
"""
from __future__ import annotations

import json

import pytest

from app.ai.pipeline import _dung_scene3d, _envelope_tu_route_sinh
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.route import verify_and_compile


def _ct_hinh_hoc() -> dict:
    """Chóp S.ABCD cạnh 1, SA ⊥ đáy, SA = 2 — dựng khối rồi đo thể tích."""
    diem = {"A": [0, 0, 0], "B": [1, 0, 0], "C": [1, 1, 0],
            "D": [0, 1, 0], "S": [0, 0, 2]}
    return {
        "spec_version": "1.0",
        "title": "Thể tích khối chóp S.ABCD",
        "memory_declarations": [
            {"name": n, "type": "point3", "initial_value": v,
             "model_assumption": "hệ trục đã chọn"} for n, v in diem.items()
        ] + [
            {"name": "M", "type": "point3"},
            {"name": "chop", "type": "solid"},
            {"name": "V", "type": "float"},
        ],
        "statements": [
            {"kind": "construct_point", "target_var": "M", "label": "M",
             "expr": {"kind": "midpoint", "a": "A", "b": "B"}},
            {"kind": "construct_solid", "target_var": "chop",
             "vertices": ["A", "B", "C", "D", "S"],
             "faces": [["A", "B", "C", "D"], ["A", "B", "S"], ["B", "C", "S"],
                       ["C", "D", "S"], ["D", "A", "S"]], "label": "S.ABCD"},
            {"kind": "assign", "target_var": "V",
             "expr": {"kind": "measure", "quantity": "volume", "of": "chop"}},
        ],
        "visual_bindings": {
            "value_boxes": [{"box_id": "kq", "var_ref": "V",
                             "label": "Thể tích"}]
        },
    }


def _spec() -> SemanticProgramSpec:
    return SemanticProgramSpec.model_validate(_ct_hinh_hoc())


# ══ TASK 1 — Scene3D sinh từ KẾT QUẢ THẬT, không dựng tay ════════════════
def test_scene3d_sinh_tu_chuong_trinh_that():
    sc = _dung_scene3d(_spec())
    assert sc is not None
    assert {o["id"] for o in sc["objects"]} == {
        "A", "B", "C", "D", "S", "M", "chop", "V"}


def test_CUNG_chuong_trinh_cho_CUNG_scene3d():
    """Tất định: cùng đầu vào, cùng đầu ra, byte-đối-byte. Không có gì phụ
    thuộc thứ tự gọi, thời gian, hay trạng thái còn sót."""
    a = json.dumps(_dung_scene3d(_spec()), sort_keys=True, ensure_ascii=False)
    b = json.dumps(_dung_scene3d(_spec()), sort_keys=True, ensure_ascii=False)
    assert a == b


def test_bai_TIN_HOC_khong_co_scene3d():
    """Cảnh rỗng ⇒ `None`, không phải `{"objects": []}`. Một khung 3D trống
    không nói được gì, và bày nó ra là mời người học đi tìm thứ không có."""
    spec = SemanticProgramSpec.model_validate({
        "spec_version": "1.0", "title": "Tìm số lớn nhất",
        "memory_declarations": [
            {"name": "day", "type": "array", "initial_value": [3, 1, 2]},
            {"name": "max_val", "type": "int", "initial_value": 0},
        ],
        "statements": [{"kind": "assign", "target_var": "max_val",
                        "expr": {"kind": "index", "container": "day",
                                 "index": {"kind": "literal", "value": 0}}}],
        "visual_bindings": {},
    })
    assert _dung_scene3d(spec) is None


def test_loi_o_TANG_CANH_khong_giet_ket_qua_da_kiem_chung():
    """Mất hình còn hơn mất cả một chương trình đã qua mọi cổng."""

    class Hong:
        statements: list = []

        def __getattr__(self, _):
            raise RuntimeError("vỡ ở tầng trình bày")

    assert _dung_scene3d(Hong()) is None


# ══ TASK 3 — PROVENANCE: mỗi đối tượng truy ngược được ═══════════════════
def test_moi_doi_tuong_DAN_XUAT_truy_nguoc_ve_cau_lenh():
    """Không đối tượng nào chỉ có `id` + `xyz` + `render` — như vậy là đồ hoạ
    thuần, và đề tài mất đúng đóng góp của nó."""
    sc = _dung_scene3d(_spec())
    theo_id = {o["id"]: o for o in sc["objects"]}

    assert theo_id["M"]["producer"] == "construct_point.midpoint"
    assert theo_id["M"]["depends"] == ["A", "B"]
    assert theo_id["chop"]["producer"] == "construct_solid"
    assert theo_id["chop"]["depends"] == ["A", "B", "C", "D", "S"]
    assert theo_id["V"]["producer"] == "measure.volume"
    assert theo_id["V"]["depends"] == ["chop"]


def test_producer_KHOP_voi_cau_lenh_that_trong_chuong_trinh():
    """Provenance phải khớp IR, không phải một nhãn đẹp gắn thêm."""
    spec = _spec()
    kind_theo_target = {
        s.target_var: s.kind for s in spec.statements
        if getattr(s, "target_var", None)
    }
    for o in _dung_scene3d(spec)["objects"]:
        if o["origin"] != "derived":
            continue
        assert o["producer"], o["id"]
        # `construct_point.midpoint` / `measure.volume` — phần TRƯỚC dấu chấm
        # là loại câu lệnh thật.
        goc = o["producer"].split(".")[0]
        that = kind_theo_target[o["id"]]
        assert goc == that or (goc == "measure" and that == "assign"), o


def test_free_object_KHONG_co_producer():
    sc = _dung_scene3d(_spec())
    for o in sc["objects"]:
        if o["origin"] == "free":
            assert o["producer"] is None and o["depends"] == []
    assert sorted(sc["free_objects"]) == ["A", "B", "C", "D", "S"]


# ══ TASK 4 — TOÀN PIPELINE ══════════════════════════════════════════════
def test_pipeline_TRON_VEN_sinh_du_nam_thanh_phan():
    from test_geometry_wave2 import _hop_dong_geo_09

    spec = _spec()
    kq = verify_and_compile(_hop_dong_geo_09(), spec)
    assert kq.executable, f"{kq.stage_reached}: {kq.details}"

    sc = _dung_scene3d(spec)
    assert sc["free_objects"], "thiếu free object"
    assert [o for o in sc["objects"] if o["origin"] == "derived"], "thiếu derived"
    assert all("depends" in o for o in sc["objects"]), "thiếu dependency"
    assert sc["events"], "thiếu events"
    assert all(e["explanation"] for e in sc["events"]), "thiếu narration"


def test_envelope_MANG_scene3d_va_KHONG_thay_duong_2D():
    from test_geometry_wave2 import _hop_dong_geo_09

    spec = _spec()
    kq = verify_and_compile(_hop_dong_geo_09(), spec)
    kq = kq.model_copy(update={"scene3d": _dung_scene3d(spec)})
    env = _envelope_tu_route_sinh(kq, {"a": 1}, {"p": 2}, None)

    assert env["scene3d"]["objects"], "envelope không mang cảnh"
    # Đường 2D cũ NGUYÊN VẸN — thêm một khoá, không thay khoá nào.
    assert env["source"] == "semantic_program"
    assert env["analysis"] == {"a": 1} and env["representation_plan"] == {"p": 2}


def test_envelope_TIN_HOC_khong_co_khoa_scene3d():
    class Gia:
        envelope = {"simulation_id": "algorithm.bubble_sort", "config": {}}
        scene3d = None

    env = _envelope_tu_route_sinh(Gia(), {}, {}, None)
    assert "scene3d" not in env


# ══ CHƯƠNG TRÌNH TRƯỢT THẨM ĐỊNH ⇒ KHÔNG CÓ HÌNH ════════════════════════
@pytest.mark.parametrize("pha,sua", [
    ("grounding", lambda ct: ct["memory_declarations"].__setitem__(
        0, {"name": "A", "type": "point3", "initial_value": [9, 9, 9],
            "source_fact_id": "khong_ton_tai"})),
    ("coverage", lambda ct: ct["statements"].pop()),  # bỏ phép đo ⇒ mất witness
])
def test_khong_qua_tham_dinh_thi_KHONG_dung_canh(pha, sua):
    """Luận điểm của đề tài, viết thành test.

    Renderer chỉ được bày thứ đã qua **mọi** cổng. Nới chỗ này thì hệ tụt xuống
    thành một bộ vẽ hình có thêm một con AI ở đầu vào — và toàn bộ chuỗi kiểm
    chứng phía trước trở thành trang trí.
    """
    from test_geometry_wave2 import _hop_dong_geo_09

    ct = _ct_hinh_hoc()
    sua(ct)
    spec = SemanticProgramSpec.model_validate(ct)
    kq = verify_and_compile(_hop_dong_geo_09(), spec)

    assert not kq.executable, f"{pha}: lẽ ra phải trượt"
    # Đường ghép ở `pipeline` chỉ dựng cảnh khi `executable`.
    assert kq.scene3d is None


def test_o_TRONG_scene3d_KHONG_do_route_dien():
    """`route.py` khai một Ô TRỐNG và KHÔNG import `scene3d` — hướng phụ thuộc
    một chiều được giữ bằng cách người GỌI đổ vào, không phải bằng cách nới
    ranh giới."""
    import ast
    from pathlib import Path

    p = (Path(__file__).resolve().parents[2] / "app" / "simulation"
         / "semantic_program" / "route.py")
    cay = ast.parse(p.read_text(encoding="utf-8"))
    nhap = [n.module for n in ast.walk(cay)
            if isinstance(n, ast.ImportFrom) and n.module]
    assert not any("scene3d" in m for m in nhap)

    from test_geometry_wave2 import _hop_dong_geo_09

    assert verify_and_compile(_hop_dong_geo_09(), _spec()).scene3d is None
