# M17-Lite — Curriculum Capability Expansion & Simulation Authenticity (PROPOSAL)

> **Trạng thái: PROPOSAL — chưa được duyệt, chưa có dòng code nào.**
> Tài liệu này là docs-only. Wave 0 chỉ bắt đầu sau khi user xác nhận scope.
> Đề tài: "Hệ thống mô phỏng tương tác 2D/3D kết hợp LLM phân tích bài toán
> bằng ngôn ngữ tự nhiên hỗ trợ dạy học môn Tin học THPT".

## 0. Baseline thực tế (đo ngày 2026-07-21, không dùng số kỳ vọng)

| Hạng mục | Giá trị thực đo |
|---|---|
| Branch / HEAD | `main` / `3504453` (tree sạch, 0 staged/unstaged) |
| Commit sau M16 close | `618ec00` (gitignore `/.claude/`) + `3504453` (FE test 2D/3D faithfulness — chỉ test/UI-polish, không đổi engine/contract) |
| Backend pytest | **660 passed, 2 skipped, 1 deselected** (14.70s) — khớp mốc M16 |
| Frontend vitest | **424 passed / 36 files** (5.22s) — +18 test/+3 file so mốc M16 (406/33), giải thích trọn bởi `3504453` |
| Production build | Sạch, 2.93s (cảnh báo chunk OrbitControls >500kB là pre-existing, không blocking) |
| CACHE_VERSION | `"13"` (`app/main.py:84`) |
| Catalog | **14 entry / 8 family** (xác nhận từ source: 8 `algorithm.*` + `algorithm.scan` + `logic.and_gate` + `binary.decimal_to_binary` + `network.packet_routing` + `network.protocol_encapsulation` + `generic.rule_scene`; `FamilyId` = 8 giá trị) |
| INTENTIONAL_GAP_MECHANISMS | 4 giá trị: `comparison_sort.select_extreme_repeated` · `comparison_sort.partition_recursive` · `comparison_sort.other_unspecified` · `positional_representation.non_binary_base` |
| FE domains | `algorithm`, `binary`, `generic`, `logic`, `network` |
| M16 frozen artifacts | Nguyên vẹn (tree sạch từ `1cc0123`/`eeedafd`) |

**Kết luận baseline: 0 blocking issue. Sai lệch duy nhất so mốc M16 (vitest 424/36
vs 406/33) được giải thích trọn vẹn bởi commit hợp lệ sau close.** Đủ điều kiện
mở milestone.

## 1. Scope M17-Lite (đã chốt với user, khác M17 full)

**Mandatory:**
- **Wave 0** — Automated Simulation Authenticity Audit + Algorithmic
  Authenticity Gate + learner-facing structured error mapping + automated
  curriculum coverage report.
- **Wave 1** — mở rộng 4 family hiện có: `positional_representation`,
  `boolean_composition`, `graph_traversal`, `comparison_sort`.
- **Wave 2** — 2 family mới chính thức: `tree_traversal`,
  `relational_table_query`.
- **Wave 3** — catalog-wide offline evaluation + targeted live + curriculum
  coverage closeout.

**Optional (checkpoint riêng, chỉ làm nếu effort/regression cho phép):**
- `text_encoding` (Wave 2.5).

**Future work — KHÔNG triển khai trong M17-Lite** (ghi vào coverage như gap
có chủ đích, làm claim trung thực hơn):
- `weighted_shortest_path` (Dijkstra), `bounded_control_flow`,
  `dom_css_resolution`.

**Nguyên tắc xuyên suốt (kế thừa nguyên vẹn):** R0; executor tất định sở hữu
state/trace/timeline/result/correctness; LLM chỉ sinh candidate spec; validator
hai tầng fail-closed; generic không nhận computational result ownership; gap
trung thực; bất biến #16–#23; Alembic sở hữu schema Postgres (M17-Lite dự kiến
**không** cần migration — không có persistent schema mới); M16 frozen artifacts
bất khả xâm phạm.

## 2. Wave 0 — Authenticity Audit & Generic Gate

