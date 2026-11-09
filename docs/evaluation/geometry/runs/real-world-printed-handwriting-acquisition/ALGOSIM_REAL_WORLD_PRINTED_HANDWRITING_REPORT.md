# ALGOSIM — REAL-WORLD GEOMETRY DATA ACQUISITION, HANDWRITTEN OCR & EVIDENCE RECONCILIATION REPORT

- **Run Slug:** `real-world-printed-handwriting-acquisition`
- **Wave ID:** `REAL_WORLD_PRINTED_HANDWRITING_ACQUISITION`
- **Branch:** `feat/local-first-geometry-understanding`
- **Start Base:** `f865c22ee7f0bc8aae91d1ce64a87637deff2896` (prior product commit `87497d79a6537681b91c3f06fffea86a7e593a02`)
- **Product Commit SHA:** `094193d2d02f9438189c1101aa1ff47ae1f9dbb9` (`094193d2d`)
- **Measured System Tree Hash:** `896ebf5898fa664b8315741c4b0d330f4d48c041056806778fe83c3b51cbf826` (`108` measured files, `CACHE_VERSION = 132`)
- **Live Provider Calls:** `0` (`ALLOW_LIVE_AI = 0`, `OFFLINE_FALLBACK_VERIFIED`)
- **Component Versions:** `local-geometry-parser/1` · `adaptive-input-router/1` · `typed-fact-next/2` · `geometry-fact-planner/26` · `geometry-functions/33` · `geometry-function-engine/24` · `hybrid-simulation-adapter/4` · `hybrid-route-d-simulation/4`

---

## I. Executive Summary & Acceptance Gate Status (Section XIV)

| Gate | Scope | Status | Epistemic Classification | Authoritative Evidence Receipts & SHA-256 |
|---|---|---|---|---|
| **Gate A** | External Source Acquisition & Provenance | **`PASS`** (`5` sources audited, `54` external images downloaded, `38` eligible retained, `16` excluded, `0` synthetic substitutes) | **`VERIFIED FACT`** | [`external_image_source_inventory.json`](external_image_source_inventory.json) (`a1e70991…`), [`external_image_corpus_manifest.json`](external_image_corpus_manifest.json) (`9748bd81…`), [`image_license_and_provenance_audit.json`](image_license_and_provenance_audit.json) (`6a2ddd00…`) |
| **Gate B** | Evidence & Namespace Integrity | **`PASS`** (`Dev72` 72-row table, `DEV72-G2..G7` vs `CURRICULUM-FAMILY-1..5` mapped, `7` C26 strict section cases proven valid, `7` decorator sites = `15` runtime strict XFAILs) | **`VERIFIED FACT`** | [`evidence_namespace_reconciliation.json`](evidence_namespace_reconciliation.json) (`c4e4d575…`), [`strict_contract_reconciliation.json`](strict_contract_reconciliation.json) (`370a436e…`) |
| **Gate C** | External Printed OCR Evaluation | **`PASS`** (`15` external printed exam images across `4` camera-captured photos + `4` digital renders + `7` `VMMU` MIT exam scans; strictly separated from handwriting) | **`VERIFIED FACT`** | [`printed_ocr_evaluation_receipt.json`](printed_ocr_evaluation_receipt.json) (`56ee894b…`), [`dual_ocr_fidelity_receipt.json`](dual_ocr_fidelity_receipt.json) (`be44185a…`) |
| **Gate D** | External Handwritten OCR Evaluation | **`PASS_WITH_HONEST_LIMITS`** (`16` external handwritten images across `B1` complete problem, `B2` student solutions/diagrams, `B3` `UIT-HWDB-line` + isolated `VietOCR-HW ONNX` benchmark; `OFFLINE_FALLBACK_VERIFIED`) | **`VERIFIED FACT` (offline OCR & VietOCR-HW ONNX) / `NOT MEASURED` (live Gemini Vision)** | [`handwritten_ocr_evaluation_receipt.json`](handwritten_ocr_evaluation_receipt.json) (`bbb37214…`), [`dual_ocr_fidelity_receipt.json`](dual_ocr_fidelity_receipt.json) (`be44185a…`) |
| **Gate E** | Mathematical Correctness & Zero Wrong-Served | **`PASS`** (`0` wrong-served across `Dev72`, `C26`, `38` external OCR images, `9` targeted shared-corruption probes, and `17` external problem statements; `Bug R1` & `Bug R2` fixed) | **`VERIFIED FACT`** | [`region_detection_external_receipt.json`](region_detection_external_receipt.json) (`b7636638…`), [`image_to_geometry_end_to_end_receipt.json`](image_to_geometry_end_to_end_receipt.json) (`5954278e…`) |
| **Gate F** | Independent `H-1` Validation | **`NOT_MEASURED`** (`EXTERNAL_SOURCE_AVAILABLE`, `INDEPENDENT_GROUND_TRUTH_PENDING`; external images are not conflated with `H-1`) | **`NOT MEASURED` / `BLOCKED`** | [`image_to_geometry_end_to_end_receipt.json`](image_to_geometry_end_to_end_receipt.json) (`5954278e…`), [`hybrid_gap_prioritization_revised.json`](hybrid_gap_prioritization_revised.json) (`78c96f08…`) |
| **Gate G** | Low-Resource & Performance Impact | **`PASS_HOST_MEASURED`** (`+0.0 MB` RSS delta on text route at `78.52 MB`; no handwriting ONNX loaded by default; physical 4 GB laptop `NOT_MEASURED`) | **`VERIFIED FACT` (12-core host) / `NOT MEASURED` (physical 4 GB laptop)** | [`performance_impact_receipt.json`](performance_impact_receipt.json) (`3d4a11ff…`) |
| **Gate H** | Candidate Freeze & Publication Safety | **`PASS`** (`EVALUATION_CANDIDATE.json` frozen at `094193d2d`, `0` unverified images tracked in Git, `0` frozen historical receipts modified, not merged/pushed/deployed) | **`VERIFIED FACT`** | [`run.json`](run.json) |

