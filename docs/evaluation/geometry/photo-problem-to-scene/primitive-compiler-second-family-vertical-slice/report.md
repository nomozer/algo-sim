# Báo Cáo Triển Khai và Kiểm Chứng Lát Cắt Dọc Primitive Compiler Họ Bài Thứ Hai (Ngoại Tuyến)

> **WAVE_ID:** `PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE_OFFLINE`  
> **NGÀY:** 2026-09-22  
> **PHÂN LOẠI:** `VERTICAL_SLICE_IMPLEMENTATION_AND_VERIFICATION_OFFLINE`  
> **PRODUCT COMMIT:** `5a5534fe697b2162a1522ed1a1e38de774085f06` (ngắn: `5a5534fe`)  
> **EVIDENCE COMMIT ROLE:** `SELF`  
> **SỐ LẦN GỌI MODEL:** `0`  
> **SỐ LẦN GỌI MẠNG:** `0`  
> **CACHE_VERSION:** `100` (bump từ 99)  
> **EVALUATION CANDIDATE:** Commit `5a5534fe`, Cây sạch `True`, 103 files sản phẩm, Hash `fc88b200e9de094b31c78aef1e0883d28fa2f102bbb5bee7329f8a6c7063e24d`  
> **KẾT QUẢ ĐẠT:** `FINAL_DECISION = PASS` (`PRISM_VERTICAL_SLICE = VERIFIED`)

---

## 1. Tóm Tắt Nhiệm Vụ và Ranh Giới Kỹ Thuật

Wave này hiện thực và kiểm chứng trọn vẹn lát cắt dọc (vertical slice) tất định ngoại tuyến cho họ hình học thứ hai: **Lăng trụ đứng có đáy là tam giác vuông** (`right_triangle_base_right_prism_volume`), nối liền 5 tầng chuyển đổi:
$$\text{Analyze Payload} \xrightarrow{\text{Transport Schema}} \text{Canonical RequestContract} \xrightarrow{\text{Contract Adapter}} \text{FactGraph} \xrightarrow{\text{Primitive Compiler}} \text{SemanticProgramSpec IR}$$

Toàn bộ quá trình tuân thủ tuyệt đối các ràng buộc cốt lõi:
1. **100% Ngoại tuyến (Zero Network / Zero LLM calls):** 0 cuộc gọi mạng hay Gemini API.
2. **Bảo tồn tuyệt đối 3 file tiền đăng ký:** LF-normalized SHA-256 khớp từng bit với hash đã đăng ký tại Gate 1.
3. **Bảo vệ working tree người dùng:** Trạng thái xóa của file `frontend/public/favicon.svg` được bảo tồn nguyên vẹn; tuyệt đối không stage, sửa đổi hay khôi phục.
4. **Không đọc `problem_text` để suy luận hình học:** `DECLARED_VERTEX_UNIVERSE` được trích xuất hoàn toàn từ dữ liệu có cấu trúc (`structured_relations`, `solid_topology`).
5. **Phân định Provenance chặt chẽ:** `LAYOUT_DERIVED != GIVEN` và `LAYOUT_DERIVED != MODEL_ASSUMPTION`. Engine không bao giờ giả mạo `GIVEN`.

---

## 2. Xác Minh Tính Bất Biến Của Bộ Ca Tiền Đăng Ký

Ba file tiền đăng ký của họ bài thứ hai tại thư mục `docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/` được đọc trực tiếp và kiểm chứng LF-normalized SHA-256:

| Tên File | SHA-256 Kỳ Vọng Đã Đăng Ký | SHA-256 Thực Tế Đo Được | Trạng Thái |
|---|---|---|---|
| `SECOND_FAMILY_MANIFEST.json` | `f5978eb5f76b72808a02791dadc96f3b001b3bd288fc84e6656307ac4d0fefe5` | `f5978eb5f76b72808a02791dadc96f3b001b3bd288fc84e6656307ac4d0fefe5` | **BIT_IDENTICAL** |
| `SECOND_FAMILY_GROUND_TRUTH.json` | `faf42e894fb9f69c8b61aba06f84767ec9806d1231633d2975516ec5367e18ce` | `faf42e894fb9f69c8b61aba06f84767ec9806d1231633d2975516ec5367e18ce` | **BIT_IDENTICAL** |
| `SECOND_FAMILY_SELECTION_MATRIX.json` | `748b04938952d84d9f40ed656697cfdac212a9cfc028d52e040b4fb46c521aa7` | `748b04938952d84d9f40ed656697cfdac212a9cfc028d52e040b4fb46c521aa7` | **BIT_IDENTICAL** |

Toàn bộ 8 ca bài toán (5 dương: PRISM_P01–P05, 3 âm: PRISM_N01–N03) giữ nguyên vẹn dữ kiện đầu vào và đáp số kỳ vọng.

---

## 3. Các Thành Phần Mã Nguồn Sản Phẩm Đã Hiện Thực

Mã sản phẩm đã được hiện thực và hoàn thiện tại Commit 1 (`5a5534fe697b2162a1522ed1a1e38de774085f06`):

