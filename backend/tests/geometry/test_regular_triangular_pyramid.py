# -*- coding: utf-8 -*-
"""regular-triangular-pyramid-w01 — chóp tam giác đều và tứ diện đều qua đúng route sản phẩm. 0 lượt gọi model.

Ca và kỳ vọng ghi TRƯỚC bản sửa ở
`docs/evaluation/geometry/runs/regular-triangular-pyramid-w01/diagnostics/corpus/LABELS.json`; test đọc nhãn từ đó,
không chép lại. Mỗi ca chạy một chương trình kiểu LLM (đáy tam giác đều đặt trên mặt nghiêng x+y+z=k bằng toạ độ bố
cục `LAYOUT_DERIVED`, trọng tâm dựng bằng giao hai trung tuyến, khối, phép đo) qua `verify_and_compile`
(`w14_cases.chay`). Luật: `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §18. Builder ở đây cũng là nguồn
fixture trình duyệt (`scripts/generate_generic_tier_a_fixtures.py`).
"""
from __future__ import annotations

import itertools
import json
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.simulation.semantic_program.shape_constraint import doc_rang_buoc, phan_chua_doc
from tests.geometry import w14_cases as W

_CORPUS = (Path(__file__).resolve().parents[3]
           / "docs/evaluation/geometry/runs/regular-triangular-pyramid-w01/diagnostics/corpus")
NHAN = json.loads((_CORPUS / "LABELS.json").read_text(encoding="utf-8"))["rows"]

THE_TICH = "V"
CANH_BEN = "d_SA"


def _so(x: F) -> str:
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def khung(ten: str, k: F) -> tuple[tuple[F, F, F], ...]:
    """Ba đỉnh đáy tam giác đều trên mặt ⊥ (1,1,1) — §18.2: N1 cạnh² = 2k², N3 cạnh² = 6k²."""
    if ten == "N1":
        return (k, F(0), F(0)), (F(0), k, F(0)), (F(0), F(0), k)
    return (k, -k, F(0)), (F(0), k, -k), (-k, F(0), k)


