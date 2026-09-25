# ARCHITECTURE CAPABILITY MATRIX

> **Kiểm kê năng lực kiến trúc toàn diện hậu merge `rectangular-pyramid`**  
> *Thời điểm kiểm kê:* 2026-09-25T16:15:00+07:00  
> *Quy tắc:* Khai thác trực tiếp từ mã nguồn thực tế, không suy luận từ báo cáo cũ.

---

## 1. Baseline & Post-Merge Tree Parity

| Tiêu chí | Giá trị thực tế | Đánh giá |
| :--- | :--- | :--- |
| **Commit `main` (Local)** | `d3651a73902ccfac6779043ba41e4f5009cd2ff1` | PASS (Khớp remote) |
| **Commit `origin/main`** | `d3651a73902ccfac6779043ba41e4f5009cd2ff1` | PASS |
| **Merged Feature Head** | `26c1787aa75bce019a4f37f920844c63282eb9b6` | PASS (Ancestor của `main`) |
| **Merge Base** | `bb3d5dbb7a91b71c3005dbfbd0282f06c5b8b75a` | PASS |
| **Tree SHA Feature Head** | `5baea3a4f9c6a219657f88bcbb75cfe5218ac92e` | PASS |
| **Tree SHA Main Head** | `5baea3a4f9c6a219657f88bcbb75cfe5218ac92e` | PASS (Trùng khớp từng byte) |
| **`git diff --exit-code 26c1787a d3651a73`** | Rỗng (Mã thoát 0) | **TREE_BYTE_PARITY = PASS** |
| **Candidate Verification** | `freeze_evaluation_candidate.py --verify` | **PASS** (103 tệp, hash `9b4678410455b570…`) |
| **Cache Verification** | `lock_cache_identity.py --verify` | **PASS** (`CACHE_VERSION 101`) |
| **Working Tree Hygiene** | ` D frontend/public/favicon.svg` (Unstaged) | **PASS** (Bảo toàn thay đổi của người dùng) |

---

## 2. Kiểm kê Kiến trúc Thực tế (Architecture Inventory)

### A. Input và Contract
1. **Đầu vào văn bản (Text Input):**
   - Điểm vào: `POST /api/analyze`.
   - Tiền xử lý văn bản tiếng Việt: chuẩn hoá khoảng trắng, ký hiệu toán học, tách các span dữ kiện đề bài.
2. **Đầu vào ảnh (Image Input):**
   - Điểm vào: `POST /api/image/extract` (`app/ingestion/image_extraction.py`, `app/ingestion/image.py`).
   - Chế độ vận hành: Provider multimodal chỉ chép đề thành bản ghi cấu trúc `ImageProblemExtraction` bằng `VISION_TRANSPORT_SCHEMA`.
   - **Ranh giới an toàn (Safety Boundary):** Server phán quyết tất định (`assess_extraction`). Khi ảnh chỉ có hình mà không có đề chữ (`MISSING_PROBLEM_TEXT`), `apply_diagram_only_provenance_guard` cách ly triệt để mọi dữ kiện đọc từ hình khỏi bản công khai. Người học buộc phải gõ lại văn bản đề bài trước khi vào pipeline dựng.
3. **Analyze Schema:**
   - Lược đồ Pydantic nghiêm ngặt: `input_facts`, `obligations`, `prescribed_procedure`, `geometric_relations`, `solid_topology`.
4. **RequestContract (`app/simulation/semantic_program/request_contract.py`):**
   - Bất biến sau khi server đóng băng:
     - `obligations`: danh sách nghĩa vụ sư phạm (`Obligation`).
     - `input_facts`: dữ kiện đề cho (`InputFact`).
     - `scale_binding`: chuẩn hoá thang đo tỉ lệ.
     - `source_invariants`: ràng buộc nguồn từ câu chữ đề bài do server phát (`SourceInvariant`).
     - `geometric_relations`: quan hệ hình học có cấu trúc (`GeometricRelation`).
     - `solid_topology`: cấu trúc tô-pô khối (`PrismTopologySpec | PyramidTopologySpec | None`).
     - `problem_text`: văn bản đề bài nguyên văn phục vụ kiểm tra nguồn.
5. **Topology Specifications:**
   - `PrismTopologySpec`: `solid_kind="prism"`, `base_cycle`, `top_cycle`, `correspondence`.
   - `PyramidTopologySpec`: `solid_kind="pyramid"`, `apex`, `base_cycle`, `base_shape` (`rectangle` | `square`).
6. **Structured Relations (`app/simulation/semantic_program/structured_relations.py`):**
   - `RELATION_KINDS = ("perpendicular_lines", "perpendicular_line_plane")`.
   - Chuẩn hoá đỉnh chính tắc (canonical sorted vertices), chống trùng lặp, xác thực tham chiếu về `source_invariants`.
