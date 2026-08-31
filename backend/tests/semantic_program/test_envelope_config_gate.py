# -*- coding: utf-8 -*-
"""CỔNG HÌNH DẠNG CONFIG TUYẾN NGỮ NGHĨA — và nó phải MIRROR đúng bản TS.

`validate_semantic_envelope_config` tồn tại vì cổng giao bài không dùng được
`CATALOG`: tuyến ngữ nghĩa không phải một target chuyên biệt. Nó là bản sao
tiếng Python của `validateSemanticConfig`
(`frontend/src/simulations/domains/semantic/model.ts`).

Hai bản sao ⇒ hai đường trôi. Chống trôi bằng cách đặt CÙNG một bộ ca cho cả
hai bên: mỗi ca dưới đây có một ca song sinh ở `semantic.test.ts`. Sửa một bên
mà quên bên kia thì bên kia đỏ — đó là toàn bộ lý do bộ ca này viết dưới dạng
bảng chứ không phải bốn hàm rời.
"""

from __future__ import annotations

import pytest

from app.simulation.semantic_program import (
    SIMULATION_ID,
    validate_semantic_envelope_config,
)


def _khung(n: int) -> list[dict]:
    return [{"step_index": i, "narration": f"Bước {i}.",
             "objects": [], "highlighted_object_ids": []} for i in range(n)]


def _cfg(**doi):
    c = {
        "spec_version": "1.0",
        "title": "Thiết diện",
        "frames": _khung(3),
        "view_steps": [{"frame_lo": 0, "frame_hi": 1}, {"frame_lo": 2, "frame_hi": 2}],
        "grouping_level": "step",
        "presentation_overflow": False,
        "execution_truncated": False,
    }
    c.update(doi)
    return c


def test_id_tuyen_ngu_nghia_dung_cai_ma_frontend_cho_doi():
    """Định danh này là khớp nối giữa hai bờ — gõ lệch là im lặng hỏng."""
    assert SIMULATION_ID == "generic.semantic_program"


def test_config_hop_le_di_qua():
    assert validate_semantic_envelope_config(_cfg()) is None


@pytest.mark.parametrize("cfg, mong", [
    (None, "rỗng"),
    ("chuỗi", "rỗng"),
    (_cfg(frames=[]), "khung hình nào"),
    (_cfg(frames="không phải mảng"), "khung hình nào"),
    (_cfg(view_steps=[]), "bước xem nào"),
    # Bỏ sót khung CUỐI: qua được mọi phép kiểm "có dữ liệu không".
    (_cfg(view_steps=[{"frame_lo": 0, "frame_hi": 1}]), "phủ hết"),
    # Không bắt đầu từ 0: khung đầu không bước xem nào chạm tới.
    (_cfg(view_steps=[{"frame_lo": 1, "frame_hi": 2}]), "phủ hết"),
    (_cfg(view_steps=[{"frame_lo": 0, "frame_hi": 0},
                      {"frame_lo": 2, "frame_hi": 2}]), "chồng lấn hoặc bỏ sót"),
    (_cfg(view_steps=[{"frame_lo": 0, "frame_hi": 2},
                      {"frame_lo": 0, "frame_hi": 2}]), "chồng lấn hoặc bỏ sót"),
    # Để chạm được nhánh "ra ngoài", phần phủ hai ĐẦU phải đúng — nếu không,
    # phép kiểm phủ bắt trước. Bản TS xếp cùng thứ tự ấy, và ca này khoá luôn
    # thứ tự đó: đảo hai phép kiểm là thông điệp đổi và ca này đỏ.
    (_cfg(view_steps=[{"frame_lo": 0, "frame_hi": 0},
                      {"frame_lo": 1, "frame_hi": 9},
                      {"frame_lo": 2, "frame_hi": 2}]), "ra ngoài"),
    (_cfg(view_steps=["không phải object"]), "không hợp lệ"),
    (_cfg(view_steps=[{"frame_lo": None, "frame_hi": 2}]), "không trỏ tới"),
    (_cfg(view_steps=[{"frame_lo": "0", "frame_hi": "2"}]), "không trỏ tới"),
])
def test_config_hong_bi_tu_choi_dung_ly_do(cfg, mong):
    loi = validate_semantic_envelope_config(cfg)
    assert loi is not None, "cổng cho qua một config hỏng"
    assert mong in loi, f"lý do sai: {loi}"


def test_BOOL_khong_duoc_tinh_la_chi_so_khung():
    """`True` là `1` trong Python — bẫy chỉ có ở bờ Python, không có ở bờ TS.

    Không chặn thì `{"frame_lo": False, "frame_hi": True}` lọt qua như `(0, 1)`,
    và bản Python im lặng NỚI hơn bản TS mà không ai thấy.
    """
    loi = validate_semantic_envelope_config(
        _cfg(frames=_khung(2), view_steps=[{"frame_lo": False, "frame_hi": True}]))
    assert loi is not None and "không trỏ tới" in loi


def test_mot_buoc_xem_phu_ca_chuoi_la_hop_le():
    """Mức gộp thô nhất — không được nhầm thành lỗi."""
    assert validate_semantic_envelope_config(
        _cfg(view_steps=[{"frame_lo": 0, "frame_hi": 2}])) is None


def test_thu_tu_buoc_xem_KHONG_quan_trong():
    """Cổng soi phần phủ, không soi thứ tự khai — sắp trước rồi mới kiểm."""
    assert validate_semantic_envelope_config(
        _cfg(view_steps=[{"frame_lo": 2, "frame_hi": 2},
                         {"frame_lo": 0, "frame_hi": 1}])) is None
