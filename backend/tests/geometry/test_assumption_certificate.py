# -*- coding: utf-8 -*-
"""W15 — chứng chỉ giả định có căn cứ (C0 / C1) và phản ví dụ HỢP LỆ. 0 lượt gọi.

`assumption_gate.danh_gia_doc_lap(contract, spec)` = cùng bước bổ sung dựng hình + thực thi
mà route chạy, rồi chứng chỉ. Trạng thái: PROVEN_SAFE chỉ từ C0/C1;
DEPENDENT_ON_UNSTATED_ASSUMPTION chỉ từ một phản ví dụ HỢP LỆ (giữ MỌI ràng buộc của đề);
còn lại UNDETERMINED. Hai trạng thái sau đều bị từ chối.

Gốc của từng ca: `docs/evaluation/geometry/runs/w15-assumption-closure/diagnostics/`
(`TRACK_B_ROOT_CAUSE_TABLE` RC1–RC5, `GOLD_ROW_VERIFICATION` 18/18 hàng được đề xác định).
Tiền đề của chứng chỉ CHỈ là ràng buộc server đọc từ đề — không bao giờ là chú thích của
mô hình (`claimed`/`confirmed`/`source_fact_id`/`model_assumption`) — R2 của plan W15.

Vai trò literal (R1): IR này không có literal hữu tỉ chính xác trong `arith` (không có phép
chia thật; `"1/3"` là CHUỖI), nên bảng FORMULA_COEFFICIENT của W15 RỖNG — hằng số công thức
nằm trong phép `measure` của kernel. Mọi literal số học trên lát cắt ⇒ không vai trò ⇒ không
chứng nhận (ruling Task 2 trong sổ W15).
"""
from __future__ import annotations

import copy
import dataclasses
import importlib
from fractions import Fraction

import pytest

from app.simulation.semantic_program.analyze_contract import gan_bat_bien_nguon
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.postconditions import check_source_invariants
from app.simulation.semantic_program.request_contract import RequestContract
from tests.geometry import test_source_grounding_closure as T
from tests.geometry import w14_cases as W

AN_TOAN, PHU_THUOC, CHUA_RO = "PROVEN_SAFE", "DEPENDENT_ON_UNSTATED_ASSUMPTION", "UNDETERMINED"


def _gate():
    return importlib.import_module("app.simulation.semantic_program.assumption_gate")


def _kq(ct, raw):
    return _gate().danh_gia_doc_lap(ct, W.spec_cua(raw))


def _demo(cid: str):
    from scripts import replay_demo_cases as RD

    art = next(a for a, c, _v, _k in RD.DEMO if c == cid)
    c = RD._tim(art, cid)
    return (RequestContract.model_validate(c["analyze"]["raw_request_contract"]),
            copy.deepcopy(c["normalized_program"]))


def _gold(cid: str):
    _t, ct, raw = W.gold(cid)
    return ct, raw


def _ho(ten: str):
    _t, ct = W.HO[ten]()
    return ct, W.chuong_trinh(ct)


def _tinh_tien_doi_truc(p):
    x, y, z = (Fraction(str(c)) for c in p)
    return [str(y + 7), str(x - 2), str(z + 1)]


def _xoay():
    _t, ct = W.chop_tam_giac()
    return ct, W.doi_toa_do(W.chuong_trinh(ct), W._xoay)


def _cung():
    return (T._contract(T.PRISM_TEXT, T._prism_payload()),
            W.doi_toa_do(T._program_with_height_5(), _tinh_tien_doi_truc))


def _dat_diem(raw: dict, ten: str, xyz: list) -> None:
    """Đặt lại toạ độ literal của một điểm, dù nó khai ở `declare_point` hay `initial_value`."""
    for s in raw["statements"]:
        if s.get("kind") == "declare_point" and s.get("target_var") == ten:
            s["at"] = [str(c) for c in xyz]
    for m in raw["memory_declarations"]:
        if m["name"] == ten and isinstance(m.get("initial_value"), list):
            m["initial_value"] = [str(c) for c in xyz]


