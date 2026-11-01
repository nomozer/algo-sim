# Kiểm toán Tái tổ hợp Tổng quát của Planner & Hợp đồng Registry (Continuation 11 — §§4, 7)

> **Phạm vi**: Offline architecture & planning audit (`ALLOW_LIVE_AI=0`, `0` provider calls).
> **Phiên bản**: `geometry-functions/28`, `geometry-fact-planner/23`, `geometry-function-engine/20`.
> **Biên nhận máy**: `planner-recomposition-matrix.json` (sinh bởi `tools/planner_recomposition_probe.py` và đối chiếu độc lập bởi `backend/scripts/planning_oracle.py`).

---

## 1. Kiểm toán 11 chiều của 49 `FunctionSpec` trong `REGISTRY` (§4.1)

Công cụ `audit_registry_contracts()` trong `backend/scripts/planning_oracle.py` đã quét toàn bộ **49 hàm** của `REGISTRY` trên đủ 11 chiều (`inputs`, `outputs`, `preconditions`, `postconditions`, `needs`, `effects`, `object_types`, `source_requirements`, `derived_dependencies`, `computational_limitations`, `verification_authority`) và 6 phân tích cắt ngang:

1. **Multi-producer effects (nhiều hàm cùng sinh một loại hiệu ứng)**:
   - `Point` (`PlanningContract` có `descriptor`): **6 producers** tổng quát (`midpoint`, `centroid`, `orthogonal_projection`, `orthogonal_projection_line`, `intersect_line_line`, `intersect_line_plane`). Ở baseline `/22`, chỉ có `midpoint` và `centroid` khai báo `Point` descriptor contract; 4 hàm dựng điểm cốt lõi còn lại tồn tại trong `REGISTRY` nhưng không có `PlanningContract` cho điểm không đặt tên.
   - `AnswerDistance`: **2 producers** (`ask_distance_point_plane` cho điểm–mặt phẳng và `ask_length` qua chân đường vuông góc `Foot(F, P, L)` cho điểm–đường thẳng).
   - `Point3D` construct producers tổng quát: **7 producers** (`centroid`, `divide_segment`, `intersect_line_line`, `intersect_line_plane`, `midpoint`, `orthogonal_projection_line`, `translate_point`).
2. **Multi-step intermediate consumers**: **19 hàm** tiêu thụ đối tượng trung gian được sinh từ nhiều bước dựng trước đó (`ask_length`, `ask_area`, `ask_distance_point_plane`, `ask_angle_line_plane`, `ask_angle_lines`, `section`, `ask_section_area`, `intersection_line`, `translate_point`, ...).
3. **Reusable intermediate producers**: **9 hàm** tạo đối tượng hình học có thể tái sử dụng giữa nhiều mục tiêu mà không sinh trùng điểm phụ (`midpoint`, `centroid`, `divide_segment`, `orthogonal_projection_line`, `intersect_line_line`, `intersect_line_plane`, `intersection_line`, `translate_point`, `section`).
4. **Shared-dependency multi-goal pairs**: `("section", "ask_section_area")`, `("ask_length", "ask_distance_point_plane")`, `("ask_section_area", "ask_distance_point_plane")`, `("ask_angle_lines", "ask_length")`.
5. **Cross-topology composability**:
   - **32 hàm đa diện bất biến theo topology** (`polyhedral_agnostic`): dùng chung cho chóp, tứ diện, lăng trụ đứng/xiên, hình hộp chữ nhật, hình lập phương.
   - **3 hàm đặc thù chóp** (`pyramid`, `regular_pyramid`, `altitude`), **1 hàm đặc thù lăng trụ** (`prism`), **12 hàm khối tròn xoay/mặt cầu cô lập** (`curved_isolated`), và `face_perpendicular_base` cho mặt bên vuông góc đáy.
