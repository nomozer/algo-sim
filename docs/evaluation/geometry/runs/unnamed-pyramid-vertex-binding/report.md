# unnamed-pyramid-vertex-binding — báo cáo

Kết luận: **`ARCHITECTURE_DECISION_REQUIRED`**. Không sửa mã sản phẩm, `CACHE_VERSION` giữ 122, candidate không đổi.
Nhánh `fix/unnamed-pyramid-vertex-binding` từ `a7c56942`; chỉ thêm hồ sơ run và cập nhật issue. Chi tiết: `plan.md`.

## 1. Đã làm

- Tái hiện 21 hàng trên `a7c56942`: 9 phục vụ đúng nhãn/quy ước, 9 từ chối, 3 phục vụ trái nhãn — trùng byte log run trước.
- Nhãn độc lập (`labels.json`) + oracle (`oracle.py`, OK 21/21): liệt kê mọi ánh xạ tên điểm → vị trí (≤ 120 / đề), mỗi
  ánh xạ là hệ tuyến tính theo (b², h²). Kết luận theo đề: 8 xác định (5 phục vụ được, 3 chương trình lỗi), 8 mơ hồ thật,
  4 mâu thuẫn, 1 thiếu dữ kiện. Ba ca được nêu: `square/N5` — đề xác định SA = √17 (vai trò "cạnh bên SA"), lỗi là chương
  trình dựng đỉnh trên một đỉnh đáy ⇒ phải từ chối; `square/R2_N9` — mâu thuẫn nguồn (không cách hiểu nào thoả
  SA = 3, SB = 5, AB = 4) ⇒ từ chối; `square/W5_C` — thiếu dữ kiện (chuỗi bằng nhau không giá trị) ⇒ từ chối.
- Probe khả thi (`diagnostics/template_per_labelling_a7c56942.log`): bộ kiểm chỉ dùng bộ đọc + khuôn T7/T8 hiện có cho
  từng ánh xạ khớp oracle 3/21 và từ chối cả 5 ca xác định — không hơn phương án từ chối toàn bộ.

## 2. Vì sao dừng

Khuôn T7/T8 đọc độ dài theo vai trò của MỘT cách đặt tên đã biết (cạnh đáy kề, cạnh bên, đỉnh–tâm) và giao phần đối
chiếu còn lại cho phép kiểm trên toạ độ chương trình; chúng không loại được cách hiểu sai (R2_S9: cạnh đáy 4 vs `SA = 3`
khi S, A kề nhau), không đọc đường chéo, trọng tâm mặt bên, vai trò "cạnh bên SA" trong câu hỏi, và không sinh độ dài
đoạn hỏi. Đạt oracle cần đưa vào sản phẩm một mô hình tham số của chóp đều (vị trí, bình phương khoảng cách dạng
α·b² + β·h², giải hệ hai ẩn, điểm phụ) và mở rộng bộ đọc (vai trò cạnh, định nghĩa điểm phụ) — mô hình hình học thứ hai
và đại số mới mà brief yêu cầu dừng để quyết.

## 3. Phương án và chi phí (21 hàng)

| | phục vụ | từ chối | 3 ca sai | 9 ca đúng theo quy ước | chi phí |
|---|---|---|---|---|---|
| **(A) từ chối cả 21** — đưa vào vùng U3, lý do "đề không cố định đỉnh" | 0 | 21 | sửa | 4 mơ hồ thật từ chối đúng; **5 xác định bị từ chối oan** (S5, S7, R2_S9, P9, P11) | ~5 dòng sản phẩm + test; bump cache (served → refused) |
| **(B) mô hình tham số trong cổng** — chuyển mô hình của `oracle.py` vào sản phẩm (≤ 120 ánh xạ, khoá ngưỡng), đọc thêm "cạnh bên XY", O = giao hai đường chéo, G = trọng tâm (dùng lại `construction_binding.doc_quan_he_dung`); phục vụ chỉ khi mọi cách hiểu hợp lệ cùng đáp số VÀ chương trình được khuôn kiểm | 5 | 16 | sửa | 5 giữ, 4 từ chối đúng (mơ hồ) | ~150–200 dòng sản phẩm, một mô hình hình học thứ hai cho chóp đều, nhãn + oracle run này làm tiêu chí; bump cache |
| **(C) giữ nguyên** | 12 | 9 | **còn 3 sai** | 9 giữ | 0 |

Đề xuất: **(A)** ngay — đóng lỗ an toàn với thay đổi nhỏ nhất (5 từ chối oan đều là đề viết lại không ký hiệu khối, hiếm
trong đề thật), rồi quay lại G05; (B) để ngỏ như việc có tiêu chí sẵn (`labels.json`, `oracle.py`). Cần người dùng chọn.
