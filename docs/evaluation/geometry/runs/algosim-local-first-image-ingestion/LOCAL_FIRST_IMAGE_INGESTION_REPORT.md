# LOCAL_FIRST_IMAGE_INGESTION_REPORT.md — Báo cáo Ổn định hóa Hybrid & Luồng Tiếp nhận Ảnh Thông minh Ưu tiên Cục bộ (Local-First Intelligent Image Ingestion)

- **Nhiệm vụ:** `ALGOSIM — HYBRID STABILIZATION & LOCAL-FIRST INTELLIGENT IMAGE INGESTION`
- **Run ID:** `algosim-local-first-image-ingestion`
- **Nhánh phát triển:** `feat/algosim-local-first-image-ingestion` (worktree `.superpowers/worktrees/algosim-local-first-image-ingestion`)
- **Commit xuất phát (Start Base):** `feat/hybrid-goal-driven-planner` tại `6dcdd690497c1aa3043188055e1dd4a738326a73` (`main = origin/main = bb046fa22aceff47abe22aa783aa64fc65caee13`)
- **Commit sản phẩm (Product Commit):** `c7b15b23a` (`c7b15b23a8a429df3ea76731e3342e124cd0d2f8`, `measured_system.tree_hash = 6290986dee3d1336a13611f0c0a452f90bfb40ab6d837c46396bcafb2cd5f81d`, `so_file = 106` hashed entries / `105` unique files, `CACHE_VERSION = 132` unchanged)
- **Chế độ kiểm chứng:** `OFFLINE_LOCAL_FIRST_IMAGE_INGESTION_AND_E2E_VERIFICATION` (`ALLOW_LIVE_AI=0`, `0` lượt gọi Gemini mạng thật)
- **Phán quyết tổng hợp:**
  - `PREVIOUS_CANDIDATE_FIXED_AND_VERIFIED`
  - `LOCAL_FIRST_IMAGE_INGESTION_VERIFIED`
  - `END_TO_END_IMAGE_TO_SIMULATION_VERIFIED`
  - `PROVIDER_DEPENDENCY_REDUCED_AND_MEASURED`
  - `LIVE_CALLS_ZERO_BY_DIRECTIVE`
  - `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`

---

## 1. Xác minh Git Ancestry & Ổn định hóa Baseline Candidate (Mục II)

### 1.1. Trạng thái Git & Worktree cô lập

- Nhánh `feat/algosim-local-first-image-ingestion` được tạo trong worktree độc lập `.superpowers/worktrees/algosim-local-first-image-ingestion` từ đầu nhánh `feat/hybrid-goal-driven-planner` (`6dcdd690497c1aa3043188055e1dd4a738326a73`).
- Không xóa, không reset và không chạm vào các worktree hiện có của người dùng.

### 1.2. Xử lý dứt điểm 3 điểm lệch của candidate trước (`feat/hybrid-goal-driven-planner`)

| Hạng mục | Hiện trạng trước khi ổn định hóa | Cách khắc phục tất định | Kết quả kiểm chứng |
|---|---|---|---|
| **Điểm 1 — `backend/app/simulation/geometry_functions/engine.py`** (`_Dung._kc2_do_dai`, dòng 3095) | Biểu thức `if d2 == 0 and a != b:` chỉ bắt trường hợp hai nhãn điểm khác tên nhưng trùng tọa độ, bỏ sót trường hợp cùng nhãn `a == b` dẫn tới khoảng cách `0` không phản ánh đoạn thẳng hợp lệ. | Đổi điều kiện thành `if d2 == 0:` để mọi truy vấn độ dài đoạn thẳng suy biến (`d2 == 0`) đều từ chối fail-closed với `SaiHinh("DEGENERATE_POINTS")`. | `PASS` |
| **Điểm 2 — `test_family_e9_degenerate_coincident_points_on_distance_goal`** (`backend/tests/geometry/test_goal_driven_planner_generalization.py`) | Đề kiểm thử yêu cầu `M` là trung điểm `AB` và `N` là trung điểm `AB` trong cùng một bài nên `bridge_v2` từ chối sớm bởi `CONTRADICTORY_POINT_ROLES` trước khi vào động cơ. | Xây dựng điểm `N` bằng giao của đường trung bình đi qua trung điểm `BC` song song `AC` với `AB` (tạo điểm `N` độc lập về vai trò mệnh đề nhưng trùng tọa độ chính xác với trung điểm `M` của `AB`), chứng minh động cơ bắt đúng `DEGENERATE_POINTS` tại `_kc2_do_dai`. | `PASS` |
| **Điểm 3 — `test_section_ix_test5_metamorphic_renaming_and_scaling`** (`backend/tests/geometry/test_goal_driven_planner_generalization.py`) | Đề kiểm thử biến đổi metamorphic đổi tên đỉnh thành `P.QRST` nhưng câu hỏi cuối vẫn giữ nguyên văn `"Tính khoảng cách từ A đến đường thẳng BC."`, khiến `bridge_v2` từ chối hợp lệ do nhãn `A, B, C` không thuộc khối `P.QRST`. | Đồng bộ câu hỏi sang đúng hệ đỉnh đã đổi tên `"Tính khoảng cách từ Q đến đường thẳng RS."`, bảo toàn phép kiểm chứng tính bất biến cấu trúc kế hoạch và tỉ lệ nhân độ dài `k = 2`. | `PASS` |

