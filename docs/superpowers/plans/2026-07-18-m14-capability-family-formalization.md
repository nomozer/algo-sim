# M14 — Capability Family Formalization & End-to-End Pilot — IMPLEMENTATION PLAN

**Design nguồn:** `docs/superpowers/specs/2026-07-17-m14-capability-family-formalization-design.md`
(rev2 `efa8558` + guardrail §O `cdb56dd`). Baseline: `main` sau `cdb56dd`.

**Nguyên tắc thực thi:** TDD (test/acceptance trước) · commit theo checkpoint ·
diff FE = 0 (ngoài test) · KHÔNG family thứ hai · dừng ở stop-condition. Mỗi task
độc lập rollback được (revert commit).

**Ký hiệu:** BE = backend (python), FE = frontend (ts). "lock" = test khóa.

---

## Task 1 — Curriculum guardrail artifact + descriptor model (khung)

- **Files/symbols:**
  - `backend/app/simulation/descriptor.py` (MỚI): dataclass `FamilyMembership`
    {family_id, variant_id?, result_authority, family_spec_version?,
    mechanism_id?}; `ReachabilityLevel`/`ResultAuthority`/`FamilyId` enum đóng;
    hàm thuần `descriptor_of(sim_id)` đọc từ metadata gắn trên SimSpec.
  - `backend/app/simulation/catalog.py`: `SimSpec.__init__` thêm kw mặc định
    `family_memberships=()`, `executor_id=None`, `reachability=()`,
    `curriculum_anchor=""`, `known_gaps=()` (mặc định an toàn — entry chưa khai
    không vỡ; lock ở Task 2 buộc khai đủ).
  - `backend/app/simulation/coverage.py` (MỚI): `KNOWLEDGE_UNITS` (curate từ
    COVERAGE.md §3 Tier1/2/3 + §7/§7b), `CoverageStatus` enum đóng
    {SUPPORTED, PARTIAL, PILOT, CAPABILITY_GAP, OUT_OF_SCOPE}, `COVERAGE_MATRIX`
    ánh xạ unit→status, `coverage_rows()` sinh bảng.
- **Test-first/acceptance:** `tests/test_coverage_matrix.py` — (a) mọi status ∈
  enum đóng; (b) mọi KNOWLEDGE_UNIT có đúng một status; (c) không unit trùng;
  (d) Dijkstra-trọng-số = CAPABILITY_GAP (khớp COVERAGE §7b); (e) sorting =
  PILOT. `tests/test_descriptor.py` — enum types load, dataclass immutable.
- **Rollback boundary:** xóa 3 file mới + revert kw SimSpec (mặc định rỗng nên
  không ai phụ thuộc).
- **Invariant bảo vệ:** §O (coverage guardrail), decision 2 (không capability giả).
- **Commit:** `M14 Task 1: descriptor dataclasses + coverage matrix enum đóng + guardrail test`.

## Task 2 — family_memberships + FAMILY_SELECTORS + derived choices + cross-lock

- **Files/symbols:**
  - `catalog.py`: KHAI `family_memberships`/`executor_id`/`reachability`/
    `curriculum_anchor`/`known_gaps` cho **cả 14 entry** (8 algorithm qua bảng
    per-id `_ALGO_META`; logic/binary/network×2/scan/generic khai trực tiếp).
    generic khai HAI membership (boolean_composition computation +
    structural_progressive_representation representation).
  - `backend/app/simulation/families/__init__.py` (MỚI): `FAMILY_SELECTORS`
    dict; dataclass `FamilySelector` {family_id, selector_token,
    family_spec_version, config_schema, contract, validate_family_spec,
    owned_mechanisms, variants: tuple[VariantSpec], resolve}; `VariantSpec`
    {variant_id, concrete_simulation_id, mechanism_id}. (Task 2 chỉ dựng khung
    rỗng cho sorting; schema/validator/resolve điền ở Task 5/7.)
  - `catalog.py`: `llm_choices()` — hàm dẫn xuất (C2): selector tokens ∪
    {sim_id runtime target không có membership thuộc family có selector}.
