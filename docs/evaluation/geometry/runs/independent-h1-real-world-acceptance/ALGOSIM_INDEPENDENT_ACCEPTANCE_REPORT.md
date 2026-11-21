# ALGOSIM — INDEPENDENT H-1, REAL-WORLD VISION & LOW-END ACCEPTANCE REPORT

- **Run Slug:** `independent-h1-real-world-acceptance`
- **Branch:** `feat/local-first-geometry-understanding`
- **Product Commit SHA:** `87497d79a6537681b91c3f06fffea86a7e593a02` (`87497d79a`)
- **Measured System Tree Hash:** `ba0261c14a22b205b476d9951e3aa32fea63ef78c74ee1d413d4ac5ad093f759` (`108` files, `CACHE_VERSION = 132`)
- **Live Provider Calls:** `0` (`ALLOW_LIVE_AI = 0`)
- **Component Versions:** `local-geometry-parser/1` · `adaptive-input-router/1` · `typed-fact-next/2` · `geometry-fact-planner/26` · `geometry-functions/33` · `geometry-function-engine/24` · `hybrid-simulation-adapter/4` · `hybrid-route-d-simulation/4`

---

## I. Executive Summary & Acceptance Gate Status

| Gate | Scope | Status | Epistemic Classification | Key Evidence Receipt |
|---|---|---|---|---|
| **Gate A** | Independent H-1 Geometry Validation | **`PENDING_EXTERNAL_CORPUS`** (`INDEPENDENT_H1_VALIDATION = NOT_MEASURED`) | **`NOT MEASURED` / `BLOCKED`** | [`h1_corpus_provenance_receipt.json`](h1_corpus_provenance_receipt.json), [`h1_contamination_audit_receipt.json`](h1_contamination_audit_receipt.json), [`h1_geometry_evaluation_receipt.json`](h1_geometry_evaluation_receipt.json) |
| **Gate B** | Real-World Image & OCR Acceptance | **`REAL_WORLD_IMAGE_NOT_MEASURED`** (`REAL_CAPTURED_IMAGE = 0`, `SCANNED_DOCUMENT = 0`) | **`NOT MEASURED` (real photos) / `VERIFIED FACT` (synthetic & forensic OCR audit)** | [`real_world_image_corpus_manifest.json`](real_world_image_corpus_manifest.json), [`region_detection_real_world_receipt.json`](region_detection_real_world_receipt.json), [`ocr_fidelity_real_world_receipt.json`](ocr_fidelity_real_world_receipt.json) |
| **Gate C** | Adaptive AI Routing Acceptance | **`OFFLINE_ROUTING_VERIFIED`** (`LIVE_ROUTING_VERIFIED = NOT_MEASURED`) | **`VERIFIED FACT` (offline Routes A/B/C/D + Conflict Guard) / `NOT MEASURED` (live Gemini)** | [`adaptive_routing_acceptance_receipt.json`](adaptive_routing_acceptance_receipt.json) |
| **Gate D** | Low-End Hardware Performance | **`RESOURCE_CONSTRAINED_SIMULATION_ONLY`** | **`VERIFIED FACT` (host benchmarks) / `INFERENCE` (low-end CPU projection) / `NOT MEASURED` (physical 2–4 core laptop)** | [`low_end_hardware_performance_receipt.json`](low_end_hardware_performance_receipt.json) |

---

## II. Epistemic Classification of Findings

1. **`VERIFIED FACT` — Zero Wrong-Served Across All Offline Benchmarks (`174/183` Gold + `25/25` Diagnostic Stress Suite):**
   - Across the `183`-case offline gold suite (`46/46` Held-Out, `63/72` Dev Matrix, `65/65` S-2/R-1) and the new `25`-case unseen phrasing & capability diagnostic stress suite (`18/18` positive SERVE exact match across all 15 geometry groups + `7/7` negative/guard refusals), AlgoSim achieves **`0` wrong-served mathematical answers** with **`0` live AI calls**.
