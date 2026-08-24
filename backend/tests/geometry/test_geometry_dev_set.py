# -*- coding: utf-8 -*-
"""DEV set hình học — kiểm HÌNH DẠNG của tập, không kiểm hệ. **0 API call.**

Tập này chưa từng chạy qua LLM. Test ở đây chỉ bảo đảm nó **dùng được**: đủ
nghĩa vụ, đề không rò đáp án, và nhãn nói đúng nó là DEV.

VÌ SAO KIỂM "ĐỀ KHÔNG RÒ ĐÁP ÁN": nếu `problem_text` chứa sẵn toạ độ, mô hình
không phải **đặt hệ toạ độ** — mà đặt hệ toạ độ chính là nửa khó của bài toán
sinh ở miền này. Một tập đề rò toạ độ sẽ cho tỉ lệ đẹp và vô nghĩa.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.simulation.semantic_program.obligations import OBLIGATION_KINDS

_F = (Path(__file__).resolve().parents[3] / "docs" / "evaluation" / "geometry"
      / "dev" / "cases.json")

DATA = json.loads(_F.read_text(encoding="utf-8"))
CASES = DATA["cases"]

#: Tám nghĩa vụ hình học — tập phải phủ ĐỦ, nếu không thì có checker chưa từng
#: được một đề nào chạm tới.
TAM_NGHIA_VU = {
    "point_on_line", "point_on_plane", "parallel", "perpendicular",
    "coplanar", "distance", "angle", "volume",
}


def test_du_muoi_bai():
    assert len(CASES) == 10


def test_case_id_khong_trung():
    assert len({c["case_id"] for c in CASES}) == 10


def test_phu_DU_tam_nghia_vu():
    """Thiếu một nghĩa vụ ⇒ checker của nó chưa từng được đề nào chạm tới, và
    ta không biết nó có hoạt động trên đường thật hay không."""
    co = {ob for c in CASES for ob in c["expected_obligations"]}
    thieu = TAM_NGHIA_VU - co
    assert not thieu, f"DEV set chưa phủ nghĩa vụ: {sorted(thieu)}"


def test_moi_nghia_vu_deu_nam_trong_taxonomy():
    for c in CASES:
        for ob in c["expected_obligations"]:
            assert ob in OBLIGATION_KINDS, f"{c['case_id']}: '{ob}' ngoài taxonomy"


@pytest.mark.parametrize("c", CASES, ids=[c["case_id"] for c in CASES])
def test_moi_bai_du_bon_phan(c):
    for khoa in ("problem_text", "expected_obligations", "oracle_result",
                 "ghi_chu_kiem_tay"):
        assert c.get(khoa), f"{c['case_id']} thiếu '{khoa}'"


@pytest.mark.parametrize("c", CASES, ids=[c["case_id"] for c in CASES])
def test_de_bai_KHONG_ro_toa_do(c):
    """Đề cho sẵn toạ độ ⇒ mô hình khỏi phải đặt hệ toạ độ, mà đó là nửa khó
    của bài toán sinh ở miền này. Tỉ lệ sẽ đẹp và vô nghĩa."""
    t = c["problem_text"]
    assert "(0,0" not in t and "(0, 0" not in t, "đề rò toạ độ"
    assert "Oxyz" not in t, "đề gợi sẵn hệ toạ độ"


@pytest.mark.parametrize("c", CASES, ids=[c["case_id"] for c in CASES])
def test_de_bai_la_van_xuoi_tieng_Viet(c):
    t = c["problem_text"]
    assert len(t) > 40, "đề quá ngắn để là một bài SGK"
    assert t.rstrip().endswith("."), "đề phải là câu hoàn chỉnh"


def test_gia_tri_so_khai_bang_PHAN_SO_khong_phai_thap_phan():
    """`2/3` chính xác; `0.667` thì không. Oracle so bằng `Fraction`."""
    for c in CASES:
        for k, v in c["oracle_result"].items():
            if k in ("distance", "volume", "cos_sq") and isinstance(v, str):
                assert "." not in v, f"{c['case_id']}.{k} dùng thập phân: {v}"


def test_tu_khai_la_DEV_khong_phai_held_out():
    """Nhãn phải nói đúng sự thật — đây là chỗ một con số đường-hạnh-phúc dễ
    đi vào luận văn nhất."""
    assert DATA["dataset"] == "geometry_generation_dev_set"
    m = DATA["muc_dich"]
    assert "KHÔNG BAO GIỜ là số held-out" in m
    assert "custodian" in m and "seed" in m


def test_luat_soan_ghi_ro_dap_an_KIEM_TAY():
    """Chạy hệ rồi chép kết quả làm đáp án là tautology — bẫy đã gặp ở
    `cross_domain_matrix`."""
    assert any("TAY" in l or "tay" in l for l in DATA["luat_soan"])
