# BÁO CÁO WAVE: PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION

## 1. TỔNG QUAN VÀ TRẠNG THÁI BẮT BUỘC

Wave **`PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION`** thực hiện kiểm toán mã nguồn, so sánh ba họ bài ứng viên, lựa chọn họ bài hình học không gian thứ hai phù hợp để mở rộng deterministic primitive compiler, và thực hiện tiền đăng ký toàn diện (manifest, ground truth, gap audit, eligibility specification, test suite và kế hoạch benchmark sau triển khai).

Wave này **chỉ lựa chọn và tiền đăng ký**, chưa triển khai compiler cho họ mới, chưa thay đổi routing và chưa chuyển kiến trúc mặc định (`DEFAULT_MODE = LLM_ONLY`).

### Trạng thái căn bản và vai trò commit
```text
WAVE_ID = PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION
BRANCH = feat/photo-problem-to-scene
START_HEAD = 6ec2e0d3837246d04f5fc9fcf27bb09d78b73997
MAIN_HEAD_EXPECTED = 085cae67392d3607ad0a58a7f48c17d8a5e5157d
CODE_COMMIT = abb377b89a4a2e13be9c5b4bc06984e149ac8566
REPORT_BASE_HEAD = abb377b89a4a2e13be9c5b4bc06984e149ac8566
REPORT_COMMIT_ROLE = SELF
DATE = 2026-09-22
VERIFICATION_MODE = 100% OFFLINE
HISTORICAL_INTEGRITY_LABEL = LF_NORMALIZED_CONTENT_PARITY
SELECTED_FAMILY_ID = right_triangle_base_right_prism_volume
```

### Bất biến vận hành (100% Offline)
* `NEW_GEMINI_REQUESTS = 0`
* `NETWORK_REQUESTS = 0`
* `DOTENV_PRESENT = NO`
* `API_KEY_LOADED = NO`
* `PRODUCT_CODE_CHANGED = NO`
* `PROMPT_CHANGED = NO`
* `SCHEMA_CHANGED = NO`
* `FACT_GRAPH_CHANGED = NO`
* `COMPILER_CHANGED = NO`
* `ROUTING_CHANGED = NO`
* `DEFAULT_MODE = LLM_ONLY`
* `CANDIDATE_SHA256 = 077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1` (103 tệp verified)
* `CACHE_VERSION = 99`

---

## 2. KIỂM TOÁN NĂNG LỰC HỆ THỐNG HIỆN TẠI (SOURCE AUDIT)

1. **Primitive Registry:**
   - Phiên bản: `geometry-primitives/1` tại `backend/app/simulation/geometry_compiler/primitives.py:136-143`.
   - Số lượng: Đúng 6 primitives (`assign_final_memory`, `construct_pyramid`, `construct_triangle`, `declare_point`, `measure_quantity`, `memory_declaration`).
2. **Semantic Program IR & Phép Đo:**
   - Trong `contract.py:707`, `MeasureExpr` là một **biểu thức giá trị (`ValueExpr`)**, không phải câu lệnh độc lập (`SemanticStatement`).
   - Phép đo được thực thi chuẩn mực qua câu lệnh gán: `AssignStmt(target_var=..., expr=MeasureExpr(quantity=..., of=..., wrt=...))`.
3. **FactGraph:**
   - Phiên bản: `geometry-fact-graph/2` tại `backend/app/simulation/geometry_compiler/fact_graph.py:34-80`.
   - Nút (`LOAI_NUT`): `point`, `segment`, `plane`, `triangle`, `pyramid`, `measurement_request`.
   - Sự kiện (`LOAI_FACT`): `incidence`, `length`, `perpendicular_lines`, `perpendicular_line_plane`, `base_of`, `apex_of`, `lies_in_plane`, `requested_operation`.
   - Bất biến xuất xứ: `LAYOUT_DERIVED` là metadata nội bộ của compiler để gắn xuất xứ trình bày cho toạ độ; không phải dữ kiện `GIVEN`, và không đi qua `model_assumption`.
