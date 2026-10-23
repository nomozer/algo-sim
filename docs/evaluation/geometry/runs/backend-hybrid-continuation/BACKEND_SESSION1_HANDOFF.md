# BACKEND HYBRID ARCHITECTURE INTEGRATION — SESSION 1 CONTINUATION HANDOFF

- **Campaign:** `BACKEND HYBRID ARCHITECTURE INTEGRATION` (Session 1: Claude Opus 5.5 → Codex → Gemini 4 Argon takeover)
- **Authorization:** `GO_BACKEND_HYBRID_LOCAL_CONTINUATION_ONLY` (local research continuation only; no merge to `main`, no push, `ALLOW_LIVE_AI = 0`, `DEFAULT_MODE = LLM_ONLY`, `RESPONSE_CONTRACT = flat`, `CACHE_VERSION = 127`)
- **Active Branch:** `research/hybrid-backend-integration-session1`
- **Active Campaign Worktree:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\hybrid-backend-s1`
- **Detached Verification Worktrees (preserved intact):**
  - `D:\Documents\projects\algo-sim\.superpowers\worktrees\s1-freeze` at `404f0568a00651505ec0773754a04ef5c493f5f9` (Claude's T3 Attempt 1 worktree)
  - `D:\Documents\projects\algo-sim\.superpowers\worktrees\hybrid-backend-continuation-verify` at `76a7ce33cc955a1e4a2e01d4d5374493c843d86c` (Authoritative Full T3 Attempt 3 worktree)
- **Session 1 Disposition:** `BACKEND_HYBRID_INTEGRATION_READY_FOR_OWNER_REVIEW`

---

## 1. Exact Git Commit Chain (`research/hybrid-backend-integration-session1`)

| Role / Stage | Full 40-char Git SHA | Description |
|---|---|---|
| Baseline (`origin/main` merge-base) | `43247c9e9375a3dbf2b5223324a58e6f932ca596` | Starting point of `research/hybrid-backend-integration-session1` |
| Claude Product Commit | `8b5916e7309a8939f0c462367120360391ccb70c` | `feat(geometry): bridge TypedFactNext into the fact planner with cut-edge section vertices` (`16` files, `+1539 / -47`) |
| Claude Evaluation & Reviews 1–4 | `9c3cdf7ccce11296aaf7fc7ffee05cdbf0efef47` | `eval(geometry): record TypedFactNext planner bridge evaluation, gate report and review rounds 1-4` |
| Claude Candidate Freeze 1 | `a0c85b4dfb386b35115341ced4c608a9e3ddaa20` | `chore(eval): freeze evaluation candidate for typedfactnext-planner-bridge` (`2711d78e401234a2bea98a983d94fe1b29973b4482b407c5529307e38f67b16d`, `115` files) |
| Claude Benchmark Taxonomy & T3 Target 1 | `404f0568a00651505ec0773754a04ef5c493f5f9` | `test(geometry): classify typedfactnext-planner-bridge refusal codes in the benchmark taxonomy` |
| Codex Bridge Safety Fix 1 | `ac719a5b597b4899c8ef1e159ca595e99d962a6c` | `fix(geometry): preserve TypedFactNext bridge constraints and fail closed on malformed operands` |
| Codex Bridge Safety Fix 2 (Product) | `4f3aaea5e0d3b5c1fe1537bd3ddf4bc73cbe88ee` | `fix(geometry): bind bridge plane identity to source-gated engine output` (`404f0568..4f3aaea5`: `4` files, `+109` lines) |
| Codex Candidate Freeze 2 & T3 Target 2 | `4fb1045f40a326f9d23e2fdad9fcd5b2290697f2` | `docs(eval): preserve takeover evidence, correct candidate chain and freeze reviewed backend` (`22c4fc6de9350cfee55d3eb4a4b3497410214ba39ac18c2f9a5db4384631ef51`, `115` files) |
| Gemini Takeover Product Commit (Final Product) | `b6684564ac4596da30819da5fcc4c875ebb1a640` | `fix(geometry): classify bridge refusal codes in preview contract and benchmark taxonomy` (`2` files, `+3 / -1`) |
| Gemini Candidate Freeze 3 & Authoritative T3 Target 3 | `76a7ce33cc955a1e4a2e01d4d5374493c843d86c` | `chore(eval): record Gemini takeover checkpoint, taxonomy divergence layer and freeze candidate b6684564` (`13fd32b498ea9e47f23f01d0f4efc99b7f8d789ed6e59fe814c8fc4891d7e172`, `115` files) |

---

## 2. Summary of Contributions by Agent

### 2.1 Claude Opus 5.5 (`8b5916e7` .. `404f0568`)
- Implemented `backend/app/simulation/geometry_functions/typed_fact_next_bridge.py` and `run_typed_fact_next_planner_route` in `backend/app/ai/function_route.py`, translating authored `typed-fact-next/1` polyhedral payloads into `TypedFact` for the existing `planner.lap_ke_hoach` → `registry.kiem_nguon` → `engine.dung_tu_loi_goi` pipeline.
- Added cost-ranked section-vertex resolution (`_dinh_cat_canh`, `SectionVertex` need) and derived-pyramid registration (`_khoi_tren_thiet_dien`, `derived_pyramid` construct, `DINH_CAT_CANH` planner certificate) in `planner.py`, `registry.py`, and `engine.py`, enabling Wave 3A `ask_volume_ratio` and `ask_residual_volume` to compose directly on planner-derived pyramids.
- Fixed `DEV-F2-02` (`divide_segment` ratio span ownership `_ty_so_khop` and optional `"là … điểm"` in `_CUM_DINH_NGHIA_DIEM` in `registry.py`) and `HOLD-F2-01` (`_validate_scene` in `hybrid_preview.py` reading object births from both `event["object"]` and `event["objects"]` for group events).
- Authored 54 unit/integration tests in `backend/tests/geometry/test_typedfactnext_planner_bridge.py` and the 60-case offline development evaluation (`docs/evaluation/geometry/runs/typedfactnext-planner-bridge/`), plus 4 rounds of independent review fixes.
- Ran Full T3 Attempt 1 at `404f0568a00651505ec0773754a04ef5c493f5f9` in `s1-freeze`, which failed `1` test (`test_C2b_candidate_hien_tai_phai_duoc_KHAI`, `KeyError: 'run_candidate_hash'`).

### 2.2 Codex (`ac719a5b` .. `4fb1045f`)
- Diagnosed and corrected the `C2b` candidate divergence chain (`docs/evaluation/geometry/runs/backend-hybrid-continuation/candidate_divergence.json` and `backend-hybrid-bridge-safety/candidate_divergence.json`) by restoring `run_id` and `run_candidate_hash`.
- Conducted an independent review (`/root/independent_backend_review`) of Claude's bridge and fixed 4 IMPORTANT boundary defects across `4` files (`+109` lines in `404f0568..4f3aaea5`):
  1. Validated solid-qualified vertex namespaces (`sid::label`) against declared `solids[sid].local_vertices()` (`UNKNOWN_SOLID_ID`, `UNKNOWN_VERTEX_REF`, `QUALIFIED_LABEL_COLLISION`) and validated `named_intersections` edge keys (`INVALID_INTERSECTION_EDGE`).
  2. Preserved explicit `length_unit` on `TypedFactNextPayload`, refusing `NON_HOMOGENEOUS_LENGTHS` when `"1"` conflicts with symbolic `"a"` facts and `BRIDGE_UNSUPPORTED_LENGTH_UNIT` when `"a"` is declared with numeric-only facts.
  3. Wrapped open `PremiseSpec.args` extraction in `typed_fact_next_bridge.py` and `function_route.py` so missing keys or non-string/non-list vertex references fail closed as `INVALID_TYPED_FACT_NEXT` instead of raising `KeyError`/`TypeError`.
  4. Bound declared `DerivedPlaneSectionSpec.plane_name` to the Source Gate verified scene plane `mp_td_{ir_name(section_id)}` (`display_label == f"({name})"`), refusing mismatched or spoofed plane names (`"β"`, `"ABC"`) with `SOURCE_OBJECT_MISMATCH`.
- Added 12 targeted boundary tests (`66` total in `test_typedfactnext_planner_bridge.py`), re-ran the 60-case offline replay (`planner-composition-final.json`), froze candidate `4fb1045f40a326f9d23e2fdad9fcd5b2290697f2`, and ran Full T3 Attempt 2 in `hybrid-backend-continuation-verify`.

### 2.3 Gemini 4 Argon (`b6684564` .. `76a7ce33`)
- Recovered the exact working tree, commit chain, and 25 untracked files in `GEMINI_TAKEOVER_CHECKPOINT.md` without modifying or deleting any historical artifacts.
- Inspected the raw `stdout.log` of Codex's Full T3 Attempt 2 (`verification/full-t3/stdout.log`) and identified all 3 failures:
  1. `test_every_refusal_code_of_the_route_is_classified` (`['INVALID_TYPED_FACT_NEXT', 'UNKNOWN_VERTEX_REF']` missing from `HB.REFUSAL_CLASS`).
  2. `test_every_literal_route_d_refusal_code_is_classified` (`['BRIDGE_UNSUPPORTED_LENGTH_UNIT', 'INVALID_TYPED_FACT_NEXT']` missing from `app/ai/hybrid_preview.py::_NHOM`).
  3. `test_runner_executes_both_real_adapters_with_separate_telemetry_and_resume[FULL_AB-288]` (`PilotStopped: PERSISTENCE_FAILED` caused by setting `PYTEST_DEBUG_TEMPROOT` inside `.superpowers\pt-22172` where Windows Defender / filesystem indexing momentarily locked `os.replace(runs.jsonl.tmp, runs.jsonl)`).
- Verified the semantic and mathematical validity of all refusal codes and committed `b6684564ac4596da30819da5fcc4c875ebb1a640` classifying `INVALID_TYPED_FACT_NEXT` and `UNKNOWN_VERTEX_REF` in `hybrid_compiler_benchmark.py` and `BRIDGE_UNSUPPORTED_LENGTH_UNIT` and `INVALID_TYPED_FACT_NEXT` in `hybrid_preview.py`.
- Ran Independent Review Round 2 (`a76efdda-c831-484e-b5f1-382bcf0cc943`, `INDEPENDENT_REVIEW_PASS`: `0` BLOCKER, `0` IMPORTANT).
- Re-froze `EVALUATION_CANDIDATE.json` (`tree_hash` = `13fd32b498ea9e47f23f01d0f4efc99b7f8d789ed6e59fe814c8fc4891d7e172`, `115` files) and added `backend-hybrid-taxonomy-completion/candidate_divergence.json` at commit `76a7ce33cc955a1e4a2e01d4d5374493c843d86c`.
- Executed Authoritative Full T3 Attempt 3 on clean detached `76a7ce33cc955a1e4a2e01d4d5374493c843d86c` (`FULL_PRODUCT_GATE_PASS`, exit code `0`, `539.14s`) and verified post-T3 candidate integrity (`freeze_evaluation_candidate.py --verify` = `MATCH`).

---

## 3. Full T3 Attempt History (All Receipts Preserved)

| Attempt | Target Commit SHA | Product Commit SHA | Measured System Hash (`115` files) | Result | Summary & Receipt Path |
|---:|---|---|---|---|---|
| Attempt 1 (Claude) | `404f0568a00651505ec0773754a04ef5c493f5f9` | `8b5916e7309a8939f0c462367120360391ccb70c` | `2711d78e401234a2bea98a983d94fe1b29973b4482b407c5529307e38f67b16d` | `FAIL` (exit `1`, `617.84s`) | Pytest `1 failed, 11492 passed` (`test_C2b_candidate_hien_tai_phai_duoc_KHAI` missing `run_candidate_hash`); Vitest `1156 passed`. Receipt: `../typedfactnext-planner-bridge/verification/t3-attempt1/execution.json` |
| Attempt 2 (Codex) | `4fb1045f40a326f9d23e2fdad9fcd5b2290697f2` | `4f3aaea5e0d3b5c1fe1537bd3ddf4bc73cbe88ee` | `22c4fc6de9350cfee55d3eb4a4b3497410214ba39ac18c2f9a5db4384631ef51` | `FAIL` (exit `1`, `559.31s`) | Pytest `3 failed, 11502 passed` (`test_every_refusal_code_of_the_route_is_classified`, `test_every_literal_route_d_refusal_code_is_classified`, `FULL_AB-288` temp-dir lock); Vitest `1156 passed`. Receipt: `verification/full-t3/execution.json` |
| **Attempt 3 (Gemini — Authoritative)** | `76a7ce33cc955a1e4a2e01d4d5374493c843d86c` | `b6684564ac4596da30819da5fcc4c875ebb1a640` | `13fd32b498ea9e47f23f01d0f4efc99b7f8d789ed6e59fe814c8fc4891d7e172` | **`FULL_PRODUCT_GATE_PASS`** (exit `0`, `539.14s`) | Pytest **`11505 passed, 1 skipped, 2 deselected, 9 xfailed`** (`0` failed, `515.4s`); Vitest **`72/72` files, `1156 passed`** (`14.9s`); Build **`PASS`** (`6.6s`); Demo **`5/5`** (`0.8s`); Crash **`6/6`** (`0.5s`); Post-T3 `--verify` **`MATCH`** (exit `0`, `1.97s`). Receipt: `verification/full-t3-attempt3/execution.json` & `verification/post-t3-freeze-verify/execution.json` |

---

## 4. Scientific Governance & Remaining Blockers Before Production Hybrid

- **Governance Invariants Preserved:**
  - `DEFAULT_MODE = "LLM_ONLY"` (`backend/app/simulation/geometry_compiler/routing.py`)
  - `semantic_route_mode() = "off"` (`backend/app/main.py`)
  - `RESPONSE_CONTRACT = "flat"` (`backend/app/ai/fact_extraction.py`)
  - `CACHE_VERSION = "127"` (`NO_BUMP`)
  - `ALLOW_LIVE_AI = 0` (`0` live provider calls)
  - All 5 provider surface fingerprints (`flat`, `v3`, `function_calling`, `TypedFact`, `function_declarations`) unchanged.
- **Remaining Blockers Before Replacing Legacy Backend Architecture (Out of Session 1 Scope):**
  1. `cut_edges` contract divergence between the planner bridge (source-stated cut edges) and Adapter /3 (complete section cycle without closure verification — `18` wrong serves on same-payload quadrilateral cuts when given bridge-style payloads).
  2. Split source-grounding authorities (`registry.kiem_nguon` closed grammar vs Adapter /3 substring checks, which served `3` invalid cases and crashed on `1` plane-equation case in the 60-case comparison).
  3. `IR_MEMORY_BUDGET_EXCEEDED` (`32` declarations) on `9/49` quadrilateral perpendicular-plane residual-volume plans.
  4. No live LLM extraction into `TypedFactNext` and no blind holdout E2E evaluation (`ALLOW_LIVE_AI = 0`).
  5. Separate owner `GO_MAIN` review required before any merge of `research/hybrid-backend-integration-session1` into `main`.
