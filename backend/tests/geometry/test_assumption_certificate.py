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
import importlib
import json
import re
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


# ── đề CHO kích thước qua một câu NGOÀI từ vựng: không bao giờ DEPENDENT (§7, đính chính) ──

def _chop_SA_qua_cau(cau: str, sa: int = 3):
    """Chóp T1 mà đề cho SA qua `cau` thay vì `SA = 5`; chương trình dựng ĐÚNG SA = `sa`."""
    payload = W.chop_tam_giac_payload()
    payload["input_facts"] = [f for f in payload["input_facts"] if f["label"] != "SA"]
    ct = W.hop_dong(W.CHOP_TAM_GIAC_TEXT.replace("SA = 5", cau), payload)
    raw = W.chuong_trinh(W.chop_tam_giac()[1])
    raw["memory_declarations"] = [m for m in raw["memory_declarations"] if m["name"] != "SA_length"]
    _dat_diem(raw, "S", [0, 0, sa])
    return ct, raw


@pytest.mark.parametrize("cau", ["Góc giữa SB và mặt phẳng đáy bằng 45°", "SA = AB",
                                 "Tam giác SAB vuông cân tại A", "SB = 3√2"])
def test_de_cho_kich_thuoc_bang_cau_khong_doc_duoc_khong_la_phu_thuoc(cau):
    """Phép kéo SA giữ mọi ràng buộc ĐỌC ĐƯỢC nhưng phá câu không đọc — nó không phải phản
    ví dụ. Từ chối với lời "chưa chứng minh", không bao giờ "đề không cho SA"."""
    kq = _kq(*_chop_SA_qua_cau(cau))
    assert kq.status == CHUA_RO, (cau, kq)
    assert any(d.startswith("CE_TEXT_NOT_FULLY_READ") for d in kq.details), kq.details


def test_do_dai_doc_duoc_ngoai_lop_kich_thuoc_lam_phep_keo_khong_hop_le():
    """Đề ĐỌC ĐƯỢC `SB = 5` (cùng AB = 3 ⇒ SA = 4): câu độ dài số nên phần dữ kiện đọc trọn và
    nó không phải `RangBuoc` — chỉ luật hợp lệ của phép kéo (độ dài đề cho, bất biến đề) thấy
    phép kéo SA phá |SB| = 5. Không bao giờ "đề không cho SA"."""
    kq = _kq(*_chop_SA_qua_cau("SB = 5", sa=4))
    assert kq.status == CHUA_RO, kq
    assert any("MISSING SA: CE_INVALID" in d for d in kq.details), kq.details


def test_tuyen_tu_choi_voi_loi_chua_chung_minh_khi_de_cho_qua_cau_khong_doc():
    _sp, out, _sc = W.chay(*_chop_SA_qua_cau("Góc giữa SB và mặt phẳng đáy bằng 45°"))
    assert (out.servable, out.stage_reached, out.reason_code) == (
        False, "assumption", "ASSUMPTION_INVARIANCE_UNPROVEN"), out.details


def _chop_vuong_qua_duong_cheo():
    """T2: đáy hình chữ nhật, AB = 3 và AC ⊥ BD — đường chéo vuông góc ⇒ hình vuông, AD = 3.
    Bộ đọc ĐỌC được AC ⊥ BD nhưng nó không là tiền đề của khuôn; chương trình dựng đúng AD = 3."""
    t, ct0 = W.chop_chu_nhat()
    text = t.replace("AB = 3, AD = 4.", "AB = 3 và AC vuông góc với BD.")
    ct = gan_bat_bien_nguon(ct0.model_copy(update={
        "problem_text": text, "source_invariants": (),
        "input_facts": tuple(f for f in ct0.input_facts if f.label != "AD")}), text)
    raw = W.chuong_trinh(ct0)
    raw["memory_declarations"] = [m for m in raw["memory_declarations"] if m["name"] != "AD_length"]
    _dat_diem(raw, "D", [0, 3, 0])
    _dat_diem(raw, "C", [3, 3, 0])
    return ct, raw


