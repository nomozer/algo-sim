# ALGOSIM REAL PRODUCT INTEGRATION REPORT

**Master Epic:** `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT`  
**Branch:** `research/hybrid-master-backend-replacement`  
**Date:** `2026-11-03`  
**Live Gemini API Calls in This Phase:** `0` (`USD 0.00`)

---

## A. Current product

- **Git HEAD (frozen candidate commit):** `123e57daaa74d616f09b213e618fb309c09be1d7` (`123e57da`, clean working tree `cay_lam_viec_sach = true`).
- **New product candidate:**
  - `product_commit_sha`: `d17116cbc4b4f4065f198a19de0957cc51eeb82e` (`d17116cb`, on top of `6fc6b309`).
  - `measured_system.tree_hash`: `730045ff43f7be806fcabbb0047717ef4ad390a8b32ad81a4b9cf0adad74075f` (`118` files).
  - Manifest: `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json` + divergence layer `docs/evaluation/geometry/runs/hybrid-master-product-integration/candidate_divergence.json` (`frozen-evaluation-candidate.json`).
  - Prior frozen candidate `15d236eb` (product `51ba6135` / `3711d4eeee260ffd…`) and all C18/C19/C21 receipts are preserved byte-for-byte (`../hybrid-master-definition-composition/frozen-evaluation-candidate.json`, `frozen-evaluation-candidate-15d236eb.json`).
  - Pilot approval templates (`PENDING_OWNER_DECISION`, `paid_project_confirmed: false`) re-bound to `measured_system = 730045ff…`, LF-normalized `runner_sha256 = e9c6ad4388032f06949ac6c0dd5d06b2882be576c0564ff4a5143e6e48229438`, `paired_harness_sha256 = 4af1dc76355ec4f59d1f9045b7cee03d40b1bab3528290963776be85daa408d6`, `scorer_sha256 = 8c330bd493f9d401f579b6383f1a1df2bc9172eee2530cf187be2024801b5a2d` (blobs: `k1` `2199eb32…`, `s2` `a6792fce…`, `r1` `9f832e67…`).
- **Hybrid runtime configuration (`backend/app/main.py`, `backend/app/ai/hybrid_offline.py`, `backend/app/runtime_identity.py`):**
  - `HYBRID_ROUTE_MODE=off` (default): `DEFAULT_MODE = LLM_ONLY`, `CACHE_VERSION = 131`, zero silent cutover, and full `D-01` lazy-import isolation when `off`.
  - `HYBRID_ROUTE_MODE=staging-replay`: executes recorded `typed-fact-next/2` corpus entries (`HYBRID_REPLAY_CORPUS`) through the full Hybrid `/4` stack across local or Docker container networks, explicitly tagged `extraction_mode = "REPLAY_STAGING_SIMULATED"` and `simulated = true`.
  - `HYBRID_ROUTE_MODE=live`: requires `ALLOW_LIVE_AI=1` and a non-empty `GEMINI_API_KEY`, runs the deterministic domain gate before any provider send, executes `TransportExtractor` with deadline-bounded transient retries (`HybridTransportTimeout`, `ApiBudget` retry accounting, normalized `resolve_hybrid_gemini_model()`), isolates cached `SERVED` envelopes under `ROUTE_D_CACHE_POLICY` (keyed by mode, model, `typed_fact_next_surface_fingerprint()`, and `Registry /31` · `Planner /26` · `Engine /22` · `Adapter /4`), and returns sanitized `no-store` HTTP `502`/`503`/`504` `INFRASTRUCTURE_FAILURE` payloads without falling back to `LLM_ONLY`.
- **Existing frontend integration (`frontend/src/simulations/domains/geometry/hybrid-preview-adapter.ts`, `SimulationWorkspace.tsx`, `photo-problem-flow.ts`, `store.ts`, `core/types.ts`):**
  - Reuses the existing `ProblemInput` → `client.ts::analyzeProblem` → `docPhanHoiPhanTich` → `docPhanHoiHybridPreview` → `store.ts` → `SimulationWorkspace` / `Scene3DExplorer` flow with zero UI redesign.
  - Fixes Category B (`ENGINE_DERIVED_SECTION`, `plane-section-certificate/1`) plane-section consumption (`kiemEngineDerivedSection`), validates and surfaces `route-d-clarification/1` clarifying questions (`kiemClarification`, `[data-clarification-question]`, Photo Review → Build `buildFailureMessage`), and clears stale `active`, `activeAssignment`, `semanticFocus`, and `unsupported` state across recoverable infrastructure errors, refusals, and subsequent runs (`M18`).

