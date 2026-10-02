# -*- coding: utf-8 -*-
"""W14 Track A — dựng hình theo LỚP HÌNH (PYRAMID_LIKE / PRISM_LIKE), một đường mã.

Đóng W12-H1/H2: chóp tam giác và lăng trụ tam giác chỉ hiện điểm → đáy → khối.
Vai trò dựng (`formation_roles`) do PRODUCER gắn, từ tô-pô và quan hệ CÓ KIỂU —
không từ nhãn, tên máy, số tham chiếu công thức hay câu chữ đề. Bước bổ sung dựng
hình (`formation.hoan_thien_dung_hinh`) chạy cho MỌI chương trình (compiler lẫn
LLM — S4). 0 lượt gọi model.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib
import json
import re
from pathlib import Path

import pytest

from app.ai.pipeline import _dung_scene3d
from tests.geometry import w14_cases as W

SP = Path(__file__).resolve().parents[2] / "app" / "simulation" / "semantic_program"
CHOP = ["CONSTRUCT_BASE", "CONSTRUCT_HEIGHT", "CONSTRUCT_LATERAL_BOUNDARY", "CLOSE_SOLID"]
LANG_TRU = ["CONSTRUCT_BASE", "CONSTRUCT_TRANSLATED_FACE", "CONSTRUCT_LATERAL_BOUNDARY",
            "CLOSE_SOLID"]
BEN_TAM_GIAC = {
    "chop_tam_giac": [{"S", "A"}, {"S", "B"}, {"S", "C"}],
    "lang_tru_tam_giac": [{"A", "D"}, {"B", "E"}, {"C", "F"}],
}


def _formation():
    return importlib.import_module("app.simulation.semantic_program.formation")


def _canh(scene: dict) -> dict:
    return {frozenset(e["endpoint_ids"]): e["edge_id"] for e in W.khoi(scene)["edge_ownership"]}


def _ho(ten: str):
    _text, ct = W.HO[ten]()
    return ct, W.chuong_trinh(ct)


def _tat_ca_ca() -> list[tuple[str, object, dict]]:
    ra = [(f"ho:{ten}", *_ho(ten)) for ten in sorted(W.HO)]
    for cid in W.GOLD_KHOI_DA_DIEN:
        _t, ct, raw = W.gold(cid)
        ra.append((f"gold:{cid}", ct, raw))
    return ra


# ── W12-H1 / W12-H2: vật dựng phải tồn tại và hiện TRƯỚC khi khép khối ──────

def test_chop_tam_giac_co_doan_duong_cao_SA():
    ct, raw = _ho("chop_tam_giac")
    _sp, out, sc = W.chay(ct, raw)
    assert out.servable, (out.stage_reached, out.reason_code)
    sa = W.vat_theo_dinh(sc, "segment3", {"S", "A"})
    assert sa, "W12-H1: chóp tam giác không có vật đường cao SA"
    assert W.buoc_hien_dau(sc, sa[0]["id"]) < W.buoc_hien_dau(sc, W.khoi(sc)["id"])


def test_chop_tam_giac_co_buoc_canh_ben_truoc_khi_khep():
    ct, raw = _ho("chop_tam_giac")
    _sp, _out, sc = W.chay(ct, raw)
    k = W.buoc_hien_dau(sc, W.khoi(sc)["id"])
    for cap in ({"S", "B"}, {"S", "C"}):
        segs = W.vat_theo_dinh(sc, "segment3", cap)
        assert segs, f"W12-H1: thiếu cạnh bên {sorted(cap)}"
        assert W.buoc_hien_dau(sc, segs[0]["id"]) < k


def test_lang_tru_tam_giac_co_mat_day_tren():
    ct, raw = _ho("lang_tru_tam_giac")
    _sp, _out, sc = W.chay(ct, raw)
    tren = W.vat_theo_dinh(sc, "polygon3", {"D", "E", "F"})
    assert tren, "W12-H2: lăng trụ tam giác không có mặt đáy trên DEF"
    assert W.buoc_hien_dau(sc, tren[0]["id"]) < W.buoc_hien_dau(sc, W.khoi(sc)["id"])


def test_lang_tru_tam_giac_co_buoc_canh_ben():
    ct, raw = _ho("lang_tru_tam_giac")
    _sp, _out, sc = W.chay(ct, raw)
    k = W.buoc_hien_dau(sc, W.khoi(sc)["id"])
    for cap in BEN_TAM_GIAC["lang_tru_tam_giac"]:
        segs = W.vat_theo_dinh(sc, "segment3", cap)
        assert segs, f"W12-H2: thiếu cạnh bên {sorted(cap)}"
        assert W.buoc_hien_dau(sc, segs[0]["id"]) < k


@pytest.mark.parametrize("ho", sorted(BEN_TAM_GIAC))
def test_khep_khoi_sau_day_va_bien_ben(ho):
    ct, raw = _ho(ho)
    _sp, _out, sc = W.chay(ct, raw)
    k = W.buoc_hien_dau(sc, W.khoi(sc)["id"])
    day = W.vat_theo_dinh(sc, "polygon3", {"A", "B", "C"})
    assert day and W.buoc_hien_dau(sc, day[0]["id"]) < k
    for cap in BEN_TAM_GIAC[ho]:
        segs = W.vat_theo_dinh(sc, "segment3", cap)
        assert segs, (ho, sorted(cap))
        assert W.buoc_hien_dau(sc, segs[0]["id"]) < k, (ho, sorted(cap))


# ── Vai trò theo lớp, do producer gắn ───────────────────────────────────────

@pytest.mark.parametrize("ho", sorted(W.HO))
def test_thu_tu_vai_tro_theo_lop_hinh(ho):
    ct, raw = _ho(ho)
    _sp, out, sc = W.chay(ct, raw)
    assert out.servable, (ho, out.stage_reached, out.reason_code)
    lop = W.LOP[ho]
    assert W.khoi(sc).get("shape_class") == lop, ho
    idx = W.thu_tu_vai_tro(sc, CHOP if lop == "PYRAMID_LIKE" else LANG_TRU)
    assert all(i >= 0 for i in idx), (ho, idx)
    a, b, c, d = idx
    assert (a < b <= c < d) if lop == "PYRAMID_LIKE" else (a < b < c < d), (ho, idx)
    assert "DECLARE_ENTITIES" in sc["formation"]["steps"][0].get("formation_roles", []), ho


@pytest.mark.parametrize("ho", sorted(W.HO))
def test_moi_buoc_hinh_hoc_doi_hinh(ho):
    """V1 — GUARD: mỗi bước dựng đổi tập vật hiện hoặc tiến độ thiết diện."""
    ct, raw = _ho(ho)
    _sp, _out, sc = W.chay(ct, raw)
    steps = sc["formation"]["steps"]
    for k in range(1, len(steps)):
        s, p = steps[k], steps[k - 1]
        if s["semantic_kind"] in ("MEASUREMENT", "FINAL_RESULT"):
            continue
        assert (s["visible_ids"] != p["visible_ids"]
                or s["geometry_progress"] != p["geometry_progress"]), (ho, k)


@pytest.mark.parametrize("ho", sorted(W.HO))
def test_loi_ke_compiler_khop_vat(ho):
    """Lời kể của compiler nói "đường cao" thì bước ấy phải dựng một ĐOẠN (W13)."""
    from app.simulation.geometry_compiler import compiler as C
    from app.simulation.geometry_compiler.contract_adapter import build_fact_graph

    ct, _raw = _ho(ho)
    bd = C.bien_dich(build_fact_graph(ct).graph)
    kieu = {d["name"]: d["type"] for d in bd.program["memory_declarations"]}
    for b in bd.construction_steps:
        if "đường cao" in b.mo_ta.lower():
            assert any(kieu.get(o) == "segment3" for o in b.scene_object_ids), (
                ho, b.index, b.mo_ta, b.scene_object_ids)


@pytest.mark.parametrize("ho", sorted(W.HO))
def test_loi_ke_canh_chi_nhac_vat_dang_hien(ho):
    """V3 — GUARD: nhãn một vật hình học xuất hiện trong lời kể ⇒ vật ấy đang hiện."""
    ct, raw = _ho(ho)
    _sp, _out, sc = W.chay(ct, raw)
    nhan = {o["id"]: (o.get("label") or "").lower() for o in sc["objects"]
            if o["type"] in ("segment3", "polygon3", "solid", "section", "plane3")
            and len(o.get("label") or "") >= 4}
    for s in sc["formation"]["steps"]:
        loi = (s["learner_text"] or "").lower()
        for oid, ten in nhan.items():
            if ten in loi:
                assert oid in s["visible_ids"], (ho, s["step_index"], oid, ten)


@pytest.mark.parametrize("ho", sorted(BEN_TAM_GIAC))
def test_canh_ben_tro_ve_canh_chuan_sau_khi_khep(ho):
    """V6 — một cạnh, một chủ hình: đoạn cạnh bên trao quyền vẽ cho cạnh chuẩn của khối."""
    ct, raw = _ho(ho)
    _sp, _out, sc = W.chay(ct, raw)
    canh = _canh(sc)
    for cap in BEN_TAM_GIAC[ho]:
        segs = W.vat_theo_dinh(sc, "segment3", cap)
        assert len(segs) == 1, (ho, sorted(cap), [s["id"] for s in segs])
        assert segs[0].get("boundary_edge_ids") == [canh[frozenset(cap)]], (ho, sorted(cap))


@pytest.mark.parametrize("ho", sorted(W.HO))
def test_buoc_hinh_hoc_co_formation_roles(ho):
    ct, raw = _ho(ho)
    _sp, _out, sc = W.chay(ct, raw)
    for s in sc["formation"]["steps"]:
        assert isinstance(s.get("formation_roles"), list), (ho, s["step_index"])
        if s["semantic_kind"] in ("MEASUREMENT", "FINAL_RESULT"):
            assert s["formation_roles"] == [], (ho, s["step_index"])


_KIEU_HINH = {"solid", "polygon3", "segment3", "line3", "plane3"}


def _doi_ten_may(ct, raw: dict):
    """Đổi TÊN MÁY của vật hình học (không đổi điểm, không đổi đại lượng) bằng song ánh."""
    ten = sorted({d["name"] for d in raw["memory_declarations"] if d["type"] in _KIEU_HINH}
                 | {s["target_var"] for s in raw["statements"]
                    if s.get("kind") == "construct_segment" and s.get("items")})
    m = {t: f"may_{i}" for i, t in enumerate(ten)}

    def walk(x, key=None):
        if isinstance(x, str):
            return x if key in ("kind", "quantity", "curved_kind", "op") else m.get(x, x)
        if isinstance(x, list):
            return [walk(v) for v in x]
        if isinstance(x, dict):
            return {k: walk(v, k) for k, v in x.items()}
        return x

    obs = tuple(o.model_copy(update={"container": m.get(o.container, o.container)})
                for o in ct.obligations)
    return ct.model_copy(update={"obligations": obs}), walk(copy.deepcopy(raw)), m


def test_vai_tro_bat_bien_khi_doi_ten_may():
    for ho in ("chop_tam_giac", "lang_tru_tam_giac", "chop_chu_nhat", "hop_chu_nhat"):
        ct, raw = _ho(ho)
        _sp, _o1, s1 = W.chay(ct, raw)
        ct2, raw2, m = _doi_ten_may(ct, raw)
        _sp2, o2, s2 = W.chay(ct2, raw2)
        assert o2.servable, (ho, o2.stage_reached, o2.reason_code)
        theo_id = {o["id"]: o for o in s2["objects"]}
        for o in s1["objects"]:
            moi = theo_id.get(m.get(o["id"], o["id"]))
            if moi is None:  # vật do bước bổ sung đặt tên theo đỉnh: so theo tô-pô
                cung = [x for x in s2["objects"]
                        if x["type"] == o["type"] and W.dinh_cua(x) == W.dinh_cua(o)]
                assert len(cung) == 1, (ho, o["id"])
                moi = cung[0]
            assert moi["formation_roles"] == o["formation_roles"], (ho, o["id"])
        k1, k2 = W.khoi(s1), W.khoi(s2)
        assert (k1["shape_class"], k1["formation_requirements"]) == (
            k2["shape_class"], k2["formation_requirements"]), ho


# ── Vai trò từ quan hệ CÓ KIỂU: chân đường cao không phải đỉnh đáy ──────────

def _chop_chan_trong(bien_the: str):
    """S.ABC, chân H ở TRONG đáy: `project_onto` của chương trình, hoặc quan hệ hợp đồng."""
    diem = {"A": [0, 0, 0], "B": [4, 0, 0], "C": [0, 4, 0], "S": [1, 1, 3]}
    decl = [W._diem_gia_dinh(n, v) for n, v in diem.items()]
    stm: list[dict] = []
    rel: list[dict] = []
    if bien_the == "project_onto":
        decl += [{"name": "mp_day", "type": "plane3"}, {"name": "H", "type": "point3"}]
        stm += [{"kind": "construct_plane", "target_var": "mp_day", "through": ["A", "B", "C"]},
                {"kind": "construct_point", "target_var": "H",
                 "expr": {"kind": "project_onto", "point": "S", "target": "mp_day"}}]
    else:
        decl.append(W._diem_gia_dinh("H", [1, 1, 0]))
        rel.append({"kind": "perpendicular_line_plane", "line": ["S", "H"],
                    "plane": ["A", "B", "C"], "source_fact_id": "f_cao",
                    "model_assumption": False})
    decl += [{"name": "day_ABC", "type": "polygon3"}, {"name": "khoi", "type": "solid"},
             {"name": "V", "type": "float"}]
    stm += [
        {"kind": "construct_polygon", "target_var": "day_ABC", "vertices": ["A", "B", "C"]},
        {"kind": "construct_solid", "target_var": "khoi", "vertices": ["S", "A", "B", "C"],
         "faces": [["A", "B", "C"], ["S", "A", "B"], ["S", "B", "C"], ["S", "C", "A"]]},
        {"kind": "assign", "target_var": "V",
         "expr": {"kind": "measure", "quantity": "volume", "of": "khoi"}},
    ]
    text = ("Cho hình chóp S.ABC, H là hình chiếu vuông góc của S trên mặt phẳng (ABC). "
            "Tính thể tích khối chóp S.ABC.")
    payload = {"input_facts": [], "geometric_relations": rel,
               "obligations": [{"kind": "volume", "container": "khoi", "witness": "V"}]}
    return W.hop_dong(text, payload), {"spec_version": "1.0", "title": "Chân đường cao trong đáy",
                                       "memory_declarations": decl, "statements": stm}


@pytest.mark.parametrize("bien_the", ["project_onto", "quan_he_hop_dong"])
def test_chan_duong_cao_khong_phai_dinh_day(bien_the):
    F = _formation()
    ct, raw = _chop_chan_trong(bien_the)
    kq = F.hoan_thien_dung_hinh(W.spec_cua(raw), ct)
    sc = _dung_scene3d(kq.spec, ct)
    sh = W.vat_theo_dinh(sc, "segment3", {"S", "H"})
    assert len(sh) == 1, bien_the
    assert sh[0]["formation_roles"] == ["CONSTRUCT_HEIGHT"], bien_the
    for cap in ({"S", "A"}, {"S", "B"}, {"S", "C"}):
        assert W.vat_theo_dinh(sc, "segment3", cap), (bien_the, sorted(cap))
    b, h, l, c = W.thu_tu_vai_tro(sc, CHOP)
    assert 0 <= b < h < l < c, (bien_the, b, h, l, c)


def test_mot_vat_hai_vai_mot_chu_ve():
    """V7 — đường cao trùng cạnh bên SA: MỘT vật, hai vai trò, một chủ nét vẽ."""
    ct, raw = _ho("chop_tam_giac")
    _sp, _out, sc = W.chay(ct, raw)
    sa = W.vat_theo_dinh(sc, "segment3", {"S", "A"})
    assert len(sa) == 1, [o["id"] for o in sa]
    assert {"CONSTRUCT_HEIGHT", "CONSTRUCT_LATERAL_BOUNDARY"} <= set(sa[0]["formation_roles"])
    assert sa[0]["boundary_edge_ids"] == [_canh(sc)[frozenset({"S", "A"})]]


# ── S4: chương trình gold tuyến LLM có khối đa diện ─────────────────────────

def _tien_do_thiet_dien(sc: dict) -> list:
    return [[(g["object_id"], tuple(g["visible_edge_ids"]), g["closed"], g["fill_visible"])
             for g in s["geometry_progress"]]
            for s in sc["formation"]["steps"] if s["geometry_progress"]]


@pytest.mark.parametrize("cid", W.GOLD_KHOI_DA_DIEN)
def test_s4_chuong_trinh_gold_llm_co_khoi(cid):
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
    from app.simulation.semantic_program.scene3d import build_scene3d
    from app.simulation.semantic_program.simulation_state import build_simulation_state

    _text, ct, raw = W.gold(cid)
    sp_goc = W.spec_cua(raw)
    kq_goc = SemanticProgramInterpreter().execute(sp_goc)
    canh_goc = build_scene3d(build_simulation_state(sp_goc, kq_goc, ct))  # KHÔNG bổ sung
    _sp, out, sc = W.chay(ct, raw)
    assert out.servable, (cid, out.stage_reached, out.reason_code)
    k = W.khoi(sc)
    assert k.get("shape_class") == "PYRAMID_LIKE", cid
    can = list(k["formation_requirements"])
    idx = W.thu_tu_vai_tro(sc, can)
    assert all(i >= 0 for i in idx) and idx == sorted(idx), (cid, can, idx)
    for o in ct.obligations:
        w = (o.params or {}).get("witness")
        if w:
            assert repr(out.final_memory.get(w)) == repr(kq_goc.final_memory.get(w)), (cid, w)
    assert _tien_do_thiet_dien(sc) == _tien_do_thiet_dien(canh_goc), cid


# ── Bất biến của bước bổ sung ──────────────────────────────────────────────

def _ket_qua(F, ct, raw) -> frozenset:
    kq = F.hoan_thien_dung_hinh(W.spec_cua(raw), ct)
    sc = _dung_scene3d(kq.spec, ct)
    return frozenset((o["type"], W.dinh_cua(o), tuple(sorted(o.get("formation_roles", []))))
                     for o in sc["objects"] if o["type"] in ("segment3", "polygon3", "solid"))


def _chuong_trinh_vat_muon(an_toan: bool):
    """Chóp tam giác; đáy (an_toan) hoặc nhóm cạnh bên có SM (M dựng SAU khối) đặt sau khối."""
    ct, raw = _ho("chop_tam_giac")
    raw = copy.deepcopy(raw)
    i_khoi = next(i for i, s in enumerate(raw["statements"]) if s["kind"] == "construct_solid")
    if an_toan:
        i_day = next(i for i, s in enumerate(raw["statements"])
                     if s["kind"] == "construct_polygon")
        day = raw["statements"].pop(i_day)
        i_khoi = next(i for i, s in enumerate(raw["statements"]) if s["kind"] == "construct_solid")
        raw["statements"].insert(i_khoi + 1, day)
        return ct, raw
    items = [{"name": f"ben_{a}{b}", "endpoint_a": a, "endpoint_b": b}
             for a, b in (("S", "A"), ("S", "B"), ("S", "C"), ("S", "M"))]
    raw["statements"][i_khoi + 1:i_khoi + 1] = [
        {"kind": "construct_point", "target_var": "M",
         "expr": {"kind": "midpoint", "a": "S", "b": "A"}},
        {"kind": "construct_segment", "target_var": "nhom_ben", "items": items},
    ]
    raw["memory_declarations"] += [{"name": "M", "type": "point3"}] + [
        {"name": it["name"], "type": "segment3"} for it in items]
    return ct, raw


def test_hoan_thien_khong_tao_trung_vat():
    F = _formation()
    ca = _tat_ca_ca() + [("vat_muon_an_toan", *_chuong_trinh_vat_muon(True)),
                         ("vat_muon_khong_an_toan", *_chuong_trinh_vat_muon(False))]
    for ten, ct, raw in ca:
        kq = F.hoan_thien_dung_hinh(W.spec_cua(raw), ct)
        sc = _dung_scene3d(kq.spec, ct)
        thay: dict = {}
        for o in sc["objects"]:
            if o["type"] in ("segment3", "polygon3"):
                khoa = (o["type"], W.dinh_cua(o))
                assert khoa not in thay, (ten, o["id"], thay.get(khoa))
                thay[khoa] = o["id"]


def test_vat_dung_muon_khong_tinh_truoc_khi_khep():
    F = _formation()
    # (a) đáy dựng sau khối, mọi toán hạng có trước khối ⇒ dời an toàn
    ct, raw = _chuong_trinh_vat_muon(True)
    kq = F.hoan_thien_dung_hinh(W.spec_cua(raw), ct)
    assert "LATE_OBJECT_MOVED" in dict(kq.trang_thai_theo_khoi).values()
    sc = _dung_scene3d(kq.spec, ct)
    idx = W.thu_tu_vai_tro(sc, CHOP)
    assert all(i >= 0 for i in idx) and idx[0] < idx[1] <= idx[2] < idx[3], idx
    # (b) nhóm cạnh bên có SM, M dựng SAU khối ⇒ không dời được ⇒ PARTIAL, không chèn trùng
    ct, raw = _chuong_trinh_vat_muon(False)
    kq = F.hoan_thien_dung_hinh(W.spec_cua(raw), ct)
    assert "PARTIAL_LATE_OBJECT" in dict(kq.trang_thai_theo_khoi).values()
    sc = _dung_scene3d(kq.spec, ct)
    for cap in ({"S", "A"}, {"S", "B"}, {"S", "C"}):
        assert len(W.vat_theo_dinh(sc, "segment3", cap)) == 1, sorted(cap)
    ben, khep = W.thu_tu_vai_tro(sc, ["CONSTRUCT_LATERAL_BOUNDARY", "CLOSE_SOLID"])
    assert ben > khep, "vật dựng muộn không được tính là xong vai trò trước khi khép khối"


def _hoan_vi(raw: dict) -> list[dict]:
    """Đổi thứ tự `vertices`, thứ tự mặt và đỉnh mở đầu của từng mặt (mặt viết bằng TÊN)."""
    ra = []
    for cach in range(3):
        r = copy.deepcopy(raw)
        for s in r["statements"]:
            if s["kind"] != "construct_solid":
                continue
            v = list(s["vertices"])
            s["vertices"] = v[::-1] if cach == 0 else v[1:] + v[:1]
            mat = [list(f) for f in s["faces"]]
            mat = mat[::-1] if cach != 1 else mat[1:] + mat[:1]
            s["faces"] = [f[1:] + f[:1] if cach != 2 else f[2:] + f[:2] for f in mat]
        ra.append(r)
    return ra


def _bo_to_po_va_quan_he(payload: dict) -> dict:
    p = copy.deepcopy(payload)
    p.pop("solid_topology", None)
    p["geometric_relations"] = []
    return p


def _mo_ho() -> list[tuple[str, object, dict]]:
    """Tứ diện, lăng trụ tam giác, lập phương — không tô-pô hợp đồng, không quan hệ đường cao."""
    from tests.geometry import test_cuboid_cube_production_route as Q
    from tests.geometry import test_source_grounding_closure as T

    ra = []
    t, p = W.CHOP_TAM_GIAC_TEXT, W.chop_tam_giac_payload()
    ra.append(("tu_dien", W.hop_dong(t, _bo_to_po_va_quan_he(p)),
               W.chuong_trinh(W.hop_dong(t, p))))
    ra.append(("lang_tru_tam_giac", W.hop_dong(T.PRISM_TEXT, _bo_to_po_va_quan_he(T._prism_payload())),
               W.chuong_trinh(T._contract(T.PRISM_TEXT, T._prism_payload()))))
    t, p = Q._cube_p01_payload()
    ra.append(("lap_phuong", W.hop_dong(t, _bo_to_po_va_quan_he(p)), W.chuong_trinh(W.hop_dong(t, p))))
    return ra


def test_hoan_thien_bat_bien_thu_tu_dinh_va_mat():
    F = _formation()
    ct, raw = _ho("chop_tam_giac")
    goc = _ket_qua(F, ct, raw)
    for r in _hoan_vi(raw):
        assert _ket_qua(F, ct, r) == goc
    for ten, ct2, raw2 in _mo_ho():
        for r in [raw2, *_hoan_vi(raw2)]:
            kq = F.hoan_thien_dung_hinh(W.spec_cua(r), ct2)
            assert set(dict(kq.trang_thai_theo_khoi).values()) == {"AMBIGUOUS_TOPOLOGY"}, ten


def test_hoan_thien_doi_ten_bien():
    F = _formation()
    ct, raw = _ho("lang_tru_tam_giac")
    m = {"A": "P", "B": "Q", "C": "R", "D": "X", "E": "Y", "F": "Z"}
    ten = sorted({d["name"] for d in raw["memory_declarations"]} - set(m))
    m.update({t: f"bien_{i}" for i, t in enumerate(ten)})

    def walk(x, key=None):
        if isinstance(x, str):
            return x if key in ("kind", "quantity", "op", "title", "label") else m.get(x, x)
        if isinstance(x, list):
            return [walk(v) for v in x]
        if isinstance(x, dict):
            return {k: walk(v, k) for k, v in x.items()}
        return x

    topo = ct.solid_topology
    topo2 = topo.model_copy(update={
        "base_cycle": tuple(m[v] for v in topo.base_cycle),
        "top_cycle": tuple(m[v] for v in topo.top_cycle),
        "correspondence": tuple((m[a], m[b]) for a, b in topo.correspondence)})
    rel2 = tuple(r.model_copy(update={"line": tuple(m[v] for v in r.line),
                                      "other_line": tuple(m[v] for v in r.other_line),
                                      "plane": tuple(m[v] for v in r.plane)})
                 for r in ct.geometric_relations)
    obs2 = tuple(o.model_copy(update={"container": m.get(o.container, o.container),
                                      "params": {k: m.get(v, v) if isinstance(v, str) else v
                                                 for k, v in (o.params or {}).items()}})
                 for o in ct.obligations)
    ct2 = ct.model_copy(update={"solid_topology": topo2, "geometric_relations": rel2,
                                "obligations": obs2})
    r1 = _ket_qua(F, ct, raw)
    r2 = _ket_qua(F, ct2, walk(copy.deepcopy(raw)))
    assert r2 == frozenset((k, frozenset(m.get(v, v) for v in s), roles) for k, s, roles in r1)


@pytest.mark.parametrize("mat", [
    [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 9]],   # chỉ số ngoài miền
    [[1, 2, 3], [0, 1], [0, 2, 3], [0, 3, 1]],      # mặt < 3 đỉnh
], ids=["chi_so_ngoai_mien", "mat_duoi_3_dinh"])
def test_bang_mat_hong_tu_choi_co_cau_truc(mat):
    from app.simulation.semantic_program.route import verify_and_compile

    ct, raw = _ho("chop_tam_giac")
    for s in raw["statements"]:
        if s["kind"] == "construct_solid":
            s["faces"] = mat
    out = verify_and_compile(ct, W.spec_cua(raw))
    assert not out.servable
    assert out.stage_reached == "formation", out.stage_reached
    assert out.reason_code == "SOLID_TOPOLOGY_MALFORMED", out.reason_code


@pytest.mark.parametrize("mat", [
    [["A", "B", "C"], ["S", "A", "X"], ["S", "B", "C"], ["S", "C", "A"]],   # tên lạ
    [["A", "B", "C"], ["S", "A", "A"], ["S", "B", "C"], ["S", "C", "A"]],   # đỉnh lặp
], ids=["ten_la", "dinh_lap"])
def test_bang_mat_hong_bi_luoc_do_chan(mat):
    """GUARD: hai dạng hỏng này đã bị lược đồ chặn (`canonical_face_indices`)."""
    from app.simulation.semantic_program.validator import validate_semantic_program

    _ct, raw = _ho("chop_tam_giac")
    for s in raw["statements"]:
        if s["kind"] == "construct_solid":
            s["vertices"] = ["S", "A", "B", "C"]
            s["faces"] = mat
    assert not validate_semantic_program(raw).ok


def test_bang_mat_hong_qua_api_khong_500(monkeypatch):
    """GUARD: chương trình mô hình với bảng mặt hỏng ⇒ HTTP 200, `unsupported`, không 500."""
    from fastapi.testclient import TestClient

    from app.ai import pipeline as PL
    from app.main import app
    from app.persistence.db import init_db

    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")
    monkeypatch.delenv("GEOMETRY_COMPILER_MODE", raising=False)
    init_db()
    ct, raw = _ho("chop_tam_giac")
    for s in raw["statements"]:
        if s["kind"] == "construct_solid":
            s["faces"] = [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 9]]
    text = W.CHOP_TAM_GIAC_TEXT + " (W14 bảng mặt hỏng qua API)"
    tra_loi = [json.dumps(W.chop_tam_giac_payload()), json.dumps(raw, default=str)]

    async def fake_transport(*_a, **_k):
        tra_loi.append(tra_loi[-1])
        return tra_loi.pop(0)

    monkeypatch.setattr(PL, "call_gemini", fake_transport)
    res = TestClient(app).post("/api/analyze", json={"input": {"type": "text", "content": text}})
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "unsupported", res.json().get("status")


def _canon_sha(sp) -> str:
    return hashlib.sha256(json.dumps(sp.model_dump(mode="json"), sort_keys=True,
                                     ensure_ascii=False, separators=(",", ":")
                                     ).encode("utf-8")).hexdigest()


def test_hoan_thien_giu_nguyen_ban_goc_va_dap_so():
    from app.simulation.semantic_program.ir_static_check import kiem_tinh

    F = _formation()
    for ten, ct, raw in _tat_ca_ca():
        sp = W.spec_cua(raw)
        truoc = sp.model_dump(mode="json")
        kq = F.hoan_thien_dung_hinh(sp, ct)
        assert sp.model_dump(mode="json") == truoc, ten
        assert kq.sha_goc == _canon_sha(sp), ten
        assert kq.sha_hoan_thien == _canon_sha(kq.spec), ten
        moi = kq.spec.model_dump(mode="json")
        for st in truoc["statements"]:
            assert st in moi["statements"], (ten, st.get("target_var"))
        for d in truoc["memory_declarations"]:
            assert d in moi["memory_declarations"], (ten, d["name"])
        m1, m2 = W.bo_nho_cuoi(sp), W.bo_nho_cuoi(kq.spec)
        for d in truoc["memory_declarations"]:
            assert repr(m1.get(d["name"])) == repr(m2.get(d["name"])), (ten, d["name"])
        assert kiem_tinh(kq.spec).ok, ten


def test_hoan_thien_bat_bien_lap():
    F = _formation()
    for ten, ct, raw in _tat_ca_ca():
        a = F.hoan_thien_dung_hinh(W.spec_cua(raw), ct)
        b = F.hoan_thien_dung_hinh(a.spec, ct)
        assert b.spec.model_dump(mode="json") == a.spec.model_dump(mode="json"), ten


def _bat_dien() -> dict:
    """Bát diện đều — 6 đỉnh, 8 mặt tam giác: không chóp, không lăng trụ."""
    diem = {"P": [1, 0, 0], "Q": [-1, 0, 0], "R": [0, 1, 0], "T": [0, -1, 0],
            "U": [0, 0, 1], "V": [0, 0, -1]}
    mat = [["P", "R", "U"], ["R", "Q", "U"], ["Q", "T", "U"], ["T", "P", "U"],
           ["R", "P", "V"], ["Q", "R", "V"], ["T", "Q", "V"], ["P", "T", "V"]]
    return {"spec_version": "1.0", "title": "Bát diện",
            "memory_declarations": [W._diem_gia_dinh(n, v) for n, v in diem.items()]
            + [{"name": "bat_dien", "type": "solid"}, {"name": "V", "type": "float"}],
            "statements": [
                {"kind": "construct_solid", "target_var": "bat_dien",
                 "vertices": list(diem), "faces": mat},
                {"kind": "assign", "target_var": "V",
                 "expr": {"kind": "measure", "quantity": "volume", "of": "bat_dien"}}]}


def test_hoan_thien_khong_dung_khoi_khong_phan_loai():
    from scripts import build_geometry_samples as B

    F = _formation()
    for raw in (B.chuong_trinh_cau_the_tich(), B.chuong_trinh_non_duong_sinh(), _bat_dien()):
        sp = W.spec_cua(raw)
        kq = F.hoan_thien_dung_hinh(sp, None)
        assert kq.spec.model_dump(mode="json") == sp.model_dump(mode="json"), raw["title"]


def test_hoan_thien_giu_31_va_ngan_sach():
    from app.simulation.semantic_program.pacer import DEFAULT_PRESENTATION_BUDGET

    _formation()
    for ten, ct, raw in _tat_ca_ca():
        _sp, out, sc = W.chay(ct, raw)
        assert out.servable, (ten, out.stage_reached, out.reason_code)
        assert out.frame_count == len(sc["formation"]["steps"]), ten
        assert out.frame_count <= DEFAULT_PRESENTATION_BUDGET, ten


@pytest.mark.parametrize("vi_tri", ["dung_sau_khoi", "khong_khai"])
def test_chan_cao_chua_dung_thi_khong_chen(vi_tri):
    """Review Focus 3: quan hệ nói SH ⊥ (ABC) nhưng H chưa có trước khối ⇒ không chèn."""
    F = _formation()
    ct, raw = _chop_chan_trong("quan_he_hop_dong")
    raw["memory_declarations"] = [d for d in raw["memory_declarations"] if d["name"] != "H"]
    if vi_tri == "dung_sau_khoi":
        raw["memory_declarations"].append({"name": "H", "type": "point3"})
        raw["statements"].append({"kind": "construct_point", "target_var": "H",
                                  "expr": {"kind": "midpoint", "a": "B", "b": "C"}})
    kq = F.hoan_thien_dung_hinh(W.spec_cua(raw), ct)
    sc = _dung_scene3d(kq.spec, ct)
    assert not W.vat_theo_dinh(sc, "segment3", {"S", "H"}), vi_tri
    assert all("CONSTRUCT_HEIGHT" not in o.get("formation_roles", []) for o in sc["objects"])


# ── Khoá kiến trúc ──────────────────────────────────────────────────────────

def test_planner_khong_re_nhanh_theo_ho():
    from app.simulation.geometry_compiler.compiler import SUPPORTED_FAMILIES

    tep = [SP / "formation.py", SP / "solid_faces.py"]
    for f in tep:
        assert f.exists(), f
    cam_ten = {"family_id", "solid_subkind", "variant", "title", "problem_text", "base_shape"}
    cam_chuoi = set(SUPPORTED_FAMILIES) | {"cuboid", "cube", "right_square_prism"}
    cam_khoa = {"label", "learner_text", "notation", "reference", "role", "title"}
    for f in tep:
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Name):
                assert n.id not in cam_ten and not n.id.startswith("SUPPORTED_FAMILY"), (f.name, n.id)
            elif isinstance(n, ast.Attribute):
                assert n.attr not in cam_ten, (f.name, n.attr)
            elif isinstance(n, ast.Constant) and isinstance(n.value, str):
                assert n.value not in cam_chuoi and not n.value.endswith("_length"), (f.name, n.value)
            elif isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant):
                assert n.slice.value not in cam_khoa, (f.name, n.slice.value)
            elif (isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "get"
                  and n.args and isinstance(n.args[0], ast.Constant)):
                assert n.args[0].value not in cam_khoa, (f.name, n.args[0].value)


def test_solid_faces_la_la():
    f = SP / "solid_faces.py"
    assert f.exists(), f
    for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
        if isinstance(n, ast.ImportFrom):
            assert n.level == 0 and not (n.module or "").startswith("app"), n.module
        elif isinstance(n, ast.Import):
            assert not any(a.name.startswith("app") for a in n.names)


def test_phan_loai_khoi_khong_doi_sau_khi_tach():
    """GUARD: `display_names._phan_loai_khoi` trả đúng như trước khi tách (đặc tả chụp trước)."""
    from app.simulation.semantic_program.display_names import _phan_loai_khoi

    goc = json.loads((Path(__file__).parent / "fixtures" / "w14_phan_loai_khoi_truoc.json")
                     .read_text(encoding="utf-8"))["rows"]
    nay = []
    for case_id, sp in W.nguon_khoi():
        for ten, gt in W.bo_nho_cuoi(sp).items():
            if type(gt).__name__ != "Polyhedron":
                continue
            k = _phan_loai_khoi(list(gt.vertices), [list(f) for f in gt.faces])
            nay.append({"case": case_id, "solid": ten,
                        "result": None if k is None else [k[0], list(k[1]), list(k[2])]})
    assert nay == goc


def test_vai_tro_dong_bo_tu_vung():
    F = _formation()
    cay = ast.parse((SP / "scene3d.py").read_text(encoding="utf-8"))
    lit = {n.value for n in ast.walk(cay) if isinstance(n, ast.Constant)
           and isinstance(n.value, str)
           and re.fullmatch(r"(CONSTRUCT|CLOSE|DECLARE)_[A-Z_]+", n.value)}
    assert lit <= set(F.VAI_TRO), lit - set(F.VAI_TRO)


def test_vai_tro_harness_dong_bo():
    """Harness (bộ chấm độ phủ vai trò, bộ dựng ảnh bằng chứng) dùng ĐÚNG từ vựng của
    `formation`; và mọi vai trò có tên người xem — vai trò mới không lên ảnh dạng token."""
    F = _formation()
    goc = Path(__file__).resolve().parents[3]
    tep = [goc / "frontend" / "scripts" / "compiler-scene-replay-lib.mjs",
           goc / "backend" / "scripts" / "build_scene3d_visual_evidence.py"]
    token = {t for f in tep for t in re.findall(r"\b(?:CONSTRUCT|CLOSE|DECLARE)_[A-Z_]*[A-Z]\b",
                                                 f.read_text(encoding="utf-8"))}
    assert token and token <= set(F.VAI_TRO), token - set(F.VAI_TRO)
    gan = next(n for n in ast.walk(ast.parse(tep[1].read_text(encoding="utf-8")))
               if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", None) == "TEN_VAI_TRO")
    assert {k.value for k in gan.value.keys} == set(F.VAI_TRO)
