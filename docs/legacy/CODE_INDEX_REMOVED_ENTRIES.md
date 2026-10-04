# CODE_INDEX.md — phần đã tách, chép nguyên văn

> Tách khỏi [`CODE_INDEX.md`](../CODE_INDEX.md) ở run `cuboid-final-review` (2026-10-05): mục mô tả mã đã gỡ (miền Tin học, DSL, công cụ và module đã xoá); chỉ mục truy vết ngắn của mã đã gỡ vẫn ở §0j.
> Nguồn: `docs/CODE_INDEX.md` tại commit `4048ff83d14ad2a1fcd940d127590ca777dbc7cf` (blob `a7758cf84b6f47528d551c4c1d3fbb9d82733ae3`). Mỗi khối dưới đây là **nguyên văn** (byte-identical)
> các dòng ghi trong chú thích của nó, theo thứ tự của bản gốc. Đây là lịch sử: không sửa, không thêm.
> Đường dẫn tương đối trong các khối viết cho thư mục `docs/`, nên từ `legacy/` chúng trỏ lệch một cấp
> (`README.md`). Kiểm lại: `docs/evaluation/geometry/runs/cuboid-final-review/diagnostics/split_history_cfr.py --verify`.

<!-- khối 1/96 · dòng 246–263 của bản gốc · whole section about removed code (⛔) · sha256 e8b457b26a64e902ad0cd6270b176981721d0570dbdde7cff7b1f08391ee1f67 -->
## ⛔ 0i. ĐÃ GỠ (HISTORICAL_REMOVED) — Đổi cơ số, MỘT nguồn (M17 P1a)

> `domains/binary/` gỡ ở `FRONTEND_LEGACY_FIXTURE_CUTOVER`. Giữ lại mục này
> vì khuôn *"một nguồn tất định, module re-export, test so tham chiếu hàm"*
> vẫn là tiền lệ đáng đọc — nhưng **không file nào dưới đây còn tồn tại**.

`frontend/src/simulations/domains/binary/base-conversion.ts` — phần **thuần tất
định** của đổi cơ số: `toBase`, `divideSteps`, `weightSteps`, `buildConvSteps`,
`parseInBase`, `digitsValid`, `canonicalDigits`, `strategyOf`, `BASE_NAME`,
`CONV_BASES`, `CONV_MAX_VALUE` + kiểu `ConvBase`/`ConvStep`/`DivideStep`.

- **Không** React / renderer / store / registry / target id;
- `convert-module.tsx` **re-export** ⇒ mọi import cũ (`./convert-module`) giữ nguyên;
- `encoding-module.tsx` dùng `divideSteps()` — **không** có converter thứ hai
  (test so **tham chiếu hàm**, và quét thư mục tìm bản cài trùng).

Trước khi viết bất kỳ phép đổi cơ số nào: **dùng file này**, đừng cài lại.

<!-- hết khối 1 -->

<!-- khối 2/96 · dòng 264–304 của bản gốc · whole section about removed code (⛔) · sha256 5be8b7d44d2ddcf05e49e10d2e868c19d76d7054658c623fcb12a3e76e74876d -->
## ⛔ 0h. ĐÃ GỠ — Mô phỏng cơ chế ≠ biểu diễn tiến triển (M17 P1b)

> Taxonomy 11 family và `FamilyMembership.result_authority` thuộc hệ Tin học,
> gỡ ở `LEGACY_INFORMATICS_REMOVAL`. Phân biệt *chạy cơ chế* với *dựng khung
> biểu diễn* vẫn đúng về ý niệm; con số và tên family thì **không còn**.

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

<!-- hết khối 2 -->

<!-- khối 3/96 · dòng 451–457 của bản gốc · entry of removed code · sha256 f868e76cc771193631d33c7f27aa9a74930a5033ebf32d8ec889e21a4203f29c -->
### `ai/edit.py` · Change impact: targeted live
NL edit nhẹ (M7.14A): 1 call LLM sinh `{required_roles, operations}`; server đối
chiếu `known_gap_roles` **tất định** rồi áp patch.
Exports: `EDIT_SCHEMA`, `edit_simulation(config, instruction, api_key)`.
Tests: `test_edit.py`. Notes: KHÔNG chạy analyze/classify/simulate; LLM không được
quyết supported/unsupported.

<!-- hết khối 3 -->

<!-- khối 4/96 · dòng 468–498 của bản gốc · entry of removed code · sha256 cb5eb02b0a9492b0f215f9ef915c29aaa5991590ee85b7c88da3b40f2ce18cdf -->
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

<!-- hết khối 4 -->

<!-- khối 5/96 · dòng 499–515 của bản gốc · entry of removed code · sha256 94daa3ca57c0014c9eac19289ba0b07b22159291231b4ccbfe506ee331f4e49d -->
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

<!-- hết khối 5 -->

<!-- khối 6/96 · dòng 516–538 của bản gốc · entry of removed code · sha256 aa5488ddeaf251313a26ee231036d55c13deef0456c73e0fa2f6a1f63c4d2699 -->
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

<!-- hết khối 6 -->

<!-- khối 7/96 · dòng 539–561 của bản gốc · entry of removed code · sha256 137a3593e6b22c8a80b30ad0c71e5ea8d8250815710b496fe011d0d4167c639b -->
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

<!-- hết khối 7 -->

<!-- khối 8/96 · dòng 562–569 của bản gốc · entry of removed code · sha256 39684b9a8ff073b42bf5e686edf57cd3cde323bdf6ade9f1a680e37b43e8021e -->
### `simulation/dsl/validator.py` · Change impact: offline
Validator SimulationSpec (allowlist/limits **dẫn xuất từ manifest**), drag
constraints, ownership rule, cấm chu trình parent/rule; (M11) **cấm hai rule
cùng ghi một target** — với đánh giá điểm bất động, rule sau trong mảng thắng
mỗi vòng quét → ngữ nghĩa phụ thuộc thứ tự khai báo.
Exports: `validate_generic_config`, `ownership_conflict`, các hằng allowlist.
Tests: `test_dsl.py`, `test_manifest.py`. Mirror TS: `generic/validate.ts`.

<!-- hết khối 8 -->

<!-- khối 9/96 · dòng 570–574 của bản gốc · entry of removed code · sha256 ac20c7086ae72ed2ad8533bae9e1d63b2e5fb8107094729dbaed34c0561af496 -->
### `simulation/representation.py` · Change impact: offline
Plan tất định + **capability gate** + scene_mode.
Exports: `required_roles`, `build_representation_plan`, `scene_mode_guidance`,
`check_scene_consistency`. Tests: `test_representation.py`.

<!-- hết khối 9 -->

<!-- khối 10/96 · dòng 575–587 của bản gốc · entry of removed code · sha256 e8b16763a10d4ce97f3f1971ecff9271a28f48124d4aa21f8aff6627bc176782 -->
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

<!-- hết khối 10 -->

<!-- khối 11/96 · dòng 588–605 của bản gốc · entry of removed code · sha256 216d1107ba7c91ab46d386e11943a8420e1d498460bd2cabb6150a91531fad17 -->
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
xem cảnh báo ở `docs/legacy/superpowers/plans/2026-07-16-m13-generic-semantic-soundness.md`
Task 4. Tests: `test_generic_engine_m13.py` (mới) + `test_semantic.py` (M11
canary chuỗi đảo thứ tự vẫn đúng giá trị — bằng chứng ngữ nghĩa KHÔNG đổi cho
spec hợp lệ).

<!-- hết khối 11 -->

<!-- khối 12/96 · dòng 606–623 của bản gốc · entry of removed code (heading marked removed) · sha256 175d4f9020241d2e79241a1137fa977d482f3324a1efdb4c1ec3a9ea151a2313 -->
### ⛔ ĐÃ GỠ (FINAL_DEAD_EVALUATION_CLEANUP 2026-09-02) — `scripts/generate_dsl_contract.py` → `frontend/src/simulations/domains/generic/dsl-contract.json` (M13) · Change impact: offline

> Nó import `app.simulation.dsl.manifest` (gỡ ở `LEGACY_INFORMATICS_REMOVAL
> PART 2`) và ghi vào `domains/generic/` (gỡ ở `FRONTEND_LEGACY_FIXTURE_CUTOVER`)
> — cả nguồn lẫn đích đều không còn, sync-lock `test_manifest_providers.py` cũng
> đã gỡ. Đừng dựng lại `manifest.py` chỉ để nó chạy được. Mô tả dưới đây giữ lại
> để đọc *vì sao* khuôn generator/sync-lock ra đời.
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

<!-- hết khối 12 -->

<!-- khối 13/96 · dòng 624–633 của bản gốc · entry of removed code · sha256 988e235f1c3052e7a7440c11dd11252f6943d627d63055275169b8b19803192c -->
### `simulation/scan_engine.py` (M12) · Change impact: offline
Port Python của scan-interpreter — mirror `frontend/src/core/scan.ts` (CÙNG
LUẬT, đổi một bên thì đổi cả hai). Backend không dựng timeline cho học sinh;
port tồn tại để validator server-side + harness chấm HÀNH VI (semantic kind
`bounded_scan`). Exports: `validate_scan_spec`, `run_scan`, `SCAN_VERSION`,
`CONDITION_OPS`, `UPDATE_KINDS`, `MARKINGS`, `STOPS` (hằng public — schema
Gemini trong catalog DẪN XUẤT từ đây, khoá bằng
`test_scan_routing::test_scan_schema_enum_dan_xuat_tu_scan_engine`).
Tests: `test_scan_engine.py`, `test_scan_routing.py`.

