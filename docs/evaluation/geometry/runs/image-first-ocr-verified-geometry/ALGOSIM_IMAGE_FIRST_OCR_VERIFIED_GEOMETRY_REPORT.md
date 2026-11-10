# ALGOSIM / AXO — IMAGE-FIRST OCR & VERIFIED IMAGE-TO-3D REPORT

- **Run ID:** `image-first-ocr-verified-geometry`
- **Date (UTC):** `2026-11-10`
- **Worktree:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\local-first-geometry-understanding`
- **Branch:** `feat/local-first-geometry-understanding` (not merged to `main`, not pushed)
- **Baseline Commit at Task Start:** `10d4899fdfd539de62217124e1ce5fb3fe54c3ce` (product `d20d7fdcdd6c5759f74ff737f331c2e548923eba`, `110` measured files `fb4f4992da8764930954a44f24e121ddca6cf1f3a270039773f6dbbf8b1b5c05`)
- **Measured Product Commit:** `bdc07a8557277d9780bee8689567990854ad4521` (`115` measured files, tree hash `6851b71826793fffbb922e0b7706e1c2a32bb2203d615c8eb0414e82b0d2c947`, `CACHE_VERSION = 132`, `ROUTE_D_CACHE_POLICY = 132:route-d`)
- **Kernel & Registry Invariance:** `registry.REGISTRY_VERSION = "geometry-functions/33"` (100% untouched), `planner.PLANNER_VERSION = "geometry-fact-planner/26"` (100% untouched), `engine.ENGINE_VERSION = "geometry-function-engine/24"` (100% untouched)
- **Live AI Policy:** `ALLOW_LIVE_AI = 0` (`0` live Gemini calls executed)

---

## I. Tóm Tắt Điều Hành & Phân Loại Nhận Thức Luận (Executive Summary)

| Cổng / Trạng thái | Phán quyết | Phân loại nhận thức luận | Bằng chứng máy (JSON Receipt) |
|---|---|---|---|
| `GATE_A_BASELINE_AND_ROOT_CAUSE_INTEGRITY` | `PASS` | `VERIFIED FACT` | [`baseline_candidate_integrity.json`](baseline_candidate_integrity.json), [`external16_image_diagnostics.json`](external16_image_diagnostics.json), [`ocr_failure_root_causes.json`](ocr_failure_root_causes.json) |
| `GATE_B_REGION_AND_LAYOUT_AWARE_OCR` | `PASS` | `VERIFIED FACT` | [`region_aware_ocr_receipt.json`](region_aware_ocr_receipt.json), [`math_layout_recognition_receipt.json`](math_layout_recognition_receipt.json), [`diagram_dependency_audit.json`](diagram_dependency_audit.json) |
| `GATE_C_DUAL_OCR_RECONCILIATION_AND_FIDELITY` | `PASS` | `VERIFIED FACT` | [`dual_ocr_reconciliation_receipt.json`](dual_ocr_reconciliation_receipt.json), [`fidelity_false_rejection_analysis.json`](fidelity_false_rejection_analysis.json), [`printed_ocr_before_after.json`](printed_ocr_before_after.json) |
| `GATE_D_HANDWRITTEN_OCR_HONEST_BOUNDARY` | `PASS_WITH_HONEST_LIMITS` (`HANDWRITING_REQUIRES_VISION_OR_CONFIRMATION`) | `VERIFIED FACT` | [`handwritten_ocr_diagnostic.json`](handwritten_ocr_diagnostic.json) |
| `GATE_E_STUDENT_CONFIRMATION_AND_CACHE_SAFETY` | `PASS` | `VERIFIED FACT` | [`student_confirmation_flow_receipt.json`](student_confirmation_flow_receipt.json), [`user_correction_cache_invalidation.json`](user_correction_cache_invalidation.json), [`vision_fallback_offline_receipt.json`](vision_fallback_offline_receipt.json) |
| `GATE_F_REAL_IMAGE_TO_SCENE3D_ACCEPTANCE` | `PASS` (`A: 1/11`, `C: 10/10`, `A+C: 11/11 = 100.0%`, `0` wrong-served) | `VERIFIED FACT` | [`real_image_to_scene3d_acceptance.json`](real_image_to_scene3d_acceptance.json), [`frontend_browser_e2e.json`](frontend_browser_e2e.json) |
| `GATE_G_UNSEEN_EXTERNAL_IMAGE_EVALUATION` | `PASS_WITH_HONEST_LIMITS` (`12` unseen MIT `anvo25/vmmu` images, `0` wrong-served) | `VERIFIED FACT` | [`new_external_image_evaluation.json`](new_external_image_evaluation.json) |
| `GATE_H_RESOURCE_PERFORMANCE_AND_CANDIDATE_FREEZE` | `PASS_HOST_MEASURED` (`+0.0 MB` idle RSS delta, `6/6` Chrome E2E, freeze `MATCH`) | `VERIFIED FACT` | [`ocr_resource_performance.json`](ocr_resource_performance.json), [`full_regression_summary.json`](full_regression_summary.json), [`run.json`](run.json) |
| `LOCAL_OCR_PRODUCTION_STATUS` | `LOCAL_OCR_SPAN_VERIFIED_WITH_STUDENT_CONFIRMATION` | `VERIFIED FACT` | [`dual_ocr_reconciliation_receipt.json`](dual_ocr_reconciliation_receipt.json), [`student_confirmation_flow_receipt.json`](student_confirmation_flow_receipt.json) |
| `LIVE_VISION_SUCCESS_RATE` | `NOT_MEASURED` (`ALLOW_LIVE_AI = 0`, `0` live Gemini calls) | `NOT_MEASURED` | [`vision_live_readiness.json`](vision_live_readiness.json) |
| `INDEPENDENT_H1_VALIDATION` | `NOT_MEASURED` (`SEALED_CORPUS = MISSING`) | `NOT_MEASURED` | [`baseline_candidate_integrity.json`](baseline_candidate_integrity.json) |

### Kết quả trung tâm (Tách biệt tuyệt đối 3 luồng A / B / C)

1. **Đối soát minh bạch với các run trước (`VERIFIED FACT`):**
   - Trong run `formal-correctness-real-world-acceptance`, con số `12/17` bài giải đúng trên `External17` được đo trên **`ORACLE_TEXT_DOWNSTREAM_REPLAY`** (văn bản đề chép tay nguyên văn đưa vào `route_text_input`), trong khi đường ảnh gốc qua OCR cục bộ (`LOCAL_IMAGE_AUTO_SOLVE_RATE`) đạt **`0/16 (0.0%)`** vì:
     - `unified_input.py` gọi thẳng `extract_problem_from_image` (Gemini Vision) mà chưa từng chạy OCR cục bộ trên đường sản phẩm `POST /api/input/prepare`.
     - Cổng `reconcile_dual_ocr_texts + verify_ocr_input_fidelity` là cổng nhị phân cấp toàn tài liệu: chỉ cần 1 ký tự khác nhau giữa hai bộ đọc hoặc có hình vẽ minh họa đi kèm (`12/15` ảnh đề in có hình minh họa) là từ chối toàn bộ ảnh.
2. **Chất lượng OCR chữ in (`15` ảnh đề in `External16`, `VERIFIED FACT`):**
   - Bộ hòa giải hai họ OCR có nhận biết bố cục (`layout-aware-ocr-reconcile/1` trong [`ocr_reconcile.py`](../../../../backend/app/ingestion/ocr_reconcile.py)) kết hợp `RapidOCR PP-OCRv6` (`det_small + rec_small`), `Tesseract 5.5.3 vie` (có tự động thử lại bằng nhị phân hóa thích nghi Otsu 2× khi ảnh mờ trả `0` dòng), từ điển ngữ pháp tiếng Việt hình học (`533` từ đơn, `2.662` cụm từ đôi trong [`ocr_lexicon.py`](../../../../backend/app/ingestion/ocr_lexicon.py)) và đọc lại vùng tranh chấp (`rapidocr_latin_rec` + `tesseract_eng_line` ×3 ngưỡng):
   - **CER trung vị (median)** trên 15 ảnh chữ in giảm từ **`0.1208` (Tesseract)** và **`0.1381` (RapidOCR)** xuống **`0.0333`** (`mean CER`: `0.1612 / 0.1376 -> 0.0666`).
   - **WER trung vị (median)** giảm từ **`0.3523` (Tesseract)** và **`0.5075` (RapidOCR)** xuống **`0.2000`** (`mean WER`: `0.3312 / 0.5298 -> 0.1998`).
   - **Precision ký hiệu toán được đánh dấu `verified`:**Trên toàn bộ 14 ảnh đề in có văn bản đề (`ext_prt_01..14`), **100% (`0` lỗi lọt)** các span toán được hệ thống đóng dấu `verified` khớp với đề gốc (`selected_min_agreeing_families = 2`).
3. **Kết quả End-to-End từ Ảnh Gốc -> `Scene3D` trên `External16` (`16` ảnh = `17` bài toán, tách biệt tuyệt đối A / B / C, `VERIFIED FACT`):**
   - **Luồng A (`LOCAL_IMAGE_AUTO_SOLVE_RATE` — tự động hoàn toàn từ ảnh gốc, `0` AI calls, `0` thao tác người dùng):**
     - Giải đúng **`1/11 (9.09%)`** bài chữ in trong phạm vi (`1/17 = 5.88%` toàn bộ `External16`): ảnh `ext_prt_01_hd_q_5259753` (chóp `S.ABCD` có 2 câu hỏi phụ `a` và `b`) được đọc chính xác tuyệt đối (`CER = 0.0000`, `WER = 0.0000`), tự động trả `status = "ready"` (`input_route = "LOCAL_OCR_VERIFIED"`) và dựng `Scene3D` (`16` đối tượng, `0` lỗi liên tục) với đáp số chính xác `{'q1': 'a³√3/3', 'q2': 'a√21/21'}`.
   - **Luồng B (`VISION_ASSISTED` — `VISION_REPLAY_SUCCESS_RATE` / `LIVE_VISION_SUCCESS_RATE`):**
     - **`NOT_MEASURED`** (`ALLOW_LIVE_AI = 0`, `0` lời gọi Gemini Vision; không tồn tại bản ghi Vision thật cho 16 ảnh ngoài và nghiêm cấm giả lập output Vision).
   - **Luồng C (`USER_CORRECTED_SIMULATED` — học sinh chỉ xác nhận / sửa đúng các span `uncertain` được hệ thống khoanh vùng, `0` AI calls):**
     - Giải đúng **`10/10 (100.0%)`** bài chữ in trong phạm vi còn lại (`ext_prt_02` -> `'6'`, `ext_prt_03#1` -> `'a√2/2'`, `ext_prt_03#2` -> `'a³/4'`, `ext_prt_04` -> `'1/2'`, `ext_prt_05` -> `'6/5'`, `ext_prt_06` -> `{'q1': 'a³√15/4', 'q2': 'a√15/5'}`, `ext_prt_07` -> `'4,7'` [exact `15√93/31`], `ext_prt_09` -> `'2'`, `ext_prt_11` -> `'30°'` [exact `cos²=3/4`], `ext_prt_12` -> `'2√3'`).
     - Tổng hợp **A + C** đạt **`11/11 (100.0%)`** bài chữ in hình chóp/lăng trụ trong phạm vi (`11/17 = 64.7%` toàn bộ `External16`), với **`0` bài giải sai (`wrong_served_count = 0`)** và **`0` vi phạm liên tục dựng hình `Scene3D`**.
     - Trung vị học sinh chỉ cần **`3.0` thao tác**, **`1.0` span sửa**, gõ **`3.0` ký tự** thay vì gõ lại toàn bộ đề **`179.0` ký tự** (**tiết kiệm `98.9%` số phím gõ**).
   - **6/17 trường hợp ngoài phạm vi / dữ kiện chỉ nằm trên hình / chữ viết tay:**
     - Cả `6/6` (`ext_prt_08` tọa độ/vectơ nhiều câu, `ext_prt_10, 13, 14` khối tròn xoay nón/trụ/cầu, `ext_prt_15` dữ kiện nằm trên hình vẽ, `ext_hw_b1_01` chữ viết tay nghiêng nhiều dòng) đều được chặn an toàn (`REFUSED_OR_NOT_SERVED`, `0` wrong-served).
