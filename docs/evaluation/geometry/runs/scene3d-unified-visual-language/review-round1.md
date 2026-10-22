# Independent review round 1

Reviewer: separate agent `/root/independent_material_review`, read-only, no edits or subagents. BASE/HEAD then `f95596716912e5550ed079287221274b2d70f24c` plus uncommitted candidate. Product source hashes: roles `b94ef05a7b90ded203196e313d2b669be9eef1b480f3d61add5e7d9c814ac959`, view `e4805ca71765ed7c79c7ff08b230b80912c7164bd45e0ff6cb04ab314ba3280d`.

Verdict: no Critical; two Important gaps, one Minor.

1. Important: span rebuilds still recreate materials during orbit; geometry pools do not solve material allocations. Development B sampled 16 allocations in derived sub-pyramid and 57 in public perpendicular scene. Fix: per-owner encountered-style cache, lifecycle disposal, repeated sweep test.
2. Important: resolver-only role test does not exercise actual hide/isolate/step integration. Fix: bounded real UI matrix on multi-solid, cone and prism with shell identity/color observations.
3. Minor: exported given-point neutral differed from renderer's given-point neutral. Fix: single shared value.

Reviewer found consistent polygon/circle/ellipse fills, preserved depth prepasses/Normal/X-ray, causal numeric/context colors and dash semantics. No geometry, topology, camera, classifier, backend or contract change found. Baseline receipt 33 scenes/0 errors; development B was partial at inspection. Reviewer viewed ellipse Normal screenshot only; no aesthetic acceptance.

Declined to judge: final browser/compact/depth results, final A/B/C choice, T3/freeze, human acceptance, live NLU E2E, physical-device performance, universal readability; inherited visibility-dependent edge deduplication/curved suppression policy remains outside this material change. Reviewer explicitly withdrew an unproven double-alpha claim about flat two-pass rims: culling matters.

Disposition: all three findings addressed in subsequent source/harness; see round 2 and final review. No merge authorization.