6. **Invalidating geometric/source constraints**:
   - Hai đường chéo nhau hoặc song song khi lấy `intersect_line_line` (`SKEW_NO_INTERSECTION` / `PARALLEL_NO_INTERSECTION`).
   - Đường thẳng song song hoặc nằm trong mặt phẳng khi lấy `intersect_line_plane` (`PARALLEL_NO_INTERSECTION`).
   - Mặt phẳng phụ đi qua điểm đã nằm trong mặt phẳng song song tham chiếu hoặc không cắt phần trong khối (`DERIVED_PLANE_IS_REFERENCE` / `PLANE_DOES_NOT_CUT` / `PLANE_IS_FACE`).
   - Ba điểm thẳng hàng khi xác định mặt phẳng (`COLLINEAR_PLANE_POINTS`).
   - Mâu thuẫn loại hình (`INCONSISTENT_FACTS`, PE-2).
   - Thiếu bậc tự do metric (`MISSING_DIMENSION` / `UNDERDETERMINED_POINT`).
   - Đảo vai trò toán hạng hoặc giả mạo đối tượng `DERIVED` thành `GIVEN` (`SOURCE_OBJECT_MISMATCH` / `UNKNOWN_LABEL`).

---

## 2. Phát hiện Khoảng trống Lập kế hoạch trên Baseline `/22` & Cải tiến Tổng quát trên `/23` (§§4.2–4.3)

### 2.1. Ba khoảng trống kiến trúc có bằng chứng (`REACHABLE_BUT_SEARCH_MISSED` trên `/22`)

1. **Gap B-1 — Thiếu hợp đồng `Point` có cấu trúc cho 4 primitive dựng điểm có sẵn**:
   - `orthogonal_projection`, `orthogonal_projection_line`, `intersect_line_line`, `intersect_line_plane` đã có mặt trong `REGISTRY` và Exact Kernel nhưng chỉ dùng được khi đề đặt tên điểm tường minh (`Gọi H là ...`). Khi đề chỉ nêu mục tiêu cuối thông qua mô tả không đặt tên (ví dụ: *"độ dài đoạn nối C với hình chiếu vuông góc của A lên SD"*, *"khoảng cách từ giao điểm của AC và BD đến (SBC)"*), `_EffectResolver` trên `/22` từ chối dù chuỗi hàm hoàn toàn khả đạt.
   - Đồng thời, `_toan_hang_muc_tieu` trên `/22` tách toán hạng điểm mô tả bằng vị trí phẳng đồng nhất, chưa phân biệt chữ ký có cấu trúc `(Point, Line)`, `(Point, Plane)`, `(Line, Line)`, `(Line, Plane)`.
2. **Gap B-2 — Mặt phẳng phụ (`MAT_SONG_SONG`, `MAT_VUONG_DUONG`, `MAT_HAI_DUONG`) chỉ nhận `fact.point` đã đặt tên**:
   - Với lớp bài tiêu chuẩn §4.2 (*"Mặt phẳng (P) đi qua hình chiếu vuông góc của A lên SD và song song với (SBC). Xác định thiết diện và tính diện tích"*), `_mat_song_song` trên `/22` đòi `fact.point` là nhãn nguồn đã khai báo và không gọi `_EffectResolver.point(...)` để tự tìm chuỗi dựng điểm đi qua rồi nối tiếp sang `translate_point` → `section` → `ask_section_area`.
3. **Gap B-3 — Chọn mốc chiếu `MAT_VUONG_DUONG` bị khóa vào cạnh khung ban đầu của khối**:
   - Khi mặt phẳng phụ vuông góc với một đường thẳng dẫn xuất từ tiền đề như `SO` (với `O = AC ∩ BD`), `_chon_moc_vuong_duong` trên `/22` chỉ quét các cạnh khung của khối nên bỏ sót đường thẳng đi qua điểm tiền đề đã dựng.

### 2.2. Giải pháp tổng quát đã triển khai (0 hàm theo đề, 0 tên hàm đóng cứng trong `_EffectResolver`)

- **`registry.py` (`/28`)**:
  - Bổ sung `PlanningContract` kiểu `Point` cho `orthogonal_projection`, `orthogonal_projection_line`, `intersect_line_line`, `intersect_line_plane` kèm `parse_descriptor_inputs` theo đúng chữ ký kiểu `(Point, Plane)`, `(Point, Line)`, `(Line, Line)`, `(Line, Plane)`.
  - Cập nhật `planning_contract(spec, effect, descriptor)` để phân biệt không nhập nhằng khi một `FunctionSpec` có nhiều hợp đồng cùng `effect.kind` (như kiểm thử đối kháng gán hợp đồng giả).
  - Mở rộng `plane_point_chain` và `_mau_mat_phu_mo_ta` trong Source Gate để tái kiểm chứng từng bước dựng của điểm đi qua mặt phẳng phụ từ hợp đồng `REGISTRY`, chống đảo vai trò (`A lên SD` ≠ `D lên SA`) và chống giả mạo điểm `DERIVED` thành `GIVEN`.
