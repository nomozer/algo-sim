# CODE_INDEX.md — Chỉ mục module + BỘ NHỚ KIẾN TRÚC

Mục đích: biết **cái gì đã tồn tại và ở đâu** trước khi viết mới (chống trùng
helper, chống hard-code vòng qua abstraction sẵn có). **Không chép thân hàm.**
Helper private nhỏ được bỏ qua có chủ ý.

Đây là **file canonical cho vai trò project index / architecture memory**, dùng
kèm `docs/ARCHITECTURE_MAP.md` (kiến trúc, bảng sở hữu, hướng phụ thuộc, bất
biến đánh số). Trước khi thêm bất cứ thứ gì: đọc `docs/RULES.md` §2b.

---

## 0. Danh tính kho mã (kiểm lại bằng lệnh, đừng tin trí nhớ)

| Hạng mục | Giá trị | Kiểm bằng |
|---|---|---|
| Active mainline | `main` | `git branch --show-current` |
| Baseline | `f2b28e2` (PATCH1 impl `8bd2324` + live evidence) | `git rev-parse HEAD` |
| `CACHE_VERSION` | **27** | `grep -n 'CACHE_VERSION = ' backend/app/main.py` |
| `HISTORY_SCHEMA_VERSION` | **2** | `frontend/src/state/history.ts:33` |
| Family / Target | **12 / 23** | `backend/.venv/Scripts/python.exe backend/scripts/catalog_runtime_matrix.py` |
| ↳ computation / representation | **10 / 2** — xem §0h | `result_authority` trên `FamilyMembership` |
| Trình bày 2D / 2D+3D | **22 / 1** | `SimSpec.visual_modes`; parity `capability-descriptors.test.ts` |
| Archive (read-only) | `archive/m17-w2b-deep-hardening` → `feb12d8` | `git rev-parse archive/m17-w2b-deep-hardening` |

Danh tính runtime (so source ↔ container) do `backend/app/runtime_identity.py` +
`backend/scripts/runtime_doctor.py` lo — endpoint `GET /api/diagnostics/runtime`.

## 0b. Điểm vào (entry point) — đã xác minh tồn tại ở baseline này

| Vai trò | Vị trí |
|---|---|
| HTTP surface | `backend/app/main.py` — `/api/analyze`, `/api/edit`, `/api/explain`, `/api/manifest`, `/api/health`, `/api/diagnostics/runtime` |
| Production pipeline | `ai/pipeline.py::run_pipeline(text, api_key, pattern_store=None, observer=None)` |
| Ba stage LLM | `stage_analyze` · `stage_classify` · `stage_simulate` (+ `stage_adapt`, `stage_simulate_family`) |
| Route recovery | `classify_with_one_route_recovery` — ≤1 lượt, TRƯỚC mọi cổng phụ thuộc route |
| Validation dispatch | **không có hàm dispatch trung tâm** — mỗi `SimSpec.validate` trỏ tới validator riêng trong `app/validation/` (`validate_algorithm_config`, `validate_logic_config`, `validate_binary_config`, `validate_base_conversion_config`, `validate_tree_traversal_config`, `validate_table_query_config`, `validate_generic_config`, `validate_network_config`, `validate_encapsulation_config`, `validate_traverse_config`, `validate_scan_config`, `validate_boolean_dag_config`) |
| Registry (BE) | `simulation/catalog.py::CATALOG: dict[str, SimSpec]` |
| Registry (FE) | `simulations/registry.ts` — `registerSimulation` / `getSimulation` / `listSimulations`; nạp qua `simulations/index.ts::registerAllSimulations()` gọi ở `main.tsx` **trước** render |
| Executor dispatch (FE) | `state/store.ts` gọi `getSimulation(id).init/apply/timeline` — store **domain-blind** |
| Renderer dispatch | `simulations/renderer.ts` — `rendererFor`, `availableVisualModes`, `effectiveVisualMode` (dẫn xuất từ hợp đồng module, **không** switch theo `simulation_id`) |
| Lịch sử zero-AI | `state/history.ts` — `HISTORY_SCHEMA_VERSION`, `createHistoryStore`, `historyStore` |

## 0c. Trừu tượng DÙNG CHUNG — bắt buộc reuse, cấm viết bản thứ hai

