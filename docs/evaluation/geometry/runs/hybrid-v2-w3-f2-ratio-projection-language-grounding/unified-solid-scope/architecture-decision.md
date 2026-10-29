# Architecture decision — one declared-solid-scope policy

Context: three point fixes (Codex `f7dd5580`/`11816921`, Claude `393864d1`/`c4d7b759`) each guarded one reader, and
an independent review then found the same defect on readers nobody had listed (`solid-scope-census.md`). The defect
is not in any one reader: the declared scope is only checked where a reader happens to remember to.

## Decision

**D1 — Declaration-level policy at the schema boundary (E0).** `typed_fact_next.py::_validate_declared_solid_scope`,
called from `TypedFactNextPayload._validate_payload`, so `/1` and `/2` and every entry point (Adapter /3 polyhedral and
curved, Adapter /4, planner route, offline, extraction, `/1 → /2` conversion) apply it before dispatch, capability
refusal or fallback (I7). It decides only what the declarations themselves prove:

| rule | inputs | refusal |
|---|---|---|
| R1 existence (I1, I4) | premise `solid_id`; relation `solid_a`/`solid_b`/`solid_id`; simulation `parent_solid_id`; measurement goal `solid_id`; `target.solid_id` — over primary ∪ declared derived solids | `UNKNOWN_SOLID_ID` |
| R2 named solid (I5, I8) | premise `args.solid`, goal `target.solid`: resolve uniquely by id, notation or canonical notation (vertex bindings applied, Adapter /3's own naming) | unknown with a declared scope `UNKNOWN_SOLID_ID`; unknown without one `UNKNOWN_SOLID` (the planner's locked code, N006) |
| R3 one object, one solid (I2) | premise (`solid_id`, `args.solid`); measurement goal (`solid_id`, `target.solid`, `target.solid_id`, section's `target_solid_id`); derived-solid goal (`parent_solid_id`, section's `target_solid_id`) | `SOURCE_OBJECT_MISMATCH` |
| R4 Owner Decision A | `solid_id` present on `volume_ratio` / `residual_volume` | `INVALID_MATH_GOAL` |
| R5 qualified namespaces (I1, I2, I8) | every `sid::X` in premise args, sections, relations, simulation goal refs, goal targets: `sid` must exist, and equal the declared scope of its object when there is one (premise `solid_id`, section `target_solid_id`, goal `solid_id`, frame `solid_id`, face side) | `UNKNOWN_SOLID_ID` / `SOURCE_OBJECT_MISMATCH` |
| R6 relation sides (Owner Decision C, I6) | `shared_faces`: every face label is a vertex of its own side; `coordinate_frame`: every anchor is a vertex of the frame solid | `SOURCE_OBJECT_MISMATCH` |

Missing optional scope stays legal (I3): no rule fires on an absent field, and no rule substitutes a default (I8).

**D2 — Ownership-level policy stays in its existing authority.** The Bridge `_kiem_pham_vi_tien_de` (constructed-point
owner propagation) additionally checks measurement-goal operands against a declared goal scope: an operand provably
owned only by other solids → `SOURCE_OBJECT_MISMATCH` (review #1). Unknown/unowned labels stay with the routes'
existing refusals, so no false refusal of section vertices or constructed points.

**D3 — Curved dispatch runs the ownership policy first.** `_Adapter3Compiler.run` calls the same Bridge validator
before `_run_curved_route` (review #2: premises/relations of curved payloads were read by nothing).

**D4 — Delete the now-redundant reader check.** The Bridge volume-goal `_pham_vi_khoi` call (`393864d1`) is replaced by
R1–R3, which know derived solids (review #5). Adapter /3 `_scoped_solid_name` remains: it is compile-time name
resolution and a second line of defence, not a separate policy.

Rejected: (a) running the whole Bridge ownership validator inside E0 — it would judge legacy qualified identities and
non-identity vertex bindings it was not designed for (false refusals of A3-DEV-02-class positives); (b) a new module —
the schema module is already the shared, import-cycle-free dependency of Bridge and both adapters; (c) making each
route call a checker — that is the pattern that failed three times.

## Contract impact

No JSON-schema field added, removed or retyped (model validators only); the provider prompts and TypedFact (route D)
are untouched; all refusal codes already exist in the taxonomy. Public version tags unchanged: the payloads now refused
were never valid under the declared-scope contract. `CACHE_VERSION` 130: cached `LLM_ONLY` path does not import these
modules. Registry /21, Planner /18, engine, kernel, radical, Adapter /4 code, Scene3D: unchanged.