### Tái sử dụng (phần lớn đã tồn tại — đây là lợi thế chính)
- **Bất biến #22**: audit chạy qua production `run_pipeline` + passive observer
  (hạ tầng M16: `observer.py`, `m16_record.py` 29-field structured-only,
  `m16_offline_scripts.py` scripted-provider + fault injection).
- **Gate đã có**: M13 `computation_gate.py` (`result_ownership` fail-closed:
  `algorithmic` → gap) **chính là lõi** của "Algorithmic Authenticity Gate";
  M14 `mechanism_gate.py`; M15 `classify_with_one_route_recovery` + direct-route
  ownership. Wave 0 **không viết lại gate** — nó kiểm chứng catalog-wide, và
  chỉ siết khi audit chứng minh có leak.
- `mechanisms.py` (owned XOR intentional-gap, machine-locked) → nguồn
  `near_miss_mechanisms`; `capability-descriptors.json` + sync-lock → nơi gắn
  authenticity contract; `coverage.py` → nền `curriculum_coverage.json`.

### Cần thêm
1. **Authenticity contract** — mở rộng descriptor (source-generated, sync-lock
   như cũ): `required_state_fields`, `required_trace_events`,
   `required_result_fields`, `renderer_semantic_requirements`,
   `generic_allowed`, `near_miss_mechanisms` (các trường
   `result_ownership`/`owned_mechanisms`/`executor_id` đã có sẵn từ M14/M15 —
   chỉ bổ sung phần thiếu, không tạo registry thứ hai).
2. **Audit runner** (`backend/app/evaluation/authenticity/`): sinh case matrix
   **từ registry/contract, không hard-code theo test ID** — ≥5 archetype mỗi
   capability (direct-name, paraphrase, changed-input, boundary, unsupported
   near-miss); chạy offline scripted qua `run_pipeline`; phân loại đóng
   {REAL, PARTIAL, REPRESENTATION_ONLY, GENERIC_LEAK, BROKEN, UNSUPPORTED}.
3. **Learner-facing error mapping**: audit đường đi `capability_gap` →
   thông báo thân thiện tiếng Việt trên FE; **không** JSON path / internal id /
   schema error lộ ra học sinh; developer diagnostics giữ đầy đủ trong
   structured events. Có test lock (nguồn scan kiểu `ui-hygiene.test.ts`).
4. **Regression "duyệt cây"**: case chuẩn — prompt duyệt cây **không** được
   dựng thành Điểm/Đoạn nối/Vật di chuyển; khi `tree_traversal` chưa có →
   phải là capability gap. Nếu audit chứng minh hiện tại leak qua generic →
   siết `computation_gate`/classify surface (thay đổi production DUY NHẤT
   được phép trong Wave 0, có bằng chứng leak kèm theo).
5. **Artifacts** (sync-lock, `docs/evaluation/m17/wave0/`):
   `authenticity_results.json`, `authenticity_metrics.json`,
   `generic_leak_ledger.json`, `curriculum_coverage.json`,
   `simulation_authenticity_report.md`, `curriculum_gap_report.md`.

### Effort / Rủi ro / Dependencies
- **Effort: M** (tái dùng nặng hạ tầng M16).
- **Rủi ro:** (a) audit phát hiện leak thật → cần siết gate = đổi production →
  CACHE bump + live smoke (đây là *mục đích* của wave, không phải tai nạn;
  scope siết được giới hạn ở gate/classify surface, cấm thêm capability);
  (b) prompt matrix sinh từ registry dễ trượt thành template vô nghĩa —
  mitigate: admission rule hiện có (`check_admission`) áp cho case sinh ra.
- **Dependencies:** không — chạy trên catalog hiện tại.

### Acceptance & checkpoint Wave 0
- 14/14 capability có authenticity contract + phân loại có bằng chứng.
- Generic leak ledger: mọi leak phát hiện được vá fail-closed hoặc ghi BACKLOG
  có phân loại NON-BLOCKING (kèm lý do).
- Regression duyệt cây: gap trung thực (chưa có family) — có test lock.
- Learner-facing error: 0 chuỗi kỹ thuật lộ ra học sinh (test lock).
- Full pytest/vitest/build xanh; tree sạch; commit checkpoint.
- **Điều kiện dừng:** phát hiện BROKEN ở capability đang public → dừng, báo
  cáo, chờ quyết định trước Wave 1.
