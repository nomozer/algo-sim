# ALGOSIM — INDEPENDENT GEOMETRY & REAL-WORLD VISION EVALUATION REPORT

- **Run ID:** `independent-geometry-and-vision-evaluation`
- **Date:** `2026-11-09`
- **Repository:** `D:\Documents\projects\algo-sim` (`https://github.com/nomozer/algo-sim`)
- **Verified Pre-Evaluation Baseline (`VERIFIED_BASE_SHA`):** `474ba080ec2cd740d39314109f279aacfa871376` (`474ba080e` on `integration/parallel-ingestion-reasoning`, product `d2d89376a053d3b06a78f2ec8cc5300e62df2707`, `measured_system.tree_hash = 0e815f39c8d02203d73ce332faa7f167c8344ef925f6adc547bbe37bae472a7c`)
- **Workstream A Branch / Worktree:** `eval/real-world-vision` @ `e872d025e` (`.superpowers/worktrees/real-world-vision`, product `38bfb0ef33146a7b86590d42dcfd6639e850570a`)
- **Workstream B Branch / Worktree:** `eval/independent-geometry` @ `04ec8e418` (`.superpowers/worktrees/independent-geometry`, product `c3a8d3f92860346655dfa5f0f9ccb060bd895cd8`)
- **Final Integrated Product Commit:** `e6a0bb8639be44f073a0b24ff22e19bd6a05a308` (`e6a0bb863` on `integration/parallel-ingestion-reasoning`)
- **Final Measured System Tree Hash:** `9dd8e882cefea630a9c2721b9d4a41c254a2e55c87ae99d80dbdd56106ced7c8` (`so_file = 106` hashed entries = `105` unique files)
- **Cache Version:** `CACHE_VERSION = 132` (`ROUTE_D_CACHE_POLICY = 132:route-d`, unchanged)
- **Live Provider Calls:** `0` (`ALLOW_LIVE_AI = 0` strictly enforced across all worktrees and processes)

---

## Executive Answers to the 6 Core Research Questions (Section I)

1. **AlgoSim Hybrid `/4` giải đúng đến đâu trên các bài toán hình học mới ngoài tập phát triển?**
   - Trên bộ kiểm thử ngoài tập phát triển (`GEOMETRY_HELDOUT_EVALUATED_NONINDEPENDENT`, `46` bài toán mới `HB01`–`HB46`, `0` trùng lặp văn bản/SHA-256 với ma trận phát triển `72` ca, phủ đủ `18/18` nhóm bài toán yêu cầu ở Mục B.4, chấm bằng oracle đại số độc lập `custodian/geometry_oracle.py`):
     - **Trong phạm vi năng lực đã đăng ký (`34` bài dương tính thuộc phạm vi):** giải đúng **`34 / 34 = 100.0%`** (`CORRECT_SERVED = 34`, `WRONG_SERVED = 0`, `FALSE_REFUSAL = 0`), `100%` chứng chỉ nhân chính xác (`certificate_verified = True`) và `100%` tính liên tục từng bước dựng `Scene3D` (`0` orphan steps, `0` non-monotonic transitions).
     - **Tính cả `4` ca dương tính chủ đích thăm dò các giới hạn mở `G2, G4, G6, G7` (`HB35`–`HB38`):** giải đúng **`34 / 38 = 89.47%`**, `4/38` từ chối an toàn đúng mã lý do đã biết (`0` `WRONG_SERVED`).
     - **Trên nhóm bài toán âm tính ngoài phạm vi / thiếu dữ kiện / suy biến (`8` bài `HB39`–`HB46`):** từ chối/làm rõ đúng **`8 / 8 = 100.0%`** (`7` `CORRECT_REFUSAL` + `1` `CORRECT_CLARIFICATION`, `0` `WRONG_SERVED`).
     - **Trạng thái kiểm định độc lập H-1:** `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` (cần người biên soạn độc lập bên ngoài theo giao thức `H1_PREREGISTRATION.md`; không tự tuyên bố tập held-out do agent tạo trong cùng phiên là `INDEPENDENT_H1_VERIFIED`).

2. **Những giới hạn còn lại thuộc `TypedFactNext`, `Source Gate`, `FactGraph`, `Planner`, `Registry`, `Exact Kernel` hay `Scene3D`?**
   - **`Exact Kernel (/24)` và `Scene3D / Adapter (/4)`:** `0` lỗi tính toán sai (`EXACT_KERNEL_ERROR = 0`, `ADAPTER_ERROR = 0`, `SCENE3D_ERROR = 0` trên cả `72` ca phát triển và `46` ca held-out). Một lỗ hổng tiềm ẩn ở phép dựng đỉnh chóp từ ba cạnh bên (`_dinh_tu_ba_canh_ben` khi có thêm một điểm thứ hai ngoài mặt đáy mà đề không chỉ rõ cùng phía hay khác phía) đã được phát hiện và khóa kín bằng kiểm tra tương đương nghiệm đối xứng qua mặt đáy (`c3a8d3f92`).
   - **`Bridge (/2)` (`G2, G3, G7`):** `3` giới hạn biểu diễn điểm mô tả ẩn (`DescribedPointSpec`):
     - `G2` (`PL5, PA3, HB35`): điểm mô tả `@m1` nằm bên trong toán hạng đường thẳng `line: ["A", "@m1"]` của mục tiêu `distance` (`_cau_hoi_mo_ta` tại `typed_fact_next_bridge.py:350-380`).
     - `G3` (`MG5`): hai điểm mô tả trong cùng một mục tiêu `segment: ["@m1", "@n1"]` (`len(used) != 1` tại `typed_fact_next_bridge.py:359`).
     - `G7` (`RE10, HB38`): điểm mô tả lồng trên một điểm định nghĩa theo tính chất `orthocenter`/`circumcenter` (`_mo_ta_phang` tại `typed_fact_next_bridge.py:311-316`).
   - **`Bridge (/2)` + `Source Gate (/33)` (`G4`):** `SE3, HB36` — mặt phẳng thiết diện có tên `(Q)` được khai bằng ràng buộc duy nhất `contains_points(M, N, P)` bị hạ về thiết diện 3 điểm `(MNP)` không mang `plane_name="Q"` (`typed_fact_next_bridge.py:422-451`), khiến `mat_cat_dung_nguon` từ chối câu hỏi `"cắt bởi mặt phẳng (Q)"` với `SOURCE_OBJECT_MISMATCH`.
   - **`Planner (/26)` + `IR Validator` (`G6`):** `MG9, HB37` — bài toán chứa đồng thời `3` điểm định nghĩa theo giao hai quỹ tích (`orthocenter`/`circumcenter`) vượt ngưỡng `MAX_EFFECT_CANDIDATES = 48` của toàn bài (`planner.py:85`) và ngưỡng `MAX_MEMORY_DECLARATIONS = 32` của IR dùng chung (`semantic_program/validator.py:143`).

