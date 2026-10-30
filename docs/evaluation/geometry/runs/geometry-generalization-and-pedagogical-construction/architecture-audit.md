# W4 architecture audit (read-only): step-by-step construction and pedagogy

Worktree: `.superpowers/worktrees/w4-geometry-pedagogy` @ e5dc3d28. Later commits that touch only `registry.py` regexes do not change these findings.
Paths are relative to the repo root. `file:line` references are to real code. Anything not checked against code is marked **UNVERIFIED**.

## 1. Execution paths from text or TypedFactNext to a rendered Scene3D

**Route B: LLM_ONLY, the product default.** `POST /api/analyze` is handled by `main.py:1110`. It checks the trial gate, then `ingest_to_text`, then the exact cache lookup (`main.py:1158-1173`), then `_ngoai_pham_vi`/`detect_domain`, then `run_pipeline(..., semantic_route=…, route_policy=tuyen)` (`main.py:1208`).
From there the path is `_semantic_route_attempt` (`ai/pipeline.py:731`):
1. `quyet_dinh_dinh_tuyen` (`:778`). The compiler is DISABLED under LLM_ONLY.
2. `stage_semantic_program`, an LLM call (`:383`).
3. `verify_and_compile` (`:817`).
4. Only if the program is `executable`, `_dung_scene3d` (`:586-655`) runs:
   - `hoan_thien_dung_hinh`, the teaching expansion (`formation.py`);
   - the interpreter is re-run under the problem metric;
   - `build_simulation_state` (`simulation_state.py:791`);
   - `build_scene3d` (`scene3d.py:380`);
   - `normalize_section_provenance`.
5. The visual obligation gate (`pipeline.py:840`).
6. `_envelope_tu_route_sinh` (`:702`) attaches `scene3d` and sets `domain="geometry"`.

On the frontend: `analyzeViaServer` → `docPhanHoiPhanTich` (`llm/client.ts:65-91`) → `store.loadEnvelope` (`state/store.ts:263`) → `SimulationWorkspace.tsx:519-546`. When `hopLeScene3D(scene3d)` passes, the workspace renders `<Scene3DExplorer scene=… hybrid={hybridViewCua(env)}>`. **This is the only route wired into the product by default.**

**Route D hybrid preview: operator-only.** `POST /api/preview/hybrid` (`main.py:1015`):
- returns 404 unless `HYBRID_ROUTE_D_PREVIEW=1`;
- returns 403 unless the caller is on loopback, sends no `Origin` header and supplies a token of at least 32 characters;
- otherwise calls `hybrid_preview.run_preview` (`:293`).

`run_preview` accepts **fixture JSON only** and passes it to `run_ai_fact_route`, then `adapt_result` (`:238`). `adapt_result` re-validates the scene and metric, builds `compile_semantic_program_to_envelope` and runs the proof-text guard (`:283`).
No frontend caller exists, because any browser request carries `Origin` and is refused. The response uses no cache.

**Adapter /3: offline research only.** `run_typed_fact_next_route` (`adapter3_simulation.py:3277`) and `build_adapter3_simulation_response` (`:3301`) have **no caller in `backend/app` or `frontend/src`**. They are reached only from 11 backend test files, for example `test_typedfact_next_adapter3.py` and `test_wave3a_adapter3_integration.py`.
Adapter /3 runs its own 2.4k-line orchestrator, `_Adapter3Compiler` (`:230`). That orchestrator wraps the engine's `_Dung`, emits IR, validates it, calls `hoan_thien_dung_hinh`, runs the interpreter, and then calls the same `build_simulation_state` + `build_scene3d` (`:3203-3221`; the curved path is at `:2816-2843`).
The frontend type `routeDSimulation` (`Scene3DExplorer.tsx:224`) is passed only in `simulation-learning-ux-session2.test.tsx:61`. **Adapter /3 has no product UI.**

