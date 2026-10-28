# Báo Cáo Đánh Giá Độc Lập — Hybrid V2 Independent Vietnamese Geometry Holdout Wave 3 (`hybrid-v2-independent-vietnamese-geometry-holdout-wave3`)

- **Task:** `HYBRID_V2_INDEPENDENT_VIETNAMESE_GEOMETRY_HOLDOUT_WAVE3`
- **Run slug:** `hybrid-v2-independent-vietnamese-geometry-holdout-wave3`
- **Chế độ thực thi:** Offline evaluation-only (`ALLOW_LIVE_AI = "0"`, `0` live provider calls)
- **Phân lớp độc lập:** `AI_CURATED_PROCEDURAL_INDEPENDENCE` (không tuyên bố độc lập con người hoặc tổ chức bên ngoài)
- **Trạng thái cuối:** `INDEPENDENT_HOLDOUT_WAVE3_EXECUTED`

---

## 1. Danh Tính Cơ Sở & Chuỗi Commit Cổng Trước Khi Chạy Product

| Hạng mục | Giá trị xác minh |
|---|---|
| GitHub `main` / `origin/main` cơ sở | `e137623c4f674135a8d7884b78614c132eb78085` |
| Product commit đang đo | `73ca8d92e74059680ce53b99692af396df37a2f8` |
| Frozen Full T3 candidate | `b61f16995dfbe0110a639a2127d0fb5a9c3afde0` |
| Product freeze (`118` file) | `1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d` (`MATCH`) |
| `backend/app` git tree hash | `29eb33d0e767069ce9d6557e7da8532644ceee7c` |
| Nhánh nghiên cứu | `research/hybrid-v2-independent-vietnamese-geometry-holdout-wave3` |
| Gate 1 — Preregistration commit (trước khi tạo corpus) | `f438a62a3485ce9b8d687cb91102c366e6848960` |
| Gate 2 — Scorer Qualification commit (`24/24` PASS, trước khi tạo corpus) | `53cba0c8a63ae3cf7c1b058b8b09f07046449f06` |
| Gate 4 — Pre-execution Freeze commit (trước khi chạy product) | `2332f7ad3d1a73733bbc720bcf36705c67bc2d6b` |
| Phiên bản hệ thống | Registry `geometry-functions/19`, Planner `geometry-fact-planner/17`, Engine `geometry-function-engine/14`, Adapter `hybrid-simulation-adapter/4`, Certificate `plane-section-certificate/1`, `CACHE_VERSION = 130`, `DEFAULT_MODE = LLM_ONLY` |

---

## 2. Kiểm Chứng Các Cổng Phương Pháp Luận Trước Khi Chạy Product

1. **Cổng tiền đăng ký & thẩm định scorer trước khi tạo corpus (Gate 1 & Gate 2):**
   - Toàn bộ tài liệu tiền đăng ký (`preregistration.md`, `supported-family-matrix.md`, `scoring-contract.md`, `refusal-taxonomy.json`, `curator-brief.md`) và bộ chấm `tools/evaluate_holdout_wave3.py` được hoàn tất và kiểm định trên `24/24` test suite tổng hợp + đột biến (`10/10` đột biến bị chặn, `0%` sống sót) trong `verification/scorer-qualification-receipt.json` tại commit `53cba0c8a63ae3cf7c1b058b8b09f07046449f06` trước khi bất kỳ bài toán nào của Wave 3 được tạo.
   - Scorer Wave 3 đã đóng hoàn toàn lỗi tra chỉ số đỉnh đa giác `W2-A10` của Wave 2: khớp tọa độ hữu tỷ chính xác `Fraction` và chuẩn hóa nhãn `_norm_label` (`A'`, `A′`, `A_prime`), kiểm tra nhất quán `ordinal` và chỉ số tọa độ đa giác cho Category B, và **không bao giờ** gán mặc định đỉnh không tìm thấy về chỉ số `0` (`test_23_unfound_vertex_never_defaults_to_polygon_index_zero`).
