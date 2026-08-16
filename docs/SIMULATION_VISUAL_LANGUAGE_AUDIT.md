# SIMULATION_VISUAL_LANGUAGE_AUDIT.md — BẢN ĐO **TRƯỚC**

> **Đây là bản audit BEFORE. KHÔNG một bản vá trình bày nào được áp trong lúc đo.**
> Toàn bộ 22 dòng mô tả **một** baseline nguồn duy nhất: `099ea303702d7391400026b40a10640803e131cc`
> (`git diff --check` sạch; working tree chỉ chứa guard toàn vẹn chưa commit).
> Đây là bằng chứng cho đóng góp **T3 — biểu diễn mô phỏng sư phạm**. Nó KHÔNG
> nói gì về kết quả học tập: `LEARNER_IMPACT_NOT_EVALUATED`, `CURRICULUM_SUPPORT_PARTIAL`.

## A. Phương pháp

**Nguồn 22 id:** `frontend/src/simulations/capability-descriptors.json` → `runtime_targets`
— artifact sinh từ registry backend, đã có sync-lock riêng. Không gõ tay danh sách.

**Luật bằng chứng.** Một chuỗi chỉ được gọi là *học sinh nhìn thấy* khi truy được
tới đường render thật: JSX của Workspace/renderer, hoặc một helper mà JSX đó
render (`narrate()`, decision model, legend builder, action-zone model). Chuỗi
lỗi validator, chú thích, fixture test, nhánh chết **không** tính. Lượt đo đầu
của wave này từng grep chuỗi tiếng Việt và bắt trúng **chú thích code** — kết
quả đó đã bị vứt bỏ, và luật này ra đời từ đó.

**"Quan sát" nghĩa là gì:** những gì học sinh thấy khi panel Giải thích **đóng**
và cổng Thí nghiệm **đóng**.

**Chữ không mặc nhiên là xấu.** `CURRENT` · `MID` · `LOW/HIGH` · `HELD` · `GAP`
· `FRONTIER` · `STACK` · `QUEUE` · `8 < 9` · `signal = 1` là **biểu diễn ngữ
nghĩa**, không phải prose. Phân loại theo **việc mà chữ đang làm**, không theo
số ký tự. Bằng chứng cho luật này nằm ngay trong bảng: `logic.and_gate` bị chấm
`LONG_TEACHING_PROSE` mà vẫn là `VISUAL_SELF_SUFFICIENT`.

**Bốn phân loại.** `VISUAL_SELF_SUFFICIENT` (biểu diễn + nhãn gắn-trạng-thái là
đủ) · `VISUAL_WITH_SHORT_CAPTION` (cần thêm đúng một caption bước) ·
`TEXT_DEPENDENT` (không hiểu được cơ chế nếu không đọc prose ngoài biểu diễn) ·
`REPRESENTATION_GAP` (ngữ nghĩa CÓ trong engine nhưng học sinh không tri giác
được ở Quan sát).

**Cách chạy.** Tám agent đo **tuần tự** (concurrency 1), mỗi họ cơ chế một agent,
chỉ ĐO — không đề xuất kiến trúc. Lượt trước fan-out 8 agent song song kèm
synthesis `effort:high` và chết cả 9 vì session limit, tiêu 823k token cho 0
dòng. Lượt này 8/8 xong, 0 lỗi.

## B. Bảng 22 dòng — phân loại