---

## B. Real execution

- **Actual API path:** `POST /api/analyze` → `main.py::_analyze_hybrid_route` → `TypedFactNext /2` extraction (`StagingReplay` or `LiveHybridRun`) → `registry.kiem_nguon` (`Source Gate`) → `FactGraph` → `Planner /26` → `Registry /31` → `Compiler/IR` → `Engine /22` (exact `Fraction` + radical arithmetic) → `Adapter /4` (`hybrid-route-d-simulation/4`).
- **Actual frontend path:** `ProblemInput` submit → `POST /api/analyze` → `docPhanHoiPhanTich` → `docPhanHoiHybridPreview` → `useSimulationStore.loadEnvelope` → `SimulationWorkspace` → `Scene3DExplorer` (`veKhongGian`, step playback, quantity panel, inspector, causal highlight) or `UnsupportedNotice` (refusal / clarification) or `error-banner` (infrastructure failure).
- **Exact math execution:** verified across `16/16` scope/refusal categories (`41/41` cases in `product-integration-16-classes-verification.json`, `0` live calls): polyhedra, regular & oblique prisms, cylinders, cones, spheres, circumscribed/inscribed/dual spheres, multi-object shared-face & section+sphere configurations, Category A & Category B plane sections, unnamed `described_points` (`R-1`), constrained planes (`MAT_RANG_BUOC`), and `orthocenter`/`circumcenter` definition-regression compositions (`C18`) — `100%` exact agreement with independent `Fraction`/radical oracles, `0` wrong-served.
- **Scene3D results:** every served case produces closed `depends` graphs, verified `plane-section-certificate/1` / `geometric-relation-certificate/1` certificates, positive object and construction-step counts, rendered `<canvas>` + step controls + quantity rows in `Scene3DExplorer`, and `0` leaked machine identifiers (`::`, `@d`, `_prime`, internal codes).
- **Refusal/clarification behavior:**
  - `4` corpus refusal/clarification categories (`11` cases in `product-integration-16-classes-verification.json`) plus the pre-extraction domain gate (`test_hybrid_product_integration.py`) verified fail-closed (`HTTP 200` refusal envelope, `0` scenes rendered, `0` cached): `13_contradictory_data` (`INCONSISTENT_FACTS`, `DEGENERATE_POINTS`), `14_missing_data` (`PLANE_NOT_UNIQUE`, `MISSING_DIMENSION`), `15_ambiguous_expressions` (`AMBIGUOUS_FACT` with `route-d-clarification/1` question displayed), `16_unsupported_goals` (`OUT_OF_SCOPE`, `BRIDGE_UNSUPPORTED_DESCRIBED_POINT`, `EXACT_DOMAIN_EXCEEDED`), and non-geometry prompts (`out_of_scope` before extraction).
  - Infrastructure/configuration faults (`LIVE_AI_DISABLED`, `MISSING_API_KEY`, `PROVIDER_ERROR`, `NO_CANDIDATE`, `PROVIDER_BLOCKED`, `RESPONSE_TRUNCATED`, `JSON_INVALID`, `HYBRID_DEADLINE_EXCEEDED`) return `HTTP 502`/`503`/`504` (`Cache-Control: no-store`) with zero secrets/tracebacks and clean UI recovery on retry.

---

## C. Tests