3. **Gemini Vision đọc đề toán từ ảnh thực tế chính xác đến đâu?**
   - **Mạng thật (`LIVE_VISION_EVALUATION = NOT_MEASURED`):** tuân thủ nghiêm ngặt `ALLOW_LIVE_AI = 0` (`0` lượt gọi Gemini trả phí khi chưa có phê duyệt ngân sách/model từ Owner). Toàn bộ hạ tầng đo live (model pinning, image config logging, cost/token/retry accounting, stop conditions) đã sẵn sàng.
   - **Corpus ảnh thực (`REAL_WORLD_CORPUS_NOT_AVAILABLE`):** kiểm kê toàn bộ kho xác nhận `REAL_CAPTURED_IMAGE = 0`, `SCANNED_DOCUMENT = 0`, `SYNTHETIC_IMAGE = 66` (gồm `12` ảnh `photo-problem-to-scene`, `10` ảnh `symbol_stress`, `11` ảnh `algosim-local-first-image-ingestion`, `15` ảnh `evaluate_unified_input_corpus`, `3` ảnh fixture crop và `15` ảnh chuẩn hóa Mục A.3 `wsa_01`–`wsa_15`). Trên tập replay/mock và kiểm thử tiền xử lý cục bộ (`wsa_01`–`wsa_15`), luồng `CV Preprocessing -> Vision -> TypedFactNext -> Hybrid /4` xử lý đúng `15/15` lớp ảnh.

4. **OCR cục bộ có thực sự giảm số lượt Vision mà không làm tăng sai dữ kiện toán học không?**
   - **Không đối với OCR đơn engine; rất hạn chế đối với OCR chéo 2 engine:**
     - `Tesseract 5.5.3 (vie_fast)` đạt độ chính xác từ tiếng Việt rất cao (`97.67%`, `462/473` từ đúng chính xác, `lenient CER median = 0.74%`), nhưng có **recall `0.00%` (`0/49` strict) trên toàn bộ các ký hiệu toán học cốt lõi (`⊥, ∥, ∠, √, α, β, ², ³, ₁, ₂`)** và làm hỏng âm thầm dữ kiện toán trên **`15/21` (`71.43%`)** đề bài (ví dụ biến mặt phẳng `(β)` thành `(B)` với độ tự tin `95.3%`, làm cổng đơn engine chấp nhận sai `3/9` ca = `33.3%` false local acceptance!).
     - `RapidOCR PP-OCRv6 small` nhận diện tốt ký hiệu toán (`100.0%` lenient recall `49/49`, đúng toàn bộ token toán trên `19/21 = 90.48%` đề), nhưng từ điển thiếu `40` nguyên âm tiếng Việt có dấu tổ hợp (`53.07%` từ tiếng Việt đúng), gây lỗi trích xuất tiếng Việt ở tầng sau.
     - Kết hợp chéo 2 engine (`Candidate A2`: chỉ chấp nhận khi `0` sai khác token toán học giữa `Tesseract` và `RapidOCR`) giữ `0%` false acceptance trên tập hiệu chỉnh, nhưng chỉ qua được `3/22` (`13.6%`) đến `5/22` (`22.7%`) ảnh đơn giản trong khi tốn **`755 MB` RAM**, **`182 MB` dung lượng đĩa** và **`1,269.6 ms` CPU median**.
     - Ngược lại, **tiền xử lý CV cục bộ không cần OCR** (chặn ảnh mờ/trắng `IMAGE_NOT_READABLE`, phát hiện trang nhiều bài `MULTIPLE_PROBLEMS_DETECTED`, khử ảnh trùng `SHA-256`, giữ văn bản người học đã sửa, và bỏ lượt retry toàn ảnh dư thừa khi `crop_holds_all_content`) giảm `100%` lượt gọi Vision trên ảnh hỏng/sửa tay và `-33.3%` (`3 -> 2`) trên luồng nhiều ảnh với **`0 MB` dependency mới**, **`5.38 MB` RAM** và **`0%` rủi ro sai dữ kiện toán**.

5. **Những cải tiến kiến trúc nào có bằng chứng đủ mạnh để đưa vào sản phẩm?**
   - **Hai bản sửa chính xác, gọn nhẹ từ kiểm định Mục VIII đã được chứng minh bằng thực nghiệm và tích hợp vào candidate `e6a0bb863`:**
     1. **Bảo vệ `crop_holds_all_content` / `need_full_retry` trước khối chữ mờ bị detector bỏ sót (`region_detector.py`, `unified_input.py`, commit `38bfb0ef3`):** Khi trang giấy chưa cắt viền (`desk_trimmed = False`) có khối chữ phụ mờ (`contrast <= 20` mức xám trên nền `248`), `_segment_layout_blocks` chỉ bắt được khối chính (`len(blocks) == 1`, `crop_area_ratio = 0.1044`) khiến `crop_holds_all_content` đúng rỗng (vacuously `True`) và chặn lượt đọc lại toàn ảnh ngay cả khi Vision báo `missing_regions != []`. Bản sửa yêu cầu `area_ratio >= 0.25` cho `crop_holds_all_content` và cho phép retry khi `missing_regions` khác rỗng trên vùng cắt hẹp (`crop_area_ratio < 0.35`), giúp giảm tỷ lệ sót dữ kiện trên tập kiểm tra Mục VIII từ **`4/9` (`44.44%`) xuống `0/9` (`0.00%`)** trong khi vẫn bảo toàn `100%` mức tiết kiệm Vision (`23 -> 22`) trên corpus 22 ảnh.
     2. **Kiểm chứng tương đương hai nghiệm đối xứng qua mặt đáy của `_dinh_tu_ba_canh_ben` (`engine.py`, commit `c3a8d3f92`):** Khi dựng đỉnh chóp từ ba cạnh bên, `dung_tu_loi_goi` kiểm tra cả hai nghiệm đối xứng $+z$ và $-z$ qua mặt phẳng đáy: (a) nếu chỉ một nhánh thỏa toàn bộ dữ kiện (`kiem()`), chọn duy nhất nhánh đó; (b) nếu cả hai nhánh đều thỏa dữ kiện và cho kết quả mục tiêu bằng nhau (`chinh_xac_{+z} == chinh_xac_{-z}`), phục vụ kết quả đã chứng minh bất biến; (c) nếu cả hai nhánh đều thỏa dữ kiện nhưng cho kết quả mục tiêu khác nhau (khi có điểm thứ hai ngoài mặt đáy mà đề không phân biệt phía), từ chối fail-closed với `AMBIGUOUS_FACT`.

