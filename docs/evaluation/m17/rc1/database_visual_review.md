# M17 W2B-VR — Review thị giác `database.relational_table_query`

Chụp trên **Chrome thật** qua CDP (không SSR), hai viewport. Phán quyết REAL/PARTIAL/BROKEN do **người xem toàn bộ PNG** chấm.

- Fixture: **9** · ảnh: **42** (desktop 21 · hẹp 21)
- REAL **9** · PARTIAL **0** · BROKEN **0** · GAP **0**
- Lỗi: tìm **7** · sửa **7** · còn chặn **0**

| Fixture | Loại | Ảnh | Trạng thái |
|---|---|---|---|
| `vrdb1-filter-projection` | canonical | 6 | **REAL_VISUAL** |
| `vrdb2-stable-sort-desc` | canonical | 6 | **REAL_VISUAL** |
| `vrdb3-count-after-filter` | canonical | 6 | **REAL_VISUAL** |
| `vrdb4-avg-empty-cells` | boundary | 6 | **REAL_VISUAL** |
| `vrdb5-combined-pipeline` | canonical | 6 | **REAL_VISUAL** |
| `vrdb6-boundary-wide` | stress | 6 | **REAL_VISUAL** |
| `vrdb8-missing-table` | refusal | 2 | **REAL_VISUAL** |
| `vrdb9-join-unsupported` | refusal | 2 | **REAL_VISUAL** |
| `vrdb10-two-queries` | refusal | 2 | **REAL_VISUAL** |

## Nhận xét từng fixture

### `vrdb1-filter-projection` — REAL_VISUAL
- N/A: không
- Bảng nguồn hiện đủ 8 hàng; hàng đang xét (▶ Đang xét) và giữ (✓ Giữ) phân biệt bằng icon+chữ+màu, không chỉ màu; cột không chọn CHỈ mờ SAU bước chọn cột; kết quả hiện dần.

### `vrdb2-stable-sort-desc` — REAL_VISUAL
- N/A: không
- Lọc tổ B còn 3 hàng; sau sắp xếp giảm dần Bùi Linh 9 trước, Trần Bình và Phạm Dũng CÙNG 8 giữ NGUYÊN thứ tự gốc (Bình trước Dũng) — sắp xếp ổn định quan sát được; Inspector ghi 'Sắp xếp: Điểm giảm dần (ổn định)'.

### `vrdb3-count-after-filter` — REAL_VISUAL
- N/A: PROJECTION_CLEAR, SORT_MECHANISM_CLEAR
- Lọc tổ A (3 hàng giữ, còn lại ✕ Loại gạch ngang mờ); accumulator đếm 1→2→3 hiện dần ở giai đoạn tích luỹ; COUNT cuối KHÔNG lộ ở bước đọc hàng.

### `vrdb4-avg-empty-cells` — REAL_VISUAL
- N/A: FILTER_MECHANISM_CLEAR, PROJECTION_CLEAR, SORT_MECHANISM_CLEAR
- Ô trống hiện '— trống —' in nghiêng, PHÂN BIỆT rõ với 0; bước tích luỹ nêu 'ô Điểm kiểm tra còn trống → bỏ qua, không tính là 0'; AVG = 8 (=(8+10+6)/3 trên 3 hàng hợp lệ), KHÔNG phải (8+0+10+0+6)/5.

### `vrdb5-combined-pipeline` — REAL_VISUAL
- N/A: không
- Năm tầng trong MỘT truy vấn: 3 hàng '✓ Giữ' đầu, 3 hàng '— Không lấy' (limit cắt) mờ — phân biệt rõ với 'Loại' của lọc; AVG = 8.9167 dùng nhãn 'Điểm'; hiểu được đây là một pipeline.

### `vrdb6-boundary-wide` — REAL_VISUAL
- N/A: AGGREGATE_CLEAR
- 12 hàng × 8 cột, nhãn tiếng Việt dài, số âm/thập phân, ô trống. Ở 768px bảng CUỘN NGANG trong khung riêng, trang KHÔNG tràn ngang; căn cột đúng; lọc + sắp xếp theo cột chênh lệch (số âm) quan sát được.

### `vrdb8-missing-table` — REAL_VISUAL
- N/A: TABLE_STRUCTURE_CLEAR, CURRENT_STATE_CLEAR, FILTER_MECHANISM_CLEAR, PROJECTION_CLEAR, SORT_MECHANISM_CLEAR, AGGREGATE_CLEAR, PROGRESSIVE_REVEAL_PASS, TERMINOLOGY_CORRECT, LAYOUT_PASS, RESPONSIVE_PASS
- Thông báo 'CHƯA ĐỦ DỮ KIỆN' đúng bản chất; hướng dẫn cung cấp cột và các hàng; KHÔNG dựng bảng mẫu; không lộ JSON/schema/mã lỗi.

### `vrdb9-join-unsupported` — REAL_VISUAL
- N/A: TABLE_STRUCTURE_CLEAR, CURRENT_STATE_CLEAR, FILTER_MECHANISM_CLEAR, PROJECTION_CLEAR, SORT_MECHANISM_CLEAR, AGGREGATE_CLEAR, PROGRESSIVE_REVEAL_PASS, TERMINOLOGY_CORRECT, LAYOUT_PASS, RESPONSIVE_PASS
- Thông báo 'NGOÀI DANH MỤC MÔ PHỎNG'; nói rõ chỉ hỗ trợ MỘT bảng; không generic fallback; không hiện lỗi SQL kỹ thuật.

### `vrdb10-two-queries` — REAL_VISUAL
- N/A: TABLE_STRUCTURE_CLEAR, CURRENT_STATE_CLEAR, FILTER_MECHANISM_CLEAR, PROJECTION_CLEAR, SORT_MECHANISM_CLEAR, AGGREGATE_CLEAR, PROGRESSIVE_REVEAL_PASS, TERMINOLOGY_CORRECT, LAYOUT_PASS, RESPONSIVE_PASS
- Thông báo 'TÁCH THÀNH TỪNG YÊU CẦU' (không phải 'NGOÀI DANH MỤC' hay 'CHƯA ĐỦ DỮ KIỆN'); yêu cầu tách thành hai truy vấn; KHÔNG lộ chữ ký goal / id kỹ thuật; không âm thầm chạy một COUNT.

