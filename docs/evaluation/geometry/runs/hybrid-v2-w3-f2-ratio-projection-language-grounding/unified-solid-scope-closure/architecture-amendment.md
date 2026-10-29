# Architecture amendment — closing the scope census

Amends `../unified-solid-scope/architecture-decision.md` (D1–D4 stay). Cause of the previous NOT_READY: the census was
a hand list (17 field groups) and the policy covered only the objects on it; the independent review found unlisted
slots (F2–F4) and a regression in the reference scanner (F1).

## Census is mechanical and enforced

`backend/tests/geometry/scope_field_census.py` walks the pydantic models (`/1`, `/2`, nested), expands
`PremiseSpec.args` from `_ARGS_LOI` / `_ARGS_GOC_VUONG` shapes and `MathGoalSpec.target` from the keys the route modules
read (AST). `schema-field-inventory.json` classifies all 185 discovered paths (112 scope-bearing). The coverage test
`test_census_inventory_complete` fails when a model gains an unclassified field, when a scope-bearing field lacks a
positive/negative test, or when one of its rule ids is absent from the product code. Per-kind meaning is covered by
`test_every_relation_kind_has_a_negative_case` / `test_every_simulation_goal_kind_has_a_negative_case`, which compare
against the kind literals of the models.

## Rules (ids appear as `# Sn` comments in product code)

| id | rule | code(s) |
|---|---|---|
| S1 | every declared solid scope exists (primary ∪ declared derived) | `UNKNOWN_SOLID_ID` |
| S2 | a named solid resolves uniquely by id, notation or canonical notation | `UNKNOWN_SOLID_ID` (scoped) / `UNKNOWN_SOLID` (unscoped) |
| S3 | all solids named by one object agree (incl. section's solid, derived parent) | `SOURCE_OBJECT_MISMATCH` |
| S4 | a scope field without documented meaning for its kind is refused, never ignored: ratio/residual `solid_id` (decision A); `parent_solid_id` outside `construct_derived_solid`, `target_solid_id` on `construct_derived_solid` (Owner D-A) | `INVALID_MATH_GOAL` / `INVALID_SIMULATION_GOAL` |
| S5 | references follow the reference grammar (`split_edge_key` for `U-V` keys, `sid::CHAIN` for containment chains; hyphens legal in ids); a qualified namespace exists and equals its object's scope | `INVALID_QUALIFIED_REF` / `INVALID_DERIVED_SECTION` / `UNKNOWN_SOLID_ID` / `SOURCE_OBJECT_MISMATCH` |
| S6 | faces / frame anchors are vertices of their own side | `SOURCE_OBJECT_MISMATCH` |
| S7 | an unqualified label declared only on other solids (and not a constructed name) contradicts the scope | `SOURCE_OBJECT_MISMATCH` |
| S8 | ownership through constructed points (Bridge `_kiem_pham_vi_tien_de`, run by every route incl. curved) for every scoped object of `scope_records` | `SOURCE_OBJECT_MISMATCH` |
| S9 | a section reference exists and its solid agrees with the object's scope | `UNKNOWN_SECTION_ID` / `SOURCE_OBJECT_MISMATCH` |
| S10 | every `target_refs` / `apex_ref` token resolves (solid, derived solid, section, vertex, constructed or section point); nothing is silently dropped | `UNKNOWN_VERTEX_REF` |
| S11 | goal operand values have reference types (`GOAL_OPERAND_KEYS`, incl. contract-level `plane1`/`plane2`); `target.section_id` is a string | `INVALID_MATH_GOAL` |

One enumeration (`typed_fact_next.scope_records`) yields every scoped object — sections, each relation side
(side a: `face_a`/`entity_a`/`pairs[*][0]` under `solid_a` or `solid_id`; side b symmetrically; single-scope fields
under `solid_id` or, for `section_membership`, the section's solid), simulation goals by kind (plane section → its
section's solid; derived solid → parent; highlight/object → `target_solid_id`) and measurement goals. The schema
(S5/S7/S10) and the Bridge (S8) both iterate it, so a new scoped object is added once.

## Other fixes

F1: `split_edge_key` replaces every raw `split("-")` on references (schema section validator, `/1 → /2` conversion,
Bridge `_check_qualified_refs` and section translation, scope scanner). F5: the curved route resolves a goal's
`target.solid` by alias; malformed targets are refused by S11/S9 at the schema. F6: the Bridge resolves area/volume
goal solids by alias (`resolve_solid_name`), so a valid notation is no longer `UNKNOWN_SOLID_ID` /
capability-refused; plane-pair operand keys are in the operand list.

Unchanged: Registry /21, Planner /18, engine /14, kernel, radical, Adapter /4 code, Scene3D, default routing, provider
prompts, JSON schemas (validators only). `CACHE_VERSION` 130 (cached `LLM_ONLY` path does not import these modules).
