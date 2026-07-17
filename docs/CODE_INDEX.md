# CODE_INDEX.md — Chỉ mục module quan trọng

Mục đích: biết **cái gì đã tồn tại và ở đâu** trước khi viết mới (chống trùng
helper, chống hard-code vòng qua abstraction sẵn có). **Không chép thân hàm.**
Helper private nhỏ được bỏ qua có chủ ý.

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
`stage_adapt`, `try_pattern_reuse`, `run_pipeline(text, api_key, pattern_store=None)`.
Deps: catalog, manifest, representation, semantic, patterns, gemini.
Tests: `test_pipeline.py`, `test_reuse.py`, `test_capability_boundary.py`.
Notes: capability gate chỉ chặn **đường generic** (bất biến #5). `pattern_store`
inject → None = hành vi compose cũ.

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
gộp cả bốn thứ trên (+ `object_roles`, `role_coercions` rỗng = DENY mặc định)
thành **MỘT artifact hợp đồng ngữ nghĩa canonical**, sinh ra `dsl-contract.json`
cho frontend (xem entry `scripts/generate_dsl_contract.py` bên dưới) — không tầng
nào viết tay allowlist song song. Re-verify: offline; nếu đổi shape hợp đồng thì
**phải chạy lại generator** trước khi commit hoặc `test_dsl_contract_json_khong_troi_khoi_manifest`
sẽ đỏ.

### `simulation/computation_gate.py` (M13) · Change impact: offline
Cổng B (workstream B): SERVER quyết accept/gap trên đường generic bằng **hai
kênh tín hiệu có cấu trúc bổ sung nhau**, tất định, KHÔNG đọc text đề, chạy
**sau** `build_representation_plan`, **trước** classify.
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

### `simulation/catalog.py` · Change impact: targeted live
Bản chiếu registry phía backend: `SimSpec` (description/schema/contract/validator/
make_title) cho từng `simulation_id`. Exports: `CATALOG`, `SimSpec`, `catalog_text`.
Notes: `_GENERIC_SCHEMA` enum **phải** dẫn xuất từ manifest (anti-pattern #1).
Enum `simulation_id` của classify (`_classify_schema`) DẪN XUẤT từ `CATALOG.keys()`
→ thêm entry vào CATALOG là ĐỦ để classify được phép trả id đó (M10-AI-ROUTE:
`network.protocol_encapsulation`). Hai module network phân biệt bằng **description**
(biến đổi PDU qua TẦNG ↔ đường đi qua NÚT), không keyword hard-code trong runtime.
Đổi menu classify → **bump `CACHE_VERSION`** ở `main.py`.

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

### `evaluation/live.py` · Change impact: full live
CLI live: **bắt buộc `ALLOW_LIVE_AI=1`**, `--suite smoke|full|boundary`,
`--max-cases`, `--max-api-calls`, `--max-retries`. Tests: `test_live_budget.py`.

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

### `simulations/domains/algorithm/interaction-policy.ts` · Change impact: offline
M9-S1 — chính sách what-if theo cơ chế (hết "một swap cho cả 8 bài"). Exports:
`whatIfPolicyOf`, `WhatIfPolicy`, `WhatIfMode` (free: bubble/insertion · framed:
linear_search · challenge: find_max/min + binary_search, ẩn mặc định, mở qua nút
thí nghiệm có khung · hidden: sum/count). Mỗi policy kèm `rationale` (vì sao
không trang trí). Gating theo `algorithm_id` ngữ nghĩa. Tests:
`interaction-policy.test.ts`, `algorithm-ui.test.tsx`.
`network/model.ts` exports: `bfsRoute`, `buildSteps`, `currentStep`, `typeLabel`,
`neighborsOf`, `hopDistance`, `NetworkState` (topology + route + steps + cursor).
**M7.FREEZE**: bố cục KHÔNG còn trong state — `layout2d` sống trong
`network/ui.tsx` (renderer). Tests: `domains.test.ts` (khóa state
renderer-neutral), `network/render.test.tsx`.

### `simulations/domains/network/ui3d.tsx` · Change impact: offline
M8 — renderer 3D (Three.js thuần, KHÔNG @react-three/fiber) của
`network.packet_routing`: đọc NGUYÊN NetworkState, không engine/BFS/prediction
riêng. Exports: `Network3DWorkspace`, `layout3d` (pure: route z=0, ngoài route
lùi chiều sâu), `tryCreateWebGLRenderer` (fail → null, không ném),
`WEBGL_FALLBACK_MESSAGE`. Nạp qua `React.lazy` trong `network/index.ts`
(code-split ~549KB — chỉ tải khi bấm 3D). Camera OrbitControls (xoay+zoom, khoá
pan) + nút reset GÓC NHÌN (không reset mô phỏng); dispose/RAF-cancel đầy đủ khi
unmount. Tests: `render3d.test.tsx`, `m8-acceptance.test.tsx` (kịch bản nghiệm
thu 2D→dự đoán→3D→2D). Deps: `three` (+ `@types/three` dev).

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

### `components/SimulationWorkspace.tsx` · `SimulationControls.tsx` · offline
Host sân khấu; thanh điều khiển **capability-driven** (có `timeline` mới hiện
Next/Prev/Play) — tiền lệ cho EditPolicy. M8: Stage = `rendererFor(mod, mode)`
trong `<Suspense>` (renderer lazy); export `VisualModeToggle` (component thuần
theo props — toggle 2D/3D chỉ khi ≥2 mode khả dụng); `PredictionBar` nằm NGOÀI
renderer nên tự nhiên renderer-independent.

### `llm/client.ts` · Change impact: offline
Exports: `analyzeViaServer`, `editViaServer`, `explainViaServer`, `fetchHealth`,
`EditResponse`. Notes: trình duyệt không bao giờ giữ API key.

### `test-setup.ts` · Change impact: offline
Guard offline vitest: stub `fetch` → ném lỗi. Tests: `llm/offline-guard.test.ts`.
