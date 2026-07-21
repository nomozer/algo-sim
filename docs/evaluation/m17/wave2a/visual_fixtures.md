# M17 Wave 2A — Visual Fixtures & Review Checklist (tree.traversal)

> Sáu fixture đại diện cho khâu **visual review** renderer cây (2D). Mỗi
> fixture: spec (LLM-fillable) + **thứ tự duyệt AUTHORITATIVE do engine tính**
> (không phải LLM) + kỳ vọng learner + checklist. Trạng thái renderer:
> **NEEDS_VISUAL_REVIEW** — SSR test (`tree.test.tsx`) đã xác nhận CẤU TRÚC
> (hiện đúng thứ tự engine, KHÔNG nhãn generic Điểm/Đoạn nối/Vật di chuyển),
> nhưng **chất lượng bố cục/độ rõ trong trình duyệt do người review xác nhận**
> — KHÔNG tự chấm REAL chỉ vì unit test xanh (đúng §8 kế hoạch).

Cây chuẩn dùng lại: `A(B(D,E), C(F,G))`.

## 1. preorder — cây cân bằng
- spec: `{variant: preorder, rootId: A, nodes: A(B,C) B(D,E) C(F,G) + lá D,E,F,G}`
- **authoritative order (engine): A → B → D → E → C → F → G**
- learner: "gốc trước, rồi TOÀN BỘ cây con trái, rồi cây con phải".
- panel: **ngăn xếp** (DFS). Event: push/pop/visit.

## 2. inorder — cây khuyết (thiếu con phải)
- spec: `{variant: inorder, rootId: A, nodes: A(B,C) B(D,·) C(·,·)}` (B chỉ có con trái D; C là lá)
- **authoritative order (engine): D → B → A → C**
- learner: "trái → gốc → phải; nút khuyết con thì bỏ qua nhánh đó".
- panel: ngăn xếp.

## 3. postorder — cây lệch trái
- spec: `{variant: postorder, rootId: A, nodes: A(B,·) B(C,·) C(D,·) D}` (chuỗi A→B→C→D)
- **authoritative order (engine): D → C → B → A**
- learner: "lá sâu nhất được thăm trước, gốc thăm cuối".
- panel: ngăn xếp (đường đệ quy = A,B,C,D rồi rút dần).

## 4. level_order — cây nhiều tầng
- spec: `{variant: level_order, rootId: A, nodes: A(B,C) B(D,E) C(F,G) D(H,·) + lá}`
- **authoritative order (engine): A → B → C → D → E → F → G → H**
- learner: "duyệt từng TẦNG từ trên xuống, trái sang phải".
- panel: **hàng đợi** (BFS). Event: enqueue/dequeue/visit.

## 5. single-node — biên
- spec: `{variant: preorder, rootId: X, nodes: [X]}`
- **authoritative order (engine): X**
- learner: "cây một nút — thăm đúng nút gốc".
- panel: ngăn xếp có đúng 1 phần tử rồi rỗng.

## 6. insufficient-input — thông điệp learner
- prompt: "Mô phỏng thuật toán duyệt cây theo thứ tự trước." (KHÔNG cho cấu trúc cây)
- kỳ vọng: **unsupported** — thông điệp learner thân thiện "chưa đủ dữ kiện để
  dựng cây" (KHÔNG tự dựng cây 7-node mặc định; KHÔNG JSON path/schema error).
- bằng chứng: `test_authenticity_audit::test_tree_regression_dong_route_specialized`
  (case `aud-regression-tree-insufficient`) + `learner_messages` (M17 W0).

## Checklist review (mỗi fixture 1–5)
- [ ] Gốc nhìn rõ (viền primary), phân biệt với nút thường.
- [ ] Quan hệ con TRÁI/PHẢI rõ (nhãn T/P trên cạnh).
- [ ] Nút current (cam) / visited (xanh) / chưa thăm (nền) phân biệt.
- [ ] Active path (gốc→current) nổi bật.
- [ ] Dải "thứ tự duyệt" hiện dần khớp authoritative order.
- [ ] Panel đúng loại: **ngăn xếp** (1–3,5) vs **hàng đợi** (4).
- [ ] KHÔNG có nhãn generic (Điểm/Đoạn nối/Vật di chuyển).
- [ ] Timeline (Next/Prev) đi qua từng bước engine.

## Kết luận
- Engine: **REAL** (4 variant khớp oracle đệ quy độc lập — `tree.test.tsx` 39
  test; validator + routing BE — 21 test).
- Renderer: **NEEDS_VISUAL_REVIEW** (cấu trúc đạt qua SSR; chờ review bố cục
  trình duyệt trước khi tuyên bố REAL toàn phần). Đây là limitation review,
  KHÔNG phải correctness issue.