4. **Structured Relations:**
   - Tại `backend/app/simulation/semantic_program/structured_relations.py:52-56`.
   - Hỗ trợ `perpendicular_lines` và `perpendicular_line_plane` với kiểm tra mâu thuẫn hình học `MULTIPLE_RIGHT_ANGLE_VERTICES_IN_TRIANGLE`.
5. **Scene Builder & Kernel Measurement:**
   - `scene3d.py:47-49`: Hỗ trợ render đối tượng `solid` dưới dạng `mesh` trong Three.js frontend.
   - `geometry_exec.py:248-275`: `volume_polyhedron` ủy quyền cho `section.the_tich_da_dien` tính thể tích chính xác bằng phân số `Fraction` cho mọi `Polyhedron`.

---

## 3. MA TRẬN ĐÁNH GIÁ VÀ LỰA CHỌN HỌ THỨ HAI

Đánh giá ba ứng viên theo 7 tiêu chí với thang điểm 0–5, quy đổi trọng số 100:

| Tiêu chí | Trọng số | A: `rectangular_base_pyramid_volume` | B: `right_triangle_base_right_prism_volume` | C: `rectangular_prism_volume` |
|---|---:|:---:|:---:|:---:|
| 1. Phù hợp chương trình THPT | 20 | 5.0/5 (20.0) | 5.0/5 (20.0) | 5.0/5 (20.0) |
| 2. Tái sử dụng primitive/IR | 20 | 4.5/5 (18.0) | 4.5/5 (18.0) | 4.0/5 (16.0) |
| 3. Dữ kiện structured contract | 15 | 3.0/5 (9.0) | 4.5/5 (13.5) | 3.0/5 (9.0) |
| 4. Công thức và suy luận tất định | 15 | 5.0/5 (15.0) | 5.0/5 (15.0) | 5.0/5 (15.0) |
| 5. Tái sử dụng scene builder/frontend | 10 | 5.0/5 (10.0) | 5.0/5 (10.0) | 5.0/5 (10.0) |
| 6. Ca âm và mã từ chối rõ ràng | 10 | 4.5/5 (9.0) | 5.0/5 (10.0) | 4.5/5 (9.0) |
| 7. Rủi ro triển khai thấp | 10 | 3.5/5 (7.0) | 4.5/5 (9.0) | 3.5/5 (7.0) |
| **TỔNG ĐIỂM XẾP HẠNG** | **100** | **88.0 / 100** | **95.5 / 100** | **86.0 / 100** |

### Kết luận lựa chọn:
* **Họ được chọn:** `right_triangle_base_right_prism_volume` (Hình lăng trụ đứng có đáy là tam giác vuông).
* **Điểm số:** **95.5 / 100** (cao nhất, cách biệt 7.5 điểm so với họ đứng thứ hai).
* **Họ đứng thứ hai (Runner-up):** `rectangular_base_pyramid_volume` (88.0 / 100).
* **Tie-break:** Không cần sử dụng (`tie_break_used = false`).
* **Lý do lựa chọn:**
  1. Tận dụng 100% năng lực biểu diễn góc vuông đáy và cạnh bên vuông góc đáy hiện có trong `structured_relations` mà không cần mở rộng `RELATION_KINDS`.
  2. Mở rộng giá trị nghiên cứu cốt lõi: chuyển đổi từ topology khối chóp (pyramid - 4 đỉnh) sang topology khối lăng trụ (prism - 6 đỉnh, 2 mặt đáy, 3 mặt bên tứ giác).
  3. Rủi ro triển khai thấp nhất, chỉ cần đăng ký 1 primitive dựng khối `construct_prism`.

---

## 4. KIỂM TOÁN GAP VÀ ĐĂNG KÝ HỢP ĐỒNG HỌ LĂNG TRỤ (PRISM AUDIT)