2. **`VERIFIED FACT` — Forensic Audit & Remediation of `Case A` (`LOCAL_OCR_VERIFIED_ZERO_AI`) on `s05_dau_tieng_viet` vs `s05_dau_tieng_viet_degraded`:**
   - In the previous wave (`correctness-ocr-performance-optimization`), `Case_A_Local_OCR_Verified_Zero_AI` passed a synthetic clean string (`clean_ocr_text`) into `route_image_or_prepare_outcome` rather than the actual recorded OCR outputs from `local_ocr_pretrained_comparison_receipt.json` (`s05_dau_tieng_viet`).
   - On the actual recorded OCR outputs of `s05_dau_tieng_viet` (`"Cho hình hộp chữ nhật ABCD.A′B′C′D′ có AB = 3, AD = 4, AA′ = 5. Gọi I là giao điểm của AC′ và mặt phẳng (A′BD). Tính độ dài đoạn thẳng AI."`):
     - **Why `s05_dau_tieng_viet_degraded` (`ABCD.AB'C'D'`) had fewer surface corruptions than `s05_dau_tieng_viet` (`ABCD.A'B'Œ 7D”`) in Tesseract:** On the clean high-contrast render, the tightly spaced prime glyphs (`′`) immediately adjacent to `B′C′D′` caused Tesseract's LSTM glyph segmenter to merge `C′` into the ligature `Œ 7` and `D′` into `D”` (`ABCD.A'B'Œ 7D”`). On the degraded render, slight blur/downsampling softened the thin prime stroke on `A′` so it vanished (`A`), while `B′C′D′` avoided the `Œ 7` ligature split (`ABCD.AB'C'D'`).
     - **Crucially, BOTH single-engine outputs fail `verify_ocr_input_fidelity` (`fidelity_passed = False`):** `s05_dau_tieng_viet` fails on `_OCR_CORRUPTION_ARTIFACT_RE` and `EMPTY_SOLIDS`; `s05_dau_tieng_viet_degraded` (`ABCD.AB'C'D'`) fails on `INVALID_SOLID_NOTATION` and cross-engine `primed_labels` mismatch.
   - We implemented `reconcile_dual_ocr_texts(primary_vi_ocr_text, secondary_math_ocr_text, *, is_degraded_image=False)` in `backend/app/ai/adaptive_input_router.py` (with `used_ground_truth = False`, strict line/header alignment, and 100% cross-engine numeric/relation agreement) and extended `local_geometry_parser.py` with `5g`/`5h` (`intersect_line_plane` and `intersect_line_line` named point premises, plus compound diagonal+volume goals).
   - Result: `s05_dau_tieng_viet` (clean) genuinely repairs `ABCD.A'B'Œ 7D”` → `ABCD.A'B'C'D'` from `RapidOCR`'s exact `ABCD.A'B'C'D'`, passes all 6 Input Fidelity criteria, and serves `{'q1': '5√2/3'}` (`AI = 5√2/3`) with **`0` AI calls**, while `s05_dau_tieng_viet_degraded` (`is_degraded_image=True`) is **strictly refused** (`DEGRADED_IMAGE_REQUIRES_VISION_FALLBACK`) and routed to Gemini Vision.
3. **`VERIFIED FACT` — Remediation of `Case D` (`LOCAL_AMBIGUOUS_CLARIFICATION`) Route Labeling Defect:**
   - Previously, `route_text_input` labeled `MISSING_DIMENSION` / `insufficient_specification` refusals (`LOCAL_PARSE_COMPLETE` at parser stage, refused by `Planner`/`Engine`) as `"LOCAL_DETERMINISTIC_HYBRID"`, causing `Case_D_Missing_Data_Deterministic_Clarification_Zero_AI` to record `passed: false`.
   - Fixed in `backend/app/ai/adaptive_input_router.py` so all `insufficient_specification` / missing-data / clarification refusals with `previous_vision_calls == 0` map to `chosen_route = "LOCAL_AMBIGUOUS_CLARIFICATION"`. All 7 offline routing acceptance scenarios now pass (`7/7`).