| Trách nhiệm | Module | Ghi chú |
|---|---|---|
| Cổng đủ dữ kiện | `simulation/sufficiency_gate.py` + `input_requirements.py` | MỘT cổng cho MỌI target; normalizer theo **nhóm dữ kiện**, không theo target. Cấm `*_sufficiency_gate.py` riêng |
| Cổng đủ ngữ nghĩa | `simulation/completeness_gate.py` | `check_requested_combination` (trước simulate) + `check_represented_coverage` (sau) |
| Kênh tầng pipeline | `simulation/pipeline_stages.py` | `stage_coverage`, `requested_stages`, `represented_stages` — đăng ký theo FAMILY, family không khai ⇒ rỗng |
| Cổng cơ chế / tính toán | `mechanism_gate.py` · `computation_gate.py` · `structure_gate.py` | |
| Danh tính cơ chế | `simulation/mechanisms.py::canonical_mechanism` | **BIÊN ALIAS DUY NHẤT** — cấm normalize ở chỗ khác |
| Danh tính thao tác | `simulation/operations.py::OPERATIONS` | id dạng `family:operation` (dấu hai chấm) |
| Taxonomy family | `simulation/descriptor.py::FamilyId` (10) | closed enum |
| Bề mặt family cho LLM | `simulation/families/` | selector token ≠ SimSpec ≠ envelope id |
| Hợp đồng DSL | `simulation/dsl/manifest.py` | mọi enum/allowlist/prompt contract **dẫn xuất** từ đây |
| Thông điệp học sinh | `app/learner_messages.py` | KHÔNG để lộ token kỹ thuật; FE render qua MỘT `UnsupportedNotice` |
| Ma trận conformance | `app/catalog_conformance.py` + `scripts/catalog_runtime_matrix.py` | sinh **từ registry**, không hard-code danh sách target |
| Observer đánh giá | `evaluation/observer.py` | THỤ ĐỘNG — `None` ⇒ production không đổi một bit (bất biến #22) |

## 0d. Luồng chính (đọc kỹ trước khi thêm nhánh mới)

1. **Fresh request** — `/api/analyze` → `run_pipeline` → analyze → representation plan → classify → (≤1 route recovery) → **4 cổng** (computation · mechanism · input-sufficiency · completeness) → simulate (≤3 lượt) → `ValidatedSimulationEnvelope`.
2. **Bounded retry** — chỉ ở `stage_simulate`, lý do từ chối được nhồi ngược vào prompt; **không** phải retry HTTP.
3. **Cache hit** — chỉ cache analyze **thành công**, khoá theo text đã chuẩn hoá + `CACHE_VERSION`.
4. **History reopen** — `store.reopenFromHistory` → thẳng vào engine tất định, **0 gọi AI** (bất biến #17).
5. **Refusal** — bất kỳ cổng nào chặn → `unsupported` + `failure_category` + learner message; **không** dựng cảnh minh hoạ.
6. **Rendering** — engine state (ngữ nghĩa thuần, **không** toạ độ pixel) → renderer 2D/3D dùng chung state.

## 0e. Luật phụ thuộc (không được đảo — chi tiết ở ARCHITECTURE_MAP §4)

- LLM **không** sở hữu kết quả cuối; renderer **không** tính lại kết quả.
- Engine **không** phụ thuộc frontend; validator **không** phụ thuộc renderer.
- Hợp đồng dùng chung **không** phụ thuộc ngược vào implementation của family.
- `generic` **không** nhận `result_authority` kiểu algorithmic.
- Cấm circular import; family **không** import ngược orchestration nếu không cần.

## 0f. Giới hạn đã biết (trung thực)

- `database.relational_table_query`: truy vấn đơn giản **VERIFIED**; pipeline
  nhiều tầng bằng NL **PARTIAL / EXPERIMENTAL** (`W2B_THESIS_SCOPE_DECISION.md`).
- Deep hardening PATCH2/PATCH3 **chỉ có trong archive**, không merge lại.
- Backlog Analyze Integrity còn mở: chưa có provenance/source-span cho từng
  object/relation.
- Coverage gap khai báo trung thực ở `simulation/coverage.py` + `docs/COVERAGE.md`.

## 0g. Chính sách cập nhật file này

**Phải cập nhật khi:** thêm/xoá family hoặc target · thêm contract/schema · đổi
entry point · thêm module lớn · đổi dependency quan trọng · đổi source of truth ·
đổi `CACHE_VERSION`/`HISTORY_SCHEMA_VERSION` · di chuyển file kiến trúc chính.

**Không cần cập nhật khi:** đổi tên biến local · thêm helper private nhỏ · sửa
CSS nhỏ · thêm một test lẻ.

> Quy mô hiện tại: **manual tracked index là đủ** — registry/target/family đã có
> generator tất định (`scripts/catalog_runtime_matrix.py`), không dựng thêm
> generator index/call-graph mới.

## 0i. Đổi cơ số — MỘT nguồn (M17 P1a)

`frontend/src/simulations/domains/binary/base-conversion.ts` — phần **thuần tất
định** của đổi cơ số: `toBase`, `divideSteps`, `weightSteps`, `buildConvSteps`,
`parseInBase`, `digitsValid`, `canonicalDigits`, `strategyOf`, `BASE_NAME`,
`CONV_BASES`, `CONV_MAX_VALUE` + kiểu `ConvBase`/`ConvStep`/`DivideStep`.

- **Không** React / renderer / store / registry / target id;
- `convert-module.tsx` **re-export** ⇒ mọi import cũ (`./convert-module`) giữ nguyên;
- `encoding-module.tsx` dùng `divideSteps()` — **không** có converter thứ hai
  (test so **tham chiếu hàm**, và quét thư mục tìm bản cài trùng).

Trước khi viết bất kỳ phép đổi cơ số nào: **dùng file này**, đừng cài lại.

## 0h. Mô phỏng cơ chế ≠ biểu diễn tiến triển (M17 P1b)

Kho mã có **11 family**, nhưng chúng **không cùng một loại**. `FamilyMembership.
result_authority` đã phân biệt sẵn từ M14 — mục này chỉ ghi lại để không ai đếm
phẳng:

| Loại | Số | Nghĩa |
|---|---|---|
| `computation` | **10** | engine **chạy cơ chế miền** và dẫn ra kết quả (sort, scan, traversal, đổi cơ số, DAG, pipeline truy vấn, luồng điều khiển…) |
| `representation` | **1** | `structural_progressive_representation` — engine dựng **frame biểu diễn**, không thực thi thuật toán |

Family `representation` duy nhất là `generic.rule_scene`:
`RevealStep { objects, narration? }` chỉ khai **object nào bắt đầu xuất hiện**;
`move_along_path` nội suy trên đường **đã khai sẵn**. Không có hệ quả miền giữa
hai bước.

**Cách nói đúng:** *"11 family năng lực, gồm 10 family mô phỏng cơ chế tính toán
và một family biểu diễn tiến triển."*

**Không viết:** "11 family đều là mô phỏng thuật toán" · "22 target đều là mô
phỏng cơ chế" · "`generic.rule_scene` thực thi thuật toán".

`generic.rule_scene` **không phải lỗi** — code đúng, renderer đúng, target giữ
nguyên. Nó là **biểu diễn hỗ trợ**, chỉ không được dùng làm bằng chứng chính cho
"mô phỏng thuật toán". Bằng chứng: `docs/evaluation/m17/simulation-authenticity/`.

---

**Change impact** (theo `CORRECTNESS.md §7`) — sửa file này thì cần kiểm gì:
- `offline` — pytest/vitest/build là đủ.
- `targeted live` — chạm hợp đồng AI (prompt/schema/contract) → live smoke có mục tiêu.
- `full live` — chỉ khi kết thúc milestone lớn / lấy số liệu luận văn.

Cập nhật khi module hoặc export **công khai** đổi.

---

## Backend — `backend/app/`

### `ai/gemini.py` · Change impact: targeted live
Lớp gọi Gemini + bộ nạp skill + **ngân sách API** (M7.14T).
Exports: `MODEL`, `SKILLS_DIR`, `MAX_ATTEMPTS`, `TRANSIENT_STATUS`, `load_skill`,
`call_gemini`, `ApiBudget`, `BudgetExceeded`, `set_budget`, `BUDGET`.
Deps: httpx. Consumers: `ai/pipeline`, `ai/edit`, `ai/explain`, `ingestion/input`
(mỗi module có **binding riêng** — mock một chỗ không che chỗ khác).
Tests: `test_gemini.py` (fake transport), `test_live_budget.py`.
Notes: **biên mạng duy nhất** của hệ. Guard offline nằm ở `conftest.py`, KHÔNG ở
đây (test_gemini có quyền dùng transport giả). `ApiBudget` inert khi `BUDGET=None`.

### `ai/pipeline.py` · Change impact: targeted live
Orchestrator: analyze → plan/gate → classify → (pattern reuse | simulate) → envelope.
Exports: `ANALYZE_SCHEMA`, `stage_analyze`, `stage_classify`, `stage_simulate`,
`stage_adapt`, `try_pattern_reuse`, `run_pipeline(text, api_key, pattern_store=None,
observer=None)`, (M15) `classify_with_one_route_recovery`, (vNext)
`stage_semantic_analyze`, `stage_semantic_program(text, analysis, api_key,
contract=None, observer=None)`, `MAX_SEMANTIC_PROGRAM_ATTEMPTS`,
`_envelope_tu_route_sinh`.
Deps: catalog, manifest, representation, semantic, patterns, gemini, (M15)
`mechanism_gate.check_mechanism_consistency_for_target`, `mechanisms.canonical_mechanism`.
Tests: `test_pipeline.py`, `test_reuse.py`, `test_capability_boundary.py`,
(M15) `test_pipeline_mechanism_consistency.py`.
Notes: capability gate chỉ chặn **đường generic** (bất biến #5). `pattern_store`
inject → None = hành vi compose cũ. (M14 bất biến #22) `observer` THỤ ĐỘNG —
`None` → hành vi production không đổi; eval đi CHUNG `run_pipeline`.
(M15) `classify_with_one_route_recovery(text, analysis, classification, api_key, observer=None)` —
route-consistency ordering: **≤ 1 reclassify BOUNDED** chạy TRƯỚC mọi
route-dependent gate khác khi `check_mechanism_consistency_for_target` phát
hiện `ROUTE_MECHANISM_FAMILY_MISMATCH` trên route đầu; reclassify ra
`unsupported` → passthrough (từ chối trung thực, không ép reclassify thêm lần
nữa); mismatch vẫn còn sau 1 lượt → `capability_gap`. Ngân sách cố định: analyze
tối đa 1 call, classify tối đa 2 (gốc + đúng 1 reclassify), simulate tối đa 1 —
không có đường quay lại vô hạn.
**(vNext 2026-08-23) `stage_semantic_program` nay ≤3 lượt**, gửi lỗi validator
ngược cho LLM sửa — khuôn `stage_simulate`. Lý do đo được: tám lượt probe E2E
trên một đề chết ở TÁM lỗi HÌNH DẠNG khác nhau (`container` nhận biểu thức rồi
nhận literal, `pop` viết như biểu thức rồi `peek` viết như câu lệnh…), không lỗi
nào là hiểu sai đề. Trần là HẰNG SỐ ⇒ claim D1 nguyên vẹn (lượt LLM chặn bởi
call graph, không theo độ dài trace). **Và nhánh PHÁT của route sinh nay chạy cả
khi `mismatch_gap` bắn**: trước đó một phán quyết lệch của classifier legacy
return TRƯỚC nhánh phát, giết một outcome `servable=true` (đo được: đề "đảo dãy
bằng ngăn xếp" đạt `stage_reached=served` rồi envelope trả `unsupported`). Cổng
mismatch bảo vệ đường module — chương trình ngữ nghĩa không đi qua target nào.
Envelope dựng ở MỘT chỗ: `_envelope_tu_route_sinh`.

### `ai/edit.py` · Change impact: targeted live
NL edit nhẹ (M7.14A): 1 call LLM sinh `{required_roles, operations}`; server đối
chiếu `known_gap_roles` **tất định** rồi áp patch.
Exports: `EDIT_SCHEMA`, `edit_simulation(config, instruction, api_key)`.
Tests: `test_edit.py`. Notes: KHÔNG chạy analyze/classify/simulate; LLM không được
quyết supported/unsupported.

### `ai/explain.py` · Change impact: targeted live
Q&A Socratic trên snapshot state THẬT. Exports: `EXPLAIN_SCHEMA`, `explain_state`.
Notes: **bề mặt hội thoại LLM duy nhất**; không phán đúng/sai, không điều khiển
mô phỏng.

### `ai/skills/*.md` · Change impact: targeted live
`analyze` `classify` `simulate` `explain` `transcribe` `edit`. Prompt là **file
markdown**, nạp qua `load_skill` (cache theo process → **restart backend** sau khi
sửa). Không bao giờ ship xuống trình duyệt.

### `simulation/dsl/manifest.py` · Change impact: targeted live
**Nguồn chân lý capability**: object/rule/interaction/process types, limits,
`SEMANTIC_ROLES` (gồm 8 **gap role** cố ý không cover), `PRIMITIVE_ROLES`.
Exports: `DSL_VERSION`, `SUPPORTED_VERSIONS`, `object_types`, `rule_types`,
`bool_ops`, `interaction_types`, `process_types`, `drag_target_types`,
`temporal_process_types`, `limit`, `roles_of_primitive`, `all_coverable_roles`,
`known_gap_roles`, `primitives_for_role`, `manifest_capability_summary`,
`manifest_contract_text`, `MANIFEST`, (M13) `value_provider_types(role)`,
`RULE_IO_ROLES`, `PATCH_ADD_FIELDS`, `patch_add_fields()`, `dsl_semantic_contract()`.
Consumers: validator, catalog (enum structured-output), representation, semantic,
patterns, edit. Tests: `test_manifest.py`.
Notes: thêm primitive = **chỉ sửa file này** (+ mirror TS). M11:
`manifest_contract_text` có đoạn hướng dẫn **chuỗi rule qua trung gian** (ví dụ
trừu tượng `kq_phu` — cố ý KHÔNG trùng case đánh giá nào, chống overfit prompt
vào benchmark; khoá bằng `test_contract_huong_dan_chuoi_rule_m11`). Đây là
**prompt-surface**, không phải từ vựng.
M13: `value_provider_types(role)` = object type nào có vai trò cung cấp giá trị
`role` (DẪN XUẤT từ `PRIMITIVE_ROLES ∩ object_types`, không viết tay). `RULE_IO_ROLES`
= input/output role của mỗi rule type (completeness khoá bằng
`test_rule_io_roles_phu_du_moi_rule_type_cua_manifest`, chống thêm rule type mà
quên khai role). `PATCH_ADD_FIELDS` (Task 12b) = allowlist field `add_object` của
SimulationPatch v1 — nguồn chân lý duy nhất cho `patch.py`/`patch.ts`, chống lệch
tay kiểu `directed` từng lệch (backend có, frontend không). `dsl_semantic_contract()`
gộp cả bốn thứ trên (+ `object_roles`, `role_compatibility` — M13 hotfix: subtyping
một chiều `logical→numeric` qua `role_satisfies()`, mọi cặp khác vẫn DENY mặc định)
thành **MỘT artifact hợp đồng ngữ nghĩa canonical**, sinh ra `dsl-contract.json`
cho frontend (xem entry `scripts/generate_dsl_contract.py` bên dưới) — không tầng
nào viết tay allowlist song song. Re-verify: offline; nếu đổi shape hợp đồng thì
**phải chạy lại generator** trước khi commit hoặc `test_dsl_contract_json_khong_troi_khoi_manifest`
sẽ đỏ.

### `simulation/computation_gate.py` (M13) · Change impact: offline
Cổng B (workstream B): SERVER quyết accept/gap trên đường generic bằng **hai
kênh tín hiệu có cấu trúc bổ sung nhau**, tất định, KHÔNG đọc text đề, chạy
**sau classify**, scoped vào đường generic bằng kết quả classify (giữ
carve-out chuyên biệt).
Exports: `check_computation_ownership(analysis, plan) -> str | None`.
Consumers: `ai/pipeline.py::run_pipeline`. Tests: `test_m13_routing.py`.
Notes: kênh 1 = `known_gap_roles()` lọt vào `plan["unsupported_capabilities"]`
(vd `arbitrary_algorithm`); kênh 2 = `analysis["result_ownership"]` **fail-closed**
— chỉ `"provided"`/`"rule_derivable"` được đi tiếp, `"algorithmic"` HOẶC
thiếu/ngoài enum đều → gap (không default sang giá trị nào). Hai kênh **bổ sung
nhau có chủ đích**: test chứng minh gap vẫn fired dù kênh 1 bị bỏ sót role
(`test_kenh_2_result_ownership_algorithmic_gap_KE_CA_khi_role_bi_bo_sot`). Không
đụng carve-out chuyên biệt (bất biến #5) — gate chỉ chặn đường generic. Đổi
taxonomy/prompt dạy `result_ownership` (`analyze.md`/`classify.md`) →
**targeted live**, đã kèm `CACHE_VERSION` 9→10.

### `simulation/mechanisms.py` (M15) · Change impact: offline (targeted live nếu đổi `analyze_exposed_values()`/`LEGACY_ALIASES`)
Taxonomy cơ chế **canonical namespaced** (`family.mechanism`) — nguồn DUY NHẤT
cho mọi so sánh cơ chế trong pipeline; KHÔNG import `catalog` (chống vòng
import; cross-lock ở test thay vì import).
Exports: `FAMILY_MECHANISMS`, `INTENTIONAL_GAP_MECHANISMS`, `LEGACY_ALIASES`,
`FORMALIZED_FAMILIES`, `canonical_mechanism(raw)`, `mechanism_family(canonical)`,
`analyze_exposed_values()`, `NO_PRESCRIPTION`.
Consumers: `mechanism_gate.py`, `ai/pipeline.py` (`ANALYZE_SCHEMA.prescribed_procedure.enum`
DẪN XUẤT từ `analyze_exposed_values()` — anti-pattern #1), `catalog.py`
(`owned_mechanisms` trên từng `FamilyMembership` phải ∈ `FAMILY_MECHANISMS`).
Tests: `test_mechanisms.py`.
Notes: **Khóa 1** — `canonical_mechanism()` là compatibility boundary DUY NHẤT:
legacy sorting bare id (live-verified M14, vd `"adjacent_compare_swap"`) →
namespaced qua `LEGACY_ALIASES` một chiều; canonical passthrough; `None`/`"none"`
→ `None` (permissive, không ép cơ chế). **Khóa 2** — mọi giá trị analyze-exposed
KHÔNG được sở hữu bởi target nào phải nằm trong `INTENTIONAL_GAP_MECHANISMS`
(gap-trigger khai tường minh, không rơi tự do). `FORMALIZED_FAMILIES` là registry
tiến độ — W1–W5 lần lượt thêm family, W5 (Task 15) đủ 8/8 == `frozenset(FamilyId)`
(kích hoạt lock K1 14/14 owned ≠ rỗng). Đổi `analyze_exposed_values()`/
`LEGACY_ALIASES` → ảnh hưởng enum Gemini thấy ở stage analyze → **targeted live**;
đổi `FAMILY_MECHANISMS`/`INTENTIONAL_GAP_MECHANISMS`/`FORMALIZED_FAMILIES` thuần
nội bộ (không đụng enum LLM) → offline.

### `simulation/mechanism_gate.py` (M14 §E4 + M15 mở rộng) · Change impact: offline
Mechanism-consistency gate: so cơ chế đề **YÊU CẦU** (`analysis.prescribed_procedure`,
chuẩn hoá qua `canonical_mechanism`) với cơ chế family/target **THỰC SỰ SỞ HỮU**
— tín hiệu có cấu trúc, KHÔNG đọc text đề, KHÔNG keyword-patch tên thuật toán.
Exports: `check_mechanism_ownership(analysis, selector)` (tầng 1, TRƯỚC simulate —
selector lifecycle), `check_variant_consistency(analysis, selector, variant_id)`
(tầng 2, SAU khi FamilySpec validate — variant có khớp cơ chế không), (M15)
`check_mechanism_consistency_for_target(analysis, spec)` (lifecycle **direct
route** — không qua selector: so canonical family/mechanism với
`spec.family_memberships[*].owned_mechanisms`; trả `ROUTE_MECHANISM_FAMILY_MISMATCH`
nếu family còn không khớp, `GATE_MECHANISM_OWNERSHIP` nếu family khớp nhưng
mechanism không được sở hữu), `ROUTE_MECHANISM_FAMILY_MISMATCH_MSG` (MỘT nguồn
message, tái dùng ở `ai/pipeline.py::_family_mismatch` — chống nhân đôi chuỗi).
Consumers: `ai/pipeline.py` (`run_pipeline`, `classify_with_one_route_recovery`).
Tests: `test_mechanism_gate.py`, `test_pipeline_mechanism_consistency.py`.
Notes: ranh giới permissive vs fail-closed — `prescribed ∈ {null, "none"}` →
KHÔNG ép cơ chế (vắng tín hiệu ≠ bằng chứng cơ chế ngoài phạm vi);
`prescribed ∈ owned` → qua; `prescribed ∉ owned` → gap/mismatch thật. M15 thêm
HAI mã lỗi tách bạch cho lifecycle direct-route: mismatch cross-family
(`ROUTE_MECHANISM_FAMILY_MISMATCH`) không bao giờ đi tới `stage_simulate` trên
target mâu thuẫn — `run_pipeline` reclassify **bounded đúng 1 lượt**
(`classify_with_one_route_recovery`) trước khi mọi route-dependent gate khác chạy.

### `simulation/dsl/validator.py` · Change impact: offline
Validator SimulationSpec (allowlist/limits **dẫn xuất từ manifest**), drag
constraints, ownership rule, cấm chu trình parent/rule; (M11) **cấm hai rule
cùng ghi một target** — với đánh giá điểm bất động, rule sau trong mảng thắng
mỗi vòng quét → ngữ nghĩa phụ thuộc thứ tự khai báo.
Exports: `validate_generic_config`, `ownership_conflict`, các hằng allowlist.
Tests: `test_dsl.py`, `test_manifest.py`. Mirror TS: `generic/validate.ts`.

### `simulation/representation.py` · Change impact: offline
Plan tất định + **capability gate** + scene_mode.
Exports: `required_roles`, `build_representation_plan`, `scene_mode_guidance`,
`check_scene_consistency`. Tests: `test_representation.py`.

### `simulation/semantic.py` · Change impact: offline
Cổng hai: `check_semantic_compatibility` (gap/mismatch) + `check_semantic` (kỳ
vọng hành vi cho harness: boolean_gate/weighted_sum/moving_path/progressive_reveal/
static_structural/draggable_reveal/**nested_boolean** (M11)). Exports: cả hai +
`roles_covered_by_spec`. Tests: `test_semantic.py`.
Notes (M11): `nested_boolean` chấm boolean HỢP THÀNH (≥2 rule nối chuỗi, đúng 1
sink) — dò bảng chân trị bằng cách tiêm vào **đầu vào toggle của học sinh**,
KHÔNG tiêm vào input của rule (input có thể là target rule khác, bị `values_of`
tính đè → âm tính giả — đúng lỗi của probe `boolean_gate` với spec lồng) và
KHÔNG đếm object trang trí có `value` (đo live: 7 "nguồn" giả). Ánh xạ
nguồn↔biến kỳ vọng là id-agnostic (thử hoán vị). `check_semantic` chỉ chạy ở
HARNESS — pipeline production không chấm bảng chân trị.

### `simulation/generic_engine.py` · Change impact: offline
Port Python của engine TS — **chỉ để kiểm ngữ nghĩa server-side**.
Exports: `values_of`, `initial_base`, `build_timeline`, `apply_toggle`,
`rule_targets`, (M13) `GenericEvaluationError`.
Notes: phải giữ **cùng luật** với `generic/model.ts`. M13 §3.4: `values_of` là
**forward-resolve trên DAG ba trạng thái** — KHÔNG còn seed target = 0; rule chỉ
chạy khi mọi input đã resolve; input còn thiếu sau ≤ `len(rules)` lượt (không
tiến triển nữa) → ném `GenericEvaluationError` thay vì hoá 0 im lặng. 4 mã lỗi:
`invalid_numeric_source` · `missing_weight` · `unresolved_dependency_after_bound` ·
`non_finite_numeric_value`. `run_gates` (patterns.py) đã bọc `values_of` trong
try/except từ trước → lỗi tự động thành reject, không cần sửa `run_gates`. Bug đã
vá trong lúc viết plan (không phải trong code cuối): thứ tự cập nhật `pending`
PHẢI đứng TRƯỚC check `break`, nếu không mọi spec có ≥ 1 rule sẽ bị raise oan —
xem cảnh báo ở `docs/superpowers/plans/2026-07-16-m13-generic-semantic-soundness.md`
Task 4. Tests: `test_generic_engine_m13.py` (mới) + `test_semantic.py` (M11
canary chuỗi đảo thứ tự vẫn đúng giá trị — bằng chứng ngữ nghĩa KHÔNG đổi cho
spec hợp lệ).

### `scripts/generate_dsl_contract.py` → `frontend/src/simulations/domains/generic/dsl-contract.json` (M13) · Change impact: offline
Generator chạy TAY (không phải build step tự động): đọc
`manifest.dsl_semantic_contract()`, ghi ra JSON committed mà frontend import
trực tiếp (`import dslContract from "./dsl-contract.json"`). Cách chạy: `cd
backend && .venv/Scripts/python scripts/generate_dsl_contract.py`. **KHÔNG sửa
tay `dsl-contract.json`** — sửa = sửa `manifest.py` rồi chạy lại generator.
Sync-lock test (`test_manifest_providers.py::test_dsl_contract_json_khong_troi_khoi_manifest`)
so sánh file committed với `dsl_semantic_contract()` hiện tại — quên chạy
generator sau khi đổi manifest → test ĐỎ (anti-pattern #1: allowlist song song
lệch tay). Đây là artifact JSON DUY NHẤT của repo được sinh thủ công và commit
thẳng; không có CI job tự regenerate.

### `simulation/scan_engine.py` (M12) · Change impact: offline
Port Python của scan-interpreter — mirror `frontend/src/core/scan.ts` (CÙNG
LUẬT, đổi một bên thì đổi cả hai). Backend không dựng timeline cho học sinh;
port tồn tại để validator server-side + harness chấm HÀNH VI (semantic kind
`bounded_scan`). Exports: `validate_scan_spec`, `run_scan`, `SCAN_VERSION`,
`CONDITION_OPS`, `UPDATE_KINDS`, `MARKINGS`, `STOPS` (hằng public — schema
Gemini trong catalog DẪN XUẤT từ đây, khoá bằng
`test_scan_routing::test_scan_schema_enum_dan_xuat_tu_scan_engine`).
Tests: `test_scan_engine.py`, `test_scan_routing.py`.

### `simulation/character_encoding.py` (M17 W3) · Change impact: targeted live
NGUỒN DUY NHẤT của từ vựng + giới hạn mã hoá ký tự. Exports: `SPEC_VERSION`
("charenc-1.0"), `ENCODINGS` (ascii | unicode_codepoint), `MAX_TEXT_CODE_POINTS`
(12), `ASCII_MAX`, `BMP_MAX` (65535 — trùng `CONV_MAX_VALUE`), `SURROGATE_MIN/MAX`,
`FORBIDDEN_SPEC_KEYS`, `encoding_enum()`, `code_point_out_of_range()` (một nguồn
cho cả kiểm định lẫn thông điệp từ chối).
Consumers: `catalog.py` (schema DẪN XUẤT), `validation/character_encoding.py`.
Notes: **backend KHÔNG có engine mã hoá và KHÔNG có bộ chuyển số sang nhị phân** —
`ord()` chỉ dùng kiểm khoảng. Thực thi nằm ở FE.

### `validation/character_encoding.py` (M17 W3) · Change impact: offline
Validator FAIL-CLOSED: `validate_character_encoding_config(raw) → (config|None, error|None)`.
Bắt: encoding ngoài enum · text không phải chuỗi (số 7 ≠ ký tự '7') · rỗng · quá
12 **code point** · ngoài ASCII ở chế độ ascii · ngoài BMP · surrogate · trường
thừa · spec mang kết quả (R0). KHÔNG coercion, KHÔNG thay ký tự bằng `e`/`?`.
Tests: `test_character_encoding.py` (gồm test khoá "backend không có engine").

### `core`/`domains/binary/encoding-module.tsx` (M17 W3) · offline
**Engine tất định + module** của `binary.character_encoding`. Exports:
`CHAR_ENC_VERSION`, `CHAR_ENCODINGS`, `codePointsOf`, `validateCharEncodingSpec`,
`runCharacterEncoding(spec) → {trace, rows}`, `committedRowCount`, `partialRow`,
`makeCharEncodingModule`, `CharEncodingWorkspace`, `CharEncodingInspector`.
**Nhị phân lấy từ `toBase()` của `convert-module.tsx`** — không có converter thứ
hai, không tự đặt quy ước đệm. Duyệt **theo code point** (`Array.from` +
`codePointAt`), KHÔNG dùng `text.length`/`charCodeAt` (nếu dùng thì emoji thành
hai ký tự BMP "hợp lệ" ⇒ lệch backend). 4 phase mỗi ký tự (chọn → tra mã → đổi
nhị phân → chốt hàng) nuôi progressive reveal. Đăng ký ở `registerBinaryDomain()`.
Tests: `encoding-module.test.tsx`.

### `simulation/program_spec.py` (M17 W2C) · Change impact: targeted live
**NGUỒN DUY NHẤT** của ngữ pháp + giới hạn luồng điều khiển hữu hạn. Exports:
`SPEC_VERSION` ("program-1.0"), `VALUE_TYPES`, `STATEMENT_KINDS`,
`EXPRESSION_KINDS`, `ARITHMETIC_OPS`/`COMPARE_OPS`/`LOGIC_OPS`/`UNARY_OPS`,
`LIMITS` (7 giới hạn cứng), `INT_MIN`/`INT_MAX`, `COMPLETION_*`,
`FORBIDDEN_SPEC_KEYS`, `structures_present(config)`, `statement_kind_enum()`,
`expression_kind_enum()`, `all_operators()`.
`normalize_inline_program(statements)` (W2C-C1 §L2) — biểu thức INLINE của LLM →
bảng biểu thức NỘI BỘ + câu lệnh tham chiếu id; TẤT ĐỊNH (id `_e1.._en` theo thứ
tự duyệt), KHÔNG đoán ý/bù toán tử/sửa tên biến. Sai ngữ pháp → `NormalizeError`.
Đây là chuẩn hoá CẤU TRÚC, KHÔNG phải repair.
Consumers: `catalog.py` (schema Gemini DẪN XUẤT — anti-pattern #1),
`validation/program.py`, `pipeline_stages.py`. Mirror TS: `frontend/src/core/program.ts`
(`PROGRAM_LIMITS` — đổi một bên PHẢI đổi bên kia).
Tests: `test_program_spec.py`. Notes: ĐÂY KHÔNG PHẢI trình thông dịch Python;
thêm loại câu lệnh/biểu thức = mở rộng ngữ pháp ⇒ phải qua scope guard §3.

### `validation/program.py` (M17 W2C) · Change impact: offline
Validator FAIL-CLOSED cho `algorithm.bounded_control_flow`. Exports:
`validate_program_config(raw) → (config|None, error|None)`.
Bắt: kind ngoài ngữ pháp · biến chưa khai báo · sai kiểu (KHÔNG coercion) ·
chia/mod cho 0 tĩnh · điều kiện không phải boolean · while thiếu `max_iterations` ·
**definite-assignment** (W2C-C1 §L1: đọc biến chưa chắc có giá trị → từ chối;
if/else = GIAO hai nhánh, if-không-else và while KHÔNG mở rộng) ·
biểu thức lồng vòng/quá sâu · câu lệnh mồ côi hoặc thuộc hai khối · spec mang
kết quả (R0). Deps: `program_spec`. Tests: `test_program_spec.py`.

### `simulation/catalog.py` · Change impact: targeted live
Bản chiếu registry phía backend: `SimSpec` (description/schema/contract/validator/
make_title) cho từng `simulation_id`. Exports: `CATALOG`, `SimSpec`, `catalog_text`,
(M14) `llm_choices()` (menu classify — ẩn concrete member của một family sau
selector token), (M14/M15) mỗi `SimSpec.family_memberships: tuple[FamilyMembership, ...]`
(`descriptor.py`) mang `owned_mechanisms` (M15, canonical — xem `mechanisms.py`) +
`config_contract_version` (descriptor-level, KHÔNG vào envelope, KHÔNG Alembic).
Notes: `_GENERIC_SCHEMA` enum **phải** dẫn xuất từ manifest (anti-pattern #1).
Enum `simulation_id` của classify (`_classify_schema`) DẪN XUẤT từ `CATALOG.keys()`
→ thêm entry vào CATALOG là ĐỦ để classify được phép trả id đó (M10-AI-ROUTE:
`network.protocol_encapsulation`). Hai module network phân biệt bằng **description**
(biến đổi PDU qua TẦNG ↔ đường đi qua NÚT), không keyword hard-code trong runtime.
Đổi menu classify → **bump `CACHE_VERSION`** ở `main.py`.
M15 W2–W5 khai `owned_mechanisms` đủ 14/14 entry (K1 lock) qua 4 conformance-proof
test riêng theo family: `test_scan_conformance.py` (W2 — `algorithm.scan` +
4 scan oracle, KHÔNG selector, scan = catch-all trong-family), `test_boolean_dual_surface.py`
(W3 — `logic.and_gate` sở hữu `single_gate_truth_table`, `generic.rule_scene` sở
hữu `composed_rule_dag`, hai bề mặt KHÔNG hợp nhất), `test_network_ownership.py`
(W4 — `network.packet_routing` sở hữu `unweighted_hop_bfs` + `known_gaps` máy-đọc
ghi Dijkstra; `network.protocol_encapsulation` sở hữu `encapsulate_decapsulate_4layer`),
`test_generic_representation_authority.py` (W5 — membership
`structural_progressive_representation` của `generic.rule_scene` owned DẪN XUẤT
từ `manifest.process_types()`, tách bạch khỏi membership `boolean_composition`
bằng `ResultAuthority` khác nhau — computation vs representation; pin bất biến
#21 làm lock của family này). `capability-descriptors.json` (sinh từ
`CATALOG`/`descriptor.py`, cross-lock FE test-only) phải regenerate mỗi khi
đổi `family_memberships`.

### `simulation/coverage.py` (M14 §O) · Change impact: offline
Curriculum coverage matrix — machine-readable, enum ĐÓNG `CoverageStatus`
{SUPPORTED/PARTIAL/PILOT/CAPABILITY_GAP/OUT_OF_SCOPE}, curate từ `COVERAGE.md`
§3/§7/§7b. KHÔNG claim phủ toàn chương trình; gap/out-of-scope khai trung thực.
Exports: `KNOWLEDGE_UNITS`, `KnowledgeUnit` (frozen dataclass), `CoverageStatus`,
`coverage_rows()`. Tests: `test_coverage_matrix.py`.

**W4B-3A — TRỤC THỨ HAI `SupportKind`** {SUPPORTED_INTERACTIVE / SUPPORTED_TRACE /
SUPPORTED_BOUNDED_ARTIFACT / SUPPORTED_EXPLANATION / PARTIAL / UNSUPPORTED /
NOT_SIMULATION_SUITABLE} + `support_evidence` (bắt buộc, nói rõ ĐO ĐƯỢC hay chỉ
KHAI BÁO) + `curriculum_support_rows()`. Vì sao cần trục thứ hai: `CoverageStatus`
trả lời *"đã ship tới đâu"*, nên một mục chỉ-bấm-Tiến-để-xem và một mục học sinh
đổi được mô hình hiện **giống hệt nhau** là `SUPPORTED`. Ràng buộc chéo có test:
`OUT_OF_SCOPE ⇔ NOT_SIMULATION_SUITABLE`, `CAPABILITY_GAP ⇒ UNSUPPORTED`, và một
test canh nhãn `CURRICULUM_SUPPORT_PARTIAL` — nó chỉ được gỡ khi KHÔNG còn unit
in-scope nào PARTIAL/UNSUPPORTED. Báo cáo:
`scripts/curriculum_support_report.py`.

### `backend/scripts/curriculum_support_report.py` · Change impact: offline
W4B-3A — bảng hướng GIÁO VIÊN (mỗi đơn vị kiến thức được hỗ trợ tới đâu và theo
KIỂU nào), sinh từ `coverage.py`. Khác `catalog_runtime_matrix.py` (hướng kĩ sư)
và khác `after-matrix` (hướng sản phẩm, theo target). Cờ `--json/--md`. Artifact:
`docs/evaluation/m17/w4b3a-after/curriculum-support.{json,md}`.

### `frontend/scripts/after-matrix-w4b3a.mjs` · Change impact: offline (cần `npm run dev`)
W4B-3A — MA TRẬN AFTER cho **toàn bộ** danh mục: ghép ba nguồn (descriptor sinh
từ registry + module frontend đang chạy qua CDP + `measure-1920.json`). Phân loại
trải nghiệm bằng luật KHAI TRƯỚC ở đầu file; **đếm tổng chỉ sau khi có bảng từng
target**. Tách bạch ĐO ĐƯỢC ↔ CHỈ KHAI BÁO (9/23 target chưa có bài mẫu offline
nên không dựng được state để đo) — cộng hai cột lại là tự cho điểm cao hơn bằng
chứng. Ba phép suy BỊ CẤM ghi ngay trong file: `predict` ⇒ thao tác trực tiếp ·
`timeline` ⇒ mô hình tương tác · có trong catalog ⇒ có phủ chương trình.
Artifact: `docs/evaluation/m17/w4b3a-after/after-matrix.{json,md}`.
Notes (M15 Task 16): `sorting` tốt nghiệp `PILOT` → `SUPPORTED` sau formalize
thành family selector (M14) + conformance proof (M15) — note tự giới hạn claim
(live n=4 M14 + n=2 M15 W1 — đếm case live chạm sorting gồm cả near-miss từ
chối đúng — là **targeted acceptance, KHÔNG phải bằng chứng thống kê**, không
được nói mạnh hơn). `binary_system` note bổ sung control cơ
số ≠ 2 (M15 W1: hex/octal → `capability_gap` có 2 lớp phòng thủ, xem
`mechanism_gate.py`).

### `domains/web/props.ts` — miền màu (M20 W5 · W5A) · Change impact: targeted live
Khai `WebProp` + `COLOR_CHOICES`/`TEXT_COLOR_CHOICES` (ô GỢI Ý) và RE-EXPORT
phép toán màu từ `simulations/color-channels.ts`.
⚠️ W5A ĐÃ DỜI chủ sở hữu: `rgbOf`/`hexOf`/`rgbTextOf`/`HEX_COLOR` không còn
định nghĩa ở đây. Lý do — `color.rgb_model` cần đúng những con số ấy, và một
miền import từ miền khác sẽ đảo hướng phụ thuộc `domains/* ← shared`. Re-export
giữ mọi nơi đang import khỏi phải đổi, và giữ đúng MỘT bản của phép toán.
W5 nới miền màu từ BẢY ô đóng sang mọi mã hex 6 chữ số (mirror
`_WEB_HEX_COLOR` bên `validation/simulation.py`). ⚠️ Nới thế KHÔNG nới ranh giới
an toàn: tập hợp lệ vẫn chỉ chứa MỘT MÀU, không hàm, không `url()`, không dấu
chấm phẩy thoát ra khai báo khác. Nới tiếp sang tên màu / hàm màu / biến CSS sẽ
mở đúng cánh cửa tập đóng đang giữ. `COLOR_CHOICES`/`TEXT_COLOR_CHOICES` nay là
ô GỢI Ý, không còn là miền.

### `domains/web/apply.ts::applyChannelChange` (M20 W5) · offline
Đổi MỘT kênh, giữ hai kênh kia — thao tác §2A đòi hỏi. Kênh tác động lên màu của
nút ĐANG CHỌN (`colorPropOf`), nên "chọn Tiêu đề rồi kéo R" không bao giờ chạm
tới nền: chỉ có một `selected` trong state, không có bộ chọn thứ hai để lệch.
Ngoài miền ⇒ `null` ⇒ giữ state cũ, KHÔNG kẹp về biên.

### `frontend/src/simulations/transport-policy.ts` (M20 W7) · Change impact: offline
NGUỒN DUY NHẤT của chế độ transport: `FULL_TRACE` · `OPTIONAL_TRACE` ·
`RESET_ONLY`, khai cho cả 23 target kèm LÝ DO CƠ CHẾ. `SimulationControls` đọc
nó; `experience-manifest.test.ts` import lại từ đây thay vì giữ bản thứ hai.
⚠️ `transportModeOf` trả `null` cho target chưa khai — KHÔNG có mặc định. Trước
W7, dải điều khiển phân loại bằng `timeline.stepCount(state) > 1`, đúng kiểu suy
diễn kĩ thuật §9 cấm: `base_conversion` có 12 bước nên được dòng thời gian đầy
đủ, dù sau W5 kết quả của nó đọc được ngay. Số hiện tại: **13 / 7 / 3**.

### `frontend/scripts/certify-experience-w12.mjs` (M20 W12) · offline (cần `npm run dev`)
Hỏi: **ĐÓNG thử thách rồi, học sinh làm được gì có nghĩa trên màn này?** — tầng
thứ ba, khác hai tầng đã có: `interaction-semantics.test.ts` hỏi *module nhận
action gì* (hợp đồng), `certify-viewports-w12.mjs` hỏi *affordance có thấy được
không* (bề mặt).
Phân loại: đổi được đầu vào ⇒ `TOOL_PASS` · không đổi được nhưng tua THAY THẾ ⇒
`TRACE_PASS` · không đổi được và tua chỉ THÊM DỒN ⇒ **`EXPERIENCE_FAIL`**.
⚠️ "Tua thì màn hình đổi" KHÔNG phân biệt được gì — trình chiếu cũng đổi. Nên
phép đo tách **thêm dồn** (bước sau chứa trọn bước trước = bảng in dần từng
dòng, đáp án có sẵn) khỏi **thay thế** (giá trị bị đổi, vùng xét co lại = cơ chế
đang chạy).
⚠️ Ứng viên action sinh từ config, và hình dạng phải ĐỌC `simulations/types.ts`:
đoán `whatif_swap {from,to}` / `toggle {id}` thì action bị **nuốt lặng lẽ** và
`find_max` đọc ra TRACE_PASS trong khi nó là công cụ — đoán sai ở đây luôn đánh
giá THẤP sản phẩm. Hợp đồng thật: `{i,j}` · `{target}` · `{a,b}`.
⚠️ PHÉP ĐO NÀY ĐÃ SAI BỐN LẦN, và **cả bốn lần đều đánh giá THẤP sản phẩm** —
ghi lại để lần sau không lặp:
1. So `st.cursor` (không tồn tại ở tầng store) ⇒ mọi vòng lặp thoát ngay bước
   đầu, báo "1 bước" cho cả 23 target.
2. Đoán hình dạng action (`whatif_swap {from,to}`, `toggle {id}`) ⇒ action bị
   **nuốt lặng lẽ**. Hợp đồng thật ở `simulations/types.ts`: `{i,j}`, `{target}`.
3. Đoán TÊN action theo TÊN field config: `decimal_to_binary` khai
   `decimalValue` nhưng `apply` nhận `set_param {name:'decimal'}` — đọc ra
   `STATIC_ILLUSTRATION` cho một bài mà `narrate` nói thẳng "bấm từng bit".
4. Chỉ đo CHỮ trong `.sim-stage` ⇒ mất hai thứ: dải quan sát
   (`.search-observe` là ANH EM của `.sim-stage`, và chính nó đổi theo bước) và
   MÀU (`ScanWorkspace` chỉ vẽ `ArrayView` — cột nào đang xét mã bằng `fill`).
   Cho ra "13 bước engine, 1 bước màn", một kết luận sai về sản phẩm.
Nay dấu vân = chữ CẢ THẺ (trừ đồ đạc) + `fill`/`class` của mọi phần tử SVG.
Vẫn KHÔNG bắt được vị trí/kích thước — giới hạn, không phải đã phủ.
Số hiện tại: **20 TOOL_PASS · 3 TRACE_PASS · 0 EXPERIENCE_FAIL**. Chênh
engine/màn còn lại (40→14, 33→14…) là trần 14 bước của vòng lặp, không phải lỗi.

### `frontend/scripts/faultcheck-visual-weight-w12.mjs` (M20 W12) · offline (cần `npm run dev`)
Chứng minh `certify-visual-weight-w12.mjs` **còn đỏ được**. Phép đo ấy đã bị NỚI
ba lần để nhìn thấy `<canvas>`, DOM thật, rồi `.encap-layer` — mỗi lần nới là
một lần dễ xanh hơn, nên con số 23/23 chưa đáng tin cho tới khi có đối chứng.
Ba nhánh: giấu khối cơ chế thật ⇒ **ĐỎ** · phình vỏ rỗng `.encap-2d` ⇒
**KHÔNG được xanh** · nguyên trạng ⇒ **XANH**. Mỗi nhánh chứng minh
`MUTATION_OBSERVED` trước khi phán — phép tiêm không chạm đối tượng thì kết quả
của nó vô nghĩa.
Số hiện tại: **3/3 đúng kì vọng** (nguyên trạng ink 0,39 · 8 chủ sở hữu).

### `frontend/scripts/certify-visual-weight-w12.mjs` (M20 W12) · offline (cần `npm run dev`)
Hỏi câu mà MỌI tiêu chí W12 khác bỏ sót: **trên sân khấu, HÌNH chiếm bao nhiêu
so với CHỮ?** Các tiêu chí trước chỉ hỏi "đổi đầu vào thì kết quả có tính lại
không" — nên `network.packet_routing` (4 biểu tượng đứng yên + 4 bước chữ) đạt
hết, trong khi mở ra nhìn thì nó là hình minh hoạ có chú thích.
Đo `inkShare` (diện tích svg/canvas/`.web-page` trên diện tích thẻ) và
`proseChars` (chỉ khối văn xuôi; KHÔNG tính nhãn trong hình, KHÔNG tính ô bảng
— bảng LÀ kết quả engine, phạt nó là phạt nhầm). Bài có bảng được miễn ngưỡng
`inkShare`, và điều đó ghi rõ chứ không miễn lặng lẽ.
⚠️ Ngưỡng `MIN_GLYPHS` của bản đầu ĐÃ GỠ vì nó SAI hai đường: đo kích thước dữ
liệu (dãy 3 phần tử có 5 hình chữ nhật) và không nhìn được vào `<canvas>` — nó
vừa gán "tranh tĩnh" cho cảnh 3D thật. `glyphs` còn trong artifact để đọc.
⚠️ Đo BỀ MẶT, không đo hiểu biết — `LEARNER_IMPACT_NOT_EVALUATED` giữ nguyên.
⚠️ Hai ngoại lệ, cả hai đều KIỂM NGƯỢC được nên không nuốt được luật: bài có
`<table>` (bảng là kết quả engine) và `CODE_IS_THE_MECHANISM`
(`bounded_control_flow` — sân khấu là mã giả có con trỏ dòng, như trình gỡ lỗi;
vẽ thêm hình ở đó là trang trí). Khai "mã là cơ chế" mà lại nhiều hình ⇒ ĐỎ.
Số hiện tại: **23/23 lấy HÌNH làm chính**.

### `frontend/scripts/certify-scroll-w12.mjs` (M20 W12) · offline (cần `npm run dev`)
Hỏi: vỏ ứng dụng có đọc thành MỘT khối liền, và máng cuộn có ổn định không?
5 màn × 4 bề rộng trên `browser-runner.mjs`: home · library · history ·
workspace gọn · workspace rất dài — cố ý phủ cả trang KHÔNG cuộn lẫn trang cuộn.
Khẳng định: header trải hết bề rộng vỏ · máng đúng bằng bề rộng thanh cuộn đã
khai (10px) · không tràn ngang · **máng giống nhau giữa trang ngắn và trang
dài** (không nhảy ngang — phép so này mới là câu hỏi thật; đo một màn thì không
bao giờ phát hiện được nhảy).
⚠️ KHÔNG đo được thumb có nhìn thấy hay không: CDP không đọc computed style của
`::-webkit-scrollbar-thumb`. Việc đó do `styles/scrollbar-ownership.test.ts`
khoá ở mức mã nguồn — ranh giới này ghi thẳng vào artifact, không để một con số
trông-như-đã-phủ.
⚠️ KHÔNG đảo quyết định W4B-1A (cuộn thuộc về TÀI LIỆU, không phải panel): vùng
cuộn nội bộ từng giấu 170px nội dung học mà không có tín hiệu ở mức trang.

### `frontend/src/simulations/action-probe.ts` (M20 W12) · Change impact: offline
NGUỒN DUY NHẤT của câu "học sinh có đường nào đổi đầu vào bài này không".
`candidateActions(config)` dẫn ứng viên từ config đã validate; dùng bởi CẢ
`experience-gate.test.ts` (offline, <1s) lẫn `scripts/certify-experience-w12.mjs`
(trình duyệt, qua `session.mods.probe`).
⚠️ TÊN ACTION KHÔNG SUY ĐƯỢC TỪ TÊN FIELD CONFIG — nó nằm trong `module.apply`.
Đã sai ba lần trong W12 và **cả ba đều đánh giá THẤP sản phẩm**, vì action sai
hình dạng không ném lỗi mà bị `apply` trả về state cũ, đọc y hệt "bài này không
tương tác được": `whatif_swap {from,to}`→`{i,j}` · `toggle {id}`→`{target}` ·
`set_param 'decimalValue'`→`'decimal'`. Thêm target mới thì MỞ MODULE RA ĐỌC.

### `frontend/src/simulations/experience-gate.test.ts` (M20 W12) · cổng offline
Hỏi câu tối thiểu một mô phỏng phải trả lời được: có ít nhất MỘT action đổi được
state, HOẶC một dòng thời gian > 1 bước. Không có cả hai ⇒ **một bức hình**.
Chạy trong vitest nên nó có mặt lúc ai đó thêm target mới; bản chứng nhận trình
duyệt đầy đủ hơn nhưng cần Chrome và vài phút.
⚠️ Cổng này KHÔNG nhìn bề mặt ⇒ không phân biệt được "trace có mà không hiện".
Có đối chứng dương (module đồng nhất không timeline) + guard chống bộ dò rỗng.

### `frontend/src/simulations/tool-affordance.ts` (M20 W12) · Change impact: offline
NGUỒN DUY NHẤT của câu hỏi "công cụ thao tác của học sinh có được hiện ra
không". `toolAffordanceOpen({exploreOpen, challengeOpen, busy})` — hàm THUẦN,
kiểm được không cần Chrome. Cả `domains/algorithm/ui.tsx` (kéo cột) và
`domains/network/ui.tsx` (ngắt/nối liên kết) đọc nó.
⚠️ Trước W12 hai miền chép tay CÙNG một luật (`exploreOpen && !busy`), nên công
cụ nằm sau một nút học sinh phải tự biết bấm: đo trên trình duyệt được **52/92**
dòng ma trận bề rộng "không có affordance". Luật nay là W12 §6 Policy B — thử
thách ĐÓNG thì công cụ dùng được; MỞ thì có thể siết để câu hỏi đang chờ không
bị chính học sinh vô hiệu hoá. `mode: "hidden"` của `interaction-policy.ts` vẫn
thắng tuyệt đối (kéo ở `sum_if`/`count_if` là trang trí).
⚠️ Bật affordance KHÔNG nâng hạng ngữ nghĩa: `whatif_swap` vẫn là
INPUT_MANIPULATION (W12 §8) — phân loại thuộc `interaction-semantics.test.ts`.

### `frontend/src/simulations/explore-vs-trace-w5e.test.ts` (W5E) · offline
Khoá luật Phase E: **KHÁM PHÁ = trạng thái hiện tại đầy đủ · TRACE = tiêu điểm
giải thích**. Con trỏ được chọn *kể tới đâu*, KHÔNG được biến một giá trị engine
đã tính thành "chưa biết" sau khi học sinh vừa hỏi.
⚠️ Phép đo là đối chiếu KHAI BÁO ↔ HÀNH VI: target khai `OPTIONAL_TRACE` tức hứa
"kết quả đọc được ngay" ⇒ sau một thao tác, thuyết minh không được còn nói "chưa
biết". KHÔNG quét bằng "con trỏ có về 0 không" — bản đầu quét thế và bắt NHẦM 5
target (`sum_if`/`count_if`/`base_conversion`/`character_encoding`/
`relational_table_query`) vốn đọc được kết quả ngay ở bước 0.
⚠️ `registerAllSimulations()` gọi ở TẦNG MODULE, không ở `beforeEach`:
`it.each(targets())` dựng lúc THU THẬP nên registry rỗng lúc ấy sinh ĐÚNG 0 ca mà
vẫn báo xanh (đã bị đúng một lần trong chính wave này).
⚠️ `NO_SHELL_NARRATION` = target không dùng khe thuyết minh shell nên phép đo đọc
không được; chỉ được NGẮN ĐI.
⚠️ Ca `logic.boolean_dag` ĐÃ ĐÓNG: xem `BoolDagState.exploreReveal` bên dưới.

### `domains/logic/dag-module.tsx::BoolDagState.exploreReveal` (W5E) · offline
Tách hai tín hiệu vốn cùng đọc mỗi `cursor`. Lỗi gốc: `apply` trả
`initFromValues(...)` vốn đặt `cursor: 0`, nên bật một đầu vào — thao tác Khám
phá DUY NHẤT của bài — đẩy cả mạch về `?` dù `nodeOutputs` lúc ấy đã giữ trọn
đáp án tất định.
Nay toggle đặt `cursor = steps.length - 1` (SÂN KHẤU trả lời câu vừa hỏi) và
`exploreReveal = true`; `goToStep` luôn đưa cờ về `false`.
⚠️ **VIỆC DUY NHẤT của cờ là GIỮ BẢNG CHÂN TRỊ ĐÓNG** — học sinh mới hỏi về MỘT
bộ đầu vào, mở cả 2^n hàng là tiết lộ những bộ chưa hỏi (chủ ý hé lộ dần, audit
2026-08-03 + `DESIGN_BRIEF §3.3`). Sân khấu KHÔNG cần cờ: con trỏ ở bước cuối đã
làm `evaluated` chứa mọi cổng. Bản đầu có thêm nhánh `exploreReveal` trong
`valueOf` và TIÊM LỖI chứng minh nó là mã CHẾT (gỡ đi, không test nào đỏ) — đừng
thêm lại.
Khoá bởi `dag.test.tsx` hai test `W5E — …` (kèm phân loại ba khẳng định cũ
thành OLD_PRODUCT_CONTRACT / STILL_VALID_INVARIANT). Tiêm lỗi đã chạy: bảng mở
theo toggle ⇒ ĐỎ · cờ không bật ⇒ ĐỎ.

### `frontend/src/simulations/state-text-consistency-w5n.test.ts` (W5N) · offline
Phase N phần KIỂM ĐƯỢC OFFLINE. Khoá ca đã SHIP HAI LẦN (`ddb24f1`): bề mặt đọc
CONFIG GỐC của đề thay vì STATE của engine, nên học sinh chọn ">" mà ô chọn nhảy
về ">=" và bị chấm theo giá trị không nhìn thấy được. Kiểm: sau `set_param`,
`state.config` (thứ engine THẬT SỰ chấm) mang ngưỡng MỚI, còn config gốc của
envelope KHÔNG bị ghi đè (nó là mốc cho `specDrift`).
⚠️ **KHÔNG có phép quét "một bất biến cho cả 24" — đã thử HAI lần, cả hai bắt
nhầm**, và lý do ghi đầy đủ trong file: (1) "thuyết minh phải đổi" sai vì thuyết
minh mô tả BƯỚC HIỆN TẠI (đổi "Tin"→"Tina" thì bước 0 vẫn là ký tự T); (2)
"`currentConfig` phải đổi" sai vì `whatif_swap` tạo NHÁNH thử nghiệm — đề chưa
bị sửa nên `currentConfig` đứng yên là ĐÚNG, nếu không `specDrift` kêu oan mỗi
lần kéo thử. Quan hệ thao-tác ↔ config khác nhau theo miền một cách chính đáng.
⚠️ Phần còn lại của Phase N (`WRONG_HIGHLIGHT`, `WRONG_LEGEND`,
`WRONG_SELECTED_STATE`) sống trong SVG ⇒ CHỈ đo được bằng `certify-*.mjs` trên
Chrome. Đừng dựng phép quét rộng rồi cấy ngoại lệ cho tới lúc nó hết nghĩa.
Tiêm lỗi đã chạy: cho `set_param` giữ ngưỡng cũ ⇒ ĐỎ 2/4.

### `frontend/scripts/e2e-stack-production.mjs` (vNext) · **TIÊU QUOTA THẬT**

E2E đường NGƯỜI DÙNG: gõ đề vào `.composer-text`, bấm `.composer-send`, chờ HTTP
`/api/analyze` thật, rồi bấm `button[title="Tiến một bước"]`. **Không**
`loadEnvelope`, không fixture, không sample offline — đó là ranh giới với
`capture-stack-vnext.mjs` bên dưới, thứ chỉ là bằng chứng COMPONENT.

Chộp response `/api/analyze` qua `page.on("response")` làm nguồn sự thật cho
"route nào đã phục vụ" (`simulation_id` / `source`), vì UI không hiển thị điều
đó. Kết quả: `docs/evaluation/semantic-vnext/e2e/`.

⚠️ Mỗi lượt là một request phân tích thật (nhiều lượt LLM phía backend) và tiêu
một lượt dùng thử của khách. Cần `SEMANTIC_ROUTE_MODE=serve` ở container thì
route sinh mới chạy. Backend chạy uvicorn KHÔNG reload dù `app/` được bind-mount
⇒ sửa mã Python xong phải `docker compose restart backend`, nếu không đo phải
bản cũ trong bộ nhớ.

### `frontend/scripts/certify-transport-vnext.mjs` (vNext) · cần dev server + Playwright

Sở hữu tầng bằng chứng **transport qua CONTROL THẬT**: bấm đúng nút "Sau"/"Trước"
trên trang rồi hỏi *màn hình có đổi không*. Ranh giới với `learner-gate.test.ts`:
test đó gọi `mod.timeline` TRỰC TIẾP nên chứng minh hợp đồng ở tầng engine, không
chứng minh nút bấm nối được vào engine — đúng khoảng trống mà sự cố `main.py`
quên `semantic_route` đã phơi ra (mảnh nào cũng xanh mà chưa mảnh nào được ghép).

Dùng **bài mẫu offline** (`data/samples.ts`) nên **0 gọi `/api`, 0 quota, không
inject store** — người dùng chọn bài, bấm nút, trạng thái đổi thật.

Hai điều kiện của anti-pattern #14 đều có: **dấu vân tay trang** (đúng bài + >1
bước, sai thì thoát != 0) và **`--faultcheck`** (chặn sự kiện nút "Sau" ⇒ bản
soát phải TỤT ĐIỂM). Chạy: `node scripts/certify-transport-vnext.mjs --port 3177
[--faultcheck]`.

### `frontend/scripts/certify-transport-vnext.mjs` (vNext) · cần dev server + Playwright

Sở hữu HAI bản soát trên UI THẬT, **không inject store**: §6 transport (Tiến ·
Lùi · Về đầu · Dựng lại · Tự chạy/Dừng) và §5 rõ ràng thị giác ở ba bề rộng.
Dùng **bài mẫu offline** (`data/samples.ts`) nên 0 API call — người dùng chọn
bài, bấm nút, trạng thái đổi thật. Ba miền: array/quét · tree/duyệt · graph/BFS.

Hai cái bẫy đã cắn và nay ghi lại trong code: nút bước là nút ICON chỉ có
`title` (tìm theo chữ trượt IM LẶNG), và `Tự chạy` **đổi nhãn thành `Dừng`** sau
khi bấm. Nhịp tự chạy đo được ~1 bước/giây, tick đầu ~1,2s — chờ 900ms thì bản
soát vu oan cho sản phẩm.

Đo HÌNH HỌC chứ không so pixel (repo không có `@playwright/test`): chữ SVG nằm
trong khung vẽ · không tràn ngang · không chữ kích thước 0 · nút bước còn bấm
được. `--faultcheck` chặn nút Tiến ở tầng capture để chứng minh guard đỏ được.

**`SUPPORTED_MIN_WIDTH = 320px`**, khoá bằng hai viewport `min-320`/`min-344`
trong chính runner. Trước vNext bố cục tràn ngang dưới ~354px và trang mất dữ
liệu ở mép phải; truy được chuỗi `.control-zone` (nowrap, 252/304px) →
`.player` (229px) → `.panel-controls` → `.app-layout` → `html`. Sửa bằng
`flex-wrap` trên `.control-zone` ở `global.css` — một luật ở tầng dùng chung,
không vá theo ảnh chụp, và không breakpoint nào phải nhớ vì wrap chỉ kích hoạt
khi hết chỗ (màn rộng không đổi một pixel).

### `frontend/scripts/capture-stack-vnext.mjs` (vNext) · cần dev server + Playwright

Bằng chứng trình duyệt cho case Stack `{[()]}`: tiêm envelope thẳng qua
`useAppStore.loadEnvelope`, đặt cursor tới 6 khung mốc, chụp ảnh và trích **phép
chiếu ngữ nghĩa từ DOM** (nội dung `<text>` trong SVG) — không so pixel. Kết quả:
`docs/evaluation/semantic-vnext/browser-evidence/` (`stack-visual-acceptance.json`
· 6 ảnh); báo cáo đi kèm ở `semantic-vnext/reports/STACK_VISUAL_ACCEPTANCE.md`.

Hai điều kiện của anti-pattern #14 đều CÓ THẬT trong script: **dấu vân tay trang**
(khẳng định đúng tiêu đề + 7 bước, sai thì thoát `3`) và **`--faultcheck`** (thay
`push`/`pop` bằng `highlight` ⇒ bản soát phải tụt khỏi 6/6, không tụt thì thoát
`4`). Chế độ tiêm lỗi tái hiện đúng triệu chứng gốc — ngăn xếp rỗng ở mọi khung
trong khi narration vẫn kể push/pop.

⚠️ Bộ trích phải LOẠI chú giải trình bày khỏi danh sách phần tử: lượt chạy đầu
nuốt nhãn `← TOP` vào `stack` và báo FAIL nhầm 4 khung. Chú giải không phải dữ
liệu. ⚠️ Cổng 3000 hay bị chiếm bởi dev server khác đang chạy mã CŨ; dùng
`--port` để dựng server riêng, đừng chụp vào cổng lạ (tiền lệ `0a71268`).

### `frontend/scripts/capture-phase-evidence.mjs` (W6) · cần `npm run dev` + Chrome
Chụp CLIP theo `.workspace-card` ở MỘT trạng thái xác định (`--target`,
`--viewport`, `--act`). Ghép với `git checkout <ref> -- <file>` (Vite HMR nạp lại
ngay, không cần dựng lại) thì có cặp TRƯỚC/SAU trên cùng máy, cùng bề rộng, cùng
đề — khác biệt duy nhất là bản vá. Dùng để chứng minh một pha có HẬU QUẢ HỌC SINH
NHÌN THẤY, chứ không chỉ có hợp đồng/test đã đổi.
⚠️ URL module lấy từ `performance.getEntriesByType('resource')`, KHÔNG `import()`
đường trần: Vite băm URL theo phiên nên import trần tạo instance THỨ HAI với store
rỗng. ⚠️ Phải nạp trước bốn module rồi mới dùng — lượt `import()` đầu của module
nặng có thể chưa trả kịp qua CDP, và khi ấy `Runtime.evaluate` trả `undefined`
CHỨ KHÔNG ném. Cả hai đều từng làm script im lặng hỏng.

### `frontend/src/simulations/generic-semantic-fit-w5m.test.ts` (W5M) · offline
Phase M bước 1 — nâng câu của `COVERAGE.md` (*"bài không có cơ chế ẩn thì mô
phỏng chỉ là trang trí"*) thành cổng chạy được: **cảnh generic CÔNG KHAI phải
khai ít nhất một `rules`** (boolean / weighted_sum). Tiêu chí dẫn xuất từ chính
DSL, không phán đoán thẩm mỹ: có `rules` ⇒ đổi đầu vào thì engine tính lại; chỉ
có `processes` (reveal/move) ⇒ hé lộ frame dựng sẵn = MINH HOẠ
(`SIMULATION_VS_ILLUSTRATION_CONTRACT.md`).
Kiểm kê tại thời điểm viết: `GENERIC_RULE_SPEC` (công khai, boolean not+and) ·
`GENERIC_AND_SPEC` + `GENERIC_BINARY_SPEC` (nội bộ, có rules, parity) ·
`GENERIC_PACKET_SPEC` + `GENERIC_REVEAL_SPEC` (nội bộ, reveal-only). Mọi cảnh
reveal-only đều là fixture NỘI BỘ ⇒ tầng bài mẫu đang trung thực; W4B-3F đã gỡ
ca công khai duy nhất trước đó.
⚠️ **LỖ HỔNG CÒN LẠI — W5M bước 2:** đường AI. Spec do LLM sinh với `rules` rỗng
+ `processes` reveal KHÔNG đi qua `OFFLINE_SAMPLES` nên test này không với tới.
Cổng cho đường đó phải nằm ở validator generic phía server
(`dsl/validator.py`): reveal-only ⇒ `capability_gap`, không dựng cảnh.
Có đối chứng: danh mục phải chứa CẢ hai loại, nếu không cổng xanh vì rỗng.

### `frontend/src/core/predicate.ts` (W5C) · Change impact: offline
CHỦ SỞ HỮU DUY NHẤT của "sáu phép so sánh `> >= < <= == !=` nghĩa là gì".
`compareNumbers(x, op, y)` + `includesBoundary(op)` — hàm THUẦN trên hai SỐ.
⚠️ Trước W5C cùng sáu toán tử được cài BA LẦN: `algorithms.ts::testCondition`
(sum_if/count_if), `scan.ts::opHolds` (algorithm.scan), và nhánh `compare` của
`program.ts` (bounded_control_flow). Ba bản đồng ý nhau vì MAY, không vì có gì
bắt chúng thế — và một lần đổi `>=` thành `>` ở một bản chỉ chấm sai đúng những
học sinh ở NGƯỠNG, tức chỗ bài học nằm ("từ 8,0 trở lên" ≠ "trên 8,0"). Cả ba
nay uỷ quyền xuống đây.
⚠️ `switch` cố ý KHÔNG có `default` — vét cạn để tsc đỏ khi thêm toán tử thứ
bảy. Đó chính là bẫy `program.ts` từng mắc: `default` cũ trả `l >= r`, nên mọi
op không khớp lặng lẽ thành `>=`. Nay op lạ thì NÉM.
⚠️ `program.ts` giữ riêng `==`/`!=`: ở đó hai vế có thể là bool/chuỗi, nên đó là
so sánh đồng nhất chứ không phải so sánh SỐ. Chỉ so sánh THỨ TỰ uỷ quyền xuống.
Khoá bởi `core/predicate-family-w5c.test.ts`: bảng chân trị 6 op × 3 quan hệ
VIẾT TAY (sinh từ code sẽ là test tự xác nhận) + đối chiếu đáp số engine + guard
chống mọc bản cài thứ tư.

### `frontend/src/simulations/color-channels.ts` (W5A) · Change impact: offline
CHỦ SỞ HỮU DUY NHẤT của phép toán BA KÊNH ↔ MỘT MÀU, dùng chung cho
`web.style_model` và `color.rgb_model`. Giữ `Channel`/`CHANNELS`/`CHANNEL_LABEL`/
`CHANNEL_MAX`, mẫu `HEX_COLOR`, `rgbOf`/`hexOf`/`rgbTextOf`/`cssColorOf`,
`isChannelValue`/`clampChannel`, `channelRamp` (vệt màu của thanh trượt) và
`readableInkOn` (chọn màu CHỮ đặt trên ô màu theo luma BT.601).
⚠️ Nâng từ `domains/web/props.ts` trong W5A — trước đó phép toán thuộc sở hữu
của MỘT miền, nên miền thứ hai chỉ có hai lối: import chéo miền (đảo hướng phụ
thuộc) hoặc chép lại (hai bản `hexOf`, và ngày chúng lệch thì hai màn hình nói
hai giá trị khác nhau về cùng một màu).
⚠️ `channelRamp` giữ HAI kênh kia cố định — đó là điều kiện để vệt màu nói thật
về màu sắp nhận được; một vệt đỏ-thuần cố định sẽ nói dối.
⚠️ `clampChannel` dùng ở BIÊN NHẬN (thanh trượt/ô số), KHÔNG dùng để chữa config
sai — kẹp im lặng ở đó biến một đề hỏng thành mô phỏng trông như đúng.

### `frontend/src/simulations/domains/color/` — `color.rgb_model` (W5A) · offline
Miền MÀU, target thứ 24. `model.ts` giữ ba số và DẪN XUẤT mọi cách viết khác
(`cssColorOfState`/`hexColorOfState`/`cornerNameOf`/`isGray`/`dominantChannel`);
`ui.tsx` dựng ba thanh trượt có vệt màu + ô số nhập được, rồi ô màu lớn mang
`rgb(...)` và `#rrggbb`; `index.ts` khai module exploratory (KHÔNG timeline,
KHÔNG `predict`) + `explore.entry` + `narrate` + `currentConfig`.
⚠️ Vì sao là target riêng chứ không phải `generic.rule_scene`: cảnh generic chở
được câu chuyện VỀ màu nhưng không chở được phép TRỘN — không có đại lượng liên
tục nào để kéo, và ô màu không thể là CHÍNH kết quả đang được tính. Định tuyến
đề RGB sang generic là `SEMANTIC_MISUSE` (Phase M).
⚠️ `cornerNameOf` chỉ đặt tên ở TÁM ĐỈNH khối màu. Gọi `rgb(200,90,40)` là "nâu"
là phán quyết thẩm mỹ do renderer bịa ra — cả bài học dựng trên nguyên tắc mọi
thứ hiện ra đều dẫn xuất tất định từ ba con số.
⚠️ KHÔNG có `predict`: trộn màu là quan hệ tức thì ba-vào-một, không có "bước
tiếp theo" nào để cam kết. Transport khai `RESET_ONLY` cùng lý do.
Bên backend: `catalog.py::CATALOG["color.rgb_model"]` +
`validation/simulation.py::validate_color_config` + cơ chế
`positional_representation.rgb_channel_composition`.

### `frontend/scripts/measure-transport-w7.mjs` (M20 W7) · offline (cần `npm run dev`)
Hỏi: cơ chế to nhỏ khác nhau thì khay điều khiển có đổi bề rộng theo không? Đo
độ LỆCH bề rộng qua nhiều target thay vì so với một con số ma. Đo ở HEAD
104c752: cơ chế lệch 849px, khay lệch **đúng 849px** — bám 1:1; sau W7 khay lệch
**0px**.
⚠️ Đếm HÀNG bằng TÂM DỌC có dung sai, không bằng mép trên: `align-items: center`
khiến ba cụm khác chiều cao có mép trên lệch vài pixel dù cùng một hàng, và bản
đầu vì thế báo 3 hàng cho một dải rõ ràng một hàng. Artifact:
`docs/evaluation/m20/transport-{before,after,catalog,browser}.json`.

### `frontend/scripts/browser-runner.mjs` (M20 W12) · offline (cần `npm run dev`)
MỘT vòng đời trình duyệt cho NHIỀU kịch bản: mở Chrome một lần, chờ trang một
lần, dọn state giữa các kịch bản bằng `store.reset()` + xoá lưu trữ, đóng một
lần. Cách ly bằng DỌN STATE, không bằng khởi động lại tiến trình. Có bộ đếm
`serverStarts` xuất ra artifact để một bản sửa vô ý quay lại kiểu
một-server-mỗi-kịch-bản không lọt im lặng. Cấp sẵn `loadTarget`/`snapshot`/
`dispatch`/`clickText`/`scenario`.

### `frontend/src/simulations/interaction-semantics.test.ts` (M20 W12-B0) · offline
Trả lời câu hỏi cổng cho từng target: **"khi ĐÓNG thử thách, học sinh thao tác
lên cái gì?"** — "một phương án trả lời" KHÔNG phải câu trả lời hợp lệ, nó thuộc
THỬ THÁCH.
Phân loại theo HAI VẾ: action phải đổi được state của CHÍNH module (thử `apply`,
so state, config lấy từ danh mục mẫu đã validate) VÀ có affordance phát ra nó
trong renderer miền (§14 `AFFORDANCE_MISSING`).
⚠️ Hai lần đếm sai đã ghi trong file: (1) quét cả thư mục miền nên mọi target
thừa hưởng mọi action của miền → 23/23 "interactive", trong khi `algorithm.scan`
có `apply: (state) => state`; (2) gộp "probe chưa trúng giá trị thật" vào
TRACE_MODEL → hạ cấp target thao tác được vì phép đo hẹp. Nay có ba mức:
`INTERACTIVE_MODEL` · `TRACE_MODEL` (xác nhận bằng `apply` đồng nhất) ·
`PROBE_LIMITED` (chưa kết luận). Artifact:
`docs/evaluation/m20/w12-interaction-semantics.json`.

### `frontend/scripts/certify-viewports-w12.mjs` (M20 W12-C) · offline (cần `npm run dev`)
23 target × 4 bề rộng = 92 dòng, dùng lại `browser-runner.mjs`. Hỏi câu KHÁC với
`audit-composition.mjs`: **ở bề rộng này học sinh có DÙNG ĐƯỢC target không** —
sân khấu hiện · affordance chính thấy được · thử thách đóng sẵn · tràn/cắt/chồng.
⚠️ Đếm affordance phải gồm CUE CON TRỎ trên SVG: cột `ArrayView` là một `rect`
gắn pointer handler và React gắn listener ở gốc nên không lộ ra DOM. Bản đầu chỉ
tìm `input/button/[tabindex]` và đọc ra 0 affordance cho mọi target thuật toán —
một kết luận sai vì thước đo hẹp.
Artifact: `docs/evaluation/m20/w12-viewport-matrix.json`.

### `frontend/scripts/quiz-dominance-w12.mjs` (M20 W12-A) · offline (cần `npm run dev`)
Hỏi: khi mở thử thách, CƠ CHẾ còn là khối lớn nhất trên màn hình không? Đo tỉ lệ
`chiều cao khối thử thách / chiều cao sân khấu` — không đo bề rộng, vì cả hai
nằm cùng cột nên bề rộng luôn bằng nhau và phép so sẽ không bao giờ phân biệt
được gì (lỗi "luật không thể sai" đã gặp ở M19).
⚠️ Bản đầu đo ngay ở cursor 0 và chỉ chạm được 2/23 target — `predict.challenge`
trả null ở phần lớn các bước, nên 21 target còn lại bị đọc nhầm thành "không có
thử thách". Nay tiến từng bước tới khi lối vào hiện ra.
Đo được ở HEAD daf9b28: `network.packet_routing` 111px/180px = **0,62** (FAIL).
Sau bản sửa chủ sở hữu chung: 61px/180px = **0,34**, 0 FAIL.
Artifact: `docs/evaluation/m20/w12-quiz-dominance.json`.

### `frontend/scripts/certify-w12.mjs` (M20 W12) · offline (cần `npm run dev`)
Chứng nhận tương tác trong trình duyệt THẬT theo luật: hành động → SimAction →
`module.apply` → **state tất định đổi** → hệ quả nhìn thấy trong DOM. Một cú bấm
không đủ, một hoạt hình không đủ, trả lời thử thách không đủ.
⚠️ Phân biệt `CERTIFIED` với `PROBE_UNVERIFIED`: state không đổi có thể là target
không nhận action ấy HOẶC probe chưa đúng từ vựng miền. Gộp hai ca thành "hỏng"
là đổ lỗi cho sản phẩm vì phép đo hẹp — Wave 1 đã ghi rằng bộ thăm dò chung chỉ
là CẬN DƯỚI. Artifact: `docs/evaluation/m20/w12-interaction.json`.

### `frontend/src/styles/transition-semantics.test.ts` (M20 W10) · offline
Phân biệt HÌNH HỌC DỮ LIỆU (SVG) với CHUYỂN ĐỘNG BỐ CỤC (HTML). `height` trên
`<rect>` encode giá trị mảng — cho chạy là cách kể "giá trị vừa đổi bao nhiêu";
`height` trên `<div>` đẩy mọi thứ bên dưới. Luật đọc NGỮ CẢNH PHẦN TỬ, không cấm
theo tên thuộc tính (cấm theo tên sẽ chặn nhầm `ArrayView`) và không miễn theo
tên file (miễn theo file thì bản vá HTML sau đó cũng lọt).
⚠️ Guard tìm ra một HẠNG MỤC THỨ BA brief không lường: `.web-page` chạy `padding`
— thuộc tính bố cục HTML nhưng chính nó LÀ state mô phỏng đang dạy. Ngoại lệ khai
theo BỘ CHỌN kèm lý do ≥80 ký tự nói vì sao không đẩy chỗ nhìn.

### `frontend/src/evidence-provenance.test.ts` (M20 W8 closure) · offline
Khoá hợp đồng xuất xứ v2 và chứng minh vòng TỰ THAM CHIẾU đã bị phá.
⚠️ Có một test tồn tại vì lỗi thật: `sourceFingerprint` bản đầu chạy `git
ls-files` với cwd của tiến trình (`frontend/`) nên không khớp file nào, và dấu
vân tay ra sha256("") — GIỐNG HỆT ở mọi trạng thái nguồn, tức `STALE_SOURCE`
không bao giờ kích hoạt được. Các test khác vẫn xanh vì chúng so hàm với chính
nó. Test "dấu vân tay PHÂN BIỆT ĐƯỢC" là chỗ bắt được nó.

### `frontend/scripts/impact.mjs` (M20 W8) · T0 IMPACT GATE · offline
Chọn test theo file vừa đổi và **in ra lý do từng lựa chọn**. Ghép ba nguồn: sở
hữu theo thư mục · sổ `SHARED_OWNERS` (mỗi dòng phải nói vì sao bán kính rộng) ·
leo thang bảo thủ.
⚠️ LUẬT: thay đổi mã sản phẩm KHÔNG BAO GIỜ được chọn 0 test — không tra ra chủ
thì trả `IMPACT_MAPPING_MISSING` và leo lên gate rộng. Guard kiến trúc
(`code-index-sync`, `tokens`, `ui-hygiene`) không import file bị đổi nên đồ thị
import không chọn được chúng; chúng phải khai theo sở hữu — đó là lý do bộ chọn
không dùng `vitest --related` một mình. Cờ `--files a,b` cho tập giả định để
`test-tiers.test.ts` kiểm được chính bộ chọn.

### `frontend/scripts/full-gate.mjs` (M20 W8) · T3 · offline
Chủ sở hữu DUY NHẤT của nhãn `FULL_PRODUCT_GATE_PASS`. Danh sách cổng con nằm
trong mảng `GATES` và bị `test-tiers.test.ts` khoá — bỏ một cổng mà vẫn phát
nhãn là chứng nhận một HEAD chưa được kiểm.

### `frontend/scripts/certify-sweep-w12.mjs` (M20 W12) · LƯỢT CHỨNG NHẬN · cần Chrome
Chủ sở hữu của bất biến **source-freeze**: chụp `HEAD`/`sourceFingerprint`/cây
bẩn ở HAI đầu lượt, chạy toàn bộ cổng con W12 (`GATES` — 1 DERIVED + 7 BROWSER),
rồi đòi nguồn y nguyên và `uniqueFingerprints === 1`. Vi phạm ⇒
`CERTIFICATION_SWEEP_INVALID`, thoát != 0.

Vì sao cần dù mọi cổng con đã có `provenance()`: `provenanceVerdict` phán MỘT
artifact tại MỘT thời điểm, nên bảy artifact đo trên bảy trạng thái nguồn khác
nhau vẫn qua được từng cổng rồi được cộng thành một tuyên bố COMPLETE về một sản
phẩm chưa từng tồn tại. Đo được điều đó phải nhìn cả LƯỢT. Khoá bởi
`src/certification-sweep.test.ts` (tiêm lỗi từng ca + chặn cổng con rụng im lặng).

Primitive nằm ở `evidence.mjs`: `sweepBegin/sweepEnd/sweepVerdict`,
`crossCheckFreshness`, `SWEEP_FAULTS`.

### `frontend/src/simulations/domains/logic/dag-module.tsx`
Chủ sở hữu target `logic.boolean_dag`: model mạch logic (đầu vào → cổng → đầu
ra theo thứ tự phụ thuộc), `apply` nhận `toggle` theo ID đầu vào THẬT (`N`/`G`/`K`,
không phải `A`), timeline lan truyền giá trị, và renderer SVG kèm bảng chân trị.

Đây là MỘT trong hai chỗ tự nối đúng hợp đồng bàn phím cho affordance SVG trước
khi có helper dùng chung (`tabIndex` + `aria-label` "Đầu vào …, giá trị …, bấm
để đổi" + Enter/Space, vì `<g>` không phải `<button>` thật). Chỗ kia là
`network/ui.tsx::LinkHandle`. Vòng tiêu điểm ở `.dag-input:focus-visible`.

### `frontend/src/core/var-label.ts` (M20 · Product Experience) · offline
`varLabel(name)` / `varPhrase(name, fallback)` — đổi TÊN BIẾN ENGINE sang cụm
tiếng Việt đọc lên được. Bảng chỉ phủ biến do chính engine đặt (`tong`, `dem`,
`max`, `min`, `can_tim`, `gia_tri_chen`, `giua`, `vi_tri_cuc_tri`, `vt`); tên do
ĐẶC TẢ cấp (`seed.varName`, LLM sinh) trả `null` ⇒ bên gọi phải nói bằng khái
niệm, không đoán cách viết có dấu (bỏ dấu là ánh xạ mất thông tin: `tong` có thể
là tổng/tông/tống).

Đóng lỗi thật quét được toàn danh mục: `core/scan.ts` và `core/algorithms.ts`
nội suy thẳng tên biến vào câu thuyết minh, nên `algorithm.scan` đọc ra
**"Khởi tạo nguong = 4."** trên màn học sinh. `ui-hygiene` không bắt được vì nó
soi chuỗi TĨNH trong mã, còn đây là chuỗi nội suy LÚC CHẠY.

### `frontend/src/simulations/svg-affordance.ts` (M20 W12) · offline
`svgAffordance({label,onAct,pressed})` trả PROPS cho một hình SVG bấm được:
`role="button"` + `tabIndex` + `aria-label` + `aria-pressed` + Enter/Space (có
`stopPropagation` vì Space là phím tắt Tự chạy toàn cục) + lớp `.sim-affordance`
(vòng tiêu điểm ở `global.css`).

Vì sao trả props chứ không phải component: chỗ gọi trải vào `<g>`/`<line>`/`<rect>`
có hình học riêng, và bọc thêm một `<g>` sẽ làm lệch phép đo hình học đã chứng
nhận (`audit-composition.mjs`, `certify-visual-weight-w12.mjs`).

Đóng lỗi thật: idiom "`<g>` có `cursor:pointer` + `onClick`" dựng ở 5 chỗ, đúng
ở 2. `logic.and_gate` có 13 phần tử focus được, không cái nào là công tắc A/B.
`network/ui.tsx::LinkHandle` và `logic/dag-module.tsx` là nguồn gốc của khuôn và
KHÔNG bị viết lại (đổi mã đã chứng nhận để cho đối xứng = đánh đổi rủi ro hồi
quy lấy cái đẹp). Khoá bởi `scripts/certify-a11y-w12.mjs`.

### `frontend/scripts/certify-a11y-w12.mjs` (M20 W12) · cần Chrome
Khả năng tiếp cận đo bằng PHÍM THẬT qua CDP `Input.dispatchKeyEvent` — sự kiện
tự dựng (`isTrusted:false`) không chứng minh được người dùng bàn phím đi được.
Sáu bề mặt đại diện; mỗi ca đòi đủ chuỗi focus → Enter thật → STATE ĐỔI, cộng
`ACCESSIBLE_NAME` · `VISIBLE_FOCUS` (`outline-style !== none`) ·
`STATE_NOT_COLOR_ONLY` · Escape đóng thử thách + trả tiêu điểm · 768px.
Tiêm lỗi: `A11Y_NAME_REMOVED` · `A11Y_KEYBOARD_PATH_REMOVED` ·
`CHALLENGE_ESCAPE_BROKEN` (thay khối bằng bản sao rời fiber) + CONTROL.

### `frontend/scripts/certify-representation-w12.mjs` (M20 W12) · cần Chrome
Hai câu hỏi một chủ đề: mỗi target bày ĐÚNG MỘT cách xem cho học sinh, và target
còn renderer nội bộ thì hai renderer đọc cùng một sự thật. Sinh bảng 23 dòng
(mode công khai · mode khả dụng · bày cho học sinh · bản nội bộ · vi phạm) +
parity 2D↔3D. Tiêm lỗi `PUBLIC_DUAL_MODE_WITHOUT_POLICY` ·
`RENDERER_PARITY_STATE_DIVERGENCE`.
⚠️ Renderer 3D là chunk NẠP LƯỜI ⇒ nó là object, không phải function.

### `frontend/scripts/certify-teaching-walkthrough-w12.mjs` (M20 W12) · cần Chrome
Câu hỏi nghiệm thu duy nhất: bỏ thử thách đi, giáo viên còn phơi bày được cơ chế
không? 11 kịch bản, từ vựng action lấy NGUYÊN từ `certify-w12.mjs::PLAN`.
⚠️ Phạm vi đo là `.workspace-card`, KHÔNG phải `.sim-stage` — cơ chế của
`web.style_model` là DOM thật, của ba target cơ số/bảng là `<table>`, của
`protocol_encapsulation` là `.encap-layer`. Tiêm lỗi
`TEACHING_WALKTHROUGH_CHALLENGE_ONLY`.
⚠️ KHÔNG dùng để nói bất cứ điều gì về kết quả học tập.

### `frontend/scripts/certify-classroom-continuation-w12.mjs` (M20 W12) · cần Chrome + backend
Rời đi rồi quay lại: đăng nhập → mở bài đã giao → thao tác THẬT → ghi tiến độ →
ĐĂNG XUẤT + xoá sạch `localStorage` → đăng nhập lại → tiến độ trở lại. Xoá lưu
trữ là bắt buộc, nếu không phép đo sẽ xanh nhờ LỊCH SỬ CỤC BỘ — cơ chế khác hẳn.
⚠️ `/api/auth/me` trả 200 kèm `user: null` cho khách, KHÔNG trả 401.
⚠️ Cần container backend MỚI (bản cũ không phục vụ `/api/auth/*`) + seed fixture.
Tiêm lỗi `CLASSROOM_PERSISTENCE_REMOVED` · `CLASSROOM_RESTORE_MISMATCH`.

### `frontend/src/test-tiers.test.ts` (M20 W8) · offline
Kiểm chính bộ chọn theo HAI CHIỀU (thiếu: chủ sở hữu dùng chung thu về một test
hẹp ⇒ đỏ · thừa: renderer lẻ kéo cả kho ⇒ đỏ) và khoá ngữ nghĩa nhãn: chỉ T3
được nói `FULL_PRODUCT_GATE_PASS`.
⚠️ Ba guard trong file này từng **khớp rỗng rồi báo đạt** — soi comment thay vì
mảng cổng, mẫu thiếu `
` nên match rỗng, soi phần "Đã đổi" thay vì phần chọn.
Mỗi guard nay tự kiểm rằng nó tìm thấy thứ cần soi trước khi khẳng định.

### `frontend/scripts/runtime-zero-ai-w7.mjs` (M20 W7 closure) · offline (cần `npm run dev`)
ĐẾM request thật thay vì suy từ cấu trúc mã. Bọc `window.fetch` và `module.init`
của mọi module trong registry, chụp số đếm trước/sau từng hành động. Có PHÉP THỬ
DƯƠNG TÍNH mỗi lượt chạy (gọi fetch một lần có chủ đích) để "delta 0" nghĩa là
"không có gọi", không phải "bộ đếm không gắn được".
Phủ: mở/đóng dòng thời gian · trace theo tham số hiện tại · Đặt lại — mỗi cái
kiểm cả fetch, `init`, và ảnh chụp state.
⚠️ Khẳng định "trace theo tham số mới" phải NỐI với giá trị hiện tại (bước chia
đầu = `decimalValue`, chia cho `targetBase`), không so với hằng số: bản đầu tìm
dấu vết "cơ số 2" nhưng mẫu offline vốn đã là cơ số 16 nên phép tiêm giữ
`state.steps` đi qua sạch 23/23. Artifact: `docs/evaluation/m20/w7-runtime.json`.

### `frontend/src/components/transport-w7.test.tsx` (M20 W7) · offline
Khoá ba nhóm: chế độ đến từ chính sách (gồm phép gán `declaredMode ??` — lỗ do
tiêm lỗi tìm ra) · bề rộng khay tách khỏi cơ chế (đòi SÀN ở **cả hai** biến thể
lưới — lỗ thứ hai do tiêm lỗi tìm ra) · dòng thời gian tuỳ chọn mở được thì đóng
được và không đụng store.

### `frontend/src/simulations/experience-manifest.test.ts` (M20 W6) · offline
MANIFEST TRẢI NGHIỆM 23 target + guard "mô hình là chính, thử thách là phụ".
Khoá bốn nhóm: thử thách đóng mặc định (đọc từ CHỦ SỞ HỮU `loadEnvelope`, không
đoán theo module) · chính sách hiện kết quả (target công cụ không được giấu đáp
án sau transport) · phản hồi KHÁM PHÁ không được nói giọng chấm điểm · lối vào/ra
thử thách tiếp cận được.
⚠️ `TRANSPORT_REASON` KHÔNG có giá trị mặc định — target chưa khai hiện
`UNCLASSIFIED` và test đòi con số đó bằng 0. Bản đầu mặc định "có timeline ⇒
FULL_TRACE" và cho ra 18, một con số chỉ là phép đếm thuộc tính kĩ thuật đội lốt
phân loại sư phạm; khai đủ theo cơ chế thì thật ra là **13 / 7 / 3**.
Artifact: `docs/evaluation/m20/experience-manifest.json`.

### `frontend/scripts/measure-tool-first-w5.mjs` (M20 W5) · offline (cần `npm run dev`)
Trả lời câu §7: **ở cursor 0, DOM có hiện đúng đáp án mà engine đang giữ không?**
Đọc đáp án THẲNG từ store rồi tìm nó trong DOM — kiểm renderer có nói đúng thứ
engine giữ (ranh giới R0); tính đúng của bản thân đáp án do oracle độc lập bên
vitest lo.
⚠️ Ba lần phải sửa chính phép đo trước khi tin được, ghi trong file: (1) hàm tua
gọi `st.next()` — API không tồn tại — nên trả 'ok' mà không tua, mọi target đọc
ra "không bị khoá"; (2) chỉ đếm `table td` nên không thấy bề mặt dựng bằng lưới
div — đo THẺ chứ không đo THÔNG TIN; (3) phán bằng hiệu số nội dung khi tua, sai
tiêu chí vì §1 nói diễn giải NÊN hiện dần. Artifact:
`docs/evaluation/m20/tool-first-{before,after-*}.json`.

### `frontend/src/simulations/target-certification.test.ts` (M20 W4) · offline
MANIFEST chứng nhận theo TARGET — **không** phải cổng chất lượng thứ tư. Wave 4
soát ra cả bốn cổng đều đã có chủ: ngữ nghĩa → `authenticity_audit.py` · trình
bày → `representation-policy-w4b2r.test.ts` · tương tác → soát trải nghiệm
W4B-4A · chỗ đứng → `audit-composition.mjs`. Thứ thiếu là **ai phủ target nào và
bằng chứng còn tươi không** — bốn cổng chạy độc lập nên không ai trả lời được, và
đó chính là chỗ một target hỏng lặng lẽ đi qua. Manifest ghi rõ `NO_EVIDENCE` /
`STALE_EVIDENCE`, KHÔNG gộp thành "đạt". Artifact:
`docs/evaluation/m20/target-certification.json`.
⚠️ Khoá một phân biệt đã suýt ship sai trong chính wave này: `explore`/`predict`
là **lối vào KHAI**, không phải thao tác — lấy chúng làm thước đo cho ra 11
target "chỉ xem" trong khi probe theo hình dạng miền chỉ thấy 3.

### `simulation/scope.py` (M20 W3) · Change impact: offline
MỘT bộ từ vựng `DomainScope` + `Simulatability` + `REQUIRES_SIMULATION`, dùng
chung production ↔ evaluation. Ở tầng `simulation/` vì production là nơi PHÁN,
evaluation chỉ ĐO — `evaluation/curriculum_schema.py` import xuống đây chứ không
dựng bộ thứ hai. Hai trục KHÔNG được gộp: đề có thể thuộc phạm vi mà không đáng
mô phỏng (đạo đức mạng), và ngoài phạm vi mà mô phỏng được (quỹ tích).

### `simulation/scope_gate.py` (M20 W3) · Change impact: targeted live
Cổng thứ NĂM, chạy TRƯỚC cổng tính toán trên **đường generic**. Bịt lỗ R0: trước
wave này không cổng tất định nào hỏi "đề này có thuộc môn Tin học không", nên một
đề hoá học (không đụng gap-role, `result_ownership="provided"`) chỉ bị chặn khi
LLM tự từ chối. Nay LLM KHAI hai trường `domain_scope`/`simulatability` (bắt buộc
trong `ANALYZE_SCHEMA`), server PHÁN.
Đọc docstring trước khi sửa — hai quyết định dễ bị "sửa cho nhất quán" mà hỏng:
(1) `AMBIGUOUS` **KHÔNG** bị từ chối dù cổng bên cạnh fail-closed, vì hai rủi ro
ngược nhau (nói dối > từ chối oan); (2) `GATE_SCOPE_UNDECLARED` là lỗi hợp đồng
prompt nên **lùi xuống cuối**, không được nuốt lời từ chối năng lực thật có nêu
vai trò. Bốn phép tiêm lỗi đã chứng minh cả bốn tính chất đỏ được
(`tests/test_scope_gate.py`).

### `evaluation/curriculum_schema.py` (M20 W2) · Change impact: offline
Tầng phân loại **ỔN ĐỊNH** của benchmark chương trình, tách khỏi tầng **DẪN
XUẤT**. Sở hữu `DomainScope` (gồm `ADJACENT_CONTEXT` — đề mang vỏ môn khác nhưng
cơ chế vẫn Tin học, để không từ chối oan), `Simulatability` (phán quyết SƯ PHẠM,
độc lập năng lực hệ — **không** gộp với `result_mode` vốn nói về hiện thực),
`capability_status()` đọc registry lúc chạy, và `expected_outcome()` ghép hai
tầng. Nhờ vậy thêm target mới KHÔNG phải viết lại benchmark.
Cũng sở hữu **neo chương trình**: `UNIT_CODE`, `NOT_ANCHORED`, `unit_codes()`,
`check_anchor()`. Đọc comment ở đó trước khi đụng — phép đếm phủ đã sai HAI lần
tại đúng chỗ này (đếm chuỗi thô → 14 "đơn vị" trong đó 6 là câu ghi chú; rồi rút
regex → ghi công `T10.CD1` cho chính câu nói nó *không* neo). Trường neo nay chỉ
nhận mã hoặc `NOT_ANCHORED — <lý do>`.

### `evaluation/metamorphic.py` (M20 W2B) · Change impact: offline
7 phép biến hình TẤT ĐỊNH giữ nguyên ngữ nghĩa (đổi tên người/thiết bị, cách nói
tương đương, đổi số, đảo dãy, hai phép khoảng trắng) để đo hệ có đọc CƠ CHẾ hay
chỉ khớp mẫu chữ. Hai ràng buộc dễ phá: `shift_numbers` **giữ nguyên 0 và 1** (ở
đề logic/nhị phân chúng là giá trị bit) và `reverse_sequence` chỉ đụng dãy ≥3 số.
`variants()` loại biến thể trùng bản gốc — giữ lại chỉ làm con số phủ to giả.

### `evaluation/product_scope.py` (M20 W2C) · Change impact: offline
`ProductScope` + `SCOPE_OVERRIDES` tách ba loại case bị trộn số: nội dung Tin học
CÔNG KHAI (tính vào phủ) · fixture ENGINE nội bộ (chứng minh DSL, KHÔNG tính) ·
case NGOÀI PHẠM VI (chứng minh từ chối trung thực, KHÔNG tính). Mỗi override phải
nói VÌ SAO theo NỘI DUNG; test từ chối lý do kiểu "nó vốn nằm trong pool khác".

### `backend/scripts/curriculum_benchmark_report.py` (M20 W2A) · Change impact: offline
Báo cáo phủ theo **ĐƠN VỊ chương trình** (không theo số case), sinh từ dữ liệu +
registry, có head stamp. Đọc đúng tập pool CHỊU luật kết nạp (`NEW_POOLS` +
`thesis`, gồm cả `m16`); `regression` đứng ngoài vì bị đóng băng và không có
trường neo. Artifact: `docs/evaluation/m20/curriculum-benchmark.json`.

### `tests/test_curriculum_benchmark.py` (M20 W2) · Change impact: offline
Khoá 5 nhóm: tầng ổn định vs dẫn xuất · biến hình · `DATASET` 30 case đổi VAI
thành `LEGACY_AI_COMPOSITION_REGRESSION` (còn nguyên, hết làm thước đo phủ) ·
tách fixture nội bộ khỏi phạm vi sản phẩm · **trường neo phải đếm được** (gồm
ngưỡng ≥3 case/đơn vị và ≥8 đơn vị). Ba phép tiêm lỗi đã chứng minh nhóm cuối đỏ
được: trả văn xuôi về trường neo · xoá 1 case khỏi đơn vị mỏng · bỏ kiểm tra
sentinel trong `unit_codes()`.

### `simulation/patterns.py` · Change impact: offline
Pattern reuse (M7.13B): chữ ký, extraction (safe allowlist), instantiate, matcher
tất định, 4 cổng, `DbPatternStore`.
Exports: `spec_signature`, `pattern_key_of`, `extract_template`, `instantiate`,
`validate_params`, `deterministic_fill`, `covered_roles_of_template`, `run_gates`,
`DbPatternStore`. Tests: `test_patterns.py`, `test_reuse.py`.

### `simulation/edit_policy.py` · Change impact: offline
EditPolicy v1 (M7.14D): affordance sửa DẪN XUẤT TỪ SPEC (không tên bài/môn).
Exports: `edit_policy_of`, `check_ops_against_policy`, `policy_contract_text`,
`EditFamily`, các hằng `POLICY_*` / `STRUCTURE_INVALID`.
Consumers: `patch.py` (enforce), `ai/edit.py` (prompt theo cảnh + enforce).
Tests: `test_edit_policy.py`. Mirror TS: `generic/edit-policy.ts`.
Notes: precedence bảo thủ `move > structural > spatial > value_only`;
multi-family CHƯA hỗ trợ.

### `simulation/patch.py` · Change impact: offline
SimulationPatch v1 (M7.14A): 5 op, áp trên bản sao, full validator + guard tiến
trình + engine smoke. Exports: `validate_and_apply_patch`, `ALLOWED_OPS`,
`MAX_OPS`, `UPDATE_FIELDS`, `PATCH_STATUSES`. Tests: `test_patch.py`.
Mirror TS: `generic/patch.ts`.

### `validation/simulation.py` · Change impact: offline
Validator config các domain chuyên biệt + `check_forbidden_keys` (chặn LLM sinh
timeline/state). Exports: `validate_algorithm_config`, `validate_logic_config`,
`validate_binary_config`, `validate_network_config`, `validate_encapsulation_config`,
`ALGORITHM_IDS`.
Tests: `test_validate.py`, `test_encap_routing.py`.
Notes (M10-AI-ROUTE): `validate_encapsulation_config` là bề mặt v1 NHỎ
(payloadLabel/appProtocol/notes, mọi field optional, mặc định an toàn — khớp
`validateEncapConfig` frontend); ngoài `check_forbidden_keys` còn cấm khóa
engine-owned (`layers/pdu/headers/packets/protocols`) — mô hình 4 tầng/9 bước
thuộc engine tất định, LLM chỉ điền nhãn ngữ cảnh (R0).

### `tests/test_encap_routing.py` · Change impact: offline
M10-AI-ROUTE — khóa định tuyến NL cho `network.protocol_encapsulation` (mock,
offline): CATALOG đăng ký + enum classify dẫn xuất; `catalog_text`/`classify.md`
mang phân biệt ngữ nghĩa encap↔routing + giới hạn v1; validator R0/v1; e2e mock
tiếng Việt → envelope encap; packet_routing nguyên vẹn. Bằng chứng live 5/5 ghi
ở `CURRENT_STATE.md` §nhật-ký-live.

### `persistence/db.py` · Change impact: offline (drift gate) + targeted (Postgres smoke)
SQLAlchemy (SQLite mặc định / Postgres qua `DATABASE_URL`).
Exports: `SimulationCache`, `SimulationPattern`, `ReuseMetric`, `bump_metric`,
`read_metrics`, `init_db(target_engine=None)`, `sqlite_owns_schema`, `db_dialect`,
`SessionLocal`, `IS_SQLITE`, `_engine_kwargs`.
Notes: `load_dotenv()` chạy **lúc import** → key thật vào `os.environ` (vì vậy
conftest phải gỡ key). **Migration = Alembic** (`backend/alembic/`); trên DB bền
Postgres, Alembic sở hữu DUY NHẤT tạo/tiến hoá schema. **Quyền sở hữu schema theo
dialect (DB-HARDEN-2)**: `init_db()` gọi `create_all()` **chỉ khi** `sqlite_owns_schema(engine)`
(`engine.dialect.name == "sqlite"`) — no-op trên Postgres. `_engine_kwargs()` là
pool dialect-aware (SQLite: `check_same_thread`; Postgres: `pool_pre_ping/recycle/
size/max_overflow`). Đổi model → phải tạo migration, nếu không **cổng chống trôi**
`tests/test_migration_drift.py` sẽ ĐỎ.

### `tests/test_db_ownership.py` · Change impact: offline
Khoá quyền sở hữu schema theo dialect: SQLite dùng `create_all`, Postgres KHÔNG;
`_engine_kwargs()` dialect-aware (SQLite không nhận pool option Postgres).

### `tests/test_migration_drift.py` · Change impact: offline
Cổng chống trôi Alembic (chạy trong suite mặc định): `upgrade head` + `alembic
check` trên **SQLite tạm** (không đụng DB dev). Đổi model mà quên migration → ĐỎ.
Đã chứng minh bằng fault-injection (thêm cột không migration → gate bắt được).

### `tests/test_postgres_integration.py` · Change impact: targeted (opt-in `pytest -m postgres`)
Smoke Postgres THẬT (marker `postgres`, mặc định bị loại qua `pytest.ini` addopts).
Container throwaway **không volume** (không đụng `pgdata`), tự skip nếu thiếu
Docker/psycopg2: migrate→head, `alembic_version`==head, ghi/đọc/sửa qua model thật,
**restart+reconnect** (dùng host port cố định vì Docker đổi random port sau restart),
`alembic check` sạch, cleanup `docker rm -f` có kiểm chứng.

### `ingestion/input.py` · Change impact: targeted live (ảnh cần LLM)
Chuẩn hóa text/document/code/image → text. Exports: `ingest_to_text`, `IngestError`.
Tests: `test_ingest.py`.

### `evaluation/dataset.py` · Change impact: offline
**Chỉ định nghĩa benchmark** (30 đề, không gọi API). Exports: `EvalItem`, `DATASET`.
`tags`: `smoke` (8 đề), `boundary` (4 đề). Đổi group/expect = đổi ngữ nghĩa
benchmark → cân nhắc kỹ.

### `evaluation/harness.py` · Change impact: offline (chạy live thì là live)
Chạy pipeline thật + metrics. Exports: `evaluate_item`, `run_eval`, `select_suite`,
`format_report`, `EvalReport`, `ItemResult`, các hằng `FAIL_*`.
Notes: `gap_gate_recall` là metric **song song** (M7.14T) — không đổi cách tính
metric cũ. `_simulate_with_metrics` **mirror** `stage_simulate` (rủi ro drift).

### `evaluation/m16_schema.py` · Change impact: offline
M16 Task 1 — lớp expectation có cấu trúc cho case đánh giá M16 + khoá integrity
nội dung dataset. Exports: `M16_DATASET_VERSION`, `M16Archetype` (enum ĐÓNG, 6
giá trị), `M16Expectation`, `check_m16_admission`, `frozen_dataset_fingerprint`.
Tests: `test_m16_schema.py`.
Notes: gắn lên `EvalItem` qua trường `m16` (kiểu khai `object | None` bên
`dataset.py` để tránh vòng import — chiều import CHỈ MỘT chiều: m16_schema →
dataset, KHÔNG ngược lại). `check_m16_admission` import trễ
`datasets.check_admission` bên TRONG hàm (phá vòng
`datasets→m16_catalog→m16_schema→datasets`, xem docstring). `frozen_dataset_
fingerprint()` khoá SHA-256 canonical JSON 30 case DATASET gốc bằng hằng PIN
trong test — DATASET đó KHÔNG BAO GIỜ được sửa nội dung.

### `evaluation/m16_record.py` · Change impact: offline
M16 Task 2 — builder `M16CaseRecord`: quan sát có cấu trúc MỘT case đánh giá,
dẫn xuất TẤT ĐỊNH từ `AttemptObserver` + envelope `run_pipeline` THẬT (bất
biến #22) — KHÔNG tái dựng stage, KHÔNG đoán khi thiếu event. Exports:
`M16CaseRecord` (dataclass, ~27 field + `detail` mặc định `""`),
`build_m16_record`, `family_of_route`.
Tests: `test_m16_record.py`.
Notes: `family_of_route(route_id, expected_family=None)` suy family canonical
của MỘT route (selector token HOẶC concrete id trong CATALOG); route mang
nhiều `family_membership` (hiện chỉ `generic.rule_scene`) mà không có
`expected_family` tham chiếu → trả `"generic_dual"` (KHÔNG đoán bừa).
`harness.evaluate_item` (M16 Task 2) nhận tham số optional `record_sink` —
truyền list thì append một `M16CaseRecord` SONG SONG, không đổi `ItemResult`/
metric cũ một bit.

### `evaluation/m16_metrics.py` · Change impact: offline
M16 Task 3 — 17 metric tỉ lệ (bảng công thức KHOÁ theo brief §4) + failure
taxonomy 15 category (structured-only, multi-label) + aggregation (micro/
per-family/macro/confusion-matrix/failure-distribution/applicability-report)
trên `M16CaseRecord` — lớp SONG SONG với `EvalReport.metrics()`, KHÔNG
import/sửa `harness.py`. Exports: `MetricValue`, `RetryChannels`,
`quality_band`, 16 hàm `metric_<name>(records, m16_by_case=None) -> MetricValue`
(vd `metric_final_route_accuracy`, `metric_unsupported_recall`…),
`metric_retry_channels`, `classify_failures`, `failure_distribution`,
`confusion_matrix`, `applicability_report`, `MetricAggregate`,
`AggregateResult`, `aggregate(records, run_label, m16_by_case=None)`.
Tests: `test_m16_metrics.py`.
Notes: mọi metric tỉ lệ (+ #15 retry_channels) gate qua "product case" (không
`infra_error`, không route `ReachabilityLevel.INTERNAL_FIXTURE`) TRỪ #17
`production_evaluation_parity` (đo trên MỌI case CÓ CHỦ Ý — lọc product-case
sẽ tự-triệt-tiêu đúng tín hiệu nó phải bắt). `aggregate()` chỉ nhận
`run_label ∈ {"offline","live_baseline","live_postfix"}` (khác domain giá trị
với `live.py --label {baseline,postfix}` — hai khái niệm riêng, không lẫn).

### `evaluation/m16_offline_scripts.py` · Change impact: offline
M16 Task 5 — kịch bản provider OFFLINE (module DATA THUẦN, không import
pytest) cho TOÀN BỘ pool m16 (50 case): `CaseScript` (analysis/classify-seq/
simulate-seq đúng schema production) + `SCRIPTS` (map case_id → CaseScript) +
factory `build_scripted_provider` (async fake `call_gemini`, dispatch theo
marker trong `user_text`). Exports: `CaseScript`, `SCRIPTS`,
`build_scripted_provider`.
Tests: `test_m16_offline_eval.py` (chạy qua `harness.evaluate_item` →
`run_pipeline` THẬT, bất biến #22 — script chỉ cấp analysis/classify/config,
validator thật chấm).
Notes: đường đi CỐ ĐỊNH cho case đa-nhánh ghi rõ trong docstring module (vd
`m16-nm-hex-gap` nhánh A gate ownership, `m16-cr-positional-fail` nhánh (a)
fail-closed, `m16-vb-binary-overrange` phủ nhánh retry) — đối chiếu notes
từng case ở `datasets/m16_catalog.py`, KHÔNG đoán.

### `evaluation/m16_artifacts.py` · Change impact: offline
M16 Task 6 — builder THUẦN cho 5 artifact JSON máy-đọc (`docs/evaluation/m16/`),
mọi hàm trả dict/list JSON-serializable, KHÔNG side-effect file. Exports:
`build_case_matrix`, `build_coverage_report`, `build_offline_results`,
`build_metrics_artifact`, `build_failure_ledger`, `run_offline_and_build_all()`
(chạy TOÀN pool m16 qua `evaluate_item`/`run_pipeline` thật với provider
scripted — Task 5 — monkeypatch THỦ CÔNG `pipeline.call_gemini`, tự khôi phục
trong `finally`, chạy được cả trong pytest lẫn ngoài pytest).
Tests: `test_m16_artifacts.py` (sync-lock so khớp JSON đã commit).
Notes: `_outcome_matches_expectation` (private, module-level) là luật DUY
NHẤT xác định "outcome khớp expectation" (unsupported↔refused;
supported↔ok+final_route đúng) — M16 Task 7 (`live.py --resume-from`) IMPORT
TRỰC TIẾP hàm này để tái dùng nguyên văn, không phát minh luật mới (không có
vòng import: module này không import `live.py`).

### `evaluation/datasets/m16_catalog.py` · Change impact: offline
M16 Task 4 — pool đánh giá ĐẦU-CUỐI toàn danh mục: 50 case phủ 14 concrete
target / 8 capability family, mỗi case gắn `m16=M16Expectation` qua 6
archetype (`explicit_positive`/`paraphrase_positive`/`valid_boundary`/
`near_miss_gap`/`cross_family_recovery`/`authority_control`). Exports:
`M16_ITEMS`, `M16_REFERENCED_CASES` (registry case pool CŨ tham chiếu vào
coverage matrix M16 — không chép lại text đề).
Tests: `test_m16_dataset.py`.
Notes: đăng ký vào `POOLS["m16"]`/`NEW_POOLS["m16"]` ở CUỐI
`datasets/__init__.py` (import đặt SAU khi `check_admission` đã định nghĩa —
phá vòng `m16_catalog→m16_schema→datasets.check_admission`, xem comment tại
chỗ). Mỗi case gắn tag `"m16_offline"` (luôn có) + `"m16_catalog_live"` (CHỈ
khi `m16.live_eligible`) — `live.py` đăng ký hai suite cùng tên qua
`select_suite`. KHÔNG sửa `dataset.py` (30 case đóng băng) hay 4 pool cũ.

### `scripts/generate_m16_artifacts.py` → `docs/evaluation/m16/*.json` (M16) · Change impact: offline
Generator chạy TAY: gọi `m16_artifacts.run_offline_and_build_all()` (chạy
TRONG-PROCESS toàn pool 50 case qua production pipeline + provider scripted,
KHÔNG mạng thật) rồi ghi 5 file JSON committed (`m16-case-matrix.json`,
`m16-coverage-report.json`, `m16-offline-results.json`, `m16-metrics.json`,
`m16-failure-ledger.json`), mỗi file bọc `{schema_version, dataset_version,
run_label:"offline", run_meta:{git_commit, generated_at}, data}`. Cách chạy:
`cd backend && .venv/Scripts/python scripts/generate_m16_artifacts.py`
(Windows: set `PYTHONIOENCODING=utf-8` trước nếu console lỗi encode tiếng
Việt). Sync-lock: `test_m16_artifacts.py` — sửa pool/scripts/metric M16 mà
quên chạy lại generator → test ĐỎ (cùng anti-pattern #1 như
`generate_dsl_contract.py`/`generate_capability_descriptors.py`).

### `scripts/generate_m16_live_artifacts.py` → `docs/evaluation/m16/*-baseline.json` (M16 live) · Change impact: offline (đọc trace, KHÔNG gọi AI)
Generator chạy TAY SAU một live run: đọc trace JSON (`--out` của `live.py`),
rehydrate `M16CaseRecord`, `aggregate(run_label="live_<label>")` rồi ghi 4
artifact live + bản sao trace nguyên vẹn: `m16-live-results-baseline.json`,
`m16-live-metrics-baseline.json`, `m16-live-failure-ledger-baseline.json`
(CHỈ failure của run thật — không kèm injected_proofs offline),
`m16-live-coverage-baseline.json`, `trace-baseline.json`. Vỏ chung thêm
`model`/`provider`/`prefix_label` (baseline = pre-fix) + `usage` (logical
cases, HTTP, retry, transient) lấy từ budget THẬT trong trace. Cách chạy:
`cd backend && .venv/Scripts/python scripts/generate_m16_live_artifacts.py
trace-baseline.json`. KHÔNG sync-lock (artifact = run-output một lần, không
tái sinh tất định được như artifact offline); pre-fix baseline là BẤT BIẾN —
correction round (nếu có) ghi label khác, không ghi đè.

### `docs/evaluation/m16/` — artifact M16 (committed, machine-readable)
**Offline (sync-locked, tái sinh được):** `m16-case-matrix.json` ·
`m16-coverage-report.json` · `m16-offline-results.json` · `m16-metrics.json` ·
`m16-failure-ledger.json`. **Live baseline (pre-fix, run-output một lần):**
`trace-baseline.json` (24 case + budget 66 HTTP) · `m16-live-results-baseline.json`
· `m16-live-metrics-baseline.json` · `m16-live-failure-ledger-baseline.json` ·
`m16-live-coverage-baseline.json`. Đọc số liệu M16 → lấy từ đây, KHÔNG chép tay.

### `evaluation/live.py` · Change impact: full live
CLI live: **bắt buộc `ALLOW_LIVE_AI=1`**, `--suite <tên>` (xem hằng `SUITES` —
tại M16: `smoke`/`full`/`boundary`/`smoke_v2`/`flagship`/`L3`/`system_flow`/
`m10_route`/`m11_compose`/`m12_scan`/`m13_soundness`/`m14_sorting`/`m15_wave1`/
**`m16_offline`/`m16_catalog_live`**), `--case <id>` (M15 T11 hotfix — rerun CÓ
MỤC TIÊU 1 case qua id, không chạy lại cả suite), `--max-cases`,
`--max-api-calls`, `--max-retries`, (M16 Task 7) **`--label {baseline,postfix}`**
(mặc định `baseline` — chỉ ghi vào `trace["run_label"]`, không đổi cách chạy),
**`--out <path>`** (ghi trace JSON: `M16CaseRecord` mỗi case qua
`evaluate_item(record_sink=...)` + budget cuối run + `run_meta`), **`--resume-from
<path>`** (nạp trace cũ, bỏ qua case `status_final=="ok"` VÀ khớp expectation —
tái dùng nguyên `m16_artifacts._outcome_matches_expectation`, KHÔNG chế luật
mới — chạy lại phần còn lại, `trace["budget_cumulative"]` cộng dồn budget cũ +
mới). Tests: `test_live_budget.py`, (M16) `test_m16_live_runner.py`.
Notes (M15): suite `m15_wave1` (`datasets/capability.py`, tag `"m15_wave1"`) —
4 case W1 (hex-gap · octal-gap · binary-positive · binsearch-unsorted) + 2 case
`m14_sorting` cũ tái dùng tag (sorting-paraphrase · selection-near-miss); live
đã chạy tại Task 11 (nhật ký `CURRENT_STATE.md` §1: run 1 = 16 HTTP 5/6, rerun
hotfix = 3 HTTP 1/1, tổng 19/20, 0 retry, 0 transient).
Notes (M16 Task 7): 3 cờ mới KHÔNG đổi hành vi khi không truyền — đường không
cờ vẫn gọi `harness.run_eval` GỐC nguyên văn. `harness.py` ngoài phạm vi sửa
của Task 7 (`run_eval` không có tham số `record_sink`) nên khi cần trace,
`live.py` tự lặp qua `evaluate_item` (helper nội bộ `_run_eval_with_records` —
bản sao TỐI THIỂU vòng lặp `run_eval`, chỉ nối thêm `record_sink`) thay vì gọi
`run_eval`. Live vẫn **PENDING APPROVAL** — Task 7 chỉ mở khả năng chạy
(trace/resume/label), chưa có run thật nào.

### `main.py` · Change impact: offline (trừ khi đổi CACHE_VERSION/pipeline)
FastAPI: `POST /api/analyze`, `POST /api/edit`, `POST /api/explain`,
`GET /api/manifest`, `GET /api/health`. Exports: `app`, `CACHE_VERSION`,
`_cache_key`, `_cache_lookup`. Tests: `test_api.py`, `test_edit.py`.
Notes: **bump `CACHE_VERSION`** khi đổi policy classify/manifest/prompt.

### `conftest.py` · Change impact: offline
**Hard guard**: patch transport mạng thật của httpx + gỡ `GEMINI_API_KEY`.
Exports: `BLOCK_MESSAGE`, `live_allowed`. Tests: `test_offline_guard.py`.

---

## Frontend — `frontend/src/`

### `simulations/types.ts` · Change impact: offline
Hợp đồng module. Exports: `SimulationModule`, `SimAction`, `TimelineCapability`,
`WorkspaceProps`, `ConfigResult`, `SimulationEnvelope`, `Domain`, `InteractionMode`,
`VisualMode`, `PredictionCapability`, `EditCapability`.
Notes: capability **optional** (vd `timeline?`) là cách mở rộng chuẩn. M8:
`renderers?: Partial<Record<VisualMode, ComponentType>>` — renderer theo mode,
"2d" mặc định là `Workspace` (tương thích ngược). (`applications?` của M9-UX1
đã GỠ ở M9-UX2 — thẻ "Ứng dụng" tay quá nông; transfer-of-learning thật là
việc tương lai cần duyệt riêng.)

### `simulations/renderer.ts` · Change impact: offline
M8 — chọn renderer từ HỢP ĐỒNG module (không switch-case id). Exports:
`rendererFor`, `availableVisualModes` (= tuyên bố ∩ có renderer thật),
`effectiveVisualMode` (rơi an toàn về "2d"). Tests: `visual-mode.test.tsx`.

**W4B-2R — CHỦ SỞ HỮU CHÍNH SÁCH BIỂU DIỄN** cũng ở đây (đừng đẻ file thứ hai):
`RepresentationPolicy` = `"2d_only" | "3d_only" | "2d_and_3d_justified"`,
`representationPolicyOf(module)` (phân loại — MÔ TẢ) và
`representationPolicyProblems(module)` (phán quyết hợp lệ — trả mảng lý do, rỗng
= hợp lệ). **DẪN XUẤT, không thêm trường vào 22 module**: chính sách đã nằm
trong `supportedVisualModes` (được cấp mode nào) + `threeD.role` (chiều sâu
nghĩa gì); trường thứ ba là nguồn sự thật thứ hai phải đồng bộ tay
(anti-pattern #1). **Điều kiện của `2d_and_3d_justified` là
`threeD.role === "pedagogical"`, KHÔNG phải sự tồn tại của renderer** — đây
chính là phép kiểm hạ `network.packet_routing` về 2D_ONLY (nó tự khai
`architectural_poc`). Danh mục: **21 / 0 / 1**. Guard toàn danh mục **dẫn xuất
từ registry**, không chép tay 22 tên: `representation-policy-w4b2r.test.ts`.
⚠️ File này chỉ được import `./types` — guard khoá đúng danh sách import để chính
sách không bao giờ đọc được tiêu đề/đề bài.

### `simulations/observe-lifecycle-w4b2r.test.ts` · Change impact: offline
Khoá TOÀN DANH MỤC ba luật vòng đời Quan sát — cả ba **đã đúng từ trước**, wave
W4B-2R chỉ đo và khoá: `LEARNER_INITIATES_FIRST_RUN` (`playing` chỉ nhận `true`
qua `setPlaying`; mọi nhánh nạp đặt `false`), `CANONICAL_RUN_CAN_COMPLETE_
WITHOUT_PREDICTION` (chạy trọn timeline MỌI envelope offline bằng `nextStep`,
`prediction` vẫn `null`), `OBSERVE_REQUIRES_NO_ANSWER` (`nextStep` không đọc
`prediction`; `submitPrediction` không đụng cursor). Mở file này trước khi định
thêm bất kỳ cổng nào chặn Play.

### `simulations/learner-gate.ts` · `learner-gate.test.ts` · Change impact: offline
Sở hữu **phép chiếu ngữ nghĩa DOM → trạng thái** và cổng tương tác dùng chung cho
MỌI mô phỏng sinh ra — không nhánh riêng cho miền nào.
`projectSemanticDom(html, spec)` đọc **chữ người học nhìn thấy** trong `<text>`,
khoá theo `data-obj` mà `ui.tsx::renderObject` gắn; `data-item` phân biệt *dữ liệu*
với *chú giải* (`← TOP`, `FRONT`/`REAR`, `[0] [1]`) — thiếu vế này guard chấm
`["{","← TOP"]` là nội dung ngăn xếp. Collection RỖNG đọc theo `LA_COLLECTION`:
vắng `data-item` = rỗng thật, không phải "đọc chú giải".
`kiemTransport` chụp bảng trạng thái khi đi xuôi rồi **lùi từng bước so lại**, nên
engine nào tính lùi bằng hoàn tác gần đúng sẽ trượt; kèm SCRUB nhảy cóc và kẹp
biên (`kiemBienTimeline`). `findPlaceholderLeaks` + `zeroKhongBiNuot` giữ cả hai
chiều của bẫy `?? 0` (chưa-có không được thành `0`; `0` thật không được thành `—`).
Gate này đã bắt được HAI lỗi sản phẩm mà mọi cổng cũ bỏ lọt (xem `ui.tsx`,
`model.ts::applyStepAction`). Thêm primitive mới ⇒ thêm nó vào `MIEN` của test.

### `simulations/registry.ts` · `legacy.ts` · Change impact: offline
Đăng ký/tra module theo id; `legacy.ts` nâng `algorithm_id` cũ thành envelope.
Exports: `registerSimulation`, `getSimulation`, `listSimulations`,
`clearRegistryForTest`; `toSimulationId`, `fromLegacyAnalysis`.

### `state/store.ts` · Change impact: offline
Zustand, **mù domain**: `active {moduleId, envelope, config, state}` + timeline
actions + `dispatch` + `resetSim` + `replaceSimulation` (M7.14, sau edit) +
`prediction`/`submitPrediction` (M8-PRE-LIP) + `visualMode`/`setVisualMode` (M8 —
lát TRÌNH BÀY: đổi mode không đụng active/cursor/prediction; loadEnvelope reset
về "2d") + M9-UX1: `view` (home/workspace/history), `history` (mirror), `goHome`,
`openHistory`, `reopenFromHistory` (ZERO-AI), `removeHistoryItem`, `clearHistory`;
`loadEnvelope(env, sampleId?, originalInput?)` ghi lịch sử; bước/visualMode
touch tiến độ. Tests: `registry.test.ts`, `visual-mode.test.tsx`,
`view-history.test.tsx`.
Notes: **không** đặt logic domain vào store. Zustand v5 trả INITIAL state khi
renderToString (SSR) — component cần test SSR phải nhận dữ liệu qua PROPS
(ngoại lệ: Home LÀ initial state nên SSR App test được). M13 (Task 6): gọi
`mod.init` được bọc try/catch **domain-blind** (bắt `Error` trần, không riêng
`GenericExecutionError`) — `init` ném lỗi (vd operand không có nguồn giá trị lọt
qua tới runtime) → `analysisError` tiếng Việt thân thiện, `active` giữ `null`
(fail-closed, không dựng cảnh một phần).

W4B-2Z: `sessions`/`activeSessionId` + `newSession`/`switchSession`/`closeSession`
— chuyển phiên là KHÔI PHỤC THUẦN (`activate()` trả về đúng object state cũ; 0
`fetch`, 0 `init`, 0 `validateConfig`). **Đừng "dọn cho gọn" bằng cách gọi
`loadEnvelope` khi chuyển phiên**: fetch vẫn 0 nên guard mạng không thấy gì,
nhưng state bị dựng lại và what-if của học sinh biến mất. Tests:
`sessions.test.ts` (spy `init`/`validateConfig` trên MỌI module đang mở).

W4B-3A: thêm `exploreOpen`/`setExploreOpen` — cờ TRÌNH BÀY thứ hai, cùng tầng
`challengeOpen`, cũng mù domain. **Hai cờ chứ không một** vì hai chế độ khác
nhau ở chỗ ai phán xét: Thử thách đưa cam kết qua `predict.check` (engine phán
đúng/sai), Khám phá đưa thao tác qua `module.apply` (không phán gì). Cả hai:
reset khi `loadEnvelope`/`resetSim`/`reset` (M18-UI: không còn lưu theo phiên).
Trước wave này cờ là `useState` cục bộ tên `labOpen` trong hai renderer miền.

### `state/history.ts` · Change impact: offline
M9-UX1 — lịch sử học BỀN (localStorage, schema v1, `algosim.history.v1`).
Exports: `createHistoryStore` (inject storage — test được), `historyStore`
(singleton; node/SSR → shim in-memory), `historyIdOf` (hash tất định
simulation_id+config → dedup), `HistoryItem`, `HISTORY_SCHEMA_VERSION`,
`HISTORY_MAX_ITEMS` (30, evict theo lastViewedAt), `__resetHistoryForTest`.
Notes: lưu envelope ĐÃ VALIDATE (mở lại zero-AI — bất biến #17) + lastCursor/
visualMode; CHỈ trường whitelist — không secret/blob/prediction/branch/camera;
entry hỏng/version lạ bỏ qua êm. Tests: `history.test.ts`.

### `components/HomeView.tsx` · `HistoryView.tsx` · `data/offline-catalog.ts` · offline
M9-UX1 — Home (hero + composer + gợi ý chọn lọc + "Tiếp tục học" ≤5) và trang
Lịch sử (đủ item, Mở lại/Xóa/Xóa tất cả). `offline-catalog.ts`: danh mục mẫu
hợp nhất (`offlineCatalog` — ĐẦY ĐỦ kể cả fixture, `publicCatalog` — chỉ
Tin học THPT cho học sinh (M9-UX2, nguyên tắc COVERAGE §2.7), `starterEntries`
(6), `DOMAIN_COLOR/LABEL`) dùng chung Home + InputPanel. `App.tsx` route theo
`store.view`; toggle panel chỉ trong workspace. Exports thêm:
`formatRelativeTime` (HomeView). **M9-UX3**: card gợi ý HÀNG NGANG (tranh trái /
chữ phải → mọi card cao bằng nhau bất kể tiêu đề); "xem tất cả" GOM NHÓM theo
domain (nhóm đã nói domain → card trong nhóm bỏ nhãn, tránh nhiễu); `InputPanel`
dùng `publicCatalog()` (KHÔNG phải `offlineCatalog()`) và không lộ `simulation_id`
ra UI — luật phạm vi M9-UX2 nay áp ở MỌI bề mặt học sinh thấy, không riêng Home.
Tests: `catalog.test.tsx`.

### `components/SamplePreview.tsx` · Change impact: offline
M9-UX2 (mở rộng M9-UX3) — preview SVG TĨNH cho starter card (thuần trình bày:
không engine, không fetch, dữ liệu minh hoạ cố định). Exports: `SamplePreview`,
`PreviewKind`, `previewKindOf(simId, explicit?)` — kind suy từ simulation_id hoặc
metadata `preview` tường minh của mẫu (KHÔNG từ tiêu đề); id lạ → "generic".
**M9-UX3 — LUẬT: một tranh = một cơ chế = một bài.** 13 kind: algorithm-bars
(find_max) · bars-min · sum-threshold · count-threshold · linear-scan ·
search-range (binary_search) · sort-swap (bubble) · insertion-lift · binary-bits ·
network-path · logic-gate · web-structure · generic. Trước M9-UX3, 8 bài thuật
toán chen vào 3 tranh và **2 tranh dạy SAI cơ chế** (linear_search mượn
trái/giữa/phải của binary; insertion mượn mũi tên đổi chỗ của bubble) — khoá lại
bằng test "không hai bài thuật toán nào dùng chung một tranh".
Tests: `catalog.test.tsx`.

### `components/ProblemInput.tsx` · Change impact: offline
M9-UX4 — MỘT dạng duy nhất (pill: ô tự cao dần, kẹp tệp + nút gửi nằm TRONG ô,
Enter gửi / Shift+Enter xuống dòng) và **chỉ sống ở Trang chủ**. M9-UX3 từng có
hai vỏ hero/compact vì `InputPanel` cũng nhúng composer; M9-UX4 gỡ composer khỏi
workspace nên vỏ `compact` hết người dùng → gỡ prop `variant`, không nuôi code
chết. `SAMPLE_PROMPTS` hiện thành chip bấm được dưới ô nhập (điền sẵn đề, học
sinh vẫn phải tự bấm gửi — không lén tiêu lượt gọi AI). Tests: `catalog.test.tsx`.

### `components/icons.tsx` · Change impact: offline
M9-UX5/UX6 — bộ icon SVG nét đậm bo tròn (stroke 2.4, `currentColor`, khung 24×24).
**LUẬT: icon trong UI phải là component ở file này** — CẤM emoji/ký tự Unicode.
Đã cháy: `◧` (U+25E7) không có glyph trong font Windows → ô vuông rỗng trên header.
Khoá bằng `components/ui-hygiene.test.ts` (**quét MÃ NGUỒN**, không quét HTML render).

### `components/LibraryView.tsx` · Change impact: offline
M9-UX5 — trang **Thư viện** (`store.view === "library"`): danh mục ĐẦY ĐỦ, gom nhóm
theo domain + lọc. Nhà riêng của danh mục → Home không phải gánh nó nữa nên
**không bao giờ phình**. M9-UX7: cũng thay luôn vai trò của `InputPanel` (đã gỡ).

### `scripts/audit-layout.mjs` · Change impact: offline (cần `npm run dev`)
M9-UX7 — **soát bố cục trên Chrome thật** qua CDP: `npm run audit:layout`.
Đo 5 thứ trên cả 4 route: icon lệch tâm · chữ bị cắt · phần tử đè nhau · tràn khỏi
khung cha · khoảng cách ngoài thang 4px. Có **dấu vân tay trang** (đo nhầm route →
thoát mã 2) và đã được **chứng minh bằng tiêm lỗi giả**. Đây là thứ DUY NHẤT bắt
được lớp lỗi CSS im lặng (vd `var(--sp-2xl)` không tồn tại) — vitest không chạy CSS.

### `scripts/diagnose-responsive.mjs` · Change impact: offline (cần `npm run dev`)
**Chủ sở hữu phép đo responsive** — trục chiều rộng **và chiều cao**, before/after.
W4B-1A mở rộng: viewport tham số hoá (`--viewports 1366x768,1536x864`), checkpoint
timeline (`--checkpoints initial,mid,final`), chế độ quét danh mục
(`--fixture catalog|stress|all`), dấu vân tay trang (sai route → **thoát 2**),
và **acceptance chấm máy có mã thoát** (vi phạm → **thoát 1**): `HORIZONTAL_OVERFLOW`
· `CONTENT_HIDDEN_IN_PANEL` · `CONTROL_OCCLUDED` (elementFromPoint) ·
`CONTROL_OFFSCREEN` · `TEXT_CLIPPED`.

**Bất biến bố cục nó khoá** (hai cái, hai trục):
1. **Chiều cao** — trang phải cuộn được khi nội dung cao hơn viewport; nội dung
   **không** được biến mất vào thanh cuộn nội bộ của `.panel-center`. Lớp lỗi mà
   mọi breakpoint theo chiều RỘNG không bao giờ bắt được (`global.css` khối
   `@media (min-width: 1101px) and (max-height: 900px)`).
2. **Chiều rộng** (W4B-1A.1) — `LAYOUT_NOT_USING_VIEWPORT`: `.app-layout` phải
   dùng gần trọn khung cha, hoặc đạt đúng `max-width` đã khai khi màn rộng hơn.
   Bề rộng mong đợi **dẫn xuất từ `css_max_width` đo được**, không hard-code.
   Lớp lỗi này guard đầu tiên không thấy: năm điều kiện cũ đều hỏi "có tràn / có
   bị giấu", không cái nào hỏi "app có DÙNG màn hình không".

**Cô lập phiên (W4B-1A.1)** — mỗi lượt chạy sở hữu Chrome riêng:
`--remote-debugging-port=0` rồi đọc cổng thật từ `DevToolsActivePort` trong
profile của chính nó; PID/cổng/profile ghi vào `session` của artifact. Dấu vân
tay kiểm **danh tính** (`store.active.moduleId` so với target đang yêu cầu), không
chỉ hình dạng DOM → lệch thì `WRONG_SIMULATION_OR_FIXTURE` + thoát 2. Mọi lối ra
(thành công · exit != 0 · throw · unhandled rejection · SIGINT/SIGTERM) đi qua
`shutdown()`. Cờ `--self-test-throw` tiêm lỗi tái lập được để chứng minh đường
dọn dẹp. **Lý do tồn tại**: cổng cố định 9337 + thiếu teardown từng khiến hai
lượt chạy song song bám chéo và sinh artifact gắn nhãn sai fixture.

Lệnh hồi quy (0 API call, cần dev server):
```bash
cd frontend && node scripts/diagnose-responsive.mjs --port 3000 --fixture all \
  --routes workspace --checkpoints initial,mid,final --viewports 1366x768,1536x864 --out <dir>
```
Bằng chứng + injected-fault proof: `docs/evaluation/m17/w4b1a-responsive/`.

### `scripts/fixtures.mjs` · Change impact: offline
**Bộ fixture DÙNG CHUNG** cho runner Chrome/CDP (dữ liệu thuần, 0 side effect).
Tách khỏi `visual-stress-audit.mjs` ở W4B-1A — script đó nay `import`, dữ liệu
không đổi. Lý do tồn tại: `offlineCatalog()` của app chỉ phủ **13/22** target,
nên bản soát bố cục cần nguồn bù. Thêm fixture ở ĐÂY, không chép sang runner
khác. Cùng `offlineCatalog()` phủ đủ **22/22** target.

### `components/SessionCard.tsx` · Change impact: offline
M9-UX4 — MỘT thẻ cho phiên đã học, dùng chung `HomeView` ("Tiếp tục học") +
`HistoryView`. Exports: `SessionCard`, `progressOf(item)`.
**Tiến độ SUY TỪ ENGINE TẤT ĐỊNH**, không persist: `progressOf` gọi
`getSimulation(item.simulationId).init(envelope.config)` → `timeline.stepCount`.
Lý do không lưu `totalSteps` vào `HistoryItem`: schema v1 đã nằm trong máy người
dùng, bump version sẽ **xoá sạch lịch sử đang có**. Module KHÔNG khai `timeline`
(exploratory, vd `logic.and_gate`) → trả `null` → **không có thanh tiến độ** (UI
dẫn xuất từ capability, không bịa "1 bước"). Envelope lạ/hỏng → `null`, không ném.
**KHÔNG BAO GIỜ render `simulationId`** ra UI (rò rỉ cũ của `HistoryView`).
Tests: `catalog.test.tsx`.

### `simulations/domains/generic/model.ts` · Change impact: offline
Engine + kiểu DSL v1 (mirror manifest). Exports (chính): `SimulationSpec`,
`GenericState`, `InteractionFeedback`, `valuesOf`, `buildTimeline`, `currentFrame`,
`initialBase`, `applyMove`, `layoutPositions`, `dragTargets`, `findFreePosition`,
`applyEditedSpec`, `visibleContentBounds`, `objectRole`, `inspectorGroups`,
`STRUCTURAL_TYPES`, `TEMPORAL_PROCESS_TYPES`, `DRAG_TARGET_TYPES`, (M13)
`GenericExecutionError`, `displayLabel`, (vNext) `PENDING_DISPLAY`,
`applyStepAction`.
Tests: `generic.test.ts`, `patch.test.ts`,
`__tests__/pending-binding-fidelity.test.tsx`,
`__tests__/stack-semantic-frame-acceptance.test.tsx`.

**vNext 2026-08-23 — `Frame.values`, kênh TRẠNG THÁI THEO BƯỚC.** Trước đó
nhánh `step_sequence` của `buildTimeline` chỉ đẩy ra lời kể + highlight, còn
`valuesOf(spec, state.base)` hằng số suốt timeline ⇒ narration kể "đẩy '[' vào
ngăn xếp" trong khi hình ngăn xếp rỗng ở MỌI khung (đã chụp màn hình). Validator
thì vẫn nhận và giữ `value`/`to_index`/`indices` từng bước — hợp đồng hứa, engine
vứt. `applyStepAction` gấp `set_value`/`push`/`pop`/`move_pointer` lên một bản đồ
chạy dần (**allowlist đóng, không `eval`**; hành động lạ ⇒ không đổi gì), chụp
vào `Frame.values`. `undefined` ⇒ lùi về `state.base` như cũ.
`PENDING_DISPLAY` (`—`) là dấu CHƯA CÓ BINDING, tách hẳn giá trị 0 thật —
`ui.tsx` từng viết `o.value ?? 0` nên ô chưa có dữ liệu hiện số `0` như thật.
Notes (M13 §3.4): `valuesOf` port ĐÚNG bản forward-resolve ba trạng thái của
`generic_engine.py::values_of` (đối chiếu 1:1 — port bản ĐÃ SỬA lỗi control-flow
`pending`, xem note ở entry backend) — KHÔNG còn seed 0. `GenericExecutionError`
mang `code: "invalid_numeric_source" | "missing_weight" |
"unresolved_dependency_after_bound" | "non_finite_numeric_value"`, song song
`GenericEvaluationError` backend; `store.ts` bọc `mod.init` để bắt lỗi này
fail-closed (xem entry `state/store.ts`). `displayLabel(spec, id)` (Task 11) —
nhãn hiển thị learner-facing: sanitize khi label **thiếu** ∨ label **=== id**
(ca lộ id kỹ thuật kiểu Dijkstra) ∨ label **dạng kỹ thuật** (snake_case/kebab-case
thuần, không khoảng trắng) → thay bằng tên tiếng Việt theo type (+ số thứ tự nếu
trùng type); label tiếng Việt thân thiện GIỮ NGUYÊN, không sanitize oan.

### `simulations/domains/generic/validate.ts` · Change impact: offline
Validator TS song song `dsl/validator.py`. Export: `validateGenericConfig`.
Notes: tách khỏi `index.ts` (M7.14) để `patch.ts` dùng chung, tránh vòng import.
M13 (Task 5): import trực tiếp `./dsl-contract.json` (KHÔNG hằng viết tay) để
kiểm operand coherence + role-typing — mirror `validator.py` từng dòng (cùng
thông điệp lỗi `"không có nguồn giá trị"`/`"vai trò"` để test hai tầng khớp
nhau). Đổi luật coherence = sửa `manifest.py` + chạy lại generator, KHÔNG sửa
tay ở đây.

### `simulations/domains/generic/patch.ts` · Change impact: offline
Mirror `simulation/patch.py`. Exports: `validateAndApplyPatch`, `PatchOp`,
`PatchResult`, `MAX_OPS`. Tests: `patch.test.ts`.

### `simulations/domains/generic/edit-policy.ts` · Change impact: offline
Mirror `simulation/edit_policy.py`. Exports: `editPolicyOf`,
`checkOpsAgainstPolicy`, `EditPolicy`, `EditFamily`, `EditUiAction`,
`ADDABLE_TYPE_LABEL`, các hằng reason_code. Tests: `edit-policy.test.ts`.

### `simulations/domains/generic/EditBar.tsx` · Change impact: offline
Thanh công cụ sửa — component RIÊNG để state nhập liệu KHÔNG re-render SVG
(nguyên nhân lag đã đo ở M7.14). Exports: `EditBar`, `EditTool`, `toolHint`.
Tests: `mode-switch.test.tsx`.

### `simulations/domains/generic/index.ts` · Change impact: offline
`makeGenericModule()` — validateConfig/init/apply/timeline/getExplainContext.
Notes: `init` dựng `pos` từ layout; `apply` xử lý `toggle` + `move`.

### `simulations/domains/generic/ui.tsx` · Change impact: offline
`GenericWorkspace` (SVG + layering + fit view + edit toolbar) và `GenericInspector`.
Notes: **toolbar edit hiện đang vô điều kiện** — M7.14D sẽ dẫn xuất từ EditPolicy.
Trạng thái edit (`editMode`/`editTool`/`editText`) là useState cục bộ.

### `simulations/domains/{algorithm,logic,binary,network}/` · Change impact: offline
4 module chuyên biệt, engine riêng, **không** dùng DSL: what-if branch
(`core/algorithms.ts`), truth table, bits⇄decimal, BFS route.
Notes: **không** module nào render edit toolbar (đúng thiết kế).

### `simulations/domains/algorithm/decision.ts` · Change impact: offline
M9-S1 — điểm quyết định theo CƠ CHẾ từng thuật toán. Exports: `decisionPointOf`
(câu hỏi + options + expectedId + evidence + consideration + expression — đáp án
DẪN XUẤT từ sự kiện trace kế tiếp), `consequenceOf` (câu nhân quả cho bước hệ
quả — CÙNG chuỗi evidence). Một nguồn nuôi cả `module.predict` lẫn dải nhân quả
trong Workspace → hỏi/chấm/trình bày không lệch nhau. binary_search hỏi ở bước
LẤY MID (3 lựa chọn trái/phải/found). Tests: `decision.test.ts`.

**Ba MÔ HÌNH TƯƠNG TÁC SÂN KHẤU** (W1/W2/W3B) cũng sống ở đây — tra tên trước khi
định viết cái thứ tư: `scanInteractionOf` (quét dãy: find_max/min · sum_if ·
count_if — nhãn theo cơ chế "Đặt X làm max mới"/"Cộng X vào tổng"/"Đếm X vào
nhóm"/"Bỏ qua phần tử này"), `searchInteractionOf` (linear_search ·
binary_search), `sortInteractionOf` (`kind` = compare-pair · select-candidate ·
shift-or-stop), `isScanFamily`/`isSortFamily`, và `stageInteractionsOf` — NGUỒN
ĐẾM DÙNG CHUNG cho "bước này có mấy vùng hành động", dùng bởi cả
`predict.presentedInStage` lẫn test bất biến. **Không mô hình nào mang
`correctActionId`/`evidence`/`expectedId`**: đáp án chỉ sống trong
`predict.check`. Tests: `scan-semantics-w3b1.test.tsx`,
`interaction-family-w1.test.tsx`, `interaction-family-w2.test.tsx`,
`interaction-family-sorting-w3b.test.tsx`.

**`searchSceneRegions(model, arrayLength) → SceneRegion[] | null`** (W4B-2I) —
ánh xạ `SearchAction.visualRole` sang **chỉ số cột thật** để học sinh bấm vào
chính vùng bị tác động thay vì một hàng nút. Ở ĐÂY chứ không ở renderer vì "nửa
trái là cột `trai..giua-1`" là **ngữ nghĩa thuật toán** (bất biến #6). ⚠️ Cẩn
thận ĐẢO NGHĨA: option `left` = nửa trái BỊ LOẠI ⇒ tìm tiếp ở nửa PHẢI; ánh xạ
tên-sang-tên là dạy ngược cơ chế. Trả `null` (⇒ hàng nút quay lại nguyên vẹn)
khi một vùng RỖNG hoặc hai hành động TRÙNG cột — **tất cả-hoặc-không**, vì nửa
vùng nửa nút là hai bề mặt cam kết. `SceneRegion` chỉ mang `id`/`label`/`indices`
(không đáp án). Tests: `scene-interaction-w4b2i.test.tsx`.

### `simulations/domains/algorithm/condition-param.ts`
W4B-4D — MIỀN ĐÓNG của ĐIỀU KIỆN, cho hai bài có điều kiện (`count_if`,
`sum_if`). `withConditionParam` nhận đúng hai tên (`condition.op`,
`condition.value`), trả config MỚI hoặc `null`; `thresholdRange` chốt ngưỡng
trong khoảng giá trị của CHÍNH dãy (ngoài khoảng thì kết quả bão hoà và mọi lần
kéo tiếp cho cùng một đáp số). Không chuỗi biểu thức, không AND/OR.

Vì sao có: `interaction-policy` khai hai bài này `mode: "hidden"` — kéo là hoán
vị, mà tổng/đếm bất biến theo hoán vị, nên kéo ở đó là trang trí. Kết luận ấy
vẫn đúng, nhưng nó bỏ hai bài lại với đúng một việc là cam kết từng bước, tức
chỉ hỏi được câu BÊN TRONG một điều kiện đứng yên. Đổi ngưỡng hỏi câu còn lại.
Bất biến (kéo vẫn tắt · hoán vị vẫn không đổi kết quả · đổi ngưỡng thì đổi) khoá
ở `explore-ownership-w4b3a.test.ts`.

### `simulations/domains/algorithm/interaction-policy.ts` · Change impact: offline
M9-S1 — chính sách what-if theo cơ chế (hết "một swap cho cả 8 bài"). Exports:
`whatIfPolicyOf`, `WhatIfPolicy`, `WhatIfMode` (free: bubble/insertion/selection — `insertion_sort` GIỮ `free` dù đã gác cổng: kéo vẫn là cơ chế đang học, chỉ đổi chỗ đặt · framed:
linear_search · challenge: find_max/min + binary_search · hidden: sum/count).
Mỗi policy kèm `rationale` (vì sao không trang trí). Gating theo `algorithm_id`
ngữ nghĩa. Tests: `interaction-policy.test.ts`, `algorithm-ui.test.tsx`.

W4B-3A: thêm `exploreLabel?` (nhãn lối vào KHÁM PHÁ — thao tác trực tiếp) tách
khỏi `challengeLabel` (lối vào CAM KẾT). Hai hàm THUẦN mới dựng câu mời:
`challengeEntryOf(policy, {inBranch, hasSurface})` và
`exploreEntryOf(policy, {canManipulate})` — module gọi ở `index.ts`, shell chỉ
đặt chỗ. `mode: "hidden"` (sum_if/count_if) KHÔNG khai `exploreLabel` ⇒ không
có lối vào Khám phá (kéo ở đó là trang trí, COVERAGE §2.6).

W4B-2I: **cả CHÍN target đều `experimentGated: true`** — `bubble_sort`/
`selection_sort` là hai bài cuối vào cổng, khép rollout 7/9 → 9/9. Từ đây không
còn bài nào bày vùng cam kết ở Quan sát, nên đừng đi tìm "bài làm chứng chưa gác"
(nó đã phải đổi ba lần rồi mới hết).

**File này là CHỦ SỞ HỮU KHAI BÁO của mọi luật bày công cụ cho học sinh.** Bốn
export nữa, tra ở đây trước khi nhét điều kiện vào JSX:

- `whatIfDragAllowed(state, {policyAllows, busy, last, answered})` (W3B §15) —
  luật *"cam kết trước, thí nghiệm sau"*: bước sắp xếp còn cam kết đang chờ thì
  HOÃN kéo. Hàm thuần ⇒ kiểm được không cần trình duyệt.
- cờ `experimentGated` (W4B-2B) — **CỔNG THÍ NGHIỆM**: bật thì cả vùng cam kết
  LẪN kéo đều nằm sau nút "Thí nghiệm". Tách khỏi `mode` có chủ đích: `mode` nói
  kéo có NGHĨA gì, cờ này nói công cụ đặt Ở ĐÂU. Đang bật cho 5 target:
  find_max · find_min · count_if · sum_if · insertion_sort. `hidden` được kiểm
  TRƯỚC cổng nên bật cờ KHÔNG bật kéo cho count_if/sum_if. **W4B-2I: nay bật cho
  cả CHÍN.**
- `commitmentSurfaceKind(commitmentVisible, sceneBound)` (W4B-2I) → `"none" |
  "scene" | "buttons"` — chủ sở hữu của **`NO_DUPLICATE_DETACHED_QUIZ_SURFACE`**.
  Tồn tại vì TIÊM LỖI chứng minh nó phải tồn tại: viết thẳng
  `actionsHidden={false}` trong `ui.tsx` làm hàng nút rời quay lại đứng song song
  với vùng bấm sân khấu **mà cả suite vẫn XANH** (`labOpen` cục bộ ⇒ SSR chỉ đi
  qua trạng thái ĐÓNG, nơi cả hai đều vắng). Hàm thuần ⇒ liệt kê được cả bốn tổ
  hợp không cần trình duyệt. Tests: `scene-interaction-w4b2i.test.tsx`.
- `commitmentSurfaceVisible(policy, labOpen)` (W4B-2D) — chủ sở hữu của bất biến
  **`COMMITMENT_SURFACE_COUNT <= 1`**. Trước đây luật này chôn trong JSX nên test
  phải chọn một bài LÀM CHỨNG chưa gác cổng, và đã phải đổi bài ba lần. Nay
  production và test gọi CÙNG hàm này. Tests: `interaction-family-w1.test.tsx`
  (ca A/B/D + phép đếm tự kiểm), `experiment-gate-w4b2b.test.tsx`.
`network/model.ts` exports: `bfsRoute`, `buildSteps`, `currentStep`, `typeLabel`,
`neighborsOf`, `hopDistance`, `NetworkState` (topology + route + steps + cursor
+ `baseline`). **M7.FREEZE**: bố cục KHÔNG còn trong state — `layout2d` sống
trong `network/ui.tsx` (renderer). Tests: `domains.test.ts` (khóa state
renderer-neutral), `network/render.test.tsx`.

**W4B-2I — THÍ NGHIỆM CẤU TRÚC** (target DUY NHẤT có what-if sửa MÔ HÌNH):
- `recompute(nodes, links, source, destination)` — **chủ sở hữu duy nhất** của
  phép tính lại `route + steps`; `init` và mọi what-if đều đi qua đây nên lượt
  đầu và lượt sau không thể chạy hai đường tính khác nhau.
- `applyNetworkAction` (`network/index.ts`) — `net_connect` · `net_disconnect` ·
  `net_reset`. **Fail-closed**: tham chiếu nút phải có thật, hai đầu khác nhau,
  ngắt thì liên kết phải đang tồn tại, nối thì phải chưa — sai ⇒ trả **NGUYÊN
  tham chiếu state cũ** (không ném, không sửa liều). Cố ý KHÔNG có thêm/xoá nút:
  đó là trình soạn đồ thị (§27).
- `isReachable` / `isModified` — dẫn xuất, không lưu cờ. `route: []` NAY HỢP LỆ
  = "không có đường đi"; `buildSteps` dựng đúng một bước với `packetAt` vẫn là
  nodeId thật (trước W4B-2I chỗ này NÉ`M`: `byId[route[0]]` → `undefined.type`).
- `state.baseline` — topology gốc đã validate; what-if **không bao giờ** ghi đè
  ⇒ `net_reset` là phép toán chứ không phải undo log.
- ⚠️ `validateNetworkConfig` **vẫn từ chối** config không tới được. Đó KHÔNG mâu
  thuẫn: mô phỏng do HỆ dựng là đúng-hoặc-từ-chối, còn HỌC SINH thì được phép
  làm đứt — đúng hai trục của `CORRECTNESS.md`. Đừng nới validator.
Tests: `network/whatif-w4b2i.test.tsx` (13 ca + 4 tiêm lỗi đã chứng minh đỏ).

### `simulations/domains/network/node-glyph.ts` · Change impact: offline
**W4B-2S — CHỦ SỞ HỮU "VAI TRÒ MIỀN → HÌNH DẠNG"** của `packet_routing`. Exports:
`nodeGlyph(type)` (hộp chuẩn 48×48: `outline` + `details[]` + `role`),
`GLYPH_BOX`, `endpointRoleOf(nodeId, source, destination)`, `EndpointRole`.
Khoá theo **`NodeType` do ENGINE sở hữu** — laptop / router có ăng-ten / tủ rack
/ switch nhiều cổng / đám mây nhà mạng. Hàm THUẦN, không React, **không màu**
(màu thuộc renderer, hình thuộc vai trò).
**Vì sao chỉ miền mạng, không phải framework icon toàn hệ:** audit W4B-2S đo cả
22 target và `packet_routing` là target DUY NHẤT vẽ nhiều vai trò KHÁC NHAU bằng
CÙNG một hình. Mảng/cây/đồ thị dùng hình trừu tượng là ĐÚNG (giá trị và đỉnh vốn
trừu tượng); logic đã có hình cổng; database đã dùng `<table>` thật; encapsulation
đã có tầng/phong bì. Đừng mở rộng file này thành "icon cho mọi domain".
`endpointRoleOf` tách **nguồn/đích** khỏi **loại thiết bị** vì một mạng có thể có
hai máy chủ — glyph không phân biệt nổi, nên đích có vòng ngắm kép riêng.
Tests: `semantic-roles-w4b2s.test.tsx` (phép thử **XOÁ HẾT CHỮ**: bỏ `<text>` mà
vẫn phải phân biệt được vai trò; 4 tiêm lỗi đã chứng minh đỏ).

### ~~`simulations/domains/network/ui3d.tsx`~~ — ĐÃ NGHỈ (W4B-2R)
Renderer 3D của `network.packet_routing` (M8) **đã gỡ khỏi kho mã** cùng
`render3d.test.tsx`. Lý do: chính module khai `threeD.role = "architectural_poc"`
+ `meaningOfZ = "bố cục, không mang nghĩa khái niệm"`, nên theo chính sách biểu
diễn W4B-2R nó không đủ tư cách bày toggle 2D/3D cho học sinh (`renderer.ts::
representationPolicyProblems`). Cơ chế của bài — topology + đường đi + khả năng
tới được — đọc trọn trên mặt phẳng.
**Đừng dựng lại nó để "cho có 3D".** Muốn thêm 3D cho một target thì điều kiện là
`threeD.role = "pedagogical"` kèm `meaningOfZ` nói được Z mã hoá BIẾN KHÁI NIỆM
nào; guard toàn danh mục sẽ chặn ngay nếu không.
Ba luật cũ sống ở đây **không mất**: state renderer-neutral của NetworkState nay
do `domains.test.ts` khoá trọn (danh sách khoá + cấm `positions/width/height` +
cấm giá trị pixel); kịch bản nghiệm thu 2D→dự đoán→3D→2D chuyển sang bài làm
chứng `network.protocol_encapsulation` (`m8-acceptance.test.tsx`, bài làm chứng
DẪN XUẤT từ chính sách chứ không viết cứng). `three` vẫn là dep runtime —
`encap-ui3d.tsx` dùng.

### `simulations/domains/network/encap-{model,ui,ui3d}.ts(x)` + `encap.ts` · offline
**M10 — 3D SƯ PHẠM: `network.protocol_encapsulation`** (module THỨ HAI của domain
network; đăng ký cùng `registerNetworkDomain`). `encap-model.ts`: engine tất định
9 bước, exports `buildEncapState`, `currentStep`, `pieceForComponents`, `LAYERS`,
`LAYER_LABEL`, `PROTOCOL_PIECES`, types `EncapConfig/EncapState/EncapStep/StepDelta`
(`{kind:add|remove|transmit|deliver, layer, componentIds[]}` — LINK+FCS nguyên tử).
State renderer-neutral (PDU = danh sách phân đoạn, KHÔNG toạ độ). `encap.ts`: module
(validate/init/timeline/predict/threeD=`pedagogical`); prediction dùng chung
`PredictionCapability`, LINK+FCS là MỘT đáp án gộp, chấm bằng engine. `encap-ui.tsx`:
2D (stack gửi/nhận). `encap-ui3d.tsx`: 3D **X = chiều truyền, Z = tầng giao thức**
(`layerDepth`/`sideX` pure, export để test), lazy code-split (~4.7KB), caption
meaning_of_z, WebGL fallback. Mẫu công khai `network-encapsulation` (Thư viện) +
preview kind `network-encapsulation`. Tests: `encap.test.ts` (engine+module+
prediction), `encap-render3d.test.tsx` (2D/3D/parity/metadata). **Không đụng
backend/pipeline; 0 gọi AI.** Re-verify: offline.

### `core/` (`algorithms.ts`, `trace-builder.ts`, `pseudocode.ts`, `types.ts`) · offline
Engine của domain `algorithm` (ngoài `simulations/` vì có trước registry).
**Không** dùng làm hạ tầng chung cho domain khác. M9-S1: narration ở BƯỚC QUYẾT
ĐỊNH là câu hỏi (không lộ đáp án sớm — hệ quả thuộc bước kế tiếp); phần tử đã
duyệt/không thỏa được mark `eliminated`; export thêm `OP_TEXT`.
`TraceBuilder` (M12) = **substrate thực thi tái dụng** cho MỌI engine trace
(cùng union `TraceEvent`); 8 engine specialized là 8 driver mệnh lệnh ~15 dòng
trên cùng substrate, KHÔNG phải 8 module rời.

### `core/program.ts` (M17 W2C) · offline
**Interpreter luồng điều khiển hữu hạn**, engine-owned — MIRROR của
`program_spec.py` + `validation/program.py`. Exports: `PROGRAM_VERSION`,
`PROGRAM_LIMITS`, kiểu `ProgramSpec`/`ProgramStatement`/`ProgramExpression`/
`ProgramVariable`/`CompletionState`, `validateProgramSpec(raw)`,
`programLines(spec) → {lines, lineOf}`, `renderExpression(spec, id)`,
`runProgram(spec) → {trace, completion, outputs}`.
Interpreter sở hữu TOÀN BỘ: môi trường biến, thứ tự chạy, kết quả điều kiện,
nhánh được chọn, số lượt lặp, biên dừng. **MỘT NGUỒN cho mã giả**: `programLines`
vừa sinh dòng hiển thị vừa trả `lineOf` mà interpreter dùng để gắn `Step.line`
⇒ highlight không thể trôi khỏi câu lệnh đang chạy.
Dùng lại `TraceBuilder`/`Step`/`Snapshot.vars` (không có trace builder thứ hai).
Chạm biên → `completion="limit_reached"` + câu "chưa kết thúc", KHÔNG treo.
Tests: `program.test.ts`. Consumer: `domains/algorithm/program-module.tsx`.

### `simulations/domains/algorithm/program-module.tsx` (M17 W2C) · offline
Adapter MỎNG quanh `core/program.ts` (cùng khuôn `scan-module.tsx`). Exports:
`makeProgramModule()`, `ProgramWorkspace`, `ProgramInspector`, `ProgramSimState`
({spec, trace, cursor, completion}). Đăng ký ở `registerAlgorithmDomain()`.
Dùng lại `PseudocodeView` + `VarsView` — KHÔNG tạo UI primitive mới. **2D-only**:
Z không mã hoá biến nào của chương trình nên 3D sẽ là chiều sâu giả (bất biến #18).
Renderer đọc `evaluate_condition`/`enter_branch`/`loop_iteration`/`output` từ
sự kiện bước — **không tự đánh giá lại** biểu thức (test khoá bằng bước "bịa").
Output hiện DẦN theo cursor; kết quả cuối chỉ hiện ở bước cuối.
Tests: `program-module.test.tsx`.

### `core/scan.ts` (M12) · offline
**Declarative Bounded Scan** — MỘT interpreter tất định, engine-owned, cho họ
bài single-pass trên mảng. Exports: `ScanSpec` (+ `ScanSeed/ScanCompare/
ScanUpdate/ScanMarking/ScanStop`), `runScan(spec, whatIf?) → Trace`,
`validateScanSpec(raw) → {ok, spec|error}`, `SCAN_VERSION`.
Interpreter sở hữu **toàn bộ** vòng lặp/tiến chỉ số/biên dừng (≤ n, non-Turing)/
sinh event/gọi `TraceBuilder`; spec chỉ chọn **enum ĐÓNG** (seed/compare/update/
marking/stop) + hằng đầu vào — **KHÔNG** while/guard/mutation/đệ quy/code. Chứng
minh (`scan.test.ts`): parity NGỮ NGHĨA (decisions + finalMarks + stepCount) với
`runAlgorithm` cho find_max/count_if/sum_if/linear_search — cùng interpreter,
spec khác, **0 primitive theo-thuật-toán**. `validateScanSpec` allowlist mọi
trường + coherence "quét trên GIÁ TRỊ phần tử". (M12-AI-SCAN) `scanPseudocode(spec)` — mã giả
5 dòng DẪN XUẤT từ spec; `runScan` gắn `Step.line`/narration từ CÙNG layout
(một nguồn, chống highlight trôi). Đã wire: module `algorithm.scan`
(`domains/algorithm/scan-module.tsx` — module thứ 9 của domain, adapter mỏng,
prediction/what-if HOÃN) + route NL backend (catalog `algorithm.scan`).
Specialized giữ nguyên làm oracle — KHÔNG thay thế. Mirror Python:
`simulation/scan_engine.py`.

### `components/ScanActionZone.tsx` · `SearchActionZone.tsx` · `SortActionZone.tsx` · offline
Ba VÙNG HÀNH ĐỘNG trên sân khấu — nơi học sinh CAM KẾT (W1/W2/W3B). Nhận `model`
từ `*InteractionOf`, phát `onAct(actionId)` lên `store.submitPrediction`, hiển
thị `feedback` từ `store.prediction`. **Không component nào tự chấm** — không
`correctActionId`, không so `=== "yes"`; có test quét mã nguồn khoá điều đó.
Nhận diện bằng `aria-label` ("Thao tác với biến tích luỹ" / "…với bước tìm kiếm"
/ "Thao tác sắp xếp") — hợp đồng với người dùng, ổn định hơn class CSS. Nút đã
chọn GIỮ vết ("✓ em đã chọn") sau khi chấm: nửa sau của vòng học phụ thuộc nó.

### `simulations/domains/algorithm/ui.tsx` — trạng thái TRÌNH BÀY · offline
`labOpen` = `useState(false)` **cục bộ trong `AlgorithmWorkspace`**, KHÔNG ở
store, không persist. Nó gác: kéo-thả (qua `dragAllowedByPolicy`) + vùng cam kết
(qua `commitmentSurfaceVisible`). ⚠️ SSR luôn thấy `labOpen = false`
(ARCHITECTURE_MAP §8 #13) ⇒ **trạng thái "Thí nghiệm đang mở" KHÔNG test được
bằng `renderToString`** — phủ bằng hàm thuần + runner trình duyệt. Dải nhân quả
(`decision-strip`) dựng theo VÙNG ĐANG HIỆN chứ không theo "bước có phải điểm
quyết định": QUAN HỆ thuộc Quan sát, chỉ NÚT CAM KẾT thuộc Thí nghiệm.

### `scripts/capture-w4b2b-experiment.mjs` · offline (cần Chrome + Vite)
Runner LUỒNG HỌC SINH qua CDP — khác `diagnose-responsive.mjs` (runner ĐO hình
học, không bấm nút). Chứng minh chuỗi: Quan sát không vùng cam kết → mở cổng
BẰNG BÀN PHÍM → cam kết sai/đúng qua `predict.check` → đóng cổng → timeline vẫn
chạy; cộng `JSON.stringify(active.state)` không đổi qua mọi lần bật/tắt trình
bày, và 0 rò rỉ đáp án trong DOM. Cờ: `--port --targets --out`. ⚠️ Chỉ tin kết
quả trên tiến trình Vite MỚI: server đã qua nhiều lượt HMR cho phán quyết sai
(đo được: store `view:"workspace"` mà React vẫn vẽ Home).

### `scripts/capture-w4b2i-interaction.mjs` · offline (cần Chrome + Vite)
Runner CDP của W4B-2I, hai chuỗi hành vi trong một lượt: (A) `binary_search` —
Quan sát 0 vùng bấm → mở Thí nghiệm → **3 vùng bấm trên chính các cột** (nửa
trái / phần tử giữa / nửa phải) → `svg` đổi `role` `img`→`group` → focus bàn
phím → bấm sai: `JSON.stringify(active.state)` KHÔNG đổi; (B) `packet_routing` —
tuyến gốc → ngắt chặng → **không tới được** → nối lại → **Về mạng ban đầu**.
Cờ: `--port --window --out`. Có **dấu vân tay trang** (`active.moduleId`, sai thì
thoát != 0).
⚠️ Hai cái bẫy đã dính trong chính wave này, đừng lặp lại:
(1) `evaluate` phải **thử lại** khi CDP báo `Promise was collected` — lần import
đầu làm Vite pre-bundle rồi RELOAD trang, huỷ execution context; coi đó là lỗi
sản phẩm là tố cáo nhầm. Có `warmup()` nạp trước đồ thị module nặng.
(2) Dừng bước theo nút "Thí nghiệm" là **SAI** — nút đó hiện ở mọi bước chưa
phải bước cuối, nên runner đứng ở bước 0 (không có điểm quyết định) rồi báo FAIL.
Mốc đúng là `.search-observe` (chỉ dựng khi `searchInteractionOf != null`).

### `simulations/domains/web/` — MÔ HÌNH CSS CÓ RÀNG BUỘC (W4B-2Z)
`web.style_model` — **BOUNDED_INTERACTIVE_ARTIFACT**, không phải trình soạn mã.
Files: `props.ts` (miền giá trị — mirror của `catalog.py::validate_web_style_config`),
`model.ts` (kiểu state), `apply.ts` (`applyStyleChange` fail-closed · `cssTextOf`
SINH từ state · `isModified`), `index.ts` (module), `ui.tsx` (bố cục chia đôi).

**Vì sao đây KHÔNG phải `code_experiment`** (vẫn DEFERRED — `ARCHITECTURE_MAP §10`):
spec/state KHÔNG chứa mã nguồn. Học sinh đổi **thuộc tính trong tập ĐÓNG**
(backgroundColor · color · fontSize · padding · borderRadius); mô hình tất định
sở hữu sự thật, trình duyệt chỉ VẼ LẠI state. Không `eval`, không `new Function`,
không iframe, không JS, không CSS passthrough. Tên/giá trị ngoài miền ⇒ no-op.
Về kiến trúc giống hệt `logic.and_gate`: đổi tham số → state → biểu diễn.

**Không khai `timeline`** ⇒ shell không dựng thanh phát (EXPLORATION_FIRST). Đây
là chỗ sửa lỗi cũ: đề HTML/CSS từng bị đẩy vào `generic.rule_scene` và dựng
thành "Bước 1/3 → hiện khung", tức BỊA một trục thời gian mà cơ chế không có.

Backend: `catalog.py::CATALOG["web.style_model"]` + `FamilyId.WEB_PRESENTATION`
+ mechanism `web_presentation.bounded_style_properties`
(`ResultAuthority.REPRESENTATION` — không có kết quả thuật toán nào được tính).
Dùng lại `set_param` sẵn có, KHÔNG đẻ SimAction riêng.
Tests: `web/bounded-model-w4b2z.test.tsx` (ranh giới bounded),
`web/contract-parity.test.ts` (**sync-lock FE≡BE từng giá trị**).

**Hợp đồng miền giá trị**: `app/validation/simulation.py::web_style_domain()` là
NGUỒN; nó đi ra `capability_descriptors()["bounded_domains"]`. `props.ts` là bản
sao (production FE không import artifact generated — M14 §C4 điểm 6), và
sync-lock so từng giá trị: bảng màu nền/chữ, biên số, **mặc định**, độ dài nội
dung. Mặc định phải khớp vì mẫu offline chỉ đi qua validate FE.

**DOMAIN_DATA_LITERAL ≠ DESIGN_SYSTEM_LITERAL**: mã màu trong `props.ts` là DỮ
LIỆU BÀI HỌC, không phải token giao diện. Token-hoá thành `var(--…)` sẽ phá
kiểm hai tầng. Đừng "sửa" chúng ở các pass thiết kế sau.

### `frontend/scripts/accept-workspace-w4b3b.mjs` — xem mục ở phần script bên dưới.

### `core/trace-builder.ts` — bổ sung W4B-3C
`clearVar(name)` — GỠ một biến TẠM khi thứ nó mô tả hết tồn tại. Không có nó thì
biến mô tả thao tác ĐANG DỞ sống tới hết trace và bước `done` tự mâu thuẫn:
`insertion_sort` tuyên bố đã sắp xong trong khi snapshot vẫn khai đang giữ một
phần tử, và renderer vẽ trung thành cái nó được kể (quân bài ngoài dãy + ô trống).
Chủ sở hữu là ENGINE — **đừng vá bằng `if (bước cuối) ẩn quân bài`**, đó là dạy
renderer nói dối hộ engine và để nguyên mâu thuẫn trong state gửi cho AI giải
thích. Tests: `core/terminal-truth-w4b3c.test.ts` (cả họ sắp xếp × 2 chiều +
quét toàn danh mục + bất biến "hold luôn có bước chèn phía sau").

### `data/samples.ts` · Change impact: offline
Mẫu LEGACY dạng `analysis` (tiền-envelope): `SAMPLES` được `offline-catalog.ts`
map qua `fromLegacyAnalysis`/`toSimulationId` thành `CatalogEntry`. Đây là nguồn
của tám bài thuật toán chuyên biệt trong danh mục. Mẫu MỚI không thêm vào đây —
thêm envelope thẳng vào `sim-samples.ts` (`OFFLINE_SAMPLES`).

### `data/sim-samples.ts` — bổ sung W4B-3D
Thêm mẫu cho **9 target chưa từng đo được trong trình duyệt**; nay 23/23 có mẫu.
Config lấy NGUYÊN VĂN từ fixture đã validate ở `authenticity-cross-lock.test.ts`
(và `program-normalized-envelope.json` cho `bounded_control_flow` — dạng chuẩn
hoá `program-2.0` KHÔNG chép tay được, bản viết tay đầu tiên bị validator từ
chối). `visibility` tách BẰNG CHỨNG khỏi QUẢNG BÁ: `algorithm.scan` là
`internal_fixture` — có mẫu để đo, không vào Thư viện vì trùng nghĩa với tám bài
chuyên biệt. Tests: `data/sample-coverage-w4b3d.test.ts` (mọi target
`ai_reachable_public` phải có mẫu · mọi mẫu phải `validateConfig`+`init` được ·
D≠E · `GROUP_ORDER` phủ mọi `Domain`).

### ~~`components/SessionTabs.tsx`~~ — ĐÃ GỠ (M18-UI)

**Nhiều phiên mở song song đã bị xoá khỏi sản phẩm.** Cùng đi: `SessionTabs.tsx`,
`session-tabs-w4b3b.test.tsx`, `state/sessions.test.ts`, các trường
`sessions`/`activeSessionId` + `newSession`/`switchSession`/`closeSession` +
`OpenSession` trong store, và ~5.2KB CSS `.session-tab*`/`.session-more*` cùng
biến thể lưới `.app-layout.has-tabs`.

**Vì sao gỡ.** Mở bài thứ hai không phải việc học sinh làm trong một tiết, và
dải tab nó sinh ra chiếm chỗ ngay trên sân khấu. Quan trọng hơn: nạp mô phỏng
vốn đã THAY phiên đang chọn, nên tab thứ hai chỉ xuất hiện sau khi bấm
"+ Mô phỏng mới" — tức không đường nào vào bài đi qua nó, mà nó vẫn phải được
nuôi (bố cục, tràn tab, lớp phủ màn hẹp, guard riêng).

**Điều kiện khiến việc gỡ chấp nhận được:** bài bị thay KHÔNG mất — `loadEnvelope`
ghi nó vào Lịch sử trước đó, và `reopenFromHistory` dựng lại từ envelope với
**0 gọi mạng**. Đây nay là đường DUY NHẤT quay lại một bài đã mở, nên bất biến
ZERO-AI của nó quan trọng hơn trước; khoá ở `state/workspace-lifecycle.test.ts`
(file thay `sessions.test.ts`, giữ lại ba bất biến không chết theo tính năng:
bài mới luôn mở ở Quan sát · Đặt lại đóng cả hai chế độ · đổi bài 0 gọi mạng).

⚠️ Khác biệt CÒN LẠI so với phiên: mở lại từ Lịch sử **dựng lại state từ
envelope** rồi tua tới `lastCursor`, nên thao tác what-if học sinh tự làm không
được khôi phục. Đó là cái giá đã biết của việc gỡ, không phải lỗi.

### `scripts/measure-composition.mjs` · offline (cần Chrome + Vite)
**ĐO bố cục, không cảm nhận** (W4B-2T §4). Với mỗi target chạy được offline, đo
trong Chrome: hộp bao **sân khấu** vs hộp bao **nội dung có nghĩa** (hợp của mọi
`svg`/`table` bên trong), mức dùng bề ngang/bề dọc, số **dải thông tin** quanh mô
phỏng (chú giải · thuyết minh · dải nhân quả · trạng thái tìm kiếm · kết quả ·
teaser · công cụ · khay giữ), và **TRÙNG NGHĨA ở bước cuối** (so tập từ ≥ 60%,
không so chuỗi — hai câu diễn đạt khác nhau vẫn là trùng). Cờ:
`--out --shots --window --port`.
⚠️ **Tỉ lệ dùng KHÔNG phải điểm chất lượng.** Cây cần khoảng thở, bit gom cụm là
đúng, `decimal_to_binary` 17% là ca DISCONFIRMING hợp lệ. Con số là dữ kiện để
phân loại, đừng biến thành mục tiêu tối ưu.
⚠️ Biết trước: encap 2D dựng bằng `div` nên không có `svg/table` ⇒ hộp bao trả
`null`. Đó là giới hạn của phép đo, không phải lỗi sản phẩm.

### `scripts/capture-w4b2r-representation.mjs` · offline (cần Chrome + Vite)
Runner CDP của W4B-2R — chứng minh CHÍNH SÁCH BIỂU DIỄN + vòng đời Quan sát trên
**7 bài làm chứng chọn theo CƠ CHẾ** (§31: tìm kiếm · sắp xếp · logic · hệ cơ số
· cảnh DSL · mạng đổi chính sách · mạng 3D sư phạm), không chọn theo ảnh ai gửi.
Mỗi bài kiểm ba việc: **READY/PAUSED** sau khi nạp (không tự chạy) · **toggle
2D/3D chỉ xuất hiện khi `representationPolicyOf` = `2d_and_3d_justified`** ·
chạy **trọn** canonical bằng nút Tiến với `prediction` vẫn `null`. Sidecar ghi
policy/renderer owner/timeline/capability đọc THẲNG từ store + `renderer.ts`,
không suy từ DOM. Cờ: `--port --window --out`.
⚠️ Dùng lại `warmup()` + thử lại `Promise was collected` của
`capture-w4b2i-interaction.mjs` (Vite pre-bundle làm reload trang giữa lượt đo).

### `docs/SIMULATION_VS_ILLUSTRATION_CONTRACT.md` · tài liệu hợp đồng
Định nghĩa ba mức AlgoSim công nhận — ILLUSTRATION (**cấm admit**) ·
STEP_VISUALIZATION · INTERACTIVE_SIMULATION — phân biệt bằng **ai sở hữu diễn
biến**, không bằng độ đẹp. Chứa PHÉP THỬ BỎ RENDERER (xoá renderer thì engine
vẫn phải sở hữu `state k → k+1 → result`), bảng sở hữu renderer-vs-engine, chỗ
đứng của LLM, hợp đồng **ngữ cảnh đổi NHÃN / cơ chế đổi HÀNH VI**, và phân mức
hiện tại 11/3/8 của 22 target. Đọc trước khi thêm target mới hoặc khi định cho
renderer "tự tính" thứ gì.

### `components/SearchStateView.tsx` — dữ kiện bước tìm kiếm · offline
Hai export: `SearchStateView` = **trạng thái quan sát** của bước tìm kiếm (tiền
đề · chip vị trí/đích/vùng xét · quan hệ · khối chi phí); `SearchPrecondition` =
dòng tiền đề, tách riêng để hai nơi không chép cùng một câu.

**W13 — `SearchActionZone.tsx` ĐÃ XOÁ, đừng đi tìm.** File cũ có hai export, hai
trách nhiệm: trạng thái (nay ở đây) và điều khiển cam kết (lời nhắc · nút · phản
hồi đúng/sai). W4B-2V đã tách trách nhiệm thứ nhất ra vì gác cả cụm làm mất
trạng thái quan sát (hồi quy W4B-2D); W13 gỡ hình thức hỏi-đáp nên trách nhiệm
thứ hai **rỗng hẳn** — không rút gọn được, mà là hết lý do tồn tại.

Luật rút ra, vẫn còn hiệu lực: **cổng gác quyền hành động, không gác thông tin.**
Dải nhân quả KHÔNG dựng cho họ tìm kiếm — `SearchStateView` là chủ sở hữu duy
nhất của quan hệ ở họ này.

### `generic/narration-boundary.characterization.test.tsx` · offline · **ĐẶC TẢ**
⚠️ Mô tả hành vi **HIỆN TẠI**, kể cả hành vi đáng lo — KHÔNG phải hợp đồng mong
muốn. Siết `RevealStep.narration` thì test này ĐỎ; sửa test cho khớp, đừng nới
bản vá cho khớp test. Đo ranh giới LLM ↔ bề mặt học sinh của
`generic.rule_scene`: validator hai tầng chỉ kiểm `typeof string` (không trần độ
dài, không ràng nội dung) nên narration mâu thuẫn/tuyên bố kết quả/tự phán đúng
sai đều ACCEPTED và tới học sinh nguyên văn qua khe thuyết minh của shell; nhưng
KHÔNG đổi được state/kết quả/phán quyết (đã đo). Kết luận + chuỗi sở hữu:
`docs/GENERIC_RULE_SCENE_LLM_BOUNDARY_AUDIT.md`.

### `simulations/observation-preservation.test.tsx` · Change impact: offline
Khoá `CORE_OBSERVATION_STATE_PRESERVED_UNDER_GATING`. Chứng minh THEO CẤU TRÚC
(không so hai lần render, vì `labOpen` là useState cục bộ nên SSR luôn thấy
`false`): (1) mọi probe cơ chế lõi nằm ngoài phần bị gác; (2) phần bị gác không
chứa probe lõi nào ⇒ mở cổng chỉ THÊM quyền hành động. Probe suy từ
`searchInteractionOf` + `decisionPointOf`, không viết tay. Ngoại lệ có tên
`PRESENTATION_COPY_TRANSITION` (teaser ↔ framing ↔ nhãn nút ↔ phản hồi được phép
đổi). Đã tiêm lỗi: gác lại trạng thái → ĐỎ; lộ cam kết ra Quan sát → ĐỎ.

### `simulations/spec-reuse.test.tsx` · Change impact: offline
Khoá hợp đồng tái dụng (W4B-2V §30): ba cặp ngữ cảnh khác nhau của cùng cơ chế
(`binary_search` điểm↔số báo danh · `count_if` điểm↔nhiệt độ · `find_max` học
sinh↔lượng mưa) phải cho **cùng chuỗi kiểu sự kiện engine** + **cùng tham chiếu
component renderer**, còn dữ liệu/nhãn phải KHÁC. So SỞ HỮU, không so pixel.
Kèm guard quét `domains/**` cấm renderer rẽ nhánh theo nội dung đề
(`summary.includes(...)`) hay theo `algorithm_id`/`simulation_id` — guard tự
kiểm bằng ba mẫu vi phạm tổng hợp trước khi tin kết quả 0.

### `scripts/audit-search-position.mjs` · offline (cần Chrome + Vite)
Runner ĐO HỆ ĐẾM VỊ TRÍ của họ tìm kiếm (W4B-2D §4) — chỉ ĐỌC, không bấm cam
kết, không mở Thí nghiệm. Ở một bước cam kết của `linear_search`/`binary_search`
nó thu hoạch MỌI bề mặt nói vị trí (nhãn cột `ArrayView` · `SearchActionZone` ·
chip `VarsView` · dải nhân quả · thuyết minh · mã giả) rồi đối chiếu bằng SỐ LẤY
TỪ ENGINE, không bằng chuỗi. Kết luận `SAME_SCREEN_CONTRADICTION` khi cùng một
vị trí ngữ nghĩa hiện hai hệ đếm. Có DẤU VÂN TAY bắt buộc (`active.moduleId` +
sân khấu đã dựng, sai thì exit 2). Cờ: `--port --out`. Artifact:
`docs/evaluation/m17/w4b2d-search-family/position-numbering/`.

### `simulations/domains/web/` — W4B-4D: THAO TÁC THẲNG LÊN TRANG
`apply.ts` thêm `selectNode` (fail-closed) · `moveBlock(order, target, slot)`
(miền = một HOÁN VỊ của tập khối đã có; `slot` là chỉ số ô ĐÍCH tuyệt đối, không
phải delta — dòng chảy tài liệu một trục nên không có toạ độ ngang) ·
`htmlTextOf(state)` (bản chiếu cấu trúc, SINH từ state — ở đây chứ không ở JSX
vì renderer tự ghép chuỗi HTML là nguồn sự thật thứ hai). `model.ts` thêm
`order`/`baselineOrder`/`selected` + `SELECTOR_OF`/`NODE_LABEL`.

Bài học nằm ở chỗ hai bản chiếu LỆCH nhau: **dời khối đổi HTML mà KHÔNG đổi
CSS** — thứ tự thuộc HTML, hình thức thuộc CSS. Khoá ở
`direct-manipulation-w4b4d.test.tsx` (đã mồi: viết cứng thứ tự trong JSX ⇒ ĐỎ).
`selected` nằm trong ENGINE state chứ không trong renderer vì sân khấu, cột
control và Inspector phải nói về CÙNG một nút.

### `simulations/domains/web/` — W4B-3F: TRANG CÓ CẤU TRÚC
`model.ts`/`props.ts`/`apply.ts`/`index.ts`/`ui.tsx` — mô hình `web.style_model`.
**Hợp đồng đổi HÌNH DẠNG ở W4B-3F**: `content` (một khối chữ) → `heading` +
`paragraph`, và style thêm `headingColor`/`headingSize`. Nguồn là backend
(`validation/simulation.py::validate_web_style_config` + `web_style_domain()`),
`props.ts` là MIRROR có sync-lock (`contract-parity.test.ts`) — sửa một bên mà
quên bên kia là ĐỎ. Đổi hình dạng ⇒ **bump `CACHE_VERSION`** (đây là bề mặt LLM
điền).

**Vì sao đổi**: một `<div>` không có tổ tiên lẫn anh em, nên bài `html_css`
(T12 CĐ4) không có gì để nói về quan hệ THẺ ↔ HIỂN THỊ, và bảng CSS chỉ ra một
luật. Có `h1`/`p` trong `.trang` thì `cssTextOf` sinh **ba bộ chọn** (hai cái là
bộ chọn hậu duệ) và "cỡ chữ tiêu đề" ≠ "cỡ chữ đoạn văn" — đó chính là bài học.
Vẫn ĐÓNG: không CSS thô, không `eval`, không iframe, không `<style>`.

Tests: `bounded-model-w4b2z.test.tsx` — ngoài các bất biến cũ, W4B-3F thêm hai
guard mà **tiêm lỗi mới lộ ra**: (1) xem trước phải là TRANG CÓ CẤU TRÚC (gỡ
`<p>` ⇒ ĐỎ); (2) xem trước phải vẽ ĐÚNG state (renderer chèn giá trị riêng ⇒
ĐỎ — trước đó hợp đồng `artifact_reflects_style_state` chưa ai kiểm).

⚠️ Bài "Trang giới thiệu" **KHÔNG còn** ở `generic.rule_scene`. Bản cũ là
`reveal_sequence` ba bước — trục thời gian bịa cho HTML. `GENERIC_WEB_SPEC` giữ
lại làm FIXTURE của engine generic, không phải bài học công khai; mẫu công khai
của generic nay là `gen-rule-library` (quy tắc hợp thành, có công tắc thật).

### `frontend/scripts/measure-dag-composition.mjs` · offline (cần `npm run dev`)
W4B-4D — ĐO KHOẢNG TRỐNG CHẾT của sân khấu `logic.boolean_dag` ở bốn bề rộng.
Hai phép đo KHÁC NHAU, đừng lẫn: `fillPct` đo MỰC (rect trong SVG) so với thẻ —
sơ đồ to hay nhỏ; `gutterLeft/gutterRight/skew` đo CỤM nội dung so với thẻ —
hình có bị dồn về một bên không. Khiếu nại "dồn sang trái" là phép đo thứ hai,
nên một bản vá chỉ kéo `fillPct` lên vẫn hỏng đúng chỗ bị kêu.

Chính nó bắt được hai lỗi mà SSR không thấy: SVG rơi về bề rộng mặc định 300px
khi cha là `fit-content`, và khung nét đứt của cổng đầu ra bị viewBox cắt mất
7px. Có dấu vân tay trang (không thấy sân khấu DAG ⇒ thoát != 0).
Artifact: `docs/evaluation/m17/w4b4d-composition/`.

### `frontend/scripts/accept-experience-w4b4c.mjs` · offline (cần `npm run dev`)
W4B-4C — NGHIỆM THU TRẢI NGHIỆM: hỏi CÂU HỎI NGHIỆM THU bằng Chrome thật ở bốn
bề rộng. Với mỗi target đã chuyển sang tương tác, nó nạp bài, phát ĐÚNG action
mà bộ điều khiển trên màn hình phát, rồi khẳng định (a) trường kết quả ĐỔI,
(b) `state` đổi tham chiếu, (c) **không** phải bật Play. Vế (c) là vế chính:
một bài chỉ đổi khi chạy timeline thì vẫn là animation-first.
Artifact: `docs/evaluation/m17/w4b4c-experience/acceptance.json`.

### `simulations/experience-audit-w4b4a.test.ts` · offline
Phép đo TRẢI NGHIỆM cho toàn danh mục, chạy bằng HÀNH VI chứ không đọc metadata:
phát mọi action mà từng miền thật sự nhận vào `module.apply` và ghi lại target
nào đổi được state (KHÔNG dùng timeline). Ghi bảng ra
`docs/evaluation/m17/w4b4a-experience/probe.json`.

Bốn bất biến nó giữ: khai `explore` ⇒ phải thao tác được · thao tác được ⇒ phải
có lối vào (trừ `exploratory`/`hybrid` vốn luôn mở) · chuỗi bước KHÔNG được tính
là thao tác · cam kết KHÔNG được tính là thao tác. Kèm `KEEP_TRACE` — danh sách
target CỐ Ý giữ dạng trace kèm lý do CƠ CHẾ, có test bắt lý do phải nói về cơ chế
chứ không phải tiến độ, và bắt lý do lỗi thời khi target đã có tương tác.

⚠️ Bản đầu của phép đo này ĐOÁN tên action và cho ba âm tính giả. Thêm action
mới thì phải đọc `apply` của miền đó, đừng suy từ miền khác — và mồi hai chiều
trong file là thứ chứng minh phép đo còn phân biệt được.

### `frontend/scripts/accept-w4b3a.mjs` · Change impact: offline (cần `npm run dev`)
W4B-3A — NGHIỆM THU TRÌNH DUYỆT ở BỐN bề rộng (1920/1536/1366/768) cho 7 target
đại diện: 0 dải `experiment-trigger`; mọi `.sim-secondary-action` phải nằm TRONG
`.player-controls`; không tràn ngang; mở Thử thách ⇒ ≤1 bề mặt cam kết; parity
2D↔3D của `protocol_encapsulation` (cursor/stepCount/`getExplainContext` phải
KHỚP khi đổi cách xem); phiên A→Khám phá→B→A giữ nguyên object state, 0 `fetch`.
Có dấu vân tay trang + `--self-test` (tiêm lỗi giả, exit 1). Cờ:
`--port --out --self-test`. Artifact: `docs/evaluation/m17/w4b3a-after/`.

### `frontend/scripts/accept-workspace-w4b3b.mjs` · Change impact: offline (cần `npm run dev`)
W4B-3B — NGHIỆM THU BỐ CỤC KHÔNG-GIAN-LÀM-VIỆC ở 4 bề rộng, ở các trạng thái
unit test không với tới: **1 phiên · 2 phiên TRÙNG TIÊU ĐỀ · 6 phiên (quá sức
chứa) · chuyển phiên**. Khẳng định: 0 cột phiên thường trực · sân khấu KHÔNG hẹp
đi và KHÔNG bị đẩy sang phải khi số phiên tăng · 0 tràn ngang · tiêu đề 1 dòng ·
đúng 1 tab đang-xem · nhãn không trùng khi tiêu đề trùng · `Mô phỏng mới` tới
được **kể cả khi chỉ có 1 phiên** · dải điều khiển không xuống dòng trên desktop ·
chuyển phiên giữ đúng object state, 0 `fetch`. Có `--self-test` + `--label`.
Artifact: `docs/evaluation/m17/w4b3b-workspace/{before,acceptance}.json`.

**BA BẪY ĐÃ CẮN KHI VIẾT SCRIPT NÀY** (đọc trước khi viết script CDP mới):
1. **Đếm dòng bằng `top` là SAI.** Trong flex row có `align-items:center`, con
   cao thấp khác nhau thì `top` khác nhau — phép đếm đó báo 5–7 dòng cho một
   hàng phẳng. Đếm bằng CHỒNG LẤN DỌC theo thứ tự DOM.
2. **WARMUP PHẢI DÙNG URL ĐÃ GIẢI**, không dùng đường dẫn trần. Warmup bằng
   `import('/src/state/store.ts')` ĐĂNG KÝ chính URL trần vào
   `performance.getEntriesByType('resource')`, nên `pick()` sau đó chọn nó thay
   vì URL `?t=…` app đang chạy ⇒ lại lái store thứ hai. Bẫy hai-instance cắn
   LẦN THỨ HAI, do chính lớp chống nó gây ra vì thêm sai thứ tự.
3. **`Promise was collected`** = Vite tối ưu deps rồi reload GIỮA lúc await.
   Phải có `warmup()` + retry trên lỗi CDP (cùng khuôn `measure-composition.mjs`).
   Và **chú thích bên trong template literal KHÔNG được chứa dấu backtick**.
4. **Đếm dòng bằng `top` là SAI** (xem 1).

**BẪY ĐÃ CẮN MỘT LẦN — đọc trước khi viết script CDP mới.** Vite gắn
`?t=<timestamp>` vào URL module sau HMR, nên `import('/src/state/store.ts')` từ
console có thể trả về **instance THỨ HAI**: script lái một store, trang vẽ theo
store kia, và mọi khẳng định "không thấy X" đều XANH vì lý do sai. Script này
giải URL từ chính trang (`performance.getEntriesByType('resource')`).
`measure-composition.mjs` KHÔNG có lớp bảo vệ đó — nó thất bại ồn ào (null
`querySelectorAll`), nên gặp lỗi đó thì **restart `npm run dev`**, đừng sửa số.

### `simulations/renderer-fit.ts` · offline
**Chủ sở hữu KHAI BÁO hợp đồng vừa-khung của renderer** — để runner đo không phải
hard-code theo `moduleId`. Phân mỗi target vào một `RendererFitClass`
(`adaptive_layout` · `canvas_fill` · `fixed_semantic_size`) kèm `semanticMaxWidth`
(trần bề rộng theo trạng thái HIỆN TẠI) và `maxWidthPerItem` (ràng buộc mật độ,
khai RIÊNG nên nới trần cài đặt sẽ làm nó đỏ). Hỏng theo **hai** hướng chứ không
một: `UNDER_UTILIZED` (khung rộng ra mà hình đứng yên) và `OVER_EXPANDED` (hình
phình quá mật độ ngữ nghĩa) — nên cổng chấm KHÔNG được là "hình phải chiếm ≥X%".
Export `ARRAY_VIEW_TARGETS`, `CANVAS_TARGETS`, `FIXED_SIZE_TARGETS`,
`TABLE_TARGETS`, `ARRAY_MAX_WIDTH_PER_ITEM`, `rendererFitOf()`.
**`SimulationWorkspace` đọc `semanticMaxWidth` để nâng sàn `--stage-min` của thẻ**,
nên target KHÔNG khai trần sẽ kẹt ở sàn mặc định 560px (đo được: `tree.traversal`
560px vs `algorithm.find_max` 1443px — nguồn của "mỗi target một bề rộng").
⚠ File này được `SimulationWorkspace` import THẲNG ⇒ **không được import renderer
miền** (nạp lười qua `<Suspense>`); lấy hình học qua module lá, xem bên dưới.

### `simulations/domains/tree/layout-size.ts` · offline
**Hình học khung vẽ cây, tách thành module LÁ** (không import registry/React/
store) để `renderer-fit.ts` đọc được TRẦN bề rộng mà **không kéo renderer nạp-lười
vào bundle shell** — `SimulationWorkspace` import thẳng `renderer-fit`, nên import
`tree-module` ở đó là phá code-splitting của `<Suspense>`. Export `TREE_SLOT_W`
(86 — một làn nút, đủ nhãn ~12 ký tự), `TREE_LEVEL_H` (78), `treeLayoutSize(config)`
→ `{w, h}`. Giá trị `w` **chính là trần ngữ nghĩa**: renderer vẽ `maxWidth: w` nên
cây giãn tới đây rồi dừng. Một nguồn cho cả renderer lẫn cổng chấm — không có con
số chép tay ở nơi thứ hai để trôi.

### `components/header-identity.ts` · offline
**Chủ sở hữu DẢI NHẬN DIỆN đầu thẻ mô phỏng** — hai trong ba dòng đầu tiên học
sinh đọc. Export `DOMAIN_BADGE: Record<Domain, string>` (nhãn miền tiếng Việt,
**toàn phần** — thêm miền mà quên nhãn ⇒ `tsc -b` GÃY, thay cho bảng
`Record<string, string>` cũ có fallback `domain.toUpperCase()` từng để lọt
`web`→"WEB" và `geometry`→"GEOMETRY") và `headerSubtitle(modTitle, envelopeTitle)`
trả `string | null` — `null` khi phụ đề lặp nguyên văn tiêu đề (chuẩn hoá hoa/
thường + khoảng trắng), để **shell** không dựng `<span>` thay vì bắt 24 module tự
nhớ. Trả `null` chứ không phải chuỗi rỗng: span rỗng vẫn ăn khoảng cách lưới.
Khoá bởi `components/header-identity.test.ts` (quét cả 24 target: nhãn đủ mọi
miền đã đăng ký · phụ đề không lặp tiêu đề · không liệt kê biến thể mà control
đã bày bằng tiếng Việt · trần 40 ký tự) và `visual-guards.test.tsx` VIS-002.

### `components/SimulationWorkspace.tsx` · `SimulationControls.tsx` · offline
Host sân khấu; thanh điều khiển **capability-driven** (có `timeline` mới hiện
Next/Prev/Play) — tiền lệ cho EditPolicy. M8: Stage = `rendererFor(mod, mode)`
trong `<Suspense>` (renderer lazy); export `VisualModeToggle` (component thuần
theo props — toggle 2D/3D chỉ khi ≥2 mode khả dụng); `PredictionBar` nằm NGOÀI
renderer nên tự nhiên renderer-independent.

**W4B-3A — `SimulationControls` là CHỦ SỞ HỮU DUY NHẤT của lối vào hành động
phụ** (Khám phá + Thử thách), dựng bằng `SecondaryEntry` (component nội bộ, một
hình thức cho cả hai). Trước wave này ba nơi dựng nút — shell + hai renderer
miền — và hai nơi sau đặt nút ngay dưới sân khấu, tức dải `experimentTrigger`
mà bốn lượt đo bố cục đều bắt được. **Renderer miền không được chứa
`sim-secondary-action`** (khoá ở `secondary-actions-w4b2w.test.ts`).

**W4B-4D — `specDrift(mod, state, baseline)`**: mô hình đã RỜI KHỎI đề bài chưa.
Hàm THUẦN (luật chôn trong JSX là luật chỉ kiểm được bằng trình duyệt), so
`mod.currentConfig(state)` với `active.config` (bản validate BẤT BIẾN). Hai luật
dễ làm sai: so bằng **GIÁ TRỊ** chứ không tham chiếu (mọi `apply` dựng config
mới ⇒ so tham chiếu là nhãn kêu vĩnh viễn), và chỉ so **các khoá module khai**
(`web` không giữ `notes` của đề ⇒ so cả khối thì mọi đề có `notes` đều "đã đổi"
ngay khi vừa mở). Module không khai `currentConfig` ⇒ luôn `false`.
Nhãn `.spec-drift` dựng trong `workspace-header`. Bất biến #25.

`SimulationWorkspace` export hai bộ chọn THUẦN mà `SimulationControls` gọi:
`challengeEntry(mod, state, config)` và `exploreEntry(mod, state, config)` →
`PresentationEntry | null`. `null` = module không có chế độ đó ⇒ không nút;
`available: false` = có năng lực nhưng bước này không dùng được ⇒ nút MỜ, không
biến mất (số bước mời được chỉ 4/13 → 21/40 tuỳ bài, tự gỡ mình thì nút nhấp
nháy). Hằng `DEFAULT_CHALLENGE` là câu mời mặc định cho module chưa khai
`predict.entry`. `challengeSurfaceVisible` GIỮ nguyên trách nhiệm cũ — chặn
`PredictionBar` khi module đã bày cam kết trên sân khấu (`presentedInStage`);
đừng dùng nó để tắt LỐI VÀO (đó chính là lỗi đã sinh ra dải).
Tests: `explore-ownership-w4b3a.test.ts`, `secondary-actions-w4b2w.test.ts`,
`dequiz-observe.test.tsx`, `interaction-family-w1.test.tsx`.

### `llm/client.ts` · Change impact: offline
Exports: `analyzeViaServer`, `editViaServer`, `explainViaServer`, `fetchHealth`,
`EditResponse`. Notes: trình duyệt không bao giờ giữ API key.

### `test-setup.ts` · Change impact: offline
Guard offline vitest: stub `fetch` → ném lỗi. Tests: `llm/offline-guard.test.ts`.

## M18 — TẦNG TÀI KHOẢN VÀ LỚP HỌC

> Tầng này KHÔNG sở hữu sự thật mô phỏng. Engine tất định vẫn là nơi duy nhất
> giữ state/timeline/kết quả và là bên duy nhất phán học sinh đúng hay sai
> (bất biến #27). Lớp học chỉ ĐỌC bằng chứng có cấu trúc.

### `backend/app/accounts/` — DANH TÍNH, VAI TRÒ, QUYỀN

Bốn file, bốn tầng, đi một chiều: `policy` (thuần) ← `service` (DB) ←
`router`/`classroom_router` (HTTP).

- **`passwords.py`** — PBKDF2-HMAC-SHA256 từ thư viện chuẩn, salt riêng mỗi tài
  khoản, so constant-time. KHÔNG thêm passlib/bcrypt: cùng thuật toán, thêm một
  dependency mật mã. Chuỗi lưu tự mô tả (`pbkdf2_sha256$vòng$salt$hash`) nên đổi
  số vòng về sau không làm hỏng hash cũ. Định dạng hỏng ⇒ `False`, không ném lỗi
  (một exception riêng là kênh dò tài khoản).
- **`policy.py`** — HÀM THUẦN, test được không cần FastAPI. `resolve_signup_role`
  (đăng ký thường LUÔN ra học sinh; vai trò giáo viên cần mã mời từ môi trường;
  thiếu cấu hình ⇒ ĐÓNG), `entitlement_for` (khách: 1 lượt thử, không lớp, không
  lịch sử bền), `can_observe_class` / `can_read_class`.
- **`service.py`** — phiên (mở/tra/gắn user/đóng), tài khoản, mã lớp. `attach_user`
  GIỮ hàng phiên đang có thay vì mở phiên mới: `guest_trials_used` nằm trên hàng
  đó, mở mới là đăng nhập-rồi-đăng-xuất lại có lượt. Mã lớp bỏ `0O1IL` vì học
  sinh gõ tay mã đó trên bảng.
- **`router.py`** — `/api/auth/*` + `/api/classes*`. Sai email và sai mật khẩu
  trả CÙNG một câu (không cho dò tài khoản). Mã lớp CHỈ hiện cho giáo viên sở
  hữu. `Caller`/`get_caller` là dependency giải danh tính dùng chung.
- **`classroom_router.py`** — `/api/assignments*` + `/api/classes/{id}/observe`.
  `_validated_envelope` là CỔNG: config phải qua đúng `SimSpec.validate` của
  target (bất biến #28). Tiến độ bị KẸP về miền hợp lệ, đếm chỉ TĂNG.

### `backend/app/persistence/classroom_models.py`
Sáu bảng: `users` · `auth_sessions` (phục vụ cả KHÁCH — chỗ đếm lượt thử) ·
`classrooms` · `class_memberships` (unique ở tầng DB) · `assignments` (giữ
envelope ĐÃ VALIDATE, không giữ đề để sinh lại) · `practice_sessions` (bằng chứng
CÓ CẤU TRÚC, không phải ảnh state của renderer).
Đặt cạnh `db.py` chứ không nhét vào: `db.py` sở hữu ngân hàng bài. Chung `Base`
nên Alembic thấy một metadata; `alembic/env.py` phải import file này VÌ TÁC DỤNG
PHỤ, nếu không autogenerate sẽ sinh migration XOÁ các bảng.

### `state/auth.ts` · `state/classroom.ts`
Hai store TÁCH khỏi `state/store.ts` (vốn cố ý mù domain). `auth` giữ danh tính
+ quyền đọc từ `/api/auth/me`; `classroom` là BẢN CHIẾU của lớp/bài/quan sát.
Vai trò ở client là để VẼ, không phải quyền: sửa nó trong devtools thì thấy được
thanh điều hướng giáo viên và không gọi nổi endpoint nào. Vì thế KHÔNG lưu bền.

### `components/AppSidebar.tsx`
Điều hướng MỨC ỨNG DỤNG, chỉ có sau đăng nhập. `itemsForRole()` export ra để test
được danh sách theo vai mà không cần SSR (zustand trả trạng thái đầu cho server
snapshot). Ba ràng buộc chống lặp lại cột 208px đã gỡ ở W4B-3B: nằm NGOÀI lưới
`.app-layout`, thu gọn thành dải biểu tượng trong mô phỏng, thành ngăn kéo ở
màn hẹp. Thu gọn thì nhãn chuyển sang `aria-label`.

### `components/AuthGate.tsx`
Hộp thoại đăng nhập/đăng ký, hai chế độ đổi tại chỗ. Ô "mã giáo viên" hiện ra khi
chọn vai giáo viên — nó KHÔNG phải cơ chế bảo mật (giấu nút không ngăn được ai);
`resolve_signup_role` trên máy chủ mới là bên quyết.

### `components/ClassesView.tsx` · `AssignmentsView.tsx` · `ObserveView.tsx`
Một component cho cả hai vai ở lớp/bài (cùng khái niệm, hai phía). `ObserveView`
hỏi lại `/observe` mỗi 5 giây — repo chưa có websocket/SSE và một bảng đổi vài
giây một lần không đáng dựng hạ tầng truyền tin thời gian thực (`§22`). Nó dọn
interval khi đổi lớp; không dọn thì mỗi lần đổi lại thêm một vòng hỏi.

### `components/PracticeReporter.tsx`
Component KHÔNG VẼ GÌ. Chuyển state engine thành bằng chứng thực hành: `cursor`/
`stepCount` đọc qua hợp đồng `timeline` (engine sở hữu), cờ Khám phá/Thử thách
đọc từ store trình bày. Đọc màn hình thay vì đọc hợp đồng chính là lỗi §38.6.
Gửi khi CHỮ KÝ state đổi, chặn nhịp 1500ms — `§22` cấm phát telemetry mỗi khung
hình. Không có bài đang làm ⇒ không gửi gì (tự luyện không đẻ telemetry).

### `components/AssignDialog.tsx`
"Giao cho lớp" — từ mô phỏng ĐANG MỞ tới bài thực hành. Giao từ trong mô phỏng
chứ không từ một trang riêng: giáo viên phải XEM được thứ mình giao, và một
danh sách tên tách quyết định khỏi thứ nó nói về. Gửi envelope của phiên; máy
chủ vẫn kiểm lại qua `SimSpec.validate` vì client không phải nơi luật sống.

### `frontend/scripts/accept-classroom-m18.mjs` · offline (cần dev + uvicorn)
Nghiệm thu tầng lớp học ở bốn bề rộng × ba vai. Kiểm DANH TÍNH BACKEND trước
tiên: container Docker cũ chiếm cổng 8000 sẽ trả 404 cho mọi endpoint mới và
làm mọi kết quả sau đó vô nghĩa (đã cắn một lần). Khẳng định: khách không có
thanh điều hướng và bị 401 ở lớp/bài · học sinh nhận bài, bị 403 khi tạo lớp và
khi quan sát · giáo viên thấy lớp + mã + bảng quan sát, và envelope hỏng bị
chặn 400. Artifact: `docs/evaluation/m18/classroom-acceptance.json`.

### `backend/scripts/seed_classroom_fixture.py`
Dữ liệu demo cho nghiệm thu: 1 giáo viên · 2 học sinh · 1 lớp · 1 bài. Mật khẩu
đọc từ `ALGOSIM_FIXTURE_PASSWORD`, không có mặc định trong mã (`§34`) — chạy
nhầm trên máy thật cũng không đẻ ra tài khoản ai cũng biết mật khẩu. Idempotent.

### `frontend/scripts/measure-stage-composition.mjs` · offline (cần `npm run dev`)
Đo bố cục sân khấu cho **mọi** target (khác `measure-dag-composition.mjs` chỉ đo
được `logic.boolean_dag`). Ba số mỗi target: `fillPct` (bề rộng MỰC / bề rộng
trong thẻ) · `skew` (lệch lề trái–phải của mực) · `railSpan` (mép trái của chữ
cách mép trái của mực bao xa — lớn = hai hệ căn lề trong cùng một thẻ).

⚠️ HAI LẦN ĐO SAI TRƯỚC KHI RA SỐ ĐÚNG, ghi lại vì cả hai đều "xanh mà vô nghĩa":
1. bản đầu lấy hộp bao của `querySelectorAll('*')` — div BỌC rộng bằng thẻ nên
   **mọi** target ra "lấp 99.9%, lệch 0", tức báo SẠCH cho đúng bố cục đang bị
   kêu. Nay chỉ đếm `<svg>` và phần tử LÁ thật sự có sơn.
2. bản thứ hai đếm cả bảng `details` gập được nên `boolean_dag` báo lệch 558px
   trong khi sơ đồ của nó đã căn giữa 0px — phép đo tự bịa ra một lỗi không có.

Và một lần nữa dính bẫy **backtick trong template literal** (đã cắn hai lần ở
`capture-*.mjs`): chú thích tiếng Việt trong khối `MEASURE` có \`...\` làm Node
báo `SyntaxError`. Trong khối đó không được có backtick nào.

Artifact: `docs/evaluation/m18/stage-composition.json`.

### `frontend/scripts/audit-composition.mjs` · offline (cần `npm run dev`)
M19 — SOÁT BỐ CỤC DÙNG CHUNG toàn danh mục. Thay `measure-stage-composition.mjs`
(bản đó chỉ đo mực/thẻ, không đo KHUNG và không đo bốn rail).

Mỗi dòng: sân khấu · khung cơ chế · mực có nghĩa · `frameFill` · bốn rail +
`maxRailDelta` · tràn ngang · cắt hình · PHÁN QUYẾT. Hai lỗi tách bạch, không
gộp thành một điểm: **A** = mực < 70% KHUNG mà khung lại chiếm > 90% sân khấu
(cơ chế nhỏ trôi trong khung quá khổ) · **B** = rail lệch > 24px (hình và chữ
hai hệ căn lề).

⚠️ KHÔNG chấm bằng tỉ lệ lấp một mình: 17% là ĐÚNG nếu khung cũng ôm sát 17% ấy.
Lỗi là 17% mực trong khung rộng 100%, nên mẫu số là KHUNG chứ không phải thẻ.

Cách chọn "mực có nghĩa" khai ngay trong file (bắt buộc — ba lần đo trước đều
trả về số mà vẫn sai): tính `<svg>` + phần tử LÁ có sơn; bỏ div BỌC (rộng bằng
thẻ nên nuốt mọi phép đo) và bỏ đồ đạc của thẻ (tiêu đề, chú giải, thuyết minh,
bảng gập, thanh tham số).

Hai hiện vật đã sửa trong chính script: lỗi trong trang bị nuốt thành
"(không trả lời)" nên bốn target hỏng đọc ra như thiếu mẫu — nay lỗi nổi lên; và
lượt nạp nặng thỉnh thoảng không trả kịp nên có THỬ LẠI một lần, vẫn hỏng thì
ghi dòng `KHÔNG ĐO ĐƯỢC` chứ không im lặng bỏ.

### `simulations/stage-size.ts`
M19 — MỘT LUẬT KÍCH THƯỚC SVG SÂN KHẤU, một chủ sở hữu. `stageSvgSize(w)` trả
`width={w}` + `max-width: 100%` (co được, KHÔNG phóng được).

Vì sao gom: sáu renderer cùng viết `width="100%"` + `maxWidth: w`, dạng đó KHÔNG
khai bề rộng riêng nên khi cha là `fit-content` thì `100%` không có gì quy chiếu
và Chrome rơi về 300px mặc định (`boolean_dag` đã dính: sơ đồ 662px vẽ ở 300px).
Nó cũng buộc phải kèm `margin: 0 auto` để trông cân, và chính cú căn giữa đó tạo
RAIL THỨ HAI — đo được `and_gate` lệch 581px, `decimal_to_binary` 673px.

Áp cho `binary/ui` · `logic/ui` · `network/ui` · `algorithm/program-module`.
`ArrayView` giữ bề rộng tự đo từ khung chứa (nó vốn co giãn theo cột) nhưng đã
BỎ `margin: 0 auto` cùng lý do.

### `frontend/scripts/evidence.mjs`
W0 — XUẤT XỨ CỦA BẰNG CHỨNG. `provenance(tool, env)` gắn `head` (git SHA) +
`dirty` (cây có thay đổi chưa commit) + môi trường vào MỌI artifact sinh ra;
`assertFresh(path)` là cổng đọc lại — artifact sinh từ commit khác bị xếp
**STALE_EVIDENCE** và không được chống lưng cho trạng thái DONE.

Vì sao cần: trước đó artifact chỉ có `when` (một dấu thời gian), nên nó có thể
sinh từ một commit khác hẳn commit đang xét mà vẫn trông "mới". Ba artifact
chính (`m19/after.json`, `m18/classroom-acceptance.json`,
`m17/w4b4a-experience/probe.json`) đều KHÔNG có dấu HEAD lúc kiểm.

Đã gắn vào: `audit-composition.mjs` · `accept-classroom-m18.mjs` ·
`accept-experience-w4b4c.mjs`.

---

## Trả nợ sync-lock 2026-08-20 (rơi lại từ `d4c1ef6`, `b06c0e9`, `09c0f49`)

Năm file dưới đây đã landed mà không có entry — `code-index-sync.test.ts` ĐỎ ở
HEAD trước khi wave sinh-ngữ-nghĩa bắt đầu. Ghi **cái chúng sở hữu**, không chỉ tên.

### `frontend/src/simulations/domains/generic/layout-compiler.ts` (G1–G7) · offline

Sở hữu **phân vùng không gian theo VAI TRÒ NGỮ NGHĨA** trong hệ toạ độ miền 0–100:
Input Zone (`array_strip`, `bar_chart`, `table_grid`) · State Zone (`value_box`,
`pointer`, `switch`, `slider`) · Structure Zone (`stack_view`, `queue_view`,
`tree_element`) · Output Zone. Đây là **nguồn duy nhất** quyết định object nằm đâu
trên sân khấu generic — renderer **không** được tự đặt toạ độ cho từng bài.

### `frontend/src/simulations/domains/generic/anchor-resolver.ts` (Semantic Anchor System, G5) · offline

Sở hữu việc **phân giải vị trí (X, Y) của pointer/annotation neo vào một thành phần
ngữ nghĩa** theo *kiểu đối tượng + `target_index`*. Tồn tại để xoá hardcode toạ độ
theo từng bài. ⚠️ Liên quan trực tiếp **bất biến #34**: neo không phân giải được thì
đường sinh ngữ nghĩa phải fail-closed, **không** vẽ một phần.

### `frontend/src/simulations/domains/generic/disallowed-collision.ts` · offline

Sở hữu **định nghĩa va chạm bị CẤM** giữa các đối tượng đã bố cục: `TEXT_ON_TEXT`
(nhãn đè nhãn) · `BOX_ON_BOX` · `CANVAS_OVERFLOW` (tràn ngoài 0–100). Đọc kết quả
của `layout-compiler.ts`. Đây là bản kiểm **tất định** cho đúng lớp lỗi mà L5a
(visual regression) bắt trên trình duyệt — hai tầng khác nhau, đừng bỏ tầng này vì
đã có tầng kia.

### `frontend/scripts/verify-semantic-e2e-render.mjs` · `verify-live-gemini-render.mjs` · `verify-real-browser-render.mjs` · cần Chrome + `npm run dev`

Ba runner Playwright chụp mô phỏng do đường `semantic_program` sinh, ở 4 viewport
(1920 · 1536 · 1366 · 768), phục vụ các lượt chứng nhận `b06c0e9`/`09c0f49`.

> ⚠️ **Cả ba đều hardcode `ARTIFACT_DIR` trỏ RA NGOÀI REPO**
> (`C:/Users/Bunny/.gemini/antigravity-ide/brain/…`). Bằng chứng ghi ra đó
> **không tái lập được** và theo luật dự án thì không được ghi DONE. Spec
> 2026-08-20 (E13) mới chỉ bắt được **một** trong ba file — Task 13 của plan phải
> sửa **cả ba**.

---

## Đường sinh ngữ nghĩa `generic.semantic_program` (2026-08-20 → 21)

Spec: `docs/superpowers/specs/2026-08-20-semantic-program-generative-route-design.md`.
Bất biến #31–#34 ở `ARCHITECTURE_MAP §5`.

### `backend/app/simulation/semantic_program/pacer.py` · Change impact: offline

Sở hữu **NGÂN SÁCH TRÌNH BÀY** và phép gộp khung máy → bước xem. Cố ý nằm NGOÀI
`visual_adapter` để adapter giữ song ánh `frame k ⇔ trace[k]` — có song ánh đó
thì bất biến #31 mới là định lý. Bất biến riêng của nó (#32): các đoạn phân hoạch
đầy đủ, không chồng lấn, **không sinh khung mới**. Chạm trần ⇒ hạ mức chi tiết,
KHÔNG cắt.

### `backend/app/simulation/semantic_program/obligations.py` · offline

Sở hữu **taxonomy nghĩa vụ ngữ nghĩa** (9 kind) + `SEMANTIC_PRESCRIBED_PROCEDURES`.
Khoá vào HỆ KIỂU của IR, **không** vào catalog — số target là mở, số kiểu dữ liệu
thì đóng. Đóng băng trước SEALED; khoá bởi `test_taxonomy_frozen.py`, trong đó có
danh sách bốn nghĩa vụ **cố ý loại** kèm lý do.

### `backend/app/simulation/semantic_program/request_contract.py` · offline

Sở hữu **hợp đồng yêu cầu đã đóng băng** (`frozen=True`). Đây là chỗ luật "stage
sinh không được khai lại nghĩa vụ" trở thành bất khả thay vì lời dặn. Ghi rõ giới
hạn: separation of responsibility, **không phải** independent oracle.

### `backend/app/simulation/semantic_program/coverage_gate.py` · offline

Sở hữu **C₁a** (structural, trước execution) và **C₁b** (realized, sau execution).
C₁a hỏi "có witness hợp lệ không", C₁b hỏi "witness có THẬT SỰ được tạo ra không"
— hai câu khác nhau, và ví dụ tách chúng là `assign` nằm trong nhánh chết.

### `backend/app/simulation/semantic_program/grounding_gate.py` · offline

Sở hữu **P2** của chuỗi provenance: mọi `initial_value` không phải HẠT KHỞI TẠO
phải tham chiếu **đúng mục** trong `RequestContract`. Kiểm THAM CHIẾU, không
tìm-theo-giá-trị. Giới hạn P1 khai ở `docs/evaluation/semantic-benchmark/P1_LIMITATION.md`.

### `backend/app/simulation/semantic_program/postconditions.py` · offline

Sở hữu **C₂** — 8 checker server-owned. Mỗi checker tính lại tính chất TỪ TRẠNG
THÁI CUỐI bằng phép toán sơ cấp, **không cài lại thuật toán của chương trình**;
đó là điều kiện để oracle giữ được tính độc lập. `structural_traversal` cố ý chưa
có checker (lý do ghi trong file).

### `backend/app/simulation/semantic_program/learner_surface.py` · offline

Cổng CUỐI và là cổng **duy nhất quay về phía màn hình** — mọi cổng khác nhìn về
phía chương trình. Chạy SAU `compile` vì câu hỏi là về những khung **sẽ được
phát**, không phải về ý định của chương trình. Hạ `servable=False` nhưng **giữ
`executable=True`** (`LEARNER_SURFACE_INCOMPLETE` → `verification_gap`): hệ chạy
được bài, cái thiếu là đường lên màn hình.

Bổ khuyết đúng chiều còn trống của bất biến #34: `_assert_bindings_resolvable`
hỏi *mỗi binding có biến không*; cổng này hỏi *mỗi biến đáng thấy có binding
không*. Chỉ đòi HAI lớp — container **biến động** và **witness** của nghĩa vụ —
vì đòi mọi biến là từ chối oan hàng loạt mô phỏng đúng (biến đếm, biến tạm), mà
một cổng kêu oan là một cổng sẽ bị tắt. Bảng tra HẰNG (`pairs`) không đổi giá trị
nên không bị đòi. Cùng danh sách `PLACEHOLDER_LEAKS` với
`frontend/src/simulations/learner-gate.ts` — hai đầu của một luật.

Phát hiện đầu tiên của nó: fixture #18 dựng bảng tần suất suốt lượt chạy mà màn
hình không bao giờ có bảng — vì `map` là `MemoryType` đã admit mà không primitive
nào biểu diễn được. Đó là nguồn gốc của `map_view` (2026-08-23), thêm theo đúng
tiền lệ `graph_view`: mở vì một **lớp trạng thái đã admit**, nguồn phát hiện DEV,
không phải một ca SEALED. Thêm primitive ⇒ đồng bộ BỐN nơi: `contract.py` Literal ·
`visual_adapter.HANDLED_PRIMITIVES` + nhánh adapt · `test_primitive_set_frozen.py` ·
renderer `domains/semantic/ui.tsx`, rồi chạy `export_semantic_program_schema.py`.

### `backend/app/simulation/semantic_program/contract.py` — BIÊN CHUẨN HOÁ · offline

Ngoài các model IR, file này giữ **bốn biên gộp cách viết**, tất cả cùng một luật:
*gộp hai cách viết của MỘT thứ, KHÔNG nới ngữ nghĩa*. Chúng tồn tại vì fail-closed
ở tầng cú pháp che mất năng lực ngữ nghĩa thật của chương trình. Mỗi biên gọi
`ghi_coercion()` khi nó thật sự gộp — xem `coercion_stats.py`; **thêm biên thứ
năm mà quên khai lớp ở đó là ĐỎ**.

- `canonical_spec_version` — `1.0` (số) ⇒ `"1.0"`. Nguồn: SEALED `7e5df014…`,
  **17/40 case** chết vì đúng lỗi này. Chặn `bool` tường minh (`True` là subclass
  của `int`). Phiên bản khác 1.0 vẫn bị từ chối.
- `canonical_container_name` — `{"kind":"var","name":X}` ⇒ `X`; mọi kind khác
  **raise có DẠY** thay vì để Pydantic nói "Input should be a valid string".
- `canonical_condition` (2026-08-23) — `hop_le` ⇒ `hop_le == true`. Nguồn: probe
  E2E, LLM viết `if hop_le and …` mà union điều kiện chỉ nhận sáu dạng mệnh đề.
  RANH GIỚI: chỉ gấp dạng mang được bool (`var/field/index/map_get/literal`);
  `arith`/`length`/`neighbors` vẫn bị từ chối vì `2+3` làm điều kiện là lỗi KIỂU
  thật — nới KÝ PHÁP không được thành nới KIỂU.
- `canonical_const_int` (2026-08-24) — `{"kind":"literal","value":1}` ⇒ `1` cho
  `for_range.step`. Nguồn: SEALED `7e5df014…`, 2 case. `start`/`end` là
  `ValueExpr` nên nhận dạng bọc, riêng `step` thì không — mô hình viết cả ba
  cùng kiểu là NHẤT QUÁN, chỉ hợp đồng là không. RANH GIỚI: chỉ gỡ `literal`
  mang số nguyên (`bool` bị chặn); `var`/`arith` vẫn từ chối vì bước nhảy phải
  HẰNG thì vòng lặp mới có biên tất định.

Tests: `test_spec_version_canonicalization.py`, `test_container_ref_canonicalization.py`,
`test_condition_canonicalization.py`. Sửa model ⇒ chạy
`scripts/export_semantic_program_schema.py` (ghi HAI bản, khoá bởi
`test_schema_sync.py`). BeforeValidator KHÔNG vào JSON schema nên hash schema chỉ
đổi khi model đổi.

### `backend/app/simulation/semantic_program/coercion_stats.py` · offline

Bộ đếm **bốn biên chuẩn hoá** của `contract.py` đã phải ra tay bao nhiêu lần.
Export: `ghi_coercion` · `reset_coercion` · `coercion_report` · `tong_coercion`
· `LOP_HOP_LE` + bốn hằng `LOP_*`.

VÌ SAO CẦN: bốn biên ấy cứu rất nhiều case, và chính vì thế mà chúng nguy hiểm —
gộp im lặng thì không phân biệt được *"mô hình thỉnh thoảng viết dạng khác"*
(biên làm đúng việc) với *"mô hình LUÔN viết dạng khác"* (hợp đồng đang mô tả
sai thứ mô hình phát, phải sửa ở prompt/thẻ văn phạm chứ không phải thêm lớp gộp
thứ năm). Phân biệt hai thứ đó chỉ cần một con số.

CỐ Ý KHÔNG DÙNG LẠI `app/ai/telemetry.py` dù cùng khuôn (bộ đếm trong tiến
trình, `reset`/`report`): telemetry ấy thuộc tầng `app.ai`, còn `contract.py`
nằm sâu trong `app.simulation` và không được phụ thuộc ngược lên tầng AI.

`coercion_report()` luôn trả **đủ bốn lớp kể cả khi bằng 0** — vắng mặt không
phân biệt được "chưa nổ" với "quên gắn bộ đếm". Không bao giờ ném lỗi (lớp lạ bị
bỏ qua im lặng): quan trắc mà giết được một lượt phân tích thì đắt hơn thứ nó đo.

Khoá bởi `tests/semantic_program/test_coercion_stats.py` (19 test), trong đó
nửa quan trọng là các ca ÂM TÍNH — dạng đã đúng thì KHÔNG được tính là một lượt
gộp, nếu không `coercion_rate` luôn 100% và vô nghĩa. `test_bon_lop_khop_voi_so
_bien_chuan_hoa_trong_contract` đếm bằng cách soi chính `contract.py`, không chép
tay danh sách — nó đã bắt được drift thật ngay lần chạy đầu (`canonical_const_int`
có trong mã mà `CODE_INDEX` vẫn ghi "ba biên").

Runner đọc nó ở `run_sealed_evaluation.py`: `reset_coercion()` đầu mỗi case,
`coercion_report()` vào `sealed_cases.json`, tổng hợp thành khối `coercion_rate`
trong `sealed_summary.json`.

### `backend/tests/semantic_program/test_repair_loop.py` · offline · 0 API call

Khoá **vòng sửa ≤3 lượt** của `stage_semantic_program` — 11 test, và nó tồn tại
vì `test_stage_synthesis.py` **không** phủ được vòng lặp: sáu test ở đó xanh y
hệt nhau dù `range(MAX_SEMANTIC_PROGRAM_ATTEMPTS)` có bị đổi thành `range(1)`.
Cùng loại lỗ đã làm `stage_semantic_program` từng **không ai gọi** mà suite vẫn
xanh.

Bốn nhóm khẳng định: vòng lặp **quay thật** (hỏng lượt 1 → sửa lượt 2 → trả
spec; JSON cụt cũng kích hoạt; thành công lượt 1 KHÔNG gọi thêm) · lỗi validator
**đi vào prompt lượt sau** kèm đề bài và thẻ văn phạm còn nguyên (thử lại mù ≠
vòng sửa) · **dừng đúng ở trần** (ngân sách 520 của `RUN2_PROTOCOL §3` dẫn từ
hằng số này) · mỗi lượt hỏng phát một `semantic_program_attempt` đánh số.

**TIÊM LỖI đã chạy**: hạ `MAX_SEMANTIC_PROGRAM_ATTEMPTS` 3 → 1 thì **7/11 test
ĐỎ**. Bốn test còn xanh là đúng — chúng phủ nhánh một-lượt hoặc dẫn bound từ
chính hằng số.

⚠️ Chọn payload hỏng cho bộ test này có HAI bẫy, đều làm test xanh vì lý do sai:
(1) bốn lớp đã có biên chuẩn hoá (`spec_version`, `container` dạng `var`, `step`
bọc literal, biến bool làm điều kiện) nay được **gộp** nên không kích hoạt được
vòng sửa; (2) ba thứ tưởng hỏng mà validator vẫn cho qua — `statements` **rỗng**,
gán vào **biến chưa khai**, `value_box` trỏ **biến lạ**. Payload dùng được là
`push` vào container chưa khai.

### `backend/scripts/classify_run1_failures.py` · offline · **0 API call**

Soi lại các ca trượt thẩm định của SEALED #1 bằng hợp đồng HIỆN TẠI, phân loại
**từng lỗi Pydantic** thành `GOP:<biên đã gộp>` hoặc `TRUOT:<lý do>`. Export:
`chay()` · `tach_loi()` · `phan_loai()` · `BOOL_KINDS`.

Nó trả lời *"bốn biên chuẩn hoá đáng giá bao nhiêu"* mà **không tiêu một lượt
LLM nào** — làm được vì `sealed_cases.json` giữ nguyên văn khối lỗi Pydantic, và
khối ấy liệt kê ĐỦ mọi lỗi của một chương trình. Kết quả 2026-08-24: **22/27 ca
nay qua tầng Pydantic**, 3 vẫn trượt (`kind` bịa ra · `field` ngoài
`{left,right,val,data}`), 2 không kết luận được (JSON cụt).

HAI RANH GIỚI, đừng trích sai: (1) qua Pydantic mới là **chạm cổng kế**, sau đó
còn `validate_semantic_program` → interpreter → C₁a → C₁b → C₂ — ở lượt #1, 9
chương trình qua cú pháp rụng còn 3 chạy được và 1 phát được; (2) nó chạy trên
**40 ca ĐÃ LỘ** nên là **chẩn đoán**, không phải số held-out.

`tach_loi()` phân biệt `None` (không phải lỗi schema — JSON hỏng) với `[]` (có
khối lỗi nhưng rỗng): hai thứ dẫn tới hai kết luận khác nhau, gộp là mất một
nhóm ca. Ba lớp `TRUOT` được ghi thành **dự đoán tiền đăng ký** ở
`RUN2_PREFLIGHT.md §3c` để lượt #2 bác bỏ được.

### `backend/scripts/cross_domain_matrix.py` · offline · 0 API call

Bảy lớp trạng thái (scalar · array · string · stack · derived_sequence · tree ·
graph) đi qua **một** bộ 11 cổng, không nhánh riêng miền nào. Đáp án mong đợi
**kiểm tay** (21=10101₂ · max=89 · "radar" · `{[()]}` · prefix [2,6,7,14,17] ·
preorder A,B,C · BFS 1→5), không chép từ đầu ra của hệ — nếu không
`EXPECTED_RESULT` là tautology. `--json/--md` ghi artifact vào
`docs/evaluation/semantic-vnext/reports/`.

Khoá bởi `tests/semantic_program/test_cross_domain_matrix.py`, và nửa quan trọng
hơn của bộ test ấy là phần TIÊM LỖI: bản đầu của ma trận **rỗng** — gỡ binding
mà 6/7 lớp vẫn xanh, vì cổng chỉ chạm container biến động còn dãy đầu vào
chỉ-đọc thì không ai đòi. Đó là nguồn gốc luật (2) của `learner_surface`.

### `backend/tests/test_mocked_production_e2e.py` · offline · 0 API call

E2E qua ĐƯỜNG HTTP THẬT (`POST /api/analyze` → `main.py` → `run_pipeline` → …
→ `learner_surface` → envelope), chỉ thay `call_gemini`. Không inject envelope,
không inject store. Ba miền: array · graph · map. Chạy TRƯỚC mọi lượt live —
mọi tầng sau LLM là tất định nên tiêu quota để phát hiện lại lỗi tất định là
lãng phí (đã xảy ra ba lượt liên tiếp trong wave này).

### `backend/app/simulation/semantic_program/analyze_contract.py` · offline

Sở hữu **bề mặt `analyze` của route semantic**, tách hẳn enum dẫn xuất catalog
(spec E5). `build_request_contract` LỌC nghĩa vụ ngoài taxonomy ngay tại đây.

### `backend/app/ai/pipeline.py` → `_semantic_shadow` · **live**

Quyết định route sinh **có được thử hay không** — và cố ý KHÔNG hỏi classifier
chọn target nào. Chỉ hai cổng: phạm vi (bỏ qua `GATE_SCOPE_UNDECLARED` vì đó là
lỗi hợp đồng prompt, không phải phán quyết về đề) và `execution_authority`.
Đặt nó trong nhánh generic là làm claim A phụ thuộc classifier legacy — tức đo
classifier chứ không đo route sinh. Việc **PHÁT** thì vẫn nhường module chuyên
biệt (ranh giới: không thay 24 module). Khoá bởi
`test_route_wiring.py::test_shadow_VAN_chay_khi_classifier_chon_module_chuyen_biet`.

### `backend/app/simulation/semantic_program/grammar_card.py` · **live**

Hợp đồng IR ở dạng gọn (~2,3 KB), **sinh 100% từ `contract.py`**, ghép vào
*user message* của `stage_semantic_program`. Nó thay `responseSchema` — thứ
Gemini KHÔNG nhận được vì schema IR đệ quy và nội suy `$ref` nổ ~10× mỗi bậc
(296 KB ở độ sâu 2, 3 MB ở độ sâu 3). Không có nó, mô hình bọc đầu ra trong
khoá `semantic_program`, gọi `variables` thay `memory_declarations`, và
38/40 case trượt thẩm định.

Phải liệt kê **cả giá trị enum** chứ không chỉ tên trường: tên trường nói được
*chỗ nào điền*, không nói được *điền gì* (mô hình từng viết `op: "add"` thay
`"+"`). Đặt ở user message chứ không ở `skills/*.md` để ngân sách prompt tĩnh
vẫn đo đúng thứ nó sinh ra để đo. Khoá bởi `test_grammar_card.py` (9 test, gồm
sync-lock từng `kind` và chặn rác kiểu `typing.Annotated` lọt vào).

### `backend/app/simulation/semantic_program/route.py` · offline

Sở hữu **thứ tự các cổng tất định** của route và **phán quyết cuối**:
P2 → C₁a → thực thi → C₁b → C₂ → biên dịch. Trả `SemanticRouteOutcome` mang HAI
cờ tách hẳn nhau — `executable` (máy chạy được không) và `servable` (đủ bằng
chứng phát canonical chưa); gộp chúng là bóp hai tỉ lệ của luận văn thành một.
Không có lượt LLM nào ở đây. Điểm dễ sai đã ghi trong file: C₁a trả `ok=False`
cho **cả** mức yếu, nên chỉ `REQUESTED_OPERATION_UNCOVERED` mới được chặn.

### `backend/app/ai/skills/semantic_analyze.md` · **live**

Prompt của `stage_semantic_analyze` — đề bài → dữ liệu đề cho + nghĩa vụ. **Tách
hẳn `analyze.md`** để đề đi đường module không phải trả tiền cho từ vựng nghĩa
vụ. Không được gộp vào lượt viết IR: một lượt sinh cả nghĩa vụ lẫn chương trình
thì C₁a tự đối chiếu một nguồn với chính nó.

### `backend/scripts/ocr_sgk_ingest.py` · **live** (Cloud Vision), có CACHE

Đọc SGK bản QUÉT thành text. Năm cuốn trong `data/knowledge/sources/` không có
lớp chữ — `pdftotext` trả 60 ký tự cho 60 trang, đúng bằng số dấu ngắt trang.
Repo **không có** RAG/index/cache nào để tái dùng, và `app/ingestion/input.py`
là lớp chuẩn hoá input của **sản phẩm** (text/docx/ảnh), không đọc PDF.

Đường đọc: PyMuPDF dựng ảnh trang → Cloud Vision `document_text_detection`.
Credential lấy từ `.secrets/` qua `GOOGLE_APPLICATION_CREDENTIALS`; **không in
và không ghi** giá trị secret vào artifact.

**Cache là điểm chính**: mỗi trang OCR đúng một lần rồi ghi vào
`data/knowledge/ocr-cache/<sách>.json`. `data/` bị gitignore nên text SGK không
vào kho mã. `--stats` báo trạng thái cache mà **không tốn call nào**.

### `backend/scripts/validate_sealed_submission.py` · offline, CUSTODIAN chạy

Kiểm **hình dạng** tập SEALED trước khi niêm phong: trường thiếu, `case_id`
trùng, `obligation_kind` sai chính tả, 4 metadata guard, và dạng `expected` cũ
`{tên_biến: giá_trị}` (bị bỏ vì tên biến do LLM đặt). Tách khỏi runner có chủ
đích — runner chạy một lần, còn cái này chạy bao nhiêu lần cũng được vì không
gọi API.

**Cố ý KHÔNG kiểm** phạm vi đề và tính đúng của ground truth: ground truth mà
máy kiểm được thì không còn độc lập. Khoá bởi `test_sealed_validator.py`, gồm cả
một test chống chính nó tự nhận là bộ chấm.

### `backend/scripts/run_sealed_evaluation.py` · **live**, chạy ĐÚNG MỘT LẦN

Runner Task 12. Kiểm candidate + vân tay con dấu **trước** khi mở SEALED, chạy
`run_pipeline(semantic_route="shadow")` nên MỘT lượt đo được cả hai route. Ngân
sách 440 logic / 520 HTTP cưỡng chế qua `gemini.ApiBudget` (dùng lại, không viết
bộ đếm mới). Viết **trước** khi thấy SEALED có chủ đích; phần chấm/tổng kết được
khoá offline bởi `tests/semantic_program/test_sealed_runner.py` vì chạy lại là
mất tính held-out.

Bốn thứ trong đây dễ bị viết sai vào luận văn, nên mỗi thứ có một test khoá:
**A−B phải phân rã** (chỉ một nhánh là `verification_gap`) · **B là
STRONG-assurance nội bộ, không phải "đúng"** (oracle độc lập báo riêng, và case
`servable` mà oracle nói sai được nêu đích danh) · **D1 là claim CẤU TRÚC**
(số lượt LLM đứng yên khi số bước trải rộng; token/case chỉ là telemetry hỗ trợ)
· **N=40 khoá**, chạy thiếu thì `evaluation_complete: false` và A/B không được
công bố như kết quả chính.

**`--dataset dev` (2026-08-24) — đường đo KHÔNG cần seed của GVHD.** 20 case ở
`dev/cases.json`, tập tự khai *"DEV **được nhìn**; SEALED thì không"*. Chạy nó
**không đốt** pool 49 bài held-out và **không cần** seed, nên nó là cách duy
nhất biết A/B của hệ hiện tại trước lượt #2. Ba khác biệt so với đường sealed,
đều cố ý: bỏ `_kiem_seal()` (DEV không có con dấu — giả vờ có là nói dối xuất
xứ) · **vẫn** `_kiem_candidate()` (chạy trên cây đã trôi thì số không gắn với
bản nào) · trần riêng `TRAN_LOGIC_DEV`/`TRAN_HTTP_DEV` = 260/310, **dẫn từ cùng
call graph** với N=20 nên đổi một trần không kéo trần kia theo.

⚠️ **Số của DEV không bao giờ là số của luận văn**: hệ đã được chỉnh trên chính
20 case này. Nó trả lời đúng một câu — *bốn biên chuẩn hoá + vòng sửa có làm
phễu thông hơn không*. Oracle sẽ **UNGRADED toàn bộ**: ground truth của DEV còn
ở định dạng cũ (khoá theo TÊN BIẾN), không phải hợp đồng nghĩa-vụ + giá-trị mà
`_cham` đòi — và **không được tự chuyển đổi**, viết lại ground truth là việc của
custodian. Báo cáo tự đeo `dataset` + `canh_bao_dataset`; đầu ra mặc định vào
`dev-results/`, và có **chặn cứng** không cho DEV ghi vào `results/`. Khoá bởi
ba test mới ở `test_sealed_runner.py` §7.

**ĐÃ CHẠY 2026-08-23 — lượt duy nhất, không được gọi lại.** Artifact ở
`docs/evaluation/semantic-benchmark/results/`:

- `sealed_summary.json` — số tổng hợp (A/B/A−B/oracle/D1/D2/ngân sách).
  **Hai khối thêm 2026-08-24, đọc được từ LƯỢT #2 trở đi**:
  `token_dau_ra_theo_route` (token ĐẦU RA = `candidates` **+** `thoughts`, tách
  route sinh ↔ route module — bỏ `thoughts` là báo thấp đi gần ba lần, nó lớn
  hơn `candidates` 2,6× ở stage `semantic_program`; vẫn là telemetry HỖ TRỢ,
  **không** phải D2 vì hai route chạy trên hai population khác nhau) và
  `coercion_rate` (bốn biên chuẩn hoá nổ bao nhiêu lần — xem `coercion_stats.py`).
  Lượt #1 **không có** hai khối này, nhưng token đầu ra của nó vẫn tính lại được
  từ `sealed_cases.json[].token` vì `record_usage` đã ghi đủ năm trường ngay từ
  đầu.
- `sealed_cases.json` — 40 bản ghi case-level: `semantic` (stage_reached,
  executable, servable, error_code, reason), `legacy` (route module để so),
  `contract` (nghĩa vụ khai), `cham` (verdict oracle), `token` theo stage.
- `OFFICIAL_RESULT.md` — **bản diễn giải chính thức, nguồn trích cho luận văn**.
  Chứa cảnh báo bắt buộc: 17/40 case chết ở `spec_version` float vs
  `Literal["1.0"]`, nên A = 3/40 là cận dưới của cận dưới.

Gọi lại runner sẽ ghi đè artifact và **phá tính held-out** — muốn đo lại phải
niêm phong SEALED MỚI, không phải chạy lại tập cũ.

### `backend/app/simulation/execution_authority_gate.py` · offline

Thay khái niệm của `computation_gate.py` (file cũ GIỮ NGUYÊN cho đường module).
Luật: kết quả phải có **authority tất định** sở hữu. `SemanticProgramInterpreter`
là một authority; LLM thì **không bao giờ**.

### `backend/app/ai/telemetry.py` · offline

Sở hữu **bộ đếm token theo stage**. Dùng `ContextVar` (`stage_scope`) chứ không
thêm tham số vào `call_gemini`: hàm đó có 13 test double, và một double gãy vì
production thêm tham số QUAN TRẮC là mùi thiết kế.

### `backend/scripts/seal_benchmark.py` · offline

Khoá/kiểm fingerprint của SEALED benchmark. Thoát != 0 khi seal vỡ.

### `frontend/src/simulations/domains/semantic/` · offline

`model.ts` — đọc frame timeline, **không** tính lại bước; `validateSemanticConfig`
kiểm lại bất biến #32 ở phía nhận (envelope có thể đến từ lịch sử đã lưu).
`ui.tsx` — renderer 2D chỉ ĐỌC khung; `DoThi` vẽ `graph_view` bằng layout vòng
tròn TẤT ĐỊNH (không physics/camera/editor), và `visited`/`current` đến TỪ
BACKEND — renderer không được tự chạy lại BFS. `index.ts` — đăng ký module,
**shadow-only** cho tới hết Task 12.

### `frontend/scripts/l5a-semantic-visual.mjs` (L5a) · cần Chrome + `npm run dev`

Sở hữu **soát thị giác đại diện** của route semantic: 4 ca × 2 bề rộng, đo
`getBoundingClientRect()` thay vì so ảnh pixel (repo không có `@playwright/test`).
Năm phép đo: chữ đè chữ · tràn/clipping · con trỏ chui vào nhãn · **chữ lặp** ·
khung ĐỔI sau 6 bước. Có `--faultcheck` để chứng minh guard đỏ được — bắt buộc
chạy trước khi tin một bản soát "SẠCH" (`ARCHITECTURE_MAP §8` #14). Fixture
`frontend/tests/fixtures/semantic/semantic_l5a.json` **sinh từ backend thật**,
không viết tay. (Trước vNext nó nằm ở `public/` nên bị Vite chép thẳng vào
`dist/` — script đọc nó bằng `fs`, chưa bao giờ qua HTTP. Khoá bởi
`src/public-assets-hygiene.test.ts`.)
Kết quả: `docs/evaluation/semantic-l5a/`.

### `frontend/scripts/capture-stack-vnext.mjs` · cần Chrome + `npm run dev`

Bằng chứng trình duyệt thật cho kịch bản Stack vNext: kiểm tra trạng thái tương tác
thay đổi thật sự khi bấm chuyển bước (khắc phục điểm mù của SSR renderToString).
Đo đạc dấu vân tay trang, kiểm tra render ngăn xếp qua Playwright và hỗ trợ `--faultcheck`.

