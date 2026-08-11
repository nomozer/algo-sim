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
| `CACHE_VERSION` | **25** | `grep -n 'CACHE_VERSION = ' backend/app/main.py` |
| `HISTORY_SCHEMA_VERSION` | **2** | `frontend/src/state/history.ts:33` |
| Family / Target | **11 / 22** | `backend/.venv/Scripts/python.exe backend/scripts/catalog_runtime_matrix.py` |
| ↳ computation / representation | **10 / 1** — xem §0h | `result_authority` trên `FamilyMembership` |
| Trình bày 2D / 2D+3D | **20 / 2** | `SimSpec.visual_modes`; parity `capability-descriptors.test.ts` |
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
observer=None)`, (M15) `classify_with_one_route_recovery`.
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
Notes (M15 Task 16): `sorting` tốt nghiệp `PILOT` → `SUPPORTED` sau formalize
thành family selector (M14) + conformance proof (M15) — note tự giới hạn claim
(live n=4 M14 + n=2 M15 W1 — đếm case live chạm sorting gồm cả near-miss từ
chối đúng — là **targeted acceptance, KHÔNG phải bằng chứng thống kê**, không
được nói mạnh hơn). `binary_system` note bổ sung control cơ
số ≠ 2 (M15 W1: hex/octal → `capability_gap` có 2 lớp phòng thủ, xem
`mechanism_gate.py`).

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
lưu theo phiên (`OpenSession`), reset khi `loadEnvelope`/`resetSim`/`reset`.
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
`GenericExecutionError`, `displayLabel`.
Tests: `generic.test.ts`, `patch.test.ts`.
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

### `components/SessionRail.tsx` — PHIÊN ĐANG MỞ (W4B-2Z §29)
Cột trái liệt kê các mô phỏng ĐANG MỞ; mở/chuyển/đóng phiên + "+ Mô phỏng mới".
**Chỉ dựng khi có ≥2 phiên** (`.has-rail` do `App.tsx` gắn) — một cột rỗng sẽ ăn
bề ngang của sân khấu suốt thời gian còn lại. ≤1100px: nằm ngang phía trên sân
khấu, cuộn ngang.

Sở hữu state: `state/store.ts` — `sessions: OpenSession[]` + `activeSessionId`,
với `newSession` / `switchSession` / `closeSession`. `active` là BẢN LÀM VIỆC
của phiên đang chọn; chuyển phiên = chụp bản làm việc vào phiên cũ rồi khôi phục
bản của phiên mới (đúng tham chiếu object cũ).

**Phiên ≠ Lịch sử.** Lịch sử ghi "đã từng mở" (bền, localStorage,
`reopenFromHistory` dựng lại từ envelope rồi tua tới `lastCursor`). Phiên ghi
"đang mở và đang dở" — chuyển phiên KHÔNG dựng lại gì, nên what-if của học sinh
còn nguyên. Cả hai đều ZERO-AI nhưng vì lý do khác nhau.
Tests: `state/sessions.test.ts` (A→B→A, đóng phiên, 0 `fetch`, 0 `init`).

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

### `components/SearchActionZone.tsx` — HAI export, HAI trách nhiệm · offline
`SearchStateView` = **trạng thái quan sát** của bước tìm kiếm (tiền đề · chip vị
trí/đích/vùng xét · quan hệ · khối chi phí) — render **NGOÀI** cổng Thí nghiệm.
`SearchActionZone` = **chỉ** điều khiển cam kết (lời nhắc · nút · phản hồi), do
`commitmentSurfaceVisible` gác. Tách ở W4B-2V vì gác cả cụm làm mất trạng thái
quan sát (hồi quy W4B-2D). Luật: **cổng gác quyền hành động, không gác thông
tin.** Dải nhân quả KHÔNG dựng cho họ tìm kiếm nữa — `SearchStateView` là chủ sở
hữu duy nhất của quan hệ ở họ này.

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

### `frontend/scripts/accept-w4b3a.mjs` · Change impact: offline (cần `npm run dev`)
W4B-3A — NGHIỆM THU TRÌNH DUYỆT ở BỐN bề rộng (1920/1536/1366/768) cho 7 target
đại diện: 0 dải `experiment-trigger`; mọi `.sim-secondary-action` phải nằm TRONG
`.player-controls`; không tràn ngang; mở Thử thách ⇒ ≤1 bề mặt cam kết; parity
2D↔3D của `protocol_encapsulation` (cursor/stepCount/`getExplainContext` phải
KHỚP khi đổi cách xem); phiên A→Khám phá→B→A giữ nguyên object state, 0 `fetch`.
Có dấu vân tay trang + `--self-test` (tiêm lỗi giả, exit 1). Cờ:
`--port --out --self-test`. Artifact: `docs/evaluation/m17/w4b3a-after/`.

**BẪY ĐÃ CẮN MỘT LẦN — đọc trước khi viết script CDP mới.** Vite gắn
`?t=<timestamp>` vào URL module sau HMR, nên `import('/src/state/store.ts')` từ
console có thể trả về **instance THỨ HAI**: script lái một store, trang vẽ theo
store kia, và mọi khẳng định "không thấy X" đều XANH vì lý do sai. Script này
giải URL từ chính trang (`performance.getEntriesByType('resource')`).
`measure-composition.mjs` KHÔNG có lớp bảo vệ đó — nó thất bại ồn ào (null
`querySelectorAll`), nên gặp lỗi đó thì **restart `npm run dev`**, đừng sửa số.

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