2. **Cổng tường lửa thông tin của Curator (Gate 3 — `verification/independence-audit.json`):**
   - Subagent Curator (`206cf35f-d6b5-4ac4-a16a-38ae2ced52d1`) chỉ đọc đúng 8 file được phép trong worktree Wave 3 (`AGENTS.md`, `docs/RULES.md`, `preregistration.md`, `supported-family-matrix.md`, `scoring-contract.md`, `curator-brief.md`, `refusal-taxonomy.json`, `typed_fact_next.py`) cùng các file do chính Curator sinh trong thư mục run.
   - `forbidden_reads = 0`, `forbidden_commands = 0`, `status = "HOLDOUT_INDEPENDENCE_ESTABLISHED"`.
3. **Cổng chống trùng lặp 9 chiều (Gate 3 — `verification/deduplication-audit.json`):**
   - Đối chiếu `144` bài Wave 3 với `940` mục lịch sử (Wave 1, Wave 2, các đợt sửa `W2-M1..W2-M5`, và toàn bộ test/fixture sản phẩm).
   - Ở lần kiểm tra tiền đông cứng đầu tiên, `143/144` bài đạt ngay và `1` bài (`W3-B01`) chạm cờ bất biến tỷ lệ (`external_scale_invariant_flags`). Theo đúng Mục 6 của GO, Curator đã thay thế `W3-B01` trước khi freeze và ghi nhận đầy đủ trong `corpus-provenance.md`.
   - Sau khi thay thế `W3-B01`: `passed = true`, `max_external_5gram_jaccard = 0.6713 < 0.80`, `max_internal_positive_5gram_jaccard = 0.7153 < 0.75`, `0` cờ vi phạm trên cả 9 chiều kiểm tra.
4. **Cổng thẩm định Oracle độc lập trước khi chạy product (Gate 3 — `verification/independent-oracle-review.json`):**
   - Subagent `Independent Holdout Wave 3 Oracle Reviewer` (`9fdf8f17-aeaf-4fd3-8530-34c02d1363c2`) tái tính độc lập từ đầu toàn bộ `72` bài dương tính (`W3-B01..W3-B54`, `W3-A01..W3-A18`) bằng số học `Fraction` thuần và kiểm tra toàn bộ `72` bài âm tính (`W3-N01..W3-N72`) với `0` import từ `app.*`.
   - Kết quả: `status = "ORACLE_VERIFIED_BEFORE_EXECUTION"`, `discrepancies = []` (`72/72` dương tính và `72/72` âm tính khớp 100%).

---

## 3. Kết Quả Định Lượng Tổng Thể (`results/scored-run-1/`)

### 3.1. Bảng chỉ số chính kèm khoảng tin cậy 95% Wilson

| Chỉ số | Tử số / Mẫu số | Tỷ lệ (%) | 95% Wilson CI |
|---|---:|---:|---|
| **Positive Serve Accuracy (Tổng 72 bài `SERVE`)** | `20 / 72` | **27.78%** | `[18.76%, 39.05%]` |
| **Positive Serve Accuracy — Stratum `P-B` (Category B, 54 bài)** | `12 / 54` | **22.22%** | `[13.20%, 34.94%]` |
| **Positive Serve Accuracy — Stratum `P-A` (Category A, 18 bài)** | `8 / 18` | **44.44%** | `[24.56%, 66.28%]` |
| **Exact Oracle Agreement khi đã phục vụ (`SERVED_CORRECT / SERVED`)** | `20 / 20` | **100.00%** | `[83.89%, 100.00%]` |
| **Tỷ lệ phục vụ của chuỗi `Planner /17 -> Engine /14 -> Adapter /4` khi qua `Source Gate`** | `20 / 20` | **100.00%** | `[83.89%, 100.00%]` |
| **False Refusal Rate trên bài `SERVE`** | `52 / 72` | **72.22%** | `[60.95%, 81.24%]` |
| **Negative Fail-Closed Refusal Rate (`REFUSE` bị từ chối)** | `72 / 72` | **100.00%** | `[94.93%, 100.00%]` |
| **Negative Refusal Reason Agreement (`REFUSED_CORRECT_REASON`)** | `60 / 72` | **83.33%** | `[73.09%, 90.20%]` |
| **Wrong-Served Rate (`WRONG_SERVED` trên toàn bộ 144 bài)** | `0 / 144` | **0.00%** | `[0.00%, 2.60%]` |
| **Wrong-Served Rate trên 72 bài dương tính** | `0 / 72` | **0.00%** | `[0.00%, 5.07%]` |
| **Wrong-Served Rate trên 72 bài âm tính** | `0 / 72` | **0.00%** | `[0.00%, 5.07%]` |
| **Track C Scene3D Clean Rate trên các bài được phục vụ** | `20 / 20` | **100.00%** | `[83.89%, 100.00%]` |
| **Uncaught Product Exceptions / Harness Errors** | `0 / 144` | **0.00%** | `[0.00%, 2.60%]` |

