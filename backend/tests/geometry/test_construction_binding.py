# -*- coding: utf-8 -*-
"""W18 — phép dựng ĐIỂM phải gắn với quan hệ của đề bằng DANH TÍNH (amendment §16). 0 lượt gọi.

Ca và kỳ vọng ghi TRƯỚC bản sửa ở
`docs/evaluation/geometry/runs/w18-binding-focus/diagnostics/construction_corpus_w18/LABELS.json`;
test đọc nhãn từ đó, không chép lại. Mỗi ca dựng trên đề gold p1 (toạ độ đề cho, khối chóp S.ABCD)
hoặc họ hình hộp chữ nhật (đỉnh A′), và chạy qua đúng route sản phẩm (`w14_cases.chay`).

Phép dò Phase 1 (trước bản sửa): hình chiếu lên sai đường/mặt phẳng, danh sách "lần lượt" bị tráo
đích, đích đổi tên và hai thực thể trùng toạ độ đều được PHỤC VỤ; trung điểm sai đoạn khi tên khớp
chỉ bị bất biến toạ độ chặn, với mã chung.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tests.geometry import w14_cases as W

NHAN = json.loads((Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/w18-binding-focus"
                   / "diagnostics/construction_corpus_w18/LABELS.json").read_text(encoding="utf-8"))["rows"]

NEN_P1 = ("Trong không gian Oxyz, cho khối chóp S.ABCD có đáy ABCD là hình vuông với A(0;0;0), "
          "B(6;0;0), C(6;6;0), D(0;6;0) và đỉnh S(0;0;6). ")


def _mid(t: str, a: str, b: str) -> dict:
    return {"kind": "construct_point", "target_var": t, "expr": {"kind": "midpoint", "a": a, "b": b}}


def _chia(t: str, a: str, b: str, k: str) -> dict:
    return {"kind": "construct_point", "target_var": t, "expr": {"kind": "divide_segment", "a": a, "b": b, "ratio": k}}


def _proj(t: str, p: str, r: str) -> dict:
    return {"kind": "construct_point", "target_var": t, "expr": {"kind": "project_onto", "point": p, "target": r}}


def _giao(t: str, d1: str, d2: str) -> dict:
    return {"kind": "construct_point", "target_var": t,
            "expr": {"kind": "intersect_line_line", "line_a": d1, "line_b": d2}}


def _duong(t: str, a: str, b: str) -> dict:
    return {"kind": "construct_line", "target_var": t, "through_a": a, "through_b": b}


def _mp(t: str, qua: list[str]) -> dict:
    return {"kind": "construct_plane", "target_var": t, "through": qua}


def _gan(t: str, nguon: str) -> dict:
    return {"kind": "assign", "target_var": t, "expr": {"kind": "var", "name": nguon}}


def _p1(van: str, them: list[dict], of: str, wrt: str, *, khai: tuple = (), facts: tuple = (),
        nen: str = NEN_P1, co_khoi: bool = True):
    """Đề gold p1 + `van`, chương trình: các điểm/đáy/khối của p1 + `them` + d_kq = d(of, wrt).

    `co_khoi=False`: chỉ năm điểm và dữ kiện toạ độ của chúng (đề ngoài vùng đa diện)."""
    from scripts import replay_negative_boundaries as RNB

    goc = RNB.doc_raw_theo_thu_tu("p1_chop_thiet_dien_khoang_cach")
    pay = json.loads(goc["semantic_analyze"][0])
    bo = {"alpha_plane_def", "T_section_def"} | (set() if co_khoi else {"s_abcd_pyramid", "abcd_square"})
    pay["input_facts"] = [f for f in pay["input_facts"] if f["id"] not in bo] + [dict(f) for f in facts]
    pay["obligations"] = [{"kind": "distance", "container": wrt, "witness": "d_kq", "wrt": of}]
    raw = json.loads(goc["semantic_program"][0])
    raw["memory_declarations"] = ([m for m in raw["memory_declarations"] if co_khoi and m["name"] == "S.ABCD"]
                                  + [{"name": "d_kq", "type": "float"}] + [dict(k) for k in khai])
    giu = ("declare_point", "construct_polygon", "construct_solid") if co_khoi else ("declare_point",)
    st = [s for s in raw["statements"] if s["kind"] in giu]
    st += [copy.deepcopy(x) for x in them]
    st.append({"kind": "assign", "target_var": "d_kq",
               "expr": {"kind": "measure", "quantity": "distance", "of": of, "wrt": wrt}})
    raw["statements"] = st
    return W.hop_dong(nen + van, pay), raw


HOP_DE = "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 5. "


def _hop(van: str, them: list[dict], of: str, wrt: str):
    """Hình hộp chữ nhật (họ W14, chương trình compiler) + `van`, thêm `them` + d_kq = d(of, wrt)."""
    from tests.geometry import test_cuboid_cube_production_route as M

    t0, pay0 = M._cuboid_p01_payload()
    raw = W.chuong_trinh(W.hop_dong(t0, pay0))
    pay = copy.deepcopy(pay0)
    pay["obligations"] = [{"kind": "distance", "container": wrt, "witness": "d_kq", "wrt": of}]
    raw["memory_declarations"].append({"name": "d_kq", "type": "float"})
    raw["statements"] += [copy.deepcopy(x) for x in them] + [
        {"kind": "assign", "target_var": "d_kq",
         "expr": {"kind": "measure", "quantity": "distance", "of": of, "wrt": wrt}}]
    return W.hop_dong(HOP_DE + van, pay), raw


def _van(ca: str) -> str:
    return NHAN[ca]["text"].removeprefix("cuboid + ")


CA = {
    "B1_mid_ok": lambda: _p1(_van("B1_mid_ok"), [_mid("M", "S", "A")], "M", "C"),
    "B2_mid_wrong_SB": lambda: _p1(_van("B2_mid_wrong_SB"), [_mid("M", "S", "B")], "M", "C"),
    "B3_mid_swap_ends": lambda: _p1(_van("B3_mid_swap_ends"), [_mid("M", "A", "S")], "M", "C"),
    "B4_mid_same_value_SB": lambda: _p1(_van("B4_mid_same_value_SB"),
                                        [_mid("M", "S", "A"), _mp("day", ["A", "B", "C"])], "M", "day"),
    "B5_list_swap_targets": lambda: _p1(_van("B5_list_swap_targets"),
                                        [_mid("M", "S", "B"), _mid("N", "S", "A")], "M", "C"),
    "B6_list_ok": lambda: _p1(_van("B6_list_ok"), [_mid("M", "S", "A"), _mid("N", "S", "B")], "M", "N"),
    "B7_rename_target_X": lambda: _p1(_van("B7_rename_target_X"), [_mid("X", "S", "A")], "X", "C"),
    "B8_alias_ok": lambda: _p1(
        _van("B8_alias_ok"), [_mid("M_tam", "S", "A"), _gan("M", "M_tam")], "M", "C",
        khai=({"name": "M_tam", "type": "point3"}, {"name": "M", "type": "point3", "source_fact_id": "M_def"}),
        facts=({"id": "M_def", "kind": "str", "label": "Trung điểm M", "value": ["M là trung điểm của SA"]},)),
    "B9_same_coord_diff_identity": lambda: _p1(
        _van("B9_same_coord_diff_identity"),
        [_mp("day", ["A", "B", "C"]), _proj("H", "S", "day"), _mid("M", "S", "A")], "M", "C"),
    "B10_proj_line_ok": lambda: _p1(_van("B10_proj_line_ok"),
                                    [_duong("BD", "B", "D"), _proj("H", "S", "BD")], "S", "H"),
    "B11_proj_line_wrong_BC": lambda: _p1(_van("B11_proj_line_wrong_BC"),
                                          [_duong("BC", "B", "C"), _proj("H", "S", "BC")], "S", "H"),
    "B12_proj_plane_ok_SBD": lambda: _p1(_van("B12_proj_plane_ok_SBD"),
                                         [_mp("SBD", ["S", "B", "D"]), _proj("H", "A", "SBD")], "A", "H"),
    "B13_proj_plane_wrong_SBC": lambda: _p1(_van("B13_proj_plane_wrong_SBC"),
                                            [_mp("SBC", ["S", "B", "C"]), _proj("H", "A", "SBC")], "A", "H"),
    "B14_proj_plane_3_of_4": lambda: _p1(_van("B14_proj_plane_3_of_4"),
                                         [_mp("day", ["A", "B", "C"]), _proj("H", "S", "day")], "S", "H"),
    "B15_foot_wording_ok": lambda: _p1(_van("B15_foot_wording_ok"),
                                       [_duong("BD", "B", "D"), _proj("H", "S", "BD")], "S", "H"),
    "B16_out_of_vocab_ok": lambda: _p1(_van("B16_out_of_vocab_ok"), [_mid("M", "S", "A")], "M", "C"),
    "B17_auxiliary_foot": lambda: _p1(_van("B17_auxiliary_foot"),
                                      [_duong("BD", "B", "D"), _proj("K", "S", "BD")], "S", "K"),
    "B18_prime_ok": lambda: _hop(_van("B18_prime_ok"), [_mid("M", "A", "A_prime")], "M", "C"),
    "B19_prime_wrong": lambda: _hop(_van("B19_prime_wrong"), [_mid("M", "A", "B_prime")], "M", "C"),
    "B20_divide_half_ok": lambda: _p1(_van("B20_divide_half_ok"), [_chia("M", "S", "A", "1/2")], "M", "C"),
    "B21_not_realized": lambda: _p1(_van("B21_not_realized"), [], "S", "C"),
    "B22_out_of_scope_intersection": lambda: _p1(
        _van("B22_out_of_scope_intersection"),
        [_duong("AC", "A", "C"), _duong("BD", "B", "D"), _giao("O", "AC", "BD")], "S", "O"),
    "B23_projection_base_wording": lambda: _p1(_van("B23_projection_base_wording"),
                                               [_mp("day", ["A", "B", "C"]), _proj("H", "S", "day")], "S", "H"),
}


def test_moi_hang_nhan_co_mot_ca_va_nguoc_lai():
    assert set(CA) == set(NHAN)


# ── bộ đọc quan hệ (§16.1) ─────────────────────────────────────────────────────────────────

def _doc(van: str):
    from app.simulation.semantic_program.construction_binding import doc_quan_he_dung

    return {(q.kind, q.dich, q.toan_hang) for q in doc_quan_he_dung(NEN_P1 + van)}


def test_w18_doc_trung_diem_mot_dich_va_danh_sach_lan_luot_theo_thu_tu():
    S = frozenset
    assert _doc("Gọi M, N lần lượt là trung điểm của SA, SB. Gọi P là trung điểm cạnh SC.") == {
        ("midpoint", "M", S({"S", "A"})), ("midpoint", "N", S({"S", "B"})), ("midpoint", "P", S({"S", "C"}))}
    assert _doc("Gọi M, N và P lần lượt là trung điểm các cạnh SA, SB và SC.") == {
        ("midpoint", "M", S({"S", "A"})), ("midpoint", "N", S({"S", "B"})), ("midpoint", "P", S({"S", "C"}))}


def test_w18_danh_sach_lech_so_luong_khong_cho_quan_he():
    assert _doc("Gọi M, N lần lượt là trung điểm của SA, SB, SC.") == set()


def test_w18_doc_hinh_chieu_hai_vai_tro_va_dich_nhan():
    assert _doc("Gọi H là hình chiếu vuông góc của S lên đường thẳng BD.") == {
        ("projection", "H", ("S", ("line", frozenset({"B", "D"}))))}
    assert _doc("Gọi H là hình chiếu của A trên mặt phẳng (SBD).") == {
        ("projection", "H", ("A", ("plane", frozenset({"S", "B", "D"}))))}
    assert _doc("Gọi H là chân đường vuông góc hạ từ S xuống BD.") == {
        ("projection", "H", ("S", ("line", frozenset({"B", "D"}))))}
    assert _doc("Gọi H là hình chiếu của S lên mặt đáy.") == {
        ("projection", "H", ("S", ("plane", frozenset({"A", "B", "C", "D"}))))}


def test_w18_cach_noi_ngoai_tu_vung_va_menh_de_muc_tieu_khong_cho_quan_he():
    assert _doc("Gọi M là điểm chính giữa của đoạn SA.") == set()
    assert _doc("Chứng minh rằng M là trung điểm của SA.") == set()


def test_w18_hai_cau_noi_khac_nhau_ve_mot_dich_thi_bo_ca_hai():
    assert _doc("Gọi M là trung điểm của SA. Gọi M là trung điểm của SB.") == set()


# ── route sản phẩm theo nhãn đăng ký (§16.3, §16.4) ──────────────────────────────────────────

@pytest.mark.parametrize("ca", sorted(CA))
def test_w18_tuyen_san_pham_theo_nhan(ca):
    _sp, out, _sc = W.chay(*CA[ca]())
    e = NHAN[ca]["expect"]
    if e == "served":
        assert out.servable, (ca, out.stage_reached, out.reason_code, out.details[:4])
    else:
        _r, stage, ma, nguyen_nhan = e.split(":")
        assert (out.servable, out.stage_reached, out.reason_code, out.refusal_cause) == (
            False, stage, ma, nguyen_nhan), (ca, out.stage_reached, out.reason_code, out.details[:4])


@pytest.mark.parametrize("ca", sorted(c for c in CA if NHAN[c]["binding"]))
def test_w18_trang_thai_doi_chieu_cua_phep_dung(ca):
    _sp, out, _sc = W.chay(*CA[ca]())
    for dich, trang_thai in NHAN[ca]["binding"].items():
        assert out.construction_binding.get(dich) == trang_thai, (ca, dich, out.construction_binding)


def test_w18_tu_choi_neu_hai_quan_he_bang_ky_hieu_hoc_sinh():
    _sp, out, _sc = W.chay(*CA["B2_mid_wrong_SB"]())
    assert out.reason_subjects == ["M là trung điểm của SA", "M là trung điểm của SB"], out.reason_subjects
    _sp, out, _sc = W.chay(*CA["B11_proj_line_wrong_BC"]())
    assert out.reason_subjects == ["H là hình chiếu của S lên BD", "H là hình chiếu của S lên BC"], out.reason_subjects


# ── vùng thi hành (§16.4): MISMATCHED ở mọi vùng, UNVERIFIED chỉ trong vùng đa diện ─────────────

NGOAI_VUNG = "Trong không gian Oxyz, cho các điểm A(0;0;0), B(6;0;0), C(6;6;0), D(0;6;0) và S(0;0;6). "


def _ngoai(van: str, them: list[dict], of: str, wrt: str):
    return _p1(van, them, of, wrt, nen=NGOAI_VUNG, co_khoi=False)


def test_w18_lech_ngoai_vung_da_dien_van_bi_tu_choi():
    _sp, out, _sc = W.chay(*_ngoai("Gọi M là trung điểm của SA. Tính độ dài đoạn MC.", [_mid("M", "S", "B")], "M", "C"))
    assert (out.servable, out.stage_reached, out.reason_code) == (
        False, "construction_binding", "CONSTRUCTION_NOT_TEXT_BOUND"), (out.stage_reached, out.details[:3])


def test_w18_chua_doi_chieu_ngoai_vung_da_dien_chi_ghi_lai():
    _sp, out, _sc = W.chay(*_ngoai("Gọi M là điểm chính giữa của đoạn SA. Tính độ dài đoạn MC.",
                                   [_mid("M", "S", "A")], "M", "C"))
    assert out.servable and out.construction_binding.get("M") == "UNVERIFIED", (
        out.stage_reached, out.reason_code, out.construction_binding)


# ── xuất xứ trong cảnh (§16.3): điểm phụ không bao giờ là dữ kiện ─────────────────────────────

def _vat(sc: dict, oid: str) -> dict:
    return next(o for o in sc["objects"] if o["id"] == oid)


def test_w18_diem_phu_tro_mang_xuat_xu_phu_tro_diem_cua_de_mang_quan_he():
    _sp, out, sc = W.chay(*CA["B17_auxiliary_foot"]())
    assert out.servable and sc is not None
    k = _vat(sc, "K")
    assert (k["source"].get("binding"), k.get("origin")) == ("AUXILIARY", "derived"), k
    _sp, out, sc = W.chay(*CA["B1_mid_ok"]())
    assert _vat(sc, "M")["source"].get("binding") == "TEXT_RELATION", _vat(sc, "M")


# ── nguyên nhân và lời cho người học (§16.4) ─────────────────────────────────────────────────

def test_w18_ma_chua_doi_chieu_co_nguyen_nhan_chua_ro_va_khong_gui_di_sua():
    from app.ai.pipeline import KHONG_SUA_NGUON
    from app.simulation.semantic_program.refusal_cause import theo_ma

    assert theo_ma("CONSTRUCTION_BINDING_UNVERIFIED") == "UNKNOWN"
    assert theo_ma("CONSTRUCTION_NOT_TEXT_BOUND") == "CONSTRUCTION"
    assert "CONSTRUCTION_BINDING_UNVERIFIED" in KHONG_SUA_NGUON


def _loi(**env) -> str:
    from app.learner_messages import learner_reason

    return learner_reason({"status": "unsupported", "error_code": "input_not_grounded",
                           "stage_reached": "construction_binding", **env})


def test_w18_loi_lech_phep_dung_neu_hai_quan_he_va_khong_bao_sua_de():
    msg = _loi(reason_code="CONSTRUCTION_NOT_TEXT_BOUND", refusal_cause="CONSTRUCTION",
               reason_subjects=["M là trung điểm của SA", "M là trung điểm của SB"])
    assert "M là trung điểm của SA" in msg and "M là trung điểm của SB" in msg, msg
    assert "đề không cần sửa" in msg and "thiết diện" not in msg, msg


def test_w18_loi_chua_doi_chieu_khong_noi_de_sai():
    msg = _loi(reason_code="CONSTRUCTION_BINDING_UNVERIFIED", refusal_cause="UNKNOWN", reason_subjects=["M"])
    assert "chưa đối chiếu" in msg and "M" in msg, msg
    for cam in ("sửa đề", "kiểm tra lại đề", "đề sai", "đề bài sai"):
        assert cam not in msg, (cam, msg)
