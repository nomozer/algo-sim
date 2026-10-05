# -*- coding: utf-8 -*-
"""regular-square-pyramid-w01 — chóp tứ giác đều qua đúng route sản phẩm. 0 lượt gọi model.

Ca và kỳ vọng ghi TRƯỚC bản sửa ở
`docs/evaluation/geometry/runs/regular-square-pyramid-w01/diagnostics/corpus/LABELS.json`; test đọc nhãn từ đó,
không chép lại. Mỗi ca chạy một chương trình kiểu LLM (điểm khai bằng toạ độ bố cục `LAYOUT_DERIVED`, tâm đáy
dựng bằng giao hai đường chéo, khối, phép đo) qua `verify_and_compile` (`w14_cases.chay`). Builder ở đây cũng là
nguồn fixture trình duyệt (`scripts/generate_generic_tier_a_fixtures.py`).

Phase 1 (trước bản sửa): ca dương thực thi đúng `V = 16` nhưng bị từ chối ở chặng `assumption`
(`TEMPLATE_NOT_MATCHED pyramid: no apex edge stated perpendicular to the base`).
"""
from __future__ import annotations

import json
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.simulation.semantic_program.shape_constraint import doc_rang_buoc, phan_chua_doc
from tests.geometry import w14_cases as W

_CORPUS = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/regular-square-pyramid-w01/diagnostics/corpus"
#: Lớp 1 (`LABELS.json`, trước sản phẩm) + lớp R2 (`LABELS_R2.json`, tự rà soát cuối — cạnh bên gọi bằng tên đoạn,
#: ghi trước bản sửa). Hai lớp không trùng khoá; lớp 1 không đổi.
NHAN = {**json.loads((_CORPUS / "LABELS.json").read_text(encoding="utf-8"))["rows"],
        **json.loads((_CORPUS / "LABELS_R2.json").read_text(encoding="utf-8"))["rows"]}

THE_TICH = "V"
CANH_BEN = "d_SA"


