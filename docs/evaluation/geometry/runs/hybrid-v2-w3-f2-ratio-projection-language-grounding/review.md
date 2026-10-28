# Independent W3-F2 safety review

Reviewer: `/root/f2_safety_review`, read-only independent subagent. Review concluded 2026-10-29.
Reviewed baseline `996f114b` and the Registry-only candidate now preserved in product checkpoint `e9d5a9d73064a15b7702eb32c008835bc99fba6d`.

**Verdict: NOT_READY — 1 BLOCKER, 1 MAJOR.** Stop under Owner GO §15; no candidate freeze or Full T3 claim.

## BLOCKER: declared premise scope is discarded

The reviewer independently reproduced DEV-NEG-08 and DEV-NEG-23 as WRONG_SERVED, code null. Each declares only solid s1 but gives the ratio/projection premise solid_id="foreign". These are valid negative inputs: PremiseSpec explicitly defines optional solid_id scope (`backend/app/simulation/geometry_functions/typed_fact_next.py:204`), the adapter contract defines refusal for undeclared solids (`docs/architecture/TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md:31,80`), and Adapter /3 already checks it (`backend/app/ai/adapter3_simulation.py:417`).

`typed_fact_next_bridge.py::_check_qualified_refs` skips keys ending in _id; the divide_segment and orthogonal_projection branches (around lines 300/305) then translate args while omitting prem.solid_id. Source Gate receives no scope to reject. This demonstrates invalid provenance being served; it does not establish incorrect arithmetic.

A read-only in-memory import of exact Registry /20 from baseline 996f114b showed both original new-language negatives refuse PREDICATE_NOT_IN_QUOTE, but canonical previously supported wording makes both serve. The defect predates F2; broader F2 wording exposes the same unsafe path. This diagnostic is not a detached-checkout acceptance gate. Parent reproduction from unchanged main independently agrees in `verification/baseline-foreign-scope-reproduction.json`.

## MAJOR: intended projection-incidence check remains unverified

DEV-NEG-20 changes the foot from base F to top F'. It is refused with UNDERDETERMINED_POINT, outside locked expected codes, reporting unresolved top/auxiliary points. The case is safely refused but does not demonstrate the intended incidence/contradiction check. Retain REFUSED_REASON_DISAGREEMENT; do not broaden the locked oracle silently.

## Independent targeted verification

F2 + W3-F1 tests: **116 passed, 4 failed**. F2 has 94 passes and failures NEG08/20/23. W3-F1 has 22 behavioral passes and its version test fails because it pins Registry /20 while the patch declares /21. The pin failure is unfinished compatibility work, not a behavioral F1 regression.

| Owner dimension | Bounded assessment |
|---|---|
| Ratio binding | Existing exact solver retains membership, direction/complement and 0<t<1; registered role mutations refuse. |
| Projection binding | New reader binds source/foot/explicit plane together and consumes the full quote; NEG20 remains unresolved. |
| Source-quote provenance | Quote presence retained; declared solid provenance lost at bridge. |
| Ambiguous language | Registered conditional, negated, proof-goal and contradictory-tail mutations refuse. |
| Mixed solids | Scope boundary fails; a future fix also needs known-solid cross-contamination coverage. |
| Primed labels | Registered prime tamper refuses; authored Unicode-prime source control passes. |
| Negative coverage | 22/24 refused; 21/24 matched locked codes; two unsafe serves. |
| W3-F1 | 22 behavioral tests pass; version pin fails. |
| Version/cache | /21 reflects changed language; cache/fixture compatibility checks incomplete. |
| Freeze/T3 | No frozen candidate; T2/Full T3 intentionally unrun after safety stop. |
| Evidence classification | Development evaluation, not a new blind holdout. |
| Hardcode | No corpus IDs, expected answers or oracle lookup in product diff. |

## Recommended future scope

After Owner decision, validate premise scope before bridge translation erases it; cover unknown scope and incompatible references to another declared solid. Prove the intended projection-incidence rejection with an isolated valid witness. Retain the bounded readers; do not alter Planner, kernel, capability matrix or historical evidence to bypass these failures.

Declined to judge: T2/Full T3, new frozen-candidate integrity, complete cache/fixture compatibility and full Wave 3 replay did not run due to the required safety stop. This review does not approve readiness or integration. The reviewer modified no file or Git state.