- **Test-first:** `tests/test_family_registry.py` — (a) 14 entry có đủ metadata
  (không rỗng ngoài known_gaps); (b) mọi family_id ∈ taxonomy đóng; (c)
  cross-lock: mọi VariantSpec.concrete_simulation_id ∈ CATALOG, có membership
  khớp {family_id, variant_id, family_spec_version}; ngược lại target mang
  membership family-có-selector xuất hiện đúng một VariantSpec (song ánh); (d)
  duplicate family+variant → reject (test dựng selector lỗi → lock ném); (e)
  `llm_choices()` chứa token comparison_sort, KHÔNG chứa bubble_sort/insertion_sort,
  CÓ generic/logic/scan; (f) selector_token không trùng simulation_id nào; (g)
  song ánh CATALOG↔registry vẫn 14 (đọc cross-ref, không đụng FE).
- **Rollback boundary:** metadata là data thuần; gỡ FAMILY_SELECTORS entry →
  llm_choices trả về tập cũ (14 id). Chưa đụng classify (Task 8) nên chưa ảnh
  hưởng pipeline.
- **Invariant:** C0–C4 (multi-family, selector≠SimSpec, derived choices), #22 (chưa).
- **Commit:** `M14 Task 2: family_memberships 14 entry + FAMILY_SELECTORS khung sorting + llm_choices dẫn xuất + cross-lock`.

## Task 3 — Generated descriptor artifact + test-only FE cross-lock

- **Files/symbols:**
  - `backend/scripts/generate_capability_descriptors.py` (MỚI, khuôn
    `generate_dsl_contract.py`): sinh `frontend/src/simulations/capability-descriptors.json`
    từ CATALOG + FAMILY_SELECTORS.
  - `tests/test_capability_descriptors.py` (BE): sync-lock — JSON == sinh lại
    từ nguồn (chống drift).
  - `frontend/src/simulations/capability-descriptors.test.ts` (FE, TEST-ONLY):
    đối chiếu `executor_id`↔registry thật; `reachability`↔`publicCatalog()`/
    `offlineCatalog()`; selector variants↔module id thật.
  - `frontend/src/simulations/ui-hygiene.test.ts` (mở rộng, hoặc test mới):
    **cấm** mọi module runtime FE import `capability-descriptors.json` (điểm 6).
- **Acceptance:** JSON commit vào repo; hai test lock xanh; grep xác nhận 0
  import production.
- **Rollback:** xóa JSON + script + 2 test.
- **Invariant:** C4 (JSON test-only, không FE prod dependency — điểm 6).
- **Commit:** `M14 Task 3: capability-descriptors.json sinh-từ-nguồn + sync-lock BE + cross-lock FE test-only + cấm import production`.

## Task 4 — prescribed_procedure closed taxonomy + analyze contract

- **Files/symbols:**
  - `backend/app/ai/pipeline.py`: `ANALYZE_SCHEMA` thêm `prescribed_procedure`
    enum đóng {none, adjacent_compare_swap, shift_into_sorted_prefix,
    select_extreme_repeated, partition_recursive, other_unspecified},
    **nullable** (KHÔNG required — không phá analyze domain khác; N7).
  - `backend/app/ai/skills/analyze.md`: dạy phán đoán cơ chế bằng ví dụ TRỪU
    TƯỢNG (không keyword tên thuật toán; mô tả THAO TÁC). Ghi rõ: chỉ mô tả cơ
    chế ĐỀ YÊU CẦU, không mô tả kết quả (O7/R0).
  - hằng enum đặt cạnh mechanism taxonomy (families module) để một-nguồn.
- **Test-first:** `tests/test_analyze_prescribed_procedure.py` — schema có field
  nullable đúng enum; thiếu field → analyze vẫn parse (fail-closed xử ở gate,
  Task 6); giá trị ngoài enum → structured-output Gemini không phát (mock kiểm
  schema). KHÔNG live ở task này.
- **Rollback:** gỡ field khỏi schema (nullable nên backward-compat) + revert md.
- **Invariant:** R0/O7 (mô tả cơ chế không kết quả), #4 manifest-derived enum.
- **Commit:** `M14 Task 4: prescribed_procedure enum đóng (nullable) + analyze.md dạy cơ chế theo thao tác, không keyword`.

## Task 5 — SortingFamilySpec schema + validator

- **Files/symbols:**
  - `backend/app/simulation/families/sorting.py` (MỚI): `SORT_FAMILY_VERSION =
    "sort-fam-1"`; `SORTING_FAMILY_SCHEMA` (structured-output, đóng:
    family_version/variant/array/order/labels?/notes?); `validate_family_spec`
    fail-closed (bound 2–15, enum variant/order, labels khớp độ dài, số hữu hạn,
    reject key lạ — tiền lệ M13 Task 12b), trả (config|None, error_code|None).
  - Điền `config_schema`/`contract`/`validate_family_spec` vào
    `FAMILY_SELECTORS["comparison_sort"]`.
  - `backend/app/simulation/families/sorting.py`: `SORT_MECHANISMS` +
    `owned_mechanisms = (adjacent_compare_swap, shift_into_sorted_prefix)`;
    `variants` = ((bubble→algorithm.bubble_sort, adjacent_compare_swap),
    (insertion→algorithm.insertion_sort, shift_into_sorted_prefix)).
