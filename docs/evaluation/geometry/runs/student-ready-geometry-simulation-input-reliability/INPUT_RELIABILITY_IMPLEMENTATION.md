# INPUT RELIABILITY IMPLEMENTATION — `student-ready-geometry-simulation-input-reliability` (`CACHE_VERSION = 145`)

- **Run ID:** `student-ready-geometry-simulation-input-reliability`
- **Measurement Class:** `OFFLINE_DETERMINISTIC_REPLAY` (`live_ai_calls = 0`, `sealed_h1_rows_opened = 0`, `locked_w2_w3_rows_read = 0`)
- **Product Commit:** `ac0ea63dd462c92a8736b607764d1df552d29329`
- **Clean Candidate Freeze Commit:** `4c463d154885e99ad9bf07e3898d11c619eb63c4`
- **Measured System Hash:** `8a88dbfe9ddc35e38639c7c81e8c7741b1ea1dd1cd848bc9e7dc6bf16885b0c6` (`120` files)
- **Primary Evaluation Artifact:** `STUDENT_READY_EVALUATION.json` (`524,128` bytes, SHA-256 `483cde8c00a2aa692b568e84a0f867b0b0481e2665cd2dbd415fbba3c3827e8d`)

---

## 1. Mục Tiêu & Ranh Giới Input Reliability

Chiến dịch nâng cấp đường ống tiếp nhận ảnh đề hình học tiếng Việt từ mức thực thi đơn thuần lên mức sẵn sàng cho học sinh tự kiểm tra từng vùng chưa chắc chắn (`span confirmation`) trước khi dựng mô phỏng 3D chính xác:

1. Tách cache đọc toàn trang và cache đọc lại crop vùng span trong worker OCR cục bộ (`local-ocr-worker/5`).
2. Bảo toàn phân số xếp chồng (`a/b`) và loại trừ ký hiệu tiểu mục đầu dòng (`b.`, `c.`, ...) khỏi lỗi nhãn đỉnh viết thường trong `layout-aware-ocr-reconcile/4`.
3. Gắn bằng chứng ảnh cắt nguồn từng span (`source_crop_png_base64`) và hợp đồng xuất xứ (`ocr-confirmation-provenance/1`, `verified-input-provenance/1`) để phân biệt rạch ròi giữa `AUTO_OCR`, `SPAN_ONLY_CONFIRMATION` và `WHOLE_DRAFT_FALLBACK`.
4. Giữ nguyên tắc fail-closed: **không tự động chấp nhận sai (0 false auto-accepts)** và **không tự sửa thầm lặng ngoài span được xác nhận**.

---

## 2. Thay Đổi Kỹ Thuật Đã Triển Khai

### 2.1 Worker OCR Cục Bộ (`local-ocr-worker/5` — `backend/app/ingestion/local_ocr_worker.py`)
- Tách hoàn toàn hai tầng cache giới hạn kích thước (`cache_split_ok = true`):
  - `_RAW_PAGE_CACHE_MAX = 32`: cache kết quả layout & văn bản toàn trang gốc.
  - `_REREAD_CROP_CACHE_MAX = 512`: cache các lần đọc lại crop cục bộ cho từng vùng chữ/toán chưa chắc chắn, ngăn hiện tượng crop reread đẩy kết quả toàn trang khỏi LRU hoặc ngược lại.
- Phát hiện dải nhiều bài trên một trang ảnh (`needs_selection`, ví dụ `ext_prt_03_hd_q_7907931`, `ext_prt_08_hd_q_7509702`) và cô lập vùng hình vẽ.

### 2.2 Đối Soát Layout & Sửa Lỗi Sau Freeze (`layout-aware-ocr-reconcile/4` — `backend/app/ingestion/ocr_reconcile.py`)
- **Ghép phân số xếp chồng cạnh vùng đáp án (`vmmu_r538`):** Trước khi vá, điều kiện `in_choice(b)` với `pad = 0.70 * med_h` phía trên phương án `A.90°.` vô tình chặn ghép tử/mẫu của thân đề (`2a` / `3` -> `2a`), gây hiểu nhầm dữ kiện độ dài cạnh. Sau bản vá tại commit `ac0ea63dd`, chỉ bỏ ghép cặp phân số xếp chồng khi mẫu khớp `_OPTION_PREFIX_RE` hoặc cả `a` lẫn `b` đều nằm trong `in_choice`. Khôi phục `vmmu_r538 -> SERVED {'q1': 'cos²=3/4'}` (`30°`).
- **Ký hiệu tiểu mục đầu dòng (`ext_prt_01`):** Loại trừ marker tiểu mục đầu dòng dạng `[b-e][.):]` khỏi `LOWERCASE_VERTEX_LABEL`, khôi phục `ext_prt_01_hd_q_5259753 -> ready (LOCAL_OCR_ACCEPT)` với kết quả chính xác `{'q1': 'a³√3/3', 'q2': 'a√21/21'}`.
- Bảo toàn danh sách kiểm tra glyph topology (`12/12`), rendered positive (`4/4`) và adversarial negative (`3/3` blocked, `0` false auto-accept).

