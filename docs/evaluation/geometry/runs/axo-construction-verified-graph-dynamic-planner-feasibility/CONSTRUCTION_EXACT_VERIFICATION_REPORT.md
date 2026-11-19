# CONSTRUCTION EXACT VERIFICATION REPORT (Phase F — L0–L4)

- **Run ID:** `axo-construction-verified-graph-dynamic-planner-feasibility`
- **Verifier Version:** `construction-exact-verifier/1`
- **Source Modules:**
  - [construction_verifier.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/experimental/construction_planner/construction_verifier.py)
  - [construction_operators.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/experimental/construction_planner/construction_operators.py)
  - [certificates.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/simulation/geometry_functions/certificates.py)

---

## 1. Năm tầng kiểm chứng độc lập (`L0`–`L4`)

| Tầng | Nội dung kiểm chứng | Khả năng chứng minh từ Exact Kernel /24 | Trạng thái trên 40 ca Gold |
| --- | --- | --- | --- |
| **L0 — Type Validity** | Ràng buộc kiểu toán hạng của `OperatorSpec` + tính DAG/định danh/tồn tại đối tượng (`validate_construction_graph`) | `EXISTS_VERIFIED` (tất định hoàn toàn) | `33/33` ca dương `PASS` |
| **L1 — Preconditions & Degeneracy** | Kiểm tra Sylvester SPD trên `chart_metric` + điểm phân biệt, không thẳng hàng, không song song/chứa trong khi giao, hai đường chéo nhau khi dựng đoạn vuông góc chung | `EXISTS_VERIFIED` (`Fraction` + `GeometryError`) | `7/7` ca âm/suy biến từ chối an toàn |
| **L2 — Geometric Relation Validity** | Chứng minh trực tiếp trong `with metric.using(chart_metric):`: `dot(u,v) == 0`, `sin_sq_line_plane == 1`, `signed_eval == 0`, định lý đường vuông góc hai đường cắt nhau (`verify_two_lines_deductive_perp_plane`), `cos_sq(ray1, ray2) == cos_sq(P, Q)` cho góc nhị diện | `EXISTS_VERIFIED` trên mọi ca đa diện hữu tỉ | `33/33` ca dương mang chứng chỉ `L2` |
| **L3 — Goal Correctness** | `evaluate_goal_if_witnessed` **cấm tính toán goal nếu chứng nhân dựng hình tương ứng chưa tồn tại** (vd: chưa dựng `H ∈ (SBC)` và chứng minh `perp_point_plane_witness`), sau đó so bình phương/căn thức chính xác bằng `Fraction` & `Radical` | `EXISTS_VERIFIED` (công thức chỉ kích hoạt sau khi có chứng nhân) | `33/33` khớp oracle độc lập qua `axo-math-evaluator/2` |
| **L4 — Scene Continuity** | `validate_construction_continuity(scene3d)` kiểm tra đồng nhất frame `canonical_chart_v1`, bất biến nguồn gốc, không phụ thuộc trước tạo, không biến mất đối tượng, đầy đủ `perpendicular_witness` | `EXISTS_VERIFIED` (backend JSON) | `33/33` `0 issues` (`PASS`) |

---

## 2. Xử lý các trường hợp suy biến & mâu thuẫn (§13)

| Trường hợp suy biến tối thiểu | Cơ chế kiểm tra | Mã lỗi chuẩn & Thực nghiệm |
| --- | --- | --- |
| Hai điểm trùng nhau | `verify_points_distinct` / `(p - q).is_zero()` | `DEGENERATE_COINCIDENT_POINTS` (`D02` từ chối trong khi Baseline A trả `0a`) |
| Ba điểm thẳng hàng | `verify_non_collinear` / `(b - a).cross(c - a).is_zero()` | `DEGENERATE_COLLINEAR_POINTS` (`D03` từ chối an toàn) |
| Mặt phẳng không xác định | `canonical_plane_key` + `Plane3.through` | `DEGENERATE_UNDEFINED_PLANE` / `DEGENERATE_COLLINEAR_POINTS` |
| Đường thẳng song song không giao | `intersect_line_plane` / `intersect_line_line` (`GeometryError`) | `DEGENERATE_PARALLEL_NO_INTERSECTION` (`D04` từ chối an toàn) |
| Vuông góc bất khả thi | `M.dot(u, v) != 0` / `sin_sq != 1` / `normal_dot != 0` | `IMPOSSIBLE_PERPENDICULARITY` (xác minh trong unit test) |
| Đối tượng phụ không duy nhất | `plane_through_line_parallel_line` khi 2 đường song song/đồng phẳng | `NON_UNIQUE_AUXILIARY` / `DEGENERATE_NON_SKEW_LINES` |
| Kích thước không hợp lệ | `_check_explicit_edge_contradictions` / `ratio <= 0` / `area == 0` | `NON_POSITIVE_DIMENSION` |
| Ràng buộc mâu thuẫn | Bất đẳng thức tam giác, xung đột độ dài, ma trận Gram không SPD | `CONTRADICTORY_CONSTRAINTS` (`D05` từ chối an toàn) |

---

## 3. Giới hạn chứng minh hiện tại của Kernel
1. Miền tọa độ và Gram metric hoạt động chính xác trên không gian affine hữu tỉ $\mathbb{Q}^3$ (`Fraction`) và kết quả căn thức bậc hai đơn (`a√b`, `ExactNumber`); các cấu hình cần giải hệ đa thức bậc cao / khối tròn xoay tiếp xúc tổng quát (`D06`) không thuộc miền chứng minh và bị phân loại fail-closed `UNSUPPORTED_OPERATOR` (`Case C`).
