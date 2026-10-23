# Backend Hybrid Session 2 — contract unification & planner integration

- **Run:** `backend-hybrid-contract-unification` · **Authorization:** `GO_BACKEND_SESSION2_LOCAL_CONTRACT_RESEARCH`
- **Branch:** `research/hybrid-backend-session2-contract` (worktree `.superpowers/worktrees/hybrid-backend-s2`), from Session 1 HEAD
  `82d3d255`. Product `3553e4d4`, candidate freeze `5beb0e86` (115 files, `96962736…`).
- **Classification:** `DEVELOPMENT_EVALUATION_NOT_BLIND`, offline, authored TypedFactNext JSON, **0 provider calls**. No
  natural-language extraction was measured; no blind or held-out claim is made (§P6).
- **Governance unchanged:** `DEFAULT_MODE = LLM_ONLY`, `RESPONSE_CONTRACT = flat`, `HYBRID_PRODUCT_ENABLEMENT = NO-GO`,
  `ALLOW_LIVE_AI = 0`, `CACHE_VERSION = 127` (NO_BUMP: `/api/analyze` reaches none of the changed code). No schema,
  contract version, provider surface, merge or push.
- **Final state:** `SESSION2_CONTRACT_DECISION_REQUIRED` (see §Status).

## Headline numbers (Session 1 reproduced at `82d3d255` → Session 2 at `3553e4d4`)

| metric | Session 1 | Session 2 | source |
|---|---|---|---|
| Bridge: expected-served cases resolved (Session 1 60-case family) | 40/49 | **49/49** | `session1-family-replay.json` |
| Bridge: exact answers correct / wrong served | 34/34 · 0 | **43/43 · 0** | same |
| Bridge: refusals correct · scene structurally valid · label leaks | 11/11 · 40/40 · 0 | 11/11 · **49/49** · 0 | same |
| Adapter /3: wrong answers on the bridge's exact payload | **18** | **0** | same (`same_payload_wrong_served`) |
| Adapter /3: invalid inputs served (Session 1 3 cases) | 3 | **1** (known, D2) | same (`served_invalid`) |
| Adapter /3: crashes | 1 (`plane_equation`) | **0** | same |
| Contract parity: 316 payloads × 2 routes (wrong served / disagree when both serve / crash) | not measured | **0 / 0 of 20 / 0** | `evaluation.json` |
| IR budget refusals (`IR_MEMORY_BUDGET_EXCEEDED`, budget 32 unchanged) | 9/49 | **0/49** | both |

Baseline reproduction: `verification/red/session1-baseline-replay-at-82d3d255.json` (identical aggregate to Session 1's
`planner-composition-final.json`).

## What changed (product `3553e4d4`, 3 files)

| file | change |
|---|---|
| `backend/app/ai/adapter3_simulation.py` | `_certify_section_boundary` (closure certificate: cycle == `section.cross_section`, else `SECTION_BOUNDARY_INCOMPLETE`); `_shared_source_gate` (bridge → planner → `registry.kiem_nguon` before compiling; gate verdict binding; `source_verification` label on every served result, curved = legacy); `UNSUPPORTED_PLANE_KIND` guard |
| `backend/app/simulation/geometry_functions/engine.py` | `gop_doi_tuong_trung`: an identical engine-internal `derived_*` line/plane is declared once (final statement order; later reads renamed to the first; labelled objects never merged) |
| `backend/app/ai/function_route.py` | `_an_dinh_thiet_dien_phu`: derived-pyramid lateral edges named as such, group step rewritten, fresh labels scrubbed from `role` |