6. **Candidate hiện tại đã đủ điều kiện làm baseline phát triển ổn định hay chưa?**
   - **Đủ điều kiện làm baseline phát triển và tích hợp vào `main` (`CANDIDATE_READY_FOR_MAIN_REVIEW`):** Candidate tích hợp `5f2de7ee1` (product `e6a0bb863`, `measured_system.tree_hash = 9dd8e882cefea630a9c2721b9d4a41c254a2e55c87ae99d80dbdd56106ced7c8`) vượt qua toàn bộ cổng **Full T3** trên worktree detached sạch (`14,030 passed, 7 skipped, 3 deselected, 15 xfailed, 0 failed`; frontend `2,000/2,000` Vitest PASS; build PASS; demo `5/5`; crash surface `6/6`; Playwright E2E `20/20` cases trên `6/6` viewports; docs IA audit PASS; publication safety `main..HEAD` `0` vi phạm; candidate freeze `--verify` MATCH).

---

## A. Candidate Identity

| Thuộc tính | Giá trị xác minh |
|---|---|
| **Repository** | `D:\Documents\projects\algo-sim` |
| **`main` / `origin/main` SHA** | `bb046fa22aceff47abe22aa783aa64fc65caee13` (không bị sửa đổi, chưa merge, chưa push) |
| **Pre-Evaluation Verified Base (`VERIFIED_BASE_SHA`)** | `474ba080ec2cd740d39314109f279aacfa871376` (`integration/parallel-ingestion-reasoning`, product `d2d89376a`, `tree_hash = 0e815f39c8d02203d73ce332faa7f167c8344ef925f6adc547bbe37bae472a7c`) |
| **Diff `37ec2db57..474ba080e` (Pre-Flight Audit)** | Chỉ `2` tệp tài liệu (`docs/evaluation/geometry/runs/parallel-ingestion-reasoning/report.md`, `run.json`, `+16/-5` dòng); `0` thay đổi mã sản phẩm, test, schema, fixture hay cấu hình |
| **Workstream A Branch & Worktree** | `eval/real-world-vision` tại `.superpowers/worktrees/real-world-vision` (commits `38bfb0ef3`, `e872d025e`) |
| **Workstream B Branch & Worktree** | `eval/independent-geometry` tại `.superpowers/worktrees/independent-geometry` (commits `c3a8d3f92`, `04ec8e418`) |
| **Integration Branch & Worktree** | `integration/parallel-ingestion-reasoning` tại `.superpowers/worktrees/parallel-ingestion-reasoning` |
| **Integrated Product Commit (`product_commit_sha`)** | `e6a0bb8639be44f073a0b24ff22e19bd6a05a308` (`e6a0bb863`) |
| **Candidate Freeze Commit (Pre-Report T3 Target)** | `5f2de7ee19f91192014c014275b5638148cf9f02` (`5f2de7ee1`) |
| **Measured System Hash (`measured_system.tree_hash`)** | `9dd8e882cefea630a9c2721b9d4a41c254a2e55c87ae99d80dbdd56106ced7c8` (`so_file = 106` entries = `105` unique files) |
| **Cache Version & Policy** | `CACHE_VERSION = 132` (`ROUTE_D_CACHE_POLICY = 132:route-d`, `IMAGE_EXTRACTION_CACHE_VERSION = 3`, không đổi) |
| **Product Files Changed vs `474ba080e` (`3` files)** | `backend/app/ingestion/region_detector.py` (`+11/-3`), `backend/app/ingestion/unified_input.py` (`+10/-7`), `backend/app/simulation/geometry_functions/engine.py` (`+57/-27`); giao cắt giữa hai luồng = `∅` (`0` file trùng) |
| **Merge / Push Status** | `merged_to_main = false`, `pushed_to_origin = false` (chờ phê duyệt của Owner) |

---

## B. Vision Evidence (`eval/real-world-vision`)

### B.1. Dataset Provenance & Ground Truth Methodology
- **Kiểm kê phân loại nguồn dữ liệu ảnh trong kho (Mục A.3):**
  - `REAL_CAPTURED_IMAGE`: **`0`** (`REAL_WORLD_CORPUS_NOT_AVAILABLE`)
  - `SCANNED_DOCUMENT`: **`0`** (`REAL_WORLD_CORPUS_NOT_AVAILABLE`)
  - `SYNTHETIC_IMAGE`: **`66`** ảnh đề toán tổng hợp có nhãn chuẩn độc lập, gồm:
    1. `docs/evaluation/geometry/photo-problem-to-scene/corpus/` (`12` ảnh `c01`–`c12`)
    2. `docs/evaluation/geometry/runs/adaptive-local-ocr-fallback/` (`10` ảnh `symbol_stress` `s01`–`s05` clean + degraded)
    3. `docs/evaluation/geometry/runs/algosim-local-first-image-ingestion/` (`11` lớp ảnh `class_01`–`class_11`)
    4. `backend/scripts/evaluate_unified_input_corpus.py` (`15` ca hình ảnh trong `20` ca unified input)
    5. `docs/evaluation/geometry/runs/image-capture-crop-extraction/fixtures/` (`3` ảnh fixture)
    6. **Benchmark 15 lớp chuẩn hóa Mục A.3 (`wsa_01`–`wsa_15`)** do `evaluate_vision_workstream_a.py` sinh và kiểm định: (1) rõ chụp thẳng, (2) nghiêng `6.5°` trên nền bàn tối, (3) xoay `90°` + EXIF Orientation=6, (4) thiếu sáng `luma p95 < 130`, (5) bóng đổ bất đối xứng, (6) nhiều vùng chữ (header/body/goal/footer), (7) nhiều bài trên một trang (`Bài 1`, `Bài 2`), (8) chữ + hình minh họa 3D, (9) phân số & căn thức (`√2, 3/2`), (10) góc, khoảng cách & vuông góc (`⊥, ∥, ∠`), (11) ký hiệu Hy Lạp `(α), (β)`, (12) tên điểm/mặt phức tạp (`A′B′C′D′, M₁, M₂`), (13) hình vẽ có nhãn không có lời đề (`diagram_only`), (14) ảnh mờ không đọc được (`blur radius=12`), (15) ảnh ngoài phạm vi (tích phân giải tích).
  - `MOCK_PROVIDER_FIXTURE`: **`4`** gói fixture phản hồi mô phỏng offline (`CORPUS.json`, `ocr_benchmark.json`, `vision_calls_before_after.json`, `after_metrics.json`).