def _so(x: F) -> str:
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def chop_deu(ca: str, *, s: F, dinh: tuple[str, ...] = ("S", "A", "B", "C", "D"), apex: tuple | None = None,
             given: tuple = (), facts: tuple = (), hoi: str = "volume", o_lech: bool = False,
             h: F = F(3), van: str | None = None) -> tuple:
    """(hợp đồng, chương trình) cho đề `NHAN[ca]`: đáy vuông cạnh `s` trên Oxy, đỉnh trên tâm ở độ cao `h`
    (hoặc `apex`), tâm O = giao hai đường chéo (`o_lech`: trung điểm cạnh đầu, sai danh tính), một phép đo hỏi.
    `van` thay đề của ca (fixture trình duyệt: biến thể ngoài corpus, vd cạnh đáy bằng 0)."""
    S, a, b, c, d = dinh
    van = van or NHAN[ca]["text"]
    o = [_so(s / 2), _so(s / 2), _so(h)] if apex is None else [_so(F(x)) for x in apex]
    nghia_vu = ({"kind": "volume", "container": "khoi_chop", "witness": THE_TICH} if hoi == "volume"
                else {"kind": "distance", "container": a, "witness": CANH_BEN, "wrt": S})
    pay = {"input_facts": [{"id": "f_khoi", "kind": "str", "label": "Khối chóp", "value": [f"{S}.{a}{b}{c}{d}"]},
                           *[dict(f) for f in facts]],
           "obligations": [nghia_vu],
           "solid_topology": {"solid_kind": "pyramid", "apex": S, "base_cycle": [a, b, c, d], "base_shape": "square"}}
    t = _so(s)
    mem = [{"name": n, "type": "float", "provenance": "GIVEN", "source_fact_id": f, "initial_value": v}
           for n, f, v in given]
    mem += [{"name": p, "type": "point3", "provenance": "LAYOUT_DERIVED"} for p in dinh]
    mem += [{"name": f"{a}{c}", "type": "line3"}, {"name": f"{b}{d}", "type": "line3"},
            {"name": "O", "type": "point3"}, {"name": f"day_{a}{b}{c}{d}", "type": "polygon3"},
            {"name": "mp_day", "type": "plane3"}, {"name": "khoi_chop", "type": "solid"},
            {"name": f"dien_tich_day_{a}{b}{c}{d}", "type": "float"}, {"name": "chieu_cao_SO", "type": "float"},
            {"name": THE_TICH if hoi == "volume" else CANH_BEN, "type": "float"}]
    o_expr = ({"kind": "midpoint", "a": a, "b": b} if o_lech
              else {"kind": "intersect_line_line", "line_a": f"{a}{c}", "line_b": f"{b}{d}"})
    st = [{"kind": "declare_point", "target_var": a, "at": ["0", "0", "0"]},
          {"kind": "declare_point", "target_var": b, "at": [t, "0", "0"]},
          {"kind": "declare_point", "target_var": c, "at": [t, t, "0"]},
          {"kind": "declare_point", "target_var": d, "at": ["0", t, "0"]},
          {"kind": "construct_polygon", "target_var": f"day_{a}{b}{c}{d}", "vertices": [a, b, c, d],
           "label": f"Đáy {a}{b}{c}{d}"},
          {"kind": "construct_line", "target_var": f"{a}{c}", "through_a": a, "through_b": c},
          {"kind": "construct_line", "target_var": f"{b}{d}", "through_a": b, "through_b": d},
          {"kind": "construct_point", "target_var": "O", "expr": o_expr},
          {"kind": "declare_point", "target_var": S, "at": o},
          {"kind": "construct_solid", "target_var": "khoi_chop", "vertices": [S, a, b, c, d],
           "faces": [[a, b, c, d], [S, a, b], [S, b, c], [S, c, d], [S, d, a]], "label": f"{S}.{a}{b}{c}{d}"},
          {"kind": "construct_plane", "target_var": "mp_day", "through": [a, b, c]},
          {"kind": "assign", "target_var": f"dien_tich_day_{a}{b}{c}{d}",
           "expr": {"kind": "measure", "quantity": "area", "of": f"day_{a}{b}{c}{d}"}},
          {"kind": "assign", "target_var": "chieu_cao_SO",
           "expr": {"kind": "measure", "quantity": "distance", "of": S, "wrt": "mp_day"}}]
    st.append({"kind": "assign", "target_var": THE_TICH,
               "expr": {"kind": "measure", "quantity": "volume", "of": "khoi_chop"}} if hoi == "volume" else
              {"kind": "assign", "target_var": CANH_BEN,
               "expr": {"kind": "measure", "quantity": "distance", "of": S, "wrt": a}})
    prog = {"spec_version": "1.0", "title": f"Chóp tứ giác đều {S}.{a}{b}{c}{d}", "memory_declarations": mem,
            "statements": st}
    return W.hop_dong(van, pay), prog


def _f(fid: str, nhan: str, v: str) -> dict:
    return {"id": fid, "kind": "float", "label": nhan, "value": [v]}


def _do_dai(doan: str, v: str) -> tuple:
    """Dữ kiện độ dài gọi bằng TÊN ĐOẠN (`SA = 3`): GIVEN `<doan>_length`, InputFact nhãn là chính tên đoạn."""
    return ((f"{doan}_length", f"f_{doan.lower()}", v),), (_f(f"f_{doan.lower()}", doan, v),)


CANH_DAY_4 = (("canh_day", "f_canh_day", "4"),), (_f("f_canh_day", "cạnh đáy", "4"),)
CAO_3 = (("chieu_cao", "f_chieu_cao", "3"),), (_f("f_chieu_cao", "chiều cao", "3"),)


def _g(*phan):
    return tuple(x for p in phan for x in p[0]), tuple(x for p in phan for x in p[1])


def _ca(ca: str, **kw):
    g, f = kw.pop("gf", ((), ()))
    return chop_deu(ca, given=g, facts=f, **kw)


