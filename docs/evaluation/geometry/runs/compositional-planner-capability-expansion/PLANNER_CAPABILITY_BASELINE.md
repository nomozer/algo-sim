# PLANNER_CAPABILITY_BASELINE — Khảo Sát Năng Lực Planner Trước Chiến Dịch (`compositional-planner-capability-expansion`)

- **Run ID:** `compositional-planner-capability-expansion`
- **Baseline anchor (`start_head`):** `c69c10fe6806012998c20245888f600ee9a1f218` (`docs(eval): simulation-first-mvp-stabilization reports, E2E/regression receipts and living docs`, candidate `077e3671a`, `CACHE_VERSION = 141`)
- **Kiến trúc khảo sát:** `Hybrid /4` tất định (`Local Geometry Parser /2` / `Gemini -> TypedFactNext /2` -> `bridge_v2` -> `Source Gate` -> `Planner /26` -> `Registry /33` -> `Exact Kernel /24` -> `Adapter /4` -> `Scene3D`), **`0` lượt gọi AI live**.

---

## 1. Cấu Trúc & Giới Hạn Năng Lực Tại Baseline (`c69c10fe6`)

Tại mốc nền `c69c10fe6`:
1. **`Planner /26` (`planner.py`) & `Registry /33` (`registry.py`):**
   - Đã có `_EffectResolver` tìm kiếm lùi giới hạn (`MAX_EFFECT_DEPTH = 4`, `MAX_EFFECT_NEEDS = 96`, `MAX_EFFECT_CANDIDATES = 48`, `MAX_FRESH_POINTS = 16`, `MAX_CALLS = 64`) và hai luật phân rã khai báo sẵn `DINH_NGHIA_DIEM` (`orthocenter`, `circumcenter`) và `DINH_CAT_CANH`.
   - Nhưng mục tiêu `TypedFact.point_tree` chỉ biểu diễn được **một toán hạng điểm mô tả đơn** trên khoảng cách điểm-đường/điểm-mặt hoặc một số nhánh cục bộ; chưa có cấu trúc `goal_trees` tổng quát cho:
     - Mục tiêu chứa **nhiều toán hạng mô tả đồng thời** (vd: độ dài `Segment(@m1, @o1)` — `MG5`, `R1-F02`/`D2`; góc giữa đường nối `@a` với `@b` và đường/mặt khác; diện tích tam giác `@a, @b, @c`).
     - **Đường thẳng dẫn xuất có đầu mút `@id`** trong `distance(line, plane)` (`PA3`, `C3-dist`) hoặc góc giữa hai đường thẳng có `@id`.
   - `_EffectResolver` chưa giải chuỗi kết hợp cho `AnswerDistanceLinePlane` khi đường thẳng có đầu mút mô tả dẫn xuất, chưa đọc các đối tượng điểm định nghĩa/mô tả đa tầng từ `POINT_DEFINITIONS` + `arg_items` trong nút lồng, và `_dinh_cat_canh` chưa tái sử dụng điểm chia đoạn (`midpoint` / `divide_segment`) sẵn có trên cạnh cắt.
2. **Bridge (`typed_fact_next_bridge.py`):**
   - `_mo_ta_phang` mới xử lý phẳng hạn chế, chưa duyệt DAG topo cho mô tả `@id` lồng sâu tới bậc 2 (`D1`, `test_family_d2`), `centroid`/`POINT_DEFINITIONS`/`arg_items`, hoặc đường dẫn xuất đầu mút `@id`.
   - `_la_mat_qua_ba_diem` trên thiết diện 3 điểm mô tả (`SE3`) chưa tự gắn quote `area` cho `section` khi `simulation_goals` không khai báo `construct_plane_section`; mục `area(section_id)` chưa truyền `point_tree` cho thiết diện qua `@id` bậc 2.