Tests: new `backend/tests/geometry/test_hybrid_contract_unification.py` (20 passing + 1 strict xfail); 3 existing test files
edited (each edit commented with this run's id), incl. 5 strict xfails for gate-grammar false refusals added after review. Red receipts (traceback-free, raw-log SHA-256):
`verification/red/red-receipts.json` — P1 6 failed / P2 3 failed / P4 4 failed / P5 1 failed before the fix.

## P1 — `cut_edges` (CRITICAL)

Root cause: one field, two meanings (bridge = stated subset; Adapter /3 = full cycle), and Adapter /3 never checked that its
cycle closes — `[SB, SC, SD]` built `S.NPQ` and dropped `M` on `SA`. Design: `CONTRACT_DECISION_PROPOSAL.md` (canonical
`typed-fact-next/2` separating stated constraints, engine-owned boundary, derived vertices, provenance and a closure
certificate; migration and cross-route rule). **Not implemented as a contract** — Owner GO D1. Implemented instead:
each route verifies its own legacy reading (Adapter /3 closure certificate), so a `/1` payload gets one answer or a
refusal. `/1` meaning untouched. Unsupported polyhedral plane kinds refuse instead of crashing.

## P2 — Source Gate

One authority where it can read the payload: Adapter /3's polyhedral path runs the Registry Source Gate (closed clause
grammar, roles, negation, conditionals, coverage, value grounding, goal ownership) on the bridged facts; a refusal is
binding with the gate's code. Session 1 regressions: `N-swapped-names` → `SOURCE_OBJECT_MISMATCH`, `N-unread-condition`
→ `SOURCE_OBJECT_MISMATCH` (both routes, both conventions); plane-equation crash → `UNSUPPORTED_PLANE_KIND`.
New negatives (20 payloads: swapped names on 4 edges, unread condition, negated relation, conditional clause, wrong
number, unstated ratio orientation, unstated residual ownership, missing height, quote not in source, anonymous ratio):
bridge serves 0; Adapter /3 serves 1 — the anonymous-ratio payload in Adapter /3's own convention (no stated cut), which
the bridge cannot express, so no gate verdict exists and the legacy checks still decide (`source_verification.authority =
adapter3.substring_legacy`, locked by `xfail(strict=True)`).

Correction layer (frozen corpus bytes unchanged; expectations overridden in `test_typedfact_next_adapter3.py`):
A3-DEV-07 / -08 were served although "tính tỉ số thể tích" does not say which solid is the numerator — **source defects
the frozen run served**; A3-DEV-11 still refuses (code order only). A3-DEV-10 is a **false refusal** (the gate's grammar
does not bind "Dựng lăng trụ, thiết diện bởi (α)" to the only prism) — not loosened for coverage, locked as a strict
xfail so it turns red when the grammar is fixed (D3).

**Real reach of the shared gate (independent review, reproduced):** of the 7 dev-corpus cases Adapter /3 still serves,
the gate gives a verdict on **0** — all 7 are `adapter3.substring_legacy`. Given their complete boundary as `cut_edges`,
A3-DEV-03/04/06/09 are refused by the same grammar gap as A3-DEV-10 (strict xfails too), so today a payload that *omits*
`cut_edges` escapes the stricter gate. This only ever refuses — no wrong serve — but it means the unified gate currently
binds the bridge-expressible authored families (Session 1 family, parity, negatives), not Adapter /3's own corpus.
`test_wave3a_adapter3_integration.py::test_adapter3_unified_halfspace_containment_refusal`: the fixture's bare "Tính thể
tích phần còn lại" now names both solids so the test again exercises the containment certificate.

Strict variant (D2), measured with a scratch plugin on `3553e4d4`, no product edit (`verification/d2-strict-fallout/`):
18 Adapter /3 tests change — 10 lose a served result (dev corpus 7/10 → 0/10 positives served), 8 only change their
refusal code. Not implemented: it removes accepted capability, so it is the owner's decision.

Not unified: Adapter /3's curved route (no planner path; labelled legacy); paraphrase coverage (§P6: 1/5).

## P3 — planner composition and reuse (evidence)

| question | answer | evidence |
|---|---|---|
| Producer search or problem-type branching? | **Both, in different places.** Goal/answer chains: bounded backward search over Registry planning contracts by effect kind + operand types (`_EffectResolver._resolve`, memoized, cost-minimal). Facts: one mapping rule per fact kind, not per problem type. Section construction: hand-written decompositions keyed by plane relation (`_mat_qua_diem`, `_mat_vuong_duong`); cut vertices by cost-ranked case analysis per lateral edge (`_dinh_cat_canh`) — not general search. | `p3-composition-suites` 334 passed, incl. `test_removing_one_contract_removes_exactly_that_composition`, `test_no_planner_branch_names_a_composed_pair`, zero-planner-edit discovery (`test_contract_driven_goal_composition.py`) |
| Reuse of points / lines / planes / solids? | Yes. Through-point reused on its edge in every served plan (38/38 here, 49/49 Session 1 family); one derived plane per (solid, point, reference) key (1.0 plane constructions per section); identical planned intersection reused at cost 0; derived pyramid registered once and named by fact id for ratio/residual. | `evaluation.json` `composition`; `test_an_identical_intersection_already_planned_is_reused_at_cost_zero` |
| Duplicate objects / constructions / certificates? | Plans: **0 duplicate calls** (38 plans). IR: every cut vertex re-declared the section plane and each foot its line → fixed (P4). One duplicate remains per section: the visible section plane `mp_td_*` (labelled) re-declares the hidden operand plane (D4c). One `DINH_CAT_CANH` certificate per section fact. | `composition.duplicate_calls`, `ir_duplicate_constructs = 38 (= 1/plan)` |
| Cheapest derivation chosen consistently? | Yes by construction: `min` on (cost, name, label, id) with deterministic ties; through-point reuse (cost 0) always beat a cost-1 intersection on SA. Bounds unchanged: `MAX_CALLS 64`, `MAX_DERIVED_PLANES 4`, `MAX_EFFECT_DEPTH 3`, `MAX_EFFECT_NEEDS 32`, `MAX_EFFECT_CANDIDATES 8`, `MAX_RESULT_LINES 4`, `MAX_RESULT_FEET 8`. | `planner.py`; selection counts |
| Same structure, different wording? | The planner is wording-independent (typed facts). End to end it is **not**: the shared gate accepts 1 of 5 paraphrases of the section clause (both routes, identical verdicts). Structural equivalence (∥ base ≡ ⊥ SA when SA ⊥ base) holds. | `metamorphic_invariance.paraphrase` 1/5; Session 1 MR |
| Goal / premise permutation, relabeling, multiple goals? | Premise permutation **24/24** (both routes), relabeling **2/2**, goal order **1/1**, two goals (ratio + residual) exact on both. `cut_edges` order: bridge order-invariant (set semantics); Adapter /3 order-sensitive by its contract (cyclic boundary) and refuses crossed orders. | `evaluation.json` `metamorphic`, `contract_parity` |

