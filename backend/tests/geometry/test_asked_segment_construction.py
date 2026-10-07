# -*- coding: utf-8 -*-
"""regular-square-pyramid-w03 · H-W2-2 — đoạn mà đề hỏi độ dài được DỰNG trước đáp số. 0 lượt gọi model.

Tái hiện: "Gọi H là hình chiếu vuông góc của S lên đường thẳng BD. Tính độ dài đoạn SH." Chương trình đo
d(S, H) nhưng không dựng đoạn SH. W2 · A (nhãn độ dài chỉ khi đoạn mang nó đã dựng) vì thế bỏ nhãn đáp số khỏi hình —
trái kỳ vọng W18 (chọn đáp số ⇒ nhãn của nó hiện), và W2 hạ kỳ vọng ấy thành "vắng" (PC1-W2).

Sửa ở bước bổ sung dựng hình (`formation`, một thẩm quyền): khi witness của nghĩa vụ là khoảng cách giữa HAI ĐIỂM mà
chưa đoạn nào nối chúng trước phép đo, dựng `construct_segment` "Đoạn SH" ngay trước phép đo. Đối chứng: khoảng cách
điểm–đường (nhân chứng W18) không thêm đoạn; đoạn đã có không bị dựng lần hai; đại lượng không phải witness của
nghĩa vụ không thêm gì.
"""
from __future__ import annotations

import copy

from app.simulation.semantic_program.formation import hoan_thien_dung_hinh
from tests.geometry import test_construction_binding as CB
from tests.geometry import route_cases as W


def _cap_doan(spec) -> list[set]:
    ra = []
    for s in spec.statements:
        if s.kind == "construct_segment":
            ra += [{s.endpoint_a, s.endpoint_b}] if s.endpoint_a else [
                {x["endpoint_a"], x["endpoint_b"]} if isinstance(x, dict) else {x.endpoint_a, x.endpoint_b}
                for x in s.items]
    return ra


def _sh():
    return CB.CA["B10_proj_line_ok"]()


def test_doan_duoc_hoi_duoc_dung_truoc_dap_so():
    contract, prog = _sh()
    _sp, out, scene = W.chay(contract, prog)
    assert out.servable, (out.stage_reached, out.reason_code, out.details)
    sh = [o for o in scene["objects"] if o["type"] == "segment3" and set(o.get("endpoint_ids") or ()) == {"S", "H"}]
    assert len(sh) == 1, [o["id"] for o in scene["objects"] if o["type"] == "segment3"]
    sh = sh[0]
    assert sh["producer"] == "construct_segment" and set(sh["depends"]) == {"S", "H"}
    assert sh["notation"] == "SH" and "SH" in sh["label"]
    d = next(o for o in scene["objects"] if o["id"] == "d_kq")
    assert d["value"] == "3√6"
    assert d["annotation"]["anchor"] == "segment" and set(d["annotation"]["subject_ids"]) == {"S", "H"}
    # thứ tự: H có trước đoạn SH; đoạn SH có trước bước kết luận đáp số
    buoc = scene["formation"]["steps"]
    hien = {i: min(k for k, st in enumerate(buoc) if i in st["visible_ids"]) for i in ("H", sh["id"])}
    ket_luan = max(k for k, st in enumerate(buoc) if st.get("semantic_kind") == "FINAL_RESULT")
    assert hien["H"] < hien[sh["id"]] < ket_luan, (hien, ket_luan)


def test_doan_da_co_khong_dung_lan_hai():
    contract, prog = _sh()
    prog = copy.deepcopy(prog)
    j = next(i for i, s in enumerate(prog["statements"]) if s.get("target_var") == "d_kq")
    prog["statements"].insert(j, {"kind": "construct_segment", "target_var": "SH_doan", "endpoint_a": "H",
                                  "endpoint_b": "S"})
    moi = hoan_thien_dung_hinh(W.spec_cua(prog), contract).spec
    assert _cap_doan(moi).count({"S", "H"}) == 1


def test_khoang_cach_diem_duong_khong_them_doan():
    contract, prog = CB._p1(CB._van("B10_proj_line_ok"), [CB._duong("BD", "B", "D")], "S", "BD")
    moi = hoan_thien_dung_hinh(W.spec_cua(prog), contract).spec
    assert not any("BD" in c for c in _cap_doan(moi)), _cap_doan(moi)


def test_khoang_cach_khong_phai_witness_cua_nghia_vu_khong_them_doan():
    contract, prog = _sh()
    contract = contract.model_copy(update={"obligations": []})
    moi = hoan_thien_dung_hinh(W.spec_cua(prog), contract).spec
    assert {"S", "H"} not in _cap_doan(moi)
