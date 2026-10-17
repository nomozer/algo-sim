# Hybrid Backend Integration Candidate — Verification & Handoff Report (`P0`–`P8`)

- **Run Slug:** `hybrid-backend-integration`
- **Branch:** `research/hybrid-backend-integration`
- **Worktree:** `.superpowers/worktrees/hybrid-backend-integration`
- **Base `main` Commit:** `4abc4afbb976babc4740bf22e42dc368a24c1b13` (`4abc4afb`)
- **Product Commit SHA:** `7507312bbb16af5527ef7c7dba4f59c2a786cbd2` (`7507312b`)
- **Combined Product Hash (`measured_system.tree_hash`):** `afab0a3ca3abfe3c3f7692d34be2aeadbd099b8d43b6543d8d234d19b5ef8443` (`110` files)
- **Live Gemini API Calls:** `0` (`ALLOW_LIVE_AI = 0`)
- **Default Production Mode:** `LLM_ONLY` (`CACHE_VERSION = "125"`, `RESPONSE_CONTRACT = "flat"`, `HYBRID_PRODUCT_ENABLEMENT = NO-GO`)
- **Final Verdict:** **`COMBINED_BACKEND_VERIFIED_PENDING_MAIN_GO`**

---

## 1. Merge Provenance & Conflict Resolution (`P0`–`P1`)

Starting from clean `main` (`4abc4afb`), three frozen research branches were merged sequentially with `--no-ff` merge commits preserving full commit history:

| Step | Source Branch | Source HEAD | Source Product Commit | Merge Commit | Conflicts |
|---|---|---|---|---|---|
| 1 | `research/semantic-extraction-v3-runtime-revision` | `bb014eb80bd17b1223717d63385139bb9b23210d` | `283813b2` (`6ba9033b…`) | `a94a54d0559394ac90c6f338ca484417f9417d93` | `0` |
| 2 | `research/contract-driven-goal-composition` | `a629ebee346bf0083cf90294ad352640bcc936ce` | `1529faa7` (`540fc9d5…`) | `7507312bbb16af5527ef7c7dba4f59c2a786cbd2` | `0` (`registry.py` auto-merged cleanly across disjoint hunks) |
| 3 | `research/step-math-validation` | `0dd1da5ce599b2a418357b7ebcc5f820b2d47dc8` | `4abc4afb` (`d122f988…`) | `f63dae86e2da35a0b341697db3643486f5c99f2c` | `0` |

### Product Code Surface Diff vs `main` (`4abc4afb`)

Only 4 product files under `backend/app/` differ from `main`:
1. `backend/app/ai/fact_extraction.py` (`+137 / -1`): `RESPONSE_CONTRACT` (`"flat"` default, `"v3"` opt-in), `facts_response_schema()`, `schema_accepts()`, `surface_fingerprint()`.
2. `backend/app/simulation/geometry_functions/registry.py` (`+215 / -36`): `REGISTRY_VERSION = "geometry-functions/6"`, possessive separator `[\s,;:]++` in `_SAU_HOP_LE`, bounded `hình hộp chữ nhật` / `dài bao nhiêu` / sentence-initial article `Một` grounding, and `PlanningContract` for `ask_area` (`AnswerArea`) & `ask_angle_line_plane` (`AnswerAngle`).
3. `backend/app/simulation/geometry_functions/planner.py` (`+54 / -16`): `PLANNER_VERSION = "geometry-fact-planner/7"`, `_cau_hoi` and `_EffectResolver` support for `AnswerArea` (tuple-of-3-operands with shared auxiliary point deduplication) and `AnswerAngle` (`ask_angle_line_plane`).
4. `backend/app/simulation/geometry_functions/engine.py` (`+103 / -11`): `ENGINE_VERSION = "geometry-function-engine/5"`, independent Gram-determinant verifiers `_dt2_tam_giac` and `_goc_duong_mat_cos2`, and `kiem_mat_cat` pre-checks for `ask_area` and `ask_angle_line_plane`.