- **Ground Truth Methodology (Mục A.4):** Mỗi mục trong manifest (`workstream_a_vision_receipt.json`) được định nghĩa độc lập với đầu ra Gemini, gồm `id`, `source_and_license`, `image_category`, `degradation_class`, `canonical_text`, `critical_math_symbols`, `geometric_facts`, `content_regions`, `has_diagram`, `diagram_only_critical_facts`, `algosim_scope_status`, và đáp số kiểm chứng độc lập từ `geometry_oracle.py`.
- **Gemini Live Status (Mục A.6):** `LIVE_VISION_EVALUATION = NOT_MEASURED` (`ALLOW_LIVE_AI = 0`, `0` request mạng thật; công tắc dừng khẩn cấp trả HTTP `503 LIVE_AI_DISABLED` đã được xác minh).

### B.2. Local OCR Benchmark: Text Recognition Accuracy vs Mathematical Fact Fidelity (`22` items, `473` VI words, `49` critical math symbols)

| Engine / Cấu hình | Strict CER (Med / P95) | Lenient CER (Med / P95) | Body WER (Med / P95) | Từ tiếng Việt chính xác (`473` từ) | Giữ dấu tiếng Việt (khi đúng chữ cái gốc) | Recall ký hiệu toán (`49` ký hiệu: Strict / Lenient) | Đề đúng trọn vẹn token toán (`21` đề) | Tỷ lệ hỏng âm thầm dữ kiện toán | Chấp nhận cục bộ / Chấp nhận SAI (Single-Engine Gate) | Cold / Warm P50 / P95 (`ms`) | Peak RSS / Disk (`MB`) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `tesseract 5.5.3 (vie_best)` | `3.51%` / `7.21%` | `1.05%` / `3.77%` | `12.00%` / `22.22%` | **`97.04%`** (`459/473`) | **`99.35%`** (`459/462`) | **`0.00%`** (`0/49`) / `46.94%` (`23/49`) | `2/21` (`9.52%`) | **`90.48%`** (`19/21`) | `0/22` / `0` | `423.8` / `170.6` / `277.7` | `101.4` / `80.61` |
| `tesseract 5.5.3 (vie_fast)` | `1.09%` / `8.11%` | `0.74%` / `4.72%` | `10.34%` / `17.39%` | **`97.67%`** (`462/473`) | **`100.00%`** (`462/462`) | **`0.00%`** (`0/49`) / `46.94%` (`23/49`) | `6/21` (`28.57%`) | **`71.43%`** (`15/21`) | `9/22` / **`3 UNSAFE (`33.3%`)`** | `205.8` / `75.9` / `130.1` | `81.5` / `71.62` |
| `RapidOCR PP-OCRv6 small` | `6.78%` / `11.03%` | `6.48%` / `8.42%` | `30.43%` / `42.42%` | `53.07%` (`251/473`) | `89.96%` (`251/279`) | `61.22%` (`30/49`) / **`100.00%`** (`49/49`) | **`19/21`** (`90.48%`) | `9.52%` (`2/21`) | `0/22` / `0` | `2098.0` / `1193.7` / `1292.6` | `755.0` / `110.72` |
| `RapidOCR PP-OCRv6 medium` | `7.12%` / `34.02%` | `7.37%` / `34.36%` | `31.03%` / `45.45%` | `49.68%` (`235/473`) | `93.25%` (`235/252`) | `34.69%` (`17/49`) / `83.67%` (`41/49`) | `14/21` (`66.67%`) | `33.33%` (`7/21`) | `0/22` / `0` | `10500.5` / `10425.7` / `11616.4` | `1389.8` / `220.19` |
| `RapidOCR PP-OCRv5 latin` | `9.31%` / `13.79%` | `9.44%` / `12.26%` | `37.21%` / `45.45%` | `43.76%` (`207/473`) | `57.50%` (`207/360`) | `28.57%` (`14/49`) / `75.51%` (`37/49`) | `16/21` (`76.19%`) | `23.81%` (`5/21`) | `0/22` / `0` | `2542.0` / `1384.95` / `1556.1` | `741.5` / `109.37` |

### B.3. Per-Symbol Recall & Silent Corruption Breakdown (`49` Critical Symbol Occurrences)

| Ký hiệu | Số lần xuất hiện | `tesseract_vie_best` (Strict / Lenient) | `tesseract_vie_fast` (Strict / Lenient) | `rapidocr_ppocrv6_small` (Strict / Lenient) | Biến dạng âm thầm điển hình trên Tesseract |
|---|---:|---:|---:|---:|---|
| `⊥` | 2 | `0/2` (`0%`) / `0/2` (`0%`) | `0/2` (`0%`) / `0/2` (`0%`) | **`2/2` (`100%`)** / **`2/2` (`100%`)** | `SA ⊥ (ABCD)` $\rightarrow$ `SA 1 (ABCD)` hoặc `SA L (ABCD)` |
| `∥` | 2 | `0/2` (`0%`) / `0/2` (`0%`) | `0/2` (`0%`) / `0/2` (`0%`) | **`2/2` (`100%`)** / **`2/2` (`100%`)** | `AB ∥ CD` $\rightarrow$ `AB |I CD` hoặc `AB II CD` |
| `∠` | 2 | `0/2` (`0%`) / `0/2` (`0%`) | `0/2` (`0%`) / `0/2` (`0%`) | **`2/2` (`100%`)** / **`2/2` (`100%`)** | `∠SBA = 60°` $\rightarrow$ `⁄SBA = 60°` hoặc `ZSBA = 60°` |
| `√` | 4 | `0/4` (`0%`) / `0/4` (`0%`) | `0/4` (`0%`) / `0/4` (`0%`) | **`4/4` (`100%`)** / **`4/4` (`100%`)** | `2√3`, `a√2` $\rightarrow$ `2v3`, `aV2`, `21/3` |
| `α` | 3 | `0/3` (`0%`) / `0/3` (`0%`) | `0/3` (`0%`) / `0/3` (`0%`) | **`3/3` (`100%`)** / **`3/3` (`100%`)** | `(α)` $\rightarrow$ `(d)`, `(a)` |
| `β` | 1 | `0/1` (`0%`) / `0/1` (`0%`) | `0/1` (`0%`) / `0/1` (`0%`) | **`1/1` (`100%`)** / **`1/1` (`100%`)** | `(β): x + z - 9 = 0` $\rightarrow$ `(B): x + z - 9 = 0` (trùng tên mặt phẳng hợp lệ!) |
| `²`, `³`, `₁`, `₂` | 7 | `0/7` (`0%`) / `0/7` (`0%`) | `0/7` (`0%`) / `0/7` (`0%`) | **`7/7` (`100%`)** / **`7/7` (`100%`)** | `x² -> X2`, `a³ -> a3`, `M₁ -> M1`, `M₂ -> Mz` |
| `′` (prime) | 28 | `0/28` (`0%`) / `23/28` (`82.1%`) | `0/28` (`0%`) / `23/28` (`82.1%`) | `9/28` (`32.1%`) / **`28/28` (`100%`)** | `A′B′C′` $\rightarrow$ `A'B'C'` (lenient OK) hoặc rụng mất dấu phẩy trên `5/28` vị trí ở ảnh mờ `s02` |

