# Báo Cáo Đối Soát Phạm Vi Mã Nguồn Họ Bài Thứ Hai (Offline)

> **Wave ID**: `SECOND_FAMILY_SOURCE_SCOPE_RECONCILIATION_OFFLINE`  
> **Lớp đính chính (Correction Layer)**:  
> `CORRECTS = SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE`  
> `REFERENCES_ORIGINAL = PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION`  
> `HISTORY_DRIFT = NO`  
> **Cam kết bất biến**: Hoàn toàn offline (0 network, 0 Gemini/provider call), không sửa mã sản phẩm (`PRODUCT_CODE_CHANGED = NO`), không sửa prompt/schema, không sửa 3 tệp preregistration đã đóng băng và không sửa báo cáo lịch sử.

---

## 1. Mốc Thực Hiện và Kiểm Tra Tiền Điều Kiện (Precheck)

```text
WAVE = SECOND_FAMILY_SOURCE_SCOPE_RECONCILIATION_OFFLINE
BRANCH = feat/photo-problem-to-scene
START_HEAD = dc444acd33292d66aebcc3fb465097b73542c887
MAIN_HEAD = 085cae67392d3607ad0a58a7f48c17d8a5e5157d
CANDIDATE_SHA256 = 077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1
CANDIDATE_FILE_COUNT = 103
CACHE_VERSION = 99
DEFAULT_MODE = LLM_ONLY
PRESERVED_USER_CHANGE = D frontend/public/favicon.svg
PRECHECK_STATUS = PASS
```

Bất biến phạm vi tuân thủ tuyệt đối:
* `PRODUCT_CODE_CHANGED = NO`
* `PROMPT_CHANGED = NO`
* `SCHEMA_CHANGED = NO`
* `FACT_GRAPH_CHANGED = NO`
* `COMPILER_CHANGED = NO`
* `ROUTING_CHANGED = NO`
* `DEFAULT_ARCHITECTURE_CHANGED = NO`
* `NEW_GEMINI_REQUESTS = 0`
* `NETWORK_REQUESTS = 0`
* `DOTENV_LOADED = NO`
* `API_KEY_LOADED = NO`
* `HISTORICAL_REPORTS_CHANGED = NO`
* `HISTORICAL_ARTIFACTS_CHANGED = NO`

---

## 2. Bảo Toàn Tính Bất Biến Của Lịch Sử (Historical Immutability)

Ba tệp kiểm nghiệm preregistration đã đóng băng của wave tiền đăng ký được giữ nguyên 100% từng byte:

| Tệp lịch sử | SHA-256 Kỳ Vọng / Thực Tế | Trạng Thái |
|---|---|---|
| `SECOND_FAMILY_SELECTION_MATRIX.json` | `748b04938952d84d9f40ed656697cfdac212a9cfc028d52e040b4fb46c521aa7` | KHỚP NGUYÊN BẢN (PASS) |
| `SECOND_FAMILY_MANIFEST.json` | `f5978eb5f76b72808a02791dadc96f3b001b3bd288fc84e6656307ac4d0fefe5` | KHỚP NGUYÊN BẢN (PASS) |
| `SECOND_FAMILY_GROUND_TRUTH.json` | `faf42e894fb9f69c8b61aba06f84767ec9806d1231633d2975516ec5367e18ce` | KHỚP NGUYÊN BẢN (PASS) |

Báo cáo lịch sử gốc `docs/PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION.md` và báo cáo đính chính `docs/SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE.md` được giữ nguyên vẹn.

---

## 3. Audit A — Sửa Sai Điểm Lịch Sử (Historical Score Correction)

* **Bằng chứng Git blob:**
  - `SECOND_FAMILY_SELECTION_MATRIX.json` dòng 164 ghi nhận: `"weighted_total": 95.5` cho Candidate B.
  - `PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION.md` dòng 76 ghi: `HISTORICAL_SCORE_B = 95.5 / 100`.
