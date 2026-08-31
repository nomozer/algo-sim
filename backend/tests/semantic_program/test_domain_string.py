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

import ast
from functools import lru_cache
from pathlib import Path

import pytest

from app.simulation.semantic_program.domain_profile import (
    DOMAIN_HINH_HOC,
    DOMAIN_TIN_HOC,
    DOMAINS,
    MienKhongHopLe,
    analyze_skill_for,
    program_skill_for,
)

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


@lru_cache(maxsize=None)
def _moi_loi_goi(f: Path) -> tuple[ast.Call, ...]:
    """Mọi `ast.Call` trong file. Cây cú pháp, không phải văn bản.

    Một file không parse được là một file không kiểm được, và im lặng bỏ qua
    nó là mở đúng cửa guard này định đóng — nên nó ĐỎ.
    """
    cay = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
    return tuple(n for n in ast.walk(cay) if isinstance(n, ast.Call))


def _ten_goi(goi: ast.Call) -> str:
    fn = goi.func
    return getattr(fn, "attr", None) or getattr(fn, "id", "") or ""


def test_chuoi_la_nay_NEM_thay_vi_roi_vao_prompt_TIN_HOC():
    """Cửa `else` đã đóng (2026-09-01).

    Bản trước của test này khẳng định chiều NGƯỢC LẠI — nó *ghi lại* hành vi
    `"geometry"` → prompt Tin học để hành vi ấy không bị đọc như lỗi đánh máy
    vô hại. Ghi lại một cái bẫy không gỡ được cái bẫy: nó vẫn cắn lần thứ hai.

    `else → Tin học` là một mặc định im lặng cho một câu hỏi không có mặc
    định. Nay miền lạ NÉM, trước khi tiêu một call nào.
    """
    with pytest.raises(MienKhongHopLe):
        program_skill_for("geometry")
    with pytest.raises(MienKhongHopLe):
        analyze_skill_for("geometry")
    assert program_skill_for(DOMAIN_HINH_HOC) == "geometry_program_generator"
    assert analyze_skill_for(DOMAIN_HINH_HOC) == "geometry_analyze"


@pytest.mark.parametrize("xau", ["", "Geometry", "HINH_HOC", "hinh hoc",
                                 "geometry_3d", None, 0])
def test_moi_bien_the_GAN_DUNG_deu_nem(xau):
    """Gần đúng là nguy hiểm nhất: nó trông như đã dùng hằng số."""
    with pytest.raises(MienKhongHopLe):
        program_skill_for(xau)


def test_duong_TIN_HOC_hop_le_van_di_duoc():
    """Đóng `else` không được chặn miền Tin học — nó đi bằng hằng số của nó."""
    assert program_skill_for(DOMAIN_TIN_HOC) == "semantic_program"
    assert analyze_skill_for(DOMAIN_TIN_HOC) == "semantic_analyze"


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


def test_moi_mien_deu_co_skill_rieng():
    """Thêm một miền mà quên skill thì nó cũng lặng lẽ dùng prompt Tin học."""
    assert {program_skill_for(d) for d in DOMAINS} == {
        "semantic_program", "geometry_program_generator"}
