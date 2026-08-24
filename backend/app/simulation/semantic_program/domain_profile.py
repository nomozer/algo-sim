# -*- coding: utf-8 -*-
"""Hồ sơ MIỀN của route ngữ nghĩa — mỗi miền có từ vựng `analyze` riêng.

VÌ SAO TỒN TẠI, ĐO ĐƯỢC Ở PHASE 5 (2026-08-24): `stage_semantic_program` đã
được ép sang prompt hình học, nhưng `stage_semantic_analyze` thì không. Enum
nghĩa vụ của nó là `sorted(OBLIGATION_KINDS)` — **cả 19**, gồm 9 nghĩa vụ Tin
học. Hệ quả đo được trên 6 bài hình học hợp lệ:

    geo_02  đề hỏi `point_on_line`  → mô hình khai `derived_sequence`
    geo_03  đề hỏi `coplanar`       → mô hình khai `structural_traversal`
    geo_04  đề hỏi `point_on_plane` → mô hình khai `predicate_verdict`

`obligation_match` 3/6. Không phải mô hình kém: prompt phân tích **chưa từng
nhắc tới hình học**, mà enum thì mời gọi cả chín cái tên Tin học. Bắt ai đó
chọn đúng trong một danh sách sai là một bài kiểm tra hỏng.

─── LUẬT DẪN XUẤT, KHÔNG CHÉP TAY ────────────────────────────────────────────

Tập nghĩa vụ của mỗi miền **suy ra từ bảng kiểu container** trong
`obligations.OBLIGATION_KINDS`, không viết lại thành một danh sách thứ hai. Lý
do đã trả giá ở kho này nhiều lần: hai danh sách rời nhau thì lần thêm nghĩa vụ
tiếp theo sẽ lệch, và lệch **câm** — miền mới có checker mà `analyze` không có
từ để khai.

Phép thử: nghĩa vụ nào nhận TOÀN BỘ chủ thể là kiểu hình học thì thuộc miền
hình học. Nghĩa vụ nhận cả hai (không có cái nào hiện giờ) sẽ thuộc **cả hai** —
đó là hành vi đúng, không phải kẽ hở.

─── FAIL-SAFE CỦA BỘ NHẬN MIỀN ───────────────────────────────────────────────

`detect_domain` là **suy đoán**, và nó được thiết kế để đoán sai về phía an
toàn: không đủ dấu hiệu ⇒ trả `tin_hoc`, tức **đúng hành vi hiện tại**. 24
target Tin học không thể bị bộ nhận miền làm hỏng, vì cửa duy nhất nó mở là cửa
đi sang hình học.

Đường đo (`run_geometry_dev_evaluation.py`) **không dùng** bộ nhận miền — nó
truyền `domain` thẳng. Phép đo không được phụ thuộc vào một suy đoán.
"""
from __future__ import annotations

from .geometry_exec import GEOMETRY_TYPES
from .obligations import OBLIGATION_KINDS

DOMAIN_TIN_HOC = "tin_hoc"
DOMAIN_HINH_HOC = "hinh_hoc"
DOMAINS = (DOMAIN_TIN_HOC, DOMAIN_HINH_HOC)


def geometry_obligation_kinds() -> frozenset[str]:
    """Nghĩa vụ nhận TOÀN BỘ chủ thể là kiểu hình học. Dẫn xuất, không chép."""
    return frozenset(
        k for k, chu_the in OBLIGATION_KINDS.items()
        if chu_the and chu_the <= GEOMETRY_TYPES
    )


def tin_hoc_obligation_kinds() -> frozenset[str]:
    """Phần bù. Nghĩa vụ dùng được ở CẢ HAI miền sẽ có mặt ở cả hai tập."""
    geo = geometry_obligation_kinds()
    return frozenset(
        k for k, chu_the in OBLIGATION_KINDS.items()
        if k not in geo or not (chu_the <= GEOMETRY_TYPES)
    )


