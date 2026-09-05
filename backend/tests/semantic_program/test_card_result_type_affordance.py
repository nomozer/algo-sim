# -*- coding: utf-8 -*-
"""Thẻ nói ra KIỂU KẾT QUẢ của từng phép. **0 lượt gọi model.**

    `docs/MODEL_FACING_OPERATION_AFFORDANCE_ALIGNMENT.md`, 2026-09-05.

Thẻ vốn in TOÁN HẠNG của mọi phép và **không in kiểu KẾT QUẢ của phép nào**,
dù cả hai vế đã nằm sẵn trong thẩm quyền: `_CHU_KY` mang kiểu trả về ở vế phải,
`_KIEU_DUNG` mang kiểu vật mà mỗi `construct_*` sinh ra.

Đo được ở `CURVED_SECTION_MODEL_DISCOVERABILITY_PROBE`: lượt tổng hợp **đầu**
chọn `construct_section` **8/8** ca — kể cả sáu ca khối cong — và `circle3`
xuất hiện trong khai báo **0/8**. Nó không vắng vì bị cấm: `curved_solid` cũng
không có trong danh sách kiểu mà vẫn được dùng 5/8. Nó vắng vì `circle3` chỉ
tồn tại với tư cách **kiểu kết quả**, tức đúng thứ thẻ không nói.

Nhãn `[BIỂU THỨC→assign]` nói **cửa tiêu thụ**, không nói **kiểu ra** — hai câu
khác nhau, và bộ test này khoá câu thứ hai.
"""
from __future__ import annotations

import sys
import typing
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
if str(GOC) not in sys.path:
    sys.path.insert(0, str(GOC))

from app.simulation.semantic_program import contract as C  # noqa: E402
from app.simulation.semantic_program.grammar_card import (  # noqa: E402
    _kieu_khai_duoc,
    _kieu_ra,
    grammar_card,
)
from app.simulation.semantic_program.ir_static_check import (  # noqa: E402
    _CHU_KY,
    _KIEU_DUNG,
)

THE = grammar_card("hinh_hoc")
DONG = {d.strip().partition("]")[2].strip().partition(":")[0].strip(): d
        for d in THE.split("\n") if d.strip().startswith("[")}


# ══ KIỂU RA — dẫn xuất, không viết tay ═══════════════════════════════════
def test_kieu_ra_DAN_XUAT_tu_dung_hai_bang_tham_quyen():
    kr = _kieu_ra()
    for n, k in _KIEU_DUNG.items():
        assert kr[n] == k, n
    for n, sig in _CHU_KY.items():
        assert kr[n] == sig[1], n
    # Không phép nào ngoài hai bảng ấy được gán kiểu ra — bịa một kiểu cố định
    # cho `assign`/`measure`/`arith` là nói dối, vì kiểu của chúng do toán hạng
    # quyết định.
    assert set(kr) == set(_KIEU_DUNG) | set(_CHU_KY)


@pytest.mark.parametrize("phep,kieu", [
    ("intersect_plane_curved", "circle3"),
    ("construct_section", "section"),
    ("construct_curved_solid", "curved_solid"),
    ("construct_solid", "solid"),
    ("construct_polygon", "polygon3"),
    ("construct_point", "point3"),
    ("construct_line", "line3"),
    ("construct_plane", "plane3"),
    ("midpoint", "point3"),
    ("vector_from_points", "vector3"),
])
def test_the_IN_RA_kieu_ket_qua_cua_tung_phep(phep, kieu):
    assert DONG[phep].endswith(f"→{kieu}"), DONG[phep]


def test_HAI_DUONG_CAT_doi_chieu_duoc_TREN_CHINH_DONG():
    """Bốn vế — kiểu vào · phép · kiểu ra · cửa tiêu thụ — cùng một dòng.

    Đây là điều mà thẻ trước KHÔNG cho làm: hai dòng có cùng hình dạng toán
    hạng (`solid` + `plane3`) mà không dòng nào nói mình sinh ra gì, nên phân
    biệt chúng phải dựa vào tên phép.
    """
    ds = DONG["construct_section"]
    ipc = DONG["intersect_plane_curved"]
    assert "solid:tên<solid>" in ds and ds.endswith("→section")
    assert "[LỆNH]" in ds
    assert "solid:tên<curved_solid>" in ipc and ipc.endswith("→circle3")
    assert "[BIỂU THỨC→assign]" in ipc