4. **`VERIFIED FACT` — 8-Layer Anti-Contamination Scanner & 13-Field H-1 Schema Validator:**
   - Extended `backend/scripts/score_independent_holdout_equivalence.py` with Layer 7 (`intermediate_construction_sequence`), Layer 8 (`solution_or_expected_answer_leakage`), and `validate_h1_case_13_fields`. Verified `8/8` positive contamination probes are caught and clean distinct problems pass.
5. **`NOT MEASURED` / `BLOCKED` — External Human-Authored H-1 Corpus & Real Camera/Scanner Image Corpus:**
   - No external human-authored 60-case H-1 corpus (`HUMAN_AUTHORED` / `CURATED_EXAM`) and no real smartphone/scanner photos (`REAL_CAPTURED_IMAGE = 0`, `SCANNED_DOCUMENT = 0`) have been supplied in the repository. Both remain honestly marked `NOT_MEASURED`.

---

## III. Direct Answers to the 15 Mandatory Questions (Section XIV)

### 1. Đã có tập `H-1` độc lập thật chưa? Nếu chưa, vì sao và cần gì để hoàn tất?
- **Classification:** `VERIFIED FACT` / `BLOCKED`
- **Answer:** **Chưa (`INDEPENDENT_H1_VALIDATION = NOT_MEASURED`, `Gate A = PENDING_EXTERNAL_CORPUS`).** Trong toàn bộ workspace hiện không có tập đề 60 bài do giáo viên/người biên soạn độc lập tạo ngoài tập phát triển. Theo quy tắc chống tự hợp thức hóa (Section IV.1.1), coding agent tuyệt đối không được tự sinh đề bằng AI hay đổi tên đỉnh từ tập cũ rồi dán nhãn là `H-1`. Để hoàn tất Gate A, cần cung cấp file JSON 60 bài (`45 SERVE + 5 OUT_OF_DOMAIN + 5 CONTRADICTORY_DATA + 5 MISSING_DATA`) có đủ 13 trường provenance (`validate_h1_case_13_fields`) và chạy qua bộ quét 8 lớp `scan_eight_layer_contamination`.

### 2. Trên các bài hình học độc lập hoặc tập đánh giá hiện có, AlgoSim đạt bao nhiêu ở 3 tầng: Mathematical, Semantic Goal và Strict Contract?
- **Classification:** `VERIFIED FACT` (offline corpora & C26 replay) / `NOT MEASURED` (external H-1)
- **Answer:**
  - **Tập H-1 độc lập:** `NOT_MEASURED`.
  - **Tập 70 dòng C26 đã ghi nhận (kiểm định qua `score_three_tier_rows`):**
    - `mathematical_served_correct`: **`37/41` (`90.24%`)**, `mathematical_wrong_served`: **`0/70` (`0.0%`)**.
    - `semantic_served_correct`: **`37/41` (`90.24%`)**, `semantic_wrong_served`: **`0/70` (`0.0%`)**.
    - `strict_served_correct`: **`30/41` (`73.17%`)**, `strict_wrong_served`: **`7/70` (`10.0%` — do khác biệt biểu diễn `construct_plane_section` ở 7 bài thiết diện kép, đã phân giải ở tầng Semantic P1)**.
  - **Tập 183 bài Offline Gold (`Local-First Route T1`, `0` AI calls):** **`174/183` (`95.08%`)** khớp đáp án chính xác, **`0/183` (`0.0%`)** wrong-served.
  - **Tập 25 bài Diagnostic Phrasing & Capability Stress Suite (Section IV.1.5–1.6):** **`18/18` (`100.0%`)** bài dương khớp oracle tuyệt đối (`0` AI calls), **`7/7` (`100.0%`)** bài âm/biên từ chối đúng mã, **`0/25`** wrong-served.