- **Lệnh kiểm chứng Mục II:**
  `python -m pytest tests/geometry/test_goal_driven_planner_generalization.py tests/geometry/test_hybrid_goal_decomposition.py -q` (`ALLOW_LIVE_AI=0`) → **`115 passed in 10.72s`**.
- **Phán quyết Mục II:** **`PREVIOUS_CANDIDATE_FIXED_AND_VERIFIED`**.

---

## 2. Khảo sát Năng lực Hiện có (Capability Discovery — Mục III)

### 2.1. Sơ đồ luồng tiếp nhận ảnh & tài liệu hiện có (Frontend ↔ Backend ↔ Hybrid `/4`)

```
[Frontend: ProblemInput.tsx (#home-problem-input, #btn-composer-plus, #btn-composer-send)]
   ├── Đính kèm ảnh / PDF / DOCX hoặc chụp ảnh từ PhotoProblemDialog.tsx (Camera-First UX)
   ├── Kiểm tra nhanh tại client (`frontend/src/llm/input.ts`: định dạng, dung lượng <= 10MB/tệp, <= 25MB/lượt, <= 6 tệp)
   ├── Gửi `POST /api/input/prepare` (`frontend/src/llm/client.ts` -> `backend/app/main.py` -> `unified_input.py`)
   │     ├── Giải mã Base64, sniff magic bytes (`document_reader.py`), chuẩn hóa EXIF + giới hạn cạnh 2048px (`image.py`)
   │     ├── Khử trùng lặp ảnh bằng SHA-256 trên `NormalizedImage` trước khi gọi VLM
   │     ├── Tiền xử lý CV cục bộ (`region_detector.py`):
   │     │     ├── `assess_and_enhance_image`: kiểm tra ảnh trắng/mờ (`is_blank_or_unreadable`), phát hiện bóng đổ / thiếu sáng
   │     │     ├── `detect_page_boundary`: tách trang giấy khỏi nền bàn học tối/màu
   │     │     ├── `estimate_and_correct_skew`: phát hiện góc nghiêng dòng chữ và tự xoay thẳng (`deskew`)
   │     │     └── `_segment_layout_blocks` + `_group_problem_clusters`: tách khối chữ/hình, lọc header/footer, ghép hình vẽ đi kèm
   │     ├── Nếu ảnh trắng/mờ -> từ chối ngay tại local (`IMAGE_NOT_READABLE`, `0` VLM call)
   │     ├── Nếu trang có nhiều bài độc lập chưa chỉ định -> trả `status="needs_selection"` kèm ảnh preview từng vùng (`0` VLM call)
   │     └── Khi có đúng 1 vùng bài -> gọi `extract_problem_from_image` (`image_extraction.py`, có `EXTRACTION_CACHE` theo SHA-256)
   └── Khi `status="ready"`:
         ├── Điền văn bản đề đã trích xuất vào `#home-problem-input` (`store.setProblemText`)
         └── Gửi `POST /api/analyze` (`Hybrid /4`: `TypedFactNext /2 -> Source Gate -> FactGraph -> Planner /26 -> Registry /33 -> Exact Kernel /24 -> Adapter /4 -> Scene3D`)
