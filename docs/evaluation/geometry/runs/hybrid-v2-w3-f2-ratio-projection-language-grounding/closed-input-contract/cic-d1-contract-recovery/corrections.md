# Corrections (new layer; the corrected files are unchanged)

| corrected file | statement | correction | source |
|---|---|---|---|
| `contract-analysis.md` §Rule after the fix | "Solid-valued alternatives … are unchanged" | False for curved solids on Adapter /3. Since `4b361c47`, `{solid_id}` (and `{solid, solid_id}`) is accepted for `radius`, `lateral_area` and `area`, and served on curved /1. Volume `{solid_id}` on curved /1 also changed from refused to served. | review F1 |
| `contract-analysis.md` §`/1` versus `/2` | "one closed grammar for `/1` and `/2`, enforced at the schema" | The schema distinctness check compares raw strings, so `{segment: [A, pr::A]}` passes on both. /2 refuses it in the Bridge. /1 serves 0 through the legacy fallback (pre-existing on main). | review F2 |
| `gate-d.json` `locked_v2_targeted.files` | "test_typed_fact_next_v2*.py (5 files)", 232 passed | The 232 come from those 5 files (185) plus `tests/geometry/test_hybrid_contract_v2.py` (47). The command explicitly listed `tests/geometry/test_hybrid_contract_v2*.py` as well; the receipt's description, hard-coded in `tools/record_d.py`, omitted it. | review F4 |
| `n2-amendment.md` §Replacement | the v1 in-target `solid` form "named the solid by notation" | It used the id `pyr2`. Its structurally valid equivalent is `N2v2.goal_solid_id`. `cases.json#N2v1.*` preserves the inputs correctly. | review F5 |
| `../operand-grammar.md` | "Scope keys may accompany geometric operands only as validated ownership assertions" | Superseded by Owner decision CIC-D1-A (`owner-decision.md`): scope keys never sit beside geometric operands. | review F11 |
