# Câu hỏi nghiên cứu và giao thức v2 (CHƯA chạy — cần quyết định của người dùng)

Thay thế (không xoá) `../text-to-geometry-functions/EXPERIMENT_PROTOCOL.md`. Nguồn giả thuyết: `LITERATURE_GAP_MATRIX_V2.md`
§4–§5 (37 công trình). Luật đo của kho: ngân sách + luật dừng đăng ký trước; khai `MEASUREMENT_CLASS` ·
`HELD_OUT_CLAIM` · `EVALUATOR_INDEPENDENCE`; `ALLOW_LIVE_AI=1` chỉ trong tiến trình đo; ghi `surface_fingerprint()`.
**Không** dùng số 0/10 của pilot `LLM_ONLY` cũ (`feat/real-model-pilot-tooling`) làm nhóm đối chứng hay bằng chứng ưu thế.

## 1. Câu hỏi

| | câu hỏi | bác bỏ khi | lượt gọi |
|---|---|---|---|
| Q1 / A1 chọn hàm | cùng model, cùng đề: chọn hàm theo mệnh đề phục vụ đúng nhiều hơn mô hình viết cả chương trình (`LLM_ONLY`) | không hơn, hoặc lỗi chỉ đổi họ | có (2 nhánh) |
| Q2 / A2 neo nguồn | quote + kiểm tất định giảm tham số bịa mà không tăng từ chối oan quá ngưỡng | tham số bịa không giảm, hoặc từ chối oan vượt ngưỡng | **0 thêm** (chạy lại engine trên đầu ra Q1 có/không cổng) |
| Q3 / A3 chuẩn hoá ngữ nghĩa | chuẩn hoá có tiền điều kiện cho nhất quán trên bộ diễn đạt mà không chuẩn hoá sai ở cặp tương phản | "không chuẩn hoá" ngang bằng, hoặc "luôn chuẩn hoá" ngang bằng trên cặp tương phản | 0 (fixture) + Q1 |
| Q4 / A4 hợp thành | engine giải phụ thuộc tốt hơn để mô hình tự sắp lời gọi / chỉ dùng primitive cấp thấp | không biến thể nào kém đi | có |
| Q5 / A5 biểu diễn gọn | chỉ chạy nếu Q1 cho thấy token hoặc giới hạn lược đồ Gemini là nút thắt | token không giảm qua ngưỡng, hoặc lỗi parse tăng | có |
| Q6 token | token ra + thinking mỗi đề của đường chọn hàm vs `LLM_ONLY` ở độ chính xác ≥ | không thấp hơn / thấp hơn kèm kém chính xác | 0 thêm (usage của Q1) |

Văn liệu đã đọc **không** cho số đo nào về token theo loại IR hay về chuẩn hoá có tiền điều kiện ⇒ Q3, Q6 là chỗ đo
được mà tập đọc để trống (không phải bằng chứng tính mới).

## 2. Pilot nhỏ đề xuất (P-FC1) — **chưa chạy, chưa duyệt**

- `MEASUREMENT_CLASS = DEVELOPMENT_FUNCTION_ROUTE_PILOT` · `HELD_OUT_CLAIM = NO` (corpus đã nhìn) ·
  `EVALUATOR_INDEPENDENCE = PARTIAL` · model `gemini-2.5-flash` (giá đã tra 2026-10-10: 0,30 / 2,50 USD mỗi triệu token
  vào / ra gồm thinking, Standard) · bề mặt `09ec4a9d…`.
- Corpus (đóng băng băm trước khi chạy): 16 đề G05 của pilot cũ (`PILOT_CASES.json`, chỉ VĂN BẢN + nhãn) + 10 cách viết
  P01–P10 + 8 đề mở rộng X01–X08 = **34 đề**; nhãn đã có.
- Nhánh: **F-ANY** (34 đề × k = 3 = 102 lượt) bắt buộc; **F-VALIDATED** (16 đề G05 × k = 3 = 48 lượt) tuỳ chọn. Nhánh
  `LLM_ONLY` đối chứng cho Q1 là phê duyệt RIÊNG (chi phí khác: 16–45 nghìn token/đề dương ở pilot cũ).
- Một lượt gọi/đề; không retry nội dung; retry mạng tính vào trần.
- **Trần cứng**: `maxOutputTokens = 8192` mỗi lượt (gồm thinking) ⇒ mỗi lượt ≤ ~9 nghìn vào + 8 192 ra (đầu vào UNKNOWN cho
  tới khi đo `countTokens` — chính lượt đầu tiên phải ghi lại). 150 lượt × (9 000 × 0,30 + 8 192 × 2,50)/10⁶ ≈ **3,5 USD
  xấu nhất**; dự kiến ≈ 0,6–1,2 USD. Đề xuất trần: **160 lượt logic · 240 lần thử HTTP · 2,8 triệu token · 4 USD**.
- Luật dừng: chạm trần; usage thiếu; hai lỗi provider liên tiếp; khoá xuất hiện trong thư mục ra; `RESPONSE_TRUNCATED`
  > 30 % ở 10 lượt đầu (dấu hiệu trần 8192 quá thấp — dừng, không tự nâng).
- Ghi mỗi lượt: payload băm, phản hồi THÔ (đã che khoá), `finishReason`, usage vào/ra/thinking, kết cục + mã, trace.
- Bộ công cụ: tái dùng `run_ai_function_route` + `live_transport`; trước khi chạy phải viết runner có ngân sách theo khuôn
  `run_g05_real_model_pilot.py` (ApiBudget, chặn trước mỗi lượt, quét khoá) và sửa các phát hiện F1–F6 của pilot cũ trên
  đường mới (tách lỗi sản phẩm khỏi lỗi công cụ; lưu phản hồi thô).

## 3. Thứ tự đề xuất

1. Người dùng duyệt ADR + run này. 2. Runner có ngân sách cho đường mới (0 lượt) + chứng nhận bằng provider giả.
3. Duyệt P-FC1 (ngân sách §2). 4. Chạy một lần; phân tích theo Q1–Q6; mở rộng hàm THEO LỖI ĐO ĐƯỢC.