<!-- hết khối 13 -->

<!-- khối 14/96 · dòng 634–643 của bản gốc · entry of removed code · sha256 b4b3b865391b4c48a873592c48f6ca5e7aa33c4c04409eaff9489b855508c2ed -->
### `simulation/character_encoding.py` (M17 W3) · Change impact: targeted live
NGUỒN DUY NHẤT của từ vựng + giới hạn mã hoá ký tự. Exports: `SPEC_VERSION`
("charenc-1.0"), `ENCODINGS` (ascii | unicode_codepoint), `MAX_TEXT_CODE_POINTS`
(12), `ASCII_MAX`, `BMP_MAX` (65535 — trùng `CONV_MAX_VALUE`), `SURROGATE_MIN/MAX`,
`FORBIDDEN_SPEC_KEYS`, `encoding_enum()`, `code_point_out_of_range()` (một nguồn
cho cả kiểm định lẫn thông điệp từ chối).
Consumers: `catalog.py` (schema DẪN XUẤT), `validation/character_encoding.py`.
Notes: **backend KHÔNG có engine mã hoá và KHÔNG có bộ chuyển số sang nhị phân** —
`ord()` chỉ dùng kiểm khoảng. Thực thi nằm ở FE.

<!-- hết khối 14 -->

<!-- khối 15/96 · dòng 644–650 của bản gốc · entry of removed code · sha256 8105f06506092083bfe160cc605098cd322326b6fffca9d3480f4cbbfdebac7b -->
### `validation/character_encoding.py` (M17 W3) · Change impact: offline
Validator FAIL-CLOSED: `validate_character_encoding_config(raw) → (config|None, error|None)`.
Bắt: encoding ngoài enum · text không phải chuỗi (số 7 ≠ ký tự '7') · rỗng · quá
12 **code point** · ngoài ASCII ở chế độ ascii · ngoài BMP · surrogate · trường
thừa · spec mang kết quả (R0). KHÔNG coercion, KHÔNG thay ký tự bằng `e`/`?`.
Tests: `test_character_encoding.py` (gồm test khoá "backend không có engine").

<!-- hết khối 15 -->

<!-- khối 16/96 · dòng 651–662 của bản gốc · entry of removed code · sha256 4f3f9d2d71a57e21995f39969c2dcafd3c0e3b4249edf75ab728fb2daa394c38 -->
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

<!-- hết khối 16 -->

<!-- khối 17/96 · dòng 663–679 của bản gốc · entry of removed code · sha256 97e6ca647071fb7a93e0d21ac1075b8694ee3ef187c10a5b5e4a91e86eb918ad -->
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

<!-- hết khối 17 -->

<!-- khối 18/96 · dòng 680–689 của bản gốc · entry of removed code · sha256 084ba37352d80abe829a1fe554a5733d3b3839184072dbfb6ab0ddd393b45ca9 -->
### `validation/program.py` (M17 W2C) · Change impact: offline
Validator FAIL-CLOSED cho `algorithm.bounded_control_flow`. Exports:
`validate_program_config(raw) → (config|None, error|None)`.
Bắt: kind ngoài ngữ pháp · biến chưa khai báo · sai kiểu (KHÔNG coercion) ·
chia/mod cho 0 tĩnh · điều kiện không phải boolean · while thiếu `max_iterations` ·
**definite-assignment** (W2C-C1 §L1: đọc biến chưa chắc có giá trị → từ chối;
if/else = GIAO hai nhánh, if-không-else và while KHÔNG mở rộng) ·
biểu thức lồng vòng/quá sâu · câu lệnh mồ côi hoặc thuộc hai khối · spec mang
kết quả (R0). Deps: `program_spec`. Tests: `test_program_spec.py`.

<!-- hết khối 18 -->

<!-- khối 19/96 · dòng 690–717 của bản gốc · entry of removed code · sha256 351f6dfc1b78d7d2695b50f1c61f22725a710abbae2903a591e102e0159d6026 -->
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

<!-- hết khối 19 -->

<!-- khối 20/96 · dòng 718–735 của bản gốc · entry of removed code · sha256 72a4ed4fd89f6adfc0fdf270233ddf868643d6941c012ab912a506e6d297e545 -->
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

<!-- hết khối 20 -->

<!-- khối 21/96 · dòng 736–741 của bản gốc · entry of removed code (heading marked removed) · sha256 2760697e4f61caba538cde74a3d113467feebcf570853dbba03af9721c6bbaaf -->
### ⛔ ĐÃ GỠ (FINAL_DEAD_EVALUATION_CLEANUP 2026-09-02) — `backend/scripts/curriculum_support_report.py` · Change impact: offline
W4B-3A — bảng hướng GIÁO VIÊN (mỗi đơn vị kiến thức được hỗ trợ tới đâu và theo
KIỂU nào), sinh từ `coverage.py`. Khác `catalog_runtime_matrix.py` (hướng kĩ sư)
và khác `after-matrix` (hướng sản phẩm, theo target). Cờ `--json/--md`. Artifact:
`docs/evaluation/m17/w4b3a-after/curriculum-support.{json,md}`.

<!-- hết khối 21 -->

<!-- khối 22/96 · dòng 759–772 của bản gốc · entry of removed code · sha256 b1706746874209637cf0008a13a4e3d955629e4369b3da699ff4116a97fa2665 -->
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

<!-- hết khối 22 -->

<!-- khối 23/96 · dòng 773–778 của bản gốc · entry of removed code · sha256 9031b09a73f20238ac7219ecfd0e5c69680d45d58b512fc81aa770282bfcbfe6 -->
### `domains/web/apply.ts::applyChannelChange` (M20 W5) · offline
Đổi MỘT kênh, giữ hai kênh kia — thao tác §2A đòi hỏi. Kênh tác động lên màu của
nút ĐANG CHỌN (`colorPropOf`), nên "chọn Tiêu đề rồi kéo R" không bao giờ chạm
tới nền: chỉ có một `selected` trong state, không có bộ chọn thứ hai để lệch.
Ngoài miền ⇒ `null` ⇒ giữ state cũ, KHÔNG kẹp về biên.

<!-- hết khối 23 -->

<!-- khối 24/96 · dòng 876–883 của bản gốc · entry of removed code · sha256 92dbcbd7a5fe366f270c45e5af74b1c584103d74540285a24822cc1e3b6e1892 -->
### `frontend/src/simulations/experience-gate.test.ts` (M20 W12) · cổng offline
Hỏi câu tối thiểu một mô phỏng phải trả lời được: có ít nhất MỘT action đổi được
state, HOẶC một dòng thời gian > 1 bước. Không có cả hai ⇒ **một bức hình**.
Chạy trong vitest nên nó có mặt lúc ai đó thêm target mới; bản chứng nhận trình
duyệt đầy đủ hơn nhưng cần Chrome và vài phút.
⚠️ Cổng này KHÔNG nhìn bề mặt ⇒ không phân biệt được "trace có mà không hiện".
Có đối chứng dương (module đồng nhất không timeline) + guard chống bộ dò rỗng.

<!-- hết khối 24 -->

<!-- khối 25/96 · dòng 898–913 của bản gốc · entry of removed code · sha256 ed813906740c0d8c9291c286c36779faa4464ea3a2e85eff1f778a4161c11e5d -->
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

<!-- hết khối 25 -->

<!-- khối 26/96 · dòng 914–930 của bản gốc · entry of removed code · sha256 48218edad62865fc92dbb4d05315491b97c7c21009128813340271cd1662aa04 -->
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

<!-- hết khối 26 -->

<!-- khối 27/96 · dòng 931–947 của bản gốc · entry of removed code · sha256 9e5e803722bae621a4371bcbbc0e3935da062a2866daeddc9cbe8c76de50d11e -->
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

<!-- hết khối 27 -->

<!-- khối 28/96 · dòng 1036–1053 của bản gốc · entry of removed code · sha256 01effcf4aebc9b16dee4d29f4fdf25ba8818b20ede5681c652a2336da1a32b9e -->
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

<!-- hết khối 28 -->

<!-- khối 29/96 · dòng 1087–1105 của bản gốc · entry of removed code (heading marked removed) · sha256 755f41f45089cd81fb8f2188779fefbf71a7a8f06f68da59ba0f30707099e670 -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `frontend/src/simulations/domains/color/` — `color.rgb_model` (W5A) · offline
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

<!-- hết khối 29 -->

<!-- khối 30/96 · dòng 1202–1232 của bản gốc · entry of removed code · sha256 3eca701ab47e25694fbbf12b7a71f01553b79be61860b19939cd7ab475d3fc63 -->
### `frontend/src/simulations/domains/geometry/scene3d-silhouette.ts` (2026-09-11) · offline

Sở hữu **ĐƯỜNG BAO khối cong**, phụ thuộc camera. Exports: `duongBaoKhoiCong` ·
`KhoiCongMoTa` · `LoaiKhoiCong` · `MauBao` · `DuongBao`. Người dùng:
`scene3d-view.tsx`, nhánh `render === "curved_solid"`.

Vì sao tồn tại: **mặt trơn không có cạnh thật**, nên `EdgesGeometry` vô dụng ở
đó. Đo trên sản phẩm trước wave này: p4/p5 dựng ra một **vệt xám không một nét
nào** — không vành, không đường sinh, không trục. Thứ làm nên hình dáng của mặt
trơn là đường bao, và nó ĐỔI KHI CAMERA ĐỔI.