CA = {
    "S1_side_height_volume": lambda: _ca("S1_side_height_volume", s=F(4), gf=_g(CANH_DAY_4, CAO_3)),
    "S2_side_apothem_volume": lambda: _ca("S2_side_apothem_volume", s=F(6), h=F(4), gf=_g(
        ((("canh_day", "f_canh_day", "6"),), (_f("f_canh_day", "cạnh đáy", "6"),)),
        ((("trung_doan", "f_trung_doan", "5"),), (_f("f_trung_doan", "trung đoạn", "5"),)))),
    "S3_apothem_phrasing": lambda: _ca("S3_apothem_phrasing", s=F(6), h=F(4), gf=_g(
        ((("canh_day", "f_canh_day", "6"),), (_f("f_canh_day", "cạnh đáy", "6"),)),
        ((("trung_doan", "f_trung_doan", "5"),), (_f("f_trung_doan", "đường cao của mặt bên", "5"),)))),
    "S4_side_lateral_volume": lambda: _ca("S4_side_lateral_volume", s=F(4), h=F(1), gf=_g(
        CANH_DAY_4, ((("canh_ben", "f_canh_ben", "3"),), (_f("f_canh_ben", "cạnh bên", "3"),)))),
    "S5_lateral_edge_length": lambda: _ca("S5_lateral_edge_length", s=F(4), hoi="distance", gf=_g(CANH_DAY_4, CAO_3)),
    "S6_renamed_vertices": lambda: _ca("S6_renamed_vertices", s=F(4), dinh=("S", "M", "N", "P", "Q"),
                                       gf=_g(CANH_DAY_4, CAO_3)),
    "S7_named_centre": lambda: _ca("S7_named_centre", s=F(4), gf=_g(
        ((("AB_length", "f_ab", "4"),), (_f("f_ab", "AB", "4"),)),
        ((("SO_length", "f_so", "3"),), (_f("f_so", "SO", "3"),)))),
    "N1_missing_height": lambda: _ca("N1_missing_height", s=F(4), gf=_g(CANH_DAY_4)),
    "N2_not_regular": lambda: _ca("N2_not_regular", s=F(4), hoi="distance", gf=_g(CANH_DAY_4, CAO_3)),
    "N3_contradiction": lambda: _ca("N3_contradiction", s=F(6), h=F(4), gf=_g(
        ((("canh_day", "f_canh_day", "6"),), (_f("f_canh_day", "cạnh đáy", "6"),)),
        ((("chieu_cao", "f_chieu_cao", "4"),), (_f("f_chieu_cao", "chiều cao", "4"),)))),
    "N4_wrong_centre_identity": lambda: _ca("N4_wrong_centre_identity", s=F(4), o_lech=True, gf=_g(
        ((("AB_length", "f_ab", "4"),), (_f("f_ab", "AB", "4"),)),
        ((("SO_length", "f_so", "3"),), (_f("f_so", "SO", "3"),)))),
    "N5_apex_over_vertex": lambda: _ca("N5_apex_over_vertex", s=F(4), hoi="distance", apex=(0, 0, 3),
                                       gf=_g(CANH_DAY_4, CAO_3)),
    "N6_goal_clause_regular": lambda: _ca("N6_goal_clause_regular", s=F(4), hoi="distance", gf=_g(CANH_DAY_4, CAO_3)),
    "N7_model_only_height": lambda: _ca("N7_model_only_height", s=F(4), gf=_g(CANH_DAY_4, CAO_3)),
    "U1_irrational_height": lambda: _ca("U1_irrational_height", s=F(2), h=F(1), gf=_g(
        ((("canh_day", "f_canh_day", "2"),), (_f("f_canh_day", "cạnh đáy", "2"),)),
        ((("canh_ben", "f_canh_ben", "2"),), (_f("f_canh_ben", "cạnh bên", "2"),)))),
    "U2_angle_data": lambda: _ca("U2_angle_data", s=F(4), gf=_g(CANH_DAY_4)),
    "U3_regular_triangular": None,                       # chương trình riêng (đáy tam giác) — test riêng dưới
    # ── lớp R2: cạnh bên gọi bằng TÊN ĐOẠN (SA, SC) — độ dài server đọc từ đề, không qua cụm "cạnh bên bằng" ──
    "R2_S8_side_AB_lateral_SA": lambda: _ca("R2_S8_side_AB_lateral_SA", s=F(4), h=F(1), gf=_g(
        _do_dai("AB", "4"), _do_dai("SA", "3"))),
    "R2_S9_side_lateral_named": lambda: _ca("R2_S9_side_lateral_named", s=F(4), h=F(1), gf=_g(
        CANH_DAY_4, _do_dai("SA", "3"))),
    "R2_S10_lateral_other_vertex": lambda: _ca("R2_S10_lateral_other_vertex", s=F(4), h=F(1), gf=_g(
        _do_dai("AB", "4"), _do_dai("SC", "3"))),
    "R2_N8_lateral_contradiction": lambda: _ca("R2_N8_lateral_contradiction", s=F(4), h=F(1), gf=_g(
        _do_dai("AB", "4"), _do_dai("SA", "3"), _do_dai("SB", "5"))),
    "R2_N9_contradiction_program_fits_lengths": lambda: _ca(
        "R2_N9_contradiction_program_fits_lengths", s=F(4), apex=(0, 0, 3), gf=_g(
            _do_dai("AB", "4"), _do_dai("SA", "3"), _do_dai("SB", "5"))),
    "R2_U4_irrational_via_lateral": lambda: _ca("R2_U4_irrational_via_lateral", s=F(2), h=F(1), gf=_g(
        _do_dai("AB", "2"), _do_dai("SA", "2"))),
    "R2_L1_chained_equal_lateral_edges": lambda: _ca("R2_L1_chained_equal_lateral_edges", s=F(4), h=F(1), gf=_g(
        _do_dai("AB", "4"), _do_dai("SA", "3"))),
}


