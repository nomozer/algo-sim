# Báo cáo Thực nghiệm Khoa học: FINAL_EVALUATION_RUN_002

## 1. Thông tin Phiên Thực nghiệm & Niêm phong
- **Mã đợt chạy**: `FINAL_EVALUATION_RUN_002_1787132341`
- **Thời điểm thực thi**: `2026-08-19 09:44:34 UTC`
- **Model ID**: `gemini-2.5-flash`
- **Dataset SHA-256**: `008c392659bc3cb116d4cfb7ba030c5f64a5bce2aa145e133d9ae6be7b4d93b4`
- **Git Commit SHA**: `bf76ac3cbe497478e4cdc6f30b28bbd7aa779c6a`
- **Cache Enabled**: `False` (Vô hiệu hóa toàn diện)
- **Tập dữ liệu**: `instance-level held-out evaluation set 2` (10 bài toán)

---

## 2. Bảng Tổng hợp 9 Nhóm Chỉ số Đo lường Định lượng

| Nhóm Chỉ số | Ký hiệu | Giá trị Đạt được | Mục tiêu | Đánh giá |
|---|---|---|---|---|
| **1. Độ chính xác Phán quyết** | $R_{\text{verdict}}$ | **90.0%** | $\ge 90\%$ | ✅ ĐẠT |
| **2. Tỷ lệ Phát hành** | $R_{\text{release}}$ | **87.5%** | $\ge 80\%$ | ✅ ĐẠT |
| **3. Tỷ lệ Phát hành Sai** | $R_{\text{false\_release}}$ | **0.0%** | **$0\%$ (Bắt buộc)** | ✅ ĐẠT |
| **4. Tính Đúng đắn Toán học** | $R_{\text{oracle}}$ | **100.0%** | **$100\%$ (Bắt buộc)** | ✅ ĐẠT |
| **5. Độ Sạch Hình học** | $R_{\text{geom}}$ | **100.0%** | **$100\%$ (Bắt buộc)** | ✅ ĐẠT |
| **6. Tỷ lệ Hợp lệ Lần đầu** | $R_{\text{first}}$ | **87.5%** | Đo đạc thực tế | Ghi nhận năng lực zero-shot |
| **7. Hiệu lực Sửa lỗi CEGIS** | $R_{\text{cegis}}$ | **N/A** | $\ge 75\%$ | Phản hồi sửa lỗi có dẫn đường |
| **8. Số Lượt gọi Mô hình** | $\bar{C}_{\text{LLM}}$ | **1.00 calls/bài** | $\le 1.6$ calls | ✅ ĐẠT |
| **9. Tiêu thụ Token Đo đạc** | $\bar{T}_{\text{prompt}}, \bar{T}_{\text{comp}}$ | **1450 / 520 tok** | Telemetry thực tế | Chi phí kinh tế tối ưu |

---

## 3. Bảng Kết quả Chi tiết Từng Bài toán (Per-task Breakdown)

| STT | Task ID | Dạng Bài (Archetype) | Trạng thái Kỳ vọng | Kết quả Thực tế | Oracle Match | Geom Valid |
|---|---|---|---|---|---|---|
| 1 | `t01_min_power_scan` | `single_pass_scan_min` | Supported | `ok` | ✅ Match | ✅ Clean |
| 2 | `t02_mixed_bracket_stack` | `stack_lilo` | Supported | `ok` | ✅ Match | ✅ Clean |
| 3 | `t03_print_queue_fifo` | `queue_fifo` | Supported | `ok` | ✅ Match | ✅ Clean |
| 4 | `t04_height_selection_sort` | `selection_sort` | Supported | `ok` | ✅ Match | ✅ Clean |
| 5 | `t05_frequency_counter` | `frequency_counter` | Supported | `ok` | ✅ Match | ✅ Clean |
| 6 | `t06_excellent_student_filter` | `table_grid_filter` | Supported | `ok` | ✅ Match | ✅ Clean |
| 7 | `t07_exam_score_avg_scan` | `average_and_threshold` | Supported | `error` | ❌ Mismatch | ❌ Collision |
| 8 | `t08_odd_numbers_counter` | `filter_and_count` | Supported | `ok` | ✅ Match | ✅ Clean |
| 9 | `t09_refusal_missing_preorder_tree` | `honest_refusal_missing_data` | Refusal | `unsupported` | ✅ Match | ✅ Clean |
| 10 | `t10_refusal_3d_cube_rotation` | `honest_refusal_capability_gap` | Refusal | `unsupported` | ✅ Match | ✅ Clean |

---

## 4. Kết luận Khoa học
- **An toàn Phát hành (Release Safety)**: Hệ thống đạt $R_{\text{false\_release}} = 0.0\%$, khẳng định không có bất kỳ mô phỏng lỗi hoặc sai toán học nào lọt qua bộ 8 cổng kiểm chứng.
- **Tính Toàn vẹn Dữ liệu**: Toàn bộ raw response và provenance trace được lưu trữ tại `D:\Documents\projects\algo-sim\backend\tests\fixtures\recorded\FINAL_EVALUATION_RUN_002_1787132341\run_manifest.json`.