TOA_DO = {**{f"gold:{c}": (lambda c=c: _gold(c)) for c in (
    "p1_chop_thiet_dien_khoang_cach", "p2_chop_day_ngu_giac_lom", "p4_hinh_tru_the_tich_va_xung_quanh",
    "p5_hinh_non_the_tich_va_xung_quanh", "p6_thiet_dien_elip_cua_hinh_tru",
    "p7_thiet_dien_elip_cua_hinh_non")},
          **{f"demo:{c}": (lambda c=c: _demo(c)) for c in ("n1_thoi_dinh_thu_tu", "n2_lang_tru_xien_hai_vecto")}}
MAU = {**{f"ho:{h}": (lambda h=h: _ho(h)) for h in sorted(W.HO)},
       "rot:chop_tam_giac_xoay": _xoay, "rigid:prism_text_translate_swap": _cung,
       **{f"demo:{c}": (lambda c=c: _demo(c)) for c in ("t3_hop_tinh_tien_day_chuyen",
                                                         "t4_mat_xich_trong_chuoi_sau")}}


# ── RC1 · tám hàng toạ độ: C0 (literal ghim bởi bất biến đề CÙNG thực thể) ──────

@pytest.mark.parametrize("cid", sorted(TOA_DO))
def test_hang_toa_do_duoc_C0(cid):
    kq = _kq(*TOA_DO[cid]())
    assert (kq.status, kq.certificate) == (AN_TOAN, "C0"), (cid, kq)


# ── RC2/RC3 · tám hàng khuôn + t3/t4: C1 (cấu hình do đề xác định) ──────────────

@pytest.mark.parametrize("cid", sorted(MAU))
def test_hang_khuon_duoc_C1(cid):
    kq = _kq(*MAU[cid]())
    assert (kq.status, kq.certificate) == (AN_TOAN, "C1"), (cid, kq)


# ── RC4 · 11 phản ví dụ SAI của W14 không còn ra DEPENDENT ──────────────────────

def _adv10(bien_the: str):
    from tests.geometry.test_assumption_gate import _p01_voi_quan_he

    return _p01_voi_quan_he(bien_the)


SAI_CE_W14 = {
    "ho:chop_chu_nhat": MAU["ho:chop_chu_nhat"], "ho:lang_tru_tam_giac": MAU["ho:lang_tru_tam_giac"],
    "rigid:prism_text_translate_swap": _cung,
    **{f"demo:{c}": (lambda c=c: _demo(c)) for c in ("n1_thoi_dinh_thu_tu", "n2_lang_tru_xien_hai_vecto",
                                                      "t3_hop_tinh_tien_day_chuyen",
                                                      "t4_mat_xich_trong_chuoi_sau")},
    **{f"adv10_quan_he_{b}": (lambda b=b: _adv10(b)) for b in ("khong_nguon", "gia_dinh", "claimed")},
    "adv11_hai_dap_so_mot_ngoai_pham_vi": W.ca_hai_dap_so_mot_ngoai_pham_vi,
}


@pytest.mark.parametrize("cid", sorted(SAI_CE_W14))
def test_phan_vi_du_sai_cua_W14_khong_con(cid):
    kq = _kq(*SAI_CE_W14[cid]())
    assert kq.status != PHU_THUOC, (cid, kq)


# ── RC5 · phép dò AC1: DEPENDENT với nhân chứng HỢP LỆ, chủ thể AD ─────────────

def _lang_tru_dung_hop_le(m) -> bool:
    """Mọi ràng buộc của đề lăng trụ (thiếu AD): AB = 3, AC = 4, vuông tại A, tịnh tiến, đứng."""
    A, B, C, D, E, F = (m[k] for k in "ABCDEF")
    return ((B - A).dot(B - A) == 9 and (C - A).dot(C - A) == 16 and (B - A).dot(C - A) == 0
            and D - A == E - B == F - C and (D - A).dot(B - A) == 0 and (D - A).dot(C - A) == 0)