```

### 2.2. Kiểm kê môi trường xử lý cục bộ (Local Environment Inventory)

- **Thư viện xử lý ảnh & tài liệu cục bộ có sẵn trong `.venv`:**
  - `Pillow (PIL)`: Đã cài đặt (`Image`, `ImageOps`, `ImageChops`, `ImageFilter`, `ImageStat`, `ExifTags`).
  - `PyMuPDF (fitz)`: Đã cài đặt (trích xuất văn bản PDF trực tiếp với `0` VLM call cho PDF có text layer).
  - `lxml` + `zipfile`: Đã cài đặt (trích xuất văn bản + công thức OMML `<m:oMath>` từ `.docx` với `0` VLM call).
- **Thư viện OCR ngoài:** `pytesseract`, `tesseract`, `rapidocr`, `easyocr` chưa được cài đặt trong môi trường. Theo đúng ràng buộc Mục I & IV, **không cài thêm dependency nặng (`PaddleOCR`, `YOLO`, `OpenCV`, `PyTorch`)**; tối ưu hóa trực tiếp trên pipeline Pillow CV cục bộ hiện có.

### 2.3. Trả lời 5 câu hỏi phân loại bắt buộc (Mục III.3)

1. **Đã hoạt động tốt từ trước:**
   - Chuẩn hóa hướng EXIF, gỡ siêu dữ liệu GPS, co kích thước an toàn tối đa `2048px` (`backend/app/ingestion/image.py`).
   - Luồng PDF có text layer và DOCX có công thức OMML chạy hoàn toàn cục bộ với **`0` lượt gọi VLM** (`backend/app/ingestion/document_reader.py`).
   - Phát hiện trang nhiều bài (`needs_selection`) bằng phân cụm khối bố cục cục bộ trước khi gọi VLM (`0` VLM call ở bước phát hiện mơ hồ).
   - Khử trùng ảnh chụp lặp bằng SHA-256 trong đa ảnh (`unified_input.py`) và bộ nhớ đệm `EXTRACTION_CACHE` (`image_extraction.py`) + `SimulationCache` (`ROUTE_D_CACHE_POLICY = 132:route-d`).
   - Giao diện Camera-First không ép người học cắt/xoay thủ công (`ProblemInput.tsx`, `PhotoProblemDialog.tsx`, `PhotoProblemPanel.tsx`).
2. **Hoạt động một phần (Cần hoàn thiện):**
   - `assess_and_enhance_image` (`region_detector.py` dòng 186–224): chỉ kiểm tra ngưỡng sáng toàn cục (`mean_luma < 108` hoặc `p95 < 175`) và dùng `dyn = p95 - p5` để quyết định nâng sáng. Với trang giấy có nền đồng nhất (nơi nét chữ/hình chỉ chiếm `1%..3%` diện tích ảnh), cả `p5` lẫn `p95` đều rơi vào màu nền giấy khiến `dyn = 0`, làm ảnh thiếu sáng (`class_04_low_light`) không được nâng sáng (`enhanced_low_light = False`).
3. **Đang thiếu hoặc lỗi (Đã chứng minh bằng đo lường baseline):**
   - **Lỗ hổng 1 — Cắt cụt vùng đề/hình dưới bóng đổ (`class_05_shadowed`):** Khi ảnh chụp trên bàn học có bóng đổ che nửa dưới trang giấy, `assess_and_enhance_image` không nhận diện được bóng đổ cục bộ, và `detect_page_boundary` (`region_detector.py` dòng 284–291) dùng ngưỡng cứng `v_thresh = (b_v_med + i_v_p75) * 0.52 = 159` nên coi phần giấy nằm trong bóng đổ (`V ≈ 89`) là mặt bàn và **cắt mất 57.7% diện tích vùng bài toán + hình vẽ** (`region_containment_recall = 0.4233`)!
   - **Lỗ hổng 2 — Mất đồng bộ văn bản đã trích xuất trên ô nhập & Gọi lại đọc ảnh khi người học chỉnh sửa văn bản (`ProblemInput.tsx` & `document_reader.py`):**
     - Ở frontend (`ProblemInput.tsx` dòng 362–427): sau khi `prepareFn` trả về `status === "ready"`, `runComposerSubmit` gửi `finalProblemText` sang `analyzeFn` nhưng **không cập nhật `store.setProblemText(finalProblemText)`**, và nếu người học chỉnh sửa văn bản đề trong `#home-problem-input` rồi bấm `Dựng hình` khi tệp ảnh vẫn đính kèm, hệ thống gọi lại `prepareFn` thay vì dùng ngay văn bản đã sửa.
     - Ở backend (`document_reader.py` dòng 824–834): khi `user_text` là một đề bài hình học đầy đủ đã được người học chỉnh sửa (ví dụ sửa `SA = 3` thành `SA = 6`), `parse_user_composer_instruction` đặt `supplemental_text = ""` và `merge_supplemental_text` trả về `base_problem_text` cũ, **ghi đè làm mất nội dung người học vừa sửa** (`api_preserved_edit = False` ở Kịch bản 6)!
   - **Lỗ hổng 3 — Giải mã Base64, chuẩn hóa ảnh và phân đoạn bố cục lặp hai lần (`unified_input.py` & `region_detector.py`):**
     - `prepare_unified_input` giải mã Base64, kiểm tra định dạng và chuẩn hóa `normalize_image`, sau đó `_prepare_single_attachment` thực hiện lại toàn bộ từ đầu.
     - `detect_problem_regions` gọi `_segment_layout_blocks(working_rgb)` ở dòng 831 và gọi lại lần thứ hai ở dòng 876 ngay cả khi `deskew_applied = False` (`working_rgb` không đổi), đồng thời mã hóa JPEG `page_work_norm` ngay cả khi nhánh cuối dùng ảnh cắt `prepared_norm`.