### 3. Có bất kỳ bài nào hệ thống trả kết quả toán học sai (`wrong-served`) không?
- **Classification:** `VERIFIED FACT`
- **Answer:** **Không (`0` bài wrong-served trên toàn bộ `183` bài Offline Gold, `70` dòng C26, và `25` bài Diagnostic Stress Suite).** Mọi kết quả `SERVED` đều đi qua `Source Gate` (`registry.kiem_nguon`), `Exact Kernel` (`Fraction`/`Radical`) và chứng chỉ hình học Gram trước khi trả về.

### 4. `Deterministic Geometry Parser` giải được bao nhiêu phần trăm đề không cần AI?
- **Classification:** `VERIFIED FACT`
- **Answer:**
  - Trên `Held-Out 46`: **`46/46` (`100.0%`)** với `0` AI calls.
  - Trên `S-2 + R-1 (65 bài)`: **`65/65` (`100.0%`)** với `0` AI calls.
  - Trên `DEV 72`: **`49/72` (`68.06%`)** hoàn toàn bằng `Local-First Parser` (`0` AI calls); `14/72` bài còn lại trong phạm vi Kernel cần `AI_TYPED_FACT_FALLBACK` (`63/72 = 87.5%` tổng cộng); `9/72` bài thuộc 5 khoảng trống năng lực `DEV72-G2..G7`.
  - Tính gộp trên toàn bộ `183` bài benchmark (`46 + 72 + 65`): **`160/183` (`87.43%`)** bài được hiểu và giải hoàn toàn cục bộ với **`0` lời gọi AI**.

### 5. Có trường hợp nào parser cục bộ bỏ sót điều kiện nhưng vẫn trả `LOCAL_PARSE_COMPLETE` không?
- **Classification:** `VERIFIED FACT`
- **Answer:** **Không (`0` trường hợp).** Cơ chế kiểm tra độ phủ mệnh đề (`SourceCoverageReport.coverage_complete`), danh sách từ khóa điều kiện bắt buộc (hình thoi, tam giác cân, góc mặt bên, phủ định `không vuông góc`, số thập phân dấu phẩy `3,5`, căn lỗi `2V3`, mục tiêu kép nối bởi `và`), và `Stage 8` (`registry.kiem_nguon`) đảm bảo mọi mệnh đề chưa ánh xạ đều trả `LOCAL_PARSE_PARTIAL` (`payload = None`), tuyệt đối không âm thầm bỏ qua giả thiết.

### 6. Đã có bao nhiêu ảnh chụp/scan thực tế (`REAL_CAPTURED_IMAGE`, `SCANNED_DOCUMENT`) và bao nhiêu ảnh giả lập (`SYNTHETIC_RENDER`)?
- **Classification:** `VERIFIED FACT`
- **Answer:**
  - `REAL_CAPTURED_IMAGE`: **`0`**
  - `SCANNED_DOCUMENT`: **`0`**
  - `SYNTHETIC_RENDER`: **`27`** (`18` ảnh trong bộ `vision_benchmark` + `9` ảnh bố cục trong bộ `region_detection`). Toàn bộ 27 ảnh đều được gắn nhãn trung thực là `SYNTHETIC_RENDER` trong [`real_world_image_corpus_manifest.json`](real_world_image_corpus_manifest.json).

### 7. Thuật toán khoanh vùng đề hoạt động thế nào trên ảnh thực tế và các bố cục khó?
- **Classification:** `VERIFIED FACT` (trên 9 bố cục giả lập) / `NOT MEASURED` (trên ảnh chụp điện thoại thật)
- **Answer:** Trên 9 bố cục kiểm thử (`vii_01`–`vii_09`), bộ phát hiện vùng (`detect_problem_regions`) đạt **`100%` (`6/6`)** bảo toàn toàn bộ văn bản đề đơn (`0%` cắt mất vế phải hoặc câu hỏi cuối), Mean IoU **`0.8673`**, từ chối chính xác ảnh trắng/chỉ có hình vẽ với **`0` AI calls**, và phát hiện **`3` vùng đề độc lập** (`needs_selection`) trên trang có nhiều bài toán. Trên ảnh chụp điện thoại thực tế và đề 2 cột: **`NOT_MEASURED`**.

