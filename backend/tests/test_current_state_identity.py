# -*- coding: utf-8 -*-
"""SYNC-LOCK — bảng DANH TÍNH KHO MÃ của `docs/CURRENT_STATE.md` phải khớp NGUỒN.

VÌ SAO CẦN. `CURRENT_STATE.md` là tài liệu có thẩm quyền về "số sống"; `CLAUDE.md`
và `RULES.md` đều cố ý KHÔNG chép số, chúng trỏ về đây. Nhưng bảng danh tính lại
là thứ phải sửa bằng tay sau mỗi wave, và nó đã trôi thật: bảng ghi
`CACHE_VERSION = 25` / `Family / Target = 11 / 22` trong khi nguồn là `26` và
`12 / 23`. Một bảng danh tính SAI còn tệ hơn không có bảng — nó tự tin trả lời
sai, kèm sẵn câu lệnh kiểm mà không ai chạy.

NGUYÊN TẮC: test này KHÔNG viết số nào. Mọi giá trị DẪN XUẤT từ nguồn
(`app.main.CACHE_VERSION`, `build_matrix()` đọc registry), nên nó không tạo ra
nguồn sự thật thứ hai — nó chỉ bắt tài liệu đi theo mã.

Cùng khuôn với các sync-lock đã có (`test_manifest_providers.py`,
`test_capability_descriptors.py`, `code-index-sync.test.ts`): nhắc thì trôi,
đỏ thì không.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.main import CACHE_VERSION

_DOC = Path(__file__).resolve().parents[2] / "docs" / "CURRENT_STATE.md"
_MARKER = "DANH TÍNH KHO MÃ"


def _identity_table() -> str:
    """Chỉ lấy KHỐI bảng danh tính.

    Cả file nhắc `CACHE_VERSION` hàng chục lần trong nhật ký bump, nên quét toàn
    file sẽ khớp nhầm một dòng lịch sử rồi báo xanh vì lý do sai.
    """
    text = _DOC.read_text(encoding="utf-8")
    start = text.find(_MARKER)
    assert start > 0, f"không tìm thấy khối '{_MARKER}' trong {_DOC.name}"
    # Khối kết thúc ở tiêu đề con đầu tiên bên trong blockquote.
    end = text.find("> ###", start)
    assert end > start, "khối danh tính không có điểm kết thúc nhận ra được"
    return text[start:end]


def _row(label: str) -> str:
    """Ô giá trị của hàng có nhãn `label` trong bảng danh tính.

    Chỉ nhận dòng THẬT SỰ là hàng bảng (≥3 dấu `|`). Khối danh tính có cả văn
    xuôi trong blockquote, và văn xuôi đó nhắc chính những tên này — khớp trần
    theo `startswith('>')` sẽ bắt nhầm câu văn rồi báo lỗi ở chỗ vô can.
    """
    for line in _identity_table().splitlines():
        stripped = line.lstrip()
        if label not in line or not stripped.startswith(">") or line.count("|") < 3:
            continue
        cells = [c.strip() for c in stripped.lstrip(">").strip().split("|")]
        # ['', nhãn, giá trị, ''] — ô giá trị là phần tử thứ 3.
        return cells[2]
    raise AssertionError(f"bảng danh tính thiếu hàng '{label}'")


def test_cache_version_trong_bang_danh_tinh_khop_nguon():
    cell = _row("CACHE_VERSION")
    assert f"**{CACHE_VERSION}**" in cell, (
        f"docs/CURRENT_STATE.md ghi CACHE_VERSION = {cell!r} nhưng nguồn "
        f"(app.main.CACHE_VERSION) là {CACHE_VERSION!r}. Sửa TÀI LIỆU, đừng sửa mã."
    )



def test_nang_luc_hinh_hoc_trong_bang_danh_tinh_khop_tham_quyen():
    """Số sống của bảng danh tính nay là NĂNG LỰC HÌNH HỌC, không phải danh mục.

    ⚠️ Ba test cũ ở đây khoá `Family / Target` và `phân rã family` theo
    `build_matrix()`/`CATALOG` — danh mục 24 target Tin học. Danh mục ấy đã gỡ
    (`LEGACY_INFORMATICS_REMOVAL`), nên bảng phải khai thứ đang chạy: số phép
    dựng, số câu lệnh dựng, số phép đo. Vẫn là số SỐNG, vẫn dẫn từ thẩm quyền,
    vẫn kèm câu lệnh kiểm được.
    """
    from app.simulation.semantic_program.ir_static_check import (
        _CHU_KY, _KIEU_DO, _KIEU_DUNG,
    )

    cell = _row('Năng lực hình học')
    mong = f'**{len(_CHU_KY)} phép dựng · {len(_KIEU_DUNG)} câu lệnh · {len(_KIEU_DO)} phép đo**'
    assert mong in cell, (
        f'docs/CURRENT_STATE.md ghi {cell!r} nhưng thẩm quyền đếm được {mong}. '
        f'Kiểm: backend/scripts/audit_named_operand_ergonomics.py')


def test_bang_danh_tinh_van_giu_cau_lenh_kiem_duoc():
    """Hàng số sống phải kèm cách kiểm — bảng không có đường kiểm thì lại trôi."""
    for label in ('CACHE_VERSION', 'Năng lực hình học'):
        cell = _row(label)
        assert 'kiểm:' in cell, f"hàng '{label}' mất câu lệnh kiểm"