1. **`backend/app/simulation/geometry_compiler/primitives.py`**:
   - Thêm hàm primitive `construct_prism(name, base_cycle, top_cycle, correspondence)` sinh IR `construct_solid`.
   - Đăng ký vào `REGISTRY["construct_prism"]`.
   - Mở rộng helper `memory_declaration(..., provenance=None)`.

2. **`backend/app/simulation/semantic_program/contract.py`**:
   - Bổ sung `provenance: Optional[Literal["GIVEN", "MODEL_ASSUMPTION", "LAYOUT_DERIVED"]] = Field(None, ...)` vào `MemoryDeclaration` và `DeclarePointStmt`.

3. **`backend/app/simulation/semantic_program/request_contract.py`**:
   - Thêm lớp mô hình Pydantic bất biến `PrismTopologySpec(BaseModel)` với `solid_kind: Literal["prism"] = "prism"`, `base_cycle`, `top_cycle`, `correspondence`.
   - Bổ sung `solid_topology: Optional[PrismTopologySpec] = None` vào `RequestContract`.

4. **`backend/app/simulation/semantic_program/analyze_contract.py`**:
   - Cung cấp `_luoc_do_solid_topology()` với thuộc tính `solid_kind` bị khóa cứng vào enum `["prism"]` (không cho phép `pyramid` hay các loại khác đi qua schema transport).
   - Bổ sung `_doc_solid_topology(payload)` kiểm tra nghiêm ngặt fail-closed các thuộc tính topo.
   - Nạp `solid_topology` vào `build_request_contract()`.

5. **`backend/app/simulation/semantic_program/grounding_gate.py`**:
   - Xây dựng `_extract_declared_vertex_universe(contract: RequestContract) -> set[str]` hoàn toàn từ cấu trúc dữ liệu (`source_invariants`, `structured_relations`, `solid_topology`). Tuyệt đối không đọc `problem_text`.
   - Kiểm tra nghiêm ngặt các khai báo điểm mang provenance `LAYOUT_DERIVED`: từ chối nếu có witness, từ chối nếu không thuộc `DECLARED_VERTEX_UNIVERSE`.

6. **`backend/app/simulation/semantic_program/structured_relations.py`**:
   - Nâng cấp `diem_hop_dong(contract)` thu nhận thêm các đỉnh được khai báo trong `contract.solid_topology` (`base_cycle` + `top_cycle`), hỗ trợ chuẩn hóa quan hệ cho các ca thiếu dữ kiện cạnh (như `PRISM_N01`).

7. **`backend/app/simulation/geometry_compiler/fact_graph.py`**:
   - Bổ sung `"prism"` vào `LOAI_NUT`.
   - Lưu trữ `solid_topology` trong `GeometryFactGraph` và bao gồm trong `chinh_tac()`.

8. **`backend/app/simulation/geometry_compiler/contract_adapter.py`**:
   - Trích xuất `solid_topology` từ `RequestContract` và chuyển sang `dung_graph()`.

9. **`backend/app/simulation/geometry_compiler/compiler.py`**:
   - Đăng ký họ `SUPPORTED_FAMILY_PRISM = "right_triangle_base_right_prism_volume"`.
   - Hiện thực `RangBuocPrism`, `_danh_gia_eligibility_prism` kiểm tra đầy đủ dữ kiện đáy tam giác vuông, cạnh đứng vuông góc đáy, và độ dài 3 cạnh cần thiết. Xử lý fail-closed chính xác các ca âm (N01: thiếu cạnh AD, N02: xung đột góc vuông, N03: thiếu quan hệ vuông góc đường cao).
   - Hiện thực `_bien_dich_prism` sinh tọa độ giải tích 6 đỉnh $A, B, C, D, E, F$, câu lệnh `declare_point` gắn `LAYOUT_DERIVED`, lệnh `construct_triangle`, `construct_prism`, `measure_quantity` (diện tích đáy và thể tích lăng trụ), `assign_final_memory`, và 5 bước diễn hoạt sư phạm `BuocDung`.

10. **`backend/app/main.py` & Cache Lock**:
    - Tăng `CACHE_VERSION = "100"`.
    - Cập nhật và khóa `backend/cache_identity.lock.json` thông qua `lock_cache_identity.py` với UTF-8 encoding an toàn trên Windows.

---

## 4. Kết Quả Thực Nghiệm Benchmark Ngoại Tuyến

Tất cả 8 ca kiểm thử benchmark được đánh giá ngoại tuyến thông qua `test_prism_primitive_compiler.py`:

| Mã Ca | Loại Ca | Dữ Kiện Đầu Vào | Thể Tích Kỳ Vọng | Thể Tích Compiler | Trạng Thái Biên Dịch | Kết Quả |
|---|---|---|---|---|---|---|
| `PRISM_P01` | Dương | $AB=3, AC=4, AD=5$ | $30$ | $30$ | Thành công (6 đỉnh, `LAYOUT_DERIVED`) | **PASS** |
| `PRISM_P02` | Dương | $AB=6, AC=4, AD=5$ | $60$ | $60$ | Thành công (6 đỉnh, `LAYOUT_DERIVED`) | **PASS** |
| `PRISM_P03` | Dương | $AB=\frac{3}{2}, AC=\frac{4}{3}, AD=\frac{5}{4}$ | $\frac{5}{4}$ | $\frac{5}{4}$ | Thành công (phân số chính xác) | **PASS** |
| `PRISM_P04` | Dương | $AB=2, AC=2, AD=3$ | $6$ | $6$ | Thành công (tam giác vuông cân) | **PASS** |
| `PRISM_P05` | Dương | $AB=5, AC=12, AD=4$ | $120$ | $120$ | Thành công ($5, 12, 13$) | **PASS** |
| `PRISM_N01` | Âm | Thiếu độ dài cạnh đứng $AD$ | REJECTED | None | Từ chối: `REQUIRED_FACT_MISSING (AD)` | **PASS** |
| `PRISM_N02` | Âm | 2 góc vuông tại đỉnh $C$ | REJECTED | None | Từ chối: `CONFLICTING_FACTS` | **PASS** |
| `PRISM_N03` | Âm | Thiếu quan hệ $AD \perp (ABC)$ | REJECTED | None | Từ chối: `REQUIRED_FACT_MISSING (AD_perpendicular_base)` | **PASS** |

Tỷ lệ thành công benchmark: **8/8 (100%)**.

---

## 5. Kết Quả Kiểm Thử Bất Biến & Hồi Quy (Regression Parity)

Các bộ kiểm thử tự động được thực thi trên môi trường chuẩn của kho mã:

1. **Bộ kiểm thử lăng trụ mới (`backend/tests/geometry/test_prism_primitive_compiler.py`)**:
   - **25 / 25 PASSED**:
     - 2 tests bảo vệ tính bất biến hash tiền đăng ký và kiểm tra ranh giới import mã nguồn.
     - 2 tests kiểm tra đăng ký primitive và Pydantic specs.
     - 8 tests benchmark cho P01–P05 và N01–N03.
     - 10 tests bất biến tô-pô đa diện lăng trụ (`INV-TOPO-01` đến `INV-TOPO-10`).
     - 1 test bất biến phân định provenance (`LAYOUT_DERIVED != GIVEN`, không giả mạo).
     - 1 test tương thích ngược với payload hình chóp lịch sử (pyramid parity).
     - 1 test schema transport từ chối dứt khoát `solid_kind="pyramid"`.

2. **Bộ kiểm thử hình chóp lịch sử (`backend/tests/geometry/test_geometry_primitive_compiler.py`)**:
   - **41 / 41 PASSED**:
     - Toàn bộ suite hồi quy của họ chóp đáy tam giác vuông tiếp tục hoạt động hoàn hảo, không có bất kỳ hiệu ứng phụ hay hồi quy nào.

3. **Kiểm tra tính nhất quán danh tính cache và tài liệu**:
   - `test_cache_identity.py`: **15 / 15 PASSED**.
   - `test_current_state_identity.py`: **3 / 3 PASSED** (khớp chính xác `CACHE_VERSION = 100`).

---

## 6. Đóng Băng Evaluation Candidate Mới

Sau khi Commit 1 (`5a5534fe`) hoàn tất, công cụ `backend/scripts/freeze_evaluation_candidate.py` đã được chạy trên worktree sạch không có dirty file để xác thực danh tính hệ thống đo:
- **Commit:** `5a5534fe697b2162a1522ed1a1e38de774085f06`
- **Cây làm việc sạch:** `True`
- **CACHE_VERSION:** `100`
- **Số file mã sản phẩm:** 103 file
- **Mã băm cây sản phẩm (Tree Hash):** `fc88b200e9de094b31c78aef1e0883d28fa2f102bbb5bee7329f8a6c7063e24d`
- **Tình trạng:** `DA_NIEM_PHONG` (`docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json`)

---

## 7. Bảo Tồn Trạng Thái Làm Việc Của Người Dùng

File `frontend/public/favicon.svg` (bị xóa trong working tree của người dùng) đã được kiểm tra liên tục qua `git status` và `git diff --cached --name-only`:
- Tuyệt đối **KHÔNG** bị stage.
- Tuyệt đối **KHÔNG** bị sửa đổi hoặc phục hồi.
- Được bảo tồn nguyên trạng qua toàn bộ các bước commit và kiểm chứng.

---

## 8. Kết Luận & Hành Động Tiếp Theo

Lát cắt dọc cho họ bài lăng trụ đứng đáy tam giác vuông đã được hiện thực và kiểm chứng thành công, đáp ứng trọn vẹn mọi yêu cầu của Gate 2.

- **QUYẾT ĐỊNH:** `FINAL_DECISION = PASS` (`PRISM_VERTICAL_SLICE = VERIFIED`).
- **BƯỚC TIẾP THEO DUY NHẤT:**
  ```text
  CANONICAL_NEXT_ACTION = SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION_PREREGISTRATION
  TARGET_NEXT_ACTION_AFTER_WAVE = SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION_PREREGISTRATION
  ```
  (Tiền đăng ký và kiểm chứng live schema revalidation với Gemini provider cho `solid_topology`).