7. **Cổng kiểm tra Grounding & Fail-closed:**
   - `NormalizedSourceInvariantGate`: kiểm tra dữ kiện nguồn trên trạng thái cuối của bộ nhớ.
   - `GroundingGate`: buộc mọi biến hình học phải truy về `source_fact_id` hoặc khai `model_assumption` hợp lệ cho toạ độ bố cục.
   - `VisualObligationCoverageGate`: đảm bảo mỗi obligation đều có đối tượng trực quan hiện diện trong Scene3D.
   - `SectionProvenanceNormalizer`: chuẩn hoá `polygon3` thành `section` khi thoả mãn quan hệ toán học với khối và mặt phẳng cắt.

---

### B. FactGraph (`app/simulation/geometry_compiler/fact_graph.py`)
1. **Loại nút (`LOAI_NUT`):** Bảng đóng:
   - `point`, `segment`, `plane`, `triangle`, `pyramid`, `prism`, `measurement_request`.
2. **Loại sự kiện (`LOAI_FACT`):** Bảng đóng:
   - `incidence`, `length`, `perpendicular_lines`, `perpendicular_line_plane`, `base_of`, `apex_of`, `lies_in_plane`, `requested_operation`.
3. **Trạng thái xuất xứ (Provenance States):**
   - `TRANG_THAI_FACT`: `GIVEN` (đề bài cho) hoặc `DERIVED` (suy ra có chứng minh).
   - `XUAT_XU_NUT`: `GIVEN`, `DERIVED`, hoặc `LAYOUT_DERIVED` (toạ độ bố cục compiler tự chọn).
4. **Bao đóng phụ thuộc (Dependency Closure):**
   - Mọi `Fact` dạng `DERIVED` bắt buộc phải có `derived_from` trỏ tới `fact_id` của các sự kiện cha. Không chấp nhận suy luận không rõ nguồn gốc.
5. **Xử lý mâu thuẫn (Contradiction Handling):**
   - Phát hiện xung đột tất định qua `kiem_mau_thuan`:
     - `INVALID_CONFLICT`: cùng một đoạn có hai độ dài khác nhau, hoặc quan hệ vừa khẳng định vừa phủ định.
     - `STRUCTURED_RELATION_CONTRADICTION`: tam giác có nhiều hơn 1 góc vuông (`MULTIPLE_RIGHT_ANGLE_VERTICES_IN_TRIANGLE`).
   - Xử lý: Ném lỗi `MauThuanFact`, kích hoạt từ chối an toàn fail-closed, tuyệt đối không lùi về LLM.

---

### C. Exact Geometry Kernel (`app/simulation/geometry/`)
1. **Biểu diễn số học:**
   - Hoàn toàn trên số hữu tỉ $\mathbb{Q}$ thông qua `Fraction`. Không sử dụng số dấu phẩy động `float` để so sánh hoặc tính toán trung gian.
   - Hoàn toàn không sử dụng ngưỡng sai số $\varepsilon$ (zero-tolerance).
2. **Các lớp thực thể hình học:**
   - `Point3` / `Vec3`: Vector/điểm bất biến trong $\mathbb{Q}^3$, hỗ trợ `add`, `sub`, `scale`, `dot`, `cross`, `norm_sq`.
   - `Segment3`: Đoạn thẳng hữu hạn giữa hai điểm phân biệt, có `length_sq`, `midpoint`, `vector`.
   - `Line3`: Đường thẳng vô hạn qua một điểm với vectơ chỉ phương khác không.
   - `Ray3`: Chưa có lớp riêng; hiện biểu diễn qua `Line3` hoặc `Segment3`.
   - `Plane3`: Mặt phẳng xác định qua `(point, normal)` hoặc từ phương trình hữu tỉ $ax + by + cz + d = 0$.
   - `Polygon3`: Chu trình các đỉnh `Vec3` đồng phẳng, kiểm tra không lặp đỉnh.
   - `Polyhedron`: Khối đa diện lồi xác định qua bảng đỉnh và danh sách mặt (`faces`).
   - `CurvedSolid`: Khối cong (hình cầu, trụ, nón) xác định qua tâm, trục, bán kính/chiều cao.
3. **Đại lượng vô tỉ bị cô lập (`app/simulation/geometry/radical.py`):**
   - `ExactNumber = Fraction | Radical` (căn thức dạng $a\sqrt{b}$ với $a, b \in \mathbb{Q}$).
   - Phép đo góc và khoảng cách thực hiện trên bình phương ($d^2, \cos^2 \theta$) trong $\mathbb{Q}$; chỉ lấy căn thức ở biên hiển thị hoặc biểu thức chính xác.