4. **Cần loại bỏ vì dư thừa:**
   - Loại bỏ lượt gọi `_segment_layout_blocks(working_rgb)` lần 2 khi `not deskew_applied`, loại bỏ việc mã hóa trước `page_work_norm` khi không sử dụng, và loại bỏ việc giải mã Base64 / `normalize_image` trùng lặp trong `_prepare_single_attachment`.
5. **Không nên đụng vào:**
   - Hợp đồng `TypedFactNext /2`, `Source Gate`, `FactGraph`, `Planner /26`, `Registry /33`, `Exact Kernel /24`, `Adapter /4`, `Scene3D`, và `CACHE_VERSION = 132`.

---

## 3. Ba Cải tiến Trọng tâm Đã Triển khai (Mục IV, V, VI, VII, IX)

### Cải tiến 1 — Phát hiện & Cân bằng Bóng đổ Cục bộ + Bảo toàn Vùng Giấy dưới Bóng đổ (`backend/app/ingestion/region_detector.py`)

- Mở rộng `ImageQualityReport` với hai trường tương thích ngược `has_shadow: bool = False` và `enhanced_shadow: bool = False`.
- Trong `assess_and_enhance_image`:
  - Sử dụng thêm phân vị `p1` (`0.5%`) và `p99` (`99.5%`) để tính `dyn = max(0, p95 - p5, p99 - p1)`, khắc phục triệt để lỗi `dyn = 0` trên các trang đề thiếu sáng có nền đồng nhất (`class_04_low_light`).
  - Phân tích lưới HSV `(80 × 60)` với bộ lọc bao phủ nét mực (`MaxFilter(5)` + `BoxBlur(2)` trên kênh `V` và `MinFilter(5)` + `BoxBlur(2)` trên kênh `S`) để phát hiện độ chênh sáng trên nền giấy trung tính vùng trung tâm (`v_p90 >= 170`, `v_p10 <= 145`, `v_p90 - v_p10 >= 52`).
  - Khi `has_shadow = True`, nội suy bản đồ khuếch đại sáng mượt trên nền giấy trung tính và áp dụng bằng phép toán C-level `ImageChops.multiply` + `ImageChops.add`, giúp nâng phần giấy bị bóng đổ từ `V ≈ 89` lên `V ≈ 245` trong khi giữ nguyên độ đậm của nét mực (`V ≈ 20..30`) và không làm sáng nền bàn học màu ở rìa ảnh.
- Trong `detect_page_boundary`: bổ sung điều kiện nhận diện vùng giấy trung tính dưới bóng đổ (`colored_desk and s <= shadow_paper_s and v >= shadow_paper_v`), nâng `region_containment_recall` của `class_05_shadowed` từ **`0.4233` lên `1.0000` (`100%`)**.

### Cải tiến 2 — Loại bỏ Xử lý Lặp Cục bộ trong Tiền xử lý Ảnh & Chuẩn bị Đầu vào (`region_detector.py` & `unified_input.py`)

- Trong `detect_problem_regions` (`region_detector.py`): tái sử dụng trực tiếp `(pre_blocks, pre_ink_mask, pre_sx, pre_sy)` khi `deskew_applied = False` và trì hoãn việc mã hóa `_get_page_work_norm()` cho tới khi thực sự dùng đến.
- Trong `prepare_unified_input` & `_prepare_single_attachment` (`unified_input.py`): truyền `predecoded` và `prenormalized_image` đã xác thực từ bước kiểm tra đầu vào xuống `_prepare_single_attachment`, loại bỏ 100% việc giải mã Base64 và chạy `normalize_image` lần thứ hai.

### Cải tiến 3 — Đồng bộ Văn bản Đề vào Composer & Không Gọi lại Đọc ảnh Khi Chỉnh sửa Văn bản (`ProblemInput.tsx` & `document_reader.py`)