### 2.3 Định Tuyến Ảnh & Hợp Đồng Xác Minh (`local-ocr-route/3` — `backend/app/ingestion/local_ocr_route.py`, `unified_input.py`)
- Phát hành hợp đồng `ocr-confirmation-provenance/1` cho giao diện xác nhận: đính kèm `source_crop_png_base64`, ứng viên thay thế và dấu vết vùng chuẩn hóa.
- Ghi nhận `verified-input-provenance/1` khi học sinh xác nhận (`origin = "local_ocr_student_confirmed"`, `counted_as_unmodified_auto_ocr = false`) so với tự động chấp nhận (`origin = "local_ocr_auto_verified"`, `counted_as_unmodified_auto_ocr = true`).
- Ràng buộc cache identity toàn tuyến về `CACHE_VERSION = "145"` (`ROUTE_D_CACHE_POLICY = "145:route-d"`).

---

## 3. Kết Quả Định Lượng Before / After (`CACHE_VERSION 144` → `145`)

> **Quy tắc tách mẫu:** `SPAN_ONLY_SCENE3D_SUCCESS_RATE` chỉ đếm các ca đi hết tuyến từ ảnh chỉ bằng xác nhận span được hệ thống gắn cờ (không sửa tự do toàn bản nháp). `whole_draft_fallback_served` và ảnh viết tay (`external16_handwritten_diagnostic`) được báo cáo tách riêng hoàn toàn.

| Tập kiểm chứng ảnh | Cỡ mẫu | Auto-accept đúng / sai | Needs Confirmation / Selection | CER median (gốc -> sau span) | Facts quan trọng (nháp -> sau span) | Span-only SERVED (Wrong) | Whole-draft fallback (tách riêng) | Effort median (actions / chars typed) | Cold prepare p50 / p95 (ms) | Warm prepare p50 / p95 (ms) |
| :--- | ---: | :--- | :--- | :--- | :--- | :--- | ---: | :--- | :--- | :--- |
| `real27_images` (tổng) | 27 | `0/27` (`0` sai) | `27` conf / `0` sel | `0.0944 -> 0.0553` (v144 `0.0533`) | `176/188 -> 187/188` (`0.9947`) | **`18/27`** (`0` wrong) *(v144: `13/27`)* | **`+3`** (`r254`, `r284`, `r488`) | `2` / `0` (`42/6098` chars) | `2605.14 / 4407.88` | `242.23 / 404.57` |
| ├─ `development` | 6 | `0/6` (`0` sai) | `6` conf | `0.0973 -> 0.0604` | `36/40 -> 40/40` (`1.0000`) | `2/6` (`r270`, `r476`) | `+2` (`r284`, `r488`) | `2.0` / `0.0` (`5/1553`) | `3810.92 / 6177.19` | `315.36 / 549.09` |
| ├─ `frozen_external_evaluation` | 19 | `0/19` (`0` sai) | `19` conf | `0.0944 -> 0.0606` | `128/136 -> 135/136` (`0.9926`) | `14/19` (`0` wrong) | `+1` (`r254`: `AA'=2√13a`) | `2` / `0` (`37/4208`) | `2605.14 / 3516.16` | `233.23 / 296.62` |
| └─ `fresh_external_evaluation` | 2 | `0/2` (`0` sai) | `2` conf | `0.1167 -> 0.0443` | `12/12 -> 12/12` (`1.0000`) | `2/2` (`r559`, `r695`) | `0` | `1.0` / `0.0` (`0/337`) | `2055.51 / 2382.11` | `233.69 / 251.94` |
| `external16_printed_images` | 15 | `1/15` (`0` sai: `ext_prt_01`) | `12` conf / `2` sel | `0.0333 -> 0.0333` (v144 `0.0319`) | n/a | `8/12` conf + `2/6` bands (`0` wrong) | `0` | `4.0` / `0.0` | `2495.27 / 3424.56` | `188.44 / 315.88` |
| `new_external_12` (untouched) | 12 | `0/12` (`0` sai) | `12` conf | `0.0706` (draft median) | n/a | `2/12` SERVED_CORRECT (`0` wrong) | n/a | n/a | `2560.74 / 2751.63` | n/a |
| `new_image_corpus_8` (`development`) | 2 | `0/2` (`0` sai) | `2` conf | `0.0829` (draft median) | n/a | `0/2` (`0` wrong) | n/a | n/a | `2636.92 / 2714.87` | n/a |
| `new_image_corpus_8` (`frozen_ext`) | 6 | `0/6` (`0` sai) | `6` conf | `0.0451` (draft median) | n/a | `1/6` SERVED_CORRECT (`r446`: `√3/3`) | n/a | n/a | `3090.64 / 3334.03` | n/a |
| `external16_handwritten_diagnostic` | 1 | `0/1` (`0` sai) | `1` conf | `1.9942 -> 2.1404` *(note dưới)* | n/a | `0/1` (`0` wrong) | `1` (`ext_hw_b1_01`) | `24` / `16` | `4431.50 / 4431.50` | `316.41 / 316.41` |