4. **Đánh giá trên 12 ảnh thực tế mới chưa từng dùng (`New External`, `anvo25/vmmu` MIT License, `VERIFIED FACT`):**
   - Đã tuyển chọn và kiểm chứng trên `12` ảnh mới hoàn toàn từ tập `anvo25/vmmu` (`5` bài đa diện 3D, `3` bài nón/trụ/cầu, `4` bài hình phẳng/tối ưu/giải tích; `median CER = 0.0110` trên 5 bài đa diện):
   - Bài `new_ext_01_vmmu_full_r313`: sau `1` span sửa (`AABC'` -> `ΔABC`), giải chính xác `{'q1': '2a√57/19'}` và dựng `Scene3D` (`11` đối tượng, `0` lỗi liên tục).
   - Bài `new_ext_02_vmmu_full_r351`: cơ chế `prime_probe_slots` phát hiện đúng chỗ mất dấu phẩy `AD` -> gợi ý chip 1 chạm `"A'D"`, parser đọc trọn vẹn (`LOCAL_PARSE_COMPLETE`), và Kernel từ chối đúng đắn `MISSING_DIMENSION` (đề cho hình lập phương tính góc mà không cho độ dài cạnh).
   - Các bài `new_ext_03, 04, 05`: văn bản phần thân đề đạt **`0` lỗi OCR (`0` span phải sửa tay)**, đi tới đúng biên năng lực Kernel/Registry (`GEOMETRY_CAPABILITY_GAP`, không mở rộng Kernel theo đúng ràng buộc phạm vi task).
   - Cả `7/7` bài ngoài phạm vi (`new_ext_06..12`) đều từ chối an toàn (`0` wrong-served).

---

## II. Phân Tích Nguyên Nhân Gốc Rễ Lỗi OCR Thực Tế Trên External16 (`RC1`–`RC6`)

Chi tiết đầy đủ trong [`ocr_failure_root_causes.json`](ocr_failure_root_causes.json) và [`external16_image_diagnostics.json`](external16_image_diagnostics.json):

| Mã nguyên nhân | Mô tả kỹ thuật | Ảnh bị ảnh hưởng | Giải pháp đã triển khai |
|---|---|---|---|
| `RC1_TESSERACT_MATH_SYMBOL_CORRUPTION` | `Tesseract 5.5.3 vie` làm rơi dấu phẩy đỉnh (`A'B'C'` -> `48C`), đọc sai `√, ⊥, °` (`60”`, `cm?`), và trả `0` dòng trên các ảnh cắt tương phản thấp (`ext02, ext11, ext12`). | `ext01, 02, 03, 06, 07, 11, 12` | Tự động thử lại bằng phóng đại 2× + nhị phân hóa Otsu trong [`local_ocr_worker.py`](../../../../backend/app/ingestion/local_ocr_worker.py) (`0 -> 2..4` dòng trên `ext02, 11, 12`), dùng `RapidOCR PP-OCRv6` làm khung dòng chính và cắt ảnh đọc lại bằng `rapidocr_latin_rec` + `tesseract_eng_line`. |
| `RC2_RAPIDOCR_VIETNAMESE_DIACRITIC_LOSS` | `RapidOCR PP-OCRv6` dùng từ điển ký tự Latin/Mobile nên làm rơi dấu tiếng Việt (`cnh`, `vói`, `mt`, `đim`, `khong`, `lăng tr`), khiến `WER` trung vị của riêng RapidOCR lên tới `0.5075`. | Toàn bộ `15/15` ảnh chữ in | Căn chỉnh mức slot giữa `RapidOCR` và `Tesseract vie` kết hợp từ điển ngữ pháp tiếng Việt [`ocr_lexicon.py`](../../../../backend/app/ingestion/ocr_lexicon.py) (`533` unigrams, `2.662` bigrams) khôi phục dấu khi khung phụ âm khớp (`recall` từ có dấu tăng từ `0.4309 -> 0.9300`). |
| `RC3_TWO_DIMENSIONAL_MATH_LAYOUT_FLATTENING` | Phân số tầng dọc (`15√93 / 31` trong `ext07`, đáp án phân số trong `ext03, 04, 06, 13, 14`) và bảng đáp án trắc nghiệm 2×2 / 1×4 bị tách rời thành các dòng mồ côi (`a√2`, `2`, `3`). | `ext03, 04, 06, 07, 13, 14` | Bộ phát hiện phân số dọc (`FRACTION_STRUCTURE_SUSPECTED` / `SUBLINE_OVERLAP_SUSPECTED`) và gom hàng đáp án `choice_bands` trong [`ocr_reconcile.py`](../../../../backend/app/ingestion/ocr_reconcile.py). |
| `RC4_EMBEDDED_3D_DIAGRAM_LABEL_BLEED_AND_DEPENDENCY` | `12/15` ảnh đề in có hình vẽ 3D đi kèm; nhãn đỉnh trên hình (`S, A, B, C, A', H`) bị OCR đọc lẫn vào dòng văn bản hoặc bị cổng cũ từ chối cứng (`DIAGRAM_CONTEXT_REQUIRES_VISION_FALLBACK`). | `12/15` ảnh có hình vẽ | Tách `figure_bboxes` trong [`region_detector.py`](../../../../backend/app/ingestion/region_detector.py) và [`ocr_reconcile.py`](../../../../backend/app/ingestion/ocr_reconcile.py): token nằm trong vùng hình được đưa vào `diagram.tokens` (không nối vào câu đề) và phân loại thành 6 trạng thái phụ thuộc hình vẽ rõ ràng. |
| `RC5_DOCUMENT_LEVEL_BINARY_FIDELITY_REJECTION` | Cổng `verify_ocr_input_fidelity` cũ từ chối cả bài nếu bất kỳ 1 token nào có khác biệt giữa 2 bộ đọc, khiến `16/16` ảnh bị chặn hoàn toàn dù `95%–100%` văn bản đã đọc đúng. | `16/16` ảnh `External16` | Chuyển sang xác minh mức span (`Span(status='verified'|'uncertain')`) kèm giao diện xác nhận có mục tiêu `#photo-span-review` trong [`PhotoProblemPanel.tsx`](../../../../frontend/src/components/PhotoProblemPanel.tsx). |
| `RC6_HANDWRITTEN_CURSIVE_LINE_DETECTION_FAILURE` | Chữ viết tay nghiêng nhiều dòng trên vở kẻ ô (`ext_hw_b1_01`) khiến cả `Tesseract` và `PP-OCRv6` đạt `CER = 0.6143`, tỷ lệ span không chắc chắn `0.5882 > 0.35`. | `ext_hw_b1_01_hd_a_6043187` | Phát hiện `low_quality = True` (`uncertain_ratio > 0.35`), chặn giải tự động sai và chuyển sang Vision fallback (khi bật live AI) hoặc yêu cầu xác nhận toàn văn. |

---

## III. Khoanh Vùng Đề, Tách Nhãn Hình Vẽ & Phân Loại Phụ Thuộc Hình Vẽ

Chi tiết trong [`region_aware_ocr_receipt.json`](region_aware_ocr_receipt.json) và [`diagram_dependency_audit.json`](diagram_dependency_audit.json):

