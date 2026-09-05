# -*- coding: utf-8 -*-
"""THIẾT DIỆN TRÒN — đường `intersect_plane_curved → circle3 → measure`.
**0 lượt gọi model.**

    `docs/CURVED_SECTION_RADIUS_PATH_ADJUDICATION.md`, 2026-09-05.
    Fixture `c5b`/`c9b` — **POST_V3_DEVELOPMENT_FIXTURE**. V3 đã tiêu; đây là
    replay tất định trên dữ liệu đã công bố, KHÔNG phải acceptance mới.

⚠️ **Bộ test này KHOÁ một năng lực ĐÃ CÓ, không dẫn dắt mã mới.** Wave điều tra
kết luận `SYSTEM_IMPLEMENTATION_GAP = NO`: hai bản sửa tối thiểu của `c5b` và
`c9b` served ngay trên candidate hiện tại, không đụng một dòng mã sản phẩm nào.
Nói thẳng điều đó ở đây, vì một bộ test xanh-từ-đầu dễ bị đọc nhầm thành bằng
chứng của một wave sửa lỗi.

Hai đường KHÁC NHAU, và ranh giới ấy là thứ phải giữ:

    construct_section        nhận khối ĐA DIỆN  → `section` (đa giác)
    intersect_plane_curved   nhận `curved_solid` → `circle3` (giao tuyến tròn)

`c5b`/`c9b` của V3 chọn đường thứ nhất cho một khối cong, rồi đo `radius` trên
`section` — mà `radius` không nhận `section`. Đó là **lựa chọn của mô hình**,
không phải khoảng trống của hệ.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(GOC))

from app.simulation.semantic_program.contract import (  # noqa: E402
    SemanticProgramSpec,
)
from app.simulation.semantic_program.obligations import Obligation  # noqa: E402
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402

V3 = GOC.parent / "docs" / "evaluation" / "geometry" / "curved-acceptance-v3"
VB = {"containers": [], "pointers": [], "value_boxes": []}


@pytest.fixture(scope="module")
def v3():
    d = json.loads((V3 / "curved_acceptance.json").read_text(encoding="utf-8"))
    return {r["id"]: r for r in d["cuoi"]}


def _hd(v3, cid=None):
    """Hợp đồng V3 **nguyên si** — nghĩa vụ không được viết lại cho dễ đậu."""
    ca = v3 if cid is None else v3[cid]
    rc = ca["request_contract"]
    return RequestContract(
        problem_text=rc["problem_text"], input_facts=rc["input_facts"],
        obligations=tuple(Obligation(**o) for o in rc["obligations"]))


def _spec(decls, stmts, title="Thiết diện tròn"):
    return SemanticProgramSpec.model_validate({
        "spec_version": "1.0", "title": title,
        "description": "Dựng khối cong rồi cắt bằng mặt phẳng.",
        "pedagogical_intent": "Thấy thiết diện vuông góc trục là đường tròn.",
        "memory_declarations": decls, "statements": stmts,
        "visual_bindings": VB})


def _gt(out):
    return {k: str(v) for k, v in (out.final_memory or {}).items()}


# ── Bộ dựng dùng chung. Tên biến TRUNG TÍNH ở phần lớn test: đường năng lực
#    không được phụ thuộc chính tả (`test_B10`).
def _khoi_cat(kind, *, dinh_z, vanh_x, cat_t, fid, ten="K", ten_c="C",
              ratio=None, do=("radius",)):
    decls = [
        {"name": "P0", "type": "point3", "initial_value": [0, 0, 0],
         "source_fact_id": fid},
        {"name": "P1", "type": "point3", "initial_value": [0, 0, dinh_z],
         "source_fact_id": fid},
        {"name": "P2", "type": "point3", "initial_value": [vanh_x, 0, 0],
         "source_fact_id": fid},
        {"name": ten, "type": "curved_solid"},
        {"name": "TR", "type": "line3"},
        {"name": "MM", "type": "point3"},
        {"name": "MP", "type": "plane3"},
        {"name": ten_c, "type": "circle3"}]
    stmts = [
        {"kind": "construct_curved_solid", "target_var": ten,
         "curved_kind": kind, "anchor": "P0", "apex_or_top": "P1",
         "rim_point": "P2"},
        {"kind": "construct_line", "target_var": "TR",
         "through_a": "P1", "through_b": "P0"},
        {"kind": "construct_point", "target_var": "MM",
         "expr": {"kind": "divide_segment", "a": "P1", "b": "P0",
                  "ratio": ratio or cat_t}},
        {"kind": "assign", "target_var": "MP",
         "expr": {"kind": "plane_perpendicular_to_line", "point": "MM",
                  "line": "TR"}},
        {"kind": "assign", "target_var": ten_c,
         "expr": {"kind": "intersect_plane_curved", "solid": ten,
                  "plane": "MP"}}]
    for q in do:
        w = {"radius": "W_R", "area": "W_A"}[q]
        decls.append({"name": w, "type": "float"})
        stmts.append({"kind": "assign", "target_var": w,
                      "expr": {"kind": "measure", "quantity": q,
                               "of": ten_c}})
    return decls, stmts


def _hd_don(de, fid, obl):
    return RequestContract(
        problem_text=de,
        input_facts=[{"fact_id": fid, "label": "dữ kiện", "values": ["K"],
                      "provenance": "confirmed"}],
        obligations=tuple(Obligation(**o) for o in obl))


# ══ POSITIVE ═════════════════════════════════════════════════════════════
def test_P1_mp_vuong_goc_truc_cat_TRU_cho_circle3():
    d, s = _khoi_cat("cylinder", dinh_z=20, vanh_x=9, cat_t="1/2", fid="f",
                     do=("radius", "area"))
    out = verify_and_compile(
        _hd_don("Hình trụ bị cắt.", "f",
                [{"kind": "radius", "container": "C",
                  "params": {"witness": "W_R"}},
                 {"kind": "area", "container": "C",
                  "params": {"witness": "W_A"}}]),
        _spec(d, s))
    assert out.executable and out.servable, getattr(out, "details", None)
    assert "Circle3" in str(type((out.final_memory or {}).get("C")))


def test_P2_P3_ban_kinh_va_dien_tich_dung():
    """r = bán kính trụ; S = πr²."""
    d, s = _khoi_cat("cylinder", dinh_z=20, vanh_x=9, cat_t="1/2", fid="f",
                     do=("radius", "area"))
    out = verify_and_compile(
        _hd_don("Hình trụ bị cắt.", "f",
                [{"kind": "radius", "container": "C",
                  "params": {"witness": "W_R"}},
                 {"kind": "area", "container": "C",
                  "params": {"witness": "W_A"}}]),
        _spec(d, s))
    g = _gt(out)
    assert (g["W_R"], g["W_A"]) == ("9", "81π")


def test_P4_P5_mp_vuong_goc_truc_cat_NON_theo_ti_le_dong_dang():
    """Nón r=10, h=15; cắt cách đỉnh 9 ⇒ r_C = 10·(9/15) = 6."""
    d, s = _khoi_cat("cone", dinh_z=15, vanh_x=10, cat_t="3/5", fid="f")
    out = verify_and_compile(
        _hd_don("Hình nón bị cắt.", "f",
                [{"kind": "radius", "container": "C",
                  "params": {"witness": "W_R"}}]),
        _spec(d, s))
    assert out.executable and out.servable, getattr(out, "details", None)
    assert _gt(out)["W_R"] == "6"


def test_P7_P8_P9_trace_va_scene3d_mang_circle3_dung_phu_thuoc():
    from app.ai import pipeline

    d, s = _khoi_cat("cylinder", dinh_z=20, vanh_x=9, cat_t="1/2", fid="f",
                     do=("radius", "area"))
    hd = _hd_don("Hình trụ bị cắt.", "f",
                 [{"kind": "radius", "container": "C",
                   "params": {"witness": "W_R"}},
                  {"kind": "area", "container": "C",
                   "params": {"witness": "W_A"}}])
    spec = _spec(d, s)
    assert verify_and_compile(hd, spec).servable
    canh = pipeline._dung_scene3d(spec, hd)
    objs = {o.get("name") or o.get("id"): o for o in (canh or {}).get("objects", [])}
    c = objs.get("C")
    assert c is not None and c["type"] == "circle3"
    assert c["producer"] == "intersect_plane_curved"
    assert set(c["depends"]) == {"K", "MP"}, c["depends"]
    # Bao đóng của đáp số phải dẫn về đường tròn.
    assert objs["W_R"]["depends"] == ["C"]
    assert objs["W_A"]["depends"] == ["C"]


# ══ P10 · `c5b` / `c9b` — REPLAY TRÊN CHÍNH CHƯƠNG TRÌNH MÔ HÌNH ĐÃ SINH ══
#
# Không dựng lại bằng tay. Lấy nguyên chương trình trong artifact V3 rồi áp
# từng delta lên nó — cách duy nhất để bảng delta nói về ca thật chứ về một bài
# tương tự do tôi viết.
# ── ABLATION: delta nào CẦN, delta nào chỉ là trang trí ──────────────────
def _sua_khai(ten, kieu):
    def f(p):
        for x in p["memory_declarations"]:
            if x["name"] == ten:
                x["type"] = kieu
    return f


def _sua_producer(p):
    for i, s in enumerate(p["statements"]):
        if s["kind"] == "construct_section":
            p["statements"][i] = {
                "kind": "assign", "target_var": s["target_var"],
                "expr": {"kind": "intersect_plane_curved",
                         "solid": s["solid"], "plane": s["plane"]}}


def _sua_ratio(moi):
    def f(p):
        for s in p["statements"]:
            e = s.get("expr") or {}
            if e.get("kind") == "divide_segment":
                e["ratio"] = moi
    return f


def _replay(v3, cid, deltas):
    import copy

    p = copy.deepcopy(v3[cid]["chuong_trinh"])
    for f in deltas:
        f(p)
    try:
        spec = SemanticProgramSpec.model_validate(p)
    except Exception:                                             # noqa: BLE001
        return None
    return verify_and_compile(_hd(v3, cid), spec)


#: Delta TỐI THIỂU đã chứng minh bằng ablation vét cạn (mọi tập con).
_DELTA = {
    "c5b": [("khai[C:circle3]", _sua_khai("C", "circle3")),
            ("producer[construct_section→intersect_plane_curved]", _sua_producer)],
    "c9b": [("khai[C:circle3]", _sua_khai("C", "circle3")),
            ("producer[construct_section→intersect_plane_curved]", _sua_producer),
            ("ratio[9/6→3/5]", _sua_ratio("3/5"))],
}


@pytest.mark.parametrize("cid,dap", [("c5b", {"r_C": "9", "area_C": "81π"}),
                                     ("c9b", {"ban_kinh_c": "6"})])
def test_P10_delta_TOI_THIEU_du_de_SERVED(v3, cid, dap):
    out = _replay(v3, cid, [f for _, f in _DELTA[cid]])
    assert out is not None and out.servable, getattr(out, "details", None)
    g = _gt(out)
    assert {k: g.get(k) for k in dap} == dap


@pytest.mark.parametrize("cid", ["c5b", "c9b"])
def test_B7_MOI_delta_deu_CAN__bo_bat_ky_cai_nao_cung_bac(v3, cid):
    """Tính tối thiểu, chứng minh chứ không tuyên bố.

    Bỏ đúng một delta rồi thấy nó bác lại — đó là điều biến bảng delta từ *"tôi
    đã sửa ba chỗ"* thành *"ba chỗ ấy đều cần"*. Với `c5b`,
    `hinh_tru: solid → curved_solid` KHÔNG có trong bảng, vì bỏ nó vẫn served
    (`test_T4a`).
    """
    ds = _DELTA[cid]
    for bo, _ in ds:
        out = _replay(v3, cid, [f for ten, f in ds if ten != bo])
        assert out is None or not out.servable, f"{cid}: bỏ {bo} mà vẫn served"


def test_B7b_c9b_co_HAI_khiem_khuyet_DOC_LAP(v3):
    """Cổng phủ che khiếm khuyết thứ hai — chỉ lộ ra sau khi vá khiếm khuyết đầu.

    Sửa kiểu + producer nhưng giữ `ratio = 9/6` thì tuyến đi SÂU HƠN rồi mới
    chết, ở `execution`, vì `t = −1/2` nằm ngoài khối. `DivideSegmentExpr` định
    nghĩa `ratio` là `t` (`t=0` là `a`, `t=1` là `b`), nên `SM=9` trên `SO=15`
    là `3/5` — mô hình đã đọc `9/6` như tỉ số `SM:MO`.
    """
    ds = dict(_DELTA["c9b"])
    out = _replay(v3, "c9b", [ds["khai[C:circle3]"],
                              ds["producer[construct_section→intersect_plane_curved]"]])
    assert not out.servable
    assert out.stage_reached == "execution"     # SÂU hơn `structural_coverage`
    assert any("CURVED_PLANE_DOES_NOT_CUT" in x for x in (out.details or [])), \
        out.details


def test_P0_duong_MO_HINH_da_chon_van_bi_bac(v3):
    """Bản gốc `c5b`/`c9b`: `construct_section` trên khối cong ⇒ vẫn bác.

    Đây là phần chứng minh rằng khoảng trống thuộc về LỰA CHỌN của mô hình,
    không thuộc về hệ — và nó phải giữ nguyên như thế.
    """
    for cid in ("c5b", "c9b"):
        ca = v3[cid]
        out = verify_and_compile(
            _hd(ca), SemanticProgramSpec.model_validate(ca["chuong_trinh"]))
        assert not out.servable
        assert out.error_code == "requested_operation_uncovered"


# ══ BOUNDARY ═════════════════════════════════════════════════════════════
def test_B2_radius_cua_section_VAN_bi_bac_theo_kieu():
    from app.simulation.semantic_program.measure_contract import BANG_PHEP_DO

    assert "section" not in BANG_PHEP_DO["radius"].kieu_of
    assert "circle3" in BANG_PHEP_DO["radius"].kieu_of


def test_B1_ranh_gioi_section_vs_circle3_GIU_NGUYEN():
    """Hai phép dựng, hai miền, hai kiểu kết quả — không được nhập một."""
    from app.simulation.semantic_program.measure_contract import BANG_PHEP_DO

    assert "circle3" in BANG_PHEP_DO["area"].kieu_of
    assert "section" in BANG_PHEP_DO["area"].kieu_of
    # `lateral_area` KHÔNG nhận circle3 — mặt cong khác hình phẳng.
    assert "circle3" not in BANG_PHEP_DO["lateral_area"].kieu_of


@pytest.mark.parametrize("t,ma", [
    ("2", "CURVED_PLANE_DOES_NOT_CUT"),      # ngoài khối
    ("0", "CURVED_PLANE_TANGENT"),           # chạm đỉnh nón
])
def test_B4_B5_B6_mat_phang_ngoai_mien_tra_MA_DA_CONG_BO(t, ma):
    d, s = _khoi_cat("cone", dinh_z=15, vanh_x=10, cat_t=t, fid="f")
    out = verify_and_compile(
        _hd_don("Hình nón bị cắt.", "f",
                [{"kind": "radius", "container": "C",
                  "params": {"witness": "W_R"}}]),
        _spec(d, s))
    assert not out.executable
    assert any(ma in x for x in (out.details or [])), out.details


def test_B3_mat_phang_XIEN_tra_ma_NGOAI_BAO_DONG():
    """Elip nằm ngoài bao đóng v1 — mã nói đúng *"ngoài bao đóng"*."""
    from app.simulation.geometry.curved import ERR_NGOAI_BAO_DONG

    d, s = _khoi_cat("cylinder", dinh_z=20, vanh_x=9, cat_t="1/2", fid="f")
    # Thay mặt phẳng ⊥ trục bằng một mặt phẳng XIÊN qua ba điểm.
    d = [x for x in d if x["name"] != "MP"] + [
        {"name": "Q", "type": "point3", "initial_value": [0, 9, 5],
         "source_fact_id": "f"},
        {"name": "MP", "type": "plane3"}]
    s = [x for x in s if x.get("target_var") != "MP"]
    # Chèn NGAY TRƯỚC `assign C` — thứ tự khai báo–dùng là luật của IR.
    i = next(k for k, x in enumerate(s) if x.get("target_var") == "C")
    s.insert(i, {"kind": "construct_plane", "target_var": "MP",
                 "through": ["P0", "P2", "Q"]})
    out = verify_and_compile(
        _hd_don("Hình trụ bị cắt xiên.", "f",
                [{"kind": "radius", "container": "C",
                  "params": {"witness": "W_R"}}]),
        _spec(d, s))
    assert not out.executable
    assert any(ERR_NGOAI_BAO_DONG in x for x in (out.details or [])), out.details


def test_B8_hoi_quy_c1a_va_c7a_van_served(v3):
    """Đường cong đã thông ở hai wave trước không được động."""
    ca = v3["c7a"]
    out = verify_and_compile(
        _hd(ca), SemanticProgramSpec.model_validate(ca["chuong_trinh"]))
    assert out.servable, getattr(out, "details", None)


def test_B9_radius_va_area_cua_CUNG_circle3_cach_ly():
    d, s = _khoi_cat("cylinder", dinh_z=20, vanh_x=9, cat_t="1/2", fid="f",
                     do=("radius", "area"))
    out = verify_and_compile(
        _hd_don("Hình trụ bị cắt.", "f",
                [{"kind": "radius", "container": "C",
                  "params": {"witness": "W_R"}},
                 {"kind": "area", "container": "C",
                  "params": {"witness": "W_A"}}]),
        _spec(d, s))
    g = _gt(out)
    assert g["W_R"] == "9" and g["W_A"] == "81π"
    assert out.servable


def test_B10_ten_bien_TRUNG_TINH_cho_ket_qua_y_het():
    """Đổi `C` thành một tên vô nghĩa ⇒ mọi thứ giữ nguyên."""
    d, s = _khoi_cat("cylinder", dinh_z=20, vanh_x=9, cat_t="1/2", fid="f",
                     ten_c="zzz", do=("radius",))
    out = verify_and_compile(
        _hd_don("Hình trụ bị cắt.", "f",
                [{"kind": "radius", "container": "zzz",
                  "params": {"witness": "W_R"}}]),
        _spec(d, s))
    assert out.servable and _gt(out)["W_R"] == "9"


# ══ AUTHORITY GUARD — mỗi dòng là một phép tiêm ══════════════════════════
def test_G_authority_dang_ky_du_cho_circle3():
    """Bỏ bất kỳ đăng ký nào dưới đây là làm đỏ đúng test tương ứng ở trên."""
    from app.simulation.semantic_program.ir_static_check import _CHU_KY
    from app.simulation.semantic_program.measure_contract import BANG_PHEP_DO
    from app.simulation.semantic_program.scene3d import _TRUONG, RENDER_HINT

    # Chữ ký ĐẦY ĐỦ: chỉ `curved_solid` mới vào được, và ra là `circle3`.
    # Đây là chỗ ranh giới `section` ↔ `circle3` được cưỡng chế ở tầng tĩnh.
    assert _CHU_KY["intersect_plane_curved"] == (
        (("solid", ("curved_solid",)), ("plane", ("plane3",))), "circle3")
    assert "circle3" in BANG_PHEP_DO["radius"].kieu_of      # tiêm ④
    assert "circle3" in BANG_PHEP_DO["area"].kieu_of        # tiêm ⑤
    assert RENDER_HINT.get("circle3") == "circle"           # tiêm ⑧
    # `radius_sq`, KHÔNG `radius`: miền chính xác dừng ở bình phương hữu tỉ.
    assert _TRUONG["circle3"] == ("center", "normal", "radius_sq")


def _tru(do=("radius",), obl=None):
    d, s = _khoi_cat("cylinder", dinh_z=20, vanh_x=9, cat_t="1/2", fid="f",
                     do=do)
    return _hd_don("Hình trụ bị cắt.", "f", obl or
                   [{"kind": "radius", "container": "C",
                     "params": {"witness": "W_R"}}]), _spec(d, s)


def _non(t="3/5"):
    d, s = _khoi_cat("cone", dinh_z=15, vanh_x=10, cat_t=t, fid="f")
    return _hd_don("Hình nón bị cắt.", "f",
                   [{"kind": "radius", "container": "C",
                     "params": {"witness": "W_R"}}]), _spec(d, s)


def _bo_chan(ma):
    """Gỡ ĐÚNG MỘT chốt của kernel, giữ nguyên phần còn lại.

    Bịa ra một đường tròn ở đúng chỗ chốt ấy đang từ chối. Nếu hệ vẫn phục vụ
    sau khi gỡ, thì chốt ấy — chứ không phải một tầng nào khác ở hạ nguồn — là
    thứ duy nhất đứng giữa hệ và một thiết diện KHÔNG TỒN TẠI.
    """
    from app.simulation.geometry import curved as CV

    goc = CV.intersect_plane_curved

    def gia(s, pl):
        try:
            return goc(s, pl)
        except Exception as e:                                    # noqa: BLE001
            if getattr(e, "code", None) == ma:
                return CV.Circle3(s.anchor, pl.normal, s.radius_sq)
            raise
    return gia


@pytest.mark.parametrize("luong,witness", [("radius", "W_R"), ("area", "W_A")])
def test_T1_T2_go_circle3_khoi_BANG_PHEP_DO_thi_BAC(monkeypatch, luong, witness):
    """Tiêm ①② — bảng phép đo là thẩm quyền thật, không phải chú thích."""
    import dataclasses

    from app.simulation.semantic_program.ir_static_check import _KIEU_DO
    from app.simulation.semantic_program.measure_contract import BANG_PHEP_DO

    hd, spec = _tru(do=("radius", "area"),
                    obl=[{"kind": luong, "container": "C",
                          "params": {"witness": witness}}])
    assert verify_and_compile(hd, spec).servable          # xanh trước khi tiêm

    # `_KIEU_DO` DẪN XUẤT lúc import, nên phải tiêm cả hai — và chính sự phải
    # tiêm hai chỗ ấy là bằng chứng dẫn xuất chỉ chạy MỘT LẦN: sửa bảng nguồn
    # lúc chạy không tới được tầng thẩm định tĩnh.
    pd = BANG_PHEP_DO[luong]
    hep = dataclasses.replace(
        pd, kieu_of=tuple(k for k in pd.kieu_of if k != "circle3"))
    monkeypatch.setitem(BANG_PHEP_DO, luong, hep)
    monkeypatch.setitem(_KIEU_DO, luong,
                        (hep.kieu_of, hep.kieu_wrt if hep.hai_toan_hang else None))
    assert not verify_and_compile(hd, spec).servable


def test_T3_doi_KIEU_TRA_VE_cua_intersect_plane_curved_thi_BAC(monkeypatch):
    """Tiêm ③ — `circle3` ra khỏi chữ ký ⇒ `measure(radius)` mất chỗ bám."""
    from app.simulation.semantic_program.ir_static_check import _CHU_KY

    hd, spec = _tru()
    assert verify_and_compile(hd, spec).servable

    toan_hang, _ = _CHU_KY["intersect_plane_curved"]
    monkeypatch.setitem(_CHU_KY, "intersect_plane_curved",
                        (toan_hang, "section"))
    assert not verify_and_compile(hd, spec).servable


def _doi_khai(d, doi):
    return [{**x, "type": doi[x["name"]]} if x["name"] in doi else x for x in d]


def _tru_khai(doi):
    d, s = _khoi_cat("cylinder", dinh_z=20, vanh_x=9, cat_t="1/2", fid="f",
                     do=("radius", "area"))
    return _hd_don("Hình trụ bị cắt.", "f",
                   [{"kind": "radius", "container": "C",
                     "params": {"witness": "W_R"}},
                    {"kind": "area", "container": "C",
                     "params": {"witness": "W_A"}}]), _spec(_doi_khai(d, doi), s)


def test_T4a_khai_SAI_kieu_KHOI_CONG_khong_can_he_lai():
    """`hinh_tru: solid` — sai, và **vô hại**. Đây là luật, không phải may.

    `ir_static_check` suy kiểu của vật dựng ra từ CÂU LỆNH dựng
    (`_KIEU_DUNG[k]`), không từ dòng khai báo — quyết định đã có từ sự cố
    `circumsphere`. Nên delta `hinh_tru: solid → curved_solid` trong bản sửa
    `c5b` **không phải** một phần của delta tối thiểu; ghi nó vào bảng delta là
    quy cho hệ một đòi hỏi mà hệ không đặt ra.
    """
    out = verify_and_compile(*_tru_khai({"K": "solid"}))
    assert out.servable
    assert (_gt(out)["W_R"], _gt(out)["W_A"]) == ("9", "81π")


def test_T4b_khai_SAI_kieu_DUONG_TRON_thi_CO_can_he_lai():
    """`C: section` — sai, và **chí mạng**. Bất đối xứng với T4a là có thật.

    `coverage_gate` đọc `memory_declarations` rồi coi đó là toàn bộ chương
    trình (docstring `ir_static_check` §"chỉ coverage_gate…"). Nó thấy `C` là
    `section`, mà `radius` không nhận `section`, nên bác ở
    `structural_coverage` — dù kernel đã dựng ra một `Circle3` thật.

    ⚠️ Đây là MỘT SỰ THẬT ĐƯỢC HAI TẦNG TRẢ LỜI KHÁC NHAU: tầng tĩnh suy kiểu
    từ câu lệnh, cổng phủ tin dòng khai báo. Test này khoá HÀNH VI ĐANG CÓ để
    nó không trôi trong im lặng; nó **không** tuyên bố hành vi ấy là đúng.
    Xem `docs/CURVED_SECTION_RADIUS_PATH_ADJUDICATION.md` §phát hiện phụ.
    """
    out = verify_and_compile(*_tru_khai({"C": "section"}))
    assert not out.servable
    assert out.stage_reached == "structural_coverage"
    assert out.error_code == "requested_operation_uncovered"


@pytest.mark.parametrize("bang,khoa", [
    ("RENDER_HINT", "circle3"), ("_TRUONG", "circle3")])
def test_T5_T6_go_circle3_khoi_scene3d_thi_MAT_VAT(monkeypatch, bang, khoa):
    """Tiêm ⑤⑥ — không có ô trình bày thì đường tròn không tới được học sinh."""
    from app.ai import pipeline
    from app.simulation.semantic_program import scene3d

    hd, spec = _tru(do=("radius", "area"),
                    obl=[{"kind": "radius", "container": "C",
                          "params": {"witness": "W_R"}},
                         {"kind": "area", "container": "C",
                          "params": {"witness": "W_A"}}])
    assert verify_and_compile(hd, spec).servable

    def _co_C(canh):
        for o in (canh or {}).get("objects", []):
            if (o.get("name") or o.get("id")) == "C":
                return o
        return None

    truoc = _co_C(pipeline._dung_scene3d(spec, hd))
    assert truoc is not None and truoc.get("radius_sq") is not None

    d = dict(getattr(scene3d, bang))
    d.pop(khoa)
    monkeypatch.setattr(scene3d, bang, d)
    sau = _co_C(pipeline._dung_scene3d(spec, hd))
    assert sau is None or sau.get("radius_sq") is None


def test_T7_go_chot_VUONG_GOC_TRUC_thi_hệ_phuc_vu_mot_ELIP(monkeypatch):
    """Tiêm ⑦ — không có chốt ⊥ trục, mặt xiên được phục vụ như đường tròn."""
    from app.simulation.geometry import curved as CV

    d, s = _khoi_cat("cylinder", dinh_z=20, vanh_x=9, cat_t="1/2", fid="f")
    d = [x for x in d if x["name"] != "MP"] + [
        {"name": "Q", "type": "point3", "initial_value": [0, 9, 5],
         "source_fact_id": "f"},
        {"name": "MP", "type": "plane3"}]
    s = [x for x in s if x.get("target_var") != "MP"]
    i = next(k for k, x in enumerate(s) if x.get("target_var") == "C")
    s.insert(i, {"kind": "construct_plane", "target_var": "MP",
                 "through": ["P0", "P2", "Q"]})
    hd = _hd_don("Hình trụ bị cắt xiên.", "f",
                 [{"kind": "radius", "container": "C",
                   "params": {"witness": "W_R"}}])
    assert not verify_and_compile(hd, _spec(d, s)).executable

    monkeypatch.setattr(CV, "intersect_plane_curved",
                        _bo_chan(CV.ERR_NGOAI_BAO_DONG))
    assert verify_and_compile(hd, _spec(d, s)).servable


@pytest.mark.parametrize("t,ma", [
    ("2", "CURVED_PLANE_DOES_NOT_CUT"), ("0", "CURVED_PLANE_TANGENT")])
def test_T8_T9_go_chot_MIEN_CAT_thi_he_phuc_vu_thiet_dien_KHONG_CO(
        monkeypatch, t, ma):
    """Tiêm ⑧⑨ — mặt phẳng ngoài khối / qua đỉnh không còn bị từ chối."""
    from app.simulation.geometry import curved as CV

    hd, spec = _non(t=t)
    assert not verify_and_compile(hd, spec).executable

    monkeypatch.setattr(CV, "intersect_plane_curved", _bo_chan(ma))
    assert verify_and_compile(hd, spec).servable


def test_T10_go_TI_LE_DONG_DANG_cua_non_thi_ban_kinh_SAI_MA_XANH(monkeypatch):
    """Tiêm ⑩ — lỗi nguy hiểm nhất: không đỏ ở đâu, chỉ ra số khác.

    Bỏ hệ số `(1−t)²` thì nón trả bán kính ĐÁY cho mọi lát cắt. Không cổng nào
    bắt được, vì kiểu vẫn đúng và chương trình vẫn chạy — chỉ đáp số sai. Đó là
    lý do test khoá GIÁ TRỊ, không khoá riêng `servable`.
    """
    from app.simulation.geometry import curved as CV

    hd, spec = _non()
    assert _gt(verify_and_compile(hd, spec))["W_R"] == "6"

    goc = CV.intersect_plane_curved
    monkeypatch.setattr(CV, "intersect_plane_curved", lambda s, pl: CV.Circle3(
        goc(s, pl).center, s.truc, s.radius_sq))
    out = verify_and_compile(hd, spec)
    assert out.servable and _gt(out)["W_R"] == "10"


def test_T11_bat_bien_radius_sq_duong_la_CHOT_THU_HAI_sau_chot_tiep_xuc(
        monkeypatch):
    """Tiêm ⑪ — hai lớp, và lớp trong CÓ bắt được thứ lớp ngoài để lọt.

    Gỡ chốt tiếp xúc thôi thì `Circle3.__post_init__` vẫn chặn: một hình bán
    kính 0 là một ĐIỂM, và trả nó về dưới kiểu `circle3` là nói dối về kiểu.
    Gỡ nốt bất biến ấy thì hệ phục vụ `r = 0` như một đáp số — xanh, và sai.
    """
    from fractions import Fraction

    from app.simulation.geometry import curved as CV

    hd, spec = _non(t="0")                    # mặt phẳng đi qua ĐỈNH nón
    assert not verify_and_compile(hd, spec).executable

    goc = CV.intersect_plane_curved

    def khong_chot_tiep_xuc(s, pl):
        try:
            return goc(s, pl)
        except Exception as e:                                    # noqa: BLE001
            if getattr(e, "code", None) == CV.ERR_TIEP_XUC:
                return CV.Circle3(s.anchor, s.truc, Fraction(0))
            raise

    monkeypatch.setattr(CV, "intersect_plane_curved", khong_chot_tiep_xuc)
    # Lớp trong đỡ được — vẫn KHÔNG phục vụ.
    assert not verify_and_compile(hd, spec).executable

    monkeypatch.setattr(CV.Circle3, "__post_init__", lambda self: None)
    out = verify_and_compile(hd, spec)
    assert out.servable and _gt(out)["W_R"] == "0"


def test_G_exact_radius_sq_giu_mien_chinh_xac():
    """Tiêm ⑦ — `Circle3` giữ `radius_sq` hữu tỉ, không giữ bán kính."""
    from fractions import Fraction

    from app.simulation.geometry.curved import Circle3
    from app.simulation.geometry.exact import Point3, Vec3

    c = Circle3(Point3(Fraction(0), Fraction(0), Fraction(0)),
                Vec3(Fraction(0), Fraction(0), Fraction(1)), Fraction(81))
    assert c.radius_sq == Fraction(81)
    with pytest.raises(Exception):
        Circle3(Point3(Fraction(0), Fraction(0), Fraction(0)),
                Vec3(Fraction(0), Fraction(0), Fraction(1)), Fraction(0))