---

## 4. Phân Tích Theo Stratum, Họ Khối, Quan Hệ Mặt Phẳng và Loại Câu Hỏi

### 4.1. Theo họ khối hình học (trên 72 bài dương tính `SERVE`)

| Họ khối (`family`) | Tổng bài `SERVE` | `P-B` (`SERVED_CORRECT`) | `P-A` (`SERVED_CORRECT`) | Tổng `SERVED_CORRECT` | Tỷ lệ (%) | 95% Wilson CI | `WRONG_SERVED` |
|---|---:|---:|---:|---:|---:|---|---:|
| `quadrilateral_pyramid` | 12 | `4 / 9` | `2 / 3` | **`6 / 12`** | 50.00% | `[25.38%, 74.62%]` | 0 |
| `right_triangular_prism` | 12 | `3 / 9` | `2 / 3` | **`5 / 12`** | 41.67% | `[19.33%, 68.05%]` | 0 |
| `cuboid` | 12 | `2 / 9` | `2 / 3` | **`4 / 12`** | 33.33% | `[13.81%, 60.94%]` | 0 |
| `triangular_pyramid` | 12 | `1 / 9` | `1 / 3` | **`2 / 12`** | 16.67% | `[4.70%, 44.80%]` | 0 |
| `oblique_triangular_prism` | 12 | `1 / 9` | `1 / 3` | **`2 / 12`** | 16.67% | `[4.70%, 44.80%]` | 0 |
| `cube` | 12 | `1 / 9` | `0 / 3` | **`1 / 12`** | 8.33% | `[1.49%, 35.39%]` | 0 |
| **Tổng cộng** | **72** | **`12 / 54`** | **`8 / 18`** | **`20 / 72`** | **27.78%** | **`[18.76%, 39.05%]`** | **0** |

### 4.2. Theo quan hệ mặt phẳng cắt (trên 72 bài dương tính `SERVE`)

| Quan hệ mặt phẳng (`plane_relation`) | Tổng bài `SERVE` | `P-B` (`SERVED_CORRECT`) | `P-A` (`SERVED_CORRECT`) | Tổng `SERVED_CORRECT` | Tỷ lệ (%) | 95% Wilson CI | `WRONG_SERVED` |
|---|---:|---:|---:|---:|---:|---|---:|
| `perpendicular_line` | 29 | `5 / 18` | `6 / 11` | **`11 / 29`** | 37.93% | `[22.69%, 56.00%]` | 0 |
| `parallel_plane` | 23 | `5 / 18` | `2 / 5` | **`7 / 23`** | 30.43% | `[15.60%, 50.87%]` | 0 |
| `parallel_two_lines` | 20 | `2 / 18` | `0 / 2` | **`2 / 20`** | 10.00% | `[2.79%, 30.10%]` | 0 |
| **Tổng cộng** | **72** | **`12 / 54`** | **`8 / 18`** | **`20 / 72`** | **27.78%** | **`[18.76%, 39.05%]`** | **0** |

### 4.3. Theo loại câu hỏi (`question_type` trên 72 bài dương tính `SERVE`)