def _chop_tam_giac():
    van = NHAN["U3_regular_triangular"]["text"]
    pay = {"input_facts": [_f("f_canh_day", "cạnh đáy", "3"), _f("f_chieu_cao", "chiều cao", "4")],
           "obligations": [{"kind": "volume", "container": "khoi_chop", "witness": THE_TICH}],
           "solid_topology": {"solid_kind": "pyramid", "apex": "S", "base_cycle": ["A", "B", "C"]}}
    mem = [{"name": "canh_day", "type": "float", "provenance": "GIVEN", "source_fact_id": "f_canh_day",
            "initial_value": "3"},
           {"name": "chieu_cao", "type": "float", "provenance": "GIVEN", "source_fact_id": "f_chieu_cao",
            "initial_value": "4"}]
    mem += [{"name": p, "type": "point3", "provenance": "LAYOUT_DERIVED"} for p in "SABC"]
    mem += [{"name": "khoi_chop", "type": "solid"}, {"name": THE_TICH, "type": "float"}]
    st = [{"kind": "declare_point", "target_var": "A", "at": ["0", "0", "0"]},
          {"kind": "declare_point", "target_var": "B", "at": ["3", "0", "0"]},
          {"kind": "declare_point", "target_var": "C", "at": ["3/2", "5/2", "0"]},
          {"kind": "declare_point", "target_var": "S", "at": ["3/2", "5/6", "4"]},
          {"kind": "construct_solid", "target_var": "khoi_chop", "vertices": ["S", "A", "B", "C"],
           "faces": [["A", "B", "C"], ["S", "A", "B"], ["S", "B", "C"], ["S", "C", "A"]], "label": "S.ABC"},
          {"kind": "assign", "target_var": THE_TICH, "expr": {"kind": "measure", "quantity": "volume", "of": "khoi_chop"}}]
    return W.hop_dong(van, pay), {"spec_version": "1.0", "title": "Chóp tam giác S.ABC", "memory_declarations": mem,
                                  "statements": st}


def _nap(ca: str):
    if ca == "U3_regular_triangular":
        return _chop_tam_giac()
    contract, prog = CA[ca]()
    return contract, prog


def ket_qua(ca: str) -> dict:
    """Kết cục route của ca: `served:<giá trị học sinh thấy>` hoặc các trường từ chối."""
    contract, prog = _nap(ca)
    _sp, out, scene = W.chay(contract, prog)
    if out.servable:
        dich = THE_TICH if any(s.get("target_var") == THE_TICH for s in prog["statements"]) else CANH_BEN
        v = next(o for o in scene["objects"] if o["id"] == dich)
        return {"served": v.get("value"), "scene": scene, "out": out}
    return {"stage": out.stage_reached, "reason_code": out.reason_code, "details": out.details, "out": out}


def _khop(ca: str, kq: dict) -> None:
    mong = NHAN[ca]["expect"]
    if mong.startswith("served:"):
        assert kq.get("served") == mong.removeprefix("served:"), (ca, kq.get("stage"), kq.get("reason_code"),
                                                                    kq.get("details"))
        return
    _tc, stage, ma = mong.split(":")
    assert "served" not in kq, (ca, "served", kq.get("served"))
    if stage != "*":
        assert kq["stage"] == stage, (ca, kq["stage"], kq["reason_code"], kq["details"])
    if ma != "*":
        assert kq["reason_code"] == ma, (ca, kq["stage"], kq["reason_code"], kq["details"])