1. **RequestContract:** Thể tích khối lăng trụ tiếp tục sử dụng `ObligationSpec(kind="volume", subject="solid")`.
2. **FactGraph:** Khối lăng trụ sẽ được đăng ký nút `"prism"` trong `LOAI_NUT` ở wave vertical slice.
3. **Sáu đỉnh và ánh xạ hai đáy (Correspondence):**
   - Đáy dưới: $A, B, C$
   - Đáy trên: $D, E, F$
   - Ánh xạ 1-1 tương ứng: $A \leftrightarrow D, B \leftrightarrow E, C \leftrightarrow F$.
   - Các cạnh đáy tương ứng song song và bằng nhau ($AB \parallel DE, BC \parallel EF, CA \parallel FD$; $AB = DE, BC = EF, CA = FD$).
4. **Quan hệ cạnh bên:**
   - Ba cạnh bên song song và bằng nhau ($AD \parallel BE \parallel CF$; $AD = BE = CF = h$).
   - Lăng trụ đứng: $AD \perp (ABC)$ (khớp `perpendicular_line_plane`).
5. **Scene Topology và Grounding:**
   - 6 đỉnh, 9 cạnh, 5 mặt (2 đáy tam giác $[A, C, B], [D, E, F]$ và 3 mặt bên tứ giác $[A, B, E, D], [B, C, F, E], [C, A, D, F]$).
   - Euler characteristic: $V - E + F = 6 - 9 + 5 = 2$.
   - Toạ độ chính tắc: $A(0,0,0), B(len_1, 0, 0), C(0, len_2, 0)$, $D(0, 0, h), E(len_1, 0, h), F(0, len_2, h)$. Mang xuất xứ `LAYOUT_DERIVED` nội bộ của compiler.
6. **Hợp đồng Primitive mới đăng ký:**
   - `primitive_id`: `construct_prism`
   - `signature`: `construct_prism(name: str, base_cycle: tuple[str, ...], top_cycle: tuple[str, ...], correspondence: tuple[tuple[str, str], ...]) -> dict[str, Any]`
   - `semantic_output`: `construct_solid` với 6 đỉnh và 5 mặt.
   - `failure_codes`: `PRISM_VERTICES_MISMATCH`, `PRISM_DEGENERATE_FACES`, `PRISM_CORRESPONDENCE_INVALID`.

---

## 5. BỘ DỮ LIỆU TIỀN ĐĂNG KÝ (8 CA OFFLINE ĐỘC LẬP)

Toàn bộ 8 ca tuân thủ chính sách nhãn `NO_APOSTROPHE_UPPERCASE_ASCII` (không dùng ký hiệu `A'`), không chứa `expected_answer` trong input của manifest, và có đáp số được tính độc lập bằng tay:

