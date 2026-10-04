# M17-Lite Wave 2A — Bounded Tree Traversal Family (DESIGN)

> Chỉ Wave 2A (`tree_traversal`). KHÔNG `relational_table_query` (Wave 2B chưa mở).
> Baseline: `main` @ `378e53d`, 18 target / 8 family, CACHE 14, pytest 732 /
> vitest 487 / build sạch.

## 1. Mục tiêu & ranh giới

Family mới `tree_traversal`: LLM sinh bounded `TreeTraversalSpec` cho cây nhị
phân hữu hạn; **deterministic executor sở hữu toàn bộ** traversal order / state
/ timeline / result / correctness. Đóng regression duyệt cây (CONDITIONAL_LEAK
probe Wave 0).

**Owned mechanisms (canonical, prefix = family_id — bắt buộc theo M15):**
- `tree_traversal.preorder`
- `tree_traversal.inorder`
- `tree_traversal.postorder`
- `tree_traversal.level_order`

(KHÔNG dùng prefix `binary_tree.*` — sẽ vỡ `mechanism_family()` matching của
route-consistency gate. "Nhị phân" nằm ở tên biến thể + contract.)

**KHÔNG sở hữu (near-miss → capability_gap/unsupported, KHÔNG nhận nhầm):**
BST insert/search/delete · AVL/RB balancing · heap ops · expression-tree eval ·
n-ary tree · general graph DFS/BFS (đã thuộc `network.graph_traversal`) ·
Dijkstra/weighted.

## 2. Routing — classify-based (nhất quán W1)

`tree_traversal` route bằng classify (KHÔNG analyze-exposed — giống
boolean_dag/graph_traversal W1). Variant do LLM chọn trong spec, validate cấu
trúc. Không keyword-router độc lập; classify đọc catalog description +
machine-readable ownership. Ranh giới cross-family **tree DFS vs graph DFS**:
- cây (có root + quan hệ trái/phải, duyệt trước/giữa/sau/theo mức) →
  `tree_traversal`;
- đồ thị chung (đỉnh/cạnh, BFS/DFS tổng quát) → `network.graph_traversal`.

## 3. TreeTraversalSpec (bounded, versioned `tree-1.0`)

```
{ spec_version: "tree-1.0",
  variant: "preorder"|"inorder"|"postorder"|"level_order",
  root_id: <string>,
  nodes: [ { id, label, left?, right? } ] }   // ≤15 node, depth ≤5
```
LLM sinh: variant + cấu trúc cây + labels. LLM **KHÔNG** sinh: traversal order,
visited sequence, stack/queue timeline, correctness. Config KHÔNG chứa đáp số.

## 4. Validation hai tầng (fail-closed, structured error)

**Structural:** spec_version đúng · variant ∈ enum · node id duy nhất, kiểu
đúng · label renderer-safe · 1 ≤ n ≤ 15 node · left/right là string hoặc vắng.
**Semantic:** root tồn tại · mọi child ref tồn tại · không self-loop · không
cycle · không multi-parent · mọi node reachable từ root (không disconnected) ·
đúng binary tree (mỗi node ≤1 left, ≤1 right) · depth ≤5.
Learner UI KHÔNG thấy JSON path / id kỹ thuật / schema trace.

## 5. Deterministic executor + trace (4 variant PHÂN BIỆT THẬT)

Executor là nguồn duy nhất: current_node, visited_order, active_path,
stack (pre/in/post) hoặc queue (level), completion, final result.

Event taxonomy (authenticity contract quy định event bắt buộc THEO variant):
- chung: `traversal_started`, `node_visited`, `traversal_completed`
- pre/in/post (stack): `stack_pushed`, `stack_popped`, (`left_selected`/
  `right_selected` khi rẽ)
- level_order (queue): `queue_enqueued`, `queue_dequeued`

Cùng spec → cùng trace + result (tất định). Oracle độc lập (đệ quy viết riêng,
KHÔNG gọi executor) đối chiếu cả 4 order trên cây chuẩn + single/skewed/
incomplete/uneven + label số/chữ.

## 6. Renderer chuyên biệt (2D bắt buộc; 3D không bắt buộc W2A)

Root rõ · quan hệ trái/phải rõ · current/visited/unvisited khác nhau · active
path · traversal order hiện dần · panel stack (pre/in/post) hoặc queue
(level) đúng variant · timeline dùng authoritative trace · label đúng thuật
ngữ. **CẤM** Điểm/Đoạn nối/Vật di chuyển/generic label. Một chấm chạy qua node
KHÔNG đủ REAL.

## 7. Đóng regression Wave 0 (CONDITIONAL_LEAK)

Prompt "Mô phỏng thuật toán tìm kiếm cây duyệt theo thứ tự trước":
- thiếu cấu trúc cây → insufficient_specification (KHÔNG tự dựng cây 7-node);
- có cấu trúc cây → `tree_traversal` variant=preorder;
- KHÔNG hợp lệ: generic success / point-edge-moving scene / LLM-order làm
  authoritative / title tree nhưng executor generic.
Probe adversarial Wave 0 đóng bằng evidence (audit fixture cập nhật + eval).

## 8. Catalog / cache

Sau W2A: **9 family**, target +1 (`tree_traversal`) → **19 target** (nếu
registry không tách variant thành target riêng — báo actual). CACHE bump
**14→15** một lần (classify surface đổi: thêm tree_traversal + thuật ngữ VI/EN).
Không sửa frozen M16 / Wave 1 expectation.

## 9. Checkpoints
2A.1 design + family/spec contract · 2A.2 validators + oracle · 2A.3 executor +
trace · 2A.4 catalog/routing · 2A.5 renderer · 2A.6 authenticity + leak
regression · 2A.7 offline eval + visual fixtures · 2A.8 full regression +
closeout offline → DỪNG xin duyệt live.