@pytest.mark.parametrize("kenh", ["layout_derived", "model_assumption", "given_length"])
def test_AC1_phu_thuoc_voi_nhan_chung_hop_le(kenh):
    ct, raw = W.kenh_gia_dinh(kenh)
    kq = _kq(ct, raw)
    assert kq.status == PHU_THUOC, kq
    assert kq.reason_code == "ASSUMPTION_DETERMINES_ANSWER", kq
    assert "AD" in kq.subjects, kq.subjects
    m = W.bo_nho_cuoi(W.spec_cua(kq.witness["program"]))
    assert _lang_tru_dung_hop_le(m), "nhân chứng phá một ràng buộc của đề"
    assert m["the_tich_lang_tru"] != W.bo_nho_cuoi(W.spec_cua(raw))["the_tich_lang_tru"]


# ── quan hệ chỉ có trong analyze, đề IM LẶNG: không dùng được (test (10) thực chất) ──

TEXT_IM_LANG = T.PRISM_TEXT.replace("lăng trụ đứng", "lăng trụ")


def _p01_im_lang(bien_the: str):
    """Lăng trụ P01 với đề KHÔNG nói "đứng"; quan hệ AD ⊥ (ABC) chỉ có trong hợp đồng."""
    from app.simulation.semantic_program.request_contract import InputFact

    ct = W.hop_dong(TEXT_IM_LANG, T._prism_payload())
    rels, facts = [], list(ct.input_facts)
    for r in ct.geometric_relations:
        if r.kind != "perpendicular_line_plane" or bien_the == "xac_nhan":
            rels.append(r)
        elif bien_the == "khong_nguon":
            rels.append(r.model_copy(update={"source_fact_id": None}))
        elif bien_the == "gia_dinh":
            rels.append(r.model_copy(update={"model_assumption": True}))
        else:
            facts.append(InputFact(fact_id="f_claimed", label="cạnh bên vuông góc đáy",
                                   values=("AD ⊥ (ABC)",), provenance="claimed"))
            rels.append(r.model_copy(update={"source_fact_id": "f_claimed"}))
    ct = ct.model_copy(update={"geometric_relations": tuple(rels), "input_facts": tuple(facts)})
    return ct, T._program_with_height_5()


@pytest.mark.parametrize("bien_the", ["xac_nhan", "khong_nguon", "gia_dinh", "claimed"])
def test_quan_he_chi_trong_phan_tich_khi_de_im_lang_khong_cap_C1(bien_the):
    kq = _kq(*_p01_im_lang(bien_the))
    assert kq.certificate != "C1", (bien_the, kq)
    assert kq.status in (PHU_THUOC, CHUA_RO), (bien_the, kq)


def test_claimed_ma_de_noi_lang_tru_dung_C1_chi_qua_tien_de_server():
    """Biến thể thứ tư của test (10): chú thích `claimed`, đề NÓI "lăng trụ đứng"."""
    kq = _kq(*_adv10("claimed"))
    assert (kq.status, kq.certificate) == (AN_TOAN, "C1"), kq
    tien_de = [d for d in kq.details if d.startswith("PREMISE")]
    assert any("right_prism" in d for d in tien_de), kq.details
    assert not any("f_claimed" in d for d in tien_de), tien_de


def test_lang_tru_xien_bac_quan_he_vuong_goc_cua_mo_hinh():
    """REFUTED_BY_SOURCE: đề nói "lăng trụ xiên", chương trình dựng cạnh bên ⊥ đáy."""
    ct = W.hop_dong(T.PRISM_TEXT.replace("lăng trụ đứng", "lăng trụ xiên"), T._prism_payload())
    kq = _kq(ct, T._program_with_height_5())
    assert kq.status != AN_TOAN, kq
    assert any("RELATION_REFUTED_BY_SOURCE" in d for d in kq.details), kq.details


# ── vai trò của literal (R1): hằng/tham số chỉ qua khi CÓ vai trò + nguồn ───────

THIEU_TI_SO = W.CHOP_TAM_GIAC_TEXT.replace(
    "Tính thể tích khối chóp S.ABC.", "Điểm M thuộc SB. Tính khoảng cách từ A đến M.")