| Loại câu hỏi (`question_type`) | Tổng bài `SERVE` | `P-B` (`SERVED_CORRECT`) | `P-A` (`SERVED_CORRECT`) | Tổng `SERVED_CORRECT` | Tỷ lệ (%) | 95% Wilson CI | `WRONG_SERVED` |
|---|---:|---:|---:|---:|---:|---|---:|
| `section_only` | 24 | `6 / 18` | `4 / 6` | **`10 / 24`** | 41.67% | `[24.47%, 61.17%]` | 0 |
| `area_only` | 24 | `6 / 18` | `4 / 6` | **`10 / 24`** | 41.67% | `[24.47%, 61.17%]` | 0 |
| `section_and_area` | 24 | `0 / 18` | `0 / 6` | **`0 / 24`** | 0.00% | `[0.00%, 13.80%]` | 0 |
| **Tổng cộng** | **72** | **`12 / 54`** | **`8 / 18`** | **`20 / 72`** | **27.78%** | **`[18.76%, 39.05%]`** | **0** |

> **Quan sát trọng tâm:** Khi xét riêng các bài câu hỏi đơn (`section_only` và `area_only`, tổng `48` bài dương tính), tỷ lệ phục vụ đúng đạt **`20 / 48 = 41.67%`** (`P-B`: `12 / 36 = 33.33%`; `P-A`: `8 / 12 = 66.67%`). Toàn bộ `24 / 24` bài câu hỏi ghép `section_and_area` bị chặn tại cổng ngôn ngữ `SOURCE_GROUNDING` (`SOURCE_OBJECT_MISMATCH`) do câu hỏi ghép tách rời khỏi câu định nghĩa mặt phẳng cắt.

---

## 5. Kiểm Chứng Độc Lập Hiệu Quả Của Các Đợt Sửa `W2-M1..W2-M5`

Đợt đánh giá mù Wave 3 cung cấp bằng chứng độc lập trực tiếp về các bản sửa sau Wave 2:

1. **Kiểm chứng `W2-M4` (Exact Radical Normalization — `RADICAL_DOMAIN_OVERFLOW`):**
   - Trong Wave 2 ban đầu, các bài có số đo nguyên tố/hợp số lớn sinh ra biểu thức căn lồng hoặc radicand lớn gây lỗi `RADICAL_DOMAIN_OVERFLOW`.
   - Trong Wave 3, toàn bộ `72` bài dương tính được thiết kế với các bộ số đo nguyên tố cùng nhau lớn (`13, 17, 19, 23, 29, 31`) và tỷ số cắt mẫu số lớn (`2/11, 3/11, 4/13, 3/16`), tạo ra các `area_squared` có tử số và mẫu số lên tới hàng tỷ (ví dụ `W3-B10`: `area_squared = 4817160208809/6468687500`).
   - Kết quả trên Wave 3: **`0 / 72` lỗi `RADICAL_DOMAIN_OVERFLOW`** (`100%` bài đi tới Engine đều rút gọn căn chính xác và khớp tuyệt đối `area_squared` với oracle).
2. **Kiểm chứng `W2-M5` (Adapter `/4` Category A Identity & Primed-Vertex Repair):**
   - Trong Wave 2 sau M4, các bài Category A (`DINH_CAT_CANH`) có `through_point` là đỉnh khối (đặc biệt là đỉnh trên có dấu phẩy `A'`) bị Adapter `/4` từ chối oan với `PREVIEW_RESULT_INVALID`.
   - Trong Wave 3, toàn bộ **`8 / 8` (`100.00%`)** bài Category A vượt qua `Source Gate` (`W3-A01`, `W3-A04`, `W3-A05`, `W3-A07`, `W3-A08`, `W3-A11`, `W3-A13`, `W3-A14` — bao gồm cả bài có `through_point` là đỉnh có dấu phẩy `A'`, `M'`, `P'` trên lăng trụ/hình hộp và điểm chia cạnh bên) đều được Adapter `/4` phục vụ thành công (`SERVED_CORRECT`), khớp 100% với oracle và không có bất kỳ lỗi `PREVIEW_RESULT_INVALID` hay rò rỉ `_prime` nào.
   - Đồng thời, trên 2 bài âm tính đối kháng thuộc lớp `incorrect_stated_intersections` (`W3-N54`, `W3-N55` — nơi đề bài khai báo các giao điểm cạnh bên không đồng phẳng với mặt phẳng cắt), sau khi route tính giao điểm từng đường, **Adapter `/4` đã phát hiện đa giác không đồng phẳng/không khép kín và chặn lại bằng `PREVIEW_RESULT_INVALID`**, giữ vững `wrong_served = 0`.

