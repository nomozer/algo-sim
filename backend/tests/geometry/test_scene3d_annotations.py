# -*- coding: utf-8 -*-
"""W17 · §15.4 — SỐ ĐO TRÊN HÌNH: backend sở hữu việc gắn đại lượng với chủ thể hình học.

`annotation = {kind, category, subject_ids, anchor, unit}` trên vật `quantity`:
- độ dài đề cho ↦ đoạn bộ đọc đề của server đọc tại span bằng chứng GIVEN, kiểm bằng khoảng cách
  CHÍNH XÁC trong bộ nhớ cuối; số trơn không nhãn đoạn ⇒ không gắn + chẩn đoán;
- đại lượng suy ra ↦ toán hạng IR của phép đo (diện tích → miền, thể tích → khối, khoảng cách → cặp);
- đích dùng CHUNG danh tính với đại lượng nó trỏ tới — bí danh không có nhãn thứ hai.
"""
from __future__ import annotations

import pytest

from tests.geometry import route_cases as W

KHONG_DON_VI = None


def _canh_ho(ho: str) -> dict:
    _t, ct = W.HO[ho]()
    _sp, out, sc = W.chay(ct)
    assert sc is not None, (ho, out.stage_reached)
    return sc


def _canh_gold(cid: str) -> dict:
    _t, ct, raw = W.gold(cid)
    _sp, out, sc = W.chay(ct, raw)
    assert sc is not None, (cid, out.stage_reached)
    return sc


#: Trường W17 của `annotation`; W18 (§16.5–16.7) thêm `role`, `same_as`, `witness` — kiểm ở phần W18.
_TRUONG_W17 = ("kind", "category", "subject_ids", "anchor", "unit")


def _ann(sc: dict) -> dict:
    return {o["id"]: ({k: v for k, v in o["annotation"].items() if k in _TRUONG_W17} if o.get("annotation") else None)
            for o in sc["objects"] if o["type"] == "quantity"}


def _ann18(sc: dict) -> dict:
    return {o["id"]: o.get("annotation") for o in sc["objects"] if o["type"] == "quantity"}


def _gan(kind: str, category: str, subject_ids: list[str], anchor: str) -> dict:
    return {"kind": kind, "category": category, "subject_ids": subject_ids, "anchor": anchor, "unit": KHONG_DON_VI}


def test_lang_tru_du_kien_so_do_va_ket_qua_gan_dung_chu_the():
    a = _ann(_canh_ho("lang_tru_tam_giac"))
    assert a["AB_length"] == _gan("length", "measurement", ["A", "B"], "segment")
    assert a["AC_length"] == _gan("length", "measurement", ["A", "C"], "segment")
    assert a["AD_length"] == _gan("length", "measurement", ["A", "D"], "segment")
    assert a["dien_tich_day_ABC"] == _gan("area", "measurement", ["day_ABC"], "region")
    assert a["the_tich_solid_ABCDEF"] == _gan("volume", "result", ["solid_ABCDEF"], "solid")
    # đích bí danh dùng CHUNG danh tính với phép đo nó trỏ tới: không có nhãn thứ hai
    assert a["the_tich_lang_tru"] is None


def test_hinh_hop_do_dai_co_phay_gan_dung_dinh():
    a = _ann(_canh_ho("hop_chu_nhat"))
    assert a["AA_prime_length"] == _gan("length", "measurement", ["A", "A_prime"], "segment")
    assert a["V"] is None and a["the_tich_khoi_hop"]["category"] == "result"


def test_mot_chu_the_mot_nhan_du_kien_truoc():
    """Hình hộp: độ dài đề cho AA′ và chiều cao đo được AA′ là CÙNG một số trên CÙNG một đoạn —
    một nhãn (của dữ kiện), không hai nhãn chồng tại một điểm neo.

    W18 §16.6 (thay đổi có chủ đích): phép đo trùng chủ thể không còn bị BỎ gắn mà mang `same_as`
    trỏ về dữ kiện — vẫn một nhãn trên hình (frontend không vẽ nhãn `same_as`), nhưng bảng chi tiết
    và lời giải biết hai dòng là một phép đo. Tiêu chí vẫn là chủ thể, không bao giờ là giá trị."""
    sc = _canh_ho("hop_chu_nhat")
    a = _ann18(sc)
    assert a["AA_prime_length"]["subject_ids"] == ["A", "A_prime"] and "same_as" not in a["AA_prime_length"]
    assert a["chieu_cao_AA_prime"]["same_as"] == "AA_prime_length"
    assert "ANNOTATION_SAME_AS chieu_cao_AA_prime: AA_prime_length" in sc["diagnostics"]


