# REAL_WORLD_INPUT_BASELINE — Phân Tích Pháp Y Đầu Vào Thực Tế & Ngưỡng Nền Trước Can Thiệp

- **Run ID:** `real-world-geometry-input-verified-simulation`
- **Điểm neo trước chiến dịch (`start_head`):** `ce280140bf89ad72e8724993f75f98edcce01e55` (`unified-geometry-understanding-ocr-autonomous-planning`, candidate trước `dbf61030357c477dc80c90adb3efc1a7342e4f1f`, `CACHE_VERSION = "143"`)
- **Chính sách đo:** `ALLOW_LIVE_AI = 0`, `0` lời gọi Gemini/Vision trả phí, `0` hàng `H-1` / `W2` / `W3` niêm phong được mở.

---

## 1. Bức Tranh Nền Trước Can Thiệp (Tầng Dữ Liệu Thực Tế)

Trước chiến dịch này, `END_TO_END_CAPABILITY_EVALUATION.json` (tại `dbf610303`) và bản ghi chẩn đoán pháp y `real_world_ocr_forensic_dump.json` ghi nhận các nghẽn sau trên ảnh chụp thực tế và văn bản tiếng Việt thực:

### 1.1 Ảnh thực tế `REAL27` (`27` ảnh `anvo25/vmmu`: `6` `development` · `19` `frozen_external_evaluation` · `2` `fresh_external_evaluation`)
- **Tỷ lệ tự chấp nhận trước sửa:** `0 / 27` (`27 / 27` đều dừng ở `LOCAL_OCR_REVIEW_REQUIRED`, `median CER = 0.0944`, `auto_served_wrong = 0`).
- **Tổng số span chặn (`blocking_uncertain_spans`):** **`81`** span chặn trên `27` ảnh, phân bổ nguyên nhân:
  - `SAME_FAMILY_AGREEMENT_ONLY`: `34`
  - `MATH_TOKEN_DISAGREEMENT`: `17`
  - `PRIME_DISAGREEMENT`: `7`
  - `FRACTION_STRUCTURE_LOSS`: `7`
  - `NOT_IN_LEXICON`: `6`
  - `DEGREE_SYMBOL_DISAGREEMENT`: `3`
  - `AMBIGUOUS_DIACRITIC_RESTORATION`: `3`
  - `RADICAL_DISAGREEMENT`: `2`
  - `RELATION_SYMBOL_DISAGREEMENT`: `1`
  - `SINGLE_READER_TOKEN`: `1`
- **Lỗi cấu trúc được phát hiện khi kiểm tra sâu:**
  1. **Cắt nhầm dải trắc nghiệm do nhãn đỉnh ngang trên hình vẽ (`_detect_choice_bands`):** Khi hình vẽ chứa các nhãn đỉnh đơn ký tự nằm ngang hàng như `D`, `A`, `C`, `B`, detector dải đáp án cũ nhận nhầm thành bắt đầu hàng `A./B./C./D.` dù không có dấu câu `[.,):]`, làm mất ngữ cảnh đỉnh hoặc chia nhầm vùng câu hỏi (điển hình `vmmu_r559` có `baseline CER = 0.1929`).
  2. **Nhiễu phân tách văn bản trong/ngoài hộp hình (`figure_bboxes`):** Dòng đề bài viết thường (`Cho`, `Tính`, `Khoảng cách`) hoặc đáp án trắc nghiệm chạm nhẹ mép dưới/mép bên `figure_bboxes` bị hút vào `diagram_tokens` hoặc bị phân loại nhầm; đồng thời chữ dính ký hiệu (`phng(A'BC)`, `ABCD.A'B'C'D'có`, `⊥(ABCD)`, `AA'=`, `12(cm2)`) chưa được tách sạch.
  3. **Dấu `=` so với `-` & homoglyph serif viết hoa:** Trong font in SGK/đề thi, Tesseract đọc `=` thành dấu gạch ngang `—`/`-` dù crop có hai vạch song song rõ (`has_equals_bars`); và serif viết hoa như `A`/`B`/`'` bị Paddle/Tesseract đọc thành `4`/`8`/`"` ở cụm như `(4BC)` hoặc `S.A8CD`.
  4. **Cắt biên bảo thủ làm mất dấu phẩy trên (`'`):** `_strip_edge_bleed` trong `local_ocr_worker.py` có thể quét nhầm nét phẩy nhỏ góc trên phải (`A'`, `C'`) sát mép vùng đọc lại, làm rơi phẩy khi đọc lại crop hẹp.
  5. **Chi phí đọc lại trùng lặp (`reread`):** Cùng tọa độ box trên một ảnh bị gửi đọc lại lặp và giới hạn `_REREAD_CACHE_MAX = 64` nhanh chóng bị đẩy qua nhiều box.

