# -*- coding: utf-8 -*-
"""regular-square-pyramid-w02 — đường cao SO của chóp đều và nguồn chiều cao theo QUAN HỆ. 0 lượt gọi model.

C. Chóp tứ giác đều: khi tâm đáy là chân đường cao đã có cơ sở (ràng buộc "đều" có kiểu + tâm dựng bằng giao hai
   đường chéo đáy), bước bổ sung dựng hình (`formation`) dựng ĐOẠN từ đỉnh tới tâm — danh tính, vai trò
   `CONSTRUCT_HEIGHT` và xuất xứ `construct_segment` thật, không đổi nhãn suông.
E. Chiều cao của công thức thể tích được chọn bằng quan hệ hình học kiểm chính xác (đoạn mang số đo vuông góc mặt
   đáy, một đầu trên mặt đáy), không bằng giá trị. Tái hiện trước bản sửa: lăng trụ đứng mà chương trình khai
   `DF_length := AC_length` (cạnh đáy TRÊN, = 4 = chiều cao) và đo d(D, (ABC)) — công thức in `V = S(ABC) × DF`.
"""
from __future__ import annotations

from fractions import Fraction as F

import pytest

from app.simulation.semantic_program.formation import DUNG_CAO, hoan_thien_dung_hinh
from tests.geometry import route_cases as W
from tests.geometry.test_regular_square_pyramid import CA, NHAN, THE_TICH, ket_qua, _nap


def _vat(scene: dict) -> dict[str, dict]:
    return {o["id"]: o for o in scene["objects"]}


def _doan(scene: dict, a: str, b: str) -> list[dict]:
    return [o for o in scene["objects"] if o["type"] == "segment3" and set(o.get("endpoint_ids") or ()) == {a, b}]


# ── C. Đoạn SO ────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("ca", ["S1_side_height_volume", "S6_renamed_vertices", "S7_named_centre"])
def test_chop_deu_dung_doan_tu_dinh_toi_tam_vai_chieu_cao(ca):
    scene = ket_qua(ca)["scene"]
    so = _doan(scene, "S", "O")
    assert len(so) == 1, [o["id"] for o in scene["objects"] if o["type"] == "segment3"]
    so = so[0]
    assert so["producer"] == "construct_segment"
    assert DUNG_CAO in so["formation_roles"], so["formation_roles"]
    assert set(so["depends"]) == {"S", "O"}
    assert so["notation"] == "SO" and "SO" in so["label"]
    # Thứ tự dựng: tâm O có trước đoạn SO; đoạn SO có trước khi khép khối.
    buoc = {sid: min(i for i, st in enumerate(scene["formation"]["steps"]) if sid in st["visible_ids"])
            for sid in ("O", so["id"], "khoi_chop")}
    assert buoc["O"] < buoc[so["id"]] < buoc["khoi_chop"], buoc


def test_chop_khong_deu_khong_dung_doan_tu_dinh_toi_giao_duong_cheo():
    """Cùng chương trình (O = giao hai đường chéo) nhưng đề KHÔNG nói "đều": giao hai đường chéo không phải chân
    đường cao đã có cơ sở — không có đoạn SO. Bước bổ sung là hàm thuần, kiểm thẳng."""
    contract, prog = _nap("N2_not_regular")
    moi = hoan_thien_dung_hinh(W.spec_cua(prog), contract).spec
    cap = [{s.endpoint_a, s.endpoint_b} for s in moi.statements if s.kind == "construct_segment" and s.endpoint_a]
    assert {"S", "O"} not in cap, cap


def test_tam_sai_danh_tinh_khong_thanh_chan_duong_cao():
    """N4: O là trung điểm cạnh AB (không phải tâm). Không được dựng 'đường cao' SO từ một điểm sai danh tính."""
    contract, prog = _nap("N4_wrong_centre_identity")
    moi = hoan_thien_dung_hinh(W.spec_cua(prog), contract).spec
    cap = [{s.endpoint_a, s.endpoint_b} for s in moi.statements if s.kind == "construct_segment" and s.endpoint_a]
    assert {"S", "O"} not in cap, cap


