# -*- coding: utf-8 -*-
"""CHUỖI MIỀN — hằng số tất định cho cổng phạm vi và định danh miền. 0 API call."""
from __future__ import annotations

import ast
from functools import lru_cache
from pathlib import Path

import pytest

from app.simulation.semantic_program.domain_profile import (
    DOMAIN_HINH_HOC,
    DOMAIN_TIN_HOC,
    DOMAINS,
    co_duong_thuc_thi,
    detect_domain,
)

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


@lru_cache(maxsize=None)
def _moi_loi_goi(f: Path) -> tuple[ast.Call, ...]:
    cay = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
    return tuple(n for n in ast.walk(cay) if isinstance(n, ast.Call))


def _ten_goi(goi: ast.Call) -> str:
    fn = goi.func
    return getattr(fn, "attr", None) or getattr(fn, "id", "") or ""


def test_chi_mien_hinh_hoc_co_duong_thuc_thi_san_pham():
    assert set(DOMAINS) == {DOMAIN_HINH_HOC, DOMAIN_TIN_HOC}
    assert co_duong_thuc_thi("Tính diện tích thiết diện.", DOMAIN_HINH_HOC) is True
    assert co_duong_thuc_thi("Tính diện tích thiết diện.", DOMAIN_TIN_HOC) is False
    assert detect_domain("Cho hình chóp S.ABCD có đáy là hình vuông.") == DOMAIN_HINH_HOC


@pytest.mark.parametrize("f", sorted(_SCRIPTS.glob("*.py")))
def test_khong_script_nao_gõ_TAY_chuoi_mien(f):
    """Bộ đo phải truyền HẰNG SỐ. Gõ tay là mở lại đúng cửa đã cắn hai lần.

    Chỉ soi `domain=` — một chuỗi `"geometry"` ở chỗ khác (tên thư mục, nhãn
    báo cáo) là vô hại, và cấm nó sẽ biến test này thành thứ người ta tắt đi.
    """
    # DUYỆT AST, không khớp văn bản.
    #
    # Khớp văn bản đã hỏng hai lần liên tiếp ở đúng file này: một lần khớp
    # chính chú thích giải thích guard, một lần khớp một chuỗi DỮ LIỆU
    # (`audit_synthesis_failures` kể lại lỗi cũ bằng chữ). Bóc chú thích chỉ
    # sửa lần đầu. Câu hỏi thật là *"có một lời gọi nào truyền chuỗi lạ
    # không"*, và chỉ cây cú pháp trả lời được — mọi phép xấp xỉ bằng regex
    # đều sẽ vướng vào văn bản nói VỀ mã.
    for goi in _moi_loi_goi(f):
        for kw in goi.keywords:
            if kw.arg != "domain":
                continue
            if isinstance(kw.value, ast.Constant) and isinstance(
                    kw.value.value, str):
                assert kw.value.value in DOMAINS, (
                    f"{f.name}:{kw.value.lineno} truyền "
                    f"domain={kw.value.value!r} — không phải miền hợp lệ "
                    f"{DOMAINS}. Chuỗi lạ rơi vào prompt Tin học IM LẶNG; "
                    "dùng `DOMAIN_HINH_HOC` thay vì gõ tay.")


@pytest.mark.parametrize("f", sorted(_SCRIPTS.glob("*.py")))
def test_moi_lenh_goi_TONG_HOP_deu_truyen_domain(f):
    """Tham số BỊ BỎ QUÊN — biến thể thứ ba, guard trên KHÔNG bắt được.

    `stage_semantic_program(de, {}, api_key, contract)` truyền bốn tham số vị
    trí, nên `domain` để `None` và tầng tổng hợp dùng prompt TIN HỌC. Không
    có chuỗi nào sai để mà soi: cái sai là một chỗ TRỐNG.

    `run_geometry_dev_evaluation.py` mắc đúng lỗi này trong khi
    `stage_semantic_analyze` ngay trên nó đã truyền `DOMAIN_HINH_HOC` — nửa
    đường đúng miền, nửa đường không, và artifact `dev-results*/` mang dấu vết
    ấy suốt nhiều wave.

    Bộ đo là chỗ DUY NHẤT bị đòi: sản phẩm đi qua `detect_domain`, luôn có
    miền. Một script gọi tầng tổng hợp mà không nói miền thì nó đang đo một
    hệ khác hệ nó tưởng.
    """
    for goi in _moi_loi_goi(f):
        if _ten_goi(goi) != "stage_semantic_program":
            continue
        co = {kw.arg for kw in goi.keywords}
        assert "domain" in co, (
            f"{f.name}:{goi.lineno} gọi `stage_semantic_program` mà KHÔNG "
            "truyền `domain=` — tầng tổng hợp sẽ im lặng dùng prompt Tin học")


def test_chi_giu_skill_transcribe_sau_khi_retire_llm_only():
    """Sau khi retire `LLM_ONLY`, `skills/` chỉ giữ `transcribe.md` cho `/api/image/extract`."""
    from app.ai.gemini import SKILLS_DIR

    assert [p.name for p in sorted(SKILLS_DIR.glob("*.md"))] == ["transcribe.md"]
