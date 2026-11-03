# -*- coding: utf-8 -*-
"""Cổng kích thước prompt trên đĩa (`skills/transcribe.md`) và prompt trích xuất Hybrid (`typed_fact_next_extraction`).

Sau khi retire `LLM_ONLY`, thư mục `backend/app/ai/skills/` chỉ còn giữ `transcribe.md` cho `/api/image/extract`,
còn tuyến chính Hybrid `/4` dùng `typed_fact_next_extraction.INSTRUCTION`.
"""

from app.ai import typed_fact_next_extraction as TFN
from app.ai.gemini import SKILLS_DIR

BUDGET_BYTES: dict[str, int] = {
    "transcribe.md": 1970,
}

HYBRID_EXTRACTION_INSTRUCTION_BUDGET_BYTES = 16384


def test_moi_skill_nam_trong_ngan_sach_byte():
    vi_pham: list[str] = []
    for path in sorted(SKILLS_DIR.glob("*.md")):
        size = len(path.read_bytes())
        limit = BUDGET_BYTES.get(path.name)
        if limit is None:
            vi_pham.append(f"{path.name} ({size}B): skill mới chưa đăng ký ngân sách")
        elif size > limit:
            vi_pham.append(f"{path.name}: {size}B > ngân sách {limit}B (+{size - limit}B)")
    assert not vi_pham, "Skill vượt ngân sách prompt:\n  - " + "\n  - ".join(vi_pham)


def test_khong_khai_ngan_sach_cho_skill_da_bien_mat():
    tren_dia = {p.name for p in SKILLS_DIR.glob("*.md")}
    thua = set(BUDGET_BYTES) - tren_dia
    assert not thua, f"BUDGET_BYTES còn giữ skill đã xóa: {sorted(thua)}"


def test_hybrid_typed_fact_next_instruction_nam_trong_ngan_sach():
    size = len(TFN.TYPED_FACT_NEXT_SYSTEM_INSTRUCTION.encode("utf-8"))
    assert 500 < size <= HYBRID_EXTRACTION_INSTRUCTION_BUDGET_BYTES