def test_cong_thuc_the_tich_doc_chieu_cao_SO():
    scene = ket_qua("S1_side_height_volume")["scene"]
    o = _vat(scene)
    V = o[THE_TICH]
    assert V["formula"]["text"] == "V = 1/3 × S(ABCD) × SO = 16", V["formula"]
    assert [r["entity_id"] for r in V["formula"]["references"]] == ["dien_tich_day_ABCD", "chieu_cao_SO"]
    # Đại lượng đo được bám ĐOẠN SO đã dựng — không còn nhân chứng nét đứt chồng lên đoạn ấy.
    ann = o["chieu_cao_SO"]["annotation"]
    assert (ann["anchor"], sorted(ann["subject_ids"])) == ("segment", ["O", "S"]), ann
    assert "witness" not in ann


# ── E. Chiều cao theo quan hệ, không theo giá trị ─────────────────────────────────────────────

def _f(fid: str, nhan: str, v: str) -> dict:
    return {"id": fid, "kind": "float", "label": nhan, "value": [v]}


def lang_tru_canh_tren_bang_chieu_cao():
    """Lăng trụ đứng ABC.DEF, đáy vuông tại A, AB = 3, AC = 4, chiều cao 4. Chương trình khai `DF_length` chép
    `AC_length` (cạnh đáy trên DF = AC = 4 — TÌNH CỜ bằng chiều cao) và đo d(D, (ABC)) = 4."""
    van = ("Cho hình lăng trụ đứng ABC.DEF có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4, chiều cao bằng 4. "
           "Tính thể tích khối lăng trụ ABC.DEF.")
    pay = {"input_facts": [_f("f_ab", "AB", "3"), _f("f_ac", "AC", "4"), _f("f_h", "chiều cao", "4")],
           "obligations": [{"kind": "volume", "container": "khoi", "witness": "V"}],
           "solid_topology": {"solid_kind": "prism", "base_cycle": list("ABC"), "top_cycle": list("DEF"),
                              "correspondence": [["A", "D"], ["B", "E"], ["C", "F"]]}}
    mem = [{"name": n, "type": "float", "provenance": "GIVEN", "source_fact_id": fi, "initial_value": v}
           for n, fi, v in (("AB_length", "f_ab", "3"), ("AC_length", "f_ac", "4"), ("chieu_cao", "f_h", "4"))]
    mem += [{"name": p, "type": "point3", "provenance": "LAYOUT_DERIVED"} for p in "ABCDEF"]
    mem += [{"name": "DF_length", "type": "float"}, {"name": "day_ABC", "type": "polygon3"},
            {"name": "mp_day", "type": "plane3"}, {"name": "khoi", "type": "solid"}, {"name": "dt", "type": "float"},
            {"name": "h", "type": "float"}, {"name": "V", "type": "float"}]
    toa = {"A": "000", "B": "300", "C": "040", "D": "004", "E": "304", "F": "044"}
    st = [{"kind": "declare_point", "target_var": p, "at": list(v)} for p, v in toa.items()]
    st += [{"kind": "assign", "target_var": "DF_length", "expr": {"kind": "var", "name": "AC_length"}},
           {"kind": "construct_polygon", "target_var": "day_ABC", "vertices": list("ABC"), "label": "Đáy ABC"},
           {"kind": "construct_solid", "target_var": "khoi", "vertices": list("ABCDEF"),
            "faces": [list("ABC"), list("DEF"), list("ABED"), list("BCFE"), list("CADF")], "label": "ABC.DEF"},
           {"kind": "construct_plane", "target_var": "mp_day", "through": list("ABC")},
           {"kind": "assign", "target_var": "dt", "expr": {"kind": "measure", "quantity": "area", "of": "day_ABC"}},
           {"kind": "assign", "target_var": "h",
            "expr": {"kind": "measure", "quantity": "distance", "of": "D", "wrt": "mp_day"}},
           {"kind": "assign", "target_var": "V", "expr": {"kind": "measure", "quantity": "volume", "of": "khoi"}}]
    return W.hop_dong(van, pay), {"spec_version": "1.0", "title": "Lăng trụ ABC.DEF", "memory_declarations": mem,
                                  "statements": st}


