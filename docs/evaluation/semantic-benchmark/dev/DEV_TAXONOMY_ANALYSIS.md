# Phân tích DEV → chọn tập checker đại diện, rồi ĐÓNG BĂNG

Ngày: 2026-08-20 · Làm trên **DEV**, trước khi SEALED được mở (spec §7.3).

Câu hỏi cho mỗi khoảng trống — không phải *"làm sao cho ca này xanh"* mà:

> **Case này làm lộ một quan hệ ngữ nghĩa TÁI SỬ DỤNG mà nhiều bài dùng chung
> không? Và quan hệ đó có checker server-owned rõ ràng không?**

Không có → `verification_gap` là **kết quả hợp lệ**, không phải lỗi cần vá.

## Số liệu thô

| | |
|---|---|
| Tổng case | 20 |
| STRONG với từ vựng hạt giống | **12** |
| WEAK | **8** |
| Nghĩa vụ ngoài từ vựng | 6 loại |

Phân bố nghĩa vụ: `count_matching` 3 · `membership` 3 · `ordering` 3 ·
`extremum` 2 · `reachability` 2 · `derived_sequence` 2 · `total_mapping` 1 ·
`structural_traversal` 1 · `aggregate_matching` 1 · `first_match_index` 1 ·
`predicate_verdict` 1 · `distinct_preserving_order` 1 · `connected_components` 1.

## Phán quyết từng khoảng trống

| Nghĩa vụ | Số ca | Phán quyết | Lý do |
|---|---:|---|---|
| `derived_sequence` | 2 (+1 gộp) | **THÊM** | Tập phép biến đổi ĐÓNG (`reverse`, `distinct`, `filter`, `map`, `identity`) kiểm được tất định **mà không cài lại thuật toán**. dev_06 (đảo chuỗi) và dev_07 (FIFO) là hai bài khác hẳn nhau về đề nhưng cùng một quan hệ — đúng dấu hiệu tái sử dụng |
| `aggregate_matching` | 1 | **THÊM** | Tổng/tích/trung bình có điều kiện là dạng phổ biến bậc nhất trong chương trình. Nó **bao trùm** `count_matching` (đếm = gộp với phép `count`), nên thêm nó làm taxonomy **gọn đi**, không phình ra |
| `first_match_index` | 1 | **THÊM** | Khác `membership` ở chỗ đòi **vị trí đầu tiên** — thứ tự duyệt là một phần của câu trả lời. Đây đúng điểm nghẽn nhận thức #3 của đề tài, và mẫu *"tìm X đầu tiên thoả…"* lặp lại khắp chương trình |
| `distinct_preserving_order` | 1 | **GỘP**, không thêm | Là một phép biến đổi của `derived_sequence`. Thêm nguyên thuỷ thứ ba cho nó là đẻ checker theo ca |
| `connected_components` | 1 | **TỔ HỢP** — nhưng GIỮ WEAK | Dựng được từ `reachability` lặp, và xét tổ hợp trước khi xét mở rộng là đúng. NHƯNG tổ hợp chỉ đáng gọi STRONG khi C₂ kiểm được **phân hoạch đầy đủ**: các thành phần rời nhau · phủ hết miền đỉnh · mỗi thành phần đúng bằng tập reachability của nó. Chưa có semantics đó ⇒ **giữ WEAK**, không gọi STRONG sớm cho bảng đẹp. Không thêm obligation mới chỉ vì điểm này |
| `predicate_verdict` | 1 | **KHÔNG thêm** → `verification_gap` | Kiểm nó đòi **cài lại chính thuật toán đang kiểm** — mất tính độc lập, và oracle mất nghĩa. Đây là ranh giới khoa học ở §5.4, khai tường minh chứ không vá |

Một mở rộng **phạm vi** (không phải checker mới): `count_matching` hiện khai cho
`array/set/map`; dev_12 (matrix) và dev_17 (cây) cho thấy nó nên áp cho **mọi
cấu trúc duyệt được**. Đây là nới miền của một checker đã có, không phải thêm
nguyên thuỷ.

## Taxonomy sau khi chốt — ĐÓNG BĂNG TRƯỚC SEALED

```
extremum(container, cmp)                  — array, matrix
aggregate_matching(container, pred, op)   — array, matrix, set, map   [bao gồm count]
ordering(container, cmp)                  — array
membership(container, item)               — array, set, map
first_match_index(container, pred)        — array
total_mapping(map, domain)                — map
derived_sequence(dest, transform, src)    — array, stack, queue        [reverse|distinct|filter|map|identity]
reachability(graph, src, set)             — graph
structural_traversal(tree, order)         — tree_node
```

**9 nghĩa vụ.** Hạt giống có 7; thêm 3, gộp 1 (`count_matching` vào
`aggregate_matching`).

## Hiệu ứng dự kiến trên DEV

6/8 ca WEAK được nâng. Còn hai ca ở `verification_gap`:

- **dev_05** (`predicate_verdict`) — kiểm đòi cài lại chính thuật toán.
- **dev_20** (`connected_components`) — tổ hợp được, nhưng chưa có kiểm phân hoạch
  đầy đủ nên **chưa đủ tư cách STRONG**.

> **18/20 STRONG, 2/20 verification_gap — TRÊN DEV.**

## Cảnh báo phải đọc kèm con số trên

Con số 18/20 **KHÔNG dự đoán được SEALED**, vì ba lý do:

1. **DEV do chính agent viết hệ soạn ra.** Dù nghĩa vụ được suy từ đề chứ không
   từ chương trình, việc chọn *đề nào* vẫn nằm trong tay người biết IR.
2. **Taxonomy được chọn SAU khi nhìn DEV.** Đó là hợp lệ theo freeze protocol —
   nhưng nó có nghĩa DEV **không còn là mẫu độc lập** để đo tỉ lệ.
3. Đây là lý do SEALED tồn tại. Con số dùng cho luận văn là con số của **SEALED**,
   mở đúng một lần ở Task 12.

Ghi 18/20 vào báo cáo như tỉ lệ năng lực của hệ là **overclaim**. Nó chỉ nói:
*với 9 checker này, phần lớn dạng bài trong chương trình mà chúng tôi liệt kê
được đều có đường kiểm chứng độc lập.*

## Ba con trỏ `for_each` — chưa mở IR

Bất biến #34 đã bắt 3 fixture + 1 output live buộc con trỏ vào biến ký tự của
`for_each`. Câu hỏi mở IR (thêm chỉ số cho `for_each`) **để lại**, vì:

- DEV này **không có ca nào** đòi con trỏ chạy dọc chuỗi mới diễn đạt được bài;
  `for_range` đã đủ cho mọi ca cần chỉ số.
- Đây là nhu cầu **trình bày**, không phải nhu cầu **diễn đạt** — chưa chạm
  ngưỡng "abstraction tái sử dụng" của ranh giới 2.

Giữ nguyên: con trỏ như vậy **không được admit**. Ghi lại làm bằng chứng, xét
lại nếu SEALED cho thấy đây là nhu cầu hệ thống.
