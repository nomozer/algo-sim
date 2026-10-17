# CURRENT_STATE.md — Trạng thái hiện tại

## INTEGRATED ON `main` — Independent NLU extraction evaluation, 2026-10-17

CANONICAL_NEXT_ACTION = POST_NLU_BASELINE_RESEARCH_PRIORITY_DECISION

**Integration (owner GO in session, 2026-10-17):** `main` fast-forwarded `76dca142` → `b22c2269`, pushed without force;
research branch deleted with `-d`; record
[`integration.md`](evaluation/geometry/runs/independent-nlu-extraction-evaluation/integration.md). Hybrid NO-GO.

Branch `research/independent-nlu-extraction-evaluation` from `main` `76dca142`; no product change (candidate `57c7f5db…`
MATCH). Preregistered offline: 60-case Vietnamese corpus by a blind AI author (dev 16 / locked 44), independent Fraction
oracle (56 values; 44 re-checked by a second agent), implementer gold Typed Facts, single-arm harness reusing the A/B
pilot helpers, two read-only audits (extraction architecture; evaluation, NOT_READY → all blockers fixed). Gold arm
(0 calls): 8/44 locked served, 23 capability/grounding gaps, 13 safe refusals. **Live pilot (owner GO pilot only):
32 requests, est. USD 0.137, 0 unsafe, 0 served; intent 32/37, goal+entity 16/34 expressible** — operands of requests
omitted and measures without their solid dominate ([`analysis`](evaluation/geometry/runs/independent-nlu-extraction-evaluation/results/live-pilot/analysis.md)).
**Locked (owner GO, 44 requests, est. USD 0.162):** preregistered answer UNSAFE (frozen scorer, L01); L01 is a verified
scorer artifact — corrected P1 PASS, **P2 NO** (24/45 → 27/45 goal+entity; CI95 upper < 0.85 both); 2/44 served correct
(gold facts 8); 30/44 rows stop at planner input from extraction errors. Baseline report:
[`report.md`](evaluation/geometry/runs/independent-nlu-extraction-evaluation/report.md).
cache125/LLM_ONLY/Hybrid NO-GO.

## INTEGRATED ON `main` — Scene3D educational visual quality finalization, 2026-10-17

**Integration (user `HUMAN_VISUAL_REVIEW_PASS` + GO INTEGRATION in session, 2026-10-17):** product commit `22df95d6`
(from `76dca142`), merged with `main` `bc0445ae` at `d4947610`, candidate `product_commit_sha` refrozen at `7dc609bd`
(`tree_hash` `57c7f5db…`, 110 files unchanged), clean detached T3 at `8aabb4b9` `FULL_PRODUCT_GATE_PASS` (pytest 10,263 passed,
vitest 68 files / 1,077 passed, build, demo, crash surface 6/6), fast-forwarded onto `main`
and pushed without force; research branch and worktree cleaned; record
[`integration.md`](evaluation/geometry/runs/scene3d-educational-finalization/integration.md).

Resolves EDU-1..8 across shared frontend Scene3D modules (`scene3d-annotations.ts`, `scene3d-camera.ts`,
`scene3d-edge-visibility.ts`, `scene3d-model.ts`, `scene3d-presentation.ts`, `scene3d-roles.ts`, `scene3d-view.tsx`,
`global.css`): distance-to-line measurement pills when witness lives on `point3.perpendicular_witness`; textbook camera
affinity + witness-foot framing; auxiliary plane colinear border yield to active section/segment borders (`aux=1`);
scene-diameter-scaled closed 4-sided right-angle square, screen-space foot marker dot, and vertex/annotation collision
avoidance; clean near-white canvas + cool slate-blue solid faces; WebGL `BufferGeometry` span pools (`capPhat = 0`) and
Z-up `OrbitControls` view-matrix settle (`scene3d-orbit-gate.mjs` `DAT` on `p1`, `p6`, `p7`); normal-state `FINAL_RESULT`
point-to-plane perpendicular witness; and open-step section intersection vertex highlighting. Independent review v2 PASS
(7/7, [`review.md`](evaluation/geometry/runs/scene3d-educational-finalization/review.md)); 68 Vitest files (1,077 tests),
49 full-size (`1280×900`) browser states, **`HUMAN_VISUAL_REVIEW_PASS`**. `DEFAULT_MODE = LLM_ONLY`, cache 125, Hybrid
NO-GO, 0 live calls. Run [`scene3d-educational-finalization`](evaluation/geometry/runs/scene3d-educational-finalization/report.md).

## INTEGRATED ON `main` — Hybrid semantic grounding reliability, 2026-10-17

Next action at that time (superseded by the NLU evaluation above): POST_SEMANTIC_GROUNDING_INTEGRATION_RESEARCH_PRIORITY_DECISION

**Integration (user GO in session, 2026-10-17):** `main` fast-forwarded `1f635ed5` → `bd20ac46`, pushed without force;
research branch deleted with `-d`, verification worktree deregistered (leftover folder kept); record
[`integration.md`](evaluation/geometry/runs/hybrid-semantic-grounding-reliability/integration.md). Hybrid NO-GO.

Resumed Claude's interrupted work on `research/hybrid-semantic-grounding-reliability`; preserved 8 working files outside
the repository before edits. Final product `94b3437b`; clean refreeze candidate `57c7f5db…` (110 files), MATCH. Offline
99-case replay: 13→0 wrong serves, 21→16 false refusals; historical 174 rows preserve answers/plan statistics, with two
declared refusal-code changes. Independent review delta has no remaining critical/important finding. Clean detached T3
`bd2dc080` FULL_PRODUCT_GATE_PASS (backend 10240/0, geometry 7949/0, vitest 1072); integration requires user GO. cache125/LLM_ONLY/Hybrid NO-GO, 0 live calls;
no human-held-out or live Vietnamese-understanding claim. Single handoff:
[`report.md`](evaluation/geometry/runs/hybrid-semantic-grounding-reliability/report.md).

## INTEGRATED ON `main` — Scene3D visual correctness (Gemini review + CONTRACT-BE-1), 2026-10-17

Next action at that time (superseded by the grounding continuation above): POST_SCENE3D_INTEGRATION_RESEARCH_PRIORITY_DECISION

**Integration (user GO in session, 2026-10-17):** `main` fast-forwarded `6d8ead99` → `ee9689e6`, pushed without force;
integration and Gemini branches deleted locally, Gemini worktree removed; record
[`integration.md`](evaluation/geometry/runs/scene3d-visual-correctness/integration.md). Hybrid NO-GO; human visual
review pending.

Branch `integration/scene3d-visual-correctness` from `main` `6d8ead99`: merge `a7388a40` of the Gemini Scene3D commit
`0ef0a20a` (plane hull, unified occlusion of non-canonical segments, line extent, highlight, right-angle marker), reviewed
independently; FE-4 fix `08021881` (displayed line span no longer pulled toward the backend anchor); CONTRACT-BE-1 fix
`f07ea069` (route D wrote no `targets`: the asked distance was `intermediate` and the target plane hid at `aux=0`; the
engine now reports the asked measure and its named operands). BE-2/3/4: no contract change (frontend owns display
geometry). Integration scenes regenerated from this backend; Scene3D harness D3D11 + SwiftShader
`PASS_CORE_CAUSAL_RENDERING` (11 scenes, 0 errors); independent review found a second line-span bug (witness foot
outside the edge), fixed `e460cfac`. Candidate `43e877ed…` (refreeze `8f437980`); clean detached T3 at `0a33fcc8` `FULL_PRODUCT_GATE_PASS` (pytest 10170/0, vitest 1072). `LLM_ONLY`, cache 125, Hybrid NO-GO, 0 Gemini;
`HUMAN_VISUAL_REVIEW_PENDING`. Run [`scene3d-visual-correctness`](evaluation/geometry/runs/scene3d-visual-correctness/report.md).

## INTEGRATED ON `main` — Generalized Goal Entry and its stack, 2026-10-16

Next action at that time (superseded 2026-10-17 by the Scene3D integration decision above): `POST_STACK_INTEGRATION_RESEARCH_PRIORITY_DECISION`

**Integration (user GO in session, 2026-10-16):** `main` fast-forwarded `2a3c0787` → `bd4d3f59` (58 commits: result binding,
Scene3D W1–W3, Function Discovery, Generalized Goal Entry), then pushed without force; record:
[`integration.md`](evaluation/geometry/runs/generalized-goal-entry/integration.md). Hybrid product enablement stays NO-GO;
human visual acceptance NOT_APPROVED.

Branch `research/generalized-goal-entry` from verified Function Discovery `96569792`, stacked on Result Binding / Scene3D
W1–W3 / Function Discovery, none integrated; `main` = `origin/main` = `2a3c0787`. Work of an interrupted Codex session,
committed and verified on handoff by Claude. Product commits `193e634a` (route D: length goals through Registry goal
contracts) + `289007a4` (Scene3D: hidden source/foot hides the projection witness). Candidate `eaddb56c…` (refreeze `297e6cce`); clean detached T3 at `5964f875` `FULL_PRODUCT_GATE_PASS` (pytest 10166/0, vitest 1062).
Re-measured on the committed product: new length corpus 8/8 exact, 10/11 negatives with the registered code (1 registration
error, label kept), 0 wrong served; experimental centroid contract 2/2 without code change; 153 earlier rows identical to
Function Discovery (status/code/answers and plan stats); Codex measurements reproduced 174/174.
`LLM_ONLY`, cache 125, Hybrid NO-GO, 0 Gemini; TypedFact schema and provider surfaces unchanged; human visual acceptance
NOT_APPROVED. Run [`generalized-goal-entry`](evaluation/geometry/runs/generalized-goal-entry/report.md).

## LOCAL — Goal-directed function discovery (unnamed derived operands), 2026-10-16

Next action at that time (closed by the 2026-10-16 stacked integration): `STACKED_RESEARCH_BRANCH_INTEGRATION_DECISION`

Research branch `research/goal-directed-function-discovery`, stacked on `8c24cb52` = `main` `2a3c0787` + result binding
(`f83b4ed1`, not integrated) + Scene3D W1–W3 (not independently reviewed); not merged, not pushed. Four identities:
product commit `cfa27baa` (first product `9fec9f43` + independent-review fixes; route D only:
`geometry_functions/{planner,registry,engine}.py`, `ai/function_route.py`); candidate
`093359c2551f11482c2a8ab06a74efba221c435561183308b39fe10e5fedd415` (110 files) frozen at `313cc537`, refreeze commit
`81315986`; independent review PASS_WITH_FINDINGS (0 wrong served; findings closed or recorded); authoritative clean detached T3 at `e6c5b0f1` `FULL_PRODUCT_GATE_PASS` (pytest 10115/0,
vitest 1061/1061, build, demo, crash surface 6/6).
Also fixes an inherited Scene3D test typing error that broke `tsc -b` (`19eec205`). `LLM_ONLY`, `CACHE_VERSION = 125` (no bump: route D is not
on `/api/analyze`), Hybrid product enablement NO-GO, 0 Gemini calls, provider surfaces A `7ea511a6…` / B `485d3834…` unchanged.
- **Capability:** distance from a point the source DESCRIBES but does not name ("trung điểm của SC") to a named plane, a
  named line or a source intersection line; Planner composes it from Registry contracts (`midpoint`,
  `ask_distance_point_plane`, `orthogonal_projection_line`, `ask_length`, `intersection_line`) — closes the composition gap
  behind benchmark B27 without a TypedFact schema change.
- **Measured (offline, development corpus, NOT_HELD_OUT):** 9/9 positives exact vs an independent Fraction/Gram oracle,
  15/16 negatives with the registered code (D-1: wrong code, `ISSUE-ARCH-LINE-REF-PREMISE-GRAMMAR-CUBE`), 0 wrong served;
  FIXED and BOUNDED planners 0/9; NEW identical to BOUNDED on benchmark 30, result binding 18, two-line 45 + 32; a contract
  added as data (centroid) served 3/3 new forms with no planner/gate/engine change; a lying contract is refused by the
  engine. Scene3D harness SwiftShader + Intel D3D11 `PASS_CORE_CAUSAL_RENDERING` (6 fixtures, 0 errors).
Receipt: [`goal-directed-function-discovery`](evaluation/geometry/runs/goal-directed-function-discovery/report.md).

## LOCAL — Scene3D architecture & visual reliability implementation (W1–W3), 2026-10-16

Next action at that time (still pending, now part of the stacked decision above): `SCENE3D_ARCHITECTURE_INDEPENDENT_REVIEW`