- **Count sau Wave 0: 14 capability / 8 family (không đổi — wave đo lường).**

## 3. Wave 1 — Mở rộng 4 family hiện có

Nguyên tắc chung: **thêm target MỚI cạnh target cũ** thay vì sửa target đã
live-verified (giữ nguyên contract cũ, giảm regression); flip gap→owned trong
`mechanisms.py` (machine-locked owned XOR gap); **một** CACHE bump 13→14 cho
toàn bộ release Wave 1 (classify/analyze surface đổi một lần, coherent).

### A. positional_representation → base conversion tổng quát
- **Tái sử dụng:** FE domain `binary` (renderer chia-lấy-dư), spec
  `binary.decimal_to_binary` giữ nguyên; `binary-cfg-1` làm mẫu.
- **Thêm:** target mới `binary.base_conversion` — spec
  `{source_base, target_base, input_value, presentation_strategy}`; validator:
  base ∈ {2,8,10,16}, digit hợp lệ theo source base, bound input, canonical
  normalization khai tường minh (hex chữ HOA, cấm leading zero); executor:
  dec→X = quotient/remainder trace, X→dec = positional-weight trace, X→Y =
  **pivot qua decimal, trace 2 giai đoạn tường minh** (digit-grouping 2↔8/16
  là variant tương lai, KHÔNG làm trong M17-Lite); renderer: mở rộng binary UI
  (bộ digit theo base, chữ hex, view 2 giai đoạn).
- **Flip gap:** `positional_representation.non_binary_base` → owned.

### B. boolean_composition → bounded Boolean DAG + truth table
- **Tái sử dụng:** FE domain `logic` (`logic.and_gate` giữ nguyên,
  exploratory); generic boolean chaining M11 giữ vai trò scene staging.
- **Thêm:** target mới `logic.boolean_dag` — spec: DAG đóng (node
  input/AND/OR/NOT/XOR, edges, output khai báo); validator: acyclic, arity
  đúng (NOT=1; AND/OR/XOR=2 ở v1), reference hợp lệ, output duy nhất/khai báo,
  bound (≤4 input ⇒ truth table ≤16 hàng, ≤12 node); executor: thứ tự đánh giá
  topo, output từng node, truth-table rows, final output; renderer: sơ đồ cổng
  + panel truth table (timeline chạy theo hàng hoặc theo bước đánh giá).

### C. graph_traversal → BFS/DFS traversal tổng quát
- **Tái sử dụng:** FE domain `network` (graph layout 2D, semantic state
  node-id — đúng bất biến no-pixel); `network.packet_routing` **giữ nguyên**
  là bounded application variant của BFS.
- **Thêm:** target mới `network.graph_traversal` — spec: nodes, edges,
  directed flag, start, goal (optional), variant ∈ {bfs, dfs}; validator:
  reference + bound (unreachable là **kết quả**, không phải lỗi validate);
  executor: frontier (queue/stack), visited order, predecessor map, path
  reconstruction, unreachable result; renderer: tái dùng graph layout + panel
  frontier (queue vs stack) + dải visited order.

### D. comparison_sort → + Selection Sort
- **Tái sử dụng:** `core/algorithms.ts` + `trace-builder` + `decision.ts` +
  `interaction-policy.ts`; `FAMILY_SELECTORS` sorting (M14) thêm variant;
  renderer algorithm domain đã có sorted-boundary/swap.
- **Thêm:** `algorithm.selection_sort` — trace events: selection range,
  current min index, comparison, selection-completed, swap/place, sorted
  boundary; decision point riêng ("phần tử nhỏ nhất còn lại là gì?").
- **Flip gap:** `comparison_sort.select_extreme_repeated` → owned.
  **Quick Sort (`partition_recursive`) GIỮ là gap** — contract hiện tại không
  biểu diễn partition mechanism; không ép.

### Effort / Rủi ro / Dependencies (Wave 1)
- **Effort: L** (4 mở rộng, 4 target mới, nhưng toàn bộ renderer/domain nền
  đã có; không domain FE mới).
