# Hybrid next phase — implementation handoff

**Planning only. No H1–H4 implementation in this campaign.** Start only after the Owner decides the renderer gate and names the integration base. New work branches from the then-integrated main; do not stack new production wiring onto an unapproved Scene3D candidate or use the dirty root checkout.

## H1 / D-10: certificate presentation delta, first deliverable

Do not rebuild capabilities already present. Code inspection on this candidate shows:

- `hybrid-preview-adapter.ts::docPhanHoiHybrid` already validates preview `/2` and simulation `/4` views, identities, section provenance and closure certificates, attaching a validated `hybrid_preview` view; the store stays domain-blind.
- `scene3d-model.ts::ghiChuGiaTriDung` and `phanTichToanHocCuaCanh` already consume symbolic units, goal results and mathematical certificates. `Scene3DExplorer.tsx` already displays `lengthUnit`.
- `SimulationWorkspace.tsx` already has `verification_gap` refusal copy; `scene3d-annotations.ts` reads backend perpendicular witnesses. The contract §9 records earlier F1/F2/F5/F6 resolution. The older `MIGRATION_CHECKLIST.md` D-10 wording is not a fresh inventory of missing implementation.

The first bounded run should reconcile D-10 against Adapter `/4`, **reuse these consumers**, and implement only a demonstrated gap. Proposed task name `hybrid-certificate-presentation`; plan and evidence in its run directory.

| Step | Exact surfaces to reuse | Acceptance |
|---|---|---|
| Inventory source → validated view → panel/mark | `backend/app/ai/adapter4_route.py`, `hybrid_preview.py`; `frontend/.../hybrid-preview-adapter.ts`, `scene3d-model.ts`, `scene3d-annotations.ts`, `Scene3DExplorer.tsx`, `SimulationWorkspace.tsx` | For every right-angle operand/foot, unit, observation, verification gap and displayed name, identify its backend certificate/source field and consumer. No frontend derivation of a fact or label from IDs. |
| Pin certificate presence/absence and mismatched identities | Existing `frontend/src/components/adapter4-consumer.test.tsx`, `hybrid-preview-contract.test.tsx`, backend `tests/test_hybrid_preview_api.py` and actual `/4` fixtures | Missing/false `can_present_as_proven`, dangling operand, wrong scene binding, missing foot or unsupported relation cannot create a square marker or a proof claim. Read existing tests before adding new ones. RED before a demonstrated fix. |
| Units and observations | `ghiChuGiaTriDung`, validated Hybrid answer/observation views, existing `cauQuanSat`/timeline consumers | With/without `length_unit`, named objects and symbolic values correct; goal observations stay observations, not proofs. Mode A hides final answers; Mode B matches the locked reveal contract. |
| Browser presentation | Frozen offline `/4` fixtures through the existing validated boundary and Scene3D | Desktop/mobile, named operands and correct square foot, no source-free markers, verification-gap copy, no answer leakage. Renderer coordinates and authoritative scene stay unchanged. |
| Documentation delta | `HYBRID_PREVIEW_FRONTEND_CONTRACT.md`, `MIGRATION_CHECKLIST.md` D-10, code/evidence indexes | Update stale status only with current consumer evidence. Finish with explicit remaining gaps, not an assertion that D-10 was wholly absent. |

T0: affected named test. T1: above directly related contract/consumer tests and needed typecheck. T2: offline browser fixture set. T3 only if product changes and a clean candidate is frozen. Cache decision must follow semantic envelope changes, not a blanket UI assumption. No `/api/analyze` wiring or live provider calls in H1.

## H2 / D-04: independent holdout

Before development use, preregister a new NL→TypedFacts V2 evaluation. Proposed initial size: 60 cases, a planning choice requiring review before sealing, not an existing dataset claim. Stratify by currently admitted families, named/unnamed entities, prime symbols, unit expressions, ambiguity, contradiction and honest refusal. Keep legacy/renderer-only curved families distinct from admitted source/engine capability.

Owner appoints a gold author/reviewer independent of extraction development. Gold expectations derive from problem text and the typed contract, not renderer output or model answers. Seal case/gold hashes, access owners, split policy and a leakage register. Do not expose gold cases to development agents, prompts, repair loops or fixture tuning. Corrections require an adjudication record; development changes use a different set.

Pin model/prompt/schema/source-gate versions, sampling policy, refusal/error treatment, completeness and unsafe-serve metrics, denominator rules and stop criteria **before** measurement. Missing outputs are UNKNOWN/error, not zero. Offline gold injection first checks harness/scorer; any provider arm requires separate Owner GO, monetary/request caps and mandatory stop rules. No live budget is allocated by this plan. Release artifact: preregistration + independent gold provenance + sealed hashes + scorer negative controls, followed by the separately authorized measurement.

## H3: family E2E one at a time

Keep the inherited capability matrix (0 FULL_E2E, 9 PARTIAL, 7 RENDER_ONLY, 2 UNSUPPORTED) as the starting record, not a new measured outcome. Reconfirm it at the approved integration base. Pick the strongest admitted polyhedron family first; prioritize cuboid/right prism, then pyramid/section according to its actual source gates. A rendered sphere/cylinder/cone does not become FULL_E2E through screenshots alone.

For each chosen family, use one run and independent mathematical expectations across:

`Problem → TypedFacts → Source Gate → Registry/Planner → Exact Engine → Adapter /4 → Scene3D → Browser`.

Require independently authored positives and refusal counterexamples (missing source, mismatched object, inconsistent metric, degenerate cut, ungrounded auxiliary). Verify exact quantities and certificate provenance, plus source point/plane identity. General rules must cover renamed points and changed dimensions; no case-ID branches. Publish stage-specific loss and one end-to-end verdict. Upgrade that family only after every stage passes; partial stages remain PARTIAL. No cross-family engine rewrite to force one fixture through.

## H4: API, cache and rollback only after H1–H3

Reuse existing `RoutePolicy`, `route_policy_snapshot`, `backend/app/main.py::_policy_identity` and operator-only preview boundary. The present cache function explicitly rejects `hybrid_preview_enabled` before product-cache access; inspect existing route identity tests before proposing another cache abstraction. This guard is not implemented route-D product caching. Do not expose the operator token endpoint as learner UI.

Propose `/api/analyze` flag wiring with LLM_ONLY as the default. Pin per-request policy snapshots; route identity must include the route's semantic versions, contract/source/planner/engine/adapter identity. Test separate cache hits, off→on→off, no cross-route reuse, interruption and rollback to the exact default response behavior. No existing cache rows may silently acquire new meaning.

Prepare offline paired inputs first. A live paired comparison versus LLM_ONLY requires its own Owner GO, preregistered budget/stop rules, measurement class, held-out claim and evaluator independence. A successful visual gate or H1 run never authorizes live traffic, production Hybrid or a default change. Final enablement is an Owner decision after all migration gates.
