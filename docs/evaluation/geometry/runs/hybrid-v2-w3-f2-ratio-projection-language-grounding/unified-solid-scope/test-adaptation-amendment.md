# Test adaptations caused by moving scope validation earlier

The unified policy (`architecture-decision.md` D1) refuses scope contradictions at the schema boundary, before the
Bridge and Adapter /3 layers that earlier tests exercised. Six existing tests observed those deeper layers and failed
on GREEN (`unified-solid-scope` GREEN run 1, 9 failures). No expected refusal code was changed; each test now asserts
the earlier refusal **and** keeps proving the deeper defence with the schema bypassed, so nothing was weakened.

| test | why it failed | adaptation |
|---|---|---|
| `test_adapter3_fallback_safety.py::test_legacy_construction_output_cannot_create_or_borrow_foreign_ownership[s2::M, foreign::M]` | `compiler(p)` parses; the schema now refuses the qualified projection output (same codes) | assert the route refuses with the same code; then build the compiler with `PremiseSpec.model_construct` (schema bypassed) and assert `_compile_premises` still raises the same code (`T` case unchanged) |
| `…::test_real_legacy_height_solid_must_agree_with_premise_scope[pyr1-pyr2, pyr1-D.ABC]` | precondition asserted the Bridge's first refusal was the capability gap; a contradiction is now refused before it (I7) | Bridge's first refusal must be the scope code for negatives and still `BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY` for the three valid variants; route outcome assertions unchanged |
| `…::test_solid_scope_oracles_kill_guard_removal` (4 mutants of `_pham_vi_khoi` / `_scoped_solid_name`) | route-level oracle is now answered by the schema, so the deeper guard's removal was invisible | oracle calls the guarded function directly with the same two cases and codes (conflict → `SOURCE_OBJECT_MISMATCH`, unknown scope → `UNKNOWN_SOLID_ID`); untyped exceptions count as failure |
| `test_premise_scope_recovery.py::test_scope_safety_oracle_kills_bypass_and_default_scope_mutants` (4) | removing only the Bridge validator no longer exposes NEG08/23 | with the Bridge mutant alone, assert the schema refuses `UNKNOWN_SOLID_ID`; the original unsafe path (SERVED) must still appear once the schema rule is removed too |
| `test_unified_solid_scope.py` helper `a4` (own new test) | `/1 → /2` conversion parses `/1`, so its refusal surfaced as an exception in the harness | conversion refusal is reported as the refusal (same code) |
| `test_unified_solid_scope.py` distance/constructed-point controls (own new test, before product change) | Adapter /3 refuses `ask_distance_point_plane` with `SCHEMA_INVALID` on main as well — a capability limit unrelated to scope | controls require Adapter /4 SERVED and Adapter /3 served or refused for a non-scope reason; negatives still require identical scope codes on both |
