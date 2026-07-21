# M17-Lite Wave 2A — Live Verification Report (Pha A + Pha B)

> Runner reproducible `backend/scripts/live_smoke_m17_wave2a.py`,
> `gemini-2.5-flash`, production `run_pipeline`. Artifacts:
> `live_smoke.json` (pha A, 6 case) · `live_stability.json` (pha B, 5 lần lặp).
> Không sửa frozen M16/Wave 1, không chỉnh expectation để làm case pass.

## Lịch sử ba lần chạy live (trung thực)

| Run | Bối cảnh | Kết quả |
|---|---|---|
| 1 | trước mọi gate | 5/6 · 18 HTTP — **insufficient: LLM BỊA CÂY** (false-positive simulation) |
| 2 | structure gate **v1** (đếm số lượng) | 4/6 · 16 HTTP — gate **không đủ** (analyze mô tả trừu tượng đếm ra rel=1/obj=2 → sẽ cho qua); case inorder **chặn oan** do classify lạc generic |
| 3 | gate **v2** (định danh nút) + consistency gate | **Pha A 5/6 · 20 HTTP** + **Pha B 5/5 · 15 HTTP** |

## Pha A — re-verify 6 case · **20/20 HTTP** (3 hỏng do bug print + 17 chạy lại) · 0 retry · 0 transient · 0 reclassify

| # | Case | Route | Variant | mech (analyze) | Gate | Evidence |
|---|---|---|---|---|---|---|
| 1 | preorder | `tree.traversal` | preorder | `tree_traversal.preorder` | PASS | linked=4, ids A–E |
| 2 | inorder (cây khuyết) | `tree.traversal` | inorder | `tree_traversal.inorder` | PASS | linked=3, ids A–D |
| 3 | postorder (EN) | `tree.traversal` | postorder | `tree_traversal.postorder` | PASS | linked=3, ids A–D |
| 4 | level_order | `tree.traversal` | level_order | `tree_traversal.level_order` | PASS | linked=6, ids A–G |
| 5 | graph DFS | `network.graph_traversal` | dfs | **None** | NOT_RUN | không bị kéo sang tree |
| 6 | insufficient | — (unsupported) | — | `tree_traversal.preorder` | **NOT_RUN_BY_DESIGN** | **linked=0, ids=[]** |

**Báo cáo hai lớp (layered-defense semantics đã duyệt):**
- **Functional safety acceptance: 6/6** — không case nào bịa cây / tạo
  simulation sai / rò generic / sai executor.
- **Exact expected-path acceptance: 5/6** — case 6 đi đường A (early refusal)
  thay vì đường B (routed-tree refusal).
- **Case insufficient: `EARLY_SAFE_REFUSAL`** — analyze nhận diện đúng cơ chế
  (`tree_traversal.preorder`), **classify tự từ chối** (`initial_route=None`),
  computation gate M13 chặn → `capability_gap`. Executor không chạy, không
  simulation envelope, không generic, không dựng cây, learner message sạch.
- **`structure_gate: NOT_RUN_BY_DESIGN`** — gate là route-dependent; classify
  đã từ chối an toàn TRƯỚC nên gate không cần chạy (không đổi thứ tự pipeline,
  không ép gate chạy trước classify).
- **Structure evidence: `linked=0, ids=[]`** — tín hiệu gate v2 **tính đúng
  "không có cấu trúc"** cho chính analyze của case này (v1 cho ra rel=1/obj=2
  → sẽ cho qua; lỗ hổng đã bịt).
- **Offline forced-route regression** (`test_tree_traversal_routing.py::
  test_forced_route_insufficient_gate_fail_voi_analyze_live_that`): ép route
  sang `tree.traversal` với **đúng analyze evidence live** → gate **FAIL**,
  `error_code=structure_insufficient`,
  `failure_category=insufficient_specification`, không simulation. Tầng phòng
  thủ 2 được chứng minh hoạt động, không chỉ "không cần chạy".

**Thu hoạch phụ:** analyze.md mới có hiệu lực — analyze đặt đúng
`tree_traversal.*` cho cây và **None** cho đồ thị chung (không kéo nhầm
cross-family). Normalization không làm mất quan hệ cụ thể (định danh trích
đúng từ từng item).

## Pha B — classify stability · 5 lần lặp case inorder · **15/15 HTTP** · 0 retry · 0 transient

| Chỉ số | Giá trị |
|---|---|
| repetitions | **5** |
| `initial_route_distribution` | **{tree.traversal: 5}** |
| `final_route_distribution` | **{tree.traversal: 5}** |
| final variant inorder | **5/5** |
| structure gate PASS | **5/5** (linked=3, ids A–D mỗi lần) |
| deterministic tree executor | **5/5** (simulate_attempts=1) |
| total reclassifications | **0** |
| consistency fail-closed count | **0** |
| generic leak | **0/5** |
| false-positive simulation | **0/5** |
| false refusal | **0/5** |
| retry / transient | **0 / 0** |

- **initial-route stability: 5/5** · **final-route stability: 5/5** — cả hai đều
  đồng nhất, không che dao động bằng cách chỉ báo final.
- **n = 5 là mẫu nhỏ**, không phải bằng chứng thống kê. Run 2 từng cho thấy
  đúng prompt này lạc sang generic → **không tuyên bố classifier ổn định tuyệt
  đối**; chỉ ghi: trong 5 lần đo sau khi phơi bày mechanism, initial route
  không dao động.
- **Consistency gate chưa kích hoạt live** (reclassifications=0) vì classify đi
  thẳng tree — nó là lưới an toàn, đã chứng minh **offline** (reclassify về
  tree; vẫn generic → fail-closed, không tạo generic simulation).

## Budget tổng

| Pha | HTTP | retry | transient | reclassify |
|---|---|---|---|---|
| A (6 case) | 3 (bug print) + 17 = **20/20** | 0 | 0 | 0 |
| B (5 lặp) | **15/15** | 0 | 0 | 0 |
| **Tổng** | **35/35** | **0** | **0** | **0** |

## Trạng thái Wave 2A

**CLOSE về correctness/routing.** Acceptance pha A (layered) và pha B đều đạt.
- Renderer: **NEEDS_VISUAL_REVIEW** (chưa review trình duyệt) — xem
  `visual_fixtures.md`.
- Wave 2B (`relational_table_query`) **chưa mở**.

## Backlog — Analyze Integrity (KHÔNG tuyên bố đã giải quyết)

> Structure gate deterministic **trên analyze output**. **Provenance /
> source-span của từng object/relation CHƯA được xác minh** — analyze
> hallucination vẫn có thể tạo false structural evidence (ví dụ tự bịa "nút A",
> "B là con của A" cho đề trống thì gate không phân biệt được). Gate v2 chỉ
> nâng ngưỡng: đòi quan hệ giữa hai nút CÓ TÊN thay vì mô tả trừu tượng — đã
> chặn được dạng hallucination quan sát thực tế (run 2, run 3), **chưa** chặn
> được hallucination có định danh. Đây là **Analyze Integrity backlog**, còn
> mở.

Backlog khác (từ W1, còn mở): base ngoài {2,8,10,16} → `capability_gap`;
heuristic PARTIAL của audit (dual-authority ≠ partial-authenticity).