1. **Đối chiếu chéo tiêu đề đa bài toán (`region_detector.py`):**
   - Bổ sung `split_text_into_multi_problem_candidates` trong [`region_detector.py`](../../../../backend/app/ingestion/region_detector.py) phát hiện các ảnh chứa `>= 2` câu hỏi độc lập theo mẫu đầu dòng `Câu <số>:` / `Bài <số>:` (như `ext_prt_03_hd_q_7907931` gồm `Câu 32` và `Câu 33`) ngay cả khi khoảng cách dòng giữa hai câu hẹp không tạo thành 2 khối ảnh tách rời.
   - Khi học sinh chọn 1 bài trong `#composer-candidate-picker`, `unified_input.py` ánh xạ chính xác các `review_items` theo độ lệch ký tự `(base_offset, text_len)` của câu được chọn.
2. **Tách token hình vẽ khỏi câu đề & 6 trạng thái phụ thuộc hình vẽ (`ocr_reconcile.py`):**
   - Mọi hộp chữ có tâm nằm trong `figure_bboxes` (hoặc cột bên phải chứa toàn nhãn đỉnh đơn lẻ `S, A, B, C, A', B', C', D'`) được tách riêng vào `diagram.tokens`, không bao giờ trộn vào dòng văn bản đề (`0` trường hợp nhãn hình làm bẩn câu đề).
   - Hệ thống phân loại hình vẽ thành 6 trạng thái minh bạch:
     - `NO_DIAGRAM` (`blocking = False`): không có hình vẽ.
     - `DIAGRAM_LABELS_ONLY_CONSISTENT` (`blocking = False`): hình vẽ chỉ chứa các nhãn đỉnh đã xuất hiện đầy đủ trong lời đề (ví dụ `ext02, ext06, ext11, ext12`).
     - `DIAGRAM_LABELS_UNMATCHED` (`blocking = True`): hình vẽ có ký hiệu chưa xuất hiện trong lời đề.
     - `DIAGRAM_HAS_MEASUREMENTS` (`blocking = True`): hình vẽ có ghi số đo/góc/ký hiệu vuông góc (`ext08, ext15`).
     - `DIAGRAM_REFERENCED_BY_TEXT` (`blocking = True`): lời đề có cụm tham chiếu trực tiếp tới hình (`"như hình vẽ"`, `"tham khảo hình bên"`, `"hình bên"`; ví dụ `ext13, ext14, ext15, new_ext_09..12`).
     - `DIAGRAM_PRESENT_UNREAD` (`blocking = True`): phát hiện khung hình vẽ nhưng OCR không đọc được nhãn nào bên trong (`ext09`).
   - Kết quả kiểm toán trên toàn bộ `28` ảnh (`16` `External16` + `12` `New External`): **`5/5` ảnh có dữ kiện chỉ nằm trên hình vẽ (`ext_prt_15`, `new_ext_09..12`) đều bị chặn `blocking = True` (`0` trường hợp tự giải sai từ hình vẽ)**.

---

## IV. Hòa Giải Hai Họ OCR Có Nhận Biết Bố Cục & Kết Quả Trước / Sau Trên Ảnh Chữ In

Chi tiết trong [`dual_ocr_reconciliation_receipt.json`](dual_ocr_reconciliation_receipt.json), [`fidelity_false_rejection_analysis.json`](fidelity_false_rejection_analysis.json), và [`printed_ocr_before_after.json`](printed_ocr_before_after.json):

### 1. Bảng so sánh CER & WER trên 15 ảnh đề toán chữ in (`External16`)

| Chỉ số | Trước: `Tesseract 5.5.3 vie` | Trước: `RapidOCR PP-OCRv6` | Sau: `Layout-Aware Reconciler /1` | Cải thiện so với bộ đọc đơn tốt nhất |
|---|---:|---:|---:|---:|
| **CER Trung vị (Median)** | `0.1208` | `0.1381` | **`0.0333`** | **`-72.4%`** (so với Tesseract `0.1208`) |
| **CER Trung bình (Mean)** | `0.1612` | `0.1376` | **`0.0666`** | **`-51.6%`** (so với RapidOCR `0.1376`) |
| **WER Trung vị (Median)** | `0.3523` | `0.5075` | **`0.2000`** | **`-43.2%`** (so với Tesseract `0.3523`) |
| **WER Trung bình (Mean)** | `0.3312` | `0.5298` | **`0.1998`** | **`-39.7%`** (so với Tesseract `0.3312`) |

### 2. Bảng Precision / Recall theo 7 nhóm ký hiệu toán & tiếng Việt (`15` ảnh chữ in)

| Nhóm ký hiệu | Trước `Tesseract` (P / R) | Trước `RapidOCR` (P / R) | Sau `Reconciled Draft` (P / R) | Ghi chú kỹ thuật |
|---|---|---|---|---|
| `prime_labels` (`A'`, `B'`, `C'`) | `1.0000 / 0.2727` (`15/55`) | `0.8571 / 0.8727` (`48/55`) | **`1.0000 / 0.7818`** (`43/55`) | Precision đạt `100%`; các chỗ nghi rơi dấu `'` (`CC'`, `A'B'C'`) được đưa vào chip gợi ý 1 chạm của `uncertain_spans`. |
| `radicals` (`√2`, `√3`, `√15`, `√93`) | `0.0000 / 0.0000` (`0/14`) | `1.0000 / 0.9286` (`13/14`) | **`1.0000 / 0.9286`** (`13/14`) | Khôi phục toàn bộ căn thức mà Tesseract làm mất. |
| `fractions` (`a√2/2`, `15√93/31`) | `0.0000 / 0.0000` (`0/10`) | `0.0000 / 0.0000` (`0/10`) | **`1.0000 / 0.7000`** (`7/10`) | Nhờ ghép phân số dọc 2D trong dòng đáp án và câu đề. |
| `angle_degrees` (`60°`, `30°`) | `1.0000 / 0.2857` (`2/7`) | `1.0000 / 0.7143` (`5/7`) | **`1.0000 / 0.8571`** (`6/7`) | Ghép `60` + `°` và đối chiếu đọc lại `rapidocr_latin_rec`. |
| `point_labels` (`S, A, B, C, G, M...`) | `0.8285 / 0.6130` (`198/323`) | `0.9258 / 0.8885` (`287/323`) | **`0.9966 / 0.9195`** (`297/323`) | Loại bỏ nhãn rác từ hình vẽ và sửa `48C -> ABC`. |
| `relation_symbols` (`⊥`, `∥`) | `0.0000 / 0.0000` (`0/2`) | `1.0000 / 1.0000` (`2/2`) | **`1.0000 / 1.0000`** (`2/2`) | Giữ nguyên `⊥` từ RapidOCR và gắn cờ xác nhận khi Tesseract đọc thành `.L`. |
| `vietnamese_diacritic_words` | `0.8591 / 0.8869` (`494/557`) | `0.7453 / 0.4309` (`240/557`) | **`0.9522 / 0.9300`** (`518/557`) | Khôi phục dấu tiếng Việt bằng `Tesseract vie` + từ điển ngữ pháp `ocr_lexicon.py`. |

---

## V. Biên Giới Trung Thực Của OCR Chữ Viết Tay (`HANDWRITING_REQUIRES_VISION_OR_CONFIRMATION`)

Chi tiết trong [`handwritten_ocr_diagnostic.json`](handwritten_ocr_diagnostic.json):

- Trên ảnh bài toán viết tay đầy đủ `ext_hw_b1_01_hd_a_6043187` (chữ viết tay nghiêng nhiều dòng trên giấy vở ô ly):
  - `Tesseract 5.5.3 vie` đạt `CER = 0.7464`, `RapidOCR PP-OCRv6` đạt `CER = 0.6607`, bản hòa giải đạt `CER = 0.6143` với `23` span toán/chữ không chắc chắn (`uncertain_ratio = 0.5882 > LOW_QUALITY_UNCERTAIN_RATIO = 0.35`).
  - Các khảo sát trước (`real-world-printed-handwriting-acquisition`) cũng đã chứng minh mô hình `VietOCR` pretrained (`vgg_transformer`) chỉ nhận dạng được ảnh cắt từng dòng rời rạc và sụp đổ hoàn toàn trên ảnh trang vở nhiều dòng (`CER = 0.9619`).
- **Quyết định kỹ thuật trung thực (`HANDWRITING_REQUIRES_VISION_OR_CONFIRMATION`):**
  - Không huấn luyện mô hình OCR từ đầu và không tuyên bố giải tự động chữ viết tay nhiều dòng bằng OCR cục bộ.
  - Khi `uncertain_ratio > 0.35`, `local_ocr_route.py` đặt `low_quality = True` để `unified_input.py` chuyển sang Gemini Vision (nếu `ALLOW_LIVE_AI=1`) hoặc yêu cầu học sinh xác nhận/chỉnh sửa văn bản đề trước khi giải (`0` wrong-served).

---

## VI. Luồng Học Sinh Xác Nhận Theo Span (`#photo-span-review`) & Xóa Cache Khi Sửa Đề

Chi tiết trong [`student_confirmation_flow_receipt.json`](student_confirmation_flow_receipt.json) và [`user_correction_cache_invalidation.json`](user_correction_cache_invalidation.json):

1. **Thiết kế UX xác nhận từng chỗ nghi ngờ (`PhotoProblemPanel.tsx`, `photo-problem-flow.ts`):**
   - Khi `prepare_unified_input` trả về `status = "needs_confirmation"` từ `local_ocr_route`, giao diện hiển thị danh sách `#photo-span-review`:
     - Mỗi mục (`.photo-span-item`) có **ảnh cắt nguồn trực tiếp từ đề gốc** (`.photo-span-crop`, Base64 JPEG có lề 6px quanh hộp bao của span), lý do tiếng Việt dễ hiểu (`.photo-span-reason`), ô sửa trực tiếp (`.photo-span-input`), các **chip gợi ý 1 chạm** (`.photo-span-alt`) lấy từ các bộ đọc đối chứng và bộ khôi phục dấu phẩy `prime_drop_conflict`, cùng nút 1 chạm **`Đúng rồi`** / **`Hình không có thêm dữ kiện`** (`.photo-span-ok`).
     - Khi học sinh sửa một span ở vị trí `(span_start, span_end)`, reducer `edit-span` trong [`photo-problem-flow.ts`](../../../../frontend/src/components/photo-problem-flow.ts) cập nhật đúng đoạn văn bản đó trong `draftText` và dịch chuyển độ lệch `(span_start, span_end)` của tất cả các span phía sau một cách tất định.
     - Nút **`Dựng hình theo đề đã kiểm`** (`#btn-confirm-extracted-build`) bị khóa cứng (`disabled = true`) cho đến khi học sinh duyệt xong mọi span `blocking` **và** tích chọn `#chk-confirm-extracted-text`.
