# Mẫu nộp case — điền rồi gửi lại

Điền mỗi đề một khối như dưới. Gửi từng đợt cũng được (5–10 đề một lần), không
cần đủ 40 mới gửi.

Phần **bạn** làm: chọn đề · giải · quyết định đề có thuộc phạm vi không.
Phần **tôi** làm: chuyển thành `cases.json` đúng hình dạng · chạy validator ·
báo lại chỗ nào thiếu. Tôi không chọn đề và không tính đáp án hộ.

```
--- CASE ---
Nguồn      : tin-hoc-11-cs.pdf, trang 62, bài 3
Đề         : Cho dãy số 12 45 67 23 89 34. Tìm giá trị lớn nhất của dãy.
Đề hỏi     : extremum
Đáp án     : 89
Đáp án từ  : tự giải tay, đối chiếu đáp số cuối sách trang 180
Trong phạm vi: có
```

## Sáu dòng, giải thích từng dòng

**Nguồn** — đủ để người khác tra lại được. Không nhớ chính xác số bài thì ghi
trang thôi.

**Đề** — chép **nguyên văn**. Nếu đề gốc dùng ký hiệu/bảng khó chép, viết lại
sát nghĩa và ghi thêm `(chép lại)` để sau này biết.

**Đề hỏi** — chọn đúng một trong 9 loại (bảng đầy đủ ở `CUSTODIAN_HANDOFF.md`):

| loại | đề hỏi gì |
|---|---|
| `extremum` | lớn nhất / nhỏ nhất |
| `aggregate_matching` | đếm · tổng · tích · max · min theo điều kiện |
| `ordering` | dãy sau khi sắp xếp |
| `membership` | có mặt hay không |
| `first_match_index` | **vị trí đầu tiên** thoả điều kiện |
| `total_mapping` | ánh xạ đầy đủ khoá → giá trị |
| `derived_sequence` | dãy dẫn xuất (đảo, lọc, khử trùng…) |
| `reachability` | đỉnh nào tới được trên đồ thị |
| `structural_traversal` | thứ tự duyệt cây |

Đề hỏi **nhiều thứ** thì ghi nhiều dòng `Đề hỏi` + `Đáp án`, theo cặp.
Đề **không đòi kết quả cụ thể** (chỉ yêu cầu quan sát diễn biến) thì ghi
`Đề hỏi: (không)` — case vẫn nhận, chỉ được đếm riêng.

**Đáp án** — giá trị đúng. Dãy thì ghi `[3, 7, 9]`.

**Đáp án từ** — bạn lấy đáp án ở đâu. Bắt buộc, và **không được là kết quả của
hệ đang bị đo**. Giải tay / đáp số cuối sách / tự chạy bằng công cụ khác đều
được, chỉ cần ghi rõ.

**Trong phạm vi** — `có` khi đề: dữ liệu **rời rạc** · đầu vào **hữu hạn** ·
có **thủ tục tất định, số bước có biên**. Không thoả thì đừng đưa vào tập.

> Câu hỏi ở dòng này là *"đề có thuộc lớp bài luận văn nhận đo không"*, **không**
> phải *"hệ có làm được không"*. Đề khó mà hệ trượt là **kết quả nghiên cứu**.

## Ba guard chống nhiễm — xác nhận một lần cho cả tập

Trước khi tôi niêm phong, bạn xác nhận:

1. **Không đề nào** thuộc 24 dạng hệ đã có module chuyên biệt (danh sách dưới).
2. **Không đề nào** được lấy từ prompt/tài liệu của chính hệ.
3. Đề lấy từ sách/đề kiểm tra, không phải bịa cho vừa hệ.

24 dạng đã có module — **đề rơi vào đây phải loại**:

```
binary_search · bounded_control_flow · bubble_sort · count_if · find_max
find_min · insertion_sort · linear_search · scan · selection_sort · sum_if
base_conversion · character_encoding · decimal_to_binary · rgb_model
relational_table_query · rule_scene · and_gate · boolean_dag
graph_traversal · packet_routing · protocol_encapsulation · tree_traversal
style_model
```

> Danh sách này khiến việc chọn đề khó hơn thật — phần lớn bài "kinh điển" trong
> SGK đã nằm trong đó. Nhưng đó **chính là điểm của benchmark**: nó phải đo lớp
> bài mà hệ **chưa** có module dựng sẵn. Đề càng nằm ngoài danh sách, con số thu
> được càng có nghĩa.

## Sau khi đủ 40

Tôi dựng `sealed/cases.json`, chạy `validate_sealed_submission.py`, báo lại chỗ
thiếu (nếu có) để **bạn** bổ sung, rồi niêm phong và trả lại đúng hai dòng:
đường dẫn + fingerprint.