## P4 — IR memory budget

Diagnosis (with the budget lifted, diagnostic only): the 9 refused plans needed 33 declarations, of which 3 were
duplicates (two extra copies of the section plane declared per cut vertex, one extra copy of line SA per perpendicular
foot). Canonicalization in `bien_dich` (one declaration per identical derived construction) brings them to 30; the
budget stays **32**. All 9 now serve with exact answers (49/49). Remaining genuine exceedances: regular hexagonal base,
33 (∥ plane) and 36 (⊥ plane) declarations — real program size, refused (`IR_MEMORY_BUDGET_EXCEEDED`), budget policy
is D4. Side effect, measured: square-base plans now fit the teaching expansion that was previously skipped; it exposed a
Session 1 presentation defect (fresh labels in `role`, lateral edges called "Đoạn của thiết diện") — fixed (P5).

## P5 — Scene3D semantics

| aspect | state |
|---|---|
| solid-qualified identities | bridge refuses non-identity bindings (`BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY`); Adapter /3 serves them under the legacy source authority (labelled) |
| derived objects | fresh cut labels never reach learner text (`label_leaks 0`, regression test); derived-pyramid lateral edges named "Cạnh bên của khối chóp đỉnh S cắt bởi (α)" |
| dependencies · births | `_validate_scene` passes on every served scene: bridge 65/65, Adapter /3 50/50 |
| goal ownership | ratio/residual operands must be named by the question (gate); A3-DEV-07/08 corrected |
| quantity classification · certificates | unchanged (engine `targets`; Gram volume/ratio/residual certificates); new closure certificate in Adapter /3 `verified_relations` |
| construction sequence | one "Xét mặt phẳng (α)" step per plane instead of one per cut; each cut keeps its own step naming its edge |
| refusal semantics · topology | refused ⇒ `scene3d` absent (unchanged); no residual frustum mesh is invented (still NOT_IMPLEMENTED) |

No colour, camera, UI or frontend rendering change. No browser gate was run (structural validity only).

## P6 — scientific evaluation

All families `DEVELOPMENT_EVALUATION_NOT_BLIND`. **No holdout was created**: every family here was written by the
author of the fixes in the same session, so independence could not be guaranteed; a blind set needs a separate author
and a lock commit before execution. Families (`evaluation.json`): Session 1 replay (60), contract parity (316 × 2),
budget (8), metamorphic (33: premise permutations 24, relabel 2, goal order 1, paraphrase 5, reference 1), negatives
(20 × 2). Per-dimension: source-grounded correctness — negatives 0/20 served (bridge), 1/20 (Adapter /3, D2); exact
mathematics — 43/43 Session 1 family, 0 wrong serves on 316 parity payloads; refusal precision — 11/11 (Session 1
family), paraphrase false refusals 4/5 (both routes); planner composition and reuse — §P3; Scene3D structural validity —
115/115; contract parity — 0 disagreements; budget exhaustion — 0/49 (was 9/49), hexagon 2/2 genuine; metamorphic — §P3.
Wall time (local, served and refused, not production latency): bridge p50 0.0028 s / max 0.060 s; Adapter /3 p50
0.0037 s / max 0.057 s. Evaluation receipt: `verification/evaluation/execution.json` (wall time of the whole run UNKNOWN).

## P7 — resources