- **Rủi ro:** (a) menu classify lớn hơn đáng kể trong 1 bump → chất lượng
  routing — mitigate: near-miss case offline cho từng target mới TRƯỚC live,
  live smoke có duyệt budget; (b) truth-table là bề mặt renderer mới —
  mitigate: bound chặt 16 hàng; (c) normalization base conversion nhiều edge
  case — mitigate: oracle độc lập (so với `int(x, base)`/`toString(base)`),
  property tests; (d) **case pool cũ kỳ vọng gap sẽ flip hợp lệ** (hex-gap
  của `m15_wave1`/`m16`, selection-refusal): xử lý bằng **M17 expectation
  overlay có changelog** — artifact M16 dưới `docs/evaluation/m16/` và frozen
  30-case DATASET **không sửa một byte** (fingerprint lock vẫn xanh; frozen 30
  không chứa case hex/selection nên không bị ảnh hưởng trực tiếp).
- **Dependencies:** Wave 0 xong (audit làm chuẩn so sánh trước/sau; rerun
  audit sau Wave 1 phải sạch leak).
- **Live:** targeted smoke bắt buộc (classify surface đổi) — chờ user duyệt
  budget riêng.

### Acceptance & checkpoint Wave 1
- 4 target mới đạt đủ 15 mục acceptance (contract → live verification).
- Audit Wave 0 rerun: 0 GENERIC_LEAK mới, 0 BROKEN.
- Gap registry nhất quán (2 gap flip thành owned, quick sort giữ gap —
  machine-lock xanh).
- CACHE bump 13→14 đúng MỘT lần, ghi fingerprint + reason.
- Full pytest/vitest/build xanh; commit checkpoint; báo cáo count thực tế.
- **Count dự kiến sau Wave 1: 18 capability / 8 family.**

## 4. Wave 2 — Hai family mới: tree_traversal + relational_table_query

Cả hai theo đúng quy trình "Adding a new specialized domain" (CLAUDE.md):
SimSpec + descriptor K1 + validator BE, domain module FE mới + 1 dòng
register. Thêm 2 giá trị `FamilyId` + mechanisms + `FORMALIZED_FAMILIES`.
CACHE bump 14→15 (một lần, hai family vào menu cùng release).

### A. tree_traversal (FE domain mới `tree`, 2D-only có chủ đích)
- **Tái sử dụng:** `SimulationModule` + `timeline` capability; pattern
  semantic-state (node id, không pixel — layout thuộc renderer).
- **Spec:** variant ∈ {preorder, inorder, postorder, level_order}, root_id,
  nodes hữu hạn (binary tree), left/right refs, label học sinh.
- **Validator:** root tồn tại, id duy nhất, ref tồn tại, không cycle, không
  multi-parent, không disconnected, đúng binary, bound node (≤15, depth ≤5).
- **Executor:** current node, active path, stack (pre/in/post) hoặc queue
  (level), visited order, final result, trace events theo variant.
- **Renderer:** cây phân tầng rõ root + left/right, current/visited node,
  dải traversal order, panel stack/queue, timeline. **Cấm label generic**
  (Điểm/Đoạn nối/Vật di chuyển) — test lock kế thừa regression Wave 0;
  sau Wave 2 prompt duyệt cây phải route vào family này (đóng regression).
- **Oracle:** reference implementation độc lập 4 variant + property tests.

### B. relational_table_query (FE domain mới `table` — chính là "table/grid
domain" roadmap ghi "cần approval riêng"; proposal này là đề nghị approval đó)
- **Giá trị:** mở khóa mảng CSDL (coverage.py hiện ghi CAPABILITY_GAP
  "chưa có table/grid — gap trung thực") — vùng curriculum THPT trọng số cao.
- **Spec:** schema, rows, filter (AND/OR bounded), projected columns, sort
  rules, limit, optional aggregate ∈ {COUNT, SUM, AVG, MIN, MAX}.
- **Validator:** column ref tồn tại, type-operator phù hợp, aggregate target
  hợp lệ, bound rows/cols (đề xuất ≤30 hàng / ≤8 cột), sort deterministic
  (stable, tie-break khai báo).
- **Executor:** rows inspected theo thứ tự, predicate outcome từng hàng,
  accepted/rejected, projection, sorting trace, aggregation running state,
  final result table/value.