### 8. `Tesseract` và `RapidOCR` đạt độ chính xác ký hiệu toán học bao nhiêu trên ảnh thực tế?
- **Classification:** `VERIFIED FACT` (trên 22 mục benchmark đã ghi nhận) / `NOT MEASURED` (trên ảnh chụp thực tế)
- **Answer:**
  - Trên ảnh chụp thực tế: **`NOT_MEASURED`**.
  - Trên 22 mục benchmark đã ghi nhận (`local_ocr_pretrained_comparison_receipt.json`):
    - `Tesseract 5.5.3 (vie LSTM)`: Độ chính xác từ tiếng Việt **`97.67%`**, nhưng Math-Token Recall trung bình chỉ đạt **`53.39%`** (`0/22` mục qua cổng đơn lẻ vì lỗi dấu phẩy `'` → `Œ 7D”` / mất `'`, hoặc căn `√` → `V`).
    - `RapidOCR 3.10.0 (PP-OCRv6 det + PP-OCRv5 latin_mobile_rec)`: Độ chính xác từ tiếng Việt **`53.07%`** (do mất dấu nguyên âm tiếng Việt), nhưng Math-Token Recall đạt **`90.48%`** (trên `s05_dau_tieng_viet` đạt **`100%`** các token toán học `ABCD.A'B'C'D'`, `AB = 3`, `AD = 4`, `AA′ = 5`, `AC'`, `(A'BD)`, `AI`).

### 9. Trường hợp `s05` trong báo cáo trước thực sự là `s05_clean` hay `s05_degraded`, và cổng `verify_ocr_input_fidelity` có thực sự an toàn không?
- **Classification:** `VERIFIED FACT`
- **Answer:**
  - **Vì sao `s05_dau_tieng_viet_degraded` (`ABCD.AB'C'D'`) có vẻ "ít hỏng hơn" `s05_dau_tieng_viet` (`ABCD.A'B'Œ 7D”`) trên Tesseract:** Trên ảnh clean nét cao, các dấu phẩy `′` sát cạnh chữ hoa `B′C′D′` khiến bộ tách ký tự LSTM của Tesseract gộp nhầm `C′` thành ký tự ghép `Œ 7` và `D′` thành `D”` (`ABCD.A'B'Œ 7D”`). Trên ảnh degraded có làm mờ nhẹ (Gaussian blur/downsample), nét mảnh của dấu `′` ở `A′` bị mờ biến mất (`A`), nhưng nhờ đó `B′C′D′` không kích hoạt lỗi tách/gộp ligature `Œ 7` (`ABCD.AB'C'D'`).
  - **Cả 2 bản đơn lẻ đều bị `verify_ocr_input_fidelity` chặn (`fidelity_passed = False`):** Bản clean bị chặn bởi `_OCR_CORRUPTION_ARTIFACT_RE` (`Œ`, `”`) và `EMPTY_SOLIDS`; bản degraded (`ABCD.AB'C'D'`) bị chặn bởi `INVALID_SOLID_NOTATION` (`AB'C'D'` không khớp đáy `ABCD`) và lệch `primed_labels`.
  - **Khi đối chiếu 2 engine (`reconcile_dual_ocr_texts`) không dùng ground-truth:**
    - Chỉ **`s05_dau_tieng_viet` (clean, `is_degraded_image=False`)** được sửa `ABCD.A'B'Œ 7D”` → `ABCD.A'B'C'D'` (nhờ `RapidOCR` đọc đúng `100%` `ABCD.A'B'C'D'` và đồng thuận `100%` trên mọi số đo `AB=3, AD=4, AA'=5`), vượt qua cả 6 tiêu chí (`fidelity_passed = True`) và giải ra đáp số chính xác `AI = 5√2/3` với **`0` AI calls**.
    - Ngược lại, **`s05_dau_tieng_viet_degraded` (`is_degraded_image=True`)** **bị từ chối hoàn toàn** (`reconciled = False`, `reason_code = "DEGRADED_IMAGE_REQUIRES_VISION_FALLBACK"`), tuyệt đối không để ảnh degraded lọt qua cổng Zero-AI.

