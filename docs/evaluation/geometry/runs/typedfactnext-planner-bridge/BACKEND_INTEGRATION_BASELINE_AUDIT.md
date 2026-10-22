# BACKEND_INTEGRATION_BASELINE_AUDIT — P0

Run `typedfactnext-planner-bridge` · 2026-10-22 · LOCAL ONLY · `ALLOW_LIVE_AI=0` · 0 provider calls.

## 1. Git state verified (not assumed)

| item | verified value |
|---|---|
| `main` = `origin/main` | `43247c9e9375a3dbf2b5223324a58e6f932ca596` (the reported baseline is still HEAD of `main`) |
| remote | `origin https://github.com/nomozer/algo-sim.git` |
| root checkout | `research/hybrid-wave3a-volume-reasoning` at `fe9f555437498432427ae6bbd54402cdd59c7eb7`; untracked only (6 `*-go-main` run folders, one T3 log, `frontend/public/`) — untouched |
| campaign worktree | `.superpowers/worktrees/hybrid-backend-s1`, branch `research/hybrid-backend-integration-session1`, created from `43247c9e`, clean at creation |
| governance in source | `CACHE_VERSION = "127"` (`backend/app/main.py`), `CHE_DO_MAC_DINH = "LLM_ONLY"` (`geometry_compiler/routing.py`), `response_contract = "flat"` (`ai/pipeline.py`) |

## 2. Research branches requested in the brief

| branch | exists | relation to `main` | content |
|---|---|---|---|
| `research/hybrid-wave3a-volume-reasoning` | yes (`fe9f5554`) | **ancestor of `main`** (0 ahead / 32 behind) — fully merged | Wave 3A volume ratio / residual volume |
| `research/typedfact-next-adapter3-simulation` | **no** (no local or remote ref) | its work is on `main`: `typed_fact_next.py`, `adapter3_simulation.py`, run `typedfact-next-adapter3-simulation`, run `wave3a-adapter3-integration` | TypedFactNext + Adapter /3 |
| `research/hybrid-source-gate-followup-ab` | **no** | its head commit `68acc140` **is an ancestor of `main`**; run `source-gate-followup-ab` on `main` | SGH-02/04/09/10 follow-up |
| `research/nl-to-scene3d-e2e-readiness` | yes (`25f57e31`) | 1 commit ahead of `main`, 0 behind; **docs/eval only** (97 files, corpora, harness, gap matrix) | E2E readiness audit, `E2E_CAPABILITY_GAP_MATRIX.md` |
| `research/hybrid-next-architecture-gap-audit` | yes (`4f1d1a48`) | 1 ahead, 163 behind; docs + offline POCs | gap audit |
| `research/hybrid-semantic-extraction-v2` | yes (`dc27009f`) | 14 ahead, 270 behind; touches `fact_extraction.py`, `registry.py` | extraction v2 pilot (owner disposition recorded; not integrated) |
| `research/hybrid-route-d-preview-wiring` | yes (`65d6ee97`) | ancestor of `main` | preview wiring |

No cherry-pick or merge was performed. Nothing in this campaign depends on an unmerged branch; the dev corpus of `nl-to-scene3d-e2e-readiness` was read with `git show` as reference input only (its sealed holdout was **not** read for development).

## 3. Component location on `main` (`43247c9e`)

| component | module | in production `/api/analyze`? |
|---|---|---|
| Production `LLM_ONLY` → SemanticProgram → Scene3D | `ai/pipeline.py`, `simulation/semantic_program/*` | **yes** (only route) |
| Direct function calling (route D-A) | `ai/function_calling.py` → `ai/function_route.run_function_route` | no |
| TypedFact → Source Gate → Planner → Engine (route D-B) | `ai/fact_extraction.py`, `geometry_functions/planner.py` (`geometry-fact-planner/11`), `registry.py` (`geometry-functions/11`, `kiem_nguon`), `engine.py` (`geometry-function-engine/9`), `ai/function_route.run_fact_route` | no |
| TypedFactNext → Adapter /3 → Scene3D | `geometry_functions/typed_fact_next.py` (`typed-fact-next/1`), `ai/adapter3_simulation.py` (`hybrid-simulation-adapter/3`) | no |
| Operator preview | `ai/hybrid_preview.py` behind `POST /api/preview/hybrid` (404 unless `HYBRID_ROUTE_D_PREVIEW=1`, token ≥ 32, loopback, no `Origin`) | no (`/api/analyze` never requests it) |