DU_TI_SO = W.CHOP_TAM_GIAC_TEXT.replace(
    "Tính thể tích khối chóp S.ABC.", "Điểm M thuộc SB sao cho SM = 2MB. Tính khoảng cách từ A đến M.")
#: Lối viết bộ phát chia đoạn hôm nay KHÔNG đọc ("thuộc CẠNH SB"): route trước W15 phục vụ
#: cả tỉ số SAI ở đây (đo trong RED log). Sau cổng: tỉ số không vai trò ⇒ không chứng nhận.
CANH_TI_SO = W.CHOP_TAM_GIAC_TEXT.replace(
    "Tính thể tích khối chóp S.ABC.", "Gọi M là điểm thuộc cạnh SB sao cho SM = 2MB. "
    "Tính khoảng cách từ A đến M.")


def _chop_voi_M(text: str, ti_so: str):
    payload = W.chop_tam_giac_payload()
    payload["obligations"] = [{"kind": "distance", "container": "A", "witness": "d_AM", "wrt": "M"}]
    ct = W.hop_dong(text, payload)
    _t, ct0 = W.chop_tam_giac()
    raw = W.chuong_trinh(ct0)
    raw["memory_declarations"] += [{"name": "M", "type": "point3"}, {"name": "d_AM", "type": "float"}]
    raw["statements"] += [
        {"kind": "construct_point", "target_var": "M",
         "expr": {"kind": "divide_segment", "a": "S", "b": "B", "ratio": ti_so}},
        {"kind": "assign", "target_var": "d_AM",
         "expr": {"kind": "measure", "quantity": "distance", "of": "A", "wrt": "M"}}]
    return ct, raw


def test_ti_so_chia_doan_de_khong_cho_khong_duoc_chung_nhan():
    kq = _kq(*_chop_voi_M(THIEU_TI_SO, "1/3"))
    assert kq.status != AN_TOAN, kq


def test_ti_so_chia_doan_de_cho_dung_doan_duoc_chung_nhan():
    kq = _kq(*_chop_voi_M(DU_TI_SO, "2/3"))
    assert (kq.status, kq.certificate) == (AN_TOAN, "C1"), kq


def test_ti_so_chia_doan_khac_ti_so_de_cho_khong_duoc_chung_nhan():
    kq = _kq(*_chop_voi_M(DU_TI_SO, "1/3"))
    assert kq.status != AN_TOAN, kq


@pytest.mark.parametrize("ti_so", ["1/3", "2/3"])
def test_ti_so_voi_loi_viet_chua_doc_duoc_khong_duoc_chung_nhan(ti_so):
    """Đề nói SM = 2MB nhưng theo lối viết bộ phát chưa đọc: tỉ số không có nguồn ⇒ từ chối,
    kể cả khi tỉ số tình cờ đúng — không bao giờ phục vụ một tỉ số chưa được đề xác nhận."""
    kq = _kq(*_chop_voi_M(CANH_TI_SO, ti_so))
    assert kq.status != AN_TOAN, (ti_so, kq)


def test_mat_phang_mo_hinh_tu_chon_vi_tri_khong_duoc_chung_nhan():
    text = W.CHOP_TAM_GIAC_TEXT.replace(
        "Tính thể tích khối chóp S.ABC.", "Một mặt phẳng song song với đáy cắt khối chóp theo thiết diện (T). "
        "Tính diện tích thiết diện (T).")
    payload = W.chop_tam_giac_payload()
    payload["obligations"] = [{"kind": "area", "container": "T", "witness": "area_T"}]
    ct = W.hop_dong(text, payload)
    _t, ct0 = W.chop_tam_giac()
    raw = W.chuong_trinh(ct0)
    raw["memory_declarations"] += [{"name": "alpha", "type": "plane3"}, {"name": "T", "type": "section"},
                                   {"name": "area_T", "type": "float"}]
    raw["statements"] += [
        {"kind": "construct_plane_from_equation", "target_var": "alpha", "a": 0, "b": 0, "c": 1, "d": -2},
        {"kind": "construct_section", "target_var": "T", "solid": "khoi_chop", "plane": "alpha"},
        {"kind": "assign", "target_var": "area_T", "expr": {"kind": "measure", "quantity": "area", "of": "T"}}]
    kq = _kq(ct, raw)
    assert kq.status != AN_TOAN, kq