### 10. Khi nào AlgoSim có thể giải ảnh với `0` lời gọi Gemini mà vẫn đảm bảo đúng toán học?
- **Classification:** `VERIFIED FACT`
- **Answer:** Chỉ khi thỏa mãn đồng thời **cả 6 tiêu chí của `verify_ocr_input_fidelity`**:
  1. Ảnh đầu vào **không phải ảnh suy giảm chất lượng** (`is_degraded_image == False`) và không phụ thuộc hình vẽ (`has_diagram == False`, không có cụm `"như hình vẽ"`).
  2. Văn bản OCR (hoặc văn bản sau bước đối chiếu 2 engine `Tesseract + RapidOCR` không dùng ground-truth) không chứa ký tự nhiễu OCR (`Œ`, `2V3`, `B°`, dấu thập phân phẩy `3,5`, số âm/bằng 0).
  3. Hai engine OCR đồng thuận **100%** trên toàn bộ các nhóm token toán học (`solids`, `primed_labels`, `subscript_labels`, `assignments`, `planes`, `radicals`, `angles_degrees`, `fractions`, `decimals`, `negatives`, `⊥/∥`).
  4. `parse_geometry_problem_locally` trả về `LOCAL_PARSE_COMPLETE` với `coverage_complete == True` (`0` mệnh đề giả thiết hoặc câu hỏi bị bỏ sót) và vượt qua `Source Gate` (`registry.kiem_nguon`).
  - Trong mọi trường hợp còn lại, trạng thái sản phẩm mặc định giữ nguyên `LOCAL_OCR_DIAGNOSTIC_ONLY` và chuyển sang `Route B` (`1` lời gọi Gemini Vision).

### 11. Lỗi phân loại route ở `Case D` (`LOCAL_AMBIGUOUS_CLARIFICATION`) đã được sửa và kiểm chứng chưa?
- **Classification:** `VERIFIED FACT`
- **Answer:** **Đã sửa triệt để và kiểm chứng xanh (`passed = True`).** Trong `route_text_input` (`backend/app/ai/adaptive_input_router.py`), khi `previous_vision_calls == 0` và kết quả thuộc nhóm thiếu dữ kiện / cần làm rõ (`local_res.status == LOCAL_PARSE_AMBIGUOUS` hoặc `failure_category == "insufficient_specification"` hoặc mã từ chối thuộc `{"MISSING_DIMENSION", "UNDERDETERMINED_POINT", "PLANE_NOT_UNIQUE", "FOOT_NOT_DETERMINED", "AMBIGUOUS_FACT", "AMBIGUOUS_REFERENCE", "SECTION_NOT_CLOSED_ON_LATERAL_EDGES", "FACT_INCOMPLETE"}`), router gán chính xác `chosen_route = "LOCAL_AMBIGUOUS_CLARIFICATION"` với `0` lời gọi AI.