Research branch `research/scene3d-visual-parity-audit` (branched from `f83b4ed1`, W0 audit at `4b51fde8`); not merged, not pushed; `main`/`origin/main` remain `2a3c0787`. Resolves all 2 CRITICAL, 5 IMPORTANT, and 2 NONBLOCKING findings from W0 (`scene3d-visual-parity-audit`) for `ISSUE-ARCH-SCENE3D-CONSTRUCTION-READABILITY` with 0 backend/Kernel/Planner changes (`LLM_ONLY`, `CACHE_VERSION = 125`, Hybrid OFF, 0 Gemini calls):
- **W1 (Mapping, Auxiliary Carrier Persistence & Parity):** `veKhongGian` (`scene3d-chart.ts`) transforms `o.perpendicular_witness` idempotently (`0.0` world-space displacement across 11/11 fixtures); `auxiliaryObjects` (`scene3d-auxiliary.ts`) excludes `perpendicular_witness.on` target carrier lines (`gt_g`, `derived_H_line`) from disposable hiding under default `aux=0` while `mp1_gt_g`, `mp2_gt_g` hide; `hybrid-section-visual.tsx` enables `withSubEntities` by default and adds `Bước học` + `Hình phụ` controls; unselected `face` sub-entities render as transparent `hit_proxy` meshes.
- **W2 (Off-Solid Auxiliary Points & Plane Framing):** `auxiliaryObjects` classifies off-solid translated auxiliary points (`H`, `H1` in `two-line-*`, ignoring synthetic sub-entities `!x.parent`) as `loai: "dung"` so they hide at the final step under `aux=0`; `surface` plane patches bound to defining points at `0.10` passive opacity and `khungMatPhang` drops the `PLANE_PATCH_MIN_SIZE` floor when `banKinh > 0`.
- **W3 (Progressive Section Sub-Entities & Coincident Labels):** section sub-entities (`td::face:0`, `td::edge:i`, `td::vertex:i`) gate on parent `geometry_progress` and skip coincident named vertices; `kyHieuDiem` (`scene3d-presentation.ts`) combines coincident labels into `"B ≡ H"`; selection details fall back across `label || notation || id`.
- **Verification:** RED 6 failing assertions (`red/vitest-red.txt`) → GREEN `68 files / 1061 passed` (`results/vitest-green.txt`), backend geometry `7758 passed` (`results/pytest-green.txt`), `result-binding-visual-check.mjs` `PASS_CORE_CAUSAL_RENDERING` (`results/result-binding-check/receipt.json`), and 11/11 browser parity & oracle pass (`results/parity_telemetry.json`, `results/math_and_readability_oracle.json`, `results/before_after_comparison.json`). Candidate not yet refrozen and authoritative T3 not yet run pending independent code review.
Receipts: [`scene3d-architecture-visual-reliability`](evaluation/geometry/runs/scene3d-architecture-visual-reliability/report.md) · [`scene3d-visual-parity-audit`](evaluation/geometry/runs/scene3d-visual-parity-audit/report.md).

## LOCAL — Result binding final acceptance, 2026-10-16

Next action at that time (superseded 2026-10-16 by the stacked decision above): `RESULT_BINDING_MAIN_INTEGRATION_DECISION`

Research branch `research/source-bound-result-planning`; not merged, not pushed; `main`/`origin/main` remain `2a3c0787`.
Four identities, not interchangeable:

- **product commit** `55c657b8`: result binding (`efb756aa`) plus the false-serve fix and the shared ask-grammar
  closure, all on research route D (`geometry_functions/`, `ai/function_route.py`, `ai/fact_extraction.py`);
- **candidate** `30808cb002b377e4ad68f224363ef58ab6e51e0facba7e2d4c501419f58d91dc` (110 files), `--verify` MATCH;
- **refreeze checkpoint / T3 commit** `7f355a81`: authoritative T3 `FULL_PRODUCT_GATE_PASS` in a clean detached worktree;
- **evidence publication commit** `4298d626`. Later commits on the branch (including the one that adds this section)
  are documentation only and are not product commits.

Evidence review E-1 (`shared-ask-grammar-safety/evidence-reconciliation-55c657b8/`, addenda 1–3) and the independent
re-run of T3 both reported PASS. Those two reviews, and the code review of `55c657b8`, are conversation reports, not
repository artifacts. Integration preflight: CONDITIONAL on this documentation sync, then the user's merge decision
(fast-forward). `LLM_ONLY`, `CACHE_VERSION = 125`, Hybrid product enablement NO-GO, 0 Gemini calls.
Scene3D product–harness visual parity / readability audit: audited in W0 and implemented in W1–W3 on `research/scene3d-visual-parity-audit` (above). Known limitations: `ISSUE-ARCH-HYBRID-GATE-RESIDUAL-FALSE-SERVES`.
Receipt: [`result-binding-final-acceptance`](evaluation/geometry/runs/result-binding-final-acceptance/report.md).
The two 2026-10-15 sections below are historical for product, candidate and T3.

## LOCAL — Result binding main-integration readiness, 2026-10-15 (historical; superseded 2026-10-16)

Next action at that time (superseded 2026-10-16 by the stacked decision above): `RESULT_BINDING_MAIN_INTEGRATION_DECISION`

`research/source-bound-result-planning` is a fast-forward of `main`/`origin/main` `2a3c0787` (0 divergent commits); not
merged, not pushed. Product `efb756aa` unchanged; candidate `c0a8792f…` (110 files) verify MATCH; T3 `7b14fe04` reused
(measured tree identical). Provider surfaces A/B/declarations recomputed at `19140e2f` and `efb756aa`: all three
INTENTIONALLY_CHANGED, backward compatible; draft-provenance and review-scope corrections in the run's `corrections.json`.
`LLM_ONLY`, `CACHE_VERSION = 125`, Hybrid product enablement NO-GO, 0 Gemini calls. Receipt:
[`source-bound-result-planning-integration-readiness`](evaluation/geometry/runs/source-bound-result-planning-integration-readiness/report.md).

## LOCAL — Source-bound result binding & bounded effect planning, 2026-10-15 (historical; superseded 2026-10-16)

Next action at that time (superseded 2026-10-16 by the stacked decision above): `RESULT_BINDING_MAIN_INTEGRATION_DECISION`

Research branch `research/source-bound-result-planning` from `19140e2f` (`main`/`origin/main` remain `2a3c0787`; no merge/push). Product `efb756aa`, candidate `c0a8792f1c491ae40b41c6af5bbb00ed372e1bbc3b6b39c1093e14572b02b79e` (110 files), `CACHE_VERSION = 125`, `DEFAULT_MODE = LLM_ONLY`, Hybrid off, `LIVE_GEMINI_REQUESTS = 0`. Implements preregistered `line_ref` transport, `PlanningContract` effects on `intersection_line` / `orthogonal_projection_line` / `ask_length`, bounded `_EffectResolver` (`MAX_EFFECT_DEPTH = 3`, `MAX_EFFECT_NEEDS = 32`, `MAX_EFFECT_CANDIDATES = 8`, `MAX_RESULT_LINES = 4`, `MAX_RESULT_FEET = 8`), `_kiem_result_binding` enclosing-sentence source certificate verification, and Engine/IR line result binding (`_Dung.lines`, `_emit_intersection`). Locked development corpus (`NOT_HELD_OUT`): RED `de5ea1a7` 18/18 `SCHEMA_INVALID` → GREEN 6/6 positive `SERVED` ($10/11, 5, 3, 10, 0, 10/11$), 12/12 negative `REFUSED` (`test_result_binding_planning.py` 72 passed; 18/18 `EXACT_MATCH` in `reconciliation.json`). Independent 11-dimension review (`review.md`) PASS (`efb756aa`). Historical two-line (45 dev / 32 heldout) and benchmark 30 (19/9/0/2) invariant; Playwright Scene3D harness SwiftShader + Intel UHD D3D11 `PASS_CORE_CAUSAL_RENDERING` (4 scenes, 0 errors); authoritative clean detached T3 `FULL_PRODUCT_GATE_PASS` at `7b14fe04` (`verification/t3-pass.json`, `verification/t3-authoritative.log` `29b09bf5…`: backend `9405 passed`, frontend `1055 passed`, build PASS, demo `5/5`, crash surface `6/6`). Receipt: [`source-bound-result-planning`](evaluation/geometry/runs/source-bound-result-planning/report.md).

## LOCAL — Planner generalization audit/design, 2026-10-14

Next action at that time (superseded 2026-10-16 by the stacked decision above): `RESULT_BINDING_MAIN_INTEGRATION_DECISION`

Research branch `research/goal-directed-planner-generalization-audit` from synchronized main/origin/remote2a3c0787.
Product/candidate/cache125/LLM_ONLY unchanged; Hybrid off/Gemini0, no merge/push. Current Planner uses fixed goal
expansions, not generic search. Diagnostic14 registered before run:6correct serves/4safe negatives/1grounding false refusal;
3 proposed-schema refusals with working lower IR chains. One result-binding/effect-resolution slice designed/preregistered,
not implemented. NEXT_PLANNER_SLICE_DESIGN_READY; user implementation decision next, before presentation work.
Receipt: [`planner generalization audit`](evaluation/geometry/runs/goal-directed-planner-generalization-audit/report.md).
Scene3D backlog/Hybrid blockers stay OPEN. The following integration snapshot remains the product baseline.

## LOCAL — Group A research integrated on main, 2026-10-14

Next action at that time (superseded 2026-10-16 by the stacked decision above): `RESULT_BINDING_MAIN_INTEGRATION_DECISION`

User-authorized fast-forward `5270f3dd` → `5d73f7c2`, first main/origin/ls-remote sync verified. Integration documentation
publication commit follows (SELF); research branch retained. Product `a5a0797c`, freeze `f227dd72`, candidate
`266983387152cfe91ddeb841ef85d4ee0da221bbbc94a650131e7575db4e39fa` (110 files), cache125/defaultLLM_ONLY.
Group A verified strict two-line plane/section composition and solid-first learner sequencing now on main, Hybrid OFF.
Clean integration265PASS; valid authoritative T3 f227dd72 inherited9329backend/1055frontend/build/demo/crash PASS.
Independent final review NONBLOCKING. User accepts research integration limits; UX/orbit/source gaps remain OPEN,
Group B deferred, Gemini extraction/Hybrid product E2E NOT_MEASURED, no general Vietnamese claim. No new task starts.
Receipt and publication identity: [`group-a-main-integration`](evaluation/geometry/runs/group-a-main-integration/report.md).
Earlier research/candidate/browser decisions retained in two-line-plane-section, scene3d-construction-audit,
pedagogical-construction-sequencing and group-a-integration-readiness runs; their bytes unchanged.

`COMPACT_DSL = NO-GO_ARCHIVED` (quyết định của người dùng): Typed Facts structured JSON giữ làm định dạng AI → Hybrid;
DSL gọn và JSON gọn không thay thế. Lý do: Hybrid chưa có consumer sản phẩm; văn phạm viết tay đã lệch `TypedFact`
(`plane_relation`) mà 95 test cũ vẫn xanh; tiết kiệm mô hình ≈ $0.00037/request (proxy, chi phí Gemini thật NOT_MEASURED).
Nhánh `research/compact-geometry-dsl` lưu trữ (`ARCHIVED_NO_ACTIVE_WORKTREE`, chỉ local), bundle đã kiểm khôi phục;
worktree `dsl-spike` đã gỡ. Điều kiện mở lại, danh tính và receipt: run
[`compact-dsl-closure`](evaluation/geometry/runs/compact-dsl-closure/report.md). LLM_ONLY/cache125/Gemini0; Hybrid off.

## LOCAL — source-grounding-integration, 2026-10-13 (đã tích hợp)

Main đã fast-forward `7767c7e1` → `27b81c51`, theo yêu cầu người dùng.
Push đến `6e053b41` đã xác minh main/origin/ls-remote trùng nhau; nhánh nguồn đã xoá sau xác nhận remote.
Commit hồ sơ đóng phiên đi sau (vai trò SELF), không đổi product/candidate.
Review cuối phát hiện lỗ hở cũ chưa khai: quote chồng nhân đôi quyền xác nhận số của một call.
Sửa tối thiểu `c30049fd`, RED 4 fail/14 pass → GREEN 227 pass/1 xfail;
review lại NON-BLOCKING. Candidate `736613f6…` (110 file) đóng băng clean tại `c30049fd`, commit `27b81c51`;
benchmark byte-identical 19/9/0/2. T3 clean `27b81c51` PASS backend 9161 / frontend 1053; push cuối và cleanup: run
[`source-grounding-integration`](evaluation/geometry/runs/source-grounding-integration/report.md).
LLM_ONLY/cache125/provider/IR/renderer giữ nguyên; Gemini 0. Các residual đã khai vẫn OPEN, Hybrid product enablement NO-GO.
Kế tiếp chỉ đề xuất người dùng duyệt thiết kế một lát Planner hướng mục tiêu trên kiến trúc sẵn có; chưa triển khai.
DSL lúc ấy `HOLD_WITH_NEXT_EXPERIMENT` (nay `NO-GO_ARCHIVED`, mục trên); hai nhánh real-model giữ, `471a2c79` chỉ được bảo toàn local.

## LOCAL — goal-directed-section-planning, 2026-10-13 (đã tích hợp)