- Trong `frontend/src/components/ProblemInput.tsx`:
  - Xuất hàm `attachmentBatchSignature(items)` và bổ sung `extractedBatchRef` vào `runComposerSubmit` cũng như `ProblemInput`.
  - Khi `prepareFn` trả về `status === "ready"` (hoặc khi người học xác nhận văn bản ở `overridePreparedText`), tự động cập nhật `store.setProblemText(finalProblemText)` để đề bài hiển thị ngay trong `#home-problem-input` và ghi nhận chữ ký lô tệp đã trích xuất.
  - Khi người học chỉnh sửa văn bản đề trong `#home-problem-input` (hoặc bấm `Dựng hình` lại sau khi bổ sung dữ kiện còn thiếu ở Hành trình E) trên cùng lô tệp đính kèm, `runComposerSubmit` **bỏ qua hoàn toàn `prepareFn` (`0` lượt gọi `/api/input/prepare` và `0` lượt gọi Gemini Vision)**, gửi trực tiếp văn bản đã chỉnh sửa sang `analyzeFn`.
- Trong `backend/app/ingestion/document_reader.py` (`merge_supplemental_text`):
  - Khi `user_text` trong composer là một đề toán hình học hoàn chỉnh đã được chỉnh sửa (không phải câu lệnh điều hướng chọn trang/bài) và khác với `base_problem_text`, bảo toàn văn bản đề đã sửa của người học thay vì ghi đè bằng `base_problem_text`.

---

## 4. Kết quả Đo lường Định lượng Trước & Sau Cải tiến (Mục VI & VIII)

- **Công cụ đo tái lập:** `docs/evaluation/geometry/runs/algosim-local-first-image-ingestion/tools/measure_image_ingestion.py`
- **Bằng chứng JSON đối chiếu:**
  - Trước cải tiến: `docs/evaluation/geometry/runs/algosim-local-first-image-ingestion/before_metrics.json`
  - Sau cải tiến: `docs/evaluation/geometry/runs/algosim-local-first-image-ingestion/after_metrics.json`

### 4.1. Tổng hợp Chỉ số Toàn cục (Before vs. After)

| Chỉ số đo lường | Trước cải tiến (`before_metrics.json`) | Sau cải tiến (`after_metrics.json`) | Thay đổi |
|---|---:|---:|---:|
| **Số nhóm ảnh đại diện đạt chuẩn (11 nhóm Mục VIII)** | `10 / 11` (`90.9%`) | **`11 / 11` (`100.0%`)** | **`+1` nhóm (`class_05_shadowed` PASS)** |
| **Độ phủ giữ nguyên vùng đề + hình trên ảnh bóng đổ (`class_05_shadowed`)** | `0.4233` (`42.3%` — mất 57.7% vùng đề/hình) | **`1.0000` (`100.0%`)** | **`+57.67%` (bảo toàn trọn vẹn)** |
| **Số kịch bản tải gọi Gemini đạt chuẩn (8 kịch bản Mục VI)** | `7 / 8` (`87.5%`) | **`8 / 8` (`100.0%`)** | **`+1` kịch bản (`s6_user_edits_extracted_text` PASS)** |
| **Trung vị thời gian tiền xử lý CV cục bộ (`median_preprocess_ms`)** | `1065.64 ms` | **`656.05 ms`** | **`-38.4%` nhanh hơn** |
| **Trung vị thời gian chuẩn bị đầu vào (`median_prepare_ms`)** | `1139.40 ms` | **`742.14 ms`** | **`-34.9%` nhanh hơn** |
| **Trung vị thời gian End-to-End Ảnh → Scene3D (`median_e2e_ms`)** | `2530.20 ms` | **`1655.72 ms`** | **`-34.6%` nhanh hơn** |
| **Đỉnh bộ nhớ RAM (`max_peak_ram_kb`)** | `12592.9 KB` | **`12493.0 KB`** | **`-99.9 KB` (`~12.2 MB`)** |
| **Số lượt gọi Gemini mạng thật (`live provider calls`)** | `0` | **`0`** | **`0` (`ALLOW_LIVE_AI=0`)** |

### 4.2. Bảng Kết quả Chi tiết trên 11 Nhóm Ảnh Đại diện (Mục VIII)

