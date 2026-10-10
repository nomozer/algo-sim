# Độ bền trước nhiều cách viết — đánh giá (lời gọi viết tay, 0 lượt gọi model)

> **Giới hạn bắt buộc đọc trước:** mọi ca dưới đây có lời gọi hàm **viết tay** đóng vai đầu ra AI. Bộ này kiểm đường
> lời gọi → cổng nguồn → engine nhận, chuẩn hoá hay từ chối ĐÚNG từng dạng câu. Nó **không** chứng minh Gemini hiểu
> được các câu ấy — đó là câu hỏi Q1/Q2 của `EXPERIMENT_PROTOCOL_V2.md`, cần đo thật.

Oracle khoá trước khi sửa mã: `backend/tests/geometry/fixtures/paraphrase_cases.json` (commit `f47c56bb`).

## 1. Giới hạn THẬT của cổng v1 (đo trên mã trước khi sửa — `diagnostics/baseline_before_change.log`)

5/31 ca đăng ký trước khớp. Hai loại hỏng:

- **Từ chối oan** (cổng quá hẹp): "SA là đường cao", "hình chiếu vuông góc của S lên (ABC) là A", "SA ⊥ AB và AC" không có
  hàm (`SCHEMA_INVALID`); dữ kiện trải nhiều câu không chép được (một quote/lời gọi); "SA vuông đáy" thiếu từ "vuông góc";
  `SA⊥(ABC)` không khớp khi AI gõ khoảng trắng khác; "AB = 3, BC = 4" bị coi là mơ hồ.
- **Phục vụ khi không được phục vụ — 4 lỗ an toàn**: AI đọc "SA vuông góc với AB" thành SA ⊥ (ABC) (N01); mệnh đề "Nếu
  … thì" (N05); điều phải chứng minh (N06); phủ định nằm NGAY TRƯỚC đoạn AI trích (N07). Cả bốn: cổng v1 chỉ nhìn chữ
  TRONG quote.

## 2. Thiết kế: năm tầng tách bạch thay vì danh sách đồng nghĩa

| tầng | trách nhiệm | ở đâu |
|---|---|---|
| 1. nhận diện mệnh đề + ngữ cảnh | vị trí quote (bỏ qua khoảng trắng), vai trò câu (tiền đề / mục tiêu chứng minh / điều kiện), phạm vi phủ định trong mệnh đề | `registry.kiem_nguon` |
| 2. chuẩn hoá ý nghĩa hình học | mỗi CẤU TRÚC câu là một hàm (`altitude`, `orthogonal_projection`, `perpendicular_lines`, `equal_length`); engine quy về quan hệ chuẩn CHỈ khi tiền điều kiện hình học đúng | `engine._rang_buoc_vuong`, `_hai_duong_cat_nhau`, `do_dai` |
| 3. liên kết giá trị/đối tượng với nguồn | mặt phẳng được nhắc, đoạn/điểm đóng vai riêng được nhắc ngoài nhóm mặt phẳng, số căn theo nhãn đoạn | `registry` |
| 4. xác minh tiền điều kiện | đỉnh của khối, chân trên đáy, ảnh ≠ điểm, hai đường không song song, đồng bậc độ dài | `engine` |
| 5. sinh + thực thi | IR → interpreter → kiểm mọi dữ kiện → Scene3D | `engine`, `function_route` |

Ba câu ví dụ của brief chỉ được chuẩn hoá thành SA ⊥ (ABC) khi ngữ cảnh chứng minh: "SA là đường cao của hình chóp
S.ABC" ⇔ chỉ vì A thuộc đáy của CHÍNH khối ấy (đỉnh khác ⇒ `PRECONDITION_FAILED`); "hình chiếu vuông góc của S lên (ABC)
là A" ⇔ chỉ khi A ∈ (ABC) và S ∉ (ABC); "SA ⊥ AB và AC" ⇔ định lý, chỉ khi AB, AC không song song trong đáy (một đường ⇒
chưa xác định, N02).

## 3. Kết quả sau sửa — 23/23 ca diễn đạt (cùng 8/8 mở rộng)

| nhóm | ca | kết cục |
|---|---|---|
| 10 cách viết của SA ⊥ (ABC) (chính quy, ký hiệu ⊥, "mặt phẳng đáy", đường cao, hình chiếu, hai đường vuông góc, nhiều câu, câu hỏi đứng trước + "biết", viết tắt học sinh "SA vuông đáy … tính V", không khoảng trắng) | P01–P10 | SERVED ×10, cùng đáp số 4√3 và **cùng hình** (độ dài² mọi cặp S, A, B, C trùng nhau) |
| cặp gần nghĩa | N01 SA ⊥ AB đọc thành ⊥ mặt · N02 một đường vuông góc · N03 đường cao của tam giác đáy · N04 ảnh hình chiếu gán nhầm | `PLANE_NOT_IN_QUOTE` · `UNDERDETERMINED_POINT` · `PREDICATE_NOT_IN_QUOTE` · `ROLE_NOT_IN_QUOTE` |
| ngữ cảnh | N05 "Nếu … thì" · N06 "Chứng minh …" · N07 "không vuông góc" ngoài quote | `CONDITIONAL_CLAUSE` · `GOAL_CLAUSE_NOT_PREMISE` · `NEGATED_CLAUSE` |
| mâu thuẫn / thiếu | N08 hình chiếu tại A nhưng SB = 4 · N09 đường cao không có độ dài | `INCONSISTENT_FACTS` · `MISSING_DIMENSION` |
| nhiều số một câu | N10 "AB = 3, BC = 4" căn theo nhãn · N11 AI gán BC = 3 · N13 quote hai số không nhãn (khoá như G7 cũ) | SERVED 8 · `UNGROUNDED_VALUE` · `AMBIGUOUS_VALUE_QUOTE` |
| đại lượng tương đương | N12 "SA = AB" | SERVED 16√3/3 |

Kiểm đột biến (`diagnostics/mutation_check.log`): bỏ vai trò mệnh đề, thu phủ định về trong quote, bỏ tham chiếu mặt
phẳng, bỏ vai trò điểm, bỏ tiền điều kiện chuẩn hoá, bỏ căn theo nhãn — mỗi cái làm test đỏ.

## 4. Giới hạn còn lại

- Từ khoá định nghĩa vẫn là điều kiện CẦN theo từ vựng; câu dùng cấu trúc chưa có hàm ⇒ từ chối (an toàn, không phục vụ
  sai), nhưng là từ chối oan nếu đề thật dùng cách nói đó. Danh sách cấu trúc mở rộng THEO LỖI ĐO ĐƯỢC, không đoán trước.
- Vai trò câu dựa vào vài dấu hiệu đầu mệnh đề ("chứng minh", "nếu … thì", "biết"); câu điều kiện ẩn ("giả sử", "khi")
  chưa phân biệt; "Nếu … thì" luôn bị từ chối — giới hạn cố ý (fail-closed), có thể là từ chối oan với đề giả định.
- Phạm vi phủ định cắt ở dấu câu; phủ định đôi, phủ định xa hơn một mệnh đề chưa xử lý.
- Căn giá trị dùng nhãn đoạn; số không nhãn ("cạnh đáy bằng 2, chiều cao bằng 3" trong MỘT quote) vẫn phải trích hẹp.
- Toàn bộ là lời gọi viết tay: AI thật có thể chọn sai hàm, chép quote lệch, hoặc tách mệnh đề khác — chỉ đo thật trả lời được.