def test_rang_buoc_doc_duoc_ngoai_khuon_khong_kiem_thi_khong_la_phu_thuoc():
    """§7: phản ví dụ chỉ hợp lệ khi MỌI ràng buộc đọc được còn thoả trên nhân chứng; ràng
    buộc ngoài tiền đề của khuôn không được kiểm ở đó ⇒ không có phản ví dụ."""
    kq = _kq(*_chop_vuong_qua_duong_cheo())
    assert kq.status == CHUA_RO, kq
    assert any(d.startswith("CE_CONSTRAINT_NOT_CHECKED line_perp_line") for d in kq.details), kq.details


# ── đỉnh phẩy viết theo lối của mô hình (quyết định U4 · G2) ────────────────

def _hop_doi_ten_phay(hau_to: str):
    """Hộp chữ nhật T4 (đề viết `ABCD.A'B'C'D'`), chương trình viết A′ thành `A<hau_to>`."""
    _t, ct = W.hop_chu_nhat()
    raw = json.dumps(W.chuong_trinh(ct))
    return ct, json.loads(re.sub(r"([A-D])_prime", lambda m: m.group(1) + hau_to, raw))


@pytest.mark.parametrize("hau_to", ["1", "prime"])
def test_dinh_phay_viet_kieu_mo_hinh_van_duoc_C1(hau_to):
    """`domain_profile` ghi bốn cách viết CÙNG một điểm bậc một đo được ở lượt sinh thật —
    `A'` · `A1` · `A_prime` · `Aprime`; đỉnh đề gắn với tên chương trình qua khoá ký hiệu."""
    kq = _kq(*_hop_doi_ten_phay(hau_to))
    assert (kq.status, kq.certificate) == (AN_TOAN, "C1"), kq


def test_hai_ten_cung_khoa_khong_gan():
    """`A_` cùng khoá với `A` — không biết tên nào là A, tên nào là A′ ⇒ không gắn, không chứng nhận."""
    kq = _kq(*_hop_doi_ten_phay("_"))
    assert (kq.status, kq.certificate) == (CHUA_RO, None), kq


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


@pytest.mark.parametrize("ca", sorted(GHI_DE))
def test_tuyen_tu_choi_ghi_de_bi_danh_khoi_phuc_o_moi_vung(ca):
    """Quyết định U5: một giá trị người học thấy đọc qua tên có NHIỀU định nghĩa với tới là lỗi
    toàn vẹn của chương trình — route từ chối ở MỌI vùng, kể cả đề không nêu khối đa diện
    (hình thoi n1 của các ca C0 điểm; các ca vô hướng đã bị cổng sớm hơn chặn)."""
    ct, raw, _ten = GHI_DE[ca]()
    _sp, out, _sc = W.chay(ct, raw)
    assert not out.servable, (ca, out.stage_reached)
    if ca in ("C0:diem_ghi_de_khoi_phuc", "C0:bi_danh_diem_bi_ghi_de"):        # ngoài vùng đa diện
        assert (out.stage_reached, out.assumption_enforced) == ("assumption", True), (ca, out.details[:3])


def _b3(doc_truoc: bool = False):
    """Quy tắc sản phẩm cũ (`test_derived_point_construction::test_B3`): P khai toạ độ (giả
    định) NHƯNG vẫn có lệnh dựng P — giá trị đến từ phép dựng. `doc_truoc`: thêm một phép đo
    ĐỌC literal khai báo của P trước khi lệnh dựng ghi đè nó."""
    from tests.geometry import test_derived_point_construction as D

    p = D._ct(D.MULTIPLE, E={"source_fact_id": None, "model_assumption": D.LY_DO},
              P={"initial_value": [2, 0, 0], "source_fact_id": None, "model_assumption": D.LY_DO})
    if doc_truoc:
        i = next(k for k, s in enumerate(p["statements"]) if s.get("target_var") == "P")
        p["memory_declarations"].append({"name": "d_som", "type": "float"})
        p["statements"].insert(i, _do("d_som", "P", "E"))
    return D._hd(D.MULTIPLE), p


