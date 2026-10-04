# M16 — Comprehensive End-to-End LLM Evaluation — Implementation Plan

Ngày: 2026-07-19 · Design:
`docs/superpowers/specs/2026-07-19-m16-comprehensive-llm-evaluation-design.md`.
Quy trình mỗi task: implementation → spec-compliance review → code-quality
review → targeted tests → full regression (pytest/vitest/build) → commit.
Rollback boundary mặc định = revert commit của task (mỗi task một commit, không
task nào sửa file của task khác ngoài phần khai báo nối tiếp).

Ràng buộc toàn cục: frozen DATASET bất biến · không sửa metric cũ của
`EvalReport.metrics()` · không sửa routing/gate/retry/output `run_pipeline`
(duy nhất Task 2 thêm `_emit` observer-only) · FE không đụng (kỳ vọng FE
production diff = 0 toàn milestone) · mọi test offline (guard mạng đã có).

## Task 1 (W1) — M16 case schema + admission + frozen-integrity lock

- **Mục tiêu**: `app/evaluation/m16_schema.py` — `M16Archetype` (6 giá trị
  đóng), `M16Expectation` (frozen dataclass, field như design §2),
  `M16_DATASET_VERSION="m16-v1"`, `check_m16_admission(item)`,
  `frozen_dataset_fingerprint()` (SHA-256 canonical JSON của 30 item:
  id/text/group/expect_simulation_id/semantic/tags, sort_keys,
  ensure_ascii=False). `EvalItem` += trường `m16: object | None = None`
  (default None — 30 case frozen + 4 pool cũ không đổi nội dung).
- **Test viết trước** (`tests/test_m16_schema.py`): enum đóng 6 archetype;
  admission bắt lỗi từng nhánh (expected_family ∉ FamilyId; positive thiếu
  expected_initial_route; analyze_mechanism_expected đặt cho family ngoài
  2 family exposed; unsupported thiếu expected_gate lẫn notes); fingerprint
  == hằng số PIN (tính một lần, ghi vào test — thay đổi bất kỳ nội dung nào
  của 30 case làm test đỏ); EvalItem cũ không m16 vẫn dựng được (backward).
- **Invariant**: frozen DATASET nội dung y nguyên; admission cũ không đổi.
- **Acceptance**: pytest targeted xanh; full suite xanh (529 + mới).
- **Dependency**: không.

## Task 2 (W2) — Observer accessors + emit đối xứng + per-case budget + record builder

- **Mục tiêu**: (a) `observer.py` += `reclassify_attempted()`,
  `reclassify_result()`, `gate_events(gate=None)`; (b) `pipeline.py` nhánh
  direct-entry emit `gate_checked{gate:"mechanism", fired:False,
  reason_code:None}` khi verdict None (observer-only — 2 dòng, sau
  `check_mechanism_consistency_for_target`); (c) `harness.py::evaluate_item`
  nhận optional `budget` → snapshot 4 counter trước/sau → `budget_delta`;
  `run_eval` truyền budget xuống; (d) `app/evaluation/m16_record.py` —
  `M16CaseRecord` dataclass + `build_m16_record(item, obs, envelope,
  pipeline_error, budget_delta)` (dẫn xuất initial/final family tất định từ
  CATALOG/selector; taxonomy KHÔNG đọc message text).
- **Test viết trước** (`tests/test_m16_record.py`): fault-injection observer
  (bỏ event classify_done → record đánh dấu infra/None chứ không đoán);
  reclassify accessors đọc đúng event pipeline thật (chạy run_pipeline mock
  với case mismatch — tái dùng fixture test_pipeline_mechanism_consistency);
  emit đối xứng: direct-entry pass → gate_events("mechanism") có fired=False
  (case find_max mock); budget_delta đúng khi budget tick giả; record builder
  map đủ trường từ một transcript đầy đủ (so tay từng field).
- **Invariant**: `observer=None` → hành vi production không đổi một bit
  (test hiện có `test_pipeline*` xanh nguyên); output run_pipeline không đổi
  contract; `ItemResult`/metric cũ không đổi.
- **Acceptance**: targeted + full regression xanh; diff pipeline.py CHỈ chứa
  `_emit` (review khẳng định).
- **Dependency**: Task 1 (dataclass import).

## Task 3 (W3) — Metric module

- **Mục tiêu**: `app/evaluation/m16_metrics.py` — `MetricValue` (num/den/
  value|None), 17 metric đúng bảng design §4, applicability predicates
  máy-đọc, failure-taxonomy classifier (design §5, structured-only),
  aggregations: micro/macro/per-family/confusion-matrix/failure-distribution/
  applicability-report; `quality_band(value)`; run_label separation
  (offline/live_baseline/live_postfix); rule loại internal-fixture (test bằng
  record tổng hợp `reachability`-flag vì catalog hiện 0 fixture).
- **Test viết trước** (`tests/test_m16_metrics.py`): fixture nhỏ tính tay
  (~8 record tổng hợp) khớp từng metric; zero-denominator → value None và
  KHÔNG vào macro; initial vs final route là 2 metric độc lập (record recovery
  giữ CẢ initial error lẫn final correct); precision/recall không trộn;
  leak/false-positive/integrity/parity đúng trên record biên; band boundary
  (0.899/0.90/0.75).
- **Invariant**: không import/không sửa `EvalReport.metrics()`.
- **Acceptance**: targeted + full xanh.
- **Dependency**: Task 2 (M16CaseRecord).

## Task 4 (W4) — Dataset pool `m16`