| Mã nhóm | Nhóm ảnh đại diện | Trạng thái Prepare | Recall vùng đề + hình (Before → After) | Xử lý CV cục bộ | Lượt gọi Gemini (VLM + TypedFactNext) | Kết quả Hybrid `/4` (`Scene3D` / Steps / Đáp án) | Thời gian Prepare (Before → After) | Phán quyết |
|---|---|---|---:|---|---:|---|---:|---|
| `class_01_clear_straight` | 1. Ảnh đề rõ, chụp thẳng | `ready` | `1.0000 → 1.0000` | Giữ nguyên, nhận diện hình đi kèm (`has_figure=True`) | `1 + 1 = 2` | `ok` (`Scene3D` + `5` bước dựng, `V = 4`) | `961.01 → 602.42 ms` | **PASS** |
| `class_02_skewed` | 2. Ảnh đề hơi nghiêng (`6.5°`) | `ready` | `1.0000 → 1.0000` | Tự phát hiện góc nghiêng `6.4°` & xoay thẳng (`deskew_applied=True`) | `1 + 1 = 2` | `ok` (`Scene3D` + `5` bước dựng, `V = 4`) | `1415.00 → 1403.60 ms` | **PASS** |
| `class_03_rotated_exif` | 3. Ảnh đề bị xoay (`EXIF Orientation = 6`) | `ready` | `1.0000 → 1.0000` | Tự xoay chuẩn hóa hướng EXIF về thẳng đứng | `1 + 1 = 2` | `ok` (`Scene3D` + `5` bước dựng, `V = 4`) | `1247.24 → 761.29 ms` | **PASS** |
| `class_04_low_light` | 4. Ảnh chụp thiếu sáng | `ready` | `1.0000 → 1.0000` | Phát hiện thiếu sáng & nâng gamma cục bộ (`enhanced_low_light`: `False → True`) | `1 + 1 = 2` | `ok` (`Scene3D` + `5` bước dựng, `V = 4`) | `1218.04 → 742.14 ms` | **PASS** |
| `class_05_shadowed` | 5. Ảnh có bóng đổ | `ready` | **`0.4233 → 1.0000`** | Phát hiện bóng đổ (`has_shadow=True`), bù sáng cục bộ (`enhanced_shadow=True`), tách nền bàn (`desk_trimmed=True`) | `1 + 1 = 2` | `ok` (`Scene3D` + `5` bước dựng, `V = 4`) | `1054.72 → 1486.83 ms` | **PASS** |
| `class_06_multi_text_regions` | 6. Ảnh có nhiều vùng chữ (header/body/footer) | `ready` | `1.0000 → 1.0000` | Lọc bỏ running header & số trang, gộp thân đề + câu hỏi | `1 + 1 = 2` | `ok` (`Scene3D` + `5` bước dựng, `V = 4`) | `1139.40 → 670.48 ms` | **PASS** |
| `class_07_text_and_diagram` | 7. Ảnh có cả chữ và hình vẽ | `ready` | `1.0000 → 1.0000` | Ghép vùng chữ bên trái + hình vẽ có nhãn nhỏ bên phải (`has_figure=True`) | `1 + 1 = 2` | `ok` (`Scene3D` + `5` bước dựng, `V = 4`) | `1154.22 → 679.66 ms` | **PASS** |
| `class_08_multi_problem_page` | 8. Ảnh có nhiều bài trong một trang | `needs_selection` → `ready` | `1.0000 → 1.0000` | Tách 2 bài độc lập với `0` VLM call ban đầu; chỉ đọc vùng bài được chọn (`region-2`) | `1 + 1 = 2` | `ok` (`Scene3D` + `5` bước dựng, `V = 4`) | `1240.32 → 753.03 ms` | **PASS** |
| `class_09_diagram_only` | 9. Ảnh chỉ có hình vẽ | `rejected` (`MISSING_PROBLEM_TEXT`) | `1.0000 → 1.0000` | Phát hiện chỉ có hình vẽ thiếu mệnh đề bài toán, không tự bịa đề | `1 + 0 = 1` | Từ chối an toàn trước bước giải | `637.56 → 382.13 ms` | **PASS** |
| `class_10_out_of_scope` | 10. Ảnh ngoài phạm vi (lượng giác/giải tích) | `rejected` (`UNSUPPORTED_PROBLEM`) | `1.0000 → 1.0000` | Chặn tại cổng miền hình học không gian trước khi gọi `/api/analyze` | `1 + 0 = 1` | Từ chối an toàn (`0` TypedFactNext call) | `878.12 → 492.13 ms` | **PASS** |
| `class_11_corrupt_or_unreadable` | 11. Ảnh lỗi hoặc mờ trắng không đọc được | `rejected` (`IMAGE_NOT_READABLE` / `IMAGE_CORRUPT`) | `1.0000 → 1.0000` | Chặn ngay tại cổng kiểm tra byte & CV cục bộ | **`0 + 0 = 0`** | Từ chối tức thì với **`0` lượt gọi Gemini** | `18.33 → 17.98 ms` | **PASS** |