def chop_deu(ca: str, *, k: F = F(3), t: F = F(1), frame: str = "N1", dinh: tuple[str, ...] = ("S", "A", "B", "C"),
             apex: tuple | None = None, day: tuple | None = None, given: tuple = (), facts: tuple = (),
             hoi: str = "volume", trong_tam: str = "trung_tuyen", van: str | None = None,
             ky_hieu_khoi: str | None = None) -> tuple:
    """(hợp đồng, chương trình) cho đề `NHAN[ca]`: đáy theo khung `frame` (hoặc `day` cho sẵn), đỉnh trên trọng tâm
    ở `t(1,1,1)` (hoặc `apex`), trọng tâm G = giao hai trung tuyến (`trong_tam="trung_diem_BC"`: trung điểm BC — sai
    danh tính), một phép đo hỏi. `van` thay đề (fixture trình duyệt)."""
    S, a, b, c = dinh
    van = van or NHAN[ca]["text"]
    P = day or khung(frame, k)
    G = tuple(sum(p[i] for p in P) / 3 for i in range(3))
    dinh_S = apex or tuple(g + t for g in G)
    khoi = ky_hieu_khoi or f"{S}.{a}{b}{c}"
    nghia_vu = ({"kind": "volume", "container": "khoi_chop", "witness": THE_TICH} if hoi == "volume"
                else {"kind": "distance", "container": a, "witness": CANH_BEN, "wrt": S})
    pay = {"input_facts": [{"id": "f_khoi", "kind": "str", "label": "Khối chóp", "value": [khoi]},
                           *[dict(f) for f in facts]],
           "obligations": [nghia_vu],
           "solid_topology": {"solid_kind": "pyramid", "apex": S, "base_cycle": [a, b, c]}}
    mem = [{"name": n, "type": "float", "provenance": "GIVEN", "source_fact_id": f, "initial_value": v}
           for n, f, v in given]
    mem += [{"name": p, "type": "point3", "provenance": "LAYOUT_DERIVED"} for p in dinh]
    mem += [{"name": "I", "type": "point3"}, {"name": "J", "type": "point3"}, {"name": f"{a}I", "type": "line3"},
            {"name": f"{b}J", "type": "line3"}, {"name": "G", "type": "point3"},
            {"name": f"day_{a}{b}{c}", "type": "polygon3"}, {"name": "mp_day", "type": "plane3"},
            {"name": "khoi_chop", "type": "solid"}, {"name": f"dien_tich_day_{a}{b}{c}", "type": "float"},
            {"name": "chieu_cao_SG", "type": "float"},
            {"name": THE_TICH if hoi == "volume" else CANH_BEN, "type": "float"}]
    st = [{"kind": "declare_point", "target_var": n, "at": [_so(x) for x in p]} for n, p in zip((a, b, c), P)]
    st += [{"kind": "construct_polygon", "target_var": f"day_{a}{b}{c}", "vertices": [a, b, c],
            "label": f"Đáy {a}{b}{c}"},
           {"kind": "construct_point", "target_var": "I", "expr": {"kind": "midpoint", "a": b, "b": c}},
           {"kind": "construct_line", "target_var": f"{a}I", "through_a": a, "through_b": "I"},
           {"kind": "construct_point", "target_var": "J", "expr": {"kind": "midpoint", "a": c, "b": a}},
           {"kind": "construct_line", "target_var": f"{b}J", "through_a": b, "through_b": "J"},
           {"kind": "construct_point", "target_var": "G",
            "expr": ({"kind": "intersect_line_line", "line_a": f"{a}I", "line_b": f"{b}J"} if trong_tam == "trung_tuyen"
                     else {"kind": "midpoint", "a": b, "b": c})},
           {"kind": "declare_point", "target_var": S, "at": [_so(F(x)) for x in dinh_S]},
           {"kind": "construct_solid", "target_var": "khoi_chop", "vertices": [S, a, b, c],
            "faces": [[a, b, c], [S, a, b], [S, b, c], [S, c, a]], "label": khoi},
           {"kind": "construct_plane", "target_var": "mp_day", "through": [a, b, c]},
           {"kind": "assign", "target_var": f"dien_tich_day_{a}{b}{c}",
            "expr": {"kind": "measure", "quantity": "area", "of": f"day_{a}{b}{c}"}},
           {"kind": "assign", "target_var": "chieu_cao_SG",
            "expr": {"kind": "measure", "quantity": "distance", "of": S, "wrt": "mp_day"}}]
    st.append({"kind": "assign", "target_var": THE_TICH,
               "expr": {"kind": "measure", "quantity": "volume", "of": "khoi_chop"}} if hoi == "volume" else
              {"kind": "assign", "target_var": CANH_BEN, "expr": {"kind": "measure", "quantity": "distance", "of": S,
                                                                   "wrt": a}})
    prog = {"spec_version": "1.0", "title": f"Chóp tam giác đều {khoi}", "memory_declarations": mem, "statements": st}
    return W.hop_dong(van, pay), prog


def _f(fid: str, nhan: str, v: str) -> dict:
    return {"id": fid, "kind": "float", "label": nhan, "value": [v]}


def _g(*cap: tuple[str, str, str]) -> dict:
    """`(tên GIVEN, nhãn fact, giá trị)` → given + facts; nhãn là tên đoạn (`SA`) hoặc cụm (`cạnh đáy`)."""
    given = tuple((n, f"f_{n}", v) for n, _nhan, v in cap)
    return {"given": given, "facts": tuple(_f(f"f_{n}", nhan, v) for n, nhan, v in cap)}


DAY = ("canh_day", "cạnh đáy", "3√2")
CAO = ("chieu_cao", "chiều cao", "√3")
BEN = ("canh_ben", "cạnh bên", "3")
TU_DIEN = dict(t=F(2))
#: Đáy "tự chọn" của mô hình khi cạnh hữu tỉ (không đều — không có tam giác đều hữu tỉ cạnh 3).
DAY_HUU_TI = ((F(0), F(0), F(0)), (F(3), F(0), F(0)), (F(3, 2), F(5, 2), F(0)))
#: Tam giác đều HỮU TỈ cạnh² 14 trên mặt ⊥ (1,1,1) — có thật, nhưng ngoài hai khung chính tắc của §18.2 (U4).
DAY_14 = ((F(0), F(0), F(0)), (F(3), F(-2), F(-1)), (F(1), F(-3), F(2)))