# ── 1. Kết cục route theo nhãn đăng ký trước ─────────────────────────────────────────────────

@pytest.mark.parametrize("ca", sorted(NHAN))
def test_ket_cuc_route_theo_nhan(ca):
    _khop(ca, ket_qua(ca))


# ── 2. Bộ đọc: "đều" là một ràng buộc đọc được, không phải chữ bị nuốt ───────────────────────

def test_doc_chop_tu_giac_deu_va_cac_kich_thuoc():
    rb = {(r.kind, r.entities, r.value) for r in doc_rang_buoc(NHAN["S1_side_height_volume"]["text"])}
    ent = ("S", "A", "B", "C", "D")
    assert ("regular_square_pyramid", ent, None) in rb
    assert ("base_square", ent[1:], F(4)) in rb
    assert ("height", ent, F(3)) in rb
    assert phan_chua_doc(NHAN["S1_side_height_volume"]["text"]) == ()


@pytest.mark.parametrize("ca, kind, value", [
    ("S2_side_apothem_volume", "apothem", F(5)),
    ("S3_apothem_phrasing", "apothem", F(5)),
    ("S4_side_lateral_volume", "lateral_edge", F(3)),
])
def test_doc_trung_doan_va_canh_ben(ca, kind, value):
    rb = {(r.kind, r.entities, r.value) for r in doc_rang_buoc(NHAN[ca]["text"])}
    assert (kind, ("S", "A", "B", "C", "D"), value) in rb
    assert phan_chua_doc(NHAN[ca]["text"]) == ()


def test_chop_day_vuong_khong_deu_khong_thanh_chop_deu():
    """Đáy vuông + chiều cao, KHÔNG có chữ "đều": không phát ràng buộc chóp đều."""
    assert not any(r.kind == "regular_square_pyramid" for r in doc_rang_buoc(NHAN["N2_not_regular"]["text"]))


def test_chung_minh_chop_deu_khong_la_tien_de():
    """'Chứng minh S.ABCD là hình chóp tứ giác đều' là mục tiêu: không là tiền đề của chứng chỉ."""
    from app.simulation.semantic_program.shape_constraint import che_muc_tieu
    de = che_muc_tieu(NHAN["N6_goal_clause_regular"]["text"])
    assert not any(r.kind == "regular_square_pyramid" for r in doc_rang_buoc(de))


def test_tam_giac_deu_khong_bi_doc_thanh_tu_giac_deu():
    assert not any(r.kind == "regular_square_pyramid"
                   for r in doc_rang_buoc(NHAN["U3_regular_triangular"]["text"]))


# ── 3. Ca dương: chứng chỉ, công thức, closure ─────────────────────────────────────────────

def test_ca_duong_mang_chung_chi_C1_chop_deu():
    from app.simulation.semantic_program.assumption_gate import danh_gia_doc_lap
    out = ket_qua("S1_side_height_volume")["out"]
    assert out.servable and out.assumption_certificate == "C1"
    contract, prog = _nap("S1_side_height_volume")
    kq = danh_gia_doc_lap(contract, W.spec_cua(prog))
    assert kq.certificate == "C1" and "C1 T7" in kq.details, kq.details
    assert any(d.startswith("PREMISE regular_square_pyramid(S,A,B,C,D)") for d in kq.details), kq.details


@pytest.mark.parametrize("ca", ["R2_S8_side_AB_lateral_SA", "R2_S10_lateral_other_vertex"])
def test_r2_canh_ben_goi_bang_ten_doan_cho_chieu_cao_T7(ca):
    """Tự rà soát cuối: `SA = 3` (hay `SC = 3`) là CẠNH BÊN của chóp đều — độ dài server tự đọc từ đề (bất biến
    nguồn), cùng hạng với "cạnh bên bằng 3". Trước bản sửa T7 bỏ qua nó: `T7 MISSING chiều cao: CE_INVALID breaks
    |AS| = 3` và đề bị từ chối dù xác định đáp số."""
    from app.simulation.semantic_program.assumption_gate import danh_gia_doc_lap
    contract, prog = _nap(ca)
    kq = danh_gia_doc_lap(contract, W.spec_cua(prog))
    assert kq.certificate == "C1" and "C1 T7" in kq.details, kq.details