def test_literal_khai_bao_bi_lenh_dung_ghi_de_truoc_moi_lan_doc_khong_phai_dinh_nghia_voi_toi():
    """U5: literal khai báo bị CHÍNH lệnh dựng ghi đè trước mọi lần đọc không với tới ai."""
    kq = _kq(*_b3())
    assert not any("CLOSURE_MULTIPLE_DEFINITIONS" in d for d in kq.details), kq.details


def test_literal_khai_bao_duoc_doc_truoc_khi_ghi_de_van_la_nhieu_dinh_nghia():
    kq = _kq(*_b3(doc_truoc=True))
    assert any("CLOSURE_MULTIPLE_DEFINITIONS" in d for d in kq.details), kq.details


def _c0_tu_doc(x0: list[int]):
    """n1: X khai toạ độ GIẢ ĐỊNH `x0` (đề không cho); lệnh dựng X ĐỌC CHÍNH literal ấy
    (X = trung điểm của X và N) rồi Q = X + NP — lệnh dựng đọc literal nó ghi đè."""
    ct, raw = _demo("n1_thoi_dinh_thu_tu")
    raw["memory_declarations"].append({"name": "X", "type": "point3", "initial_value": x0,
                                       "model_assumption": "Điểm phụ tự đặt."})
    raw["statements"].insert(0, _trung_diem("X", "X", "N"))
    next(s for s in raw["statements"] if s.get("target_var") == "Q")["expr"]["point"] = "X"
    return ct, raw


def test_lenh_dung_doc_chinh_literal_no_ghi_de_van_la_nhieu_dinh_nghia():
    """U5 chỉ bỏ literal khai báo khi KHÔNG ai đọc nó — kể cả CHÍNH lệnh dựng ghi đè nó.
    Ở đây đáp số đổi theo literal giả định của X (tiền đề kiểm ngay trong test), nên C0 mà
    chứng nhận là chứng nhận một giá trị phụ thuộc giả định đề không cho."""
    a, b = (SemanticProgramInterpreter().execute(W.spec_cua(_c0_tu_doc(x0)[1])).final_memory["dist_q_mp"]
            for x0 in ([7, 7, 7], [0, 9, 1]))
    assert a != b
    kq = _kq(*_c0_tu_doc([7, 7, 7]))
    assert kq.status != AN_TOAN, kq
    assert any("CLOSURE_MULTIPLE_DEFINITIONS" in d for d in kq.details), kq.details


# ── cos² nằm NGOÀI C1; mọi giá trị số học sinh thấy đều phải được chứng nhận ─────

def test_cos2_ngoai_pham_vi_C1_tu_choi_ca_bai():
    kq = _kq(*W.ca_hai_dap_so_mot_ngoai_pham_vi())
    assert kq.status != AN_TOAN, kq
    assert kq.certificate is None, kq
    assert any("angle_cos_sq" in d for d in kq.details), kq.details


# ── đối chiếu độc lập: hiện thực thứ hai bất đồng ⇒ UNDETERMINED + báo động ─────

def test_doi_chieu_hien_thuc_chinh_tac_bat_dong_thi_khong_chung_nhan(monkeypatch):
    """Đường bất đồng của phép đối chiếu C1 (ruling Task 5): hiện thực thứ hai là hiện thực
    CHÍNH TẮC của khuôn dựng từ kích thước đề cho — không phải `compiler.bien_dich`, vì
    `test_structured_geometry_relations::test_Y` cấm tệp sản phẩm tham chiếu gói compiler.
    Hai hiện thực cho hai giá trị khác nhau ⇒ một trong hai thẩm quyền sai ⇒ không chứng nhận."""
    from app.simulation.geometry.exact import Vec3

    G = _gate()
    goc = G._hien_thuc_chinh_tac

    def lech(khuon, do_dai):
        return {e: (v + Vec3.of(0, 0, 1) if e == "S" else v) for e, v in goc(khuon, do_dai).items()}

    monkeypatch.setattr(G, "_hien_thuc_chinh_tac", lech)
    _t, ct = W.chop_tam_giac()
    kq = _kq(ct, W.chuong_trinh(ct))
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


# ══ W16 · tái hiện trước khi sửa (ASSUMPTION_CERTIFICATE_AMENDMENT §14) ══════════════════

