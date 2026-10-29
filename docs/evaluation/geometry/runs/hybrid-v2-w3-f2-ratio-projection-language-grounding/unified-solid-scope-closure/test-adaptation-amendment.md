# Test adaptations caused by the closure policy

The closure policy adds S7 (an unqualified label declared only on other solids contradicts the scope) at the schema
boundary. Four earlier mutation oracles relied on cases that a deeper layer used to decide alone; S7 now refuses them
first, so removing the deeper guard no longer changed the outcome (compatibility run 1, `closure-compat1`, 4 mutants
reported alive). No expected refusal code changed; each oracle now uses a case that only the guarded layer can decide,
so every guard is still proven load-bearing.

| test | old oracle | new oracle (same expected code) |
|---|---|---|
| `test_unified_solid_scope.py::test_oracles_kill_unified_scope_mutants[remove_relation_sides]` | face `SAB` claimed for T.ABCD (S belongs to s1 → now S7) | face label `Q` that is no vertex of any solid: only the strict side check (S6) |
| `…[remove_goal_operand_ownership]` | distance from `S` under s2 (now S7); needle moved to the generic S8 loop | distance from constructed `M` (midpoint of SA in s1) under s2: only constructed-point ownership (S8) |
| `…[bypass_curved_prevalidation]` | premise under `zz` with operands `O`,`O'` of `cyl` (now S7) | constructed `M` of `cyl` used by a premise under `zz`: only the Bridge validator run before the curved route |
| `test_adapter3_fallback_safety.py::test_safety_oracles_kill_semantic_and_scope_mutants[remove_terminal_guard]` | `invalid_scope` payload (now refused by the schema before the gate) | schema-valid `control()` with the stubbed Bridge semantic refusal, so the gate's terminal guard is exercised |

Own new suite, before GREEN: the mutation helper rebinds the mutated function in modules that imported it (a source
mutation changes every importer); the parent-ancestry oracle uses a same-label copy of the parent so only S3 decides;
the valid whole-solid containment control requires Adapter /3 to serve and the Bridge routes not to refuse for scope
(they refuse containment as a capability).
