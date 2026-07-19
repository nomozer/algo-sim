# M16 — Comprehensive End-to-End LLM Evaluation — Design

Ngày: 2026-07-19 · Sau audit `docs/superpowers/specs/2026-07-19-m16-evaluation-audit.md`
(`a650783`). Đề tài: "Hệ thống mô phỏng tương tác 2D/3D kết hợp LLM phân tích
bài toán bằng ngôn ngữ tự nhiên hỗ trợ dạy học môn Tin học THPT".

Nguyên tắc bao trùm: M16 là milestone **đo lường** — không capability mới,
không executor mới, không sửa routing/gate/validator production (ngoại lệ duy
nhất: `_emit` observer-only, no-op khi `observer=None`). Bất biến #22/#23 giữ
nguyên. Frozen DATASET (30) bất khả xâm phạm.

## 1. Evaluation universe (khóa theo audit §C)

- **14 concrete runtime targets** — đúng danh sách CATALOG, tất cả
  `AI_REACHABLE_PUBLIC`; **0 internal fixture** (rule loại trừ vẫn cài trong
  metric để phòng tương lai, test bằng record tổng hợp).
- **8 capability family** (`FamilyId`).
- **1 selector token**: `algorithm.comparison_sort` (không bao giờ là envelope id).
- Analyze-exposed mechanism signal: CHỈ `comparison_sort` +
  `positional_representation` (claim boundary M15 — denominator metric #1).

## 2. Case schema (Wave 1)

`EvalItem` thêm **một** trường optional `m16: M16Expectation | None = None`
(tiền lệ M8-PRE — metadata optional, không metric cũ nào đọc; frozen 30 và 4
pool cũ không đổi nội dung). `M16Expectation` (dataclass frozen, module mới
`app/evaluation/m16_schema.py`):

```
archetype: M16Archetype            # enum ĐÓNG, bên dưới
expected_family: str               # giá trị FamilyId (canonical, KHÔNG nhãn tự do)
expected_initial_route: str | None # token nếu target sau selector; else concrete id; None với unsupported
expected_gate: str | None          # "route_mechanism" | "mechanism" | "computation" | None
expected_error_code: str | None    # giá trị ErrorCode | None
analyze_mechanism_expected: str | None  # canonical mechanism — CHỈ sorting/positional
algorithmic_request: bool = False  # unsupported case đòi cơ chế thuật toán (denominator #12)
recovery_route_exists: bool = False # denominator #14
live_eligible: bool = False        # đề cử vào m16_catalog_live
notes: str = ""
```

`M16Archetype` (enum đóng): `explicit_positive` · `paraphrase_positive` ·
`valid_boundary` · `near_miss_gap` · `cross_family_recovery` ·
`authority_control` (computation-leak / anti-merge control).

- `expected_final_route` = `expect_simulation_id` sẵn có (không nhân đôi).
- `M16_DATASET_VERSION = "m16-v1"`.
- `check_m16_admission(item)`: yêu cầu admission cũ (`check_admission`) PASS +
  `m16` đầy đủ theo archetype (positive phải có expected_initial_route;
  unsupported phải có expected_gate hoặc lý do classify-refusal tường minh
  trong notes; `expected_family` ∈ FamilyId; `analyze_mechanism_expected` chỉ
  được đặt khi family ∈ {comparison_sort, positional_representation} — sai →
  vi phạm).

**Applicability rules máy-đọc** (không loại case thủ công sau khi thấy kết
quả): mỗi metric khai một predicate trên (item, record) — xem §4; module
`m16_metrics.py` xuất `applicability_report()` liệt kê case bị loại + rule.

**Locks Wave 1** (`tests/test_m16_schema.py` + `tests/test_m16_dataset.py`):
frozen-integrity = SHA-256 canonical-JSON của 30 item (id/text/group/
expect_simulation_id/semantic/tags) so hằng số pin; public-catalog coverage
lock (14/14 target có ≥2 supported positive; 8/8 family có ≥1 `near_miss_gap`
+ ≥1 `valid_boundary` — đếm trên coverage matrix, cho phép THAM CHIẾU case
pool cũ qua registry tường minh `M16_REFERENCED_CASES`, không chép lại text);
admission lock; case-id ổn định (prefix `m16-`).

## 3. Structured observations (Wave 2)

Đúng audit §F — bốn việc, KHÔNG đổi output `run_pipeline`:

- (a) `AttemptObserver` += accessor `reclassify_attempted()`,
  `reclassify_result()`, `gate_events(gate)`.
- (b) pipeline.py: emit đối xứng `gate_checked{gate:"mechanism", fired:False,
  reason_code:None}` ở nhánh direct-entry khi verdict None (sửa asymmetry M15
  T6 — observer-only; production `observer=None` → `_emit` no-op).
- (c) `run_eval`/`evaluate_item`: snapshot `ApiBudget` (logical_calls,
  http_requests, retry_requests, transient_hits) trước/sau mỗi case →
  `budget_delta` per-case (offline mock = 0, live = thật).
- (d) Builder `build_m16_record(item, obs, envelope, pipeline_error,
  budget_delta) -> M16CaseRecord` — mọi trường lấy từ event/envelope có cấu
  trúc; message text CHỈ được chép vào field `detail` tham khảo, KHÔNG dùng để
  phân loại (fallback `classify_error` cũ không tham gia taxonomy M16).

`M16CaseRecord` (per-case, JSON-serializable): case_id, group, archetype,
expected_*, raw/canonical prescribed, result_ownership, initial_route,
initial_family (dẫn xuất tất định), reclassify_attempted/result, final_route,
final_family, selector_token_used, variant, gates: list{gate, fired,
reason_code}, simulate_attempts: list{n, ok, error_code}, first_attempt_ok,
semantic_ok, envelope_status, envelope_error_code, failure_category (dẫn xuất
§5), source (composed/family_resolved/pattern_reuse), budget_delta,
via_production_pipeline: bool (parity flag — set bởi evaluate path, fault-
injectable), infra_error: str | None.

Quy ước máy-đọc: **absence-of-event = gate không được lượng giá trên đường đi
đó** (ghi trong docstring schema; sau (b), mechanism gate luôn có event trên
mọi final route direct/selector).

## 4. Metrics (Wave 3) — công thức KHÓA trước khi chạy

Module `app/evaluation/m16_metrics.py`. Mọi metric trả
`MetricValue{numerator: int, denominator: int, value: float | None}` —
**denominator 0 → value None (N/A)**, không bao giờ 0.0 giả. "Supported" =
group ∈ {specialized, generic}. "Refused" = envelope status unsupported
(không ok, không infra_error). Product cases = record không `infra_error` và
không internal-fixture.

| # | Metric | Numerator / Denominator |
|---|---|---|
| 1 | analyze_mechanism_accuracy | canonical_prescribed == analyze_mechanism_expected / case có analyze_mechanism_expected ≠ None |
| 2 | family_selection_accuracy | final_family == expected_family / supported có expected_family |
| 3 | variant_selection_accuracy | final_route == expect / supported có expected route sau selector (comparison_sort) |
| 4 | initial_route_accuracy | initial_route == expected_initial_route / supported |
| 5 | final_route_accuracy | envelope ok ∧ final_route == expect / supported |
| 6 | valid_spec_first_attempt_rate | first_attempt_ok / supported có ≥1 simulate_attempt |
| 7 | semantic_pass_rate | semantic_ok / supported có semantic check áp dụng (generic, semantic.kind ≠ "none") |
| 8 | false_refusal_rate | supported bị refused / supported |
| 9 | unsupported_recall | unsupported bị refused / unsupported |
| 10 | unsupported_precision | refused có group unsupported / mọi case refused |
| 11 | false_positive_simulation_rate | unsupported có envelope ok / unsupported |
| 12 | generic_fallback_leak_rate | unsupported-algorithmic có envelope ok với final_route == generic.rule_scene / unsupported có algorithmic_request |
| 13 | reclassification_rate | reclassify_attempted / mọi product case |
| 14 | route_recovery_success_rate | reclassify_attempted ∧ envelope ok ∧ final_route == expect / reclassify_attempted ∧ recovery_route_exists |
| 15 | retry (3 kênh riêng) | semantic_retries = Σ simulate_attempts sau lần đầu; transient_retries = Σ budget_delta.retry_requests; reclassify_count = Σ reclassify_attempted — báo count + avg, không trộn |
| 16 | concrete_envelope_integrity | ok envelope có simulation_id ∈ CATALOG ∧ ∉ selector tokens / mọi ok envelope |
| 17 | production_evaluation_parity | record có via_production_pipeline / mọi evaluated case |

Aggregation: **micro** (trên toàn product cases), **macro** = trung bình
per-family value (family N/A bị loại và LIỆT KÊ), **per-family table**,
**confusion matrix** (expected final route × actual outcome, outcome gồm mọi
concrete id + `refused` + `error`), **failure distribution** (§5),
**applicability report** (per metric: rule + case bị loại). Pre-fix/post-fix:
mỗi run mang `run_label ∈ {offline, live_baseline, live_postfix}` — không ghi
đè; metric tính riêng theo label.

Quality bands (chỉ nhãn báo cáo): STRONG ≥ 0.90 · MODERATE 0.75–0.899 ·
WEAK < 0.75; luôn kèm numerator/denominator.

Metric harness CŨ (`EvalReport.metrics()`) **không sửa** — M16 metrics là lớp
song song (tiền lệ M7.14T/M14 §F3), so sánh lịch sử giữ nguyên.

## 5. Failure taxonomy (khóa) — phân loại từ structured fields ONLY

Ưu tiên theo thứ tự; một case giữ CẢ initial-stage error lẫn final outcome:

| Category | Điều kiện structured |
|---|---|
| TRANSIENT_PROVIDER_ERROR | budget_delta.transient_hits > 0 (đánh dấu kèm, không thay outcome) |
| EVALUATION_INFRASTRUCTURE_ERROR | infra_error ≠ None (mock/script hỏng, exception ngoài pipeline semantics) |
| ANALYZE_MECHANISM_ERROR | analyze_mechanism_expected ≠ None ∧ canonical_prescribed ≠ expected |
| INITIAL_FAMILY_SELECTION_ERROR | supported ∧ initial_family ≠ expected_family |
| INITIAL_VARIANT_SELECTION_ERROR | supported sau selector ∧ variant đầu tiên sai (mechanism_variant_mismatch attempt) |
| ROUTE_MECHANISM_FAMILY_MISMATCH | gate route_mechanism fired (reason_code khớp) |
| ROUTE_RECOVERY_FAILED | reclassify_attempted ∧ recovery_route_exists ∧ final không đúng expect |
| GATE_MECHANISM_OWNERSHIP | error_code gate_mechanism_ownership trên final |
| FAMILY_SPEC_INVALID | simulate_attempt error_code family_spec_invalid (mọi attempt fail) |
| CONCRETE_CONFIG_INVALID | simulate_attempt error_code structural_invalid (mọi attempt fail) |
| SEMANTIC_VALIDATION_FAILED | semantic_incompat/scene_mode/system_flow fail cuối, hoặc semantic_ok=False |
| FALSE_REFUSAL | supported ∧ refused |
| FALSE_POSITIVE_SIMULATION | unsupported ∧ envelope ok |
| GENERIC_FALLBACK_LEAK | unsupported-algorithmic ∧ envelope ok generic.rule_scene |
| EXECUTOR_ORACLE_MISMATCH | reserved — chỉ đặt khi so oracle tất định lệch (M16 offline không kỳ vọng ca nào) |

Ví dụ giữ hai tầng: `initial_family_selection_error=true` +
`route_recovery_success=true` + `final_outcome=correct` — báo CẢ HAI.

## 6. Dataset M16 (Wave 4) — pool `m16`, version `m16-v1`

File `app/evaluation/datasets/m16_catalog.py`, đăng ký `POOLS["m16"]`
(qua NEW_POOLS để ăn admission). **~52 case** (số cuối chốt khi viết, ưu tiên
coverage rõ; mọi case id prefix `m16-`, ổn định):

- 14 target × explicit_positive + paraphrase_positive = **28** (binary_search
  paraphrase = wording "chia đôi vùng xét" không nêu tên; generic tách
  reveal_sequence positive + move_along_path positive làm cặp positive của
  structural family; boolean: and_gate 2-input positive + generic DAG positive).
- 8 family × valid_boundary = **8** (scan: thiếu thông tin optional; interval:
  target-absent trên dãy đã sắp; sorting: dãy có phần tử trùng; boolean:
  anti-merge control "3 công tắc AND" → generic (không and_gate); positional:
  boundary 0 và 255 (2 case — positional có 2 boundary, bù cho family khác khi
  đếm tổng); graph: alternative topology / unreachable theo contract; encap:
  decapsulation explicit; structural: webstatic-kiểu prebuilt).
- 8 family × near_miss_gap = **8** (sorting: selection-sort mới ĐÃ có pool cũ
  → M16 viết case MỚI có m16 metadata: quicksort-partition wording khác;
  scan: multi-pass "duyệt nhiều lượt đến khi không đổi chỗ" (phân biệt với
  sorting!) — chọn free-loop biến tự do wording mới; interval: interpolation
  search / "chia ba"; boolean: threshold k-of-n mới; positional: hex mới
  wording khác; graph: Dijkstra trọng số wording mới; encap: TCP handshake
  wording mới; structural: computation request "dựng cảnh minh họa kết quả
  Dijkstra" authority_control).
- cross_family_recovery = **2** (recovery-success: đề positional wording gây
  classify lệch sang generic — kỳ vọng recovery về binary.decimal_to_binary;
  recovery-failure: prescribed positional nhưng khắp nơi lệch → fail-closed
  gap; cả hai offline scripted, live chỉ chạy success candidate).
- authority_control bổ sung = **2** (generic computation-leak: "vẽ sơ đồ và
  TÍNH đường ngắn nhất" → unsupported không generic; representation positive
  đối chứng "chỉ VẼ sơ đồ" → generic ok).
- binsearch controls = target-found (positive explicit đã đếm), target-absent
  (boundary đã đếm), unsorted → normalize + annotation (valid_boundary thứ 2
  của interval), wording-gần-linear (near-miss của interval đã đếm ở trên nếu
  chọn; nếu không, thêm 1 case). Positional out-of-range contract error = 1
  case (valid_boundary — kỳ vọng validator từ chối cấu trúc, LLM retry, không
  phải capability gap; expected behavior ghi máy-đọc).

Coverage matrix (machine-readable, sinh ở Wave 6): case_id → target/expected
gap → family → archetype → curriculum_area → result_mode → expected final
route → expected gate → expected error_code → live_eligible.

Suites: tag `m16_offline` (tất cả), `m16_catalog_live` (subset ≤24 —
live_eligible=True). `live.py` SUITES += 2 tag này.

## 7. Offline end-to-end evaluation (Wave 5)

Scripted provider per-case (test fixture `tests/m16_scripts.py`, KHÔNG nằm
trong dataset — dataset là benchmark definition thuần): map case_id →
{analysis dict (đúng ANALYZE_SCHEMA, prescribed/result_ownership thật),
classify sequence (lượt 1 [+ lượt 2 nếu recovery]), simulate sequence}.
Monkeypatch `pipeline.call_gemini` (đúng chỗ harness offline hiện có —
`test_evaluation.py::_make_mock` tiền lệ), chạy `evaluate_item` →
`build_m16_record` → metrics.

Phủ bắt buộc: correct-first-route; wrong-initial + recovery success; wrong-
initial + recovery failure; ownership gap (direct + selector); config invalid
(retry rồi ok / cạn); semantic invalid; **fault injection**: false-refusal
(script ép classify unsupported trên supported case → metric #8 bắt);
generic-fallback-leak (script ép classify generic + simulate ok trên
unsupported-algorithmic case KHÔNG qua gate được — nếu gate production chặn
thật thì đó là bằng chứng leak=0 do gate, ghi rõ hai nhánh); transient
separation (budget delta giả). Hard correctness (spec M16) assert trong test.

## 8. Reporting artifacts (Wave 6)

`backend/scripts/generate_m16_artifacts.py` (chạy tay như
`generate_capability_descriptors.py`) sinh vào `docs/evaluation/m16/`:

- `m16-case-matrix.json` — sinh từ pool + m16 metadata (schema_version 1).
- `m16-coverage-report.json` — đếm coverage lock (14/14, 8/8, per-archetype).
- `m16-offline-results.json` — per-case record của offline run (scripted).
- `m16-metrics.json` — metric values + aggregations + applicability + bands.
- `m16-failure-ledger.json` — failure taxonomy per case (offline: expected
  failures của fault-injection ghi nhãn injected=true).

Mọi artifact: `schema_version`, `dataset_version`, `run_label`,
`git_commit` + `generated_at` (hai field volatile — sync-lock test so sánh
nội dung SAU KHI bỏ 2 field này), numerator/denominator đầy đủ, phân biệt
offline/live + pre-fix/post-fix (live artifacts sinh sau live run, KHÔNG ở
wave này). Sync-lock: `tests/test_m16_artifacts.py` regenerate-and-compare
(bỏ volatile fields).

## 9. Live suite `m16_catalog_live` (Phase 4 — PENDING APPROVAL)

Nguyên tắc chọn (spec user): ≥1 positive/target (14), ≥1 near-miss/family
(8, gộp khi trùng cơ chế), sorting positive+unsupported variant, positional
binary+non-binary, generic representation+leak control, ≥2 cross-family
recovery, paraphrase ở mọi family — gộp case trùng cơ chế → **≤24 logical
case**, trần tuyệt đối **80 HTTP**. Live runner mở rộng (offline-tested):
`--label baseline|postfix`, `--out <trace.json>` (structured trace per-case:
record + budget delta), `--resume-from <trace.json>` (bỏ case đã OK, cộng dồn
budget). Live fix discipline + CACHE_VERSION bump theo đúng spec user (chỉ khi
prompt/schema production đổi; 1 correction round tối đa).

## 10. Reproducibility & claim boundary

- Offline: scripted provider tất định → metric tái lập bit-một-bit; artifact
  sync-locked.
- Live: nhật ký HTTP/retry/transient chính xác (CURRENT_STATE §1 convention);
  trace JSON per run; pre-fix baseline giữ nguyên khi có correction.
- Claim sau M16 đúng 3 câu trong spec user (đầu-cuối trên toàn public catalog
  bằng production orchestration; số X/Y cụ thể; phạm vi = capability đại diện
  trong đề tài). KHÔNG claim: hiệu quả học tập, phủ toàn chương trình, mọi bài
  toán tự nhiên.

## 11. COMPLETE criteria

Đúng 23 mục trong spec user (không thêm bớt). Offline phase này phủ mục
1–10, 13(offline)–20(một phần docs), 23; mục 11/12/21/22 chờ live + close.

## 12. Quyết định kiến trúc

Audit xác nhận: **không có** quyết định production-lifecycle mới — mọi thay
đổi thuộc lớp evaluation + 1 emit observer-only (no-op production). → đủ điều
kiện triển khai offline trong cùng session (spec Phase 2). Điểm dừng cứng:
OFFLINE CHECKPOINT + live stop gate.
