# M16 — Evaluation Audit (Phase 1, A–H)

Ngày: 2026-07-19 · HEAD: `c93a7a4` (main, tree sạch) · Người audit: Claude (Fable 5)

Mỗi mục đánh dấu **FACT** (có file/symbol evidence), **INFERENCE** (suy luận từ
FACT), **RECOMMENDATION** (đề xuất cho design M16).

## Phase 0 — Baseline (số thật, đo tại HEAD c93a7a4)

| Hạng mục | Số đo | Evidence |
|---|---|---|
| pytest | **529 passed, 2 skipped, 1 deselected** | `.venv/Scripts/python -m pytest` chạy 2026-07-19 |
| vitest | **406 passed / 33 files** | `npx vitest run` |
| build FE | **sạch** (`tsc -b && vite build`) | `npm run build` |
| CATALOG | **14 concrete entries** | `len(CATALOG)` — `catalog.py` |
| FamilyId | **8** | `descriptor.py:36` |
| Frozen DATASET | **30** (10 specialized / 13 generic / 7 unsupported) | `dataset.py`, `test_evaluation.py::test_dataset_du_30_de_3_nhom` |
| Pools | regression 30 · curriculum 18 · capability 12 · cross_domain 3 · thesis 12 | `datasets/__init__.py::POOLS` |
| Sync-locks | xanh (trong pytest 529) | `test_capability_descriptors.py`, `test_manifest_providers.py` |
| Frozen dataset diff | 0 (tree sạch) | `git status --short` |
| audit:layout | **SKIP có chủ đích** — chưa có diff CSS/UI production nào trong M16 | chính sách CLAUDE.md |

Không có baseline đỏ. `CACHE_VERSION = "13"` (`main.py`).

## A. Production lifecycle map

**FACT** — `run_pipeline` (`ai/pipeline.py:455-684`) chạy đúng thứ tự:

1. `stage_analyze` (1 call, ≤1 retry JSON) → `ANALYZE_SCHEMA` (`pipeline.py:49`):
   `result_ownership` **required** (enum provided/rule_derivable/algorithmic);
   `prescribed_procedure` nullable, enum = `analyze_exposed_values()` =
   `"none"` + 5 legacy sorting + 2 `positional_representation.*`
   (`mechanisms.py:90-98`).
2. `build_representation_plan` — tất định, không LLM (`representation.py`).
3. `stage_classify` (1 call, ≤1 retry JSON) — menu = `llm_choices()` = 12
   concrete llm-facing + token `algorithm.comparison_sort` (bubble/insertion ẩn)
   (`catalog.py`); id ngoài menu → unsupported (`pipeline.py:191`).