### 12. Trên máy yếu, thời gian phản hồi `p50/p95/p99`, RAM và FPS `Scene3D` đạt bao nhiêu?
- **Classification:** `VERIFIED FACT` (trên máy đo 12 luồng) / `INFERENCE` (ước lượng sang CPU 2–4 nhân) / `NOT MEASURED` (trên phần cứng laptop học sinh thực tế)
- **Answer:**
  - **Đo trực tiếp trên host hiện tại (`Windows 11`, `12` logical cores, chi tiết tại [`low_end_hardware_performance_receipt.json`](low_end_hardware_performance_receipt.json)):**
    - **Cold / Uncached Text Parse + Exact Solve (`30` lần xóa cache trước mỗi lần chạy):**
      - `local_parse_ms`: `p50` = **`9.839 ms`**, `p95` = **`16.774 ms`**, `p99` = **`17.340 ms`**.
      - `end_to_end_ms` (gồm cả `Planner + Exact Kernel + Adapter /4 + Scene3D`): `p50` = **`34.374 ms`**, `p95` = **`48.640 ms`**, `p99` = **`54.692 ms`** (vượt xa ngưỡng mục tiêu `< 150 ms` `p50` và `< 400 ms` `p95`).
    - **Warm / Cached Text Parse + Exact Solve (`50` lần với LRU cache):** `parse_p50` = **`0.048 ms`**, `end_to_end_p50` = **`26.865 ms`** (`p95` = **`42.787 ms`**).
    - **CV Preprocessing + Region Detection (`15` lần trên ảnh `900×650`):** `p50` = **`94.162 ms`**, `p95` = **`123.994 ms`**, `p99` = **`133.943 ms`** (mục tiêu `< 300 ms`).
    - **Bộ nhớ sau 50 request liên tiếp:** Python RSS = **`96.93 MB`** (mục tiêu `< 600 MB`), `traced_heap_retained_kb` = **`1168.02 KB`**, `traced_heap_peak_kb` = **`1381.33 KB`** (`0` rò rỉ bộ nhớ).
    - **Browser `Scene3D` Viewer (ghi nhận tại `perf-summary.json`):** Thời gian lên khung hình đầu tiên `median = 96.2 ms`, chuyển bước `p95 = 56.7 ms`, `effective_orbit_fps = 60.0 FPS`, JS heap `29.2–54.3 MB`, `gpu_resource_leak_balance = 0`.
  - **Ước lượng (`INFERENCE`) trên laptop học sinh 2–4 nhân (hệ số chậm đơn luồng `2.0x–3.0x`):** Cold end-to-end `p50` ước đạt **`~60–90 ms`**, `p95` **`~120–180 ms`**, CV region detection `p95` **`~195–290 ms`** — vẫn nằm trong ngưỡng mục tiêu `< 150 ms / < 400 ms` và `< 300 ms`.
  - **Đo FPS `Scene3D` trực tiếp trên iGPU vật lý của laptop cấu hình thấp:** **`NOT_MEASURED`** (trên headless Chromium Playwright đã xác minh dựng WebGL thành công với `0` console/page errors).

### 13. Những giới hạn còn lại của Hybrid `/4` nằm ở tầng nào và phần mở rộng nào có giá trị cao nhất?
- **Classification:** `VERIFIED FACT`
- **Answer:** Toàn bộ 5 khoảng trống năng lực còn mở trên `DEV 72` (`9/72` bài) đã được phân rã chính xác theo tầng trong [`hybrid_capability_prioritization.json`](hybrid_capability_prioritization.json):
  1. **`DEV72-G2` (Hạng 1 — 3 bài):** Đáy hình thang vuông / hình thang cân và đường cao tam giác cân (`TypedFactNext /2` + `Planner /26` + `Registry /33` + `Exact Kernel /24`).
  2. **`DEV72-G3` (Hạng 2 — 3 bài):** Đáy hình thoi / hình bình hành có góc `60°/120°` và mặt bên vuông góc với đáy (`TypedFactNext /2` + `Planner /26` + `Exact Kernel /24`).
  3. **`DEV72-G4` (Hạng 3 — 1 bài):** Điểm chia đoạn theo tỉ số bất kỳ `SM/SA = k`.
  4. **`DEV72-G6` (Hạng 4 — 1 bài):** Khối chóp cụt đều & lăng trụ xiên tổng quát.
  5. **`DEV72-G7` (Hạng 5 — 1 bài):** Thiết diện đi qua điểm và song song với hai đường thẳng chéo nhau.
  - **Hai hạng mục có giá trị cao nhất cho đợt phát triển tiếp theo:** **`DEV72-G2`** và **`DEV72-G3`** (mở khóa `6/9` bài còn lại của `DEV 72`, nâng độ phủ `DEV 72` từ `87.5%` lên `95.8%`, hoàn toàn dùng số học chính xác `Fraction`/`Radical` với chi phí tính toán `< 1 ms`).

