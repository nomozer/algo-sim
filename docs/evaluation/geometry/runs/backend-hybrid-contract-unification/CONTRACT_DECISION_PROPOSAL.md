# Contract decision proposal — `cut_edges`, section boundary and shared Source Gate

Status: **PROPOSAL — needs Owner GO before any schema / version change.** Nothing in this file is implemented as a
contract change. What *is* implemented (backward compatible, `typed-fact-next/1` unchanged) is listed in §2 and in
`report.md`. Authorization in force: `GO_BACKEND_SESSION2_LOCAL_CONTRACT_RESEARCH`.

## 1. The problem, measured

`typed-fact-next/1` has one field, `DerivedPlaneSectionSpec.cut_edges`, with two incompatible meanings:

| route | reading of `cut_edges` | where |
|---|---|---|
| TypedFactNext → planner bridge | the lateral edges the **source text states** are cut (a subset; unstated edges get a vertex only by cost-0 reuse) | `typed_fact_next_bridge._section_fact` → `TypedFact.cut_edges` → `planner._dinh_cat_canh` |
| Adapter /3 | the **complete section boundary**, in cyclic order (`[]` = every lateral edge) | `adapter3_simulation._Adapter3Compiler._compile_derived_sections` |

Same JSON, two programs. On the Session 1 60-case family, Adapter /3 given the bridge's payload served 18 wrong exact
answers (quadrilateral bases: `[SB, SC, SD]` became the triangle `S.NPQ`, dropping `M` on `SA`; ratio 1/16 instead of
1/8). Reproduced at `82d3d255`: `verification/red/session1-baseline-replay-at-82d3d255.json`,
`verification/red/p1-red.log`.

The schema cannot express which reading a payload means, and it has no place for the five things a section actually
involves:

1. **source-stated intersection constraints** — "(α) cắt SB, SC lần lượt tại N, P": which edges, which names, which quote;
2. **the complete verified section boundary** — a geometric fact, owned by the engine, not an input;
3. **derived intersection vertices** — vertices the source never names (fresh `I…`, hidden from the learner);
4. **source provenance** — which quote supports each stated constraint;
5. **a geometric closure certificate** — proof that the boundary is the exact cross-section.

## 2. What was done without a contract change (implemented, `3553e4d4`)

Each route now *verifies its own legacy reading*, so one `/1` payload can no longer be served with two different answers:

- **Bridge** (unchanged): stated subset; the planner refuses an open cycle (`SECTION_NOT_CLOSED_ON_LATERAL_EDGES`); the
  engine checks every vertex on its edge segment (0 < t ≤ 1, `kiem_dinh_cat`).
- **Adapter /3** (new closure certificate `_certify_section_boundary`): the built cycle must equal
  `section.cross_section(solid, plane)` up to rotation/reversal (exact `Fraction`, affine-invariant), else
  `SECTION_BOUNDARY_INCOMPLETE`. Served results carry the certificate (`verified_relations[kind=section_closure]`).

Measured (`evaluation.json`, contract-parity family, every ordered subset of lateral edges × 2 bases × 2 plane kinds × 2
ratios = 316 payloads, both routes): **0 wrong serves on either route, 0 disagreements on the 20 payloads both serve, 0
crashes**. Session 1 family: same-payload wrong serves 18 → 0.

This is *safety by refusal*, not unification: the two routes still disagree about what `/1.cut_edges` means; they just
no longer serve different numbers for it.

## 3. Proposed canonical contract (`typed-fact-next/2`, NOT implemented)

Inputs say only what the source says; the boundary is an output.

```jsonc
"derived_sections": [{
  "section_id": "sec", "target_solid_id": "pyr", "plane_name": "α",
  "plane": { "kind": "through_point_parallel_plane", "through_point": "M", "parallel_plane": ["A","B","C"] },
  "quote": "Mặt phẳng (α) qua M và song song với (ABC) cắt SB, SC, SD lần lượt tại N, P, Q.",
  // (1)+(4) source-stated constraints: each with its own quote; `point` null = the source states the cut, not a name
  "stated_intersections": [
    { "edge": ["S","B"], "point": "N", "quote": "cắt SB, SC, SD lần lượt tại N, P, Q" },
    { "edge": ["S","C"], "point": "P", "quote": "…" },
    { "edge": ["S","D"], "point": "Q", "quote": "…" } ],
  // optional: a boundary the AUTHOR asserts (Adapter /3's /1 meaning). Never trusted: verified by (5) or refused.
  "declared_boundary": null,
  // what the section is used for: a derived solid needs the full boundary; a construction does not
  "requires_closed_boundary": true
}]
```

Engine-owned outputs (route result, never input):

```jsonc
"section_result": {
  "boundary": ["M","N","P","Q"],                                   // (2) cyclic, exact cross-section
  "vertices": [                                                    // (3) every boundary vertex, typed provenance
    { "label": "M", "edge": ["S","A"], "provenance": "THROUGH_POINT_REUSE", "stated": false },
    { "label": "N", "edge": ["S","B"], "provenance": "SOURCE_NAMED", "stated": true, "quote": "…" },
    { "label": "I", "edge": ["S","D"], "provenance": "DERIVED_FRESH", "stated": false, "display": "giao điểm của SD và (α)" } ],
  "closure_certificate": {                                         // (5)
    "rule": "boundary == cross_section(solid, plane) up to rotation/reversal; every vertex 0 < t ≤ 1 on its edge",
    "verified": true }
}
```

