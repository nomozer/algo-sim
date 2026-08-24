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
    # MỞ 2026-08-23. Câu hỏi bắt buộc của test này — *thay đổi đến từ DEV hay
    # từ một case SEALED?* — trả lời: **DEV**. Ma trận xuyên miền
    # (`cross_domain_matrix.py`) cho thấy bài "chuỗi ngoặc hợp lệ" không có kind
    # nào diễn đạt được: `membership` kiểm `item in container`, còn bài này hỏi
    # một VỊ TỪ trên toàn bộ đầu vào. Hệ quả đo được: `executable=True` mà không
    # bao giờ `servable`, cho cả một lớp bài chứ không riêng bài nào.
    #
    # Phản đối cũ ("kiểm nó đòi cài lại thuật toán đang kiểm") được trả lời đầy
    # đủ trong docstring của `obligations.py` — tóm tắt: `_extremum` cũng tính
    # lại `max`, và điều giữ tính oracle là *tính lại TỪ DỮ LIỆU ĐỀ, không đọc
    # witness để suy đáp án*, chứ không phải *không được cài lại*.
    "predicate_verdict",
    # MỞ 2026-08-24, nguồn DEV và đo được TỪ CHÍNH BẢNG NÀY: trước khi thêm,
    # **0/10 nghĩa vụ nhận được một chủ thể vô hướng** — toàn bộ taxonomy hình
    # dạng *container*. Trong khi vòng lặp tích luỹ trên một biên số
    # (`S = 1+2+…+n`, `1×2×…×n`, `S = 1³+…+n³`) là kiến trúc cơ bản nhất của
    # chương trình Tin học 10. Đó là khoảng trống của HỢP ĐỒNG, chứng minh được
    # mà không cần nhìn bài nào — không phải nhu cầu của một ca.
    #
    # Tính độc lập của oracle giữ được nhờ HAI tập ĐÓNG: `op` ∈ {sum, product}
    # và `term` ∈ `TERM_TRANSFORMS`. Số hạng ngoài tập ⇒ mức yếu, vì kiểm nó
    # đòi đánh giá biểu thức của chương trình — tức chạy lại chính nó.
    "scalar_accumulation",
    # ── MIỀN HÌNH HỌC KHÔNG GIAN — MỞ 2026-08-24 ────────────────────────────
    #
    # Câu hỏi bắt buộc của test này là *"thay đổi đến từ DEV hay từ một ca
    # SEALED?"*. Ở đây câu trả lời là **KHÔNG PHẢI CẢ HAI**: đề tài đã ĐỔI
    # (`STATUS_LEDGER §0-2026-08-24`, nguồn: GVHD), và tám kind dưới đây là
    # taxonomy của một MIỀN MỚI, không phải bản nới của miền cũ.
    #
    # Chín kind phía trên **giữ nguyên**, không đụng — chúng vẫn là taxonomy
    # thật của lượt SEALED #1, và số `A 3/40 · B 1/40` vẫn trích được.
    #
    # ĐIỂM KHÁC BẢN CHẤT so với miền Tin học: cả tám đều có checker
    # **server-owned**, không cái nào ở mức yếu. Ở đó, kiểm `predicate_verdict`
    # đòi cài lại chính thuật toán đang kiểm nên phải cãi nhau nhiều tháng; ở
    # đây kiểm là một PHÉP TÍNH giải tích (`u·v == 0`), không phải một lời giải.
    # Tính độc lập không mất, nên không kind nào phải để mức yếu.
    #
    # Vì sao tách `point_on_line` khỏi `point_on_plane` thay vì gộp `incidence`:
    # hai cái nhận CHỦ THỂ khác nhau, gộp thì bảng kiểu mất tác dụng và một đề
    # hỏi "M có thuộc (SBC)" sẽ lọt khi LLM gắn nhầm vào một đường thẳng.
    "point_on_line",
    "point_on_plane",
    "parallel",
    "perpendicular",
    "coplanar",
    "distance",
    "angle",
    "volume",
}

#: Cố ý KHÔNG có mặt — ghi lại kèm lý do để lần sau khỏi "bổ sung cho đủ".
CO_Y_KHONG_CO = {
    # `predicate_verdict` ĐÃ RỜI danh sách này 2026-08-23 — xem
    # `TAXONOMY_DA_DONG_BANG` và docstring `obligations.py`. Giữ lại một dòng
    # lịch sử thay vì xoá sạch: lý do loại nó năm xưa vẫn đúng về một nửa (không
    # kiểm được từ trạng thái cuối), chỉ sai ở vế "mất tính độc lập".
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