Đã tích hợp: `main` = `origin/main` = `b653d381` (ff `132e9b23` → `b653d381`, push fast-forward; review cuối sửa
anaphor/định nghĩa đọc từ nguồn; candidate `fd80c8c9…`; T3 clean `b653d381` PASS backend 8934, frontend 1053; run
[`goal-directed-section-planning-main-integration`](evaluation/geometry/runs/goal-directed-section-planning-main-integration/report.md)).
Nhánh nguồn `research/goal-directed-section-planning` (đã xoá sau push) từ `132e9b23`.
Phase A: lỗ hở đổi giả thiết sau "sau đó"/"rồi" đóng bằng luật đóng (A/B, hỏi và dựng). Phase B: planner tuyến B tự
phân rã thiết diện với mặt qua điểm đã xác minh song song mặt có tên (`MAT_SONG_SONG`, `translate_point` chỉ cho
planner), bề mặt B `4a20601f…`. Product `68fbc844`, candidate `6110cd67…` (`a443d2a2`), T3 clean PASS (backend 8925,
frontend 1053); benchmark 19/9/0/2 byte-identical; Scene3D harness SwiftShader + GPU PASS; LLM_ONLY/cache125/Gemini0.
Run [`goal-directed-section-planning`](evaluation/geometry/runs/goal-directed-section-planning/report.md).

## LOCAL — question-local-givens, 2026-10-12 (đã tích hợp)

Đã tích hợp: `main` = `origin/main` = `ebe4e463` (ff `232c1225` → `5fe14001` + commit SessionStart; push fast-forward;
T3 clean `5fe14001` PASS; run [`question-local-givens-main-integration`](evaluation/geometry/runs/question-local-givens-main-integration/report.md)).
Nhánh nguồn `research/question-local-givens` (đã xoá sau push) từ main `232c1225`; product `f56d8cb7` (review cuối, run `question-local-givens-final-review`),
candidate commit `8fa3ae4c`, candidate `25c85eed…` (110 file), verify khớp; T3 clean `8fa3ae4c` PASS (backend 8764).
Lỗ hở còn mở: đổi giả thiết cùng câu sau "sau đó"/"rồi" (có từ `232c1225`). Cổng chung A/B kiểm ngữ cảnh yêu cầu và dữ kiện gốc bị model bỏ sót;
không phục vụ hình cũ cho dữ kiện thay đổi/chưa xác minh. Dữ kiện cùng câu đã khớp tiếp tục phục vụ.
RED baseline 34 fail/28 pass (62 test); review 19 fail/4 pass → 23 pass; cluster 861 pass/4 xfail.
Benchmark 30 ca byte-identical 19/9/0/2; provider/schema/cache125/default LLM_ONLY không đổi; Gemini0.
Đã merge/push (xem trên). Scoped replacement, arbitrary wording, chuyển đơn vị và vị từ ngoài vocabulary vẫn unsupported.
Bằng chứng/gate cuối: [`question-local-givens`](evaluation/geometry/runs/question-local-givens/report.md).
T3 clean detached `678f5b7b`: PASS, backend 8760 / frontend 1053, build/demo/crash PASS. Đề nghị GO tích hợp offline có giới hạn; chờ quyết định người dùng.

## LOCAL override — hybrid-main-integration, 2026-10-12

Main đã fast-forward cục bộ `a6e27a78` → `22edf7ff` theo lệnh người dùng; remote vẫn `a6e27a78`, không push.
Candidate `d1410731…` (product `624e7fc5`, 110 file) verify khớp. T3 clean detached tại `22edf7ff`: FULL_PRODUCT_GATE_PASS,
backend 8675/0, frontend 1053; build/demo/crash PASS. Benchmark 30 ca giữ nguyên byte (19/9/0/2).
LLM_ONLY/cache125/provider surfaces không đổi, Gemini0. Run: [`hybrid-main-integration`](evaluation/geometry/runs/hybrid-main-integration/report.md).
Kế tiếp: question-local givens có giới hạn trên research branch mới; chưa triển khai tại mốc integration này.

## LOCAL override — hybrid-semantic-hardening, 2026-10-12

Mới nhất:
- Nhánh `research/hybrid-semantic-hardening` (con của tip đã review `9cfd0fca`; chưa merge/push). S1: cổng nguồn buộc toán hạng câu
  hỏi vào cụm được hỏi (văn phạm đóng), giá trị phải là phép bằng, mở rộng vai trò mệnh đề — probe phần dư 1/79 (cách đọc đúng).
  S2: giao tuyến "vô hình" do đoạn hiển thị cố định ±6 đâm ra sau camera; nay theo cỡ cảnh (SwiftShader + GPU thật).
- Mở: `ISSUE-ARCH-HYBRID-QUESTION-LOCAL-GIVENS`. Candidate/T3 ở run. LLM_ONLY/cache125; LIVE Gemini0.
- Report: [`hybrid-semantic-hardening`](evaluation/geometry/runs/hybrid-semantic-hardening/report.md); handoff tách A (baseline) / B (S1+S2).

Trước đó: [`hybrid-slice-review`](evaluation/geometry/runs/hybrid-slice-review/report.md) (kiểm toán độc lập S0 + lát thiết diện,
candidate 451b046c); [`hybrid-section-slice`](evaluation/geometry/runs/hybrid-section-slice/report.md) (S0 + lát thiết diện).

Trước đó (hybrid-slice1-main-integration):
- Hybrid B slice 1 (B26) + hai bản sửa Important đã tích hợp `main` bằng fast-forward `548066a8` → `a246dd19`; không merge
  commit, không cherry-pick.
- Candidate `dda3a884` (product `62f0b18e`) verify 0 trên `main`; T3 FULL_PRODUCT_GATE_PASS trên `main` (pytest 8362/0,
  vitest 1051); A/B `12da4768` giữ nguyên; cache125/LLM_ONLY; LIVE Gemini0.
- B27/B28 chưa được phê duyệt triển khai. Remote: tra `git log -1 origin/main`.
- Report: [`hybrid-slice1-main-integration`](evaluation/geometry/runs/hybrid-slice1-main-integration/report.md).

Trước đó trong việc Hybrid B (chi tiết ở `STATUS_LEDGER.md` và report của từng run):
[`hybrid-slice1-review`](evaluation/geometry/runs/hybrid-slice1-review/report.md) (kiểm toán độc lập, 2 lỗi Important đã sửa) ·
[`hybrid-goal-decomposition`](evaluation/geometry/runs/hybrid-goal-decomposition/report.md) (lát 1, 18/9/0/3 → 19/9/0/2) ·
[`hybrid-compiler-capability-audit`](evaluation/geometry/runs/hybrid-compiler-capability-audit/report.md) (ADR Hybrid B, benchmark 30 ca).

## LOCAL override — main-integration-readiness, 2026-10-11

Mới nhất: nhánh `integration/geometry-functions` dựng từ main 28ac1d61 bằng fast-forward; T3 FULL_PRODUCT_GATE_PASS
tại `49cf739e` (pytest 8198/0, vitest 1051); candidate a8dc02fc (product `74df2a78`) verify 0; A/B 12da4768 giữ nguyên.
Orbit gate v3 đã kiểm định; đỏ y hệt trên main do cảnh p1 không lắng (lỗi sản phẩm có sẵn). 31 file untracked trùng
nhánh đã backup, chưa xoá (chủ CodexSandboxOffline). ALGOSIM_MAIN_INTEGRATION_READY_FOR_FINAL_APPROVAL.
Report: [`main-integration-readiness`](evaluation/geometry/runs/main-integration-readiness/report.md); trước đó
[`final-integration-gates`](evaluation/geometry/runs/final-integration-gates/report.md) và
[`geometry-library-important-fixes`](evaluation/geometry/runs/geometry-library-important-fixes/report.md).
Đoạn dưới là trạng thái của lượt expansion trước đó (giữ để truy vết):

Thẩm quyền cho checkout LOCAL này (các snapshot remote/main cũ dưới đây không phải Git pre-flight):
nhánh nghiên cứu `feat/geometry-library-expansion`, base2990d87d, product a0eb1450,
tooling3b6104e3; original checkout vẫn `feat/text-to-geometry-functions` tại2990d87d,
main28ac1d61 không đổi; favicon untracked của người dùng giữ nguyên. Không fetch/push/merge.
Registry24→27; hai nhóm dựng điểm trên cùng Engine/Planner/IR/Kernel/Scene3D, không thêm solver.
Candidate mới8ff994c6 (110 file), candidate A/B cũ12da4768 giữ nguyên;
cache125/default LLM_ONLY không đổi.91 feature tests,74 fake calls/network0 và34 renderer tests;
clean backend8166 PASS/1 skip/2 deselected tại815f06be; geometry frontend695 PASS.
GEOMETRY_LIBRARY_EXPANSION_AWAITING_REVIEW; offline GO có giới hạn, live/integration NO-GO.
Không dùng kết quả này thay pilot A/B.
Report/run/handoff: [`geometry-library-expansion`](evaluation/geometry/runs/geometry-library-expansion/report.md).
Human visual acceptance chưa thực hiện; real-model quality chưa đo. LIVE Gemini=0.

File này chỉ giữ **trạng thái và con trỏ**: danh tính kho mã (có sync-lock), cơ sở
mã + bằng chứng, việc kế tiếp, và bảng của wave gần nhất. Chỉ ghi việc **đã thật sự
xong** (có commit + test). Lịch sử thuộc `STATUS_LEDGER.md`; báo cáo và artifact
thuộc thư mục run trong `docs/evaluation/`.

> **Nhật ký phát triển cũ** — bảng w17 trở về trước, các khối W4B, các mục §1–§7 cũ
> (phần lớn mô tả hệ **Tin học** đã gỡ ở `LEGACY_INFORMATICS_REMOVAL`, 2026-09-02) —
> đã chuyển **nguyên văn** sang
> [`legacy/CURRENT_STATE_HISTORY.md`](legacy/CURRENT_STATE_HISTORY.md) ở W19. Trích
> dẫn kiểu *"CURRENT_STATE §3/§4/§5"* trong tài liệu cũ trỏ vào mục cùng số ở đó.
>
> Kiến trúc hiện tại: [`ARCHITECTURE_MAP.md`](ARCHITECTURE_MAP.md) + contract ở
> [`architecture/`](architecture/). Năng lực sản phẩm:
> `backend/app/simulation/product_capability.py`; năng lực theo tầng:
> [`architecture/geometry_capability_matrix_v2.json`](architecture/geometry_capability_matrix_v2.json).
> Tuyên bố ↔ bằng chứng ↔ giới hạn: [`research/CLAIM_EVIDENCE_MAP.md`](research/CLAIM_EVIDENCE_MAP.md).