def _arith(op, trai, phai):
    return {"kind": "arith", "op": op, "left": trai, "right": phai}


def _lit(x):
    return {"kind": "literal", "value": x}


def _var(n):
    return {"kind": "var", "name": n}


def _do(dich: str, of: str, wrt: str) -> dict:
    return {"kind": "assign", "target_var": dich,
            "expr": {"kind": "measure", "quantity": "distance", "of": of, "wrt": wrt}}


def _lang_tru_cong_thuc(the_tich_expr: dict, them: list | None = None):
    """Lăng trụ P01 (đề đủ): V = <biểu thức> trên S_day = diện tích đáy, h = d(D, mp(ABC))."""
    ct = T._contract(T.PRISM_TEXT, T._prism_payload())
    raw = T._program_with_height_5()
    raw["memory_declarations"] += [{"name": "mp_day", "type": "plane3"}, {"name": "h", "type": "float"}]
    cuoi = next(s for s in raw["statements"] if s.get("target_var") == "the_tich_lang_tru")
    raw["statements"].remove(cuoi)
    raw["statements"] += [
        {"kind": "construct_plane", "target_var": "mp_day", "through": ["A", "B", "C"]},
        _do("h", "D", "mp_day"), *(them or []),
        {"kind": "assign", "target_var": "the_tich_lang_tru", "expr": the_tich_expr}]
    return ct, raw


S_NHAN_H = _arith("*", _var("dien_tich_day_ABC"), _var("h"))


@pytest.mark.parametrize("ten,expr", [
    ("S·h (không literal)", S_NHAN_H),
    ("S·AD_length (dữ kiện đề, CÙNG thực thể AD)", _arith("*", _var("dien_tich_day_ABC"), _var("AD_length"))),
])
def test_cong_thuc_khong_literal_tu_do_duoc_chung_nhan(ten, expr):
    kq = _kq(*_lang_tru_cong_thuc(expr))
    assert (kq.status, kq.certificate) == (AN_TOAN, "C1"), (ten, kq)


def test_literal_trong_cong_thuc_khong_co_vai_tro_du_hop_le_thu_nguyen():
    """`S·5`: diện tích × độ dài = thể tích, đúng cả số (30) — vẫn KHÔNG chứng nhận."""
    kq = _kq(*_lang_tru_cong_thuc(_arith("*", _var("dien_tich_day_ABC"), _lit(5))))
    assert kq.status != AN_TOAN, kq


def test_chia_nguyen_cho_hang_so_khong_duoc_chung_nhan():
    """Chóp: `(S·h) // 3` ra 10 — đúng nhờ may; literal 3 không vai trò, `//` không phải chia thật."""
    _t, ct = W.chop_tam_giac()
    raw = W.chuong_trinh(ct)
    raw["memory_declarations"] += [{"name": "mp_day", "type": "plane3"}, {"name": "h", "type": "float"}]
    cuoi = next(s for s in raw["statements"] if s.get("target_var") == "the_tich_khoi")
    raw["statements"].remove(cuoi)
    raw["statements"] += [
        {"kind": "construct_plane", "target_var": "mp_day", "through": ["A", "B", "C"]},
        _do("h", "S", "mp_day"),
        {"kind": "assign", "target_var": "the_tich_khoi",
         "expr": _arith("//", _arith("*", _var("dien_tich_day_ABC"), _var("h")), _lit(3))}]
    assert W.bo_nho_cuoi(W.spec_cua(raw))["the_tich_khoi"] == 10
    kq = _kq(ct, raw)
    assert kq.status != AN_TOAN, kq


# ── reaching definitions (R3): giá trị THẬT đi vào phép đo, cả dạng C0 lẫn C1 ────

def _gan(dich: str, nguon: str) -> dict:
    return {"kind": "assign", "target_var": dich, "expr": _var(nguon)}