- **Mục tiêu**: `app/evaluation/datasets/m16_catalog.py` — `M16_ITEMS`
  (~52 case theo design §6, mỗi case đủ admission cũ + m16 expectation),
  `M16_REFERENCED_CASES` (registry tham chiếu case pool cũ vào coverage
  matrix — không chép text), đăng ký `NEW_POOLS["m16"]`; `live.py` SUITES +=
  `m16_offline`, `m16_catalog_live`; đánh dấu `live_eligible` ≤24 case.
- **Test viết trước** (`tests/test_m16_dataset.py`): coverage lock 14/14
  target ≥2 supported positive (explicit+paraphrase); 8/8 family ≥1
  near_miss_gap + ≥1 valid_boundary; ≥2 cross_family_recovery (1 success +
  1 failure); admission + m16-admission xanh toàn pool; id prefix `m16-` +
  unique + ổn định (snapshot danh sách id pin trong test); frozen fingerprint
  (Task 1) vẫn xanh; live subset ≤24; sorting/positional có
  analyze_mechanism_expected; generic có authority_control cặp
  (leak control + representation đối chứng).
- **Invariant**: 4 pool cũ + frozen không đổi nội dung.
- **Acceptance**: targeted + full xanh.
- **Dependency**: Task 1.

## Task 5 (W5) — Scripted provider + offline end-to-end + hard correctness

- **Mục tiêu**: `tests/m16_scripts.py` (fixture — map case_id → analysis/
  classify-seq/simulate-seq, đúng schema production) + 
  `tests/test_m16_offline_eval.py`: chạy TOÀN BỘ pool m16 qua
  `evaluate_item` (production run_pipeline, monkeypatch
  `pipeline.call_gemini`), build record, compute metrics; assert HARD
  CORRECTNESS: false_positive_simulation=0/den, generic_fallback_leak=0/den,
  concrete_envelope_integrity=1.0, production_evaluation_parity=1.0, selector
  token ∉ mọi envelope id, frozen fingerprint nguyên; fault-injection tests
  riêng: false-refusal injected → metric #8 bắt; leak injected (bỏ gate bằng
  script analysis rule_derivable? KHÔNG — không bypass gate production; leak
  test = script classify→generic + analysis không có tín hiệu chặn → nếu gate
  production chặn: bằng chứng leak=0 do gate, assert đúng nhánh đó; +1 record
  tổng hợp chứng minh metric #12 BẮT được leak nếu xảy ra); transient
  separation bằng budget delta giả; wrong-initial+recovery-success/failure
  đi qua reclassify thật (2 classify call).
- **Invariant**: evaluator không dựng pipeline mirror (chỉ evaluate_item);
  0 network (guard tự chứng minh); executor oracle giữ nguyên (không đụng).
- **Acceptance**: toàn pool chạy xanh trong pytest; metric report tái lập
  (chạy 2 lần cùng kết quả); full regression xanh.
- **Dependency**: Task 2, 3, 4.

## Task 6 (W6) — Artifact generator + sync-lock

- **Mục tiêu**: `backend/scripts/generate_m16_artifacts.py` (stdlib-only,
  chạy tay) sinh 5 JSON vào `docs/evaluation/m16/` (design §8) từ pool +
  offline scripted run (tái dùng scripts fixture — import từ tests qua đường
  dẫn hoặc chuyển `m16_scripts.py` thành module data dùng chung
  `app/evaluation/m16_offline_scripts.py` để scripts KHÔNG sống trong tests
  nếu generator cần — quyết ở implementation, ưu tiên module dùng chung);
  commit artifacts; `tests/test_m16_artifacts.py` — regenerate-and-compare bỏ
  2 field volatile (git_commit, generated_at); schema_version/dataset_version/
  run_label/numerator-denominator hiện diện.
- **Invariant**: artifact sinh từ source/run output — không viết tay.
- **Acceptance**: sync-lock xanh; full regression xanh.
- **Dependency**: Task 5.

## Task 7 — Live runner extension (offline-tested) + docs CODE_INDEX

- **Mục tiêu**: `live.py` += `--label {baseline,postfix}`, `--out trace.json`
  (per-case M16CaseRecord + budget delta + run meta), `--resume-from
  trace.json` (skip case đã OK, cộng dồn budget vào report); KHÔNG đổi
  semantics opt-in/budget hiện có. `docs/CODE_INDEX.md` += entries
  m16_schema/m16_record/m16_metrics/m16_catalog/generate_m16_artifacts.
- **Test viết trước** (`tests/test_m16_live_runner.py`): parse args; trace
  ghi đúng schema (mock run 2 case); resume bỏ case OK + giữ case fail; label
  ghi vào meta; không opt-in vẫn abort (test cũ giữ).
- **Acceptance**: targeted + full xanh; docs-only phần CODE_INDEX đi cùng
  commit này (thay đổi thực tế đã có).
- **Dependency**: Task 2 (record), Task 4 (suite tag).

## Offline checkpoint (sau Task 7)

Trình bảng ≤25 dòng: commit range, HEAD, tree, pytest/vitest/build thật,
targets/families/cases, coverage summary, hard correctness, offline metric
summary, failure taxonomy counts, FE diff, live proposal (≤24 case, trần 80
HTTP, model gemini-2.5-flash), case list live. **DỪNG** — live PENDING
APPROVAL. CURRENT_STATE/ARCHITECTURE_MAP/COVERAGE cập nhật ở close (sau
live), không phải ở checkpoint.

## Thứ tự & song song

1 → (2, 4 song song) → 3 → 5 → 6 → 7. Mỗi task một commit; review theo quy
trình subagent-driven (implementer subagent + reviewer độc lập; final
whole-branch review trước checkpoint).