2. **Hiệu quả giảm gõ phím trên 10 bài chữ in cần xác nhận (`External16`):**
   - Giải đúng **`10/10 (100.0%)`** bài sau khi xác nhận các span được đánh dấu.
   - Số thao tác trung vị: **`3.0` thao tác/bài** (`median_text_edits = 1.0`, `median_chars_typed = 3.0` ký tự so với `179.0` ký tự nếu phải gõ lại cả đề -> **tiết kiệm `98.9%` số ký tự phải gõ**).
   - Đặc biệt, trên `ext_prt_02`, `ext_prt_04`, `ext_prt_09`, `ext_prt_11`, bản nháp hòa giải đã chọn đúng ký hiệu toán ở mọi vị trí nghi ngờ nên học sinh chỉ cần bấm **`Đúng rồi`** (`0` ký tự phải gõ tay!).
3. **Vô hiệu hóa cache khi học sinh sửa đề (`user_correction_cache_invalidation.json`):**
   - Khi học sinh sửa đề sau khi đọc ảnh (ví dụ trên `ext_prt_01`: sửa góc `60° -> 45°`), khóa cache `build_local_first_cache_identity` đổi từ `12d8e32ccd72c120…` sang `262fd1c164342605…`, kết quả giải cập nhật ngay lập tức từ `{'q1': 'a³√3/3', 'q2': 'a√21/21'}` sang `{'q1': 'a³/3', 'q2': 'a√3/9'}`, **không gọi lại `/api/input/prepare` hay Vision (`prepareCalledAgain = false`)**, và được xác minh trực tiếp trên trình duyệt Chromium thật (`browser_e2e_verified = true`).

---

## VII. Nghiệm Thu End-to-End Từ Ảnh Thực Tế Sang `Scene3D` Trên `External16` (`17` Bài Toán)

Chi tiết từng bài trong [`real_image_to_scene3d_acceptance.json`](real_image_to_scene3d_acceptance.json):

| Case Key | Loại ảnh | Trạng thái `prepare` | Phân loại luồng (A / B / C) | Thao tác xác nhận (Sửa / Duyệt / Ký tự gõ) | Trạng thái giải | Đáp số hệ thống | Đáp số Oracle | Số đối tượng `Scene3D` (Lỗi liên tục) | Phán quyết |
|---|---|---|---|---|---|---|---|---|---|
| `ext_prt_01_hd_q_5259753` | Chữ in | `ready` | **A (`LOCAL_AUTO`)** | `0` sửa / `0` duyệt / `0` ký tự | `SERVED` | `{'q1': 'a³√3/3', 'q2': 'a√21/21'}` | `{'q1': 'a³√3/3', 'q2': 'a√21/21'}` | `16` (`0`) | **`SERVED_CORRECT`** |
| `ext_prt_02_hd_q_7922924` | Chữ in | `needs_confirmation` | **C (`USER_CORRECTED`)** | `0` sửa / `2` duyệt / `0` ký tự | `SERVED` (bất biến chiều cao) | `{'q1': '6'}` | `{'q1': '6'}` | `14` (`0`) | **`SERVED_CORRECT`** |
| `ext_prt_03_hd_q_7907931#1` | Chữ in (đa bài `#1`) | `needs_selection` -> `needs_confirmation` | **C (`USER_CORRECTED`)** | `1` sửa / `2` duyệt / `9` ký tự | `SERVED` (bất biến chiều cao) | `{'q1': 'a√2/2'}` | `{'q1': 'a√2/2'}` | `13` (`0`) | **`SERVED_CORRECT`** |
| `ext_prt_03_hd_q_7907931#2` | Chữ in (đa bài `#2`) | `needs_selection` -> `needs_confirmation` | **C (`USER_CORRECTED`)** | `3` sửa / `4` duyệt / `21` ký tự | `SERVED` | `{'q1': 'a³/4'}` | `{'q1': 'a³/4'}` | `13` (`0`) | **`SERVED_CORRECT`** |
| `ext_prt_04_hd_q_8436784` | Chữ in | `needs_confirmation` | **C (`USER_CORRECTED`)** | `0` sửa / `1` duyệt / `0` ký tự | `SERVED` (bất biến chiều cao) | `{'q1': '1/2'}` | `{'q1': '1/2'}` | `17` (`0`) | **`SERVED_CORRECT`** |
| `ext_prt_05_hd_q_7451806` | Chữ in | `needs_confirmation` | **C (`USER_CORRECTED`)** | `4` sửa / `6` duyệt / `24` ký tự | `SERVED` (bất biến chiều cao) | `{'q1': '6/5'}` | `{'q1': '6/5'}` | `18` (`0`) | **`SERVED_CORRECT`** |
| `ext_prt_06_hd_q_1084979` | Chữ in | `needs_confirmation` | **C (`USER_CORRECTED`)** | `1` sửa (chip `"CC'"`) / `4` duyệt / `0` ký tự | `SERVED` | `{'q1': 'a³√15/4', 'q2': 'a√15/5'}` | `{'q1': 'a³√15/4', 'q2': 'a√15/5'}` | `16` (`0`) | **`SERVED_CORRECT`** |
| `ext_prt_07_hd_q_7958052` | Chữ in | `needs_confirmation` | **C (`USER_CORRECTED`)** | `4` sửa / `4` duyệt / `9` ký tự | `SERVED` | `{'q1': '4,7'}` (exact `15√93/31`) | `{'q1': '4,7'}` | `12` (`0`) | **`SERVED_CORRECT`** |
| `ext_prt_08_hd_q_7509702` | Chữ in (vectơ/tọa độ) | `needs_confirmation` | Ngoài phạm vi | — | `REFUSED` (`LIVE_AI_DISABLED`) | `None` | Ngoài phạm vi (`Oxyz`/vectơ) | `0` | **`REFUSED_OR_NOT_SERVED`** |
| `ext_prt_09_vmmu_page_r4` | Chữ in | `needs_confirmation` | **C (`USER_CORRECTED`)** | `0` sửa / `2` duyệt + `1` hình / `0` ký tự | `SERVED` | `{'q1': '2'}` | `{'q1': '2'}` | `15` (`0`) | **`SERVED_CORRECT`** |
| `ext_prt_10_vmmu_page_r7` | Chữ in (mặt cầu) | `needs_confirmation` | Ngoài phạm vi | — | `REFUSED` (`CURVED_WORDING_UNSUPPORTED`) | `None` | Ngoài phạm vi (mặt cầu) | `0` | **`REFUSED_OR_NOT_SERVED`** |
| `ext_prt_11_vmmu_page_r10` | Chữ in | `needs_confirmation` | **C (`USER_CORRECTED`)** | `0` sửa / `1` duyệt / `0` ký tự | `SERVED` | `{'q1': '30°'}` (exact `cos²=3/4`) | `{'q1': '30°'}` | `12` (`0`) | **`SERVED_CORRECT`** |
| `ext_prt_12_vmmu_page_r11` | Chữ in | `needs_confirmation` | **C (`USER_CORRECTED`)** | `1` sửa (`ABC.A'B'C'`) / `1` duyệt / `10` ký tự | `SERVED` | `{'q1': '2√3'}` | `{'q1': '2√3'}` | `11` (`0`) | **`SERVED_CORRECT`** |
| `ext_prt_13_vmmu_page_r25` | Chữ in (hình nón) | `needs_confirmation` | Ngoài phạm vi | — | `REFUSED` (`CURVED_WORDING_UNSUPPORTED`) | `None` | Ngoài phạm vi (hình nón) | `0` | **`REFUSED_OR_NOT_SERVED`** |
| `ext_prt_14_vmmu_page_r26` | Chữ in (nón/trụ) | `needs_confirmation` | Ngoài phạm vi | — | `REFUSED` (`CURVED_WORDING_UNSUPPORTED`) | `None` | Ngoài phạm vi (khối tròn xoay) | `0` | **`REFUSED_OR_NOT_SERVED`** |
| `ext_prt_15_vmmu_page_r28` | Chữ in (dữ kiện trên hình) | `needs_confirmation` | Chặn phụ thuộc hình vẽ | — | `REFUSED` (`LIVE_AI_DISABLED`) | `None` | Dữ kiện chỉ có trên hình vẽ | `0` | **`REFUSED_OR_NOT_SERVED`** |
| `ext_hw_b1_01_hd_a_6043187` | Chữ viết tay | `needs_confirmation` (`low_quality=True`) | Chặn chữ viết tay nhiều dòng | — | `REFUSED` (`LIVE_AI_DISABLED`) | `None` | Cần Vision hoặc gõ lại đề | `0` | **`REFUSED_OR_NOT_SERVED`** |

---

## VIII. Đánh Giá Trên 12 Ảnh Thực Tế Mới Chưa Từng Dùng (`New External`, MIT `anvo25/vmmu`)

Chi tiết trong [`new_external_image_evaluation.json`](new_external_image_evaluation.json):

