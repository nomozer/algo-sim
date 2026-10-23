# Combined contract compatibility matrix

Run `hybrid-disabled-integration`, branch `research/hybrid-session4b-integration`. Base: local `main` `f10e6283`.
Integrated: `main` + Session 3 (`0f7b3a69`, which contains Sessions 1–2) + Session 4A (`ef6829d3`). 0 provider calls.

The integrated `backend/app`, `backend/tests`, `backend/scripts`, `frontend/src` and `frontend/scripts` are the
same Git trees as the Session 3 T3 candidate `84c729e0`. Every row below is therefore a property of the Session 3
product placed on current `main`; what is new here is that it was measured on the combined tree.

## Production default (must not move)

| Surface | main | integrated | Evidence |
|---|---|---|---|
| `DEFAULT_MODE` (`routing.che_do`) | `LLM_ONLY` | `LLM_ONLY` | `results/invariants-default-isolation.json` |
| `RESPONSE_CONTRACT` (`fact_extraction.py`) | `flat` | `flat` | same |
| `CACHE_VERSION` (`main.py`) | `"127"` | `"127"` | same; `tests/test_api.py` in focused run |
| `MAX_MEMORY_DECLARATIONS` (`validator.py`) | 32 | 32 | same |
| `ALLOW_LIVE_AI` | 0 | 0 | every command in this run |
| Default `RoutePolicy` | `LLM_ONLY`, preview off, `flat`, fingerprint `None` | identical | same |
| `/api/analyze` policy when `HYBRID_ROUTE_D_PREVIEW=1` is set | preview off | preview off | same (`route_policy_snapshot(env)` without `preview=True`) |
| Product modules loaded by `import app.main, app.ai.pipeline` | 47 | 47, **0 differ from main** | same; all ten changed files are absent at startup |
| `semantic_program/`, `ai/skills/`, `main.py`, `ai/pipeline.py`, `docs/schemas/`, `frontend/` | — | **no diff vs main** | `git diff --stat main HEAD -- …` empty |
| Flat extraction surface fingerprint (what a provider sees) | `485d3834…` | `485d3834…` | computed on `git archive main` and on the integrated tree |
| Hybrid product enablement | NO-GO | NO-GO | no product caller; preview 404 unless operator env + token |

Conclusion: no cache bump is warranted. Default route code, prompts, schema, route policy and provider surface are
byte-identical to `main`; only opt-in research modules changed.

## Research contracts (opt-in, not on `/api/analyze`)

| Contract | main | integrated | Caller | Status |
|---|---|---|---|---|
| `geometry-functions` (Registry) | `/11` | `/13` | planner, engine, Adapter /3, /4, preview | 35 functions, 11 fact / 12 construct / 11 ask / 1 escape, 31 provider-offered, 4 internal — unchanged counts; adds `DINH_CAT_CANH` certificate and G1–G7 source grammar |
| `geometry-fact-planner` | `/11` | `/13` | fact route, Adapter /3 gate, /4 | adds section-vertex planning (`_dinh_cat_canh`), derived pyramid, `derived_fresh` via `PlanningContract` |
| `geometry-function-engine` | `/9` | `/11` | same | adds `kiem_dinh_cat`, closure certificate, typed `IR_MEMORY_BUDGET_EXCEEDED`, IR dedup |
| `TypedFact` (planner input) | provider schema | same provider schema + provider-hidden internal fields | fact route | provider sending an internal field ⇒ `INTERNAL_FIELD_FROM_PROVIDER` |
| `typed-fact-next/1` | parsed by Adapter /3 | unchanged parser; never reads `/2` | Adapter /3 | `/1.cut_edges` meaning is route-dependent |
| `typed-fact-next/2` | absent | canonical | Adapter /4 only | strict schema; never reads `/1` |
| `convert_v1_to_v2(raw, route)` | absent | `route ∈ {bridge, adapter3}` or `ROUTE_LABEL_REQUIRED` | tests/evaluators | no route-free conversion; Adapter /3 unnamed cuts are not guessed |
| `typed-fact-next-bridge` | `/1` | `/1` + `/2` | fact route / Adapter /4 | pure translation; refusals `BRIDGE_UNSUPPORTED_{CURVED,DERIVED_SOLID,MEASUREMENT,PLANE_KIND,PREMISE,QUALIFIED_IDENTITY,RELATION}` |
| `hybrid-simulation-adapter/3` | `/3` | `/3` label, **behaviour changed in Session 2** | Adapter /3 demos/tests | closure certificate + shared source gate; legacy-labelled authority where the bridge cannot express a payload (`docs/CODE_INDEX.md` Session 2 entry); the adapter label string itself did not change |
| `hybrid-simulation-adapter/4` / `hybrid-route-d-simulation/4` | absent | new | **none (Python function only)** | every SERVED result carries `source_verification.authority = registry.kiem_nguon` |
| `hybrid-preview-adapter/2`, `hybrid-route-d-preview/1` | same labels | same labels | operator-only `POST /api/preview/hybrid` | runs the flat fact route, not `/4`; preview identity now reports planner `/13`; preview has no cache |
| Frontend `hybrid-preview-adapter.ts` | accepts preview `/2` envelope | unchanged | `Scene3DExplorer` | no consumer for `/4` exists |

## Consumer boundary for Adapter /4 (backend side only)

`check_adapter4_consumer.py` on the locked Session 3 grammar set (`DEVELOPMENT_EVALUATION_NOT_BLIND`); final receipt
`results/adapter4-consumer-after-review/` (the first receipt in `results/adapter4-consumer/` used a narrower leak scan):

| Check | Result |
|---|---|
| Expected SERVE served / expected refusal refused | 22/22 · 25/25, 0 wrong serves, 0 refusals without code |
| Squared-coefficient oracle (Session 3 `square_of`, lock verified) | 15/15 numeric oracles match; 7 served cases are construct-only (no numeric oracle) |
| Section closure certificate | 21/22 served; `CORPUS-DEV10-prism-area` (plane-only section, no derived solid) has none |
| `hybrid_preview._validate_scene` on every served scene | 22/22 PASS |
| Metric agreement (`chart_metric`, `metric`) | 22/22 |
| `compile_semantic_program_to_envelope` + `validate_semantic_envelope_config`, not truncated | 22/22 |
| Internal identifiers in learner-visible text (snake_case tokens and scene ids across label/display_label/role/notation, event and step text, frame narration) | 0 |
| Residual volume | readout quantity only; ≤ 2 solids per scene (parent + derived pyramid); no residual mesh |

This is not browser acceptance. Fixtures for a frontend session: `results/adapter4-consumer/adapter4-frontend-fixtures.json`.
