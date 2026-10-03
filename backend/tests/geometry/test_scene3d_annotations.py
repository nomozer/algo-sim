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

from tests.geometry import w14_cases as W

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


def _ann(sc: dict) -> dict:
    return {o["id"]: o.get("annotation") for o in sc["objects"] if o["type"] == "quantity"}


def _gan(kind: str, category: str, subject_ids: list[str], anchor: str) -> dict:
    return {"kind": kind, "category": category, "subject_ids": subject_ids, "anchor": anchor, "unit": KHONG_DON_VI}


def test_w17_lang_tru_du_kien_so_do_va_ket_qua_gan_dung_chu_the():
    a = _ann(_canh_ho("lang_tru_tam_giac"))
    assert a["AB_length"] == _gan("length", "measurement", ["A", "B"], "segment")
    assert a["AC_length"] == _gan("length", "measurement", ["A", "C"], "segment")
    assert a["AD_length"] == _gan("length", "measurement", ["A", "D"], "segment")
    assert a["dien_tich_day_ABC"] == _gan("area", "measurement", ["day_ABC"], "region")
    assert a["the_tich_solid_ABCDEF"] == _gan("volume", "result", ["solid_ABCDEF"], "solid")
    # đích bí danh dùng CHUNG danh tính với phép đo nó trỏ tới: không có nhãn thứ hai
    assert a["the_tich_lang_tru"] is None


def test_w17_hinh_hop_do_dai_co_phay_gan_dung_dinh():
    a = _ann(_canh_ho("hop_chu_nhat"))
    assert a["AA_prime_length"] == _gan("length", "measurement", ["A", "A_prime"], "segment")
    assert a["V"] is None and a["the_tich_khoi_hop"]["category"] == "result"


def test_w17_mot_chu_the_mot_nhan_du_kien_truoc():
    """Hình hộp: độ dài đề cho AA′ và chiều cao đo được AA′ là CÙNG một số trên CÙNG một đoạn —
    một nhãn (của dữ kiện), không hai nhãn chồng tại một điểm neo."""
    sc = _canh_ho("hop_chu_nhat")
    a = _ann(sc)
    assert a["AA_prime_length"]["subject_ids"] == ["A", "A_prime"]
    assert a["chieu_cao_AA_prime"] is None
    assert "ANNOTATION_UNBOUND chieu_cao_AA_prime: same subject as AA_prime_length" in sc["diagnostics"]


def test_w17_do_dai_de_cho_kiem_bang_khoang_cach_chinh_xac():
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


def test_w17_thiet_dien_va_khoang_cach_gan_mien_va_cap():
    a = _ann(_canh_gold("p1_chop_thiet_dien_khoang_cach"))
    assert a["area_T"] == _gan("area", "result", ["T"], "region")
    assert a["the_volume_sabcd"] == _gan("volume", "result", ["S.ABCD"], "solid")
    assert a["dist_S_BD"] == _gan("distance", "result", ["S", "BD"], "pair")


def test_w17_so_tron_khong_nhan_doan_thi_khong_gan_va_co_chan_doan():
    """Lập phương "có cạnh bằng 4": đề không gắn con số với một ĐOẠN có tên — không đoán đoạn."""
    sc = _canh_ho("lap_phuong")
    a = _ann(sc)
    assert a["AB_length"] is None
    assert any(d.startswith("ANNOTATION_UNBOUND AB_length") for d in sc.get("diagnostics", [])), sc.get("diagnostics")
    assert a["the_tich_khoi_hop"]["category"] == "result"


@pytest.mark.parametrize("ho", sorted(W.HO))
def test_w17_moi_annotation_tro_toi_vat_co_trong_canh(ho):
    sc = _canh_ho(ho)
    co = {o["id"] for o in sc["objects"]}
    for qid, an in _ann(sc).items():
        if an is not None:
            assert set(an["subject_ids"]) <= co, (ho, qid, an)
            assert an["category"] in ("measurement", "result") and an["anchor"] in ("segment", "region", "solid", "pair")