- **Backend regression:** `pytest tests/test_hybrid_product_integration.py tests/test_hybrid_route_d_cache_and_rollback.py tests/test_paired_route_evaluation.py tests/geometry/test_s2_student_language_pilot_runner.py tests/geometry/test_typed_fact_next_extraction.py` — **PASS**; full backend suite inside Full T3: **`16,648 passed, 0 failed, 7 skipped, 2 deselected, 15 xfailed`** (`694.11s`).
- **Frontend regression:** `npx vitest run` — **`85/85` test files (`1,486/1,486` tests) PASS**, including `src/components/hybrid-product-integration.test.tsx` (**`62` tests** covering Category B sections, clarifications, Photo Review → Build clarification forwarding, `M18` store reset, and leak guards).
- **End-to-end & 16-class runtime verification:** `pytest tests/test_hybrid_product_integration.py -k test_staging_replay_serves_and_refuses_all_16_scope_classes` (generated once via `backend/scripts/export_hybrid_product_integration_corpus.py`) → **`16/16` categories (`41/41` cases) PASS** (`product-integration-16-classes-verification.json`).
- **Browser verification:** `node frontend/scripts/verify-hybrid-product-e2e.mjs` (built `frontend/dist` + real `uvicorn` backend + headless Playwright Chromium over HTTP) → **`6/6` required user flows PASS (`0` page errors)** (`product-e2e-browser-receipt.json`):
  1. `flow_1_supported_polyhedral`: `S2-B-I07_ve_va_tinh` → `8/3` (`Bước 1/4` → `Bước 2/4`, `<canvas>` `1391×717` rendered);
  2. `flow_2_curved_and_composite_geometry`: `cr.shared_base_pyramids_plus_inscribed_sphere` (`72`, `9π`) + `cone.par.S` (`81π/16`);
  3. `flow_3_multi_function_composition`: `S2-B-P07_shared_intermediate_two_goals` → `√3`, `1` (`Bước 1/6` → `Bước 2/6`);
  4. `flow_4_constrained_plane_and_orthocenter`: `K-A01` (`3√2/2`, `ENGINE_DERIVED_SECTION`) + `R1-B01` (`2304/625`);
  5. `flow_5_ambiguous_and_contradictory_refusal`: `S2-C-A01_goc_chieu` (`[data-clarification-question]` rendered, `0` canvas) + `S2-D-D03_contradictory_length` (`geometry_generation_failed` `UnsupportedNotice`, prior clarification cleared, `0` canvas);
  6. `flow_6_infrastructure_failure_and_recovery`: `live` with `ALLOW_LIVE_AI=0` → `HTTP 503` (`LIVE_AI_DISABLED`) `.error-banner` → clean recovery on `S2-B-I07_ve_va_tinh` (`8/3`) + `rollback_off` check.
- **Security checks:** `python backend/scripts/check_publication_safety.py --range f986e897..HEAD` → **`PASS` (`violations=0, pending_exception=0`)**; secret redaction and traceback suppression verified in `test_hybrid_product_integration.py` and `test_publication_safety_gate.py`.
- **Independent review:** fresh-context adversarial `research` subagent (`fb072bfb-a333-491f-b146-5990179d9d8e`): Round 1 `NOT_READY` (`1 BLOCKER`, `2 MAJOR`, `5 MINOR`, `2 NIT` — closed in `6fc6b309`/`d17116cb`); Round 2 `NOT_READY` (`0` code/test defects; `1 MAJOR`, `1 MINOR`, `1 NIT` report-prose drift — closed in `88c67fc7`); **Round 3 `READY` (`0 BLOCKER`, `0 MAJOR`, `0 MINOR`, `0 NIT`, `product-integration-adversarial-review.md`).**
- **Full T3 (`full-t3-123e57da.json`):** Attempt 1 on `ebb3e546` failed 2 backend tests (`runner_sha256` Windows CRLF checkout drift + generic `httpx.ReadTimeout` mapping in `TransportExtractor`), fixed in `d17116cb`; **Attempt 2 on clean detached worktree `hm-t3-123e57da` → `FULL_PRODUCT_GATE_PASS` (`exit 0`, `16,648` pytest, `1,486` vitest, `tsc -b && vite build` PASS, demo replay `5/5`, crash surface `6/6`, pre/post `freeze_evaluation_candidate.py --verify` `MATCH`, worktree & junctions safely removed).**

---

## D. Deployment

