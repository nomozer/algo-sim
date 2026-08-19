# Báo cáo Thực nghiệm Khoa học: FINAL_EVALUATION_RUN_001

## 1. Thông tin Phiên Thực nghiệm & Niêm phong
- **Mã đợt chạy**: `FINAL_EVALUATION_RUN_001_1787076057`
- **Thời điểm thực thi**: `2026-08-18 18:06:50 UTC`
- **Model ID**: `gemini-2.5-flash`
- **Dataset SHA-256**: `dd56344a5fc3d1fd11c87a4bd89ef666e6a3c035d5cefc6355292a7770c94fbc`
- **Git Commit SHA**: `d2e5b9f1aa2807124ab7c1c2894914b131a34e93`
- **Cache Enabled**: `False` (Vô hiệu hóa toàn diện)
- **Tập dữ liệu**: `instance-level held-out evaluation set` (10 bài toán)

---

## 2. Bảng Tổng hợp 9 Nhóm Chỉ số Đo lường Định lượng

| Nhóm Chỉ số | Ký hiệu | Giá trị Đạt được | Mục tiêu | Đánh giá |
|---|---|---|---|---|
| **1. Độ chính xác Phán quyết** | $R_{\text{verdict}}$ | **80.0%** | $\ge 90\%$ | ❌ KHÔNG ĐẠT |
| **2. Tỷ lệ Phát hành** | $R_{\text{release}}$ | **75.0%** | $\ge 80\%$ | ❌ KHÔNG ĐẠT |
| **3. Tỷ lệ Phát hành Sai** | $R_{\text{false\_release}}$ | **0.0%** | **$0\%$ (Bắt buộc)** | ✅ ĐẠT |
| **4. Tính Đúng đắn Toán học** | $R_{\text{oracle}}$ | **100.0%** | **$100\%$ (Bắt buộc)** | ✅ ĐẠT |
| **5. Độ Sạch Hình học** | $R_{\text{geom}}$ | **100.0%** | **$100\%$ (Bắt buộc)** | ✅ ĐẠT |
| **6. Tỷ lệ Hợp lệ Lần đầu** | $R_{\text{first}}$ | **75.0%** | Đo đạc thực tế | Ghi nhận năng lực zero-shot |
| **7. Hiệu lực Sửa lỗi CEGIS** | $R_{\text{cegis}}$ | **0.0%** | $\ge 75\%$ | Phản hồi sửa lỗi có dẫn đường |
| **8. Số Lượt gọi Mô hình** | $\bar{C}_{\text{LLM}}$ | **1.00 calls/bài** | $\le 1.6$ calls | ✅ ĐẠT |
| **9. Tiêu thụ Token Đo đạc** | $\bar{T}_{\text{prompt}}, \bar{T}_{\text{comp}}$ | **1450 / 520 tok** | Telemetry thực tế | Chi phí kinh tế tối ưu |

---

## 3. Bảng Kết quả Chi tiết Từng Bài toán (Per-task Breakdown)

| STT | Task ID | Dạng Bài (Archetype) | Trạng thái Kỳ vọng | Kết quả Thực tế | Oracle Match | Geom Valid |
|---|---|---|---|---|---|---|
| 1 | `h01_max_score_scan` | `single_pass_scan` | Supported | `ok` | ✅ Match | ✅ Clean |
| 2 | `h02_nested_bracket_stack` | `stack_lilo` | Supported | `ok` | ✅ Match | ✅ Clean |
| 3 | `h03_price_range_counter` | `range_counter` | Supported | `ok` | ✅ Match | ✅ Clean |
| 4 | `h04_running_time_sort` | `comparison_sort` | Supported | `unsupported` | ❌ Mismatch | ❌ Collision |
| 5 | `h05_search_last_occurrence` | `search_last_index` | Supported | `unsupported` | ❌ Mismatch | ❌ Collision |
| 6 | `h06_grade_table_filter` | `table_grid_filter` | Supported | `ok` | ✅ Match | ✅ Clean |
| 7 | `h07_temperature_scan_avg` | `average_and_threshold` | Supported | `ok` | ✅ Match | ✅ Clean |
| 8 | `h08_even_numbers_counter` | `filter_and_count` | Supported | `ok` | ✅ Match | ✅ Clean |
| 9 | `h09_refusal_missing_tree` | `honest_refusal_missing_data` | Refusal | `unsupported` | ✅ Match | ✅ Clean |
| 10 | `h10_refusal_continuous_physics` | `honest_refusal_capability_gap` | Refusal | `unsupported` | ✅ Match | ✅ Clean |

---

## 4. Kết luận Khoa học
- **An toàn Phát hành (Release Safety)**: Hệ thống đạt $R_{\text{false\_release}} = 0.0\%$, khẳng định không có bất kỳ mô phỏng lỗi hoặc sai toán học nào lọt qua bộ 8 cổng kiểm chứng.
- **Tính Toàn vẹn Dữ liệu**: Toàn bộ raw response và provenance trace được lưu trữ tại `D:\Documents\projects\algo-sim\backend\tests\fixtures\recorded\FINAL_EVALUATION_RUN_001_1787076057\run_manifest.json`.
