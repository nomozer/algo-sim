# Báo Cáo Đính Chính và Chuẩn Hóa Khớp Nối Benchmark Tiền Đăng Ký Họ Bài Thứ Hai (Ngoại Tuyến)

> **WAVE_ID:** `SECOND_FAMILY_FROZEN_BENCHMARK_ALIGNMENT_REPAIR_OFFLINE`  
> **NGÀY:** 2026-09-22  
> **PHÂN LOẠI:** `REPORTING_AND_TEST_ASSERTION_EVIDENCE_MISMATCH`  
> **START_BASE:** `b4521d285942687e284767e8163335f2fbdc873b`  
> **TEST_COMMIT:** `0714e929042fb109f9054772d191b6dc812844d6`  
> **PRODUCT_COMMIT:** `5a5534fe697b2162a1522ed1a1e38de774085f06` (giữ nguyên, `PRODUCT_CODE_REPAIR_REQUIRED = NO`)  
> **EVIDENCE_COMMIT_ROLE:** `SELF`  
> **CORRECTS:** `PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE_OFFLINE`  
> **CACHE_VERSION:** `100` (giữ nguyên, không bump)  
> **CANDIDATE_REFREEZE_REQUIRED:** `NO` (candidate giữ nguyên tại commit `5a5534fe`)  
> **SỐ LẦN GỌI MODEL:** `0`  
> **SỐ LẦN GỌI MẠNG:** `0`  
> **KẾT LUẬN:** `FINAL_DECISION = PASS_WITH_REPORTING_AND_ASSERTION_CORRECTION`  
> **PREREGISTERED_BENCHMARK_VERIFIED:** `YES`  
> **LIVE_REVALIDATION_ALLOWED:** `YES`  
> **BƯỚC TIẾP THEO:** `SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION_PREREGISTRATION`

---

## 1. Tóm Tắt Mục Đích và Lý Do Đính Chính

Trong wave trước (`PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE_OFFLINE`), quá trình kiểm chứng lát cắt dọc ngoại tuyến đã thành công về mặt thực thi mã nguồn sản phẩm. Tuy nhiên, đợt kiểm toán nghiêm ngặt tại Gate 1 phát hiện các sai lệch bằng chứng nghiêm trọng ở tầng báo cáo và kiểm thử:
1. **Sai lệch dữ liệu trong báo cáo và artifact lịch sử:** Báo cáo `docs/PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE_OFFLINE.md` và artifact `OFFLINE_BENCHMARK_MATRIX.json` đã ghi nhầm số liệu dữ kiện đầu vào và đáp số kỳ vọng của các ca PRISM_P02, PRISM_P04, PRISM_P05 so với file tiền đăng ký bất biến `SECOND_FAMILY_MANIFEST.json` và `SECOND_FAMILY_GROUND_TRUTH.json`.
2. **Kiểm thử mang tính thỏa hiệp (permissive assertions):** Trong file `backend/tests/geometry/test_prism_primitive_compiler.py`, bộ kiểm thử cho 3 ca âm N01–N03 đã sử dụng chuỗi `or` lỏng lẻo và return sớm bypass assertion cho N02, không kiểm tra chính xác 3 tầng phân định (benchmark outcome, internal status, reason/detail codes).
3. **Mã nguồn sản phẩm thực tế:** Chạy kiểm chẩn độc lập từ harness ngoài repo khẳng định mã sản phẩm tại commit `5a5534fe` **đã đạt chính xác 8/8 ca tiền đăng ký** (5/5 ca dương cho đáp số Fraction hoàn hảo, 3/3 ca âm bị từ chối fail-closed với đúng reason code và detail code). Do đó, **không cần sửa mã sản phẩm**, không bump `CACHE_VERSION`, và không refreeze `EVALUATION_CANDIDATE`.

Wave repair này thiết lập một lớp đính chính mới (**Correction Layer**), độc lập và bất biến, bảo toàn toàn bộ tài liệu lịch sử theo đúng quy tắc an toàn bằng chứng.

---

## 2. Xác Minh Tính Bất Biến 3 File Tiền Đăng Ký Frozen

Ba file tiền đăng ký tại thư mục `docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/` được đọc trực tiếp và kiểm chứng LF-normalized SHA-256:

| Tên File | SHA-256 Đăng Ký | SHA-256 Thực Tế Đo Được | Trạng Thái |
|---|---|---|---|
| `SECOND_FAMILY_MANIFEST.json` | `f5978eb5f76b72808a02791dadc96f3b001b3bd288fc84e6656307ac4d0fefe5` | `f5978eb5f76b72808a02791dadc96f3b001b3bd288fc84e6656307ac4d0fefe5` | **BIT_IDENTICAL** |
| `SECOND_FAMILY_GROUND_TRUTH.json` | `faf42e894fb9f69c8b61aba06f84767ec9806d1231633d2975516ec5367e18ce` | `faf42e894fb9f69c8b61aba06f84767ec9806d1231633d2975516ec5367e18ce` | **BIT_IDENTICAL** |
| `SECOND_FAMILY_SELECTION_MATRIX.json` | `748b04938952d84d9f40ed656697cfdac212a9cfc028d52e040b4fb46c521aa7` | `748b04938952d84d9f40ed656697cfdac212a9cfc028d52e040b4fb46c521aa7` | **BIT_IDENTICAL** |

---

## 3. Bảng Đính Chính Sai Lệch Giữa Báo Cáo Lịch Sử và Thực Chứng

Dưới đây là bảng đối soát chi tiết chỉ rõ các điểm ghi sai trong báo cáo lịch sử so với dữ liệu thực chứng từ `SECOND_FAMILY_GROUND_TRUTH.json` và kết quả thực thi của production code:

| Mã Ca | Dữ Kiện Thực Tế (Frozen Manifest) | Báo Cáo Cũ Ghi | Giá Trị Đúng (Ground Truth) | Kết Quả Compiler Thực Tế | Đánh Giá Khớp Nối |
|---|---|---|---|---|---|
| `PRISM_P01` | $AB=3, AC=4, AD=5$, vuông tại $A$ | $V=30$ | $V=30$ | $V=30$ | Khớp 100% |
| `PRISM_P02` | $MN=6, MP=8, MQ=7$, vuông tại $M$ | Ghi nhầm $V=60$ ($AB=6, AC=4, AD=5$) | **$V=168$** | **$V=168$** | **ĐÍNH CHÍNH:** $60 \to 168$ |
| `PRISM_P03` | $AB=3/2, AC=4/3, AD=5/4$, vuông tại $A$ | $V=5/4$ | $V=5/4$ | $V=5/4$ | Khớp 100% |
| `PRISM_P04` | $BA=5, BC=12, BE=6$, vuông tại $B$ | Ghi nhầm $V=6$ ($AB=2, AC=2, AD=3$) | **$V=180$** | **$V=180$** | **ĐÍNH CHÍNH:** $6 \to 180$ |
| `PRISM_P05` | $AD=10, AC=6, AB=8$, vuông tại $A$ | Ghi nhầm $V=120$ ($AB=5, AC=12, AD=4$) | **$V=240$** | **$V=240$** | **ĐÍNH CHÍNH:** $120 \to 240$ |
| `PRISM_N01` | Thiếu chiều cao $AD$ | `REQUIRED_FACT_MISSING (AD)` | `REJECTED`, `REQUIRED_FACT_MISSING`, detail `REQUIRED_LENGTH_MISSING` | `UNSUPPORTED_MISSING_FACT`, reason: `REQUIRED_FACT_MISSING`, diag: `('REQUIRED_LENGTH_MISSING', 'AD')` | Khớp exact lý do và chi tiết |
| `PRISM_N02` | 2 góc vuông tại đỉnh $A$ & $B$ | Ghi nhầm `CONFLICTING_FACTS (AC_perpendicular_BC)` | `REJECTED`, `STRUCTURED_RELATION_CONTRADICTION`, detail `MULTIPLE_RIGHT_ANGLE_VERTICES_IN_TRIANGLE` | `INVALID_CONFLICT`, reason: `STRUCTURED_RELATION_CONTRADICTION`, rule_id: `MULTIPLE_RIGHT_ANGLE_VERTICES_IN_TRIANGLE` | **ĐÍNH CHÍNH:** Bị chặn tại FactGraph với đúng rule_id |
| `PRISM_N03` | Thiếu quan hệ vuông góc cạnh bên | Ghi nhầm `REQUIRED_FACT_MISSING (AD_perpendicular_base)` | `REJECTED`, `UNSUPPORTED_STRUCTURED_RELATION_MISSING`, detail `LINE_PLANE_RELATION_MISSING` | `UNSUPPORTED_STRUCTURED_RELATION_MISSING`, reason: `UNSUPPORTED_STRUCTURED_RELATION_MISSING`, diag: `('LINE_PLANE_RELATION_MISSING', 'perpendicular_line_plane')` | **ĐÍNH CHÍNH:** Khớp exact reason và detail |

