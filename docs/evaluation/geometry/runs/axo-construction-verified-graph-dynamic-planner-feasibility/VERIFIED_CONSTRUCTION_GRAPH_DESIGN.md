# VERIFIED CONSTRUCTION GRAPH DESIGN (`verified-construction-graph/1`)

- **Run ID:** `axo-construction-verified-graph-dynamic-planner-feasibility`
- **Prototype Status:** `RESEARCH_PROTOTYPE_NON_PRODUCTION`
- **Core Modules:**
  - [__init__.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/experimental/construction_planner/__init__.py)
  - [construction_objects.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/experimental/construction_planner/construction_objects.py)
  - [construction_graph.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/experimental/construction_planner/construction_graph.py)
  - [construction_serializer.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/experimental/construction_planner/construction_serializer.py)

---

## 1. Kiến trúc tách đôi đồ thị (§3 & §14)

1. **`ConstructionProofGraph` (`verified-construction-graph/1`)**: Lưu toàn bộ DAG chứng minh hình học gồm 5 loại nút (`GIVEN`, `CONSTRUCTION`, `DERIVED_RELATION`, `VERIFICATION`, `GOAL`), chứng cứ đại số chính xác trên `Fraction` / Gram `Metric`, và xuất xứ từng đối tượng.
2. **`PresentationStepGraph` (`presentation-step-graph/1`)**: Chiếu tất định từ `ConstructionProofGraph` đã kiểm chứng. Các nút kiểm tra nội bộ (`VERIFICATION` và ràng buộc đánh dấu `presentation_internal_only=True`) bị lọc khỏi bước hiển thị cho học sinh nhưng được nhúng làm `explanation_evidence.attached_verifications` của bước sở hữu. Không bước trình bày nào được phép tuyên bố một quan hệ hoặc đối tượng chưa có trong `ConstructionProofGraph` ở trạng thái `VERIFIED`.

---

## 2. Phân biệt nguồn gốc & Định danh chính tắc đối tượng

| Nguồn gốc (`ObjectOrigin`) | Ý nghĩa | Quy tắc an toàn |
| --- | --- | --- |
| `GIVEN_OBJECT` | Đối tượng tồn tại từ giả thiết nguồn của đề | Có `source_fact_refs`; sinh từ nút `GIVEN` |
| `DERIVED_OBJECT` | Đối tượng/quan hệ suy ra hoặc dẫn xuất trực tiếp từ giả thiết qua phép tính/suy diễn tất định | Phải trỏ `supporting_node_id` hợp lệ |
| `AUXILIARY_CONSTRUCTION` | Điểm phụ, đoạn phụ, mặt phẳng phụ do Planner tìm ra khi dựng hình | Ràng buộc cứng trong `ConstructionObject.__post_init__`: `source_fact_refs` phải rỗng; không được sinh từ nút `GIVEN` |

**Định danh hình học chính tắc (`canonical_geom_key`) tách khỏi nhãn hiển thị (`object_id`):**
- `point3`: bộ ba hữu tỉ `(x, y, z)`.
- `segment3`: cặp khóa điểm đầu-cuối sắp thứ tự chuẩn.
- `line3`: chuẩn hoá phương bằng tọa độ khác 0 đầu tiên $= 1$ và khử anchor theo trục pivot (`anchor - d_norm * anchor[pivot]`) để hai cặp điểm cộng tuyến bất kỳ sinh **cùng một khóa `ln(...)`**.
- `plane3`: chuẩn hoá covector dual `(nx, ny, nz, -n·P)` theo thành phần pháp tuyến khác 0 đầu tiên để mọi bộ ba điểm không thẳng hàng đồng phẳng đều cho **cùng một khóa `pl(...)`**.

---

## 3. Lược đồ Node (16 trường bắt buộc §4) & Bất biến DAG (§5)

Mỗi `ConstructionNode` chứa đủ 16 trường: `node_id`, `node_type`, `geometric_object_type`, `object_refs`, `geometry_context`, `source_fact_refs`, `producing_operation_id`, `input_object_ids`, `preconditions`, `derived_constraints`, `output_objects`, `dependency_ids`, `verification_status`, `verification_evidence`, `exact_computation_ref`, `scene3d_render_hints`.

**Quy tắc fail-closed của `validate_construction_graph`:**
- Chu trình phụ thuộc $\Rightarrow$ `CYCLIC_DEPENDENCY`.
- Thiếu nút phụ thuộc, thiếu đối tượng vào/ra hoặc thiếu tiền điều kiện $\Rightarrow$ `MISSING_PRECONDITION`.
- Bất kỳ nút nào không có `verification_status == "VERIFIED"` hoặc thiếu `verification_evidence` $\Rightarrow$ `UNVERIFIED_CONSTRUCTION`.
- Nút `CONTRADICTORY` hoặc `AUXILIARY_CONSTRUCTION` gán vào `GIVEN` $\Rightarrow$ `CONTRADICTORY_CONSTRAINTS`.
- Hai nút `CONSTRUCTION` khác nhau sinh cùng `canonical_geom_key` $\Rightarrow$ `DUPLICATE_GEOMETRIC_CONSTRUCTION`.
- Hỗ trợ `topological_order`, `trace_dependencies`, `find_unused_nodes`, `prune_to_goal_closure`, và `canonical_json_dumps` + SHA-256 LF tất định.