def test_do_dai_de_cho_kiem_bang_khoang_cach_chinh_xac():
    """Đề nói AB = 3; chương trình đặt B cách A một khoảng 4 ⇒ nhãn "AB = 3" KHÔNG được gắn lên đoạn AB
    (khoảng cách chính xác trong bộ nhớ cuối là điều kiện gắn, không phải tên biến)."""
    from app.simulation.semantic_program.formation import hoan_thien_dung_hinh
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
    from app.simulation.semantic_program.simulation_state import build_simulation_state
    from tests.geometry.test_assumption_certificate import _dat_diem

    _t, ct = W.HO["lang_tru_tam_giac"]()
    raw = W.chuong_trinh(ct)
    _dat_diem(raw, "B", [4, 0, 0])
    _dat_diem(raw, "E", [4, 0, 5])     # E trên B: lăng trụ vẫn hợp lệ, chỉ |AB| = 4
    spec = hoan_thien_dung_hinh(W.spec_cua(raw), ct).spec
    st = build_simulation_state(spec, SemanticProgramInterpreter().execute(spec), ct)
    assert "AB_length" not in st["annotations"], st["annotations"].get("AB_length")
    assert "ANNOTATION_UNBOUND AB_length: the figure's AB is not 3" in st["annotation_diagnostics"]
    assert st["annotations"]["AC_length"]["subject_ids"] == ["A", "C"]


def test_thiet_dien_va_khoang_cach_gan_mien_va_cap():
    a = _ann(_canh_gold("p1_chop_thiet_dien_khoang_cach"))
    assert a["area_T"] == _gan("area", "result", ["T"], "region")
    assert a["the_volume_sabcd"] == _gan("volume", "result", ["S.ABCD"], "solid")
    # W18 §16.7 (thay đổi có chủ đích): khoảng cách điểm → đường neo ở nhân chứng (trung điểm đoạn tới chân).
    assert a["dist_S_BD"] == _gan("distance", "result", ["S", "BD"], "witness")


def test_so_tron_khong_nhan_doan_thi_khong_gan_va_co_chan_doan():
    """Lập phương "có cạnh bằng 4": đề không gắn con số với một ĐOẠN có tên — không đoán đoạn."""
    sc = _canh_ho("lap_phuong")
    a = _ann(sc)
    assert a["AB_length"] is None
    assert any(d.startswith("ANNOTATION_UNBOUND AB_length") for d in sc.get("diagnostics", [])), sc.get("diagnostics")
    assert a["the_tich_khoi_hop"]["category"] == "result"


@pytest.mark.parametrize("ho", sorted(W.HO))
def test_moi_annotation_tro_toi_vat_co_trong_canh(ho):
    sc = _canh_ho(ho)
    co = {o["id"] for o in sc["objects"]}
    for qid, an in _ann(sc).items():
        if an is not None:
            assert set(an["subject_ids"]) <= co, (ho, qid, an)
            assert an["category"] in ("measurement", "result") and an["anchor"] in (
                "segment", "region", "solid", "pair", "witness")


# ══ W18 · §16.5–16.7 — vai trò, gộp trình bày, nhân chứng khoảng cách ══════════════════════════

def test_vai_tro_du_kien_trung_gian_ket_qua():
    a = _ann18(_canh_ho("lang_tru_tam_giac"))
    assert (a["AB_length"]["role"], a["dien_tich_day_ABC"]["role"], a["the_tich_solid_ABCDEF"]["role"]) == (
        "given", "intermediate", "result")
    assert a["the_tich_solid_ABCDEF"]["category"] == "result"        # `category` giữ cho envelope v109


def _p1(van: str, them: list, of: str, wrt: str, **kw):
    from tests.geometry import test_construction_binding as B

    _sp, out, sc = W.chay(*B._p1(van, them, of, wrt, **kw))
    assert out.servable and sc is not None, (out.stage_reached, out.reason_code, out.details[:3])
    return sc