def test_canh_tinh_co_bang_chieu_cao_khong_thanh_chieu_cao_cua_cong_thuc():
    _sp, out, scene = W.chay(*lang_tru_canh_tren_bang_chieu_cao())
    assert out.servable, (out.stage_reached, out.reason_code, out.details)
    V = _vat(scene)["V"]
    refs = [r["entity_id"] for r in (V.get("formula") or {}).get("references", [])]
    assert "DF_length" not in refs, V.get("formula")
    assert refs == ["dt", "h"], V.get("formula")
    # Đính chính kỳ vọng (ghi ở REPORT §đính chính, trước commit sửa): lúc viết test đỏ tôi kỳ vọng ký hiệu
    # `d(D, (ABC))`. Khoảng cách đo có chân là A, và cạnh bên AD đã được bước bổ sung dựng ⇒ nó bám đoạn AD —
    # đúng chiều cao của lăng trụ đứng. Điều test khoá không đổi: DF không bao giờ là chiều cao.
    assert V["formula"]["text"] == "V = S(ABC) × AD = 24"


#: Công thức của sáu họ cũ trước W2 — mọi chiều cao ở đây là cạnh VUÔNG GÓC đáy thật, nên luật quan hệ phải giữ
#: nguyên chúng (hồi quy, không phải kỳ vọng mới).
SAU_HO = {
    "chop_tam_giac": ("V = 1/3 × S(ABC) × SA = 10", ["dien_tich_day_ABC", "SA_length"]),
    "lang_tru_tam_giac": ("V = S(ABC) × AD = 30", ["dien_tich_day_ABC", "AD_length"]),
    "chop_chu_nhat": ("V = 1/3 × S(ABCD) × SA = 24", ["dien_tich_day_ABCD", "SA_length"]),
    "hop_chu_nhat": ("V = S(ABCD) × AA′ = 60", ["dien_tich_day_ABCD", "AA_prime_length"]),
    "lap_phuong": ("V = S(ABCD) × AA′ = 64", ["dien_tich_day_ABCD", "AA_prime_length"]),
    "lang_tru_day_vuong": ("V = S(ABCD) × AA′ = 63", ["dien_tich_day_ABCD", "AA_prime_length"]),
}


@pytest.mark.parametrize("ho", sorted(SAU_HO))
def test_nguon_chieu_cao_cua_sau_ho_cu_khong_doi(ho):
    _text, contract = W.HO[ho]()
    _sp, out, scene = W.chay(contract)
    assert out.servable
    V = next(o for o in scene["objects"] if o.get("producer") == "measure.volume")
    text, refs = SAU_HO[ho]
    assert V["formula"]["text"] == text
    assert [r["entity_id"] for r in V["formula"]["references"]] == refs


def test_canh_ben_vuong_goc_gia_tri_bang_khoang_cach_van_la_chieu_cao():
    """Chóp đáy chữ nhật, SA ⊥ đáy, chương trình khai SA_length VÀ đo d(S, (ABC)): SA vẫn là chiều cao — vì SA
    vuông góc mặt đáy (kiểm chính xác), không vì hai giá trị bằng nhau."""
    from tests.geometry.test_regular_square_pyramid import _chop_chu_nhat_co_ca_SA_va_khoang_cach
    _sp, out, scene = W.chay(*_chop_chu_nhat_co_ca_SA_va_khoang_cach())
    assert out.servable
    assert _vat(scene)[THE_TICH]["formula"]["text"] == "V = 1/3 × S(ABCD) × SA = 24"


