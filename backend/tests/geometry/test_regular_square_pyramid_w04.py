# -*- coding: utf-8 -*-
"""regular-square-pyramid-w04 · yêu cầu 4 — đoạn nằm TRÊN một cạnh khối có sẵn không được vẽ nét thứ hai. 0 lượt gọi.

Tái hiện (ca đối chứng của run, `diagnostics/sm_overlap/`): "Gọi M là trung điểm của SA. Tính độ dài đoạn SM." Bước
bổ sung W3 dựng `doan_SM` (đầu mút S, M ≠ hai đầu cạnh), nên `_attach_topology` — vốn chỉ so TÊN hai đầu mút — không
gắn nó với cạnh S-A; frontend vẽ nét riêng của SM đè lên SA (trình duyệt tại f3db0f6f: nét liền trên khúc S–M của
cạnh SA đang nét đứt).

Sửa ở thẩm quyền topology của cảnh: đoạn mà hai đầu mút nằm TRÊN cạnh khối (kiểm chính xác trên toạ độ hữu tỉ) trỏ
về cạnh ấy (`boundary_edge_ids`) kèm khoảng tham số trên cạnh (`edge_span`); cạnh chuẩn vẫn là owner nét duy nhất.
"""
from __future__ import annotations

import copy

from app.simulation.semantic_program.scene3d import _attach_topology
from tests.geometry import test_construction_binding as CB
from tests.geometry import w14_cases as W

VAN_SM = "Gọi M là trung điểm của SA. Tính độ dài đoạn SM."


def _canh(scene: dict, oid: str) -> dict:
    return next(o for o in scene["objects"] if o["id"] == oid)


def test_doan_con_tren_canh_tro_ve_canh_ay():
    _sp, out, scene = W.chay(*CB._p1(VAN_SM, [CB._mid("M", "S", "A")], "S", "M"))
    assert out.servable, (out.stage_reached, out.reason_code)
    sm = _canh(scene, "doan_SM")
    assert sm["boundary_edge_ids"] == ["S.ABCD::edge:S-A"]
    khoi = _canh(scene, "S.ABCD")
    canh = next(e for e in khoi["edge_ownership"] if e["edge_id"] == "S.ABCD::edge:S-A")
    # khoảng tham số đo từ endpoint_ids[0] tới endpoint_ids[1] của cạnh: M là trung điểm
    t = {canh["endpoint_ids"][0]: 0.0, canh["endpoint_ids"][1]: 1.0}
    assert sm["edge_span"] == {"edge_id": "S.ABCD::edge:S-A", "t0": min(t["S"], 0.5), "t1": max(t["S"], 0.5)}


def test_doan_trung_ca_canh_giu_nhu_cu_khong_co_khoang():
    _sp, _out, scene = W.chay(*CB._p1(VAN_SM, [CB._mid("M", "S", "A")], "S", "M"))
    sa = _canh(scene, "canh_ben_S_A")
    assert sa["boundary_edge_ids"] == ["S.ABCD::edge:S-A"]
    assert "edge_span" not in sa


def test_chi_khi_ca_hai_dau_nam_tren_doan_canh():
    """Quan hệ "nằm trên cạnh" tính CHÍNH XÁC ở tầng được gọi kernel (`quantity_annotations`), không ở tầng cảnh."""
    from fractions import Fraction as F

    from app.simulation.geometry.exact import Vec3
    from app.simulation.semantic_program.quantity_annotations import doan_tren_canh

    mem = {"A": Vec3.of(0, 0, 0), "B": Vec3.of(4, 0, 0), "C": Vec3.of(0, 4, 0), "D": Vec3.of(0, 0, 4),
           "P": Vec3.of(1, 0, 0), "Q": Vec3.of(3, 0, 0), "R": Vec3.of(5, 0, 0), "T": Vec3.of(3, F(1, 1000), 0)}
    khoi = {"id": "K", "type": "solid", "vertex_ids": ["A", "B", "C", "D"],
            "faces": [[0, 1, 2], [0, 1, 3], [1, 2, 3], [0, 2, 3]]}
    doan = lambda oid, u, w: {"id": oid, "type": "segment3", "endpoint_ids": [u, w]}  # noqa: E731
    objs = [khoi, doan("tren", "Q", "P"), doan("vuot", "Q", "R"), doan("lech", "P", "T"), doan("ca_canh", "A", "B")]
    kq = doan_tren_canh(objs, mem)
    assert kq == {"tren": {"solid": "K", "edge": ["A", "B"], "t0": 0.25, "t1": 0.75}}


def test_tang_canh_chi_chep_khoang_da_tinh():
    """`_attach_topology` không tính hình: chỉ tra tên đầu mút cạnh ra id cạnh chuẩn và chép khoảng."""
    objs = [{"id": "K", "type": "solid", "vertex_ids": ["A", "B", "C"], "vertices": [[0, 0, 0]] * 3,
             "faces": [[0, 1, 2]]},
            {"id": "tren", "type": "segment3", "endpoint_ids": ["P", "Q"]}]
    _attach_topology(objs, {"tren": {"solid": "K", "edge": ["A", "B"], "t0": 0.25, "t1": 0.75}})
    assert objs[1]["boundary_edge_ids"] == ["K::edge:A-B"]
    assert objs[1]["edge_span"] == {"edge_id": "K::edge:A-B", "t0": 0.25, "t1": 0.75}
    objs2 = copy.deepcopy(objs)
    objs2[1].pop("boundary_edge_ids"), objs2[1].pop("edge_span")
    _attach_topology(objs2)
    assert "boundary_edge_ids" not in objs2[1]