### B.4. Section VIII Audit & Fix: `crop_holds_all_content` When Detector Misses a Faint Content Block
- **Phát hiện trên mã gốc (`474ba080e`):** Trên trang giấy chưa cắt viền (`desk_trimmed = False`, `1200×1600`), khi khối chữ phụ (`"Biết SA = 3. Tính thể tích khối chóp S.ABCD."`) được viết bằng nét mờ (`contrast <= 20` mức xám trên nền `248`, các ca `viii_05, viii_06, viii_07, viii_09`), bước thu nhỏ xuống `max_side = 640` trong `_adaptive_ink_image` (`region_detector.py:435`) làm độ tương phản tụt xuống dưới ngưỡng `20`. Khi đó `_segment_layout_blocks` chỉ trả về `1` khối (`len(blocks) == 1`, `crop_area_ratio = 0.1044` = `10.44%` diện tích trang), làm `crop_holds_all_content = not desk_trimmed and all(chosen.bbox contains b.bbox for b in blocks)` đúng một cách tầm thường (vacuously `True`) và chặn lượt đọc lại toàn ảnh ngay cả khi Vision báo `missing_regions != []`!
- **Bản sửa có bằng chứng (`38bfb0ef3`):**
  1. Trong `region_detector.py` (`L1110–1122`): chỉ gán `crop_holds_all_content = True` khi `not desk_trimmed`, `area_ratio >= 0.25`, và mọi khối phát hiện được đều nằm trong `chosen.bbox`.
  2. Trong `unified_input.py` (`L358–378`): khi Vision báo `missing_regions` khác rỗng trên vùng cắt hẹp (`crop_area_ratio < 0.35`), luôn bật `need_full_retry = True`.
- **Kết quả đo trước và sau bản sửa (9 ca `viii_01`–`viii_09` + 22 ca corpus):**
  - **Tỷ lệ bỏ sót dữ kiện trên tập kiểm tra Mục VIII (`9` ca):** giảm từ **`4/9` (`44.44%`) xuống `0/9` (`0.00%`)** (`9/9 = 100%` khôi phục đầy đủ `"SA = 3"` và giải ra thể tích `4`).
  - **Số lượt gọi Vision trên corpus 22 ảnh (`c01`–`c12` + `s01`–`s05`):** giữ nguyên mức tiết kiệm **`23 -> 22` (`-4.3%`)** trên ảnh đơn (vì `c11_chi_co_hinh.png` có `area_ratio = 0.4320 >= 0.25` và `missing_regions == []`) và **`3 -> 2` (`-33.3%`)** trên luồng nhiều ảnh.

---

## C. Geometry Evidence (`eval/independent-geometry`)

### C.1. Dataset Provenance, Development vs Held-Out & H-1 Status
- **Development Matrix (`72` ca, `tools/reasoning_matrix.py`):** Tập phát triển dùng để thiết kế và kiểm tra các cải tiến ở vòng trước (`56/62` dương tính giải đúng, `10/10` âm tính từ chối/làm rõ đúng, `0` false refusal, `0` wrong-served). **Không dùng tập 72 ca này để báo cáo tỷ lệ tổng quát hóa trên đề mới.**
- **Held-Out Generalization Benchmark (`46` ca mới `HB01`–`HB46`, `evaluate_geometry_workstream_b.py`):**
  - Nhãn phân loại trung thực: **`GEOMETRY_HELDOUT_EVALUATED_NONINDEPENDENT`** (`INDEPENDENT_H1_VALIDATION = NOT_MEASURED`).
  - Kiểm tra chống nhiễm dữ liệu (contamination check) tự động: `0` trùng lặp văn bản chuẩn hóa và `0` trùng lặp SHA-256 với toàn bộ `72` ca phát triển; sử dụng các khung kích thước mới (`Q43`, `Q64`, `Q33`, `P345`, `P512`, `T236`, `T346`, `Y68_13`).
  - Oracle độc lập: mọi đáp số kỳ vọng được tính bằng đại số hữu tỉ/căn thức chính xác trong `docs/evaluation/geometry/custodian/geometry_oracle.py` (`0` import từ `backend/app/`).

### C.2. Per-Group Results Across All 18 Required Problem Groups (Section B.4)