- **Renderer:** grid mới (highlight hàng đang xét, panel predicate, bảng kết
  quả) — **hạng mục UI mới lớn nhất của M17-Lite**; v1 layout cố định, không
  scroll ảo/tùy biến.
- **Ngoài phạm vi wave (fail về gap):** joins, subqueries, mutation, SQL tự
  do, kết nối DB thật.
- **LLM:** đề thiếu rows/schema → `insufficient_specification`; **cấm bịa
  dữ liệu mặc định** rồi coi là dữ liệu người học cung cấp.

### Effort / Rủi ro / Dependencies (Wave 2)
- **Effort: L–XL** (2 domain FE mới; grid renderer từ đầu chiếm phần lớn).
- **Rủi ro:** (a) scope creep grid renderer — mitigate: v1 đóng băng layout,
  danh sách "ngoài phạm vi" khai tường minh ở trên; (b) tree layout suy biến
  (cây lệch sâu) — mitigate: bound depth trong validator; (c) LLM điền rows
  dài sai type — mitigate: validator type-check từng cell + retry có lý do;
  (d) 2 family mới cùng bump → routing — mitigate như Wave 1 (near-miss
  offline trước, live smoke sau).
- **Dependencies:** Wave 1 đóng sạch (audit rerun xanh); regression duyệt
  cây của Wave 0 chuyển trạng thái gap → route (bằng chứng hai chiều).

### Acceptance & checkpoint Wave 2
- Mỗi family đạt đủ 15 mục acceptance (mục XI kế hoạch gốc), gồm oracle
  tests, near-miss, trace contract, renderer semantic contract, LLM routing,
  generic-leak regression, lifecycle integration, offline artifact, targeted
  live khi surface đổi.
- Renderer đẹp nhưng thiếu authoritative trace → KHÔNG tính hoàn thành;
  executor đúng nhưng UI generic → đánh PARTIAL, không REAL.
- **Điều kiện dừng:** generic leak hoặc oracle mismatch còn tồn tại → không
  sang wave sau.
- **Count dự kiến sau Wave 2: 20 capability / 10 family.**

## 5. Wave 2.5 (OPTIONAL) — text_encoding

Chỉ mở sau checkpoint riêng khi Wave 2 đóng sạch và user duyệt effort.
- Variants: character↔ASCII, character↔code point, text↔UTF-8 bytes,
  bounded comparison; executor sở hữu code points/byte groups/bit patterns/
  decode-encode trace; structured invalid-sequence result; không đồng nhất
  ký tự / code point / UTF-16 unit / UTF-8 byte.
- **Oracle độc lập:** `TextEncoder`/Python `codecs` cross-check.
- **Effort: M** · domain FE mới `encoding` (renderer dạng bảng byte/bit —
  tái dùng pattern binary UI). CACHE bump chỉ khi thật sự vào menu.
- **Count nếu làm: 21 capability / 11 family.**

## 6. Wave 3 — Evaluation & Coverage Closeout

- **Dataset M17 riêng** (`datasets/m17_catalog.py`): direct / paraphrase /
  VI + EN / changed-input / boundary / invalid-spec / near-miss /
  cross-family ambiguity / generic-leak control cho từng family mới+mở rộng;
  mỗi case ghi expected mechanism/family/variant/status/ownership/executor +
  required state/events/result; admission rule kép như M16. **Không sửa
  frozen M16 dataset/artifacts.**
- **Metrics:** tái dùng 17 metric M16 (công thức khóa trước, N/A ≠ 0.0) +
  bổ sung: trace contract coverage, renderer semantic projection coverage,
  variant accuracy cho family mới.
- **Offline trước — live sau:** offline deterministic xanh 100% là điều kiện
  mở live; live = production orchestration thật, representative cases, budget
  user duyệt; báo cáo HTTP/retry/transient/model thực tế.
- **Curriculum coverage dashboard:** registry máy-đọc (knowledge_unit_id,
  curriculum area, mechanism, family, capability/variant, support status,
  authenticity status, representation mode, evidence cases, remaining gaps)
  sinh **tự động** từ descriptor + authenticity contract + kết quả eval —
  trả lời 7 câu hỏi (mô phỏng thật / minh họa / partial / chưa hỗ trợ /
  từng leak / family phủ cao nhất / gap để future work). Người dùng không
  phải nhập tay từng prompt.