CA = {
    "P1_side_height": lambda: chop_deu("P1_side_height", **_g(DAY, CAO)),
    "P2_side_lateral": lambda: chop_deu("P2_side_lateral", **_g(DAY, BEN)),
    "P3_tetrahedron": lambda: chop_deu("P3_tetrahedron", dinh=("A", "B", "C", "D"), ky_hieu_khoi="ABCD", **TU_DIEN,
                                       **_g(("canh", "cạnh", "3√2"))),
    "P4_all_edges_equal": lambda: chop_deu("P4_all_edges_equal", **TU_DIEN, **_g(("canh", "cạnh", "3√2"))),
    "P5_equal_chains": lambda: chop_deu("P5_equal_chains", **_g(("AB_length", "AB", "3√2"), ("SA_length", "SA", "3"))),
    "P6_base_equilateral_phrase": lambda: chop_deu("P6_base_equilateral_phrase", **_g(DAY, ("SA_length", "SA", "3"))),
    "P7_renamed_vertices": lambda: chop_deu("P7_renamed_vertices", dinh=("M", "N", "P", "Q"), **_g(DAY, CAO)),
    "P8_phrasing_variant": lambda: chop_deu("P8_phrasing_variant", **_g(DAY, CAO)),
    "P9_named_centroid": lambda: chop_deu("P9_named_centroid", **_g(DAY, ("SG_length", "SG", "√3"))),
    "P10_frame_six": lambda: chop_deu("P10_frame_six", frame="N3", k=F(2),
                                      **_g(("canh_day", "cạnh đáy", "2√6"), CAO)),
    "P11_lateral_length": lambda: chop_deu("P11_lateral_length", hoi="distance", **_g(DAY, CAO)),
    "N1_missing_height": lambda: chop_deu("N1_missing_height", **_g(DAY)),
    "N2_contradiction": lambda: chop_deu("N2_contradiction", **_g(DAY, BEN, ("chieu_cao", "chiều cao", "2"))),
    "N3_lateral_mixed": lambda: chop_deu("N3_lateral_mixed", **_g(DAY, ("SA_length", "SA", "3"))),
    "N4_declared_value_conflict": lambda: chop_deu("N4_declared_value_conflict",
                                                   **_g(("AB_length", "AB", "3√2"), ("SA_length", "SA", "4"))),
    "N5_apex_over_vertex": lambda: chop_deu("N5_apex_over_vertex", apex=(4, 1, 1), **_g(DAY, CAO)),
    "N5b_apex_off_normal": lambda: chop_deu("N5b_apex_off_normal", apex=(2, 2, 0), **_g(DAY, CAO)),
    "N6_wrong_centroid_identity": lambda: chop_deu("N6_wrong_centroid_identity", trong_tam="trung_diem_BC",
                                                   **_g(DAY, ("SG_length", "SG", "√3"))),
    "N7_layout_as_data": lambda: chop_deu("N7_layout_as_data"),
    "N8_equal_laterals_base_not_stated": lambda: chop_deu("N8_equal_laterals_base_not_stated",
                                                          **_g(("SA_length", "SA", "3"), ("AB_length", "AB", "3√2"))),
    "N9_regular_is_not_tetrahedron": lambda: chop_deu("N9_regular_is_not_tetrahedron", **TU_DIEN, **_g(DAY)),
    "U1_rational_side": lambda: chop_deu("U1_rational_side", day=DAY_HUU_TI, apex=(F(3, 2), F(5, 6), 2),
                                         **_g(("canh_day", "cạnh đáy", "3"), ("chieu_cao", "chiều cao", "2"))),
    "U2_rational_tetrahedron": lambda: chop_deu("U2_rational_tetrahedron", dinh=("A", "B", "C", "D"),
                                                ky_hieu_khoi="ABCD", day=DAY_HUU_TI, apex=(F(3, 2), F(5, 6), 2),
                                                **_g(("canh", "cạnh", "3"))),
    "U3_height_outside_domain": lambda: chop_deu("U3_height_outside_domain",
                                                 **_g(DAY, ("chieu_cao", "chiều cao", "2"))),
    "U4_side_outside_frames": lambda: chop_deu("U4_side_outside_frames", day=DAY_14,
                                               **_g(("canh_day", "cạnh đáy", "√14"), CAO)),
}


def ket_qua(ca: str) -> dict:
    """Kết cục route của ca: `served:<giá trị học sinh thấy>` hoặc các trường từ chối."""
    contract, prog = CA[ca]()
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


def test_nhan_va_builder_cung_mot_tap_ca():
    assert set(CA) == set(NHAN)


# ── 1. Kết cục route theo nhãn đăng ký trước ─────────────────────────────────────────────────

@pytest.mark.parametrize("ca", sorted(NHAN))
def test_ket_cuc_route_theo_nhan(ca):
    _khop(ca, ket_qua(ca))