| # | Nhóm bài toán (Section B.4) | Mã ca trong Held-Out (`46` ca) | Số ca | `CORRECT_SERVED` | `CORRECT_REFUSAL` / `CLARIFICATION` | `FALSE_REFUSAL` | `WRONG_SERVED` | Ghi chú giới hạn (nếu có) |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | Hình chóp (`PYRAMID`) | `HB01, HB02` | 2 | `2/2` (`100%`) | — | 0 | 0 | Chóp đáy vuông & chóp đều |
| 2 | Tứ diện (`TETRAHEDRON`) | `HB03, HB04` | 2 | `2/2` (`100%`) | — | 0 | 0 | Tứ diện vuông tại `O` & tứ diện đều |
| 3 | Hình lăng trụ (`PRISM`) | `HB05, HB06` | 2 | `2/2` (`100%`) | — | 0 | 0 | Lăng trụ đứng tam giác & hộp chữ nhật |
| 4 | Quan hệ vuông góc (`PERPENDICULARITY`) | `HB07, HB08` | 2 | `2/2` (`100%`) | — | 0 | 0 | `SA ⊥ đáy` từ 2 đường cắt nhau; mặt bên `⊥` đáy |
| 5 | Quan hệ song song (`PARALLELISM`) | `HB09, HB10` | 2 | `2/2` (`100%`) | — | 0 | 0 | Khoảng cách đường–mặt song song |
| 6 | Trung điểm & trọng tâm (`MIDPOINT_CENTROID`) | `HB11, HB12` | 2 | `2/2` (`100%`) | — | 0 | 0 | Trọng tâm `G` và giao điểm hai đường trung tuyến |
| 7 | Khoảng cách điểm–đường (`DISTANCE_POINT_LINE`) | `HB13, HB14, HB35*` | 3 | `2/2` supported (`2/3` raw) | — | 0 | 0 | `*HB35` chủ đích thăm dò `G2` (`BRIDGE_ERROR`) |
| 8 | Khoảng cách điểm–mặt (`DISTANCE_POINT_PLANE`) | `HB15, HB16` | 2 | `2/2` (`100%`) | — | 0 | 0 | Chân đường cao & điểm mô tả trung điểm |
| 9 | Góc giữa đường và mặt (`ANGLE_LINE_PLANE`) | `HB17, HB18` | 2 | `2/2` (`100%`) | — | 0 | 0 | Cạnh bên & đường nối trung điểm với mặt đáy |
| 10 | Góc giữa hai đường (`ANGLE_LINE_LINE`) | `HB19, HB20` | 2 | `2/2` (`100%`) | — | 0 | 0 | Hai đường chéo nhau & đường qua trung điểm |
| 11 | Thiết diện (`SECTION`) | `HB21, HB22, HB23, HB36*` | 4 | `3/3` supported (`3/4` raw) | — | 0 | 0 | `*HB36` chủ đích thăm dò `G4` (`SOURCE_GATE_ERROR`) |
| 12 | Phép dựng phụ (`AUXILIARY_CONSTRUCTION`) | `HB24, HB25, HB26, HB38*` | 4 | `3/3` supported (`3/4` raw) | — | 0 | 0 | Trực tâm, tâm ngoại tiếp; `*HB38` thăm dò `G7` |
| 13 | Đa mục tiêu (`MULTI_GOAL`) | `HB27, HB28, HB37*` | 3 | `2/2` supported (`2/3` raw) | — | 0 | 0 | `*HB37` chủ đích thăm dò `G6` (`SEARCH_BUDGET_EXHAUSTED`) |
| 14 | Tái sử dụng trung gian (`INTERMEDIATE_REUSE`) | `HB29, HB30` | 2 | `2/2` (`100%`) | — | 0 | 0 | Tái dùng trung điểm `@m1` và chân vuông góc `H` |
| 15 | Nhiều phương án giải (`COMPETING_PLANS`) | `HB31, HB32, HB33, HB34` | 4 | `4/4` (`100%`) | — | 0 | 0 | So sánh chi phí kế hoạch, cắt tỉa nhánh, thay thế producer |
| 16 | Không đủ dữ kiện (`MISSING_DATA`) | `HB39, HB40, HB41` | 3 | — | **`3/3` (`100%`)** | 0 | 0 | `MISSING_DIMENSION`, `UNDERDETERMINED_POINT`, `AMBIGUOUS_FACT` |
| 17 | Ngoài phạm vi (`OUT_OF_SCOPE`) | `HB42, HB43` | 2 | — | **`2/2` (`100%`)** | 0 | 0 | Mặt cầu ngoại tiếp khi chưa dựng tâm; câu đề không được trích dẫn |
| 18 | Suy biến (`DEGENERATE`) | `HB44, HB45, HB46` | 3 | — | **`3/3` (`100%`)** | 0 | 0 | Bất đẳng thức tam giác, 3 điểm thẳng hàng, cạnh bên quá ngắn |
| **Tổng cộng** | **18 nhóm bài toán** | **`HB01`–`HB46`** | **46** | **`34/34` (`100%` supported) / `34/38` (`89.47%` all pos)** | **`8/8` (`100%` neg)** | **0** | **0** | **`0` wrong-served, `100%` chứng chỉ & Scene3D hợp lệ** |

### C.3. Section VIII Audit & Fix: Pyramid Apex from Three Lateral Edges (`_dinh_tu_ba_canh_ben`) Mirror-Solution Equivalence
- **Chứng minh và kiểm nghiệm khi chỉ có một mốc độ cao ngoài mặt đáy (`S.ABC` biết `AB=6, AC=8, ∠BAC=90°, SA=SB=SC=13`):**
  - Phép đối xứng qua mặt phẳng đáy $R_z(x, y, z) = (x, y, -z)$ giữ cố định toàn bộ mặt đáy $z = 0$ và là một phép đẳng cự chính xác của metric Gram $G = \operatorname{diag}(G_2, h^2)$. Thử nghiệm trực tiếp cả hai nhánh $z_S = +1$ và $z_S = -1$ trên `11/11` loại mục tiêu (`ask_volume`, `ask_distance_point_plane`, `ask_length` tới trung điểm/trọng tâm/chân đường cao, `ask_distance_lines`, `ask_angle_line_plane`, `ask_angle_lines`, `ask_angle_plane_plane`, `ask_area`) cho kết quả và chứng chỉ **trùng khớp 100%**.
- **Phát hiện và sửa lỗi khi có hai mốc độ cao độc lập ngoài mặt đáy (`P` từ `PA ⊥ (ABC), PA = 5` và `S` từ `SA = SB = SC = 13`, commit `c3a8d3f92`):**
  - Trên mã gốc (`474ba080e`), `_dat_ngoai_day` luôn chọn nghiệm dương $z_S = +12/5$ (cùng phía với $P$) dù nghiệm đối xứng $z_S = -12/5$ (khác phía với $P$) cũng thỏa mãn `100%` giả thiết. Khi mục tiêu phụ thuộc vị trí tương đối giữa $S$ và $P$ (`ask_length(S, P)` cho $\sqrt{74}$ ở nhánh $+z$ nhưng $\sqrt{314}$ ở nhánh $-z$; `ask_angle_line_plane(SP, (ABC))` cho $\cos^2 = 25/74$ so với $25/314$), chọn tùy ý một nhánh là không chặt chẽ toán học.
  - **Bản sửa trong `engine.py` (`_Dung`, `_dinh_tu_ba_canh_ben`, `dung_tu_loi_goi`):**
    1. Khi `dung.mirror_apices` khác rỗng, chạy kiểm chứng cả nhánh $+z$ và nhánh đối xứng $-z$ (`_flip_apices`).
    2. Nếu cả hai nhánh đều thỏa mãn mọi giả thiết (`SERVED`) và cho đáp số mục tiêu như nhau (ví dụ `ask_volume(S.ABC) = 96` hoặc `ask_distance_point_plane(P, (SBC)) = 24/5`), phục vụ kết quả đã chứng minh tương đương.
    3. Nếu cả hai nhánh đều thỏa mãn giả thiết nhưng bất kỳ mục tiêu được hỏi nào có đáp số khác nhau (`ask_length(S, P)` hoặc `ask_angle_line_plane(SP, (ABC))`), từ chối fail-closed với `AMBIGUOUS_FACT`.
    4. Nếu một dữ kiện bổ sung (ví dụ `segment_length(S, P) = √314`) loại bỏ nhánh $+z$ (`INCONSISTENT_FACTS`) và chỉ nhánh $-z$ thỏa mãn toàn bộ giả thiết, tự động chọn nghiệm duy nhất hợp lệ $-z$.

---

## D. Cross-Pipeline Evidence (Section VI)