---

## II. Key Findings, Bug Remediations & Architecture Decisions

1. **`VERIFIED FACT` — Real External Printed & Handwritten Corpus Acquired Without Committing Unlicensed Binaries:**
   - Audited `5` external source groups (`115` candidate URLs/rows), downloaded `54` real external images (`0` Python-synthesized substitutes), excluded `16` off-domain/blurry/duplicate candidates during visual screening, and retained **`38` distinct eligible images**:
     - **`15` Printed (`Group A`):** `4` camera-captured worksheet/handout photos (`A1`), `4` digital exam renders (`A2`), and `7` `anvo25/vmmu` MIT-licensed Vietnamese math exam scans (`A3`).
     - **`16` Handwritten (`Group B`):** `1` complete handwritten geometry problem with hand-drawn 3D pyramid (`B1`: `hd_a_6043187.jpg`), `9` student notebook handwritten solutions + hand-drawn 3D diagrams (`B2`), and `6` `HungNguyen29/UIT-HWDB-line` handwritten Vietnamese text lines (`B3`).
     - **`7` Diagram-Only (`Group D`):** `7` `anvo25/vmmu` MIT-licensed figure-only 3D geometry crops (`D1`–`D7`) testing vertex/edge label retention without problem prose.
   - All `38` binaries remain stored strictly inside gitignored `.superpowers/external_image_cache/` (`0` external image files staged or committed to Git; `0` student/teacher PII found).