Chia việc, và cách chia là điểm chính: **vành** (trên/dưới của trụ, đáy của nón)
là đường tròn CỐ ĐỊNH — phần thấy/khuất đã có hai lượt chiều sâu lo, y hệt cạnh
khối đa diện, tự đúng khi xoay mà không tính gì. Chỉ **hai đường sinh bao**
(trụ/nón) và **đường bao mặt cầu** mới phải tính lại mỗi khung.

Toán, dạng đóng, không dò số — `n` là hướng bán kính, `u` trục, `C` mắt:
trụ `n(θ)·(C−O) = r` ⇒ `θ = φ ± acos(r/R)` · nón `h(a cosθ + b sinθ) + r·c = 0`
⇒ `θ = φ ± acos(−rc/(hR))` · cầu: tâm `Q + (r²/D²)(C−Q)`, bán kính
`r√(1 − r²/D²)`. Khoá bằng `scene3d-silhouette.test.ts` — kiểm **điều kiện tiếp
tuyến** `n·(C−P) = 0`, không so với ảnh mẫu.

⚠ **`capNhat` KHÔNG được cấp phát.** Nó chạy mỗi khung; gọi lại `setPositions`
sẽ dựng `InstancedInterleavedBuffer` mới và phá điều kiện `capPhatBuffer = 0`
của cổng tương tác. Hình học dựng một lần, `capNhat` ghi đè vào mảng đã có.

⚠ **Vật bao động mang `userData.baoDong`** và phải đứng NGOÀI phép khớp khung:
lúc dựng bộ đệm toàn số 0 nên hộp bao ôm gốc toạ độ (đo được: p4 tụt từ 0,565
xuống 0,22 khung), và kể cả khi có toạ độ thật thì nó là hệ quả của vị trí
camera — để nó quyết định vị trí camera là một vòng lặp phản hồi.

<!-- hết khối 30 -->

<!-- khối 31/96 · dòng 1233–1252 của bản gốc · entry of removed code · sha256 c5fb5e778a64cafec631ba765d275916ca7b216af3b91ac7c9720ba59619f4bb -->
### `frontend/scripts/scene3d-d2-gate.mjs` (2026-09-12) · offline

**CỔNG NGHIỆM THU VÒNG D2.** Bổ sung cho `scene3d-fidelity-gate.mjs` (vai màu,
bề dày, nhãn chồng, tràn khung, nét khuất đổi chỗ) và `scene3d-orbit-gate.mjs`
(quay 360°, trục ổn định). Hỏi bốn câu hai cổng kia không hỏi:

- **bất biến DPR** — cỡ CSS và cỡ khung vẽ phải đúng tích số. Chỗ DUY NHẤT bắt
  được lỗi bật `setPixelRatio` mà quên `setSize(…, true)`, và lỗi lấy cỡ khung
  vẽ làm `resolution` của `LineMaterial`;
- **độ sắc** — vẽ thẳng ở 2× phải cho mép nét hẹp hơn bản 1× phóng to; đo được
  hẹp hơn 2,0×;
- **khoảng cách nhãn ↔ mực, đo từ ĐIỂM ẢNH** — không đọc lại niềm tin của bộ
  giải. Loại hộp chữ và hộp lớp phủ giao diện khỏi phép quét, vì chữ và ô đọc
  số cũng là mực nhưng không phải NÉT HÌNH;
- **lớp phủ có che nhãn không** — hộp CHỒNG nhau, khác hẳn "nằm gần".

Ma trận: P1–P7 × {1440×900, 390×844} × DPR {1, 2} = 28 ô. Khung nhìn ép bằng
`Emulation.setDeviceMetricsOverride` — `BrowserSession({viewport})` một mình cho
sai cỡ (xin 390 nhận 504).

<!-- hết khối 31 -->

<!-- khối 32/96 · dòng 1253–1279 của bản gốc · entry of removed code · sha256 556f9c73835b111518bdbbca2e6a4ae73a019bb1967a0e3f722b593b44134ccc -->
### `frontend/src/simulations/domains/geometry/scene3d-nhan.ts` (2026-09-12) · offline

Sở hữu **BỐ TRÍ NHÃN CÓ VẬT CẢN**. Exports: `giaiNhan` · `doanNetTrenMan` ·
`kcHopDoan` · `kcDiemDoan` · các kiểu `Doan` / `NhanVao` / `Hop` / `CanNhan` /
`ChoNhan` / `KetQuaNhan`.

Ba đời bộ đặt nhãn, và lý do phải sang đời thứ ba: ① đặt mọi nhãn ngay trên
điểm neo rồi **ẩn** cái nào chồng — `N` của `(MNP)` biến mất ở 1440×900, `S`
biến mất ở 390×844; ② tám hướng × hai bán kính, cộng dồn ba khoản phạt — vẫn
không biết gì về NÉT nên chữ đáp xuống đúng trên cạnh khối và biên thiết diện;
③ bản này: mười sáu hướng × bốn bán kính, và tách hẳn **ràng buộc cứng**
(loại thẳng ứng viên vi phạm) khỏi **giá mềm** (chỉ xếp hạng ứng viên đã hợp
lệ). Gộp làm một tổng phạt thì một vị trí đè lên cạnh vẫn thắng nếu nó gần neo
hơn — vi phạm mua được bằng điểm cộng ở tiêu chí khác.

`doanNetTrenMan` đọc `instanceStart`/`instanceEnd` của mọi `LineSegments2` nên
gom đủ cạnh khối, biên thiết diện, viền mặt phẳng, đường dựng và đường thẳng vô
hạn trong MỘT lối, không cần sổ đăng ký và không bỏ sót vai mới.
⚠️ `attributes.position` của `Line2` là khuôn tám đỉnh của MỘT đoạn (đều nằm
trên `z = 0`) — đọc nhầm chỗ ấy cho một chùm đoạn vô nghĩa quanh gốc toạ độ.

⚠️ **Hàm này không giấu nhãn và không tự nới ngưỡng.** Hết chỗ hợp lệ thì nó
đặt ở chỗ ít vi phạm nhất và khai tên nhãn ấy trong `thieu`; `scene3d-view.tsx`
lùi camera từng nấc rồi thử lại, tới sàn `0,72` thì khai
`LABEL_LAYOUT_UNSATISFIABLE`. Nới ngầm là cách một bản dựng trông đạt mà không
đạt.

<!-- hết khối 32 -->

<!-- khối 33/96 · dòng 1280–1316 của bản gốc · entry of removed code (heading marked removed) · sha256 551b11f33d3ed2749c055ef3a86e2358e8683442c34a4fddc5b3996fa5d5fa40 -->
### `frontend/src/simulations/domains/geometry/scene3d-tokens.ts` (2026-09-12) · offline · ⚠️ **ĐÃ GỠ** (kiểm 2026-09-29, xem mục w11)

Sở hữu **NGÔN NGỮ THỊ GIÁC** — nguồn token DUY NHẤT, và nó là **bản chép của
bộ mockup `p1`–`p7` đã duyệt**, không phải một bảng tự cân. Exports: `MAU_D2` ·
`MAU_GIAY_D2` · `BE_DAY_D2` · `DO_MO_D2` · `DIEM_PX_D2` · `DIEM_VANH_PX_D2` ·
`TI_LE_LAP_KHUNG_D2` · `NHAN_BAN_KINH` · `KHUNG_HEP_PX`.

Trước 2026-09-12 token nằm rải ba chỗ — màu ở `scene3d-view.tsx`, bề dày ở
`scene3d-wide-line.ts`, tỉ lệ lấp khung ở `scene3d-camera.ts` — nên không ai trả
lời được *"vai `cạnh khuất` gồm những gì"* mà không mở ba file, và một lượt sửa
màu rất dễ quên bề dày đi kèm. Renderer, test và mọi phép đo nay đọc chung file
này; `BE_DAY_PX` chỉ còn là bí danh của `BE_DAY_D2`.

⚠️ **Bảng này đã trôi khỏi mockup một lần, và trôi im lặng** (sửa 2026-09-12,
lượt sau). Vòng "D2" hạ toàn bộ thang bề dày (2,8/1,6/3,5 → 2,4/1,4/3,2), hạ
mảng tô còn một nửa tới một phần ba (0,07 → 0,035 và 0,022), thu chấm điểm từ
đường kính 8 px xuống 4,4 px, đổi nền giấy `#FAF9F7` thành trắng phủ gradient,
và đặt cho thiết diện khuất một màu hồng `#e79a84` mockup không có. **Không
dòng nào trong bảng thị giác còn khớp bản đã duyệt**, mà ba cổng vẫn xanh — vì
cổng đọc token, và token chính là thứ đã trôi.

Lý lẽ của vòng ấy nghe được nhưng đang tranh luận với một bản đã duyệt: nó coi
Δ màu thiết diện thấy/khuất = 0 là con bọ, trong khi mockup cố ý giữ chung màu
và tách bằng **độ mờ 0,55 + nét đứt**; nó coi ba lớp tô cộng dồn là vết bẩn, và
chữa bằng cách hạ từng lớp thay vì sửa chỗ cộng dồn. Luật rút ra: **mockup là
thẩm quyền, token chỉ là bản chép** — và test phải khoá **đúng con số mockup**,
không khoá một tính chất suy ra từ chúng.