4. `classify_with_one_route_recovery` (`pipeline.py:414-450`) — nhánh-3
   family-mismatch trên **route tạm**; ≤1 reclassify (extra_note); vẫn lệch →
   fail-closed `ROUTE_MECHANISM_FAMILY_MISMATCH` (không lượt 3). **TRƯỚC** mọi
   route-dependent gate (bất biến #23).
5. Computation gate (M13) — CHỈ đường generic hoặc classify unsupported
   (`pipeline.py:509-524`; carve-out chuyên biệt = bất biến #5).
6. **Nhánh selector** (`comparison_sort`): `check_mechanism_ownership` (tầng 1)
   → `stage_simulate_family` (≤3 attempts; `check_variant_consistency` tầng 2
   mỗi attempt) → `selector.resolve` tất định → **double validation** qua
   `concrete_spec.validate` → envelope CONCRETE (`source=family_resolved`).
7. **Nhánh direct**: `check_mechanism_consistency_for_target`
   (`mechanism_gate.py:77`, 2 mã: mismatch defensive + `GATE_MECHANISM_OWNERSHIP`)
   → pattern reuse (chỉ generic, eval `pattern_store=None` → bỏ qua) →
   `stage_simulate` (≤3 attempts: structural → scene-mode → system-flow →
   semantic-compat) → envelope (`source=composed`).
8. Kết cục: envelope ok (concrete id) · unsupported (+`failure_category`,
   +`error_code` ở các gate M14/M15) · RuntimeError (simulate cạn retry — API 422).

## B. Evaluation lifecycle map

**FACT** — `evaluate_item` (`harness.py:261-274`) gọi **THẲNG**
`pipeline.run_pipeline(text, key, pattern_store=None, observer=AttemptObserver())`
— bất biến #22; `_item_result_from` (`harness.py:198`) dựng `ItemResult` từ
observer + envelope. `run_eval` tuần tự; `BudgetExceeded` dừng cả bộ; lỗi khác
ghi `pipeline_error` per-case. `live.py`: opt-in `ALLOW_LIVE_AI=1`,
`--dataset/--suite/--case/--max-cases/--max-api-calls/--max-retries`;
`SUITES` hiện có 13 tag (`live.py:31`).

**FACT** — Observer events đã phát (`pipeline.py` `_emit` calls):
`analyze_done{result_ownership, prescribed_procedure, canonical_prescribed}` ·
`plan_built{unsupported_capabilities}` · `classify_done{status, simulation_id}`
(lượt 1) · `gate_checked{gate: route_mechanism|computation|mechanism, fired,
reason_code}` · `reclassify_attempted{from_simulation_id, canonical_prescribed}`
· `reclassify_result{status, simulation_id}` · `simulate_attempt{n, ok,
error_code, message}` · `family_resolved{family_id, variant, concrete_id}` ·
`envelope{status, simulation_id, failure_category?, source?}`.

**FACT** — Ba lỗ hổng quan sát cho metric M16:
1. `AttemptObserver` (`observer.py`) **không có accessor** cho
   `reclassify_attempted`/`reclassify_result` (event có, accessor chưa).
2. `gate_checked{gate:"mechanism"}` nhánh **direct-entry chỉ emit khi fired**
   (`pipeline.py:594-596`) — asymmetry đã ghi ở M15 T6 minor (nhánh selector
   emit cả hai chiều, `pipeline.py:543`).
3. **Không có per-case API budget**: `ApiBudget` là global
   (`gemini.set_budget`); `run_eval` không snapshot per case → transient/HTTP
   per-case không tách được ở live.

**INFERENCE** — initial route = `classify_done`; final route = envelope; route
recovery = 2 event reclassify; initial family dẫn xuất tất định từ initial
route qua `CATALOG[...].family_memberships` / `selector_for_token`. **Không cần
sửa routing/gate/retry nào của pipeline** — Wave 2 chỉ cần: accessor mới +
emit đối xứng cho direct gate (observer-only, `observer=None` → no-op) +
budget snapshot per-case ở harness.

## C. Public catalog inventory

**FACT** — 14/14 entry đều mang `AI_REACHABLE_PUBLIC` (kiểm bằng script trên
`CATALOG[*].reachability`); **0 entry** `INTERNAL_FIXTURE`. `llm_choices()` =
13 giá trị (12 concrete + token; bubble/insertion ẩn sau token — M14 §C2).
Đủ 8 family; `generic.rule_scene` 2 membership với `result_authority` khác nhau
(computation + representation). `known_gaps` máy-đọc: `network.packet_routing`
(Dijkstra có trọng số, dựng topo từng bước), `network.protocol_encapsulation`
(bắt tay 3 bước, phân mảnh, retransmission, congestion, DNS).
`INTENTIONAL_GAP_MECHANISMS` = 4 (`mechanisms.py:50`): select_extreme /
partition / other_unspecified / non_binary_base. `config_contract_version`
đủ 14/14 (8× algo-cfg-1, scan-1.0, logic-cfg-1, binary-cfg-1, net-cfg-1,
encap-cfg-1, dsl-1.0).

**INFERENCE** — Evaluation universe của M16 = đúng 14 concrete targets user dự
kiến; mục "internal fixture thống kê riêng" trong spec M16 là **tập rỗng** ở
catalog hiện tại (vẫn giữ rule loại trừ trong metric để phòng tương lai).

**FACT** — Claim boundary M15 (close report §2): chỉ 2/8 family
(`comparison_sort`, `positional_representation`) có analyze-exposed
prescription signal; 6 family còn lại ownership máy-đọc nhưng **không có** live
mismatch-detection — **by design**. → metric `analyze_mechanism_accuracy` chỉ
có denominator ở 2 family này (đúng như spec M16 §metrics-1).

## D. Existing dataset coverage

**FACT** — Frozen 30 (immutable): 1 case mỗi target cho find_max/find_min/
count_if/linear/binary/and_gate/binconv/sum_if, 2 routing; **0** case
bubble/insertion/scan/encap; 13 generic; 7 unsupported (threshold, parabola,
chem, …). Không có admission metadata (miễn trừ).

**FACT** — Pools mới (45 case, có admission): sorting 5 (bubble×2+insertion+2
gap), positional 4 (2 positive + hex/octal gap), binsearch 3 (gồm
`m15-binsearch-unsorted`), scan/encap/routing/boolean/generic như liệt kê ở
`datasets/*.py`. Near-miss/gap hiện có: `m11-loop-gap` (scan), selection/quick
(sorting), hex/octal (positional), `cap-dijkstra-gap` (graph), 
`cur-t12-tcp-advanced` (encap), `c-threshold` (boolean, frozen).

**FACT** — Trường `capability_family` của case hiện hành là **nhãn tự do
legacy** ("sorting_movement", "search_path", "data_representation"…) — KHÔNG
phải giá trị `FamilyId`. Không case nào có expected error_code / expected gate /
archetype / live-eligibility máy-đọc.

**INFERENCE** — Lỗ trống M16 phải lấp (so yêu cầu ≥2 positive/target + ≥1
near-miss & ≥1 boundary/family): paraphrase positive cho ~9 target (find_max,
find_min, sum_if, count_if, linear, and_gate, scan, routing, encap-decap…);
valid-boundary cho cả 8 family (binary 0/255, binsearch target-absent,
unreachable node…); near-miss cho `interval_elimination` (chưa có);
computation-leak control cho structural; ≥2 cross-family recovery case
(success + failure); out-of-range contract-error control cho positional.

**RECOMMENDATION** — Case M16 nằm ở pool **mới** `m16` (không đụng 4 pool cũ,
không đụng frozen), mang trường structured expectation mới (optional trên
`EvalItem`, tiền lệ M8-PRE), `expected_family` dùng đúng giá trị `FamilyId`.

## E. Existing metric definitions & denominators

**FACT** — `EvalReport.metrics()` (`harness.py:118-179`): classification_accuracy
(classify_ok, dung nạp final==expect), final_route_accuracy (den = sup_all),
family/variant_selection (den = routed — chỉ token sorting), gap_gate_recall/FP,
specialized/generic_selection, unsupported_recall (den = group unsupported),
unsupported_precision (den = predicted None), valid_spec_first_attempt (den =
composed = có tới simulate), avg_retry, semantic_pass_rate, error_categories.
`rate()` trả **0.0 khi den=0** (`harness.py:138-139`) — trộn N/A với 0.
`classify_error` string-match chỉ còn là **fallback** khi attempt không mang
`error_code` (`harness.py:253`).

**FACT** — Chưa tồn tại: per-family aggregation, macro average, confusion
matrix, false_refusal_rate, false_positive_simulation_rate,
generic_fallback_leak_rate, reclassification/route_recovery metrics, retry
split (semantic/transient/reclassify), concrete_envelope_integrity,
production_evaluation_parity, initial_route_accuracy (classify lượt 1 riêng),
applicability rules máy-đọc, pre-fix/post-fix run separation, artifact JSON.

**INFERENCE** — 17 metric M16 map như sau: đã có tương đương (một phần): #2
(family_selection — chỉ selector-token), #3 (variant — sorting), #5
(final_route), #6 (valid_spec_first — den "composed" khớp định nghĩa spec), #9,
#10. Hoàn toàn mới: #1, #4, #7 (tách riêng), #8, #11–#17. **Không sửa metric
cũ** (so sánh lịch sử) — M16 metrics là lớp SONG SONG, tiền lệ M7.14T/M14 §F3.

## F. Observer/event completeness (đối chiếu danh sách Wave 2)

| Trường Wave 2 | Trạng thái | Nguồn |
|---|---|---|
| raw/canonical prescribed | ✅ có | `analyze_done` |
| initial route / final route | ✅ có | `classify_done` / `envelope` |
| initial/final family | dẫn xuất tất định | CATALOG memberships + selector |
| selector token / concrete target | ✅ có | `classify_done` + `family_resolved` |
| route recovery attempted/result | ✅ event, ❌ accessor | `reclassify_*` |
| gate fired + error code | ◐ direct-entry chỉ emit khi fired | `gate_checked` |
| simulate attempts + semantic retries | ✅ có | `simulate_attempt` |
| transient retries per-case | ❌ | ApiBudget global — cần snapshot ở harness |
| final envelope status | ✅ có | `envelope` + return value (error_code trong return) |

**RECOMMENDATION** (Wave 2, tối thiểu): (a) accessor `reclassify_attempted()`/
`reclassify_result()`; (b) emit đối xứng `gate_checked{fired:False}` cho direct
mechanism gate (2 dòng `_emit`, observer-only — production `observer=None` →
no-op, giữ nguyên contract output); (c) `run_eval` snapshot ApiBudget
trước/sau mỗi case → per-case delta; (d) quy ước máy-đọc "absence-of-event =
gate not evaluated" ghi trong schema record.

## G. Gap/near-miss coverage per family (hiện trạng)

| Family | Positive | Near-miss/gap | Boundary | Thiếu cho M16 |
|---|---|---|---|---|
| single_pass_scan | 6 target đủ 1+; scan 1 | loop-gap ✅ | ❌ | paraphrase/target, boundary |
| interval_elimination | 3 (binsearch) | ❌ | unsorted ✅ (m15) | near-miss (wording gần linear), target-absent |
| comparison_sort | 3 | selection+quick ✅ | ❌ | insertion paraphrase, boundary |
| boolean_composition | and 1, generic nhiều | threshold ✅ (frozen) | ❌ | boundary chống hợp nhất 2 surface (mới, có admission) |
| positional_representation | 3 | hex/octal ✅ | ❌ | boundary 0/255, out-of-range |
| graph_traversal | 3 | dijkstra ✅ | ❌ | alt topology, unreachable |
| layered_pdu_transform | 3 encap | tcp-advanced ✅ | mixed ✅ | decap explicit, paraphrase |
| structural_progressive_repr | webbuild/tridrag/netbuild | ❌ control riêng | webstatic | computation-leak control, move_along_path positive có nhãn family |

## H. Proposed M16 case matrix + implementation waves

**RECOMMENDATION** — Pool `m16` ~**52 case** (quyết số cuối ở design): 14
target × (explicit + paraphrase) = 28 positive; 8 family × boundary = 8; 8
family × near-miss/gap = 8 (tái dùng có kiểm soát: một số control bắt buộc đã
tồn tại ở pool cũ được **tham chiếu** vào coverage matrix thay vì chép lại —
frozen/pool cũ giữ nguyên); + 2 cross-family recovery (success/failure) + ~6
control đặc thù (binsearch found/absent/unsorted, binary 0/255/out-of-range,
generic computation-leak, boolean anti-merge). Wave 1–6 như spec user; không
có quyết định kiến trúc production nào ngoài phạm vi "bổ sung evaluation
artifacts/metrics/tests" → **đủ điều kiện tiếp tục offline trong session**
(mục Phase 2 của spec).

## Backlog M15 — 13 minor + trạng thái M16

Nguồn: `.superpowers/sdd/progress.md:94-112` (per-task review) + final review.

| # | Backlog (task gốc) | Trạng thái M16 |
|---|---|---|
| 1 | T1 — `canonical_mechanism`/`mechanism_family` passthrough giá trị lạ | OBSERVED_ONLY (downstream gate xử; taxonomy đóng ở schema) |
| 2 | T2 — message variant-mismatch interpolate canonical id (LLM-facing) | OBSERVED_ONLY |
| 3 | T2 — bare assert `sorting.py` bị strip dưới `-O` | OBSERVED_ONLY (CI không chạy -O) |
| 4 | T2 — owned literal hardcode interval/positional | OBSERVED_ONLY (test canonical che) |
| 5 | T5 — thiếu type hints hàm mới | OBSERVED_ONLY |
| 6 | T5 — union multi-membership cùng family chưa entry nào exercise | DEFERRED_WITH_REASON (không entry nào có 2 membership cùng family — dead path by construction) |
| 7 | T6 — `gate_checked` direct-entry chỉ emit khi fired (asymmetry) | **FIXED_BY_EVALUATION_INFRA** (Wave 2b) |
| 8 | T7 — analyze.md lặp bullet cùng field + assert subset redundant | OBSERVED_ONLY (live đã chứng minh hoạt động) |
| 9 | T9 — computation-gate override đường `chosen=None`+algorithmic thiếu test riêng | **COVERED_BY_M16_CASE** (offline case: classify unsupported + result_ownership=algorithmic) |
| 10 | T12 — `test_scan_khong_khai_predict` vacuous hasattr | DEFERRED_WITH_REASON (test hygiene, ngoài phạm vi eval) |
| 11 | T13 — source-scan truth_table chỉ phủ pipeline.py | OBSERVED_ONLY (tripwire chấp nhận) |
| 12 | T15 — prefix literal thay vì FamilyId.value | OBSERVED_ONLY (style) |
| 13 | Final review — analyze.md bullet-1 "không sắp xếp→null" mâu thuẫn chữ bullet-2 positional | **COVERED_BY_M16_CASE** (đo trong baseline: positional positive + hex/octal gap; failure có evidence → correction round giữ pre/post-fix) |

## Kết luận audit

- **FACT**: eval hiện tại đã đứng trên production `run_pipeline` (bất biến #22)
  — M16 KHÔNG cần pipeline mirror, không cần đổi routing/gate/retry/output.
- **FACT**: mọi bổ sung cần thiết đều thuộc lớp evaluation (case schema, pool
  mới, accessor observer, emit đối xứng observer-only, metric module song song,
  artifact generator) — đúng điều kiện "chỉ bổ sung evaluation
  artifacts/metrics/tests → tiếp tục offline trong cùng session".
- **RECOMMENDATION**: 6 wave như spec; số case cuối + công thức metric khóa ở
  design doc; live suite `m16_catalog_live` ≤24 logical case / trần 80 HTTP —
  PENDING APPROVAL tại stop gate.
