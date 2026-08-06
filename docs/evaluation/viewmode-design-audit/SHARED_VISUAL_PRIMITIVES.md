# SHARED_VISUAL_PRIMITIVES

Mục tiêu: đợt sau **không** đi làm 22 component thủ công. Nhóm target theo
*primitive cơ chế* tái sử dụng được, và ghi rõ renderer hiện đã có bao nhiêu phần.

Nguyên tắc giữ nguyên: **primitive chỉ ĐỌC state/event của engine**. Không
primitive nào được tự tính kết quả, không dựng hình tự do thay cho engine.

| Primitive | Target dùng | State cần | Event cần | 2D/3D | Hiện có | Còn thiếu |
|---|---|---|---|---|---|---|
| **Array scan** (dãy + vùng đã/chưa xét + con trỏ hiện tại) | find_max · find_min · count_if · sum_if · linear_search · scan · binary_search · 3 sort | `snapshot.array` · `ids` · `marks` | `compare` · `compare_value` · `mark` | 2D | **đầy đủ** — `components/ArrayView.tsx`, dùng lại ở 10 target | chú giải trạng thái dùng chung |
| **Compare pair** (cặp đang so + biểu thức quyết định) | bubble_sort · insertion_sort · selection_sort · binary_search | `snapshot` + sự kiện `compare` | `compare{i,j,result}` | 2D | **đầy đủ** — `.decision-strip` + `decision.ts` (cùng nguồn với ô dự đoán) | biểu diễn **hành động đổi chỗ**; hiện chỉ suy ra từ hai trạng thái |
| **Accumulator** (biến tích luỹ đổi theo bước) | count_if · sum_if · find_max · find_min · scan · bounded_control_flow | `snapshot.vars` | `assign_var` | 2D | **một phần** — chip biến ở panel Quan sát | chip nằm ở Quan sát, không nằm cạnh chỗ nó thay đổi trên sân khấu |
| **Held item + gap** (giá trị rút ra + ô trống để lại) | insertion_sort *(hiện tại)* · có thể dùng cho mọi thuật toán "nhấc–dời–đặt" | `snapshot.ids` (định danh bền) + `vars` | `shift{from,to}` · `insert{index,value}` | 2D | **đầy đủ nhưng CHƯA tách** — `insertionHold()` nằm trong `algorithm/ui.tsx`, `gapIndex` là prop của `ArrayView` | tách thành primitive dùng chung nếu có target thứ hai cần |
| **Loop axis** (trục giá trị + biên + 4 pha + cạnh quay lại) | bounded_control_flow *(hiện tại)* · dành cho `for` khi có | `snapshot.vars[loopVar]` qua các bước + spec (biến/op/biên) | `evaluate_condition` · `enter_branch` · `loop_iteration` · `assign_var` | 2D | **đầy đủ nhưng CHƯA tách** — `LoopStage`/`LoopAxis`/`LoopCycle` nằm trong `program-module.tsx` | tổng quát hoá cho `for` (miền lặp rời rạc) |
| **Queue (FIFO)** | graph_traversal (BFS) | `step.frontierAfter` | `visit` · `enqueue`/`push` (đang gộp trong `frontierAfter`) | 2D | **CHƯA CÓ** — frontier chỉ là chuỗi chữ "Hàng đợi: C, D" | toàn bộ: ô xếp hàng, phần tử vừa vào, phần tử vừa ra |
| **Stack (LIFO)** | tree.traversal (DFS/inorder) · graph_traversal (DFS) | `step.frontierAfter` | như trên | 2D | **CHƯA CÓ** — "Ngăn xếp: A, B" là chữ | toàn bộ: cột đẩy/lấy, đỉnh ngăn xếp |
| **Graph traversal** (node trạng thái + cạnh đang đi) | graph_traversal · tree.traversal | `nodes` · `edges` · `visitedOrder` · `frontierAfter` | `visit` · `enter_branch` | 2D | **một phần** — `tree.traversal` **đã** tô cạnh đang đi; `graph_traversal` **chưa tô cạnh nào** | đồng bộ hai target về cùng một cách vẽ |
| **Division remainder stack** (bảng chia mọc dần + đọc ngược) | base_conversion · character_encoding | `rows`/`trace` từng phép chia | bước chia (đã có trong trace) | 2D | **một phần** — cả hai đã có bảng; `character_encoding` **có** tô hàng hiện tại, `base_conversion` **không** | thống nhất tô hàng hiện tại; hình cho bước "đọc ngược" |
| **Bit weights** (ô bit + trọng số + đóng góp + tổng) | decimal_to_binary | `bits` · `bitWidth` | `toggle` | 2D | **đầy đủ** — `binary/ui.tsx` | — |
| **Layer stack** (chồng tầng + PDU thêm/gỡ) | protocol_encapsulation | `layers` · `steps[].pdu` | `add` · `remove` · `transmit` · `deliver` | 2D **+3D tuỳ chọn** | **đầy đủ** — `encap-ui.tsx` (2D) + `encap-ui3d.tsx` (3D, Z = tầng) | — |
| **Table pipeline** (dòng mang trạng thái qua từng tầng) | relational_table_query | `steps[].kind` · `row_index` · `filteredIndices` · `resultRows` | `read_row` · `keep` · `drop` · … | 2D | **đầy đủ** — `table-module.tsx`, nhãn Giữ/Loại/Đang xét | làm nổi tầng đang chạy trong dải chip |
| **Boolean signal graph** (node-edge + lan truyền + `?`) | boolean_dag · (and_gate là ca đặc biệt 1 cổng) | `config.gates` · `values` · `nodeOutputs` · `evalOrder` | `eval` | 2D | **đầy đủ** — `DagDiagram` trong `dag-module.tsx` | chú giải tín hiệu; tách màu "đầu ra" khỏi màu "tín hiệu 1" |
| **State legend** (chú giải trạng thái dùng chung) | **toàn bộ 22** | — (thuần trình bày) | — | 2D | **một phần** — `.stage-legend` + quy ước màu đã có trong `global.css`, mới dùng ở 2 target | áp cho 20 target còn lại |

## Đọc ra từ bảng này

1. **Ba primitive đã đủ và đang được tái sử dụng tốt** (Array scan, Layer stack,
   Table pipeline) — đó là lý do 10 target thuộc domain algorithm đạt 13–15 điểm
   mà không cần làm gì riêng cho từng target.
2. **Hai primitive vừa được viết nhưng còn nằm trong một module** (Held item+gap,
   Loop axis). Chưa cần tách vội — chỉ tách khi có target thứ hai dùng tới.
3. **Hai primitive còn thiếu hoàn toàn là Queue và Stack** — và đúng hai target
   thấp điểm nhất (`graph_traversal` 9, `tree.traversal` 11) đều thiếu chúng.
   Đây là chỗ một primitive dùng chung trả lại giá trị cao nhất: **một** thành
   phần "frontier" sửa được **hai** target.
4. **State legend là primitive rẻ nhất và phủ rộng nhất**: thuần trình bày, không
   chạm engine, áp được cho cả 22 target, và đang là tiêu chí thấp nhất toàn hệ.