# ── §14.1 · hệ số mặt phẳng phải thuộc CÙNG mặt phẳng của đề ──────────────────────────

NEN_P1 = ("Trong không gian Oxyz, cho khối chóp S.ABCD có đáy ABCD là hình vuông với A(0;0;0), "
          "B(6;0;0), C(6;6;0), D(0;6;0) và đỉnh S(0;0;6). ")
HAI_MP = "Cho hai mặt phẳng (α): z = 3 và (β): z = 2. Mặt phẳng (β) cắt khối chóp theo thiết diện (T)."
MOT_MP_KHONG_TEN_VA_BETA = ("Cho mặt phẳng z = 3. Mặt phẳng (β) song song với mặt phẳng đó cắt khối chóp "
                            "theo thiết diện (T).")


def _p1_mat_phang(cau: str, mat_phang: list, cat: str):
    """Gold p1 (toạ độ đề cho, khối đa diện): đề = nền + `cau` + hỏi diện tích (T); chương
    trình dựng các mặt phẳng `mat_phang` = [(tên biến, (a, b, c, d))] rồi cắt (T) bằng `cat`."""
    from scripts import replay_negative_boundaries as RNB

    goc = RNB.doc_raw_theo_thu_tu("p1_chop_thiet_dien_khoang_cach")
    pay = json.loads(goc["semantic_analyze"][0])
    pay["input_facts"] = [f for f in pay["input_facts"] if f["id"] != "alpha_plane_def"]
    pay["obligations"] = [o for o in pay["obligations"] if o["kind"] == "area"]
    raw = json.loads(goc["semantic_program"][0])
    raw["memory_declarations"] = [m for m in raw["memory_declarations"] if m["name"] in ("S.ABCD", "T", "area_T")]
    st = [s for s in raw["statements"] if s["kind"] in ("declare_point", "construct_polygon", "construct_solid")]
    st += [{"kind": "construct_plane_from_equation", "target_var": t, "a": a, "b": b, "c": c, "d": d}
           for t, (a, b, c, d) in mat_phang]
    st += [{"kind": "construct_section", "target_var": "T", "solid": "S.ABCD", "plane": cat},
           {"kind": "assign", "target_var": "area_T", "expr": {"kind": "measure", "quantity": "area", "of": "T"}}]
    raw["statements"] = st
    return W.hop_dong(NEN_P1 + cau + " Tính diện tích thiết diện (T).", pay), raw