def test_phep_KHONG_co_kieu_ra_co_dinh_thi_KHONG_gan_bua():
    for n in ("assign", "declare_point", "measure", "literal", "var", "arith",
              "unary"):
        if n in DONG:
            assert "→" not in DONG[n].rsplit("]", 1)[-1] or \
                not DONG[n].rstrip().split()[-1].startswith("→"), DONG[n]


# ══ KIỂU KHAI ĐƯỢC — mọi kiểu thẻ NHẮC TỚI đều phải khai được ════════════
def test_moi_kieu_the_NHAC_TOI_deu_khai_duoc():
    """Bất biến trung tâm của `_kieu_khai_duoc`, kiểm bằng chính văn bản thẻ."""
    khai = set(_kieu_khai_duoc())
    nhac = set()
    for _, sig in _CHU_KY.items():
        toan_hang, ra = sig
        nhac.add(ra)
        for _, chap_nhan in toan_hang:
            nhac.update(chap_nhan)
    nhac.update(_KIEU_DUNG.values())
    thieu = (nhac & set(typing.get_args(C.MemoryType))) - khai
    assert not thieu, f"thẻ nhắc {sorted(thieu)} mà không cho khai"


def test_circle3_va_curved_solid_NAY_khai_duoc():
    """Hồi quy cho đúng chỗ danh sách viết tay đã trôi (wave cong 2026-09-03)."""
    khai = _kieu_khai_duoc()
    assert "circle3" in khai and "curved_solid" in khai
    dong = [d for d in THE.split("\n") if "type nhận đúng một trong" in d][0]
    assert "circle3" in dong and "curved_solid" in dong


def test_danh_sach_kieu_GIU_THU_TU_cua_hop_dong():
    thu_tu = [k for k in typing.get_args(C.MemoryType)]
    khai = _kieu_khai_duoc()
    assert khai == [k for k in thu_tu if k in set(khai)]


def test_KHONG_lot_kieu_Tin_hoc_vao_the_hinh_hoc():
    """Dẫn xuất không được biến thành 'liệt kê tất cả'."""
    khai = set(_kieu_khai_duoc())
    assert not (khai & {"array", "stack", "queue", "matrix", "map", "set",
                        "tree_node", "graph", "node_ref", "null", "str"})


# ══ TIÊM LỖI ═════════════════════════════════════════════════════════════
def test_TIEM_1_bo_kieu_ra_khoi__CHU_KY_thi_the_MAT_mui_ten(monkeypatch):
    """Nguồn là `_CHU_KY`, không phải một chuỗi viết tay ở thẻ."""
    from app.simulation.semantic_program import grammar_card as GC

    goc = dict(_CHU_KY)
    monkeypatch.setattr(
        GC, "_kieu_ra",
        lambda: {n: k for n, k in _KIEU_DUNG.items()})
    # Gọi lại bộ dựng dòng với bảng đã gỡ — dòng phép giao mất mũi tên.
    lenh, bt = GC._tap_hinh_hoc()
    khoi = GC._khoi_loc("x", C.ValueExpr, bt, lenh=lenh,
                        cua=GC._cua_tieu_thu(lenh), kieu_ra=GC._kieu_ra())
    d = [l for l in khoi.split("\n") if "intersect_plane_curved" in l][0]
    assert not d.rstrip().endswith("→circle3")
    assert goc["intersect_plane_curved"][1] == "circle3"   # thẩm quyền còn nguyên


def test_TIEM_2_danh_sach_kieu_quay_ve_VIET_TAY_thi_guard_do():
    """Tái dựng đúng danh sách viết tay cũ ⇒ bất biến ở trên phải bắt được."""
    cu = [k for k in typing.get_args(C.MemoryType)
          if k in ("point3", "vector3", "line3", "plane3", "polygon3",
                   "solid", "section", "float", "bool")]
    nhac = set(_KIEU_DUNG.values())
    for _, sig in _CHU_KY.items():
        nhac.add(sig[1])
    thieu = (nhac & set(typing.get_args(C.MemoryType))) - set(cu)
    assert {"circle3", "curved_solid"} <= thieu


def test_TIEM_3_the_day_du_KHONG_bi_dung_toi():
    """Mũi tên chỉ áp cho thẻ hình học — bản Tin học giữ nguyên hành vi."""
    day_du = grammar_card()
    assert "→circle3" not in day_du
    assert len(day_du.encode("utf-8")) == 5588