@pytest.mark.parametrize("ca", sorted(c for c in NHAN if c.startswith("U")))
def test_ngoai_mien_bieu_dien_tu_choi_dung_ly_do(ca):
    """§18.2: ngoài miền ⇒ chứng chỉ nói đúng tên giới hạn (không làm tròn, không phải "thiếu chiều cao")."""
    from app.simulation.semantic_program.assumption_gate import danh_gia_doc_lap
    contract, prog = CA[ca]()
    kq = danh_gia_doc_lap(contract, W.spec_cua(prog))
    assert kq.certificate is None, kq.details
    assert any("TEMPLATE_NOT_REPRESENTABLE T8" in d for d in kq.details), kq.details


def test_dinh_lech_phap_tuyen_bi_chan_boi_rang_buoc_dinh_tren_trong_tam():
    """N5b (amendment 1): |SG|² đúng nhưng đỉnh không trên trọng tâm — chính ràng buộc "apex above the centroid" từ
    chối (đối chiếu chính tắc là lớp thứ hai: bỏ ràng buộc thì nó vẫn chặn, xem tiêm lỗi FL2)."""
    from app.simulation.semantic_program.assumption_gate import danh_gia_doc_lap
    contract, prog = CA["N5b_apex_off_normal"]()
    kq = danh_gia_doc_lap(contract, W.spec_cua(prog))
    assert any("T8 TEMPLATE_CONSTRAINT_VIOLATED apex above the centroid" in d for d in kq.details), kq.details


@pytest.mark.parametrize("ca", sorted(c for c in NHAN if NHAN[c]["expect"].startswith("served:")))
def test_moi_ca_phuc_vu_qua_duoc_cong_pham_vi(ca):
    from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC, co_duong_thuc_thi

    assert co_duong_thuc_thi(NHAN[ca]["text"], DOMAIN_HINH_HOC), NHAN[ca]["text"]


# ── 2. Bộ đọc §18.1 ─────────────────────────────────────────────────────────────────────────

def _rb(ca: str) -> set:
    return {(r.kind, r.entities, r.value) for r in doc_rang_buoc(NHAN[ca]["text"])}


def test_doc_chop_tam_giac_deu_va_kich_thuoc_can():
    from app.simulation.geometry.radical import parse_exact
    rb = _rb("P1_side_height")
    ent = ("S", "A", "B", "C")
    assert ("regular_triangular_pyramid", ent, None) in rb
    assert ("base_equilateral", ent[1:], parse_exact("3√2")) in rb
    assert ("height", ent, parse_exact("√3")) in rb
    assert not any(k == "regular_tetrahedron" for k, _e, _v in rb)
    assert phan_chua_doc(NHAN["P1_side_height"]["text"]) == ()


def test_doc_tu_dien_deu_la_chop_voi_moi_canh_bang_nhau():
    from app.simulation.geometry.radical import parse_exact
    rb = _rb("P3_tetrahedron")
    ent = ("A", "B", "C", "D")
    assert {("pyramid", ent, None), ("regular_tetrahedron", ent, None),
            ("regular_triangular_pyramid", ent, None), ("edge_all", ent, parse_exact("3√2"))} <= rb
    assert phan_chua_doc(NHAN["P3_tetrahedron"]["text"]) == ()
    rb4 = _rb("P4_all_edges_equal")
    assert ("regular_tetrahedron", ("S", "A", "B", "C"), None) in rb4
    assert phan_chua_doc(NHAN["P4_all_edges_equal"]["text"]) == ()


def test_ba_canh_ben_bang_nhau_khong_lam_day_deu():
    rb = _rb("N8_equal_laterals_base_not_stated")
    assert not any(k in ("regular_triangular_pyramid", "base_equilateral") for k, _e, _v in rb)


def test_tu_dien_tron_khong_vao_vung_da_dien():
    """Đính chính §18.1 (trước khi đo): "tứ diện ABCD" không có "đều" KHÔNG phát gì — đưa mọi tứ diện vào vùng đa diện
    làm từ chối các đề tứ diện vuông/ngoại tiếp đang phục vụ (`test_obligation_binding_contract::A2`,
    `test_radius_verification::T7`, `test_scalar_fact_visibility::S4` đỏ khi thử) — quyết định U3 giữ nguyên."""
    from app.simulation.semantic_program.shape_constraint import neu_khoi_da_dien
    de = "Cho tứ diện ABCD có AB = 3. Tính thể tích khối tứ diện ABCD."
    assert doc_rang_buoc(de) == ()
    assert not neu_khoi_da_dien(de)
    assert neu_khoi_da_dien(NHAN["P3_tetrahedron"]["text"])