**Adapter /4: Hybrid V2, local opt-in.** `/api/analyze` takes this path only when the server sets `HYBRID_V2_LOCAL=offline-replay` and the client is on loopback (`main.py:1059-1069, 1150-1151`). The chain is:
- `_analyze_hybrid_v2_local` → `hybrid_offline.run_local_replay` (`:164`), which reads a replay corpus with no live model;
- `run_hybrid_offline` → `run_typed_fact_next_v2_route` (`adapter4_route.py:36`);
- `bridge_v2` → `function_route.chay_sau_cau_noi` (`:493`) → `run_fact_route` (`:437`), which runs planner `lap_ke_hoach`, then `run_function_route` (`:373`), then `engine.dung_tu_loi_goi` (`engine.py:1993`). That function runs Source Gate → `_Dung` → IR → `hoan_thien_dung_hinh` → interpreter → self-checks;
- `build_simulation_state` + `build_scene3d`, followed by post-patches in function_route;
- `build_adapter4_response` (`adapter4_route.py:102`), which re-validates and builds the envelope.

The frontend recognises the /4 response through `docPhanHoiHybrid` (`client.ts:77-90`) and renders it in **the same Scene3DExplorer**. This path does not use the cache (`main.py:1147-1151`).

**Summary.**

| Route | Status |
|---|---|
| B | Product |
| /4 | Product UI, but only on a local, loopback-gated, offline-replay switch |
| Preview D | Operator HTTP only |
| /3 | Tests only |

All four routes converge on **one** scene builder (`simulation_state.build_simulation_state` + `scene3d.build_scene3d`) and **one** renderer.

## 2. From plan to construction steps, and whether construction is truly incremental

The chain of data structures is a 1:1 chain from the trace:

1. `SemanticTraceStep` (`interpreter.py:108`; fields `step_index`, `action`, `target`, `details`, `tier1_narration`, `semantic_kind`).
2. `build_timeline` (`simulation_state.py:709-738`) makes one entry per trace step.
3. `build_scene_events` (`scene3d.py:512-562`) makes one `event` per step, with `action` INIT/CREATE/EXTEND/MEASURE, `object`, `depends`, `semantic_kind`, `learner_text` and `details`.
4. `_ke_lai` (`scene3d.py:828-890`) rewrites text and kind but never adds or removes steps.
5. `_build_formation` (`scene3d.py:893-978`) produces `formation.steps[k]`, each with `visible_ids`, `focus_ids`, `readout_ids`, `learner_text`, `semantic_kind`, `geometry_progress` (section edges revealed so far, `closed`, `fill_visible`) and `formation_roles`.

Scene objects carry `producer`, `depends`, `dependency_edges`, `origin`, `formation_roles`, `parent` and `display_group` (`scene3d.py:405-470`).

The teaching order is decided before execution:
- `formation.hoan_thien_dung_hinh` inserts teaching steps;
- `engine.thu_tu_su_pham` (`engine.py:171`) splits point blocks topologically.

**Verdict: construction is genuinely incremental at the level of visibility.** Objects keep their final exact coordinates, which is safe because construction is monotonic and deterministic. Each step k exposes only `visible_ids` = the free objects plus every focus object seen up to step k.
- `objectsAt` (`scene3d-model.ts:646-666`) filters `scene.objects` by `formation.steps[k].visible_ids`.
- Section polygons grow edge by edge (EXTEND events, `geometry_progress`).
- One caveat: the **last** step force-shows every object (`scene3d.py:970-977`). Topology objects without an event therefore appear only at the end.