### 4.3. Bảng Đo lường Tải Gọi Gemini theo 7 Kịch bản Bắt buộc (Mục VI)

| Kịch bản (Mục VI) | Lượt gọi Gemini Vision (VLM) | Lượt gọi Gemini TypedFactNext `/2` | Lượt gọi Retry | Lượt gọi Trùng lặp (Duplicate) | Lượt trúng Cache / Tái sử dụng | Xử lý thuần Local (`0` Gemini) | Tổng lượt gọi Gemini | Thời gian thực thi | Ghi chú kỹ thuật |
|---|---:|---:|---:|---:|---:|:---:|---:|---:|---|
| **1. Nhập đề văn bản trực tiếp** (`s1_direct_text`) | `0` | `1` | `0` | `0` | `0` | `False` | **`1`** | `63.96 ms` | Đi thẳng vào `POST /api/analyze` (`0` VLM). |
| **2. Tải 1 ảnh đề rõ** (`s2_single_clear_image`) | `1` | `1` | `0` | `0` | `0` | `False` | **`2`** | `131.46 ms` | `1` lượt đọc ảnh đã chuẩn hóa + `1` lượt trích xuất `TypedFactNext /2`. |
| **3. Tải nhiều ảnh của cùng một bài (gồm 1 ảnh chụp trùng)** (`s3_multi_image_same_problem`) | `2` | `1` | `0` | `0` | `1` | `False` | **`3`** | `346.18 ms` | Khử trùng SHA-256 ảnh chụp lặp trước khi gọi VLM (`2` VLM thay vì `3`), hợp nhất toàn bài rồi chỉ gọi `TypedFactNext /2` đúng `1` lần. |
| **4. Tải ảnh có cả chữ và hình** (`s4_image_text_and_diagram`) | `1` | `1` | `0` | `0` | `0` | `False` | **`2`** | `185.85 ms` | Bộ tách khối CV cục bộ gộp đoạn chữ + hình vẽ vào `1` vùng crop duy nhất (`1` VLM call). |
| **5a. Tải ảnh chất lượng thấp — mờ trắng/hỏng không đọc được** (`s5a_unreadable_blank_image`) | **`0`** | **`0`** | `0` | `0` | `0` | **`True`** | **`0`** | `20.73 ms` | Cổng CV cục bộ phát hiện `is_blank_or_unreadable=True` và từ chối ngay tại local với **`0` lượt gọi Gemini**. |
| **5b. Tải ảnh chất lượng thấp — thiếu sáng / có bóng đổ nhưng đọc được** (`s5b_shadowed_low_light_image`) | `1` | `1` | `0` | `0` | `0` | `False` | **`2`** | `270.66 ms` | Cân bằng bóng đổ & nâng sáng ngay tại local CV trước khi trích xuất (`0` retry). |
| **6. Người dùng chỉnh sửa nhẹ văn bản đã trích xuất** (`s6_user_edits_extracted_text`) | **`0`** | `1` | `0` | `0` | `0` | `False` | **`1`** | `214.19 ms` | Văn bản đề đã trích xuất nằm sẵn trên `#home-problem-input`; khi sửa `SA = 3` → `SA = 6`, **không gọi lại bước đọc ảnh (`0` VLM call)**, chỉ chạy lại phân tích bài toán (`V = 8`). |
| **7. Người dùng chạy lại mô phỏng cùng bài** (`s7_user_resimulates_same_problem`) | **`0`** | **`0`** | `0` | `0` | `2` | **`True`** | **`0`** | `304.98 ms` | Tái sử dụng kết quả đã trích xuất (`EXTRACTION_CACHE` / `extractedBatchRef`) và `SimulationCache` (`ROUTE_D_CACHE_POLICY = 132:route-d`) với **`0` lượt gọi Gemini**. |

---

## 5. Kiểm chứng 5 Hành trình Người dùng End-to-End (Mục X)