Cặp vai thật sự gần nhau vẫn còn: cạnh khuất `#7d7975` ↔ mặt phẳng `#77736f`,
Δ ≈ 10,4. Mockup chấp nhận vì chúng tách ở chiều KHÁC — cạnh khuất là nét đứt
1,6 px không mảng tô, mặt phẳng là mảng tô 0,07 có viền liền 1,2 px mờ 0,85.

⚠️ File này là **DỮ LIỆU**: không import gì (kể cả `three`), không chứa phép
tính. `scene3d.test.tsx` khoá cả hai điều đó — một phép tính lọt vào đây là
thẩm quyền thị giác thứ hai và nó sẽ trôi khỏi renderer. Thang bậc màu/bề dày
khoá bởi `scene3d-tokens.test.ts`.

<!-- hết khối 33 -->

<!-- khối 34/96 · dòng 1317–1354 của bản gốc · entry of removed code (heading marked removed) · sha256 e6ca01713d146b02cc56826843e929bb9f9a0d598e8e8e8cd2afc18a84a563e4 -->
### `frontend/src/simulations/domains/geometry/scene3d-wide-line.ts` (2026-09-11) · offline · ⚠️ **ĐÃ GỠ** (kiểm 2026-09-29, xem mục w11)

Sở hữu **NÉT CÓ BỀ DÀY THẬT** cho khung 3D. Exports: `BE_DAY_PX` (bảng bề dày
theo vai, pixel CSS) · `DASH_TREN_GAP` · `DPR_TRAN` · `tiLeDiemAnh` ·
`datKichThuocKhung` · `kichThuocKhung` · `laVatLieuNet` · `capNhatDoPhanGiai` ·
`taoVatLieuNet` · `taoNet` · `TuyChonNet`.

⚠️ **`tiLeDiemAnh` sở hữu chính sách DPR, và nó đi CẶP với `setSize(…, true)`.**
Trần là 2 vì chi phí tô tăng theo bình phương. Trước 2026-09-12 `setPixelRatio`
không bao giờ được gọi nên màn retina nhận bản vẽ 1× phóng to. Bật nó mà vẫn
truyền `updateStyle = false` thì thẻ `<canvas>` phình gấp đôi theo px CSS và
`overflow: hidden` của `.geo3d-canvas` **giấu chỗ vỡ** — hỏng sẽ ship dưới dạng
"hình bị cắt". `resolution` của `LineMaterial` vẫn lấy cỡ CSS, nhờ vậy bề dày
px CSS bất biến theo DPR (đo được lệch ≤ 0,03 px). Khoá: `scene3d-dpr.test.ts`.

Vì sao tồn tại: **WebGL bỏ qua `THREE.LineBasicMaterial.linewidth`** — mọi
`THREE.Line` vẽ ra đúng 1 px dù khai bao nhiêu. Bảng token nói cạnh thấy 2,8 px
· cạnh khuất 1,6 px · thiết diện 3,5 px, nhưng đo trên ảnh sản phẩm thật thì bề
dày trung vị là **1,89 px cho mọi vai** — ba vai đọc ngang hàng và hình mất câu
trả lời *"cạnh này trước hay sau"*. Module dựng `Line2`/`LineSegments2` +
`LineMaterial`, bề dày thành bề dày thật. Đo lại sau bản vá: trung vị 3,34 px.
Người dùng: `scene3d-view.tsx` (qua `duongHaiLuot` và ba nơi gọi vai phụ).

⚠ **`resolution` phải là kích thước CSS, không phải kích thước buffer.** Shader
tính `offset_ndc = linewidth / resolution.y`; cho `resolution.y` = chiều cao CSS
thì bề dày theo pixel CSS đúng bằng `linewidth` ở **mọi** `devicePixelRatio`.
Truyền kích thước buffer sẽ cho nét mảnh đi DPR lần trên màn hình retina.

⚠ **Setter `LineMaterial.resolution` là `.copy()`, không giữ tham chiếu** — nên
không chia sẻ được một `Vector2` chung. `capNhatDoPhanGiai(goc, w, h)` quét cây
và gán lại từng vật liệu; `scene3d-view.tsx` gọi nó trong `chinhCo`.

⚠ **`Line2`/`LineSegments2` KẾ THỪA `THREE.Mesh`** ⇒ `isMesh === true` và có
`attributes.position`, nhưng position ấy là **khuôn của một đoạn** (8 đỉnh, tất
cả z = 0). Mọi phép quét đếm tam giác theo `isMesh` sẽ nhặt phải khuôn đó — phép
đo diện tích chiếu đáy khối lõm đọc ra 14 thay vì 10 đúng vì lý do này. Vật nét
mang cờ `userData.net = true` để loại ra, cùng lối với `userData.chieuSau`.

<!-- hết khối 34 -->

<!-- khối 35/96 · dòng 1355–1385 của bản gốc · entry of removed code · sha256 894dce050a5f13c7505cbe74c6a5795a2c8b20ee8b187776c768444474b548b4 -->
### `frontend/scripts/scene3d-fidelity-gate.mjs` (2026-09-11) · offline

Sở hữu **CỔNG TRUNG THỰC THỊ GIÁC** trên `dist/`: hình có đúng ngôn ngữ đã
duyệt không. Exports: `NGUONG` · `TRANG_THAI` (11 trạng thái) · `doAnh` ·
`doiChoKhuat` · `soatNhan` · `motCa` · `phanLoai` · `chay`. Cờ: `--ca` · `--ra` ·
`--anh` · `--tiem` · `--bo-qua-build`. Đo P1–P7 ở `1440×900` và P1/P6/P7 ở
`390×844`, mỗi ca chụp thêm một ảnh SAU KHI XOAY.

Bốn phép đo: ① mực và tràn khung · ② đếm điểm ảnh theo vai màu (`#D95A43` phải
có ở ca có thiết diện; `#0075DE` phải bằng 0 khi chưa chọn gì) · ③ bề dày nét
bằng `doBeDayCucBo`, loại vùng chữ · ④ nhãn đọc thẳng từ DOM (cỡ, độ đậm, ra
ngoài khung, đè nhau).

⚠ **Ngưỡng mực là 200, không phải gần nền.** Nền khung là gradient `L ≈ 227…248`
và mảng tô khối (opacity 0,07) rơi vào `L ≈ 230` — nền và mảng tô **cùng một
dải**. Lượt chạy đầu để ngưỡng 232 và đọc ra `chiếm = 0,999` ở mọi ca: cổng đang
đo nền chứ không đo hình.

⚠ **Lớp phủ phải loại theo DOM.** Hai nút "Tách khối"/"Xem lại toàn hình" nằm
ĐÈ LÊN canvas; không loại thì mực của chúng tính vào hình và mọi ca đọc ra
`TRAN_KHUNG`.

⚠ **`doiChoKhuat` so VỊ TRÍ, không so số lượng.** Bản đầu so số điểm ảnh xám
trước/sau khi xoay; p6 ở `390×844` rơi đúng vào ca hai ảnh khác hẳn nhau mà cùng
số điểm (`Δ = 0,016`). Hiệu đối xứng của hai mặt nạ cho `Δ = 0,98–0,99`.

⚠ **`kiemDistMoi()` — `dist/` phải mới hơn `src/`.** Bản sửa của một kết luận
SAI đã xảy ra thật: một phép tiêm không biên dịch được, `npm run build` đỏ,
`--bo-qua-build` bỏ qua, và cổng đo `dist/` của **phép tiêm trước đó**. Cùng một
hàm có trong `scene3d-orbit-gate.mjs`.

<!-- hết khối 35 -->

<!-- khối 36/96 · dòng 1535–1549 của bản gốc · entry of removed code · sha256 bd34255887f2673aa70e96c0a8d950b74896206f97cba3a71f27f0b17ef8f5a3 -->
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

<!-- hết khối 36 -->

<!-- khối 37/96 · dòng 1670–1679 của bản gốc · entry of removed code (heading marked removed) · sha256 b14bc60ba078a6f44415b7cbacf572d5c5be501459aed4551817e59b4f6ab5ec -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `frontend/src/simulations/domains/logic/dag-module.tsx`
Chủ sở hữu target `logic.boolean_dag`: model mạch logic (đầu vào → cổng → đầu
ra theo thứ tự phụ thuộc), `apply` nhận `toggle` theo ID đầu vào THẬT (`N`/`G`/`K`,
không phải `A`), timeline lan truyền giá trị, và renderer SVG kèm bảng chân trị.

