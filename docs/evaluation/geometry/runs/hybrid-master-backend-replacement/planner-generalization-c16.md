# Continuation 16 — goal-directed planning: measured capability, root cause, and what was changed

**Verdict: `GENUINE_DISCOVERY_NOT_ESTABLISHED`.** On every case measured, on both route B and Hybrid `/4`, each served
plan either builds what the problem text describes or applies a declared decomposition. 0 plans required a step found
by open search. The cause is structural; the evidence follows.

**Product change, one:** planner `/24` reports step provenance honestly (§4). No search engine was added, because the
experiments found no planning gap for one to close (§2.3). That would have been the "invent a positive" this Master
Directive forbids.

All results are `VERIFIED_OFFLINE` and implementer-authored development data, with 0 provider calls.

## 1. How the `/23` planner builds a plan (read from the code)

- **Measurement goals.** The kernel has a direct primitive for every quantity in the vocabulary:
  - distances point–plane, line–line (skew), line–plane and plane–plane;
  - angles line–plane, line–line and plane–plane;
  - lengths, areas, volumes, section area.

  So a measurement never *needs* an intermediate construction. The textbook "method", meaning auxiliary feet and
  parallel planes, is replaced by exact analytic geometry.
- **`_EffectResolver`.** This is a bounded backward search over Registry `PlanningContract`s; the bounds are depth 3,
  32 needs and 8 candidates.
  - A `Point` need is either a label (a leaf) or a *described* point, and each description has exactly one producer.
  - `AnswerDistance` has two producers, chosen by the operand's type (plane or line). That is type dispatch; there is
    no alternative to search between.
  - The only chain longer than one step is Foot → `ask_length`, which is the declared rule
    `AUXILIARY_RULES["distance(point,line)"]`.
- **Derived planes (sections).** These are the only place where the kernel needs objects the text does not name: a
  plane is cut through three points. Hand-written decompositions build them:
  - `_mat_qua_diem` for `MAT_SONG_SONG` and `MAT_HAI_DUONG`;
  - `_mat_vuong_duong` for `MAT_VUONG_DUONG`, whose anchor vertices come from a 170-line structural heuristic without
    coordinates.
- **Root cause of the false label.** `/23` set `has_discovered = rule == "effect-chain" or point_chain`. Both are the
  certificates of a goal or plane on a *described point*. So "discovered" meant "built the point the question
  described".

## 2. Experiments

### 2.1 The planner's own label, re-measured with the reviewed rule (C15 `composition_label`)

| set | planner self-label "DISCOVERED" | under the rule | receipt |
|---|---|---|---|
| C13 probe, `/4` | 9 | 6 `SOURCE_EXPLICIT_SEQUENCE` + 3 `REGISTERED_DECOMPOSITION` | `r1-composition-relabel.json` |
| C11 matrix, route B | 9 served (+1 refused, H1) | 6 source-explicit + 3 registered | `route-b-composition-relabel.json` |
| R-1 pilot gold, `/4` | 11 | 7 source-explicit + 4 registered | `r1-live-pilot-gold-replay.jsonl` |

### 2.2 Reachable but missed? A systematic search (`plane-witness-reachability.json`)

- **Cases:** every "(P) qua M ⊥ d" on the pyramid S.ABCD (SA ⊥ base) and the right prism ABC.A'B'C', each at 2 sizes.
  d is every vertex pair; M is every vertex and every edge midpoint. That gives **710 cases**, generated rather than
  hand-picked, run on the real `/4` path.
- **Oracle:** independent exact coordinates (no product import). It computes the section polygon and its area², and
  enumerates the witness anchor pairs the primitives could use.
- **Result:**
  - 364 reachable, **all served exactly**;
  - 346 unreachable (no section), all refused;
  - **0 reachable-but-missed**, 0 wrong-served.
- **The other two plane kinds** (∥ a plane, ∥ two lines) have no choice to search: their directions are fixed by the
  text.
- **Review round 1 (MINOR-4).**
  - In all 710 rows the oracle found ≥ 2 witness pairs, so "reachable" reduces to "the plane cuts the interior". Any
    two vertices not coplanar with d work, which makes the anchor choice easy, not deep.
  - The reviewer also ran 948 extra cases in scratch: a regular pyramid with its apex over the centre, a cube, and
    S.ABC with SA ⊥ (ABC) and a right angle at B, with M also at face centroids. Again 0 reachable-but-refused and
    0 wrong-served. These are reviewer evidence, not a committed receipt.

**On the tested topologies and point choices, no planning gap exists for a search engine to close.** This is evidence
for the representable domain, not a proof over it.

### 2.3 Ablation (`planner-ablation.json`; monkeypatch in the evaluation process only)

There are 34 served cases, from C13 `/4`, the R-1 gold and the C11 route B.

