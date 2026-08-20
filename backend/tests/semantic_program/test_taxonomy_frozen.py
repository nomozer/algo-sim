# -*- coding: utf-8 -*-
"""Khoá TAXONOMY ĐÃ ĐÓNG BĂNG (hard scope lock §1.1).

Sau khi SEALED niêm phong, thêm một obligation checker để cải thiện kết quả
SEALED làm seal MẤT HIỆU LỰC. Nhưng một dòng thêm vào dict thì lặng lẽ — nên
khoá bằng test: đổi taxonomy là ĐỎ, và người đổi phải đối diện câu hỏi
"thay đổi này đến từ DEV hay từ một ca SEALED?".

Danh sách dưới đây chốt 2026-08-20 từ phân tích DEV
(`docs/evaluation/semantic-benchmark/dev/DEV_TAXONOMY_ANALYSIS.md`).
"""
from app.simulation.semantic_program.obligations import (
    AGGREGATE_OPS,
    OBLIGATION_KINDS,
    SEQUENCE_TRANSFORMS,
)

TAXONOMY_DA_DONG_BANG = {
    "extremum",
    "aggregate_matching",
    "ordering",
    "membership",
    "first_match_index",
    "total_mapping",
    "derived_sequence",
    "reachability",
    "structural_traversal",
}

#: Cố ý KHÔNG có mặt — ghi lại kèm lý do để lần sau khỏi "bổ sung cho đủ".
CO_Y_KHONG_CO = {
    "predicate_verdict": "kiểm nó đòi cài lại chính thuật toán đang kiểm → oracle mất tính độc lập; đây là verification_gap thật",
    "count_matching": "đã bị bao trùm bởi aggregate_matching (đếm = gộp với phép count)",
    "distinct_preserving_order": "là một phép của derived_sequence, không phải nguyên thuỷ riêng",
    "connected_components": "tổ hợp được từ reachability lặp — xét TỔ HỢP trước khi xét MỞ RỘNG",
}


def test_taxonomy_dung_bang_ban_da_dong_bang():
    assert set(OBLIGATION_KINDS) == TAXONOMY_DA_DONG_BANG, (
        "Taxonomy đã đổi. Câu hỏi bắt buộc trước khi sửa test này: thay đổi đến "
        "từ DEV hay từ một case SEALED? Từ SEALED ⇒ seal MẤT HIỆU LỰC (§7.4)."
    )


def test_khong_lang_le_them_lai_cai_da_co_y_loai():
    lan_vao = sorted(set(CO_Y_KHONG_CO) & set(OBLIGATION_KINDS))
    assert not lan_vao, (
        "Nghĩa vụ đã cố ý loại nay lại có mặt: "
        + "; ".join(f"{k} — {CO_Y_KHONG_CO[k]}" for k in lan_vao)
    )


def test_phep_gop_va_phep_bien_doi_deu_dong():
    assert AGGREGATE_OPS == {"count", "sum", "product", "max", "min"}
    assert SEQUENCE_TRANSFORMS == {"reverse", "distinct", "filter", "map", "identity"}


def test_moi_nghia_vu_deu_khai_mien_kieu_khong_rong():
    """Nghĩa vụ không khai miền kiểu thì `accepts_container_type` luôn False —
    nó sẽ từ chối mọi thứ một cách câm."""
    rong = sorted(k for k, v in OBLIGATION_KINDS.items() if not v)
    assert not rong, f"Nghĩa vụ khai miền kiểu RỖNG: {rong}"