pytest single worker, BLAS threads 1, no parallel full gates; one clean detached freeze; independent review before the
single Authoritative Full T3 (§Verification).

## Answers to the ten handoff questions

1. **What is actually unified?** The source authority for every polyhedral payload the bridge can express (Adapter /3
   now takes the Registry gate's verdict); the IR canonicalization (one engine `bien_dich`, both routes); the section
   geometry authority (Adapter /3's closure proof uses the kernel's `cross_section`). **Not unified:** the meaning of
   `/1.cut_edges`, Adapter /3 as a separate compiler, the curved route.
2. **`cut_edges`:** resolved at the **design** level (`CONTRACT_DECISION_PROPOSAL.md`, needs D1); at the implementation level
   only its **safety** is resolved (each route proves its own reading; 0 wrong serves, 0 disagreements on 316 payloads).
3. **Does Adapter /3 still produce wrong results or serve invalid problems?** Wrong exact answers: 0 on every family
   measured. Invalid served: 1 known case (anonymous ratio operand in Adapter /3's own convention, no gate verdict
   possible) — closes only with D2 (+D6). Crashes: 0.
4. **Is the Source Gate unified across routes?** Partly: one gate wherever the bridge can express the payload; elsewhere
   Adapter /3's legacy checks still decide, and every served result says which authority verified it. On Adapter /3's own
   dev corpus the gate decides 0 of the 7 served cases, and its grammar false-refuses the complete-boundary encodings of
   4 of them (D2 + D3 together close this).
5. **How well does the planner recompose and reuse?** §P3: bounded contract search for goal chains (ablation-proven),
   rule-based section construction, full reuse of through-points/planes/intersections, 0 duplicate calls; invariant to
   premise order, relabeling and goal order; **not** invariant to wording (1/5 paraphrases) because of the gate grammar.
6. **IR budget cases improved:** 9 of 9 (Session 1's `IR_MEMORY_BUDGET_EXCEEDED` set), budget unchanged at 32; 2 genuine
   exceedances found (hexagonal base).
7. **Geometry families still missing in backend reasoning (planner path):** curved solids (only Adapter /3 legacy);
   derived solids over a prism section; ⊥-line planes on prisms; plane kinds `plane_equation`,
   `parallel_to_base_at_distance` / `_ratio`, `axial_section`; sections cutting base edges (only lateral edges); unstated
   cut vertices (D6); multi-solid qualified identity / multiple frames; residual polyhedron (frustum) mesh; larger bases
   beyond the IR budget (D4).
8. **Contracts needing Owner GO:** D1 `typed-fact-next/2` + bridge `/2` + Adapter `/4` + route-D `/4`; D2 gate strictness;
   D4 IR budget policy for engine programs; D5 version labels for this session's behaviour change; D6 planner semantics
   (derived unstated cuts). D3 (gate grammar wave) is a scope decision, not a contract.
9. **Conditions not met to replace the old backend:** D1/D2 open; no live extraction into TypedFactNext (frozen `flat`
   cannot emit bridge fields); no blind/held-out E2E; paraphrase false refusals; Adapter /3 still separate and curved not
   on the planner; `MIGRATION_CHECKLIST.md` 20 gates not re-evaluated; no browser acceptance of the new scenes; separate
   `GO_MAIN` and production enablement absent.
10. **Next work before Hybrid enters the product path:** owner decisions D1–D6 → (if D1) `/2` schema, converter, dual run →
    D6 planner derived cuts + D2 strict gate → D3 preregistered gate-grammar wave with negative controls → a blind holdout
    authored and locked by someone else → a budgeted live extraction pilot (separate `ALLOW_LIVE_AI` GO) → browser gates
    for the new scenes → migration checklist.

## Verification

Independent review round 1: **`INDEPENDENT_REVIEW_PASS`** (0 BLOCKER, 2 IMPORTANT, 3 MINOR) — `independent-review.md`.
IMPORTANT #1 is reported above (gate reach), #2 fixed in tests (strict xfails). MINOR #3–#5 recorded as follow-ups
(narrow the `except` around the bridge; enforce the dedup name invariant; pre-existing Adapter /3 crash surface on
malformed premise args — 412 of 2223 fuzzed mutations raised a non-`TuChoi` exception, none through the new gate).
Authoritative Full T3: `handoff.md` and `verification/full-t3/`.

## Status

`SESSION2_CONTRACT_DECISION_REQUIRED` — the backward-compatible implementation is complete, tested, frozen and reviewed
(see handoff for T3); the remaining unification (`cut_edges` meaning, single source authority without a legacy path)
cannot proceed without Owner decisions D1 and D2.
