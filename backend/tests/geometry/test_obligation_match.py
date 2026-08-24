# -*- coding: utf-8 -*-
"""`obligation_match` — bắt ca "trả lời đúng một câu không ai hỏi". 0 API call.

VÌ SAO CẦN MỘT CHỈ SỐ RIÊNG: checker chỉ kiểm nghĩa vụ **đã khai** có được thoả
không. Đề hỏi *"chứng minh SA ⊥ (ABCD)"* mà LLM khai `volume` rồi tính thể tích
đúng ⇒ checker PASS, C₂ PASS, oracle PASS. Không cổng nào bắt được, vì không
cổng nào biết đề hỏi gì — chỉ **bộ đo** biết.

VÀ VÌ SAO NÓ KHÔNG PHẢI MỘT CỔNG: *"đề mong đợi nghĩa vụ nào"* là phán đoán của
người soạn đề, không phải sự thật toán học. Một đề chứng minh được bằng nhiều
đường. Biến phán đoán ấy thành cổng là dựng một oracle thứ hai không ai kiểm.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_M = Path(__file__).resolve().parents[2] / "scripts" / "reliability_v2.py"


@pytest.fixture(scope="module")
def rv():
    spec = importlib.util.spec_from_file_location("reliability_v2", _M)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["reliability_v2"] = mod
    spec.loader.exec_module(mod)
    return mod


_SERVED = {"stage_reached": "served", "executable": True, "servable": True}


# ── ca trung tâm: giải đúng một bài KHÁC ──────────────────────────────────
def test_khai_NHAM_loai_nghia_vu_bi_ghi_nhan(rv):
    """Đề hỏi vuông góc, mô hình khai thể tích."""
    m = rv.obligation_match(["perpendicular"], ["volume"])
    assert m["khop_hoan_toan"] is False
    assert m["thieu"] == ["perpendicular"]
    assert m["thua"] == ["volume"]


def test_lech_KHONG_lam_hong_A_va_B(rv):
    """Quan trắc, không gác cửa: ca lệch vẫn `executable` và `servable`."""
    k = rv.chi_so_case("geo_05", _SERVED,
                       mong_doi_obl=["perpendicular"], khai_obl=["volume"])
    assert k["executable_A"] is True
    assert k["assurance_B"] is True
    assert k["failure_layer"] is None, "lệch nghĩa vụ KHÔNG được thành tầng thất bại"
    assert k["obligation_match"]["khop_hoan_toan"] is False


# ── khớp ──────────────────────────────────────────────────────────────────
def test_khop_hoan_toan(rv):
    m = rv.obligation_match(["perpendicular"], ["perpendicular"])
    assert m["khop_hoan_toan"] and not m["thieu"] and not m["thua"]


def test_de_nhieu_nghia_vu_khai_du_thi_khop(rv):
    m = rv.obligation_match(["perpendicular", "point_on_plane", "volume"],
                            ["volume", "perpendicular", "point_on_plane"])
    assert m["khop_hoan_toan"], "thứ tự không được ảnh hưởng"


def test_khai_THUA_cung_la_LECH(rv):
    """Thừa che mất chỗ thiếu: mô hình trả lời thêm thứ đề không hỏi, và ở một
    bài đánh giá thì đó không phải điểm cộng."""
    m = rv.obligation_match(["perpendicular"], ["perpendicular", "volume"])
    assert m["khop_hoan_toan"] is False
    assert m["thua"] == ["volume"] and not m["thieu"]


def test_khai_THIEU_mot_trong_ba(rv):
    m = rv.obligation_match(["perpendicular", "point_on_plane", "volume"],
                            ["perpendicular"])
    assert m["thieu"] == ["point_on_plane", "volume"]


def test_khong_khai_gi_thi_KHONG_khop(rv):
    m = rv.obligation_match(["perpendicular"], [])
    assert m["khop_hoan_toan"] is False and m["thieu"] == ["perpendicular"]


# ── CHƯA ĐO ≠ KHÔNG LỆCH ──────────────────────────────────────────────────
def test_bo_do_khong_khai_expected_thi_la_None_khong_phai_False(rv):
    """Cùng luật `replay_R`: trộn 'chưa đo' với 'lệch' là bịa thêm thất bại."""
    k = rv.chi_so_case("x", _SERVED)
    assert k["obligation_match"] is None


def test_expected_rong_thi_khop_hoan_toan_la_False(rv):
    """Đề không khai nghĩa vụ nào ⇒ không có gì để khớp. Trả `True` ở đây là
    cho một tập rỗng đi qua như thể đã đúng."""
    assert rv.obligation_match([], [])["khop_hoan_toan"] is False


# ── tổng hợp ──────────────────────────────────────────────────────────────
def test_tong_hop_dem_tho_va_neu_nghia_vu_hay_lech(rv):
    khoi = [
        rv.chi_so_case("a", _SERVED, mong_doi_obl=["perpendicular"],
                       khai_obl=["perpendicular"]),
        rv.chi_so_case("b", _SERVED, mong_doi_obl=["perpendicular"],
                       khai_obl=["volume"]),
        rv.chi_so_case("c", _SERVED, mong_doi_obl=["distance"], khai_obl=[]),
    ]
    t = rv.tong_hop(khoi)["obligation_match"]
    assert t["khop_hoan_toan"] == 1 and t["mau_so"] == 3
    assert "perpendicular" in t["nghia_vu_hay_bi_THIEU"]
    assert "volume" in t["nghia_vu_hay_bi_KHAI_THUA"]


def test_tong_hop_bao_CHUA_DO_khi_khong_ca_nao_co_expected(rv):
    t = rv.tong_hop([rv.chi_so_case("x", _SERVED)])["obligation_match"]
    assert t["chua_do"] == 1


def test_khoi_v2_cu_KHONG_vo_khi_thieu_hai_tham_so_moi(rv):
    """Runner Tin học gọi `chi_so_case` không truyền `mong_doi_obl` — hai tham
    số mới phải có mặc định, nếu không mọi lượt đo cũ vỡ."""
    k = rv.chi_so_case("x", _SERVED, replay_ok=True)
    assert k["obligation_match"] is None and k["replay_R"] is True