- **Final report:** actual metrics only; claim tự giới hạn theo đúng khuôn
  đã chốt (nêu số family/capability thực tại closeout; không claim phủ toàn
  bộ chương trình Tin học THPT).

## 7. Chính sách CACHE_VERSION & migration

- Dự kiến **2 bump có kế hoạch**: 13→14 (Wave 1 — classify/analyze surface),
  14→15 (Wave 2 — 2 family mới vào menu). Wave 0 chỉ bump **nếu** phải siết
  gate/classify có bằng chứng leak (báo cáo trước khi bump). Wave 2.5 bump
  riêng nếu được duyệt.
- Mỗi bump: đúng một lần cho một coherent release, ghi fingerprint + reason,
  chạy cache/history revalidation. **Không bump vì audit artifacts/docs.**
- **Alembic:** M17-Lite không dự kiến persistent schema mới → không migration;
  nếu phát sinh, dùng Alembic đúng quy trình OPERATIONS.md.

## 8. Tổng hợp effort & thứ tự

| Wave | Nội dung | Effort | Capability/Family sau wave | Live cần duyệt? |
|---|---|---|---|---|
| 0 | Audit + gate + error mapping + coverage | M | 14 / 8 | Chỉ nếu siết gate |
| 1 | Mở rộng 4 family (4 target mới) | L | 18 / 8 | Có (smoke) |
| 2 | tree_traversal + relational_table_query | L–XL | 20 / 10 | Có (smoke) |
| 2.5 | text_encoding (OPTIONAL) | M | 21 / 11 | Có (smoke) |
| 3 | Eval catalog-wide + coverage closeout | M | không đổi | Có (representative) |

Mỗi wave: targeted tests → full pytest/vitest/build → audit rerun → coverage
diff → commit checkpoint → báo cáo ≤20 dòng (HEAD/range, commits, counts,
test totals, build, audit summary, leaks, blocking, readiness). Wave có
blocking failure → dừng trước wave kế tiếp.

## 9. Final acceptance M17-Lite (điều chỉnh từ mục XIV kế hoạch gốc)

1. Generic algorithmic leak chặn fail-closed (bằng chứng audit + regression).
2. **2 family mới** (tree_traversal, relational_table_query) đủ spec /
   validator / executor / trace / renderer contract (+ text_encoding nếu
   được duyệt ở checkpoint 2.5).
3. 4 family hiện có mở rộng đúng phạm vi (4 target mới, quick sort giữ gap).
4. LLM sinh candidate spec cho mọi family mới/mở rộng; executor là nguồn
   duy nhất của authoritative result.
5. Curriculum coverage sinh tự động; không cần nhập tay từng bài.
6. M15/M16 contracts xanh; M16 frozen artifacts không đổi một byte.
7. Full pytest + vitest + build xanh; tracked tree sạch.
8. Offline catalog-wide eval hoàn tất; targeted live hoàn tất (budget duyệt).
9. 0 false-positive simulation trong unsupported cases đã eval; 0 generic
   leak trong computational cases đã eval.
10. Final report dùng actual metrics; claim nêu số thực tế
    (dự kiến 20/10 — hoặc 21/11 nếu 2.5 được duyệt) và không tuyên bố phủ
    toàn bộ chương trình Tin học THPT.

## 10. Điểm cần user quyết trước khi mở Wave 0

1. **Duyệt scope M17-Lite** như mục 1 (mandatory / optional / future work).
2. **Xác nhận nguyên tắc "expectation overlay"** cho case pool cũ kỳ vọng
   gap sẽ flip hợp lệ sau Wave 1 (hex/octal, selection) — artifact M16 và
   frozen DATASET không sửa; overlay có changelog.
3. **Chấp nhận trước** rằng Wave 0 có thể đề xuất 1 lần siết gate/classify
   (kèm bằng chứng leak) → 1 CACHE bump ngoài kế hoạch — sẽ báo cáo trước
   khi thực hiện, không tự ý.
4. Live budget sẽ xin duyệt **riêng từng wave**, không duyệt gộp trước.