4. **Các phép dựng hạt nhân (`kernel.py` & `measure.py`):**
   - `midpoint`, `translate`, `divide_segment`, `intersect_line_plane`, `intersect_plane_plane`, `intersect_line_line`.
   - `project_point_onto_plane`, `project_point_onto_line`, `plane_through_point_perpendicular_to`.
   - `cross_section`: Dựng thiết diện bằng thuật toán duyệt mặt đa diện lồi, sinh bước dựng tuần tự.
   - `the_tich_da_dien`: Phân rã quạt có dấu, tính đúng thể tích cho cả đa diện lõm và lồi.

---

### D. Primitive Compiler (`app/simulation/geometry_compiler/`)
1. **Phiên bản:** `geometry-primitive-compiler/1`.
2. **Danh mục Primitives chuẩn (`primitives.py`):**
   - `declare_point`: Gán toạ độ bố cục cho đỉnh (`LAYOUT_DERIVED`).
   - `construct_triangle`, `construct_polygon`: Dựng đa giác từ các đỉnh.
   - `construct_line`: Dựng đường thẳng vô hạn qua 2 điểm.
   - `construct_segment`: Dựng đoạn thẳng hữu hạn giữa 2 điểm.
   - `construct_segments_group`: Dựng nhóm đoạn thẳng hữu hạn đồng thời trong một bước.
   - `construct_pyramid`: Dựng khối chóp từ đỉnh và đáy đa giác.
   - `construct_prism`: Dựng khối lăng trụ từ 2 đáy và quan hệ tương ứng.
   - `measure_quantity`: Biểu thức đo đại lượng hình học (`volume`, `area`, `distance`, `angle_cos_sq`, `radius`).
   - `assign_final_memory`: Gán kết quả vào biến mục tiêu (`witness`).
   - `memory_declaration`: Khai báo bộ nhớ kèm xuất xứ và giả định bố cục.
3. **Hành vi khi không hỗ trợ:**
   - Compiler trả về mã chẩn đoán đóng: `UNSUPPORTED_MISSING_FACT`, `UNSUPPORTED_EXTRA_OBLIGATION`, `UNSUPPORTED_STRUCTURED_RELATION_MISSING`, `INVALID_CONFLICT`, `INVALID_NON_POSITIVE_LENGTH`.
   - Tầng định tuyến (`routing.py`) quyết định chuyển sang `FALLBACK_TO_LLM` hoặc `REFUSE`.

---

### E. Ma Trận Đánh Giá Từng Họ Bài Toán (Problem Families Evaluation)

Không gộp chung nhãn "SUPPORTED", đánh giá độc lập từng tầng:

| Family ID | Contract | Analyze Schema | FactGraph | Compiler | Prod Route (`main`) | Scene3D | Pedagogical Trace | Browser Verified | Live Analyze | Fail-Closed |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`right_triangle_base_pyramid_volume`** | YES | YES | YES | YES | NO (`LLM_ONLY`) | YES | YES | YES | YES | YES |
| **`right_triangle_base_right_prism_volume`** | YES | YES | YES | YES | NO (`LLM_ONLY`) | YES | YES | YES | NO | YES |
| **`rectangular_base_pyramid_volume`** | YES | YES | YES | YES | NO (`LLM_ONLY`) | YES | YES | YES | NO | YES |
| **`rectangular_cuboid_and_cube_volume`** | NO | YES | NO | NO | NO | YES | NO | NO | NO | NO |
| **`regular_tetrahedron_volume`** | NO | NO | NO | NO | NO | YES | NO | NO | NO | NO |
| **`regular_pyramid_volume`** | NO | NO | NO | NO | NO | YES | NO | NO | NO | NO |
| **`oblique_prism_volume`** | NO | NO | NO | NO | NO | YES | NO | NO | NO | NO |
| **`cross_section_plane_polyhedron`** | YES | YES | NO | NO | YES (LLM) | YES | YES | PARTIAL | YES | YES |

*Ghi chú quan trọng:* `PRODUCTION_ROUTE_SUPPORTED` của cả 3 họ chóp/lăng trụ compiler đều là **NO** vì `DEFAULT_MODE = "LLM_ONLY"` vẫn được giữ nguyên trên `main` theo quy tắc an toàn (chưa hoàn thành 20 cổng di chuyển).

---

### F. Độ Bao Phủ Ngữ Nghĩa Của Renderer (Renderer Semantic Coverage)