def test_hai_vai_tro_cung_chu_the_giu_hai_nhan():
    """Đề cho SA = 6 VÀ hỏi độ dài SA: dữ kiện và đáp số cùng chủ thể nhưng hai vai trò đề nêu —
    đáp số giữ nhãn riêng (không `same_as`). Trước W18 nhãn đáp số bị bỏ."""
    sc = _p1("Biết SA = 6. Tính độ dài đoạn SA.", [], "S", "A",
             khai=({"name": "SA_length", "type": "float", "initial_value": 6, "source_fact_id": "SA_len"},),
             facts=({"id": "SA_len", "kind": "float", "label": "SA", "value": ["6"]},))
    a = _ann18(sc)
    assert a["SA_length"]["role"] == "given" and a["SA_length"]["subject_ids"] == ["S", "A"]
    assert a["d_kq"]["role"] == "result" and "same_as" not in a["d_kq"], a["d_kq"]


def test_cung_gia_tri_khac_chu_the_khong_gop():
    """§16.6: giá trị bằng nhau KHÔNG BAO GIỜ là tiêu chí gộp — SA = 6 (đề cho) và AB = 6 (đo, trung gian,
    KHÔNG phải đáp số) là hai đoạn khác nhau, hai nhãn. Lượt tiêm lỗi đầu (FA4, gộp theo giá trị) lọt vì
    ca cũ dùng ĐÁP SỐ — luật "đáp số không gộp vào dữ kiện" che mất; ca này dùng đại lượng trung gian."""
    do_ab = {"kind": "assign", "target_var": "ab_len",
             "expr": {"kind": "measure", "quantity": "distance", "of": "A", "wrt": "B"}}
    sc = _p1("Biết SA = 6. Tính độ dài đoạn SC.", [do_ab], "S", "C",
             khai=({"name": "SA_length", "type": "float", "initial_value": 6, "source_fact_id": "SA_len"},
                   {"name": "ab_len", "type": "float"}),
             facts=({"id": "SA_len", "kind": "float", "label": "SA", "value": ["6"]},))
    a = _ann18(sc)
    assert a["ab_len"]["role"] == "intermediate" and a["ab_len"]["subject_ids"] == ["A", "B"], a["ab_len"]
    assert "same_as" not in a["ab_len"] and "same_as" not in a["SA_length"], (a["ab_len"], a["SA_length"])


def _vuong_goc_dung_chan(w: dict) -> None:
    from fractions import Fraction as F

    u, v = ([F(x) for x in w["marker"][k]] for k in ("u", "v"))
    assert any(u) and any(v) and sum(x * y for x, y in zip(u, v)) == 0, w


def test_nhan_chung_khoang_cach_diem_duong_thang():
    sc = _canh_gold("p1_chop_thiet_dien_khoang_cach")
    w = _ann18(sc)["dist_S_BD"]["witness"]
    assert (w["from"], w["on"], w["foot"]) == ("S", "BD", ["3", "3", "0"]), w
    assert w["marker"]["v"] == ["-3", "-3", "6"], w                   # từ chân tới S
    _vuong_goc_dung_chan(w)


def test_nhan_chung_khoang_cach_diem_mat_phang():
    from tests.geometry import test_construction_binding as B

    sc = _p1("Gọi M là trung điểm của SA. Tính khoảng cách từ M đến mặt phẳng (ABCD).",
             [B._mid("M", "S", "A"), B._mp("day", ["A", "B", "C"])], "M", "day")
    an = _ann18(sc)["d_kq"]
    assert an["anchor"] == "witness" and (an["witness"]["from"], an["witness"]["on"], an["witness"]["foot"]) == (
        "M", "day", ["0", "0", "0"]), an
    _vuong_goc_dung_chan(an["witness"])


def test_dien_tich_thiet_dien_co_ky_hieu_ngan_theo_ten_de_dat():
    """Đề gọi thiết diện là (T) ⇒ nhãn ngắn trên hình là `S(T) = …`, không phải câu dài."""
    sc = _canh_gold("p1_chop_thiet_dien_khoang_cach")
    q = next(o for o in sc["objects"] if o["id"] == "area_T")
    assert q["notation"] == "S(T)", q