Đây là MỘT trong hai chỗ tự nối đúng hợp đồng bàn phím cho affordance SVG trước
khi có helper dùng chung (`tabIndex` + `aria-label` "Đầu vào …, giá trị …, bấm
để đổi" + Enter/Space, vì `<g>` không phải `<button>` thật). Chỗ kia là
`network/ui.tsx::LinkHandle`. Vòng tiêu điểm ở `.dag-input:focus-visible`.

<!-- hết khối 37 -->

<!-- khối 38/96 · dòng 1932–1943 của bản gốc · entry of removed code · sha256 01f5b7a9a4bfac4d1cf9c325fb71f7e50ee91e6549483e98aae9fa8623159372 -->
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

<!-- hết khối 38 -->

<!-- khối 39/96 · dòng 1956–1968 của bản gốc · entry of removed code · sha256 fd9be3e80931d831432dc62bb57275797ece4cedbff05786635beb952ce79875 -->
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

<!-- hết khối 39 -->

<!-- khối 40/96 · dòng 1969–1975 của bản gốc · entry of removed code · sha256 1c25dbfdf894766d80026a6302bf0607a71003ba7aa607413e1dbb2446070b4c -->
### `simulation/scope.py` (M20 W3) · Change impact: offline
MỘT bộ từ vựng `DomainScope` + `Simulatability` + `REQUIRES_SIMULATION`, dùng
chung production ↔ evaluation. Ở tầng `simulation/` vì production là nơi PHÁN,
evaluation chỉ ĐO — `evaluation/curriculum_schema.py` import xuống đây chứ không
dựng bộ thứ hai. Hai trục KHÔNG được gộp: đề có thể thuộc phạm vi mà không đáng
mô phỏng (đạo đức mạng), và ngoài phạm vi mà mô phỏng được (quỹ tích).

<!-- hết khối 40 -->

<!-- khối 41/96 · dòng 1976–1988 của bản gốc · entry of removed code · sha256 e5f92871a44dec6e00b15f47057a4152c32541ac3f0a6c134bc043923322385d -->
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

<!-- hết khối 41 -->

<!-- khối 42/96 · dòng 1989–2001 của bản gốc · entry of removed code (heading marked removed) · sha256 56c866ab671fd02fdff616c3f566de620e96b5ef46711f63ada5048512c254b7 -->
### ⛔ ĐÃ GỠ (FINAL_DEAD_EVALUATION_CLEANUP 2026-09-02) — `evaluation/curriculum_schema.py` (M20 W2) · Change impact: offline
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

<!-- hết khối 42 -->

<!-- khối 43/96 · dòng 2015–2020 của bản gốc · entry of removed code (heading marked removed) · sha256 f6993d2edbdbeab6f6702da275c40abadd5e36a6639ef0304749393d16f1ae95 -->
### ⛔ ĐÃ GỠ (FINAL_DEAD_EVALUATION_CLEANUP 2026-09-02) — `backend/scripts/curriculum_benchmark_report.py` (M20 W2A) · Change impact: offline
Báo cáo phủ theo **ĐƠN VỊ chương trình** (không theo số case), sinh từ dữ liệu +
registry, có head stamp. Đọc đúng tập pool CHỊU luật kết nạp (`NEW_POOLS` +
`thesis`, gồm cả `m16`); `regression` đứng ngoài vì bị đóng băng và không có
trường neo. Artifact: `docs/evaluation/m20/curriculum-benchmark.json`.

<!-- hết khối 43 -->

<!-- khối 44/96 · dòng 2021–2028 của bản gốc · entry of removed code · sha256 6ceabbe96c5eb48902945c7431dfb2df1f93ce311a3af807d9c5a81812cc6693 -->
### `tests/test_curriculum_benchmark.py` (M20 W2) · Change impact: offline
Khoá 5 nhóm: tầng ổn định vs dẫn xuất · biến hình · `DATASET` 30 case đổi VAI
thành `LEGACY_AI_COMPOSITION_REGRESSION` (còn nguyên, hết làm thước đo phủ) ·
tách fixture nội bộ khỏi phạm vi sản phẩm · **trường neo phải đếm được** (gồm
ngưỡng ≥3 case/đơn vị và ≥8 đơn vị). Ba phép tiêm lỗi đã chứng minh nhóm cuối đỏ
được: trả văn xuôi về trường neo · xoá 1 case khỏi đơn vị mỏng · bỏ kiểm tra
sentinel trong `unit_codes()`.

<!-- hết khối 44 -->

<!-- khối 45/96 · dòng 2029–2035 của bản gốc · entry of removed code · sha256 387baccaf1eec9b63bfb08a70cb1c2f163742ae28b0e86ada9419414cf2357d6 -->
### `simulation/patterns.py` · Change impact: offline
Pattern reuse (M7.13B): chữ ký, extraction (safe allowlist), instantiate, matcher
tất định, 4 cổng, `DbPatternStore`.
Exports: `spec_signature`, `pattern_key_of`, `extract_template`, `instantiate`,
`validate_params`, `deterministic_fill`, `covered_roles_of_template`, `run_gates`,
`DbPatternStore`. Tests: `test_patterns.py`, `test_reuse.py`.

<!-- hết khối 45 -->

<!-- khối 46/96 · dòng 2036–2044 của bản gốc · entry of removed code · sha256 97f735bd4f3476001e82ec4815b05992ac9304fbad40a308f8e3c8aff7828333 -->
### `simulation/edit_policy.py` · Change impact: offline
EditPolicy v1 (M7.14D): affordance sửa DẪN XUẤT TỪ SPEC (không tên bài/môn).
Exports: `edit_policy_of`, `check_ops_against_policy`, `policy_contract_text`,
`EditFamily`, các hằng `POLICY_*` / `STRUCTURE_INVALID`.
Consumers: `patch.py` (enforce), `ai/edit.py` (prompt theo cảnh + enforce).
Tests: `test_edit_policy.py`. Mirror TS: `generic/edit-policy.ts`.
Notes: precedence bảo thủ `move > structural > spatial > value_only`;
multi-family CHƯA hỗ trợ.

<!-- hết khối 46 -->

<!-- khối 47/96 · dòng 2045–2050 của bản gốc · entry of removed code · sha256 fc4f14f90bed1466d45d45613c9e6e97f28859ec8a4b96083a13fc985efa9425 -->
### `simulation/patch.py` · Change impact: offline
SimulationPatch v1 (M7.14A): 5 op, áp trên bản sao, full validator + guard tiến
trình + engine smoke. Exports: `validate_and_apply_patch`, `ALLOWED_OPS`,
`MAX_OPS`, `UPDATE_FIELDS`, `PATCH_STATUSES`. Tests: `test_patch.py`.
Mirror TS: `generic/patch.ts`.

<!-- hết khối 47 -->

<!-- khối 48/96 · dòng 2051–2062 của bản gốc · entry of removed code · sha256 400d651d06e63773f1c576e0d4f296d3d2d65798558390baebbbf135f339de93 -->
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

<!-- hết khối 48 -->

<!-- khối 49/96 · dòng 2063–2069 của bản gốc · entry of removed code · sha256 66d2a4e2fff680da08fecfe6a02a6a879d3c206ac227fe60abb1c2e0b37111da -->
### `tests/test_encap_routing.py` · Change impact: offline
M10-AI-ROUTE — khóa định tuyến NL cho `network.protocol_encapsulation` (mock,
offline): CATALOG đăng ký + enum classify dẫn xuất; `catalog_text`/`classify.md`
mang phân biệt ngữ nghĩa encap↔routing + giới hạn v1; validator R0/v1; e2e mock
tiếng Việt → envelope encap; packet_routing nguyên vẹn. Bằng chứng live 5/5 ghi
ở `CURRENT_STATE.md` §nhật-ký-live.

<!-- hết khối 49 -->

<!-- khối 50/96 · dòng 2177–2182 của bản gốc · entry of removed code (heading marked removed) · sha256 825370f693a8e6895e150d516f35d93085b5890d261da0c62134609b6287c537 -->
### ⛔ ĐÃ GỠ (FINAL_DEAD_EVALUATION_CLEANUP 2026-09-02) — `evaluation/harness.py` · Change impact: offline (chạy live thì là live)
Chạy pipeline thật + metrics. Exports: `evaluate_item`, `run_eval`, `select_suite`,
`format_report`, `EvalReport`, `ItemResult`, các hằng `FAIL_*`.
Notes: `gap_gate_recall` là metric **song song** (M7.14T) — không đổi cách tính
metric cũ. `_simulate_with_metrics` **mirror** `stage_simulate` (rủi ro drift).

<!-- hết khối 50 -->

<!-- khối 51/96 · dòng 2183–2195 của bản gốc · entry of removed code (heading marked removed) · sha256 2bc2971b82dc1925134b603f68dac322f194fbf20b5bd4524f9494dab13ebf80 -->
### ⛔ ĐÃ GỠ (FINAL_DEAD_EVALUATION_CLEANUP 2026-09-02) — `evaluation/m16_schema.py` · Change impact: offline
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

<!-- hết khối 51 -->

<!-- khối 52/96 · dòng 2196–2210 của bản gốc · entry of removed code (heading marked removed) · sha256 d47e6099c23561ebbef28e95eab8a743efa85bb8bf546029b42c6973481e92e2 -->
### ⛔ ĐÃ GỠ (FINAL_DEAD_EVALUATION_CLEANUP 2026-09-02) — `evaluation/m16_record.py` · Change impact: offline
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

<!-- hết khối 52 -->

<!-- khối 53/96 · dòng 2211–2229 của bản gốc · entry of removed code (heading marked removed) · sha256 75ddb13766961e6b246b9b1908bdd67f3b26ab02a958461fb8a06d61690e7781 -->
### ⛔ ĐÃ GỠ (FINAL_DEAD_EVALUATION_CLEANUP 2026-09-02) — `evaluation/m16_metrics.py` · Change impact: offline
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

<!-- hết khối 53 -->

<!-- khối 54/96 · dòng 2230–2244 của bản gốc · entry of removed code (heading marked removed) · sha256 3e70ddb2bd9fe2be255db35c51b46d69919f0888c5e2a310bda0b5d69abbb443 -->
### ⛔ ĐÃ GỠ (FINAL_DEAD_EVALUATION_CLEANUP 2026-09-02) — `evaluation/m16_offline_scripts.py` · Change impact: offline
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

<!-- hết khối 54 -->

<!-- khối 55/96 · dòng 2245–2259 của bản gốc · entry of removed code (heading marked removed) · sha256 d74d591178ec951ad33212c17c3373449b98382bd29724e749be25008d2f29f8 -->
### ⛔ ĐÃ GỠ (FINAL_DEAD_EVALUATION_CLEANUP 2026-09-02) — `evaluation/m16_artifacts.py` · Change impact: offline
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

<!-- hết khối 55 -->

<!-- khối 56/96 · dòng 2260–2274 của bản gốc · entry of removed code (heading marked removed) · sha256 e0591e885ca168c96d5a311a2663da2d2fbdcac15d38ef882b4ba2cf7dd28162 -->
### ⛔ ĐÃ GỠ (FINAL_DEAD_EVALUATION_CLEANUP 2026-09-02) — `evaluation/datasets/m16_catalog.py` · Change impact: offline
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

<!-- hết khối 56 -->

<!-- khối 57/96 · dòng 2275–2289 của bản gốc · entry of removed code (heading marked removed) · sha256 22fd8c106f9ba6c25e6b7f608b8fef67fb4a69af930964c165c47a8194add8a0 -->
### ⛔ ĐÃ GỠ (FINAL_DEAD_EVALUATION_CLEANUP 2026-09-02) — `scripts/generate_m16_artifacts.py` → `docs/evaluation/m16/*.json` (M16) · Change impact: offline
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
`generate_dsl_contract.py` — nay CHẾT KHI IMPORT, xem §mục của nó — và
`generate_capability_descriptors.py`, **đã gỡ hẳn** ở
`FRONTEND_LEGACY_FIXTURE_CUTOVER`).