> ## ⛳ DANH TÍNH KHO MÃ — ĐỌC TRƯỚC MỌI THAY ĐỔI (cập nhật 2026-10-05)
>
> Ba hàng số sống dưới đây **có sync-lock**: `backend/tests/test_current_state_identity.py`
> dẫn xuất chúng từ nguồn (`app.main.CACHE_VERSION`, `build_matrix()` đọc registry)
> và ĐỎ khi bảng này trôi. Test không viết số nào — sửa **tài liệu**, đừng sửa mã.
>
> | | |
> |---|---|
> | Active development branch | **`feat/regular-square-pyramid`** — việc `regular-square-pyramid`: W1 (run `regular-square-pyramid-w01`) + W2 (run `regular-square-pyramid-w02`, 2026-10-05, cloud) + W3 (`regular-square-pyramid-w03`, nghiệm thu local) + W4 (`regular-square-pyramid-w04`, 2026-10-06, giao diện chung) + W5 (`regular-square-pyramid-w05`, 2026-10-06/07, chế độ tập trung + bộ đọc chuỗi bằng nhau) + việc `regular-triangular-pyramid` W1 (`regular-triangular-pyramid-w01`, 2026-10-07, chóp tam giác đều + tứ diện đều, giữ trên cùng nhánh theo lệnh người dùng) + việc `exact-dimensions` (run `exact-dimensions`, 2026-10-07/08, kích thước hữu tỉ + chụp ảnh tại nguồn + chuẩn hoá tên) + việc `mobile-canvas-fit` (run `mobile-canvas-fit`, 2026-10-08, D5: canvas vừa hình trên điện thoại) + việc `phone-landscape-layout` (run `phone-landscape-layout`, 2026-10-08/09, điện thoại ngang + 360 px + nghiệm thu cuối; W3–W5 và các việc sau chỉ ở local), rẽ từ `main` = `38d41588`; **đã fast-forward vào `main` = `caed3809` và push (2026-10-09, run `frontend-freeze`, baseline frontend tạm thời có ngoại lệ theo `APPROVAL.md`); nhánh giữ lại — xoá chưa được phép**. Trước đó: nhánh `fix/cuboid-visual-semantic-closure` đã fast-forward vào `main`, push và xoá (run `cuboid-merge`) |
> | Remote baseline | **`origin/main` = `caed38096f0693702dc0b69668ad8ba58d5fb1fd`** sau push của run `frontend-freeze` (2026-10-09, fast-forward từ `38d41588`, không force, `ls-remote` khớp; commit ghi kết quả tích hợp đi sau, tra `git log -1 origin/main`). Trước đó: `origin/main` = `c282a5f398ea5ed19e311dec10a8c5c2bc4d02ec` sau push của run `cuboid-merge` (2026-10-05, fast-forward từ `a9492ee9`). Lịch sử trước đó: `origin/main` = `a9492ee98ff9dc3302d1ff64465f1c06e9001bce` tại repository gate 2026-09-28; w11 (2026-09-29) và w12 (2026-10-01): ref cục bộ không đổi, là tổ tiên của HEAD; w13 (2026-10-01), w14 (2026-10-01), w15 (2026-10-02), w16 (2026-10-03), w17 (2026-10-03), w18 (2026-10-04) và w19 (2026-10-04): `git fetch --prune origin` + `ls-remote` — không đổi; w20 và run `cuboid-final-review` (2026-10-05): `ls-remote` — không đổi; run `cuboid-acceptance` và run `cuboid-merge` (2026-10-05): `git fetch --prune origin` + `ls-remote` — không đổi; regular-square-pyramid-w01 (2026-10-05): `ls-remote` = `38d41588…` — không đổi (commit ghi kết quả tích hợp của cuboid-merge) |
> | `CACHE_VERSION` | **125** (regular-prisms, 2026-10-09: lăng trụ tam giác đều / lục giác đều đọc + T12, C0 "lăng trụ … đều" có cạnh bên toạ độ không vuông góc đáy served → refused; trước: 124 ở regular-hexagonal-pyramid, 2026-10-09: chóp lục giác đều đọc + T11, giá trị đã phục vụ đổi và C0 lục giác mâu thuẫn served → refused; trước: 123 ở unnamed-pyramid-vertex-binding, 2026-10-09: chính sách A — chóp đều không tên có tên điểm thiếu toạ độ bị chặn, served → refused; trước: 122 ở unnamed-regular-pyramid-grounding, 2026-10-09: chóp đều không tên gắn vào khối duy nhất + kiểm như ký hiệu chuẩn, served → refused và giá trị khung T8 đổi; trước: 121 ở c0-whole-solid-reader, 2026-10-09: bộ đọc nhận "có đỉnh S và đáy ABCD" / "chóp đều S.ABCD" như ký hiệu chuẩn, served → refused; trước: 120 ở c0-whole-solid-grounding, 2026-10-09: C0 kiểm khẳng định toàn khối của đề trên toạ độ đề cho, served → refused; trước: 119 ở geometry-grounding-safety, 2026-10-09: C0 kiểm quan hệ hình dạng đề nói trên toạ độ đề cho, served → refused; trước: 118 ở docs-cleanup, 2026-10-08: envelope từ chối T8 thiếu kích thước đổi nguyên nhân `UNKNOWN` → `SOURCE`, phán quyết vẫn `unsupported`; trước: 117 ở exact-dimensions) — kiểm: `grep -n 'CACHE_VERSION = ' backend/app/main.py` |
> | `HISTORY_SCHEMA_VERSION` | **2** — kiểm: `grep -n 'HISTORY_SCHEMA_VERSION' frontend/src/state/history.ts` |
> | Năng lực hình học | **11 phép dựng · 9 câu lệnh · 7 phép đo** — kiểm: `backend/.venv/Scripts/python.exe backend/scripts/audit_named_operand_ergonomics.py` |
> | `simulation_id` sản phẩm | **`generic.semantic_program`** — duy nhất. Danh mục 24 target Tin học đã gỡ (`LEGACY_INFORMATICS_REMOVAL`, 2026-09-02); xem `docs/evaluation/reports/SCOPE_ALIGNMENT_AUDIT.md` |
> | Archive (read-only) | tag **`m17-w2b-deep-hardening-archive`** → `feb12d8` — kiểm: `git rev-parse m17-w2b-deep-hardening-archive` (nhánh cùng tên đã xoá 2026-08-24) |
>
> ### Mười một tài liệu CANONICAL theo 11 Information Domain
>
> | Domain | File canonical | Ghi chú |
> |---|---|---|
> | Agent rules | **`docs/RULES.md`** | Quy tắc cứng, scope guard; entry point tại `AGENTS.md` |
> | Architecture map | **`docs/ARCHITECTURE_MAP.md`** | Kiến trúc, luồng xử lý, pipeline tất định |
> | Current state | **`docs/CURRENT_STATE.md`** (file này) | Trạng thái + con trỏ; nhật ký cũ ở `docs/legacy/CURRENT_STATE_HISTORY.md` |
> | Status ledger | **`docs/STATUS_LEDGER.md`** | Lịch sử theo thời gian các wave |
> | Code index | **`docs/CODE_INDEX.md`** | Vị trí code, tooling, test |
> | Roadmap | **`docs/ROADMAP.md`** | Lộ trình ưu tiên khóa luận P0–P6 |
> | Open issues | **`docs/OPEN_ISSUES.md`** | Vấn đề đang mở với stable IDs |
> | Migration checklist | **`docs/MIGRATION_CHECKLIST.md`** | 20 cổng di chuyển compiler-first |
> | AI / session handoff | **`docs/AI_CONTEXT_BUNDLE.md`** | Tóm tắt handoff (<= 300 dòng) |
> | Evidence index | **`docs/EVIDENCE_INDEX.md`** | Chỉ mục báo cáo, artifact và chuỗi đính chính |
> | Docs navigation | **`docs/README.md`** | Cổng điều hướng tài liệu |
>
> ### 🎯 CƠ SỞ KHO MÃ & BẰNG CHỨNG (Base State & Canonical Next Action)
>
> ```text
> PRODUCT_AND_EVIDENCE_BASE_HEAD = 45f5a7f0 (dải lớp học gọn thành chip trên màn chật; trên nền điện thoại ngang 95a56a17 + D5 c9bcdcdb); bằng chứng trình duyệt 3095e4f0 (đo 6a1801e7 lần 3, run classroom-band-fit: dải lớp 24/24, không dải lớp 55/56, Tier-A 8/8 một lượt); cổng T3 ở commit tài liệu cuối của run (runs/classroom-band-fit/handoff.md §2)
> DOCUMENTATION_COMMIT_ROLE = SELF
> DEFAULT_MODE = LLM_ONLY
> CACHE_VERSION = 125 trên `main` từ 9b783cb4 (regular-prisms, lăng trụ tam giác/lục giác đều, T12: 6 C0 "lăng trụ … đều" + 2 C0 chóp "đáy là lục giác đều" mâu thuẫn toạ độ served → refused; runs/regular-prisms/cache/decision.json) · trước đó 124 (regular-hexagonal-pyramid; runs/regular-hexagonal-pyramid/cache/decision.json)
> CANDIDATE = nhánh `feat/text-to-geometry-functions` (CHƯA tích hợp): 12da4768495572d7b4d04af733edf0c787337a6ab486ce2cae42f7c94bbbce52 (110 file; product/freeze source cfe2ada5; cache125; clean LOCAL; run hybrid-ab-pilot-readiness) · trước đó e9d20aa2 (historical hybrid) · main: 93077b51d033c198… (102 file; product d8b9da74; cache125; run regular-prisms). Không chấm lại historical results.
> USER_DIRTY_STATE = có — `frontend/public/favicon.svg` untracked của người dùng, giữ nguyên; không stage/commit.
> CURRENT_WAVE = HYBRID_AB_PILOT_READINESS (run hybrid-ab-pilot-readiness, LOCAL, cùng nhánh, live Gemini0): object-binding chính xác, observation ≠ proof; runner SMOKE24/FULL288 có identity riêng, shared output3072; 344 focused PASS,9 mutation killed,312 fake/network0; clean backend8068 PASS/1 skip/2 deselected tại2f1b457c. CORRECTS HYBRID_COMPILER_SELECTION: lịch sử nguyên byte, đọc cùng correction layer. Report/handoff của run là thẩm quyền; không tuyên bố safety population/visual/real-model.
> FINAL_DECISION = HYBRID_AB_PILOT_READINESS_AWAITING_REVIEW — offline GO có giới hạn kiểm chứng; SMOKE/FULL live NO-GO (prompt estimator chưa provider-bound, storage cause UNKNOWN, chưa phê duyệt riêng). Main giữ nguyên28ac1d61; không merge/push/default change; human visual acceptance NOT_PERFORMED.
> TARGET_NEXT_ACTION_AFTER_WAVE = OCR_AFTER_FAMILY_EXPANSION (sau giai đoạn mở rộng họ hình; ROADMAP §0.4 P4)
> ```

> **G05 lăng trụ đều — run regular-prisms (2026-10-09, Cloud, nhánh `feat/g05-regular-prisms`; 0 model call; LOCAL đã kiểm; đã tích hợp `main` = `9b783cb4` theo `APPROVAL.md` của run, 2026-10-10):**
>
> | Mục | Kết quả |
> |---|---|
> | Trước (`ea85216b`) | lăng trụ tam giác/lục giác đều: bộ đọc chỉ thấy `prism`, "lăng trụ đứng … đáy tam giác đều" cần góc vuông (T3) ⇒ 13/13 đề dương bị từ chối; C0 "lăng trụ … đều" với toạ độ mâu thuẫn vẫn PHỤC VỤ |
> | Thêm | bộ đọc lăng trụ đều + khuôn **T12** + metric khung lăng trụ (`do_luong_cua`, A, B, C, A′) + C0 lục giác đều / cạnh bên lăng trụ (amendment §27) — tái dùng khung affine của T8/T11, không engine mới |
> | Kết quả | 13/13 đề dương phục vụ đúng oracle (C1; Scene3D lục giác 12 đỉnh/8 mặt/18 cạnh, tam giác 6/5/9, Euler 2, `chart_metric`); 12 biên từ chối; không đính chính nhãn |
> | Đường chạy | LLM_ONLY route trên chương trình kiểu mô hình (`foundation_only`, mô hình chưa đo); compiler: chưa có họ |
> | `CACHE_VERSION` · candidate | **125** (C0 mâu thuẫn served → refused) · candidate **`93077b51…`** (product `d8b9da74`; đóng băng LOCAL `eaeedb38`, `--verify` khớp) |
> | LOCAL | toán độc lập (metric dựng từ lăng trụ Euclid thật) 13/13, G = `chart_metric`; Scene3D + biến đổi renderer + ảnh trình duyệt (X4, X5, T1, T5) đúng; hồi quy trùng byte; Tier-A 49/49; T3 PASS tại `eaeedb38` (pytest 7729, vitest 1040) (`handoff.md` của run) |
> | Run | [`regular-prisms`](evaluation/geometry/runs/regular-prisms/) (`plan.md`, `report.md`, `handoff.md`) |

> **G05 chóp lục giác đều — run regular-hexagonal-pyramid (2026-10-09, Cloud, nhánh `feat/g05-geometry-capability-expansion`; 0 model call; LOCAL đã kiểm; đã tích hợp `main` = `55f51395` theo `APPROVAL.md` của run, 2026-10-10):**
>
> | Mục | Kết quả |
> |---|---|
> | Trước (`f20caf8a`) | chóp lục giác đều: bộ đọc chỉ thấy `pyramid` ⇒ 7/8 đề dương bị từ chối, "… có đỉnh S và đáy ABCDEF" PHỤC VỤ SAI (1 thay 6√3) |
> | Thêm | bộ đọc lục giác đều + khuôn **T11** + metric khung lục giác (`do_luong_cua`) + C0 kiểm lục giác (amendment §26) — tái dùng cơ chế khung affine của T8, không engine mới |
> | Kết quả | 8/8 đề dương phục vụ đúng giá trị oracle (C1, Scene3D có `chart_metric`); biên từ chối đúng; 1 đính chính nhãn (khung affine, như T8) |
> | Đường chạy | LLM_ONLY route trên chương trình kiểu mô hình (`foundation_only`, mô hình chưa đo); compiler: chưa có họ |
> | `CACHE_VERSION` · candidate | **124** · candidate **`cf47dd61…`** (product `6c792434`; đóng băng LOCAL `0fe806ff`, `--verify` khớp) |
> | Kiểm LOCAL | T3 `FULL_PRODUCT_GATE_PASS` tại `0fe806ff`: pytest 7665 passed / 1 skipped, vitest 1040/1040, build, demo, bề mặt sập; 8 đề dương + N4 kiểm bằng metric Gram tính độc lập (V = (√3/2)a²h, l² = h² + a²); N4 (đính chính nhãn) CHẤP NHẬN — dưới metric từ đề, đỉnh nằm đúng trên pháp tuyến tại tâm, h = 3; Scene3D 7 đỉnh / 7 mặt / Euler 2 / `chart_metric`; phép biến đổi khung → thế giới của frontend (`veKhongGian`) cho lục giác đều thật; ảnh chụp trình duyệt thật (H6, H8, N4, bước 4/4) đúng hình — `diagnostics/local_verification/` |
> | Run | [`regular-hexagonal-pyramid`](evaluation/geometry/runs/regular-hexagonal-pyramid/) (`plan.md`, `report.md`, `handoff.md`) |