| arm | survive | refused | which |
|---|---|---|---|
| C: all declared rules off | 21 | 13 | the 21 are exactly the source-explicit plans; the 13 are exactly the registered ones (sections, distance to a line) |
| D: budget depth 1 / 4 needs / 2 candidates | 12 | 22 | sections survive (rules do not search); goals on described points need depth ≥ 2 |

So the capability is attributed completely: source descriptions plus declared rules. Nothing depends on open search.

### 2.4 Contract-only extension, and a missing primitive (`test_planner_recomposition_oracle.py::test_c16_*`)

- **A new function known only by its contract** (a clone of `orthogonal_projection_line` under a new name) is selected
  by the resolver and written from its template, with no dispatch code.
  - This is planner level only: the clone has no IR of its own, so nothing is executed.
- **Deleting the only producer** gives a typed refusal, not a guess.

## 3. Why genuine discovery cannot appear here (`INFERRED` from §1–§2, and testable)

1. **The kernel answers every vocabulary quantity directly.** A measurement never needs a hidden intermediate.
2. **Problem texts name or describe every object a goal uses.** By the rule, building it is source-explicit.
3. **The only hidden objects are a derived plane's witness points.** Declared rules build them, and §2.2 found them
   complete in this domain.

Discovery would become necessary, and measurable, only for goals whose objects are **implicit**. `TypedFactNext /2` and
the bridge cannot represent any of them today, so this is a representation gap, not a planner gap:
- a plane through two points ⊥ a plane ("mặt phẳng qua MN và vuông góc với (ABCD)");
- a plane containing a line ∥ another line ("(P) chứa AB và song song với SC");
- a measure on a described line ("giao tuyến của (SAB) và (SCD)");
- a point fixed by a property, not a construction.

Each of these is a model-surface change, so it needs an Owner decision: additive `/2` kinds, Source Gate grammar, gate
certificates and engine postconditions.

Only then would a constraint-to-witness planner (Direction effects realized by `translate_point`,
`orthogonal_projection_line` and `orthogonal_projection`, verified exactly by the kernel) have goals whose plans are not
written down anywhere. `HYPOTHESIS`: on those goals it would produce genuinely search-generated steps.

## 4. The product change: planner `/24` (`b70995db`)

- **Provenance at emission.** The effect resolver tags each step it writes:
  - a descriptor contract is `source_defined`;
  - a declared rule's policy (projection foot, section vertex, declared intersection) is `registered`;
  - anything else is `search_generated`.

  Steps of the hand-written decompositions are `registered`. A `DEFINITION_FUNCTIONS` step (`regular_polygon` /
  `rectangle` spelling out the base that "hình lập phương" or "chóp đều" defines) is `source_defined` (review MINOR-2).
  With that, `/23` and `/24` differ only where `/23` said DISCOVERED.
- **Telemetry.** `search_telemetry` adds `source_defined_steps`, `registered_decomposition_steps` and
  `search_generated_steps`. `DISCOVERED_FUNCTION_COMPOSITION` now requires a search-generated step.
- **Agreement with the independent rule:** case for case, on all served rows of route B (13,
  `route-b-composition-relabel-r2.json`) and the R-1 gold (11, `r1-live-pilot-gold-replay-r2.jsonl`:
  `planner_label_disagreements = []`).
  - The runner now applies its rule to **every** served row, never only to those the planner calls discovered
    (review MAJOR).
  - **Stated limit (review MINOR-1):** in Registry `/29`, every contract the resolver can emit is an answer, a
    descriptor or a declared rule's policy. So `search_generated`, and with it DISCOVERED, **cannot occur today**.
    Agreement on that label is by construction and carries no evidence; the label is ready for a contract that would
    make it reachable (§3).
- **Reviewer's comparison:** they ran the `/23` planner next to `/24` on 752 plans from 15 planner-heavy test files.
  Calls and auxiliary certificates were identical, except in tests that monkeypatch planner globals.
- **Unchanged:** answers, calls, envelopes and cache identity. 41/41 preview fixtures verify through the declared
  `/23 → /24` identity delta. `CACHE_VERSION` stays 131: `/api/analyze` does not reach the planner.
- **Tests:** the three tests that locked the false label now assert the provenance contract (it is a correction, not a
  repin; see §2.1).
- **Still open:** a refused route-B plan still carries the planner's proposal telemetry (H1). It describes the proposal,
  not an outcome.

## 5. Status labels

| label | state |
|---|---|
| `PLANNER_GENERALIZATION_OFFLINE_VERIFIED` | **no.** Telemetry is honest and the capability is measured; genuine discovery is `NOT_ESTABLISHED` |
| `LIVE_EXTRACTION_NOT_MEASURED` | yes |
| `PAIRED_EVALUATION_NOT_MEASURED` | yes |
| `INTEGRATION_NOT_READY` | yes |
| `PRODUCTION_NOT_READY` | yes |
