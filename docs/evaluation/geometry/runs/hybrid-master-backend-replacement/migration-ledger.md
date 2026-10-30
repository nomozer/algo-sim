# Task 3 (offline part) — entry points, migration ledger and gate reassessment

Read from the code at `e33ae978`. Nothing has been retired, and no production routing has changed.

## Production entry points

| entry point | orchestrator today | reaches Hybrid /4? |
|---|---|---|
| `POST /api/analyze` (`main.py`) | `ai/pipeline.py::run_pipeline`, default `LLM_ONLY`. LLM `stage_semantic_program` synthesis, then the deterministic gates. Compiler C is wired through `quyet_dinh_dinh_tuyen` but is `DISABLED` under `LLM_ONLY`. | **No.** Route D is locked out by the import closure (`test_structured_geometry_relations.py::test_Y_*`, D-01). |
| `POST /api/image/extract` | `ingestion/image*.py` transcribes the problem; the reviewed text then goes to `/api/analyze`. | No. It has no geometry orchestration of its own. |
| `POST /api/preview/hybrid` | `ai/hybrid_preview.py`. Operator-only: flag, token, loopback, no `Origin`. Offline fixtures only. | Preview of Route D only; not production. |
| `GET /api/diagnostics/*`, `/api/health` | identity and diagnostics | No; they only report policy. |

So there are **three** orchestrators today: LLM_ONLY synthesis (the production default), compiler C (opt-in, disabled) and Route D (/4 offline replay plus operator preview). The contract requires one production orchestrator at cutover. That has **not** been reached.

## Migration ledger

| OLD_COMPONENT | NEW_OWNER | MIGRATION_TEST | LAST_CONSUMER | REMOVAL_STATUS |
|---|---|---|---|---|
| `pipeline.stage_semantic_program` (LLM program synthesis) | Route D: `typed_fact_next_extraction` → bridge → planner → engine → `adapter4_route` | Paired live differential vs LLM_ONLY (D-11) | `run_pipeline` ← `/api/analyze` (production default) | **ACTIVE.** Cannot retire before D-11 and cutover. |
| `geometry_compiler/` (six-family compiler C, `GEOMETRY_COMPILER_MODE`) | Route D planner (Registry effect search) | Family-by-family /4 parity on the compiler's served set | `pipeline.py` (routing gate) plus 7 `backend/scripts/*` diagnostics | **ACTIVE (opt-in).** Parity is not measured, so it is kept. |
| Adapter /3 (`function_route.run_typed_fact_next_route` and its wrapper `ai/adapter3_simulation.py`) | `adapter4_route.py` | Capabilities /3 has but /4 lacks (curved and qualified identity, per contract) | Wrapper: 10 test modules only (no `app/` or `scripts/` importer). /3 route: the test suites and the shared schema/engine docs it co-owns. | **ACTIVE.** /4 refuses curved solids by design, so /3 is still the only owner of that capability; it must not be removed before /4 parity. |
| `ai/function_calling.py` (route D branch A: AI chooses the function) | branch B: facts + deterministic planner | — | `fact_extraction.py`, `typed_fact_next_extraction.py` (reuses `_openapi` only), A/B scripts | **ACTIVE as a library.** Its schema helper is a live dependency. |
| bridge private identity copy | `typed_fact_next.py::canonical_vertex_ref` | `test_bridge_ownership_resolves_identity_through_the_one_canonical_resolver` + identity suites | none | **REMOVED** (Task 1, `7bf0a3ab`) |

## Gate reassessment (`docs/MIGRATION_CHECKLIST.md`)

**Route D gates (D-01…D-13)** are the gates relevant to Hybrid replacement.

| status | gates |
|---|---|
| PROVED | D-01, D-03, D-05, D-06, D-09 |
| PROVED for preview only | D-07, D-08 |
| PARTIAL | D-02 (no Route D cache yet), D-12 (rollback needs D-02) |
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