def test_r2_hai_canh_ben_khac_nhau_la_mau_thuan_T7():
    """Đề nói chóp ĐỀU mà SA = 3, SB = 5: chương trình khớp mọi độ dài (đỉnh trên A) vẫn bị từ chối, và chứng chỉ
    gọi đúng tên — mâu thuẫn giữa các cạnh bên, không phải "thiếu chiều cao"."""
    from app.simulation.semantic_program.assumption_gate import danh_gia_doc_lap
    contract, prog = _nap("R2_N9_contradiction_program_fits_lengths")
    kq = danh_gia_doc_lap(contract, W.spec_cua(prog))
    assert kq.certificate is None, kq.details
    assert any("TEMPLATE_CONTRADICTION T7" in d and "lateral" in d for d in kq.details), kq.details


def test_cong_thuc_the_tich_tham_chieu_dien_tich_day_va_chieu_cao():
    scene = ket_qua("S1_side_height_volume")["scene"]
    V = next(o for o in scene["objects"] if o["id"] == THE_TICH)
    refs = [r["entity_id"] for r in V["formula"]["references"]]
    assert refs == ["dien_tich_day_ABCD", "chieu_cao_SO"], V.get("formula")
    assert V["formula"]["text"].startswith("V = 1/3 × ")
    so = {e["source_id"] for e in V["dependency_edges"] if e["relation"] == "numerical"}
    assert {"dien_tich_day_ABCD", "chieu_cao_SO"} <= so


@pytest.mark.parametrize("ca", sorted(c for c in NHAN if NHAN[c]["expect"].startswith("served:")))
def test_moi_ca_phuc_vu_qua_duoc_cong_pham_vi(ca):
    """Kết cục `served` của nhãn là kết cục của SẢN PHẨM, không chỉ của route: cổng phạm vi tất định chạy trước
    mọi lượt gọi. Đầu dò cache W1 (`run_pipeline`) bắt được S5 "Tính độ dài cạnh bên SA" bị từ chối ở `scope`
    dù route phục vụ √17 — cổng không có manh mối cho câu hỏi độ dài."""
    from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC, co_duong_thuc_thi

    assert co_duong_thuc_thi(NHAN[ca]["text"], DOMAIN_HINH_HOC), NHAN[ca]["text"]


def _chop_chu_nhat_co_ca_SA_va_khoang_cach():
    """Chương trình kiểu LLM phục vụ được TRƯỚC W1 (CACHE_VERSION 111): chóp đáy chữ nhật, SA ⊥ đáy cho trong
    đề, mô hình vừa khai SA_length vừa đo d(S, (ABC)). Trước W1 công thức là `V = 1/3 × S(ABCD) × SA`."""
    van = ("Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 3, AD = 4, SA vuông góc với mặt phẳng "
           "(ABCD), SA = 6. Tính thể tích khối chóp S.ABCD.")
    pay = {"input_facts": [_f("f_ab", "AB", "3"), _f("f_ad", "AD", "4"), _f("f_sa", "SA", "6")],
           "obligations": [{"kind": "volume", "container": "khoi_chop", "witness": THE_TICH}],
           "solid_topology": {"solid_kind": "pyramid", "apex": "S", "base_cycle": list("ABCD"),
                              "base_shape": "rectangle"}}
    mem = [{"name": n, "type": "float", "provenance": "GIVEN", "source_fact_id": f, "initial_value": v}
           for n, f, v in (("AB_length", "f_ab", "3"), ("AD_length", "f_ad", "4"), ("SA_length", "f_sa", "6"))]
    mem += [{"name": p, "type": "point3", "provenance": "LAYOUT_DERIVED"} for p in "SABCD"]
    mem += [{"name": "day_ABCD", "type": "polygon3"}, {"name": "mp_day", "type": "plane3"},
            {"name": "khoi_chop", "type": "solid"}, {"name": "dt", "type": "float"}, {"name": "h", "type": "float"},
            {"name": THE_TICH, "type": "float"}]
    toa = {"A": "000", "B": "300", "C": "340", "D": "040", "S": "006"}
    st = [{"kind": "declare_point", "target_var": p, "at": list(v)} for p, v in toa.items()]
    st += [{"kind": "construct_polygon", "target_var": "day_ABCD", "vertices": list("ABCD"), "label": "Đáy ABCD"},
           {"kind": "construct_solid", "target_var": "khoi_chop", "vertices": list("SABCD"),
            "faces": [list("ABCD"), list("SAB"), list("SBC"), list("SCD"), list("SDA")], "label": "S.ABCD"},
           {"kind": "construct_plane", "target_var": "mp_day", "through": ["A", "B", "C"]},
           {"kind": "assign", "target_var": "dt", "expr": {"kind": "measure", "quantity": "area", "of": "day_ABCD"}},
           {"kind": "assign", "target_var": "h",
            "expr": {"kind": "measure", "quantity": "distance", "of": "S", "wrt": "mp_day"}},
           {"kind": "assign", "target_var": THE_TICH,
            "expr": {"kind": "measure", "quantity": "volume", "of": "khoi_chop"}}]
    return W.hop_dong(van, pay), {"spec_version": "1.0", "title": "Chóp S.ABCD", "memory_declarations": mem,
                                  "statements": st}


