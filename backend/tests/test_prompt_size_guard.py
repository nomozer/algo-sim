# -*- coding: utf-8 -*-
"""Cổng TĨNH chặn prompt phình — hard-fail build (spec §6.4).

Vì sao cổng nằm ở tầng tĩnh chứ không ở số live: số live nhiễu và tốn tiền, để
nó gác cổng mặc định là vừa đắt vừa hay đỏ oan. Live token regression chỉ BÁO
CÁO. Còn kích thước prompt thì tất định, không tốn call, và đo đúng thứ đang
trôi: mỗi lần vá lỗi bằng cách nhồi thêm một dòng vào prompt.

Chi phí thật của một bản vá prompt gồm HAI phần: prompt to hơn vĩnh viễn, CỘNG
một đợt gọi lại toàn bộ vì sửa `skills/*.md` buộc bump `CACHE_VERSION` (xoá sạch
exact-cache). Cổng này chặn phần thứ nhất.

NGƯỠNG: chốt 2026-08-20 ở mức ~5% trên kích thước hiện tại. Hạ được thì hạ.
TĂNG ngưỡng phải kèm lý do trong commit message — và trước khi tăng, hãy hỏi
luật vừa thêm có mã hoá được xuống schema/validator không (spec §6.3.1).
"""
from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parents[1] / "app" / "ai" / "skills"

BUDGET_BYTES: dict[str, int] = {
    "adapt.md": 1500,
    "analyze.md": 6900,
    "classify.md": 4550,
    "edit.md": 3550,
    "explain.md": 1550,
    "semantic_program.md": 2100,
    "simulate.md": 1450,
    "transcribe.md": 1050,
}


@pytest.mark.parametrize("name,budget", sorted(BUDGET_BYTES.items()))
def test_prompt_khong_vuot_ngan_sach_byte(name, budget):
    actual = (SKILLS / name).stat().st_size
    assert actual <= budget, (
        f"{name} = {actual} byte, vượt ngân sách {budget}. "
        "Luật nào mã hoá được thì chuyển sang schema/validator, đừng nhồi prompt: "
        "luật trong prompt là GỢI Ý, luật trong validator là RÀNG BUỘC."
    )


def test_moi_skill_deu_co_ngan_sach():
    """Thêm skill mới mà quên khai ngân sách ⇒ nó phình tự do, không ai biết."""
    tren_dia = {p.name for p in SKILLS.glob("*.md")}
    thieu = tren_dia - set(BUDGET_BYTES)
    assert not thieu, f"Skill chưa khai ngân sách byte: {sorted(thieu)}"


def test_khong_khai_ngan_sach_cho_skill_da_bien_mat():
    tren_dia = {p.name for p in SKILLS.glob("*.md")}
    thua = set(BUDGET_BYTES) - tren_dia
    assert not thua, f"Ngân sách khai cho skill không còn tồn tại: {sorted(thua)}"