def test_chung_minh_chop_deu_khong_la_tien_de():
    from app.simulation.semantic_program.shape_constraint import che_muc_tieu
    de = che_muc_tieu("Cho hình chóp S.ABC có AB = 3√2. Chứng minh S.ABC là hình chóp tam giác đều.")
    assert not any(r.kind == "regular_triangular_pyramid" for r in doc_rang_buoc(de))


def test_do_dai_can_doc_tu_de_bang_mot_so():
    from app.simulation.geometry.radical import parse_exact
    from app.simulation.semantic_program.segment_relation import do_dai_trong_de
    d = do_dai_trong_de(NHAN["P5_equal_chains"]["text"])
    assert {frozenset(k): v for k, v in d.items()} == {
        **{frozenset(p): parse_exact("3√2") for p in (("A", "B"), ("B", "C"), ("C", "A"))},
        **{frozenset(p): F(3) for p in (("S", "A"), ("S", "B"), ("S", "C"))}}


def test_toa_do_va_ti_so_van_chi_huu_ti():
    """§18.3: độ dài căn KHÔNG mở toạ độ điểm hay tỉ số chia đoạn."""
    from app.simulation.semantic_program.point_coordinate import bat_bien_toa_do
    assert bat_bien_toa_do(None, "Cho điểm A(√2; 0; 0). Tính OA.") == ()


# ── 3. Ca dương: chứng chỉ, công thức, phép dựng ───────────────────────────────────────────

@pytest.mark.parametrize("ca", ["P1_side_height", "P2_side_lateral", "P3_tetrahedron", "P5_equal_chains",
                                "P10_frame_six"])
def test_ca_duong_mang_chung_chi_C1_T8(ca):
    from app.simulation.semantic_program.assumption_gate import danh_gia_doc_lap
    contract, prog = CA[ca]()
    kq = danh_gia_doc_lap(contract, W.spec_cua(prog))
    assert kq.certificate == "C1" and "C1 T8" in kq.details, kq.details


def test_cong_thuc_the_tich_tham_chieu_dien_tich_day_va_chieu_cao():
    scene = ket_qua("P1_side_height")["scene"]
    o = {x["id"]: x for x in scene["objects"]}
    V = o[THE_TICH]
    assert [r["entity_id"] for r in V["formula"]["references"]] == ["dien_tich_day_ABC", "chieu_cao_SG"], V["formula"]
    assert o["dien_tich_day_ABC"]["value"] == "9√3/2"
    assert o["chieu_cao_SG"]["value"] == "√3"


def test_chan_duong_cao_la_trong_tam_dung_bang_trung_tuyen():
    """§18.4: bước dựng thêm đoạn SG (chiều cao) — chân nhận theo TÊN phép dựng (giao hai trung tuyến)."""
    scene = ket_qua("P1_side_height")["scene"]
    cao = W.vat_theo_dinh(scene, "segment3", {"S", "G"})
    assert cao and "CONSTRUCT_HEIGHT" in cao[0]["formation_roles"], [o["id"] for o in scene["objects"]]


def test_trong_tam_de_goi_ten_khop_phep_dung():
    assert ket_qua("P9_named_centroid")["out"].construction_binding.get("G") == "MATCHED"
    assert ket_qua("N6_wrong_centroid_identity")["out"].construction_binding.get("G") == "MISMATCHED"


# ── 4. Miền biểu diễn — kiểm tất định (không giả định số học) ──────────────────────────────

def test_tam_giac_deu_nguyen_khong_bao_gio_co_canh_huu_ti():
    """PLAN §1: dò vét |x|,|y|,|z| ≤ 3 — mọi tam giác đều đỉnh nguyên chung đỉnh O có cạnh² = 2·(chuẩn Eisenstein),
    không cạnh² chính phương. (Phép dò nhỏ hơn PLAN — cùng kết luận — để test nhanh.)"""
    R = range(-3, 4)
    canh2 = set()
    diem = [p for p in itertools.product(R, R, R) if any(p)]
    for b, c in itertools.combinations(diem, 2):
        s = sum(x * x for x in b)
        if s == sum(x * x for x in c) == sum((x - y) ** 2 for x, y in zip(b, c)):
            canh2.add(s)
    assert canh2 and all(s % 2 == 0 for s in canh2)
    assert not any(int(s ** 0.5 + 0.5) ** 2 == s for s in canh2)