* **Báo cáo đính chính gần nhất (`SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE.md:90`):**
  - Ghi nhầm do lỗi sao chép văn bản: `HISTORICAL_SCORE_B = 94.0 / 100`.
* **Kết luận đính chính:**
  ```text
  HISTORICAL_SCORE_B_CORRECT = 95.5 / 100
  EVIDENCE_REPAIR_REPORTED_SCORE = 94.0 / 100
  CLASSIFICATION = REPORTING_ERROR
  HISTORY_DRIFT = NO
  CORRECTED_SELECTION_SCORE = 75.5 / 80
  NORMALIZED_SCORE = 94.375 / 100
  ```
* Candidate B (`right_triangle_base_right_prism_volume`) vẫn là họ đứng đầu với cách biệt +7.5 điểm thô (+9.375% chuẩn hóa) so với Candidate A.

---

## 4. Audit B — Định Danh Primitive Registry (Registry Identity Map)

Đối soát mã nguồn tại `backend/app/simulation/geometry_compiler/primitives.py:136-143`:
* **`COMPILER_PRIMITIVE_REGISTRY`**:
  - Phiên bản: `geometry-primitives/1` (`PRIMITIVE_REGISTRY_VERSION`).
  - Đúng **6 primitives**:
    1. `declare_point`
    2. `construct_triangle`
    3. `construct_pyramid`
    4. `measure_quantity`
    5. `assign_final_memory`
    6. `memory_declaration`
  - Người tiêu thụ trực tiếp: `backend/app/simulation/geometry_compiler/compiler.py` (`from . import primitives as P`).
* **Giải quyết mâu thuẫn tồn kho:**
  - Danh sách 7 phần tử (`point`, `segment`, `triangle`, `polygon`, `polygon_regular`, `circle`, `sphere`) tại báo cáo trước là một bảng phân loại hình học trừu tượng bị ghi nhầm thành tên registry primitive.
  - Quét AST toàn bộ thư mục `backend/app`: không có bất kỳ định nghĩa hay ký hiệu nào tên `polygon_regular`.
  - Kết luận: `REGISTRY_IDENTITY_CONFLICTS = 0`. Chỉ có một registry compiler 6 hàm duy nhất.

---

## 5. Audit C — Định Danh Quan Hệ Có Cấu Trúc (Structured Relations Identity Map)

Tại `backend/app/simulation/semantic_program/structured_relations.py:52-56`:
* `RELATION_KINDS = ("perpendicular_lines", "perpendicular_line_plane")`.
* Phân loại:
  - `perpendicular_lines`: `CURRENT_CONTRACT_KIND`. Dùng cho hai cạnh góc vuông của đáy tam giác vuông ($AB \perp AC$).
  - `perpendicular_line_plane`: `CURRENT_CONTRACT_KIND`. Dùng cho cạnh bên vuông góc với mặt phẳng đáy ($AD \perp (ABC)$).
  - `perpendicular_to_base`, `face_perpendicular_to_base`, `lateral_edge_perpendicular_to_base`: `PROPOSED_FUTURE_KIND` (không tồn tại trong mã nguồn).
* **Kết luận**: Hợp đồng quan hệ có cấu trúc hiện hành đã đủ 100% để biểu diễn lăng trụ đứng đáy tam giác vuông mà không cần mở rộng `RELATION_KINDS`.

---

## 6. Audit D — Kiểm Toán RequestContract & Phân Loại 12 Tầng

### 6.1. Kiểm Toán RequestContract & Kinds của SourceInvariant
* `SourceInvariant` tại `START_HEAD` có chính xác **5 kinds**:
  1. `segment_length`: độ dài đoạn thẳng hữu tỉ số học (`scale_normalization.py:118`, `segment_relation.py:215`).
  2. `segment_division`: quan hệ chia đoạn đọc từ đề (`segment_relation.py:80`).
  3. `segment_division_unresolved`: quan hệ chia đoạn chưa giải được (`segment_relation.py:82`).
  4. `point_coordinate`: tọa độ điểm đề cho tường minh (`point_coordinate.py:121`).
  5. `plane_equation`: phương trình mặt phẳng đề cho (`plane_equation.py:269`).
  *(Lưu ý: `contract_adapter.py:135` chỉ lọc lấy `segment_length` cho compiler)*.