def obligation_kinds_for(domain: str) -> frozenset[str]:
    if domain == DOMAIN_HINH_HOC:
        return geometry_obligation_kinds()
    return tin_hoc_obligation_kinds()


#: Kiểu mục dữ liệu đề cho, theo miền.
#:
#: Miền hình học KHÔNG dùng `array`/`graph`/`tree_node`: dữ kiện của nó là *"cạnh
#: đáy bằng 1"*, *"SA ⊥ (ABCD)"* — một số đo hoặc một quan hệ, không phải một
#: cấu trúc dữ liệu. Cho `analyze` nguyên bảng kiểu Tin học là mời nó khai hình
#: chóp thành `array`, và mọi thứ phía sau sẽ hỏng theo một cách khó đọc.
INPUT_FACT_KINDS_HINH_HOC = ("float", "int", "str", "bool")


def analyze_skill_for(domain: str) -> str:
    """Skill nào đọc đề ở miền này."""
    return "geometry_analyze" if domain == DOMAIN_HINH_HOC else "semantic_analyze"


def program_skill_for(domain: str) -> str:
    """Skill nào viết chương trình ở miền này."""
    return (
        "geometry_program_generator"
        if domain == DOMAIN_HINH_HOC
        else "semantic_program"
    )


# ── Bộ nhận miền — TẤT ĐỊNH, và cố ý thiên về `tin_hoc` ───────────────────
#
# Hai hạng dấu hiệu, khác nhau ở mức RIÊNG BIỆT chứ không ở độ "quan trọng":
#
#   MẠNH  — cụm chỉ xuất hiện trong hình học không gian. Một cái là đủ.
#   YẾU   — cụm hình học nhưng dùng chung được với văn cảnh khác. Cần ba cái,
#           để một đề Tin học lỡ nhắc "song song" không bị kéo sang.
#
# Ngưỡng 3 không phải số đẹp: nó là số nhỏ nhất mà bài `geo_08` (hình vuông
# phẳng, không có cụm mạnh nào) vẫn qua được — `mặt phẳng`, `đường thẳng`,
# `đường chéo`, `góc giữa` = 4. Hạ xuống 2 là nới không có lý do.
_DAU_HIEU_MANH = (
    "hình chóp", "khối chóp", "tứ diện", "lăng trụ", "hình hộp", "hình nón",
    "hình trụ", "mặt cầu", "thiết diện", "giao tuyến", "mặt phẳng đáy",
    "vuông góc với đáy", "vuông góc với mặt phẳng", "hình chiếu vuông góc",
    "đồng phẳng", "chéo nhau",
)
_DAU_HIEU_YEU = (
    "mặt phẳng", "đường thẳng", "đường chéo", "góc giữa", "trung điểm",
    "hình vuông", "hình chữ nhật", "tam giác", "thể tích", "khoảng cách từ",
    "song song", "vuông góc", "cạnh bên", "đáy",
)


def detect_domain(text: str) -> str:
    """Đoán miền của một đề. Không chắc ⇒ `tin_hoc` (= hành vi hiện tại).

    KHÔNG dùng ở đường đo. Đây là tiện ích cho đường sản phẩm, và giới hạn của
    nó phải đọc kèm: nó nhận diện **từ ngữ**, không nhận diện **bài toán**. Một
    đề Tin học về "đồ thị hình học" viết bằng đủ ba cụm yếu sẽ bị kéo sang, và
    khi ấy `analyze` hình học sẽ khai được rất ít nghĩa vụ — thất bại lộ ra ở
    C₁a chứ không âm thầm.
    """
    if not text:
        return DOMAIN_TIN_HOC
    t = text.lower()
    if any(d in t for d in _DAU_HIEU_MANH):
        return DOMAIN_HINH_HOC
    if sum(1 for d in _DAU_HIEU_YEU if d in t) >= 3:
        return DOMAIN_HINH_HOC
    return DOMAIN_TIN_HOC