> **Chính sách A cho chóp đều không tên chưa gắn được — run unnamed-pyramid-vertex-binding (2026-10-09, Cloud, nhánh `fix/unnamed-pyramid-vertex-binding`; 0 model call; LOCAL đã kiểm; đã tích hợp `main` = `32705882` theo `APPROVAL.md`):**
>
> | Mục | Kết quả |
> |---|---|
> | Nghiên cứu (b) | nhãn + oracle độc lập cho 21 đề: 8 do đề xác định, 8 mơ hồ thật, 4 mâu thuẫn, 1 thiếu; bộ kiểm chỉ từ khuôn T7/T8 đạt 3/21 ⇒ cần mô hình hình học thứ hai |
> | Quyết định | người dùng chọn **A** (cuối cùng): chặn cả 21 — giảm thiểu an toàn, KHÔNG phải kết luận toán học |
> | Sửa | vùng U3 gồm mọi chóp đều không tên; §24 không gắn được ⇒ cổng từ chối `ASSUMPTION_INVARIANCE_UNPROVEN` (amendment §25) |
> | Kết quả | 21/21 từ chối: 12 served → refused (gồm 3 đáp số sai), 9 giữ; 5 đề do đề xác định chưa hỗ trợ (B hoãn) |
> | `CACHE_VERSION` · candidate | **123** (served → refused; bề mặt mô hình không đổi) · candidate **`b13a3ef1…`** (product `56692926`; đóng băng LOCAL `39b0fb4a`, `--verify` khớp) |
> | Kiểm LOCAL | T3 `FULL_PRODUCT_GATE_PASS` tại `39b0fb4a`: pytest 7627 passed / 1 skipped, vitest 1040/1040, build, demo, bề mặt sập (`diagnostics/t3_39b0fb4a.log`); probe C1 chạy lại trên `main` và nhánh trùng byte log Cloud; 21/21 từ chối; 5 đáp số do đề xác định tính lại tay; C0 29 + 27 + 11 hàng trùng byte `main` |
> | Run | [`unnamed-pyramid-vertex-binding`](evaluation/geometry/runs/unnamed-pyramid-vertex-binding/) (`plan.md`, `report.md`, `handoff.md`) |

> **Chóp đều không tên — run unnamed-regular-pyramid-grounding (2026-10-09, Cloud, nhánh `fix/unnamed-regular-pyramid-grounding`; 0 model call; LOCAL đã kiểm; đã tích hợp `main` = `2d3c510c` theo `APPROVAL.md`):**
>
> | Mục | Kết quả |
> |---|---|
> | Trước (`ede8d329`) | 47 đề chóp đều không tên: 37 phục vụ (22 đúng nhãn, 4 sai giá trị, 11 nhãn đòi từ chối), 10 từ chối — ngoài vùng từ chối U3; 3 đề C0 không tên mâu thuẫn được phục vụ |
> | Sửa | bộ đọc phát `regular_*_pyramid ()` (không đoán tên); cổng gắn vào khối duy nhất của chương trình CHỈ khi đề không gọi tên điểm nào thiếu toạ độ, rồi KIỂM như `S.ABCD` (amendment §24); vùng U3 thêm các đề ấy |
> | Kết quả | 26 hàng gắn được = nhãn corpus (13 đúng giữ, 4 sai → đúng giá trị, 8 → từ chối đúng lý do, 1 giữ từ chối); 21 hàng có tên điểm thiếu toạ độ không đổi (3 vẫn phục vụ trái nhãn — quyết định kiến trúc); C0 11/11 nhãn |
> | `CACHE_VERSION` · candidate | **122** (served → refused + giá trị đổi; bề mặt mô hình không đổi) · candidate **`d07a92de…`** (product `12edf57a`; đóng băng LOCAL `97db084f`, `--verify` khớp) |
> | Kiểm LOCAL | T3 `FULL_PRODUCT_GATE_PASS` tại `97db084f`: pytest 7602 passed / 1 skipped, vitest 1040/1040, build, demo, bề mặt sập (`diagnostics/t3_97db084f.log`); probe C1 + C0 chạy lại trên `main` và nhánh trùng byte log Cloud; 4 giá trị sửa và 8 từ chối kiểm lại bằng công thức; thứ tự mặt của chương trình không đổi kết cục; C0 11/11; lối viết khác 0 đổi. Hướng tiếp (người dùng chọn): phương án (b) ở lượt Cloud riêng |
> | Run | [`unnamed-regular-pyramid-grounding`](evaluation/geometry/runs/unnamed-regular-pyramid-grounding/) (`plan.md`, `report.md`, `handoff.md`) |

> **Bộ đọc chóp đều — run c0-whole-solid-reader (2026-10-09, Cloud, nhánh `fix/c0-whole-solid-reader`; 0 model call; LOCAL đã kiểm; đã tích hợp `main` = `81ff8899` theo `APPROVAL.md`):**
>
> | Mục | Kết quả |
> |---|---|
> | Trước (`a1350da3`) | "có đỉnh S và đáy ABCD" và "chóp đều S.ABCD" không phát khẳng định chóp đều ⇒ 10 đề C0 mâu thuẫn được phục vụ; C1 viết lại: từ chối thay vì như ký hiệu chuẩn, 2 đề phục vụ đáp số sai; phủ định ký hiệu chuẩn bị đọc thành tiền đề |
> | Sửa | chỉ bộ đọc (`shape_constraint`): hai lối viết phát đúng tập ràng buộc của ký hiệu chuẩn; không đọc sau "không phải (là)" |
> | Nhãn | 27 hàng C0 ghi trước + oracle độc lập, 27/27; C1 tương đương 94/94 trên hai corpus chóp đều; ký hiệu chuẩn không đổi |
> | `CACHE_VERSION` · candidate | **121** (served → refused, probe trước/sau; bề mặt mô hình không đổi) · candidate **`c3f83399…`** (product `7d551535`; đóng băng LOCAL `1396878e`, `--verify` khớp) |
> | Kiểm LOCAL | T3 `FULL_PRODUCT_GATE_PASS` tại `1396878e`: pytest 7530 passed / 1 skipped, vitest 1040/1040, build, demo, bề mặt sập (`diagnostics/t3_1396878e.log`); probe C0 + C1 chạy lại trên `main` và nhánh trùng byte log Cloud; C1: 3 lối viết × 47 hàng khớp nhãn corpus độc lập (24 refused → served đúng giá trị nhãn; N5 served → refused: `main` phục vụ SA = 3 sai, đúng √17) |
> | Còn mở | chóp đều không tên (`ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ` thu hẹp) · `ISSUE-ARCH-UNNAMED-REGULAR-PYRAMID-OUTSIDE-REFUSAL-ZONE` (15/37 đề C1 không tên phục vụ sai/không đủ dữ kiện) |
> | Run | [`c0-whole-solid-reader`](evaluation/geometry/runs/c0-whole-solid-reader/) (`plan.md`, `report.md`, `handoff.md`) |

> **C0 kiểm khẳng định toàn khối — run c0-whole-solid-grounding (2026-10-09, Cloud, nhánh `fix/c0-whole-solid-grounding`; 0 model call; LOCAL đã kiểm; đã tích hợp `main` = `11be6092` theo `APPROVAL.md`):**
>
> | Mục | Kết quả |
> |---|---|
> | Trước (`9762f441`) | 16 đề tự mâu thuẫn được phục vụ C0: lăng trụ đứng/xiên, hộp chữ nhật, lập phương (+ cạnh), chóp tứ giác/tam giác đều (+ cạnh bên, trung đoạn, tâm đáy chỉ có toạ độ trong đề), tứ diện đều (+ cạnh), chiều cao chóp/lăng trụ |
> | Sửa | `_KIEM_C0` thêm định nghĩa chính xác các khẳng định toàn khối trên khối CÓ TÊN (amendment §22); cùng mã/đường từ chối §21 |
> | Nhãn | 29 hàng ghi trước + oracle độc lập, 29/29 khớp; thiếu dữ kiện (không toạ độ, khối không tên) không bị coi là mâu thuẫn |
> | `CACHE_VERSION` · candidate | **120** (served → refused, probe trước/sau; bề mặt mô hình không đổi) · candidate **`8c4c0128…`** (product `c11e8c9d`; đóng băng LOCAL `d838cc5b`, `--verify` khớp) |
> | Kiểm LOCAL | T3 `FULL_PRODUCT_GATE_PASS` tại `d838cc5b`: pytest 7401 passed / 1 skipped, vitest 1040/1040, build, demo, bề mặt sập (`diagnostics/t3_d838cc5b.log`); chạy lại nhãn trên `main` và nhánh: **15** (không phải 16) hàng served → refused, 0 hồi quy; ca biên LOCAL (căn, chiều cao ≠ cạnh bên, ký hiệu `a`, mệnh đề mục tiêu, phủ định) đúng |
> | Còn mở | `ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ` (bộ đọc không phát khẳng định cho vài cách viết) |
> | Run | [`c0-whole-solid-grounding`](evaluation/geometry/runs/c0-whole-solid-grounding/) (`plan.md`, `report.md`, `handoff.md`) |

> **Sửa an toàn grounding — run geometry-grounding-safety (2026-10-09, Cloud, nhánh `fix/geometry-grounding-safety`; 0 model call; LOCAL đã kiểm; đã tích hợp `main` = `47d05f22` theo `APPROVAL.md`):**
>
> | Mục | Kết quả |
> |---|---|
> | C0 | quan hệ hình dạng đề nói được kiểm chính xác trên toạ độ đề cho; mâu thuẫn ⇒ `SOURCE_SHAPE_CONTRADICTS_COORDINATES` (amendment §21) |
> | Compiler | tứ giác chưa khai dạng là hình chữ nhật chỉ khi ≥ 3 góc vuông kề; một góc ⇒ `BASE_RECTANGLE_NOT_PROVEN` |
> | Nhãn | 18 hàng ghi trước + oracle độc lập, 21/21; red-before 10 đỏ |
> | LOCAL bổ sung | điểm chương trình không khai lấy toạ độ chính đề trong phép kiểm C0 (`765291ab`; trước: `E(5;5;0)` + "AE ⊥ AB" vẫn phục vụ) — 3 test, tiêm lỗi đỏ |
> | Candidate · `CACHE_VERSION` | **`bbfa5b0d…`** (product `765291ab`; đóng băng LOCAL `e1dfc851`, `--verify` khớp) · **119** (served → refused, kiểm độc lập; khoá danh tính khớp) |
> | Kiểm LOCAL | T3 `FULL_PRODUCT_GATE_PASS` tại `e1dfc851`: pytest 7367 passed / 1 skipped, vitest 1040/1040, build, demo, bề mặt sập (`diagnostics/t3_e1dfc851.log`); còn mở: `ISSUE-ARCH-C0-WHOLE-SOLID-RELATIONS-NOT-CHECKED` |
> | Run | [`geometry-grounding-safety`](evaluation/geometry/runs/geometry-grounding-safety/) |

> **G05 đáy đa giác theo chuỗi góc vuông — run general-polygon-base (2026-10-09, Cloud, nhánh `feat/general-polygon-base`; 0 model call; LOCAL đã kiểm; đã tích hợp `main` = `9666b861` theo `APPROVAL.md`):**
>
> | Mục | Kết quả |
> |---|---|
> | Trước | hình thang vuông bị từ chối (LLM_ONLY: không đọc cụm; compiler: coi là hình chữ nhật); chóp đáy tam giác vuông với chân ≠ đỉnh vuông bị từ chối |
> | Thêm | kernel `polygon_from_right_angle_chain` (một thẩm quyền) · bộ đọc "hình thang vuông tại P và Q" · khuôn **T10** (amendment §20) · hai họ compiler `polygon_base_*` (mọi số cạnh, một chuỗi câu lệnh) |
> | Nhãn | 15 hàng ghi trước, oracle độc lập: 7/7 dương + 8/8 âm trên HAI tuyến; red-before 39 đỏ tại `d5287ff7` |
> | Candidate · `CACHE_VERSION` | **`72d6070a…`** (product `4e30a211`; đóng băng LOCAL `f250f5ef`, `--verify` khớp) · **118** (không bump; cache lock verify; ca toạ độ C0 có cụm hình thang vuông trùng byte trước/sau) |
> | Kiểm LOCAL | T3 `FULL_PRODUCT_GATE_PASS` tại `f250f5ef` (worktree tách rời sạch): pytest 7343 passed / 1 skipped, vitest 1040/1040, build, demo, bề mặt sập (`diagnostics/t3_f250f5ef.log`); compiler tự giả định hình chữ nhật: cổng giả định từ chối, khoá bằng test (`handoff.md` §LOCAL) |
> | Năng lực sản phẩm | `right_angle_chain_base` = `foundation_only` (mô hình chưa đo); đa giác đều/góc/lõm/toạ độ-trên-compiler: `ISSUE-ARCH-G05-REMAINING-BASES` |
> | Run | [`general-polygon-base`](evaluation/geometry/runs/general-polygon-base/) (`plan.md`, `report.md`, `handoff.md`) |

> **G04 lăng trụ xiên — run oblique-prism (2026-10-09, Cloud, nhánh `feat/oblique-prism`; 0 model call; LOCAL đã kiểm; đã tích hợp `main` = `a0fdbba4` theo `APPROVAL.md`):**
>
> | Mục | Kết quả |
> |---|---|
> | Trước | 0 dạng G04 có đáp số: cổng giả định chỉ có khuôn lăng trụ ĐỨNG; compiler lăng trụ tam giác bỏ qua `lateral_structure` |
> | Thêm | khuôn **T9** (amendment §19, dùng chung LLM_ONLY + compiler) · họ compiler thứ bảy `oblique_prism_volume` (đáy trên = `translate` do kernel tính, chiều cao = khoảng cách tới mặt đáy) |
> | Miền | đáy tam giác vuông / chữ nhật / vuông, `T F ⊥ (đáy)` với F một đỉnh đáy, chiều cao hữu tỉ (trực tiếp hoặc từ cạnh bên); góc nghiêng, chân ở trung điểm/trọng tâm ⇒ từ chối (`ISSUE-ARCH-OBLIQUE-PRISM-FOOT-VOCABULARY`) |
> | Nhãn | 16 hàng ghi trước, oracle độc lập: 6/6 dương + 10/10 âm khớp trên HAI tuyến; red-before 39 đỏ tại `ba995887` |
> | Candidate · `CACHE_VERSION` | **`02ce5e1e…`** (product `0fe4edc5`; đóng băng LOCAL `75c24394`, `--verify` khớp) · **118** (không bump; 49/49 fixture trùng byte; cache lock verify) |
> | Kiểm LOCAL | T3 `FULL_PRODUCT_GATE_PASS` tại `75c24394` (worktree tách rời sạch): pytest 7290 passed / 1 skipped, vitest 1040/1040, build, demo, bề mặt sập (`diagnostics/t3_75c24394.log`) |
> | Năng lực sản phẩm | `oblique_prism` = `foundation_only` (mô hình chưa đo) |
> | Run | [`oblique-prism`](evaluation/geometry/runs/oblique-prism/) (`plan.md`, `report.md`, `handoff.md`) |

