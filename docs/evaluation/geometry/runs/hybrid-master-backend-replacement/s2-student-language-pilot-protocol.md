# Protocol & Harness Pilot Ngôn ngữ Học sinh `S-2` (Continuation 11 — §5.2)

> **Trạng thái thực thi Live**: **`NOT_EXECUTED` (`0` live provider calls, ngân sách live = `$0`)**.
> **Bộ chấm điểm tất định offline**: `backend/scripts/score_s2_student_language_pilot.py` + `backend/tests/geometry/test_s2_student_language_pilot_harness.py`.
> **Cô lập tuyệt đối**: Pilot phát triển `S-2` **tách biệt hoàn toàn** với đợt đánh giá đối chứng 60 bài live (`live-evaluation-protocol.md`) và với các tập Independent Holdout (Waves 1–3). Không bao giờ dùng ví dụ development làm independent holdout.

---

## 1. Mục tiêu Nghiên cứu của Pilot `S-2`

Đo lường thực nghiệm hành vi của tầng trích xuất LLM (`/4` `TypedFactNextPayloadV2` + `unresolved` + `route-d-clarification/1`) trên văn phong học sinh thực tế (viết tắt, chỉ yêu cầu vẽ/mô phỏng `SL-1`, câu hỏi thiếu toán hạng `SL-2`, thuật ngữ sai, gõ lệch nhẹ, nhiều câu hỏi gộp) mà gold-fact replay offline không thể đo thay được.

---

## 2. Tám Chỉ số Đo lường Bắt buộc (§5.2)

Bộ chấm `backend/scripts/score_s2_student_language_pilot.py` tính toán tất định 8 chỉ số chuẩn hóa:

1. **`extraction_accuracy`**: Tỷ lệ ca trích xuất đúng toàn bộ chữ ký dữ kiện hình học (khối, ràng buộc hình dạng, quan hệ vuông góc/song song, kích thước số) so với nhãn chuẩn.
2. **`goal_completeness`**: Tỷ lệ ca trích xuất đủ 100% mục tiêu mô phỏng/tính toán trong đề (không rơi vế câu hỏi phụ).
3. **`operand_preservation`**: Tỷ lệ ca bảo toàn chính xác tên đỉnh, giá trị số và trích dẫn `quote` nguyên văn trong `raw_source` (`quotes_verbatim_in_raw = True`).
4. **`ambiguity_detection`**: Trên tập ca thực sự mơ hồ/thiếu toán hạng, tỷ lệ hệ thống phát hiện đúng sự mơ hồ (`CLARIFY` hoặc gắn cờ `unresolved`).
5. **`clarification_correctness`**: Trên tập ca hệ thống trả `CLARIFY`, tỷ lệ ca thực sự cần làm rõ **và** trả đúng mã lý do làm rõ hợp lệ.
6. **`false_clarification`**: Trên tập ca rõ nghĩa (đủ dữ kiện hoặc phải từ chối thẳng), tỷ lệ hệ thống hỏi lại `CLARIFY` sai (chống lạm dụng `unresolved`).
7. **`unsupported_classification`**: Trên tập ca ngoài miền hỗ trợ (Oxyz, chóp cụt, phép biến hình, quỹ tích cực trị, ...), tỷ lệ hệ thống phân loại đúng về nhánh từ chối `unsupported` an toàn.
8. **`wrong_served_end_to_end`**: Tỷ lệ ca trả `SERVED` sai trên toàn tập đo được (trả `SERVED` cho đề mơ hồ/mâu thuẫn/ngoài miền, rơi mục tiêu, sai đáp số chính xác, hoặc thiếu chứng chỉ Kernel). **Ngưỡng chấp nhận bắt buộc: `wrong_served_end_to_end == 0`**.

Tuân thủ `AGENTS.md` §4: mọi bản ghi lỗi mạng/timeout hoặc chưa chạy live đều được ghi nhận tường minh là `"NOT_MEASURED"` / `"NOT_RECOVERABLE"` / `"UNKNOWN"`, tuyệt đối không gán bằng `0`.

---

## 3. Phân tầng Tập mẫu Pilot Đề xuất (36 câu phát triển riêng, tách khỏi 60 bài Live Paired)

| Phân tầng (`stratum`) | Số câu đề xuất | Nội dung kiểm định | Kết quả chuẩn kỳ vọng |
| --- | ---: | --- | --- |
| `S2-A: Simulation-only (SL-1)` | 6 | *"Vẽ hình chóp đều..."*, *"Mô phỏng lăng trụ đứng..."* đủ kích thước | `SERVED` (dựng Scene3D đúng, 0 câu hỏi số giả) |
| `S2-B: Compound Multi-Goal` | 6 | Vẽ thiết diện + tính diện tích + tính khoảng cách trong cùng đề | `SERVED` (đủ mọi goal, 0 dropped goal) |
| `S2-C: Incomplete / Elliptical Goal (SL-2)` | 6 | *"Vẽ hình rồi tính."*, *"Tính góc giữa SB và mặt phẳng."* | `CLARIFY` (`route-d-clarification/1`) |
| `S2-D: Contradictory Shape / Terminological Error` | 6 | Hình lập phương có đáy chữ nhật `2×3` (PE-2), cạnh đáy vuông góc mặt đáy | `REFUSED` (`INCONSISTENT_FACTS` / `SOURCE_MISMATCH`) |
| `S2-E: Out-of-Scope School Topics` | 6 | Tọa độ `Oxyz`, hình chóp cụt, cực trị thể tích | `REFUSED_UNSUPPORTED` |
| `S2-F: Colloquial / Noisy Phrasing` | 6 | Văn phong học sinh tự nhiên có dấu nhưng viết gọn (`mp(SBC)`, `đt SC`, `k/c`) | `SERVED` hoặc `CLARIFY` an toàn (`0` wrong-served) |
| **Tổng cộng** | **36** | **1 request / câu (`max 36 requests`, dừng ngay nếu gặp lỗi hệ thống)** | **`wrong_served_end_to_end == 0`** |

---

## 4. Sáu Cổng Cấp quyền Bắt buộc của Owner trước khi Chạy Live (§5.2)

Công cụ chấm điểm khóa cứng `ALLOW_LIVE_AI=0`. Không một request live nào được phép gửi đi khi Owner chưa phê duyệt đủ **6 thông số**:

1. **Quyền thực hiện (`Execution Authorization`)**: Owner GO tường minh cho `S-2 Pilot` (riêng hoặc kèm 60 bài paired evaluation).
2. **Model (`Model ID`)**: Tên model cụ thể (ví dụ `gemini-2.5-flash` hoặc model được chỉ định).
3. **Project / API Key hợp lệ**: Xác nhận nguồn khóa/project được phép dùng.
4. **Giới hạn số lượng request (`Hard Request Cap`)**: Trần cứng `<= 36` requests kèm circuit-breaker dừng ngay sau 3 lỗi liên tiếp.
5. **Ngân sách tối đa (`Hard Budget Cap`)**: Trần chi phí USD cụ thể trước khi chạy.
6. **Phạm vi dữ liệu (`Data Scope`)**: Xác nhận tập 36 câu pilot phát triển (không chạm tập Holdout độc lập).
