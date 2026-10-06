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
import json

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


# ── Yêu cầu 6 — lời kể không lộ tên nội bộ, không lặp danh từ (nguồn: interpreter / geometry_exec) ─────────────
import re  # noqa: E402

import pytest  # noqa: E402

TOKEN_IR = re.compile(r"\b[\w.]*[A-Za-z0-9]_[A-Za-z0-9][\w.]*\b")
LAP_DANH_TU = re.compile(r"(?i)\b(thiết diện|mặt phẳng|đoạn thẳng|đường thẳng|khối)\s+\1\b")


def test_cau_thiet_dien_cua_nguoi_dung():
    """Ảnh của người dùng: "Thiết diện thiết diện là đa giác 4 đỉnh, cắt khối chop bởi mặt phẳng mp."."""
    from app.simulation.semantic_program.geometry_exec import ke_thiet_dien

    cau = ke_thiet_dien("thiết diện", "chop", "mp", 4)
    assert not LAP_DANH_TU.search(cau), cau
    assert "chop" not in cau and " mp" not in cau, cau
    assert cau == "Thiết diện là đa giác 4 đỉnh, giao của mặt phẳng với khối."
    assert ke_thiet_dien("Thiết diện (T)", "S.ABCD", "alpha_plane", 4) == \
        "Thiết diện (T) là đa giác 4 đỉnh, giao của mặt phẳng với khối S.ABCD."
    assert ke_thiet_dien("T", "S.ABCD", "P", 3) == "Thiết diện T là đa giác 3 đỉnh, giao của mặt phẳng P với khối S.ABCD."
    # nhãn câu lệnh mặt phẳng hay kèm phương trình — tên là phần trước dấu hai chấm
    assert ke_thiet_dien("Thiết diện (T)", "S.ABCD", "Mặt phẳng (α): z = 3", 4) == \
        "Thiết diện (T) là đa giác 4 đỉnh, giao của mặt phẳng (α) với khối S.ABCD."


def test_cau_thiet_dien_p1_goi_ten_mat_phang_cua_de():
    """Đối soát băm cảnh P1 (W4): câu khép thiết diện từng mất "(α)" vì chỉ tên biến `alpha_plane` tới được nó;
    tên của mặt phẳng phải lấy từ NHÃN câu lệnh đã dựng nó ("Mặt phẳng (α): z = 3"), đúng như đề gọi."""
    _ho, contract, prog = next(x for x in _bay_ho() if x[0] == "cross_section")
    _sp, out, scene = W.chay(contract, prog)
    cau = next(e["explanation"] for e in scene["events"] if (e.get("explanation") or "").startswith("Thiết diện"))
    assert cau == "Thiết diện (T) là đa giác 4 đỉnh, giao của mặt phẳng (α) với khối S.ABCD.", cau


@pytest.mark.parametrize("nhan,bien,danh_tu,mong", [
    ("thiết diện", "td", "thiết diện", ""),
    ("Thiết diện (T)", "T", "thiết diện", "(T)"),
    (None, "alpha_plane", "mặt phẳng", ""),
    (None, "S.ABCD", "khối", "S.ABCD"),
    ("Mặt phẳng (P)", "mp", "mặt phẳng", "(P)"),
    ("mp_day", "mp_day", "mặt phẳng", ""),
    (None, "A_prime", "điểm", "A′"),
    ("Mặt phẳng (α): z = 3", "alpha_plane", "mặt phẳng", "(α)"),
    # P6: mô hình viết "alpha" thay ký hiệu của đề — một TỪ, không phải ký hiệu ⇒ không in, không đoán thành α
    ("Mặt phẳng alpha", "mat_phang_alpha", "mặt phẳng", ""),
    ("Hình trụ", "hinh_tru", "hình trụ", ""),
    ("Đường thẳng d", "d", "đường thẳng", "d"),
])
def test_ten_trong_loi_ke(nhan, bien, danh_tu, mong):
    from app.simulation.semantic_program.geometry_exec import ten_trong_loi_ke

    assert ten_trong_loi_ke(nhan, bien, danh_tu) == mong


def _bay_ho():
    from app.simulation.semantic_program.analyze_contract import build_request_contract
    from scripts import replay_negative_boundaries as RNB
    from tests.geometry import test_assumption_certificate as AC
    from tests.geometry import test_regular_square_pyramid as RSP

    for ho, f in sorted(W.HO.items()):
        _t, contract = f()
        yield ho, contract, W.chuong_trinh(contract)
    raw = RNB.doc_raw_theo_thu_tu("p1_chop_thiet_dien_khoang_cach")
    yield "cross_section", build_request_contract(
        json.loads(raw["semantic_analyze"][0]), problem_text=RNB.doc_de_bai()["p1_chop_thiet_dien_khoang_cach"],
        domain="hinh_hoc"), json.loads(raw["semantic_program"][0])
    yield ("cross_section_correct_plane", *AC.PHEP_DUNG_DUNG["O1b_doi_chung_cat_bang_beta"]())
    yield ("regular_square_pyramid", *RSP._nap("S1_side_height_volume"))
    yield ("sm_on_edge", *CB._p1(VAN_SM, [CB._mid("M", "S", "A")], "S", "M"))


def test_loi_ke_bay_ho_khong_lo_ten_noi_bo():
    loi = []
    for ho, contract, prog in _bay_ho():
        _sp, out, scene = W.chay(contract, prog)
        assert out.servable, (ho, out.stage_reached, out.reason_code)
        for e in scene["events"]:
            for truong in ("explanation", "learner_text"):
                cau = e.get(truong) or ""
                if TOKEN_IR.search(cau) or LAP_DANH_TU.search(cau):
                    loi.append((ho, truong, cau))
    assert not loi, loi