def _trung_diem(ten: str, a: str, b: str) -> dict:
    """Điểm DẪN XUẤT (neo vào hai điểm đã có) — grounding chấp nhận, khác một điểm tự đặt."""
    return {"kind": "construct_point", "target_var": ten, "expr": {"kind": "midpoint", "a": a, "b": b}}


def _c0_diem(kieu: str):
    """n1: M có toạ độ đề cho; ghi đè M (bằng trung điểm MN) trước phép đo, khôi phục sau
    (hoặc qua bí danh)."""
    ct, raw = _demo("n1_thoi_dinh_thu_tu")
    raw["memory_declarations"] += [{"name": "X", "type": "point3"}, {"name": "M_luu", "type": "point3"},
                                   {"name": "M_moi", "type": "point3"}]
    st = raw["statements"]
    if kieu == "ghi_de":
        st[:0] = [_trung_diem("X", "M", "N"), _gan("M_luu", "M"), _gan("M", "X")]
        st.append(_gan("M", "M_luu"))
    else:  # bí danh của điểm bị ghi đè; M được khôi phục NGAY, phép đo đi qua bí danh
        st[:0] = [_trung_diem("X", "M", "N"), _gan("M_luu", "M"), _gan("M", "X"), _gan("M_moi", "M"),
                  _gan("M", "M_luu")]
        for s in st[5:]:
            for k in ("point", "through_a"):
                for o in (s, s.get("expr") or {}):
                    if o.get(k) == "M":
                        o[k] = "M_moi"
    return ct, raw, "dist_q_mp"


def _c1_diem(kieu: str):
    """Chóp tam giác: S là đỉnh khuôn; ghi đè S (bằng trung điểm SA) trước khi dựng khối,
    khôi phục sau."""
    _t, ct = W.chop_tam_giac()
    raw = W.chuong_trinh(ct)
    raw["memory_declarations"] += [{"name": "S_xa", "type": "point3"}, {"name": "S_luu", "type": "point3"},
                                   {"name": "S_moi", "type": "point3"}]
    st = raw["statements"]
    i = 1 + next(k for k, s in enumerate(st) if s.get("kind") == "declare_point" and s["target_var"] == "S")
    if kieu == "ghi_de":
        st[i:i] = [_trung_diem("S_xa", "S", "A"), _gan("S_luu", "S"), _gan("S", "S_xa")]
        st.append(_gan("S", "S_luu"))
    else:
        st[i:i] = [_trung_diem("S_xa", "S", "A"), _gan("S_luu", "S"), _gan("S", "S_xa"), _gan("S_moi", "S"),
                   _gan("S", "S_luu")]
        khoi = next(s for s in st if s["kind"] == "construct_solid")
        doi = lambda x: "S_moi" if x == "S" else x  # noqa: E731
        khoi["vertices"] = [doi(v) for v in khoi["vertices"]]
        khoi["faces"] = [[doi(v) for v in f] if isinstance(f, list) else f for f in khoi["faces"]]
    return ct, raw, "the_tich_khoi"


def _c1_vo_huong():
    """Lăng trụ P01, V = S·h; h bị ghi đè bằng |DE| = 3 trước khi tính V, khôi phục sau.

    (Ghi đè bằng một độ dài HỮU TỈ: `arith` của interpreter không nhân `Fraction` với căn.)"""
    ct, raw = _lang_tru_cong_thuc(S_NHAN_H, them=[_do("h", "D", "E")])
    raw["statements"].append(_do("h", "D", "mp_day"))
    return ct, raw, "the_tich_lang_tru"


def _c0_vo_huong(ghi_de: bool = True):
    """p1 (toạ độ): d0 = d(S, BD); d0 bị ghi đè bằng |SB|, đáp số đọc d0, rồi d0 khôi phục."""
    ct, raw = _gold("p1_chop_thiet_dien_khoang_cach")
    raw["memory_declarations"].append({"name": "d0", "type": "float"})
    i = next(i for i, s in enumerate(raw["statements"]) if s.get("target_var") == "dist_S_BD")
    raw["statements"][i:i + 1] = ([_do("d0", "S", "BD"), _do("d0", "S", "B"), _gan("dist_S_BD", "d0"),
                                   _do("d0", "S", "BD")] if ghi_de
                                  else [_do("d0", "S", "BD"), _gan("dist_S_BD", "d0")])
    return ct, raw, "dist_S_BD"