> **Dải lớp học trên điện thoại — run classroom-band-fit (2026-10-09, máy local; đo `6a1801e7` lần 3, worktree tách rời sạch; chờ review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Nguyên nhân | ngang thấp: hàng trên một dòng ép tên bài về 0 px, nhóm công cụ còn `flex-wrap` nên bốn nút xếp dọc; dọc 360 px: mỗi mục dải lớp một dòng; ngân sách chiều cao (sàn canvas 320 px, chạm 44 px) không chứa nổi một dòng dải lớp riêng ở 640×360 · 844×340 · 360×640 |
> | Sửa | tên bài `min-width: 4rem`; công cụ và nút quay lại không co/không xuống dòng; màn chật: dải lớp gọn thành chip trạng thái (`NhomLop` + `LiveClassStrip tomTat`), chạm mở dải đầy đủ — lựa chọn của người dùng; màn rộng và mô phỏng không lớp giữ nguyên |
> | Trình duyệt | dải lớp 3 vai × 8 khổ 24/24 (trước 9/24); không dải lớp 55/56 như trước; Tier-A 8/8 một lượt; W02 16/16, W04 24/24, W05 23/24 (một trang không tải) |
> | Còn lại | ở 640–667 px ngang chip chỉ hiện chấm màu + «…» (quyết H-3); giơ tay hai chạm trên màn chật |
> | Candidate · `CACHE_VERSION` | **`7f3f0423…`** (cây đo không đổi; product `45f5a7f0`) · **118** (không bump) |
> | Run | [`classroom-band-fit`](evaluation/geometry/runs/classroom-band-fit/) (`review.md`, `report.md`, `handoff.md`) |

> **Nghiệm thu cuối — run final-acceptance (2026-10-09, máy local; không sửa sản phẩm, 0 model call):**
>
> | Mục | Kết quả |
> |---|---|
> | Danh tính | candidate `7f3f0423…` `--verify` khớp; `CACHE_VERSION` 118; `LLM_ONLY`; ngoài `docs/` từ `95a56a17` chỉ dời `product_commit_sha` của manifest Tier-A ⇒ Tier-A 8/8 + T3 của phone-landscape-layout còn hiệu lực |
> | Dải lớp học trên điện thoại | lỗi thật, **có từ `main`**: nhánh 11/24, `main` 5/24, không hồi quy — `ISSUE-ARCH-CLASSROOM-BAND-CROWDS-PHONE-TOP-ROW` (OPEN) |
> | E-R6 / F-R7 | chạm giả lập 8/8 (hỗ trợ); thao tác tay vẫn chờ người dùng |
> | UX debt chấp nhận tạm | bảng nổi che canvas khi ngang; nhãn rời canvas sau cú xoay ở màn thấp; header/thanh công cụ mobile — vẫn OPEN |
> | Run | [`final-acceptance`](evaluation/geometry/runs/final-acceptance/) (`review.md`, `report.md`, `handoff.md`) |

> **Điện thoại ngang + 360 px + nghiệm thu cuối — run phone-landscape-layout (2026-10-08/09, máy local; đo `221ec0a0` lần 3, worktree tách rời sạch; chờ review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Nguyên nhân | 844×390: canvas ở sàn 320 px + thanh phát dưới canvas tràn khung 37 px; 667×375 dùng bố cục khổ hẹp khi nằm ngang; 360×640: ba nút phát xuống ba hàng |
> | Sửa | ngang thấp: thanh điều khiển thành cột 10rem cạnh canvas (canvas giữ chiều cao ⇒ hình giữ cỡ; sàn 320 px giữ), ≤ 48rem dùng bố cục rộng; 360 px: ba nút một hàng |
> | Trình duyệt (8 họ × 7 khổ) | điện thoại/ngang 55/56 (trước 15/40 + 0/8; còn ca xoay màn thấp có từ trước); Tier-A 8/8 một lượt; W02 16/16, W04 24/24, W05 24/24, occlusion pass, phát lại pass |
> | Candidate · `CACHE_VERSION` | **`7f3f0423…`** (cây đo không đổi; product `95a56a17`) · **118** (không bump) |
> | Run | [`phone-landscape-layout`](evaluation/geometry/runs/phone-landscape-layout/) (`review.md`, `report.md`, `handoff.md`) |

> **D5 — canvas vừa hình trên điện thoại — run mobile-canvas-fit (2026-10-08, máy local; đo `90921f53`, worktree tách rời sạch; chờ review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Nguyên nhân | canvas lấy trọn chiều cao khả dụng, camera vừa hình theo bề ngang trên điện thoại dọc ⇒ dải trắng trên/dưới; bảng chảy dưới thanh sát đáy ⇒ mở bảng là cuộn, hình rời khung |
> | Sửa | khổ hẹp ≤ 48rem: canvas = rộng × tỉ lệ hình (`caoKhungVuaHinh`, `tiLeKhungHinh`), ≤ phần khả dụng, ≥ 320 px; hình ràng theo chiều cao giữ nguyên; desktop không đổi; bảng bước giữ bước đang xem trong thân bảng |
> | Trình duyệt (8 họ) | D5 39/40 (trước 18/40; còn một ca xoay có từ trước); 390×844 canvas 519 → 320–485 px; W02 16/16, W04 24/24, W05 24/24, occlusion pass, phát lại 16/16; suite 7/8 + chạy lại bước đỏ (kỳ vọng cũ của bộ đo) PASS |
> | Candidate · `CACHE_VERSION` | **`7f3f0423…`** (cây đo không đổi; product `c9bcdcdb`) · **118** (không bump) |
> | Run | [`mobile-canvas-fit`](evaluation/geometry/runs/mobile-canvas-fit/) (`review.md`, `report.md`, `handoff.md`) |

> **Dọn tài liệu + tên — run docs-cleanup (2026-10-08, máy local; chỉ test/CSS chết/tài liệu, không đổi hành vi):**
>
> | Mục | Kết quả |
> |---|---|
> | Tên test | 123 hàm pytest bỏ mã lượt (`test_w17_…` → `test_…`), 74 tiêu đề vitest + 44 node:test bỏ thẻ; bộ chọn `-k wNN` trong tài liệu sống → đường dẫn file; commit riêng `a993aa8f`; bảng ở `evaluation/RUN_NAMING.md` |
> | `docs/legacy/` | 42 → 15 file: xoá 26 (plan/spec Superpowers M9–M17, W13; tài liệu chuyển đề; REPOSITORY_MAP; RULES_v0.3), thiết kế + kế hoạch route Semantic Program → `legacy/architecture/`, `CUBOID_CUBE_CONTRACT_DECISION.md` về `architecture/` (mã còn cài đúng nó) |
> | Hướng dẫn | kế hoạch/spec của skill: thiết kế ⇒ `docs/architecture/`, kế hoạch ⇒ `plan.md` của run (AGENTS §4, `docs/README.md` §8) |
> | Tàn dư Tin học | 12 lớp `geo3d-*` chết gỡ; còn `SamplePreview`/`threeD`/`specDrift` và prompt + IR (sáu prompt không loader) — hai issue `ISSUE-ARCH-*-INFORMATICS-*` |
> | Candidate · `CACHE_VERSION` | **`7f3f042309dd1c54…`** (product `f967ba24`, 102 file) · **118** (bump do refusal envelope đổi) |
> | Run | [`docs-cleanup`](evaluation/geometry/runs/docs-cleanup/) (`plan.md`, `report.md`, `handoff.md`, `inventory.md`, hai manifest độc lập) |

> **Tổ chức tài liệu cuối — lần report organization đã hợp nhất vào docs-cleanup (2026-10-08, không đổi nội dung bằng chứng):** 167/167 report
> có mapping từng file; 33 report về package artifact, 123 report vào `evaluation/reports/`, 11 ngoại lệ path-bound
> ở gốc; 167/167 blob giữ nguyên, catalog/link/consumer được cập nhật. Duyệt hình vẫn NOT_APPROVED.

> **Dọn kho: gỡ phần Tin học hết vai trò + chuẩn hoá tên — run repo-cleanup (2026-10-08, máy local; chỉ tài liệu/mã chết, không đổi hành vi):**
>
> | Mục | Kết quả |
> |---|---|
> | Gỡ | 132 file: bộ đánh giá `app/evaluation/`, `POST /api/explain`, 42 fixture + oracle thuật toán, 9 script một lần, 26 file engine/view Tin học ở `frontend/src`, 42 runner trình duyệt của danh mục Tin học; 325 selector CSS chết; 8 script `test:domain:*` chết — bằng chứng từng file: `runs/repo-cleanup/inventory.json` |
> | Chuyển sang ca hình học | "runner ghi model" → runner DEV hình học; bộ chọn T0 → `domains/geometry`/`semantic`; SEALED còn consumer giữ, pin M17 thuần Tin học đã gỡ ở cleanup tiếp nối; `/api/explain` khoá 404 |
> | Đổi tên | 29 file + gộp hai test pin + một lớp, commit riêng `67e11671` — bảng ở `evaluation/RUN_NAMING.md` |
> | Còn lại có lý do | prompt Tin học + từ vựng container của IR (băm bề mặt mô hình, IR cấm đổi) · vỏ `SamplePreview`/`threeD`/`specDrift`, 9 lớp `geo3d-*` chết — `ISSUE-ARCH-INFORMATICS-MODEL-SURFACE-AND-IR-VOCABULARY`, `ISSUE-ARCH-SHELL-INFORMATICS-RESIDUE` |
> | Candidate · `CACHE_VERSION` | `e1927f84…` → **`b4a33205…`** (product `be4b8287`, 102 file) · **117** (không bump: khoá danh tính cache khớp nguyên) |
> | Run | [`repo-cleanup`](evaluation/geometry/runs/repo-cleanup/) (`report.md`, `handoff.md`, `inventory.json`) |

> **Kích thước chính xác + chụp ảnh tại nguồn + chuẩn hoá tên — run exact-dimensions (2026-10-07/08, máy local; chờ review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Miền mới | chóp tam giác đều với cạnh đáy + chiều cao hữu tỉ/phân số/thập phân, cạnh đáy + cạnh bên, tứ diện đều cạnh hữu tỉ — phục vụ trên route (b=6, h=4 → 12√3; tứ diện a=6 → 18√2); ca căn cũ trùng byte; vẫn từ chối: thiếu/mâu thuẫn/suy biến, kích thước chữ, tổng căn |
> | Biểu diễn | toạ độ chương trình = khung affine ℚ³; độ dài từ ma trận Gram hữu tỉ G suy từ sáu cạnh của đề (`geometry/metric.py`, `assumption_gate.do_luong_cua`); G = I ⇒ biểu thức cũ nguyên byte; renderer ánh xạ khung → không gian một lần (`scene3d-chart.ts`) |
> | Lỗi tìm ra | bộ đọc độ dài lấy vế đầu của biểu thức ("4 + 1" từng phục vụ V = 16) — sửa, `CACHE_VERSION` 117 |
> | Trình duyệt | họ chóp tam giác đều: suite 7/7, điều khiển cảnh 2/2, bảng 3/3, tập trung 3/3, occlusion pass, phát lại 2/2; 3 lần đo — lần 1–2 đỏ vì lỗi BỘ ĐO (khung không trực giao), chỉ chạy lại bước đỏ |
> | Ảnh (cùng họ, cùng bước) | tạo 109 → **15** (runner 103 → 11; xoá sau chụp 52 → 0), quyết trước khi chụp (`capture-policy.mjs`) — `runs/exact-dimensions/capture_counts.json` |
> | Tên | 11 tệp/thư mục đổi tên ở commit riêng `0ed6332f`; một tài liệu sống `evaluation/RUN_NAMING.md` |
> | Candidate · `CACHE_VERSION` | `92c9e198…` → **`e1927f84…`** (product `ed3ae208`) · 116 → **117** |
> | Run | [`exact-dimensions`](evaluation/geometry/runs/exact-dimensions/) (`review.md`, `report.md`, `handoff.md`) |

> **Chóp tam giác đều + tứ diện đều (miền ℚ³) — regular-triangular-pyramid-w01 (đo `1bb11018`, worktree tách rời sạch; chờ review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Họ mới | chóp tam giác đều + tứ diện đều trên route sản phẩm, miền khai: cạnh đáy² ∈ {2k², 6k²}, chiều cao² = 3t²; ngoài miền từ chối `TEMPLATE_NOT_REPRESENTABLE T8`; năng lực `foundation_only` |
> | Backend | độ dài nguồn đọc căn (`segment_relation`), khuôn T8 (`assumption_gate`, thẩm quyền `shape_constraint.la_chop_tam_giac_deu`), trọng tâm suy ra (`formation`, `construction_binding`), so khớp chính xác cho căn |
> | Giao diện | D1–D4 sửa; D5 chờ quyết định (`ISSUE-ARCH-MOBILE-CANVAS-WHITESPACE-AND-PANEL-SCROLL`); D6 giữ; xoay hiển thị đáy nghiêng; khung nhìn ban đầu nay ở giữa mọi họ (`diemVuaKhung`, sau lượt đo 1) |
> | Trình duyệt `1bb11018` | suite 8/8, 16/16 + 31/31 âm; W02 16/16 (chạy lại riêng); W04 24/24 (cross_section chạy lại riêng); W05 24/24; occlusion pass; phát lại 16/16; 3 lần đo, chỉ lần 3 dùng |
> | Ảnh | 492 giữ / 358 tỉa (W5: 767 cho bảy họ) — `TEST_TIERS.md` luật "chụp để kiểm, lưu có chọn" |
> | Candidate · `CACHE_VERSION` | `5e1c0639…` → **`92c9e198…`** (product `1e90ca0e`, hai lần đóng băng) · **116** (bump: hai envelope thiết diện đổi nhãn bước) |
> | Run | [`regular-triangular-pyramid-w01`](evaluation/geometry/runs/regular-triangular-pyramid-w01/) (`REVIEW.md`, `REPORT.md`, `HANDOFF.md`) |

> **Chế độ tập trung + bộ đọc chuỗi bằng nhau — regular-square-pyramid-w05 (đo `f01df0e5`, worktree tách rời sạch; chờ review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Không gian mô phỏng | cảnh 3D lấp trang, không thanh trên toàn cục; «← trang trước» · tên bài · «Đề bài» · menu «Khám phá»/«Hiển thị»/«Thêm»; toàn màn hình tuỳ chọn; trang vừa một màn ở desktop/màn thấp, mobile cuộn |
> | Bỏ lặp | thẻ lời giải dưới thanh phát gỡ — đại lượng ở «Đại lượng», công thức + nguồn ở ô soi, chú giải màu trong «Hiển thị» |
> | Backend | `segment_relation` đọc `SA = SB = SC = SD = 3` cho mọi đoạn; `R2_L1` phục vụ `V = 16/3` (`ISSUE-ARCH-SOURCE-LENGTH-CHAINED-EQUALITY` khép) |
> | Trình duyệt `f01df0e5` | suite 7/7, 14/14; W2 14/14; W4 21/21; **W05 21/21**; occlusion pass (4 cảnh chờ duyệt, U2); phát lại 14/14; 4 lần đo, chỉ lần 4 dùng |
> | Candidate · `CACHE_VERSION` | `8a27a58b…` → **`5e1c0639…`** (product `82225a7b`, hai lần đóng băng) · **115** (không bump) |
> | Run | [`regular-square-pyramid-w05`](evaluation/geometry/runs/regular-square-pyramid-w05/) (`REVIEW.md`, `REPORT.md`, `HANDOFF.md`) |

> **Giao diện mô phỏng dùng chung — regular-square-pyramid-w04 (đo `103494c4`, worktree tách rời sạch; chờ review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Bảng thông tin | ô soi, Xem đề, Thành phần, Đại lượng, Các bước dựng: một cơ chế `BangNoi` — nổi, kéo tiêu đề, phím, Escape, về mặc định, thu gọn; không cột, không đổi canvas/camera/bước; nhiều bảng cùng mở; mobile là tấm trong dòng chảy (H-W2-3 khép) |
> | Bố cục | canvas theo chiều cao khả dụng, thanh phát sát đáy; «Bước n/N» trong thanh; mô tả bước trong «Các bước dựng»; canvas WebGL theo khung |
> | Chọn thành phần | bấm thẳng lên hình; cây «Thành phần» theo bước, nhóm thu gọn mặc định, không lộ vật tương lai |
> | Câu chữ · SM | lời kể theo ký hiệu đề (`ten_trong_loi_ke`); SM trên SA nhường nét, chọn SM chỉ sáng khúc S–M |
> | Trình duyệt `103494c4` | suite 7/7, 14/14 lượt dương; đầu dò W2 14/14; đầu dò W4 21/21 (7 họ × desktop/màn thấp/mobile); occlusion 0 lỗi (4 cảnh chờ duyệt, U2); phát lại pass; 4 lần đo, chỉ lần 4 dùng |
> | Candidate · `CACHE_VERSION` | `5dec4572…` → **`8a27a58b…`** (product `53e4bec5`, ba lần đóng băng) · 114 → **115** (36 row v114 vẫn HIT) |
> | Run | [`regular-square-pyramid-w04`](evaluation/geometry/runs/regular-square-pyramid-w04/) (`REVIEW.md`, `REPORT.md`, `HANDOFF.md`) |

> **Nghiệm thu local W2 + hai bản sửa — regular-square-pyramid-w03 (đo `a5d233ce`, worktree tách rời sạch; chờ review người):**
>
> | Mục | Kết quả |
> |---|---|
> | W2 nguyên trạng `fe68b4ca` | T3 `FULL_PRODUCT_GATE_PASS`; cổng danh tính xanh; test node đường dẫn có dấu cách qua; 14/14 lượt dương xanh trọn — `camera_settled_rotated_neutral` và `causal_restore` thiết diện đỏ trên cloud là lỗi môi trường |
> | H-W2-4 (lỗi) | mặt phẳng phụ chỉ để đo không mở bước dựng (`measurementOnlyPlanes`); miễn trừ W2 ở ba cổng đã gỡ; chóp đều 8 bước |
> | H-W2-2 (lỗi) | đoạn đề hỏi độ dài được dựng trước đáp số (`formation._doan_duoc_hoi`); kỳ vọng W18 `d_kq` khôi phục (đính chính PC1-W2) |
> | H-W2-3, H-W2-5 | lựa chọn trình bày, chưa đổi; đề nghị giữ — chưa được người dùng chấp nhận |
> | Trình duyệt `a5d233ce` | suite 7/7, 14/14 lượt dương xanh; đầu dò W2 14/14; occlusion 0 lỗi (4 cảnh chờ duyệt, U2); phát lại PASS không miễn trừ; 68 crop, 0 bất đồng |
> | Candidate · `CACHE_VERSION` | `d3de9c44…` → **`5dec4572…`** (product `45beaed3`) · 113 → **114** (13 row v113 vẫn HIT) |
> | Run | [`regular-square-pyramid-w03`](evaluation/geometry/runs/regular-square-pyramid-w03/) (`REVIEW.md`, `REPORT.md`, `HANDOFF.md`) |

> **Khép phần sư phạm của chóp đều — regular-square-pyramid-w02 (triển khai trên cloud, đo `94200b50`; nghiệm thu local ở W3):**
>
> | Mục | Kết quả |
> |---|---|
> | Kết luận | **`CLOUD_IMPLEMENTATION_COMPLETE_LOCAL_VERIFICATION_REQUIRED`** — HANDOFF.md §2 (kiểm còn phải chạy ở máy local), §3 (H-W2-1 chặn merge) |
> | Nhãn theo formation state | nhãn đoạn chỉ khi đoạn mang nó đã dựng (đoạn, cạnh đa giác, cạnh khối), ở mọi chế độ; nhãn hợp lệ thiếu chỗ phân biệt được |
> | Bảng nổi «Các bước dựng» | nổi trên khung, kéo bằng tiêu đề, phím, về mặc định, kẹp khi kéo/đổi cỡ; không đổi cỡ canvas/camera; mobile trong dòng chảy, thu gọn |
> | SO + chiều cao | bước bổ sung dựng SO khi đề nói "đều" và tâm dựng từ hai đường chéo; chiều cao của công thức chọn theo quan hệ ⊥ kiểm chính xác (gỡ luật giá trị W1) |
> | Hình phụ · lưới | AC, BD ẩn sau khi có O; mặt phẳng chỉ để đo ẩn; chip «Hình phụ», «Lưới» (mặc định tắt) |
> | Trình duyệt | đầu dò W2 **14/14** (7 họ × desktop + mobile: kéo, phím, đổi cỡ, về mặc định, Escape; canvas/camera không đổi; nhãn theo bước khớp oracle); từ chối 54/54, phục vụ 6/6, chọn 68/68, ngăn 14/14; occlusion 0 lỗi; phát 14/14; 68 crop, 0 bất đồng oracle. Đỏ chỉ ở hai cổng nghi môi trường, cũng đỏ ở W1 head trên cloud: `camera_settled_rotated_neutral` (6 desktop), `causal_restore` thiết diện (desktop + mobile) — chạy lại ở máy local |
> | Candidate · `CACHE_VERSION` | `5234c37e…` → **`d3de9c44…`** (bốn lần đóng băng cùng tree hash; product commit `70665542`) · 112 → **113** (13 row v112 vẫn HIT; sáu họ cũ trùng byte) |
> | Run | [`regular-square-pyramid-w02`](evaluation/geometry/runs/regular-square-pyramid-w02/) (`REPORT.md`, `HANDOFF.md`) |

> **Chóp tứ giác đều + chín chỉnh sửa giao diện §0.1 — regular-square-pyramid-w01 (đo `ed37f9fa`, worktree tách rời sạch; chưa có review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Kết luận | **`READY_FOR_HUMAN_VISUAL_REVIEW`** — mọi cổng tự động đạt; điều kiện merge: người duyệt H-W1-1 (`HANDOFF.md` §1) |
> | Chóp tứ giác đều | bộ đọc "đều"/cạnh đáy/cạnh bên/trung đoạn/tâm đáy; khuôn C1 T7 (cạnh bên cả từ `SA = 3`); tâm O theo danh tính; chiều cao đo được của thể tích; corpus đăng ký trước **24/24** (hai lớp: 17 + 7) |
> | Giao diện §0.1 | card Kết quả ẩn khi thu gọn · ngăn «Đại lượng» · panel «Các bước dựng» (desktop cạnh khung, mobile dưới điều khiển) · gỡ dải «Đang dựng» · ghi vị trí cuộn mỗi ảnh |
> | Trình duyệt · occlusion · playback | **7/7 họ**: 14/14 dương, 54/54 âm, 6/6 phục vụ, chọn đại lượng 68/68, ngăn + panel 14/14 · occlusion 0 lỗi (bốn cảnh W14 chờ người) · playback 14/14 · 68 crop, 0 bất đồng |
> | T3 từ đường dẫn CÓ dấu cách (`7b99ccaa`) | **PASS** — pytest 7131/0 (1 skipped, 2 deselected) · vitest 1071/1071 · build · demo 5/5 · bề mặt sập 6/6; cổng danh tính, audit tài liệu, harness node đạt |
> | Lỗi tìm ra | công thức thể tích mất khi có hai ứng viên chiều cao (`98e2b8f7`) · cổng phạm vi từ chối "độ dài" (`9d66c603`, đóng `ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE`) · tự rà soát cuối: T7 bỏ qua cạnh bên `SA = 3` (`ad7172ab`; lớp nhãn R2 7/7) |
> | Candidate · `CACHE_VERSION` | `b2d4187a…` → `4629c3e8…` (trung gian, `de5b2331`) → **`5234c37e…`** (`ad7172ab`, sau tự rà soát) · 111 → **112** (`de5b2331`, chứng minh theo hàng; bản sửa giữ 112); vân tay bề mặt mô hình không đổi |
> | Run | [`regular-square-pyramid-w01`](evaluation/geometry/runs/regular-square-pyramid-w01/) (`REPORT.md`, `HANDOFF.md`) |

> **Gói duyệt hình + tích hợp — run `cuboid-merge` (2026-10-05; chỉ tài liệu; đã duyệt, đã merge và push):**
>
> | Mục | Kết quả |
> |---|---|
> | Kết luận | **`MERGED_AND_PUSHED`** — người dùng ACCEPTED A–E, F (F1–F5 hoãn, vẫn mở) cho [`REVIEW.md`](evaluation/geometry/runs/cuboid-merge/REVIEW.md) ([`APPROVAL.md`](evaluation/geometry/runs/cuboid-merge/APPROVAL.md)); `main` fast-forward `a9492ee9` → `c282a5f3`, push thường, nhánh local đã xoá (không có trên remote) |
> | Ảnh W18 → candidate `b2d4187a` | **chuyển tiếp được, 0 ảnh chụp mới**: fixture tái sinh offline trùng byte bản đã đo; 32/32 fixture hiện hành chỉ khác hai trường danh tính; frontend chỉ đổi ở thẻ từ chối (`results/logs/TRANSFER.log`) |
> | Run | [`cuboid-merge`](evaluation/geometry/runs/cuboid-merge/) (`REVIEW.md`, `HANDOFF.md`, `results/FIXTURE_TRANSFER.json`) |

> **Đối chiếu bất biến + hồ sơ nghiệm thu — run `cuboid-acceptance` (2026-10-05; chỉ tài liệu, byte sản phẩm không đổi so với candidate `b2d4187a`; chưa có review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Kết luận | **`READY_FOR_HUMAN_VISUAL_REVIEW`** — 0 bất biến vi phạm, 0 lỗi chặn nghiệm thu; điều kiện merge còn lại: duyệt hình theo `HANDOFF.md` §1 của run |
> | Bất biến §5 | **24** hàng có con trỏ chết (sửa số 22: #9/#12 thừa hưởng qua "như trên") — 9 đang khoá · 1 chưa đủ bằng chứng (#14, `ISSUE-OPS-LIVE-OPT-IN-NOT-UNIFORM`, không chặn merge) · 14 lịch sử · 0 vi phạm; con trỏ chỉ còn file sống (39/39 hàng, 0 thiếu) — `ISSUE-DOCS-INVARIANT-ENFORCEMENT-POINTERS-STALE` RESOLVED |
> | Quyết định người dùng | H-CFR-2 giữ chữ thường và "toạ độ"; H-CFR-1 = backlog giao diện (`ROADMAP.md` §0.1); H-CFR-3 `THESIS_DRAFT` §1.8 là bản chính đề xuất, `RELATED_WORK_DRAFT` giữ tới khi đối chiếu nội dung riêng |
> | Kiểm chứng | worktree tách rời sạch tại commit tài liệu: `results/logs/INVARIANT_CHECKS_FINAL.log`, `results/logs/DOCS_GATES_FINAL.log` (candidate/cache verify, `LLM_ONLY`, audit tài liệu, test tài liệu, `git diff --check`, báo cáo lịch sử không đổi) |
> | Run | [`cuboid-acceptance`](evaluation/geometry/runs/cuboid-acceptance/) (`REPORT.md`, `HANDOFF.md`, `results/INVARIANT_RECONCILIATION.json`) |

> **Rà soát trọn tài liệu + thẻ từ chối §17 — run `cuboid-final-review` (lượt chốt của việc cuboid; kiểm chứng `a1c53cdb`, worktree tách rời sạch; chưa có review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Kết luận | **`READY_FOR_HUMAN_VISUAL_REVIEW`** — điều kiện merge: review người W18-H1 + thẻ từ chối §17 mới (`HANDOFF.md` §1, đường dẫn ảnh) |
> | Rà soát tài liệu | 8812 file phân lớp (`inventory/DOCS_INVENTORY*.json`); phần thời Tin học của 7 tài liệu sống tách **nguyên văn** sang `legacy/` (119 khối, 2960 dòng, `split_history_cfr.py --verify`); tài liệu sống: 0 link chết, link theo máy 4 → 0; 0 file đã theo dõi bị xoá; 180 báo cáo ở gốc = giới hạn có chủ đích |
> | Đánh số wave | theo từng việc — việc mới, nhánh mới bắt đầu ở W1; định danh `<task-slug>-wNN` (`evaluation/RUN_NAMING.md`; AGENTS §2, RULES §2) |
> | Thẻ từ chối §17 | "Hệ chưa kiểm chứng được ‹quan hệ›, vì điểm này ‹cách đặt› thay vì dựng từ quan hệ trong đề. Hệ tạm dừng…" + nhãn "chưa kiểm chứng được phép dựng"; lệch/chưa đối chiếu giữ nhãn; trình duyệt **12/12** desktop + mobile |
> | T3 từ đường dẫn CÓ dấu cách (`a1c53cdb`) | **PASS** — pytest 7079/0 (1 skipped, 2 deselected) · vitest 1061/1061 · build · demo 5/5 · bề mặt sập 6/6; cổng danh tính, audit tài liệu, harness node đạt |
> | Candidate · `CACHE_VERSION` | `27c31de6…` → **`b2d4187a…`** (một lần đóng băng, `284a9bfa`) · **111** giữ nguyên (chứng minh theo hàng, `6ec40806`); vân tay bề mặt mô hình không đổi |
> | Bất biến | 0/181 báo cáo lịch sử đổi; ngoài run, `docs/evaluation` chỉ đổi `RUN_NAMING.md` + hai registry sống; `LLM_ONLY`; 0 lượt gọi live; không push/merge/xoá nhánh |
> | Run | [`cuboid-final-review`](evaluation/geometry/runs/cuboid-final-review/) (`REPORT.md`, `HANDOFF.md`) |

> **Đóng tính đúng trước merge + dọn kho — w20 (kiểm chứng `5fbb397b`, worktree tách rời sạch; chưa có review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Kết luận | **`READY_FOR_HUMAN_VISUAL_REVIEW`** — hai issue chặn đã đóng bằng bằng chứng; điều kiện merge còn lại: review người W18-H1 (`NOT_APPROVED`) |
> | Đích quan hệ đặt bằng toạ độ (amendment §17) | Trước sửa: hình chiếu đặt bằng toạ độ ngoài vùng đa diện được phục vụ (một ca đáp số sai 2√14 thay vì 3√6), toạ độ rồi mới dựng và bí danh của một đỉnh cũng được phục vụ. Nay: `DEFINED_BY_COORDINATES` → `CONSTRUCTION_REPLACED_BY_COORDINATES` ở mọi vùng. Probe 20/27 → **26/27** (hàng còn lại do cổng miền, ghi trước bản sửa); census 179 hàng không đổi; tiêm lỗi 10/10 bắt |
> | Test không ghi bằng chứng đông cứng | `run_reconciliation(out_dir)` bắt buộc thư mục ra, từ chối thư mục đông cứng và thư mục con; lượt backend đầy đủ ở cây chính để `git status` y nguyên |
> | T3 từ đường dẫn CÓ dấu cách (`5fbb397b`) | **PASS** — pytest 7077/0 (1 skipped, 2 deselected) · vitest 1058/1058 · build · demo · bề mặt sập 6/6; cổng danh tính, audit tài liệu, harness node đạt |
> | Candidate · `CACHE_VERSION` | `d3b4cab9…` → **`27c31de6…`** (hai lần đóng băng, khai ở run) · 110 → **111** (`bedb1040`; khoá `ac241a8d`; vân tay bề mặt mô hình không đổi) |
> | Luật và dọn kho | AGENTS.md §2/§4 + RULES.md §1 (`a36f3e97`); 64 mục xoá có bằng chứng cơ giới, `docs/legacy/superpowers/` giữ 18/18, 314 mục chờ quyết định |
> | Bất biến | ngoài run W20, `docs/evaluation` chỉ đổi hai registry sống; 0/181 báo cáo lịch sử đổi; `LLM_ONLY`; 0 lượt gọi live; không push/merge/xoá nhánh |
> | Run | [`w20-cleanup-premerge`](evaluation/geometry/runs/w20-cleanup-premerge/) (`REPORT.md`, `HANDOFF.md`) |

> **Tổ chức lại tài liệu và bằng chứng nghiên cứu — w19 (chỉ tài liệu; 0 thay đổi sản phẩm; 0 lượt gọi model):**
>
> | Mục | Kết quả |
> |---|---|
> | Kết luận | **`DOCS_REORGANIZED_AND_VERIFIED`** — trạng thái sản phẩm vẫn là của w18 (bảng dưới; người duyệt `NOT_APPROVED`) |
> | Cấu trúc | gốc `docs/` = 11 tài liệu chuẩn tắc + 7 tài liệu dự án + báo cáo wave cũ (catalog đóng, 180); `research/` (bản đồ tuyên bố, khoá luận, bài báo); `evaluation/` (run); `legacy/` (hết hiệu lực) — [`README.md`](README.md) |
> | Di chuyển | 65 file bằng `git mv` (33 sang `research/`, 32 sang `legacy/`); nhật ký phát triển của file này sang [`legacy/CURRENT_STATE_HISTORY.md`](legacy/CURRENT_STATE_HISTORY.md) nguyên văn; cũ → mới: `inventory/MIGRATION_MAP.json` của run |
> | Một nơi có thẩm quyền | tuyên bố ↔ bằng chứng ↔ giới hạn: [`research/CLAIM_EVIDENCE_MAP.md`](research/CLAIM_EVIDENCE_MAP.md) thay ba bảng cũ; báo cáo wave mới chỉ trong thư mục run (`audit_docs_layout`) |
> | Bất biến | báo cáo wave cũ và `docs/evaluation/**` cũ trùng blob với `6d0e6321`; candidate và cache 110 verify; `LLM_ONLY`; 0 lượt gọi live; không push/merge |
> | Run | [`w19-docs-organization`](evaluation/geometry/runs/w19-docs-organization/) |

> **Phép dựng điểm gắn với quan hệ của đề + nhãn tập trung — w18 (measurement `0ca3accf`, detached clean worktree; chưa có review người):**
>
> | Mục | Kết quả |
> |---|---|
> | Kết luận | **`READY_FOR_HUMAN_VISUAL_REVIEW`** — mọi cổng bắt buộc đạt trên candidate cuối; review người `NOT_APPROVED` |
> | Phép dựng điểm cùng thực thể với đề (§16.1–16.4) | Trước sửa: chiếu lên sai đường (6√2 thay vì 3√6), sai mặt phẳng, tráo danh sách "lần lượt" (3√6 thay vì 9), đổi tên đích và một điểm trùng toạ độ khác danh tính đều được PHỤC VỤ. Nay chặng `construction_binding` đối chiếu theo danh tính: lệch ⇒ `CONSTRUCTION_NOT_TEXT_BOUND` ở mọi vùng, nêu cả hai quan hệ; chưa đối chiếu được ⇒ `CONSTRUCTION_BINDING_UNVERIFIED` trong vùng đa diện, không bao giờ nói đề sai |
> | Census (`00654627`) | **SHIP** · AC2 **18/18** · không hàng phục vụ nào của W14–W17C bị từ chối · thay đổi tuyến duy nhất: W15 `oov:chia_doan_canh` (vốn bị từ chối) nay bị từ chối sớm hơn · corpus W18 23/23 đúng kỳ vọng |
> | Nhãn tập trung + một nơi giải thích (§16.5–16.6) | Mặc định: tên điểm + dữ kiện; chọn đại lượng ⇒ nhãn + chuỗi số; một công tắc "Hiện tất cả" (thay "Số đo"/"Kết quả"); ô soi là nơi giải thích duy nhất; lời giải thu gọn mặc định; bản đo trùng gộp theo chủ thể (`same_as`), không theo giá trị |
> | Nhân chứng khoảng cách (§16.7) | Điểm → đường/mặt: đoạn nét đứt tới chân CHÍNH XÁC do kernel tính + ký hiệu vuông góc, chỉ khi nhãn khoảng cách hiện; frontend không tính chân |
> | Bộ đo | Lượt đo nghiệm thu đầu (`8caa8307`) đạt hết; tiêm lỗi frontend vòng 1 tìm ra ba điểm mù của bộ đo trình duyệt (nét đứt khi tô sáng, mốc của công tắc, hai bản công thức khi lời giải mở). Sửa bộ đo đỏ-trước (`1d8dfc6f`), giữ riêng lần thử 1, đo lại toàn bộ ở `0ca3accf` |
> | Tiêm lỗi | backend **12/12** (vòng 3) · frontend vòng 2 tại `0ca3accf` **12/12** (8 đơn vị + 4 trình duyệt; vòng 1 tại `8caa8307`: đơn vị 8/8, trình duyệt 1/4 — ba điểm mù của bộ đo, đã sửa) |
> | T3 từ đường dẫn CÓ dấu cách (`0ca3accf`) | **PASS** — pytest 7001/0 fail (1 skipped, 2 deselected) · vitest 1058/1058 · build · demo 5/5 · bề mặt sập 6/6 |
> | Ảnh · oracle · playback | Trình duyệt 12/12 dương, 46/46 âm (8 loại, có 3 loại W18), 6/6 phục vụ; chọn từng đại lượng 58/58; một vùng công thức 10/10 (thu gọn) + 10/10 (mở); "Hiện tất cả" so với trạng thái trước lần bấm 12/12; nét đứt theo bước 72/72 · occlusion `HUMAN_REVIEW_PENDING` (bốn cảnh như w15–w17) · playback 12/12 · 64 crop, 0 bất đồng |
> | Candidate · `CACHE_VERSION` | `d63d6fd4…` → **`d3b4cab9…`** (đóng băng MỘT lần tại `7a06ee47`) · 109 → **110** (`1e8c5658`; khoá danh tính `5cfb53a1`; fingerprint provider không đổi) |
> | Giới hạn khai | Từ vựng đóng (trung điểm, hình chiếu): tâm, trọng tâm, giao điểm chưa đối chiếu; cách nói ngoài từ vựng bị từ chối dù đúng (`ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY`) · cổng phạm vi chưa có manh mối "độ dài" (`ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE`) · tô sáng cạnh khuất chỉ xảy ra ở họ thiết diện nên ở năm họ kia luật nét đứt do test đơn vị giữ |
> | Run | [`w18-binding-focus`](evaluation/geometry/runs/w18-binding-focus/) |
>
> Nguồn: `docs/evaluation/geometry/runs/w18-binding-focus/` (`REPORT.md`, `HANDOFF.md`).
> Bảng w17 trở về trước: [`legacy/CURRENT_STATE_HISTORY.md`](legacy/CURRENT_STATE_HISTORY.md).
