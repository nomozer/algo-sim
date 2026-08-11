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

from app.catalog_conformance import build_matrix
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


def test_family_va_target_trong_bang_danh_tinh_khop_registry():
    rows = build_matrix()
    targets = len(rows)
    families = len({f for r in rows for f in r["family_ids"]})
    cell = _row("Family / Target")
    assert f"**{families} / {targets}**" in cell, (
        f"docs/CURRENT_STATE.md ghi Family / Target = {cell!r} nhưng registry "
        f"(build_matrix) đếm được {families} / {targets}. "
        f"Kiểm: backend/scripts/catalog_runtime_matrix.py"
    )


def test_bang_danh_tinh_van_giu_cau_lenh_kiem_duoc():
    """Hàng số sống phải kèm cách kiểm — bảng không có đường kiểm thì lại trôi."""
    for label in ("CACHE_VERSION", "Family / Target"):
        cell = _row(label)
        assert "kiểm:" in cell, f"hàng '{label}' mất câu lệnh kiểm"


def test_phan_ra_family_dem_dung_so_family_representation():
    """Dòng phân rã nói '10 computation + 2 representation' — cũng là số sống."""
    authority: dict[str, set[str]] = {}
    for target in build_matrix():
        for fid in target["family_ids"]:
            authority.setdefault(fid, set())
    # result_authority sống ở descriptor của SimSpec, không ở matrix row.
    from app.simulation.catalog import CATALOG

    for spec in CATALOG.values():
        for m in getattr(spec, "family_memberships", ()):
            authority.setdefault(str(m.family_id.value), set()).add(
                str(m.result_authority.value)
            )
    representation = sorted(f for f, a in authority.items() if a == {"representation"})
    computation = sorted(f for f, a in authority.items() if a == {"computation"})
    cell = _row("phân rã family")
    assert f"**{len(computation)} mô phỏng cơ chế tính toán**" in cell, (
        f"phân rã family ghi {cell!r} nhưng registry đếm {len(computation)} family "
        f"result_authority=computation"
    )
    assert f"**{len(representation)} biểu diễn**" in cell, (
        f"phân rã family ghi {cell!r} nhưng registry đếm {len(representation)} family "
        f"result_authority=representation: {representation}"
    )