---

## 2. Version, Surface Fingerprint & Candidate Identity Separation (`P2`–`P3`)

| Constant / Surface | Value / SHA-256 | Status |
|---|---|---|
| `REGISTRY_VERSION` | `"geometry-functions/6"` | Active on combined candidate |
| `PLANNER_VERSION` | `"geometry-fact-planner/7"` | Active on combined candidate |
| `ENGINE_VERSION` | `"geometry-function-engine/5"` | Active on combined candidate |
| `CACHE_VERSION` | `"125"` | Unchanged (`DEFAULT_MODE = LLM_ONLY`) |
| `RESPONSE_CONTRACT` | `"flat"` | Default preserved (`v3` opt-in for evaluation) |
| `surface_fingerprint("flat")` | `485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a` | Unchanged |
| `surface_fingerprint("v3")` | `90bf8f039df830062e068adcf1d243643c8ebebfde5b4a5cf9ec340078ea7aab` | Unchanged |
| `function_calling.surface_fingerprint()` | `7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25` | Unchanged |
| `TypedFact.model_json_schema()` SHA-256 | `aa9d93eeac9f1659af8e5acd42af1904b7aaed674a8ab0f56f0c7dd8b2ad4ee8` | Unchanged |
| `registry.function_declarations()` SHA-256 | `5ceb0f999d4d7c1ee37c02207ea6470a7f972a168d6c52fa597392934d86f169` | Unchanged |
| Historical `v3-runtime-revision` Product Hash | `6ba9033bfca06d671cd27891e2dad06c7d44f365fed45527123c907d664b65ed` | Preserved in `semantic-extraction-v3-runtime-revision/` |
| Combined Candidate Product Hash | `afab0a3ca3abfe3c3f7692d34be2aeadbd099b8d43b6543d8d234d19b5ef8443` | Frozen in `EVALUATION_CANDIDATE.json` & declared in `candidate_divergence.json` |

---

## 3. End-to-End Integration Test Suite & Regressions (`P4`–`P5`)

New suite `backend/tests/geometry/test_hybrid_backend_integration.py` (`19` tests, `19/19 PASS`) verifies:
- `flat` and `v3` contract gates -> Source Grounding -> `PlanningContract` -> `Engine` -> Geometry IR -> `Scene3D` + `formation.steps`.
- Forensic reconciliation of the `24` LOCKED held-out gold payloads under `v3` (`8` raw pass, `16` rejected due to `13` redundant `solid` on segment lengths + `3` author `reason` notes; `24/24` pass after deterministic stripping).
- Multi-goal shared unnamed midpoint deduplication (`1` synthesized midpoint call across `ask_area` + `ask_distance_point_plane`) and named midpoint reuse.
- All 6 geometry quantity & construction families (`area`, `angle`, `length`, `distance` on non-Euclidean Gram metric $G \neq I_3$, `volume`, `section`).
- Safe refusals (`17/17` negative cases), lying contract verifier (`AUXILIARY_RULE_MISMATCH`), tampered engine verifier (`ENGINE_SELF_CHECK_FAILED`), and sub-`250ms` question-tail regex guard on 4,096-space suffixes.
- Strict Riemannian metric validation (`strict_parse_metric` and `strict_mat3_inv` reject `10/10` missing, non-3x3, singular, indefinite, and asymmetric metrics as `INVALID` without ever falling back to Euclidean `IDENTITY_METRIC`).
- `174/174` historical Planner cases (`65` served, `109` refused), `40/40` Slice A/B cases (`19` production served + `4` discovery served = `23` served, `17` refused), `88/88` combined served scenes verified by the 11-category Step Math Oracle, `148/148` baseline scenes verified, `10/10` geometric counterexamples detected, and `8/8` offline `v3` evaluation cells matching frozen `04b0db37` scores 100%.