GHI_DE = {"C0:diem_ghi_de_khoi_phuc": lambda: _c0_diem("ghi_de"),
          "C0:bi_danh_diem_bi_ghi_de": lambda: _c0_diem("bi_danh"),
          "C0:vo_huong_ghi_de_khoi_phuc": _c0_vo_huong,
          "C1:diem_ghi_de_khoi_phuc": lambda: _c1_diem("ghi_de"),
          "C1:bi_danh_diem_bi_ghi_de": lambda: _c1_diem("bi_danh"),
          "C1:vo_huong_ghi_de_khoi_phuc": _c1_vo_huong}


def _gia_tri_dung(ca: str):
    """Đáp số đúng của bài gốc (chương trình chưa bị ghi đè)."""
    if ca.startswith("C0:vo_huong"):
        return W.bo_nho_cuoi(W.spec_cua(_gold("p1_chop_thiet_dien_khoang_cach")[1]))["dist_S_BD"]
    if ca.startswith("C0"):
        return W.bo_nho_cuoi(W.spec_cua(_demo("n1_thoi_dinh_thu_tu")[1]))["dist_q_mp"]
    return Fraction(30) if ca.startswith("C1:vo_huong") else Fraction(10)


@pytest.mark.parametrize("ca", sorted(GHI_DE))
def test_GUARD_chuong_trinh_ghi_de_tinh_sai_ma_trang_thai_cuoi_dung(ca):
    """GUARD (xanh hôm nay): mỗi ca thật sự tính SAI đáp số trong khi trạng thái CUỐI vẫn
    khớp mọi bất biến nguồn — đúng lối hở R3 mà phép kiểm trên `final_memory` không thấy."""
    ct, raw, ten = GHI_DE[ca]()
    res = SemanticProgramInterpreter().execute(W.spec_cua(raw))
    assert res.final_memory[ten] != _gia_tri_dung(ca), (ca, res.final_memory[ten])
    # Bất biến đọc lại từ ĐỀ hôm nay (hợp đồng demo lưu trước khi có bộ phát).
    moi = gan_bat_bien_nguon(ct.model_copy(update={"source_invariants": ()}), ct.problem_text)
    kq = check_source_invariants(moi, res)
    assert kq.ok and kq.checked > 0, (ca, kq)


@pytest.mark.parametrize("ca", sorted(GHI_DE))
def test_ghi_de_bi_danh_khoi_phuc_khong_duoc_chung_nhan(ca):
    ct, raw, _ten = GHI_DE[ca]()
    kq = _kq(ct, raw)
    assert kq.status == CHUA_RO, (ca, kq)
    assert any("CLOSURE_MULTIPLE_DEFINITIONS" in d for d in kq.details), (ca, kq.details)


def test_doi_chung_C0_bien_trung_gian_dinh_nghia_mot_lan_duoc_chung_nhan():
    """Đối chứng dương của ca vô hướng dạng C0: cùng chuỗi gán, d0 chỉ định nghĩa MỘT lần."""
    ct, raw, _ten = _c0_vo_huong(ghi_de=False)
    kq = _kq(ct, raw)
    assert (kq.status, kq.certificate) == (AN_TOAN, "C0"), kq


# ── cos² nằm NGOÀI C1; mọi giá trị số học sinh thấy đều phải được chứng nhận ─────

def test_cos2_ngoai_pham_vi_C1_tu_choi_ca_bai():
    kq = _kq(*W.ca_hai_dap_so_mot_ngoai_pham_vi())
    assert kq.status != AN_TOAN, kq
    assert kq.certificate is None, kq
    assert any("angle_cos_sq" in d for d in kq.details), kq.details


# ── đối chiếu độc lập với compiler: bất đồng ⇒ UNDETERMINED + báo động ───────────

