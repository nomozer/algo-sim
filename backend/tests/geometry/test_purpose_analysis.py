# -*- coding: utf-8 -*-
"""PHASE 7 TASK 3 — tầng phân tích MỤC ĐÍCH. **0 API call.**

Thứ file này khoá chặt nhất là **ba nhãn phải tách nhau**:

    bước CẦN · bước THỪA THẬT · LỆCH DANH XƯNG

Gộp hai cái sau lại thì `geo_05` bị đọc thành *"mô hình dựng hai bước vô ích"*,
trong khi lỗi thuộc **hợp đồng của ta**. Một chỉ số vu oan cho mô hình ở đúng
chỗ ta sai là chỉ số tệ hơn không có.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.purpose_analysis import (
    NHAN_CAN,
    NHAN_LECH_TEN,
    purpose_analysis,
)
from app.simulation.semantic_program.request_contract import RequestContract

_W4 = json.loads(
    (Path(__file__).resolve().parents[3] / "docs" / "evaluation" / "geometry"
     / "dev-results-w4" / "geometry_dev_results.json").read_text(encoding="utf-8"))


def _hd(rc: dict) -> RequestContract:
    return RequestContract(obligations=tuple(
        Obligation(kind=o["kind"], container=o["container"], params=o["params"])
        for o in rc["obligations"]))


def _pa(case: dict) -> dict:
    return purpose_analysis(
        _hd(case["request_contract"]),
        SemanticProgramSpec.model_validate(case["generated_program"]))


def _case(cid: str) -> dict:
    return next(c for c in _W4["cases"] if c["case_id"] == cid)


# ══ TRÊN IR THẬT — bốn bài đi trọn đường ═════════════════════════════════
@pytest.mark.parametrize("cid", ["geo_06", "geo_07", "geo_08", "geo_09"])
def test_bai_di_tron_duong_KHONG_co_buoc_thua(cid):
    """Bốn bài AI sinh, cả bốn qua oracle: **mọi bước đều phục vụ đáp án**.

    Đây là con số nói được điều mà một bảng liệt kê bước không nói được —
    không phải *"có 3 bước"* mà *"cả 3 bước đều cần"*.
    """
    kq = _pa(_case(cid))
    assert kq["buoc_thua"] == [], kq
    assert not kq["co_lech_danh_xung"]
    assert kq["tom_tat"]["ti_le_huu_ich"] == 1.0


def test_geo_09_neu_ro_hai_buoc_can():
    kq = _pa(_case("geo_09"))
    assert kq["buoc_can"] == ["S.ABCD", "V_S_ABCD"]
    nv = kq["theo_nghia_vu"][0]
    assert nv["kind"] == "volume" and nv["trang_thai"] == NHAN_CAN


# ══ HAI BỆNH KHÁC NHAU, KHÔNG ĐƯỢC GỘP ══════════════════════════════════
def test_geo_02_la_BUOC_THUA_THAT():
    """Mô hình dựng `giao_tuyen` rồi không dùng tới — thừa thật."""
    kq = _pa(_case("geo_02"))
    assert not kq["co_lech_danh_xung"], "geo_02 KHÔNG phải ca lệch tên"
    assert kq["buoc_thua"], kq
    assert "giao_tuyen" in kq["buoc_thua"]


def test_geo_05_la_LECH_DANH_XUNG_khong_phai_thua():
    """Hợp đồng gọi `(ABCD)`/`SA`; chương trình khai `ABCD_plane`/`SA_line`.

    Bao đóng rỗng ở đây **không** nói gì về các bước — nó nói hai lượt LLM đặt
    tên khác nhau. Wave 4 đã ghi nhận lỗi này thuộc hợp đồng.
    """
    kq = _pa(_case("geo_05"))
    assert kq["co_lech_danh_xung"] is True
    assert kq["theo_nghia_vu"][0]["trang_thai"] == NHAN_LECH_TEN
    assert kq["theo_nghia_vu"][0]["ten_khong_giai_duoc"]
    # KHÔNG được kết luận "hai bước thừa".
    assert kq["buoc_thua"] == []
    assert kq["tom_tat"]["ti_le_huu_ich"] is None


def test_ti_le_huu_ich_la_None_chu_KHONG_phai_0_khi_khong_do_duoc():
    """"Không đo được" và "không có bước nào hữu ích" là hai kết luận khác hẳn.
    Trả `0` sẽ vào bảng thống kê như một điểm 0 thật."""
    kq = _pa(_case("geo_05"))
    assert kq["tom_tat"]["ti_le_huu_ich"] is None


def test_lech_ten_neu_ro_CA_HAI_PHIA():
    """Người đọc phải thấy hợp đồng đòi gì VÀ chương trình có gì — nếu không
    lại phải chạy forensics như Phase 5 lượt 2."""
    nv = _pa(_case("geo_05"))["theo_nghia_vu"][0]
    assert nv["ten_khong_giai_duoc"] and nv["chuong_trinh_khai"]


# ══ RANH GIỚI ═══════════════════════════════════════════════════════════
def test_KHONG_module_nao_dung_purpose_analysis_de_GAC_CUA():
    """Chương trình có bước thừa vẫn là chương trình ĐÚNG. "Thừa" là nhận xét
    sư phạm, không phải bản án — dùng nó để chặn là biến một cái thành cái kia."""
    import ast

    goc = Path(__file__).resolve().parents[2] / "app" / "simulation"
    for f in goc.rglob("*.py"):
        if f.name == "purpose_analysis.py":
            continue
        cay = ast.parse(f.read_text(encoding="utf-8"))
        ten = {n.func.id for n in ast.walk(cay)
               if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        assert "purpose_analysis" not in ten, f.name


def test_hop_dong_RONG_khong_lam_vo():
    spec = SemanticProgramSpec.model_validate(
        _case("geo_09")["generated_program"])
    kq = purpose_analysis(RequestContract(), spec)
    assert kq["buoc_can"] == []
    # Không nghĩa vụ nào ⇒ mọi bước "không phục vụ gì" — đúng về mặt logic, và
    # không có lệch tên nào để che nó.
    assert kq["buoc_thua"] and not kq["co_lech_danh_xung"]


def test_serialize_duoc_ra_JSON():
    json.dumps(_pa(_case("geo_09")), ensure_ascii=False)