So sánh 3 đường đi trên các bài toán có cả ảnh, đầu ra OCR và văn bản chuẩn (`workstream_b_geometry_receipt.json`):
- **Path 1 — Gold Text (`Ground Truth Text -> TypedFactNext -> Hybrid /4 -> Scene3D`):** `5/5` bài probe (`OCR_C1`–`OCR_C5`) và `12/12` bài thuộc phạm vi trong `wsa_01`–`wsa_15` giải đúng chính xác `100%` (`0` wrong-served).
- **Path 2 — Local OCR (`Image -> Local OCR -> TypedFactNext -> Hybrid /4 -> Scene3D`):**
  - **Path 2a (Dữ kiện sạch đối chiếu với văn bản OCR lỗi qua Source Gate):** `Source Gate` (`kiem_nguon`) chặn được `4/4` ca biến dạng ký hiệu (`QUOTE_NOT_IN_SOURCE`).
  - **Path 2b (Trích xuất `TypedFactNext` trực tiếp từ văn bản OCR đã bị biến dạng):** Vì câu trích dẫn `quote` được lấy nguyên văn từ chính văn bản OCR lỗi nên `Source Gate` không thể phát hiện lỗi nhận dạng chữ! Kết quả thực nghiệm chỉ ra **2 lỗi trả lời sai nghiêm trọng có chứng chỉ hợp lệ (`WRONG_SERVED` do lỗi fidelity đầu vào):**
    1. `OCR_C2_PRIME_DROPPED`: rụng dấu phẩy `′` biến mặt phẳng `(A′BC)` thành `(ABC)`, khiến `d(A, (A′BC)) = 120√1201/1201` bị giải thành `d(A, (ABC)) = 0`!
    2. `OCR_C4_NUMBER_CORRUPTED`: đọc nhầm chữ số `SA = 3` thành `SA = 8`, khiến thể tích/khoảng cách được tính chính xác cho đề sai (`8√3/3` thay vì `12√82/41`)!
  - **Kết luận kiến trúc quan trọng:** `Source Gate` bảo vệ tính trung thực giữa `văn bản đầu vào` và `TypedFactNext`, nhưng không thể biết `văn bản đầu vào` đã bị OCR cục bộ làm rụng dấu `′`, đổi `(β) -> (B)` hay đổi số `3 -> 8`. Do đó, giữ `LOCAL_OCR_DIAGNOSTIC_ONLY` (và yêu cầu người học xác nhận văn bản khi độ tin cậy thấp) là điều kiện bắt buộc để bảo toàn `WRONG_SERVED = 0`.
- **Path 3 — Gemini Vision (`Image -> Gemini Vision -> TypedFactNext -> Hybrid /4 -> Scene3D`):**
  - Trên tập replay/mock (`12/12` ca `photo-problem-to-scene` và `15/15` ca `wsa_01`–`wsa_15`): `100%` khớp kỳ vọng (`0` wrong-served).
  - Trên mạng thật: `LIVE_VISION_EVALUATION = NOT_MEASURED` (`ALLOW_LIVE_AI = 0`).

---

## E. Engineering & Performance Evidence (Sections VII & IX)

### E.1. Performance & Resource Summary

| Nhóm đo lường | Chỉ số | Giá trị đo thực tế | Điều kiện & cỡ mẫu |
|---|---|---|---|
| **Ingestion CV (Local)** | Tiền xử lý CV cục bộ (`p50` / `p95`) | `23.0 ms` (`22`-item corpus) · `88.22 ms` / `149.04 ms` (`15`-class `wsa`) | CPU local, `0` AI calls, Peak RSS `5.38 MB` |
| **Local OCR (Diagnostic)** | `tesseract_vie_fast` (`cold` / `warm p50` / `p95` / `RSS`) | `205.8 ms` / `75.9 ms` / `130.1 ms` / `81.5 MB` | Disk `71.62 MB`, math recall `0%` strict |
| **Local OCR (Diagnostic)** | `rapidocr_ppocrv6_small` (`cold` / `warm p50` / `p95` / `RSS`) | `2098.0 ms` / `1193.7 ms` / `1292.6 ms` / `755.0 MB` | Disk `110.72 MB`, VI word acc `53.07%` |
| **Hybrid `/4` (Dev 72)** | `Planner` / `Kernel` / `Adapter+Scene3D` CPU (`p50` / `p95`) | `0.867 / 2.919 ms` · `12.792 / 26.949 ms` · `8.025 / 24.462 ms` | `n = 72`, Peak Python heap `924.78 KiB` |
| **Hybrid `/4` (Held-Out 46)** | `Planner` / `Kernel` / `Adapter+Scene3D` CPU (`p50` / `p95`) | `0.954 / 3.260 ms` · `13.807 / 24.935 ms` · `7.388 / 24.501 ms` | `n = 46`, Peak Python heap `920.72 KiB` |
| **End-to-End Text $\rightarrow$ Scene3D** | Route D Cold / Warm (`p50` / `p95`) | Cold `123.26 / 279.55 ms` · Warm `21.89 / 47.34 ms` | Held-Out `n = 46` (`115.43 / 239.04 ms` cold, `19.98 / 46.24 ms` warm on Dev `n = 72`) |
| **Planner Search Complexity** | `explored_states` / `candidates` / `pruned` / `depth` (`max`) | `48` / `39` / `15` / `4` (`reused_intermediates`: `15` Dev, `12` Held-Out) | Search exhausted `1` ca mỗi tập (`MG9`, `HB37` — probe `G6`) |

### E.2. Release Gates & Full T3 Verification on Final Integrated Candidate (`5f2de7ee1` / product `e6a0bb863`)

