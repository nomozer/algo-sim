# M17-Lite Wave 2A — Targeted Live Smoke Report

> Budget user duyệt: ≤6 case / ≤20 HTTP · `gemini-2.5-flash` · production
> `run_pipeline`. **Đã dùng: 18/20 HTTP · 0 retry · 0 transient · 0
> reclassify.** Runner: `backend/scripts/live_smoke_m17_wave2a.py`. Artifact:
> `live_smoke.json`. Không đụng frozen M16/Wave 1, không chỉnh expectation.

## Kết quả: 5/6 PASS — 1 FAIL (case insufficient)

| # | Case | Kết quả | HTTP |
|---|---|---|---|
| 1 | preorder (VI, cơ chế tự nhiên) | ✅ `tree.traversal` variant=preorder | 3 |
| 2 | inorder (cây khuyết) | ✅ `tree.traversal` variant=inorder | 3 |
| 3 | postorder (EN — song ngữ) | ✅ `tree.traversal` variant=postorder | 3 |
| 4 | level_order ("từng tầng") | ✅ `tree.traversal` variant=level_order | 3 |
| 5 | cross-family graph DFS | ✅ `network.graph_traversal` variant=dfs (KHÔNG tree) | 3 |
| 6 | insufficient ("duyệt cây preorder") | ❌ **LLM tự BỊA cây** → `tree.traversal` variant=preorder | 3 |

## 4/4 tree + cross-family: đạt trọn

- 4/4 tree variant đúng family/capability/variant; executor chuyên biệt
  (simulate_attempts=1 mỗi case); **thứ tự duyệt KHÔNG nằm trong LLM spec**
  (config chỉ {specVersion,variant,rootId,nodes,notes} — không visitedOrder/
  steps/result; order do engine FE tính, offline-proven 39 oracle test).
- Cross-family: graph DFS route `network.graph_traversal` (KHÔNG nhầm tree).
- Song ngữ EN (postorder) route đúng.
- generic leak **0** · false refusal trên supported **0** · variant sai **0**.

## Case #6 (insufficient) — FAIL: false-positive simulation

**Đường đi thực:** analyze → classify **thẳng `tree.traversal`** (initial_route
= tree.traversal) → simulate **BỊA một cây đầy đủ** (nodes present) → ok. 3 HTTP.

**Vi phạm tiêu chí:** "insufficient prompt không tự sinh cây" và
"false-positive simulation = 0". Prompt "Mô phỏng duyệt cây preorder." KHÔNG
cho cấu trúc cây, nhưng LLM tự dựng cây mặc định rồi chạy executor — đúng thứ
R0 cấm (LLM không được bịa dữ liệu thiếu).

**Vì sao nghiêm trọng hơn base-5 (W1):** base-5 là từ chối AN TOÀN (0 false-sim)
chỉ lệch tag. Đây là **false-positive simulation THẬT** — hệ mô phỏng thứ người
dùng KHÔNG cung cấp. Không thể backlog nhẹ như base-5.

**Root cause:** classify.md 2f ĐÃ dặn "thiếu cấu trúc → unsupported, KHÔNG dựng
cây mặc định" nhưng LLM phớt lờ vì prompt tối giản. Hệ KHÔNG có lifecycle
clarification/insufficient_specification (chỉ ok/unsupported) → phòng thủ duy
nhất là LLM tự từ chối, mà LLM đã bịa. Đây là biểu hiện của bài toán chung
"LLM bịa dữ liệu thiếu" (không riêng tree).

## Trạng thái close

- **KHÔNG hit blocking "supported case sai":** 4/4 supported tree + cross-family
  đều đúng. Case #6 là insufficient (không phải supported case).
- **NHƯNG vi phạm "false-positive simulation = 0"** — tiêu chí cốt lõi. Wave 2A
  **CHƯA close** cho tới khi user quyết hướng xử lý case #6.
- Đây là quyết định của user — xem câu hỏi phiên làm việc.