- **Test-first:** `tests/test_sorting_family_spec.py` — bubble/insertion positive;
  descending; labels khớp/lệch; array 1/16/NaN → reject có mã `family_spec_invalid`;
  variant "selection" → reject (ngoài enum); key lạ → reject không strip;
  family_version sai → reject.
- **Rollback:** xóa sorting.py + revert selector fill.
- **Invariant:** D (bounded, không field mở, không result/trace), #1 (R0).
- **Commit:** `M14 Task 5: SortingFamilySpec schema đóng + validate_family_spec fail-closed + owned_mechanisms/variants`.

## Task 6 — Mechanism-consistency gate + structured error codes

- **Files/symbols:**
  - `backend/app/simulation/mechanism_gate.py` (MỚI): `check_mechanism_ownership(
    analysis, selector) → reason|None` (tầng 1: prescribed_procedure ∉
    owned_mechanisms ∧ ≠ none → capability_gap, `gate_mechanism_ownership`;
    fail-closed thiếu/ngoài enum);
    `check_variant_consistency(analysis, selector, variant) → error|None` (tầng
    2: prescribed ∈ owned nhưng ≠ mechanism_id của variant →
    `mechanism_variant_mismatch`).
  - `backend/app/simulation/error_codes.py` (MỚI): enum mã lỗi cổng (H) —
    nguồn phân loại CHÍNH; helper gắn mã.
- **Test-first:** `tests/test_mechanism_gate.py` — selection→gap; quick→gap;
  none→pass; thiếu field→gap (fail-closed); prescribed=shift + variant=bubble→
  mismatch; prescribed=adjacent + variant=bubble→pass. KHÔNG keyword: test dùng
  prescribed_procedure enum, không text đề.
- **Rollback:** xóa 2 file (chưa nối pipeline tới Task 8).
- **Invariant:** E4 (điểm 3), #8/#9 (right-or-refuse), #13 (structured error).
- **Commit:** `M14 Task 6: mechanism-consistency gate 2 tầng + error_codes có cấu trúc (không keyword-patch)`.

## Task 7 — selector.resolve adapter → concrete runtime targets

- **Files/symbols:**
  - `families/sorting.py`: `resolve(family_config, analysis) →
    (concrete_simulation_id, concrete_config)` tất định: variant→id theo bảng
    variants; FamilySpec→config AnalysisOk-shape {problem, data{array,labels,
    order}, notes}. KHÔNG đọc text, KHÔNG LLM, KHÔNG đổi array/order.
  - Gắn `resolve` vào selector.
- **Test-first:** `tests/test_sorting_adapter.py` — bubble→algorithm.bubble_sort,
  insertion→algorithm.insertion_sort; config resolve qua được
  `validate_algorithm_config(variant_id, ...)` hiện có (validation kép); order
  bảo toàn; labels bảo toàn; adapter output KHÔNG chứa family_version/variant.
- **Rollback:** revert resolve (selector chưa nối pipeline tới Task 8).
- **Invariant:** E1/E2 (adapter chung, output qua validator concrete), #2
  (không switch theo id).
- **Commit:** `M14 Task 7: selector.resolve tất định → concrete + validation kép qua validator hiện có`.

## Task 8 — Classify family surface + wire selector vào run_pipeline

- **Files/symbols:**
  - `pipeline.py`: `_classify_schema()` enum = `llm_choices()` (thay
    `list(CATALOG.keys())`); `catalog_text()` (catalog.py) duyệt llm_choices —
    selector token kèm `selector.contract`/description.
  - `pipeline.py` `run_pipeline`: sau classify, nếu id ∈ FAMILY_SELECTORS →
    nhánh family: mechanism gate tầng 1 (Task 6) → simulate với
    selector.config_schema/contract → validate_family_spec → variant-consistency
    tầng 2 (retry) → resolve → validate_algorithm_config concrete → envelope
    concrete. Nếu id là runtime target trực tiếp → đường cũ NGUYÊN VẸN.
  - `CACHE_VERSION` "10"→"11" (main.py).
