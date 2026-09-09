# -*- coding: utf-8 -*-
"""ELIP PHẢI CÓ TÊN — `ellipse3` là kiểu đầy đủ từ 2026-09-07. **0 API call.**

─── LỖ ĐƯỢC ĐÓNG Ở ĐÂY ─────────────────────────────────────────────────────

`ellipse3` vào `MemoryType` cùng wave thiết diện xiên, nhưng **ba** bảng ở tầng
trình bày không đi theo. Cả ba đều là *lối rơi cuối*, nên thiếu một kiểu là
kiểu ấy mất tên trong mọi câu nhắc tới nó — và mất **im lặng**:

    _CACH_GOI["intersect_plane_curved_ellipse"]  vắng ⇒ không có CÂU gọi tên
    MO_TA_KIEU["ellipse3"]                       vắng ⇒ nhãn vật  = "Đối tượng"
    _DANH_TU_NGAN["ellipse3"]                    vắng ⇒ cách gọi  = "đối tượng"

Hệ quả đo được trên hai ca của lượt nghiệm thu cuối:

    p6 · p7    Diện tích «đối tượng»    25π√5 · 2π√6

Đường tròn giao — cùng hình dạng bài toán, khác đúng một kiểu — thì có đủ:
`Diện tích «Đường tròn giao của khối cong và mặt phẳng»`. Nên bản vá **soi
gương ca đường tròn**, không phát minh một cách viết thứ hai.

⚠️ Các test dưới đây khoá **bất biến**, không khoá một câu tiếng Việt cụ thể:
cách hành văn là quyết định trình bày và được phép đổi, còn *"một kiểu có mặt
trong `MemoryType` thì phải có tên tiếng Việt"* thì không.
"""
from __future__ import annotations

import typing

import pytest

from app.simulation.semantic_program.contract import MemoryType
from app.simulation.semantic_program.display_names import (
    MO_TA_KIEU,
    ten_hien_thi,
)

#: Chuỗi chỉ xuất hiện khi một KIỂU không có trong bảng danh từ.
PLACEHOLDER = ("đối tượng", "Đối tượng", "undefined", "null", "None")

#: Kiểu hình học — những kiểu thật sự lên được màn hình 3D. Các kiểu Tin học
#: cũ (`array`, `stack`…) không thuộc miền sản phẩm nữa nên không đòi tên.
#:
#: ⚠️ `quantity` KHÔNG nằm đây và đó không phải thiếu sót: nó là kiểu của một ô
#: đọc số trong CẢNH, không phải một kiểu bộ nhớ mà chương trình khai được.
#: Gộp hai taxonomy ấy là đúng lỗi mà `tu_choi_ten_nghia_vu_lam_kieu` đi chặn.
KIEU_HINH_HOC = ("point3", "vector3", "line3", "plane3", "polygon3", "solid",
                 "section", "circle3", "curved_solid", "ellipse3")


def _thong_tin(loai: str, producer: str | None = None,
               sources: list[str] | None = None) -> dict:
    return {"E": {"type": loai, "producer": producer,
                  "sources": sources or [], "label": None}}


# ══ ① ELIP CÓ TÊN TIẾNG VIỆT ═════════════════════════════════════════════
def test_ellipse3_duoc_goi_la_elip():
    """§5.1 — `ellipse3` phải hiện thành **elip**, không phải "đối tượng"."""
    r = ten_hien_thi(_thong_tin("ellipse3"))["E"]
    assert "elip" in (r["label"] or "").lower(), r["label"]
    assert "elip" in (r["reference"] or "").lower(), r["reference"]
    for p in PLACEHOLDER:
        assert p not in (r["label"] or ""), (p, r["label"])
        assert p not in (r["reference"] or ""), (p, r["reference"])


def test_elip_giao_co_CAU_goi_ten_nhu_duong_tron():
    """Cùng hình dạng bài toán với đường tròn giao ⇒ cùng dạng câu.

    Khoá QUAN HỆ chứ không khoá chữ: câu của elip phải nhắc **cả hai** toán
    hạng, y như câu của đường tròn — nếu không thì học sinh đọc một cái tên
    không nói được nó cắt cái gì.
    """
    tt = {
        "T": {"type": "curved_solid", "producer": None, "sources": [],
              "label": "Hình trụ"},
        "P": {"type": "plane3", "producer": None, "sources": [],
              "label": "Mặt phẳng alpha"},
        "E": {"type": "ellipse3", "producer": "intersect_plane_curved_ellipse",
              "sources": ["T", "P"], "label": None},
    }
    r = ten_hien_thi(tt)
    nhan = r["E"]["label"] or ""
    assert "elip" in nhan.lower(), nhan
    # So với CÁCH GỌI mà chính thẩm quyền phát cho hai toán hạng, không so với
    # một chuỗi gõ tay: cách hành văn được phép đổi, còn *"câu phải nhắc cả hai
    # toán hạng"* thì không.
    for s in ("T", "P"):
        goi = r[s]["reference"] or ""
        assert goi and goi in nhan, (s, goi, nhan)

    # Đối chứng: đường tròn giao — cùng cấu trúc, khác kiểu — vẫn như cũ.
    tt2 = dict(tt)
    tt2["E"] = {"type": "circle3", "producer": "intersect_plane_curved",
                "sources": ["T", "P"], "label": None}
    assert "Đường tròn giao" in (ten_hien_thi(tt2)["E"]["label"] or "")