def test_canh_ben_bang_khoang_cach_van_la_chieu_cao_cua_cong_thuc():
    """Hồi quy W1 (đầu dò cache): luật chiều cao ĐO thêm d(S, (ABC)) làm ứng viên thứ hai, và công thức thể
    tích — cần đúng MỘT ứng viên — biến mất. SA bằng khoảng cách từ S tới mặt đáy ⇒ SA là chiều cao: giữ
    công thức trước W1."""
    _sp, out, scene = W.chay(*_chop_chu_nhat_co_ca_SA_va_khoang_cach())
    assert out.servable, (out.stage_reached, out.reason_code, out.details)
    V = next(o for o in scene["objects"] if o["id"] == THE_TICH)
    assert (V.get("formula") or {}).get("text") == "V = 1/3 × S(ABCD) × SA = 24", V.get("formula")


def test_canh_ben_khong_vuong_goc_khong_thanh_chieu_cao_cua_chop_deu():
    """Chóp đều S4 mà mô hình đặt tên cạnh bên là SA_length (= 3, KHÔNG vuông góc đáy): công thức không được
    nói `× SA`; chiều cao là khoảng cách đo được từ S tới mặt đáy."""
    contract, prog = CA["S4_side_lateral_volume"]()
    for m in prog["memory_declarations"]:
        if m["name"] == "canh_ben":
            m["name"] = "SA_length"
    _sp, out, scene = W.chay(contract, prog)
    assert out.servable, (out.stage_reached, out.reason_code, out.details)
    V = next(o for o in scene["objects"] if o["id"] == THE_TICH)
    refs = [r["entity_id"] for r in (V.get("formula") or {}).get("references", [])]
    assert refs == ["dien_tich_day_ABCD", "chieu_cao_SO"], V.get("formula")


def test_du_kien_khong_ten_doan_mang_nhan_cua_fact_de():
    """'cạnh đáy bằng 4' không có tên đoạn; khai báo bộ nhớ không có ô nhãn — học sinh phải đọc 'Cạnh đáy = 4',
    không phải 'đại lượng = 4' (nhãn mượn từ InputFact mà khai báo GIVEN trích dẫn)."""
    scene = ket_qua("S1_side_height_volume")["scene"]
    o = {x["id"]: x for x in scene["objects"]}
    assert (o["canh_day"]["label"], o["canh_day"]["formula"]["text"]) == ("Cạnh đáy", "Cạnh đáy = 4")
    assert o["chieu_cao"]["formula"]["text"] == "Chiều cao = 3"


def test_doi_ten_dinh_van_dung_va_giai_thich_dung():
    scene = ket_qua("S6_renamed_vertices")["scene"]
    V = next(o for o in scene["objects"] if o["id"] == THE_TICH)
    assert V["value"] == "16"
    assert [r["entity_id"] for r in V["formula"]["references"]] == ["dien_tich_day_MNPQ", "chieu_cao_SO"]


def test_tam_O_la_giao_hai_duong_cheo_va_khop_voi_de():
    out = ket_qua("S7_named_centre")["out"]
    assert out.servable and out.construction_binding == {"O": "MATCHED"}
    lech = ket_qua("N4_wrong_centre_identity")["out"]
    assert lech.construction_binding == {"O": "MISMATCHED"}