*Ghi chú minh bạch đo lường:*
- Trên `real27_images`, `blocking_spans_before = 81` và `blocking_spans_after = 0` trong báo cáo phản ánh đồng thời `diagnostic_4_1.blocking_spans == 0` sau kiểm soát chặn cứng và việc DTO giao diện `uncertain_tokens` lược bỏ trường nội bộ `blocking`.
- Điểm fact quan trọng duy nhất chưa khôi phục trong 188 critical facts của `real27` (`187/188 = 0.9947`) là `AA'=2√13a` trên `vmmu_r254`, khiến `vmmu_r254` không qua được chỉ bằng span-only mà cần fallback sửa bản nháp (nơi nó phục vụ đúng `9a³√13/2`). Hai ca fallback còn lại là `vmmu_r284 -> a√21/7` và `vmmu_r488 -> a³/3`.
- Với `external16_printed_images`, ở lần chọn vùng trên `ext_prt_03_hd_q_7907931`, cả hai ứng viên tách đúng (`text-p1-1` `Bài 32 -> a√2/2`, `text-p1-2` `Bài 33 -> a³/4`) đều `SERVED_CORRECT` với `0` lỗi continuity; trên `ext_prt_08_hd_q_7509702`, cả `4` dải `page~band-1..4` đều từ chối an toàn (`REFUSED`, `0` wrong, `0` continuity errors).
- Với `external16_handwritten_diagnostic`, tóm tắt benchmark ghi nhận `cer_before_median: 1.9942`, `cer_after_median: 2.1404` (trong bản ghi chi tiết dòng `cer_after = 1.7895` sau khi gõ 16 ký tự across 24 actions); ảnh viết tay được báo cáo riêng và không bao giờ gộp vào cam kết OCR chữ in.
- **Vision Fallback Offline Mock:** `VISION_THEN_LOCAL_DETERMINISTIC` đạt `passed: true` (`answers: {"q1": "a³√3/3"}`, `live_ai_calls: 0`, `continuity_errors: 0`). Đo live Gemini Vision: `NOT_MEASURED`.

---

## 4. Tập Mù Đóng Băng Trước Điều Chỉnh (`frozen_unseen_vmmu20` — Tách Biệt Tuyệt Đối)

- **Trạng thái nhãn:** `ground_truth_status = "GROUND_TRUTH_UNVERIFIED"` · `independent_ground_truth_validation = "NOT_MEASURED"` · `status = "FROZEN_BEFORE_ANY_TUNING_OR_FINAL_EVAL"`.
- **Manifest:** `frozen_unseen_vmmu20_manifest.json` (bất biến, `19` ảnh MIT `anvo25/vmmu`: `13` `polyhedron_3d`, `6` `curved_or_mixed_solid`).
- **Quy tắc sử dụng:** Tuyệt đối **không** gộp vào mẫu số độ chính xác hay tỷ lệ thành công giải đúng vì không có answer key kiểm chứng độc lập. Chỉ dùng để quan sát khả năng tiếp nhận OCR, độ trễ và tính liên tục Scene3D:
  - `prepare_status`: `18` `needs_confirmation` (`LOCAL_OCR_REVIEW_REQUIRED`), `1` `ready` (`LOCAL_OCR_ACCEPT`: `unseen_vmmu_13`).
  - Tuyến nháp hạ nguồn (khi `ALLOW_LIVE_AI=0`): `2 SERVED` (`unseen_vmmu_08`, `unseen_vmmu_09`), `17 REFUSED` (gồm `unseen_vmmu_13` bị `REFUSED` với `LIVE_AI_DISABLED`), `scene3d_continuity_errors = 0`.
  - Độ trễ: cold prepare `p50 = 2636.49 ms, p95 = 3430.40 ms, mean = 2722.02 ms`; warm prepare `p50 = 226.36 ms, p95 = 441.96 ms, mean = 249.24 ms`.