| Đối tượng ngữ nghĩa | Trạng thái hiển thị | Chi tiết triển khai phía Frontend |
| :--- | :--- | :--- |
| **Point (Điểm)** | SUPPORTED | `point_marker`: Sphere mesh và nhãn chữ 3D bằng HTML billboard. |
| **Finite Segment (Đoạn thẳng)** | SUPPORTED | `segment`: Đoạn thẳng nối 2 đầu mút hữu hạn, không kéo dài vô tận. |
| **Infinite Line (Đường thẳng)** | SUPPORTED | `line`: Cắt theo bán kính bounding sphere của cảnh. |
| **Ray (Tia)** | PARTIAL | Chưa có render hint `ray` riêng; hiện mô phỏng qua `line` hoặc `segment`. |
| **Polygon / Base Region (Đáy)** | SUPPORTED | `polygon` / `mesh`: Tô mờ đa giác đáy với opacity 0.16 (nổi bật 0.35 khi chọn). |
| **Plane (Mặt phẳng)** | SUPPORTED | `surface`: Mặt phẳng bán trong suốt có viền khung giới hạn. |
| **Solid (Khối đa diện)** | SUPPORTED | `mesh`: Bề mặt đa diện mờ kết hợp khung dây wireframe. |
| **Visible / Hidden Edge (Khuất)** | SUPPORTED | `duongHaiLuot`: Tự động phân tách nét liền (thấy) và nét đứt (khuất). |
| **Perpendicular Marker (Góc vuông)** | SUPPORTED | Khung vuông góc tại chân đường cao nếu là chiều cao (`laChieuCao`). |
| **Provenance Highlight (Nhân quả)**| SUPPORTED | Chọn readout/vật thể -> Highlight toàn bộ chuỗi nhân quả màu `--accent-orange`. |
| **Step Scrubbing (Tua bước dựng)** | SUPPORTED | Slider timeline cho phép xem lại từng bước từ ban đầu tới hoàn tất. |

---

## 3. Phân Loại Khoảng Trống (Gap Classification)

Mỗi khoảng trống kỹ thuật được gán vào đúng một nhóm duy nhất:

### 1. `MISSING_CONTRACT`
- Hợp đồng `RequestContract` chưa có quan hệ song song (`parallel_lines`, `parallel_line_plane`, `parallel_planes`).
- Chưa có khái niệm tâm đa giác đáy (`center_of_polygon`, `centroid`) cho các bài toán chóp đều.
- Chưa có specification riêng biệt cho hình hộp chữ nhật (`CuboidTopologySpec`).

### 2. `MISSING_RELATION`
- `structured_relations.py` chỉ có 2 loại quan hệ vuông góc; chưa hỗ trợ quan hệ độ dài tỉ lệ (tỉ số đoạn thẳng, trung điểm, trọng tâm).
- Chưa có quan hệ góc giữa đường thẳng và mặt phẳng hoặc góc giữa hai mặt phẳng dưới dạng có cấu trúc.

### 3. `MISSING_EXACT_GEOMETRY`
- Thiếu lớp `Ray3` độc lập với tính chất nửa đường thẳng một đầu mút hữu hạn.
- Kernel `Vec3` thuần túy hữu tỉ $\mathbb{Q}^3$; chưa có `RadicalVec3` cho các điểm có toạ độ chứa căn vô tỉ (như đỉnh chóp tam giác đều hoặc tứ diện đều).

### 4. `MISSING_PRIMITIVE`
- Thiếu primitive `construct_cuboid` dựng nhanh hình hộp chữ nhật từ 3 kích thước dài, rộng, cao.
- Thiếu primitive dựng chóp đều từ tâm đáy và chiều cao (`construct_regular_pyramid`).

### 5. `MISSING_COMPILER_RULE`
- Compiler chưa có quy tắc phân xử cho hình hộp chữ nhật / hình lập phương (lăng trụ 4 đỉnh đáy có các mặt bên vuông góc đáy).
- Compiler chưa có quy tắc phân xử chóp đều (đáy đều, chân đường cao trùng tâm đáy).

### 6. `MISSING_PRODUCTION_ROUTING`
- `DEFAULT_MODE` trên nhánh chính vẫn là `LLM_ONLY`. Compiler hiện hoạt động dạng opt-in qua biến môi trường `GEOMETRY_COMPILER_MODE=DETERMINISTIC_FIRST`.

### 7. `MISSING_TRACE`
- Thiếu sinh trace sư phạm giải thích công thức diện tích/thể tích cho các họ hình chưa được compiler hỗ trợ.

### 8. `MISSING_RENDERER_SEMANTICS`
- Chưa có ký hiệu góc nhị diện (cung tròn góc giữa 2 mặt) trên không gian 3D.
- Chưa có render hint riêng biệt cho tia (`ray3`).

### 9. `MISSING_BROWSER_EVIDENCE`
- Chưa có bộ bằng chứng visual contact sheet tự động bằng Playwright cho họ lăng trụ đứng tam giác vuông (`right_triangle_base_right_prism_volume`).

### 10. `MISSING_LIVE_EXTRACTION_EVIDENCE`
- Chưa có đo lường live provider với các hợp đồng mở rộng gần đây (`PrismTopologySpec`, `PyramidTopologySpec` có `base_shape`).