---

## 4. Thắt Chặt Ba Tầng Kiểm Thử Trong `test_prism_primitive_compiler.py`

Tại Commit 1 (`0714e929`), file test đã được sửa đổi và thắt chặt hoàn toàn:
1. **Phân định rõ 3 tầng:**
   - **Tầng Benchmark Outcome:** Đánh giá nhị phân `SUPPORTED` vs `REJECTED`. Cả 3 ca âm đạt đúng `benchmark_outcome == "REJECTED"`.
   - **Tầng Trạng Thái Nội Bộ (Internal Status):** Giữ nguyên kiến trúc của adapter và compiler (`UNSUPPORTED_MISSING_FACT`, `INVALID_CONFLICT`, `UNSUPPORTED_STRUCTURED_RELATION_MISSING`), không ép chuỗi nội bộ thành `REJECTED`.
   - **Tầng Lý Do và Chi Tiết (Reason Code & Detail Code):** Kiểm tra khớp từng chuỗi với Ground Truth:
     - `PRISM_N01`: `reason_code == "REQUIRED_FACT_MISSING"`, `diagnostics[0] == "REQUIRED_LENGTH_MISSING"`, `diagnostics[1] == "AD"`.
     - `PRISM_N02`: `reason_code == "STRUCTURED_RELATION_CONTRADICTION"`, `rule_id == "MULTIPLE_RIGHT_ANGLE_VERTICES_IN_TRIANGLE"`, `diagnostics` chứa `"PHASE=FACT_GRAPH"`.
     - `PRISM_N03`: `reason_code == "UNSUPPORTED_STRUCTURED_RELATION_MISSING"`, `diagnostics[0] == "LINE_PLANE_RELATION_MISSING"`, `diagnostics[1] == "perpendicular_line_plane"`.
2. **Loại bỏ toàn diện:**
   - Xóa bỏ mọi chuỗi `or` lỏng lẻo (`assert el.reason_code == ... or ... in el.diagnostics or ...`).
   - Xóa bỏ câu lệnh `return` sớm trong N02 vốn bỏ qua việc thẩm tra toàn diện.

---

## 5. Đo Lường Synthesis Schema Sanitizer và Khẳng Định Không Hồi Quy

Đo lường so sánh giữa `BASE_HEAD` (`f4a547ab`) và `CURRENT_HEAD` (`b4521d28`):
- `SYNTHESIS_SCHEMA_RAW_HASH_BEFORE = 5e18c176002d28976a6f3cda00f2a225040d5beb36b954778863c3734019a481`
- `SYNTHESIS_SCHEMA_RAW_HASH_AFTER = 5e18c176002d28976a6f3cda00f2a225040d5beb36b954778863c3734019a481`
- `SANITIZED_SYNTHESIS_BEFORE = None` (Hành vi baseline: Pydantic schema chứa `$defs`/`$ref` được khử bởi `_sanitize_gemini_schema`)
- `SANITIZED_SYNTHESIS_AFTER = None`
- `SYNTHESIS_SANITIZER_REGRESSION = NO`
- `SYNTHESIS_LIVE_ACCEPTANCE = NOT_ESTABLISHED_NO_OFFLINE_REGRESSION`

Kết quả chứng minh 100% không có hồi quy trong synthesis schema. Việc kiểm chứng thực tế sẽ được chuyển tiếp sang bước live-schema revalidation.

---

## 6. Audit Trace Sư Phạm (Pedagogical Construction Trace)