| Hành trình | Luồng kiểm chứng End-to-End | Kiểm thử Backend (`pytest`) | Kiểm thử Frontend (`vitest`) | Kết quả |
|---|---|---|---|---|
| **Hành trình A — Ảnh đề chuẩn** | Tải ảnh đề rõ → Tự động xử lý CV cục bộ → Nhận diện đề → Điền vào `#home-problem-input` (`store.problemText`) → Chạy Hybrid `/4` → Tạo `Scene3D` (`>= 6` đối tượng), `5` bước dựng (`formation.steps`), đáp án chính xác `V = 4`. | `test_user_journeys_a_b_c_d_e_end_to_end` (`test_local_first_image_ingestion_e2e.py`) | `Journey A + B (Section X)` (`photo-problem-panel.test.tsx`) | **PASS** |
| **Hành trình B — Ảnh đề cần người dùng sửa nhẹ sau trích xuất** | Tải ảnh đề → Nhận văn bản đã trích xuất trên `#home-problem-input` → Sửa nhẹ `SA = 3` thành `SA = 6` → Chạy phân tích với **`0` lượt gọi lại đọc ảnh (`prepareSpy` vẫn chỉ gọi `1` lần)** → Tạo mô phỏng và kết quả mới chính xác `V = 8`. | `test_user_journeys_a_b_c_d_e_end_to_end` (`test_local_first_image_ingestion_e2e.py`) | `Journey A + B (Section X)` (`photo-problem-panel.test.tsx`) | **PASS** |
| **Hành trình C — Ảnh có cả chữ và hình vẽ** | Tải ảnh đề có hình vẽ đi kèm → CV cục bộ ghép chung vùng chữ và hình vẽ (`has_associated_figure=True`) → Bảo toàn đầy đủ tên đỉnh/cạnh/quan hệ → Hybrid `/4` dựng `Scene3D` hợp lệ. | `test_user_journeys_a_b_c_d_e_end_to_end` (`test_local_first_image_ingestion_e2e.py`) | `test_unified_input_20_cases.py` (`C04_TEXT_AND_3D_DIAGRAM`) | **PASS** |
| **Hành trình D — Nhiều ảnh của cùng một bài** | Tải 3 ảnh gồm ảnh thân đề + ảnh chụp trùng + ảnh hình vẽ riêng → Khử trùng SHA-256 ảnh lặp trước khi gọi VLM (`2` VLM calls thay vì `3`), ghép thông tin hình vẽ vào bài toán → Hybrid `/4` dựng `Scene3D` hợp lệ. | `test_user_journeys_a_b_c_d_e_end_to_end` (`test_local_first_image_ingestion_e2e.py`) | `test_multi_image_prepare.py` | **PASS** |
| **Hành trình E — Ảnh thiếu dữ kiện hoặc ngoài phạm vi** | Tải ảnh đề thiếu chiều cao `SA` → Trích xuất văn bản đề vào `#home-problem-input` → Hybrid `/4` từ chối fail-closed với `status="unsupported"`, `failure_category="insufficient_specification"`, `reason_code="MISSING_DIMENSION"` → Học sinh bổ sung `"và SA = 3"` ngay trên `#home-problem-input` rồi bấm `Dựng hình` → Khôi phục thành công (`status="ok"`, `V = 4`) với **`0` lượt đọc ảnh thừa**. | `test_user_journeys_a_b_c_d_e_end_to_end` (`test_local_first_image_ingestion_e2e.py`) | `Journey E (Section X)` (`photo-problem-panel.test.tsx`) | **PASS** |

---

## 6. Kiểm thử Hồi quy Toàn diện & Ranh giới Trung thực Nghiên cứu (Mục XI–XVI)

- **Kiểm thử Frontend (`npm run test:wave`):** **`136/136` test files PASS (`2,000/2,000` tests PASS)**, `tsc -b` PASS, `vite build` PASS.
- **Kiểm thử Toàn diện Backend (`pytest -q`, `ALLOW_LIVE_AI=0`):** **`13,994 passed, 7 skipped, 3 deselected, 9 xfailed, 0 failed`** (`tests/test_local_first_image_ingestion_e2e.py`: `2 passed`; `tests/test_image_normalization.py`, `tests/test_image_extraction.py`, `tests/test_multi_image_prepare.py`, `tests/test_unified_input_20_cases.py`: `77 passed`; `tests/geometry/test_goal_driven_planner_generalization.py` + `tests/geometry/test_hybrid_goal_decomposition.py`: `115 passed`).
- **Đóng băng Candidate (`freeze_evaluation_candidate.py --verify`):** `so_file = 106` hashed entries (`105` unique files), `tree_hash = 6290986dee3d1336a13611f0c0a452f90bfb40ab6d837c46396bcafb2cd5f81d`, `CACHE_VERSION = 132` (không đổi).
- **Tính trung thực của bằng chứng (Mục XIII):**
  - Toàn bộ phép đo trong nhiệm vụ này được thực hiện ở chế độ offline tất định (`ALLOW_LIVE_AI=0`, `0` lượt gọi Gemini thật).
  - Không tuyên bố hệ thống đọc được mọi ảnh chụp tự do ngoài thực tế trong mọi điều kiện ánh sáng/chữ viết tay.
  - Giữ nguyên trạng thái kiểm chứng độc lập: `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`.