MP_SAI_THUC_THE = {
    "A1_beta_chua_xac_dinh_mang_he_so_alpha": lambda: _p1_mat_phang(
        "Cho mặt phẳng (α): z = 3. Mặt phẳng (β) song song với (α) cắt khối chóp theo thiết diện (T).",
        [("beta_plane", (0, 0, 1, -3))], "beta_plane"),
    "A2_hai_mat_phang_doi_cheo_he_so": lambda: _p1_mat_phang(
        HAI_MP, [("alpha_plane", (0, 0, 1, -2)), ("beta_plane", (0, 0, 1, -3))], "beta_plane"),
    "A6_beta_chua_xac_dinh_mang_he_so_mp_khong_ten": lambda: _p1_mat_phang(
        MOT_MP_KHONG_TEN_VA_BETA, [("beta", (0, 0, 1, -3))], "beta"),
    "A6b_bien_khong_ten_khi_de_nhac_hai_mat_phang": lambda: _p1_mat_phang(
        MOT_MP_KHONG_TEN_VA_BETA, [("mp_cat", (0, 0, 1, -3))], "mp_cat"),
    "A7_bien_khong_ten_hai_mat_phang_co_ten": lambda: _p1_mat_phang(
        HAI_MP, [("mp", (0, 0, 1, -3))], "mp"),
    "A8_bien_khong_ten_mat_phang_thu_hai_khong_ten": lambda: _p1_mat_phang(
        "Cho mặt phẳng z = 3. Một mặt phẳng song song với mặt phẳng đó cắt khối chóp theo thiết diện (T).",
        [("mp_cat", (0, 0, 1, -3))], "mp_cat"),
}
MP_DUNG_THUC_THE = {
    "A2_doi_chung_hai_mat_phang_dung_ten": lambda: _p1_mat_phang(
        HAI_MP, [("alpha_plane", (0, 0, 1, -3)), ("beta_plane", (0, 0, 1, -2))], "beta_plane"),
    "A3_ti_le_khac_0": lambda: _p1_mat_phang(
        "Mặt phẳng (α): z = 3 cắt khối chóp theo thiết diện (T).", [("alpha_plane", (0, 0, 2, -6))], "alpha_plane"),
    "A3b_ti_le_am": lambda: _p1_mat_phang(
        "Mặt phẳng (α): z = 3 cắt khối chóp theo thiết diện (T).", [("alpha_plane", (0, 0, -1, 3))], "alpha_plane"),
    "A4_doi_ten_nhat_quan_P": lambda: _p1_mat_phang(
        "Mặt phẳng (P): z = 3 cắt khối chóp theo thiết diện (T).", [("mp_P", (0, 0, 1, -3))], "mp_P"),
    "A4b_doi_ten_nhat_quan_gamma": lambda: _p1_mat_phang(
        "Mặt phẳng (γ): z = 3 cắt khối chóp theo thiết diện (T).", [("gammaPlane", (0, 0, 1, -3))], "gammaPlane"),
    "A5_khong_ten_duy_nhat": lambda: _p1_mat_phang(
        "Mặt phẳng z = 3 cắt khối chóp theo thiết diện (T).", [("mp_cat", (0, 0, 1, -3))], "mp_cat"),
    "A5b_bien_khong_ten_de_chi_mot_mat_phang": lambda: _p1_mat_phang(
        "Mặt phẳng (α): z = 3 cắt khối chóp theo thiết diện (T).", [("mp_cat", (0, 0, 1, -3))], "mp_cat"),
    "RF1_mat_phang_qua_ba_diem_ben_canh": lambda: _p1_mat_phang(
        "Mặt phẳng (α): z = 3 song song với mặt phẳng (ABCD) cắt khối chóp theo thiết diện (T).",
        [("alpha_plane", (0, 0, 1, -3))], "alpha_plane"),
}


def test_GUARD_w16_gia_tri_hien_thi_doi_theo_mat_phang_duoc_dung():
    """GUARD: đổi chéo hệ số α/β làm ĐỔI diện tích người học thấy (9 thay vì 16) — lỗi gắn
    thực thể ở đây không vô hại."""
    sai = W.bo_nho_cuoi(W.spec_cua(MP_SAI_THUC_THE["A2_hai_mat_phang_doi_cheo_he_so"]()[1]))["area_T"]
    dung = W.bo_nho_cuoi(W.spec_cua(MP_DUNG_THUC_THE["A2_doi_chung_hai_mat_phang_dung_ten"]()[1]))["area_T"]
    assert (sai, dung) == (9, 16)


@pytest.mark.parametrize("ca", sorted(MP_SAI_THUC_THE))
def test_w16_he_so_mat_phang_khong_gan_duoc_dung_thuc_the_khong_duoc_C0(ca):
    """Trùng bộ số KHÔNG là trùng thực thể (§14.1)."""
    kq = _kq(*MP_SAI_THUC_THE[ca]())
    assert kq.status != AN_TOAN, (ca, kq)
    assert any(d.startswith("PLANE_BINDING") for d in kq.details), (ca, kq.details)


@pytest.mark.parametrize("ca", sorted(MP_DUNG_THUC_THE))
def test_w16_he_so_mat_phang_gan_dung_thuc_the_van_duoc_C0(ca):
    kq = _kq(*MP_DUNG_THUC_THE[ca]())
    assert (kq.status, kq.certificate) == (AN_TOAN, "C0"), (ca, kq)


@pytest.mark.parametrize("ca", ["A1_beta_chua_xac_dinh_mang_he_so_alpha", "A2_hai_mat_phang_doi_cheo_he_so"])
def test_w16_tuyen_tu_choi_mat_phang_sai_thuc_the(ca):
    _sp, out, _sc = W.chay(*MP_SAI_THUC_THE[ca]())
    assert (out.servable, out.stage_reached) == (False, "assumption"), (ca, out.stage_reached, out.details[:3])


