# Pre-main hardening of the Hybrid backend candidate

- **Run:** `hybrid-pre-main-hardening` · branch `research/hybrid-pre-main-hardening` · base `research/hybrid-backend-integration` `2620cffa`
- **Owner approval:** `GO_PRE_MAIN_BACKEND_SAFETY_HARDENING` (no merge/push of `main`, no live AI, no default change, no frontend edit, no deletion)
- **Product commit:** `3afe2fdd` · candidate freeze `81ba464f` · `measured_system.tree_hash` `7cd48f8c3d19299e95e5d31b341ec52120f0bc33b0e1ffc9cce03a2e9c37caf4` (110 files)
- **Held constant:** `DEFAULT_MODE = LLM_ONLY` · `RESPONSE_CONTRACT = flat` · `HYBRID_PRODUCT_ENABLEMENT = NO-GO` · `ALLOW_LIVE_AI = 0` · `CACHE_VERSION` unchanged (125)
- **Model requests:** 0

## 0. Verdict

See §8 (filled after the independent review and the authoritative T3).

## 1. Findings of the preceding review — what was confirmed

| # | Finding | Result | Evidence (RED on `2620cffa`) |
|---|---|---|---|
| 1 | Default-route guard `test_Y_duong_mac_dinh_VAN_khong_tham_chieu_compiler` falsely green | **CONFIRMED** | `pipeline.py:716` loads `geometry_compiler.routing` via `__import__("app.simulation.geometry" + "_compiler.routing")`; a clean `LLM_ONLY` `run_pipeline` loads 7 `app.*` modules the static closure did not see |
| 2 | Cache identity blind to the route | **CONFIRMED** | switching `GEOMETRY_COMPILER_MODE` returned `cached: true` with the other mode's envelope, both directions; an env flip mid-request ran `DETERMINISTIC_FIRST` and stored the row as default |
| 3 | `RESPONSE_CONTRACT` read twice per call | **CONFIRMED** (new) | flipping the global between request and validation SERVED the v3-invalid unnamed-midpoint payload requested under v3 |
| 4 | Zero length misclassified | **CONFIRMED** | height 0 / √0 / 0/5 / 0,0 → `ENGINE_SELF_CHECK_FAILED` ("bố cục engine vi phạm chính dữ kiện nó đã dùng": the layout replaced h² = 0 by 1); lateral edge 0 → `INCONSISTENT_FACTS`; `0a` → `NON_HOMOGENEOUS_LENGTHS`. Never served |
| 5 | `Metric` accepts non-SPD matrices | **CONFIRMED** | indefinite, asymmetric, singular, det < 0 all constructed. No current producer emits one (layout checks `G2` and `h² > 0`) |
| 6 | 174 rows checked on status/code only | **CONFIRMED** (test gap) | no test compared answers; answers reproduce 65/65 |
| 7 | Multi-goal ownership | **NOT REPRODUCED** as a defect | two different unnamed midpoints (SC, SB) give two points and the hand-oracle answers 13/4 and 9/13 |
| 8 | B29 "64/289 vs 8/17" | **NOT A DEFECT** | angle answers are cos²; the probe squared them again. Hand: AC² / SC² = 8/17 |
| 9 | Negative lengths | **NOT A DEFECT** | the value grammar has no sign: `SCHEMA_INVALID`, nothing served; locked as is |
| 10 | Cleanup inventory errors | **CONFIRMED** | `cleanup-manifest.json` §corrections C1–C5 |

## 2. Fixes (product code, RED → GREEN → regression)

Exactly seven product files changed against `2620cffa`:

| File | Change |
|---|---|
| `backend/app/ai/pipeline.py` | explicit lazy import of the routing gate; `RoutePolicy` + `route_policy_snapshot`; `run_pipeline(route_policy=…)` threaded to `quyet_dinh_dinh_tuyen` |
| `backend/app/main.py` | `_policy_identity`; `_cache_lookup(…, policy_version)`; one snapshot per `/api/analyze` for lookup, pipeline and store |
| `backend/app/simulation/geometry_compiler/routing.py` | `dinh_danh_be_mat(che)` — versions of the compiler layers, through the gate |
| `backend/app/ai/fact_extraction.py` | `run_ai_fact_route(…, contract=None)` resolved once per call; prompt, schemas and surface fingerprints unchanged |
| `backend/app/simulation/geometry_functions/registry.py` | `doc_so` refuses zero as `NON_POSITIVE_LENGTH` (route A and B) |
| `backend/app/simulation/geometry/metric.py` | `Metric.__post_init__`: symmetric + Sylvester minors, exact |
| `backend/app/simulation/geometry_functions/engine.py` | `_Dung.metric()` maps the type error to a coded refusal for every caller |

### 2.1 Guard (finding 1)

Three layers (`test_structured_geometry_relations.py::test_Y_*`):

1. a **deny-list of known dynamic-import mechanisms** in `backend/app` (AST: `__import__`, `exec`, `eval`, `compile`,
   `__builtins__`, importlib/builtins/runpy/pkgutil imports, `import_module`, `spec_from_*`, `sys.modules`). It is not
   spelling-proof: the independent review found 11 further spellings that pass it (`globals()[…]`, `pydoc.locate`,
   `pickle.loads`, `vars(sys)["modules"]`, `os.sys.modules`, `__subclasses__()` loaders, `logging.config.dictConfig`,
   `mock.patch`, pydantic `ImportString`, `operator.methodcaller`, nested `getattr`);
2. static closure from `app.main` / `app.ai.pipeline`: compiler only through the declared gate
   `(ai/pipeline.py, geometry_compiler.routing)`, route D unreachable; positive controls prove the closure sees
   relative and transitive imports;
