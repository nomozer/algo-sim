# -*- coding: utf-8 -*-
"""Khoá ĐỒNG BỘ Python ↔ TypeScript cho Scene3D. **0 API call.**

`scene3d.RENDER_HINT` (Python) quyết định *loại hình vẽ* nào được phát ra;
`scene3d-model.ts::RENDER_KINDS` (TS) quyết định renderer xử lý loại nào.

Hai bảng ở hai ngôn ngữ, không compiler nào nối chúng lại. Thêm một loại ở
Python mà quên nhánh ở TS thì renderer **im lặng bỏ qua** đối tượng — đúng chế
độ hỏng của bất biến #33, đã xảy ra thật với `bar_chart` (LLM khai nó và nhận
về một object rỗng, không ai biết trong nhiều tuần).

Đây là cùng khuôn sync-lock mà kho đã dùng cho `capability-descriptors` và
`semantic_program.schema.json`: một artifact sinh ở phía này, một test đỏ ở phía
kia.
"""
from __future__ import annotations

import re
from pathlib import Path

from app.simulation.semantic_program.scene3d import RENDER_HINT

_TS = (Path(__file__).resolve().parents[3] / "frontend" / "src" / "simulations"
       / "domains" / "geometry" / "scene3d-model.ts")


def _render_kinds_ts() -> list[str]:
    """Đọc `RENDER_KINDS` từ TS. Vắng mặt là ĐỎ, không phải rỗng.

    Rỗng-là-hỏng chứ không phải "chưa có gì": regex không khớp thì mọi assert
    dưới đây thành vô nghĩa mà vẫn xanh — đúng kiểu cổng-luôn-xanh mà
    `evidence.mjs` đã phải sửa một lần.
    """
    src = _TS.read_text(encoding="utf-8")
    m = re.search(r"export const RENDER_KINDS = \[(.*?)\] as const;", src, re.S)
    assert m, f"không tìm thấy `RENDER_KINDS` trong {_TS.name} — đổi tên?"
    ten = re.findall(r'"([^"]+)"', m.group(1))
    assert ten, "`RENDER_KINDS` rỗng"
    return ten


def test_hai_bang_KHOP_NHAU():
    assert sorted(set(RENDER_HINT.values())) == sorted(set(_render_kinds_ts()))


def test_khong_loai_nao_o_PYTHON_ma_TS_khong_biet():
    """Chiều nguy hiểm: backend phát ra một loại renderer không xử lý ⇒ đối
    tượng biến mất khỏi màn hình, KHÔNG có lỗi nào."""
    thieu = set(RENDER_HINT.values()) - set(_render_kinds_ts())
    assert not thieu, f"TS chưa xử lý: {sorted(thieu)}"


def test_khong_loai_nao_o_TS_ma_PYTHON_khong_phat():
    """Chiều còn lại: TS có nhánh cho một loại không tồn tại ⇒ mã chết, và mã
    chết trong renderer là chỗ người sau tưởng có năng lực mà thật ra không."""
    thua = set(_render_kinds_ts()) - set(RENDER_HINT.values())
    assert not thua, f"TS có nhánh thừa: {sorted(thua)}"


def test_TS_khong_them_hinh_ngoai_hop_dong():
    """`cylinder`/`sphere`/`curve` ở tầng TRÌNH BÀY là năng lực GIẢ: renderer vẽ
    được thứ mà không chương trình nào tạo ra nổi."""
    for cam in ("cylinder", "sphere", "curve", "torus", "cone"):
        assert cam not in _render_kinds_ts()