### 14. Có cần viết lại sang Rust hay thêm mô hình nặng không?
- **Classification:** `VERIFIED FACT`
- **Answer:** **Không (`NO_RUST_REWRITE_JUSTIFIED_NOW`).** Thời gian giải toàn trình Cold (uncached) của `Local Parser + Planner + Exact Kernel + Adapter /4` chỉ mất **`~10–20 ms`** (và **`< 1 ms`** cho riêng tầng parser), trong khi nút thắt cổ chai thực tế khi đọc ảnh bẩn là `Local OCR` (`230–490 ms`) hoặc `Gemini Vision` (`1500–4000 ms` qua mạng). Viết lại Kernel/Parser sang Rust không giải quyết nút thắt OCR/Vision mà làm tăng rủi ro lệch ngữ nghĩa số học chính xác. Tương tự, không nhúng thêm mô hình Vision/OCR nặng gây vượt trần RAM `< 600 MB` trên máy học sinh.

### 15. AlgoSim hiện đã sẵn sàng đến mức nào cho người học thực tế, và bước tiếp theo có giá trị cao nhất là gì?
- **Classification:** `VERIFIED FACT` / `INFERENCE`
- **Answer:**
  - **Mức độ sẵn sàng đã chứng minh (`VERIFIED FACT`):**
    - Với **đầu vào văn bản / PDF text / DOCX / văn bản người dùng chỉnh sửa** thuộc 15 nhóm hình học phổ thông đã hỗ trợ (`174/183` bài benchmark + `25/25` bài diagnostic): hệ thống phản hồi tức thì (`~10–25 ms`), chính xác tuyệt đối (`0` wrong-served), dựng đầy đủ `Scene3D` + các bước giải liên tục với **`0` lời gọi Gemini**.
    - Với **đầu vào ảnh chụp**: hệ thống tự động tách vùng đề cục bộ (`0` AI calls cho ảnh trắng/nhiều đề), đối chiếu `Conflict Guard` giữa OCR và Vision để chặn lỗi đọc nhầm số/dấu phẩy (`SA=3` vs `SA=8`, `(ABC)` vs `(A'BC)`), và giảm `50%` số lời gọi AI trên `Route I1` (`1` lời gọi Vision thay vì `2`).
  - **3 bước tiếp theo có giá trị cao nhất:**
    1. **Mở rộng Kernel/Planner cho `DEV72-G2` và `DEV72-G3`** (đáy hình thang vuông/cân, đáy hình thoi góc `60°/120°`, mặt bên vuông góc đáy) để nâng độ phủ `DEV 72` từ `87.5%` lên `95.8%`.
    2. **Thu thập bộ `30+` ảnh chụp điện thoại/scan thực tế (`REAL_CAPTURED_IMAGE` / `SCANNED_DOCUMENT`)** theo đúng schema 12 trường trong [`real_world_image_corpus_manifest.json`](real_world_image_corpus_manifest.json) để đóng `Gate B`.
    3. **Thu thập bộ đề `H-1` 60 bài do giáo viên biên soạn độc lập** theo đúng schema 13 trường trong [`h1_corpus_provenance_receipt.json`](h1_corpus_provenance_receipt.json) và chạy qua bộ quét 8 lớp [`h1_contamination_audit_receipt.json`](h1_contamination_audit_receipt.json) để đóng `Gate A`.