| # | target | family | mức | Observe prose | Explain? | phân loại | phát hiện chính xác |
|---|---|---|---|---|---|---|---|
| 1 | `algorithm.binary_search` | search (SEARCH_FAMILY, decision.ts:464) | INTERACTIVE·WHAT_IF | SHORT_CAPTION | NO | **REPRESENTATION_GAP** | Phần tử giữa ở bước quyết định (chỉ .decision-strip); giá trị cần tìm; biên trai/phai chỉ có trong thuyết minh bước set_range; tiền đề 'chỉ đúng khi dãy đã sắp tăng dần' không có kênh thị… |
| 2 | `algorithm.bounded_control_flow` | bounded control flow (assignment /… | STEP_VIS | SHORT_STATE_BOUND | NO | **REPRESENTATION_GAP** | non-loop programs: all variable values (narration only); branch taken (BRANCH_LABEL text "nhánh THÌ"/"nhánh NGƯỢC LẠI") |
| 3 | `algorithm.bubble_sort` | sort family… | INTERACTIVE·WHAT_IF | SHORT_STATE_BOUND | NO | **VISUAL_SELF_SUFFICIENT** | — |
| 4 | `algorithm.count_if` | scan + accumulator (SCAN_FAMILY, 4… | INTERACTIVE·PREDICT | SHORT_CAPTION | NO | **VISUAL_WITH_SHORT_CAPTION** | — |
| 5 | `algorithm.find_max` | scan + accumulator (SCAN_FAMILY, 4… | INTERACTIVE·WHAT_IF | SHORT_CAPTION | NO | **VISUAL_SELF_SUFFICIENT** | — |
| 6 | `algorithm.find_min` | scan + accumulator (SCAN_FAMILY, 4… | INTERACTIVE·WHAT_IF | SHORT_CAPTION | NO | **VISUAL_SELF_SUFFICIENT** | — |
| 7 | `algorithm.insertion_sort` | sort family, ArrayView stage + hold/gap… | INTERACTIVE·WHAT_IF | SHORT_STATE_BOUND | NO | **VISUAL_SELF_SUFFICIENT** | — |
| 8 | `algorithm.linear_search` | search (SEARCH_FAMILY, decision.ts:464) | INTERACTIVE·WHAT_IF | SHORT_STATE_BOUND | NO | **REPRESENTATION_GAP** | Giá trị cần tìm và phép so sánh ('Đang xét 7 (vị trí 3) — cần tìm: 9', '7 = 9 ?') chỉ ở .decision-strip; chi phí (đã so sánh/chưa xét/xấu nhất) không hiện ở đâu trong Quan sát |
| 9 | `algorithm.scan` | single-pass array scan with accumulator… | STEP_VIS | SHORT_STATE_BOUND | YES | **REPRESENTATION_GAP** | accumulator value on to_constant variants (tổng/đếm), the comparison constant/threshold, comparison count in final result |
| 10 | `algorithm.selection_sort` | sort family, ArrayView stage | INTERACTIVE·WHAT_IF | SHORT_STATE_BOUND | NO | **REPRESENTATION_GAP** | "nhỏ nhất hiện tại" (vars.vi_tri_cuc_tri) and "Phần chưa sắp: vị trí 2–6" (set_range) exist only as SortActionZone chips; sort order likewise |
| 11 | `algorithm.sum_if` | scan + accumulator (SCAN_FAMILY, 4… | INTERACTIVE·PREDICT | SHORT_CAPTION | NO | **REPRESENTATION_GAP** | Running total `tong` (decision strip "tổng: 12", narration "Cộng thêm 5 → tong = 17"); condition threshold (only inside "5 > 3 ?" and step-0 narration) |
| 12 | `binary.base_conversion` | binary / đổi cơ số {2,8,10,16},… | STEP_VIS | SHORT_STATE_BOUND | NO | **REPRESENTATION_GAP** | which step is current; the intro step and the stage-1/stage-2 boundary (kind 'intro'/'stage' render an empty sim-stage); the read-upward rule |
| 13 | `binary.character_encoding` | binary / mã hoá ký tự, progressive | STEP_VIS | SHORT_STATE_BOUND | NO | **VISUAL_WITH_SHORT_CAPTION** | — |
| 14 | `binary.decimal_to_binary` | binary / hệ cơ số — bit toggle,… | INTERACTIVE·WHAT_IF | SHORT_STATE_BOUND | NO | **VISUAL_WITH_SHORT_CAPTION** | — |
| 15 | `database.relational_table_query` | Single-table query pipeline (filter →… | STEP_VIS | SHORT_STATE_BOUND | NO | **TEXT_DEPENDENT** | The filter predicate itself and its per-clause evaluation (column, operator, compared value, actual cell, AND/OR result) exist only in the shell narration line built by narrateStep (table-… |
| 16 | `generic.rule_scene` | DSL v1 rule/reveal scene — spatial… | INTERACTIVE·WHAT_IF | SHORT_STATE_BOUND | NO | **REPRESENTATION_GAP** | NONE in Observe — values are digits inside the shapes. Note: the rule set is absent from Observe entirely (Inspector "QUY TẮC", closed panel), and RevealStep.narration is uncapped LLM text… |
| 17 | `logic.and_gate` | logic — single-gate circuit exploration | INTERACTIVE·WHAT_IF | LONG_TEACHING_PROSE | NO | **VISUAL_SELF_SUFFICIENT** | — |
| 18 | `logic.boolean_dag` | logic — multi-gate boolean circuit (DAG) | INTERACTIVE·WHAT_IF | SHORT_STATE_BOUND | NO | **VISUAL_SELF_SUFFICIENT** | — |
| 19 | `network.graph_traversal` | network graph traversal — BFS (queue) /… | STEP_VIS | SHORT_STATE_BOUND | NO | **VISUAL_SELF_SUFFICIENT** | — |
| 20 | `network.packet_routing` | network routing — packet forwarding… | INTERACTIVE·PREDICT | SHORT_STATE_BOUND | NO | **REPRESENTATION_GAP** | MISSING SEMANTIC: state.destination vs state.source — 2D collapses both to isEnd stroke 3.5, so the goal of routing is named only in narration/Inspector (3D does mark it with rings + "·… |
| 21 | `network.protocol_encapsulation` | network protocol encapsulation — TCP/IP… | INTERACTIVE·PREDICT | SHORT_STATE_BOUND | NO | **VISUAL_WITH_SHORT_CAPTION** | — |
| 22 | `tree.traversal` | Binary-tree traversal — DFS pre/in/post… | STEP_VIS | SHORT_STATE_BOUND | NO | **REPRESENTATION_GAP** | GAP: buildDfs Frame.stage (0=before-left, 1=between, 2=after-right) — the rule deciding WHEN visit fires — is never put on TreeStep nor rendered; traversal variant appears only in step-0… |
| 23 | `web.style_model` | Bounded presentation properties — learner sets a closed set of CSS properties and the model recomputes the rendered artifact | INTERACTIVE·EXPLORATION_FIRST | SHORT_STATE_BOUND | NO | **VISUAL_SELF_SUFFICIENT** | W4B-2Z. Split workspace: bounded controls left, dominant preview right, generated CSS view beneath. State proximity is inherent — the control and its consequence sit in one eyeline. No timeline (no temporal process), no Experiment row, no Challenge. Truth is the bounded model; the browser only paints state. Limitation: five properties only; no text editing of the artifact; JS remains UNSUPPORTED (`code_experiment` deferred) |
| 24 | `color.rgb_model` | color — RGB colour model: three 0..255 channels compose one colour | INTERACTIVE·EXPLORATION_FIRST | SHORT_STATE_BOUND | NO | **VISUAL_SELF_SUFFICIENT** | W5A. Stage reads in one direction: three ramped sliders (each ramp holds the other two channels fixed, so the control answers "where does this go" before it is dragged) above a dominant swatch carrying `rgb(...)` and `#rrggbb`. Swatch label ink is chosen by BT.601 luma so it stays legible across the whole 24-bit range. No timeline (composition is instantaneous, transport RESET_ONLY), no Challenge (there is no next step to commit to). Colour names appear ONLY at the eight cube corners — naming an arbitrary mix would be a renderer-invented aesthetic judgement, not a derived fact. Limitation: additive RGB only; no CMYK, no colour space claims |

## C. Bảng 22 dòng — nguồn ngữ nghĩa vs chủ sở hữu trình bày

> `semantic_source` là nơi **sự thật** sống (engine/state). `presentation_owner` là nơi **vẽ** nó.
> Hai cột này cố ý tách: một từ vựng ngữ nghĩa dùng chung KHÔNG kéo theo một component dùng chung.

| target | semantic_source | presentation_owner (từ vựng vai trò) | objects · roles |
|---|---|---|---|
| `algorithm.binary_search` | `core/algorithms.ts::runBinarySearch` | core/types.ts Mark + ArrayView (nhãn 'nửa đã bị loại' là biến thể family-local trong… | Cột SVG ArrayView (giá trị + vị trí 1-based) + con trỏ ▲; không có ngoặc/khung… · nửa đã bị loại (xám, mark eliminated), đang xét/so sánh (xanh + ▲, chỉ ở bước… |
| `algorithm.bounded_control_flow` | `core/program.ts::runProgram` | own family-local convention (loop-axis / loop-cycle / loop-cond classes) | loop shape: SVG value axis with bound line, phase-cycle chips, var chip, cond… · current value (primary dot, enlarged), visited values (green dots), stop bound… |
| `algorithm.bubble_sort` | `frontend/src/core/algorithms.ts::runBubbleSort` | core/types.ts Mark + ArrayView | ArrayView SVG bars (value above, 1-based index below, optional name label),… · compare pair = sky fill + arrow; swap = orange fill; sorted = green; default =… |
| `algorithm.count_if` | `core/algorithms.ts::runAggregateIf` | core/types.ts Mark + ArrayView (family-local FOUND_LABEL inside ArrayView.tsx) | SVG bar columns (value label + 1-based position), triangle pointer, StageLegend… · current element (sky + pointer), đã được đếm (green), đã duyệt qua (gray) |
| `algorithm.find_max` | `core/algorithms.ts::runFindExtreme` | core/types.ts Mark + ArrayView (family-local CONSIDERING_LABEL/FOUND_LABEL inside ArrayView.tsx) | SVG bar columns (value label + 1-based position), triangle pointer, StageLegend… · current element (sky + pointer), max hiện tại (teal, no pointer), đã duyệt qua… |
| `algorithm.find_min` | `core/algorithms.ts::runFindExtreme` | core/types.ts Mark + ArrayView (family-local CONSIDERING_LABEL/FOUND_LABEL inside ArrayView.tsx) | SVG bar columns (value label + 1-based position), triangle pointer, StageLegend… · current element (sky + pointer), min hiện tại (teal, no pointer), đã duyệt qua… |
| `algorithm.insertion_sort` | `frontend/src/core/algorithms.ts::runInsertionSort` | core/types.ts Mark + ArrayView, plus family-local hold/gap convention (insertionHold +… | ArrayView bars, dashed "trống" gap column (ArrayView.tsx:393), hold-tray card… · held card outside array; gap = dashed frame (different shape, not just color);… |
| `algorithm.linear_search` | `core/algorithms.ts::runLinearSearch` | core/types.ts Mark + ArrayView | Cột SVG ArrayView: giá trị trên đỉnh, vị trí 1-based dưới chân, nhãn tên nếu đề… · đang xét/so sánh (xanh + ▲, event compare_value), đã duyệt qua (xám, mark… |
| `algorithm.scan` | `core/scan.ts::runScan` | core/types.ts Mark + ArrayView | ArrayView SVG bar columns: value on top, 1-based index below, optional element… · current-compared (sky fill + pointer), held winner mark considering (teal, no… |
| `algorithm.selection_sort` | `frontend/src/core/algorithms.ts::runSelectionSort` | core/types.ts Mark + ArrayView | ArrayView bars + arrow pointer; SortActionZone chips (ungated, visible in… · compare bars i and j both sky + arrow (identical styling); swap = orange;… |
| `algorithm.sum_if` | `core/algorithms.ts::runAggregateIf` | core/types.ts Mark + ArrayView (family-local FOUND_LABEL inside ArrayView.tsx) | SVG bar columns (value label + 1-based position), triangle pointer, StageLegend… · current element (sky + pointer), đã được cộng vào tổng (green), đã duyệt qua… |
| `binary.base_conversion` | `simulations/domains/binary/base-conversion.ts::buildConvSteps…` | NONE | two plain HTML tables (weight 4-col, divide 4-col) plus a bold result sentence;… · NONE — no row highlight, no color, no marks anywhere in the JSX |
| `binary.character_encoding` | `simulations/domains/binary/encoding-module.tsx::runCharacterEncoding…` | own family-local convention (truth-table + is-current) | 5-column encoding table with progressive rows and '…' placeholders;… · is-current blue tint (#e8f2fd) on the in-progress row and on the newest… |
| `binary.decimal_to_binary` | `simulations/domains/binary/model.ts::decimalOf +…` | own family-local convention | SVG row of bit cells (rect per bit), place-value label above, bit digit inside,… · bit=1 filled --primary with white digit; bit=0 canvas-soft with faint digit;… |
| `database.relational_table_query` | `frontend/src/simulations/domains/database/table-…` | own family-local convention — local STATUS badge set; no Mark, ArrayView, or StageLegend | HTML table of source rows, per-row status badge column, numbered stage-chip… · Đang xét (orange + play icon), Giữ (green + check), Loại (cross + strikethrough… |
| `generic.rule_scene` | `frontend/src/simulations/domains/generic/model.ts::valuesOf +…` | own family-local convention — DSL object-type vocabulary + NODE_COLOR map; no Mark, ArrayView,… | SVG scene — switch pills showing 0/1, lamps showing 0/1, value boxes,… · current (gen-pop + gen-glow + thicker stroke) / completed / hidden (not… |
| `logic.and_gate` | `domains/logic/model.ts::andOutput (state: index.ts::makeAndGateModule)` | own family-local convention | SVG circuit: two toggle switches, D-shaped AND gate, three wires, output lamp… · switch on/off (green pill + knob position), wire energised/dead, lamp lit/dark,… |
| `logic.boolean_dag` | `domains/logic/dag-module.tsx::initFromValues (evaluateDag, topoOrder,…` | own family-local convention | layered node-edge SVG: input pills, gate boxes labelled by op, orthogonal… · input pill vs gate box; output = dashed frame + ĐẦU RA; active gate = thick… |
| `network.graph_traversal` | `domains/network/traverse-module.tsx::TraverseState via buildTraversal…` | own family-local convention (edge-view.ts EdgeStatus + components/TraversalFrontier); not… | ellipse-layout SVG graph, TraversalFrontier queue/stack widget, "đã thăm"… · node current/visited/in-frontier/idle fills; edge… |
| `network.packet_routing` | `domains/network/model.ts::NetworkState (2D ui.tsx and 3D ui3d.tsx read…` | own family-local convention (edge-view.ts EdgeStatus + NODE_COLOR by NodeType); not… | 2D SVG: node circles + id/type text, link lines, pink packet dot above current… · node type (5 stroke colours); endpoint (stroke 3.5 — source and destination… |
| `network.protocol_encapsulation` | `domains/network/encap-model.ts::EncapState (2D encap-ui.tsx and 3D…` | own family-local convention (encap-model PduRole + ROLE_COLOR / ROLE_COLOR_3D); not… | 2D: MÁY GỬI / MÁY NHẬN columns × 4 layer boxes, PDU segment row drawn only… · segment role border colour payload/header/trailer; active layer box (tint +… |
| `tree.traversal` | `frontend/src/simulations/domains/tree/tree-…` | own family-local convention — shared TraversalFrontier primitive + .stage-legend CSS; no Mark /… | SVG binary tree (circles + edges), TraversalFrontier stack/queue panel, "đã… · Tree: current=orange fill, visited=green fill, root=primary ring,… |

## D. Bảng 22 dòng — quan hệ · chuyển tiếp · tiến độ · phát hiện

| target | relations | transition | progress | phát hiện chính xác | bằng chứng |
|---|---|---|---|---|---|
| `algorithm.binary_search` | Nửa bị loại vs phần còn sống bằng màu (vùng xét đọc được bằng vắng-mặt-xám); quan hệ… | Cả một nửa dãy chuyển xám cùng lúc, nhưng CHẬM MỘT BƯỚC: mark… | Vùng xám thu hẹp dần + 'Bước k / n'; chip 'vùng xét 1–7' và số lần so… | Phần tử giữa ở bước quyết định (chỉ .decision-strip); giá trị cần tìm; biên trai/phai chỉ có trong thuyết minh bước set_range; tiền đề 'chỉ đúng khi dãy đã sắp tăng dần' không có kênh thị giác nào và… | D:/Documents/projects/algo-… |
| `algorithm.bounded_control_flow` | distance from current value to stop bound; last-jump arc between the two most recent… | dot moves along axis, new visited dot plus jump arc, active phase cell… | shell footer SimulationControls.tsx:134 "Bước k / n" plus range slider | non-loop programs: all variable values (narration only); branch taken (BRANCH_LABEL text "nhánh THÌ"/"nhánh NGƯỢC LẠI") | frontend/src/simulations/domains/algorithm/program-module.tsx:299-357 |
| `algorithm.bubble_sort` | the two adjacent compared bars co-highlighted; green sorted suffix vs unsorted prefix… | id-keyed columns slide via CSS transform 0.35s on swap; height/fill… | "Bước k / N" indicator + seek slider (SimulationControls.tsx:134,151)… | SortActionZone chips "Vị trí 3 / 7" repeat value and 1-based position already printed on the bars | frontend/src/simulations/domains/algorithm/ui.tsx:200-255;… |
| `algorithm.count_if` | counted set (green) vs skipped set (gray); count = number of green columns. No… | discrete step; CSS fill 0.25s recolor of the just-tested column | shell step indicator "Bước k / n" + seek slider… | Count step shows NarrationSlot "Đếm thêm 1 → dem = 3" AND consequence strip "…biến đếm tăng: 2 → 3" | frontend/src/simulations/domains/algorithm/ui.tsx:281 + components/ArrayView.tsx:193 |
| `algorithm.find_max` | candidate vs current-max readable by bar height; scanned/unscanned boundary as gray… | discrete step; CSS fill/height 0.25s + column translate 0.35s | shell step indicator "Bước k / n" + seek slider… | Update step shows NarrationSlot "Cập nhật: max = 9" AND consequence strip "…max được cập nhật: 7,5 → 9"; decision strip restates candidate value+position already printed on the column | frontend/src/simulations/domains/algorithm/ui.tsx:281 + components/ArrayView.tsx:141 |
| `algorithm.find_min` | candidate vs current-min readable by bar height; scanned/unscanned boundary as gray… | discrete step; CSS fill/height 0.25s + column translate 0.35s | shell step indicator "Bước k / n" + seek slider… | Update step shows NarrationSlot "Cập nhật: min = …" AND consequence strip "…min được cập nhật: a → b"; decision strip restates candidate value+position already on the column | frontend/src/simulations/domains/algorithm/ui.tsx:281 + components/ArrayView.tsx:166 |
| `algorithm.insertion_sort` | held value sits outside the array next to its empty slot; gap position relative to… | shift = column slides right 0.35s while gap moves left; insert = purple… | "Bước k / N" indicator + seek slider; green sorted prefix grows one… | gap position printed twice on one screen: hold-note "ô trống ở vị trí N" (ui.tsx:195) and shift narration "ô trống lùi về vị trí N" (algorithms.ts:471); held value in tray also repeated as decision-… | frontend/src/simulations/domains/algorithm/ui.tsx:188-215;… |
| `algorithm.linear_search` | Ranh giới đã-duyệt / chưa-xét bằng màu + vị trí con trỏ; quan hệ phần-tử ↔ giá-trị-… | Đổi màu cột tại chỗ (CSS fill 0.25s) + ▲ nhảy sang cột kế; không có… | Vệt xám 'đã duyệt qua' dài dần + 'Bước k / n' của shell… | Giá trị cần tìm và phép so sánh ('Đang xét 7 (vị trí 3) — cần tìm: 9', '7 = 9 ?') chỉ ở .decision-strip; chi phí (đã so sánh/chưa xét/xấu nhất) không hiện ở đâu trong Quan sát | D:/Documents/projects/algo-… |
| `algorithm.scan` | current element vs held accumulator element — two colours plus pointer-only-on-… | mark/colour change between snapshots; a miss emits no step, so the… | shell footer SimulationControls.tsx:134 "Bước k / n" plus range slider | accumulator value on to_constant variants (tổng/đếm), the comparison constant/threshold, comparison count in final result | frontend/src/simulations/domains/algorithm/scan-module.tsx:41-54 |
| `algorithm.selection_sort` | green sorted prefix boundary only; current-extreme vs candidate are NOT visually… | end-of-pass swap slides two columns 0.35s; "ghi nhớ vị trí mới" step… | "Bước k / N" indicator + seek slider; green sorted prefix grows one… | "nhỏ nhất hiện tại" (vars.vi_tri_cuc_tri) and "Phần chưa sắp: vị trí 2–6" (set_range) exist only as SortActionZone chips; sort order likewise | frontend/src/components/ArrayView.tsx:117-150 (considering branch never reached: mark emitted… |
| `algorithm.sum_if` | included set (green) vs rejected set (gray). No threshold reference line, no… | discrete step; CSS fill 0.25s recolor of the just-tested column | shell step indicator "Bước k / n" + seek slider… | Running total `tong` (decision strip "tổng: 12", narration "Cộng thêm 5 → tong = 17"); condition threshold (only inside "5 > 3 ?" and step-0 narration) | frontend/src/simulations/domains/algorithm/ui.tsx:290 + components/ArrayView.tsx:186 |
| `binary.base_conversion` | column adjacency only (chữ số\|trọng số\|tích\|tổng dồn; phép chia\|thương\|dư\|chữ… | one more table row appended and the narration paragraph swaps; the new… | shell 'Bước k / N' + seek slider (SimulationControls.tsx:134-159) | which step is current; the intro step and the stage-1/stage-2 boundary (kind 'intro'/'stage' render an empty sim-stage); the read-upward rule | frontend/src/simulations/domains/binary/convert-module.tsx:127-192 (BaseConvWorkspace JSX) |
| `binary.character_encoding` | per character: ký tự -> U+xxxx -> thập phân -> nhị phân; division chain where… | progressive reveal — row appears then fills cell-by-cell per phase,… | shell 'Bước k / N' + seek slider (SimulationControls.tsx:134-159) | exact — shell narration restates the newest division row verbatim; 'Số dư đã thu (từ trên xuống)' restates the Số dư column; assign_var events emitted but nothing renders them (no VarsView in this… | frontend/src/simulations/domains/binary/encoding-module.tsx:407-459 (Workspace JSX) + 354-397… |
| `binary.decimal_to_binary` | per-bit vertical stack weight -> bit -> contribution (+64 or 0); no sum relation drawn | NOT_SHOWN as steps — no timeline; click toggles a bit, fill transitions… | NONE — exploratory, controls show only Đặt lại + hint | narrate() restates the binary string already drawn digit-by-digit in the SVG | frontend/src/simulations/domains/binary/ui.tsx:24-64 (SVG JSX); index.ts:70 narrate ->… |
| `database.relational_table_query` | Row display order switches to engine sort order after the sort step; limit-cut rows… | Discrete re-render — badge/opacity flip, row reorder at sort step,… | Shell "Bước k / n" + slider; numbered stage chips flip to done (green… | The filter predicate itself and its per-clause evaluation (column, operator, compared value, actual cell, AND/OR result) exist only in the shell narration line built by narrateStep (table-… | frontend/src/simulations/domains/database/table-module.tsx:579-692 (TableWorkspace JSX);… |
| `generic.rule_scene` | Only spec-declared edges, container/parent nesting, and the move_along_path route.… | Animated — gen-pop keyframe on newly revealed/current objects, gen-… | Shell "Bước k / n" + slider only when timeline.length > 1; exploratory… | NONE in Observe — values are digits inside the shapes. Note: the rule set is absent from Observe entirely (Inspector "QUY TẮC", closed panel), and RevealStep.narration is uncapped LLM text… | frontend/src/simulations/domains/generic/ui.tsx:529-708 (GenericWorkspace JSX); renderObject at… |
| `logic.and_gate` | wires A->gate, B->gate, gate->lamp (input to gate to output flow) | NOT_SHOWN — no timeline; toggle instantly recolours wires and lamp… | NONE — controls show only Đặt lại plus exploratory hint… | narrate 'Hiện tại: 1 AND 0 = 0' restates switch labels and lamp digit | frontend/src/simulations/domains/logic/ui.tsx:34-77 (narration: index.ts:59-62 via… |
| `logic.boolean_dag` | DAG edges source->gate; depth columns left-to-right encode dependency order | cursor+1 flips next topo gate from '?' to its digit, active border… | shell step indicator 'Bước k / n' + seek slider; on-stage count of… | narrate 'Cổng g1 (AND) nhận [1, 0] → ra 0' restates active node op, inbound wire values and its digit | frontend/src/simulations/domains/logic/dag-module.tsx:539-577 (nodes/values: 429-526) |
| `network.graph_traversal` | edges (directed honoured), tree edge parent→current from engine provenance, frontier… | node fill + edge status recolour per step; frontier items tagged mới /… | shell "Bước k / N" + seek; frontier count "N phần tử"; visited chain… | pop + newly-enqueued neighbours — frontier widget tags "vừa lấy ra"/"mới" AND the narration line restates both | D:/Documents/projects/algo-sim/frontend/src/simulations/domains/network/traverse-… |
| `network.packet_routing` | adjacency links; on-route row vs off-route row; route order left→right | packet dot animates cx/cy 0.4s to new node; active edge repaints to… | shell "Bước k / N" + seek slider; traversed-vs-remaining edge split on… | MISSING SEMANTIC: state.destination vs state.source — 2D collapses both to isEnd stroke 3.5, so the goal of routing is named only in narration/Inspector (3D does mark it with rings + "· nguồn"/"·… | D:/Documents/projects/algo-sim/frontend/src/simulations/domains/network/ui.tsx:71-137 (2D JSX);… |
| `network.protocol_encapsulation` | layer stack order top→bottom; PDU segment order LINK\|IP\|TCP\|data\|FCS; sender →… | PDU row re-renders inside the next layer box and segment count… | shell "Bước k / N" + seek; PDU segment count on stage | active layer + which piece is present — layer highlight and segment row AND the narration sentence restate the same fact | D:/Documents/projects/algo-sim/frontend/src/simulations/domains/network/encap-ui.tsx:40-70 (2D… |
| `tree.traversal` | parent→child edges labelled "trái"/"phải"; active root→current path as thick orange… | Discrete recolor per step + frontier enter/leave tags ("mới" / "vừa lấy… | Shell "Bước k / n" + seek slider (SimulationControls.tsx:134); visited… | GAP: buildDfs Frame.stage (0=before-left, 1=between, 2=after-right) — the rule deciding WHEN visit fires — is never put on TreeStep nor rendered; traversal variant appears only in step-0 narration… | frontend/src/simulations/domains/tree/tree-module.tsx:401-472 (TreeWorkspace JSX); frontier at… |

## E. Tổng hợp

- **VISUAL_SELF_SUFFICIENT = 7**
- **VISUAL_WITH_SHORT_CAPTION = 4**
- **TEXT_DEPENDENT = 1**
- **REPRESENTATION_GAP = 10**

Tổng = **22** = số target trong catalog (**22**).

### Theo domain

| domain | n | self-suff | short-caption | text-dep | gap |
|---|---|---|---|---|---|
| `algorithm` | 11 | 4 | 1 | 0 | 6 |
| `binary` | 3 | 0 | 2 | 0 | 1 |
| `database` | 1 | 0 | 0 | 1 | 0 |
| `generic` | 1 | 0 | 0 | 0 | 1 |
| `logic` | 2 | 2 | 0 | 0 | 0 |
| `network` | 3 | 1 | 1 | 0 | 1 |
| `tree` | 1 | 0 | 0 | 0 | 1 |

## F. Cụm root cause — suy từ chính các dòng trên

Mỗi target gap được xếp vào **đúng một** cụm chính. Cụm mô tả **VÌ SAO** ngữ
nghĩa vắng mặt, không phải nó trông thế nào.

### F1. `OBSERVATION_STATE_OWNED_BY_COMMITMENT_ZONE` — 3 target

`linear_search` · `binary_search` · `selection_sort`

Trạng thái quan sát (vị trí hiện tại · giá trị cần tìm · vùng xét · mốc giữa ·
chi phí so sánh · "nhỏ nhất hiện tại" · ranh giới phần chưa sắp) sống **bên
trong** component cam kết (`SearchActionZone` / `SortActionZone`) thay vì trên
sân khấu.

- `linear_search`, `binary_search`: **HỒI QUY**. W4B-2D thêm `&& commitmentVisible`
  để gác *nút cam kết*, nhưng cổng nằm **trên** cả cây con nên nó lấy luôn chip
  trạng thái và khối chi phí. Trước W4B-2D chúng hiện ở Quan sát.
- `selection_sort`: **TIỀM ẨN**, chưa lộ. Bài này chưa gác cổng nên zone vẫn
  hiện — nhưng cùng kiểu ghép cặp, nên nó sẽ mất trạng thái **đúng vào lúc**
  W4B-2E gác nó.

### F2. `MISSING_STATE_PROJECTION` — 5 target

`sum_if` · `algorithm.scan` · `bounded_control_flow` · `network.packet_routing`
· `binary.base_conversion`

Engine sở hữu ngữ nghĩa nhưng **chưa từng có kênh thị giác nào** cho nó:

| target | ngữ nghĩa có trong engine, không có kênh thị giác |
|---|---|
| `sum_if` | biến tích luỹ `tong`; ngưỡng điều kiện |
| `algorithm.scan` | biến tích luỹ (biến thể `to_constant`); hằng so sánh |
| `bounded_control_flow` | giá trị biến ở chương trình không-vòng-lặp; nhánh được chọn |
| `packet_routing` | `state.destination` — 2D gộp source/destination thành cùng nét `isEnd`, nên **đích đến** chỉ được gọi tên bằng chữ (3D thì CÓ đánh dấu) |
| `base_conversion` | bước nào đang chạy; ranh giới giai đoạn 1/2 (bước `intro`/`stage` render sân khấu RỖNG) |

Đây **không** phải hồi quy — là giới hạn có sẵn.

### F3. `RULE_NOT_PROJECTED` — 2 target

`tree.traversal` · `generic.rule_scene`

Luật quyết định diễn biến không được đưa lên state để vẽ.
`tree.traversal`: `buildDfs Frame.stage` (0=trước-trái, 1=giữa, 2=sau-phải) —
**đúng cái quyết định KHI NÀO thăm nút** — không bao giờ được đặt lên `TreeStep`
lẫn render. `generic.rule_scene`: tập luật vắng hẳn khỏi Quan sát (nằm trong
Inspector đóng), và `RevealStep.narration` là **văn bản LLM không giới hạn**.

### F4. `PREDICATE_ONLY_IN_NARRATION` — 1 target *(cũng là `TEXT_DEPENDENT` duy nhất)*

`database.relational_table_query` — vị từ lọc và việc chấm từng mệnh đề (cột ·
toán tử · giá trị so sánh · ô thật · kết quả AND/OR) chỉ tồn tại trong dòng
thuyết minh do `narrateStep` dựng.

### F5. `DUPLICATED_SEMANTIC_CHANNEL` — quan sát ngang, không phải phân loại

Trên `find_max` · `find_min` · `sum_if` · `count_if` · `linear_search`:
`NarrationSlot` và dải hệ quả nói **cùng một sự kiện** bằng hai câu khác nhau ở
cùng một bước; `linear_search` bước cuối in **nguyên văn** `done.result` ở cả
`NarrationSlot` lẫn `.result-banner`. Không đủ để hạ phân loại, nhưng là nợ có
thật và có thể sửa bằng quyền sở hữu chứ không phải bằng cách xoá chuỗi.

## G. Hồi quy vs giới hạn có sẵn

| Loại | Số | Target |
|---|---|---|
| **HỒI QUY** (do wave kiến trúc của chính dự án gây ra) | **2** | `linear_search` · `binary_search` (W4B-2D) |
| **TIỀM ẨN** (cùng nguyên nhân, chưa lộ) | 1 | `selection_sort` |
| **GIỚI HẠN CÓ SẴN** | 8 | 5 của F2 · 2 của F3 · 1 của F4 |

Phân biệt này quan trọng với phạm vi khoá luận: một hồi quy do chính mình tạo ra
đáng sửa ngay; một giới hạn dị chất trải trên nhiều renderer khác nhau thì nên
được **ghi nhận trung thực** thay vì kích hoạt cuộc thiết kế lại toàn catalog.

## H. Hai giả thuyết bị bằng chứng BÁC BỎ

**H1. "Họ nào không dùng `StageLegend`/`Mark` thì yếu thị giác." — SAI.**
`logic.and_gate`, `logic.boolean_dag`, `network.graph_traversal` đều dùng từ
vựng **riêng của họ**, không đụng `Mark` lẫn `StageLegend`, và đều
`VISUAL_SELF_SUFFICIENT`. Ngược lại, `sum_if`/`linear_search`/`binary_search`/
`selection_sort`/`algorithm.scan` **có** dùng `Mark + ArrayView` mà vẫn là gap.
⇒ **Nhất quán ngữ nghĩa ≠ dùng chung component React.** Ngữ pháp riêng theo
domain là hợp lệ; đây là căn cứ để KHÔNG dựng framework biểu diễn phổ quát.

**H2. "Conflation quan sát/cam kết là root cause trội của catalog." — SAI.**
Nó chỉ giải thích **3/10** gap, và chỉ **2** trong đó đang thực sự hỏng. Cụm lớn
nhất là `MISSING_STATE_PROJECTION` (5). Conflation vẫn đáng ưu tiên, nhưng vì
**mức nghiêm trọng + có chủ sở hữu dùng chung thật**, không vì phổ biến nhất.

## I. Điều bảng này KHÔNG nói

- Không nói học sinh hiểu bài tốt hơn hay kém hơn ở target nào — không có dữ
  liệu người học nào được thu thập.
- Không xếp hạng chất lượng renderer giữa các domain: `VISUAL_SELF_SUFFICIENT`
  ở một cơ chế đơn giản không "hơn" `VISUAL_WITH_SHORT_CAPTION` ở một cơ chế khó.
- Không kết luận gì về 2D so với 3D. Ghi nhận được kiểm: hai target có 3D
  (`packet_routing`, `protocol_encapsulation`) đều đọc **cùng một state** với
  bản 2D — đó là bằng chứng cho **T4**, không phải tuyên bố ưu thế sư phạm.