---

## 6. Chẩn Đoán Chi Tiết 5 Cụm Từ Chối Sai (`52` Bài `FALSE_REFUSAL`)

Toàn bộ `52 / 52` (`100%`) trường hợp `FALSE_REFUSAL` trên bài dương tính đều xảy ra tại tầng **`SOURCE_GROUNDING` (`kiem_nguon` trong `registry.py`)**. Không có bất kỳ bài dương tính nào thất bại ở Planner `/17`, Engine `/14`, Adapter `/4`, hay Certificate `/1`.

| Mã cụm | Mã từ chối (`code`) | Số bài | Tỷ trọng | Danh sách bài bị ảnh hưởng | Nguyên nhân kỹ thuật xác định |
|---|---|---:|---:|---|---|
| **`W3-F1`** | `SOURCE_OBJECT_MISMATCH` | **24** | 46.15% | `W3-B03, W3-B06, W3-B09, W3-B12, W3-B15, W3-B18, W3-B21, W3-B24, W3-B27, W3-B30, W3-B33, W3-B36, W3-B39, W3-B42, W3-B45, W3-B48, W3-B51, W3-B54, W3-A03, W3-A06, W3-A09, W3-A12, W3-A15, W3-A18` | Trong cả 24 bài `section_and_area`, câu định nghĩa mặt phẳng cắt `(P)` và câu hỏi ghép (`"Hãy xác định thiết diện tạo bởi mặt phẳng (P) với hình ... và tính diện tích của thiết diện đó"`) tách thành hai câu riêng. Khi `derived_section.source.quote` trỏ vào câu hỏi, `kiem_nguon` đòi hỏi quote của `derived_section` phải tự chứa lại cả `through_point` và quan hệ song song/vuông góc của `(P)` thay vì liên kết qua tên mặt phẳng `(P)` đã định nghĩa ở câu trước. |
| **`W3-F2`** | `PREDICATE_NOT_IN_QUOTE` | **14** | 26.92% | `W3-B02, W3-B04, W3-B14, W3-B20, W3-B22, W3-B28, W3-B31, W3-B32, W3-B38, W3-B40, W3-B46, W3-A02, W3-A10, W3-A16` | Gồm 2 nhánh từ vựng: (a) **10 bài** dùng từ nối tỷ số chuẩn tiếng Việt `"thỏa mãn"` hoặc `"với"` (`"lấy điểm K thỏa mãn SK = 3/7 SM"`, `"chọn điểm I với SI = 3/8 SP"`) trong khi `divide_segment` chỉ chấp nhận từ khóa cứng `'sao cho'`; (b) **4 bài** `oblique_triangular_prism` diễn đạt chân đường cao là `"chân đường cao kẻ/hạ từ A' đến/xuống mặt phẳng (ABC) là B"` trong khi `orthogonal_projection` chỉ chấp nhận từ khóa cứng `'hình chiếu'`. |
| **`W3-F3`** | `SOURCE_PREMISE_UNREAD` | **10** | 19.23% | `W3-B07, W3-B08, W3-B16, W3-B26, W3-B34, W3-B35, W3-B43, W3-B44, W3-B52, W3-B53` | Bộ kiểm tra lát cắt văn phạm toàn bài (`văn phạm lát hai đường`) cho quan hệ `parallel_two_lines` từ chối các câu tiền đề ghép hoặc cụm `"đồng thời song song với hai đường thẳng ... và ..."` khi không khớp khít mẫu câu cứng. |
| **`W3-F4`** | `UNGROUNDED_VALUE` | **3** | 5.77% | `W3-B47, W3-B50, W3-A17` | Ở 3 bài `cube`, độ dài cạnh hình lập phương được phát biểu qua mặt đáy (`"biết mặt đáy MNPQ là hình vuông có cạnh bằng 9a"`), nhưng `kiem_nguon` không gắn giá trị `9a` cho `segment_length(M, N)` nếu thiếu cụm `"hình lập phương ... có cạnh"` hoặc `"MN = 9a"`. |
| **`W3-F5`** | `CONDITIONAL_CLAUSE` | **1** | 1.92% | `W3-B01` | Đề bài mở đầu mệnh đề lấy điểm bằng từ `"Giả sử H là điểm thuộc cạnh bên SE sao cho SH = 3/11 SE. Mặt phẳng (P) đi qua H..."`; do quote của `derived_section` bao trùm hai câu, bộ lọc chuỗi con `"giả sử"` kích hoạt nhầm `CONDITIONAL_CLAUSE`. |