Dữ liệu máy đo được từ quá trình biên dịch của P01 và P03:
- **`PEDAGOGICAL_TRACE_STEP_COUNT = 11`** (gồm 11 bước diễn hoạt thực tế).
- **Thứ tự Primitive IDs:**
  `declare_point` ($A$) $\to$ `declare_point` ($B$) $\to$ `declare_point` ($C$) $\to$ `construct_triangle` ($ABC$) $\to$ `declare_point` ($D$) $\to$ `declare_point` ($E$) $\to$ `declare_point` ($F$) $\to$ `construct_prism` ($ABC.DEF$) $\to$ `measure_quantity` (diện tích) $\to$ `measure_quantity` (thể tích) $\to$ `assign_final_memory` (gán biến witness).
- **So với 7 danh mục lý thuyết:** 6 đỉnh được dựng riêng rẽ; cạnh bên được tích hợp trong khối đa diện `construct_prism`; 2 phép đo diện tích và thể tích diễn ra ở 2 bước độc lập; bước 11 gán đúng biến witness.
- **Phân định rõ:**
  - `PEDAGOGICAL_TRACE_GENERATED = YES` (đã có unit test `test_pedagogical_trace_11_steps` kiểm chứng).
  - `PEDAGOGICAL_TRACE_UI_CONSUMPTION = NOT_ESTABLISHED` (chưa có browser proof diễn hoạt từng bước trên UI).

---

## 7. Audit Scope Drift Trong Lịch Sử Commit

Kiểm toán các file thay đổi ngoài allowlist ban đầu của Commit 1:

1. **`backend/app/simulation/semantic_program/structured_relations.py`**:
   - **Lý do thay đổi:** Mở rộng `diem_hop_dong` đọc `contract.solid_topology` để nhận diện các đỉnh có cấu trúc khi ca bài toán thiếu dữ kiện cạnh.
   - **Cần thiết cho ca frozen:** **BẮT BUỘC** cho `PRISM_N01`. Nếu không có, `PRISM_N01` sẽ bị lỗi tham chiếu đỉnh không rõ (`STRUCTURED_RELATION_REFERENCE_UNKNOWN`) ở adapter, trượt khỏi trạng thái kỳ vọng `REQUIRED_FACT_MISSING`.
   - **Quyết định:** **KEEP** (bảo toàn thay đổi, đã ghi nhận kiến trúc).
2. **`backend/scripts/lock_cache_identity.py`**:
   - **Lý do thay đổi:** Bổ sung cấu hình UTF-8 cho Windows stdout/stderr để tránh crash `UnicodeEncodeError`.
   - **Quyết định:** **KEEP** (`PRODUCT_RUNTIME_CHANGE = NO`).
3. **`backend/tests/test_api.py`**:
   - **Lý do thay đổi:** Đồng bộ assertion `CACHE_VERSION == "100"`.
   - **Quyết định:** **KEEP** (`PRODUCT_RUNTIME_CHANGE = NO`).

---

## 8. Kết Quả Kiểm Thử Toàn Diện

- `backend/tests/geometry/test_prism_primitive_compiler.py`: **26 / 26 PASSED** (thêm test trace 11 bước, siết chặt 3 ca âm).
- `backend/tests/geometry/test_geometry_primitive_compiler.py`: **41 / 41 PASSED** (pyramid regression parity).
- `backend/tests/test_cache_identity.py`: **15 / 15 PASSED**.
- `backend/tests/test_current_state_identity.py`: **3 / 3 PASSED**.
- `freeze_evaluation_candidate.py --verify`: **PASS** (103 product files, tree_hash `fc88b200...`).
- `lock_cache_identity.py --verify`: **PASS** (`CACHE_VERSION = 100`).

---

## 9. Kết Luận & Bước Tiếp Theo

Lớp đính chính và chuẩn hóa đã hoàn tất việc sửa sai toàn bộ các điểm lệch trong báo cáo và kiểm thử:
- **`FINAL_DECISION = PASS_WITH_REPORTING_AND_ASSERTION_CORRECTION`**
- **`PREREGISTERED_BENCHMARK_VERIFIED = YES`**
- **`LIVE_REVALIDATION_ALLOWED = YES`**
- **BƯỚC TIẾP THEO DUY NHẤT:**
  ```text
  CANONICAL_NEXT_ACTION = SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION_PREREGISTRATION
  TARGET_NEXT_ACTION_AFTER_WAVE = SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION_PREREGISTRATION
  ```