def test_doi_chieu_compiler_bat_dong_thi_khong_chung_nhan(monkeypatch):
    from app.simulation.geometry_compiler import compiler as C

    _t, ct = W.chop_tam_giac()
    raw = W.chuong_trinh(ct)
    goc = C.bien_dich

    def lech(graph):
        bd = goc(graph)
        prog = copy.deepcopy(bd.program)
        _dat_diem(prog, "S", [0, 0, 6])
        return dataclasses.replace(bd, program=prog)

    monkeypatch.setattr(C, "bien_dich", lech)
    kq = _kq(ct, raw)
    assert kq.status == CHUA_RO, kq
    assert any("CROSS_CHECK" in d for d in kq.details), kq.details


# ── metamorphic ──────────────────────────────────────────────────────────────

def test_chuyen_dong_cung_va_phep_quay_giu_phan_quyet_va_gia_tri():
    _t, ct = W.chop_tam_giac()
    raw = W.chuong_trinh(ct)
    for bien in (raw, W.doi_toa_do(raw, W._xoay), W.doi_toa_do(raw, _tinh_tien_doi_truc)):
        kq = _kq(ct, bien)
        assert (kq.status, kq.certificate) == (AN_TOAN, "C1"), kq
        assert W.bo_nho_cuoi(W.spec_cua(bien))["the_tich_khoi"] == 10


CHOP_DOI_TEN = ("Cho hình chóp Q.MNP có đáy MNP là tam giác vuông tại M, MN = 3, MP = 4. "
                "Cạnh bên QM vuông góc với đáy, QM = 5. Tính thể tích khối chóp Q.MNP.")


def test_song_anh_ten_thuc_the_giu_phan_quyet():
    doi = {"A": "M", "B": "N", "C": "P", "S": "Q"}
    payload = W.chop_tam_giac_payload()
    for f in payload["input_facts"]:
        f["label"] = "".join(doi.get(c, c) for c in f["label"])
        f["id"] = f"fact_len_{f['label']}"
    for r in payload["geometric_relations"]:
        for k in ("line", "other_line", "plane"):
            if k in r:
                r[k] = [doi[x] for x in r[k]]
    ct = W.hop_dong(CHOP_DOI_TEN, payload)
    raw = W.chuong_trinh(ct)
    kq = _kq(ct, raw)
    assert (kq.status, kq.certificate) == (AN_TOAN, "C1"), kq


def test_doi_kich_thuoc_de_khong_cho_bi_phat_hien():
    """Mô hình hợp lệ (chóp vuông tại A, SA ⊥ đáy) nhưng đề KHÔNG cho SA; S đặt ở cao 7."""
    payload = W.chop_tam_giac_payload()
    payload["input_facts"] = [f for f in payload["input_facts"] if f["label"] != "SA"]
    ct = W.hop_dong(W.CHOP_TAM_GIAC_TEXT.replace(", SA = 5", ""), payload)
    _t, ct_du = W.chop_tam_giac()
    raw = W.chuong_trinh(ct_du)
    raw["memory_declarations"] = [m for m in raw["memory_declarations"] if m["name"] != "SA_length"]
    _dat_diem(raw, "S", [0, 0, 7])
    kq = _kq(ct, raw)
    assert kq.status == PHU_THUOC, kq
    assert "SA" in kq.subjects, kq.subjects


CHUNG_NHAN_PHUC_VU = {**TOA_DO, **MAU}


@pytest.mark.parametrize("cid", sorted(CHUNG_NHAN_PHUC_VU))
def test_hang_duoc_chung_nhan_van_duoc_phuc_vu(cid):
    """Route sản phẩm: hàng đề xác định vẫn được phục vụ, và kết quả MANG chứng chỉ."""
    ct, raw = CHUNG_NHAN_PHUC_VU[cid]()
    _sp, out, _sc = W.chay(ct, raw)
    assert out.servable, (cid, out.stage_reached, out.reason_code, out.details[:3])
    assert out.assumption_certificate in ("C0", "C1"), (cid, out.assumption_certificate)
