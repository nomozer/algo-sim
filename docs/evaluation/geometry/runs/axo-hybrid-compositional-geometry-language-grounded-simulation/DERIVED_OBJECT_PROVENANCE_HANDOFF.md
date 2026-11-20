# DERIVED_OBJECT_PROVENANCE_HANDOFF (`AXO HYBRID /12` P7 §19)

## 1. Vấn đề Quan sát được trên Sản phẩm Khóa (`A4`)

- Trong `backend/app/simulation/geometry_functions/engine.py` (tại dòng `~5137–5139`), tâm đáy `O` (`self.tam`) do chóp đều tự sinh không nằm trong `self.midpoints` / `self.centroids`, nên rơi vào nhánh `else:` cuối hàm `bien_dich` và được xuất dưới dạng:
  - `P.declare_point(ir_name(t), self.pts[t], t)`
  - `P.memory_declaration(ir_name(t), "point3", provenance="LAYOUT_DERIVED")`
- Vì vậy điểm `O` của chóp tứ giác đều (`S.ABCD`) và chóp tam giác đều (`S.ABC`) mang nhãn `provenance = "LAYOUT_DERIVED"` trong IR dù vị trí của nó hoàn toàn được xác định hình học từ các đỉnh đáy (`midpoint(A, C)` hoặc trọng tâm tam giác đáy `divide_segment(A, mid_BC, "2/3")`).

## 2. Hiện vật Bàn giao (Không chạm Mã Khóa `engine.py`)

- `engine.py` giữ nguyên **`0` diff** theo ma trận quyền sở hữu `A4`.
- Patch bàn giao: [`handoff/derived_point_o_provenance.patch`](handoff/derived_point_o_provenance.patch) (tạo tất định bằng `difflib.unified_diff`).
  - Với đáy 4 đỉnh (`self.root.base` có 4 điểm): dựng `O = midpoint(base[0], base[2])` qua `construct_point` và khai báo `P.memory_declaration("O", "point3")` (không gắn `LAYOUT_DERIVED`).
  - Với đáy 3 đỉnh (`self.root.base` có 3 điểm): dựng trung điểm `O_mid_BC = midpoint(base[1], base[2])` rồi `O = divide_segment(base[0], O_mid_BC, "2/3")` qua `construct_point`.
  - Với đa giác đáy `n >= 5`: giữ fallback `declare_point(..., provenance="LAYOUT_DERIVED")`.
- Kiểm thử cô lập: `backend/tests/geometry/test_v12_point_o_provenance_handoff.py` xác minh `git apply --check` sạch và chạy thử trên bản sao tạm trong subprocess cho cả chóp tứ giác đều lẫn chóp tam giác đều (`SERVED`, `provenance is None`, `kind == "construct_point"`).