@pytest.mark.xfail(strict=True, reason="ISSUE-ARCH-ASSUMPTION-CONSTRUCTION-RELATION-NOT-SOURCE-BOUND: C0 gắn "
                   "literal với thực thể của nó, không kiểm phép dựng dùng đúng thực thể đề nói (§14.1, A′)")
def test_w16_gioi_han_A_phay_cat_bang_mat_phang_khac_mat_phang_de_noi():
    """(T) do (β) cắt; chương trình cắt bằng (α) — cả hai literal đều ghim đúng mặt phẳng của nó."""
    kq = _kq(*_p1_mat_phang(HAI_MP, [("alpha_plane", (0, 0, 1, -3)), ("beta_plane", (0, 0, 1, -2))],
                            "alpha_plane"))
    assert kq.status != AN_TOAN, kq


# ── §14.2 · quan hệ trong yêu cầu chứng minh không bao giờ là tiền đề ─────────────────

NEN_T1 = "Cho hình chóp S.ABC có "
DAY_T1 = "đáy ABC là tam giác vuông tại A, AB = 3, AC = 4"
HOI_T1 = " Tính thể tích khối chóp S.ABC."


def _t1_cau(text: str):
    """Chóp T1 (đề `text`, hợp đồng T1), chương trình compiler đúng của bài ĐỦ dữ kiện."""
    return W.hop_dong(text, W.chop_tam_giac_payload()), W.chuong_trinh(W.chop_tam_giac()[1])


MUC_TIEU_THANH_TIEN_DE = {
    "B1_chung_minh_SA_vuong_day": NEN_T1 + DAY_T1 + ", SA = 5. Chứng minh rằng SA vuông góc với đáy." + HOI_T1,
    "B1b_CMR_ky_hieu": NEN_T1 + DAY_T1 + ", SA = 5. CMR: SA ⊥ (ABC)." + HOI_T1,
    "B2_chung_minh_goc_vuong_day": NEN_T1 + "AB = 3, AC = 4. Cạnh bên SA vuông góc với đáy, SA = 5. "
                                            "Chứng minh rằng tam giác ABC vuông tại A." + HOI_T1,
    "B3b_kiem_tra_ky_hieu": NEN_T1 + DAY_T1 + ", SA = 5. Kiểm tra SA ⊥ (ABC)." + HOI_T1,
    "B3c_cau_hoi_hay_khong": NEN_T1 + DAY_T1 + ", SA = 5. SA ⊥ (ABC) hay không?" + HOI_T1,
    "B5_cau_ghep_gia_thiet_va_yeu_cau": NEN_T1 + "AB = 3, AC = 4, SA = 5. Biết SA vuông góc với đáy, "
                                                 "chứng minh rằng tam giác ABC vuông tại A." + HOI_T1,
    "B7_chung_minh_do_dai": NEN_T1 + DAY_T1 + ". Cạnh bên SA vuông góc với đáy. Chứng minh rằng SA = 5." + HOI_T1,
}
GIA_THIET_GIU_NGUYEN = {
    "B0_gia_thiet": W.CHOP_TAM_GIAC_TEXT,
    "B4b_phu_dinh_trong_yeu_cau": W.CHOP_TAM_GIAC_TEXT.replace(
        "Tính thể tích", "Chứng minh rằng SB không vuông góc với BC. Tính thể tích"),
    "B5b_gia_thiet_truoc_yeu_cau_cung_cau": NEN_T1 + DAY_T1 + ", SA = 5. Biết SA vuông góc với đáy, "
                                                              "chứng minh rằng AC vuông góc với (SAB)." + HOI_T1,
    "B6_tinh_biet_gia_thiet": NEN_T1 + DAY_T1 + ". Tính thể tích khối chóp S.ABC, biết cạnh bên SA vuông góc "
                                                "với đáy và SA = 5.",
}
KHONG_KHAI_THAC_DUOC = {
    "B3_hoi_co_khong": NEN_T1 + DAY_T1 + ", SA = 5. Hỏi SA có vuông góc với đáy không?" + HOI_T1,
    "B4_phu_dinh_gia_thiet": NEN_T1 + DAY_T1 + ". Cạnh bên SA không vuông góc với đáy, SA = 5." + HOI_T1,
}