- **`planner.py` (`/23`)**:
  - Giữ nguyên bề mặt provider khóa cứng (`TypedFact` JSON Schema SHA `aa9d93ee...`, `flat` surface `485d3834...`, `v3` surface `4bff35bb...`, Route A `7ea511a6...` — **0 byte thay đổi** nhờ `WithJsonSchema` cho `FLAT_POINT_KINDS` trong khi runtime chấp nhận đủ 6 `ALL_POINT_KINDS`).
  - `_EffectResolver.point(...)` giải hiệu ứng `Point` tổng quát từ `REGISTRY`, tự động memoize và tái sử dụng điểm phụ giữa nhiều mục tiêu (`self.reused`), đồng thời kết nối trực tiếp vào `_phan_giai_diem_mat_phu` cho `MAT_SONG_SONG`, `MAT_HAI_DUONG`, `MAT_VUONG_DUONG`.
  - `_chon_moc_vuong_duong` mở rộng tổng quát cho mọi đường thẳng tạo bởi các điểm tiền đề đã xác thực của hình, theo dõi bao đóng điểm cố định trên các mặt phẳng mang 2D (`carrier_planes`), ánh xạ vuông góc đường–mặt (`perp_faces`), và chọn cặp đường vuông góc không đồng phẳng tạo không gian $\mathbb{R}^3$ với đường thẳng dẫn xuất `d` (kể cả khi `d` nối giữa hai tầng của chóp hoặc lăng trụ, vd trọng tâm mặt bên `G = centroid(S, A, B)` hay `G = centroid(A, B, B')`).
  - Bổ sung `search_telemetry` tường minh (`classification` phân tách 3 nhãn `SOURCE_EXPLICIT_SEQUENCE` / `REGISTERED_DECOMPOSITION` / `DISCOVERED_FUNCTION_COMPOSITION`, `explored_states`, `search_depth`, `reused_intermediates`, `planner_originated_steps`, `search_budget`, và `outcome="SEARCH_EXHAUSTED"` khi chạm trần ngân sách tìm kiếm).
- **`engine.py` (`/20`)**:
  - Bổ sung kiểm chứng hậu điều kiện độc lập bằng tích vô hướng Gram và tọa độ affine trong `_MO_TA` cho cả 6 descriptor (`midpoint`, `centroid`, `orthogonal_projection`, `orthogonal_projection_line`, `intersect_line_line`, `intersect_line_plane`) trên cả `effect-chain` lẫn `point_operand` của mặt phẳng phụ, đồng thời kiểm tra bất suy biến cho điểm tiền định vị trong `_dung_khong` và mặt phẳng chiếu thẳng hàng trong `_mot_buoc` (`COLLINEAR_POINTS`). Mọi hợp đồng nói dối (`lying contract`) bị chặn bởi `ENGINE_SELF_CHECK_FAILED`.

---

## 3. Oracle Độc lập & Ma trận Chẩn đoán 24 Trường hợp qua 9 Nhãn (§§4.4, 7)

`backend/scripts/planning_oracle.py` (`0` import từ `planner.py`) duyệt không gian kế hoạch hữu hạn trực tiếp từ `REGISTRY` + thực thi qua Exact Kernel + kiểm chứng hậu điều kiện Gram/affine độc lập.