2. **`VERIFIED FACT` — Region Detection Bugs (`Bug R1` & `Bug R2`) Found on Real External Photos and Fixed (`region_detector.py`):**
   - **`Bug R1` (`hd_q_1084979.jpg` premise truncation):** On a real camera photo of dark printed exam paper surrounded by a darker desk border (`detect_page_boundary`), `p70` background-luminance thresholding trimmed the top line of problem text (`Cho hình chóp S.ABCD...`), and wide diagram-sandwich horizontal rules split the prose above and below an embedded figure. Fixed in [`region_detector.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/ingestion/region_detector.py) via `_page_trim_cuts_dark_ink` (rejecting page trims when inner margin strips retain significant dark ink) and `_sandwich_prose_merge` (merging prose blocks separated vertically by an embedded figure/rule).
   - **`Bug R2` (`5/15` single-problem exam scans falsely flagged `ambiguous_multi_problem = True`):** Exam header badges (`Câu 42`), figure vertex labels (`S, A, B, C`), and multiple-choice columns (`A. ... B. ... C. ... D. ...`) were previously scored as independent problem candidates. Fixed via `_filter_multi_problem_candidates`, requiring true secondary candidates to match layout-level problem headers or substantial multi-line prose away from the bottom multiple-choice band.
   - **Before vs After across all `38` external images:** Premise truncations dropped from **`1/38` (`2.63%`) to `0/38` (`0.0%`)**; false multi-problem splits on single-problem printed exams dropped from **`5/15` (`33.33%`) to `0/15` (`0.0%`)**, while the genuine 2-question photograph (`hd_q_7509702.jpg`, `Câu 9` + `Câu 10`) still triggers `ambiguous_multi_problem = True` (`candidates = 2`).

3. **`VERIFIED FACT` — Printed vs Handwritten OCR Limits & Isolated `VietOCR-HW ONNX` Evaluation:**
   - **Printed (`15` external items):** `tesseract_vie_best` achieves `mean CER = 0.2185` (`median = 0.1520`) and `mean VN word accuracy = 0.6132`, but only `0.2677` math-token recall (`2/15` exact math-token items). `rapidocr_ppocrv6_small` achieves `mean CER = 0.1376` (`median = 0.1380`) and **`0.8352` math-token recall** (`7/15` exact math-token items, `1.0000` prime recall, `0.9545` numeric assignment recall, `0.9109` point-label recall), while dropping Vietnamese diacritics (`mean VN word accuracy = 0.4702`).
   - **Handwritten (`16` external items):** Both general printed OCR engines fail completely on cursive notebook handwriting (`tesseract_vie_best`: `B1 full CER = 0.9035`, `B2 mean CER = 0.4444`, `B3 mean CER = 0.7554`; `rapidocr_ppocrv6_small`: `B1 full CER = 0.6845`, `B2 mean CER = 0.9507`, `B3 mean CER = 0.9689`).
   - **Isolated `VietOCR-HW ONNX` (`vgg_transformer`, `73.47 MB` total ONNX weights, Apache-2.0, CPU `onnxruntime`, no PyTorch):** Cuts `B3` (`UIT-HWDB-line`) handwritten prose `mean CER` from `0.7554` to **`0.0560`** (`VN word accuracy = 0.8190`) and `B1` (`hd_a_6043187_problem_crop.jpg`) problem-crop `CER` from `0.7836` to **`0.1637`**, **but** its pre-trained character vocabulary lacks `√, ⊥, ∥, °`, causing systematic math corruption (`AC = a√3 -> AC = aV7`, `ABC.A'B'C' -> ABC-ABC`, `60° -> 609`). Therefore, `VietOCR-HW ONNX` is **not** loaded in default production (`LOCAL_OCR_PRODUCTION_STATUS = "LOCAL_OCR_DIAGNOSTIC_ONLY"`), keeping text/printed route memory bloat at **`0.0 MB`** and routing handwritten math images to Vision / user-confirmation fallback (`OFFLINE_FALLBACK_VERIFIED`).

4. **`VERIFIED FACT` — Vietnamese Exam Grammar & Newline Multiple-Choice Hardening (`local_geometry_parser.py`, `registry.py`, `adaptive_input_router.py`):**
   - Extended [`local_geometry_parser.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/ai/local_geometry_parser.py) to parse authentic external exam phrasing (`", có đáy ..."` comma-clause solid introductions, `";"` semicolon premise separators, `"tất cả các cạnh bằng ..."`, `"cạnh bên bằng ..."` on right/regular prisms, and `"Thể tích (của) khối chóp/lăng trụ đã cho bằng"` anaphoric goals).
   - Extended [`registry.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/simulation/geometry_functions/registry.py) (`_co_doi_tuong_hinh`) so `Cho`-introduced root solids `"Cho (hình|khối) chóp đều S.ABC"` and `"Cho (hình|khối) lăng trụ đều ABC.A'B'C'"` ground base regularity without weakening Source Gate refusal on `"Xét hình chóp đều S.MNPQ."` derived child solids (`test_composite_geometry.py` `100%` preserved).
   - Extended [`adaptive_input_router.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/ai/adaptive_input_router.py) (`_TRAILING_MC_OPTIONS_RE`) to strip newline-separated multiple-choice options after stems ending in `)` (`... mặt phẳng (ABB'A')\nA. 3. B. 6√2. C. 3√2. D. 6.`), enabling `hd_q_7922924.jpg` to achieve `LOCAL_PARSE_COMPLETE` (`0` AI calls) and return deterministic `MISSING_DIMENSION` (`LOCAL_AMBIGUOUS_CLARIFICATION`).

---

## III. Direct Answers to All 20 Mandatory Questions (Section XV)

### 1. Đã tìm được bao nhiêu nguồn ảnh từ Internet?
- **Classification:** `VERIFIED FACT`
- **Answer:** Đã khảo sát và kiểm chứng **5 nhóm nguồn bên ngoài** trên Internet (tổng cộng **115 URL / dòng dữ liệu** được kiểm tra trong [`external_image_source_inventory.json`](external_image_source_inventory.json)):
  1. `hoidap247.com` (cộng đồng hỏi đáp toán học phổ thông Việt Nam — ảnh chụp đề giấy, phiếu bài tập và vở học sinh viết tay).
  2. `HuggingFace: anvo25/vmmu` (bộ dữ liệu multimodal kỳ thi THPT Việt Nam, giấy phép **MIT**).
  3. `HuggingFace: HungNguyen29/UIT-HWDB-line` (bộ dữ liệu dòng chữ viết tay tiếng Việt học thuật công khai trên HuggingFace).
  4. Các trang tuyển tập đề toán (`hoc24.vn`, `vietjack.com`, `loigiaihay.com`, `toanmath.com` — kiểm tra cấu trúc trang: đa số nhúng LaTeX/MathJax hoặc ảnh hình vẽ rời, đã ghi nhận rõ lý do loại).
  5. Kiểm tra tính khả dụng của các bộ dữ liệu nghiên cứu (`VietHTR-Line`, `Viet-Geometry-VQA` — ghi nhận trạng thái không mở tải trực tiếp công khai hoặc không khớp miền hình học không gian THPT).

### 2. Bao nhiêu ảnh thực sự tải thành công?
- **Classification:** `VERIFIED FACT`
- **Answer:** Đã tải thành công **54 ảnh thực từ bên ngoài** (`0` ảnh tổng hợp bằng Python). Sau bước sàng lọc thị giác và khử trùng lặp SHA-256 / nội dung, **16 ảnh bị loại có ghi biên bản** (trùng nội dung, ngoài miền hình học phẳng lớp dưới, hoặc quá mờ không xác minh được nhãn) và **38 ảnh độc lập đủ điều kiện** được giữ lại trong [`external_image_corpus_manifest.json`](external_image_corpus_manifest.json) (cộng thêm `1` ảnh cắt con chẩn đoán `hd_a_6043187_problem_crop.jpg` phục vụ đối sánh vùng đề chữ viết tay, không tính trùng vào tổng 38).

### 3. Bao nhiêu ảnh có giấy phép hoặc quyền sử dụng được xác minh?
- **Classification:** `VERIFIED FACT`
- **Answer:** Phân loại pháp lý của **38 ảnh** trong [`image_license_and_provenance_audit.json`](image_license_and_provenance_audit.json):
  - **14 ảnh (`anvo25/vmmu`):** Giấy phép **MIT (`MIT`)** — đã xác minh đầy đủ quyền lưu trữ và tái phân phối.
  - **6 ảnh (`HungNguyen29/UIT-HWDB-line`):** **`OPEN_ACADEMIC_PUBLIC_HF_DATASET`** — bộ dữ liệu nghiên cứu học thuật mở công khai, được phép đánh giá cục bộ, không tái phân phối nhị phân vào mã nguồn sản phẩm.
  - **18 ảnh (`hoidap247.com`):** **`LICENSE_UNVERIFIED`** — chỉ lưu cục bộ trong `.superpowers/external_image_cache/` (gitignored) để đo kiểm nghiên cứu, **0 tệp ảnh** được commit vào Git, và **0 thông tin cá nhân (PII)** xuất hiện trên ảnh.

### 4. Bao nhiêu ảnh chữ in và bao nhiêu ảnh viết tay?
- **Classification:** `VERIFIED FACT`
- **Answer:** Trong tổng số **38 ảnh** của bộ mẫu:
  - **15 ảnh đề chữ in (`PRINTED`, Nhóm A):** gồm `4` ảnh chụp thực tế bằng camera điện thoại trên giấy đề/phiếu bài tập (`A1`), `4` ảnh đề thi kỹ thuật số có hình vẽ (`A2`), và `7` ảnh quét/trích trang đề thi THPT từ `VMMU` (`A3`).
  - **16 ảnh chữ viết tay (`HANDWRITTEN`, Nhóm B):** gồm `1` ảnh đề toán hình học không gian viết tay hoàn chỉnh kèm hình chóp vẽ tay (`B1`: `hd_a_6043187.jpg`), `9` ảnh vở học sinh viết tay lời giải kèm hình không gian vẽ tay (`B2`), và `6` ảnh dòng chữ viết tay tiếng Việt từ `UIT-HWDB-line` (`B3`).
  - **7 ảnh chỉ có hình vẽ chữ in (`PRINTED_DIAGRAM_ONLY`, Nhóm D):** `7` ảnh cắt riêng hình không gian 3D có nhãn đỉnh/cạnh từ `VMMU` (không có lời đề).

### 5. Bao nhiêu ảnh chứa đề toán hoàn chỉnh?
- **Classification:** `VERIFIED FACT`
- **Answer:** Có **16 ảnh chứa đề toán hoàn chỉnh** (`15` ảnh chữ in Nhóm A + `1` ảnh chữ viết tay hoàn chỉnh `B1` `hd_a_6043187.jpg`), tương ứng với **17 câu đề toán hoàn chỉnh** (do `hd_q_7509702.jpg` chứa 2 câu đề hoàn chỉnh `Câu 9` và `Câu 10`). Chỉ 16 ảnh đề hoàn chỉnh này mới được đưa vào đánh giá End-to-End Image-to-Geometry trong [`image_to_geometry_end_to_end_receipt.json`](image_to_geometry_end_to_end_receipt.json).

### 6. Bao nhiêu ảnh chỉ có lời giải hoặc hình vẽ?
- **Classification:** `VERIFIED FACT`
- **Answer:** Có **22 ảnh không phải đề toán hoàn chỉnh** (tuyệt đối không tính gộp vào mẫu số giải toán End-to-End):
  - **9 ảnh (`B2`):** Lời giải viết tay trong vở học sinh kèm hình vẽ tay 3D (`HANDWRITTEN_SOLUTION_AND_DIAGRAM`).
  - **7 ảnh (`Nhóm D`):** Chỉ có hình vẽ không gian 3D và nhãn đỉnh (`PRINTED_DIAGRAM_ONLY`).
  - **6 ảnh (`B3`):** Dòng văn bản chữ viết tay rời từ `UIT-HWDB-line` (`HANDWRITTEN_BENCHMARK_LINE`) chỉ dùng để đo CER/WER chữ viết tay tiếng Việt.

### 7. OCR chữ in đạt độ chính xác bao nhiêu?
- **Classification:** `VERIFIED FACT`
- **Answer:** Trên **15 ảnh đề chữ in bên ngoài** ([`printed_ocr_evaluation_receipt.json`](printed_ocr_evaluation_receipt.json)):
  - **`tesseract_vie_best` (Tesseract 5.5.3 LSTM `vie`):** `mean CER = 0.2185` (`median CER = 0.1520`), `mean WER = 0.3712`, độ chính xác từ tiếng Việt có dấu `mean = 61.32%`, nhưng **Math-Token Recall trung bình chỉ đạt `26.77%`** (`2/15` ảnh khớp trọn vẹn token toán; Prime Recall `40.00%`, Radical Recall `0.00%`).
  - **`rapidocr_ppocrv6_small` (PP-OCRv6 det + PP-OCRv5 mobile rec ONNX):** `mean CER = 0.1376` (`median CER = 0.1380`), `mean WER = 0.3821`, độ chính xác từ tiếng Việt có dấu `mean = 47.02%` (do bộ nhận dạng Latin không sinh dấu nguyên âm tiếng Việt), nhưng **Math-Token Recall trung bình đạt `83.52%`** (`7/15` ảnh khớp trọn vẹn token toán; **Prime Recall `100.00%`**, Numeric Assignment Recall **`95.45%`**, Point Label Recall **`91.09%`**).
  - Tách riêng theo nguồn chữ in: trên `A1` (4 ảnh chụp camera giấy thật), `RapidOCR` đạt `mean CER = 0.1342` và `Math-Token Recall = 76.79%`; trên `A2` (4 ảnh đề số), `mean CER = 0.1453`, `Math-Token Recall = 91.67%`; trên `A3` (7 ảnh `VMMU`), `mean CER = 0.1351`, `Math-Token Recall = 82.71%`.

### 8. OCR chữ viết tay đạt độ chính xác bao nhiêu?
- **Classification:** `VERIFIED FACT`
- **Answer:** Trên **16 ảnh chữ viết tay bên ngoài** ([`handwritten_ocr_evaluation_receipt.json`](handwritten_ocr_evaluation_receipt.json)):
  - **`tesseract_vie_best`:** `B1` (toàn trang có hình vẽ tay) `CER = 0.9035` (vùng cắt riêng chữ đề `CER = 0.7836`); `B2` (9 ảnh vở giải toán viết tay) `mean CER = 0.4444`, `Math-Token Recall = 3.89%`; `B3` (`UIT-HWDB-line`) `mean CER = 0.7554`.
  - **`rapidocr_ppocrv6_small`:** `B1` toàn trang `CER = 0.6845` (vùng cắt chữ đề `CER = 0.3977`); `B2` `mean CER = 0.9507`; `B3` `mean CER = 0.9689`.
  - **Mô hình chuyên biệt chữ viết tay `VietOCR-HW ONNX` (`vgg_transformer`, chạy cô lập bằng `onnxruntime` CPU, `73.47 MB`):** Giảm mạnh lỗi trên văn bản viết tay tiếng Việt `B3` từ `CER = 0.7554` xuống **`mean CER = 0.0560`** (`median CER = 0.0365`, độ chính xác từ tiếng Việt có dấu **`81.90%`**) và trên vùng cắt đề viết tay `B1` (`hd_a_6043187_problem_crop.jpg`) xuống **`CER = 0.1637`** (`VN word accuracy = 67.35%`). Tuy nhiên, với ký hiệu toán học viết tay (`√, ⊥, ', °`), `VietOCR-HW ONNX` vẫn đọc sai (`AC = a√3 -> AC = aV7`, `ABC.A'B'C' -> ABC-ABC`, `60° -> 609`), nên chưa đủ an toàn để giải tự động 0-AI cho toán viết tay.

### 9. Có bao nhiêu trường hợp sai ký hiệu toán học?
- **Classification:** `VERIFIED FACT`
- **Answer:**
  - **Trên 15 ảnh chữ in (`Nhóm A`):** `13/15` ảnh có ít nhất 1 lỗi ký hiệu toán học ở `tesseract_vie_best` (mất căn `√`, gộp chữ hoa nghiêng `S.ABCD`, mất dấu `'`, tách phân số tầng `a√2 / 2`), và `8/15` ảnh có ít nhất 1 lỗi ký hiệu toán học ở `rapidocr_ppocrv6_small` (chủ yếu ở căn thức `√`, góc `°` -> `0`, ký hiệu vuông góc `⊥`, và phân số tầng 2 dòng).
  - **Trên 10 ảnh chữ viết tay có ký hiệu toán học (`1 B1 + 9 B2`):** **`10/10` (`100%`)** ảnh bị sai ít nhất một ký hiệu toán học trên tất cả các bộ OCR cục bộ (`Tesseract`, `RapidOCR`, và `VietOCR-HW ONNX`).

### 10. Có trường hợp hai OCR cùng đọc sai không?
- **Classification:** `VERIFIED FACT`
- **Answer:** **Có (`observed = True`).** Đã ghi nhận trực tiếp trên dữ liệu thật trong [`dual_ocr_fidelity_receipt.json`](dual_ocr_fidelity_receipt.json):
  1. **Phân số tầng chữ in (`hd_q_7907931.jpg`, `a√2 / 2`):** Cả `Tesseract` và `RapidOCR` đều tách tử số và mẫu số thành các dòng rời nên đều đánh mất cấu trúc phân số `a√2/2`.
  2. **Chữ viết tay & căn thức viết tay (`hd_a_6043187.jpg` và `9/9` ảnh `B2`):** Cả hai engine đều đọc sai chuỗi ký hiệu viết tay và căn thức `√`.
  - **Kết quả kiểm chứng an toàn:** Trong **100% trường hợp hai OCR cùng sai** trên dữ liệu thật cũng như toàn bộ **9 probe đồng thuận sai có chủ đích** (`SA=a√3 -> SA=aV3`, `60° -> 600`, `ABCD.A'B'C'D' -> ABCD.AB'C'D'`, `SA ⊥ (ABCD) -> SA 1 (ABCD)`, phân số tầng bị tách dòng, v.v.), cổng 6 tiêu chí `verify_ocr_input_fidelity` + `SourceCoverageReport` đều **chặn thành công 100%** (`fidelity_passed = False`, **`0` trường hợp lọt xuống Exact Kernel**).

### 11. Bao nhiêu ảnh vượt Fidelity Gate để giải với 0 AI?
- **Classification:** `VERIFIED FACT`
- **Answer:** Trên **38 ảnh thô bên ngoài** (`16` ảnh đề hoàn chỉnh + `22` ảnh lời giải/hình vẽ/dòng chữ), có **`0/38` (`0/16` đề hoàn chỉnh)** vượt qua `verify_ocr_input_fidelity` để tự giải 0-AI trực tiếp từ OCR cục bộ. Nguyên nhân thực tế hoàn toàn minh bạch: đề thi thực tế bên ngoài thường đi kèm hình vẽ 3D (`c6_no_diagram_premise_gap`), có nhiều câu trắc nghiệm trên cùng ảnh, hoặc bất đồng giữa chữ in nghiêng ở `Tesseract` và mất dấu tiếng Việt ở `RapidOCR`. Việc chặn `38/38` chứng minh cổng an toàn không đánh đổi độ đúng đắn toán học lấy tỷ lệ 0-AI ảo.

### 12. Bao nhiêu ảnh cần Vision fallback?
- **Classification:** `VERIFIED FACT` (offline routing) / `NOT MEASURED` (live Gemini Vision call)
- **Answer:** Toàn bộ **`38/38` ảnh bên ngoài** (`16/16` ảnh đề hoàn chỉnh, `9/9` ảnh lời giải viết tay `B2`, `6/6` dòng viết tay `B3`, và `7/7` ảnh chỉ có hình vẽ `Nhóm D`) đều được định tuyến an toàn sang nhánh **Vision / User Confirmation Fallback** (`OFFLINE_FALLBACK_VERIFIED` dưới chế độ `ALLOW_LIVE_AI = 0`; trong đó `7/7` ảnh chỉ có hình vẽ và `1` ảnh đa đề `hd_q_7509702.jpg` yêu cầu chọn vùng/nhập lời đề thay vì tự đoán đề).

### 13. Có bài nào OCR sai nhưng vẫn trả lời không?
- **Classification:** `VERIFIED FACT`
- **Answer:** **Tuyệt đối không (`0` bài).** Trên toàn bộ `38` ảnh thực bên ngoài, `9` probe đồng thuận sai của 2 OCR, `17` câu đề hoàn chỉnh bên ngoài, `72` bài `Dev72`, và `70` dòng `C26`, số lượng bài trả lời sai do OCR hỏng hoặc suy diễn thiếu căn cứ là **`0` (`wrong_served_count = 0`)**.

### 14. Region Detection có cắt mất dữ kiện không?
- **Classification:** `VERIFIED FACT`
- **Answer:**
  - **Trước khi sửa trong wave này:** Có **`1/38` ảnh bị cắt mất dòng mở đầu đề** (`hd_q_1084979.jpg` — `Bug R1`, cắt mất `"Cho hình chóp S.ABCD..."` do viền bàn tối quanh tờ đề xám và thước kẻ ngang giữa lời đề với hình vẽ) và **`5/15` ảnh đề đơn bị tách nhầm thành đa đề** (`Bug R2`, do nhãn đỉnh hình vẽ và đáp án `A/B/C/D`).
  - **Sau khi sửa trong [`region_detector.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/ingestion/region_detector.py) (`094193d2d`):** **`0/38` ảnh bị cắt mất dữ kiện (`0.0%` premise truncation)** và **`0/15` đề đơn bị tách nhầm**, trong khi ảnh chụp 2 câu đề thật (`hd_q_7509702.jpg`) vẫn được phát hiện đúng `ambiguous_multi_problem = True` (`2` vùng đề).

### 15. Dev72 và namespace G2–G7 đã được đối soát chưa?
- **Classification:** `VERIFIED FACT`
- **Answer:** **Đã đối soát đầy đủ từng bài một (`72/72`)** trong [`evidence_namespace_reconciliation.json`](evidence_namespace_reconciliation.json):
  - **Bảng 72 bài `Dev72`:** `56` bài dương trong miền hỗ trợ đều đạt `local_parsed = True` & `local_solved = True` với **`0` AI calls** (`56/56 = 100%` supported positive); `10` bài âm (`N1`–`N10`) đều từ chối đúng trên gold payload (`10/10`, trong đó ghi rõ `N3` là bài kiểm thử `TAMPERED_QUOTE_SOURCE_GATE_PROBE` có văn bản gốc hợp lệ nhưng quote giả mạo để test `QUOTE_NOT_IN_SOURCE`); `6` bài còn lại là các capability probes đang mở (`PL5, PA3 [DEV72-G2], MG5 [DEV72-G3], SE3 [DEV72-G4], MG9 [DEV72-G6], RE10 [DEV72-G7]`). Tổng cộng `56 + 10 = 66/72` (`91.67%`) khớp kỳ vọng với `0` AI calls; con số `63/72` ở một số báo cáo trước là do đếm gộp các lát cắt khác nhau mà không tách rõ `N3` và `6` strict XFAIL.
  - **Đối soát Namespace:** Đã lập bảng ánh xạ tường minh 3 họ mã: `DEV72-G2..G7` (khoảng trống năng lực Kernel/Planner trên `Dev72`) $\neq$ `CURRICULUM-FAMILY-1..5` (nhóm hình thang/hình thoi chương trình phổ thông đề xuất ở báo cáo trước) $\neq$ `W11-G2..G7` (cổng kiểm định UI lịch sử).
  - **Đối soát `15` Strict XFAILs:** `7` vị trí gắn decorator `@pytest.mark.xfail(..., strict=True)` trong `backend/tests/geometry/` sinh ra đúng **`15` test items `xfailed`** khi chạy `pytest` do `@pytest.mark.parametrize` (`6 + 2 + 2 + 2 + 1 + 2 = 15`), được bảo toàn nguyên vẹn `15/15`.

### 16. Bảy strict-contract mismatches có thực sự ảnh hưởng Scene3D không?
- **Classification:** `VERIFIED FACT`
- **Answer:** **Không ảnh hưởng `Scene3D` và không có bất kỳ lỗi hình học nào (`0/7` lỗi).** Kiểm chứng trực tiếp cả 7 bài (`K-A01, K-A02, K-A03, K-A04, R1-B01, R1-B02, R1-C02`) trong [`strict_contract_reconciliation.json`](strict_contract_reconciliation.json) chứng minh:
  1. Cả `7/7` đề gốc tiếng Việt đều yêu cầu rõ ràng hai vế: *"Xác định thiết diện ... và tính diện tích thiết diện đó"*.
  2. `TypedFactNext /2` trích xuất trung thực cả `simulation_goals=[construct_plane_section]` lẫn `math_goals=[area(section)]`; đa giác thiết diện trên `Scene3D` của cả `7/7` bài đều **đồng phẳng chính xác, lồi thực sự, và đạt `0` lỗi `validate_construction_continuity`**.
  3. **Chứng minh thực nghiệm:** Nếu xóa `construct_plane_section` khỏi `simulation_goals` để khớp với kỳ vọng strict cũ của C26, `Source Gate` (`registry.kiem_nguon`) **từ chối ngay cả `7/7` bài với mã `SOURCE_OBJECT_MISMATCH`**. Như vậy, sự lệch `30/41` vs `37/41` hoàn toàn do tập kỳ vọng strict cũ thiếu `construct_plane_section`, không phải lỗi của Planner, Kernel hay `Scene3D`.

### 17. Bộ H-1 độc lập đã đủ điều kiện chạy chưa?
- **Classification:** `VERIFIED FACT` / `BLOCKED`
- **Answer:** **Chưa (`INDEPENDENT_H1_VALIDATION = NOT_MEASURED`; trạng thái nguồn: `EXTERNAL_SOURCE_AVAILABLE`, `INDEPENDENT_GROUND_TRUTH_PENDING`).** Mặc dù đã thu thập được ảnh đề thi thật từ Internet (bao gồm nguồn giấy phép MIT `anvo25/vmmu`), chúng tôi **không tự ý gắn nhãn bộ ảnh này thành `H-1`** vì:
  1. `4` ảnh đã được dùng trong tập `geometry_development` / `ocr_development` để sửa lỗi `Bug R1` và ngữ pháp đề thi (`đã cho bằng`, `;`).
  2. Bộ quét chống rò rỉ 8 lớp (`scan_eight_layer_contamination`) đã phát hiện `ext_prt_03_hd_q_7907931::q1` trùng cấu trúc phép dựng trung gian (Layer 7) với dữ liệu lịch sử.
  3. Để tuyên bố `H-1` hợp lệ, cần tối thiểu `40–60` bài từ nguồn độc lập chưa từng dùng để sửa code, có đáp án/oracle toán học được con người xác minh độc lập đầy đủ 13 trường (`validate_h1_case_13_fields`).

### 18. Những capability hình học nào nên mở rộng tiếp?
- **Classification:** `VERIFIED FACT` (tần suất xuất hiện trên đề thực tế) / `INFERENCE` (thứ tự ưu tiên triển khai)
- **Answer:** Dựa trên tần suất xuất hiện thực tế trong 17 câu đề bên ngoài kết hợp với 6 khoảng trống `Dev72` ([`hybrid_gap_prioritization_revised.json`](hybrid_gap_prioritization_revised.json)), thứ tự ưu tiên cho wave kế tiếp là:
  1. **`EXT-GAP-ANGLE-PREMISE` (Ưu tiên #1 — xuất hiện ở `3` đề thực tế bên ngoài, gồm cả đề viết tay `B1`):** Suy ra chiều cao khối chóp/lăng trụ từ giả thiết góc giữa cạnh bên và mặt đáy hoặc góc nhị diện (`30°, 45°, 60°`) trong trường mở rộng căn thức chính xác $\mathbb{Q}(\sqrt{2}, \sqrt{3})$.
  2. **`CURRICULUM-FAMILY-1` (Ưu tiên #2 — xuất hiện ở `2` đề thực tế bên ngoài):** Khung tọa độ Gram chính xác cho đáy **hình thang vuông / hình thang cân** và **tam giác cân** biết góc hoặc đường cao.
  3. **`CURRICULUM-FAMILY-2` (Ưu tiên #3 — xuất hiện ở `2` đề thực tế bên ngoài):** Đáy **hình thoi góc `60°/120°`** (hoặc biết hai đường chéo) và **tam giác biết hai cạnh và góc xen giữa (`SAS`)**.
  4. Tiếp theo mới đến **`DEV72-G2`** (`PA3, PL5` — ràng buộc song song đường–mặt trong thiết diện tham số) và **`DEV72-G3`** (`MG5` — quỹ tích chân đường cao từ hai mặt phẳng vuông góc).

### 19. Có thay đổi nào làm tăng RAM hoặc độ trễ đáng kể không?
- **Classification:** `VERIFIED FACT` (trên máy đo Windows 11, 12 luồng CPU, 15.78 GB RAM) / `NOT MEASURED` (trên laptop vật lý 4 GB RAM)
- **Answer:** **Không có sự gia tăng RAM hay độ trễ trên tuyến mặc định** ([`performance_impact_receipt.json`](performance_impact_receipt.json)):
  - **RAM trên tuyến văn bản & chữ in mặc định:** `78.52 MB -> 78.52 MB` (**`+0.0 MB` delta**); không nạp PyTorch, không nạp `VietOCR-HW ONNX` mặc định (`170.53 MB` RSS chỉ phát sinh trong tiến trình benchmark viết tay cô lập).
  - **Độ trễ các chặng cục bộ:** Tiền xử lý ảnh trên 38 ảnh thực `p50 = 14.235 ms` (`p95 = 47.891 ms`); khoanh vùng đề `region_detector` `p50 = 65.140 ms` (`p95 = 234.268 ms`); cổng đối chiếu Dual-OCR + 6 kiểm tra Fidelity `p50 = 0.473 ms`; `local_geometry_parser` cold `12.484 ms` / warm cache **`p50 = 0.062 ms`**; `Planner + Registry + Exact Kernel + Adapter /4` warm **`p50 = 18.493 ms`** (`p95 = 19.438 ms`).
  - Hiệu năng trên phần cứng laptop học sinh cấu hình thấp thực tế (2–4 nhân, 4 GB RAM, iGPU) được ghi nhận trung thực là **`NOT MEASURED`**.

### 20. Candidate hiện tại đủ điều kiện ở mức nào?
- **Classification:** `VERIFIED FACT`
- **Answer:** Candidate tại commit sản phẩm `094193d2d02f9438189c1101aa1ff47ae1f9dbb9` (`tree_hash = 896ebf5898fa664b8315741c4b0d330f4d48c041056806778fe83c3b51cbf826`, `108` tệp đo, nhánh `feat/local-first-geometry-understanding`) **đủ điều kiện làm baseline nghiên cứu & phát triển đã đối soát chứng cứ** cho:
  - Giải toán cục bộ 0-AI trên các dạng đa diện đã hỗ trợ (`56/56` bài dương hỗ trợ trong `Dev72`, `2` đề thi thực tế bên ngoài dựng đủ `Scene3D` + `2` đề thiếu dữ kiện từ chối đúng `LOCAL_AMBIGUOUS_CLARIFICATION`, **`0` wrong-served** trên mọi tập kiểm thử).
  - Khoanh vùng đề thực tế bên ngoài (`0/38` cắt mất giả thiết, `0/15` tách nhầm đề đơn) và chặn an toàn `100%` lỗi OCR chữ in / chữ viết tay trước khi vào Kernel (`LOCAL_OCR_PRODUCTION_STATUS = "LOCAL_OCR_DIAGNOSTIC_ONLY"`, `OFFLINE_FALLBACK_VERIFIED`).
  - Các giới hạn chưa đo được giữ nguyên trung thực: `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`, `LIVE_VISION_EVALUATION = NOT_MEASURED`, `PRODUCTION_DEPLOYMENT_VERIFIED = NO`. Nhánh được đóng băng candidate tại chỗ, không merge vào `main`, không push và không deploy.