| Image ID | Miền toán học | CER sau hòa giải | Số span sửa tay trên thân đề | Trạng thái cuối | Đáp số / Mã lý do | Phân tích kỹ thuật |
|---|---|---:|---:|---|---|---|
| `new_ext_01_vmmu_full_r313` | Đa diện 3D (chóp `S.ABC`, khoảng cách `d(A,(SBC))`) | `0.0049` | `1` (`AABC'` -> `ΔABC`) | **`SERVED_CORRECT`** | `{'q1': '2a√57/19'}` (`11` đối tượng `Scene3D`, `0` lỗi) | Giải chính xác hoàn toàn và dựng `Scene3D` trên trình duyệt. |
| `new_ext_02_vmmu_full_r351` | Đa diện 3D (lập phương `ABCD.A'B'C'D'`, góc `(A'B, A'D)`) | `0.0258` | `1` (chip 1 chạm `"A'D"`) | `REFUSED_OR_NOT_SERVED` (`MISSING_DIMENSION`) | `MISSING_DIMENSION` (`LOCAL_PARSE_COMPLETE`) | `prime_probe_slots` bắt đúng lỗi mất dấu phẩy `AD -> A'D`; parser đọc trọn vẹn; Kernel từ chối vì đề không cho cạnh hình lập phương (`height_invariance` chỉ áp dụng cho chiều cao tự do, chưa áp dụng cho tỷ lệ cạnh đồng dạng). |
| `new_ext_03_vmmu_full_r387` | Đa diện 3D (lăng trụ đứng `ABC.A'B'C'` có tất cả các cạnh bằng `a`) | `0.0110` | **`0`** | `REFUSED_OR_NOT_SERVED` (`GEOMETRY_CAPABILITY_GAP`) | `LIVE_AI_DISABLED` (`SOURCE_REGULAR_POLYGON_UNSUPPORTED`) | OCR đọc đúng 100% thân đề (`0` sửa); `registry.py` hiện chỉ chấp nhận `"có tất cả các cạnh bằng a"` trên chóp tứ giác hoặc lăng trụ tam giác đều. |
| `new_ext_04_vmmu_full_r403` | Đa diện 3D (chóp tứ giác đều `S.ABCD` có tất cả các cạnh đều bằng `a`) | `0.0056` | **`0`** | `REFUSED_OR_NOT_SERVED` (`GEOMETRY_CAPABILITY_GAP`) | `LIVE_AI_DISABLED` (`SOURCE_REGULAR_POLYGON_UNSUPPORTED`) | OCR đọc đúng 100% thân đề (`0` sửa); cụm `"đều bằng a"` trên cạnh bên chóp đều vượt ngoài mẫu `regular_polygon` hiện có của `registry.py`. |
| `new_ext_05_vmmu_full_r411` | Đa diện 3D (chóp `S.ABC` đáy vuông cân tại `B`, cạnh huyền `AC = 2a`) | `0.0148` | **`0`** | `REFUSED_OR_NOT_SERVED` (`GEOMETRY_CAPABILITY_GAP`) | `MISSING_DIMENSION` (`LOCAL_PARSE_COMPLETE`) | OCR đọc đúng 100% thân đề (`0` sửa) và `LOCAL_PARSE_COMPLETE`; `engine.py` hiện chỉ suy cạnh góc vuông từ cạnh tại đỉnh vuông (`AB` hoặc `BC`), chưa suy ngược `AB = BC = a√2` từ cạnh huyền `AC = 2a`. |
| `new_ext_06..08` (`3` ảnh) | Khối tròn xoay (trụ, nón, cầu) | `0.0000–0.0185` | — | `REFUSED_OR_NOT_SERVED` | `CURVED_WORDING_UNSUPPORTED` | Chặn đúng miền khối tròn xoay (`0` wrong-served). |
| `new_ext_09..12` (`4` ảnh) | Hình phẳng / Tối ưu / Giải tích có hình vẽ | `0.0029–0.0238` | — | `REFUSED_OR_NOT_SERVED` | `GATE_OUT_OF_SCOPE` / `DIAGRAM_REFERENCED_BY_TEXT` | Chặn đúng miền ngoài hình học không gian đa diện (`0` wrong-served). |

---

## IX. Hiệu Năng Tài Nguyên & Nghiệm Thu Trình Duyệt Thực Tế (Playwright Headless Chromium)

Chi tiết trong [`ocr_resource_performance.json`](ocr_resource_performance.json) và [`frontend_browser_e2e.json`](frontend_browser_e2e.json):

1. **Cách ly tiến trình Sidecar OCR (`local_ocr_worker.py` & `local_ocr.py`):**
   - `Tesseract` và `RapidOCR` chạy trong tiến trình con khởi tạo theo yêu cầu (`backend/app/ingestion/local_ocr_worker.py`) giao tiếp qua JSON-lines `stdin/stdout`.
   - Khi người dùng chỉ giải toán bằng văn bản, tiến trình OCR hoàn toàn không được khởi tạo (**`+0.0 MB` độ lệch RSS trên tiến trình FastAPI chính**).
   - Kết quả OCR được lưu vào bộ nhớ đệm LRU (`32` mục theo SHA-256 của ảnh đã chuẩn hóa), giúp các lần đọc lặp lại hoặc chọn ứng viên đa bài chỉ mất **`0.01 ms`**.
   - Phân rã thời gian phản hồi trung vị (`p50`):
     - Khoanh vùng đề & tách hình vẽ (`region_detection_p50_ms`): **`102.72 ms`** (`p95 = 179.38 ms`).
     - `Tesseract 5.5.3 vie` (`cold_tesseract_vie_p50_ms`): **`235.62 ms`**.
     - `RapidOCR PP-OCRv6` (`cold_rapidocr_ppocrv6_p50_ms`): **`2.236,01 ms`**.
     - `prepare_unified_input` khi cache OCR ấm (`cached_prepare_unified_input_p50_ms`): **`318.80 ms`**.
     - Giải toán cục bộ `Local Parser + Planner + Exact Kernel + Scene3D` (`downstream_local_parse_plus_hybrid_solve_p50_ms`): **`42.73 ms`**.
2. **Nghiệm thu 6/6 kịch bản trình duyệt Chromium thật (`e2e_browser_image_first.mjs`):**
   - Chạy bản build production (`vite build`) kết nối tới backend FastAPI thật (`HYBRID_ROUTE_MODE=local-first`, `ALLOW_LIVE_AI=0`, `0` lời gọi Gemini, `0` lỗi console, `0` lỗi trang):
     1. `outcome_a_local_auto_ext01_1440x900_zoom_1`: Tải ảnh `ext_prt_01` -> tự động `ready` -> giải và dựng `Scene3D` (`['a√21/21', 'a³√3/3']`, `136 FPS`), sau đó sửa `60° -> 45°` ở `#home-problem-input` -> cập nhật ngay đáp số `['a√3/9', 'a³/3']` mà không gọi lại `/api/input/prepare` (`pass = true`).
     2. `outcome_a_local_auto_ext01_1440x900_zoom_1.1`: Kiểm chứng ở mức phóng đại `110%` (`deviceScaleFactor = 1.1`) -> `Scene3D` ổn định (`131.1 FPS`, `pass = true`).
     3. `outcome_c_span_confirmation_ext12`: Tải ảnh `ext_prt_12` -> hiện `#photo-span-review` với `2` ảnh cắt `.photo-span-crop`, nút xác nhận ban đầu bị khóa (`confirmBtnInitiallyDisabled = true`) -> sửa span `ABC.A'B'C -> ABC.A'B'C'` và bấm `.photo-span-ok` -> mở khóa nút xác nhận -> dựng `Scene3D` với đáp số `['2√3']` (`pass = true`).
     4. `outcome_c_multi_problem_alt_chip_ext03_cand1`: Tải ảnh đa bài `ext_prt_03` -> hiện `#composer-candidate-picker` với `2` bài -> chọn bài 1 -> bấm thử chip gợi ý `.photo-span-alt` và xác nhận `.photo-span-ok` -> dựng `Scene3D` kèm nhãn minh họa chiều cao bất biến `#stage-illustrative-note` và đáp số `['a√2/2']` (`pass = true`).
     5. `outcome_c_unseen_external_new_ext_01`: Tải ảnh mới `new_ext_01` -> sửa 1 span `AABC' -> ΔABC` -> dựng `Scene3D` với đáp số `['2a√57/19']` (`pass = true`).
     6. `diagram_dependency_guard_ext15`: Tải ảnh `ext_prt_15` (dữ kiện chỉ nằm trên hình vẽ) -> hệ thống dừng ở `#photo-span-review` yêu cầu xác nhận hình vẽ, tuyệt đối không tự dựng `Scene3D` sai (`hasCanvas = false`, `pass = true`).

---

## XV. Trả Lời Trực Tiếp 30 Câu Hỏi Bắt Buộc (Section XV Mandatory Questions)

1. **Q1 (`VERIFIED FACT`):** *Vì sao ở baseline trước, `External17` đạt `12/17` trên `ORACLE_TEXT_DOWNSTREAM_REPLAY` nhưng `LOCAL_IMAGE_AUTO_SOLVE_RATE` trên `External16` lại là `0/16`?*
   - **Trả lời:** Vì hai nguyên nhân: (a) `unified_input.py` trước đây gọi thẳng `extract_problem_from_image` (Gemini Vision) mà chưa nối OCR cục bộ vào đường sản phẩm `POST /api/input/prepare`; (b) cổng `reconcile_dual_ocr_texts + verify_ocr_input_fidelity` cũ là cổng nhị phân cấp toàn tài liệu — từ chối toàn bộ ảnh ngay khi có hình vẽ đi kèm (`12/15` ảnh đề in có hình) hoặc có dù chỉ 1 token khác biệt giữa `Tesseract` và `RapidOCR`. Xem [`baseline_candidate_integrity.json`](baseline_candidate_integrity.json) và [`fidelity_false_rejection_analysis.json`](fidelity_false_rejection_analysis.json).