<!-- hết khối 57 -->

<!-- khối 58/96 · dòng 2290–2303 của bản gốc · entry of removed code (heading marked removed) · sha256 2cf3ee6a99895bd12c8fb572819c70e9adad3a853be2dc5ee731b630536d2aea -->
### ⛔ ĐÃ GỠ (FINAL_DEAD_EVALUATION_CLEANUP 2026-09-02) — `scripts/generate_m16_live_artifacts.py` → `docs/evaluation/m16/*-baseline.json` (M16 live) · Change impact: offline (đọc trace, KHÔNG gọi AI)
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

<!-- hết khối 58 -->

<!-- khối 59/96 · dòng 2312–2338 của bản gốc · entry of removed code (heading marked removed) · sha256 5926cd4d40da67bfdd4a409ebdafee675037f83f398f81bbb7b3b878c4113daf -->
### ⛔ ĐÃ GỠ (FINAL_DEAD_EVALUATION_CLEANUP 2026-09-02) — `evaluation/live.py` · Change impact: full live
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

<!-- hết khối 59 -->

<!-- khối 60/96 · dòng 2390–2398 của bản gốc · entry of removed code · sha256 82b9d5187ebb3ce3578911cedcce8992e82e33b3acca6599ff72596bae0c1912 -->
### `simulations/observe-lifecycle-w4b2r.test.ts` · Change impact: offline
Khoá TOÀN DANH MỤC ba luật vòng đời Quan sát — cả ba **đã đúng từ trước**, wave
W4B-2R chỉ đo và khoá: `LEARNER_INITIATES_FIRST_RUN` (`playing` chỉ nhận `true`
qua `setPlaying`; mọi nhánh nạp đặt `false`), `CANONICAL_RUN_CAN_COMPLETE_
WITHOUT_PREDICTION` (chạy trọn timeline MỌI envelope offline bằng `nextStep`,
`prediction` vẫn `null`), `OBSERVE_REQUIRES_NO_ANSWER` (`nextStep` không đọc
`prediction`; `submitPrediction` không đụng cursor). Mở file này trước khi định
thêm bất kỳ cổng nào chặn Play.

<!-- hết khối 60 -->

<!-- khối 61/96 · dòng 2399–2413 của bản gốc · entry of removed code (heading marked removed) · sha256 ff4a9b1dc60f53b665e64e601d22a126fe8a370e9d420a47fd8839f2628ba141 -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/learner-gate.ts` · `learner-gate.test.ts` · Change impact: offline
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

<!-- hết khối 61 -->

<!-- khối 62/96 · dòng 2606–2639 của bản gốc · entry of removed code (heading marked removed) · sha256 bbda8ca8b17afb2e8d7e2d1995f0945260609afa29d1ada1a66697bbb3aabbb3 -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/domains/generic/model.ts` · Change impact: offline
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

<!-- hết khối 62 -->

<!-- khối 63/96 · dòng 2640–2648 của bản gốc · entry of removed code (heading marked removed) · sha256 c2be727fe90ecc6df89dfbfe31d912bf2025343b86fab10291c5ed97d9d5cf7e -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/domains/generic/validate.ts` · Change impact: offline
Validator TS song song `dsl/validator.py`. Export: `validateGenericConfig`.
Notes: tách khỏi `index.ts` (M7.14) để `patch.ts` dùng chung, tránh vòng import.
M13 (Task 5): import trực tiếp `./dsl-contract.json` (KHÔNG hằng viết tay) để
kiểm operand coherence + role-typing — mirror `validator.py` từng dòng (cùng
thông điệp lỗi `"không có nguồn giá trị"`/`"vai trò"` để test hai tầng khớp
nhau). Đổi luật coherence = sửa `manifest.py` + chạy lại generator, KHÔNG sửa
tay ở đây.

<!-- hết khối 63 -->

<!-- khối 64/96 · dòng 2649–2652 của bản gốc · entry of removed code (heading marked removed) · sha256 c349ddaee44322537dc3f5f8d2f93d3bb85f86fa9a4494f616f84e84022a019c -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/domains/generic/patch.ts` · Change impact: offline
Mirror `simulation/patch.py`. Exports: `validateAndApplyPatch`, `PatchOp`,
`PatchResult`, `MAX_OPS`. Tests: `patch.test.ts`.

<!-- hết khối 64 -->

<!-- khối 65/96 · dòng 2653–2657 của bản gốc · entry of removed code (heading marked removed) · sha256 e2a6ef39fa977c33315eb3603ed43395df31f090e747b21acc9e02de688f70f4 -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/domains/generic/edit-policy.ts` · Change impact: offline
Mirror `simulation/edit_policy.py`. Exports: `editPolicyOf`,
`checkOpsAgainstPolicy`, `EditPolicy`, `EditFamily`, `EditUiAction`,
`ADDABLE_TYPE_LABEL`, các hằng reason_code. Tests: `edit-policy.test.ts`.

<!-- hết khối 65 -->

<!-- khối 66/96 · dòng 2658–2662 của bản gốc · entry of removed code (heading marked removed) · sha256 83fd248e088d05a362e6a775db4f7e1f7d0841dd294aa235cfae00d139501209 -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/domains/generic/EditBar.tsx` · Change impact: offline
Thanh công cụ sửa — component RIÊNG để state nhập liệu KHÔNG re-render SVG
(nguyên nhân lag đã đo ở M7.14). Exports: `EditBar`, `EditTool`, `toolHint`.
Tests: `mode-switch.test.tsx`.

<!-- hết khối 66 -->

<!-- khối 67/96 · dòng 2663–2666 của bản gốc · entry of removed code (heading marked removed) · sha256 78a89429de676f8a96329311d5ddcf71551bf97e9c402d3abf4733ab6edbdbfa -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/domains/generic/index.ts` · Change impact: offline
`makeGenericModule()` — validateConfig/init/apply/timeline/getExplainContext.
Notes: `init` dựng `pos` từ layout; `apply` xử lý `toggle` + `move`.

<!-- hết khối 67 -->

<!-- khối 68/96 · dòng 2667–2671 của bản gốc · entry of removed code (heading marked removed) · sha256 1d97fd8592bead7505fe02573f1d2136a4965d8a3b90e9b9f9a2f9a84864e26b -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/domains/generic/ui.tsx` · Change impact: offline
`GenericWorkspace` (SVG + layering + fit view + edit toolbar) và `GenericInspector`.
Notes: **toolbar edit hiện đang vô điều kiện** — M7.14D sẽ dẫn xuất từ EditPolicy.
Trạng thái edit (`editMode`/`editTool`/`editText`) là useState cục bộ.

<!-- hết khối 68 -->

<!-- khối 69/96 · dòng 2672–2676 của bản gốc · entry of removed code · sha256 7d0be78e1ce9bd4c8da96694da89b2458c81a0a078cbb2a45d3e2ae2474eb84d -->
### `simulations/domains/{algorithm,logic,binary,network}/` · Change impact: offline
4 module chuyên biệt, engine riêng, **không** dùng DSL: what-if branch
(`core/algorithms.ts`), truth table, bits⇄decimal, BFS route.
Notes: **không** module nào render edit toolbar (đúng thiết kế).

<!-- hết khối 69 -->

<!-- khối 70/96 · dòng 2677–2707 của bản gốc · entry of removed code (heading marked removed) · sha256 a5ade308a967f031fa2cf3baa816528d489f0c5bbe520c0d3f921588bda4a21d -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/domains/algorithm/decision.ts` · Change impact: offline
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

<!-- hết khối 70 -->

<!-- khối 71/96 · dòng 2708–2721 của bản gốc · entry of removed code (heading marked removed) · sha256 937d499afaeabcae668333f32aea8dccb8383c9f323c38f9ab31f5605b19319c -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/domains/algorithm/condition-param.ts`
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

