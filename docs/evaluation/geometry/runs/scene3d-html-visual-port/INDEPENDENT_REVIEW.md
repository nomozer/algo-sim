# Independent review

A separate, freshly started read-only reviewer agent examined `git diff 3bfc8dd0 656759fc`. It edited nothing, ran no build or browser gate, and ran 3 targeted test files (74/74 pass). The first attempt stopped on an API session limit and was resumed with its context intact; the verdict below is from the completed run.

**Verdict: PASS_WITH_LIMITS.** No Critical finding. The reviewer confirmed the following as correct:
- Line2 in-place buffer layout and cumulative dash distances, and the count-bucketed pool (no stale lines left visible).
- Marker scaling about the foot.
- Two-pass shells over the unchanged depth prepass; the CPU edge classifier untouched.
- Plane border change is presentation-only.
- No geometry, name or provenance inference.
- No backend or LLM_ONLY change.

| # | Severity | Finding | Resolution (commit `852f6501`) |
|---|---|---|---|
| 1 | Important | Right-angle duplicate key used parent-local feet, so explode/isolate could hide the wrong mark; first-found always won, so a highlighted witness mark could lose to a faded one; invisible ancestors still claimed keys | Key in world space (feet and directions through `parent.matrixWorld`); the strongest (highest-opacity, non-faded) mark wins; marks under hidden ancestors do not compete. Test + 2 fault injections (first-wins, local key) → red |
| 2 | Minor | Section-vertex label role read the whole timeline, so a point could show a future role (#31 frame k ⇔ trace[k]) | Role computed from `objectsAt(scene, buoc)` only |
| 3 | Minor | Marker size cache ignored parent translation (explode without zoom) | Cache key includes the parent's world translation |
| 4 | Minor | Section-fill test lost its lower bound; comment said 0.27 | Floor `≥ 0.32` restored; comment corrected |
| 5 | Minor | Plane-border tests lost `colorWrite` on the standalone case and never checked the span-split path | Both added; fault injection (solid border after the span pass) → red |
| 6 | Minor | Curved-rim bounding sphere computed over the full fixed buffer (oversized) | Accepted: conservative culling only; `raycast` honours `drawRange`; no test reads `position.count` |
| 7 | Minor | Perpendicular-line mark material now `transparent: true` | Accepted: the visible stroke is the Line2 copy |

Limits: the review covered `3bfc8dd0..656759fc`; the fixes in `852f6501` were verified by the tests and fault injections above and by the orbit gate, not by a second independent review. The reviewer did not run the orbit gate or the section-fill measurement; both are reported in GEOMETRY_SEMANTICS_REGRESSION.md.
