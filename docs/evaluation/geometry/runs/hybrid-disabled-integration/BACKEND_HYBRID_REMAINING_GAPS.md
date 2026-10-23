# Backend Hybrid remaining gaps

Run `hybrid-disabled-integration`. Scope: the integrated candidate (`main` + Session 3 + Session 4A). Nothing listed
here was fixed in this run unless it says so; no geometry feature was added and no corpus, fixture, oracle or
wording was changed. Sources are linked so each gap can be re-checked.

## Integration defects (found and fixed in this run)

| ID | Defect | Fix | Evidence |
|---|---|---|---|
| INT-1 | `main` gateway docs (`ARCHITECTURE_MAP.md`, `architecture/README.md`, `TEXT_TO_GEOMETRY_FUNCTIONS_CONTRACT.md`) described registry/planner `/11`, engine `/9`, Adapter /3 only; integrated code is `/13`, `/13`, `/11` with `typed-fact-next/2` and Adapter `/4`. The contract doc also named a non-existent `DEFAULT_RESPONSE_CONTRACT`. | Docs-only commit `84cd09e3`; §2 counts re-verified against code. | `git show 84cd09e3` |
| INT-2 | Index conflicts between Session 3 and Session 4A in `CODE_INDEX.md` / `EVIDENCE_INDEX.md`. | Both sides kept; `hybrid-contract-v2` now `CORRECTED_BY HYBRID_SESSION4A_READINESS`. | merge `14cdc25a` |

No product-code integration defect was found: the product trees equal the Session 3 candidate, `main` had no
product change since the Session 3 fork point (`43247c9e`), and the merge had no code conflict.

## Contract limitations

| ID | Limitation | Source |
|---|---|---|
| CON-1 | Adapter `/4` has no HTTP route and no frontend caller; the preview endpoint runs the flat fact route. A product caller for `/4` is new work, not integration. | `adapter4_route.py`, `hybrid_preview.run_preview` |
| CON-2 | Canonical `/2` excludes curved solids, non-root qualified identity, non-pyramid derived solids and unsupported plane kinds; legacy Adapter `/3` and the default route still serve some of these. Schema admission ≠ route support. | 4A `PLANNER_GENERALIZATION_GAP_REPORT.md` capability matrix |
| CON-3 | `/1 → /2` conversion is only defined per declared route; Adapter `/3` payloads carry no record of which unnamed cuts the text states. | `typed_fact_next.convert_v1_to_v2` |
| CON-4 | Adapter `/3` behaviour changed in Session 2 under an unchanged label string. Consumers keyed on the label cannot tell the two behaviours apart. | `CODE_INDEX.md` Session 2 entry |
| CON-5 | Owner decision D2 (anonymous ratio operand on Adapter `/3`) still pending; test is xfail. | `test_hybrid_contract_unification.py` xfail |

## Source grammar limitations

| ID | Limitation | Source |
|---|---|---|
| SRC-1 | B28: "tâm" of a square is refused `PREDICATE_NOT_IN_QUOTE` (centroid keyword vocabulary). Identity unchanged; reproduced here in both arms. | `results/planner-diagnostics-integrated/planner-diagnostics.json` |
| SRC-2 | Gate-grammar false refusals for "thiết diện bởi (α)" (owner decision D3) remain xfail on A3-DEV-03/04/06/09/10. | `test_typedfact_next_adapter3.py` |
| SRC-3 | Generalized goal entry: two refusal codes differ from registered labels (xfail, labels preserved). | `test_generalized_goal_entry.py` |

## Planner capability limitations

| ID | Limitation | Source |
|---|---|---|
| PLN-1 | Generic goal composition is bounded (typed Answer/Point/Line/Plane needs, depth 3, 64 calls, 32 needs). Section-vertex `Meet` selection is handwritten section orchestration. No general geometry planner claim. | 4A planner report; reproduced row-for-row here |
| PLN-2 | B27: frozen facts encode the described-midpoint question as `kind="unsupported"` ⇒ `OUT_OF_SCOPE` in both arms. Historical fixture encoding, not an isolated current planner defect; re-encoding would be a new measurement. | 4A reconciliation; reproduced here |
| PLN-3 | Hexagonal sections exceed the IR memory cap (33/36 declarations > 32) ⇒ `IR_MEMORY_BUDGET_EXCEEDED`. Cap kept at 32 (owner D4). | Session 3 F receipts |

## Kernel limitations

| ID | Limitation | Source |
|---|---|---|
| KER-1 | Centre-label exhaustion raises `StopIteration` instead of a coded refusal (xfail). | `ISSUE-ARCH-ENGINE-CENTRE-LABEL-EXHAUSTION` |
| KER-2 | No generic solid Boolean; residual volume is certified arithmetic, not a residual solid. | engine certificates |

## Renderer consumer limitations

| ID | Limitation | Source |
|---|---|---|
| REN-1 | `FRONTEND_CONSUMER_ACCEPTANCE_OPEN` for `/4`: backend-boundary check only (scene gate, envelope compile, metric, leak scan). No browser run on a `/4` scene; owner visual acceptance not done. Fixtures provided. | `results/adapter4-consumer/` |
| REN-2 | Residual volume shows as a readout; there is no residual mesh by design. A frontend that wants to draw the residual needs a new contract, not a fake mesh. | same |

## Provider-dependent unknowns

| ID | Unknown | Source |
|---|---|---|
| PRV-1 | NL → `typed-fact-next/2` extraction quality: no V2 provider output exists (44 archived outputs are flat). | 4A `E2E_EXTRACTION_READINESS.md`; seam replay here |
| PRV-2 | Tokens, latency, cost of a V2 extraction arm: UNKNOWN (not zero). | same |
| PRV-3 | Independent holdout: protocol prepared, not executed. All sets used are development, not blind. | 4A `INDEPENDENT_HOLDOUT_PROTOCOL.md` |

## Not done in this run, by design

Live provider calls, production enablement, default switch, cache bump, `/4` HTTP or frontend wiring, merge/push to
`main`, and any new geometry family.
