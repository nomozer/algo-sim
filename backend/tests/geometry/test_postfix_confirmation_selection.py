# -*- coding: utf-8 -*-
"""Tập XÁC NHẬN POSTFIX — chọn trước, không chọn lại.

Sáu ca lấy từ **22 bài dự trữ** của pool Phase 7B: accepted, nhưng con dấu
không rút. Giá trị của chúng nằm ở một tính chất không mua lại được — chúng
được soạn khi **chưa ai biết hệ V2 sẽ hỏng ở đâu**. Đi tìm đề mới bây giờ thì
mất hẳn tính chất ấy, vì người soạn đã đọc taxonomy thất bại của lượt chính
thức.

Ba luật, ba lý do khác nhau:

**Không chọn lại.** `selection_hash` dẫn từ `case_ids + luat_chon + k`. Đổi
một ca sau khi đã thấy số là bỏ đúng thứ tập này bảo vệ.

**Không dùng ca đã rút.** Giao với 20 ca chính thức phải rỗng, nếu không thì
đây là chạy lại benchmark dưới một cái tên khác.

**Không chọn theo độ khó.** Luật xếp theo `case_id` — thứ tự chữ không mang
thông tin về việc bài dễ hay khó, và đó chính là điều cần.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
GEO = ROOT / "docs" / "evaluation" / "geometry"
SEL = GEO / "postfix-confirmation" / "CONFIRMATION_SELECTION.json"


@pytest.fixture(scope="module")
def sel() -> dict:
    if not SEL.exists():
        pytest.skip("chưa đóng băng tập xác nhận")
    return json.loads(SEL.read_text(encoding="utf-8"))


def test_dung_SAU_ca_va_khong_trung_nhau(sel):
    assert len(sel["case_ids"]) == 6
    assert len(set(sel["case_ids"])) == 6


def test_KHONG_giao_voi_20_ca_chinh_thuc(sel):
    dau = json.loads((GEO / "holdout" / "HOLDOUT_SEAL.json").read_text(encoding="utf-8"))
    giao = set(sel["case_ids"]) & set(dau["case_ids"])
    assert not giao, f"dùng lại ca chính thức: {sorted(giao)}"


def test_moi_ca_deu_la_reserve_ACCEPTED_cua_pool(sel):
    pool = json.loads((GEO / "holdout" / "pool.json").read_text(encoding="utf-8"))
    nhan = {c["case_id"] for c in pool["cases"]
            if c.get("status", "accepted") == "accepted"}
    assert set(sel["case_ids"]) <= nhan


def test_selection_hash_DAN_tu_noi_dung_khong_ghi_tay(sel):
    lai = hashlib.sha256(json.dumps(
        {k: sel[k] for k in ("case_ids", "luat_chon", "k")},
        ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    assert sel["selection_hash"] == lai


def test_dong_bang_TRUOC_khi_co_bat_ky_ket_qua_V2_nao(sel):
    """Không thư mục kết quả xác nhận nào được có mặt lúc đóng băng.

    Kiểm bằng hiện trường chứ không bằng lời hứa: nếu file kết quả đã tồn tại
    thì tuyên bố *"chọn trước khi thấy số"* không kiểm được nữa.
    """
    d = SEL.parent
    ket_qua = [f.name for f in d.glob("*.json") if f.name != SEL.name]
    if ket_qua:
        # Có kết quả rồi thì `dong_bang_luc` phải CŨ HƠN mọi file kết quả.
        t = SEL.stat().st_mtime
        moi = [f.name for f in d.glob("*.json")
               if f.name != SEL.name and f.stat().st_mtime < t]
        assert not moi, f"kết quả có TRƯỚC lúc chọn: {moi}"


def test_luat_chon_KHAI_RO_khoa_xep_va_phu_dinh_do_kho(sel):
    """Một luật xếp theo độ khó là cherry-pick, dù có viết ra hay không.

    Bản đầu của test này CẤM chuỗi `"độ khó"` xuất hiện — và nó đỏ ngay, vì
    luật viết *"không xếp theo độ khó"*. Cấm một từ thì bắt nhầm cả câu phủ
    định nó, và tệ hơn: một luật cherry-pick chỉ cần tránh dùng từ ấy là lọt.
    Nên đòi **lời khai dương** — khoá xếp là gì — thay vì cấm từ.
    """
    van = " ".join(sel["luat_chon"]).lower()
    assert "case_id nhỏ nhất theo thứ tự chữ" in van, \
        "luật không khai KHOÁ XẾP là gì"
    assert "không xếp theo độ khó" in van, "luật không phủ định độ khó"
    # Và khoá xếp phải ĐÚNG là thứ đã dùng: sáu ca theo thứ tự chữ trong ô của
    # chúng — kiểm bằng cách chạy lại bộ chọn, không bằng cách đọc câu chữ.
    import importlib.util
    import sys
    d = ROOT / "backend" / "scripts" / "freeze_postfix_confirmation.py"
    spec = importlib.util.spec_from_file_location("_fpc", d)
    m = importlib.util.module_from_spec(spec)
    sys.modules["_fpc"] = m
    spec.loader.exec_module(m)
    lai, _ = m.chon(m.reserve())
    assert [c["case_id"] for c in lai] == sel["case_ids"], \
        "chạy lại bộ chọn ra tập KHÁC — luật không tất định"


def test_sau_o_CAU_TRUC_deu_co_mat(sel):
    """Sáu ô của §9 — thiếu ô nào phải KHAI, không được im lặng bù."""
    assert len(sel["theo_o_cau_truc"]) == 6
    if sel["o_thieu_ung_vien"]:
        assert "bu_tat_dinh" in sel["theo_o_cau_truc"], \
            "khai thiếu ô mà không thấy dấu vết bù"


def test_ghi_du_danh_tinh_de_truy_nguoc(sel):
    for k in ("pool_hash_luc_chon", "commit", "dong_bang_luc", "nguon", "k"):
        assert sel.get(k), k
    assert sel["nguon"] == "PRE_EXISTING_UNUSED_PHASE7B_RESERVE"
    assert sel["k"] == 2