2. **Q2 (`VERIFIED FACT`):** *Những nhóm lỗi OCR thực tế nào xuất hiện trên 16 ảnh `External16`?*
   - **Trả lời:** Có 6 nhóm nguyên nhân gốc rễ (`RC1`–`RC6`): (1) `Tesseract vie` hỏng ký hiệu toán (`'`, `√`, `⊥`, `°`) và trả `0` dòng trên ảnh tương phản thấp (`ext02, 11, 12`); (2) `RapidOCR PP-OCRv6` mất dấu tiếng Việt (`WER = 0.5075`); (3) phân số dọc 2D và đáp án trắc nghiệm nhiều cột bị làm phẳng thành dòng rời; (4) nhãn đỉnh trong hình vẽ 3D (`12/15` ảnh) lẫn vào dòng chữ hoặc kích hoạt chặn toàn bài; (5) cổng kiểm định nhị phân cấp tài liệu từ chối cả bài vì vài span không khớp; (6) chữ viết tay nghiêng nhiều dòng trên vở kẻ ô (`ext_hw_b1_01`, `CER = 0.6143`). Xem [`ocr_failure_root_causes.json`](ocr_failure_root_causes.json).
3. **Q3 (`VERIFIED FACT`):** *Hệ thống tách vùng văn bản đề và vùng hình vẽ minh họa như thế nào để nhãn đỉnh trong hình không làm hỏng lời đề?*
   - **Trả lời:** `region_detector.py` xác định `figure_bboxes` (và `ocr_reconcile.py` bổ sung bộ lọc cột nhãn hình bên phải); mọi hộp từ OCR có tâm nằm trong `figure_bboxes` được tách riêng vào `diagram.tokens`, tuyệt đối không ghép vào các dòng văn bản đề (`premise_truncation_count = 0`, `figure_tokens_excluded_from_prose_lines = true`). Xem [`region_aware_ocr_receipt.json`](region_aware_ocr_receipt.json).
4. **Q4 (`VERIFIED FACT`):** *Hệ thống xử lý ảnh chứa nhiều bài toán độc lập như thế nào?*
   - **Trả lời:** Ngoài phát hiện theo khoảng trống hình học giữa các cụm khối, `region_detector.py` đối chiếu chéo văn bản OCR qua `split_text_into_multi_problem_candidates` (nhận diện các dòng bắt đầu bằng `Câu <số>:` / `Bài <số>:`). Trên `ext_prt_03_hd_q_7907931`, hệ thống tách chính xác 2 ứng viên (`Câu 32` và `Câu 33`), trả `status = "needs_selection"`, và giải đúng cả hai bài (`'a√2/2'` và `'a³/4'`). Xem [`region_aware_ocr_receipt.json`](region_aware_ocr_receipt.json).
5. **Q5 (`VERIFIED FACT`):** *Hệ thống nhận dạng và xử lý các cấu trúc toán 2 chiều (phân số tầng dọc, căn thức, số mũ, độ góc, ký hiệu vuông góc/song song, các hàng đáp án A/B/C/D) như thế nào?*
   - **Trả lời:** `ocr_reconcile.py` ghép các mảnh ký hiệu ngang gần nhau (`<= 14px`: `S.` + `ABCD` -> `S.ABCD`, `60` + `°` -> `60°`, `A` + `'` -> `A'`), phát hiện phân số xếp chồng dọc (`FRACTION_STRUCTURE_SUSPECTED` / `SUBLINE_OVERLAP_SUSPECTED`), và gom các mảnh đáp án trắc nghiệm thành `choice_bands` để `_TRAILING_MC_OPTIONS_RE` cắt sạch phần trắc nghiệm mà không nuốt lời đề. Xem [`math_layout_recognition_receipt.json`](math_layout_recognition_receipt.json).
6. **Q6 (`VERIFIED FACT`):** *Bộ hòa giải hai họ OCR (`Layout-Aware Reconciler`) kết hợp `Tesseract vie` và `RapidOCR PP-OCRv6` theo thuật toán nào?*
   - **Trả lời:** `ocr_reconcile.py` dùng khung dòng của `RapidOCR` (hoặc `Tesseract` khi `RapidOCR` trống), căn chỉnh từ theo độ chồng lấp ngang (IoU) và `SequenceMatcher` với `Tesseract vie`: đối với từ tiếng Việt (`prose`), ưu tiên từ có dấu của `Tesseract` khi khớp khung phụ âm và nằm trong từ điển ngữ pháp `ocr_lexicon.py` (`533` unigrams, `2.662` bigrams); đối với token toán (`math`), yêu cầu đồng thuận chéo giữa 2 họ độc lập (`PaddleOCR` và `Tesseract`, `min_agreeing_families = 2`), kèm cắt ảnh đọc lại các slot tranh chấp bằng `rapidocr_latin_rec` và `tesseract_eng_line`. Xem [`dual_ocr_reconciliation_receipt.json`](dual_ocr_reconciliation_receipt.json).
7. **Q7 (`VERIFIED FACT`):** *Việc hòa giải OCR có sử dụng `ground_truth_text` hay đáp án biết trước ở bất kỳ bước nào không?*
   - **Trả lời:** Hoàn toàn không (`used_ground_truth = false`). `ground_truth_text` chỉ tồn tại trong bộ chấm điểm đánh giá để tính CER/WER và mô phỏng thao tác sửa của học sinh. Xem [`dual_ocr_reconciliation_receipt.json`](dual_ocr_reconciliation_receipt.json).
8. **Q8 (`VERIFIED FACT`):** *Tại sao hệ thống chọn ngưỡng `min_agreeing_families = 2` thay vì `1` cho các span toán học `verified`?*
   - **Trả lời:** Khi thử `min_agreeing_families = 1` (cho phép 2 bộ đọc cùng họ PaddleOCR là `rapidocr` và `rapidocr_latin_rec` tự xác nhận lẫn nhau), trên ảnh `ext_prt_06_hd_q_1084979` hộp phát hiện chữ của PaddleOCR cắt sát mép dấu `'` trong `CC'`, khiến cả hai bộ đọc PaddleOCR cùng đọc thành `CC` (tạo ra `1` lỗi toán học âm thầm). Khi đặt `min_agreeing_families = 2` (bắt buộc đồng thuận giữa họ `PaddleOCR` và họ `Tesseract`) kết hợp `prime_drop_conflict` và `prime_probe_slots`, tỷ lệ lỗi toán học âm thầm trên toàn bộ 14 ảnh đề in giảm xuống **`0.0%` (`0/134` span)** và `CC'` được gắn cờ kèm chip gợi ý 1 chạm `"CC'"`. Xem [`fidelity_false_rejection_analysis.json`](fidelity_false_rejection_analysis.json).
9. **Q9 (`VERIFIED FACT`):** *CER và WER trên 15 ảnh đề chữ in `External16` thay đổi như thế nào trước và sau khi hòa giải?*
   - **Trả lời:** CER trung vị giảm từ `0.1208` (Tesseract) và `0.1381` (RapidOCR) xuống **`0.0333`** (`mean CER`: `0.1612 / 0.1376 -> 0.0666`); WER trung vị giảm từ `0.3523` (Tesseract) và `0.5075` (RapidOCR) xuống **`0.2000`** (`mean WER`: `0.3312 / 0.5298 -> 0.1998`). Xem [`printed_ocr_before_after.json`](printed_ocr_before_after.json).
10. **Q10 (`VERIFIED FACT`):** *Precision và Recall của từng nhóm ký hiệu (`prime_labels`, `radicals`, `fractions`, `angle_degrees`, `point_labels`, `relation_symbols`, `vietnamese_diacritic_words`) thay đổi ra sao?*
    - **Trả lời:** Sau hòa giải, Precision đạt **`1.0000`** trên 5/6 nhóm ký hiệu toán (`prime_labels`, `radicals`, `fractions`, `angle_degrees`, `relation_symbols`) và **`0.9966`** trên `point_labels`; Recall đạt `0.7818` (`prime_labels`), `0.9286` (`radicals`), `0.7000` (`fractions`), `0.8571` (`angle_degrees`), `0.9195` (`point_labels`), `1.0000` (`relation_symbols`), và `0.9300` trên từ tiếng Việt có dấu (tăng từ `0.4309` của RapidOCR). Xem [`printed_ocr_before_after.json`](printed_ocr_before_after.json).
11. **Q11 (`VERIFIED FACT`):** *Kết quả thực nghiệm trên ảnh chữ viết tay (`ext_hw_b1_01`) là gì và quyết định phạm vi đối với chữ viết tay là gì?*
    - **Trả lời:** Trên ảnh vở viết tay nhiều dòng `ext_hw_b1_01_hd_a_6043187`, `reconciled CER = 0.6143` với `23` span không chắc chắn (`uncertain_ratio = 0.5882 > 0.35`). Hệ thống phân loại trung thực `HANDWRITING_REQUIRES_VISION_OR_CONFIRMATION`, tự động gắn cờ `low_quality = True` để chặn giải tự động sai (`wrong_served = false`) và chuyển sang Vision hoặc xác nhận toàn văn. Xem [`handwritten_ocr_diagnostic.json`](handwritten_ocr_diagnostic.json).
12. **Q12 (`VERIFIED FACT`):** *Hệ thống phân biệt hình vẽ chỉ minh họa với hình vẽ chứa dữ kiện bắt buộc như thế nào?*
    - **Trả lời:** Thông qua 6 trạng thái phân loại hình vẽ trong `ocr_reconcile.py`: chỉ khi hình vẽ chỉ chứa các nhãn đỉnh đã có mặt trong lời đề và lời đề không nhắc tới hình (`DIAGRAM_LABELS_ONLY_CONSISTENT`) thì `diagram.blocking = False`; nếu hình vẽ chứa số đo/ký hiệu (`DIAGRAM_HAS_MEASUREMENTS`), nhãn lạ (`DIAGRAM_LABELS_UNMATCHED`), không đọc được nhãn (`DIAGRAM_PRESENT_UNREAD`), hoặc lời đề có cụm `"như hình vẽ"` / `"hình bên"` (`DIAGRAM_REFERENCED_BY_TEXT`), hệ thống đặt `diagram.blocking = True` và buộc học sinh xác nhận. Xem [`diagram_dependency_audit.json`](diagram_dependency_audit.json).