| Nhãn phân loại (§7) | Baseline `/22` | Hiện tại `/23` | Diễn giải kỹ thuật |
| --- | ---: | ---: | --- |
| `SOURCE_EXPLICIT_SEQUENCE` | 2 | 2 | Đề nêu sẵn từng bước dựng (`M = midpoint(SC)`, `O = AC ∩ BD`); Planner chỉ ánh xạ và sắp thứ tự DAG. |
| `REGISTERED_DECOMPOSITION` | 2 | 2 | Điểm đã đặt tên nhưng Planner sinh bước phụ theo quy tắc phân rã đã đăng ký (`distance(point, line)`, `MAT_SONG_SONG`). |
| `DISCOVERED_FUNCTION_COMPOSITION` | **0** | **9** | **9 chuỗi tổ hợp mới không gợi ý bước trung gian** được `_EffectResolver` tự tìm từ hợp đồng `REGISTRY` (gồm cả bài toán mẫu §4.2: `orthogonal_projection_line` → `translate_point` × 2 → `section` + `ask_section_area`, tái sử dụng điểm phụ đa mục tiêu, đường vuông góc dẫn xuất `SO`, và lăng trụ đứng `ABC.A'B'C'`). |
| `REACHABLE_BUT_SEARCH_MISSED` | **11** | **2** | Giảm từ 11 xuống 2. Hai trường hợp còn lại (`D1`: mô tả điểm lồng 2 tầng đệ quy; `D2`: hai đầu mút đều không đặt tên trong cùng một `ask_length`) được giữ nguyên có chủ đích vì schema phẳng `TypedFact` (`aa9d93ee...`) chỉ biểu diễn 1 `point_kind` phẳng cho mỗi fact câu hỏi. |
| `MISSING_PRIMITIVE` | 2 | 2 | Thiếu primitive toán học thật sự trong `REGISTRY`: `circumcenter` (tâm ngoại tiếp tam giác thường) và `incenter` (tâm nội tiếp). |
| `UNSUPPORTED_EXACT_DOMAIN` | 2 | 2 | Tổng số đo độ của các `arccos` vô tỉ ngoài bảng cyclotomic; thiết diện conic xiên của hình nón ngoài miền trục/vuông góc trục. |
| `INSUFFICIENT_GIVENS` | 2 | 2 | Thiếu chiều cao `SA` hoặc đáy tứ giác `ABCD` không cho hình dạng/độ dài (`MISSING_DIMENSION`). |
| `SOURCE_UNVERIFIED` | 2 | 2 | Đảo vai trò hình chiếu (`B lên SA` so với `A lên SB`) và giả mạo điểm `DERIVED` thành `GIVEN` (`SOURCE_OBJECT_MISMATCH`). |
| `NOT_ESTABLISHED` | 1 | 1 | Chuỗi lặp vượt giới hạn chân trời hữu hạn của oracle (`ORACLE_STEP_LIMIT = 8`), phân loại trung thực `NOT_ESTABLISHED`. |
| **Tổng cộng (`wrong_served = 0`)** | **24** | **24** | **100% (24/24) đồng thuận với Independent Planning Oracle & Exact Geometry Kernel.** |

---

## 4. Ranh giới Trung thực & Những Trường hợp Cần Primitive Mới (§§4.5, 13)

1. **Không đánh đồng 3 cơ chế lập kế hoạch**: `planner.py` phân tách tường minh `SOURCE_EXPLICIT_SEQUENCE` (chỉ ánh xạ bước đề nêu), `REGISTERED_DECOMPOSITION` (quy tắc phân rã 1 bước cho đối tượng đã đặt tên) và `DISCOVERED_FUNCTION_COMPOSITION` (tự hợp nhất typed `effect → input` qua nhiều hàm).
2. **Hai giới hạn biểu diễn còn lại (`D1`, `D2`)**: `REGISTRY` đã có đủ hàm và `planning_oracle.py` chứng minh tồn tại kế hoạch 3 bước (`√2`, `√6`), nhưng `TypedFact` giữ nguyên schema phẳng khóa cứng để bảo toàn 100% tương thích ngược với các bề mặt provider đã đóng băng. Muốn mở `D1`/`D2` ở tầng trích xuất cần nâng phiên bản schema đệ quy riêng trong tương lai.
3. **Các bài toán thật sự cần Geometry Function mới (`MISSING_PRIMITIVE`)**: tâm đường tròn ngoại tiếp tam giác bất kỳ (`circumcenter`), tâm đường tròn nội tiếp (`incenter`), trực tâm (`orthocenter`), và chân đường phân giác trong/ngoài (`angle_bisector_foot`) trên mặt phẳng 2D (lưu ý: mặt cầu ngoại tiếp/nội tiếp đa diện 3D đã có trên hợp đồng `typed-fact-next/2` qua `SolidSpec.circumscribes` / `SolidSpec.inscribed_in`, nhưng tâm đường tròn 2D nội/ngoại tiếp tam giác thường chưa là hàm dựng điểm `Point` trong `REGISTRY`). Chúng không thể biểu diễn bằng tổ hợp hữu hạn của `midpoint` / `centroid` / `divide_segment` với hệ số hằng độc lập dữ kiện.