| Mã Ca | Loại Ca | Mô Tả Tóm Tắt | Đáy Vuông | Chiều Cao | Thể Tích Lý Thuyết | Trạng Thái Kỳ Vọng | Mã Từ Chối Kỳ Vọng |
|---|---|---|---|---|---|---|---|
| **PRISM_P01** | Dương | Cơ bản số nguyên ($A, B, C, D, E, F$) | $A$ ($AB=3, AC=4$) | $AD=5$ | $V = 30$ | `SUPPORTED` | — |
| **PRISM_P02** | Dương | Hoán đổi nhãn ($M, N, P, Q, R, S$) | $M$ ($MN=6, MP=8$) | $MQ=7$ | $V = 168$ | `SUPPORTED` | — |
| **PRISM_P03** | Dương | Phân số chính xác | $A$ ($AB=3/2, AC=4/3$) | $AD=5/4$ | $V = 5/4$ | `SUPPORTED` | — |
| **PRISM_P04** | Dương | Đổi đỉnh vuông đáy | $B$ ($BA=5, BC=12$) | $BE=6$ | $V = 180$ | `SUPPORTED` | — |
| **PRISM_P05** | Dương | Đổi thứ tự dữ kiện, đủ top base & correspondence | $A$ ($AC=6, AB=8$) | $AD=10$ | $V = 240$ | `SUPPORTED` | — |
| **PRISM_N01** | Âm | Thiếu dữ kiện chiều cao bắt buộc | $A$ ($AB=3, AC=4$) | Thiếu $AD$ | Không xác định | `REJECTED` | `REQUIRED_FACT_MISSING` |
| **PRISM_N02** | Âm | Mâu thuẫn quan hệ (vuông ở cả $A$ và $B$) | $A$ và $B$ mâu thuẫn | $AD=6$ | Không xác định | `REJECTED` | `STRUCTURED_RELATION_CONTRADICTION` |
| **PRISM_N03** | Âm | Lăng trụ xiên (đúng 1 lỗi: cạnh bên không $\perp$ đáy) | $A$ ($AB=3, AC=4$) | $AD=5$ ($\not\perp$) | Không xác định | `REJECTED` | `UNSUPPORTED_STRUCTURED_RELATION_MISSING` |

### Mã băm đông kết (Frozen Hashes - LF Normalized):
* `SECOND_FAMILY_SELECTION_MATRIX.json`: `748b04938952d84d9f40ed656697cfdac212a9cfc028d52e040b4fb46c521aa7`
* `SECOND_FAMILY_MANIFEST.json`: `f5978eb5f76b72808a02791dadc96f3b001b3bd288fc84e6656307ac4d0fefe5`
* `SECOND_FAMILY_GROUND_TRUTH.json`: `faf42e894fb9f69c8b61aba06f84767ec9806d1231633d2975516ec5367e18ce`

---

## 6. KIỂM THỬ VÀ THẨM ĐỊNH MÁY ĐỘC LẬP

1. **Validator chỉ đọc (`backend/scripts/validate_second_family_preregistration.py`):**
   - Đọc 3 tệp tĩnh, kiểm toán và thẩm định độc lập 18 tiêu chí.
   - Kết quả: `OVERALL PREREGISTRATION VALIDITY: PASS`.
2. **Bộ kiểm thử tự động (`backend/tests/geometry/test_second_family_preregistration.py`):**
   - 18 bài kiểm thử độc lập tương ứng 18 tiêu chí của đặc tả.
   - Kết quả: `18 passed in 3.47s`.
3. **Kiểm tra hồi quy họ thứ nhất (`test_geometry_primitive_compiler.py`):**
   - Kết quả: `41 passed in 0.77s`.
4. **Kiểm tra kiến trúc tài liệu (`audit_docs_information_architecture.py`):**
   - Kết quả: `=== DOCS INFORMATION ARCHITECTURE AUDIT: PASS ===`.
5. **Kiểm tra Candidate & Cache Lock:**
   - Candidate: `103 file, 077dbc6b7bf6f62f...` (KHỚP).
   - Cache lock: `CACHE_VERSION 99` (KHỚP).

---

## 7. KẾT LUẬN VÀ HÀNH ĐỘNG TIẾP THEO

Wave **`PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION`** đã hoàn thành trọn vẹn mục tiêu lựa chọn và tiền đăng ký họ lăng trụ đứng đáy tam giác vuông (`right_triangle_base_right_prism_volume`). Mọi tiêu chuẩn an toàn sản phẩm, bảo toàn working tree (`frontend/public/favicon.svg`), tính bất biến của lịch sử và không gian mã nguồn đều được bảo đảm tuyệt đối.

Hệ thống chính thức chuyển giao hành động tiếp theo:
```text
PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION = PASS
SECOND_FAMILY = right_triangle_base_right_prism_volume
IMPLEMENTATION_STARTED = NO
NEXT_ACTION = PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE
```