* **Đường dữ liệu lăng trụ trong RequestContract:**
  - Không có trường hoặc JSON pointer nào chở `prism identity`, `base_cycle`, `top_cycle`, hay `correspondence`.
  - `ObligationSpec(kind="volume", subject="solid")` chỉ nêu mục tiêu đo lường, không mang topology lăng trụ.
  - `FactGraph` và `contract_adapter` bị cấm đọc `problem_text` (tuân thủ R0 và `contract_adapter.py:44`).
  - Do đó: `REQUEST_CONTRACT_CLASSIFICATION = CHANGE_REQUIRED`.

### 6.2. Phân Loại 12 Tầng Kỹ Thuật

```text
CHANGE_REQUIRED = 6
REUSE_AS_IS = 5
NOT_REQUIRED_FOR_ISOLATED_VERTICAL_SLICE = 1
OPTIONAL_FUTURE_ENHANCEMENT = 0
NOT_ESTABLISHED = 0
```

1. `request_contract`: `CHANGE_REQUIRED` (thiếu trường chở cấu trúc lăng trụ).
2. `structured_relations`: `REUSE_AS_IS` (tái sử dụng `perpendicular_lines` và `perpendicular_line_plane`).
3. `contract_adapter`: `CHANGE_REQUIRED` (cần chuẩn hóa thực thể lăng trụ sang FactGraph).
4. `fact_graph`: `CHANGE_REQUIRED` (thêm `"prism"` vào `LOAI_NUT`).
5. `eligibility`: `CHANGE_REQUIRED` (thêm kiểm tra họ lăng trụ đứng tam giác vuông trong `compiler.py`).
6. `primitive_helper_registry`: `CHANGE_REQUIRED` (đăng ký `construct_prism(name, base_cycle, top_cycle, correspondence)`).
7. `semantic_program_ir`: `REUSE_AS_IS` (tái sử dụng `construct_solid` 6 đỉnh 5 mặt).
8. `type_static_grounding_gates`: `REUSE_AS_IS` (hệ thống kiểu tĩnh đã hỗ trợ `solid` và `measure[volume]`).
9. `scene_topology_compiler_layout`: `CHANGE_REQUIRED` (layout tính tọa độ 6 đỉnh mang `LAYOUT_DERIVED`).
10. `measurement_kernel_final_memory`: `REUSE_AS_IS` (kernel đa diện `the_tich_da_dien` tính chính xác 100%).
11. `routing_fallback`: `NOT_REQUIRED_FOR_ISOLATED_VERTICAL_SLICE` (giữ nguyên `DEFAULT_MODE = LLM_ONLY`).
12. `frontend_renderer`: `REUSE_AS_IS` (Three.js generic mesh renderer hiển thị đầy đủ đa diện lăng trụ).

---

## 7. Audit E, F, G, H, I — Bằng Chứng Thực Nghiệm

* **Audit E (IR Reuse)**: Câu lệnh `ConstructSolidStmt` chở 6 đỉnh và 5 mặt (2 tam giác, 3 hình chữ nhật) hợp lệ 100% trên `ir_static_check.py`.
* **Audit F (Kernel Reuse)**: `the_tich_da_dien` tính trên `Polyhedron`:
  - Ca nguyên ($3, 4, h=5$): $V = 30$ (`Fraction(30)`).
  - Ca phân số ($3/2, 4/3, h=5/4$): $V = 5/4$ (`Fraction(5, 4)`).
  - Không cần công thức riêng `volume_prism`.
