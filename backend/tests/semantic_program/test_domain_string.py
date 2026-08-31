# -*- coding: utf-8 -*-
"""CHUỖI MIỀN — một hằng số, không phải một chuỗi gõ tay. 0 API call.

─── LỖI NÓ BỊT, VÀ NÓ ĐÃ XẢY RA HAI LẦN ───────────────────────────────────

`program_skill_for(domain)` so `domain == "hinh_hoc"`. Mọi chuỗi khác rơi vào
nhánh `else` và trả `"semantic_program"` — **prompt Tin học**. Không có lỗi,
không có cảnh báo: một đề hình học lặng lẽ được viết chương trình bằng hợp
đồng của môn khác, rồi trượt ở chỗ trông như mô hình kém.

    LẦN 1 (đã sửa) — `stage_semantic_program` viết CỨNG `"semantic_program"`,
    nên `geometry_program_generator.md` không có người gọi nào trong `app/`.
    Docstring của hàm ấy còn giữ nguyên lời kể.

    LẦN 2 (2026-08-31, tìm ra ở wave này) — SẢN PHẨM đã đúng, nhưng BỘ ĐO thì
    không: `run_generalization_matrix.py` và `probe_dihedral_synthesis.py`
    truyền `domain="geometry"`. Cả GENERALIZATION MATRIX lẫn bốn probe nhị
    diện đo hình học bằng prompt Tin học. Không con số nào của hai tuyến ấy
    nói về `geometry_program_generator.md`.

Hai lần cùng một hình: một chuỗi tự do ở chỗ đáng lẽ là một hằng số. Test này
là hàng rào thứ ba, và nó canh cả `scripts/` — vì lần thứ hai xảy ra ở đó.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.simulation.semantic_program.domain_profile import (
    DOMAIN_HINH_HOC,
    DOMAINS,
    program_skill_for,
)

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def test_chuoi_la_roi_vao_prompt_TIN_HOC_khong_bao_loi():
    """Ghi lại HÀNH VI đã cắn, để nó không bị đọc như một lỗi đánh máy vô hại."""
    assert program_skill_for("geometry") == "semantic_program"
    assert program_skill_for(DOMAIN_HINH_HOC) == "geometry_program_generator"


@pytest.mark.parametrize("f", sorted(_SCRIPTS.glob("*.py")))
def test_khong_script_nao_gõ_TAY_chuoi_mien(f):
    """Bộ đo phải truyền HẰNG SỐ. Gõ tay là mở lại đúng cửa đã cắn hai lần.

    Chỉ soi `domain=` — một chuỗi `"geometry"` ở chỗ khác (tên thư mục, nhãn
    báo cáo) là vô hại, và cấm nó sẽ biến test này thành thứ người ta tắt đi.
    """
    src = f.read_text(encoding="utf-8", errors="replace")
    xau = re.findall(r"domain\s*=\s*(['\"])([^'\"]*)\1", src)
    for _, gia_tri in xau:
        assert gia_tri in DOMAINS, (
            f"{f.name} truyền domain={gia_tri!r} — không phải miền hợp lệ "
            f"{DOMAINS}. Chuỗi lạ rơi vào prompt Tin học IM LẶNG; dùng "
            "`DOMAIN_HINH_HOC` thay vì gõ tay.")


def test_moi_mien_deu_co_skill_rieng():
    """Thêm một miền mà quên skill thì nó cũng lặng lẽ dùng prompt Tin học."""
    assert {program_skill_for(d) for d in DOMAINS} == {
        "semantic_program", "geometry_program_generator"}