- **Build status:** `cd frontend && npm run build` (`tsc -b && vite build`) **PASS**; `docker compose config --quiet` **PASS**.
- **Local application status:** `uvicorn app.main:app` + built frontend verified end-to-end across `off`, `staging-replay`, and `live` pre-request gates; `/api/health` and `/api/diagnostics/runtime` report `hybrid_route` mode, `simulated`, surface hashes, model, and `allow_live_ai` without exposing secrets.
- **Staging status:** `docker-compose.yml` forwards `HYBRID_ROUTE_MODE`, `HYBRID_REPLAY_CORPUS`, `ALLOW_LIVE_AI`, and `GEMINI_MODEL` (plus `env_file: ./backend/.env`), `backend/.env.example` documents `GEMINI_API_KEY` (`<dan-key-vao-day>`), `HYBRID_ROUTE_MODE`, `HYBRID_REPLAY_CORPUS`, and `ALLOW_LIVE_AI`, and `backend/app/main.py` optionally reads `HYBRID_LIVE_TIMEOUT_SECONDS` / `HYBRID_LIVE_DEADLINE_SECONDS` (`60s` / `180s` defaults); `staging-replay` works across container bridge networks and explicitly marks responses `REPLAY_STAGING_SIMULATED`.
- **Production configuration:** `HYBRID_ROUTE_MODE` defaults to `off` (`LLM_ONLY` default preserved until all 20 migration gates in `docs/MIGRATION_CHECKLIST.md` pass).
- **Rollback:** setting `HYBRID_ROUTE_MODE=off` (or unsetting it) immediately restores `LLM_ONLY` without touching `LLM_ONLY` cache rows (`ROUTE_D_CACHE_POLICY` isolation) and without importing Hybrid Route D modules (`D-01` verified).
- **Remaining release blockers:**
  1. `PAID_PROJECT_NOT_VERIFIED` — Google Cloud Billing confirmation or separate explicit Owner paid-tier attestation is not yet present on this host (`c21-delegated-attempt/c21-delegated-execution-receipt.json`);
  2. Live Gemini pilots (`K-1`, `S-2`, `R-1`) and independent held-out live evaluation (`H-1`, requiring an Owner-attested independent author) remain `NOT_MEASURED`;
  3. Production default cutover (`docs/MIGRATION_CHECKLIST.md` gates `D-04`, `D-11`, `D-13`, `GATE-16`) and explicit Owner merge/push authorization remain gated.

---

## E. Research integrity

- **Registered composition remains verified offline:** `SOURCE_EXPLICIT_SEQUENCE`, `REGISTERED_DECOMPOSITION`, constrained planes (`C17`), and textbook definition-regression composition (`C18`: `orthocenter`, `circumcenter`) are verified end-to-end through the real `/api/analyze` → `Scene3DExplorer` product path.
- **Genuine discovery remains `NOT_ESTABLISHED`:** no new open-ended planner discovery claim is made (`GENUINE_DISCOVERY_NOT_ESTABLISHED`, `composition-c18.md`).
- **Live Gemini status:** `LIVE_PROVIDER_NOT_MEASURED` (`0` live Gemini requests in this phase; `USD 0.00`).
- **Strict separation of replay vs live extraction:** `HYBRID_ROUTE_MODE=staging-replay` is explicitly labeled `REPLAY_STAGING_SIMULATED` (`simulated: true`) in both API responses and `/api/diagnostics/runtime` and is never counted as live NLU accuracy, latency, or cost evidence.

---

## F. Final release decision

- **Product Integration Status:** `PRODUCT_INTEGRATION_VERIFIED`
- **Live Provider Status:** `LIVE_PROVIDER_NOT_MEASURED`
- **Production Release Status:** `PRODUCTION_RELEASE_BLOCKED`

### Exact Release Checklist (Post-Integration Gates)

1. **Confirm Paid Gemini Project (`PAID_PROJECT_NOT_VERIFIED`):** supply either Cloud Billing OAuth verification (`GOOGLE_CLOUD_PROJECT` + `GOOGLE_OAUTH_ACCESS_TOKEN`) or a separate explicit Owner paid-tier attestation JSON, then run `python backend/scripts/run_s2_student_language_pilot.py --delegated-c21` under the locked `70` request / `USD 4.00` two-tier ledger (`K-1` → `S-2` → `R-1`).
2. **Execute Independent Held-Out Live Evaluation (`H-1`):** obtain an Owner-attested independent corpus author (`hybrid-only-independent-evaluation-protocol.md`) and run paired live evaluation (`D-04`, `D-11`, `GATE-16`).
3. **Owner Cutover & Publication GO:** review live pilot/holdout results against `docs/MIGRATION_CHECKLIST.md` before authorizing any default-mode cutover or fast-forward integration/push of `research/hybrid-master-backend-replacement` to `main`.