3. **the spelling-independent layer** — runtime: a clean subprocess (DNS/connect blocked, provider stubbed) imports
   `app.main` and runs `run_pipeline` in `LLM_ONLY` END TO END to an `ok` envelope (the synthesis reply is the
   compiler's own program for the prism fixture, so validator, interpreter, kernel, adapter and `scene3d` run); the
   probe asserts analyze → synthesis ran and status `ok`; every loaded `app.*` module must lie in the static closure,
   route D must not load, and tail modules (`interpreter`, `scene3d`, `route`) must load.

Limit: layer 3 covers the code the probe executes — one fixture on the default path. Code that only other inputs or
modes reach is covered by layers 1 and 2 alone.

Fault injection: 8 bypass spellings caught by layer 1; a split-string `__import__` of `function_route` caught by
layer 3 both at the start of the path (synthesis) and inside the deterministic tail (wrapping `build_scene3d`).
`LLM_ONLY` still returns `DISABLED` without calling `bien_dich` / `build_fact_graph`.

Review-driven corrections to the first version of this guard: its proof "routing module loaded ⇒ routing line ran"
became vacuous once `route_policy_snapshot()` (called at `run_pipeline` entry) imported `routing`; it stopped at the
first provider call, so the tail never ran; and it had no network block although `db.py` calls `load_dotenv`.

### 2.2 Route-aware cache (finding 2) and per-call contract (finding 3)

- Default identity = `CACHE_VERSION` exactly ⇒ existing rows still hit. Other modes: `CACHE_VERSION:<8 hex>` over the
  mode and `COMPILER/ADAPTER/FACT_GRAPH/PRIMITIVE_REGISTRY_VERSION` (read at call time; ≤ `String(16)`).
- `SEMANTIC_ROUTE_MODE` is not part of the identity: `run_pipeline` no longer uses `semantic_route`.
- One row per key (`UNIQUE(key)`, delete-then-insert): alternating modes evicts the other mode's row. A miss is never
  a wrong serve, but it is eviction, not two caches. `GEMINI_MODEL` is not in the identity either (pre-existing, out of
  scope).
- `scripts/cache_clear.py --cu` treated every row `!= CACHE_VERSION` as stale and would have deleted valid compiler-mode
  rows; it now uses `con_hieu_luc` (`test_cache_clear_khong_coi_hang_cua_che_do_khac_la_cu`).
- `/api/analyze` now takes the snapshot before the pipeline's `try`, which imports the `geometry_compiler` package
  (its `__init__` re-exports compiler, adapter, fact graph, primitives) on the first request of a process, cache hits
  and non-geometry text included. Before, only geometry requests imported it, inside the caught pipeline. An import
  error there would now answer 500 to every request; no behaviour change otherwise (NIT, left as is).
- `backend/tests/test_route_aware_cache.py`: forward and rollback isolation, same-mode hits, identity tracks versions,
  one snapshot despite a mid-request env change, pipeline routes by snapshot not env, snapshot immutable.
  Mutation checks: storing under bare `CACHE_VERSION` → 2 red; looking up without identity → 2 red.

### 2.3 Values and metric (findings 4, 5)

- Zero lengths refused as `NON_POSITIVE_LENGTH` — the code route C and `learner_messages.py` already use. No frozen
  route-D corpus contains a zero input (searched every JSON under `backend/tests` and `docs/evaluation`; the four hits
  are answer values / IR literals of older routes), so no recorded outcome moves. Refusal taxonomy:
  `NON_POSITIVE_LENGTH → contradictory` (`hybrid_compiler_benchmark.REFUSAL_CLASS`).
- `Metric` enforces SPD. Measured layering on a non-SPD base Gram injected after the layout guard: the layout
  self-check refuses first (`ENGINE_SELF_CHECK_FAILED`); with it disabled, `kiem_mat_cat` maps the type error to
  `METRIC_NOT_EUCLIDEAN`; before the type check that case surfaced late as `ENGINE_EXECUTION_FAILED`. `_Dung.metric()`
  now refuses with a code itself, because goal checkers call it after serving, outside any handler.

## 3. Regression and mathematical safety

| Check | Result |
|---|---|
| 174 historical rows — REGRESSION vs `regression-174.json` (product 540fc9d5): status, code, served squares | 174/174 · 65/65 |
| 174 rows — INDEPENDENT: served answer = source-corpus expectation (goal-directed-function-discovery, benchmark30, next-slice, two-line inputs; angles as cos²) | 65/65 |
| refusals of rows whose source records an answer (capability gaps, never wrong serves) | 7, locked in `CAPABILITY_GAPS_174` |
| fault injection: one length read wrong (3 → 6) | caught |
| two goals, two different unnamed midpoints | 2 points, 13/4 and 9/13 (hand oracle) |
| zero / negative lengths, routes A and B | `NON_POSITIVE_LENGTH` / `SCHEMA_INVALID`, no scene |
| non-SPD metric (type) / injected into the engine | 5/5 rejected / coded refusal |
| lying PlanningContract, tampered engine verifier, source tampering, 17 negatives | existing suite PASS (`test_safe_refusals_*`, `test_registry_permutation_*`) |
| source-grounding safety probes: `integration/extraction-v2-safety`'s file run against this tree / in-tree superset | 35/35 behavioural (its 36th test is path-bound to its own run dir) / 72/72 |
| timeline dependency closure, 84 served scenes, with fault injection | 0 violations; reordered dependency caught |
| step-math oracle (scene self-consistency, NOT correctness against the problem) | 88/88 VERIFIED, 10/10 counterexamples |

Two claims are kept apart throughout: the step-math oracle checks that a scene agrees with its own coordinates and
constructions; correctness against the problem statement is the independent-expectation check above.

## 4. `CACHE_VERSION` decision

**No bump.** The default (`LLM_ONLY`) identity is byte-identical to before, so every existing row stays valid for the
mode that wrote it, and no prompt, schema or routing policy of the default path changed. Bumping would only discard
valid rows. Residual: rows written earlier while `GEOMETRY_COMPILER_MODE=DETERMINISTIC_FIRST` was set are
indistinguishable from default rows (no mode was recorded); whether any exist is `UNKNOWN`; they passed the same
gates and the compiler mode is opt-in local tooling.

## 5. Interpretation corrections to `hybrid-backend-integration` (original files unchanged)

- "Strict Riemannian metric validation … 10/10 rejected": `strict_parse_metric` / `strict_mat3_inv` live in the test
  module; the product type enforces SPD only since this run.
- "88/88 combined scenes verified": scene self-consistency; the oracle was called without expected answers.
- "174/174 historical": status/code only until this run.
- `cleanup-inventory.json`: superseded by `cleanup-manifest.json` (C1–C5).
- The test `test_version_constants_…` pinned the live tree hash to `afab0a3c`; it now checks the receipt keeps
  `afab0a3c` and the live tree equals the frozen candidate.

## 6. Cleanup and preservation

`cleanup-manifest.json`. Nothing deleted. KEEP (unique work or active): `research/hybrid-semantic-extraction-v2`
(14 unpushed commits), `integration/extraction-v2-safety` (uncommitted docs, `330a222a`, upstream `origin/main` —
a bare `git push` would target main), `research/compact-geometry-dsl` (8), `research/scene3d-plane-grid-camera`
(active), `docs/real-model-e2e-readiness`, `feat/real-model-pilot-tooling`. CONDITIONAL after a verified GO MAIN push:
the four merged research branches and `research/hybrid-backend-integration`; the three unregistered folders (5.2 GB,
owner-run elevated removal after re-verifying blob equality). UNKNOWN: `backend/.tmp/pytest-05045731…`, other
`.superpowers/` drafts.

## 7. Frontend handoff and remaining runtime gaps

`frontend-handoff.md` (F1 uncertified altitude marker, F2 unguarded `maTranKhung`, F3 `length_unit`, F4 proof status);
`docs/OPEN_ISSUES.md` (`ISSUE-ARCH-SCENE3D-ALTITUDE-MARKER-UNCERTIFIED`, `ISSUE-ARCH-SCENE3D-CHART-METRIC-UNGUARDED`,
`ISSUE-ARCH-HYBRID-ROUTE-D-NOT-WIRED`); route-D gates `docs/MIGRATION_CHECKLIST.md` §2.

## 8. Verification

### 8.1 Independent review — PASS, 0 blocking

A separate read-only review agent (0 live calls, 0 modifications) checked all ten scope items. Dispositions:

| # | Finding | Severity | Disposition |
|---|---|---|---|
| 1 | runtime probe's "routing loaded" proof vacuous since `route_policy_snapshot` | NON_BLOCKING (harness) | fixed: probe asserts analyze → synthesis ran and status `ok`; tail modules must load |
| 2 | layer (c) ran only the head of the path | NON_BLOCKING (harness) | fixed: end to end with the compiler's program as the synthesis reply; tail injection test added |
| 3 | layer (a) is a deny-list (11 spellings pass) but was described as spelling-proof | NON_BLOCKING (overclaim) | fixed in §2.1 and checklist D-01 |
| 4 | probe subprocess had no network block (`load_dotenv` can restore keys) | NON_BLOCKING (latent) | fixed: `getaddrinfo` / `create_connection` blocked |
| 5 | snapshot outside the pipeline `try` imports the compiler package on every first request | NIT | recorded in §2.2, unchanged |
| 6 | `cache_clear.py --cu` would delete valid compiler-mode rows | NIT | fixed + test |
| 7 | one row per key ⇒ mode alternation evicts | NIT | recorded in §2.2 |
| 8 | `3afe2fdd` / `81ba464f` leave 2 tests red, fixed in `5d8f97a1` (a `docs(eval)` commit that also touches the test taxonomy `hybrid_compiler_benchmark.py`) | NIT (bisect) | recorded here; no history rewrite |
| 9 | manifest C2 said "all 14 '+'" (13 + 1 merge) | NIT | fixed |

Also reported, not a defect: a height *derived* as ≤ 0 (base 2, lateral edge 1 or √2) is refused as
`INCONSISTENT_FACTS`, classed contradictory.

### 8.2 Authoritative T3

Filled from the receipt (`run.json`).