@pytest.mark.parametrize("ca", sorted(MUC_TIEU_THANH_TIEN_DE))
def test_w16_quan_he_trong_yeu_cau_chung_minh_khong_la_tien_de(ca):
    kq = _kq(*_t1_cau(MUC_TIEU_THANH_TIEN_DE[ca]))
    assert kq.status != AN_TOAN, (ca, kq)
    assert any(d.startswith("GOAL_CLAUSE") for d in kq.details), (ca, kq.details)


@pytest.mark.parametrize("ca", sorted(GIA_THIET_GIU_NGUYEN))
def test_w16_gia_thiet_hop_le_van_la_tien_de(ca):
    """Giả thiết đứng trước yêu cầu (kể cả cùng câu), và `Tính …, biết <giả thiết>`, giữ nguyên."""
    kq = _kq(*_t1_cau(GIA_THIET_GIU_NGUYEN[ca]))
    assert (kq.status, kq.certificate) == (AN_TOAN, "C1"), (ca, kq)


@pytest.mark.parametrize("ca", sorted(KHONG_KHAI_THAC_DUOC))
def test_w16_cau_hoi_co_khong_va_phu_dinh_khong_doc_thanh_tien_de(ca):
    """Không khai thác được hôm nay (bộ đọc không khớp khi có chữ chen giữa) — giữ như vậy."""
    kq = _kq(*_t1_cau(KHONG_KHAI_THAC_DUOC[ca]))
    assert kq.status != AN_TOAN, (ca, kq)


def test_w16_chieu_cao_sau_tinh_bi_tu_choi_thua_khong_bao_gio_phu_thuoc():
    """`Tính …, biết chiều cao bằng 5`: bộ đọc chiều cao chỉ đọc phần dữ kiện ⇒ từ chối thừa,
    nhưng không bao giờ nói "đề không cho SA" (§14.2, ngoài W16)."""
    kq = _kq(*_t1_cau(NEN_T1 + DAY_T1 + ", cạnh bên SA vuông góc với đáy. Tính thể tích khối chóp S.ABC, "
                                       "biết chiều cao của khối chóp bằng 5."))
    assert kq.status == CHUA_RO, kq


def test_w16_muc_tieu_sau_tinh_khong_tao_phan_vi_du():
    """Ruling T3: đề có mệnh đề mục tiêu thì không thử phản ví dụ. Ở đây `SA = 5` chỉ nằm trong
    yêu cầu chứng minh ĐỨNG SAU `Tính` — ngoài phần dữ kiện `phan_chua_doc` soi — nên không có
    luật này cổng sẽ nói "đề không cho SA" với một đề có viết SA = 5."""
    text = (NEN_T1 + DAY_T1 + ". Cạnh bên SA vuông góc với đáy. Tính thể tích khối chóp S.ABC. "
            "Chứng minh rằng SA = 5.")
    kq = _kq(*_t1_cau(text))
    assert kq.status == CHUA_RO, kq
    assert "CE_GOAL_CLAUSE_PRESENT" in kq.details, kq.details


def test_w16_tuyen_tu_choi_yeu_cau_chung_minh_lam_tien_de():
    _sp, out, _sc = W.chay(*_t1_cau(MUC_TIEU_THANH_TIEN_DE["B1_chung_minh_SA_vuong_day"]))
    assert (out.servable, out.stage_reached) == (False, "assumption"), (out.stage_reached, out.details[:3])


# ── §14.3 · bốn nhánh đóng an toàn: ca kích hoạt, mã lý do, đối chứng hợp lệ ──────────

def _t1():
    _t, ct = W.chop_tam_giac()
    return ct, W.chuong_trinh(ct)


def _guard_if():
    ct, raw = _t1()
    raw["statements"].append({"kind": "if", "condition": {"kind": "literal", "value": True},
                              "then_body": [], "else_body": []})
    return ct, raw


def _guard_dinh_khuon():
    """S dời khỏi pháp tuyến tại A (A ở gốc): SA không còn ⊥ đáy."""
    ct, raw = _t1()
    _dat_diem(raw, "S", [1, 0, 5])
    return ct, raw