- **Test-first:** `tests/test_pipeline_sorting.py` (mock call_gemini) — bubble
  positive→envelope algorithm.bubble_sort; insertion→insertion; selection near-miss
  →capability_gap (KHÔNG generic); variant-mismatch→retry; token KHÔNG BAO GIỜ là
  envelope.simulation_id. Regression: generic/logic/scan classify KHÔNG đổi.
- **Rollback:** revert classify enum về CATALOG.keys() + gỡ nhánh family +
  CACHE_VERSION về 10.
- **Invariant:** E1, C2 (llm_choices), #6 (reuse chỉ sau classify — giữ), #5
  (specialized không vạ lây).
- **Commit:** `M14 Task 8: classify family surface (comparison_sort) + nhánh family trong run_pipeline + CACHE_VERSION 11`.

## Task 9 — Production/evaluation shared orchestration + passive observer

- **Files/symbols:**
  - `pipeline.py` `run_pipeline(..., observer=None)`: thread observer thụ động;
    phát event (F2): analyze_done, gate_checked{channel,reason_code},
    classify_done, simulate_attempt{n,rejected_by,error_code,message},
    family_resolved, envelope. Mặc định None → hành vi production KHÔNG đổi.
  - `backend/app/evaluation/observer.py` (MỚI): `AttemptObserver` collector thụ
    động (append-only; per-case).
  - `harness.py` `evaluate_item`: gọi `run_pipeline(text, api_key,
    pattern_store=None, observer=obs)`; dựng ItemResult TỪ observer + envelope
    (predicted/spec_valid/retry/failure/semantic).
- **Test-first:** `tests/test_observer_passive.py` — chạy mock có/không observer
  → envelope + mọi quyết định GIỐNG HỆT (lock passive). `tests/test_eval_uses_pipeline.py`
  — evaluate_item gọi run_pipeline (spy), KHÔNG gọi _simulate_with_metrics.
- **Rollback:** observer optional; revert evaluate_item về bản cũ (giữ
  _simulate_with_metrics tới Task 10).
- **Invariant:** #22 (eval = production orchestration), F2 (observer passive).
- **Commit:** `M14 Task 9: run_pipeline observer thụ động + evaluate_item đi qua production orchestration`.

## Task 10 — Side-effect isolation + transcript parity + retire _simulate_with_metrics