### 1.2 Tập ảnh in ngoài `External16` (`15` ảnh in + `1` ảnh viết tay tách riêng) & Ảnh chưa chạm tới
- **`External15` in:** `1` `LOCAL_OCR_ACCEPT` (`ext_prt_01_hd_q_5259753`, `CER = 0.0`), `12` `LOCAL_OCR_REVIEW_REQUIRED`, `2` `needs_selection` (`ext_prt_03_hd_q_7907931`, `ext_prt_08_hd_q_7509702`), `median CER = 0.0333`, tổng **`72`** blocking spans, `0` wrong-served.
- **`ext_hw_b1_01_hd_a_6043187` (viết tay):** Giữ tách biệt trong báo cáo chẩn đoán (`needs_confirmation`, không gộp vào nhóm in).
- **Watermark / font mờ chưa gắn cờ (`ext_prt_03`):** Trong đề `Bài 32 / Bài 33` bị đè watermark, cả hai nhánh đọc ra `ABCE` (thay vì `ABCD`) và `khói` (thay vì `khối`), chứng minh ranh giới thực tế của mô phỏng chỉ sửa đúng các span được đánh dấu so với sửa tự do toàn văn bản.

### 1.3 Tuyến Văn Bản `REAL27_TEXT` & Cổng Nguồn (`Source Gate`)
- **Nền trước chiến dịch:** `18 / 27` `SERVED` (`0` wrong-served), **`9 / 27` `REFUSED`**:
  - `6` ca dừng ở parser cục bộ (`vmmu_r254`, `vmmu_r256` lỗi chính tả đề gốc `đên`, `vmmu_r277`, `vmmu_r461`, `vmmu_r488`, `vmmu_r491`) -> trả `503 LIVE_AI_DISABLED` khi tắt AI live.
  - `1` ca ngoài miền đại số đóng (`vmmu_r266`: góc `50°`/`70°` -> `EXACT_DOMAIN_EXCEEDED`).
  - `1` ca ngoài phạm vi đa diện lồi (`vmmu_r475`).
  - **`1` ca lệch ranh giới câu hỏi tại Source Gate (`vmmu_r513`):** Đề gốc viết thiếu dấu chấm cuối mệnh đề giả thiết: `"... có AA' = 1, AB = 2 Khoảng cách từ điểm A' đến mặt phẳng ADC'B' bằng."`. Bộ tách câu cũ không nhận diện mốc câu viết hoa khuyết dấu chấm trước `Khoảng cách`, khiến `_cau_chua` / `_bien_cau` trong `registry.py` gộp mệnh đề giả thiết và câu hỏi thành một khoảng đơn và từ chối `NOT_ASKED_IN_SOURCE` (lọt xuống `503 LIVE_AI_DISABLED`) thay vì `REFUSED MISSING_DIMENSION` kèm kiểm toán thiếu kích thước (`UNPROVED_DUE_TO_CAPABILITY_GAP`).
- **Khoảng trống hợp đồng xác nhận & cache:** Chưa có trường băm `raw_ocr_text_sha256` / `prepared_region_sha256` / `edited_from_raw_ocr` / `counted_as_unmodified_auto_ocr` gắn tường minh ở tầng chuẩn bị (`unified_input.py`) và tầng phân tích (`/api/analyze` trong `main.py`), nên cần khóa rạch ròi chữ xác nhận chưa sửa so với chữ học sinh đã chỉnh tay trước khi nâng `CACHE_VERSION` lên `144`.