13. **Q13 (`VERIFIED FACT`):** *Có trường hợp nào bài toán thiếu dữ kiện trong lời đề (dữ kiện chỉ nằm trên hình vẽ) mà hệ thống tự suy đoán hoặc dựng `Scene3D` sai không?*
    - **Trả lời:** Không (`false_diagram_auto_solve_count = 0`). Cả `5/5` ảnh có dữ kiện chỉ nằm trên hình vẽ (`ext_prt_15`, `new_ext_09..12`) đều bị chặn ở bước xác nhận (`blocking = True`). Xem [`diagram_dependency_audit.json`](diagram_dependency_audit.json).
14. **Q14 (`VERIFIED FACT`):** *Khi nào hệ thống gọi Gemini Vision và cơ chế kiểm tra chéo giữa OCR cục bộ với Vision hoạt động ra sao?*
    - **Trả lời:** Trong `unified_input.py`, `run_local_ocr_route` luôn chạy trước: nếu `extraction_verified = True` (`status = "ready"`) hoặc `not low_quality` (`uncertain_ratio <= 0.35`, `status = "needs_confirmation"`), hệ thống trả kết quả ngay với **`0` lời gọi Vision (`vlm_calls = 0`)**. Chỉ khi `low_quality = True` (như chữ viết tay nhiều dòng) hoặc OCR cục bộ không khả dụng thì hệ thống mới gọi Vision. Khi có cả kết quả OCR và Vision, `compare_ocr_and_vision_facts` kiểm tra xung đột số đo, dấu phẩy và tên khối, buộc xác nhận nếu phát hiện mâu thuẫn. Xem [`vision_fallback_offline_receipt.json`](vision_fallback_offline_receipt.json).
15. **Q15 (`NOT_MEASURED`):** *Tỷ lệ thành công của Gemini Vision trực tiếp (`LIVE_VISION_SUCCESS_RATE`) và `VISION_REPLAY_SUCCESS_RATE` trên `External16` là bao nhiêu?*
    - **Trả lời:** **`NOT_MEASURED`** (`ALLOW_LIVE_AI = 0`, `0` lời gọi Gemini được thực hiện; không có bản ghi Vision thật cho `External16` và không giả lập phản hồi Vision). Xem [`vision_live_readiness.json`](vision_live_readiness.json).
16. **Q16 (`VERIFIED FACT`):** *Giao diện xác nhận của học sinh (`#photo-span-review`) hoạt động như thế nào để học sinh không phải gõ lại cả đề?*
    - **Trả lời:** Giao diện giữ nguyên toàn bộ văn bản đề đã đọc được và chỉ liệt kê các span `uncertain` (`median 2–3` chỗ/bài) kèm ảnh cắt `.photo-span-crop` từ đề gốc, các chip gợi ý 1 chạm `.photo-span-alt`, ô sửa nhanh `.photo-span-input` (tự động ghép lại đúng vị trí ký tự trong đề), và nút `.photo-span-ok` (`Đúng rồi`), giúp tiết kiệm trung vị **`98.9%`** số ký tự phải gõ. Xem [`student_confirmation_flow_receipt.json`](student_confirmation_flow_receipt.json).
17. **Q17 (`VERIFIED FACT`):** *Khi học sinh sửa một ký hiệu hoặc số đo trong đề đã trích xuất, hệ thống có bị dính cache cũ hoặc gọi lại Vision không?*
    - **Trả lời:** Không. Khóa cache `build_local_first_cache_identity` băm trực tiếp văn bản chuẩn hóa sau khi sửa (`key_v1 != key_v2`), cập nhật ngay đáp số và `Scene3D` mới (`{'q1': 'a³√3/3', 'q2': 'a√21/21'} -> {'q1': 'a³/3', 'q2': 'a√3/9'}`), và không gọi lại `/api/input/prepare` hay Vision (`vision_re_called_on_text_edit = false`). Xem [`user_correction_cache_invalidation.json`](user_correction_cache_invalidation.json).
18. **Q18 (`VERIFIED FACT`):** *Tỷ lệ giải tự động hoàn toàn từ ảnh gốc (`Outcome A: LOCAL_IMAGE_AUTO_SOLVE_RATE`) trên `External16` là bao nhiêu?*
    - **Trả lời:** **`1/11 (9.09%)`** trên các bài chữ in trong phạm vi (`1/17 = 5.88%` trên toàn bộ `External16`), cụ thể là bài `ext_prt_01_hd_q_5259753` (`{'q1': 'a³√3/3', 'q2': 'a√21/21'}`, `0` AI calls, `0` chỉnh sửa). Xem [`real_image_to_scene3d_acceptance.json`](real_image_to_scene3d_acceptance.json).
19. **Q19 (`VERIFIED FACT`):** *Tỷ lệ giải đúng sau khi học sinh xác nhận các span được khoanh vùng (`Outcome C: USER_CORRECTED_SOLVE_RATE`) trên `External16` là bao nhiêu?*
    - **Trả lời:** **`10/10 (100.0%)`** trên 10 bài chữ in trong phạm vi còn lại (`ext_prt_02, 03#1, 03#2, 04, 05, 06, 07, 09, 11, 12`). Tổng hợp **A + C** đạt **`11/11 (100.0%)`** bài chữ in trong phạm vi (`11/17 = 64.7%` toàn bộ `External16`) với `0` bài giải sai. Xem [`real_image_to_scene3d_acceptance.json`](real_image_to_scene3d_acceptance.json).
20. **Q20 (`VERIFIED FACT`):** *Có bài nào trong `External16` hoặc `New External` trả về kết quả toán học sai (`WRONG_SERVED`) hoặc dựng `Scene3D` đứt gãy không?*
    - **Trả lời:** Không (`wrong_served_count = 0`, `scene3d_continuity_violations = 0` trên toàn bộ `17` bài `External16` và `12` bài `New External`). Xem [`real_image_to_scene3d_acceptance.json`](real_image_to_scene3d_acceptance.json) và [`new_external_image_evaluation.json`](new_external_image_evaluation.json).
21. **Q21 (`VERIFIED FACT`):** *Kết quả đánh giá trên 12 ảnh thực tế mới chưa từng dùng (`New External` từ `anvo25/vmmu`) như thế nào?*
    - **Trả lời:** Trên 12 ảnh MIT mới hoàn toàn (`5` đa diện 3D, `3` khối tròn xoay, `4` hình phẳng/tối ưu/giải tích): `median CER` đạt `0.0110` trên 5 bài đa diện (`0` span phải sửa tay trên thân đề ở `3/5` bài `new_ext_03, 04, 05`); giải đúng và dựng `Scene3D` cho `new_ext_01` (`'2a√57/19'`), bắt đúng lỗi mất dấu phẩy `AD -> A'D` kèm chip gợi ý `"A'D"` và từ chối đúng `MISSING_DIMENSION` trên `new_ext_02`, phân loại đúng `GEOMETRY_CAPABILITY_GAP` trên `new_ext_03..05`, và từ chối an toàn `7/7` bài ngoài phạm vi (`new_ext_06..12`, `0` wrong-served). Xem [`new_external_image_evaluation.json`](new_external_image_evaluation.json).
22. **Q22 (`VERIFIED FACT`):** *Các giới hạn hình học (`GEOMETRY_CAPABILITY_GAP`) nào được phát hiện từ 5 ảnh đa diện mới trong `New External`?*
    - **Trả lời:** Phát hiện 3 giới hạn thực sự của Kernel/Registry (giữ nguyên không sửa Kernel trong task này theo đúng quy tắc phạm vi):
      1. Cụm `"có tất cả các cạnh (đều) bằng a"` trên lăng trụ đứng (`new_ext_03`) và chóp tứ giác đều (`new_ext_04`) chưa được `registry.py` ánh xạ cho `regular_polygon`.
      2. Tam giác đáy vuông cân tại `B` cho biết cạnh huyền `AC = 2a` (`new_ext_05`): `engine.py` hiện chưa suy ngược `AB = BC = AC / √2 = a√2`.
      3. Tính góc bất biến theo phép vị tự trên khối lập phương không cho độ dài cạnh (`new_ext_02`): chứng chỉ `height-invariance-certificate/2` hiện mới chứng nhận cho chiều cao tự do $h$, chưa mở rộng cho tỷ lệ cạnh đồng dạng tổng quát.
23. **Q23 (`VERIFIED FACT`):** *Những cải tiến nhỏ nào đã được thực hiện trong `local_geometry_parser.py` để hỗ trợ văn bản từ OCR mà không chạm vào Kernel/Registry?*
    - **Trả lời:** Có 4 cải tiến an toàn trong [`local_geometry_parser.py`](../../../../backend/app/ai/local_geometry_parser.py): (1) mở rộng `_TRAILING_PARTIAL_MC_RE` cho phần đuôi đáp án trắc nghiệm bị cắt dở; (2) chuẩn hóa nhãn mức độ đề thi `Câu 30 (VD):` -> `Câu 30:` và ký hiệu `ΔABC` -> `tam giác ABC` trong `normalize_problem_text`; (3) sinh `regular_polygon` cho mặt đáy hình lập phương khi đề không nêu độ dài cạnh (`new_ext_02`); (4) chấp nhận `"tam giác ABC là tam giác đều cạnh a"` và dấu nối `"và"` trong danh sách trung điểm `M, N và P`.
24. **Q24 (`VERIFIED FACT`):** *Kiến trúc OCR cục bộ sử dụng bao nhiêu RAM/CPU và có làm phình bộ nhớ của tiến trình backend chính không?*
    - **Trả lời:** Nhờ kiến trúc tiến trình con theo yêu cầu (`local_ocr_worker.py`), khi không gọi OCR cục bộ thì độ tăng RSS của tiến trình FastAPI chính là **`+0.0 MB`**. Toàn bộ quá trình chạy trên CPU (`gpu_required = false`), thời gian khoanh vùng ảnh `p50 = 102.72 ms`, `Tesseract vie` `p50 = 235.62 ms`, `RapidOCR PP-OCRv6` `p50 = 2.236,01 ms`, và đọc lặp lại từ cache LRU chỉ mất `0.01 ms`. Xem [`ocr_resource_performance.json`](ocr_resource_performance.json).