- **Files/symbols:**
  - `tests/test_eval_side_effects.py`: chạy suite mock → 0 row mới ở
    simulation_cache/simulation_patterns/reuse_metrics (F5).
  - `tests/test_eval_parity.py`: transcript MOCK cố định → metric qua đường mới
    == metric `_simulate_with_metrics` cũ, TRỪ danh sách khác-biệt-hợp-lệ
    (case gate-refusal: cũ chấm sai, mới chấm đúng) liệt kê tường minh.
  - `tests/test_eval_fault_injection.py`: mock classify cho qua nhưng gate chặn
    → report = honest refusal (khóa #22).
  - Sau parity xanh: **XÓA** `_simulate_with_metrics` + `classify_error` chuyển
    sang đọc error_code trước (string-match fallback).
- **Acceptance:** 3 test trên xanh; grep xác nhận `_simulate_with_metrics` đã
  xóa; suite eval offline xanh.
- **Rollback:** nếu parity đỏ ngoài danh sách → KHÔNG xóa, dừng báo user
  (stop-condition 6).
- **Invariant:** #22, F4/F5, #13.
- **Commit:** `M14 Task 10: eval side-effect isolation lock 0-row + transcript parity proof + retire _simulate_with_metrics`.

## Task 11 — Metric split + evaluation admission

- **Files/symbols:**
  - `harness.py` `EvalReport.metrics()`: thêm `family_selection_accuracy`,
    `variant_selection_accuracy`, `final_route_accuracy` (đọc envelope),
    `mechanism_gate_fired`; giữ metric cũ CHỈ khi đo cùng đối tượng (item
    non-family: final_route == classification cũ). Report ghi rõ item
    family-routed.
  - `backend/app/evaluation/datasets/capability.py` (hoặc curriculum): thêm case
    sorting theo `check_admission` (learning_objective, pedagogical_rationale
    nêu cơ chế, capability_family, complexity, result_mode, curriculum_area);
    tag suite `m14_sorting`.
  - `live.py` `SUITES` += `"m14_sorting"`.
- **Test-first:** `tests/test_metric_split.py` — item family-routed: family vs
  final-route hai số tách; non-family: hai số trùng. `test_datasets.py` mở rộng:
  case sorting pass admission.
- **Rollback:** revert metrics() thêm + gỡ case.
- **Invariant:** F3 (metric semantics — điểm 5), luật kết nạp.
- **Commit:** `M14 Task 11: metric split family/variant/final-route + case sorting theo admission + suite m14_sorting`.

## Task 12 — Offline positive/paraphrase/near-miss/fault-injection regressions

- **Files/symbols:**
  - Hợp nhất mọi offline control I1 (12 mục) + Acceptance "Offline" của session
    vào test đã tạo (Task 5–11) + bổ sung thiếu.
  - FE: `frontend/src/simulations/domains/algorithm/*.test.ts` — executor trace
    preservation (config family-resolved vs config cũ tương đương → runAlgorithm
    trace giống hệt); FE module/renderer KHÔNG đổi (diff = 0).
- **Acceptance:** toàn bộ offline control có test xanh; đếm THỰC (không phát
  minh số).
- **Rollback:** test-only.
- **Invariant:** toàn bộ acceptance offline của session.
- **Commit:** `M14 Task 12: hoàn tất offline controls (descriptor/sorting/semantic/eval/coverage) + FE trace-preservation`.

## Task 13 — Targeted live pilot (user đã duyệt ngân sách: ≤16 call, ≤4 case)

- **Suite:** `m14_sorting` (Bubble explicit · Insertion explicit/paraphrase ·
  Selection near-miss→capability_gap · [case 4 dự phòng nếu cần kiểm 1 nhánh]).
- **Lệnh:** `ALLOW_LIVE_AI=1 python -m app.evaluation.live --dataset capability
  --suite m14_sorting --max-api-calls 16 --max-cases 4`.
- **Acceptance (ghi TRƯỚC):** classify→comparison_sort; final envelope
  bubble/insertion đúng; selection→capability_gap KHÔNG generic; ghi nhật ký
  live chính xác (HTTP/retry/transient) vào CURRENT_STATE §1.
- **Prompt-fix policy:** chỉ khi có trace/evidence; ≤1 lần; phải nằm trong
  design; targeted regression trước rerun; KHÔNG lách gate/validator.
- **Rollback:** live là quan sát; không đổi code trừ prompt-fix (nếu có, commit
  riêng).
- **Invariant:** #14 (live opt-in), #22 (đo trên production lifecycle).
- **Commit:** `M14 Task 13: live pilot m14_sorting — nhật ký + kết quả` (docs-only trừ prompt-fix).

## Task 14 — Docs + final review + close report

- **Files:** CURRENT_STATE §1 (nhật ký live) + §2 (hàng M14) + known-issues nếu
  có; ARCHITECTURE_MAP §5 bất biến #22 (+ mechanism gate); COVERAGE nếu chạm
  phát ngôn/§ma trận; CLAUDE.md KHÔNG sửa (gitignore); README KHÔNG sửa (ngoài scope).
- **Acceptance:** claim boundary đúng (§M "được phép"/"không claim"); tree sạch;
  hash báo cáo.
- **Commit:** `M14 Task 14: docs checkpoint + close report`.

---

## Thứ tự phụ thuộc + checkpoint

1→2→3 (descriptor/registry/artifact) · 4→5→6→7 (family spec + gate + adapter, độc
lập pipeline) · 8 (wire classify — điểm hợp nhất) · 9→10→11 (eval convergence +
metric) · 12 (đóng offline) · 13 (live) · 14 (docs). Mỗi task một commit; offline
xanh trước khi sang task sau. Full regression (pytest + vitest + build) chạy sau
Task 12, trước Task 13.

## Stop-condition mapping (dừng báo user)

- Task 7/8: nếu resolve buộc đổi array/order để hợp validator concrete → FamilySpec
  thành "ngôn ngữ ẩn" (stop 3) hoặc cần rewrite executor (stop 2).
- Task 6/13: nếu selection/quick chỉ chặn được bằng keyword (stop 4).
- Task 9/10: nếu không dùng chung orchestration mà không đổi hành vi production
  (stop 6) hoặc side-effect không cô lập được (stop 7).
- Task 11: nếu buộc sửa frozen expectations để che regression (stop 5).
- Bất kỳ: source cho thấy rev2 sai invariant (stop 8); baseline đỏ không liên quan
  (stop 9); quota không đủ (stop 10).