* **Audit G (Frontend Reuse)**: `RENDER_HINT["solid"] == "mesh"`. `scene3d-view.tsx:515-550` tự động phân rã mặt thành tam giác và vẽ nét đứt camera bằng `EdgesGeometry`. Shader riêng là `OPTIONAL_FUTURE_ENHANCEMENT`.
* **Audit H (Routing Isolation)**: `DEFAULT_MODE = LLM_ONLY` (`semantic_route_mode() == 'off'`). Slice được gọi cô lập trong test/eval harness.
* **Audit I (Semantic Ownership Path)**:
  1. `RequestContract`: **External Semantic Source**.
  2. `contract_adapter`: **Normalization Boundary** (sắp xếp đỉnh chính tắc, kiểm tra không suy biến, cấm đọc `problem_text`).
  3. `FactGraph`: **Canonical Internal Normalized Owner** (sở hữu `Nut(kind="prism")`).
  4. `primitive arguments`: **Derived Projection from FactGraph** (`construct_prism(name, base_cycle, top_cycle, correspondence)` — không có tham số `nhan`).
  5. `Semantic Program IR`: **Serialized Execution** (`construct_solid`).
  6. `Layout`: **LAYOUT_DERIVED** (tọa độ trình bày của compiler).

---

## 8. Phân Tích Bế Tắc Schema & Allowlist (Direction A vs B)

Khi `RequestContract = CHANGE_REQUIRED`, xuất hiện bế tắc kiến trúc:
* **Direction A (Mở rộng External Model Schema)**:
  - Thêm trường lăng trụ vào schema gửi cho mô hình.
  - *Hệ quả*: Đổi schema hash, đòi hỏi bump `CACHE_VERSION` (từ 99 lên 100), phá vỡ candidate freeze (103 tệp), mở rộng allowlist tệp của vertical slice ra cả chục tệp AI/prompt, và bắt buộc phải có wave đo lường live với Gemini để kiểm chứng mô hình có trích xuất được trường này không.
  - *Kết luận*: Không thể khép kín trong wave offline này.
* **Direction B (Internal-Only Derivation)**:
  - Giữ nguyên schema gửi cho mô hình, tự suy diễn lăng trụ ở tầng nội bộ `contract_adapter`.
  - *Bế tắc*: Không thể tự suy diễn lăng trụ 6 đỉnh $A, B, C, D, E, F$ và quan hệ tương ứng $A-D, B-E, C-F$ nếu không đọc `problem_text` (vốn bị cấm triệt để bởi R0 và `contract_adapter.py:44`) và không được dựa vào ground truth / test fixture trong production code.
  - *Kết luận*: Chưa có thuật toán tất định nội bộ nào được chứng minh là an toàn và khả thi tại `START_HEAD`.

=> **Bản chất phán quyết**: Do cả hai hướng chưa thể chứng minh khép kín offline, danh sách 6 tệp của vertical slice **chưa đủ cơ sở khẳng định là hoàn chỉnh**.

---

## 9. Phán Quyết Cuối Cùng (Final Decision)

Áp dụng nguyên tắc fail-closed:
```text
SOURCE_IDENTITY_CONFLICTS = 0
CRITICAL_NOT_ESTABLISHED_COUNT = 1
CRITICAL_NOT_ESTABLISHED_ITEMS = [
  "RequestContract_to_FactGraph_prism_data_path_resolution"
]
MINIMAL_SCOPE_ESTABLISHED = NO
SINGLE_SEMANTIC_SOURCE_OF_TRUTH = YES
PRODUCT_CODE_CHANGED = NO
FINAL_DECISION = INCOMPLETE
VERTICAL_SLICE_ALLOWED = NO
NEXT_ACTION = SECOND_FAMILY_SOURCE_SCOPE_REAUDIT
```

**Lý do**:
Chưa chứng minh khép kín được đường dữ liệu từ `RequestContract` sang `FactGraph` cho lăng trụ (Direction A vs Direction B). Không được tự ý mở vertical slice khi phạm vi kỹ thuật của hợp đồng bên ngoài chưa được giải quyết dứt điểm. Dừng lại an toàn và chuyển giao hành động kế tiếp sang `SECOND_FAMILY_SOURCE_SCOPE_REAUDIT`.
