# Task 3 (offline part) — entry points, migration ledger and gate reassessment

Read from the code at `e33ae978`. Nothing has been retired, and no production routing has changed.

## Production entry points

| entry point | orchestrator today | reaches Hybrid /4? |
|---|---|---|
| `POST /api/analyze` (`main.py`), default | `ai/pipeline.py::run_pipeline`, `LLM_ONLY`. LLM `stage_semantic_program` synthesis, then the deterministic gates. Compiler C is wired through `quyet_dinh_dinh_tuyen` but is `DISABLED` under `LLM_ONLY`. | **No.** The default path's import closure excludes Route D (`test_structured_geometry_relations.py::test_Y_*`, D-01). |
| `POST /api/analyze`, declared opt-in `HYBRID_V2_LOCAL=offline-replay` + loopback | `main._analyze_hybrid_v2_local` → `hybrid_offline` (recorded TypedFactNext /2 extraction) → /4 route → adapter /4; Route D cache (D-02) | **Yes**, offline replay only. There is no live extractor. *Correction (Phase B): the first version of this table missed this pre-existing Stage 2 branch.* |
| `POST /api/image/extract` | `ingestion/image*.py` transcribes the problem; the reviewed text then goes to `/api/analyze`. | No. It has no geometry orchestration of its own. |
| `POST /api/preview/hybrid` | `ai/hybrid_preview.py`. Operator-only: flag, token, loopback, no `Origin`. Offline fixtures only. | Preview of Route D only; not production. |
| `GET /api/diagnostics/*`, `/api/health` | identity and diagnostics | No; they only report policy. |

So there are **three** orchestrators today:
- LLM_ONLY synthesis, the production default;
- compiler C, opt-in and disabled;
- Route D: /4 offline replay on the declared `/api/analyze` opt-in, plus the operator preview. The contract requires one production orchestrator at cutover. That has **not** been reached.

## Migration ledger

| OLD_COMPONENT | NEW_OWNER | LAST_CONSUMER | PARITY_EVIDENCE | REMOVAL_STATUS |
|---|---|---|---|---|
| `pipeline.stage_semantic_program` (LLM program synthesis) | Route D: `typed_fact_next_extraction` → bridge → planner → engine → `adapter4_route`, via the declared `/api/analyze` opt-in | `run_pipeline` ← `/api/analyze` (production default) | Offline only: Wave 3 replay 67/72, locked 96/96, the measurement probe and recomposition evidence. **Live paired differential (D-11): NOT_MEASURED.** | **ACTIVE.** Cannot retire before D-11 and cutover. |
| `geometry_compiler/` (six-family compiler C, `GEOMETRY_COMPILER_MODE`) | Route D planner (Registry effect search) | `pipeline.py` (routing gate) plus 7 `backend/scripts/*` diagnostics | **None.** No corpus exists in both `RequestContract` and TypedFactNext form. | **ACTIVE (opt-in, disabled).** |
| Adapter /3 (`function_route.run_typed_fact_next_route` and its wrapper `ai/adapter3_simulation.py`) | `adapter4_route.py` | Wrapper: 10 test modules only (no `app/` or `scripts/` importer). /3 route: test suites and shared schema/engine code. | **Partial.** Polyhedral parity is the /4 inventory. Curved solids and qualified identity: /4 refuses them by design, so there is no parity. | **ACTIVE.** /3 is the only curved-solid owner. |
| Preview flat-facts contract (`hybrid_preview.run_preview` → `run_ai_fact_route`) | the same `run_fact_route` → planner → engine; /4 TypedFactNext is the target contract | `/api/preview/hybrid` (operator), 41 locked fixtures, `HYBRID_PREVIEW_FRONTEND_CONTRACT.md` | The shared downstream is the same code, so no parity is needed there. The input contract differs (D-04: flat is the product contract; v3 NO-GO). | **ACTIVE.** Locked product contract, not a duplicate authority. |
| `ai/function_calling.py` (route D branch A: AI chooses the function) | branch B: facts + deterministic planner | `fact_extraction.py`, `typed_fact_next_extraction.py` (reuses `_openapi` only), A/B scripts | — | **ACTIVE as a library.** Its schema helper is a live dependency. |
| bridge private identity copy | `typed_fact_next.py::canonical_vertex_ref` | none | `test_bridge_ownership_resolves_identity_through_the_one_canonical_resolver` + identity suites (3384 passed) | **REMOVED** (Task 1, `7bf0a3ab`) |
| Route D "never cached" special case on `/api/analyze` | Route D cache identity (`prepare_local_replay.cache_key` + `ROUTE_D_CACHE_POLICY`) | — | `test_hybrid_route_d_cache_and_rollback.py`, `test_hybrid_v2_local_analyze.py` | **REPLACED** (Phase A, `e9c9b8e9`) |

## Gate reassessment (`docs/MIGRATION_CHECKLIST.md`)

**Route D gates (D-01…D-13)** are the gates relevant to Hybrid replacement.

| status | gates |
|---|---|
| PROVED | D-01, D-03, D-05, D-06, D-09; **D-02 and D-12 offline (Phase A, `e9c9b8e9`)** |
| PROVED for preview only | D-07, D-08. The `/api/analyze` opt-in serves the /4 envelope offline; production enablement is still D-13. |
| OPEN | D-10: presentation from certificates is frontend-owned and out of scope for this backend-only epic |
| BLOCKED | D-04 (flat is the product contract; a NEW pre-registered held-out set is needed), D-11 (paired live measurement), D-13 (`NO-GO`) |

This epic changes no gate status. Its new evidence:
- extraction source references, for D-04 provenance;
- one identity authority, for D-05 safety;
- a measured /4 inventory with independent controls, for D-05.

**Section 1 gates (GATE-01…20)** were written for compiler C. GATE-13 canary, GATE-15 holdout, GATE-16 tokens and latency, and GATE-20 user study all need live or human measurement and are `NOT_STARTED` / `NOT_MEASURED`.

## Cutover blocker (Owner decision)

Production cutover needs a measured real-text extraction quality on a new pre-registered held-out set (D-04), plus a paired live differential, reliability, latency and token/cost run against LLM_ONLY (D-11, GATE-16). The contract states: "No live budget is currently authorized." Without these, switching `/api/analyze` to Hybrid would be a mode-name change with no acceptance evidence, which the contract forbids. Retiring LLM_ONLY synthesis is therefore blocked as well.

**What an Owner GO must state:** provider and model; the maximum number of calls and the cost; stop rules; the held-out construction (independent author, pre-registered before any prompt or schema change); `MEASUREMENT_CLASS`, `HELD_OUT_CLAIM` and `EVALUATOR_INDEPENDENCE`.

## Offline work that can continue without a budget

- **D-02:** Route D cache identity (route-aware cache keys, two-way MISS tests).
- **D-12:** rollback tests.
- An opt-in `/api/analyze` Hybrid route behind a **declared** gate (D-01: "cổng nối phải được KHAI"), with an injected extractor and no silent fallback. It stays off by default, and `LLM_ONLY` must stay byte-identical.
- **Adapter /3 → /4 parity:** fail-closed curved support in /4 only with certified exact curved geometry.