<!-- hết khối 71 -->

<!-- khối 72/96 · dòng 2722–2789 của bản gốc · entry of removed code (heading marked removed) · sha256 82f6ee15eb50ab1d7de49a01ba98e1487d4668e9bdc5f21f5ed99a40f84947d2 -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/domains/algorithm/interaction-policy.ts` · Change impact: offline
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

<!-- hết khối 72 -->

<!-- khối 73/96 · dòng 2790–2806 của bản gốc · entry of removed code (heading marked removed) · sha256 9b0dfb041158775fc694134d14eb54b0ec073f82350972ccc3022a9eb8b9514f -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/domains/network/node-glyph.ts` · Change impact: offline
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

<!-- hết khối 73 -->

<!-- khối 74/96 · dòng 2807–2823 của bản gốc · entry of removed code · sha256 a1330cc1711203f12ab62b4df194d48baa689bcbbd2aadbf82ff3ff15e0707fb -->
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

<!-- hết khối 74 -->

<!-- khối 75/96 · dòng 2824–2839 của bản gốc · entry of removed code (heading marked removed) · sha256 f95243c61603bd5bad2359ecad50a4b6774a899f7806057a5b83b2d75ee1eee2 -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/domains/network/encap-{model,ui,ui3d}.ts(x)` + `encap.ts` · offline
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

<!-- hết khối 75 -->

<!-- khối 76/96 · dòng 2864–2874 của bản gốc · entry of removed code (heading marked removed) · sha256 25a329cce6bfae1317d6533516585cb895d433c3d4ab0ee1ec41313c851b9ae8 -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/domains/algorithm/program-module.tsx` (M17 W2C) · offline
Adapter MỎNG quanh `core/program.ts` (cùng khuôn `scan-module.tsx`). Exports:
`makeProgramModule()`, `ProgramWorkspace`, `ProgramInspector`, `ProgramSimState`
({spec, trace, cursor, completion}). Đăng ký ở `registerAlgorithmDomain()`.
Dùng lại `PseudocodeView` + `VarsView` — KHÔNG tạo UI primitive mới. **2D-only**:
Z không mã hoá biến nào của chương trình nên 3D sẽ là chiều sâu giả (bất biến #18).
Renderer đọc `evaluate_condition`/`enter_branch`/`loop_iteration`/`output` từ
sự kiện bước — **không tự đánh giá lại** biểu thức (test khoá bằng bước "bịa").
Output hiện DẦN theo cursor; kết quả cuối chỉ hiện ở bước cuối.
Tests: `program-module.test.tsx`.

<!-- hết khối 76 -->

<!-- khối 77/96 · dòng 2894–2902 của bản gốc · entry of removed code (heading marked removed) · sha256 c395364cb7eab30ceac2c29b24f256e1681d9f336c71732f8af079bc957570bf -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `components/ScanActionZone.tsx` · `SearchActionZone.tsx` · `SortActionZone.tsx` · offline
Ba VÙNG HÀNH ĐỘNG trên sân khấu — nơi học sinh CAM KẾT (W1/W2/W3B). Nhận `model`
từ `*InteractionOf`, phát `onAct(actionId)` lên `store.submitPrediction`, hiển
thị `feedback` từ `store.prediction`. **Không component nào tự chấm** — không
`correctActionId`, không so `=== "yes"`; có test quét mã nguồn khoá điều đó.
Nhận diện bằng `aria-label` ("Thao tác với biến tích luỹ" / "…với bước tìm kiếm"
/ "Thao tác sắp xếp") — hợp đồng với người dùng, ổn định hơn class CSS. Nút đã
chọn GIỮ vết ("✓ em đã chọn") sau khi chấm: nửa sau của vòng học phụ thuộc nó.

<!-- hết khối 77 -->

<!-- khối 78/96 · dòng 2903–2911 của bản gốc · entry of removed code (heading marked removed) · sha256 d4de0bff44b30e1bd51b129dcc90360d4cdd2c357963efa44bd72816a0222417 -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/domains/algorithm/ui.tsx` — trạng thái TRÌNH BÀY · offline
`labOpen` = `useState(false)` **cục bộ trong `AlgorithmWorkspace`**, KHÔNG ở
store, không persist. Nó gác: kéo-thả (qua `dragAllowedByPolicy`) + vùng cam kết
(qua `commitmentSurfaceVisible`). ⚠️ SSR luôn thấy `labOpen = false`
(ARCHITECTURE_MAP §8 #13) ⇒ **trạng thái "Thí nghiệm đang mở" KHÔNG test được
bằng `renderToString`** — phủ bằng hàm thuần + runner trình duyệt. Dải nhân quả
(`decision-strip`) dựng theo VÙNG ĐANG HIỆN chứ không theo "bước có phải điểm
quyết định": QUAN HỆ thuộc Quan sát, chỉ NÚT CAM KẾT thuộc Thí nghiệm.

<!-- hết khối 78 -->

<!-- khối 79/96 · dòng 2937–2970 của bản gốc · entry of removed code (heading marked removed) · sha256 7ab8690a01d169eb7b1cc323e6865d1b03c9d791dcf3f69931d982d7659c292b -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/domains/web/` — MÔ HÌNH CSS CÓ RÀNG BUỘC (W4B-2Z)
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

<!-- hết khối 79 -->

<!-- khối 80/96 · dòng 2983–2988 của bản gốc · entry of removed code (heading marked removed) · sha256 614be7f8716835b83f83ae1657e15a5cf8ccbb05813c36b98ec90fbeced0e0f4 -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `data/samples.ts` · Change impact: offline
Mẫu LEGACY dạng `analysis` (tiền-envelope): `SAMPLES` được `offline-catalog.ts`
map qua `fromLegacyAnalysis`/`toSimulationId` thành `CatalogEntry`. Đây là nguồn
của tám bài thuật toán chuyên biệt trong danh mục. Mẫu MỚI không thêm vào đây —
thêm envelope thẳng vào `sim-samples.ts` (`OFFLINE_SAMPLES`).

<!-- hết khối 80 -->

<!-- khối 81/96 · dòng 2989–2999 của bản gốc · entry of removed code (heading marked removed) · sha256 86482db3894e5fc07efce76a7062cca4235e98345798454169e7b279d14f5cb7 -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `data/sim-samples.ts` — bổ sung W4B-3D
Thêm mẫu cho **9 target chưa từng đo được trong trình duyệt**; nay 23/23 có mẫu.
Config lấy NGUYÊN VĂN từ fixture đã validate ở `authenticity-cross-lock.test.ts`
(và `program-normalized-envelope.json` cho `bounded_control_flow` — dạng chuẩn
hoá `program-2.0` KHÔNG chép tay được, bản viết tay đầu tiên bị validator từ
chối). `visibility` tách BẰNG CHỨNG khỏi QUẢNG BÁ: `algorithm.scan` là
`internal_fixture` — có mẫu để đo, không vào Thư viện vì trùng nghĩa với tám bài
chuyên biệt. Tests: `data/sample-coverage-w4b3d.test.ts` (mọi target
`ai_reachable_public` phải có mẫu · mọi mẫu phải `validateConfig`+`init` được ·
D≠E · `GROUP_ORDER` phủ mọi `Domain`).

<!-- hết khối 81 -->

<!-- khối 82/96 · dòng 3000–3024 của bản gốc · entry of removed code (heading marked removed) · sha256 b1176e3a03ea4378dd840bde7558f238e11c919a5a1544e2d5ca214c7de88643 -->
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

<!-- hết khối 82 -->

<!-- khối 83/96 · dòng 3060–3074 của bản gốc · entry of removed code (heading marked removed) · sha256 c4cf8461a52ba7c54e2ac12d5839b850b697db95fa6a4cfef6715207bceee74f -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `components/SearchStateView.tsx` — dữ kiện bước tìm kiếm · offline
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

<!-- hết khối 83 -->

<!-- khối 84/96 · dòng 3075–3084 của bản gốc · entry of removed code · sha256 2d658a3aefbf3de9a871cb5269831459d92a7b4e5572cd5cc345c6b9da837754 -->
### `generic/narration-boundary.characterization.test.tsx` · offline · **ĐẶC TẢ**
⚠️ Mô tả hành vi **HIỆN TẠI**, kể cả hành vi đáng lo — KHÔNG phải hợp đồng mong
muốn. Siết `RevealStep.narration` thì test này ĐỎ; sửa test cho khớp, đừng nới
bản vá cho khớp test. Đo ranh giới LLM ↔ bề mặt học sinh của
`generic.rule_scene`: validator hai tầng chỉ kiểm `typeof string` (không trần độ
dài, không ràng nội dung) nên narration mâu thuẫn/tuyên bố kết quả/tự phán đúng
sai đều ACCEPTED và tới học sinh nguyên văn qua khe thuyết minh của shell; nhưng
KHÔNG đổi được state/kết quả/phán quyết (đã đo). Kết luận + chuỗi sở hữu:
`docs/GENERIC_RULE_SCENE_LLM_BOUNDARY_AUDIT.md`.

<!-- hết khối 84 -->

<!-- khối 85/96 · dòng 3085–3093 của bản gốc · entry of removed code · sha256 fade0b01965746d17cb29586af91f632f7e1a3a236440eb75bcc8e84a105d107 -->
### `simulations/observation-preservation.test.tsx` · Change impact: offline
Khoá `CORE_OBSERVATION_STATE_PRESERVED_UNDER_GATING`. Chứng minh THEO CẤU TRÚC
(không so hai lần render, vì `labOpen` là useState cục bộ nên SSR luôn thấy
`false`): (1) mọi probe cơ chế lõi nằm ngoài phần bị gác; (2) phần bị gác không
chứa probe lõi nào ⇒ mở cổng chỉ THÊM quyền hành động. Probe suy từ
`searchInteractionOf` + `decisionPointOf`, không viết tay. Ngoại lệ có tên
`PRESENTATION_COPY_TRANSITION` (teaser ↔ framing ↔ nhãn nút ↔ phản hồi được phép
đổi). Đã tiêm lỗi: gác lại trạng thái → ĐỎ; lộ cam kết ra Quan sát → ĐỎ.

<!-- hết khối 85 -->

<!-- khối 86/96 · dòng 3094–3102 của bản gốc · entry of removed code · sha256 c74daa75306b918d4a55641ad6e295c61713e0eaeade06da3521366ac1150ca6 -->
### `simulations/spec-reuse.test.tsx` · Change impact: offline
Khoá hợp đồng tái dụng (W4B-2V §30): ba cặp ngữ cảnh khác nhau của cùng cơ chế
(`binary_search` điểm↔số báo danh · `count_if` điểm↔nhiệt độ · `find_max` học
sinh↔lượng mưa) phải cho **cùng chuỗi kiểu sự kiện engine** + **cùng tham chiếu
component renderer**, còn dữ liệu/nhãn phải KHÁC. So SỞ HỮU, không so pixel.
Kèm guard quét `domains/**` cấm renderer rẽ nhánh theo nội dung đề
(`summary.includes(...)`) hay theo `algorithm_id`/`simulation_id` — guard tự
kiểm bằng ba mẫu vi phạm tổng hợp trước khi tin kết quả 0.

<!-- hết khối 86 -->

<!-- khối 87/96 · dòng 3113–3126 của bản gốc · entry of removed code (heading marked removed) · sha256 510c02b8a6ca1cc2a0cd4b79a1c4dbe60a7e7431490a78583e2e28b76268e0cd -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/domains/web/` — W4B-4D: THAO TÁC THẲNG LÊN TRANG
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

<!-- hết khối 87 -->

<!-- khối 88/96 · dòng 3127–3151 của bản gốc · entry of removed code (heading marked removed) · sha256 c1e4a456dbc5fc7f9630ee0392b70ff8fc27371a5f3bdc0c211f700343fd5a41 -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/domains/web/` — W4B-3F: TRANG CÓ CẤU TRÚC
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

<!-- hết khối 88 -->

<!-- khối 89/96 · dòng 3172–3187 của bản gốc · entry of removed code · sha256 3cb1e9bee596af483a456abdf7376aaf595a75b689b67e54e380d67be9927af6 -->
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

<!-- hết khối 89 -->

<!-- khối 90/96 · dòng 3229–3244 của bản gốc · entry of removed code (heading marked removed) · sha256 c02a068dd2eab39319031f623c58261be023a8538a9e25601fc811d6e49b440e -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/renderer-fit.ts` · offline
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

<!-- hết khối 90 -->

<!-- khối 91/96 · dòng 3245–3254 của bản gốc · entry of removed code (heading marked removed) · sha256 786c59a8ee3a70fb89361c58bd02b606e9e1be9a73d6b0b991585c291d81f9ca -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `simulations/domains/tree/layout-size.ts` · offline
**Hình học khung vẽ cây, tách thành module LÁ** (không import registry/React/
store) để `renderer-fit.ts` đọc được TRẦN bề rộng mà **không kéo renderer nạp-lười
vào bundle shell** — `SimulationWorkspace` import thẳng `renderer-fit`, nên import
`tree-module` ở đó là phá code-splitting của `<Suspense>`. Export `TREE_SLOT_W`
(86 — một làn nút, đủ nhãn ~12 ký tự), `TREE_LEVEL_H` (78), `treeLayoutSize(config)`
→ `{w, h}`. Giá trị `w` **chính là trần ngữ nghĩa**: renderer vẽ `maxWidth: w` nên
cây giãn tới đây rồi dừng. Một nguồn cho cả renderer lẫn cổng chấm — không có con
số chép tay ở nơi thứ hai để trôi.

<!-- hết khối 91 -->

<!-- khối 92/96 · dòng 3954–3961 của bản gốc · entry of removed code (heading marked removed) · sha256 81ddfb42c434ba3b8fce2bf8a33b8c634b6d0617e04b66f76052e5de61cc004c -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `frontend/src/simulations/domains/generic/layout-compiler.ts` (G1–G7) · offline

Sở hữu **phân vùng không gian theo VAI TRÒ NGỮ NGHĨA** trong hệ toạ độ miền 0–100:
Input Zone (`array_strip`, `bar_chart`, `table_grid`) · State Zone (`value_box`,
`pointer`, `switch`, `slider`) · Structure Zone (`stack_view`, `queue_view`,
`tree_element`) · Output Zone. Đây là **nguồn duy nhất** quyết định object nằm đâu
trên sân khấu generic — renderer **không** được tự đặt toạ độ cho từng bài.

<!-- hết khối 92 -->

<!-- khối 93/96 · dòng 3962–3968 của bản gốc · entry of removed code (heading marked removed) · sha256 349d3daffa28af47166f59051fc2bd98aa317029a71415b3b67974b9c0585cdd -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `frontend/src/simulations/domains/generic/anchor-resolver.ts` (Semantic Anchor System, G5) · offline

Sở hữu việc **phân giải vị trí (X, Y) của pointer/annotation neo vào một thành phần
ngữ nghĩa** theo *kiểu đối tượng + `target_index`*. Tồn tại để xoá hardcode toạ độ
theo từng bài. ⚠️ Liên quan trực tiếp **bất biến #34**: neo không phân giải được thì
đường sinh ngữ nghĩa phải fail-closed, **không** vẽ một phần.

<!-- hết khối 93 -->

<!-- khối 94/96 · dòng 3969–3976 của bản gốc · entry of removed code (heading marked removed) · sha256 d554f497adc206dcacba9afc6fa8f1b8aa07bf2e825740cc8c23137872e9a5d4 -->
### ⛔ ĐÃ GỠ (FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02) — `frontend/src/simulations/domains/generic/disallowed-collision.ts` · offline

Sở hữu **định nghĩa va chạm bị CẤM** giữa các đối tượng đã bố cục: `TEXT_ON_TEXT`
(nhãn đè nhãn) · `BOX_ON_BOX` · `CANVAS_OVERFLOW` (tràn ngoài 0–100). Đọc kết quả
của `layout-compiler.ts`. Đây là bản kiểm **tất định** cho đúng lớp lỗi mà L5a
(visual regression) bắt trên trình duyệt — hai tầng khác nhau, đừng bỏ tầng này vì
đã có tầng kia.

<!-- hết khối 94 -->

<!-- khối 95/96 · dòng 6236–6255 của bản gốc · entry of removed code · sha256 fc7035db6ee46056c5aa2caf0f811235d6f7db349be08c699a33351a67d0162c -->
### ~~`.../geometry/Scene3DSection.tsx`~~ — GỠ 2026-08-30

Vùng "Quá trình dựng hình 3D" **đã hết tồn tại**: xưởng 3D nay là TRANG chứ
không phải một khối dưới thẻ mô phỏng. `hopLeScene3D` chuyển sang
`scene3d-model.ts` (cạnh định nghĩa `Scene3D` — đó là phép kiểm của KIỂU, và để
ở component thì `SimulationWorkspace` phải import cả một component chỉ để mượn
một type guard). Test cũ viết lại thành `scene3d-page.test.tsx`.

Lý do đo được: với kiến trúc cũ, học sinh mở một bài thiết diện thì thấy — theo
đúng thứ tự đọc — tiêu đề, nhãn miền, renderer 2D của route ngữ nghĩa, khay điều
khiển, panel Giải thích, **rồi mới tới cái hình**. Thứ cả bài nói về nằm dưới
nếp gấp. `SimulationWorkspace` nay rẽ nhánh sớm khi `hopLeScene3D(canh3d)` —
theo cảnh ĐÃ DỰNG, không theo `visual_mode` được KHAI (khai được thì khai sai
được; cảnh đã dựng thì hoặc có hoặc không).

`scene3d-page.test.tsx` khoá bốn thứ: biên nhận fail-closed (9 hình dạng lạ) ·
đường 2D nguyên vẹn · rẽ nhánh theo cảnh đã dựng · canvas đứng trước mọi bảng
chữ. ⚠️ Guard **bóc chú thích trước khi quét** mã shell — bản đầu ĐỎ vì chính
chú thích giải thích *"vì sao không dùng `visual_mode === '3d'`"* khớp mẫu cấm.

<!-- hết khối 95 -->

<!-- khối 96/96 · dòng 7386–7391 của bản gốc · entry of removed code · sha256 c76fb2e25593dd916caa0390b399e0447f4997a94699bfdd7b95fda5d81be6bd -->
### `backend/app/simulation/execution_authority_gate.py` (HISTORICAL_REMOVED) · offline

Thay khái niệm của `computation_gate.py` (file cũ GIỮ NGUYÊN cho đường module).
Luật: kết quả phải có **authority tất định** sở hữu. `SemanticProgramInterpreter`
là một authority; LLM thì **không bao giờ**.

<!-- hết khối 96 -->
