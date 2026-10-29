# Independent pre-freeze adversarial review — NOT_READY (2 MAJOR, 0 BLOCKER)

A fresh-context subagent of this session reviewed research HEAD `6b4a9752` (product `717f8b2b`) against `main`
`996f114b` and `5e44d5da`. It was read-only on the repository, made no provider calls, and wrote its probes outside the
tree. Its scripts and raw outputs are copied verbatim into `pre-freeze-review/` (SHA-256 list:
`pre-freeze-review-files.sha256`). The harness blocked the reviewer from writing `report.md`, so its findings are
transcribed below. The two MAJOR rows were re-checked against `pre-freeze-review/analysis.txt`, `alias.txt` and
`locked16.txt`.

**Verdict: `NOT_READY`.** Per Owner GO §8 there is no freeze, replay, T0/T1/T2 or Full T3.

| id | sev | finding | evidence |
|---|---|---|---|
| F1 | MAJOR | **Target grammar widened.** The scope-only branch of `_validate_goal_target` accepts `{solid_id}` and `{solid, solid_id}` for `radius`, `lateral_area` and `area`. Their registered alternatives are `solid` / `section_id` / `polygon` only. Since `4b361c47`, the curved Adapter /3 path reads `measurement_scope`. As a result, cylinder/cone/sphere `radius` and `lateral_area` with `{solid_id}` are **SERVED on /1**, where `main` and `5e44d5da` refuse `INVALID_MATH_GOAL_TARGET`. Curved `volume {solid_id}` changed the same way; that form is registered, but the change was not disclosed. Answers are correct, but this contradicts "the grammar is not widened" and the `contract-analysis.md` claim "solid-valued alternatives … unchanged". Gate A could not see it: it only counts losses. | `analysis.txt` `K.{cyl,cone,sph}.*.solid_id` |
| F2 | MAJOR | **/1 and /2 do not share one grammar.** Locked param 13, `{"segment": ["A", "pr::A"]}`, passes the schema on both versions: the distinctness check compares strings. On /2 the Bridge refuses it with `INVALID_MATH_GOAL`. On /1 the Planner's capability exit comes first, Adapter /3 falls back to legacy, and it **serves 0**. Main does the same, so the defect is pre-existing. It still falsifies the CIC-D1-C record "one closed grammar … enforced at the schema". | `locked16.txt` L13, `alias.txt` |
| F3 | MINOR | Two reviewer mutants survive. `pure_scope_any`: no test isolates the schema's scope-only rule; later layers refuse. `identity_ignores_scope`: killed only by an `inspect.getsource` artifact; the failure mode is fail-closed. | `mutant2_*.log`, `pure_scope_probe.out` |
| F4 | MINOR | `gate-d.json` describes the 232-test command as "test_typed_fact_next_v2*.py (5 files)". Those 5 files give 185; 232 = those 5 + `test_hybrid_contract_v2.py`. The description was hard-coded in `tools/record_d.py`. | — |
| F5 | MINOR | `n2-amendment.md` says the v1 in-target `solid` form named the solid by notation. It used the id `pyr2` (`cases.json` preserves that correctly). Its valid equivalent is `N2v2.goal_solid_id`. | `git show 1490e3cd:backend/tests/geometry/test_closed_input_contract.py` |
| F6 | MINOR | Pre-existing (`11816921`, before this task): in `test_typedfact_planner_bridge.py`, an input changed from `pyr::M` to `pyr::Z`, and one assertion was removed with an inaccurate note. Re-applying the assertion still passes 11/11. | `moved_assert_probe.out` |
| F7 | MINOR | Pre-existing: prism `radius`/`lateral_area {solid: pr}` on Adapter /3 returns `ADAPTER_INTERNAL_ERROR KeyError 'ask2'`, the same as on main and pre. Gate A's "0 internal" covers only its own probe set. | `summary.txt` |
| F8 | NOTE | An explicit `null` in an inapplicable field is now refused; this is documented. No recorded payload is affected. A provider emitting nulls cannot be measured offline. | `corpus_diff.txt` |
| F9 | NOTE | `{section_id, solid*}` is now `INVALID_MATH_GOAL`, as documented. No corpus payload uses it. | `summary.txt` |
| F10 | NOTE | An unscoped measurement that mixes solids is served (correct); an unscoped premise that mixes solids is refused. Policy asymmetry. | `analysis.txt` `O.mixed.*` |
| F11 | NOTE | `../operand-grammar.md` still says scope keys may accompany operands. CIC-D1 superseded that, so it needs a CORRECTED_BY pointer. | — |

What held:
- Of 315 inputs with a scope key beside geometric operands, none was served on any route or tree.
- Of 23 wrong-scope ownership inputs, none was served (main served 18 on a3).
- Locked test file unchanged versus main; 43/43 pass.
- No hard-coded ids in the product diff.
- The Gate A POS reclassification is legitimate: the valid goal-level equivalent is still served (√5/2)·a.
- GREEN 791/6 reproduced.