---

## 7. Phân Tích 18 Lớp Âm Tính / Đối Kháng (`72` Bài `REFUSE`)

Toàn bộ `72 / 72` (`100.00%`) bài âm tính đều bị từ chối an toàn (`0` `WRONG_SERVED`), trong đó `60 / 72` (`83.33%`) khớp chính xác nhóm lý do dự kiến (`REFUSED_CORRECT_REASON`) và `12 / 72` (`16.67%`) bị từ chối ở một tầng/nhóm sớm hơn (`REFUSED_REASON_DISAGREEMENT`).

| Lớp âm tính (`negative_class`) | Tổng | `REFUSED` | `REFUSED_CORRECT_REASON` | `REFUSED_REASON_DISAGREEMENT` | `WRONG_SERVED` |
|---|---:|---:|---:|---:|---:|
| `wrong_solid_kind` | 4 | 4 | 4 | 0 | 0 |
| `wrong_solid_notation` | 4 | 4 | 4 | 0 | 0 |
| `mixed_solid_operands` | 4 | 4 | 4 | 0 | 0 |
| `unproven_parallel_or_perpendicular_relation` | 4 | 4 | 4 | 0 | 0 |
| `wrong_ratio` | 4 | 4 | 4 | 0 | 0 |
| `wrong_edge` | 4 | 4 | 4 | 0 | 0 |
| `invalid_section_declaration` | 4 | 4 | 4 | 0 | 0 |
| `primed_label_identity_ambiguity` | 4 | 4 | 4 | 0 | 0 |
| `source_provenance_mismatch` | 4 | 4 | 4 | 0 | 0 |
| `missing_mandatory_premise` | 4 | 4 | 3 | 1 (`W3-N20`) | 0 |
| `ambiguous_source_labels` | 4 | 4 | 3 | 1 (`W3-N25`) | 0 |
| `impossible_vertex` | 4 | 4 | 3 | 1 (`W3-N38`) | 0 |
| `unsupported_geometry_capability` | 4 | 4 | 3 | 1 (`W3-N47`) | 0 |
| `conflicting_section_area_requests` | 4 | 4 | 3 | 1 (`W3-N49`) | 0 |
| `category_a_b_semantic_contradictions` | 4 | 4 | 3 | 1 (`W3-N58`) | 0 |
| `geometry_degeneration` | 4 | 4 | 3 | 1 (`W3-N72`) | 0 |
| `contradictory_source_facts` | 4 | 4 | 2 | 2 (`W3-N02, W3-N03`) | 0 |
| `incorrect_stated_intersections` | 4 | 4 | 1 | 3 (`W3-N53, W3-N54, W3-N55`) | 0 |
| **Tổng cộng** | **72** | **72 (100%)** | **60 (83.33%)** | **12 (16.67%)** | **0 (0%)** |

---

## 8. Kết Quả Track B (Khả Năng Biểu Diễn Hợp Đồng) & Track C (Ngữ Nghĩa Scene3D)

