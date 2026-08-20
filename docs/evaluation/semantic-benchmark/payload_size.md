# Kích thước payload frame timeline — ĐO THẬT, 2026-08-20

Spec §4.1 cấm ước lượng cảm tính. Đây là số đo trên 18 fixture chương trình,
sau khi envelope chuyển sang mang **toàn bộ chuỗi khung** (bất biến #31).

Sinh lại: chạy `compile_semantic_program_to_envelope` trên
`backend/tests/semantic_program/fixtures_coverage_18.py`, đo
`len(json.dumps(envelope, ensure_ascii=False).encode("utf-8"))`.

| fixture | khung | bước xem | mức gộp | bytes |
|---|---:|---:|---|---:|
| P01_STACK_BRACKET | 23 | 23 | step | 13.068 |
| P02_FIND_MAX | 19 | 19 | step | 10.880 |
| P03_BINARY_SEARCH | 14 | 14 | step | 11.375 |
| P04_BUBBLE_SORT | 38 | 38 | step | 14.448 |
| P05_SELECTION_SORT | 42 | 42 | step | **23.317** |
| P06_INSERTION_SORT | 32 | 32 | step | 17.704 |
| P07_TWO_SUM_SORTED | 14 | 14 | step | 9.627 |
| P08_PALINDROME | 8 | 8 | step | 5.049 |
| P09_GRAPH_BFS | 31 | 31 | step | 12.927 |
| P10_REVERSE_STRING_STACK | 21 | 21 | step | 11.694 |
| P11_TREE_PREORDER | 16 | 16 | step | 11.585 |
| P12_TREE_INORDER | 17 | 17 | step | 12.835 |
| P13_DECIMAL_TO_BINARY | 17 | 17 | step | 9.085 |
| P14_BITWISE_CHECK | 4 | 4 | step | 2.285 |
| P15_MATRIX_TRAVERSAL | 22 | 22 | step | 9.097 |
| P16_DFA_LEXER | 15 | 15 | step | 8.003 |
| P17_PREFIX_SUM | 10 | 10 | step | 5.188 |
| P18_FREQUENCY_COUNT | 19 | 19 | step | 8.217 |

**Tổng hợp:** lớn nhất **23.317 B** · trung bình **10.910 B** · nhiều khung nhất
**42** · ít nhất **4** · `grouping_level = "step"` ở **18/18**.

## Ba kết luận

1. **Giữ snapshot đầy đủ mỗi khung, KHÔNG dùng delta.** 23KB là không đáng kể;
   đổi lại renderer không cần logic replay — mà logic replay chính là chỗ trục
   hiển thị lệch khỏi trục ngữ nghĩa. Quyết định này nay có số đỡ lưng.

2. **"300 bước không xem nổi" là GIẢ ĐỊNH, không phải quan sát.** Bài thuật toán
   ở mức chương trình THPT cho **4–42 khung**, và chưa bài nào chạm ngân sách
   trình bày 60 — `PresentationPacer` chưa từng phải gộp trên tập này. Nó vẫn
   cần thiết (đề học sinh tự gõ có thể lớn hơn), nhưng **đừng tối ưu mức gộp
   khi chưa có bài nào chạm trần**.

3. **Ngân sách thực thi 300 còn rất rộng** so với 42 khung thực tế. Trần cũ của
   DSL là 20 — tức nó đã cắt câm ngay cả ở bài trung bình.