| Cổng kiểm chứng | Lệnh thực thi | Kết quả | Chi tiết bằng chứng |
|---|---|---|---|
| **Targeted Vision & Ingestion Pytest** | `pytest backend/tests/test_image_crop_retry_dedup.py ... -q` | **PASS** | `524 passed, 0 failed` (`+2` test mới cho Mục VIII `crop_holds_all_content`) |
| **Targeted Geometry & Planner Pytest** | `pytest backend/tests/geometry/test_hybrid_reasoning_generalization.py ... -q` | **PASS** | `509 passed, 10 xfailed (strict), 0 failed` (`+5` test mới cho Mục VIII `_dinh_tu_ba_canh_ben`) |
| **Full Backend Pytest (Clean Detached T3)** | `pytest -q` (default `pytest.ini` `addopts`, `ALLOW_LIVE_AI=0`) | **PASS** | **`14,030 passed, 7 skipped, 3 deselected, 15 xfailed, 0 failed`** (= baseline `14,023` + `2` Workstream A + `5` Workstream B) |
| **Frontend Vitest + TypeScript + Vite Build** | `npm run test:wave && npm run build` | **PASS** | **`136` files, `2,000 passed, 0 failed`**, `tsc -b` `0` errors, Vite build `99` modules |
| **Playwright Browser E2E Verification** | `node .../verify-camera-photo-fan-stack.mjs` | **PASS** | **`20/20` cases, `6/6` viewports** (`1440x900`, `390x844`, `390x560`, `390x500`, `768x1024`, `zoom 110%`), `0` console/page errors |
| **Demo Replay & Crash Surface (Full T3)** | `replay_demo_cases.py` & `audit_demo_crash_surface.py` | **PASS** | Demo `5/5` (`REDUCED_CHAIN 1/1`), Crash Surface `6/6` (`0` thrown) |
| **Candidate Freeze Verification** | `python backend/scripts/freeze_evaluation_candidate.py --verify` | **MATCH** | `106` entries, `tree_hash = 9dd8e882cefea630a9c2721b9d4a41c254a2e55c87ae99d80dbdd56106ced7c8`, `CACHE_VERSION = 132` |
| **Documentation IA Audit** | `python backend/scripts/audit_docs_information_architecture.py` | **PASS** | `0` broken links, `0` stale `CODE_INDEX` paths, `0` unclassified root docs, `0` secret leaks |
| **Publication Safety Gate** | `python backend/scripts/check_publication_safety.py --range main..HEAD` | **PASS** | `0` violations across all commits and blobs in `main..HEAD` |
| **New Production Dependencies** | Kiểm tra `requirements.txt` & `package.json` | **`0`** | Không cài thêm bất kỳ thư viện production mới nào |

---

## F. Recommendations

1. **Có nên tích hợp local OCR vào luồng sản phẩm không?**
   - **Không.** Giữ nguyên `LOCAL_OCR_DIAGNOSTIC_ONLY`. Dữ liệu thực nghiệm chứng minh `Tesseract 5.5.3` làm hỏng âm thầm `100%` ký hiệu hình học (`⊥, ∥, ∠, √, α, β`) và biến `(β)` thành `(B)`, dẫn tới `WRONG_SERVED` nếu đưa vào trích xuất `TypedFactNext`; trong khi `RapidOCR PP-OCRv6` thiếu `40` nguyên âm tiếng Việt và tốn `755 MB` RAM + `1.27 s` CPU.
2. **Có nên giữ Gemini Vision như hiện tại và có nên thay đổi cơ chế fallback không?**
   - **Giữ Gemini Vision làm bộ đọc ảnh chính**, kết hợp với tầng tiền xử lý CV cục bộ và **đưa bản sửa Mục VIII (`crop_holds_all_content` / `need_full_retry` tại `38bfb0ef3`) vào sản phẩm** để đảm bảo khi detector bỏ sót khối chữ mờ trên trang chưa cắt viền, hệ thống tự động đọc lại toàn ảnh (`0/9` bỏ sót dữ kiện) mà vẫn tiết kiệm lượt gọi Vision trên các ảnh chỉ có hình (`c11_chi_co_hinh`).
3. **Những năng lực Hybrid `/4` nào thực sự cần mở rộng và những giới hạn nào nên giữ nguyên?**
   - **Đưa ngay bản sửa Mục VIII của `_dinh_tu_ba_canh_ben` (`c3a8d3f92`) vào sản phẩm:** đảm bảo tính đúng đắn toán học tuyệt đối cho phép dựng đỉnh chóp từ ba cạnh bên đối với hai nghiệm đối xứng qua mặt đáy.
   - **Giữ nguyên `MAX_MEMORY_DECLARATIONS = 32` (`G6`):** không nới trần bộ nhớ IR dùng chung chỉ để phục vụ một bài toán hiếm gặp có 3 trực tâm/tâm ngoại tiếp (`MG9`, `HB37`).
   - **Nếu mở vòng phát triển hợp đồng tiếp theo cho `Bridge /2` & `Source Gate /33`:** ưu tiên theo thứ tự chi phí thấp – lợi ích rõ ràng: (1) `G4` (giữ `plane_name` cho mặt phẳng thiết diện 3 điểm có tên riêng như `(Q) đi qua M, N, P`), (2) `G2` (cho phép điểm mô tả `@m1` nằm trong toán hạng `line` của mục tiêu `distance`). `G3` và `G7` hiếm gặp hơn và đòi hỏi mở rộng cấu trúc chứng chỉ `effect-chain`, nên giữ nguyên ở trạng thái từ chối an toàn (`BRIDGE_UNSUPPORTED_DESCRIBED_POINT`).
4. **Candidate tích hợp đã đủ điều kiện vào `main` và thử nghiệm người dùng thực tế chưa?**
   - **Đủ điều kiện tích hợp vào `main` (`CANDIDATE_READY_FOR_MAIN_REVIEW`):** Mọi cổng kỹ thuật, toán học, hiệu năng và an toàn xuất bản đều đạt `100%` (`Full T3 PASS`, `0` wrong-served trên cả `72` ca Dev và `46` ca Held-Out).
   - **Đối với thử nghiệm người dùng thực tế / khẳng định chất lượng live cuối cùng:** cần (a) Owner phê duyệt ngân sách chạy pilot Gemini Vision mạng thật trên bộ ảnh chụp thực tế (`LIVE_VISION_EVALUATION`) và (b) người biên soạn độc lập cung cấp bộ đề `H-1` theo `H1_PREREGISTRATION.md` (`INDEPENDENT_H1_VALIDATION`).

---

## XII. Final Verdicts

- **Vision Verdict:** **`LOCAL_OCR_DIAGNOSTIC_ONLY`** *(kèm `CURRENT_GEMINI_VISION_PREFERRED` cho đường sản phẩm và `LIVE_VISION_EVALUATION = NOT_MEASURED` / `REAL_WORLD_CORPUS_NOT_AVAILABLE` theo đúng ranh giới `ALLOW_LIVE_AI = 0`)*
- **Geometry Verdict:** **`GEOMETRY_HELDOUT_EVALUATED_NONINDEPENDENT`** *(giải đúng `34/34 = 100.0%` bài thuộc phạm vi hỗ trợ, `34/38 = 89.47%` toàn bộ bài dương tính gồm 4 probe `G2/G4/G6/G7`, từ chối đúng `8/8 = 100.0%` bài âm tính, `0` `WRONG_SERVED`; giữ nguyên `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`)*
- **Integration Verdict:** **`CANDIDATE_READY_FOR_MAIN_REVIEW`** *(Candidate `5f2de7ee1` / product `e6a0bb863`, `measured_system.tree_hash = 9dd8e882cefea630a9c2721b9d4a41c254a2e55c87ae99d80dbdd56106ced7c8`, `Full T3 PASS`, chờ Owner phê duyệt merge vào `main`)*