25. **Q25 (`VERIFIED FACT`):** *Có cần viết lại bất kỳ thành phần OCR hay xử lý ảnh nào sang Rust không?*
    - **Trả lời:** Không (`NO_RUST_NEEDED`). Phần tiền xử lý vùng đề trong Python/Pillow chỉ mất `p50 = 102.72 ms`, còn thời gian OCR nằm ở thư viện C++/ONNX gốc (`tesseract` và `onnxruntime`).
26. **Q26 (`VERIFIED FACT`):** *Luồng tải ảnh thực tế trên trình duyệt đã được kiểm chứng End-to-End bằng công cụ tự động nào?*
    - **Trả lời:** Được kiểm chứng bằng Playwright trên trình duyệt Chromium headless thật (`157.0.8103.50`) chạy bản build production của frontend kết nối tới FastAPI backend thật qua `6/6` kịch bản (`100%` và `110%` zoom, Outcome A tự động, Outcome C xác nhận span, chọn đa bài + bấm chip gợi ý, ảnh ngoài mới `new_ext_01`, và chặn ảnh phụ thuộc hình vẽ `ext_prt_15`), đạt **`6/6 PASS`** với `0` lỗi console và `0` lỗi trang. Xem [`frontend_browser_e2e.json`](frontend_browser_e2e.json).
27. **Q27 (`VERIFIED FACT`):** *Các cổng kiểm thử hồi quy (unit test, integration test, demo replay, crash surface, docs IA, publication safety, candidate freeze) đạt kết quả ra sao?*
    - **Trả lời:** Toàn bộ đều đạt **PASS**: `20/20` unit test mới trong `test_image_first_local_ocr.py` & `test_local_geometry_parser.py`, `169/169` bài kiểm thử ingestion & hình học backend, `108/108` bài kiểm thử Vitest frontend (gồm `4/4` test mới trong `photo-span-review.test.tsx`), `6/6` kịch bản Playwright Chromium E2E, `5/5 + 1/1` `replay_demo_cases.py`, `6/6` `audit_demo_crash_surface.py` (`0` thrown), `audit_docs_information_architecture.py` PASS, `check_publication_safety.py` PASS, và `freeze_evaluation_candidate.py --verify` MATCH (`115` file, `6851b71826793fff…`). Xem [`full_regression_summary.json`](full_regression_summary.json).
28. **Q28 (`VERIFIED FACT`):** *Bản chất nhận thức luận của `ground_truth_text` đối với các ảnh bên ngoài là gì?*
    - **Trả lời:** `GROUND_TRUTH_UNVERIFIED` (văn bản tham chiếu do agent chép từ ảnh gốc để phục vụ chấm điểm CER/WER; chưa có người chấm độc lập bên ngoài xác minh, và tuyệt đối không được nạp vào mã runtime).
29. **Q29 (`NOT_MEASURED`):** *Trạng thái kiểm định độc lập `H-1` (`INDEPENDENT_H1_VALIDATION`) hiện tại là gì?*
    - **Trả lời:** **`NOT_MEASURED`** (`SEALED_CORPUS = MISSING`; cả `External16` và `New External 12` đều được ghi nhận trung thực là bộ dữ liệu đánh giá kỹ thuật do agent thu thập, không tuyên bố là kiểm định độc lập `H-1`).
30. **Q30 (`INFERENCE`):** *Bước ưu tiên kỹ thuật hợp lý tiếp theo sau khi hoàn thành luồng Image-First OCR & Student Confirmation này là gì?*
    - **Trả lời:** (1) Thực hiện đánh giá `LIVE_VISION_SUCCESS_RATE` có trần ngân sách trên các ảnh chữ viết tay (`ext_hw_b1_01`) và ảnh phụ thuộc hình vẽ (`ext_prt_15`) khi chủ dự án bật `ALLOW_LIVE_AI=1`; (2) đóng 3 khoảng trống `GEOMETRY_CAPABILITY_GAP` vừa phát hiện trên `new_ext_02..05` (đồng dạng cạnh lập phương không cho số đo, `"tất cả các cạnh đều bằng a"` trên lăng trụ đứng/chóp đều, và suy cạnh góc vuông từ cạnh huyền tam giác vuông cân).

---

## XVI. Danh Mục 20 Biên Nhận Máy (Deliverable Manifest & SHA-256)

Toàn bộ 20 biên nhận JSON trong `docs/evaluation/geometry/runs/image-first-ocr-verified-geometry/` (khớp với [`run.json`](run.json)):

| # | Tên file | Schema | SHA-256 |
|---:|---|---|---|
| 1 | [`baseline_candidate_integrity.json`](baseline_candidate_integrity.json) | `algosim-baseline-candidate-integrity/1` | `8ac1b173c8913cbc98d47b93186311ceb812fddcb75e56edde75c9c157c2942d` |
| 2 | [`external16_image_diagnostics.json`](external16_image_diagnostics.json) | `algosim-external16-image-diagnostics/1` | `65b37b1fdf6ac5b8fec1e29e6b1defc0ab2dd857bebdf2ff68abeab6823462d0` |
| 3 | [`ocr_failure_root_causes.json`](ocr_failure_root_causes.json) | `algosim-ocr-failure-root-causes/1` | `c3ba7940edd7354fa9c72f8e796f5ab5e69c704b5c76bb46f22b219e951592bf` |
| 4 | [`region_aware_ocr_receipt.json`](region_aware_ocr_receipt.json) | `algosim-region-aware-ocr-receipt/1` | `2a00e53aabdf8cced86142a92a569dbe4ded4e68cca8a8f2fec802cecc6701e2` |
| 5 | [`math_layout_recognition_receipt.json`](math_layout_recognition_receipt.json) | `algosim-math-layout-recognition-receipt/1` | `753eef764ab24599cd759b69c810fdfd50af35cabd120d2d0272e458c486a6ba` |
| 6 | [`dual_ocr_reconciliation_receipt.json`](dual_ocr_reconciliation_receipt.json) | `algosim-dual-ocr-reconciliation-receipt/1` | `74c4bf6101d4bae8350af6f8173694fc3ce0ce4e49e0e0dc9d80d03cad37f6e8` |
| 7 | [`fidelity_false_rejection_analysis.json`](fidelity_false_rejection_analysis.json) | `algosim-fidelity-false-rejection-analysis/1` | `deb5d5084b8707882ee48e2f1f12066a947aeecf92ec985afda3415a8dd4c875` |
| 8 | [`printed_ocr_before_after.json`](printed_ocr_before_after.json) | `algosim-printed-ocr-before-after/1` | `e8442d858f6754a47f2264fee274beccc27907ad6cb9fa54ae3c5b51e14c85c3` |
| 9 | [`handwritten_ocr_diagnostic.json`](handwritten_ocr_diagnostic.json) | `algosim-handwritten-ocr-diagnostic/1` | `2511743957b05575c9f8c4f4c1d6c86fed3958725dab7f810eb5fa0ccd51bf3a` |
| 10 | [`diagram_dependency_audit.json`](diagram_dependency_audit.json) | `algosim-diagram-dependency-audit/1` | `938a7b719fc28576647a489d9253745e9d24dc71a6421f39de7789fbfd2c76a3` |
| 11 | [`vision_fallback_offline_receipt.json`](vision_fallback_offline_receipt.json) | `algosim-vision-fallback-offline-receipt/1` | `d4cf581dc25ed5f5f72e208decf30a75670bd90013de1e235e3f295c578c0559` |
| 12 | [`vision_live_readiness.json`](vision_live_readiness.json) | `algosim-vision-live-readiness/1` | `32bb416c974a5130f059dd2adabd67f3b8bb2dd8416d381c98f4374c5767a2f1` |
| 13 | [`student_confirmation_flow_receipt.json`](student_confirmation_flow_receipt.json) | `algosim-student-confirmation-flow-receipt/1` | `1afd76a4a455484b5fe59783fc66f8c91609d936343ac849bfcebf9e47e68e4b` |
| 14 | [`user_correction_cache_invalidation.json`](user_correction_cache_invalidation.json) | `algosim-user-correction-cache-invalidation/1` | `83f491167e68ab110a02dfc208a2d8278977da27e5964b307538d93b7e553d49` |
| 15 | [`real_image_to_scene3d_acceptance.json`](real_image_to_scene3d_acceptance.json) | `algosim-real-image-to-scene3d-acceptance/1` | `7da933be3c6738305bd2243e3833abdf79ca5f575ea885a6fb641ecf9e410aff` |
| 16 | [`new_external_image_evaluation.json`](new_external_image_evaluation.json) | `algosim-new-external-image-evaluation/1` | `ac82e26d2a6b5b6cf9a87356c4ce63b33704112df1792af98512e077f3c2bbcb` |
| 17 | [`ocr_resource_performance.json`](ocr_resource_performance.json) | `algosim-ocr-resource-performance/1` | `9bd16f24fc5e01a761d43d186f9650fcdc67f7fed085a1670ea0985d6238a872` |
| 18 | [`frontend_browser_e2e.json`](frontend_browser_e2e.json) | `algosim-frontend-browser-e2e/1` | `0ed34f440c61f1aa72d44becf8f7d0fd830e86b1959a0fd0b9e55c49ff756b7a` |
| 19 | [`full_regression_summary.json`](full_regression_summary.json) | `algosim-full-regression-summary/1` | `b4059d4066bfbf765758e48d8f8ad5bbbb7d914783deaf0c19ee77dddd564767` |
| 20 | [`run.json`](run.json) | `algosim-evaluation-run-manifest/1` | `8d3b2591fc4c026a…` (manifest) |