Rules: a stated intersection is validated by the Source Gate (the `DINH_CAT_CANH` cut-clause binding that exists
today); an unstated boundary vertex is `DERIVED_*`, never presented as a source fact; a `declared_boundary` that differs
from the certificate is `SECTION_BOUNDARY_INCOMPLETE`; a section with `requires_closed_boundary` whose stated
constraints cannot be closed is refused (bridge) or closed by derived vertices (only with decision D6).

## 4. Compatibility and migration plan

1. **`/1` stays parseable and keeps its per-route legacy meaning** (as implemented). No silent reinterpretation.
2. **Cross-route boundary rule.** Any component that may hand one payload to *either* route (none exists today: the two
   routes are separate offline callables; `/api/analyze` reaches neither) must treat a `/1` payload with non-empty
   `cut_edges` as `CUT_EDGES_SEMANTICS_UNDETERMINED` and refuse it, unless the payload is tagged with its route or the
   two readings provably coincide (stated set = full boundary in cyclic order). Today's per-route verification is the
   fallback that makes a mis-routed payload refuse rather than serve wrong (§2).
3. **Converter `/1 → /2`, keyed by declared route only.** Bridge fixtures: `cut_edges` + `named_intersections` →
   `stated_intersections` (quote = the section quote; per-edge quotes need re-authoring where the clause is split).
   Adapter /3 fixtures: `cut_edges` → `declared_boundary`, `stated_intersections` from `named_intersections` only.
   Fixtures without a declared route are not migrated automatically.
4. **Dual run.** Every migrated fixture runs `/1` (legacy route) and `/2` on both routes against the independent oracle;
   compare status, exact answers, derived identities, goal outcomes. Accept only zero wrong serves and documented
   refusal deltas.
5. **Version bumps then, not now:** `typed-fact-next/2`, `typed-fact-next-bridge/2`, Adapter successor
   (`hybrid-simulation-adapter/4`, `hybrid-route-d-simulation/4`). Planner/Registry/Engine internal versions follow.
6. Provider surfaces (`flat`, `v3`, function calling, TypedFact, declarations) are **not** touched by `/2`; a provider
   that emits `/2` is a separate, separately measured decision.

## 5. Owner decisions requested

| id | decision | options (recommended first) | evidence / trade-off |
|---|---|---|---|
| **D1** | Adopt `typed-fact-next/2` section shape (§3) and the migration plan (§4) | **GO** / modify / reject | Removes the ambiguity at its root. Cost: converter + dual-run session; fixtures with split clauses need re-authored quotes. |
| **D2** | Source Gate strictness for Adapter /3 payloads the bridge cannot express | **(a) strict: refuse `SOURCE_GATE_UNAVAILABLE`** / (b) keep legacy checks, labelled (implemented now) | (b) leaves 1 known invalid serve (anonymous ratio operand, `xfail(strict)` in `test_hybrid_contract_unification.py`). (a), measured on `3553e4d4` with a scratch plugin (no product edit): 18 Adapter /3 tests change — 10 lose a served result (qualified multi-solid identity, unstated cuts, two-line planes; the frozen dev corpus drops from 7/10 to **0/10** served positives) and 8 only change their refusal code. Curved is untouched (no planner path). A "strict only for numeric answers" variant costs the same. Recommended **together with D6**, which makes the bridge express most of those payloads. |
| **D3** | Source Gate phrase coverage | **(a) a preregistered, measured gate-grammar wave** / (b) accept | 4 of 5 paraphrases of the section clause are false refusals on both routes (`SOURCE_OBJECT_MISMATCH`); so are A3-DEV-10 and the complete-boundary encodings of A3-DEV-03/04/06/09 ("Dựng …, thiết diện bởi (α)" not bound to the solid; 5 strict xfails). Without D3, D2(a) would refuse Adapter /3's whole dev corpus. Never loosen the gate to gain coverage; extend its grammar with negative controls. |
| **D4** | IR budget for engine-generated programs | **(a) keep 32, refuse (now)** / (b) a structural budget derived from the solid (e.g. 32 + 3 per extra lateral edge) / (c) merge the last duplicate (visible section plane re-declares the hidden operand plane: −1 declaration, moves the plane's birth) | Hexagonal base: 33 (∥ plane) and 36 (⊥ plane) declarations after canonicalization — genuine size, not redundancy. 32 was set against LLM over-declaration (`validator.py` comment); engine programs are a different population. |
| **D5** | Version labels for the implemented behaviour change | **(a) bump with `/2` (D1)** / (b) bump internal Engine `/11` + Adapter `/4` now | Engine IR shape changed (fewer declarations) and Adapter /3 refuses more; today identified only by the candidate tree hash `96962736…`. |
| **D6** | Planner derives unstated cut vertices for a derived solid (cost 2, `DERIVED_FRESH`), gated by the closure certificate | **GO as a separate wave** / no | Makes the bridge express Adapter /3's own convention (A3-DEV-03/04/06/09, `S-open-cycle`, `S-cut-edges-not-in-payload`), so D2(a) costs far less. Changes Session 1's reviewed "never assert an unstated cut" design — derived, not asserted, but it is a semantic change and needs its own review. |

Stop condition honoured: no schema, version, provider surface or default-route change was made in this session.