1. **Track B (`results/scored-run-1/track-b.json`):**
   - `representable_without_loss`: `72 / 144` (toàn bộ `72` bài `SERVE`).
   - `representable_with_explicit_gap`: `64 / 144` (`16` lớp âm tính có thể biểu diễn trên `typed-fact-next/2` kèm lỗ hổng ngữ nghĩa/hình học tường minh).
   - `intentionally_outside_supported_v2_capability`: `8 / 144` (`wrong_solid_kind` và `unsupported_geometry_capability`).
2. **Track C (`scene3d_semantics` trong `results/scored-run-1/summary.json`):**
   - Số bài phục vụ được kiểm tra: `20 / 20`.
   - Rò rỉ danh tính nguồn (`track_c_source_identity_leak_cases`): **`0` bài (`[]`)**.
   - Rò rỉ mã máy `_prime` ra bề mặt người học (`track_c_machine_id_leak_cases`): **`0` bài (`[]`)**.
   - Điểm phụ sư phạm (`track_c_r2_auxiliary_notation_cases`): `20 / 20` bài đều gắn đúng `origin = "derived"` và phân biệt rõ với điểm đề bài (`track_c_all_auxiliary_visibly_distinguished = true`).

---

## 9. Kết Luận Nghiên Cứu

1. **Tính đúng đắn toán học & cơ chế fail-closed đạt mức tuyệt đối (`100%`):**
   - Trên toàn bộ `144` bài mới hoàn toàn của Holdout Wave 3, Hybrid V2 đạt **`0 / 144` (`0.00%`) `WRONG_SERVED`**, **`20 / 20` (`100.00%`) đồng thuận tuyệt đối với oracle hữu tỷ chính xác** trên mọi bài được phục vụ, và **`72 / 72` (`100.00%`) từ chối an toàn** trên mọi bài âm tính/đối kháng.
2. **Các bản sửa `W2-M4` (Exact Radical) và `W2-M5` (Adapter `/4` Category A Identity) đã khái quát hóa thành công 100% sau cổng ngôn ngữ:**
   - Mọi bài toán (`20 / 20`, gồm `12` bài Category B và `8` bài Category A) vượt qua được tầng kiểm tra trích dẫn `Source Gate` đều đi trọn vẹn qua `Planner /17 -> Engine /14 -> Adapter /4 -> Certificate /1` với tỷ lệ thành công **`100%` (`0` lỗi tràn căn `RADICAL_DOMAIN_OVERFLOW`, `0` lỗi từ chối oan Category A `PREVIEW_RESULT_INVALID`, `0` lỗi rò rỉ `_prime`)**.
3. **Điểm nghẽn khái quát hóa còn lại nằm tập trung 100% ở tầng `Source Gate` (`52 / 52` false refusals):**
   - Tỷ lệ phục vụ tổng thể đạt `20 / 72` (`27.78%`; riêng câu hỏi đơn `section_only` + `area_only` đạt `20 / 48 = 41.67%`, riêng `Category A` câu hỏi đơn đạt `8 / 12 = 66.67%`).
   - Cả `52` trường hợp từ chối sai đều tập trung vào 5 mẫu câu tiếng Việt tự nhiên trong `kiem_nguon` (`W3-F1`: câu hỏi ghép `section_and_area` tách câu định nghĩa mặt phẳng — `24` bài; `W3-F2`: từ khóa `'thỏa mãn'`/`'với'` cho `divide_segment` và `'chân đường cao'` cho `orthogonal_projection` — `14` bài; `W3-F3`: văn phạm lát cắt `parallel_two_lines` — `10` bài; `W3-F4`: cạnh hình lập phương nêu qua mặt đáy — `3` bài; `W3-F5`: từ mở đầu `'Giả sử'` — `1` bài).
   - Hiện trạng này xác nhận chính xác quyết định giữ `DEFAULT_MODE = LLM_ONLY` và cung cấp danh mục 5 cụm ngôn ngữ định lượng rõ ràng nếu Owner quyết định mở wave cải tiến Source Gate tiếp theo.
