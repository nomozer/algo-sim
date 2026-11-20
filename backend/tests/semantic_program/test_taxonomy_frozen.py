# -*- coding: utf-8 -*-
"""Khoá TAXONOMY ĐÃ ĐÓNG BĂNG (hard scope lock §1.1).

Sau khi SEALED niêm phong, thêm một obligation checker để cải thiện kết quả SEALED làm seal MẤT HIỆU LỰC. Một dòng
thêm vào dict thì lặng lẽ — nên khoá bằng test: đổi taxonomy là ĐỎ, và người đổi phải đối diện câu hỏi "thay đổi này
đến từ DEV hay từ một ca SEALED?".

─── /13 (2026-11-20): taxonomy chỉ còn MIỀN HÌNH HỌC ─────────────────────────────────────────────────────────────
Câu hỏi bắt buộc của test này — trả lời: **KHÔNG TỪ DEV, KHÔNG TỪ SEALED**. Nguồn là khoá phạm vi của Owner
("loại bỏ hoàn toàn miền Tin học"), quyết định trước mọi phép đo của /13. Mười một nghĩa vụ Tin học (danh sách ở
`CO_Y_KHONG_CO`) rời taxonomy cùng checker của chúng. Seal #1 (`a075e9f5…`) thuộc miền Tin học: điểm số lịch sử vẫn
trích được từ bằng chứng đóng băng của nó, nhưng hệ hiện hành không còn chạy lại được lượt ấy — so số cũ với hệ mới
là so hai hệ khác nhau. Lịch sử mở từng nghĩa vụ hình học (`section_matches` 2026-08-30, `radius` 2026-09-03,
`area`/`lateral_area` 2026-09-04) nằm trong git history của file này.
"""
from app.simulation.semantic_program.obligations import OBLIGATION_KINDS

TAXONOMY_DA_DONG_BANG = {
    "point_on_line",
    "point_on_plane",
    "parallel",
    "perpendicular",
    "coplanar",
    "distance",
    "angle",
    "volume",
    "section_matches",
    "radius",
    "area",
    "lateral_area",
}

#: Cố ý KHÔNG có mặt — ghi lại kèm lý do để lần sau khỏi "bổ sung cho đủ".
_TIN_HOC_DA_GO = "nghĩa vụ miền Tin học — gỡ ở /13 theo khoá phạm vi của Owner"
CO_Y_KHONG_CO = {
    "count_matching": "đã bị bao trùm bởi aggregate_matching (đếm = gộp với phép count)",
    "distinct_preserving_order": "là một phép của derived_sequence, không phải nguyên thuỷ riêng",
    "connected_components": "tổ hợp được từ reachability lặp — xét TỔ HỢP trước khi xét MỞ RỘNG",
    **{k: _TIN_HOC_DA_GO for k in (
        "extremum", "aggregate_matching", "ordering", "membership", "first_match_index", "total_mapping",
        "derived_sequence", "reachability", "structural_traversal", "predicate_verdict", "scalar_accumulation",
    )},
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


def test_rows_written_before_the_IR_container_prune_miss():
    """CACHE_VERSION 149 -> 150 (/13): taxonomy, IR schema and grammar surface lost the informatics vocabulary, so a
    `149:route-d` row was written by a system that still carried it and must MISS."""
    from tests.cache_policy import assert_cache_policy_at_least, assert_route_d_row_misses

    assert_cache_policy_at_least(150)
    assert_route_d_row_misses("149:route-d")


def test_moi_nghia_vu_deu_khai_mien_kieu_khong_rong():
    """Nghĩa vụ không khai miền kiểu thì `accepts_container_type` luôn False —
    nó sẽ từ chối mọi thứ một cách câm."""
    rong = sorted(k for k, v in OBLIGATION_KINDS.items() if not v)
    assert not rong, f"Nghĩa vụ khai miền kiểu RỖNG: {rong}"