def _guard_khung():
    """Đề T1 đủ dữ kiện + `(P): z = 2` (phương trình theo khung toạ độ mà đề KHÔNG cho), mặt
    phẳng cắt khối trên lát cắt C1."""
    text = W.CHOP_TAM_GIAC_TEXT.replace(
        "Tính thể tích khối chóp S.ABC.",
        "Tính diện tích thiết diện (T) của khối chóp cắt bởi mặt phẳng (P): z = 2.")
    pay = W.chop_tam_giac_payload()
    pay["obligations"] = [{"kind": "area", "container": "T", "witness": "area_T"}]
    _ct0, raw = _t1()
    raw["memory_declarations"] += [{"name": "P", "type": "plane3"}, {"name": "T", "type": "section"},
                                   {"name": "area_T", "type": "float"}]
    raw["statements"] += [
        {"kind": "construct_plane_from_equation", "target_var": "P", "a": 0, "b": 0, "c": 1, "d": -2},
        {"kind": "construct_section", "target_var": "T", "solid": "khoi_chop", "plane": "P"},
        {"kind": "assign", "target_var": "area_T", "expr": {"kind": "measure", "quantity": "area", "of": "T"}}]
    return W.hop_dong(text, pay), raw


def _guard_bang_mat():
    """Một mặt chỉ có hai đỉnh — lược đồ IR nhận (không kiểm cỡ từng mặt), dựng hình bác."""
    ct, raw = _t1()
    next(s for s in raw["statements"] if s.get("kind") == "construct_solid")["faces"] = [
        [1, 2], [0, 1, 2], [0, 2, 3], [0, 3, 1]]
    return ct, raw


BON_NHANH = {"CLOSURE_UNSUPPORTED_KIND": _guard_if, "TEMPLATE_CONSTRAINT_VIOLATED": _guard_dinh_khuon,
             "FRAME_DEPENDENT": _guard_khung, "FORMATION_REJECTED": _guard_bang_mat}


def test_w16_doi_chung_bon_nhanh_la_C1():
    kq = _kq(*_t1())
    assert (kq.status, kq.certificate) == (AN_TOAN, "C1"), kq


def test_w16_nhanh_luong_dieu_khien_CLOSURE_UNSUPPORTED_KIND():
    kq = _kq(*_guard_if())
    assert (kq.status, kq.reason_code) == (CHUA_RO, "ASSUMPTION_INVARIANCE_UNPROVEN"), kq
    assert kq.details == ("CLOSURE_UNSUPPORTED_KIND control flow",), kq.details


def test_w16_nhanh_dinh_khuon_pha_rang_buoc_TEMPLATE_CONSTRAINT_VIOLATED():
    kq = _kq(*_guard_dinh_khuon())
    assert (kq.status, kq.reason_code) == (CHUA_RO, "ASSUMPTION_INVARIANCE_UNPROVEN"), kq
    assert kq.details[-1] == "T1 TEMPLATE_CONSTRAINT_VIOLATED apex edge ⊥ base", kq.details


def test_w16_nhanh_phep_dung_phu_thuoc_khung_FRAME_DEPENDENT():
    """Mặt phẳng từ phương trình trên lát cắt C1 là lý do trượt DUY NHẤT (hệ số tự nó có
    nguồn: đề cho đúng (P): z = 2)."""
    kq = _kq(*_guard_khung())
    assert (kq.status, kq.reason_code) == (CHUA_RO, "ASSUMPTION_INVARIANCE_UNPROVEN"), kq
    loi = [d for d in kq.details if d.startswith(("NO_ROLE", "FRAME_DEPENDENT", "UNCERTIFIED"))]
    assert loi == ["FRAME_DEPENDENT construct_plane_from_equation"], kq.details


def test_w16_nhanh_bang_mat_hong_FORMATION_REJECTED():
    kq = _kq(*_guard_bang_mat())
    assert (kq.status, kq.reason_code, kq.details) == (
        CHUA_RO, "ASSUMPTION_INVARIANCE_UNPROVEN", ("FORMATION_REJECTED",)), kq