3. **Source Gate (`registry.py`) & Exact Kernel (`engine.py`):**
   - `_kiem_result_binding` chỉ chứng thực một tập hẹp kiểu chuỗi (`mode`), chưa hỗ trợ đồng bộ cây lồng `centroid`/độ sâu 2/`derived_line`/multi-`@id`, dẫn tới từ chối `SOURCE_OBJECT_MISMATCH` hoặc `UNSUPPORTED_CAPABILITY` trên `PL5`, `PA3`, `MG5`, `SE3`, `RE10`, `D1`, `D2`, `C3-dist`.
   - `Mode A output-policy/1` (`_kiem_don_vi_hoi`) khi gặp chuỗi `effect-chain` đa mô tả không rơi về kiểm `ask_id`, làm rớt các câu hỏi làm tròn trên `@id` phức hợp.
   - `engine.py::kiem_mo_ta` và `kc2_dich` chưa kiểm định đệ quy cây toán hạng lồng đa nhánh và khoảng cách `distance_line_plane` trên đường thẳng dẫn xuất mà không va chạm khóa di sản `GOAL_VERIFIER_TARGET["distance_line_plane"]`.

---

## 2. Bảng So Sánh Baseline Trước Thay Đổi (Từ Bằng Chứng Gốc Repository)

| Hạng mục đo (Offline Development) | Nguồn baseline tại `c69c10fe6` | Trạng thái trước wave | Khoảng trống cần đóng |
|---|---|---|---|
| `reasoning_matrix.py` (`72` ca) | `test_hybrid_reasoning_generalization.py` | **`56 / 62`** dương · `10 / 10` âm · `0` phục vụ sai | `6` `xfail` đã ghi nhận: `PL5`, `PA3`, `MG5`, `SE3`, `RE10`, `MG9` (`PLAN_TOO_LARGE` / `MAX_MEMORY_DECLARATIONS = 32`) |
| `r1-live-pilot-corpus.json` (gold) | `r1-live-pilot-gold-replay-final.jsonl` | **`13 / 15`** phục vụ (`(13, 0, 0)`) | `R1-F01` (`D1` `√6/2`) và `R1-F02` (`D2` `√2`) vẫn ở trạng thái từ chối ranh giới |
| `r1-described-point-probe.json` | `test_route_d4_described_points.py` | `12` ca dương cơ bản + `X1–X6` | Thiếu `C3-dist` (`ask_distance_line_plane` với `@id` = `0`) |
| `test_production_dynamic_composition.py` | C19 suite | `11` ca đạt, `test_family_d2` `xfail` | `test_family_d2` (hình chiếu của trực tâm `@o1` lên `(ABCD)` đến `(SAD)`) chưa qua bridge/Source Gate/Planner |
| Thiết diện qua `@orthocenter` (`C6a` biến thể) | `test_route_d_function_composition.py:237` | `REFUSED` (stated C18 boundary) | `plane_point_chain` chưa đọc điểm định nghĩa (`DINH_NGHIA_DIEM`) trong chuỗi mặt phẳng |

---

## 3. Ràng Buộc Kiến Trúc & Phạm Vi Bất Biến Khi Bước Vào Wave

1. Giữ nguyên `Hybrid /4` tất định (`Local Geometry Parser /2` / `TypedFactNext /2` -> `Source Gate` -> `Planner /26` -> `Registry /33` -> `Exact Kernel /24` -> `Adapter /4`); không chuyển sang AI-guided Planner, không sinh mã cho từng đề, không hardcode ID/tọa độ/đáp án.
2. Giữ nguyên mọi hợp đồng khóa bề mặt: `TypedFact.model_json_schema()` SHA-256, `typed_fact_next_surface_fingerprint()`, `function_calling.surface_fingerprint()`, `fact_extraction.surface_fingerprint("flat")` & `surface_fingerprint("v3")`, `NO_PLANNER_HARDCODING`, và `CACHE_VERSION = 141`.
3. Không nâng trần `MAX_MEMORY_DECLARATIONS = 32` (`MG9` giữ `PLAN_TOO_LARGE`); không sửa `typed_fact_next.py` (`@id` trong `PlaneConstraintSpec` giữ `INVALID_QUALIFIED_REF`); không chạm worktree Frontend `axo-geometry-library` (`FE-2/3/4/6 = BLOCKED_OWNERSHIP`).