def test_dien_tich_cua_elip_khong_con_la_dien_tich_doi_tuong():
    """Đại lượng NHẮC TỚI elip — đây đúng là nhãn `p6`/`p7` giao ra."""
    tt = {
        "T": {"type": "curved_solid", "producer": None, "sources": [],
              "label": "Hình trụ"},
        "P": {"type": "plane3", "producer": None, "sources": [], "label": None},
        "E": {"type": "ellipse3", "producer": "intersect_plane_curved_ellipse",
              "sources": ["T", "P"], "label": None},
        "S": {"type": "quantity", "producer": "measure.area",
              "sources": ["E"], "label": None},
    }
    nhan = ten_hien_thi(tt)["S"]["label"] or ""
    assert nhan.startswith("Diện tích"), nhan
    assert "«đối tượng»" not in nhan, nhan
    assert "elip" in nhan.lower(), nhan


# ══ ② TÊN BIẾN KHÔNG ĐƯỢC LÀ NGUỒN CỦA TÊN HIỂN THỊ ══════════════════════
@pytest.mark.parametrize("ten_bien", ["E", "dien_tich_E", "e_1", "xyz"])
def test_doi_ten_bien_KHONG_doi_phan_quyet(ten_bien):
    """§4 — nhãn phải dẫn từ KIỂU, không từ chính tả tên biến.

    Hai chương trình tương đương chỉ khác tên biến phải cho cùng một nhãn.
    """
    tt = {ten_bien: {"type": "ellipse3", "producer": None, "sources": [],
                     "label": None}}
    r = ten_hien_thi(tt)[ten_bien]
    assert "elip" in (r["label"] or "").lower(), (ten_bien, r["label"])
    # và tên biến KHÔNG được lọt nguyên si lên nhãn khi nó không phải ký hiệu
    if ten_bien not in ("E",):
        assert ten_bien not in (r["label"] or ""), (ten_bien, r["label"])


# ══ ③ CHỐNG TÁI PHÁT — mọi kiểu hình học phải có tên ═════════════════════
def test_moi_kieu_hinh_hoc_deu_co_danh_tu_tieng_viet():
    """Guard CHỐNG TÁI PHÁT, và nó là phần đáng giá nhất của wave này.

    `ellipse3` lọt lưới vì không có gì bắt buộc bảng tên đi theo `MemoryType`.
    Thêm một kiểu hình học mà quên bảng ⇒ ĐỎ ở đây, thay vì hiện "đối tượng"
    trên màn hình học sinh vài wave sau.
    """
    hop_le = set(typing.get_args(MemoryType))
    for loai in KIEU_HINH_HOC:
        assert loai in hop_le, f"{loai} không còn trong MemoryType — sửa test"
        r = ten_hien_thi(_thong_tin(loai))[loai if False else "E"]
        assert loai in MO_TA_KIEU, f"MO_TA_KIEU thiếu {loai}"
        for p in ("đối tượng", "Đối tượng"):
            assert p not in (r["reference"] or ""), (loai, r["reference"])


def test_kieu_LA_van_di_qua_fallback_tieng_viet_co_nghia():
    """§6 — kiểu chưa có ánh xạ vẫn phải ra tiếng Việt đọc được, KHÔNG ra `id`.

    Đây là lối rơi cuối cùng và nó được giữ NGHÈO có chủ đích: một kiểu mới
    hiện ra là "Đối tượng" trên màn hình thì người ta thấy ngay và sửa, còn in
    định danh máy thì trông như đã có tên.
    """
    r = ten_hien_thi(_thong_tin("mot_kieu_chua_ton_tai"))["E"]
    assert r["label"] == "Đối tượng"
    assert "mot_kieu_chua_ton_tai" not in (r["label"] or "")
    assert "E" != r["label"]


# ══ ④ TÊN KHÔNG ĐƯỢC CHẠM VÀO GIÁ TRỊ ════════════════════════════════════
def test_ten_hien_thi_KHONG_dung_toi_gia_tri():
    """§6 — đổi nhãn không được đổi `Radical`/`Fraction`/biểu diễn π.

    `ten_hien_thi` chỉ nhận `{type, producer, sources, label}` — nó KHÔNG nhận
    giá trị, nên về cấu tạo nó không thể chạm tới. Guard này khoá đúng ranh
    giới ấy: thêm một trường giá trị vào đầu vào là mở đường cho tầng trình bày
    sửa số.
    """
    tt = _thong_tin("ellipse3")
    truoc = {k: dict(v) for k, v in tt.items()}
    ten_hien_thi(tt)
    assert tt == truoc, "ten_hien_thi đã MUTATE đầu vào"
    assert set(tt["E"]) == {"type", "producer", "sources", "label"}