`ai/pipeline.py` and `main.py` import `hybrid_preview` only behind the preview flag; no production path imports `planner`, `registry.kiem_nguon`, `adapter3_simulation` or `typed_fact_next`. Frozen provider fingerprints are locked in `test_wave3a_volume_reasoning.py`, `test_schema_contract_v3.py`, `test_contract_driven_goal_composition.py`, `test_function_discovery_planning.py`, `test_goal_directed_function_composition.py`, `test_hybrid_backend_integration.py`.

## 4. Fragmentation found in code (not in documents)

1. **Two fact-to-call mappers.** `planner._anh_xa` maps each `TypedFact` to a Registry call; `adapter3_simulation._Adapter3Compiler._compile_premises` maps each `PremiseSpec` kind to the same Registry functions by a second hand-written `if/elif` table (~20 kinds).
2. **Two copies of the three plane decompositions.** `planner._mat_qua_diem` / `_mat_vuong_duong` and `adapter3._compile_derived_sections` both write `translate_point` (+ `orthogonal_projection_line`) + `section` for `MAT_SONG_SONG`, `MAT_HAI_DUONG`, `MAT_VUONG_DUONG`, with different anchor choices and label stems (`H…` vs `X…`/`F…`).
3. **Two source-grounding authorities.** Route D-B runs `kiem_nguon` (closed grammar, clause roles, premise coverage, number ownership) and `kiem_mat_viet` / `kiem_mo_ta` in `engine.dung_tu_loi_goi`. Adapter /3 builds `_Dung` directly and checks only quote substrings and numbers inside quotes (`_verify_quote_in_problem`, `_verify_number_in_quote`); it never calls `kiem_nguon`.
4. **Planner capability that Adapter /3 has and the planner lacks:** unnamed section vertices on lateral edges and a derived sub-solid over a derived section (Adapter /3 writes one `intersect_line_plane` per edge with fresh `I…` labels, then folds them).

## 5. Reported defects re-checked on `43247c9e`

| defect (as reported) | reproduced? | actual root cause on current code |
|---|---|---|
| `divide_segment` + `1/3` ⇒ `SOURCE_PREMISE_UNREAD` (dev case `DEV-F2-02`) | **yes** — `REFUSED SOURCE_PREMISE_UNREAD: giá trị trong tiền đề 'Điểm M thuộc cạnh SA sao cho SM = 1/3 SA.' không nằm trong quote của lời gọi mang giá trị ấy` | `registry._kiem_vung_tien_de` credits a premise number only through a call's `value_fields`; `divide_segment` declares none, and listing `ratio` alone would be wrong because the stated number need not equal t (SM = 2MA ⇒ text 2, t = 2/3) |
| `hybrid_preview` reports `PREVIEW_DEPENDENCY_INVALID` "because `depends` holds fact IDs" | **yes, but the stated cause is wrong** — on the midpoint variant of `DEV-F2-02` (route B SERVED, ratio 1/8, residual 7a³√3/8) no object's `depends` names a non-object id | `hybrid_preview._validate_scene` reads birth steps from `event["object"]` only. The sub-solid's lateral edges `canh_ben_S_M/N/P` are born at step 8 inside a **group event's `objects` list**, after M (4), N (5), P (6); the scene and the frontend (`objectsAt` reads `objects`) are correct, the validator misreads the timeline |

## 6. Stale claims in documents (not corrected in place; noted here)

- `E2E_CAPABILITY_GAP_MATRIX.md` (unmerged branch) states `research/hybrid-source-gate-followup-ab` (`68acc140`) is not integrated into `main`: false on `43247c9e`.
- The same matrix attributes the preview failure to fact IDs in `depends`: not reproduced; see §5.
- `docs/architecture/TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md` §1 says Adapter /3 runs through "Verified Geometry Functions & Bounded Planner": Adapter /3 does not call `planner.py` (see §4.1–4.2).

## 7. Constraints carried into the campaign

Backend + backend tests + architecture docs only; no frontend/CSS/renderer. `LLM_ONLY`, `flat`, Hybrid NO-GO, `ALLOW_LIVE_AI=0`, `CACHE_VERSION=127`. Frozen provider surfaces (`TypedFact.model_json_schema`, `fact_extraction.surface_fingerprint("flat"|"v3")`, `function_calling.surface_fingerprint`, `registry.function_declarations`) must stay byte-identical. Sealed holdouts are not development data. CPU: focused sequential pytest only; Full T3 once, on the frozen candidate, only if product code changed.