There are two step layers, and both are partitions of the trace:
- **Backend:** one frame and one event per trace step (#31).
- **Frontend:** `geometryTimeline` (`scene3d-model.ts:1593-1617`) groups events into *construction steps*. A new step opens only on a `GEOMETRY_CONSTRUCTION` event whose figure signature changes (`_chuKyHinh` `:1582`). MEASUREMENT and FINAL_RESULT events join the open step (#35). The step's anchor is its last event.

There is also a separate 2D frame axis, `envelope.config.frames`. It is built from `VisualTraceAdapter(spec).adapt(trace)` + `pace()` in `pipeline_adapter.compile_semantic_program_to_envelope` (`pipeline_adapter.py:139-177`). Scene3DExplorer **does not read it**.

**Where #31 (`frame k ⇔ trace[k]`) is enforced:**
- `pipeline_adapter.py:153` (frames = adapt(trace)) and `validate_semantic_envelope_config` (`:90-137`, partition check);
- `pacer.py` (#32);
- `build_timeline` / `build_scene_events` (1:1 by construction);
- tests: `backend/tests/semantic_program/test_frame_state_invariant.py`, `test_pacer_partition.py`, `test_binding_fail_closed.py`; frontend `scene3d-geometry-timeline.test.tsx`.

**Gap:** no test asserts `len(scene3d.events) == len(formation.steps) == len(config.frames)` across routes. A grep for an `events`/`frames` length equality returned nothing. (**UNVERIFIED** whether an indirect assertion exists inside `test_scene3d.py`.)

The frontend's own step state lives in `InteractionState.current_step` (`Scene3DExplorer.tsx:232, 324`). The store's `goToStep`/`nextStep` (`store.ts:163-169`) are **not used** by the 3D path.

## 3. Justification and certificates compared with explanation text

**Where certified data exists:**
- **Perpendicular witnesses.** On Route B, `quantity_annotations.py:88-180` attaches an exact Gram certificate on the segment with `can_present_as_proven: True`. On Route D/3/4, `geometry_functions/certificates.py:525-612` attaches it and `verify_perpendicular_witness` (`:353`) checks it. The frontend re-checks every witness fail-closed before drawing a right-angle mark (`scene3d-witness-gate.ts:26-60`, used from `scene3d-annotations.ts:156-190`).
- **Engine self-checks** (Route D, `engine.py:2066-2125`): volume, volume-ratio and residual-volume certificates, area, angle and distance values by independent Gram formulas, kernel coordinates equal to the layout, and section closure `kiem_chung_chi_thiet_dien`. These produce `section_certificates` (`plane-section-certificate/1`).
- **Adapter /4 re-verification** (`adapter4_route.py:126-217`): answers, intermediate quantities and points against `final_memory`, sections (`_validate_sections`), quote-in-source, and planner observations (which must be `UNVERIFIABLE` and `can_present_as_proven=False`).
- **Adapter /3:** `verified_relations` and `math_goals[*].certificate` (`adapter3_simulation.py:2730-2800`, `3256-3266`).
- **Route B gates:** the grounding, coverage, postcondition, assumption (C0/C1) and visual obligation gates.

**Where student-facing text is generated.** There are five layers, all string templates and none tied to a certificate:
1. **Interpreter `tier1_narration`.** Assignments are at `interpreter.py:221-262` ("Tính {label}: val", "Ghi nhận …"); constructions are in `geometry_exec.py:608-905` ("Dựng điểm X = (x,y,z)", "Dựng {label}").
2. **`scene3d._learner_text`** (`scene3d.py:584-609`) filters snake_case only; it falls back to "Dựng {label}".
3. **`scene3d._ke_lai`** (`:828-890`) rewrites from structured scene data: givens, sections, measurement formulas, FINAL_RESULT, and "Gọi (α) là …".
4. **Route-specific post-patches:**
   - `function_route._ke_diem_dung` (`function_route.py:91-112`) writes producer-based text such as "Dựng M là trung điểm của đoạn AB". **It runs on Route D/3/4 only, not Route B.**
   - `_gan_nhan_chung_*`, `_dich_khoang_cach_diem_duong`, `_vai_mat_cat`, plus a line-construction relabel (`:399-407`).
   - Adapter /3 has regex `_clean_curved_text` (`adapter3_simulation.py:2821-2867`), which rewrites labels, events and step text.
5. **Frontend fallback** `narrationGoc` (`scene3d-model.ts:707-718`), re-gated by `learnerTextIsSafe` (`:721`), with the same "Dựng X." templates.

**Can text claim more than is certified?**
- **Route B.** IR statement `label`s are LLM-authored and reach the narration:
  - `geometry_exec.py:683-684`: segments, "Dựng {label}";
  - `:784-789`: polygons; a label starting with "dựng " is passed **verbatim**;
  - `interpreter.py:253-256`: "Tính {label}: val".

  `_ke_lai` overwrites CREATE, section and quantity events. The `else: _sua_cau(...)` branch (`scene3d.py:889-890`) and EXTEND/STEP actions keep the original text. The only filter checks for identifier leakage (`_learner_text`, `learnerTextIsSafe`). **No claim-word guard exists on Route B**, so an LLM label such as "dựng SH ⊥ (ABC)" could reach the student without a witness.
- **Route D preview and /4.** These do have a guard: `_noi_chung_minh` rejects any "chứng minh" wording in title, frames, events and steps (`hybrid_preview.py:279-284`, `adapter4_route.py:211-216`). It is a word guard only. It does not tie a relational claim ("vuông góc", "song song", "trung điểm") to a certificate.
- **Divergence points between scene and text:**
  - (a) `_clean_curved_text` regex edits labels after the scene is built (Adapter /3).
  - (b) Function_route patches mutate both `events[i]` and `formation.steps[step_index]`. The index alignment is assumed, not asserted (`function_route.py:112, 406`).
  - (c) The last-step force-show (`scene3d.py:970`) makes objects appear with no narrating step.
  - (d) The `formation_budget` fallback silently drops the teaching expansion when the IR budget is exceeded. It is recorded only in the trace (`engine.py:2047-2053`; Adapter /3 `:3155-3162`). The student sees fewer steps and is not told.
  - (e) Certificates are never attached **per step**. The Analysis panel (`phanTichToanHocCuaCanh`, `scene3d-model.ts:1947`; `Scene3DExplorer.tsx:773-822`) is a whole-scene static list.

## 4. Frontend step navigation today

`Scene3DPlayer` (`scene3d-playback.tsx:110-388`) provides:
- **Bước trước** (previous) and **Bước sau** (next), disabled at the ends;
- **Phát/Tạm dừng** (play/pause) on a 1400 ms interval (`PLAYBACK_INTERVAL_MS`, `scene3d-model.ts:1509`); the button becomes **Xem lại** (replay from step 0, clearing the selection) at the end;
- a range scrubber with "Bước n/N", which is keyboard-operable as a native slider;
- the **«Các bước dựng»** floating panel: a list that groups auxiliary-only runs with `<details>` (`scene3d-auxiliary.ts:112`) and shows the current step's narration inline (`:255-263`);
- an auto-scroll of the active item.

The Explorer adds:
- a "Xem lại toàn hình" jump to the end (`Scene3DExplorer.tsx:546`);
- step highlighting via `geometryHighlightedAt` (none at the last step);
- a causal or dependency highlight on selection (`interaction-state.ts:174-226`);
- hide, isolate and explode controls;
- X-ray;
- an auxiliary toggle (`auxiliaryHiddenAt` hides auxiliary objects after their step ends unless they are selected or the toggle is on);
- hidden-edge dashing (`scene3d-edge-visibility.ts:194`, `LineDashedMaterial` in `scene3d-view.tsx`);
- certified right-angle marks;
- hybrid observations gated by step (`hybridTaiBuoc`, `hybrid-preview-adapter.ts:345`).

Reduced-motion users get no Play or Replay button (`scene3d-playback.tsx:293`).

**Missing:**
- global keyboard shortcuts (←/→/Space/Home/End): there are no step key handlers, and the only keydown handlers are Escape and menus;
- a "why this step" justification line;
- a per-step certificate badge;
- a "new in this step" diff list or legend: focus is highlighted, but nothing names what appeared;
- a playback speed control: the store has `setSpeedMs`, but Scene3D ignores it;
- any notice when the teaching expansion was skipped.

`solutionAt` / `quantityChoices` feed only the quantities panel. The docs cite `scene3d-solution.tsx`, **which does not exist**, so the docs are stale.

**By route:**
- **/4 (Hybrid V2)** gets the same player, with richer producer-based point narration and observations.
- **Route B** lacks the `_ke_diem_dung` narration.
- **Adapter /3** has **no UI path at all**: its `math_goals` and `verified_relations` certificates reach only the test-only `routeDSimulation` prop.
- **Preview D** has no UI.

## 5. Determinism, replay and cache

**Deterministic and independently checkable:**
- Everything after the IR: validator, `hoan_thien_dung_hinh`, interpreter, kernel (exact ℚ plus radicals), `build_simulation_state`, `build_scene3d`. `_dung_scene3d` re-runs the interpreter to recover the trace (`pipeline.py:600-606`).
- On Route D, everything after extraction (Source Gate, planner, engine) is deterministic as well.
- Independent oracles: `docs/evaluation/geometry/custodian/geometry_oracle.py`, and the step-math oracle under `docs/evaluation/geometry/runs/step-math-validation/`, which is locked by `backend/tests/geometry/test_step_math_validation.py`. The frontend witness gate re-checks witnesses.

**Not deterministic:** the LLM stages (Route B analyze and program; Route D extraction, which is replay/fixture only here).

**Cache:**
- Only the `/api/analyze` default path is cached. The key is the sha256 of the normalised text (`main.py:902`). `policy_version` is `CACHE_VERSION` ("130", `main.py:841`), plus a route fingerprint when the mode is not the default (`_policy_identity` `:906-915`). Only `status=="ok"` results are written (`:1225-1265`).
- Preview D raises an error if it would touch the cache (`:912-913`). Hybrid V2 local skips the cache (`:1147`). Image extraction keys on `cache_version=CACHE_VERSION` (`:1306`).
- **Consequence:** any change to scene or narration text (`scene3d.py`, `simulation_state.py`, `_ke_lai`) leaves old cached Route-B envelopes stale. Precedent tests exist: `test_cache_display_identity_invalidation.py`, `test_cache_right_angle_witness_invalidation.py`, `test_cache_segment_witness_invalidation.py`. A bump decision is needed per change.

## 6. Duplication and coupling

1. **Five explanation layers** (§3), with duplicated templates and guards: `scene3d._learner_text` ↔ `scene3d-model.narrationGoc`/`learnerTextIsSafe`.
2. **Route-specific scene patching outside the builder:**
   - `function_route.py:25-370` (`_ke_diem_dung`, `_gan_nhan_chung_hinh_chieu`, `_gan_nhan_chung_duong_cao_chinh_xac`, `_dich_khoang_cach_diem_duong`, `_an_dinh_thiet_dien_phu`, `_vai_mat_cat`);
   - these are imported into `adapter3_simulation.py:82`, so the AI layer depends on itself;
   - the Adapter /3 regex text cleaner.
3. **Adapter /3 duplicates engine work:** `_Adapter3Compiler` (2.4k lines) re-implements the orchestration and copies the self-checks (volume certificate and `kernel_ok`, `adapter3_simulation.py:3184-3200` vs `engine.py:2081-2101`). It is a second orchestrator next to planner + `dung_tu_loi_goi`.
4. **Two step axes per envelope:** `config.frames` (visual_adapter + pacer) and `scene3d.events` + `formation.steps`, both from the trace. 3D uses only the latter. The store timeline actions are dead for 3D.
5. **Duplicated scene/answer validation:** `hybrid_preview.adapt_result` and `adapter4_route.build_adapter4_response` both do metric, length-unit and proof-text checks plus `compile_semantic_program_to_envelope`.
6. **Good news:** a single scene builder, a single renderer and a single kernel. No second renderer or planner is needed.

## 7. Ranked improvements (at most 8): low risk, reuse only

1. **Producer-based step narration on every route.**
   - Change: move `function_route._ke_diem_dung` (and the line-relabel at `:399-407`) into `scene3d._ke_lai`, keyed on `producer` + `depends` notation, which `build_scene3d` already has. Route B then gains "Dựng M là trung điểm của đoạn AB"; Route D behaviour stays the same.
   - Files: `semantic_program/scene3d.py`, `ai/function_route.py` (delete the patch), `ai/adapter3_simulation.py` (drop the import).
   - Cost: a CACHE_VERSION bump with evidence (Route B envelopes change) and a re-freeze of the candidate, since `backend/app` is a measured path.
   - Locks: `tests/geometry/test_scene3d.py`, `test_scene3d_learner_surface.py`, `test_pedagogical_sequencing.py`, `test_point_line_distance_presentation.py`, `tests/test_api.py` (cache assert), `test_cache_display_identity_invalidation.py`.
2. **Per-step certificate references (data only).**
   - Change: in `_build_formation`, add `formation.steps[k].certificate_ids`, the focus objects that carry `perpendicular_witness` with `can_present_as_proven`, or section `closure_certificate` / `section_certificates`.
   - Frontend: show a small "đã kiểm chứng" badge plus the witness rule in the step panel, read only after the existing witness gate passes.
   - Files: `scene3d.py`, `scene3d-model.ts` (`FormationStep`), `scene3d-playback.tsx`.
   - Locks: `test_scene3d.py`, `test_scene3d_ts_sync.py`, `test_adapter4_plane_section_certificate.py`, `scene3d-right-angle-witness.test.ts`, `scene3d-steps-panel.test.tsx`.
3. **Claim-word guard tied to certificates, on every route.**
   - Change: generalise `hybrid_preview._noi_chung_minh` into a shared check in the scene layer. A step text containing relational claims ("vuông góc", "⊥", "song song", "trung điểm") must have a matching certified producer or witness on its focus objects; otherwise fall back to "Dựng {notation}".
   - This closes the Route B gap where LLM labels pass verbatim (`geometry_exec.py:784-789`, `scene3d.py:889-890`).
   - Files: `scene3d.py` (`_learner_text`), `hybrid_preview.py`/`adapter4_route.py` (reuse).
   - Locks: `test_scene3d_learner_surface.py`, `tests/test_hybrid_preview_contract.py`, `test_learner_surface_3d.py`. Needs a CACHE_VERSION decision.
4. **Keyboard step navigation.** Bind ←/→, Home/End and Space on the player group (`role="group"`), scoped to focus inside `.geo3d-player`, reusing `prevGeometryStep`/`nextGeometryStep`/`anchorOfGeometryStep`. Files: `scene3d-playback.tsx`. Locks: `scene3d-playback.test.tsx`, `Scene3DExplorer.test.tsx` (it already source-scans `addEventListener("keydown"`), `scene3d-page.test.tsx`. No backend or cache impact.
5. **"New in this step" line.** Show the difference of `formation.steps[anchor].visible_ids` against the previous anchor, mapped to `notation`/`reference`, under the current step's narration in «Các bước dựng». This is pure derivation from existing snapshots. Files: `scene3d-model.ts` (helper next to `geometryHighlightedAt`), `scene3d-playback.tsx`. Locks: `scene3d-geometry-timeline.test.tsx`, `scene3d-steps-panel.test.tsx`, `scene3d-learner-formation.test.ts`.
6. **Disclose a skipped teaching expansion.**
   - Change: when the trace carries `formation_budget` (`engine.py:2050`, Adapter /3 `:3160`), set a scene flag (for example `formation_expansion_skipped`). The player then shows a one-line notice instead of silently showing fewer steps.
   - Files: `ai/function_route.py`/`adapter4_route.py` (copy the flag onto the scene), `scene3d-model.ts`, `scene3d-playback.tsx`.
   - Locks: `test_formation_plan_parity.py`, `adapter4-consumer.test.tsx`.
7. **Cross-route invariant test.** Assert `len(events) == len(formation.steps)`, that `events[k].step_index == k`, and (for Route B / Adapter /4 envelopes) `== len(config.frames)`. This protects the index-aligned patches (`function_route.py:112, 406`). It adds a test only, in `tests/semantic_program/test_frame_state_invariant.py` and `tests/geometry/test_hybrid_contract_v2.py`.
8. **Remove the last-step force-show surprise.** Give topology-only objects a visible step with the parent solid's CREATE event, through the `parent` field already computed by `_cha` (`scene3d.py:310`), instead of revealing them all at `steps[-1]` (`:970-977`). Files: `scene3d.py`. Locks: `test_scene3d.py`, `test_scene3d_construction_audit.py`, `scene3d-subentities.test.ts`. Needs a cache decision.

**Explicitly not recommended:**
- giving Adapter /3 a product path (it duplicates the engine; /4 already covers it);
- a second timeline or step model;
- reviving `config.frames` for 3D;
- drag-style ("GeoGebra") manipulation, which is out of scope under #31.