def test_canh_ben_xien_cua_chop_deu_khong_thanh_chieu_cao():
    contract, prog = CA["S4_side_lateral_volume"]()
    for m in prog["memory_declarations"]:
        if m["name"] == "canh_ben":
            m["name"] = "SA_length"
    _sp, out, scene = W.chay(contract, prog)
    assert out.servable, (out.stage_reached, out.reason_code, out.details)
    V = _vat(scene)[THE_TICH]
    assert [r["entity_id"] for r in V["formula"]["references"]] == ["dien_tich_day_ABCD", "chieu_cao_SO"]
    assert "× SA" not in V["formula"]["text"]


def test_nhan_cua_ca_dung_trong_ho_so_w02():
    assert NHAN["S1_side_height_volume"]["expect"] == "served:16"


# ── Độ dài không dương do chính đề ghi (ISSUE-ARCH-DEFAULT-ROUTE-NON-POSITIVE-LENGTH-CAUSE) ───────────────────

def _khong_duong(van_canh: str, s: str):
    from fractions import Fraction as Fr

    from tests.geometry import test_regular_square_pyramid as RSP
    van = RSP.NHAN["S1_side_height_volume"]["text"].replace("cạnh đáy bằng 4", f"cạnh đáy bằng {van_canh}")
    return RSP._ca("S1_side_height_volume", s=Fr(0), van=van, gf=RSP._g(
        ((("canh_day", "f_canh_day", s),), (RSP._f("f_canh_day", "cạnh đáy", s),)), RSP.CAO_3))


def test_de_ghi_canh_day_bang_0_la_loi_cua_de():
    """Đề tự ghi 'cạnh đáy bằng 0': kernel từ chối đáy suy biến ở `execution`. Nguyên nhân CHẮC CHẮN là đề — một
    độ dài ≤ 0 không có hình nào — nên lời từ chối nói đúng điều ấy (SOURCE), không UNKNOWN."""
    _sp, out, _scene = W.chay(*_khong_duong("0", "0"))
    assert not out.servable and out.stage_reached == "execution"
    assert (out.reason_code, out.refusal_cause, out.reason_subjects) == ("NON_POSITIVE_LENGTH", "SOURCE", ["cạnh đáy"])


def test_de_hop_le_ma_he_dung_suy_bien_khong_bi_goi_la_loi_de():
    """Đối chứng: đề ghi 'cạnh đáy bằng 4' (hợp lệ), chương trình đặt đáy suy biến. Hệ không gọi đề sai."""
    _sp, out, _scene = W.chay(*_khong_duong("4", "4"))
    assert not out.servable and out.stage_reached == "execution"
    assert out.refusal_cause == "UNKNOWN" and out.reason_code != "NON_POSITIVE_LENGTH"


@pytest.mark.parametrize("nhan", ["canh_day", "canhDay"])
def test_nhan_InputFact_kieu_token_may_khong_len_be_mat_hoc_sinh(nhan):
    """Tự rà soát W1 (Minor, hoãn): GIVEN không ký hiệu mượn nguyên nhãn InputFact; nhãn mô hình kiểu token máy sẽ
    lên bề mặt học sinh. Nay nhãn ấy không được mượn."""
    from tests.geometry import test_regular_square_pyramid as RSP
    contract, prog = RSP._ca("S1_side_height_volume", s=F(4), gf=RSP._g(
        ((("canh_day", "f_canh_day", "4"),), (RSP._f("f_canh_day", nhan, "4"),)), RSP.CAO_3))
    _sp, out, scene = W.chay(contract, prog)
    o = _vat(scene)["canh_day"] if scene else None
    assert o is not None, (out.stage_reached, out.reason_code, out.details)
    for chu in (o["label"], o.get("reference") or "", (o.get("formula") or {}).get("text", "")):
        assert "_" not in chu and (nhan[0].upper() + nhan[1:]) not in chu, chu
