# CURRENT_STATE.md — Trạng thái hiện tại

Cập nhật **sau mỗi milestone**. Chỉ ghi việc **đã thật sự xong** (có commit +
test). Không ghi việc đang định làm vào mục "đã xong".

Cập nhật lần cuối: sau **M15 — Public Capability Contract Formalization &
Migration (Task 1–16, nhánh làm việc trên `main`)**. Design rev2
(`docs/superpowers/specs/2026-07-18-m15-*.md`, `cd1b8e5`); plan rev2
(`docs/superpowers/plans/2026-07-18-m15-*.md`, `b54e507`). Formalize toàn bộ
capability đã tồn tại (KHÔNG registry mới, KHÔNG selector mới ngoài sorting đã
có từ M14): **(1)** `mechanisms.py` — taxonomy cơ chế **canonical namespaced,
ĐÓNG, đủ 8 family** + `INTENTIONAL_GAP_MECHANISMS` registry (giá trị analyze-
exposed cố ý không target nào sở hữu, khai tường minh — không rơi tự do) +
alias **MỘT CHIỀU** legacy sorting → canonical (`canonical_mechanism` là
compatibility boundary DUY NHẤT; analyze vẫn giữ giá trị sorting cũ live-
verified ở M14, không đổi để khỏi vỡ hợp đồng LLM đã kiểm chứng). **(2)**
`owned_mechanisms` khai ở mức MEMBERSHIP (`FamilyMembership`, không phải mức
target) — đủ **14/14 entry CATALOG** (K1 lock kích hoạt đầy đủ ở Task 15).
**(3)** `config_contract_version` khai ở mức DESCRIPTOR (8× `algo-cfg-1` +
`scan-1.0` + `logic-cfg-1` + `binary-cfg-1` + `net-cfg-1` + `encap-cfg-1` +
`dsl-1.0`) — KHÔNG vào envelope, KHÔNG chạm Alembic/DB. **(4)** route-
consistency ordering trong `run_pipeline`: `classify_with_one_route_recovery`
chạy **≤ 1 reclassify BOUNDED, TRƯỚC** mọi route-dependent gate khác, với
**HAI mã lỗi tách bạch** — `ROUTE_MECHANISM_FAMILY_MISMATCH` (cross-family, ở
`classify_with_one_route_recovery`) khác `GATE_MECHANISM_OWNERSHIP` (cùng-
family nhưng cơ chế không sở hữu, ở `check_mechanism_consistency_for_target`,
chạy trên route CUỐI). **(5)** direct-route ownership gate — mechanism-
consistency nay sống trên CẢ HAI lifecycle (selector M14 + direct-entry M15).
**(6)** `ANALYZE_SCHEMA.prescribed_procedure` enum dẫn xuất
`analyze_exposed_values()` (+2 giá trị `positional_representation.*`). **(7)**
per-entry policy lock cho `algo-cfg-1` (required/bounds/normalize/annotation)
+ proof `binary_search` normalize-không-refuse dãy chưa sắp (BE+FE,
`docs/CORRECTNESS.md §9`). **(8)** suite eval `m15_wave1` (4 case mới: hex-gap
· octal-gap · binary-positive · binsearch-unsorted, + 2 case `m14_sorting` tái
dùng tag). `CACHE_VERSION` 11→12 (Task 10, một bump duy nhất cho toàn W1)
→ **13** (Task 11 hotfix — vá bề mặt classify `binary_search` mâu thuẫn policy
normalize-not-refuse đã lock, xem nhật ký live §1). **(9)** coverage matrix
(Task 16): `sorting` tốt nghiệp `PILOT` → `SUPPORTED` (claim boundary tự giới
hạn — targeted acceptance, KHÔNG phải bằng chứng thống kê); `binary_system`
note bổ sung control cơ số ≠ 2. Offline cuối: pytest **529 pass, 2 skipped, 1
deselected** · vitest **406 pass (33 files)** · build sạch · FE production
diff toàn M15 **= 0** (chỉ `capability-descriptors.json` sinh lại + 2 file
test). Live Task 11 (user duyệt ≤6 case/≤20 HTTP, nhật ký đầy đủ ở §1): run 1
**16 HTTP, 5/6** (hex/octal fail-closed qua recovery đúng; binary-positive
không chặn oan; sorting-paraphrase/selection đúng; binsearch-unsorted bị từ
chối oan ở classify — root cause CHỨNG MINH: bề mặt classify mâu thuẫn chính
policy đã lock) + hotfix prompt-only (`f52f1a2`, dùng ĐÚNG MỘT quyền prompt-fix)
+ rerun **3 HTTP OK** → **tổng 19/20 · 0 retry · 0 transient**. KHÔNG: selector
mới, đổi executor/renderer, Alembic, M16 (chưa mở). Xem hàng **M15** ở §2.
Trước đó: sau **M14 — Capability Family Formalization & End-to-End
Pilot (Task 1–14, nhánh làm việc trên `main`)**. Offline: pytest **450 pass, 1
deselected** · vitest **403 pass (32 files)** · build sạch. Live pilot
`m14_sorting` (user duyệt ngân sách ≤16 call/≤4 case) **ĐÃ CHẠY — 4/4 OK, 11 HTTP,
0 retry, 0 transient**: sorting formalize thành family selector LLM-facing +
adapter về executor bubble/insertion HIỆN CÓ; final_route/family_selection/
variant_selection = 1.0; selection-sort → từ chối trung thực; token
`comparison_sort` KHÔNG lọt vào envelope. Eval NAY đi chung `run_pipeline` (bất
biến #22), `_simulate_with_metrics` đã retire. Xem hàng **M14** ở §2. Trước đó:
sau **M13-SOUNDNESS Task 1–14 + hotfix role-compat — ĐÃ MERGE FF vào `main`**
(`db5ba3f`→`e8c9dba`). Task 14 live smoke ĐÃ CHẠY (user
duyệt, 37 HTTP tổng + 4 HTTP rerun xác nhận hotfix); live phát hiện MỘT false
positive M13 (`boolean → value_box` bị check role từ chối oan) và đã VÁ bằng
role compatibility một chiều `logical→numeric` — canonical rerun ✅ OK. Offline
cuối: pytest **377** · vitest **393** · build sạch. Xem hàng **M13-SOUNDNESS**
ở §2 + known-issue 7f. Trước đó: sau **M12-AI-SCAN** (tiếp nối
M12-SCAN-PROOF trên main) — M11: LLM compose chuỗi rule boolean lồng qua trung
gian trên đường generic (validator cấm trùng target 2 tầng, probe
`nested_boolean`, vòng lặp biến tự do từ chối trung thực); M12: scan-interpreter
tất định (engine sở hữu) tái tạo đúng ngữ nghĩa 4 engine specialized
single-pass qua spec khai báo bounded — KHÔNG ngôn ngữ lập trình ẩn, LLM/UI của
scan HOÃN có chủ đích.

> ## ✅ M8 SLICE 1+2 HOÀN THÀNH — SCOPE FREEZE §5b VẪN HIỆU LỰC CHO PHẦN CÒN LẠI
>
> - **M8 đã chứng minh tuyên bố kiến trúc**: cùng config → cùng engine tất định →
>   cùng state/timeline/action/prediction → renderer 2D **hoặc** 3D
>   (`network.packet_routing` là PoC duy nhất, đúng kế hoạch).
> - **3D là renderer, không phải domain**: không có simulation_id "_3d" nào,
>   không fork engine (bất biến #16, `ARCHITECTURE_MAP.md §5`).
> - **M8 Slice 3 (mạng phân tầng) HOÃN post-M8**: cần năng lực tất định MỚI
>   (đóng gói/mở gói qua tầng — biến đổi trạng thái PDU), không fake bằng
>   reveal-boxes (xem §6).
> - M7.15 (geometry) vẫn KHÔNG nằm trong kế hoạch; danh sách §5b vẫn áp dụng
>   cho mọi thứ không phải blocker renderer.

## 1. Baseline

| | |
|---|---|
| pytest | **372 pass, 1 deselected** (đo lại tại Task 13, nhánh `m13-semantic-soundness`, `.venv/Scripts/python -m pytest`; 0 API call thật — guard là bằng chứng; +37 so với 335 do M13 Task 1–12b: contract-lock/sync-lock, validator operand coherence, runtime fail-closed, computation_gate 2 kênh, patch fail-closed, fixture regression lock) |
| vitest | **390 pass** (đo lại tại Task 13, nhánh `m13-semantic-soundness`, `npm test`; 0 network call; +31 so với 359 do M13: mirror validator/runtime/displayLabel/regression lock phía frontend) |
| audit bố cục | `npm run audit:layout` — **4/4 route sạch** (đo lại tại Task 13: vẫn 4/4 — M13 chỉ đổi nguồn text nhãn, không đổi CSS/layout; Chrome thật, CDP; đã chứng minh bằng tiêm lỗi giả ở M9-UX7) |
| build | `tsc -b && vite build` sạch (đo lại tại Task 13) — bundle chính ~307KB; chunk Three.js 544KB + `ui3d` 5.4KB + `encap-ui3d` 4.7KB **đều code-split**, chỉ tải khi bấm 3D |
| nghiệm thu M10 | CDP browser thật (SwiftShader WebGL) — **15/15**: 2D đóng gói→truyền→mở gói→giao đúng payload; dự đoán sai → phản hồi tất định; 3D canvas dựng thật + caption; parity 2D↔3D; **0 gọi /api/analyze\|edit\|explain** |
| Docker | `docker compose up -d --build` OK (backend :8000 + Postgres) |
| Live smoke gần nhất (M7.14T) | 8/8 OK · 22 HTTP request · 0 retry · 0 transient · `gap_gate_recall = 1.0` · không false positive |

**Không chạy full live eval theo mặc định.**

### Nhật ký live call (ghi chính xác, không ghi khoảng)

| Khi nào | Suite/case | HTTP request | retry | transient |
|---|---|---|---|---|
| M7.14T | smoke suite (8 đề) | **22** | 0 | 0 |
| M7.14D — run A (code trước fix empty-ops) | 3 case edit: structural+đoạn văn (1) · structural+"thêm điểm P1" (2) · spatial+"thêm D nối A" (1) | **4** | 0 | 0 |
| M7.14D — run B (sau fix, chỉ case 2) | LLM đề xuất `node` trước → policy reject → retry → từ chối | **3** | 0 | 0 |
| M7.14D — run C (sau fix, chỉ case 2, đo lại) | LLM từ chối ngay lần đầu | **1** | 0 | 0 |
| **Tổng M7.14D** | | **8** | 0 | 0 |
| M8-PRE (S3) | verify có mục tiêu: đề "phân tích hệ thống" + guard quan hệ đời thường; 3 lần diag đếm object/attempt; 1 lần probe schema | **55** | 6 | 9 (1 ReadTimeout + 8× HTTP 503 "high demand" ở lần chạy cuối) |
| M8-PRE (plan C) | inspect composition (2 dump) + verify sau nén (V1 + V2) | **15** | 1 | 1 |
| M8-PRE (stability smoke) | đề "phân tích hệ thống" × **5 lần hoàn tất** | **19** | 2 | 2 (429/5xx — retry nuốt trọn, **0 run bị hỏng**) |
| **M8 (Slice 1+2)** | frontend-only: kiến trúc renderer + network 3D; nghiệm thu bằng bài mẫu offline trên browser thật | **0** | 0 | 0 |
| **M9-UX1..7 · M10-3D-PED · DB-HARDEN-2** | frontend/UX + engine + DB infra — offline-first, không đụng hợp đồng AI | **0** | 0 | 0 |
| **M10-AI-ROUTE — run 1** (menu classify mới, prompt CŨ) | suite `m10_route` (5 case: 2 encap + mixed + routing tương phản + unsupported) | **18** | 6 | 6 (429) — **2/5 đúng**: 2 đề encap rơi về generic, TCP nâng cao ép về generic |
| **M10-AI-ROUTE — run 2** (sau vá classify.md) | cùng 5 case | **19** | 5 | 5 (429) — **5/5 đúng**: classification 1.0, unsupported recall/precision 1.0, valid_spec_first_attempt 1.0, 0 retry validation |
| **Tổng M10-AI-ROUTE** | | **37** | 11 | 11 |
| **M11 — baseline** (prompt CŨ) | suite `m11_compose`, 3 case đầu (canonical + access + paraphrase) | **10** | 0 | 0 — canonical ✅ 8/8 chuỗi 2 rule (câu hỏi trung tâm trả lời CÓ ngay baseline) · access ✅ · paraphrase ❌ probe đếm 7 "nguồn" (label trang trí có value → lỗi PROBE, không phải LLM) |
| **M11 — chẩn đoán** | 1 case paraphrase, dump spec | **3** | 0 | 0 — spec lần này HOÀN HẢO (2 rule chuỗi, 3 toggle) → xác nhận lỗi probe + bất ổn định lấy mẫu |
| **M11 — rerun sau vá probe** (prompt CŨ) | trọn suite 5 case | **20** | 0 | 0 — canonical ✅ · NOT ✅ 4/4 · access ❌ ép PHẲNG 1 rule · paraphrase ❌ invalid 3 attempt · **loop-gap ❌ bị ép về generic (misroute có bằng chứng)** |
| **M11 — sau vá contract+analyze+classify** | trọn suite 5 case | **17** | 0 | 0 — access ✅ · paraphrase ✅ 8/8 (k=1 về generic, đúng quyết định) · **loop-gap ✅ gate=fired, unsupported recall/precision 1.0, 0 false positive** · canonical ❌ spec chết tương tác (switch không value — probe bắt đúng) · NOT ❌ misroute and_gate |
| **M11 — rerun có mục tiêu sau vá ranh giới and_gate** | NOT + a-and (đối chứng) | **7** | 1 | 1 (429) — NOT ✅ generic 4/4 · a-and ✅ vẫn specialized (không over-correction) |
| **Tổng M11** | 16 lượt case logic | **57** | 1 | 1 |
| **M12-AI-SCAN — smoke** (prompt mới) | suite `m12_scan` (4 case: flagship first-above + count/linear đối chứng + loop-gap M11) | **11** | 0 | 0 — **4/4 OK**: flagship → `algorithm.scan` spec valid lần đầu + semantic bounded_scan PASS (dừng đúng vị trí 4); count_if/linear_search không bị nuốt; loop-gap vẫn unsupported (gate fired). Lưu ý: `gap_gate_false_positives` ghi flagship (analyze gắn numeric_threshold — metric-only, xem §5) |
| **M12-AI-SCAN — rerun flagship sau vá carve-out analyze** | 1 case | **3** | 0 | 0 — vẫn OK routing + semantic; gate VẪN fired (salience prompt dài — dừng đuổi theo bài học M8-PRE S3, ghi known-issue) |
| **Tổng M12-AI-SCAN** | 5 lượt case logic | **14** | 0 | 0 |
| **M13 Task 14 — tier 1** | `cap-dijkstra-gap` (1 case, trần 15) | **2** | 0 | 0 — ✅ `unsupported`, gate=fired, KHÔNG sinh generic config; classification/unsupported recall/precision đều 1.0; 0 gap-gate false positive |
| **M13 Task 14 — tier 2a** | trọn suite `m11_compose` (5 case, trần 20) | **17** | 0 | 0 — **4/5**: access ✅ · paraphrase ✅ · NOT ✅ (bảng chân trị hợp thành đúng toàn bộ, semantic 1.0) · loop-gap ✅ gate=fired · **canonical ❌ `unknown_primitive` invalid 3 attempt** |
| **M13 Task 14 — rerun chẩn đoán canonical** | 1 case (trần 6) | **5** | 0 | 0 — ❌ CÙNG chữ ký `unknown_primitive` → stop-condition, dừng chẩn đoán live (xem §5, known-issue 7f) |
| **M13 Task 14 — tier 2b** | trọn suite `m12_scan` (4 case, trần 15) | **13** | 0 | 0 — **4/4** ✅: flagship → `algorithm.scan` (valid sau retry, semantic bounded_scan PASS) · count_if/linear_search giữ route chuyên biệt · loop-gap unsupported gate=fired; specialized_selection 1.0, 0 FP |
| **Tổng M13 Task 14** | 11 lượt case logic | **37** | 0 | 0 (trần tuyệt đối 39 — không vượt; MỌI failure là semantic, KHÔNG có lỗi 429/network) |
| **M14 Task 13 — live pilot** (user duyệt ≤16 call/≤4 case) | suite `m14_sorting` (bubble explicit · insertion explicit · bubble paraphrase-CƠ-CHẾ · selection-sort near-miss) | **11** | 0 | 0 — **4/4 OK**: classification 1.0, final_route/family_selection/variant_selection 1.0 (n=3), unsupported recall/precision 1.0, valid_spec_first_attempt 1.0. 3 sorting positive: classify → token `algorithm.comparison_sort` → adapter → envelope CONCRETE (bubble/insertion) đúng; token KHÔNG lọt vào envelope. selection-sort → từ chối ngay ở classify (mechanism gate là backstop, không cần fire live — offline đã khoá). Paraphrase-theo-cơ-chế (không nêu tên "nổi bọt") → đúng bubble → định tuyến theo CƠ CHẾ. Không prompt-fix (4/4 lần đầu) |
| **M15 T11 — run 1** (user duyệt ≤6 case/≤20 HTTP) | suite `m15_wave1` (hex-gap · octal-gap · binary-positive · binsearch-unsorted · sorting-paraphrase · selection-near-miss) | **16** | 0 | 0 — **5/6**: hex/octal → unsupported KHÔNG generic config (classify chọn generic nhưng recovery mismatch fail-closed — mỗi đề +1 reclassify; mechanism_gate không cần fire); binary-positive ✅ không chặn oan; sorting-paraphrase ✅ token→concrete (family/variant 1.0, n=1); selection ✅ gate=fired · **binsearch-unsorted ❌ classify trả unsupported** — root cause CHỨNG MINH: bề mặt classify (description + classify.md 2c) khoá "dãy ĐÃ SẮP", mâu thuẫn policy normalize-not-refuse đã lock (CORRECTNESS §9); LLM từ chối ĐÚNG theo prompt cũ |
| **M15 T11 — rerun sau hotfix prompt-only** (`f52f1a2`: vá description+2c, CACHE 12→13; dùng đúng MỘT quyền prompt-fix) | 1 case `m15-binsearch-unsorted` (qua `--case` mới) | **3** | 0 | 0 — ✅ `algorithm.binary_search`, valid spec lần đầu, final_route 1.0; chuẩn hoá + chú thích đảm bảo TẤT ĐỊNH bởi validator (lock Task 8) vì envelope chỉ phát sau `validate_algorithm_config` |
| **Tổng M15 T11** | 7 lượt case logic | **19** | 0 | 0 (trần duyệt 20 — không vượt; 0 lỗi transient/mạng) |

**TRẠNG THÁI của đề "phân tích hệ thống" — sau STABILITY SMOKE 5 lần chạy hoàn tất:**
- Định tuyến: ✅ **đã sửa** — **0/5** lần `unsupported` im lặng; **5/5** vào `generic.rule_scene`.
- Vai trò hệ thống: ✅ **5/5** có đủ actor + process + data_store (4/5 có cả input/output).
- Chiều luồng dữ liệu: ✅ **39/39 edge (100%) có `directed`** — cổng suy tất định hoạt
  động ổn định (LLM vẫn không tự khai, đúng như đã đo).
- Kết quả: ✅ **5/5 validate end-to-end**, đều là `executable_simulation`
  (`reveal_sequence` 5/5; `move_along_path` 3/5) — **result mode khai báo trung thực**.
- Ngân sách object: **KHÔNG cảnh hợp lệ nào cần > 20** (spec cuối: 13, 14, 15, 17, 17).
  Khẳng định lại kết luận plan C: **không nâng hạn mức, không cần capability-aware budget.**
- **Nén dư thừa: fired 0/5.** Nó là LƯỚI AN TOÀN, không phải thứ đang gánh tính năng.
  Ở run 4 có một bản nháp 27 object bị từ chối vì hạn mức — nén **cố ý KHÔNG cứu** vì
  các label đó **không trùng hệt** nhãn inline nào (không có dư thừa chứng minh được),
  đúng thiết kế bảo thủ; **retry của pipeline** phục hồi (27 → 16 → 15 ✅).
- Cách diễn đạt ĐƯỢC PHÉP: *"Repeated targeted live verification showed consistent
  end-to-end success across a five-run stability sample."*
  **CẤM** nói: ~~"đã chứng minh tin cậy về mặt thống kê"~~ (n = 5, không đủ).

**M8-PRE (S3) — điều live PHÁT HIỆN ra mà offline không thấy được:**
1. LLM dựng đúng `actor→process→data_store` trong `from`/`to` nhưng **KHÔNG BAO GIỜ khai
   `directed`** — kể cả khi contract yêu cầu tường minh, kể cả sau khi bị từ chối kèm
   lý do (3 attempt liên tiếp). Probe riêng chứng minh **schema KHÔNG phải thủ phạm**
   (gọi trực tiếp thì Gemini phát `directed: true` bình thường) → **không phải
   anti-pattern #1**, mà là *salience* trong prompt dài.
   → **Xử lí đúng kiến trúc: SUY tất định ở server**, không đi xin LLM. Chiều đã nằm
   sẵn trong `from`/`to`; validator (cả hai tầng) tự gắn `directed` cho cạnh nối hai
   node vai trò hệ thống. Không đụng hình học, không đụng topology mạng (2 chiều).

Case 2 tốn 1 hoặc 3 request tùy LLM có thử đề xuất `node` trước hay không —
**cả hai đường đều ra đúng phán quyết** `policy.operation_not_allowed`.
M7.14D.1 là **UI-only: 0 live call**.

## 2. Milestone đã hoàn thành (có commit)

| Milestone | Commit | Nội dung |
|---|---|---|
| **M15 — Public Capability Contract Formalization & Migration (Task 1–16)** | `3d1a0a2`→`b5fef42` | **Formalize TOÀN BỘ capability đã tồn tại thành hợp đồng công khai, máy-đọc — 0 family cần MIGRATE_SPEC_SURFACE.** Design rev2 (`cd1b8e5`) sửa 6 điểm review; plan rev2 (`b54e507`) sửa 3 điểm ordering/isolation/STOP-GATE. **(1) Taxonomy** (`mechanisms.py`) — canonical namespaced (`family.mechanism`) ĐÓNG đủ **8 family**, `INTENTIONAL_GAP_MECHANISMS` (giá trị cố ý không target nào sở hữu, khai tường minh — không rơi tự do), alias **MỘT CHIỀU** `LEGACY_ALIASES` (legacy sorting bare id → canonical; `canonical_mechanism()` là compatibility boundary DUY NHẤT, KHÔNG phải nguồn sự thật thứ hai — analyze GIỮ NGUYÊN giá trị sorting live-verified M14, không đổi để khỏi vỡ hợp đồng LLM đã kiểm chứng). **(2) Ownership membership-level**: `owned_mechanisms` trên từng `FamilyMembership` (không phải mức target — generic có 2 membership, `boolean_composition`/`structural_progressive_representation`, mỗi cái owned riêng) — đủ **14/14 entry CATALOG** (khoá K1) qua 4 wave conformance-proof theo family (W2 scan — KHÔNG selector mới, `algorithm.scan` = catch-all trong-family; W3 boolean dual-surface — `single_gate_truth_table` ↔ `composed_rule_dag` tách bạch, KHÔNG hợp nhất 2 bề mặt; W4 network — routing owned `unweighted_hop_bfs` + `known_gaps` máy-đọc ghi Dijkstra, encap owned `encapsulate_decapsulate_4layer`; W5 representation — owned DẪN XUẤT `manifest.process_types()`, hai membership của generic có `ResultAuthority` khác nhau, pin bất biến #21 làm lock). **(3) `config_contract_version` descriptor-level** (8× `algo-cfg-1` + `scan-1.0` + `logic-cfg-1` + `binary-cfg-1` + `net-cfg-1` + `encap-cfg-1` + `dsl-1.0`) — KHÔNG vào envelope, KHÔNG Alembic; per-entry policy lock cho `algo-cfg-1` (required/bounds/normalize/annotation) + proof `binary_search` **normalize-không-refuse** trên dãy chưa sắp (BE+FE, `CORRECTNESS.md §9`). **(4) Route-consistency ordering trong `run_pipeline`**: `classify_with_one_route_recovery` chạy **≤ 1 reclassify BOUNDED, TRƯỚC** mọi route-dependent gate; **HAI mã lỗi tách bạch** — `ROUTE_MECHANISM_FAMILY_MISMATCH` (cross-family, tại recovery) ≠ `GATE_MECHANISM_OWNERSHIP` (cùng-family nhưng cơ chế không sở hữu, tại `check_mechanism_consistency_for_target` — nay sống trên CẢ HAI lifecycle: selector M14 + direct-entry M15 mới); mismatch KHÔNG BAO GIỜ tới `stage_simulate` trên target mâu thuẫn; ngân sách cố định (analyze ≤1/classify ≤2/simulate ≤1, không recursion). **(5) `ANALYZE_SCHEMA.prescribed_procedure`** enum dẫn xuất `analyze_exposed_values()` (+2 giá trị `positional_representation.*`); `null`/`"none"` vẫn permissive (không ép cơ chế, không từ chối oan). **(6) Hai control offline khoá 9**: hex/octal (đổi cơ số ≠ 2) → `capability_gap` qua HAI lớp phòng thủ độc lập (ownership gate trên direct entry + route-mismatch recovery khi bị misroute sang generic); binary_search dãy chưa sắp → normalize + annotate, KHÔNG refuse. **(7) suite eval `m15_wave1`** (4 case mới hex-gap/octal-gap/binary-positive/binsearch-unsorted + 2 case `m14_sorting` tái dùng tag). `CACHE_VERSION` 11→12 (Task 10) → **13** (Task 11 hotfix prompt-only — vá bề mặt classify `binary_search` mâu thuẫn chính policy normalize-not-refuse đã lock, dùng ĐÚNG MỘT quyền prompt-fix). **(8, Task 16) Coverage matrix**: `sorting` `PILOT`→`SUPPORTED` (claim tự giới hạn — targeted acceptance n nhỏ, KHÔNG phải bằng chứng thống kê); `binary_system` note += control cơ số ≠ 2. **Verify offline**: pytest **529 pass, 2 skipped, 1 deselected** (+79 so với 450) · vitest **406 pass, 33 files** (+3/+1) · build sạch · **FE production diff toàn M15 = 0** (chỉ `capability-descriptors.json` sinh lại + 2 file test — `binary-normalized.test.ts` mới, `scan-module.test.ts` +3 dòng). **Verify LIVE Task 11** (STOP GATE — user duyệt ≤6 case/≤20 HTTP, suite `m15_wave1`): run 1 **16 HTTP, 5/6** OK (hex/octal fail-closed qua recovery đúng; binary-positive không chặn oan; sorting-paraphrase/selection đúng; binsearch-unsorted bị từ chối oan ở classify — root cause CHỨNG MINH bằng live: bề mặt classify khoá "dãy ĐÃ SẮP" mâu thuẫn chính policy normalize-not-refuse đã lock ở Task 8) → hotfix prompt-only (`f52f1a2`, CACHE 12→13) → rerun có mục tiêu **3 HTTP, OK** → **tổng 19/20 · 0 retry · 0 transient** (chi tiết đầy đủ §1). **KHÔNG**: selector mới (ngoài sorting đã có từ M14), đổi executor/renderer, capability mới, Alembic, mở M16. Claim hợp lệ: *"Toàn bộ 8 capability family hiện có đã formalize thành hợp đồng ownership + version tường minh, máy-đọc, kiểm chứng cả offline lẫn live trên đúng MỘT wave slice (W1) — không cần di trú bề mặt LLM nào (0/8 MIGRATE_SPEC_SURFACE)."* Design: `docs/superpowers/specs/2026-07-18-m15-*.md` (rev2); plan: `docs/superpowers/plans/2026-07-18-m15-*.md` (rev2). Close report: `.superpowers/sdd/m15-close-report.md` (gitignored). |
| **M14 — Capability Family Formalization & End-to-End Pilot (Task 1–14)** | `cdb56dd`→(HEAD) | **Uniform LLM-facing spec surface, heterogeneous deterministic execution — pilot family SORTING, end-to-end trên production lifecycle thật.** Formalize abstraction capability SẴN CÓ (không registry mới): **(1) descriptor** trên chính `SimSpec` — `family_memberships[]` (đa membership; generic thuộc HAI family với `result_authority` khác nhau: boolean_composition=computation + structural_progressive_representation=representation) + `executor_id`/`reachability`/`curriculum_anchor`/`known_gaps`; taxonomy 8 family đóng (`descriptor.py`); coverage matrix enum đóng {SUPPORTED/PARTIAL/PILOT/CAPABILITY_GAP/OUT_OF_SCOPE} (`coverage.py`, §O guardrail — không claim phủ toàn chương trình, gap khai trung thực). **(2) FAMILY_SELECTORS** (`families/`) = bề mặt LLM của family (span nhiều target, fact KHÁC CATALOG, cross-lock song ánh chống drift); `comparison_sort` là **selector token**, KHÔNG phải SimSpec, KHÔNG BAO GIỜ là envelope id. `llm_choices()` DẪN XUẤT (ẩn 2 sort concrete, +token). Descriptor artifact `capability-descriptors.json` sinh-từ-nguồn + sync-lock BE + cross-lock FE test-only (production FE KHÔNG import — điểm 6). **(3) SortingFamilySpec** đóng (`family_version/variant/array/order/labels?`) + `validate_family_spec` fail-closed. **(4) mechanism-consistency gate** (`mechanism_gate.py`, §E4): tín hiệu analyze `prescribed_procedure` (enum đóng theo THAO TÁC, không tên thuật toán, không kết quả) + `owned_mechanisms` → tầng 1 selection/quick/other_unspecified → `capability_gap`; tầng 2 variant sai cơ chế → `mechanism_variant_mismatch`→retry. `null`/`none` = permissive (đề sắp-xếp-thường, không từ chối oan). **(5) adapter** `selector.resolve` tất định (variant→concrete id, FamilySpec→config AnalysisOk) → validation KÉP qua `validate_algorithm_config` HIỆN CÓ → envelope CONCRETE; executor/renderer/FE **KHÔNG viết lại** (FE production diff=0). `CACHE_VERSION` 10→11. **(6) production/eval convergence (bất biến #22)**: `evaluate_item` đi CHUNG `run_pipeline` + observer THỤ ĐỘNG; computation gate M13 + mechanism gate M14 NAY sống trong eval; `_simulate_with_metrics` (known-issue #1 drift) RETIRE sau transcript-parity proof; side-effect isolation lock 0-row; fault-injection (classify qua nhưng gate chặn → honest refusal). **(7) metric split** family_selection/variant_selection/final_route (đo trên FINAL envelope, không lẫn classification cũ) + suite `m14_sorting`. **Verify offline**: pytest **450** (+73 so với 377) · vitest **403** (+10) · build sạch · FE diff=0. **Verify LIVE** (user duyệt ≤16/≤4): **4/4 OK · 11 HTTP · 0 retry · 0 transient** (nhật ký §1). **KHÔNG**: migrate family thứ hai (M15), eval toàn catalog (M16), universal DSL, module riêng từng đề. Claim hợp lệ: *"MỘT public specialized capability family (sorting) đã formalize thành bounded LLM-facing FamilySpec, validate, chuyển vào executor tất định HIỆN CÓ, kiểm chứng end-to-end trên production lifecycle thật."* Design: `docs/superpowers/specs/2026-07-17-m14-*.md` (rev2+§O); plan: `docs/superpowers/plans/2026-07-18-m14-*.md`. |
| **M13-SOUNDNESS (Task 1–14 + hotfix role-compat — ĐÃ MERGE main)** | `db5ba3f`→`e8c9dba` *(đã merge FF vào `main`)* | **Generic semantic soundness + algorithmic right-or-refuse.** Hai lỗi ngữ nghĩa gốc đã sửa: (1) **numeric silent-zero** — `weighted_sum` ăn input không có nguồn giá trị hợp lệ (vd id của một `edge`) từng bị runtime lặng lẽ hoá 0, cảnh "chạy" đủ bước nhưng kết quả sai câm; (2) **misroute kiểu "pseudo-Dijkstra"** — đường generic từng chấp nhận dựng cảnh MINH HOẠ một thuật toán tối ưu (tìm đường ngắn nhất) mà không engine tất định nào thật sự SỞ HỮU cơ chế tính đó, tạo ảo giác "đã tính đúng". Ba workstream: **(A)** hợp đồng ngữ nghĩa numeric/logical CANONICAL dẫn xuất từ manifest (`dsl_semantic_contract()` → sinh `dsl-contract.json`, sync-lock chống trôi) + validator hai tầng từ chối operand không có nguồn giá trị / role sai (`INVALID_SOURCE`, coercion DENY mặc định) + runtime hai tầng fail-closed (`GenericEvaluationError`/`GenericExecutionError`, 4 mã lỗi, KHÔNG còn seed/fallback 0) + store fail-closed khi `init` ném lỗi; cũng gỡ `object.weight` (field được dạy/validate/patch nhưng KHÔNG runtime nào đọc — silent semantic no-op). **(B)** `computation_gate.py` — SERVER quyết accept/gap trên đường generic bằng **hai kênh tín hiệu có cấu trúc bổ sung nhau** (known-gap roles lọt vào representation plan; `analysis.result_ownership` fail-closed — chỉ `provided`/`rule_derivable` được đi tiếp, `algorithmic` hoặc thiếu/ngoài enum → gap) + mở rộng taxonomy `arbitrary_algorithm` sẵn có (KHÔNG keyword-patch) + vá analyze.md/classify.md dạy ranh giới bằng ví dụ + `CACHE_VERSION` 9→10. **(C)** `displayLabel` — sanitize nhãn hiển thị runtime theo 3 điều kiện (thiếu ∨ label===id ∨ dạng kỹ thuật snake_case/kebab-case) để id kỹ thuật không còn lộ ra làm nhãn học sinh thấy. **Hai lớp regression khoá lại phát hiện**: fixture pseudo-Dijkstra TÁI DỰNG (Task 7 — artifact gốc không khôi phục được từ cache/localStorage, ghi rõ là reconstructed) bị chặn ở cả validator backend lẫn history-reopen frontend; FP-budget offline xác nhận cảnh cấu trúc/nested-boolean hợp lệ vẫn xanh sau khi siết (Task 8); pattern-reuse vẫn phải qua đủ `run_gates`, không có đường tắt bỏ qua gate mới (Task 10); eval case `cap-dijkstra-gap` + `COVERAGE.md §7b` ghi nhận trung thực Dijkstra ngoài phạm vi công khai (Task 12); patch `add_object` fail-closed trên field lạ thay vì strip im lặng, allowlist `PATCH_ADD_FIELDS` vào hợp đồng sinh (Task 12b). **Verify Task 13 (đo lại, offline)**: pytest **372 pass, 1 deselected**; vitest **390 pass**; `npm run build` sạch; `npm run audit:layout` **4/4 route sạch** (M13 chỉ đổi nguồn text nhãn). **Task 14 (live, user duyệt `ALLOW_LIVE_AI=1`, trần tuyệt đối 39 call) ĐÃ CHẠY — 37 HTTP · 0 retry · 0 transient** (nhật ký §1): **Dijkstra → `unsupported` gate=fired, KHÔNG generic config** ✅ · **m12_scan 4/4** ✅ (flagship scan + 2 control chuyên biệt + loop-gap) · **m11_compose 4/5** — canonical ❌ đỏ ×2 cùng chữ ký, dán nhãn `unknown_primitive` bởi harness lúc đó (nhãn SAI — xem sửa lại ở known-issue 7f): rerun chẩn đoán dump được message thật, xác nhận đây **LÀ M13 chặn oan** (check rule-output→target-role từ chối `boolean → value_box`, một chuỗi hợp lệ ngữ nghĩa), categorizer khớp nhầm vì message chứa cụm "object type" trong câu gợi ý. Đã vá bằng role compatibility một chiều `logical→numeric` + categorizer nhóm `role_mismatch` + message dẫn xuất từ contract (nhánh `m13-hotfix-role-compat`, chi tiết ở 7f). Không phát sinh gap-gate false positive nào ở cả 11 lượt case. Chi tiết đầy đủ 13 task + finding: `.superpowers/sdd/progress.md`; spec nguồn: `docs/superpowers/specs/2026-07-16-m13-generic-semantic-soundness-design.md`; plan: `docs/superpowers/plans/2026-07-16-m13-generic-semantic-soundness.md`. |
| **M12-AI-SCAN** | `439d12e`→`d14ded3`+ | **Đóng gap M12 deferred: NL tiếng Việt → `algorithm.scan` + pseudocode dẫn xuất + UI.** (1) `scanPseudocode(spec)` — mã giả 5 dòng kiểu SGK DẪN XUẤT từ spec, `runScan` gắn `Step.line`/narration từ CÙNG layout (một nguồn, chống highlight trôi; narration bước quyết định là CÂU HỎI — M9-S1); vét cạn mọi combo enum hợp lệ. (2) Module **`algorithm.scan`** (adapter mỏng, module thứ 9 domain algorithm): init = `runScan` → Trace; ScanWorkspace/Inspector tái dùng ArrayView/VarsView/PseudocodeView (thêm prop `lines`); prediction + what-if HOÃN có chủ đích. (3) Backend: port `scan_engine.py` (mirror scan.ts — validator + run_scan cho harness chấm HÀNH VI) + semantic kind **`bounded_scan`** + catalog entry với schema/contract **DẪN XUẤT từ hằng scan_engine** (anti-pattern #1) + `validate_scan_config` (R0) + classify quy tắc 2c (scan CHỈ cho biến thể ngoài 8 bài chuyên biệt; ưu tiên chuyên biệt; loop biến tự do vẫn unsupported). `CACHE_VERSION` 8→9. (4) Suite `m12_scan` 4 case (2 mới + 2 case sẵn gắn tag). **Live smoke 4/4 OK ngay lần đầu** (11 HTTP · 0 retry · 0 429): flagship "tìm ngày đầu tiên vượt 35°C" — bài KHÔNG bài chuyên biệt nào biểu diễn được — chạy trọn NL→scan spec→interpreter dừng đúng vị trí. Known-issue metric: gap-gate false positive trên flagship (§5). pytest **335** · vitest **359** · build sạch |
| **M12-SCAN-PROOF** | `85495af`→`47fbb95` *(nhánh `m12-bounded-scan`, đã merge)* | **Declarative Bounded Scan Proof — giảm nhu cầu "một module thực thi cho mỗi bài".** Audit xác nhận [TraceBuilder](../frontend/src/core/trace-builder.ts) ĐÃ là substrate thực thi tái dụng; gap thật = driver thuật toán còn viết mệnh lệnh bằng TS. **NO-GO cho universal imperative kernel** (thành ngôn ngữ lập trình ẩn → LLM sở hữu semantics, validator không chứng minh được đúng, bài mới không oracle). **GO cho MỘT họ toàn phần rất hẹp: single bounded scan.** `core/scan.ts` — `ScanSpec` (enum ĐÓNG: seed/compare/update/marking/stop, không while/guard/mutation do spec định nghĩa) + `runScan` interpreter **sở hữu toàn bộ** vòng lặp/tiến chỉ số/biên dừng (≤ n → non-Turing)/sinh event/gọi TraceBuilder. **Parity NGỮ NGHĨA** (decisions + finalMarks + stepCount, KHÔNG đòi narration/line) với **4 oracle specialized giữ nguyên**: find_max, count_if, sum_if, linear_search (tìm thấy + không thấy) — MỘT interpreter, spec khác nhau, **0 primitive đặt tên theo thuật toán**. `validateScanSpec` (allowlist mọi trường + coherence "quét trên GIÁ TRỊ phần tử" chống cấu hình vô nghĩa). Test tất định + biên. **Giữ nguyên** mọi engine specialized (oracle), sort/binary/routing/encap KHÔNG đụng (hình khác, ngoài họ). **HOÃN có chủ đích** (đúng scope): tích hợp LLM (analyze/classify/simulate sinh ScanSpec) + wiring UI/renderer — chỉ sau khi proof offline xanh (đã xanh). **0 live AI.** vitest 348 trên nhánh · sau merge M11: **350** · build sạch |
| **M11-COMPOSE** | `9d93153`→`48a1f31` | **Generic composition hardening + đo trung thực composition LỒNG.** KHÔNG phải "tạo generic composition lần đầu" (cảnh phẳng đã compose được từ trước): câu hỏi là LLM có tự dựng CHUỖI rule qua object trung gian không — **CÓ, ngay với prompt cũ** (canonical `A ∧ (B ∨ C)` pass 8/8 ở baseline). Hardening tái dụng, 0 đổi từ vựng manifest: (1) validator 2 tầng **cấm hai rule cùng target** (điểm bất động → rule sau thắng → phụ thuộc thứ tự khai báo); (2) expectation kind **`nested_boolean`** cho harness — dò bảng chân trị theo ĐẦU VÀO TOGGLE của học sinh, id-agnostic, vá âm tính giả của probe `boolean_gate` với rule lồng; (3) contract dạy **chuỗi rule qua trung gian** bằng ví dụ TRỪU TƯỢNG (`kq_phu`, shape khác mọi case đánh giá — chống overfit); (4) analyze/classify chặn **vòng lặp biến tự do** (`x+=3` dừng theo ngưỡng → gate fired, unsupported trung thực; ngoại lệ tường minh: "ít nhất MỘT trong hai" = OR thuần, KHÔNG phải ngưỡng) + ranh giới năng lực `logic.and_gate` (phủ định/≥3 điều kiện/ghép → generic; `a-and` đối chứng vẫn specialized). 5 case dev tag `m11_compose` (curriculum pool; là case REGRESSION đã dùng tune prompt — không được trình bày như held-out). `CACHE_VERSION` 7→8. Live tổng **57 HTTP · 1 retry transient · 0 full dataset**. Bất ổn định lấy mẫu ghi nhận trung thực (n nhỏ, không claim thống kê). pytest **317** · vitest **325** · build sạch |
| **M10-AI-ROUTE** | `422297b`→`45c0aa3` | **Đóng gap M10 deferred: định tuyến NL tiếng Việt → `network.protocol_encapsulation`.** Đề tiếng Việt về đóng gói dữ liệu qua tầng TCP/IP nay được pipeline LLM phân tích → classify → chọn module encapsulation → config v1 được validate → engine tất định 9 bước (LLM **không** sở hữu tầng/PDU/timeline). Đăng ký backend: `_ENCAP_SCHEMA` (bề mặt v1 nhỏ: payloadLabel/appProtocol/notes) + `validate_encapsulation_config` (R0 + cấm khóa engine-owned) + `SimSpec` mang phân biệt ngữ nghĩa (biến đổi PDU qua TẦNG ↔ đường đi qua NÚT). `CACHE_VERSION` 6→7. Vá `classify.md`: tách **tiến trình diễn biến** (engine tự dựng) khỏi **dựng cảnh từng bước** (generic) + quy tắc mạng 3d (encap/routing/unsupported). **Live smoke có mục tiêu: 2/5 → 5/5** sau vá (tổng 37 HTTP call, 0 full dataset). **Merge M10-3D-PED vào main** (FF `1c05d4e`→`422297b`). Còn HOÃN: click 3D trực tiếp, TCP/UDP branching/handshake/phân mảnh. pytest **307** · vitest 323 · build sạch |
| **M10-3D-PED** | `810b5ed`→`dcd31ca` *(đã merge vào main)* | **3D SƯ PHẠM đầu tiên: đóng gói/mở gói TCP/IP.** Module THỨ HAI của domain network (`network.protocol_encapsulation`) — engine tất định **9 bước** dựng PDU phân đoạn với **delta tường minh** `{kind, layer, componentIds[]}` (add/remove/transmit/deliver); LINK+FCS **thêm/gỡ NGUYÊN TỬ**. 2D (stack MÁY GỬI/MÁY NHẬN, phân đoạn trải ngang) + **3D CÓ NGHĨA**: X = chiều truyền, **Z = tầng giao thức** (`meaning_of_z`), PDU đi xuống→băng ngang→đi lên. Dùng chung `PredictionCapability` (LINK+FCS là MỘT đáp án gộp; chấm bằng engine). Thêm field hợp đồng **`threeD`** phân loại TRUNG THỰC: encapsulation = `pedagogical`, packet_routing hạ về `architectural_poc`. **Bất biến #18**. Một mẫu công khai (Thư viện) + preview phân đoạn. **Định tuyến AI HOÃN** (frontend + mẫu offline; **0 gọi AI**); **click 3D trực tiếp HOÃN**; không TCP/UDP branching / handshake / phân mảnh. `practice_activity` vẫn PARTIAL. pytest 289 · vitest 323 · build sạch · audit 4/4 · nghiệm thu browser 15/15 |
| M7.13A | `7fa4046` | Generic interaction semantics: `drag` (allowlist `node`), constraints (bounds/axis/snap), ownership rule, **position state-owned** (`GenericState.pos`), scene-mode consistency (exploratory/progressive/hybrid) truyền vào simulate |
| M7.13B | `d1d518c` | Exact cache version-aware (`simulation_cache`), validated **pattern reuse** (`simulation_patterns`), matcher tất định (không embedding), hybrid adaptation (deterministic fill + 1 call adapt), metrics reuse |
| M7.14 | `7835330` | **Correctness audit** (8 gap role, canonical↔learner policy, `docs/CORRECTNESS.md`), **SimulationPatch v1** + NL edit + manual edit generic, viewport safety (fit/reset, layering, label flip, edge label) |
| M7.14T | `72a715d` | Offline-first testing: hard network guard, gỡ key khỏi env test, `ALLOW_LIVE_AI=1` opt-in, suite smoke/full/boundary, API budget, metric **`gap_gate_recall`** song song |
| Phase 0 | `9034d7c` | Context docs: `ARCHITECTURE_MAP` / `CODE_INDEX` / `CURRENT_STATE` |
| M7.14D | `27c0f1f` | **EditPolicy v1**: affordance sửa suy từ spec (spatial/structural/value_only/observation), reason_code `policy.*` vs `structure.*`, enforce 3 tầng; EditBar tách component (fix lag); stable control shell; Esc hủy công cụ |
| M7.14D.1 | `af6dc4f` | UI-only: ẩn nút "Chỉnh sửa" khi policy không có công cụ thật (`hasMeaningfulEditAffordance`) — value_only/observation không còn chế độ sửa RỖNG; backend policy giữ nguyên |
| **M7.FREEZE** | `7452cbf` | **Đóng M7.x.** Gỡ bố cục pixel khỏi `NetworkState` (blocker 3D duy nhất): state chỉ còn topology + route + steps + cursor; `layout2d` chuyển sang renderer. Quy tắc **renderer-neutral state** vào ARCHITECTURE_MAP. Danh sách **DO NOT ADD BEFORE M8** |
| **M8-PRE** | `cb31adc` | **Coverage + Pedagogical audit → hardening trước M8** (`docs/COVERAGE.md`). **S1**: metadata `EvalItem` (optional, backward-compat) + 4 pool đề mới (`curriculum`/`capability`/`cross_domain`/`thesis` 12 case) + **luật kết nạp** thực thi bằng code; `dataset.py` 30 case **ĐÓNG BĂNG**. Vá lỗ hổng bằng chứng **sắp xếp** (engine có từ lâu, benchmark 0 case). **S2**: `edge.directed` (manifest-first) + node_type mở rộng (actor/process/data_store/input/output) + mũi tên ở renderer + analyze/classify/simulate hỗ trợ **sơ đồ hệ thống thông tin** → đề "phân tích hệ thống" **không còn bị từ chối im lặng**. `CACHE_VERSION` 5→6 |
| M8-PRE-LIP | `f4e3793` | **PredictionCapability** (`predict?` cùng khuôn `timeline?`/`edit?`) + **một** `PredictionBar` dùng chung 2 domain (network: chọn nút; algorithm: có/không); engine tất định chấm; kết quả ở `store.prediction` TÁCH khỏi engine state |
| **M9-UX2** | `08a9a7a` | **Onboarding trực quan + simulation-first + phạm vi luận văn.** `OfflineSample.visibility` (metadata tường minh; "public" mặc định · "internal_fixture") — `publicCatalog()` 12 mẫu Tin học THPT cho học sinh; tam giác + 3 bản "(tổng quát)" thành fixture nội bộ (giữ năng lực + parity coverage; lịch sử vẫn reopen bằng envelope — không phụ thuộc danh mục). `SamplePreview` — 8 preview SVG tĩnh theo simulation_id/metadata (fallback generic). Home: rộng 1040, card preview + chữ, recent card khác biệt ("Tiếp tục ▸"), trạng thái máy chủ im khi ổn. Workspace: cột 264/1fr/300, panel trái đóng mặc định — sân khấu là tiêu điểm. GỠ thẻ "Ứng dụng của cơ chế này" + metadata `applications` (chỉ nuôi thẻ đó). Nguyên tắc #7 vào COVERAGE §2. Acceptance browser 22/22; 0 live AI |
| **M9-UX7** | *(nhánh `m9-ux3-home-preview`)* | **Gỡ panel trái + trình soát bố cục.** `InputPanel` **XOÁ HẲN**: sau khi có trang Thư viện, danh mục tồn tại ở BA nơi (Home 6 gợi ý / Thư viện đầy đủ / panel trái đầy đủ) — panel trái là **bản sao thứ ba**, đúng lỗi "hai nơi làm một việc" mà M9-UX4 đã dùng để gỡ composer khỏi chính panel đó. Workspace còn **2 cột** (sân khấu 700 → **1028px**), header bớt 1 nút, store bớt `leftOpen`/`toggleLeft`. Đổi bài đi qua **Thư viện**. **Độ phủ test KHÔNG mất** dù bỏ 2 test của `InputPanel`: "chỉ mẫu công khai" nay do `ux-shell.test.tsx` kiểm trên `LibraryView`; "không lộ chuỗi kĩ thuật" nay do `ui-hygiene.test.ts` **quét mã nguồn** — mạnh hơn hẳn vì soi mọi component, không chỉ component có test đi qua. **`scripts/audit-layout.mjs`** (`npm run audit:layout`) — soát bố cục trên **Chrome thật** qua CDP: icon lệch tâm · chữ bị cắt · phần tử đè nhau · tràn khung cha · khoảng cách ngoài thang 4px, trên cả 4 route. Đây là công cụ DUY NHẤT bắt được lớp lỗi CSS im lặng (vitest không chạy CSS). Có **dấu vân tay trang** (đo nhầm route → exit 2) và **đã chứng minh bằng tiêm lỗi giả** trước khi tin kết quả "sạch" — anti-pattern #14. Kết quả trên code thật: **4/4 route sạch**. **0 live AI** |
| **M9-UX6** | *(nhánh `m9-ux3-home-preview`)* | **Tuân thủ DESIGN.md + guard vệ sinh đặt ĐÚNG CHỖ.** Bản thiết kế thanh dự đoán trước đó **vi phạm chính `DESIGN.md`**: lấy TÍM (sticker palette) tô nút "Có"/"Kiểm tra", tô nền thẻ, viền trái tím → biến màu **trang trí** thành **accent cấu trúc thứ hai**. `DESIGN.md` §Don't cấm cả hai. Làm lại đúng tài liệu: thẻ nổi bằng **surface tint** (`canvas-soft` + hairline + `rounded-md`, khuôn `pricing-plan-card-featured` — *"distinguished by surface tint rather than a coloured border"*); lựa chọn = `button-utility` trắng, đang-chọn dùng `--primary` (đúng vai *active signal*); phán quyết đúng/sai **được phép** dùng sticker vì §Semantic nói *"status is carried by the sticker palette"*. **Nút primary disabled → XÁM TRUNG TÍNH** (trước đây `opacity: .4` toàn cục biến nút xanh thành **xanh-nhạt-như-hỏng**). Ô tìm kiếm gỡ bo tròn viên thuốc (§Don't: form field giữ `rounded-xs`). **GUARD ĐẶT SAI CHỖ (anti-pattern #13)**: guard cấm-emoji của M9-UX5 quét `renderToString(<App/>)` — SSR chỉ đi qua trạng thái đầu (Home) nên **không bao giờ chạm workspace**; emoji 🔮 và chuỗi `find_max` **lọt qua guard xanh lè**. Thay bằng `ui-hygiene.test.ts` **quét MÃ NGUỒN** → lập tức lộ thêm ⚠, ✓, ⤺, 🔍, 💡. Gỡ `find_max` khỏi `AnalysisCard` (lần **thứ ba** chuỗi kĩ thuật lọt lên UI). Anti-pattern #12/#13. **0 live AI** |
| **M9-UX5** | *(nhánh `m9-ux3-home-preview`)* | **Vỏ ứng dụng + AI hết ngang hàng + TOKEN CSS MA.** **Lỗi im lặng lớn nhất từ trước tới nay**: `global.css` gọi `var(--sp-2xl)` nhưng token thật là `--sp-xxl` → trình duyệt **vứt cả dòng khai báo, không báo gì** → `.home-composer` mất `margin: 0 auto` (ô nhập **lệch hẳn trái**), `.home-title` mất margin (**chữ dí sát ô**), `.app-single` mất padding đáy. Trôi im từ **M9-UX1**; chỉ lộ khi **đo `getBoundingClientRect` trong browser thật** qua CDP. Cùng lúc lộ `--border`/`--radius-sm`/`--radius-md` (M8-PRE-LIP) → `PredictionBar` suốt nay **không viền, không bo góc**. Khoá bằng `styles/tokens.test.ts`: mọi `var()` phải có định nghĩa (anti-pattern #11). Thêm `--sp-3xl`/`--sp-4xl`. **Header**: điều hướng thành LINK CHỮ đẩy phải + gạch chân trang đang xem (trước là 2 nút pill dính wordmark); thêm mục **Thư viện**. **`LibraryView`** (`view: "library"`) — nhà riêng của danh mục đầy đủ, gom nhóm + lọc. Nhờ đó **Home KHÔNG BAO GIỜ phình**: bỏ nút "Xem tất cả (12)", "Tiếp tục học" chỉ **1 thẻ** (học dở 30 bài vẫn y nguyên chiều cao — khoá bằng test), bỏ phụ đề + hàng chip `SAMPLE_PROMPTS` (3 đề đó trùng nội dung 3 bài mẫu ngay dưới, chỉ khác là tốn API → Home có ĐÚNG MỘT đường dùng AI: gõ đề). **AI hết ngang hàng với mô phỏng**: gỡ cặp tab `[Quan sát][Hỏi AI]` (một nửa cột phải, lúc nào cũng vậy, là AI — trái với chính R0); cột phải LUÔN là Quan sát, AI là mục thu gọn ở đáy (`aiOpen` thay `inspectorTab`). **`components/icons.tsx`** — bộ icon SVG nét đậm bo tròn; **cấm emoji/ký tự Unicode làm icon** (khoá bằng test quét ký tự); kẹp giấy thay `+` (nút chỉ gửi tệp, không phải menu). Composer: pill → **HỘP** nhiều dòng. **Thanh cuộn** mảnh, tự ẩn (`scrollbar-gutter: stable` nên nội dung không nhảy). Nghiệm thu browser thật qua CDP + đo bố cục; **0 live AI** |
| **M9-UX4** | *(nhánh `m9-ux3-home-preview`)* | **Thẻ phiên học dùng chung + panel một việc + hết rò chuỗi kĩ thuật.** `SessionCard` — MỘT thẻ cho Home ("Tiếp tục học") lẫn Lịch sử; **thanh tiến độ SUY TỪ ENGINE** (`progressOf`: `init(config)` → `timeline.stepCount`), KHÔNG persist `totalSteps` vào localStorage (bump schema v1 sẽ **xoá sạch lịch sử đang có**). Module không khai `timeline` (exploratory, vd `logic.and_gate`) → **không có thanh tiến độ** — UI dẫn xuất từ capability, không bịa "1 bước". **Vá 2 lỗi thật**: `HistoryView` in thẳng `{item.simulationId}` (`algorithm.bubble_sort`) ra cho học sinh — cùng loại rò rỉ đã vá ở `InputPanel` (M9-UX3) nhưng còn sót; header dùng ký tự `◧`/`◨` (U+25E7/25E8) → font Windows không có glyph → **ô vuông rỗng (tofu)**, thay bằng SVG `PanelIcon`. **Panel trái = MỘT việc (đổi bài)**: gỡ composer khỏi workspace (Trang chủ ĐÃ LÀ nơi phân tích đề), thêm bộ lọc + tranh nhỏ mỗi hàng; `ProblemInput` gỡ luôn prop `variant` (vỏ `compact` hết người dùng — không nuôi code chết). `SAMPLE_PROMPTS` thành **chip bấm được** dưới ô nhập ở Home (điền sẵn đề, học sinh vẫn tự bấm gửi). Dọn CSS chết (`recent-*`, `history-row*`, `sample-dot`, `upload-row`). **BẪY ĐÃ GHI LẠI**: `renderToString(<App/>)` KHÔNG thấy state đã mutate (zustand v5 + `useSyncExternalStore` → SSR lấy *initial state*) — mọi test SSR chỉ hợp lệ ở trạng thái đầu; kiểm view có dữ liệu thì render thẳng component với prop. Nghiệm thu browser thật qua CDP (click thật: mở bài → bước 12/40 → Home → Lịch sử); **0 live AI** |
| **M9-UX3** | *(nhánh `m9-ux3-home-preview`)* | **Home gọn + preview ĐÚNG CƠ CHẾ + vá rò rỉ fixture.** `SamplePreview` 7 → **13 kind**, luật mới **một tranh = một cơ chế = một bài**: 8 bài thuật toán có 8 tranh riêng (`algorithm-bars` find_max · `bars-min` · `sum-threshold` Σ · `count-threshold` bộ đếm · `linear-scan` · `search-range` binary · `sort-swap` bubble · `insertion-lift`). Vá **2 tranh DẠY SAI** (không chỉ trùng): `linear_search` mượn trái/giữa/phải của binary (tìm tuần tự không có mid); `insertion_sort` mượn mũi tên đổi chỗ của bubble (chèn là DỜI — chính `decision.ts` hỏi hai câu khác nhau). Vi phạm nguyên tắc sư phạm #6 (COVERAGE §2.6), nay khoá bằng test "không hai bài thuật toán nào dùng chung một tranh". `ProblemInput` **hai vỏ một lõi** (`variant` hero pill / compact) — hết textarea 5 dòng rỗng + nút xanh kín chiều ngang. Home: card **hàng ngang** (cao bằng nhau bất kể tiêu đề), 2 cột, chấm màu `DOMAIN_COLOR` (hằng số có sẵn, Home chưa từng dùng), cột 1040 → **920**, "xem tất cả" **gom nhóm** theo domain. `InputPanel`: `offlineCatalog()` → **`publicCatalog()`** + bỏ `simulation_id` khỏi UI — luật phạm vi M9-UX2 trước đó **mới chỉ áp ở Home**, panel trái vẫn rò tam giác + 3 bản "(tổng quát)" + chuỗi `algorithm.find_max`. Nghiệm thu browser thật (headless Chrome); **0 live AI** |
| **M9-UX1** | `1f95e92` | **Home + phiên học + lịch sử zero-AI + vệ sinh RULES.** Home thật (view mặc định): MỘT hành động chính + gợi ý chọn lọc + "Tiếp tục học"; không inspector/timeline rỗng trước khi có bài. `state/history.ts`: lịch sử BỀN (localStorage schema v1, whitelist, dedup theo id tất định, max 30 evict, corrupt-safe) lưu **envelope đã validate** → **mở lại ZERO-AI** (bất biến #17) + khôi phục lastCursor/visualMode; reset/goHome không phá lịch sử. Header gọn [Trang chủ][Lịch sử]; HistoryView đủ item + xóa. §17: `applications?` trên module (tĩnh, không LLM) cho 4 domain chuyên biệt. RULES.md → con trỏ ngắn (thứ tự đọc + 10 luật cứng); bản v0.3 lưu `docs/legacy/RULES_v0.3.md` kèm cảnh báo LEGACY (khoá bằng `rules-hygiene.test.ts`). Acceptance browser thật 23/23 (reload + reopen 0 /api/analyze); 0 live AI |
| **M9-S1** | `548f1fc` | **Mechanism-aligned interactions (algorithm).** `decision.ts` — điểm quyết định theo cơ chế từng bài: max/min "có cập nhật?", sum/count "cộng/tăng?", linear "tìm thấy chưa?", binary "**nửa nào bị loại**" (3 lựa chọn, hỏi ở bước lấy mid), sorts "đổi chỗ?/dời?"; đáp án + bằng chứng nhân quả (số thật, biến trước → sau) DẪN XUẤT từ sự kiện trace kế tiếp; MỘT nguồn nuôi cả predict lẫn dải nhân quả. `interaction-policy.ts` — hết "một swap cho cả 8 bài": free (sorts) · framed (linear: chi phí) · challenge (find_max/min: bất biến vùng-đã-duyệt; binary: tiền điều kiện dãy-đã-sắp — ẩn mặc định, mở qua nút thí nghiệm có khung) · hidden (sum/count). Engine: narration bước quyết định thành CÂU HỎI (không lộ đáp án sớm), marks `eliminated` cho phần tử đã duyệt. Nguyên tắc sư phạm #6 vào `COVERAGE.md §2`. UX acceptance 18/18 trên browser thật; 0 live AI |
| **M8 Slice 1+2** | `f83b635`, `18e4c2a`, `cce75fc` | **Shared 2D/3D renderer.** S1: `renderers?` trên SimulationModule ("2d" mặc định = Workspace), `simulations/renderer.ts` (khả dụng = tuyên bố ∩ có renderer thật), `store.visualMode` (lát TRÌNH BÀY — đổi mode không đụng active/cursor/prediction, không rebuild, không AI), `VisualModeToggle` theo capability. S2: `network/ui3d.tsx` — Three.js thuần (KHÔNG R3F), `React.lazy` code-split; `layout3d` renderer-owned (route z=0, ngoài route lùi sâu); OrbitControls xoay+zoom khoá pan; reset GÓC NHÌN ≠ reset mô phỏng; WebGL fail → fallback tiếng Việt; nội suy HÌNH ẢNH gói tin, sự thật vẫn là `packetAt`. Nghiệm thu browser thật 16/16 (headless Chrome + SwiftShader, bài mẫu offline). **Bất biến #16** vào ARCHITECTURE_MAP. Slice 3 (mạng phân tầng) HOÃN — cần semantics đóng gói tất định mới |

Milestone trước đó (M1–M7.12) đã có trong lịch sử commit gộp/ban đầu; kiến trúc
của chúng được mô tả trong `ARCHITECTURE_MAP.md`.

**Lưu ý hồ sơ (M14 discovery):** chỉ M9-UX3, M10-3D-PED và M13 có design
doc/plan độc lập trong `docs/superpowers/`; **M11-COMPOSE, M12-SCAN-PROOF,
M12-AI-SCAN KHÔNG có file design/plan riêng** — hồ sơ thiết kế của chúng là
chính các hàng §2 ở trên + commit messages. Không dẫn chiếu "M11/M12 design
doc" như thể file tồn tại.

## 3. Năng lực đang hỗ trợ

**Chuyên biệt (engine tất định riêng, không dùng DSL):**
- `algorithm.*`: find_max, find_min, sum_if, count_if, linear_search,
  binary_search, bubble_sort, insertion_sort. **M9-S1**: mỗi bài có ĐIỂM QUYẾT
  ĐỊNH riêng theo cơ chế ẩn (dự đoán + dải nhân quả cùng nguồn `decision.ts`) và
  **chính sách what-if theo cơ chế** (`interaction-policy.ts`) — what-if branch
  chỉ mở nơi nó dạy được điều gì đó.
- `logic.and_gate` (bảng chân trị), `binary.decimal_to_binary` (bits⇄decimal),
  `network.packet_routing` (**route = BFS tất định**, không phải LLM) — M8:
  module DUY NHẤT có renderer **2D + 3D** (cùng engine state; các module khác
  CỐ Ý 2D-only vì 3D không thêm giá trị sư phạm, `COVERAGE.md §8`).

**Generic (`generic.rule_scene`, DSL v1):**
- Object: `switch`, `lamp`, `value_box`, `node`, `edge`, `moving_entity`, `label`,
  `container`, `group`, `heading`, `paragraph`, `text`.
- Rule: `boolean` (and/or/not/xor), `weighted_sum`. **M11: rule NỐI CHUỖI qua
  object trung gian** (target của rule này làm input rule khác — DAG, cấm chu
  trình, mỗi target đúng MỘT rule) — engine điểm bất động vốn hỗ trợ sẵn, nay
  được validator/probe/contract bảo vệ tường minh; LLM compose được biểu thức
  ghép `A ∧ (B ∨ C)`, `A ∧ ¬B` không cần module chuyên biệt.
- Interaction: `toggle`, `drag` (chỉ `node`; bounds/axis/snap).
- Process: `reveal_sequence`, `move_along_path`.
- Scene mode: exploratory / progressive / hybrid (tất định từ analysis).
- Chỉnh sửa tăng dần: 5 patch op + NL edit; viewport fit/reset.
- **EditPolicy v1 (M7.14D)**: công cụ sửa suy từ spec — `spatial` (thêm điểm/nối/
  xóa) · `structural` (thêm/sửa/xóa nội dung, KHÔNG thêm điểm) · `value_only`
  (chỉ tương tác sẵn có) · `observation` (có `move_along_path` → khóa topology).
  M7.14D.1: cảnh không có công cụ thật (value_only/observation) **không hiện nút
  "Chỉnh sửa"** — không quảng bá affordance rỗng; toggle/kéo vẫn chạy.

**Hạ tầng:** exact cache + pattern reuse; eval harness (30 đề, suite smoke/full/
boundary); ingest text/docx/code/image.

## 4. Capability gap CỐ Ý (không phải bug — `docs/CORRECTNESS.md §5`)

Không primitive nào cover → `capability_gap`, **không** render xấp xỉ:

`geometric_projection` · `geometric_perpendicular` · `geometric_intersection` ·
`geometric_circle` · `geometric_locus` · `numeric_threshold` ·
`continuous_motion` · `arbitrary_algorithm`

Hệ quả đã verify live: bài hình học phức tạp (chân đường cao / giao điểm / đường
tròn ngoại tiếp / quỹ tích), "đèn sáng khi ít nhất 2 trong 3", quỹ đạo hành tinh,
"thuật toán em tự nghĩ" → **unsupported đúng và ổn định**.

## 5. Known issues / giới hạn đã biết

1. **[ĐÃ XỬ LÍ — M14 Task 9–10, bất biến #22]** `_simulate_with_metrics` (harness)
   mirror `stage_simulate` — drift đã đo cụ thể ở M14 discovery: (a) harness
   không gọi `run_pipeline`; (b) không chạy `check_semantic_compatibility` trong
   retry; (c) không gọi `check_computation_ownership`; (d) `classify_error`
   string-match. **Nay `evaluate_item` đi CHUNG `run_pipeline` + observer thụ
   động** (computation gate + mechanism gate sống trong eval); `_simulate_with_metrics`
   + `_evaluate_item_legacy` ĐÃ RETIRE sau transcript-parity proof (`test_eval_parity`
   — non-gate khớp; gate-refusal là khác biệt hợp lệ). `classify_error` còn làm
   FALLBACK khi attempt không mang error_code có cấu trúc. Side-effect isolation:
   eval 0 row mới (`test_eval_side_effects`).
1b. **[M14] mechanism gate (E4) là BACKSTOP, không phải cổng duy nhất.** Live
   pilot cho thấy LLM từ chối selection-sort NGAY ở classify (predicted=None) →
   mechanism gate không cần fire. Gate chỉ nổ khi classify LỠ route một đề cơ-chế-
   ngoài-family về `comparison_sort` (offline test khoá nhánh đó). Residual risk
   (đã ghi §E4): nếu analyze phán SAI `prescribed_procedure` (đề selection nhưng
   nói null) thì tầng 1 không nổ — lỗi Ở TẦNG ANALYZE, đo được bằng eval near-miss;
   không keyword-patch tên thuật toán trong code.
2. **`move_along_path` không bắt path phải đi theo edge có thật** (waypoint tường
   minh vẫn hợp lệ) — giữ có chủ đích; bài routing thật được specialized bảo vệ.
3. **Multi-family edit chưa hỗ trợ** (M7.14D): cảnh LAI (vừa structural vừa
   node/edge) dùng precedence bảo thủ → chỉ sửa được theo family thắng.
4. **StrictMode nhân đôi render ở dev** — chỉ ảnh hưởng cảm nhận khi chạy
   `npm run dev`, không ảnh hưởng bản build.
5. **`CLAUDE.md` bị gitignore** → sự thật bền vững phải nằm ở `docs/*`.
6. **[ĐÃ XỬ LÍ — Alembic + DB-HARDEN-2]** Trước chỉ có `create_all` (thêm bảng
   OK, ALTER bảng cũ thì không). Nay có **Alembic** (`backend/alembic/`, migration
   đầu `72095b7dd318`): entrypoint Docker chạy `alembic upgrade head` trước khi
   phục vụ (đường DUY NHẤT đổi schema trên DB bền); đổi model → `alembic revision
   --autogenerate`. env.py dùng chung `DATABASE_URL`+`Base.metadata` của app
   (chống drift), `render_as_batch` để ALTER được cả trên SQLite.

   **DB-HARDEN-2 (quyền sở hữu schema theo dialect — chất lượng triển khai, KHÔNG
   phải đóng góp học thuật):**
   - `init_db()` gọi `create_all()` **chỉ khi** dialect là SQLite
     (`sqlite_owns_schema(engine)` — đọc `engine.dialect.name`, không string-check
     URL). Trên **Postgres bền `init_db()` là no-op**: Alembic sở hữu DUY NHẤT
     tạo & tiến hoá schema; runtime KHÔNG lặng lẽ vá schema thiếu.
   - **Cổng chống trôi** `tests/test_migration_drift.py` chạy trong suite mặc định
     (`upgrade head` + `alembic check` trên SQLite tạm, không đụng DB dev): đổi
     model mà quên tạo migration → test ĐỎ. Đã chứng minh bằng fault-injection.
   - **Smoke Postgres thật** opt-in: `pytest -m postgres` (marker bị `pytest.ini`
     addopts loại khỏi run mặc định → default vẫn nhanh/offline, không cần Docker).
     Container throwaway KHÔNG volume (không đụng `pgdata`): migrate→head,
     `alembic_version`==head, ghi/đọc/sửa qua model thật, restart+reconnect,
     `alembic check` sạch, cleanup có kiểm chứng.
   - Pool dialect-aware giữ nguyên (SQLite: `check_same_thread`; Postgres:
     `pool_pre_ping/recycle/size/max_overflow`, chỉnh qua env).

   *Volume Postgres CŨ* (tạo bằng `create_all`, chưa có `alembic_version`) khi
   chuyển sang có HAI đường AN TOÀN: **(A)** dữ liệu bỏ được → `docker compose
   down -v` cho volume mới sạch; **(B)** giữ dữ liệu → `alembic stamp head` **chỉ
   khi** đã xác nhận schema khớp head. **Không tự động stamp DB lạ** (giấu drift).
   Bảng `problems` cũ vẫn orphan vô hại.
7. **Pattern chứa bool op lưu `status="candidate"`** → không auto-reuse (chống
   mẫu AND bị dùng cho đề OR). Cần benchmark/người duyệt để nâng `verified`.
7c. **[M12-AI-SCAN] gap-gate false positive trên đề scan-ngưỡng (metric-only).** Analyze gắn `numeric_threshold` cho "tìm ngày đầu tiên vượt 35 độ" dù đề là duyệt DÃY CHO SẴN (n=2/2 lần, kể cả sau khi vá carve-out — salience prompt dài, đúng loại hiện tượng M8-PRE S3). KHÔNG ảnh hưởng routing: gate chỉ chặn đường generic (bất biến #5), classify chọn `algorithm.scan` đúng cả 2 lần và spec/semantic đều pass. Rủi ro còn lại: nếu classify chệch một bài scan về generic thì bị từ chối oan. Hướng xử lý NẾU cắn thật: sửa tất định server-side (bỏ numeric_threshold khỏi required_roles khi analysis có dãy số cụ thể) — không đuổi tiếp bằng prompt.
7d. **[M13] `gap_gate_recall` (harness) chỉ phản ánh KÊNH 1 của `computation_gate.py` (known-gap roles lọt vào `unsupported_capabilities`), CHƯA phản ánh KÊNH 2 (`result_ownership` fail-closed).** **[SỬA — M14 discovery, đối chiếu source]** Câu từng ghi ở đây ("outcome mỗi case eval vẫn đi qua `run_pipeline` thật, cả hai kênh cùng sống ở đó") là **SAI so với source**: `evaluate_item` (`harness.py`) tự tái dựng chuỗi stage (`stage_analyze` → `stage_classify` → `_simulate_with_metrics`) và **không gọi `run_pipeline`, không gọi `check_computation_ownership`** (grep toàn `app/evaluation/`: 0 match) — KÊNH 2 không sống trong đường eval. Đây vì thế không chỉ là giới hạn metric mà là giới hạn **lifecycle của harness**: production nghiêm ngặt hơn eval; hướng lệch là eval có thể chấm FAIL (`unsupported_as_generic`) ở case mà production từ chối ĐÚNG bằng gate. Metric kênh 1 giữ nguyên cách tính để còn so sánh với baseline M7.14T; hợp nhất lifecycle là target bắt buộc của M14 (xem known-issue 1).
7e. **[M13] Fixture nội bộ `GENERIC_REVEAL_SPEC` (label === id, ví dụ `"A"`/`"B"`/`"C"`) nay hiển thị "Điểm 1"/"Điểm 2"/"Điểm 3"** thay vì đúng chữ cái gốc — lệch với narration cũ ("Dựng điểm C"). Đây là **hệ quả trực tiếp, đã duyệt** của luật `displayLabel` sanitize (Task 11: label === id bị coi là kỹ thuật, không phải nhãn thân thiện — đúng ca lộ id Dijkstra mà M13 phải chặn). Fixture này là **internal** (không thuộc `publicCatalog()`), không lộ ra học sinh; không sửa vì sửa đúng sẽ làm yếu chính luật sanitize.
7f. **[M13 HOTFIX] `m11-nested-canonical` đỏ ×2 live — ĐÃ CHẨN ĐOÁN ĐÚNG và VÁ. Kết luận trước ("KHÔNG phải M13 chặn oan") là SAI, đã bị đảo lại bằng bằng chứng.** Sau khi harness được vá lưu message lỗi thật (commit `c3a11b9`), rerun có mục tiêu (ngân sách nhỏ, controller giữ) dump được message live nguyên văn: `Rule boolean sinh giá trị vai trò "logical" nhưng target "vbOR" (value_box) không nhận được vai trò đó — dùng object type có vai trò logical làm target (vd value_box/lamp).` **Đây LÀ M13 chặn oan thật** (check rule-output→target-role, `validator.py` §3.2/Task 3): đề canonical "A ∧ (B ∨ C)" dựng trung gian bằng `value_box` (`{numeric}`) thay vì `lamp` (`{logical, numeric}`) — shape hợp lệ ngữ nghĩa trước M13 (boolean executor sinh đúng 0/1, 0/1 LÀ số) nhưng check role cũ đòi EXACT match nên từ chối. 4 case m11 khác xanh chỉ vì LLM tình cờ chọn `lamp`. **Nguyên nhân chẩn đoán sai ban đầu**: `classify_error` (harness) khớp nhầm — message role-mismatch CHỨA cụm "object type" trong chính câu gợi ý ("dùng object type ... làm target"), nên bị nhánh `unknown_primitive` (dựa trên cụm chung "object type") khớp trước, che mất chữ ký thật. Message gốc còn TỰ MÂU THUẪN: gợi ý "dùng object type có vai trò logical (vd value_box/lamp)" ngay sau khi vừa từ chối `value_box` vì KHÔNG có vai trò đó → LLM retry lại đúng thứ vừa bị cấm → 3 attempt đỏ. **Đã sửa (nhánh `m13-hotfix-role-compat`)**: (1) role compatibility MỘT CHIỀU `logical → numeric` trong contract (`dsl_semantic_contract()["role_compatibility"]`, helper `role_satisfies()`) — chiều `numeric ↛ logical` VẪN DENY (đây chính là coercion `v>=1` mà M13 Task 3 sinh ra để diệt, canary `test_derived_target_sai_role_bi_tu_choi_weighted_sum_nuoi_boolean` còn xanh); KHÔNG runtime conversion, KHÔNG thêm role `logical` cho `value_box`, `value_provider_types("logical")` vẫn `{switch, lamp}`; (2) message lỗi hai tầng nay DẪN XUẤT gợi ý target type từ contract thay vì hardcode, nên không còn tự mâu thuẫn; (3) `classify_error` thêm nhóm `role_mismatch` kiểm TRƯỚC `unknown_primitive`, regression test dùng nguyên văn message live ở trên + test case-(b) nối message-generator thật với categorizer (fault-injection: không có nhánh → rơi `invalid_value`). `.superpowers/sdd/hotfix-role-compat-report.md` có đầy đủ bằng chứng/test. **XÁC NHẬN LIVE sau vá** (ngân sách 4 HTTP · 0 retry · 0 transient): `m11-nested-canonical` nay **✅ OK** — `generic.rule_scene`, bảng chân trị hợp thành đúng toàn bộ (8 tổ hợp, 2 rule nối chuỗi); FP đã hết. Offline sau vá: pytest **377** · vitest **393** · build sạch.
7b. **[M11] `nested_boolean` là probe HARNESS-ONLY** — pipeline production không
   chấm bảng chân trị (chỉ role-compat + system-flow); một spec lồng cú-pháp-đúng
   nhưng hành-vi-sai vẫn có thể ship tới học sinh (giống mọi expectation khác —
   không phải regression mới). Đo live M11 cho thấy hai kiểu spec kém do LẤY MẪU:
   ép phẳng nhiều mức thành 1 rule; cảnh "chết tương tác" (switch không `value` →
   0 toggle). Contract đã dạy chống cả hai nhưng KHÔNG có cổng tất định production;
   nâng cấp (nếu cần) là milestone riêng. **Route/compose ổn định qua nhiều lần
   lấy mẫu CHƯA chứng minh thống kê** (n = 2–4 mỗi case) — chỉ được nói "mỗi case
   đã pass live sau vá ít nhất một lần".
8. **[M8-PRE plan C — ĐÃ XỬ LÍ bằng nén dư thừa; hạn mức GIỮ NGUYÊN 20]**
   Cảnh sơ đồ hệ thống từng vượt `max_objects = 20` → 422.
   **Ngữ nghĩa của con số 20** (đã inspect): **KHÔNG phải bất biến ngữ nghĩa** —
   vào repo từ `0621910` cùng DSL v1, không có lý do ghi trong RULES.md. Thực chất
   là **ngân sách CHỨA đầu ra LLM + ngân sách DỄ ĐỌC của renderer** (canvas 600×340,
   toạ độ miền 0–100). Engine không phụ thuộc con số này. Khoá bởi
   `test_manifest.py` (assert `== 20`) + test dẫn xuất; **hard-code ngoài manifest
   đúng MỘT chỗ**: `frontend/.../generic/validate.ts` (mirror `MAX_OBJECTS`).
   **Bằng chứng quyết định (đo live):** MỌI cảnh hệ thống HỢP LỆ về ngữ nghĩa đều
   **nằm gọn trong 20** (đếm được: 11, 12, 14, 14, **19** object). Chỉ các bản nháp
   BỊ PHỒNG mới vượt — do Gemini vừa đặt `label` inline cho node/edge, VỪA tạo thêm
   **một object `label` rời lặp lại đúng chuỗi đó** (11 label rời cho 5 node + 6 edge).
   → **Không nâng hạn mức. Không cần capability-aware budget.** Thay vào đó:
   `compact_redundant_labels` (validator, cả hai tầng) gỡ **chỉ** label rời TRÙNG HỆT
   nhãn inline của node/edge có thật, **chỉ khi cảnh đã vượt hạn mức**, và **không bao
   giờ** gỡ label mang chữ riêng hay đang bị tham chiếu cấu trúc. Cảnh trong hạn mức
   không bị đụng tới → **0 bề mặt regression**.

## 5b. DO NOT ADD BEFORE M8 (scope freeze tạm thời)

Cho tới khi M8 bắt đầu, **không thêm** — trừ khi một **blocker 3D thật sự** đòi hỏi:

- specialized domain module mới;
- geometry solver (projection/perpendicular/intersection/circle/locus);
- theorem prover / CAS;
- code playground (`code_experiment`);
- mở rộng RAG / OCR;
- edit mode mới;
- primitive DSL mới tùy hứng;
- hệ learner-feedback mới — **đã MỞ HẸP MỘT LẦN cho M8-PRE-LIP, nay ĐÓNG LẠI** (xem §5c);
- undo/redo · pan/zoom · style editor · topology editing;
- rule DSL mới không liên quan blocker M8.

Mục đích: chấm dứt vòng lặp M7.x tự nuôi chính nó.

## 5c. M8-PRE-LIP — Learning Interaction Proof (ĐÃ XONG, ĐÃ RE-FREEZE)

**Đây KHÔNG phải `practice_activity` đầy đủ.** Đây là **bằng chứng tối thiểu** rằng
**MỘT** optional capability + **MỘT** UI dùng chung phục vụ được **NHIỀU** domain:

> Quan sát → Dự đoán/Chọn → Nộp → **engine TẤT ĐỊNH chấm** → phản hồi là **dữ liệu
> kết quả** → **mô phỏng canonical KHÔNG ĐỔI**.

- `PredictionCapability` (`predict?` trong `SimulationModule`) — cùng khuôn
  `timeline?` / `edit?`: **không khai → không có UI** (3 domain còn lại giữ nguyên).
- Một component **duy nhất** `components/PredictionBar.tsx` phục vụ **cả hai**:
  `network` (N lựa chọn — chọn nút) và `algorithm` (2 lựa chọn — có/không).
- Ground truth **có sẵn miễn phí** trong engine: BFS route (network) · trace thật
  (algorithm). **Không engine mới, không LLM, không gọi mạng.**
- `network.packet_routing` **hết watch-only**: trước đây `apply: (state) => state`.
- Kết quả chấm sống ở `store.prediction`, **TÁCH KHỎI** engine state → học sinh sai
  cũng không đụng được dòng chính (khoá bằng test).
- Phát ngôn thận trọng (network): chỉ nói *"không phải chặng kế tiếp trên đường đi
  ngắn nhất mà engine BFS đã tính"*; nếu nút học sinh chọn **cũng** nằm trên một
  đường ngắn nhất khác thì **phải nói rõ**. **Cấm** nói "đi lối đó là không thể".

**FREEZE ĐÃ ĐÓNG LẠI.** Mở rộng tiếp (chấm điểm, mục tiêu/nhiệm vụ, theo dõi tiến
độ, gợi ý, phản hồi hội thoại, dashboard) → **post-M8**, cần duyệt riêng.

**M9-S1 dùng LẠI capability này, không thêm framework thứ hai**: nội dung câu hỏi
của domain algorithm được nâng từ MỘT câu chung ("có biến nào được cập nhật
không?") thành câu hỏi ĐÚNG CƠ CHẾ từng bài (kể cả 3 lựa chọn cho binary_search —
hợp đồng `PredictionCapability` vốn đã hỗ trợ N lựa chọn). Không đổi
`PredictionBar`, không đổi store, không đổi hợp đồng module.

> **`practice_activity` vẫn là PARTIAL / CHƯA IMPLEMENT** (xem `COVERAGE.md` §6).
> M9-S1 **không** thay đổi điều này: vẫn không có chấm điểm / mục tiêu-nhiệm vụ /
> theo dõi tiến độ / gợi ý / dashboard.

## 6. Việc hoãn CÓ CHỦ ĐÍCH

- **M7.11 Slice 2 — CHƯA hoàn thành.**
- **M7.15 — Minimal Constraint-Aware Geometry**: projection/perpendicular/
  intersection/circle thành rule tất định. Chỉ khi đó `invalid_with_feedback` mới
  có producer thật và generic experimental branch mới có nền.
- **`invalid_with_feedback`**: đã có trong taxonomy, **chưa có producer** nào.
- **`code_experiment`**: deferred — cần sandbox, không được bypass engine tất
  định, **không** pivot thành IDE.
- **3D phân tầng (M8 Slice 3)**: ✅ **đã ship ở M10** (`network.protocol_encapsulation`,
  engine 9 bước tất định) và **định tuyến AI đã ship ở M10-AI-ROUTE**. Còn hoãn
  TRONG module: click 3D trực tiếp, TCP/UDP branching / handshake ba bước / phân
  mảnh / retransmission / congestion / DNS — các đề này classify trả **unsupported
  trung thực** (kiểm bằng case `cur-t12-tcp-advanced`), **cấm** ép vào mô hình v1.
- **M9-S2 / M9-S3** (theo M9-PED-AUDIT §8): *binary — thử thách dựng số N* và
  *packet routing — học sinh tự dẫn gói tin, engine so chi phí với BFS*. Chưa làm.
- **Topology editing cho cảnh network-like**: chỉ mở khi EditPolicy cho phép
  tường minh.
- **Embeddings/pgvector/RAG/OCR/GraphRAG**: cố ý không làm.

## 7. Roadmap

1. ~~Phase 0 — 3 file context~~ (`9034d7c`).
2. ~~M7.14D / D.1 — capability-driven EditPolicy + UI/UX~~ (`27c0f1f`, `af6dc4f`).
3. ~~M7.FREEZE — gỡ blocker 3D, đóng M7.x~~ (`7452cbf`).
4. ~~M8-PRE — coverage/pedagogical audit + S1 dataset + S2 directed data-flow~~
   (`cb31adc`). Quyết định mở #8 (`max_objects`) đã chốt ở plan C: giữ 20 + nén.
5. ~~M8-PRE-LIP — PredictionCapability (2 domain, 1 UI)~~ (`f4e3793`).
6. ~~**M8 Slice 1+2 — shared 2D/3D renderer + network 3D PoC**~~ (nhánh
   `m8-shared-renderer`). Đã chứng minh: cùng config/state/timeline/action/
   prediction → renderer 2D hoặc 3D; 3D là renderer, không phải domain.
   - **Tuyên bố được phép**: "AlgoSim dùng lại config/state/timeline tất định trên
     nhiều renderer, và **chỉ** áp dụng 3D cho nội dung mà chiều sâu/phân tầng thực
     sự mang giá trị biểu diễn." **CẤM** tuyên bố "3D luôn giúp học tốt hơn"
     (`COVERAGE.md §8`).
   - **KHÔNG 3D hoá** (giữ nguyên): cổng logic · nhị phân · **sắp xếp** · **mảng** ·
     trang web · **bảng CSDL**.
   - **Slice 3 (mạng phân tầng) HOÃN post-M8**: có cơ sở sư phạm (T12 B4; 12CS
     B22–24) nhưng đòi năng lực tất định MỚI — trạng thái PDU biến đổi khi qua
     tầng (đóng gói/mở gói). Reveal-boxes chỉ là progressive visualization,
     KHÔNG được gọi là executable simulation.
   - Chưa làm (không phải blocker M8): `z?` optional cho `pos`/`SimAction.move`;
     3D cho cảnh generic `node+edge+moving_entity` — mở khi có nhu cầu thật.
7. ~~**M9-PED-AUDIT** — audit chất lượng sư phạm + tham chiếu bên ngoài (PhET
   implicit scaffolding; Mayer coherence)~~. Kết luận: kiến trúc đúng, nhưng
   nhiều cảnh còn *watch-heavy*; **một** affordance kéo-đổi-chỗ dùng cho cả 8
   thuật toán là khiếm khuyết lớn nhất (hệ quả hầu như bằng 0, riêng
   binary_search còn gây hiểu lầm vì phá tiền điều kiện mà không có khung).
8. ~~**M9-S1 — mechanism-aligned interactions (algorithm)**~~ (`548f1fc`). Vá đúng
   khiếm khuyết trên: điểm quyết định theo cơ chế + chính sách what-if 4 mode.
   **Bất biến mới** (`COVERAGE.md §2.6`): *mọi tương tác phải chạm cơ chế ẩn và
   sinh hệ quả tất định; tương tác trang trí không được admit.*
9. ~~**M9-UX1 — Home + lịch sử học cục bộ zero-AI + vệ sinh RULES**~~ (`1f95e92`).
   Nền sản phẩm: vào cửa đơn giản → phiên học → liên tục học không tốn AI;
   RULES.md hết gây nhiễu cho coding agent tương lai.
9b. ~~**M9-UX2 — onboarding trực quan + simulation-first + phạm vi luận văn**~~
   (`08a9a7a`). Preview trực quan cho starter; sân khấu là tiêu điểm; danh mục
   công khai khoanh Tin học THPT (nguyên tắc COVERAGE §2.7); gỡ thẻ Ứng dụng.
9c. ~~**M9-UX3 — Home gọn + preview đúng cơ chế**~~ (nhánh `m9-ux3-home-preview`).
   Composer pill; card hàng ngang; gom nhóm khi mở rộng. Sửa **2 tranh dạy sai cơ
   chế** và đóng lỗ hổng "luật phạm vi chỉ áp ở Home" (`InputPanel` vẫn rò fixture).
   Bất biến mới khoá bằng test: **một tranh = một cơ chế = một bài**.
9d. ~~**M11-COMPOSE — generic composition hardening + đo composition lồng**~~
   (nhánh `m11-generic-composition`, `9d93153`→`48a1f31`). Đảo ưu tiên có ý thức
   (M11 chạm câu hỏi lõi luận văn trước M9-S2/S3). Tuyên bố ĐƯỢC PHÉP: *"AlgoSim
   dùng phân tích LLM để compose bộ năng lực khai báo generic sẵn có thành cảnh
   tương tác khám phá đã validate cho một LỚP GIỚI HẠN bài Tin học THPT, không
   cần module chuyên biệt riêng cho từng bài trong lớp đó."* **CẤM** nói: sinh
   mô phỏng/code tùy ý · hỗ trợ mọi bài · reveal = executable · thay thế module
   chuyên biệt · tin cậy thống kê (n nhỏ). Phát hiện kiến trúc công bố được:
   ranh giới declarative↔executable TRÙNG ranh giới generic↔specialized.
10. **Kế tiếp — M9-S2: binary "dựng số N"** (`COVERAGE.md §6`, M9-PED-AUDIT §8):
   `binary.decimal_to_binary` là cảnh thao-tác-trực-tiếp tốt nhất nhưng học sinh
   **không thể sai** (không có đích) → thêm thử thách tất định dùng LẠI
   `PredictionCapability`, ground truth `bitsOf`/`decimalOf`/`placeValues` có sẵn.
   Sau đó M9-S3 (packet routing: học sinh tự dẫn đường, engine so chi phí với BFS).
11. Sau M9: `table/grid` (mở khoá CSDL) · practice_activity đầy đủ (cần duyệt
    riêng — vẫn **PARTIAL / CHƯA IMPLEMENT**).
12. Không có M7.15.
